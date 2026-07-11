from __future__ import annotations

from decimal import Decimal

import pytest

from mnq_ai.config import Phase1Config
from mnq_ai.exceptions import ConfigurationError


def test_config_validates_tick_and_timezone() -> None:
    config = Phase1Config.from_mapping(
        {
            "batch_size": 10,
            "tick_size": "0.25",
            "exchange_timezone": "America/Chicago",
            "invalid_row_policy": "quarantine",
        }
    )

    assert config.tick_size == Decimal("0.25")
    assert config.invalid_row_policy == "quarantine"


def test_config_rejects_bad_policy() -> None:
    with pytest.raises(ConfigurationError):
        Phase1Config.from_mapping({"invalid_row_policy": "drop"})
