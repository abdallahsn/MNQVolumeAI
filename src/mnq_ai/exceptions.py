"""Custom exceptions used by the Phase 1 pipeline."""

from __future__ import annotations


class MNQAIError(Exception):
    """Base class for project-specific exceptions."""


class ConfigurationError(MNQAIError):
    """Raised when configuration is missing or invalid."""


class SchemaValidationError(MNQAIError):
    """Raised when an input schema cannot support Phase 1 processing."""


class DataValidationError(MNQAIError):
    """Raised when raw rows violate fail-closed data-quality rules."""


class OutputValidationError(MNQAIError):
    """Raised when a produced trade tape fails manifest validation."""
