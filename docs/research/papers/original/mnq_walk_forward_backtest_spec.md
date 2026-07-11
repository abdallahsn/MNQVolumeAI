# MNQ Walk-Forward And Backtest Specification

Scope: chronological validation and realistic setup-driven backtesting.

## Data Split Rules

Random train/test splits are prohibited.

Recommended structure when enough sessions exist:

```text
final holdout: last 15-20% of sessions, untouched until final report
development: earlier sessions only
walk-forward inside development:
  train: 120 sessions
  validation: 20 sessions
  test: 20 sessions
  advance: 20 sessions
```

The current five-day MNQM6 sample is not enough for model validation. Use it only
for engineering correctness.

## Purge And Embargo

1. purge length must be at least the maximum labeling horizon.
2. embargo after validation/test windows prevents overlap leakage.
3. all folds use session order.
4. setup labels with `label_end_ts` crossing a fold boundary are excluded.

## Backtest Engine Requirements

The backtester must model:

```text
commission
configurable slippage
tick rounding
entry latency
stop-market slippage
time stops
partial exits
one-position-at-a-time option
maximum daily loss
maximum trades per session
cooldown
RTH/overnight controls
forced exit before session close
no fills at impossible prices
```

Same-bar entry and exit must not use future bar extremes to improve fills.

## Stress Tests

Required scenarios:

```text
zero slippage
one tick slippage
two tick slippage
three tick slippage
250 ms entry delay
one second entry delay
doubled commission
missing-data simulation
reduced-liquidity periods
```

## Evaluation Metrics

### Classification

```text
PR-AUC
ROC-AUC
precision at trading threshold
recall
Brier score
log loss
expected calibration error
```

### Trading

```text
net expectancy in R
profit factor
win rate
average win
average loss
maximum drawdown
number of trades
exposure
trade duration
performance per setup type
performance per session segment
performance per volatility regime
performance after costs
```

### Regression

```text
MAE
quantile loss
MFE/MAE prediction coverage
holding-time error
```

## Reporting

Every fold report must include:

1. fold date/session ranges;
2. train/validation/test row counts;
3. purge and embargo counts;
4. setup counts by type;
5. class balance;
6. calibration metrics;
7. trading metrics after costs;
8. slippage/latency stress table;
9. feature blacklist check result.

## Acceptance Criteria

1. fold construction is reproducible from sessions.
2. no random split path exists in the MNQ pipeline.
3. purging and embargo are active.
4. backtest cost assumptions are explicit in reports.
5. fold-level and aggregate metrics are both produced.

