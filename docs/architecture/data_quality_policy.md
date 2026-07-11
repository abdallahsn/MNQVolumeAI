# Data Quality Policy

Invalid-row policy is configurable:

- `fail`: stop the job on critical violations.
- `quarantine`: exclude invalid trade rows from canonical output and write a bounded `quarantine_rows.parquet` sample.
- `warn`: exclude invalid trade rows and report counts without writing quarantine rows.

Fail-closed conditions include:

- missing required columns;
- duplicate column names;
- unknown action or side values;
- unparsable `ts_event`;
- invalid sequence for causal ordering;
- invalid trade price, size, symbol, or tick increment;
- causal ordering anomalies under `(ts_event, sequence, source_row_number)`.

Reports are written as both JSON and Markdown under the artifact root:

- `schema_report`
- `action_side_report`
- `timestamp_report`
- `session_report`
- `trade_volume_report`
- `tick_size_report`
- `duplicate_report`
- `phase1_manifest`
- `phase1_summary`
