# MNQ Deterministic Setup Engine Specification

Scope: deterministic setup generation. The setup engine chooses setup type,
side, entry, invalidation, stops, targets, max holding time, and reason codes.
The ML model only decides ENTER or NO_TRADE.

## Core Principle

The model must not learn market direction from raw market data. Direction comes
from the setup definition.

```text
setup engine -> deterministic entry_side
meta model   -> take or skip that setup
```

## Setup Candidate Schema

Required columns:

```text
setup_id
ts_event
symbol
cme_session_id
setup_type
entry_side
reference_level
entry_price
structural_invalidation
stop_price
target_1
target_2
target_3
max_holding_bars
max_holding_seconds
reason_codes
feature_timestamp
setup_version
```

Optional diagnostics:

```text
vp_level_name
distance_to_reference_ticks
delta_context
vwap_context
day_type_context
dedupe_group_id
cooldown_until
```

## Candidate Setups

| Setup | Side rule | Reference |
|---|---|---|
| Look Above and Fail | SHORT | Price probes above VAH/prior high and re-enters value. |
| Look Below and Fail | LONG | Price probes below VAL/prior low and re-enters value. |
| VAH Rejection | SHORT | Rejection at VAH with failed acceptance. |
| VAL Rejection | LONG | Rejection at VAL with failed acceptance. |
| Value-Area Acceptance Retest | Side follows accepted breakout direction | Acceptance outside value then causal retest. |
| VWAP + VP Confluence | Side from setup geometry | VWAP reclaim/reject aligns with VP level. |
| Naked POC Reaction | Side from rejection/attraction pattern | Untouched prior POC. |
| LVN Transition | Side toward next HVN | Acceptance through LVN. |
| Developing POC Migration | Side from migration + price response | POC migration and acceptance. |
| Auction Excess / Failed Auction | Side against failed auction | Excess tail or poor high/low proxy. |

## Online State Requirements

Some setups require state across bars. The state machine must track:

1. probe start time;
2. level touched;
3. max ticks outside value so far;
4. volume/delta outside value so far;
5. re-entry time;
6. confirmation time;
7. cooldown and dedupe group.

Do not mark confirmation at the original probe timestamp unless confirmation was
known at that timestamp. Use separate occurrence and confirmation timestamps.

## Deduplication Rules

1. Define `dedupe_group_id` from session, setup type, reference level, and side.
2. Do not emit repeated labels for the same structural event.
3. Enforce one active signal per side and setup group unless explicitly allowed.
4. Cooldown starts after exit, timeout, or invalidation.

## Stop And Target Rules

Stops and targets must be structural and tick-rounded:

| Field | Rule |
|---|---|
| `entry_price` | next actionable price after confirmation, not same-bar hindsight. |
| `structural_invalidation` | level that invalidates setup logic. |
| `stop_price` | structural invalidation plus buffer, rounded to tick. |
| `target_1..3` | next VP/VWAP/session levels or fixed R multiples from setup spec. |
| `max_holding_time` | setup-specific and known at decision time. |

## Reason Codes

Reason codes are deterministic strings, for example:

```text
LAF_REENTERED_VALUE
VAH_REJECTION_TAIL
CVD_DIVERGENCE_SUPPORTS_REJECTION
VWAP_RECLAIM_CONFIRMED
NEAR_PRIOR_NAKED_POC
LOW_ACCEPTANCE_TIME
DAY_TYPE_ROTATIONAL
```

Reason codes explain why the setup exists. They must not use future outcome.

## Acceptance Criteria

1. setup generation is deterministic for identical input.
2. every setup has exactly one `entry_side`.
3. model target columns are absent from setup features.
4. occurrence and confirmation times are explicit.
5. setup output can be labeled independently.
6. no order-book depth directional features are used.

