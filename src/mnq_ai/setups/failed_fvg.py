"""Deterministic Failed FVG setup generation.

This module consumes already-built OHLCV bars. It does not read order-book depth
and it does not learn direction: direction is fixed by the failed-FVG rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from hashlib import sha256
from typing import Literal

FVGType = Literal["BULL", "BEAR"]
EntrySide = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class Bar:
    """Causal OHLCV bar used by deterministic setup generation."""

    ts_event: datetime
    symbol: str
    cme_session_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    @property
    def range(self) -> Decimal:
        return self.high - self.low


@dataclass(frozen=True)
class FVG:
    """Three-bar Fair Value Gap with explicit availability time."""

    fvg_id: str
    formed_at: datetime
    available_at: datetime
    symbol: str
    cme_session_id: str
    fvg_type: FVGType
    low: Decimal
    high: Decimal

    @property
    def mid(self) -> Decimal:
        return (self.low + self.high) / Decimal("2")


@dataclass(frozen=True)
class SetupCandidate:
    """Deterministic setup candidate emitted for a meta-model to take or skip."""

    setup_id: str
    ts_event: datetime
    symbol: str
    cme_session_id: str
    setup_type: str
    entry_side: EntrySide
    reference_level: Decimal
    entry_price: Decimal
    entry_timestamp: datetime
    structural_invalidation: Decimal
    stop_price: Decimal
    target_1: Decimal
    target_2: Decimal
    target_3: Decimal
    max_holding_bars: int
    max_holding_seconds: int
    reason_codes: tuple[str, ...]
    feature_timestamp: datetime
    setup_version: str
    fvg_id: str
    fvg_low: Decimal
    fvg_high: Decimal
    effort_range_ratio: Decimal
    effort_volume_ratio: Decimal

    def fingerprint(self) -> tuple[object, ...]:
        """Return stable fields used by causality/invariance tests."""

        return (
            self.setup_id,
            self.ts_event,
            self.setup_type,
            self.entry_side,
            self.entry_price,
            self.stop_price,
            self.target_1,
            self.target_2,
            self.target_3,
            self.reason_codes,
        )


@dataclass(frozen=True)
class FailedFVGConfig:
    """Parameters for Failed FVG setup generation."""

    tick_size: Decimal = Decimal("0.25")
    h1_bar_duration: timedelta = timedelta(hours=1)
    m30_bar_duration: timedelta = timedelta(minutes=30)
    fvg_window: timedelta = timedelta(minutes=90)
    effort_range_mult: Decimal = Decimal("1.20")
    effort_volume_mult: Decimal = Decimal("1.30")
    atr_window: int = 20
    volume_window: int = 20
    stop_buffer_ticks: int = 0
    take_profit_r: tuple[Decimal, Decimal, Decimal] = (
        Decimal("1"),
        Decimal("2"),
        Decimal("4"),
    )
    max_holding_bars: int = 12
    setup_version: str = "failed_fvg_v1"

    def validated(self) -> FailedFVGConfig:
        if self.tick_size <= 0:
            raise ValueError("tick_size must be positive")
        if self.atr_window <= 0:
            raise ValueError("atr_window must be positive")
        if self.volume_window <= 0:
            raise ValueError("volume_window must be positive")
        if self.effort_range_mult <= 0 or self.effort_volume_mult <= 0:
            raise ValueError("effort multipliers must be positive")
        if self.stop_buffer_ticks < 0:
            raise ValueError("stop_buffer_ticks cannot be negative")
        if self.max_holding_bars <= 0:
            raise ValueError("max_holding_bars must be positive")
        if any(item <= 0 for item in self.take_profit_r):
            raise ValueError("take_profit_r values must be positive")
        return self


class FailedFVGSetupEngine:
    """Generate deterministic Failed FVG setup candidates from OHLCV bars."""

    def __init__(self, config: FailedFVGConfig | None = None) -> None:
        self.config = (config or FailedFVGConfig()).validated()

    def generate(self, *, h1_bars: list[Bar], m30_bars: list[Bar]) -> list[SetupCandidate]:
        h1 = sorted(h1_bars, key=lambda bar: bar.ts_event)
        m30 = sorted(m30_bars, key=lambda bar: bar.ts_event)
        fvgs = build_h1_fvgs(h1, bar_duration=self.config.h1_bar_duration)
        used_fvg_ids: set[str] = set()
        setups: list[SetupCandidate] = []

        first_signal_index = max(self.config.atr_window, self.config.volume_window)
        for index in range(first_signal_index, len(m30) - 1):
            signal_bar = m30[index]
            entry_bar = m30[index + 1]
            expected_entry_time = signal_bar.ts_event + self.config.m30_bar_duration
            if (
                entry_bar.ts_event != expected_entry_time
                or entry_bar.symbol != signal_bar.symbol
                or entry_bar.cme_session_id != signal_bar.cme_session_id
            ):
                continue
            active_fvgs = [
                fvg
                for fvg in fvgs
                if fvg.symbol == signal_bar.symbol
                and fvg.cme_session_id == signal_bar.cme_session_id
                and fvg.available_at <= signal_bar.ts_event
                and signal_bar.ts_event - fvg.available_at <= self.config.fvg_window
                and fvg.fvg_id not in used_fvg_ids
            ]
            if not active_fvgs:
                continue
            effort = self._effort_ratios(m30, index)
            if effort is None:
                continue
            effort_range_ratio, effort_volume_ratio = effort
            if (
                effort_range_ratio <= self.config.effort_range_mult
                or effort_volume_ratio <= self.config.effort_volume_mult
            ):
                continue

            for fvg in sorted(active_fvgs, key=lambda item: item.available_at, reverse=True):
                setup = self._candidate_from_failed_fvg(
                    fvg=fvg,
                    signal_bar=signal_bar,
                    entry_bar=entry_bar,
                    effort_range_ratio=effort_range_ratio,
                    effort_volume_ratio=effort_volume_ratio,
                )
                if setup is None:
                    continue
                setups.append(setup)
                used_fvg_ids.add(fvg.fvg_id)
                break
        return setups

    def _effort_ratios(
        self,
        bars: list[Bar],
        signal_index: int,
    ) -> tuple[Decimal, Decimal] | None:
        signal = bars[signal_index]
        if signal.range <= 0 or signal.volume <= 0:
            return None
        atr_start = signal_index - self.config.atr_window
        volume_start = signal_index - self.config.volume_window
        if atr_start < 0 or volume_start < 0:
            return None

        trailing_ranges = [bar.range for bar in bars[atr_start:signal_index]]
        trailing_volumes = [bar.volume for bar in bars[volume_start:signal_index]]
        if any(item <= 0 for item in trailing_ranges) or any(item <= 0 for item in trailing_volumes):
            return None

        atr = sum(trailing_ranges, Decimal("0")) / Decimal(len(trailing_ranges))
        volume_sma = Decimal(sum(trailing_volumes)) / Decimal(len(trailing_volumes))
        if atr <= 0 or volume_sma <= 0:
            return None
        return signal.range / atr, Decimal(signal.volume) / volume_sma

    def _candidate_from_failed_fvg(
        self,
        *,
        fvg: FVG,
        signal_bar: Bar,
        entry_bar: Bar,
        effort_range_ratio: Decimal,
        effort_volume_ratio: Decimal,
    ) -> SetupCandidate | None:
        if not _overlaps_zone(signal_bar, fvg):
            return None

        if fvg.fvg_type == "BULL":
            failed = signal_bar.close <= fvg.mid or signal_bar.close < fvg.high
            if not failed:
                return None
            return self._build_candidate(
                fvg=fvg,
                signal_bar=signal_bar,
                entry_bar=entry_bar,
                setup_type="FAILED_BULL_FVG",
                entry_side="SHORT",
                structural_invalidation=signal_bar.high,
                effort_range_ratio=effort_range_ratio,
                effort_volume_ratio=effort_volume_ratio,
            )

        failed = signal_bar.close >= fvg.mid or signal_bar.close > fvg.low
        if not failed:
            return None
        return self._build_candidate(
            fvg=fvg,
            signal_bar=signal_bar,
            entry_bar=entry_bar,
            setup_type="FAILED_BEAR_FVG",
            entry_side="LONG",
            structural_invalidation=signal_bar.low,
            effort_range_ratio=effort_range_ratio,
            effort_volume_ratio=effort_volume_ratio,
        )

    def _build_candidate(
        self,
        *,
        fvg: FVG,
        signal_bar: Bar,
        entry_bar: Bar,
        setup_type: str,
        entry_side: EntrySide,
        structural_invalidation: Decimal,
        effort_range_ratio: Decimal,
        effort_volume_ratio: Decimal,
    ) -> SetupCandidate | None:
        entry = _round_to_tick(entry_bar.open, self.config.tick_size)
        buffer = self.config.tick_size * self.config.stop_buffer_ticks
        if entry_side == "SHORT":
            stop = _round_up_to_tick(structural_invalidation + buffer, self.config.tick_size)
            risk = stop - entry
            if risk <= 0:
                return None
            targets = tuple(_round_to_tick(entry - (risk * r), self.config.tick_size) for r in self.config.take_profit_r)
            reason_prefix = "FAILED_BULL_FVG_SHORT"
        else:
            stop = _round_down_to_tick(structural_invalidation - buffer, self.config.tick_size)
            risk = entry - stop
            if risk <= 0:
                return None
            targets = tuple(_round_to_tick(entry + (risk * r), self.config.tick_size) for r in self.config.take_profit_r)
            reason_prefix = "FAILED_BEAR_FVG_LONG"

        setup_id = _setup_id(
            self.config.setup_version,
            fvg.fvg_id,
            signal_bar.ts_event.isoformat(),
            entry_side,
            str(entry),
        )
        return SetupCandidate(
            setup_id=setup_id,
            ts_event=signal_bar.ts_event,
            symbol=signal_bar.symbol,
            cme_session_id=signal_bar.cme_session_id,
            setup_type=setup_type,
            entry_side=entry_side,
            reference_level=fvg.mid,
            entry_price=entry,
            entry_timestamp=entry_bar.ts_event,
            structural_invalidation=structural_invalidation,
            stop_price=stop,
            target_1=targets[0],
            target_2=targets[1],
            target_3=targets[2],
            max_holding_bars=self.config.max_holding_bars,
            max_holding_seconds=int(
                self.config.m30_bar_duration.total_seconds() * self.config.max_holding_bars
            ),
            reason_codes=(
                reason_prefix,
                "FVG_OVERLAP_CONFIRMED",
                "EFFORT_WITHOUT_RESULT",
            ),
            feature_timestamp=signal_bar.ts_event,
            setup_version=self.config.setup_version,
            fvg_id=fvg.fvg_id,
            fvg_low=fvg.low,
            fvg_high=fvg.high,
            effort_range_ratio=effort_range_ratio,
            effort_volume_ratio=effort_volume_ratio,
        )


def build_h1_fvgs(bars: list[Bar], *, bar_duration: timedelta) -> list[FVG]:
    """Build three-bar FVGs and expose them only after the forming bar closes."""

    ordered = sorted(bars, key=lambda bar: bar.ts_event)
    fvgs: list[FVG] = []
    for index in range(2, len(ordered)):
        current = ordered[index]
        prior_2 = ordered[index - 2]
        formed_at = current.ts_event
        available_at = formed_at + bar_duration
        if current.low > prior_2.high:
            low = min(prior_2.high, current.low)
            high = max(prior_2.high, current.low)
            fvgs.append(_fvg(current, "BULL", low, high, formed_at, available_at))
        if current.high < prior_2.low:
            low = min(current.high, prior_2.low)
            high = max(current.high, prior_2.low)
            fvgs.append(_fvg(current, "BEAR", low, high, formed_at, available_at))
    return fvgs


def _fvg(
    bar: Bar,
    fvg_type: FVGType,
    low: Decimal,
    high: Decimal,
    formed_at: datetime,
    available_at: datetime,
) -> FVG:
    fvg_id = _setup_id(
        "fvg",
        bar.symbol,
        bar.cme_session_id,
        formed_at.isoformat(),
        fvg_type,
        str(low),
        str(high),
    )
    return FVG(
        fvg_id=fvg_id,
        formed_at=formed_at,
        available_at=available_at,
        symbol=bar.symbol,
        cme_session_id=bar.cme_session_id,
        fvg_type=fvg_type,
        low=low,
        high=high,
    )


def _overlaps_zone(bar: Bar, fvg: FVG) -> bool:
    return bar.high >= fvg.low and bar.low <= fvg.high


def _round_to_tick(price: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (price / tick_size).to_integral_value(rounding=ROUND_HALF_UP)
    return ticks * tick_size


def _round_up_to_tick(price: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (price / tick_size).to_integral_value(rounding=ROUND_CEILING)
    return ticks * tick_size


def _round_down_to_tick(price: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (price / tick_size).to_integral_value(rounding=ROUND_FLOOR)
    return ticks * tick_size


def _setup_id(*parts: str) -> str:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"setup_{digest}"
