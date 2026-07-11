from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import pytest

from mnq_ai.config import Phase1Config
from mnq_ai.data.manifests import stable_manifest_checksum, validate_trade_tape
from mnq_ai.data.trade_extractor import Phase1TradeExtractor
from mnq_ai.exceptions import DataValidationError


def test_build_trade_tape_filters_t_only_and_maps_signed_volume(tmp_path: Path) -> None:
    input_path = _write_fixture(tmp_path)
    output = tmp_path / "trade_tape"
    artifacts = tmp_path / "artifacts"
    config = _config(tmp_path, invalid_row_policy="quarantine")

    result = Phase1TradeExtractor(config).build_trade_tape(input_path, output, artifacts)
    table = ds.dataset(output, format="parquet", partitioning="hive").to_table()
    manifest = json.loads((artifacts / "phase1_manifest.json").read_text(encoding="utf-8"))

    assert result.output_rows == 4
    assert table.num_rows == 4
    assert table.column_names == [
        "ts_event",
        "ts_recv",
        "sequence",
        "publisher_id",
        "instrument_id",
        "price",
        "size",
        "aggressor_side",
        "signed_volume",
        "unknown_aggressor",
        "session_id",
        "session_segment",
        "is_rth",
        "source_row_number",
        "symbol",
        "trading_date",
    ]
    assert sorted(table["signed_volume"].to_pylist()) == [-3, 0, 1, 2]
    assert sum(table["size"].to_pylist()) == 10
    assert manifest["total_F_rows"] == 1
    assert manifest["output_row_count"] == manifest["valid_T_rows"] == 4
    assert manifest["sum_output_trade_size"] == manifest["sum_size_for_valid_T_rows"] == 10
    assert (artifacts / "quarantine_rows.parquet").exists()
    assert validate_trade_tape(output, artifacts / "phase1_manifest.json")["valid"] is True


def test_f_rows_are_not_double_counted(tmp_path: Path) -> None:
    input_path = _write_fixture(
        tmp_path,
        rows=[
            _row(action="T", side="B", size=5, sequence=1),
            _row(action="F", side="B", size=5, sequence=2),
        ],
    )
    output = tmp_path / "trade_tape"
    artifacts = tmp_path / "artifacts"
    config = _config(tmp_path, invalid_row_policy="fail")

    Phase1TradeExtractor(config).build_trade_tape(input_path, output, artifacts)
    table = ds.dataset(output, format="parquet", partitioning="hive").to_table()
    manifest = json.loads((artifacts / "phase1_manifest.json").read_text(encoding="utf-8"))

    assert table.num_rows == 1
    assert table["size"].to_pylist() == [5]
    assert table["signed_volume"].to_pylist() == [5]
    assert manifest["total_F_rows"] == 1
    assert manifest["sum_output_trade_size"] == 5


def test_fail_policy_rejects_invalid_tick(tmp_path: Path) -> None:
    input_path = _write_fixture(tmp_path, rows=[_row(action="T", side="B", price=18000.10)])
    config = _config(tmp_path, invalid_row_policy="fail")

    with pytest.raises(DataValidationError):
        Phase1TradeExtractor(config).build_trade_tape(
            input_path,
            tmp_path / "trade_tape",
            tmp_path / "artifacts",
        )


def test_manifest_checksum_is_stable_across_identical_reruns(tmp_path: Path) -> None:
    input_path = _write_fixture(tmp_path, rows=[_row(action="T", side="B", sequence=1)])
    output = tmp_path / "trade_tape"
    artifacts = tmp_path / "artifacts"
    config = _config(tmp_path, invalid_row_policy="fail")

    Phase1TradeExtractor(config).build_trade_tape(input_path, output, artifacts)
    first = json.loads((artifacts / "phase1_manifest.json").read_text(encoding="utf-8"))
    Phase1TradeExtractor(config).build_trade_tape(input_path, output, artifacts)
    second = json.loads((artifacts / "phase1_manifest.json").read_text(encoding="utf-8"))

    assert stable_manifest_checksum(first) == stable_manifest_checksum(second)
    assert first["aggregate_checksum"] == second["aggregate_checksum"]


def _config(tmp_path: Path, *, invalid_row_policy: str) -> Phase1Config:
    return Phase1Config.from_mapping(
        {
            "artifact_root": str(tmp_path / "artifacts"),
            "output_root": str(tmp_path / "trade_tape"),
            "batch_size": 3,
            "symbol_filters": ["MNQM6"],
            "invalid_row_policy": invalid_row_policy,
            "overwrite": True,
            "compression": "zstd",
        }
    )


def _write_fixture(tmp_path: Path, rows: list[dict[str, object]] | None = None) -> Path:
    path = tmp_path / "mbo.parquet"
    pq.write_table(pa.Table.from_pylist(rows or _rows()), path)
    return path


def _rows() -> list[dict[str, object]]:
    return [
        _row(action="T", side="B", size=2, sequence=1),
        _row(action="F", side="B", size=2, sequence=2),
        _row(action="T", side="A", size=3, sequence=3),
        _row(action="T", side="N", size=4, sequence=3),
        _row(action="A", side="B", size=8, sequence=4),
        _row(action="C", side="A", size=8, sequence=5),
        _row(action="M", side="N", size=8, sequence=6),
        _row(action="R", side="B", size=8, sequence=7),
        _row(action="T", side="B", price=18000.10, size=1, sequence=8),
        _row(action="T", side="A", size=0, sequence=9),
        _row(action="T", side="B", size=1, sequence=10),
    ]


def _row(
    *,
    action: str,
    side: str,
    price: float = 18000.25,
    size: int = 1,
    sequence: int = 1,
) -> dict[str, object]:
    return {
        "ts_recv": "2026-04-06T00:00:00.001184655Z",
        "ts_event": "2026-04-06T00:00:00.001184655Z",
        "rtype": 160,
        "publisher_id": 1,
        "instrument_id": 123,
        "action": action,
        "side": side,
        "price": price,
        "size": size,
        "channel_id": 1,
        "order_id": 1000 + sequence,
        "flags": 0,
        "ts_in_delta": 0,
        "sequence": sequence,
        "symbol": "MNQM6",
    }
