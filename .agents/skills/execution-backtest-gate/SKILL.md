---
name: execution-backtest-gate
description: "Use for labels, fills, slippage, commissions, replay, paper trading, or release gates; do not run for research or feature design alone."
---

# execution-backtest-gate

## Trigger

Use this Skill when implementing labels, trade simulation, stops, targets, fills, slippage, commissions, replay, paper trading, or production-readiness decisions.

## Do Not Trigger

Do not run this Skill for dependency updates, raw data ingestion, feature engineering without fills, or model research that does not affect execution or release readiness.

## Required Workflow

- Enforce causal entry eligibility.
- No fill may occur before a signal exists.
- Reject impossible fills.
- Round all prices to valid ticks.
- Include commissions.
- Include slippage.
- Include entry latency.
- Include stop-market slippage.
- Define first-barrier ambiguity handling.
- Define maximum holding time.
- Define session-close policy.
- Enforce one-position rules.
- Enforce cooldown.
- Enforce daily loss limits.
- Run stress tests.
- Run delayed-entry tests.
- Run doubled-cost tests.
- Do not use future bar high/low to improve an entry.
- Require paper-trading parity checks before release.
- Apply a fail-closed production gate.

## Required Evidence

For every gate decision, list:

- signal timestamp;
- earliest eligible entry timestamp;
- fill model;
- fee/slippage assumptions;
- ambiguity policy;
- risk limits;
- stress-test results;
- remaining production blockers.

## Gate Output

Output exactly one recommendation:

- GO
- CONDITIONAL GO
- NO-GO

List the evidence for the decision and fail closed when execution realism cannot be proven.
