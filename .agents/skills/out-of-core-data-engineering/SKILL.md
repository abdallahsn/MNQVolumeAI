---
name: out-of-core-data-engineering
description: "Use when Parquet, Arrow, MBO, trade, feature, or label datasets may exceed memory; do not run for small local text or config edits."
---

# out-of-core-data-engineering

## Trigger

Use this Skill when processing large Parquet, Arrow, MBO, trade, feature, or label datasets that may exceed memory.

## Do Not Trigger

Do not run this Skill for small Markdown edits, skill validation, dependency policy writing, or tiny fixtures that safely fit in memory.

## Required Workflow

- Estimate input size and memory before execution.
- Inspect Parquet metadata first.
- Use row-group and column pruning.
- Use predicate pushdown where possible.
- Prefer streaming or lazy processing.
- Bound batch sizes.
- Partition deterministically.
- Avoid full pandas materialization.
- Avoid millions of small files.
- Finalize outputs atomically.
- Make jobs restartable.
- Write checksums and manifests.
- Report peak memory.
- Report throughput.
- Smoke test before full execution.
- Run a subset benchmark before 179M-row processing.
- Check disk space explicitly.
- Clean incomplete staging output only after verification.

## Candidate Tools

Preferred candidates may include PyArrow, Polars, and DuckDB, but their selection and versions must go through `$dependency-governor`.

## Required Outputs

Report estimated bytes, scanned bytes, output bytes, partitions, row counts, peak memory, runtime, throughput, checksum status, and restart instructions.
