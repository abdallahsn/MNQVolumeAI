# MNQ Labeling And Leakage Specification

Scope: event-based labels for deterministic setup candidates.

## Label Philosophy

Labels may look forward. Features, setup generation, filters, scalers, model
selection, and validation may not.

The label answers:

> After this deterministic setup was confirmed, would a realistic execution have
> produced a favorable result after costs?

It does not choose LONG or SHORT.

## Required Labels

```text
setup_success
net_return_R_after_costs
maximum_adverse_excursion_ticks
maximum_favorable_excursion_ticks
time_to_target_or_stop
first_barrier_hit
timeout_flag
entry_fill_price
exit_fill_price
commission_paid
slippage_ticks
label_start_ts
label_end_ts
label_valid
```

## Target Roles

| Column | Role | Feature use |
|---|---|---|
| `setup_success` | classification target | forbidden |
| `net_return_R_after_costs` | regression target | forbidden |
| `maximum_adverse_excursion_ticks` | quantile target/diagnostic | forbidden |
| `maximum_favorable_excursion_ticks` | quantile target/diagnostic | forbidden |
| `time_to_target_or_stop` | holding-time target | forbidden |
| `first_barrier_hit` | diagnostic/target | forbidden |
| `timeout_flag` | diagnostic | forbidden |
| `label_*` | metadata | forbidden |

## Execution Assumptions

Labels must account for:

1. structural stop;
2. target levels;
3. max holding time;
4. commission;
5. slippage;
6. tick rounding;
7. delayed entry;
8. stop-market slippage;
9. forced session-close exit where configured.

Same-bar dual hits must be conservative. If ordering cannot be known, choose the
less favorable path or mark ambiguous depending on the label policy.

## Repeated Event Prevention

Required fields:

```text
event_identity
dedupe_group_id
cooldown_bars
one_active_signal
```

Rows from the same structural event should not create repeated correlated labels
unless the event was explicitly reset.

## Purging Metadata

Every label row must expose:

```text
label_start_ts
label_end_ts
effective_horizon_bars
crosses_session_break
```

Purged walk-forward must remove training rows whose label windows overlap
validation/test windows.

## Leakage Blacklist

These patterns must never enter feature matrices:

```text
label_*
setup_success
net_return_R*
maximum_adverse_excursion*
maximum_favorable_excursion*
mfe*
mae*
first_barrier_hit
timeout_flag
time_to_target*
time_to_stop*
trade_duration
entry_fill_price
exit_fill_price
commission_paid
slippage_ticks
label_end_ts
dataset_slice
is_train_slice
is_holdout_slice
is_purged_slice
```

The restored or recreated `modules/dataset_schema.py` must include these labels
with `LEAKAGE_TARGET` or `LEAKAGE_FORWARD`.

## Automated Leakage Tests

1. Feature recomputation on truncated data matches full data at t.
2. Feature matrix builder fails closed if a label column is present.
3. Train/validation split is chronological.
4. Scalers and encoders are fit on training fold only.
5. Feature selection uses training fold only.
6. Purging removes overlapping label windows.
7. Final holdout is not used for threshold or parameter selection.

## Acceptance Criteria

1. labels are deterministic and reproducible.
2. costs are included in `net_return_R_after_costs`.
3. invalid/cross-session labels are masked.
4. label side is inherited from setup, not inferred by model.
5. every label family is registered in schema.
6. all leakage tests pass.

