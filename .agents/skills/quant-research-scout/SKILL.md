---
name: quant-research-scout
description: "Use for trading algorithm, labeling, validation, microstructure, feature, or model research; do not run for local-only edits or non-research tasks."
---

# quant-research-scout

## Trigger

Use this Skill when researching a trading algorithm, labeling method, validation method, market-microstructure concept, feature family, model architecture, or recent quantitative-finance technique.

## Do Not Trigger

Do not run this Skill for formatting, project-tree inspection, local script edits with no research choice, or implementation work where the research decision has already been recorded.

## Required Workflow

1. Prefer primary sources: peer-reviewed papers, arXiv originals, exchange documentation, official vendor documentation, and original library documentation.
2. Search for both recent work and foundational work.
3. Record the search date.
4. Separate published evidence from implementation hypotheses.
5. Examine dataset, instrument, sample period, transaction costs, split method, leakage controls, baselines, statistical significance, reproducibility, and code availability.
6. Reject papers using random row splits for dependent time series unless the result is studied specifically as a flawed baseline.
7. Do not transfer reported results from ES, NQ, equities, crypto, FX, or other markets to MNQ without independent validation.
8. Compare every recent algorithm to at least one simple baseline.
9. Do not choose deep learning merely because it is newer.
10. Add useful papers or notes to `docs/research/research_catalog.yaml`.
11. Update `docs/research/claims_registry.md`.
12. Run a Graphify incremental update after adding research materials.
13. Produce a short algorithm decision record before implementation.

## Evidence Types

Distinguish:

- research finding;
- engineering decision;
- trading assumption;
- empirical result;
- unresolved question.

## Acceptance Rule

Reported win rates, profit factors, Sharpe values, and drawdowns remain unverified until reproduced with causal, cost-aware, out-of-sample validation in this repository.
