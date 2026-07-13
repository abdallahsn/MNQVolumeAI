from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mnq_ai.setups.failed_fvg import Bar, FailedFVGConfig, FailedFVGSetupEngine, build_h1_fvgs

SESSION_ID = "CME_EQ_FUT_2026-04-07"


def test_build_h1_fvgs_uses_three_bar_gap_and_delays_availability() -> None:
    h1 = [
        _bar("2026-04-06T13:00:00Z", high="100.00", low="95.00"),
        _bar("2026-04-06T14:00:00Z", high="104.00", low="102.00"),
        _bar("2026-04-06T15:00:00Z", high="106.00", low="102.00"),
        _bar("2026-04-06T16:00:00Z", high="99.00", low="93.00"),
    ]

    fvgs = build_h1_fvgs(h1, bar_duration=timedelta(hours=1))

    assert len(fvgs) == 2
    assert fvgs[0].fvg_type == "BULL"
    assert fvgs[0].low == Decimal("100.00")
    assert fvgs[0].high == Decimal("102.00")
    assert fvgs[0].formed_at == _ts("2026-04-06T15:00:00Z")
    assert fvgs[0].available_at == _ts("2026-04-06T16:00:00Z")
    assert fvgs[1].fvg_type == "BEAR"
    assert fvgs[1].low == Decimal("99.00")
    assert fvgs[1].high == Decimal("102.00")
    assert fvgs[1].available_at == _ts("2026-04-06T17:00:00Z")


def test_failed_bull_fvg_emits_short_candidate_from_next_bar_entry() -> None:
    config = FailedFVGConfig(
        tick_size=Decimal("0.25"),
        effort_range_mult=Decimal("1.20"),
        effort_volume_mult=Decimal("1.30"),
        atr_window=3,
        volume_window=3,
        take_profit_r=(Decimal("1"), Decimal("2"), Decimal("4")),
    )
    engine = FailedFVGSetupEngine(config)
    h1 = [
        _bar("2026-04-06T13:00:00Z", high="100.00", low="95.00"),
        _bar("2026-04-06T14:00:00Z", high="101.00", low="96.00"),
        _bar("2026-04-06T15:00:00Z", high="106.00", low="102.00"),
    ]
    m30 = [
        _bar("2026-04-06T14:30:00Z", open_="99.00", high="100.00", low="99.00", close="99.50", volume=100),
        _bar("2026-04-06T15:00:00Z", open_="101.00", high="102.00", low="101.00", close="101.50", volume=100),
        _bar("2026-04-06T15:30:00Z", open_="102.00", high="103.00", low="102.00", close="102.50", volume=100),
        _bar("2026-04-06T16:00:00Z", open_="102.50", high="103.00", low="99.50", close="100.75", volume=200),
        _bar("2026-04-06T16:30:00Z", open_="100.50", high="101.00", low="98.00", close="99.00", volume=150),
    ]

    setups = engine.generate(h1_bars=h1, m30_bars=m30)

    assert len(setups) == 1
    setup = setups[0]
    assert setup.setup_type == "FAILED_BULL_FVG"
    assert setup.entry_side == "SHORT"
    assert setup.feature_timestamp == _ts("2026-04-06T16:00:00Z")
    assert setup.entry_timestamp == _ts("2026-04-06T16:30:00Z")
    assert setup.entry_price == Decimal("100.50")
    assert setup.structural_invalidation == Decimal("103.00")
    assert setup.stop_price == Decimal("103.00")
    assert setup.target_1 == Decimal("98.00")
    assert setup.target_2 == Decimal("95.50")
    assert setup.target_3 == Decimal("90.50")
    assert setup.max_holding_bars == 12
    assert setup.reason_codes == (
        "FAILED_BULL_FVG_SHORT",
        "FVG_OVERLAP_CONFIRMED",
        "EFFORT_WITHOUT_RESULT",
    )


def test_failed_fvg_generation_is_invariant_to_future_bars() -> None:
    config = FailedFVGConfig(
        tick_size=Decimal("0.25"),
        effort_range_mult=Decimal("1.20"),
        effort_volume_mult=Decimal("1.30"),
        atr_window=3,
        volume_window=3,
    )
    engine = FailedFVGSetupEngine(config)
    h1 = [
        _bar("2026-04-06T13:00:00Z", high="100.00", low="95.00"),
        _bar("2026-04-06T14:00:00Z", high="101.00", low="96.00"),
        _bar("2026-04-06T15:00:00Z", high="106.00", low="102.00"),
    ]
    causal_prefix = [
        _bar("2026-04-06T14:30:00Z", open_="99.00", high="100.00", low="99.00", close="99.50", volume=100),
        _bar("2026-04-06T15:00:00Z", open_="101.00", high="102.00", low="101.00", close="101.50", volume=100),
        _bar("2026-04-06T15:30:00Z", open_="102.00", high="103.00", low="102.00", close="102.50", volume=100),
        _bar("2026-04-06T16:00:00Z", open_="102.50", high="103.00", low="99.50", close="100.75", volume=200),
        _bar("2026-04-06T16:30:00Z", open_="100.50", high="101.00", low="98.00", close="99.00", volume=150),
    ]
    future = [
        _bar("2026-04-06T17:00:00Z", open_="99.00", high="110.00", low="90.00", close="105.00", volume=999),
        _bar("2026-04-06T17:30:00Z", open_="105.00", high="106.00", low="80.00", close="81.00", volume=999),
    ]

    prefix_setups = engine.generate(h1_bars=h1, m30_bars=causal_prefix)
    full_setups = engine.generate(h1_bars=h1, m30_bars=causal_prefix + future)

    assert [setup.fingerprint() for setup in full_setups[: len(prefix_setups)]] == [
        setup.fingerprint() for setup in prefix_setups
    ]


def test_failed_fvg_skips_when_next_m30_entry_bar_is_missing() -> None:
    config = FailedFVGConfig(
        tick_size=Decimal("0.25"),
        effort_range_mult=Decimal("1.20"),
        effort_volume_mult=Decimal("1.30"),
        atr_window=3,
        volume_window=3,
    )
    engine = FailedFVGSetupEngine(config)
    h1 = [
        _bar("2026-04-06T13:00:00Z", high="100.00", low="95.00"),
        _bar("2026-04-06T14:00:00Z", high="101.00", low="96.00"),
        _bar("2026-04-06T15:00:00Z", high="106.00", low="102.00"),
    ]
    m30_with_gap = [
        _bar("2026-04-06T14:30:00Z", open_="99.00", high="100.00", low="99.00", close="99.50", volume=100),
        _bar("2026-04-06T15:00:00Z", open_="101.00", high="102.00", low="101.00", close="101.50", volume=100),
        _bar("2026-04-06T15:30:00Z", open_="102.00", high="103.00", low="102.00", close="102.50", volume=100),
        _bar("2026-04-06T16:00:00Z", open_="102.50", high="103.00", low="99.50", close="100.75", volume=200),
        _bar("2026-04-06T17:00:00Z", open_="100.50", high="101.00", low="98.00", close="99.00", volume=150),
    ]

    assert engine.generate(h1_bars=h1, m30_bars=m30_with_gap) == []


def test_build_h1_fvgs_does_not_bridge_symbols_or_sessions() -> None:
    h1 = [
        _bar("2026-04-06T13:00:00Z", high="100.00", low="95.00"),
        _bar("2026-04-06T14:00:00Z", high="101.00", low="96.00"),
        Bar(
            ts_event=_ts("2026-04-06T15:00:00Z"),
            symbol="MNQM6",
            cme_session_id="CME_EQ_FUT_2026-04-08",
            open=Decimal("102.00"),
            high=Decimal("106.00"),
            low=Decimal("102.00"),
            close=Decimal("105.00"),
            volume=100,
        ),
    ]

    assert build_h1_fvgs(h1, bar_duration=timedelta(hours=1)) == []


def _bar(
    timestamp: str,
    *,
    open_: str = "100.00",
    high: str,
    low: str,
    close: str = "100.00",
    volume: int = 100,
) -> Bar:
    return Bar(
        ts_event=_ts(timestamp),
        symbol="MNQM6",
        cme_session_id=SESSION_ID,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=volume,
    )


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
