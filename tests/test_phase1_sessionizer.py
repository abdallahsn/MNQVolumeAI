from __future__ import annotations

import pyarrow as pa

from mnq_ai.config import Phase1Config
from mnq_ai.data.schemas import parse_timestamp_array, timestamp_array_to_ns
from mnq_ai.data.sessionizer import CMESessionizer


def test_cme_trading_date_uses_exchange_timezone_and_dst() -> None:
    config = Phase1Config.from_mapping({})
    parsed = parse_timestamp_array(
        pa.array(
            [
                "2026-03-08T22:30:00.000000000Z",
                "2026-03-09T14:00:00.000000000Z",
            ]
        )
    )
    metadata = CMESessionizer(config).assign(timestamp_array_to_ns(parsed.values))

    assert metadata.trading_date == ["2026-03-09", "2026-03-09"]
    assert metadata.session_segment == ["OVERNIGHT", "RTH"]
    assert metadata.is_rth == [False, True]
