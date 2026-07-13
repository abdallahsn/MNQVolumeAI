from __future__ import annotations

import argparse
import logging
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

import numpy as np
import pandas as pd

try:
    import pyarrow.dataset as ds
except ModuleNotFoundError:
    ds = None


LOGGER = logging.getLogger("fail_fvg_backtest")

# MES-style defaults from the original script.
COST = 2.50
SLIP = 2.50
POINT_VALUE = 5.0
MARGIN = 100.0
RISK_PCT = 0.025
INITIAL = 10_000.0

DAILY_DD_LIMIT = 0.018
MAX_TRADES_PER_DAY = 2
DAILY_SAFETY_MARGIN = 0.8

FVG_WINDOW_MIN = 90
VOL_PRICE_MULT = 1.2
VOL_VOLUME_MULT = 1.3

STOP_BUFFER_POINTS = 0.0
TAKE_PROFIT_R = 4.0
MAX_HOLD_BARS = 12

SESSION_START_HOUR = 3
SESSION_END_HOUR = 16
SKIP_0930_OPEN = True
MARKET_TZ = "America/New_York"

OUTPUT_DIR = Path("fail_fvg_outputs")
TRADES_CSV = "fail_fvg_trades.csv"
SUMMARY_CSV = "fail_fvg_summary.csv"

DEFAULT_FILES = [
    r"C:\Users\Administrator\Documents\2024-01_MES_continuous.parquet",
]

TRADE_COLUMNS = [
    "month",
    "time",
    "signal_time",
    "entry_time",
    "exit_time",
    "fvg_type",
    "signal",
    "direction",
    "contracts",
    "entry",
    "stop",
    "target",
    "exit",
    "risk_points",
    "status",
    "pnl",
    "points",
    "balance",
    "fvg_low",
    "fvg_high",
    "fvg_mid",
    "fvg_available_at",
    "close_vs_mid",
    "close_vs_zone",
    "effort_range_ratio",
    "effort_volume_ratio",
]

SUMMARY_COLUMNS = [
    "month",
    "file",
    "trades",
    "wins",
    "losses",
    "win_rate",
    "net_pnl",
    "return_pct",
    "max_drawdown_pct",
    "max_daily_dd_pct",
    "skipped_missing_entry",
    "skipped_no_contracts",
    "skipped_invalid_risk",
]


@dataclass(frozen=True)
class FVG:
    fvg_id: str
    formed_at: pd.Timestamp
    available_at: pd.Timestamp
    fvg_type: str
    low: float
    high: float

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2.0


@dataclass(frozen=True)
class Signal:
    fvg: FVG
    signal_name: str
    direction: str
    signal_time: pd.Timestamp
    close_vs_mid: float
    close_vs_zone: float
    effort_range_ratio: float
    effort_volume_ratio: float


@dataclass(frozen=True)
class TradeResult:
    status: str
    pnl: float
    gross_points: float
    exit_price: float
    exit_time: pd.Timestamp
    exit_pos: int
    target: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="No-lookahead Failed FVG / Effort Without Result backtest."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Input parquet files. If omitted, DEFAULT_FILES inside this script are used.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory for trades and summary CSV output.",
    )
    parser.add_argument(
        "--point-value",
        type=float,
        default=POINT_VALUE,
        help="Dollar value per point. Use 2.0 for MNQ and 5.0 for MES.",
    )
    parser.add_argument(
        "--cost",
        type=float,
        default=COST,
        help="Round-turn commission cost per contract in dollars.",
    )
    parser.add_argument(
        "--slip",
        type=float,
        default=SLIP,
        help="Round-turn slippage cost per contract in dollars.",
    )
    parser.add_argument(
        "--market-tz",
        default=MARKET_TZ,
        help="Timezone used for session filtering.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def month_from_path(file_path: Path) -> str:
    path_text = str(file_path)
    stem = PureWindowsPath(path_text).stem if "\\" in path_text else file_path.stem
    first_token = stem.split("_")[0]
    if re.fullmatch(r"\d{4}-\d{2}", first_token):
        return first_token
    return stem


def load_trade_data(file_path: Path) -> pd.DataFrame:
    base_columns = ["ts_event", "price", "size"]
    if ds is not None:
        dataset = ds.dataset(str(file_path))
        schema_names = set(dataset.schema.names)
        missing = sorted(set(base_columns) - schema_names)
        if missing:
            raise ValueError(f"{file_path} missing required columns: {missing}")
        has_action = "action" in schema_names
        table = dataset.to_table(
            columns=base_columns + (["action"] if has_action else []),
            filter=ds.field("action") == "T" if has_action else None,
        )
        raw = table.to_pandas()
    else:
        try:
            raw = pd.read_parquet(file_path, columns=base_columns + ["action"])
        except (KeyError, ValueError):
            raw = pd.read_parquet(file_path, columns=base_columns)
        missing = sorted(set(base_columns) - set(raw.columns))
        if missing:
            raise ValueError(f"{file_path} missing required columns: {missing}")
        if "action" in raw.columns:
            raw = raw[raw["action"] == "T"]
        else:
            LOGGER.info("No action column found in %s; assuming canonical trade tape is already action-T only", file_path)

    if raw.empty:
        return pd.DataFrame(columns=["price", "size"])

    if pd.api.types.is_datetime64_any_dtype(raw["ts_event"]):
        ts = pd.to_datetime(raw["ts_event"], utc=True, errors="coerce")
    else:
        ts = pd.to_datetime(raw["ts_event"], unit="ns", utc=True, errors="coerce")

    raw = raw.assign(ts=ts)
    raw = raw.dropna(subset=["ts", "price", "size"])
    raw = raw[(raw["price"] > 0) & (raw["size"] > 0)]
    raw["ts"] = raw["ts"].dt.tz_convert(MARKET_TZ)
    raw = raw.sort_values("ts")
    raw = raw.set_index("ts")
    return raw[["price", "size"]]


def build_bars(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    h1 = trades["price"].resample("1h", label="left", closed="left").ohlc()
    h1 = h1.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c"})
    h1 = h1.dropna()

    m30_price = trades["price"].resample("30min", label="left", closed="left").ohlc()
    m30_volume = trades["size"].resample("30min", label="left", closed="left").sum()
    m30 = m30_price.join(m30_volume.rename("volume"))
    m30 = m30.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c"})
    m30 = m30.dropna(subset=["o", "h", "l", "c"])
    m30["volume"] = m30["volume"].fillna(0.0)
    m30["range"] = m30["h"] - m30["l"]
    m30["atr20"] = m30["range"].shift(1).rolling(20, min_periods=20).mean()
    m30["volume_sma20"] = m30["volume"].shift(1).rolling(20, min_periods=20).mean()
    return h1, m30


def build_h1_fvgs(h1: pd.DataFrame) -> list[FVG]:
    fvgs: list[FVG] = []
    for i in range(2, len(h1)):
        formed_at = h1.index[i]
        available_at = formed_at + pd.Timedelta(hours=1)

        if h1["l"].iloc[i] > h1["h"].iloc[i - 2]:
            bound1 = float(h1["h"].iloc[i - 2])
            bound2 = float(h1["l"].iloc[i])
            fvg_low = min(bound1, bound2)
            fvg_high = max(bound1, bound2)
            fvgs.append(
                FVG(
                    fvg_id=f"{formed_at.isoformat()}_Bull_{fvg_low:.4f}_{fvg_high:.4f}",
                    formed_at=formed_at,
                    available_at=available_at,
                    fvg_type="Bull",
                    low=fvg_low,
                    high=fvg_high,
                )
            )

        if h1["h"].iloc[i] < h1["l"].iloc[i - 2]:
            bound1 = float(h1["h"].iloc[i])
            bound2 = float(h1["l"].iloc[i - 2])
            fvg_low = min(bound1, bound2)
            fvg_high = max(bound1, bound2)
            fvgs.append(
                FVG(
                    fvg_id=f"{formed_at.isoformat()}_Bear_{fvg_low:.4f}_{fvg_high:.4f}",
                    formed_at=formed_at,
                    available_at=available_at,
                    fvg_type="Bear",
                    low=fvg_low,
                    high=fvg_high,
                )
            )
    return fvgs


def is_in_session(ts: pd.Timestamp) -> bool:
    if not (SESSION_START_HOUR <= ts.hour < SESSION_END_HOUR):
        return False
    return not (SKIP_0930_OPEN and ts.hour == 9 and ts.minute == 30)


def overlaps_zone(candle: pd.Series, fvg: FVG) -> bool:
    return float(candle["h"]) >= fvg.low and float(candle["l"]) <= fvg.high


def detect_failed_fvg_signal(
    candle: pd.Series,
    signal_time: pd.Timestamp,
    active_fvgs: Iterable[FVG],
    used_fvg_ids: set[str],
) -> Signal | None:
    candle_range = float(candle["range"])
    atr20 = float(candle["atr20"])
    volume = float(candle["volume"])
    volume_sma20 = float(candle["volume_sma20"])

    if (
        candle_range <= 0
        or not np.isfinite(atr20)
        or atr20 <= 0
        or not np.isfinite(volume_sma20)
        or volume_sma20 <= 0
    ):
        return None

    effort_range_ratio = candle_range / atr20
    effort_volume_ratio = volume / volume_sma20
    if effort_range_ratio <= VOL_PRICE_MULT or effort_volume_ratio <= VOL_VOLUME_MULT:
        return None

    close = float(candle["c"])
    candidates = sorted(active_fvgs, key=lambda item: item.available_at, reverse=True)
    for fvg in candidates:
        if fvg.fvg_id in used_fvg_ids:
            continue
        if fvg.available_at > signal_time:
            continue
        if signal_time - fvg.available_at > pd.Timedelta(minutes=FVG_WINDOW_MIN):
            continue
        if not overlaps_zone(candle, fvg):
            continue

        close_vs_mid = close - fvg.mid
        if fvg.fvg_type == "Bull":
            close_vs_zone = close - fvg.high
            failed = close <= fvg.mid or close < fvg.high
            if failed:
                return Signal(
                    fvg=fvg,
                    signal_name="FAILED_BULL_FVG_SHORT",
                    direction="SHORT",
                    signal_time=signal_time,
                    close_vs_mid=close_vs_mid,
                    close_vs_zone=close_vs_zone,
                    effort_range_ratio=effort_range_ratio,
                    effort_volume_ratio=effort_volume_ratio,
                )
        else:
            close_vs_zone = close - fvg.low
            failed = close >= fvg.mid or close > fvg.low
            if failed:
                return Signal(
                    fvg=fvg,
                    signal_name="FAILED_BEAR_FVG_LONG",
                    direction="LONG",
                    signal_time=signal_time,
                    close_vs_mid=close_vs_mid,
                    close_vs_zone=close_vs_zone,
                    effort_range_ratio=effort_range_ratio,
                    effort_volume_ratio=effort_volume_ratio,
                )

    return None


def calculate_contracts(
    balance: float,
    day_start_balance: float,
    daily_loss_pct: float,
    risk_points: float,
) -> int:
    if balance <= 0 or day_start_balance <= 0 or risk_points <= 0:
        return 0

    remaining_daily_risk = DAILY_DD_LIMIT - daily_loss_pct
    if remaining_daily_risk <= 0:
        return 0

    risk_cash = min(
        balance * RISK_PCT,
        remaining_daily_risk * day_start_balance * DAILY_SAFETY_MARGIN,
    )
    loss_per_contract = risk_points * POINT_VALUE + COST + SLIP
    if risk_cash <= 0 or loss_per_contract <= 0:
        return 0

    risk_contracts = int(math.floor(risk_cash / loss_per_contract))
    margin_contracts = int(math.floor(balance / MARGIN))
    return min(risk_contracts, margin_contracts)


def execute_trade(
    m30: pd.DataFrame,
    entry_pos: int,
    entry: float,
    stop: float,
    direction: str,
    contracts: int,
) -> TradeResult:
    risk_points = abs(entry - stop)
    if direction == "LONG":
        target = entry + (risk_points * TAKE_PROFIT_R)
    else:
        target = entry - (risk_points * TAKE_PROFIT_R)

    end_pos = min(len(m30), entry_pos + MAX_HOLD_BARS)
    future = m30.iloc[entry_pos:end_pos]
    if future.empty:
        raise ValueError("execute_trade called without future bars after entry")

    status = "TIME_OUT"
    exit_price = float(future.iloc[-1]["c"])
    exit_time = future.index[-1]
    exit_pos = end_pos - 1

    for offset, (bar_time, bar) in enumerate(future.iterrows()):
        bar_high = float(bar["h"])
        bar_low = float(bar["l"])
        pos = entry_pos + offset

        if direction == "LONG":
            stop_hit = bar_low <= stop
            target_hit = bar_high >= target
            if stop_hit:
                status = "STOP_LOSS"
                exit_price = stop
                exit_time = bar_time
                exit_pos = pos
                break
            if target_hit:
                status = "TAKE_PROFIT"
                exit_price = target
                exit_time = bar_time
                exit_pos = pos
                break
        else:
            stop_hit = bar_high >= stop
            target_hit = bar_low <= target
            if stop_hit:
                status = "STOP_LOSS"
                exit_price = stop
                exit_time = bar_time
                exit_pos = pos
                break
            if target_hit:
                status = "TAKE_PROFIT"
                exit_price = target
                exit_time = bar_time
                exit_pos = pos
                break

    gross_points = exit_price - entry if direction == "LONG" else entry - exit_price

    gross = contracts * gross_points * POINT_VALUE
    net = gross - contracts * (COST + SLIP)
    return TradeResult(
        status=status,
        pnl=net,
        gross_points=gross_points,
        exit_price=exit_price,
        exit_time=exit_time,
        exit_pos=exit_pos,
        target=target,
    )


def empty_summary(file_path: Path, month: str) -> dict[str, object]:
    return {
        "month": month,
        "file": str(file_path),
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "net_pnl": 0.0,
        "return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "max_daily_dd_pct": 0.0,
        "skipped_missing_entry": 0,
        "skipped_no_contracts": 0,
        "skipped_invalid_risk": 0,
    }


def backtest_file(file_path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    month = month_from_path(file_path)
    summary = empty_summary(file_path, month)

    if not file_path.exists():
        LOGGER.warning("Skipping missing file: %s", file_path)
        return [], summary

    trades_df = load_trade_data(file_path)
    if trades_df.empty:
        LOGGER.warning("Skipping empty trade file after filtering action == 'T': %s", file_path)
        return [], summary

    h1, m30 = build_bars(trades_df)
    if len(h1) < 3 or len(m30) < 22:
        LOGGER.warning("Not enough bars for %s", file_path)
        return [], summary

    fvgs = build_h1_fvgs(h1)
    if not fvgs:
        LOGGER.info("%s: no H1 FVGs found", month)
        return [], summary

    balance = INITIAL
    peak = INITIAL
    max_drawdown = 0.0
    max_daily_dd = 0.0

    current_day = None
    day_start_balance = INITIAL
    trades_today = 0
    day_locked = False

    skipped_missing_entry = 0
    skipped_no_contracts = 0
    skipped_invalid_risk = 0

    used_fvg_ids: set[str] = set()
    rows: list[dict[str, object]] = []

    j = 20
    while j < len(m30) - 1:
        signal_time = m30.index[j]
        if not is_in_session(signal_time):
            j += 1
            continue

        entry_time = signal_time + pd.Timedelta(minutes=30)
        entry_pos = j + 1
        if entry_pos >= len(m30) or m30.index[entry_pos] != entry_time:
            skipped_missing_entry += 1
            j += 1
            continue

        trade_day = entry_time.date()
        if current_day != trade_day:
            current_day = trade_day
            day_start_balance = balance
            trades_today = 0
            day_locked = False

        if day_locked or trades_today >= MAX_TRADES_PER_DAY:
            j += 1
            continue

        daily_loss_pct = max(0.0, (day_start_balance - balance) / day_start_balance)
        if daily_loss_pct >= DAILY_DD_LIMIT:
            day_locked = True
            j += 1
            continue

        candle = m30.iloc[j]
        active_fvgs = [
            fvg
            for fvg in fvgs
            if fvg.available_at <= signal_time
            and signal_time - fvg.available_at <= pd.Timedelta(minutes=FVG_WINDOW_MIN)
        ]
        signal = detect_failed_fvg_signal(candle, signal_time, active_fvgs, used_fvg_ids)
        if signal is None:
            j += 1
            continue

        entry = float(m30.iloc[entry_pos]["o"])
        if signal.direction == "SHORT":
            stop = float(candle["h"]) + STOP_BUFFER_POINTS
            risk_points = stop - entry
        else:
            stop = float(candle["l"]) - STOP_BUFFER_POINTS
            risk_points = entry - stop

        if risk_points <= 0 or not np.isfinite(risk_points):
            skipped_invalid_risk += 1
            j += 1
            continue

        contracts = calculate_contracts(
            balance=balance,
            day_start_balance=day_start_balance,
            daily_loss_pct=daily_loss_pct,
            risk_points=risk_points,
        )
        if contracts <= 0:
            skipped_no_contracts += 1
            j += 1
            continue

        result = execute_trade(
            m30=m30,
            entry_pos=entry_pos,
            entry=entry,
            stop=stop,
            direction=signal.direction,
            contracts=contracts,
        )

        used_fvg_ids.add(signal.fvg.fvg_id)
        balance += result.pnl
        peak = max(peak, balance)
        max_drawdown = max(max_drawdown, peak - balance)

        daily_dd = max(0.0, (day_start_balance - balance) / day_start_balance)
        max_daily_dd = max(max_daily_dd, daily_dd)
        if daily_dd >= DAILY_DD_LIMIT:
            day_locked = True

        trades_today += 1
        rows.append(
            {
                "month": month,
                "time": entry_time.isoformat(),
                "signal_time": signal_time.isoformat(),
                "entry_time": entry_time.isoformat(),
                "exit_time": result.exit_time.isoformat(),
                "fvg_type": signal.fvg.fvg_type,
                "signal": signal.signal_name,
                "direction": signal.direction,
                "contracts": contracts,
                "entry": round(entry, 4),
                "stop": round(stop, 4),
                "target": round(result.target, 4),
                "exit": round(result.exit_price, 4),
                "risk_points": round(risk_points, 4),
                "status": result.status,
                "pnl": round(result.pnl, 2),
                "points": round(result.gross_points, 4),
                "balance": round(balance, 2),
                "fvg_low": round(signal.fvg.low, 4),
                "fvg_high": round(signal.fvg.high, 4),
                "fvg_mid": round(signal.fvg.mid, 4),
                "fvg_available_at": signal.fvg.available_at.isoformat(),
                "close_vs_mid": round(signal.close_vs_mid, 4),
                "close_vs_zone": round(signal.close_vs_zone, 4),
                "effort_range_ratio": round(signal.effort_range_ratio, 4),
                "effort_volume_ratio": round(signal.effort_volume_ratio, 4),
            }
        )

        # One active position at a time. This prevents future trade P&L from
        # influencing signals that occurred before the simulated exit.
        j = max(result.exit_pos + 1, j + 1)

    if rows:
        out = pd.DataFrame(rows)
        wins = int((out["pnl"] > 0).sum())
        losses = int((out["pnl"] <= 0).sum())
        net_pnl = float(balance - INITIAL)
        summary.update(
            {
                "trades": len(out),
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / len(out) * 100.0, 2),
                "net_pnl": round(net_pnl, 2),
                "return_pct": round(net_pnl / INITIAL * 100.0, 2),
                "max_drawdown_pct": round((max_drawdown / peak * 100.0) if peak > 0 else 0.0, 2),
                "max_daily_dd_pct": round(max_daily_dd * 100.0, 2),
            }
        )

    summary.update(
        {
            "skipped_missing_entry": skipped_missing_entry,
            "skipped_no_contracts": skipped_no_contracts,
            "skipped_invalid_risk": skipped_invalid_risk,
        }
    )
    return rows, summary


def save_outputs(
    trades: list[dict[str, object]],
    summaries: list[dict[str, object]],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trades_path = output_dir / TRADES_CSV
    summary_path = output_dir / SUMMARY_CSV

    trades_df = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    summary_df = pd.DataFrame(summaries, columns=SUMMARY_COLUMNS)
    trades_df.to_csv(trades_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    return trades_path, summary_path


def print_summary(summary_df: pd.DataFrame) -> None:
    if summary_df.empty:
        print("No files processed.")
        return

    print("\nFAILED FVG BACKTEST SUMMARY")
    print("-" * 110)
    for _, row in summary_df.iterrows():
        print(
            f"{row['month']:<12} | Trades:{int(row['trades']):<3} | "
            f"Win:{row['win_rate']:>6.2f}% | Ret:{row['return_pct']:>7.2f}% | "
            f"Net:${row['net_pnl']:>10,.2f} | MaxDD:{row['max_drawdown_pct']:>6.2f}% | "
            f"DayDD:{row['max_daily_dd_pct']:>5.2f}%"
        )


def main() -> None:
    global COST, MARKET_TZ, POINT_VALUE, SLIP

    args = parse_args()
    COST = args.cost
    SLIP = args.slip
    POINT_VALUE = args.point_value
    MARKET_TZ = args.market_tz
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    files = [Path(item) for item in (args.files if args.files else DEFAULT_FILES)]
    all_trades: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    for file_path in files:
        try:
            trades, summary = backtest_file(file_path)
        except Exception as exc:
            LOGGER.exception("Failed processing %s: %s", file_path, exc)
            month = month_from_path(file_path)
            summary = empty_summary(file_path, month)
        all_trades.extend(trades)
        summaries.append(summary)

    output_dir = Path(args.output_dir)
    trades_path, summary_path = save_outputs(all_trades, summaries, output_dir)
    print_summary(pd.DataFrame(summaries, columns=SUMMARY_COLUMNS))
    print(f"\nSaved trades:  {trades_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
