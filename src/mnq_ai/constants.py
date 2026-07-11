"""Shared constants for Phase 1 market-data processing."""

from __future__ import annotations

from decimal import Decimal

REQUIRED_MBO_COLUMNS: tuple[str, ...] = (
    "ts_recv",
    "ts_event",
    "rtype",
    "publisher_id",
    "instrument_id",
    "action",
    "side",
    "price",
    "size",
    "channel_id",
    "order_id",
    "flags",
    "ts_in_delta",
    "sequence",
    "symbol",
)

PHASE1_SCAN_COLUMNS: tuple[str, ...] = (
    "ts_recv",
    "ts_event",
    "publisher_id",
    "instrument_id",
    "action",
    "side",
    "price",
    "size",
    "sequence",
    "symbol",
)

ACTION_DOMAIN: frozenset[str] = frozenset({"A", "C", "M", "R", "T", "F"})
SIDE_DOMAIN: frozenset[str] = frozenset({"A", "B", "N"})

TRADE_ACTION = "T"
FILL_ACTION = "F"
DEFAULT_TICK_SIZE = Decimal("0.25")
DEFAULT_EXCHANGE_TIMEZONE = "America/Chicago"

CAUSAL_ORDER_COLUMNS: tuple[str, ...] = ("ts_event", "sequence", "source_row_number")
PARTITION_COLUMNS: tuple[str, ...] = ("symbol", "trading_date")
