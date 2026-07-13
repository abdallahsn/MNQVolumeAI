"""CME session assignment for MNQ Phase 1 trade rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from mnq_ai.config import Phase1Config


@dataclass(frozen=True)
class SessionMetadata:
    """Vector-friendly session fields for a batch."""

    trading_date: list[str]
    session_id: list[str]
    session_segment: list[str]
    is_rth: list[bool]


@dataclass(frozen=True)
class SessionBounds:
    """UTC nanosecond bounds for a CME trading date."""

    open_ns: int
    close_ns: int


class CMESessionizer:
    """Assign CME equity-index futures trading dates without fixed UTC offsets."""

    def __init__(self, config: Phase1Config) -> None:
        self.exchange_tz = ZoneInfo(config.exchange_timezone)
        self.session_start = _parse_time(config.session_start)
        self.session_end = _parse_time(config.session_end)
        self.rth_start = _parse_time(config.rth_start)
        self.rth_end = _parse_time(config.rth_end)

    def assign(self, ts_event_ns: list[int | None]) -> SessionMetadata:
        """Assign session metadata for UTC nanosecond timestamps."""

        trading_dates: list[str] = []
        session_ids: list[str] = []
        segments: list[str] = []
        rth_flags: list[bool] = []
        for value in ts_event_ns:
            if value is None:
                trading_dates.append("")
                session_ids.append("")
                segments.append("UNKNOWN")
                rth_flags.append(False)
                continue
            local_dt = _ns_to_utc_datetime(value).astimezone(self.exchange_tz)
            trading_day = self.trading_date_for_local(local_dt)
            is_rth = self.rth_start <= local_dt.time() < self.rth_end
            trading_date = trading_day.isoformat()
            trading_dates.append(trading_date)
            session_ids.append(f"CME_EQ_FUT_{trading_date}")
            segments.append("RTH" if is_rth else "OVERNIGHT")
            rth_flags.append(is_rth)
        return SessionMetadata(trading_dates, session_ids, segments, rth_flags)

    def trading_date_for_local(self, local_dt: datetime) -> date:
        """Return CME trading date for an exchange-local timestamp."""

        if local_dt.time() >= self.session_start:
            return local_dt.date() + timedelta(days=1)
        return local_dt.date()

    def session_bounds_utc_ns(self, trading_date: str) -> SessionBounds:
        """Return session open/close bounds in UTC nanoseconds."""

        trading_day = date.fromisoformat(trading_date)
        open_local = datetime.combine(
            trading_day - timedelta(days=1),
            self.session_start,
            tzinfo=self.exchange_tz,
        )
        close_local = datetime.combine(trading_day, self.session_end, tzinfo=self.exchange_tz)
        return SessionBounds(_datetime_to_ns(open_local.astimezone(UTC)), _datetime_to_ns(close_local.astimezone(UTC)))


def _parse_time(value: str) -> time:
    hour, minute, second = (int(part) for part in value.split(":"))
    return time(hour, minute, second)


def _ns_to_utc_datetime(value: int) -> datetime:
    seconds, nanos = divmod(int(value), 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=nanos // 1_000)


def _datetime_to_ns(value: datetime) -> int:
    return int(value.timestamp()) * 1_000_000_000 + value.microsecond * 1_000
