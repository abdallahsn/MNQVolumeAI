"""Configuration loading and validation for Phase 1 jobs."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from mnq_ai.constants import DEFAULT_EXCHANGE_TIMEZONE, DEFAULT_TICK_SIZE
from mnq_ai.exceptions import ConfigurationError

InvalidRowPolicy = Literal["fail", "quarantine", "warn"]


@dataclass(frozen=True)
class Phase1Config:
    """Validated runtime configuration for MBO auditing and trade extraction."""

    input_path: Path | None = None
    output_root: Path = Path("data/trade_tape")
    artifact_root: Path = Path("artifacts/phase1")
    batch_size: int = 250_000
    symbol_filters: tuple[str, ...] = ()
    tick_size: Decimal = DEFAULT_TICK_SIZE
    exchange_timezone: str = DEFAULT_EXCHANGE_TIMEZONE
    session_start: str = "17:00:00"
    session_end: str = "16:00:00"
    rth_start: str = "08:30:00"
    rth_end: str = "15:00:00"
    invalid_row_policy: InvalidRowPolicy = "fail"
    overwrite: bool = False
    compression: str = "zstd"
    target_parquet_file_size_mb: int = 128
    target_rows_per_file: int = 500_000
    quarantine_sample_limit: int = 10_000
    partial_session_tolerance_minutes: int = 5
    logging_level: str = "INFO"

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        input_path: str | Path | None = None,
        output_root: str | Path | None = None,
        artifact_root: str | Path | None = None,
    ) -> Phase1Config:
        """Load a config file, following a single optional ``extends`` reference."""

        config_path = Path(path)
        if not config_path.exists():
            raise ConfigurationError(f"Config file does not exist: {config_path}")
        raw = _load_yaml_with_extends(config_path)
        if input_path is not None:
            raw["input_path"] = str(input_path)
        if output_root is not None:
            raw["output_root"] = str(output_root)
        if artifact_root is not None:
            raw["artifact_root"] = str(artifact_root)
        return cls.from_mapping(raw)

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> Phase1Config:
        """Build and validate config from a mapping."""

        allowed = {field.name for field in fields(cls)}
        unknown = sorted(set(values) - allowed - {"extends"})
        if unknown:
            raise ConfigurationError(f"Unknown config keys: {', '.join(unknown)}")

        kwargs: dict[str, Any] = {}
        for key, value in values.items():
            if key == "extends" or value is None:
                continue
            if key in {"input_path", "output_root", "artifact_root"}:
                kwargs[key] = Path(value)
            elif key == "symbol_filters":
                kwargs[key] = tuple(str(item) for item in value or ())
            elif key == "tick_size":
                try:
                    kwargs[key] = Decimal(str(value))
                except InvalidOperation as exc:
                    raise ConfigurationError(f"Invalid tick_size: {value}") from exc
            else:
                kwargs[key] = value
        return cls(**kwargs).validated()

    def with_overrides(
        self,
        *,
        input_path: str | Path | None = None,
        output_root: str | Path | None = None,
        artifact_root: str | Path | None = None,
        overwrite: bool | None = None,
    ) -> Phase1Config:
        """Return a validated copy with common CLI overrides."""

        updates: dict[str, Any] = {}
        if input_path is not None:
            updates["input_path"] = Path(input_path)
        if output_root is not None:
            updates["output_root"] = Path(output_root)
        if artifact_root is not None:
            updates["artifact_root"] = Path(artifact_root)
        if overwrite is not None:
            updates["overwrite"] = overwrite
        return replace(self, **updates).validated()

    def validated(self) -> Phase1Config:
        """Fail closed on invalid configuration."""

        if self.batch_size <= 0:
            raise ConfigurationError("batch_size must be positive")
        if self.target_rows_per_file <= 0:
            raise ConfigurationError("target_rows_per_file must be positive")
        if self.target_parquet_file_size_mb <= 0:
            raise ConfigurationError("target_parquet_file_size_mb must be positive")
        if self.quarantine_sample_limit < 0:
            raise ConfigurationError("quarantine_sample_limit cannot be negative")
        if self.tick_size <= 0:
            raise ConfigurationError("tick_size must be positive")
        if self.invalid_row_policy not in {"fail", "quarantine", "warn"}:
            raise ConfigurationError("invalid_row_policy must be fail, quarantine, or warn")
        try:
            ZoneInfo(self.exchange_timezone)
        except ZoneInfoNotFoundError as exc:
            raise ConfigurationError(f"Unknown exchange timezone: {self.exchange_timezone}") from exc
        for field in ("session_start", "session_end", "rth_start", "rth_end"):
            _parse_hms(getattr(self, field), field)
        if self.compression not in {"zstd", "snappy", "gzip", "brotli", "lz4", "none"}:
            raise ConfigurationError("compression must be one of zstd, snappy, gzip, brotli, lz4, none")
        return self


def _load_yaml_with_extends(path: Path) -> dict[str, Any]:
    raw = _read_yaml(path)
    parent = raw.get("extends")
    if parent is None:
        return raw
    parent_path = (path.parent / str(parent)).resolve()
    merged = _load_yaml_with_extends(parent_path)
    merged.update({k: v for k, v in raw.items() if k != "extends"})
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ConfigurationError(f"Config root must be a mapping: {path}")
    return loaded


def _parse_hms(value: str, field: str) -> tuple[int, int, int]:
    parts = value.split(":")
    if len(parts) != 3:
        raise ConfigurationError(f"{field} must use HH:MM:SS")
    try:
        hour, minute, second = (int(part) for part in parts)
    except ValueError as exc:
        raise ConfigurationError(f"{field} must use numeric HH:MM:SS") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ConfigurationError(f"{field} is outside valid time range")
    return hour, minute, second
