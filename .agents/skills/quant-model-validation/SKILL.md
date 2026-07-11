---
name: quant-model-validation
description: "Use for ML algorithm choice, targets, hyperparameters, walk-forward validation, and calibration; do not run for feature extraction alone."
---

# quant-model-validation

## Trigger

Use this Skill when selecting ML algorithms, targets, probability models, regression models, hyperparameter search, walk-forward validation, or confidence calibration.

## Do Not Trigger

Do not run this Skill for raw data parsing, deterministic feature definitions, dependency changes, or documentation updates that do not choose or evaluate a model.

## Required Workflow

- Establish a simple baseline first.
- Use CatBoost or another suitable tabular baseline before deep learning.
- Require evidence-based algorithm comparison.
- Use chronological splits only.
- Use purged walk-forward validation.
- Add embargo where labels overlap.
- Keep an untouched final holdout.
- Keep preprocessing fold-local.
- Keep feature selection fold-local.
- Reject target leakage.
- Do not optimize against the final test.
- Calibrate probabilities on validation-only data.
- Report Brier score, log loss, expected calibration error, and PR-AUC for imbalanced decisions.
- Report net expectancy after costs.
- Add confidence intervals or bootstrap uncertainty where appropriate.
- Report performance by setup and market regime.
- Compare against no-skill and rules-only baselines.

## Required Outputs

For each model decision, report:

- target definition;
- split design;
- feature availability proof;
- baseline metrics;
- calibration metrics;
- cost-aware trading metrics;
- failure cases;
- decision to accept, reject, or keep under investigation.

## Acceptance Rule

Recent algorithms may be evaluated, but they must not replace a simpler model without reproducible out-of-sample improvement.
