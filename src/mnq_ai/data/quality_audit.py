"""Streaming data-quality audit accumulation and report writing."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc

from mnq_ai.config import Phase1Config
from mnq_ai.constants import REQUIRED_MBO_COLUMNS
from mnq_ai.data.schemas import (
    TimestampParseResult,
    timestamp_array_to_ns,
    timestamp_ns_to_iso,
)
from mnq_ai.data.sessionizer import CMESessionizer


@dataclass
class SessionCoverage:
    """Observed coverage for one trading session."""

    min_ts_ns: int | None = None
    max_ts_ns: int | None = None
    rows: int = 0

    def update(self, ts_ns: int | None) -> None:
        if ts_ns is None:
            return
        self.rows += 1
        self.min_ts_ns = ts_ns if self.min_ts_ns is None else min(self.min_ts_ns, ts_ns)
        self.max_ts_ns = ts_ns if self.max_ts_ns is None else max(self.max_ts_ns, ts_ns)


@dataclass
class AuditAccumulator:
    """Memory-bounded audit state reduced from input batches."""

    total_input_rows: int = 0
    action_counts: Counter[str] = field(default_factory=Counter)
    side_counts: Counter[str] = field(default_factory=Counter)
    action_side_counts: Counter[str] = field(default_factory=Counter)
    rows_per_symbol: Counter[str] = field(default_factory=Counter)
    rows_per_session: Counter[str] = field(default_factory=Counter)
    null_counts: Counter[str] = field(default_factory=Counter)
    invalid_row_counts: Counter[str] = field(default_factory=Counter)
    total_t_rows: int = 0
    total_f_rows: int = 0
    valid_t_rows: int = 0
    unknown_side_t_rows: int = 0
    sum_t_size: int = 0
    output_row_count: int = 0
    output_total_size: int = 0
    sum_signed_volume: int = 0
    invalid_tick_prices: int = 0
    min_price: float | None = None
    max_price: float | None = None
    min_size: int | None = None
    max_size: int | None = None
    min_ts_event_ns: int | None = None
    max_ts_event_ns: int | None = None
    duplicate_candidates: int = 0
    ordering_anomalies: int = 0
    output_file_count: int = 0
    output_byte_size: int = 0
    input_byte_size: int = 0
    quarantine_row_count: int = 0
    last_order_key: tuple[int, int, int] | None = None
    last_duplicate_prefix: tuple[int, int] | None = None
    session_coverage: dict[str, SessionCoverage] = field(default_factory=lambda: defaultdict(SessionCoverage))

    def observe_input(
        self,
        table: pa.Table,
        *,
        ts_event: TimestampParseResult,
        ts_recv: TimestampParseResult,
    ) -> None:
        """Record raw batch diagnostics."""

        self.total_input_rows += table.num_rows
        for name in REQUIRED_MBO_COLUMNS:
            if name in table.column_names:
                self.null_counts[name] += _true_count(pc.is_null(table[name]))

        actions = [str(value) if value is not None else "<NULL>" for value in table["action"].to_pylist()]
        sides = [str(value) if value is not None else "<NULL>" for value in table["side"].to_pylist()]
        symbols = [str(value) if value is not None else "<NULL>" for value in table["symbol"].to_pylist()]
        batch_action_counts = Counter(actions)
        self.action_counts.update(batch_action_counts)
        self.side_counts.update(sides)
        self.rows_per_symbol.update(symbols)
        self.action_side_counts.update(f"{action}|{side}" for action, side in zip(actions, sides, strict=True))
        self.total_t_rows += batch_action_counts.get("T", 0)
        self.total_f_rows += batch_action_counts.get("F", 0)
        self._update_min_max_timestamp(ts_event.values)
        self._update_ordering(ts_event.values, table["sequence"], table["source_row_number"])

    def observe_trade_candidates(self, table: pa.Table) -> None:
        """Record source-side valid trade candidates before output writing."""

        if table.num_rows == 0:
            return
        sizes = table["size"]
        self.valid_t_rows += table.num_rows
        self.sum_t_size += _sum_int(sizes)
        self.unknown_side_t_rows += sum(1 for side in table["side"].to_pylist() if side == "N")
        self._update_min_max_price(table["price"])
        self._update_min_max_size(sizes)

    def observe_output(self, table: pa.Table) -> None:
        """Record canonical trade tape output diagnostics."""

        if table.num_rows == 0:
            return
        self.output_row_count += table.num_rows
        self.output_total_size += _sum_int(table["size"])
        self.sum_signed_volume += _sum_int(table["signed_volume"])
        session_ids = [str(value) for value in table["session_id"].to_pylist()]
        self.rows_per_session.update(session_ids)
        for session_id, ts_ns in zip(session_ids, timestamp_array_to_ns(table["ts_event"]), strict=True):
            self.session_coverage[session_id].update(ts_ns)

    def observe_invalid(self, reason_counts: Counter[str], *, quarantined_rows: int = 0) -> None:
        """Record invalid-row reason counts."""

        self.invalid_row_counts.update(reason_counts)
        self.invalid_tick_prices += reason_counts.get("invalid_tick_price", 0)
        self.quarantine_row_count += quarantined_rows

    def observe_output_layout(self, output_file_count: int, output_byte_size: int) -> None:
        """Record final output file statistics."""

        self.output_file_count = output_file_count
        self.output_byte_size = output_byte_size

    def reports(self, schema: dict[str, Any], config: Phase1Config) -> dict[str, dict[str, Any]]:
        """Build all Phase 1 machine-readable reports except the manifest."""

        partial_sessions = self._partial_session_warnings(config)
        return {
            "schema_report": {
                **schema,
                "total_input_rows": self.total_input_rows,
                "null_counts": dict(self.null_counts),
            },
            "action_side_report": {
                "total_input_rows": self.total_input_rows,
                "count_by_action": dict(self.action_counts),
                "count_by_side": dict(self.side_counts),
                "count_by_action_and_side": dict(self.action_side_counts),
                "total_T_rows": self.total_t_rows,
                "total_F_rows": self.total_f_rows,
                "unknown_side_T_rows": self.unknown_side_t_rows,
            },
            "timestamp_report": {
                "min_ts_event": timestamp_ns_to_iso(self.min_ts_event_ns),
                "max_ts_event": timestamp_ns_to_iso(self.max_ts_event_ns),
                "invalid_ts_event": self.invalid_row_counts.get("invalid_ts_event", 0),
                "invalid_ts_recv": self.invalid_row_counts.get("invalid_ts_recv", 0),
                "ordering_anomalies": self.ordering_anomalies,
                "causal_order": ["ts_event", "sequence", "source_row_number"],
            },
            "session_report": {
                "rows_per_session": dict(self.rows_per_session),
                "partial_session_warnings": partial_sessions,
                "exchange_timezone": config.exchange_timezone,
                "session_start": config.session_start,
                "session_end": config.session_end,
                "rth_start": config.rth_start,
                "rth_end": config.rth_end,
            },
            "trade_volume_report": {
                "total_T_rows": self.total_t_rows,
                "valid_T_rows": self.valid_t_rows,
                "sum_size_for_valid_T_rows": self.sum_t_size,
                "sum_output_trade_size": self.output_total_size,
                "sum_signed_volume": self.sum_signed_volume,
                "output_row_count": self.output_row_count,
                "min_price": self.min_price,
                "max_price": self.max_price,
                "min_size": self.min_size,
                "max_size": self.max_size,
                "rows_per_symbol": dict(self.rows_per_symbol),
            },
            "tick_size_report": {
                "tick_size": str(config.tick_size),
                "invalid_tick_prices": self.invalid_tick_prices,
            },
            "duplicate_report": {
                "duplicate_candidates": self.duplicate_candidates,
                "ordering_anomalies": self.ordering_anomalies,
            },
        }

    def _update_min_max_timestamp(self, ts_event: pa.Array) -> None:
        values = [value for value in timestamp_array_to_ns(ts_event) if value is not None]
        if not values:
            return
        batch_min = min(values)
        batch_max = max(values)
        self.min_ts_event_ns = batch_min if self.min_ts_event_ns is None else min(self.min_ts_event_ns, batch_min)
        self.max_ts_event_ns = batch_max if self.max_ts_event_ns is None else max(self.max_ts_event_ns, batch_max)

    def _update_min_max_price(self, prices: pa.ChunkedArray) -> None:
        values = [float(value) for value in prices.to_pylist() if value is not None]
        if not values:
            return
        self.min_price = min(values) if self.min_price is None else min(self.min_price, min(values))
        self.max_price = max(values) if self.max_price is None else max(self.max_price, max(values))

    def _update_min_max_size(self, sizes: pa.ChunkedArray) -> None:
        values = [int(value) for value in sizes.to_pylist() if value is not None]
        if not values:
            return
        self.min_size = min(values) if self.min_size is None else min(self.min_size, min(values))
        self.max_size = max(values) if self.max_size is None else max(self.max_size, max(values))

    def _update_ordering(
        self,
        ts_event: pa.Array,
        sequence: pa.ChunkedArray,
        source_row_number: pa.ChunkedArray,
    ) -> None:
        ts_values = timestamp_array_to_ns(ts_event)
        seq_values = sequence.to_pylist()
        source_values = source_row_number.to_pylist()
        for ts_ns, seq, source in zip(ts_values, seq_values, source_values, strict=True):
            if ts_ns is None or seq is None or source is None:
                continue
            prefix = (int(ts_ns), int(seq))
            key = (int(ts_ns), int(seq), int(source))
            if self.last_duplicate_prefix == prefix:
                self.duplicate_candidates += 1
            if self.last_order_key is not None and key < self.last_order_key:
                self.ordering_anomalies += 1
            self.last_duplicate_prefix = prefix
            self.last_order_key = key

    def _partial_session_warnings(self, config: Phase1Config) -> list[dict[str, Any]]:
        if not self.session_coverage:
            return []
        sessionizer = CMESessionizer(config)
        session_items = sorted(self.session_coverage.items())
        first_id = session_items[0][0]
        last_id = session_items[-1][0]
        tolerance_ns = config.partial_session_tolerance_minutes * 60 * 1_000_000_000
        warnings: list[dict[str, Any]] = []
        for session_id, coverage in session_items:
            trading_date = session_id.removeprefix("CME_EQ_FUT_")
            bounds = sessionizer.session_bounds_utc_ns(trading_date)
            starts_late = coverage.min_ts_ns is not None and coverage.min_ts_ns > bounds.open_ns + tolerance_ns
            ends_early = coverage.max_ts_ns is not None and coverage.max_ts_ns < bounds.close_ns - tolerance_ns
            is_edge = session_id in {first_id, last_id}
            if is_edge and (starts_late or ends_early):
                warnings.append(
                    {
                        "session_id": session_id,
                        "rows": coverage.rows,
                        "observed_min": timestamp_ns_to_iso(coverage.min_ts_ns),
                        "observed_max": timestamp_ns_to_iso(coverage.max_ts_ns),
                        "expected_open": timestamp_ns_to_iso(bounds.open_ns),
                        "expected_close": timestamp_ns_to_iso(bounds.close_ns),
                        "potentially_partial": True,
                    }
                )
        return warnings


def write_reports(
    artifact_root: Path,
    reports: dict[str, dict[str, Any]],
    *,
    summary_extra: dict[str, Any] | None = None,
) -> None:
    """Write JSON and Markdown audit reports."""

    artifact_root.mkdir(parents=True, exist_ok=True)
    for name, payload in reports.items():
        _write_json(artifact_root / f"{name}.json", payload)
        _write_markdown(artifact_root / f"{name}.md", name, payload)
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "reports": sorted(reports),
        **(summary_extra or {}),
    }
    _write_markdown(artifact_root / "phase1_summary.md", "phase1_summary", summary)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [f"# {title.replace('_', ' ').title()}", ""]
    for key, value in payload.items():
        if isinstance(value, dict):
            lines.append(f"## {key}")
            if value:
                lines.extend(f"- `{item_key}`: {item_value}" for item_key, item_value in sorted(value.items()))
            else:
                lines.append("- none")
            lines.append("")
        elif isinstance(value, list):
            lines.append(f"## {key}")
            if value:
                for item in value:
                    lines.append(f"- {item}")
            else:
                lines.append("- none")
            lines.append("")
        else:
            lines.append(f"- `{key}`: {value}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _sum_int(array: pa.ChunkedArray) -> int:
    return int(pc.sum(array).as_py() or 0)


def _true_count(mask: pa.ChunkedArray | pa.Array) -> int:
    return int(pc.sum(mask.cast(pa.int64())).as_py() or 0)
