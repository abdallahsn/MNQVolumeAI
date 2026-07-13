from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mnq_ai.cli import main
from mnq_ai.data.schemas import TRADE_TAPE_SCHEMA

SESSION_ID = "CME_EQ_FUT_2026-04-06"


def test_build_qep_technical_candidates_cli_writes_manifest_and_parquet(tmp_path: Path) -> None:
    trade_tape = tmp_path / "trade_tape.parquet"
    output = tmp_path / "qep_candidates"
    artifacts = tmp_path / "artifacts"
    _write_trade_tape_fixture(trade_tape)

    exit_code = main(
        [
            "build-qep-technical-candidates",
            "--trade-tape",
            str(trade_tape),
            "--config",
            "configs/mnq.yaml",
            "--output",
            str(output),
            "--artifacts",
            str(artifacts),
            "--rsi-period",
            "3",
            "--macd-fast",
            "2",
            "--macd-slow",
            "3",
            "--macd-signal",
            "2",
            "--atr-window",
            "3",
            "--atr-stop-mult",
            "2",
            "--overwrite",
        ]
    )

    assert exit_code == 0
    manifest = json.loads((artifacts / "qep_technical_manifest.json").read_text(encoding="utf-8"))
    table = pq.read_table(output / "setup_candidates.parquet")

    assert manifest["setup_type"] == "QEP_TECHNICAL"
    assert manifest["candidate_count"] == 1
    assert manifest["input_columns"] == ["ts_event", "sequence", "symbol", "price", "size", "session_id", "source_row_number"]
    assert table.num_rows == 1
    row = table.to_pylist()[0]
    assert row["setup_type"] == "QEP_TECHNICAL"
    assert row["entry_side"] == "LONG"
    assert row["entry_price"] == 103.0
    assert row["stop_price"] == 101.0
    assert row["target_1"] == 106.0
    assert row["reason_codes"] == [
        "QEP_RSI_ABOVE_50",
        "QEP_MACD_BULLISH_POSITIVE",
        "QEP_ATR_STOP_2X",
    ]


def _write_trade_tape_fixture(path: Path) -> None:
    rows = [
        _trade("2026-04-06T13:00:00Z", price=100.0, sequence=1),
        _trade("2026-04-06T13:30:00Z", price=101.0, sequence=2),
        _trade("2026-04-06T14:00:00Z", price=102.0, sequence=3),
        _trade("2026-04-06T14:30:00Z", price=103.0, sequence=4),
        _trade("2026-04-06T15:00:00Z", price=103.0, sequence=5),
    ]
    pq.write_table(pa.Table.from_pylist(rows, schema=TRADE_TAPE_SCHEMA), path)


def _trade(timestamp: str, *, price: float, sequence: int) -> dict[str, object]:
    ts = _ts(timestamp)
    return {
        "ts_event": ts,
        "ts_recv": ts,
        "sequence": sequence,
        "publisher_id": 1,
        "instrument_id": 123,
        "symbol": "MNQM6",
        "price": price,
        "size": 100,
        "aggressor_side": "B",
        "signed_volume": 100,
        "unknown_aggressor": False,
        "trading_date": "2026-04-06",
        "session_id": SESSION_ID,
        "session_segment": "ETH",
        "is_rth": False,
        "source_row_number": sequence,
    }


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
