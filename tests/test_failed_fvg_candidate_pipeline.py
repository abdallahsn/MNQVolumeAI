from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mnq_ai.cli import main
from mnq_ai.data.schemas import TRADE_TAPE_SCHEMA

SESSION_ID = "CME_EQ_FUT_2026-04-06"


def test_build_failed_fvg_candidates_cli_writes_manifest_and_parquet(tmp_path: Path) -> None:
    trade_tape = tmp_path / "trade_tape.parquet"
    output = tmp_path / "setup_candidates"
    artifacts = tmp_path / "artifacts"
    _write_trade_tape_fixture(trade_tape)

    exit_code = main(
        [
            "build-failed-fvg-candidates",
            "--trade-tape",
            str(trade_tape),
            "--config",
            "configs/mnq.yaml",
            "--output",
            str(output),
            "--artifacts",
            str(artifacts),
            "--atr-window",
            "3",
            "--volume-window",
            "3",
            "--effort-range-mult",
            "1.20",
            "--effort-volume-mult",
            "1.30",
            "--overwrite",
        ]
    )

    assert exit_code == 0
    manifest = json.loads((artifacts / "failed_fvg_manifest.json").read_text(encoding="utf-8"))
    table = pq.read_table(output / "setup_candidates.parquet")

    assert manifest["setup_type"] == "FAILED_FVG"
    assert manifest["candidate_count"] == 1
    assert manifest["input_columns"] == ["ts_event", "sequence", "symbol", "price", "size", "session_id", "source_row_number"]
    assert table.num_rows == 1
    row = table.to_pylist()[0]
    assert row["setup_type"] == "FAILED_BULL_FVG"
    assert row["entry_side"] == "SHORT"
    assert row["entry_price"] == 100.5
    assert row["stop_price"] == 103.0
    assert row["target_1"] == 98.0
    assert row["target_2"] == 95.5
    assert row["target_3"] == 90.5
    assert row["reason_codes"] == [
        "FAILED_BULL_FVG_SHORT",
        "FVG_OVERLAP_CONFIRMED",
        "EFFORT_WITHOUT_RESULT",
    ]


def _write_trade_tape_fixture(path: Path) -> None:
    rows: list[dict[str, object]] = []
    sequence = 1
    for timestamp, price, size in [
        ("2026-04-06T13:00:00Z", 95.0, 50),
        ("2026-04-06T13:30:00Z", 100.0, 50),
        ("2026-04-06T14:00:00Z", 96.0, 50),
        ("2026-04-06T14:10:00Z", 101.0, 50),
        ("2026-04-06T14:30:00Z", 99.0, 50),
        ("2026-04-06T14:59:00Z", 100.0, 50),
        ("2026-04-06T15:00:00Z", 101.0, 50),
        ("2026-04-06T15:29:00Z", 102.0, 50),
        ("2026-04-06T15:30:00Z", 102.0, 50),
        ("2026-04-06T15:59:00Z", 103.0, 50),
        ("2026-04-06T16:00:00Z", 102.5, 50),
        ("2026-04-06T16:10:00Z", 103.0, 50),
        ("2026-04-06T16:20:00Z", 99.5, 50),
        ("2026-04-06T16:29:00Z", 100.75, 50),
        ("2026-04-06T16:30:00Z", 100.5, 50),
        ("2026-04-06T16:45:00Z", 99.0, 100),
    ]:
        rows.append(_trade(timestamp, price=price, size=size, sequence=sequence))
        sequence += 1
    pq.write_table(pa.Table.from_pylist(rows, schema=TRADE_TAPE_SCHEMA), path)


def _trade(timestamp: str, *, price: float, size: int, sequence: int) -> dict[str, object]:
    ts = _ts(timestamp)
    return {
        "ts_event": ts,
        "ts_recv": ts,
        "sequence": sequence,
        "publisher_id": 1,
        "instrument_id": 123,
        "symbol": "MNQM6",
        "price": price,
        "size": size,
        "aggressor_side": "B",
        "signed_volume": size,
        "unknown_aggressor": False,
        "trading_date": "2026-04-06",
        "session_id": SESSION_ID,
        "session_segment": "ETH",
        "is_rth": False,
        "source_row_number": sequence,
    }


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
