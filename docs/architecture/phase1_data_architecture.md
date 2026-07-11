# Phase 1 Data Architecture

Phase 1 is a streaming data-foundation layer for Databento CME GLBX MDP3 MBO data.

Flow:

1. `MBOParquetReader` scans Parquet through `pyarrow.dataset` with column pruning.
2. `schemas.py` validates required columns and parses UTC nanosecond timestamps.
3. `Phase1TradeExtractor` audits every batch, selects `action == "T"`, validates trade rows, derives signed volume, and assigns session metadata.
4. `CMESessionizer` derives CME trading dates, RTH flags, and session IDs using `America/Chicago`.
5. `PartitionedTradeTapeWriter` writes staged Parquet partitioned by `symbol` and `trading_date`.
6. `manifests.py` writes completion manifests and validates aggregate output invariants.
7. `quality_audit.py` writes JSON and Markdown audit reports.

The pipeline avoids full raw-data pandas materialization. Batch size, output compression, invalid-row policy, and target rows per output file are configurable.

The deterministic causal order is:

```text
ts_event, sequence, source_row_number
```

`source_row_number` is generated from deterministic scanner order and acts only as a tie breaker. If fail policy is enabled, ordering anomalies fail the job.
