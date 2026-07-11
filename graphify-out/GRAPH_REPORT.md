# Graph Report - .  (2026-07-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 74 nodes · 75 edges · 29 communities (5 shown, 24 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Skill Validation and Parsing|Skill Validation and Parsing]]
- [[_COMMUNITY_Skill and Algorithm Policies|Skill and Algorithm Policies]]
- [[_COMMUNITY_MNQ Project Specifications|MNQ Project Specifications]]
- [[_COMMUNITY_Limit Order Book Forecasting|Limit Order Book Forecasting]]
- [[_COMMUNITY_LLM Agents for Trading|LLM Agents for Trading]]
- [[_COMMUNITY_Hook Utilities|Hook Utilities]]
- [[_COMMUNITY_Reinforcement Learning Trading|Reinforcement Learning Trading]]
- [[_COMMUNITY_Decentralized Market Microstructure|Decentralized Market Microstructure]]
- [[_COMMUNITY_MNQVolumeAI Utility Scripts|MNQVolumeAI Utility Scripts]]
- [[_COMMUNITY_MNQVolumeAI Test Utilities|MNQVolumeAI Test Utilities]]
- [[_COMMUNITY_Survival Analysis in Order Books|Survival Analysis in Order Books]]
- [[_COMMUNITY_Price Prediction with Deep Learning|Price Prediction with Deep Learning]]
- [[_COMMUNITY_LSTM Trend Forecasting|LSTM Trend Forecasting]]
- [[_COMMUNITY_Natural Language to Option Strategies|Natural Language to Option Strategies]]
- [[_COMMUNITY_Reinforcement Learning for Trading|Reinforcement Learning for Trading]]
- [[_COMMUNITY_LLM Debiasing Techniques|LLM Debiasing Techniques]]
- [[_COMMUNITY_Institutional Liquidity Impact|Institutional Liquidity Impact]]
- [[_COMMUNITY_Out-of-Money RL Trading Models|Out-of-Money RL Trading Models]]
- [[_COMMUNITY_Microstructure Regime Detection|Microstructure Regime Detection]]
- [[_COMMUNITY_Research Corpus Overview|Research Corpus Overview]]
- [[_COMMUNITY_Research Catalog|Research Catalog]]
- [[_COMMUNITY_Research Gaps Identification|Research Gaps Identification]]
- [[_COMMUNITY_StockSharp GitHub Repository|StockSharp GitHub Repository]]
- [[_COMMUNITY_TradeMaster GitHub Repository|TradeMaster GitHub Repository]]
- [[_COMMUNITY_Riskfolio-Lib GitHub Repository|Riskfolio-Lib GitHub Repository]]
- [[_COMMUNITY_Nautilus Trader GitHub Repository|Nautilus Trader GitHub Repository]]
- [[_COMMUNITY_Price Formation Features|Price Formation Features]]
- [[_COMMUNITY_Bayesian Deep CNN for Order Books|Bayesian Deep CNN for Order Books]]
- [[_COMMUNITY_Order-Flow Imbalance Analysis|Order-Flow Imbalance Analysis]]

## God Nodes (most connected - your core abstractions)
1. `Claims Registry` - 11 edges
2. `validate()` - 9 edges
3. `MNQVolumeAI Project README` - 8 edges
4. `Phase 0.5 Skill Trigger Tests` - 7 edges
5. `Path` - 6 edges
6. `MNQ Feature Contract` - 6 edges
7. `load_skill()` - 5 edges
8. `MNQ Phase 0 Rebuild And Cleanup Decision` - 5 edges
9. `parse_front_matter()` - 4 edges
10. `main()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Phase 0.5 Skill Trigger Tests` --references--> `mbo-data-causality Skill`  [EXTRACTED]
  docs/phases/phase0_5_skill_trigger_tests.md → .agents/skills/mbo-data-causality/SKILL.md
- `MNQVolumeAI Project README` --references--> `mbo-data-causality Skill`  [EXTRACTED]
  README.md → .agents/skills/mbo-data-causality/SKILL.md
- `Phase 0.5 Skill Trigger Tests` --references--> `auction-feature-engineering Skill`  [EXTRACTED]
  docs/phases/phase0_5_skill_trigger_tests.md → .agents/skills/auction-feature-engineering/SKILL.md
- `MNQVolumeAI Project README` --references--> `auction-feature-engineering Skill`  [EXTRACTED]
  README.md → .agents/skills/auction-feature-engineering/SKILL.md
- `Phase 0.5 Skill Trigger Tests` --references--> `quant-model-validation Skill`  [EXTRACTED]
  docs/phases/phase0_5_skill_trigger_tests.md → .agents/skills/quant-model-validation/SKILL.md

## Import Cycles
- None detected.

## Communities (29 total, 24 thin omitted)

### Community 0 - "Skill Validation and Parsing"
Cohesion: 0.31
Nodes (9): int, Path, load_skill(), main(), parse_front_matter(), SkillDoc, validate(), str (+1 more)

### Community 1 - "Skill and Algorithm Policies"
Cohesion: 0.26
Nodes (12): auction-feature-engineering Skill, dependency-governor Skill, execution-backtest-gate Skill, graphify Skill, mbo-data-causality Skill, out-of-core-data-engineering Skill, quant-model-validation Skill, quant-research-scout Skill (+4 more)

### Community 2 - "MNQ Project Specifications"
Cohesion: 0.30
Nodes (12): Claims Registry, MNQ Data Audit Plan, MNQ Feature Contract, MNQ Labeling And Leakage Specification, MNQ Model And Calibration Specification, MNQ Phase 0 Rebuild And Cleanup Decision, MNQ Phase 1 Implementation Tasks, MNQ Risk Register (+4 more)

### Community 3 - "Limit Order Book Forecasting"
Cohesion: 0.67
Nodes (3): Deep Limit Order Book Forecasting, HLOB -- Information Persistence and Structure in Limit Order Books, TLOB: A Novel Transformer Model with Dual Attention for Price Trend Prediction with Limit Order Book Data

### Community 4 - "LLM Agents for Trading"
Cohesion: 0.67
Nodes (3): ATLAS: Adaptive Trading with LLM AgentS Through Dynamic Prompt Optimization and Multi-Agent Coordination, Large Language Models and Stock Investing: Is the Human Factor Required?, Learning to Aggregate Zero-Shot LLM Agents for Corporate Disclosure Classification

## Knowledge Gaps
- **32 isolated node(s):** `PreToolUse`, `int`, `Deep Attentive Survival Analysis in Limit Order Books`, `HLOB -- Information Persistence and Structure in Limit Order Books`, `Price predictability in limit order book with deep learning model` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `PreToolUse`, `Utility scripts for MNQVolumeAI.`, `int` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._