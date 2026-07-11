# MNQ Risk Register

| ID | Risk | Level | Evidence | Mitigation |
|---|---|---:|---|---|
| R1 | Core safety files are deleted from working tree | Critical | `modules/`, `tests/`, `tools/`, `validation/`, `labeling/` show as deleted | Restore or recreate active safety files before implementation. |
| R2 | Depth-derived direction leaks into model | Critical | Previous architecture includes LOB/DeepLOB and depth features | Enforce feature whitelist and forbidden-depth blacklist. |
| R3 | UTC-date sessions replace CME sessions | High | New feature modules default to `ts.dt.date` when no session column exists | Implement CME session calendar and require `cme_session_id`. |
| R4 | Full-session Volume Profile leaks into intraday decisions | High | VP features are a primary signal | Online current-session profiles only; prior full profiles shifted to next session. |
| R5 | MBO `T` and `F` double-counting | High | Databento MBO contains both normalized trade and passive fill records | Extract executed trade volume from `action == "T"` only. |
| R6 | Unknown aggressor side inferred | High | `side == "N"` exists | Signed volume is zero for unknown side; mark CVD validity. |
| R7 | Bars-only preflight creates synthetic flow features | High | Modified `prepare_day_trading.py` can fill buy/sell/CVD placeholders | Mark as preflight-only; block from training unless real trade flow is present. |
| R8 | Random split or overlapping labels | Critical | Market data labels overlap by horizon | Purged walk-forward with embargo only. |
| R9 | Raw probability reported as confidence | Medium | CatBoost proba is uncalibrated | Validation-only calibration and reliability reporting. |
| R10 | Five-day sample misused as evidence | Critical | Current fixture has only five dates | Engineering validation only; no production or profitability claims. |
| R11 | Generated folders confuse code search and imports | Medium | `graphify-code-scope/`, `graphify-scope/`, graph caches are deleted/generated | Keep generated copies ignored or out of active path. |
| R12 | Archived code accidentally restored as active | Medium | `_archive/` contains old V19/V20/quantum code | Do not restore archived folders into active imports. |
| R13 | Backtest fills impossible prices | High | Bar-level backtests can use future extremes | Event-driven or conservative bar execution with latency and slippage. |
| R14 | Feature selection uses targets | High | Setup outcome labels are forward-looking | Feature selection inside training folds only, with label blacklist. |
| R15 | Contract roll handling absent | Medium | Current data is MNQM6 only | Explicit roll rules before multi-contract data. |

## Current Stop/Go

Production implementation: STOP.

Phase 1 engineering rebuild after review: GO, if active safety files are restored
or recreated and cleanup policy is approved.

