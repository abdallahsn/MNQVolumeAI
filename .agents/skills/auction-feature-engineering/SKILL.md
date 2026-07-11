---
name: auction-feature-engineering
description: "Use for Volume Profile, CVD, VWAP, auction, rejection, acceptance, and setup features; do not run for labels, models, or dependencies alone."
---

# auction-feature-engineering

## Trigger

Use this Skill when designing or implementing Volume Profile, CVD, VWAP, Auction Market Theory, rejection, acceptance, session context, or deterministic setup features.

## Do Not Trigger

Do not run this Skill for dependency changes, generic model validation, raw MBO parsing without feature design, or backtest fill logic without feature changes.

## Required Workflow

- All current-session features must be developing and causal.
- Previous-session levels may use only completed previous sessions.
- No full-session POC, VAH, VAL, VWAP, high, low, or volume can appear intraday before it becomes known.
- Volume Profile must be built from executed `T` trades.
- Tick-size alignment must be explicit.
- Store feature timestamps and availability timestamps.
- Give every feature a mathematical definition.
- Use trailing windows only; never centered windows.
- Do not backward-fill from future values.
- Do not derive direction from depth.
- Setup direction must be deterministic from setup rules.
- The ML layer takes or skips a setup rather than learning direction from raw depth.
- Every feature needs leakage and invariance tests.

## Required Checks

1. Document the exact input columns and availability timestamp.
2. Document whether a feature is current-session developing, previous-session completed, or trailing-window.
3. Test that recomputing on a truncated stream yields identical values up to the truncation point.
4. Test tick-size rounding and bin alignment.
5. Test missing-data behavior without silent future fill.

## Ablation Requirement

Require an ablation plan before accepting a large feature family.
