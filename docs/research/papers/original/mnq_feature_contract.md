# MNQ Feature Contract

Scope: causal feature families for the initial MNQ setup-validation baseline.
Depth-derived direction learning is prohibited.

## Forbidden Directional Inputs

The meta model must not use these as directional inputs:

```text
resting bid/ask depth
order-book imbalance
queue position
microprice
depth pressure
cancellation imbalance
add/cancel/modify pressure
spoofing indicators
DOM-derived long/short prediction
```

Depth and order-book state may be used only for descriptive diagnostics after a
separate approval, not for deciding LONG/SHORT or setup success in the initial
baseline.

## Allowed Feature Families

| Family | Source | Current code |
|---|---|---|
| Volume Profile | executed trades / bars | `features/volume_profile_features.py`, `volume_profile/` |
| Auction rejection | OHLC + VP levels + delta | `features/auction_rejection_features.py` |
| CVD/delta | MBO `T` trades with aggressor side | `features/cvd_delta_features.py` |
| VWAP | executed volume | `features/vwap_features.py` |
| Intraday context | timestamps/session state | `features/intraday_context_features.py` |

## Global Rules

1. Every feature row must satisfy `feature_timestamp <= decision_timestamp`.
2. Current-session aggregates must be online, not full-session.
3. Prior-session levels must be shifted from completed sessions only.
4. Use CME session IDs, not UTC date groups.
5. Rolling windows must be trailing.
6. Missing MBO aggressor side creates invalid CVD/delta features, not inferred
   direction.
7. Labels, MFE, MAE, barrier hits, and outcome diagnostics are never features.

## Feature Family Contracts

### `volume_profile_features`

Required outputs:

```text
prior_vp_poc, prior_vp_vah, prior_vp_val
current_vp_poc, current_vp_vah, current_vp_val
current_vp_profile_high, current_vp_profile_low
current_vp_value_area_width
current_vp_total_volume
current_vp_distance_to_poc_ticks
current_vp_distance_to_vah_ticks
current_vp_distance_to_val_ticks
vp_price_location
vp_poc_migration
vp_value_area_migration
naked_poc_distance_ticks
naked_poc_first_touch
rolling_vp_<window>_poc/vah/val
```

Current status: code is mostly causal because current profile is updated
row-by-row. Required fix: inject CME session IDs; do not allow default UTC date
session grouping for production training.

### `auction_rejection_features`

Required outputs:

```text
look_above_value_fail
look_below_value_fail
vah_rejection_short_condition
val_rejection_long_condition
auction_acceptance_above_value
auction_acceptance_below_value
ticks_outside_value
time_outside_value_so_far
volume_outside_value_so_far
delta_outside_value_so_far
reentry_speed
acceptance_time_so_far
rejection_tail_size
price_progress_per_volume
price_progress_per_delta
```

Current status: row-local flags exist. Required addition: online state-machine
features for duration/volume/delta outside value without future confirmation.

### `cvd_delta_features`

Required outputs:

```text
bar_delta
session_cvd
cvd_slope_<window>
delta_acceleration
buy_volume
sell_volume
delta_volume_ratio
price_cvd_divergence_<window>
delta_at_poc/vah/val/vwap
absorption_proxy_from_trades
exhaustion_proxy_from_trades
price_progress_per_contract
cvd_delta_valid
```

Current status: module correctly requires explicit side or buy/sell volume.
Required fix: use CME session IDs and `action == "T"` extraction upstream.

### `vwap_features`

Required outputs:

```text
session_vwap
session_vwap_dist_ticks
session_vwap_slope
session_vwap_velocity
vwap_reclaim_flag
vwap_rejection_flag
vwap_cross_count_so_far
time_above_vwap_so_far
volume_above_vwap_so_far
vwap_deviation_band_1/2/3
vwap_distance_zscore_trailing
```

Current status: cumulative VWAP is causal. Required fix: CME session IDs and
tick-normalized distance columns.

### `intraday_context_features`

Required outputs:

```text
cme_session_id
trading_date
is_rth
is_overnight
seconds_from_session_open
seconds_to_session_close
session_segment
opening_range_so_far
previous_session_high/low/close
overnight_high/low_so_far
session_gap
realized_volatility_trailing
rolling_range_trailing
trend_efficiency_trailing
chop_score_trailing
current_session_volume_percentile_so_far
current_session_delta_percentile_so_far
developing_day_type
```

Current status: basic timestamp features exist, but default UTC date grouping is
not acceptable for production.

## Leakage Tests Required

For each family:

1. recompute features on truncated data ending at t and compare row t to full
   computation;
2. assert no future label/outcome columns are present;
3. assert rolling windows are trailing;
4. assert prior-session features are absent for the first session or shifted
   from a completed prior session;
5. assert feature values do not change when future rows are shuffled or removed.

## Feature Sidecar

Every feature parquet must ship with:

```json
{
  "schema_version": "mnq_phase1_feature_contract",
  "symbol": "MNQM6",
  "tick_size": 0.25,
  "session_calendar": "CME Globex MNQ",
  "feature_timestamp_col": "ts_event",
  "forbidden_depth_direction_inputs_excluded": true,
  "families": {}
}
```

