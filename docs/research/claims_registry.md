# Claims Registry

Verification date: 2026-07-11

## Status Definitions

- **source claim:** A claim stated by a copied source document.
- **independently verified claim:** A claim reproduced in this repository with documented data, code, and validation.
- **unverified claim:** A source claim not yet reproduced here.
- **contradicted claim:** A source claim that conflicts with reproduced evidence or stronger primary evidence.
- **implementation hypothesis:** A design idea that may be tested later.
- **rejected claim:** A claim excluded from implementation or research use.

## Current Registry

| ID | Claim | Type | Source | Status | Notes |
|---|---|---|---|---|---|
| C001 | Volume Profile levels such as POC, VAH, and VAL can describe market acceptance and rejection. | source claim | volume_profile_research_en.md | unverified claim | Must be tested causally using only known-at-time executed volume. |
| C002 | Current-session full POC, VAH, VAL, VWAP, high, low, or total volume are leakage-prone intraday. | implementation hypothesis | volume_profile_research_en.md, mnq_feature_contract.md | unverified claim | Treated as a safety rule until formal leakage tests exist. |
| C003 | MBO `action == "T"` is the sole executed-trade volume source, while `action == "F"` must not be double-counted. | implementation hypothesis | mnq_data_audit_plan.md | unverified claim | Must be reconciled against raw Databento data in Phase 1 before features. |
| C004 | The ML layer should take or skip deterministic setups rather than learn direction from raw depth. | implementation hypothesis | mnq_setup_engine_spec.md, mnq_model_and_calibration_spec.md | unverified claim | Architecture constraint, not yet an empirical result. |
| C005 | CatBoost should precede deep learning for the initial setup-validation baseline. | implementation hypothesis | mnq_model_and_calibration_spec.md | unverified claim | Requires reproducible baseline comparison before any model commitment. |
| C006 | Random train/test splits are prohibited for dependent market time series. | implementation hypothesis | mnq_walk_forward_backtest_spec.md | unverified claim | Safety constraint; empirical impact still requires tests. |
| C007 | Five trading days are sufficient only for engineering smoke tests, not production or profitability claims. | implementation hypothesis | mnq_risk_register.md, mnq_walk_forward_backtest_spec.md | unverified claim | No performance claims accepted from five-day samples. |

## Independently Verified Claims

None yet.

## Contradicted Claims

None yet.

## Rejected Claims

None yet.
