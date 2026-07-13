"""Deterministic QEP technical setup generation.

This is a causal Python translation of the executable core in the supplied
MT5 EA: RSI/MACD determine side, ATR determines stop distance, and entry is
delayed until the next completed M30 bar open.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from hashlib import sha256

from mnq_ai.setups.failed_fvg import Bar, EntrySide, SetupCandidate


@dataclass(frozen=True)
class QEPTechnicalConfig:
    """Parameters for the QEP RSI/MACD/ATR setup translation."""

    tick_size: Decimal = Decimal("0.25")
    m30_bar_duration: timedelta = timedelta(minutes=30)
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_window: int = 14
    atr_stop_mult: Decimal = Decimal("2")
    stop_buffer_ticks: int = 0
    take_profit_r: tuple[Decimal, Decimal, Decimal] = (
        Decimal("1.5"),
        Decimal("3"),
        Decimal("4.5"),
    )
    max_holding_bars: int = 12
    setup_version: str = "qep_technical_v1"

    def validated(self) -> QEPTechnicalConfig:
        if self.tick_size <= 0:
            raise ValueError("tick_size must be positive")
        if self.m30_bar_duration.total_seconds() <= 0:
            raise ValueError("m30_bar_duration must be positive")
        if self.rsi_period <= 0:
            raise ValueError("rsi_period must be positive")
        if self.macd_fast <= 0 or self.macd_slow <= 0 or self.macd_signal <= 0:
            raise ValueError("MACD periods must be positive")
        if self.macd_fast >= self.macd_slow:
            raise ValueError("macd_fast must be smaller than macd_slow")
        if self.atr_window <= 0:
            raise ValueError("atr_window must be positive")
        if self.atr_stop_mult <= 0:
            raise ValueError("atr_stop_mult must be positive")
        if self.stop_buffer_ticks < 0:
            raise ValueError("stop_buffer_ticks cannot be negative")
        if any(item <= 0 for item in self.take_profit_r):
            raise ValueError("take_profit_r values must be positive")
        if self.max_holding_bars <= 0:
            raise ValueError("max_holding_bars must be positive")
        return self


class QEPTechnicalSetupEngine:
    """Generate deterministic QEP technical setup candidates from M30 bars."""

    def __init__(self, config: QEPTechnicalConfig | None = None) -> None:
        self.config = (config or QEPTechnicalConfig()).validated()

    def generate(self, *, m30_bars: list[Bar]) -> list[SetupCandidate]:
        bars = sorted(m30_bars, key=lambda bar: bar.ts_event)
        if len(bars) < 2:
            return []

        closes = [bar.close for bar in bars]
        rsi_values = _rsi_values(closes, self.config.rsi_period)
        macd_line, macd_signal = _macd_values(
            closes,
            fast_period=self.config.macd_fast,
            slow_period=self.config.macd_slow,
            signal_period=self.config.macd_signal,
        )
        atr_values = _atr_values(bars, self.config.atr_window)
        first_signal_index = max(
            self.config.rsi_period,
            self.config.atr_window,
            self.config.macd_slow + self.config.macd_signal - 2,
        )

        setups: list[SetupCandidate] = []
        for index in range(first_signal_index, len(bars) - 1):
            signal_bar = bars[index]
            entry_bar = bars[index + 1]
            expected_entry_time = signal_bar.ts_event + self.config.m30_bar_duration
            if (
                entry_bar.ts_event != expected_entry_time
                or entry_bar.symbol != signal_bar.symbol
                or entry_bar.cme_session_id != signal_bar.cme_session_id
            ):
                continue

            rsi = rsi_values[index]
            macd = macd_line[index]
            signal = macd_signal[index]
            atr = atr_values[index]
            if rsi is None or macd is None or signal is None or atr is None or atr <= 0:
                continue

            side = _entry_side(rsi=rsi, macd=macd, macd_signal=signal)
            if side is None:
                continue

            setup = self._build_candidate(
                signal_bar=signal_bar,
                entry_bar=entry_bar,
                entry_side=side,
                atr=atr,
            )
            if setup is not None:
                setups.append(setup)
        return setups

    def _build_candidate(
        self,
        *,
        signal_bar: Bar,
        entry_bar: Bar,
        entry_side: EntrySide,
        atr: Decimal,
    ) -> SetupCandidate | None:
        entry = _round_to_tick(entry_bar.open, self.config.tick_size)
        buffer = self.config.tick_size * self.config.stop_buffer_ticks
        stop_distance = atr * self.config.atr_stop_mult
        if entry_side == "LONG":
            stop = _round_down_to_tick(entry - stop_distance - buffer, self.config.tick_size)
            risk = entry - stop
            if risk <= 0:
                return None
            targets = tuple(_round_to_tick(entry + (risk * r), self.config.tick_size) for r in self.config.take_profit_r)
            reason_codes = ("QEP_RSI_ABOVE_50", "QEP_MACD_BULLISH_POSITIVE", _atr_reason(self.config.atr_stop_mult))
        else:
            stop = _round_up_to_tick(entry + stop_distance + buffer, self.config.tick_size)
            risk = stop - entry
            if risk <= 0:
                return None
            targets = tuple(_round_to_tick(entry - (risk * r), self.config.tick_size) for r in self.config.take_profit_r)
            reason_codes = ("QEP_RSI_BELOW_50", "QEP_MACD_BEARISH_NEGATIVE", _atr_reason(self.config.atr_stop_mult))

        setup_id = _setup_id(
            self.config.setup_version,
            signal_bar.ts_event.isoformat(),
            entry_side,
            str(entry),
        )
        return SetupCandidate(
            setup_id=setup_id,
            ts_event=signal_bar.ts_event,
            symbol=signal_bar.symbol,
            cme_session_id=signal_bar.cme_session_id,
            setup_type="QEP_TECHNICAL",
            entry_side=entry_side,
            reference_level=signal_bar.close,
            entry_price=entry,
            entry_timestamp=entry_bar.ts_event,
            structural_invalidation=stop,
            stop_price=stop,
            target_1=targets[0],
            target_2=targets[1],
            target_3=targets[2],
            max_holding_bars=self.config.max_holding_bars,
            max_holding_seconds=int(self.config.m30_bar_duration.total_seconds() * self.config.max_holding_bars),
            reason_codes=reason_codes,
            feature_timestamp=signal_bar.ts_event,
            setup_version=self.config.setup_version,
            fvg_id="QEP_TECHNICAL_NA",
            fvg_low=signal_bar.low,
            fvg_high=signal_bar.high,
            effort_range_ratio=signal_bar.range / atr if atr > 0 else Decimal("0"),
            effort_volume_ratio=Decimal("0"),
        )


def _entry_side(*, rsi: Decimal, macd: Decimal, macd_signal: Decimal) -> EntrySide | None:
    if rsi > Decimal("50") and macd > macd_signal and macd > 0:
        return "LONG"
    if rsi < Decimal("50") and macd < macd_signal and macd < 0:
        return "SHORT"
    return None


def _rsi_values(closes: list[Decimal], period: int) -> list[Decimal | None]:
    values: list[Decimal | None] = [None] * len(closes)
    for index in range(period, len(closes)):
        changes = [closes[pos] - closes[pos - 1] for pos in range(index - period + 1, index + 1)]
        gains = [change for change in changes if change > 0]
        losses = [-change for change in changes if change < 0]
        avg_gain = sum(gains, Decimal("0")) / Decimal(period)
        avg_loss = sum(losses, Decimal("0")) / Decimal(period)
        if avg_loss == 0:
            values[index] = Decimal("100") if avg_gain > 0 else Decimal("50")
            continue
        rs = avg_gain / avg_loss
        values[index] = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
    return values


def _macd_values(
    closes: list[Decimal],
    *,
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> tuple[list[Decimal], list[Decimal]]:
    if not closes:
        return [], []
    fast = _ema_values(closes, fast_period)
    slow = _ema_values(closes, slow_period)
    macd_line = [fast_item - slow_item for fast_item, slow_item in zip(fast, slow, strict=True)]
    signal_line = _ema_values(macd_line, signal_period)
    return macd_line, signal_line


def _ema_values(values: list[Decimal], period: int) -> list[Decimal]:
    alpha = Decimal("2") / Decimal(period + 1)
    output: list[Decimal] = []
    ema: Decimal | None = None
    for value in values:
        ema = value if ema is None else ((value - ema) * alpha) + ema
        output.append(ema)
    return output


def _atr_values(bars: list[Bar], period: int) -> list[Decimal | None]:
    true_ranges: list[Decimal] = []
    for index, bar in enumerate(bars):
        if index == 0:
            true_ranges.append(bar.range)
            continue
        previous_close = bars[index - 1].close
        true_ranges.append(
            max(
                bar.range,
                abs(bar.high - previous_close),
                abs(bar.low - previous_close),
            )
        )

    values: list[Decimal | None] = [None] * len(bars)
    for index in range(period, len(bars)):
        window = true_ranges[index - period + 1 : index + 1]
        if any(item <= 0 for item in window):
            continue
        values[index] = sum(window, Decimal("0")) / Decimal(period)
    return values


def _round_to_tick(value: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (value / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return ticks * tick_size


def _round_up_to_tick(value: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (value / tick_size).quantize(Decimal("1"), rounding=ROUND_CEILING)
    return ticks * tick_size


def _round_down_to_tick(value: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (value / tick_size).quantize(Decimal("1"), rounding=ROUND_FLOOR)
    return ticks * tick_size


def _setup_id(*parts: str) -> str:
    payload = "|".join(parts)
    return sha256(payload.encode("utf-8")).hexdigest()


def _atr_reason(value: Decimal) -> str:
    normalized = value.normalize()
    return f"QEP_ATR_STOP_{normalized}X"
