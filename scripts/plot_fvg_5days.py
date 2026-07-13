from __future__ import annotations

import argparse
import math
import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pyarrow.dataset as pads
import pyarrow.parquet as pq


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an interactive MNQ candlestick chart, detect 3-candle FVGs, "
            "and overlay failed-FVG setup candidates."
        )
    )
    parser.add_argument(
        "--trade-tape",
        required=True,
        type=Path,
        help="Phase-1 trade-tape Parquet file or dataset directory.",
    )
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="setup_candidates.parquet path.",
    )
    parser.add_argument(
        "--output",
        default=Path("artifacts/charts/mnq_5days_fvg.html"),
        type=Path,
        help="Output interactive HTML chart.",
    )
    parser.add_argument(
        "--timeframe",
        default="30min",
        help="Pandas bar frequency, for example 30min, 15min, or 5min.",
    )
    parser.add_argument(
        "--symbol",
        default=None,
        help="Optional symbol filter, for example MNQM6.",
    )
    parser.add_argument(
        "--max-fvgs",
        type=int,
        default=300,
        help="Maximum raw FVG rectangles to draw. Newest FVGs are retained.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the generated HTML automatically.",
    )
    return parser.parse_args()


def load_trade_tape(path: Path, symbol: str | None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Trade-tape path not found: {path}")

    dataset = pads.dataset(
        str(path),
        format="parquet",
        partitioning="hive" if path.is_dir() else None,
    )
    available = set(dataset.schema.names)
    required = {"ts_event", "price"}
    missing = required - available
    if missing:
        raise ValueError(
            f"Trade tape is missing required columns: {sorted(missing)}. "
            f"Available columns: {sorted(available)}"
        )

    columns = ["ts_event", "price"]
    if "size" in available:
        columns.append("size")
    if "symbol" in available:
        columns.append("symbol")

    filter_expr = None
    if symbol is not None:
        if "symbol" not in available:
            raise ValueError(
                "--symbol was supplied, but the trade tape has no symbol column or Hive symbol partition."
            )
        filter_expr = pads.field("symbol") == symbol

    table = dataset.to_table(columns=columns, filter=filter_expr)
    trades = table.to_pandas()

    trades["ts_event"] = pd.to_datetime(trades["ts_event"], utc=True, errors="coerce")
    trades["price"] = pd.to_numeric(trades["price"], errors="coerce")

    if "size" not in trades.columns:
        trades["size"] = 0
    trades["size"] = pd.to_numeric(trades["size"], errors="coerce").fillna(0)

    trades = trades.dropna(subset=["ts_event", "price"])
    trades = trades.sort_values("ts_event", kind="stable")

    if trades.empty:
        raise ValueError("No valid trades remained after filtering.")

    return trades


def build_candles(trades: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    indexed = trades.set_index("ts_event")
    bars = indexed.resample(
        timeframe,
        label="left",
        closed="left",
        origin="epoch",
    ).agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("size", "sum"),
        trades=("price", "size"),
    )

    bars = bars.dropna(subset=["open", "high", "low", "close"]).copy()
    if bars.empty:
        raise ValueError("No candles were produced. Check the requested timeframe.")
    return bars


def first_full_fill_index(
    bars: pd.DataFrame,
    start_pos: int,
    kind: str,
    zone_low: float,
    zone_high: float,
) -> int | None:
    for pos in range(start_pos + 1, len(bars)):
        if kind == "BULL_FVG" and float(bars.iloc[pos]["low"]) <= zone_low:
            return pos
        if kind == "BEAR_FVG" and float(bars.iloc[pos]["high"]) >= zone_high:
            return pos
    return None


def detect_fvgs(bars: pd.DataFrame, bar_delta: pd.Timedelta) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for pos in range(2, len(bars)):
        current = bars.iloc[pos]
        two_back = bars.iloc[pos - 2]
        start_time = bars.index[pos]

        # Bullish FVG: current candle low is above candle i-2 high.
        if float(current["low"]) > float(two_back["high"]):
            zone_low = float(two_back["high"])
            zone_high = float(current["low"])
            kind = "BULL_FVG"
        # Bearish FVG: current candle high is below candle i-2 low.
        elif float(current["high"]) < float(two_back["low"]):
            zone_low = float(current["high"])
            zone_high = float(two_back["low"])
            kind = "BEAR_FVG"
        else:
            continue

        fill_pos = first_full_fill_index(bars, pos, kind, zone_low, zone_high)
        if fill_pos is None:
            end_time = bars.index[-1] + bar_delta
            status = "OPEN"
        else:
            end_time = bars.index[fill_pos] + bar_delta
            status = "FULLY_FILLED"

        records.append(
            {
                "kind": kind,
                "start_time": start_time,
                "end_time": end_time,
                "zone_low": zone_low,
                "zone_high": zone_high,
                "status": status,
            }
        )

    return pd.DataFrame.from_records(records)


def load_candidates(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Candidate file not found: {path}")

    candidates = pq.read_table(path).to_pandas()
    required = {
        "ts_event",
        "setup_type",
        "entry_side",
        "entry_price",
        "fvg_low",
        "fvg_high",
    }
    missing = required - set(candidates.columns)
    if missing:
        raise ValueError(
            f"Candidate file is missing required columns: {sorted(missing)}"
        )

    for col in ("ts_event", "entry_timestamp", "feature_timestamp"):
        if col in candidates.columns:
            candidates[col] = pd.to_datetime(candidates[col], utc=True, errors="coerce")

    numeric_cols = [
        "entry_price",
        "stop_price",
        "target_1",
        "target_2",
        "target_3",
        "fvg_low",
        "fvg_high",
        "max_holding_bars",
    ]
    for col in numeric_cols:
        if col in candidates.columns:
            candidates[col] = pd.to_numeric(candidates[col], errors="coerce")

    candidates = candidates.dropna(
        subset=["ts_event", "entry_price", "fvg_low", "fvg_high"]
    ).sort_values("ts_event", kind="stable")
    return candidates


def rgba(hex_color: str, alpha: float) -> str:
    value = hex_color.lstrip("#")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    return f"rgba({red},{green},{blue},{alpha})"


def add_horizontal_segment(
    fig: go.Figure,
    x0: pd.Timestamp,
    x1: pd.Timestamp,
    y: float | int | None,
    color: str,
    dash: str,
    width: int,
) -> None:
    if y is None or pd.isna(y):
        return
    fig.add_shape(
        type="line",
        x0=x0,
        x1=x1,
        y0=float(y),
        y1=float(y),
        line={"color": color, "width": width, "dash": dash},
        layer="above",
    )


def build_chart(
    bars: pd.DataFrame,
    fvgs: pd.DataFrame,
    candidates: pd.DataFrame,
    timeframe: str,
    max_fvgs: int,
) -> go.Figure:
    bar_delta = pd.Timedelta(timeframe)
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=bars.index,
            open=bars["open"],
            high=bars["high"],
            low=bars["low"],
            close=bars["close"],
            name=f"MNQ {timeframe}",
            increasing_line_color="#17a673",
            decreasing_line_color="#e55353",
            increasing_fillcolor="#17a673",
            decreasing_fillcolor="#e55353",
            hovertext=[
                f"Volume: {volume:,.0f}<br>Trades: {trades:,.0f}"
                for volume, trades in zip(bars["volume"], bars["trades"], strict=True)
            ],
            hoverinfo="x+open+high+low+close+text",
        )
    )

    if not fvgs.empty:
        fvgs_to_draw = fvgs.tail(max_fvgs)
        for row in fvgs_to_draw.itertuples(index=False):
            is_bull = row.kind == "BULL_FVG"
            base_color = "#2ca02c" if is_bull else "#d62728"
            fill_alpha = 0.12 if row.status == "OPEN" else 0.065
            fig.add_shape(
                type="rect",
                x0=row.start_time,
                x1=row.end_time,
                y0=row.zone_low,
                y1=row.zone_high,
                fillcolor=rgba(base_color, fill_alpha),
                line={"color": rgba(base_color, 0.42), "width": 1},
                layer="below",
            )

        # Hover anchors for raw FVGs because Plotly shapes do not carry hover text.
        fig.add_trace(
            go.Scatter(
                x=fvgs_to_draw["start_time"],
                y=(fvgs_to_draw["zone_low"] + fvgs_to_draw["zone_high"]) / 2,
                mode="markers",
                name="Detected FVG",
                marker={"size": 8, "opacity": 0.06},
                customdata=fvgs_to_draw[
                    ["kind", "zone_low", "zone_high", "status", "end_time"]
                ].to_numpy(),
                hovertemplate=(
                    "%{customdata[0]}<br>"
                    "Low: %{customdata[1]:.2f}<br>"
                    "High: %{customdata[2]:.2f}<br>"
                    "Status: %{customdata[3]}<br>"
                    "Ends: %{customdata[4]}<extra></extra>"
                ),
            )
        )

    long_candidates = candidates.loc[candidates["entry_side"].astype(str).str.upper() == "LONG"]
    short_candidates = candidates.loc[candidates["entry_side"].astype(str).str.upper() == "SHORT"]

    def candidate_hover(frame: pd.DataFrame) -> list[str]:
        hover_rows: list[str] = []
        for row in frame.itertuples(index=False):
            stop = getattr(row, "stop_price", math.nan)
            t1 = getattr(row, "target_1", math.nan)
            t2 = getattr(row, "target_2", math.nan)
            t3 = getattr(row, "target_3", math.nan)
            hover_rows.append(
                f"{row.setup_type}<br>"
                f"Side: {row.entry_side}<br>"
                f"Entry: {row.entry_price:.2f}<br>"
                f"FVG: {row.fvg_low:.2f} – {row.fvg_high:.2f}<br>"
                f"Stop: {stop:.2f}<br>T1: {t1:.2f}<br>T2: {t2:.2f}<br>T3: {t3:.2f}"
            )
        return hover_rows

    if not long_candidates.empty:
        fig.add_trace(
            go.Scatter(
                x=long_candidates["ts_event"],
                y=long_candidates["entry_price"],
                mode="markers+text",
                name="Failed FVG LONG",
                marker={
                    "symbol": "triangle-up",
                    "size": 15,
                    "color": "#00b894",
                    "line": {"color": "#ffffff", "width": 1},
                },
                text=[f"L{i + 1}" for i in range(len(long_candidates))],
                textposition="bottom center",
                hovertext=candidate_hover(long_candidates),
                hoverinfo="text",
            )
        )

    if not short_candidates.empty:
        fig.add_trace(
            go.Scatter(
                x=short_candidates["ts_event"],
                y=short_candidates["entry_price"],
                mode="markers+text",
                name="Failed FVG SHORT",
                marker={
                    "symbol": "triangle-down",
                    "size": 15,
                    "color": "#d63031",
                    "line": {"color": "#ffffff", "width": 1},
                },
                text=[f"S{i + 1}" for i in range(len(short_candidates))],
                textposition="top center",
                hovertext=candidate_hover(short_candidates),
                hoverinfo="text",
            )
        )

    # Highlight candidate FVG zones and trade levels more strongly.
    for idx, row in candidates.reset_index(drop=True).iterrows():
        signal_time = row["ts_event"]
        holding_bars = row.get("max_holding_bars", math.nan)
        if pd.isna(holding_bars) or int(holding_bars) <= 0:
            holding_bars = 8
        x0 = signal_time - bar_delta
        x1 = signal_time + bar_delta * int(holding_bars)
        side = str(row["entry_side"]).upper()
        color = "#00b894" if side == "LONG" else "#d63031"

        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=float(row["fvg_low"]),
            y1=float(row["fvg_high"]),
            fillcolor=rgba("#f1c40f", 0.14),
            line={"color": "#f1c40f", "width": 3},
            layer="above",
        )

        add_horizontal_segment(fig, signal_time, x1, row.get("entry_price"), color, "solid", 2)
        add_horizontal_segment(fig, signal_time, x1, row.get("stop_price"), "#ff7675", "dash", 1)
        add_horizontal_segment(fig, signal_time, x1, row.get("target_1"), "#74b9ff", "dot", 1)
        add_horizontal_segment(fig, signal_time, x1, row.get("target_2"), "#0984e3", "dot", 1)
        add_horizontal_segment(fig, signal_time, x1, row.get("target_3"), "#6c5ce7", "dot", 1)

        fig.add_annotation(
            x=signal_time,
            y=float(row["fvg_high"]),
            text=f"#{idx + 1} {row['setup_type']} → {side}",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-38 if side == "SHORT" else 38,
            bgcolor="rgba(255,255,255,0.84)",
            bordercolor=color,
            borderwidth=1,
            font={"size": 10},
        )

    min_time = bars.index.min()
    max_time = bars.index.max()
    symbol_label = "MNQ"
    if "symbol" in candidates.columns and not candidates["symbol"].dropna().empty:
        symbol_label = str(candidates["symbol"].dropna().iloc[0])

    fig.update_layout(
        title=(
            f"{symbol_label} — {timeframe} Candles with Fair Value Gaps"
            f"<br><sup>{min_time:%Y-%m-%d} to {max_time:%Y-%m-%d} UTC | "
            f"Raw FVGs: {len(fvgs):,} | Failed-FVG candidates: {len(candidates):,}</sup>"
        ),
        template="plotly_white",
        height=900,
        margin={"l": 65, "r": 30, "t": 95, "b": 55},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.02, "x": 0},
        xaxis={
            "title": "UTC time",
            "rangeslider": {"visible": True, "thickness": 0.08},
            "showspikes": True,
            "spikemode": "across",
            "spikesnap": "cursor",
        },
        yaxis={
            "title": "Price",
            "fixedrange": False,
            "showspikes": True,
            "spikemode": "across",
            "spikesnap": "cursor",
        },
    )

    return fig


def main() -> None:
    args = parse_args()

    print(f"Loading trade tape: {args.trade_tape}")
    trades = load_trade_tape(args.trade_tape, args.symbol)
    print(f"Loaded {len(trades):,} trades")

    bars = build_candles(trades, args.timeframe)
    print(f"Built {len(bars):,} {args.timeframe} candles")

    bar_delta = pd.Timedelta(args.timeframe)
    fvgs = detect_fvgs(bars, bar_delta)
    print(f"Detected {len(fvgs):,} raw 3-candle FVGs")

    candidates = load_candidates(args.candidates)
    print(f"Loaded {len(candidates):,} failed-FVG candidates")

    fig = build_chart(
        bars=bars,
        fvgs=fvgs,
        candidates=candidates,
        timeframe=args.timeframe,
        max_fvgs=args.max_fvgs,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        args.output,
        include_plotlyjs=True,
        full_html=True,
        auto_open=False,
    )

    resolved = args.output.resolve()
    print(f"Chart written to: {resolved}")
    if not args.no_open:
        webbrowser.open(resolved.as_uri())


if __name__ == "__main__":
    main()
