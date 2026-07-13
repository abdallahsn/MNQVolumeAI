"""Partitioned Parquet writers with staging-based finalization."""

from __future__ import annotations

import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from mnq_ai.config import Phase1Config
from mnq_ai.constants import PARTITION_COLUMNS
from mnq_ai.data.schemas import QUARANTINE_SCHEMA, TRADE_TAPE_SCHEMA
from mnq_ai.exceptions import OutputValidationError


class PartitionedTradeTapeWriter:
    """Write canonical trade tape batches to staged partitioned Parquet."""

    def __init__(self, output_root: Path, config: Phase1Config) -> None:
        self.output_root = output_root
        self.config = config
        self.staging_root = output_root.parent / f".{output_root.name}.incomplete"
        self._batch_index = 0

    def prepare(self) -> None:
        """Prepare staging output and enforce overwrite policy."""

        if self.output_root.exists() and not self.config.overwrite:
            raise OutputValidationError(f"Output exists and overwrite=false: {self.output_root}")
        if self.staging_root.exists():
            if not self.config.overwrite:
                raise OutputValidationError(f"Staging output exists: {self.staging_root}")
            shutil.rmtree(self.staging_root)
        self.staging_root.mkdir(parents=True, exist_ok=True)

    def write_batch(self, table: pa.Table) -> None:
        """Write one canonical batch."""

        if table.num_rows == 0:
            return
        table = table.select(TRADE_TAPE_SCHEMA.names).cast(TRADE_TAPE_SCHEMA)
        file_format = ds.ParquetFileFormat()
        compression = None if self.config.compression == "none" else self.config.compression
        file_options = file_format.make_write_options(compression=compression)
        partition_schema = pa.schema([(name, TRADE_TAPE_SCHEMA.field(name).type) for name in PARTITION_COLUMNS])
        ds.write_dataset(
            table,
            base_dir=str(self.staging_root),
            format=file_format,
            file_options=file_options,
            partitioning=ds.partitioning(partition_schema, flavor="hive"),
            existing_data_behavior="overwrite_or_ignore",
            basename_template=f"part-{self._batch_index:06d}-{{i}}.parquet",
            max_rows_per_file=self.config.target_rows_per_file,
            min_rows_per_group=min(self.config.target_rows_per_file, 64_000),
            max_rows_per_group=min(self.config.target_rows_per_file, 128_000),
        )
        self._batch_index += 1

    def finalize(self) -> tuple[int, int]:
        """Move staged output into place and return file count and byte size."""

        files = list(self.staging_root.rglob("*.parquet"))
        if not files:
            raise OutputValidationError("No trade-tape Parquet files were written")
        output_bytes = sum(path.stat().st_size for path in files)
        if self.output_root.exists():
            shutil.rmtree(self.output_root)
        self.output_root.parent.mkdir(parents=True, exist_ok=True)
        self.staging_root.rename(self.output_root)
        return len(files), output_bytes


class QuarantineWriter:
    """Append invalid trade rows to a bounded Parquet quarantine file."""

    def __init__(self, artifact_root: Path, limit: int) -> None:
        self.path = artifact_root / "quarantine_rows.parquet"
        self.limit = limit
        self.rows_written = 0
        self._writer: pq.ParquetWriter | None = None

    def write(self, table: pa.Table) -> int:
        """Write up to the configured sample limit and return rows written."""

        if table.num_rows == 0 or self.rows_written >= self.limit:
            return 0
        remaining = self.limit - self.rows_written
        sample = table.slice(0, min(table.num_rows, remaining)).select(QUARANTINE_SCHEMA.names).cast(QUARANTINE_SCHEMA)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._writer is None:
            self._writer = pq.ParquetWriter(self.path, QUARANTINE_SCHEMA)
        self._writer.write_table(sample)
        self.rows_written += sample.num_rows
        return int(sample.num_rows)

    def close(self) -> None:
        """Close the underlying Parquet writer if it was opened."""

        if self._writer is not None:
            self._writer.close()
            self._writer = None
