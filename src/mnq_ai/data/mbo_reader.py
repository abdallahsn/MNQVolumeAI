"""Memory-safe readers for Databento MBO Parquet inputs."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds

from mnq_ai.constants import PHASE1_SCAN_COLUMNS
from mnq_ai.exceptions import SchemaValidationError


class MBOParquetReader:
    """Thin wrapper around ``pyarrow.dataset`` with column pruning."""

    def __init__(self, input_path: str | Path) -> None:
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise SchemaValidationError(f"Input path does not exist: {self.input_path}")
        self.dataset = ds.dataset(self.input_path, format="parquet")

    @property
    def schema(self) -> pa.Schema:
        """Return the input dataset schema."""

        return self.dataset.schema

    def iter_batches(
        self,
        *,
        columns: Iterable[str] = PHASE1_SCAN_COLUMNS,
        batch_size: int = 250_000,
    ) -> Iterable[pa.RecordBatch]:
        """Yield record batches without materializing the whole dataset."""

        scanner = self.dataset.scanner(columns=list(columns), batch_size=batch_size)
        yield from scanner.to_batches()
