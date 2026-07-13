"""Manifest creation and trade-tape validation."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds

from mnq_ai.config import Phase1Config
from mnq_ai.constants import CAUSAL_ORDER_COLUMNS
from mnq_ai.data.quality_audit import AuditAccumulator
from mnq_ai.exceptions import OutputValidationError


def create_phase1_manifest(
    *,
    input_path: Path,
    output_root: Path,
    artifact_root: Path,
    config: Phase1Config,
    audit: AuditAccumulator,
) -> dict[str, Any]:
    """Create a deterministic Phase 1 completion manifest."""

    output_files = _output_files(output_root)
    payload: dict[str, Any] = {
        "phase": "1",
        "status": "complete",
        "generated_at": datetime.now(UTC).isoformat(),
        "input_path": str(input_path),
        "output_root": str(output_root),
        "artifact_root": str(artifact_root),
        "causal_order_columns": list(CAUSAL_ORDER_COLUMNS),
        "partition_columns": ["symbol", "trading_date"],
        "config": {
            "batch_size": config.batch_size,
            "symbol_filters": list(config.symbol_filters),
            "tick_size": str(config.tick_size),
            "exchange_timezone": config.exchange_timezone,
            "session_start": config.session_start,
            "session_end": config.session_end,
            "rth_start": config.rth_start,
            "rth_end": config.rth_end,
            "invalid_row_policy": config.invalid_row_policy,
            "compression": config.compression,
            "target_parquet_file_size_mb": config.target_parquet_file_size_mb,
            "target_rows_per_file": config.target_rows_per_file,
        },
        "input_rows": audit.total_input_rows,
        "valid_T_rows": audit.valid_t_rows,
        "output_row_count": audit.output_row_count,
        "sum_size_for_valid_T_rows": audit.sum_t_size,
        "sum_output_trade_size": audit.output_total_size,
        "sum_signed_volume": audit.sum_signed_volume,
        "total_F_rows": audit.total_f_rows,
        "invalid_row_counts": dict(audit.invalid_row_counts),
        "ordering_anomalies": audit.ordering_anomalies,
        "duplicate_candidates": audit.duplicate_candidates,
        "output_file_count": len(output_files),
        "output_byte_size": sum(item["bytes"] for item in output_files),
        "output_files": output_files,
    }
    payload["aggregate_checksum"] = stable_manifest_checksum(payload)
    return payload


def write_manifest(artifact_root: Path, manifest: dict[str, Any]) -> Path:
    """Write the Phase 1 manifest JSON."""

    artifact_root.mkdir(parents=True, exist_ok=True)
    path = artifact_root / "phase1_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def stable_manifest_checksum(manifest: dict[str, Any]) -> str:
    """Return a checksum excluding runtime-only fields."""

    stable = _strip_runtime_fields(manifest)
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_trade_tape(input_root: Path, manifest_path: Path) -> dict[str, Any]:
    """Validate aggregate invariants for a produced trade tape."""

    if not input_root.exists():
        raise OutputValidationError(f"Trade tape input does not exist: {input_root}")
    if not manifest_path.exists():
        raise OutputValidationError(f"Manifest does not exist: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observed = aggregate_trade_tape(input_root)
    failures: list[str] = []
    if observed["row_count"] != manifest.get("output_row_count"):
        failures.append("output row count does not match manifest")
    if observed["sum_size"] != manifest.get("sum_output_trade_size"):
        failures.append("output size sum does not match manifest")
    if observed["sum_signed_volume"] != manifest.get("sum_signed_volume"):
        failures.append("signed-volume sum does not match manifest")
    if manifest.get("total_F_rows", 0) and manifest.get("output_row_count") == manifest.get("input_rows"):
        failures.append("manifest suggests F rows may have been included")
    if failures:
        raise OutputValidationError("; ".join(failures))
    return {"valid": True, **observed}


def aggregate_trade_tape(input_root: Path) -> dict[str, int]:
    """Read only aggregate columns from a trade-tape dataset."""

    dataset = ds.dataset(input_root, format="parquet", partitioning="hive")
    row_count = 0
    sum_size = 0
    sum_signed_volume = 0
    scanner = dataset.scanner(columns=["size", "signed_volume"])
    for batch in scanner.to_batches():
        row_count += batch.num_rows
        table = pa.Table.from_batches([batch])
        sum_size += int(pc.sum(table["size"]).as_py() or 0)
        sum_signed_volume += int(pc.sum(table["signed_volume"]).as_py() or 0)
    return {
        "row_count": row_count,
        "sum_size": sum_size,
        "sum_signed_volume": sum_signed_volume,
    }


def _output_files(output_root: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("*.parquet")):
        files.append({"path": str(path.relative_to(output_root)), "bytes": path.stat().st_size})
    return files


def _strip_runtime_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_runtime_fields(item)
            for key, item in value.items()
            if key not in {"generated_at", "aggregate_checksum"}
        }
    if isinstance(value, list):
        return [_strip_runtime_fields(item) for item in value]
    return value
