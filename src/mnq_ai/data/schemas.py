"""Arrow schemas and schema-level validation."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc

from mnq_ai.constants import REQUIRED_MBO_COLUMNS
from mnq_ai.exceptions import SchemaValidationError

TIMESTAMP_NS_UTC = pa.timestamp("ns", tz="UTC")

TRADE_TAPE_SCHEMA = pa.schema(
    [
        ("ts_event", TIMESTAMP_NS_UTC),
        ("ts_recv", TIMESTAMP_NS_UTC),
        ("sequence", pa.uint64()),
        ("publisher_id", pa.int64()),
        ("instrument_id", pa.int64()),
        ("symbol", pa.string()),
        ("price", pa.float64()),
        ("size", pa.int64()),
        ("aggressor_side", pa.string()),
        ("signed_volume", pa.int64()),
        ("unknown_aggressor", pa.bool_()),
        ("trading_date", pa.string()),
        ("session_id", pa.string()),
        ("session_segment", pa.string()),
        ("is_rth", pa.bool_()),
        ("source_row_number", pa.uint64()),
    ]
)

QUARANTINE_SCHEMA = pa.schema(
    [
        ("rejection_reason", pa.string()),
        ("source_row_number", pa.uint64()),
        ("ts_event", pa.string()),
        ("ts_recv", pa.string()),
        ("sequence", pa.uint64()),
        ("publisher_id", pa.int64()),
        ("instrument_id", pa.int64()),
        ("symbol", pa.string()),
        ("action", pa.string()),
        ("side", pa.string()),
        ("price", pa.float64()),
        ("size", pa.int64()),
    ]
)


@dataclass(frozen=True)
class TimestampParseResult:
    """Parsed timestamp values plus an invalid-row mask."""

    values: pa.Array
    invalid_mask: pa.Array
    invalid_count: int


def validate_required_columns(schema: pa.Schema) -> None:
    """Validate required raw MBO columns and duplicate column names."""

    names = list(schema.names)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    missing = sorted(set(REQUIRED_MBO_COLUMNS) - set(names))
    errors: list[str] = []
    if duplicates:
        errors.append(f"duplicate columns: {', '.join(duplicates)}")
    if missing:
        errors.append(f"missing required columns: {', '.join(missing)}")
    if errors:
        raise SchemaValidationError("; ".join(errors))


def schema_report(schema: pa.Schema) -> dict[str, object]:
    """Return machine-readable schema diagnostics."""

    names = list(schema.names)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    missing = sorted(set(REQUIRED_MBO_COLUMNS) - set(names))
    return {
        "columns": names,
        "column_types": {field.name: str(field.type) for field in schema},
        "missing_required_columns": missing,
        "duplicate_columns": duplicates,
        "valid": not missing and not duplicates,
    }


def parse_timestamp_array(array: pa.Array | pa.ChunkedArray) -> TimestampParseResult:
    """Parse an Arrow array into timezone-aware UTC nanosecond timestamps.

    The fast path uses Arrow casting for valid ISO-8601 strings. If a batch contains
    a malformed value, a row-wise fallback identifies the invalid entries without
    silently coercing them.
    """

    combined = _combine(array)
    if pa.types.is_timestamp(combined.type):
        parsed = combined.cast(TIMESTAMP_NS_UTC)
        invalid_mask = pc.is_null(parsed)
        return TimestampParseResult(parsed, invalid_mask, _true_count(invalid_mask))

    try:
        parsed = pc.cast(combined, TIMESTAMP_NS_UTC)
        invalid_mask = pc.is_null(parsed)
        return TimestampParseResult(parsed, invalid_mask, _true_count(invalid_mask))
    except (pa.ArrowInvalid, pa.ArrowTypeError):
        parsed_ints: list[int | None] = []
        invalid: list[bool] = []
        for value in combined.to_pylist():
            ns = _parse_iso8601_utc_ns(value)
            parsed_ints.append(ns)
            invalid.append(ns is None)
        parsed = pa.array(parsed_ints, type=pa.int64()).cast(TIMESTAMP_NS_UTC)
        invalid_mask = pa.array(invalid, type=pa.bool_())
        return TimestampParseResult(parsed, invalid_mask, sum(invalid))


def timestamp_ns_to_iso(ns: int | None) -> str | None:
    """Format an integer nanosecond UTC timestamp without pandas."""

    if ns is None:
        return None
    seconds, nanos = divmod(int(ns), 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=UTC)
    return f"{dt:%Y-%m-%dT%H:%M:%S}.{nanos:09d}Z"


def timestamp_scalar_to_ns(value: pa.Scalar | None) -> int | None:
    """Convert an Arrow timestamp scalar to integer nanoseconds."""

    if value is None or not value.is_valid:
        return None
    return int(value.cast(pa.int64()).as_py())


def timestamp_array_to_ns(array: pa.Array | pa.ChunkedArray) -> list[int | None]:
    """Return timestamp values as integer nanoseconds."""

    values = _combine(array).cast(pa.int64()).to_pylist()
    return [None if value is None else int(value) for value in values]


def file_size_bytes(path: str | Path) -> int:
    """Return file size for regular files, or recursive size for directories."""

    root = Path(path)
    if root.is_file():
        return root.stat().st_size
    return sum(child.stat().st_size for child in root.rglob("*") if child.is_file())


def _combine(array: pa.Array | pa.ChunkedArray) -> pa.Array:
    if isinstance(array, pa.ChunkedArray):
        return array.combine_chunks()
    return array


def _true_count(mask: pa.Array) -> int:
    return int(pc.sum(mask.cast(pa.int64())).as_py() or 0)


_ISO_UTC_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T(?P<time>\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d{1,9}))?Z$"
)


def _parse_iso8601_utc_ns(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    match = _ISO_UTC_RE.match(value)
    if match is None:
        return None
    try:
        base = datetime.fromisoformat(f"{match.group('date')}T{match.group('time')}+00:00")
    except ValueError:
        return None
    fraction = (match.group("fraction") or "").ljust(9, "0")
    nanos = int(fraction)
    seconds = int(base.timestamp())
    return seconds * 1_000_000_000 + nanos


def arrow_table_from_rows(rows: Iterable[dict[str, object]], schema: pa.Schema) -> pa.Table:
    """Build a schema-conformant table from row dictionaries."""

    return pa.Table.from_pylist(list(rows), schema=schema)
