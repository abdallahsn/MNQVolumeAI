from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from mnq_ai.setups.failed_fvg import Bar
from mnq_ai.setups.qep_technical import QEPTechnicalConfig, QEPTechnicalSetupEngine

SESSION_ID = "CME_EQ_FUT_2026-04-07"


def test_qep_technical_emits_long_from_rsi_macd_signal_on_next_bar() -> None:
    config = QEPTechnicalConfig(
        tick_size=Decimal("0.25"),
        rsi_period=3,
        macd_fast=2,
        macd_slow=3,
        macd_signal=2,
        atr_window=3,
        atr_stop_mult=Decimal("2"),
        take_profit_r=(Decimal("1.5"), Decimal("3"), Decimal("4.5")),
    )
    engine = QEPTechnicalSetupEngine(config)
    bars = [
        _bar("2026-04-07T13:00:00Z", close="100.00"),
        _bar("2026-04-07T13:30:00Z", close="101.00"),
        _bar("2026-04-07T14:00:00Z", close="102.00"),
        _bar("2026-04-07T14:30:00Z", close="103.00"),
        _bar("2026-04-07T15:00:00Z", close="103.00"),
    ]

    setups = engine.generate(m30_bars=bars)

    assert len(setups) == 1
    setup = setups[0]
    assert setup.setup_type == "QEP_TECHNICAL"
    assert setup.entry_side == "LONG"
    assert setup.feature_timestamp == _ts("2026-04-07T14:30:00Z")
    assert setup.entry_timestamp == _ts("2026-04-07T15:00:00Z")
    assert setup.entry_price == Decimal("103.00")
    assert setup.stop_price == Decimal("101.00")
    assert setup.target_1 == Decimal("106.00")
    assert setup.target_2 == Decimal("109.00")
    assert setup.target_3 == Decimal("112.00")
    assert setup.reason_codes == (
        "QEP_RSI_ABOVE_50",
        "QEP_MACD_BULLISH_POSITIVE",
        "QEP_ATR_STOP_2X",
    )


def test_qep_technical_emits_short_from_rsi_macd_signal_on_next_bar() -> None:
    config = QEPTechnicalConfig(
        tick_size=Decimal("0.25"),
        rsi_period=3,
        macd_fast=2,
        macd_slow=3,
        macd_signal=2,
        atr_window=3,
        atr_stop_mult=Decimal("2"),
    )
    engine = QEPTechnicalSetupEngine(config)
    bars = [
        _bar("2026-04-07T13:00:00Z", close="103.00"),
        _bar("2026-04-07T13:30:00Z", close="102.00"),
        _bar("2026-04-07T14:00:00Z", close="101.00"),
        _bar("2026-04-07T14:30:00Z", close="100.00"),
        _bar("2026-04-07T15:00:00Z", close="100.00"),
    ]

    setups = engine.generate(m30_bars=bars)

    assert len(setups) == 1
    setup = setups[0]
    assert setup.entry_side == "SHORT"
    assert setup.entry_price == Decimal("100.00")
    assert setup.stop_price == Decimal("102.00")
    assert setup.target_1 == Decimal("97.00")
    assert setup.reason_codes == (
        "QEP_RSI_BELOW_50",
        "QEP_MACD_BEARISH_NEGATIVE",
        "QEP_ATR_STOP_2X",
    )


def test_qep_technical_generation_is_invariant_to_future_bars() -> None:
    config = QEPTechnicalConfig(
        tick_size=Decimal("0.25"),
        rsi_period=3,
        macd_fast=2,
        macd_slow=3,
        macd_signal=2,
        atr_window=3,
    )
    engine = QEPTechnicalSetupEngine(config)
    prefix = [
        _bar("2026-04-07T13:00:00Z", close="100.00"),
        _bar("2026-04-07T13:30:00Z", close="101.00"),
        _bar("2026-04-07T14:00:00Z", close="102.00"),
        _bar("2026-04-07T14:30:00Z", close="103.00"),
        _bar("2026-04-07T15:00:00Z", close="103.00"),
    ]
    future = [
        _bar("2026-04-07T15:30:00Z", close="90.00"),
        _bar("2026-04-07T16:00:00Z", close="80.00"),
    ]

    prefix_setups = engine.generate(m30_bars=prefix)
    full_setups = engine.generate(m30_bars=prefix + future)

    assert [setup.fingerprint() for setup in full_setups[: len(prefix_setups)]] == [
        setup.fingerprint() for setup in prefix_setups
    ]


def _bar(timestamp: str, *, close: str) -> Bar:
    close_dec = Decimal(close)
    return Bar(
        ts_event=_ts(timestamp),
        symbol="MNQM6",
        cme_session_id=SESSION_ID,
        open=close_dec,
        high=close_dec,
        low=close_dec,
        close=close_dec,
        volume=100,
    )


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
