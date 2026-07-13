from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mnq_ai.data.execution_gate import PHASE2_LABEL_SCHEMA
from scripts.qep_failure_report import build_report


def test_qep_failure_report_identifies_overtrading_and_max_hold_failure(tmp_path: Path) -> None:
    labels = tmp_path / "setup_labels.parquet"
    output = tmp_path / "qep_failure_report.md"
    _write_labels(labels)

    summary = build_report(labels_path=labels, output_path=output, m30_bar_count=10)

    text = output.read_text(encoding="utf-8")
    assert summary["candidate_count"] == 5
    assert summary["success_count"] == 1
    assert summary["exit_reason_counts"] == {"MAX_HOLD": 3, "STOP": 1, "TARGET_1": 1}
    assert summary["sum_net_r"] == -1.7
    assert summary["avg_net_r"] == -0.34
    assert "candidate_density_per_m30_bar" in text
    assert "MAX_HOLD dominates exits" in text
    assert "target conversion is weak" in text
    assert "candidate density is high" in text


def _write_labels(path: Path) -> None:
    start = _ts("2026-04-06T10:00:00Z")
    rows = [
        _label("qep_1", "LONG", start, "MAX_HOLD", False, -0.2),
        _label("qep_2", "LONG", start + timedelta(minutes=30), "MAX_HOLD", False, -0.1),
        _label("qep_3", "SHORT", start + timedelta(minutes=60), "MAX_HOLD", False, -0.4),
        _label("qep_4", "SHORT", start + timedelta(minutes=90), "STOP", False, -1.0),
        _label("qep_5", "LONG", start + timedelta(minutes=120), "TARGET_1", True, 0.0),
    ]
    pq.write_table(pa.Table.from_pylist(rows, schema=PHASE2_LABEL_SCHEMA), path)


def _label(
    setup_id: str,
    side: str,
    entry_ts: datetime,
    exit_reason: str,
    success: bool,
    net_r: float,
) -> dict[str, object]:
    return {
        "setup_id": setup_id,
        "ts_event": entry_ts - timedelta(minutes=30),
        "symbol": "MNQM6",
        "cme_session_id": "CME_EQ_FUT_2026-04-06",
        "setup_type": "QEP_TECHNICAL",
        "entry_side": side,
        "entry_timestamp": entry_ts,
        "earliest_entry_timestamp": entry_ts,
        "max_exit_timestamp": entry_ts + timedelta(hours=6),
        "entry_price": 100.0,
        "entry_fill_price": 100.25 if side == "LONG" else 99.75,
        "stop_price": 98.0 if side == "LONG" else 102.0,
        "target_price": 103.0 if side == "LONG" else 97.0,
        "exit_timestamp": entry_ts + timedelta(hours=1),
        "exit_trade_price": 100.0,
        "exit_fill_price": 100.0,
        "exit_reason": exit_reason,
        "success": success,
        "planned_risk_points": 2.0,
        "gross_points": net_r * 2.0,
        "gross_r": net_r,
        "net_points": net_r * 2.0,
        "net_r": net_r,
        "commission_per_side": 0.35,
        "point_value": 2.0,
        "entry_slippage_ticks": 1,
        "stop_slippage_ticks": 1,
        "time_exit_slippage_ticks": 1,
        "entry_latency_seconds": 0,
        "event_count": 10,
        "label_available_timestamp": entry_ts + timedelta(hours=1),
        "ambiguity_policy": "event_order_first_barrier",
        "reason_codes": ["QEP_RSI_ABOVE_50"] if side == "LONG" else ["QEP_RSI_BELOW_50"],
    }


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
