from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mnq_ai.cli import main
from mnq_ai.data.schemas import TRADE_TAPE_SCHEMA
from mnq_ai.data.setup_candidates import SETUP_CANDIDATE_SCHEMA

SESSION_ID = "CME_EQ_FUT_2026-04-06"


def test_phase2_execution_gate_labels_first_barrier_after_entry(tmp_path: Path) -> None:
    trade_tape = tmp_path / "trade_tape.parquet"
    setup_candidates = tmp_path / "setup_candidates.parquet"
    output = tmp_path / "labels"
    artifacts = tmp_path / "artifacts"
    _write_trade_tape(trade_tape)
    _write_setup_candidates(setup_candidates)

    exit_code = main(
        [
            "build-phase2-labels",
            "--trade-tape",
            str(trade_tape),
            "--setup-candidates",
            str(setup_candidates),
            "--config",
            "configs/mnq.yaml",
            "--output",
            str(output),
            "--artifacts",
            str(artifacts),
            "--commission-per-side",
            "0",
            "--entry-slippage-ticks",
            "0",
            "--stop-slippage-ticks",
            "0",
            "--time-exit-slippage-ticks",
            "0",
            "--point-value",
            "2",
            "--overwrite",
        ]
    )

    assert exit_code == 0
    labels = pq.read_table(output / "setup_labels.parquet").to_pylist()
    manifest = json.loads((artifacts / "phase2_gate_manifest.json").read_text(encoding="utf-8"))

    assert manifest["gate_recommendation"] == "NO-GO"
    assert manifest["candidate_count"] == 2
    assert manifest["label_count"] == 2
    assert manifest["fill_model"]["ambiguity_policy"] == "event_order_first_barrier"

    by_id = {row["setup_id"]: row for row in labels}
    assert by_id["long_target"]["exit_reason"] == "TARGET_1"
    assert by_id["long_target"]["success"] is True
    assert by_id["long_target"]["exit_timestamp"] == _ts("2026-04-06T10:00:01Z")
    assert by_id["long_target"]["gross_r"] == 1.0
    assert by_id["long_target"]["net_r"] == 1.0

    assert by_id["short_stop"]["exit_reason"] == "STOP"
    assert by_id["short_stop"]["success"] is False
    assert by_id["short_stop"]["exit_timestamp"] == _ts("2026-04-06T11:00:02Z")
    assert by_id["short_stop"]["gross_r"] == -1.0
    assert by_id["short_stop"]["net_r"] == -1.0


def _write_trade_tape(path: Path) -> None:
    rows = [
        _trade("2026-04-06T09:59:59Z", price=106.00, sequence=1),
        _trade("2026-04-06T10:00:01Z", price=105.00, sequence=2),
        _trade("2026-04-06T10:00:02Z", price=95.00, sequence=3),
        _trade("2026-04-06T11:00:01Z", price=198.00, sequence=4),
        _trade("2026-04-06T11:00:02Z", price=205.00, sequence=5),
    ]
    pq.write_table(pa.Table.from_pylist(rows, schema=TRADE_TAPE_SCHEMA), path)


def _write_setup_candidates(path: Path) -> None:
    rows = [
        _candidate(
            setup_id="long_target",
            entry_side="LONG",
            entry_timestamp="2026-04-06T10:00:00Z",
            entry_price=100.0,
            stop_price=95.0,
            target_1=105.0,
            target_2=110.0,
            target_3=115.0,
        ),
        _candidate(
            setup_id="short_stop",
            entry_side="SHORT",
            entry_timestamp="2026-04-06T11:00:00Z",
            entry_price=200.0,
            stop_price=205.0,
            target_1=195.0,
            target_2=190.0,
            target_3=185.0,
        ),
    ]
    pq.write_table(pa.Table.from_pylist(rows, schema=SETUP_CANDIDATE_SCHEMA), path)


def _candidate(
    *,
    setup_id: str,
    entry_side: str,
    entry_timestamp: str,
    entry_price: float,
    stop_price: float,
    target_1: float,
    target_2: float,
    target_3: float,
) -> dict[str, object]:
    entry_ts = _ts(entry_timestamp)
    return {
        "setup_id": setup_id,
        "ts_event": entry_ts,
        "symbol": "MNQM6",
        "cme_session_id": SESSION_ID,
        "setup_type": "FAILED_BULL_FVG" if entry_side == "SHORT" else "FAILED_BEAR_FVG",
        "entry_side": entry_side,
        "reference_level": entry_price,
        "entry_price": entry_price,
        "entry_timestamp": entry_ts,
        "structural_invalidation": stop_price,
        "stop_price": stop_price,
        "target_1": target_1,
        "target_2": target_2,
        "target_3": target_3,
        "max_holding_bars": 12,
        "max_holding_seconds": 21_600,
        "reason_codes": ["TEST"],
        "feature_timestamp": entry_ts,
        "setup_version": "test",
        "fvg_id": f"fvg_{setup_id}",
        "fvg_low": min(entry_price, target_1),
        "fvg_high": max(entry_price, target_1),
        "effort_range_ratio": 2.0,
        "effort_volume_ratio": 2.0,
    }


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
        "size": 1,
        "aggressor_side": "B",
        "signed_volume": 1,
        "unknown_aggressor": False,
        "trading_date": "2026-04-06",
        "session_id": SESSION_ID,
        "session_segment": "RTH",
        "is_rth": True,
        "source_row_number": sequence,
    }


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
