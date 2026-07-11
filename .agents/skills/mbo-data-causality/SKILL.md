---
name: mbo-data-causality
description: "Use for Databento MBO ingestion, trade extraction, timestamps, CME sessions, and data quality; do not run for non-market-data work."
---

# mbo-data-causality

## Trigger

Use this Skill for Databento MBO ingestion, trade extraction, timestamps, CME sessions, executed volume, signed trade volume, or market-data quality.

## Do Not Trigger

Do not run this Skill for generic dependency decisions, documentation-only edits, model selection, or backtest execution unless MBO/session causality is involved.

## Required Workflow

- Treat `action == "T"` as the sole executed-trade volume source.
- Do not count `action == "F"` again.
- Map `side == "B"` to positive signed volume.
- Map `side == "A"` to negative signed volume.
- Map `side == "N"` to zero and unknown.
- Do not allow `A`, `C`, `M`, `R`, or `F` actions to become directional features.
- Preserve UTC timestamps.
- Derive CME sessions with an exchange-calendar-aware method.
- Do not represent DST with a permanently fixed UTC offset.
- Make event ordering deterministic.
- Detect partial sessions.
- Quarantine or explicitly reject invalid rows.
- Prove that no future event can affect an earlier feature.
- Reconcile volume against independent aggregates where available.
- Never load full MBO data blindly into pandas.

## Required Checks

1. Validate timestamp monotonicity within deterministic event order.
2. Validate symbol and contract continuity.
3. Validate prices, sizes, tick increments, duplicate rows, and abnormal gaps.
4. Record rejected or quarantined rows with counts and reasons.
5. Produce a smoke test on a bounded subset before full execution.

## Fail-Closed Rule

Fail closed when causal ordering, executed-volume semantics, or session assignment cannot be proven.
