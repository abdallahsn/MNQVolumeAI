"""Phase 1 MBO audit and canonical trade-tape extraction."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows fallback
    resource = None  # type: ignore[assignment]
import sys
import time

import pyarrow as pa
import pyarrow.compute as pc

from mnq_ai.config import Phase1Config
from mnq_ai.constants import ACTION_DOMAIN, FILL_ACTION, SIDE_DOMAIN, TRADE_ACTION
from mnq_ai.data.manifests import create_phase1_manifest, write_manifest
from mnq_ai.data.mbo_reader import MBOParquetReader
from mnq_ai.data.partition_writer import PartitionedTradeTapeWriter, QuarantineWriter
from mnq_ai.data.quality_audit import AuditAccumulator, write_reports
from mnq_ai.data.schemas import (
    QUARANTINE_SCHEMA,
    TRADE_TAPE_SCHEMA,
    parse_timestamp_array,
    schema_report,
    timestamp_array_to_ns,
    timestamp_ns_to_iso,
    validate_required_columns,
)
from mnq_ai.data.sessionizer import CMESessionizer
from mnq_ai.exceptions import DataValidationError, OutputValidationError

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Phase1RunResult:
    """Result summary returned by audit and build jobs."""

    manifest_path: Path
    reports_dir: Path
    output_root: Path | None
    rows_processed: int
    output_rows: int
    elapsed_seconds: float
    peak_rss_mb: float


class Phase1TradeExtractor:
    """Audit Databento MBO data and extract action-T trades only."""

    def __init__(self, config: Phase1Config) -> None:
        self.config = config.validated()
        self.sessionizer = CMESessionizer(self.config)

    def audit_mbo(self, input_path: Path, artifact_root: Path) -> Phase1RunResult:
        """Run schema and data-quality audits without writing a trade tape."""

        return self._run(input_path=input_path, output_root=None, artifact_root=artifact_root)

    def build_trade_tape(
        self,
        input_path: Path,
        output_root: Path,
        artifact_root: Path,
    ) -> Phase1RunResult:
        """Build the canonical Phase 1 trade tape."""

        return self._run(input_path=input_path, output_root=output_root, artifact_root=artifact_root)

    def _run(
        self,
        *,
        input_path: Path,
        output_root: Path | None,
        artifact_root: Path,
    ) -> Phase1RunResult:
        start_time = time.perf_counter()
        artifact_root.mkdir(parents=True, exist_ok=True)
        reader = MBOParquetReader(input_path)
        validate_required_columns(reader.schema)
        schema_payload = schema_report(reader.schema)
        audit = AuditAccumulator()
        writer = PartitionedTradeTapeWriter(output_root, self.config) if output_root is not None else None
        if writer is not None:
            writer.prepare()
        quarantine = QuarantineWriter(artifact_root, self.config.quarantine_sample_limit)
        source_start = 0
        try:
            for batch_index, batch in enumerate(
                reader.iter_batches(batch_size=self.config.batch_size),
                start=1,
            ):
                table = self._prepare_batch(pa.Table.from_batches([batch]), source_start)
                source_start += table.num_rows
                output = self._process_batch(table, audit, quarantine)
                if writer is not None and output.num_rows:
                    writer.write_batch(output)
                if batch_index == 1 or batch_index % 20 == 0:
                    LOGGER.info(
                        "processed batch=%s input_rows=%s output_rows=%s peak_rss_mb=%.1f",
                        batch_index,
                        audit.total_input_rows,
                        audit.output_row_count,
                        _peak_rss_mb(),
                    )
        finally:
            quarantine.close()

        if self.config.invalid_row_policy == "fail":
            self._fail_closed_gate(audit)

        if writer is not None:
            assert output_root is not None
            self._check_build_invariants(audit)
            file_count, byte_size = writer.finalize()
            audit.observe_output_layout(file_count, byte_size)
            manifest = create_phase1_manifest(
                input_path=input_path,
                output_root=output_root,
                artifact_root=artifact_root,
                config=self.config,
                audit=audit,
            )
        else:
            manifest = self._audit_only_manifest(input_path, artifact_root, audit)

        reports = audit.reports(schema_payload, self.config)
        manifest_path = write_manifest(artifact_root, manifest)
        reports["phase1_manifest"] = manifest
        write_reports(
            artifact_root,
            reports,
            summary_extra={
                "rows_processed": audit.total_input_rows,
                "output_rows": audit.output_row_count,
                "elapsed_seconds": round(time.perf_counter() - start_time, 6),
                "peak_rss_mb": round(_peak_rss_mb(), 3),
            },
        )
        return Phase1RunResult(
            manifest_path=manifest_path,
            reports_dir=artifact_root,
            output_root=output_root,
            rows_processed=audit.total_input_rows,
            output_rows=audit.output_row_count,
            elapsed_seconds=time.perf_counter() - start_time,
            peak_rss_mb=_peak_rss_mb(),
        )

    def _prepare_batch(self, table: pa.Table, source_start: int) -> pa.Table:
        source_ids = pa.array(range(source_start, source_start + table.num_rows), type=pa.uint64())
        return table.append_column("source_row_number", source_ids)

    def _process_batch(
        self,
        table: pa.Table,
        audit: AuditAccumulator,
        quarantine: QuarantineWriter,
    ) -> pa.Table:
        ts_event = parse_timestamp_array(table["ts_event"])
        ts_recv = parse_timestamp_array(table["ts_recv"])
        table = table.set_column(table.schema.get_field_index("ts_event"), "ts_event", ts_event.values)
        table = table.set_column(table.schema.get_field_index("ts_recv"), "ts_recv", ts_recv.values)
        audit.observe_input(table, ts_event=ts_event, ts_recv=ts_recv)

        masks = self._build_masks(table, ts_event.invalid_mask, ts_recv.invalid_mask)
        reason_counts = Counter(
            {
                name: _count_mask(mask)
                for name, mask in masks.reason_masks.items()
                if _count_mask(mask) > 0
            }
        )
        invalid_trade_mask = masks.invalid_trade_mask
        quarantined = 0
        if _count_mask(invalid_trade_mask):
            invalid_table = self._quarantine_table(table, invalid_trade_mask, masks.reason_masks)
            if self.config.invalid_row_policy == "fail":
                raise DataValidationError(f"Invalid trade rows: {dict(reason_counts)}")
            if self.config.invalid_row_policy == "quarantine":
                quarantined = quarantine.write(invalid_table)
        audit.observe_invalid(reason_counts, quarantined_rows=quarantined)

        valid_trade_table = table.filter(masks.valid_trade_mask)
        audit.observe_trade_candidates(valid_trade_table)
        output = self._canonical_trade_table(valid_trade_table)
        audit.observe_output(output)
        return output

    def _build_masks(
        self,
        table: pa.Table,
        ts_event_invalid: pa.Array,
        ts_recv_invalid: pa.Array,
    ) -> _BatchMasks:
        action = _array(table, "action")
        side = _array(table, "side")
        price = _array(table, "price")
        size = _array(table, "size")
        sequence = _array(table, "sequence")
        symbol = _array(table, "symbol")

        action_t = _eq(action, TRADE_ACTION)
        symbol_scope = _symbol_scope(symbol, self.config.symbol_filters)
        trade_scope = _and(action_t, symbol_scope)
        valid_action = _is_in(action, ACTION_DOMAIN)
        valid_side = _is_in(side, SIDE_DOMAIN)
        valid_price = _and(_finite_positive(price), _not_null(price))
        valid_size = _and(_gt(size, 0), _not_null(size))
        valid_sequence = _not_null(sequence)
        valid_symbol = _and(_not_null(symbol), _not(_eq(symbol, "")))
        valid_tick = _valid_tick(price, self.config.tick_size)
        valid_ts_event = _not(ts_event_invalid)
        valid_ts_recv = _not(ts_recv_invalid)
        domain_invalid = _or(_not(valid_action), _not(valid_side))

        reason_masks = {
            "invalid_action": _not(valid_action),
            "invalid_side": _not(valid_side),
            "invalid_ts_event": _not(valid_ts_event),
            "invalid_ts_recv": _not(valid_ts_recv),
            "invalid_sequence": _not(valid_sequence),
            "invalid_price": _and(trade_scope, _not(valid_price)),
            "invalid_size": _and(trade_scope, _not(valid_size)),
            "invalid_symbol": _and(trade_scope, _not(valid_symbol)),
            "invalid_tick_price": _and(trade_scope, _not(valid_tick)),
        }
        valid_trade = trade_scope
        for mask in (
            valid_action,
            valid_side,
            valid_ts_event,
            valid_ts_recv,
            valid_sequence,
            valid_price,
            valid_size,
            valid_symbol,
            valid_tick,
        ):
            valid_trade = _and(valid_trade, mask)
        invalid_trade = _and(trade_scope, _not(valid_trade))
        if self.config.invalid_row_policy == "fail" and _count_mask(domain_invalid):
            raise DataValidationError("Unknown action or side value in input batch")
        return _BatchMasks(valid_trade, invalid_trade, reason_masks)

    def _canonical_trade_table(self, table: pa.Table) -> pa.Table:
        if table.num_rows == 0:
            return pa.Table.from_arrays([pa.array([], type=field.type) for field in TRADE_TAPE_SCHEMA], schema=TRADE_TAPE_SCHEMA)
        side = _array(table, "side")
        size = _array(table, "size").cast(pa.int64())
        signed_volume = pc.if_else(
            _eq(side, "B"),
            size,
            pc.if_else(_eq(side, "A"), pc.multiply(size, -1), pa.scalar(0, type=pa.int64())),
        )
        unknown_aggressor = _eq(side, "N")
        sessions = self.sessionizer.assign(timestamp_array_to_ns(table["ts_event"]))
        arrays = [
            _array(table, "ts_event"),
            _array(table, "ts_recv"),
            _array(table, "sequence").cast(pa.uint64()),
            _array(table, "publisher_id").cast(pa.int64()),
            _array(table, "instrument_id").cast(pa.int64()),
            _array(table, "symbol").cast(pa.string()),
            _array(table, "price").cast(pa.float64()),
            size,
            side.cast(pa.string()),
            signed_volume.cast(pa.int64()),
            unknown_aggressor,
            pa.array(sessions.trading_date, type=pa.string()),
            pa.array(sessions.session_id, type=pa.string()),
            pa.array(sessions.session_segment, type=pa.string()),
            pa.array(sessions.is_rth, type=pa.bool_()),
            _array(table, "source_row_number").cast(pa.uint64()),
        ]
        return pa.Table.from_arrays(arrays, schema=TRADE_TAPE_SCHEMA)

    def _quarantine_table(
        self,
        table: pa.Table,
        invalid_mask: pa.Array,
        reason_masks: dict[str, pa.Array],
    ) -> pa.Table:
        invalid = table.filter(invalid_mask)
        reasons_by_source: dict[int, list[str]] = {}
        source_values = _array(table, "source_row_number").to_pylist()
        invalid_sources = set(_array(invalid, "source_row_number").to_pylist())
        for reason, mask in reason_masks.items():
            values = mask.to_pylist()
            for source, is_bad in zip(source_values, values, strict=True):
                if source in invalid_sources and is_bad:
                    reasons_by_source.setdefault(int(source), []).append(reason)
        columns = {name: _array(invalid, name).to_pylist() for name in invalid.column_names if name not in {"ts_event", "ts_recv"}}
        ts_event_values = [timestamp_ns_to_iso(value) for value in timestamp_array_to_ns(invalid["ts_event"])]
        ts_recv_values = [timestamp_ns_to_iso(value) for value in timestamp_array_to_ns(invalid["ts_recv"])]
        rows: list[dict[str, object]] = []
        for index in range(invalid.num_rows):
            source = int(columns["source_row_number"][index])
            rows.append(
                {
                    "rejection_reason": ",".join(sorted(reasons_by_source.get(source, ["invalid_trade"]))),
                    "source_row_number": source,
                    "ts_event": ts_event_values[index],
                    "ts_recv": ts_recv_values[index],
                    "sequence": columns["sequence"][index],
                    "publisher_id": columns["publisher_id"][index],
                    "instrument_id": columns["instrument_id"][index],
                    "symbol": columns["symbol"][index],
                    "action": columns["action"][index],
                    "side": columns["side"][index],
                    "price": columns["price"][index],
                    "size": columns["size"][index],
                }
            )
        return pa.Table.from_pylist(rows, schema=QUARANTINE_SCHEMA)

    def _fail_closed_gate(self, audit: AuditAccumulator) -> None:
        critical = {
            key: value
            for key, value in audit.invalid_row_counts.items()
            if value
            and key
            in {
                "invalid_action",
                "invalid_side",
                "invalid_ts_event",
                "invalid_ts_recv",
                "invalid_sequence",
                "invalid_price",
                "invalid_size",
                "invalid_symbol",
                "invalid_tick_price",
            }
        }
        if critical:
            raise DataValidationError(f"Fail-closed audit violations: {critical}")
        if audit.ordering_anomalies:
            raise DataValidationError(f"Causal ordering anomalies: {audit.ordering_anomalies}")

    def _check_build_invariants(self, audit: AuditAccumulator) -> None:
        if audit.output_row_count != audit.valid_t_rows:
            raise OutputValidationError("Output row count does not equal valid action-T row count")
        if audit.output_total_size != audit.sum_t_size:
            raise OutputValidationError("Output size does not reconcile to valid action-T size")
        if audit.total_f_rows and audit.output_row_count > audit.valid_t_rows:
            raise OutputValidationError(f"{FILL_ACTION} rows may have leaked into output")

    def _audit_only_manifest(
        self,
        input_path: Path,
        artifact_root: Path,
        audit: AuditAccumulator,
    ) -> dict[str, object]:
        return {
            "phase": "1",
            "status": "audit-only",
            "input_path": str(input_path),
            "artifact_root": str(artifact_root),
            "input_rows": audit.total_input_rows,
            "valid_T_rows": audit.valid_t_rows,
            "total_F_rows": audit.total_f_rows,
            "output_row_count": 0,
            "sum_size_for_valid_T_rows": audit.sum_t_size,
            "sum_output_trade_size": 0,
            "sum_signed_volume": 0,
            "ordering_anomalies": audit.ordering_anomalies,
            "invalid_row_counts": dict(audit.invalid_row_counts),
        }


@dataclass(frozen=True)
class _BatchMasks:
    valid_trade_mask: pa.Array
    invalid_trade_mask: pa.Array
    reason_masks: dict[str, pa.Array]


def _array(table: pa.Table, name: str) -> pa.Array:
    return table[name].combine_chunks()


def _eq(array: pa.Array, value: object) -> pa.Array:
    return pc.fill_null(pc.equal(array, pa.scalar(value)), False)


def _gt(array: pa.Array, value: int | float) -> pa.Array:
    return pc.fill_null(pc.greater(array, pa.scalar(value)), False)


def _not_null(array: pa.Array) -> pa.Array:
    return pc.invert(pc.is_null(array))


def _is_in(array: pa.Array, values: frozenset[str]) -> pa.Array:
    return pc.fill_null(pc.is_in(array, value_set=pa.array(sorted(values), type=pa.string())), False)


def _and(left: pa.Array, right: pa.Array) -> pa.Array:
    return pc.and_kleene(left, right).cast(pa.bool_())


def _or(left: pa.Array, right: pa.Array) -> pa.Array:
    return pc.or_kleene(left, right).cast(pa.bool_())


def _not(mask: pa.Array) -> pa.Array:
    return pc.invert(pc.fill_null(mask, False))


def _finite_positive(array: pa.Array) -> pa.Array:
    return _and(pc.fill_null(pc.is_finite(array), False), _gt(array, 0))


def _valid_tick(price: pa.Array, tick_size: Decimal) -> pa.Array:
    scale = float(Decimal("1") / tick_size)
    scaled = pc.multiply(price, pa.scalar(scale))
    rounded = pc.round(scaled, ndigits=0)
    delta = pc.abs(pc.subtract(scaled, rounded))
    return _and(_finite_positive(price), pc.less_equal(delta, pa.scalar(1e-9)))


def _symbol_scope(symbol: pa.Array, filters: tuple[str, ...]) -> pa.Array:
    if not filters:
        return pa.array([True] * len(symbol), type=pa.bool_())
    return pc.fill_null(pc.is_in(symbol, value_set=pa.array(list(filters), type=pa.string())), False)


def _count_mask(mask: pa.Array) -> int:
    return int(pc.sum(mask.cast(pa.int64())).as_py() or 0)


def _peak_rss_mb() -> float:
    if resource is None:
        return 0.0
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return usage / (1024 * 1024)
    return usage / 1024
