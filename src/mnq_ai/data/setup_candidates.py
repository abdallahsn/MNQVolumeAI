"""Build deterministic setup-candidate datasets from the canonical trade tape."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from mnq_ai.config import Phase1Config
from mnq_ai.data.schemas import TIMESTAMP_NS_UTC, file_size_bytes, timestamp_array_to_ns
from mnq_ai.exceptions import OutputValidationError, SchemaValidationError
from mnq_ai.setups.failed_fvg import Bar, FailedFVGConfig, FailedFVGSetupEngine, SetupCandidate
from mnq_ai.setups.qep_technical import QEPTechnicalConfig, QEPTechnicalSetupEngine

FAILED_FVG_INPUT_COLUMNS = [
    "ts_event",
    "sequence",
    "symbol",
    "price",
    "size",
    "session_id",
    "source_row_number",
]

SETUP_CANDIDATE_SCHEMA = pa.schema(
    [
        ("setup_id", pa.string()),
        ("ts_event", TIMESTAMP_NS_UTC),
        ("symbol", pa.string()),
        ("cme_session_id", pa.string()),
        ("setup_type", pa.string()),
        ("entry_side", pa.string()),
        ("reference_level", pa.float64()),
        ("entry_price", pa.float64()),
        ("entry_timestamp", TIMESTAMP_NS_UTC),
        ("structural_invalidation", pa.float64()),
        ("stop_price", pa.float64()),
        ("target_1", pa.float64()),
        ("target_2", pa.float64()),
        ("target_3", pa.float64()),
        ("max_holding_bars", pa.int64()),
        ("max_holding_seconds", pa.int64()),
        ("reason_codes", pa.list_(pa.string())),
        ("feature_timestamp", TIMESTAMP_NS_UTC),
        ("setup_version", pa.string()),
        ("fvg_id", pa.string()),
        ("fvg_low", pa.float64()),
        ("fvg_high", pa.float64()),
        ("effort_range_ratio", pa.float64()),
        ("effort_volume_ratio", pa.float64()),
    ]
)


@dataclass(frozen=True)
class FailedFVGCandidateRunResult:
    """Result summary for setup-candidate generation."""

    manifest_path: Path
    output_root: Path
    artifact_root: Path
    input_rows: int
    h1_bar_count: int
    m30_bar_count: int
    candidate_count: int
    elapsed_seconds: float


@dataclass(frozen=True)
class QEPTechnicalCandidateRunResult:
    """Result summary for QEP technical setup-candidate generation."""

    manifest_path: Path
    output_root: Path
    artifact_root: Path
    input_rows: int
    m30_bar_count: int
    candidate_count: int
    elapsed_seconds: float


def build_failed_fvg_candidates(
    *,
    trade_tape_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    failed_fvg_config: FailedFVGConfig | None = None,
) -> FailedFVGCandidateRunResult:
    """Build Failed FVG setup candidates from the canonical action-T trade tape."""

    start = time.perf_counter()
    config = config.validated()
    output_root = Path(output_root)
    artifact_root = Path(artifact_root)
    staging_root = _prepare_output(output_root, config)
    artifact_root.mkdir(parents=True, exist_ok=True)

    engine_config = failed_fvg_config or FailedFVGConfig(tick_size=config.tick_size)
    bars = TradeTapeBarBuilder(config).build(trade_tape_path)
    candidates = FailedFVGSetupEngine(engine_config).generate(
        h1_bars=bars.h1_bars,
        m30_bars=bars.m30_bars,
    )
    table = _candidate_table(candidates)
    pq.write_table(table, staging_root / "setup_candidates.parquet", compression=_compression(config))
    _finalize_output(staging_root, output_root)
    manifest = _manifest(
        trade_tape_path=trade_tape_path,
        output_root=output_root,
        artifact_root=artifact_root,
        config=config,
        failed_fvg_config=engine_config,
        bars=bars,
        candidates=candidates,
        elapsed_seconds=round(time.perf_counter() - start, 6),
    )
    manifest_path = artifact_root / "failed_fvg_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _write_summary(artifact_root / "failed_fvg_summary.md", manifest)
    return FailedFVGCandidateRunResult(
        manifest_path=manifest_path,
        output_root=output_root,
        artifact_root=artifact_root,
        input_rows=bars.input_rows,
        h1_bar_count=len(bars.h1_bars),
        m30_bar_count=len(bars.m30_bars),
        candidate_count=len(candidates),
        elapsed_seconds=time.perf_counter() - start,
    )


def build_qep_technical_candidates(
    *,
    trade_tape_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    qep_config: QEPTechnicalConfig | None = None,
) -> QEPTechnicalCandidateRunResult:
    """Build QEP technical setup candidates from the canonical action-T trade tape."""

    start = time.perf_counter()
    config = config.validated()
    output_root = Path(output_root)
    artifact_root = Path(artifact_root)
    staging_root = _prepare_output(output_root, config)
    artifact_root.mkdir(parents=True, exist_ok=True)

    engine_config = qep_config or QEPTechnicalConfig(tick_size=config.tick_size)
    bars = TradeTapeBarBuilder(config).build(trade_tape_path)
    candidates = QEPTechnicalSetupEngine(engine_config).generate(m30_bars=bars.m30_bars)
    table = _candidate_table(candidates)
    pq.write_table(table, staging_root / "setup_candidates.parquet", compression=_compression(config))
    _finalize_output(staging_root, output_root)
    manifest = _qep_manifest(
        trade_tape_path=trade_tape_path,
        output_root=output_root,
        artifact_root=artifact_root,
        config=config,
        qep_config=engine_config,
        bars=bars,
        candidates=candidates,
        elapsed_seconds=round(time.perf_counter() - start, 6),
    )
    manifest_path = artifact_root / "qep_technical_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _write_qep_summary(artifact_root / "qep_technical_summary.md", manifest)
    return QEPTechnicalCandidateRunResult(
        manifest_path=manifest_path,
        output_root=output_root,
        artifact_root=artifact_root,
        input_rows=bars.input_rows,
        m30_bar_count=len(bars.m30_bars),
        candidate_count=len(candidates),
        elapsed_seconds=time.perf_counter() - start,
    )


@dataclass(frozen=True)
class BuiltBars:
    """Causal bar output derived from the canonical trade tape."""

    input_rows: int
    h1_bars: list[Bar]
    m30_bars: list[Bar]


class TradeTapeBarBuilder:
    """Stream trade-tape rows into causal OHLCV bars without pandas."""

    def __init__(self, config: Phase1Config) -> None:
        self.config = config.validated()

    def build(self, trade_tape_path: Path) -> BuiltBars:
        if not trade_tape_path.exists():
            raise SchemaValidationError(f"Trade tape path does not exist: {trade_tape_path}")
        dataset = ds.dataset(trade_tape_path, format="parquet", partitioning="hive")
        missing = sorted(set(FAILED_FVG_INPUT_COLUMNS) - set(dataset.schema.names))
        if missing:
            raise SchemaValidationError(f"Trade tape missing columns for Failed FVG pipeline: {', '.join(missing)}")

        h1: dict[tuple[str, str, int], _BarAccumulator] = {}
        m30: dict[tuple[str, str, int], _BarAccumulator] = {}
        input_rows = 0
        scanner = dataset.scanner(columns=FAILED_FVG_INPUT_COLUMNS, batch_size=self.config.batch_size)
        for batch in scanner.to_batches():
            table = pa.Table.from_batches([batch])
            input_rows += table.num_rows
            self._observe_table(table, h1=h1, m30=m30)

        return BuiltBars(
            input_rows=input_rows,
            h1_bars=_finalize_bars(h1),
            m30_bars=_finalize_bars(m30),
        )

    def _observe_table(
        self,
        table: pa.Table,
        *,
        h1: dict[tuple[str, str, int], _BarAccumulator],
        m30: dict[tuple[str, str, int], _BarAccumulator],
    ) -> None:
        timestamps = timestamp_array_to_ns(table["ts_event"])
        sequences = table["sequence"].to_pylist()
        symbols = table["symbol"].to_pylist()
        prices = table["price"].to_pylist()
        sizes = table["size"].to_pylist()
        session_ids = table["session_id"].to_pylist()
        source_rows = table["source_row_number"].to_pylist()

        for ts_ns, sequence, symbol, price, size, session_id, source_row in zip(
            timestamps,
            sequences,
            symbols,
            prices,
            sizes,
            session_ids,
            source_rows,
            strict=True,
        ):
            if (
                ts_ns is None
                or sequence is None
                or symbol is None
                or price is None
                or size is None
                or session_id is None
                or source_row is None
            ):
                raise OutputValidationError("Trade tape contains null values in required setup input columns")
            order_key = (int(ts_ns), int(sequence), int(source_row))
            price_dec = Decimal(str(float(price)))
            size_int = int(size)
            symbol_str = str(symbol)
            session_str = str(session_id)
            self._observe_bar(h1, symbol_str, session_str, int(ts_ns), order_key, price_dec, size_int, 3_600)
            self._observe_bar(m30, symbol_str, session_str, int(ts_ns), order_key, price_dec, size_int, 1_800)

    def _observe_bar(
        self,
        bars: dict[tuple[str, str, int], _BarAccumulator],
        symbol: str,
        session_id: str,
        ts_ns: int,
        order_key: tuple[int, int, int],
        price: Decimal,
        size: int,
        seconds: int,
    ) -> None:
        duration_ns = seconds * 1_000_000_000
        start_ns = (ts_ns // duration_ns) * duration_ns
        key = (symbol, session_id, start_ns)
        bar = bars.get(key)
        if bar is None:
            bar = _BarAccumulator(symbol=symbol, session_id=session_id, start_ns=start_ns)
            bars[key] = bar
        bar.update(order_key=order_key, price=price, size=size)


@dataclass
class _BarAccumulator:
    symbol: str
    session_id: str
    start_ns: int
    open_price: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    volume: int = 0
    first_key: tuple[int, int, int] | None = None
    last_key: tuple[int, int, int] | None = None

    def update(self, *, order_key: tuple[int, int, int], price: Decimal, size: int) -> None:
        if self.first_key is None or order_key < self.first_key:
            self.first_key = order_key
            self.open_price = price
        if self.last_key is None or order_key > self.last_key:
            self.last_key = order_key
            self.close = price
        self.high = price if self.high is None else max(self.high, price)
        self.low = price if self.low is None else min(self.low, price)
        self.volume += size

    def to_bar(self) -> Bar:
        if self.open_price is None or self.high is None or self.low is None or self.close is None:
            raise OutputValidationError("Cannot finalize an empty OHLCV bar")
        return Bar(
            ts_event=_datetime_from_ns(self.start_ns),
            symbol=self.symbol,
            cme_session_id=self.session_id,
            open=self.open_price,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )


def _finalize_bars(bars: dict[tuple[str, str, int], _BarAccumulator]) -> list[Bar]:
    return [bars[key].to_bar() for key in sorted(bars)]


def _candidate_table(candidates: list[SetupCandidate]) -> pa.Table:
    rows = [
        {
            "setup_id": item.setup_id,
            "ts_event": item.ts_event,
            "symbol": item.symbol,
            "cme_session_id": item.cme_session_id,
            "setup_type": item.setup_type,
            "entry_side": item.entry_side,
            "reference_level": _float(item.reference_level),
            "entry_price": _float(item.entry_price),
            "entry_timestamp": item.entry_timestamp,
            "structural_invalidation": _float(item.structural_invalidation),
            "stop_price": _float(item.stop_price),
            "target_1": _float(item.target_1),
            "target_2": _float(item.target_2),
            "target_3": _float(item.target_3),
            "max_holding_bars": item.max_holding_bars,
            "max_holding_seconds": item.max_holding_seconds,
            "reason_codes": list(item.reason_codes),
            "feature_timestamp": item.feature_timestamp,
            "setup_version": item.setup_version,
            "fvg_id": item.fvg_id,
            "fvg_low": _float(item.fvg_low),
            "fvg_high": _float(item.fvg_high),
            "effort_range_ratio": _float(item.effort_range_ratio),
            "effort_volume_ratio": _float(item.effort_volume_ratio),
        }
        for item in candidates
    ]
    return pa.Table.from_pylist(rows, schema=SETUP_CANDIDATE_SCHEMA)


def _manifest(
    *,
    trade_tape_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    failed_fvg_config: FailedFVGConfig,
    bars: BuiltBars,
    candidates: list[SetupCandidate],
    elapsed_seconds: float,
) -> dict[str, Any]:
    output_file = output_root / "setup_candidates.parquet"
    payload: dict[str, Any] = {
        "phase": "1_setup_candidates",
        "status": "complete",
        "setup_type": "FAILED_FVG",
        "generated_at": datetime.now(UTC).isoformat(),
        "trade_tape_path": str(trade_tape_path),
        "output_root": str(output_root),
        "artifact_root": str(artifact_root),
        "input_columns": list(FAILED_FVG_INPUT_COLUMNS),
        "forbidden_inputs": ["depth", "order_book_imbalance", "microprice", "queue_position"],
        "input_rows": bars.input_rows,
        "h1_bar_count": len(bars.h1_bars),
        "m30_bar_count": len(bars.m30_bars),
        "candidate_count": len(candidates),
        "output_files": [{"path": output_file.name, "bytes": output_file.stat().st_size}],
        "input_byte_size": file_size_bytes(trade_tape_path),
        "output_byte_size": output_file.stat().st_size,
        "elapsed_seconds": elapsed_seconds,
        "config": {
            "batch_size": config.batch_size,
            "tick_size": str(config.tick_size),
            "compression": config.compression,
            "overwrite": config.overwrite,
        },
        "failed_fvg_config": {
            "h1_bar_duration_seconds": int(failed_fvg_config.h1_bar_duration.total_seconds()),
            "m30_bar_duration_seconds": int(failed_fvg_config.m30_bar_duration.total_seconds()),
            "fvg_window_seconds": int(failed_fvg_config.fvg_window.total_seconds()),
            "atr_window": failed_fvg_config.atr_window,
            "volume_window": failed_fvg_config.volume_window,
            "effort_range_mult": str(failed_fvg_config.effort_range_mult),
            "effort_volume_mult": str(failed_fvg_config.effort_volume_mult),
            "max_holding_bars": failed_fvg_config.max_holding_bars,
            "setup_version": failed_fvg_config.setup_version,
        },
    }
    payload["aggregate_checksum"] = _checksum(payload)
    return payload


def _qep_manifest(
    *,
    trade_tape_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    qep_config: QEPTechnicalConfig,
    bars: BuiltBars,
    candidates: list[SetupCandidate],
    elapsed_seconds: float,
) -> dict[str, Any]:
    output_file = output_root / "setup_candidates.parquet"
    payload: dict[str, Any] = {
        "phase": "1_setup_candidates",
        "status": "complete",
        "setup_type": "QEP_TECHNICAL",
        "generated_at": datetime.now(UTC).isoformat(),
        "trade_tape_path": str(trade_tape_path),
        "output_root": str(output_root),
        "artifact_root": str(artifact_root),
        "input_columns": list(FAILED_FVG_INPUT_COLUMNS),
        "forbidden_inputs": ["depth", "order_book_imbalance", "microprice", "queue_position"],
        "input_rows": bars.input_rows,
        "m30_bar_count": len(bars.m30_bars),
        "candidate_count": len(candidates),
        "output_files": [{"path": output_file.name, "bytes": output_file.stat().st_size}],
        "input_byte_size": file_size_bytes(trade_tape_path),
        "output_byte_size": output_file.stat().st_size,
        "elapsed_seconds": elapsed_seconds,
        "config": {
            "batch_size": config.batch_size,
            "tick_size": str(config.tick_size),
            "compression": config.compression,
            "overwrite": config.overwrite,
        },
        "qep_technical_config": {
            "m30_bar_duration_seconds": int(qep_config.m30_bar_duration.total_seconds()),
            "rsi_period": qep_config.rsi_period,
            "macd_fast": qep_config.macd_fast,
            "macd_slow": qep_config.macd_slow,
            "macd_signal": qep_config.macd_signal,
            "atr_window": qep_config.atr_window,
            "atr_stop_mult": str(qep_config.atr_stop_mult),
            "stop_buffer_ticks": qep_config.stop_buffer_ticks,
            "take_profit_r": [str(item) for item in qep_config.take_profit_r],
            "max_holding_bars": qep_config.max_holding_bars,
            "setup_version": qep_config.setup_version,
        },
    }
    payload["aggregate_checksum"] = _checksum(payload)
    return payload


def _write_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Failed FVG Candidate Summary",
        "",
        f"- `generated_at`: {manifest['generated_at']}",
        f"- `input_rows`: {manifest['input_rows']}",
        f"- `h1_bar_count`: {manifest['h1_bar_count']}",
        f"- `m30_bar_count`: {manifest['m30_bar_count']}",
        f"- `candidate_count`: {manifest['candidate_count']}",
        f"- `output_root`: {manifest['output_root']}",
        f"- `elapsed_seconds`: {manifest['elapsed_seconds']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_qep_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# QEP Technical Candidate Summary",
        "",
        f"- `generated_at`: {manifest['generated_at']}",
        f"- `input_rows`: {manifest['input_rows']}",
        f"- `m30_bar_count`: {manifest['m30_bar_count']}",
        f"- `candidate_count`: {manifest['candidate_count']}",
        f"- `output_root`: {manifest['output_root']}",
        f"- `elapsed_seconds`: {manifest['elapsed_seconds']}",
    ]
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


def _datetime_from_ns(value: int) -> datetime:
    seconds, nanos = divmod(value, 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=nanos // 1_000)


def _float(value: Decimal) -> float:
    return float(value)


def _checksum(manifest: dict[str, Any]) -> str:
    stable = {key: value for key, value in manifest.items() if key not in {"generated_at", "aggregate_checksum"}}
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
