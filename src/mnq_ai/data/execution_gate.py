"""Phase 2 execution labels and fail-closed gate artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from mnq_ai.config import Phase1Config
from mnq_ai.data.schemas import TIMESTAMP_NS_UTC, file_size_bytes, timestamp_array_to_ns
from mnq_ai.data.setup_candidates import SETUP_CANDIDATE_SCHEMA
from mnq_ai.exceptions import ConfigurationError, OutputValidationError, SchemaValidationError

TRADE_LABEL_INPUT_COLUMNS = [
    "ts_event",
    "sequence",
    "symbol",
    "session_id",
    "price",
    "source_row_number",
]

PHASE2_LABEL_SCHEMA = pa.schema(
    [
        ("setup_id", pa.string()),
        ("ts_event", TIMESTAMP_NS_UTC),
        ("symbol", pa.string()),
        ("cme_session_id", pa.string()),
        ("setup_type", pa.string()),
        ("entry_side", pa.string()),
        ("entry_timestamp", TIMESTAMP_NS_UTC),
        ("earliest_entry_timestamp", TIMESTAMP_NS_UTC),
        ("max_exit_timestamp", TIMESTAMP_NS_UTC),
        ("entry_price", pa.float64()),
        ("entry_fill_price", pa.float64()),
        ("stop_price", pa.float64()),
        ("target_price", pa.float64()),
        ("exit_timestamp", TIMESTAMP_NS_UTC),
        ("exit_trade_price", pa.float64()),
        ("exit_fill_price", pa.float64()),
        ("exit_reason", pa.string()),
        ("success", pa.bool_()),
        ("planned_risk_points", pa.float64()),
        ("gross_points", pa.float64()),
        ("gross_r", pa.float64()),
        ("net_points", pa.float64()),
        ("net_r", pa.float64()),
        ("commission_per_side", pa.float64()),
        ("point_value", pa.float64()),
        ("entry_slippage_ticks", pa.int64()),
        ("stop_slippage_ticks", pa.int64()),
        ("time_exit_slippage_ticks", pa.int64()),
        ("entry_latency_seconds", pa.int64()),
        ("event_count", pa.int64()),
        ("label_available_timestamp", TIMESTAMP_NS_UTC),
        ("ambiguity_policy", pa.string()),
        ("reason_codes", pa.list_(pa.string())),
    ]
)


@dataclass(frozen=True)
class Phase2ExecutionConfig:
    """Deterministic fill assumptions for Phase 2 labeling."""

    tick_size: Decimal
    commission_per_side: Decimal = Decimal("0")
    entry_slippage_ticks: int = 0
    stop_slippage_ticks: int = 0
    time_exit_slippage_ticks: int = 0
    point_value: Decimal = Decimal("2")
    entry_latency_seconds: int = 0
    ambiguity_policy: str = "event_order_first_barrier"

    def validated(self) -> Phase2ExecutionConfig:
        """Fail closed on invalid fill assumptions."""

        if self.tick_size <= 0:
            raise ConfigurationError("tick_size must be positive")
        if self.commission_per_side < 0:
            raise ConfigurationError("commission_per_side cannot be negative")
        if self.entry_slippage_ticks < 0:
            raise ConfigurationError("entry_slippage_ticks cannot be negative")
        if self.stop_slippage_ticks < 0:
            raise ConfigurationError("stop_slippage_ticks cannot be negative")
        if self.time_exit_slippage_ticks < 0:
            raise ConfigurationError("time_exit_slippage_ticks cannot be negative")
        if self.point_value <= 0:
            raise ConfigurationError("point_value must be positive")
        if self.entry_latency_seconds < 0:
            raise ConfigurationError("entry_latency_seconds cannot be negative")
        if self.ambiguity_policy != "event_order_first_barrier":
            raise ConfigurationError("ambiguity_policy must be event_order_first_barrier")
        return self


@dataclass(frozen=True)
class Phase2LabelRunResult:
    """Result summary for Phase 2 execution labeling."""

    manifest_path: Path
    output_root: Path
    artifact_root: Path
    candidate_count: int
    label_count: int
    gate_recommendation: str
    elapsed_seconds: float


@dataclass(frozen=True)
class _TradeEvent:
    ts_ns: int
    sequence: int
    source_row_number: int
    price: Decimal

    @property
    def timestamp(self) -> datetime:
        return _datetime_from_ns(self.ts_ns)


def build_phase2_labels(
    *,
    trade_tape_path: Path,
    setup_candidates_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    execution_config: Phase2ExecutionConfig,
) -> Phase2LabelRunResult:
    """Build first-barrier execution labels from setup candidates and trade tape."""

    start = time.perf_counter()
    config = config.validated()
    execution_config = execution_config.validated()
    output_root = Path(output_root)
    artifact_root = Path(artifact_root)
    staging_root = _prepare_output(output_root, config)
    artifact_root.mkdir(parents=True, exist_ok=True)

    candidates = _read_setup_candidates(setup_candidates_path)
    trade_tape = _trade_tape_dataset(trade_tape_path)
    labels = [_label_candidate(candidate, trade_tape, config, execution_config) for candidate in candidates]

    table = pa.Table.from_pylist(labels, schema=PHASE2_LABEL_SCHEMA)
    pq.write_table(table, staging_root / "setup_labels.parquet", compression=_compression(config))
    _finalize_output(staging_root, output_root)

    elapsed_seconds = round(time.perf_counter() - start, 6)
    manifest = _manifest(
        trade_tape_path=trade_tape_path,
        setup_candidates_path=setup_candidates_path,
        output_root=output_root,
        artifact_root=artifact_root,
        config=config,
        execution_config=execution_config,
        candidate_count=len(candidates),
        labels=labels,
        elapsed_seconds=elapsed_seconds,
    )
    manifest_path = artifact_root / "phase2_gate_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _write_summary(artifact_root / "phase2_gate_summary.md", manifest)
    return Phase2LabelRunResult(
        manifest_path=manifest_path,
        output_root=output_root,
        artifact_root=artifact_root,
        candidate_count=len(candidates),
        label_count=len(labels),
        gate_recommendation=str(manifest["gate_recommendation"]),
        elapsed_seconds=time.perf_counter() - start,
    )


def _label_candidate(
    candidate: dict[str, Any],
    trade_tape: ds.Dataset,
    config: Phase1Config,
    execution_config: Phase2ExecutionConfig,
) -> dict[str, Any]:
    symbol = _required_str(candidate, "symbol")
    session_id = _required_str(candidate, "cme_session_id")
    entry_side = _required_str(candidate, "entry_side")
    entry_timestamp = _required_datetime(candidate, "entry_timestamp")
    max_holding_seconds = _required_int(candidate, "max_holding_seconds")
    earliest_entry_timestamp = entry_timestamp + timedelta(seconds=execution_config.entry_latency_seconds)
    max_exit_timestamp = entry_timestamp + timedelta(seconds=max_holding_seconds)
    base = _base_label(candidate, earliest_entry_timestamp, max_exit_timestamp, execution_config)

    if entry_side not in {"LONG", "SHORT"}:
        return {**base, **_failed_metrics("INVALID_ENTRY_SIDE", earliest_entry_timestamp)}

    entry_price = _required_decimal(candidate, "entry_price")
    stop_price = _required_decimal(candidate, "stop_price")
    target_price = _required_decimal(candidate, "target_1")
    planned_risk = abs(entry_price - stop_price)
    if planned_risk <= 0:
        return {**base, **_failed_metrics("INVALID_RISK", earliest_entry_timestamp)}

    events = _load_events(
        trade_tape,
        symbol=symbol,
        session_id=session_id,
        start=earliest_entry_timestamp,
        end=max_exit_timestamp,
        batch_size=config.batch_size,
    )
    if not events:
        return {
            **base,
            **_priced_metrics(
                entry_side=entry_side,
                entry_price=entry_price,
                stop_price=stop_price,
                target_price=target_price,
                planned_risk=planned_risk,
                exit_reason="NO_FUTURE_DATA",
                exit_event=None,
                exit_trade_price=None,
                exit_fill_price=None,
                event_count=0,
                label_available_timestamp=max_exit_timestamp,
                execution_config=execution_config,
            ),
        }

    for event in events:
        exit_reason = _barrier_reason(
            entry_side=entry_side,
            price=event.price,
            stop_price=stop_price,
            target_price=target_price,
        )
        if exit_reason is None:
            continue
        exit_fill_price = _barrier_fill_price(
            entry_side=entry_side,
            exit_reason=exit_reason,
            stop_price=stop_price,
            target_price=target_price,
            trade_price=event.price,
            execution_config=execution_config,
        )
        return {
            **base,
            **_priced_metrics(
                entry_side=entry_side,
                entry_price=entry_price,
                stop_price=stop_price,
                target_price=target_price,
                planned_risk=planned_risk,
                exit_reason=exit_reason,
                exit_event=event,
                exit_trade_price=event.price,
                exit_fill_price=exit_fill_price,
                event_count=len(events),
                label_available_timestamp=event.timestamp,
                execution_config=execution_config,
            ),
        }

    last_event = events[-1]
    time_exit_fill_price = _time_exit_fill_price(entry_side, last_event.price, execution_config)
    return {
        **base,
        **_priced_metrics(
            entry_side=entry_side,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            planned_risk=planned_risk,
            exit_reason="MAX_HOLD",
            exit_event=last_event,
            exit_trade_price=last_event.price,
            exit_fill_price=time_exit_fill_price,
            event_count=len(events),
            label_available_timestamp=last_event.timestamp,
            execution_config=execution_config,
        ),
    }


def _read_setup_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SchemaValidationError(f"Setup candidates path does not exist: {path}")
    dataset = ds.dataset(path, format="parquet", partitioning="hive")
    missing = sorted(set(SETUP_CANDIDATE_SCHEMA.names) - set(dataset.schema.names))
    if missing:
        raise SchemaValidationError(f"Setup candidates missing columns: {', '.join(missing)}")
    table = dataset.to_table(columns=SETUP_CANDIDATE_SCHEMA.names)
    rows = table.to_pylist()
    return sorted(
        rows,
        key=lambda row: (
            _required_datetime(row, "entry_timestamp"),
            _required_str(row, "setup_id"),
        ),
    )


def _trade_tape_dataset(path: Path) -> ds.Dataset:
    if not path.exists():
        raise SchemaValidationError(f"Trade tape path does not exist: {path}")
    dataset = ds.dataset(path, format="parquet", partitioning="hive")
    missing = sorted(set(TRADE_LABEL_INPUT_COLUMNS) - set(dataset.schema.names))
    if missing:
        raise SchemaValidationError(f"Trade tape missing columns for Phase 2 labels: {', '.join(missing)}")
    return dataset


def _load_events(
    dataset: ds.Dataset,
    *,
    symbol: str,
    session_id: str,
    start: datetime,
    end: datetime,
    batch_size: int,
) -> list[_TradeEvent]:
    if end < start:
        return []
    filter_expr = (
        (ds.field("symbol") == symbol)
        & (ds.field("session_id") == session_id)
        & (ds.field("ts_event") >= pa.scalar(start, type=TIMESTAMP_NS_UTC))
        & (ds.field("ts_event") <= pa.scalar(end, type=TIMESTAMP_NS_UTC))
    )
    events: list[_TradeEvent] = []
    scanner = dataset.scanner(columns=TRADE_LABEL_INPUT_COLUMNS, filter=filter_expr, batch_size=batch_size)
    for batch in scanner.to_batches():
        table = pa.Table.from_batches([batch])
        timestamps = timestamp_array_to_ns(table["ts_event"])
        sequences = table["sequence"].to_pylist()
        prices = table["price"].to_pylist()
        source_rows = table["source_row_number"].to_pylist()
        for ts_ns, sequence, price, source_row in zip(timestamps, sequences, prices, source_rows, strict=True):
            if ts_ns is None or sequence is None or price is None or source_row is None:
                raise OutputValidationError("Trade tape contains null values in required Phase 2 label columns")
            events.append(
                _TradeEvent(
                    ts_ns=int(ts_ns),
                    sequence=int(sequence),
                    source_row_number=int(source_row),
                    price=Decimal(str(float(price))),
                )
            )
    return sorted(events, key=lambda event: (event.ts_ns, event.sequence, event.source_row_number))


def _base_label(
    candidate: dict[str, Any],
    earliest_entry_timestamp: datetime,
    max_exit_timestamp: datetime,
    execution_config: Phase2ExecutionConfig,
) -> dict[str, Any]:
    return {
        "setup_id": _required_str(candidate, "setup_id"),
        "ts_event": _required_datetime(candidate, "ts_event"),
        "symbol": _required_str(candidate, "symbol"),
        "cme_session_id": _required_str(candidate, "cme_session_id"),
        "setup_type": _required_str(candidate, "setup_type"),
        "entry_side": _required_str(candidate, "entry_side"),
        "entry_timestamp": _required_datetime(candidate, "entry_timestamp"),
        "earliest_entry_timestamp": earliest_entry_timestamp,
        "max_exit_timestamp": max_exit_timestamp,
        "entry_price": _float(_required_decimal(candidate, "entry_price")),
        "entry_fill_price": None,
        "stop_price": _float(_required_decimal(candidate, "stop_price")),
        "target_price": _float(_required_decimal(candidate, "target_1")),
        "exit_timestamp": None,
        "exit_trade_price": None,
        "exit_fill_price": None,
        "exit_reason": "UNLABELED",
        "success": False,
        "planned_risk_points": None,
        "gross_points": None,
        "gross_r": None,
        "net_points": None,
        "net_r": None,
        "commission_per_side": _float(execution_config.commission_per_side),
        "point_value": _float(execution_config.point_value),
        "entry_slippage_ticks": execution_config.entry_slippage_ticks,
        "stop_slippage_ticks": execution_config.stop_slippage_ticks,
        "time_exit_slippage_ticks": execution_config.time_exit_slippage_ticks,
        "entry_latency_seconds": execution_config.entry_latency_seconds,
        "event_count": 0,
        "label_available_timestamp": earliest_entry_timestamp,
        "ambiguity_policy": execution_config.ambiguity_policy,
        "reason_codes": list(candidate.get("reason_codes") or []),
    }


def _failed_metrics(exit_reason: str, label_available_timestamp: datetime) -> dict[str, Any]:
    return {
        "exit_reason": exit_reason,
        "success": False,
        "label_available_timestamp": label_available_timestamp,
    }


def _priced_metrics(
    *,
    entry_side: str,
    entry_price: Decimal,
    stop_price: Decimal,
    target_price: Decimal,
    planned_risk: Decimal,
    exit_reason: str,
    exit_event: _TradeEvent | None,
    exit_trade_price: Decimal | None,
    exit_fill_price: Decimal | None,
    event_count: int,
    label_available_timestamp: datetime,
    execution_config: Phase2ExecutionConfig,
) -> dict[str, Any]:
    entry_fill_price = _entry_fill_price(entry_side, entry_price, execution_config)
    gross_points: Decimal | None = None
    gross_r: Decimal | None = None
    net_points: Decimal | None = None
    net_r: Decimal | None = None
    if exit_fill_price is not None:
        gross_points = exit_fill_price - entry_fill_price if entry_side == "LONG" else entry_fill_price - exit_fill_price
        gross_r = gross_points / planned_risk
        commission_points = (execution_config.commission_per_side * Decimal("2")) / execution_config.point_value
        net_points = gross_points - commission_points
        net_r = net_points / planned_risk

    return {
        "entry_fill_price": _float(entry_fill_price),
        "stop_price": _float(stop_price),
        "target_price": _float(target_price),
        "exit_timestamp": None if exit_event is None else exit_event.timestamp,
        "exit_trade_price": _float_or_none(exit_trade_price),
        "exit_fill_price": _float_or_none(exit_fill_price),
        "exit_reason": exit_reason,
        "success": exit_reason == "TARGET_1",
        "planned_risk_points": _float(planned_risk),
        "gross_points": _float_or_none(gross_points),
        "gross_r": _float_or_none(gross_r),
        "net_points": _float_or_none(net_points),
        "net_r": _float_or_none(net_r),
        "event_count": event_count,
        "label_available_timestamp": label_available_timestamp,
    }


def _barrier_reason(
    *,
    entry_side: str,
    price: Decimal,
    stop_price: Decimal,
    target_price: Decimal,
) -> str | None:
    if entry_side == "LONG":
        if price <= stop_price:
            return "STOP"
        if price >= target_price:
            return "TARGET_1"
        return None
    if price >= stop_price:
        return "STOP"
    if price <= target_price:
        return "TARGET_1"
    return None


def _entry_fill_price(
    entry_side: str,
    entry_price: Decimal,
    execution_config: Phase2ExecutionConfig,
) -> Decimal:
    slippage = Decimal(execution_config.entry_slippage_ticks) * execution_config.tick_size
    return entry_price + slippage if entry_side == "LONG" else entry_price - slippage


def _barrier_fill_price(
    *,
    entry_side: str,
    exit_reason: str,
    stop_price: Decimal,
    target_price: Decimal,
    trade_price: Decimal,
    execution_config: Phase2ExecutionConfig,
) -> Decimal:
    stop_slippage = Decimal(execution_config.stop_slippage_ticks) * execution_config.tick_size
    if exit_reason == "TARGET_1":
        return target_price
    if entry_side == "LONG":
        return min(stop_price, trade_price) - stop_slippage
    return max(stop_price, trade_price) + stop_slippage


def _time_exit_fill_price(
    entry_side: str,
    trade_price: Decimal,
    execution_config: Phase2ExecutionConfig,
) -> Decimal:
    slippage = Decimal(execution_config.time_exit_slippage_ticks) * execution_config.tick_size
    return trade_price - slippage if entry_side == "LONG" else trade_price + slippage


def _manifest(
    *,
    trade_tape_path: Path,
    setup_candidates_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    execution_config: Phase2ExecutionConfig,
    candidate_count: int,
    labels: list[dict[str, Any]],
    elapsed_seconds: float,
) -> dict[str, Any]:
    output_file = output_root / "setup_labels.parquet"
    reason_counts = Counter(str(label["exit_reason"]) for label in labels)
    payload: dict[str, Any] = {
        "phase": "2_execution_gate",
        "status": "complete",
        "gate_recommendation": "NO-GO",
        "generated_at": datetime.now(UTC).isoformat(),
        "trade_tape_path": str(trade_tape_path),
        "setup_candidates_path": str(setup_candidates_path),
        "output_root": str(output_root),
        "artifact_root": str(artifact_root),
        "input_columns": {
            "trade_tape": list(TRADE_LABEL_INPUT_COLUMNS),
            "setup_candidates": list(SETUP_CANDIDATE_SCHEMA.names),
        },
        "forbidden_inputs": [
            "resting_bid_ask_depth",
            "order_book_imbalance",
            "queue_position",
            "microprice",
            "depth_pressure",
            "cancellation_imbalance",
            "add_cancel_modify_pressure",
            "spoofing_indicators",
            "dom_direction_prediction",
        ],
        "candidate_count": candidate_count,
        "label_count": len(labels),
        "success_count": sum(1 for label in labels if label["success"]),
        "exit_reason_counts": dict(sorted(reason_counts.items())),
        "output_files": [{"path": output_file.name, "bytes": output_file.stat().st_size}],
        "trade_tape_byte_size": file_size_bytes(trade_tape_path),
        "setup_candidates_byte_size": file_size_bytes(setup_candidates_path),
        "output_byte_size": output_file.stat().st_size,
        "elapsed_seconds": elapsed_seconds,
        "config": {
            "batch_size": config.batch_size,
            "tick_size": str(config.tick_size),
            "compression": config.compression,
            "overwrite": config.overwrite,
        },
        "fill_model": {
            "entry_price_source": "setup_candidate_entry_price",
            "barrier_source": "executed_trade_tape_action_T_only",
            "ambiguity_policy": execution_config.ambiguity_policy,
            "commission_per_side": str(execution_config.commission_per_side),
            "entry_slippage_ticks": execution_config.entry_slippage_ticks,
            "stop_slippage_ticks": execution_config.stop_slippage_ticks,
            "time_exit_slippage_ticks": execution_config.time_exit_slippage_ticks,
            "entry_latency_seconds": execution_config.entry_latency_seconds,
            "point_value": str(execution_config.point_value),
        },
        "production_blockers": [
            "Current five-day fixture is for engineering validation only, not model validation.",
            "No walk-forward out-of-sample validation has been run.",
            "No live or paper-trading execution parity check has been run.",
            "No doubled-cost or stressed-slippage release gate has been run.",
            "Setup sample may be too small for statistical inference.",
        ],
    }
    payload["aggregate_checksum"] = _checksum(payload)
    return payload


def _write_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Phase2 Execution Gate Summary",
        "",
        f"- `generated_at`: {manifest['generated_at']}",
        f"- `gate_recommendation`: {manifest['gate_recommendation']}",
        f"- `candidate_count`: {manifest['candidate_count']}",
        f"- `label_count`: {manifest['label_count']}",
        f"- `success_count`: {manifest['success_count']}",
        f"- `output_root`: {manifest['output_root']}",
        f"- `elapsed_seconds`: {manifest['elapsed_seconds']}",
        "## exit_reason_counts",
    ]
    for reason, count in manifest["exit_reason_counts"].items():
        lines.append(f"- `{reason}`: {count}")
    lines.append("## production_blockers")
    for blocker in manifest["production_blockers"]:
        lines.append(f"- {blocker}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _prepare_output(output_root: Path, config: Phase1Config) -> Path:
    staging_root = output_root.parent / f".{output_root.name}.incomplete"
    if output_root.exists() and not config.overwrite:
        raise OutputValidationError(f"Output exists and overwrite=false: {output_root}")
    if staging_root.exists():
        if not config.overwrite:
            raise OutputValidationError(f"Staging output exists: {staging_root}")
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)
    return staging_root


def _finalize_output(staging_root: Path, output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging_root.rename(output_root)


def _compression(config: Phase1Config) -> str | None:
    return None if config.compression == "none" else config.compression


def _required_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None:
        raise SchemaValidationError(f"Setup candidate contains null {key}")
    return str(value)


def _required_int(row: dict[str, Any], key: str) -> int:
    value = row.get(key)
    if value is None:
        raise SchemaValidationError(f"Setup candidate contains null {key}")
    return int(value)


def _required_decimal(row: dict[str, Any], key: str) -> Decimal:
    value = row.get(key)
    if value is None:
        raise SchemaValidationError(f"Setup candidate contains null {key}")
    return Decimal(str(float(value)))


def _required_datetime(row: dict[str, Any], key: str) -> datetime:
    value = row.get(key)
    if not isinstance(value, datetime):
        raise SchemaValidationError(f"Setup candidate contains invalid {key}")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _datetime_from_ns(value: int) -> datetime:
    seconds, nanos = divmod(value, 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=nanos // 1_000)


def _float(value: Decimal) -> float:
    return float(value)


def _float_or_none(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _checksum(manifest: dict[str, Any]) -> str:
    stable = {key: value for key, value in manifest.items() if key not in {"generated_at", "aggregate_checksum"}}
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
