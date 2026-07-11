# MNQ Data Audit Plan

Scope: Databento CME Globex MBO data for MNQ. This plan is required before
feature, label, model, or backtest work.

## Objectives

1. Prove that the raw file can be parsed reproducibly.
2. Extract executed trade volume from `action == "T"` only.
3. Preserve UTC event timestamps and derive exchange-local sessions separately.
4. Detect partial sessions, duplicates, invalid prices, invalid sizes, and gaps.
5. Produce partitioned parquet artifacts suitable for feature engineering.

## Source Schema

Expected columns:

```text
ts_recv, ts_event, rtype, publisher_id, instrument_id, action, side, price,
size, channel_id, order_id, flags, ts_in_delta, sequence, symbol
```

## MBO Trade Semantics

| Field | Rule |
|---|---|
| `action == "T"` | Normalized trade record. Use for executed trade volume. |
| `action == "F"` | Passive fill detail associated with trade. Do not sum with `T`. |
| `side == "B"` | Buy aggressor. Signed volume is `+size`. |
| `side == "A"` | Sell aggressor. Signed volume is `-size`. |
| `side == "N"` | Unknown aggressor. Signed volume is `0`. |
| `A/C/M/R/F` actions | Do not use as directional features in Phase 1. |

## Required Audit Outputs

| Artifact | Contents |
|---|---|
| `data_audit_summary.json` | row counts, date range, symbol/instrument IDs, invalid counts |
| `mbo_trade_extract_manifest.json` | action counts, side counts, signed-volume rules |
| `session_coverage.parquet` | session IDs, start/end, row counts, partial flags |
| `invalid_rows_sample.parquet` | bounded sample of invalid rows |
| `gap_report.parquet` | abnormal gaps by session/symbol |
| `partition_manifest.json` | parquet partitions and schema hash |

## Checks

### Timestamp checks

1. `ts_event` parses as UTC.
2. `ts_recv` parses as UTC when present.
3. `ts_event <= ts_recv` tolerance is audited, not silently assumed.
4. Sort order is monotonic within symbol/instrument after stable sort by
   `ts_event`, `sequence`, and raw row order.
5. Duplicate event keys are counted and sampled.

### Price and size checks

1. price is finite and positive after applying Databento price scaling.
2. size is finite and non-negative.
3. tick increments match MNQ tick size.
4. zero-size trades are counted and excluded from volume profile unless
   explicitly justified.

### Symbol and contract checks

1. expected symbol is `MNQM6` for the current fixture.
2. all instrument IDs mapped to symbol.
3. first and last sessions are flagged if truncated by file boundaries.
4. future multi-contract support must use explicit roll rules.

### Session checks

Do not group by UTC calendar date. The audit must produce CME exchange session
IDs. UTC timestamps remain canonical; local exchange fields are derived fields.

Required columns:

```text
ts_event_utc
exchange_datetime
trading_date
cme_session_id
is_rth
is_overnight
session_segment
is_partial_session
seconds_from_session_open
seconds_to_session_close
```

## Chunking Strategy

1. Load only required columns for each audit pass.
2. Use chunk-level summaries first, then reduce summaries.
3. Store intermediate normalized trades as parquet partitioned by
   `symbol/trading_date`.
4. Avoid global full-file DataFrame operations on 179M rows.
5. Maintain a stable row id or source chunk id for reproducibility.

## Validation Commands To Create In Phase 1

```bash
python tools/mnq_audit_mbo.py --input <mbo> --output <audit_dir> --symbol MNQM6
python tools/mnq_extract_trades.py --input <mbo> --output <trades_dir> --symbol MNQM6
python tools/mnq_build_bars.py --trades <trades_dir> --output <bars_dir> --freq 1min
```

## Acceptance Criteria

1. action counts reconcile to raw row count.
2. trade volume comes only from `T`.
3. unknown aggressor side is not inferred.
4. sessions are exchange-session based.
5. invalid row counts are explicit.
6. partitioned parquet can be reloaded with identical schema.
7. first and last session partial status is reported.

