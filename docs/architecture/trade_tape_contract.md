# Trade Tape Contract

Canonical schema:

| Column | Meaning |
|---|---|
| `ts_event` | UTC nanosecond event timestamp. |
| `ts_recv` | UTC nanosecond receive timestamp. |
| `sequence` | Databento sequence. |
| `publisher_id` | Source publisher. |
| `instrument_id` | Instrument identifier. |
| `symbol` | Contract symbol, partitioned in output. |
| `price` | Original trade price. |
| `size` | Original trade size. |
| `aggressor_side` | Original `side` value: `B`, `A`, or `N`. |
| `signed_volume` | `+size` for `B`, `-size` for `A`, `0` for `N`. |
| `unknown_aggressor` | True only for `side == "N"`. |
| `trading_date` | CME exchange trading date, partitioned in output. |
| `session_id` | `CME_EQ_FUT_<trading_date>`. |
| `session_segment` | `RTH` or `OVERNIGHT`. |
| `is_rth` | Boolean RTH flag. |
| `source_row_number` | Deterministic source-order tie breaker. |

Phase 1 explicitly excludes bars, Volume Profile, VWAP, CVD feature families beyond signed trade volume, setup signals, labels, models, and backtests.

Critical invariants:

- output row count equals valid `action == "T"` row count;
- output size sum equals valid `T` size sum;
- `F` rows contribute zero output rows and zero output volume;
- no non-`T` source row enters the canonical tape;
- invalid tick prices are rejected, quarantined, or warned by explicit policy.
