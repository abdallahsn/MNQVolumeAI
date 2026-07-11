# MNQ Model And Calibration Specification

Scope: initial machine-learning baseline for deterministic setup candidates.

## Model Role

The model decides whether to take a deterministic setup. It does not choose
market direction.

Required outputs:

```text
calibrated setup-success probability
expected net return in R
predicted MAE quantiles
predicted MFE quantiles
expected holding time
optional early-exit probability
```

## Initial Model Set

| Output | Candidate model |
|---|---|
| setup success | CatBoost classifier |
| expected net R | CatBoost regressor |
| MAE quantiles | CatBoost quantile regressor |
| MFE quantiles | CatBoost quantile regressor |
| holding time | CatBoost regressor or survival model |

Do not introduce deep learning in the initial baseline until the setup-driven
CatBoost baseline is documented and insufficient.

## Feature Inputs

Allowed families:

```text
volume_profile_features
auction_rejection_features
cvd_delta_features
intraday_context_features
vwap_features
setup metadata that is known at decision time
```

Forbidden:

```text
depth-derived direction inputs
labels/outcomes/diagnostics
future session levels
global statistics fit before split
```

## Calibration

Raw `predict_proba` is not a reliable confidence. Required calibration:

1. fit model on training fold;
2. fit isotonic or Platt calibration on validation fold only;
3. evaluate on test fold;
4. report Brier score, log loss, ECE, and reliability table.

Final production threshold selection must use development folds only, never the
final untouched holdout.

## Class Imbalance

Report:

1. setup count by type and side;
2. positive/negative class counts;
3. precision/recall at thresholds;
4. PR-AUC;
5. minimum trade count for any claim.

Class weights may be used, but must be fit from training folds only.

## Artifact Contract

Required artifacts:

```text
model_success.cbm
model_expected_R.cbm
model_mae_quantile_<q>.cbm
model_mfe_quantile_<q>.cbm
model_holding_time.cbm
calibrator_success.pkl
feature_schema.json
training_manifest.json
walk_forward_report.json
```

`training_manifest.json` must include:

```json
{
  "train_sessions": [],
  "validation_sessions": [],
  "test_sessions": [],
  "feature_columns": [],
  "forbidden_columns_excluded": true,
  "calibration_method": "isotonic_or_platt",
  "cost_assumptions": {}
}
```

## Decision Thresholds

A setup can be accepted only if all configured gates pass:

```text
calibrated_probability >= threshold_by_setup_type
expected_net_R_after_costs >= min_expected_R
predicted_MAE_quantile <= max_allowed_MAE
liquidity/session/risk guard passes
daily risk guard passes
```

## Acceptance Criteria

1. all preprocessing is fit on training fold only.
2. calibration uses validation only.
3. test metrics are out-of-sample.
4. final holdout is untouched until final reporting.
5. confidence shown to users is calibrated probability, not raw proba.
6. no depth-direction features are present in `feature_schema.json`.

