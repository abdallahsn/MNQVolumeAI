# Graph Report - MNQVolumeAI  (2026-07-13)

## Corpus Check
- 73 files · ~49,716 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 651 nodes · 1039 edges · 69 communities (32 shown, 37 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 81 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4f8eae84`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_Community 11|Community 11]]
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
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]

## God Nodes (most connected - your core abstractions)
1. `Decimal` - 24 edges
2. `Phase1Config` - 21 edges
3. `MNQ Volume Profile AI Master Plan` - 18 edges
4. `FailedFVGConfig` - 17 edges
5. `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` - 17 edges
6. `ConfigurationError` - 16 edges
7. `backtest_file()` - 15 edges
8. `Bar` - 15 edges
9. `MNQVolumeAI` - 15 edges
10. `MNQ Volume Profile AI Master Plan` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_config_validates_tick_and_timezone()` --calls--> `Decimal`  [INFERRED]
  tests/test_phase1_config.py → src/mnq_ai/setups/failed_fvg.py
- `datetime` --uses--> `FailedFVGConfig`  [INFERRED]
  tests/test_failed_fvg_setup_engine.py → src/mnq_ai/setups/failed_fvg.py
- `int` --uses--> `FailedFVGConfig`  [INFERRED]
  tests/test_failed_fvg_setup_engine.py → src/mnq_ai/setups/failed_fvg.py
- `str` --uses--> `FailedFVGConfig`  [INFERRED]
  tests/test_failed_fvg_setup_engine.py → src/mnq_ai/setups/failed_fvg.py
- `test_failed_bull_fvg_emits_short_candidate_from_next_bar_entry()` --calls--> `FailedFVGConfig`  [INFERRED]
  tests/test_failed_fvg_setup_engine.py → src/mnq_ai/setups/failed_fvg.py

## Import Cycles
- 1-file cycle: `src/mnq_ai/setups/failed_fvg.py -> src/mnq_ai/setups/failed_fvg.py`
- 1-file cycle: `tests/test_failed_fvg_candidate_pipeline.py -> tests/test_failed_fvg_candidate_pipeline.py`
- 1-file cycle: `tests/test_phase2_execution_gate.py -> tests/test_phase2_execution_gate.py`
- 1-file cycle: `tests/test_failed_fvg_setup_engine.py -> tests/test_failed_fvg_setup_engine.py`

## Communities (69 total, 37 thin omitted)

### Community 0 - "Skill Validation and Parsing"
Cohesion: 0.07
Nodes (41): auction-feature-engineering Skill, dependency-governor Skill, execution-backtest-gate Skill, mbo-data-causality Skill, out-of-core-data-engineering Skill, quant-model-validation Skill, quant-research-scout Skill, Ablation Requirement (+33 more)

### Community 1 - "Skill and Algorithm Policies"
Cohesion: 0.08
Nodes (48): ArgumentParser, Exception, float, _config_from_args(), main(), _parser(), Command-line interface for MNQ research pipeline jobs., Run the ``mnq-ai`` CLI. (+40 more)

### Community 2 - "MNQ Project Specifications"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 3 - "Limit Order Book Forecasting"
Cohesion: 0.11
Nodes (26): MNQ Volume Profile AI Master Plan, Acceptance Criteria By Phase, Current Architecture Inventory, Current Issues And Risks, Data Readiness Assessment, Deleted but required before implementation, Deleted or generated paths that should not block the rebuild, Dependency Graph (+18 more)

### Community 4 - "LLM Agents for Trading"
Cohesion: 0.23
Nodes (15): Any, bool, _load_yaml_with_extends(), _parse_hms(), Return a validated copy with common CLI overrides., Fail closed on invalid configuration., Load a config file, following a single optional ``extends`` reference., Build and validate config from a mapping. (+7 more)

### Community 5 - "Hook Utilities"
Cohesion: 0.14
Nodes (22): MNQ Walk-Forward And Backtest Specification, Acceptance Criteria, Automated Leakage Tests, Execution Assumptions, Label Philosophy, Leakage Blacklist, MNQ Labeling And Leakage Specification, Purging Metadata (+14 more)

### Community 6 - "Reinforcement Learning Trading"
Cohesion: 0.13
Nodes (22): Comprehensive Research Report: Volume Profile Analysis in Financial Markets, 1. Concepts and Historical Origin of Volume-by-Price Studies, 2. Microeconomic Foundations and Continuous Auction Theory, 3. Mathematical Structure and Calculation of Volume Profile Levels, 4.1 Price Interaction with POC Levels on Poland's WIG20 Index, 4.2 Taiwan Market Profile Study and Weak-Form Market Efficiency, 4.3 Volume-Centred Range Bars (VCRB) for Machine Learning Pattern Extraction, 4.4 Fair Value Gaps and Linear Regression Slope of Liquidity (+14 more)

### Community 7 - "Decentralized Market Microstructure"
Cohesion: 0.09
Nodes (21): 1. Concepts and Historical Origin of Volume-by-Price Studies, 2. Microeconomic Foundations and Continuous Auction Theory, 3. Mathematical Structure and Calculation of Volume Profile Levels, 4.1 Price Interaction with POC Levels on Poland's WIG20 Index, 4.2 Taiwan Market Profile Study and Weak-Form Market Efficiency, 4.3 Volume-Centred Range Bars (VCRB) for Machine Learning Pattern Extraction, 4.4 Fair Value Gaps and Linear Regression Slope of Liquidity, 4. Major Academic Studies and Empirical Analyses (+13 more)

### Community 8 - "MNQVolumeAI Utility Scripts"
Cohesion: 0.09
Nodes (21): 1. Concepts and Historical Origin of Volume-by-Price Studies, 2. Microeconomic Foundations and Continuous Auction Theory, 3. Mathematical Structure and Calculation of Volume Profile Levels, 4.1 Price Interaction with POC Levels on Poland's WIG20 Index, 4.2 Taiwan Market Profile Study and Weak-Form Market Efficiency, 4.3 Volume-Centred Range Bars (VCRB) for Machine Learning Pattern Extraction, 4.4 Fair Value Gaps and Linear Regression Slope of Liquidity, 4. Major Academic Studies and Empirical Analyses (+13 more)

### Community 9 - "MNQVolumeAI Test Utilities"
Cohesion: 0.08
Nodes (21): Engineering Rules, graphify, Mandatory Project Skills, Phase 1 Data Architecture, CME Session Definition, Trade Tape Contract, 2026-07-13 Update: `tzdata`, Decisions (+13 more)

### Community 10 - "Survival Analysis in Order Books"
Cohesion: 0.26
Nodes (12): int, Path, load_skill(), main(), parse_front_matter(), int, Path, str (+4 more)

### Community 11 - "Community 11"
Cohesion: 0.23
Nodes (13): Acceptance Criteria, Checks, Chunking Strategy, MBO Trade Semantics, MNQ Data Audit Plan, Objectives, Price and size checks, Required Audit Outputs (+5 more)

### Community 12 - "LSTM Trend Forecasting"
Cohesion: 0.12
Nodes (25): MNQ Phase 0 Rebuild And Cleanup Decision, MNQ Phase 1 Implementation Tasks, Current Finding, Exact Next Patch After Approval, Files Not To Edit In The First Implementation Patch, MNQ Phase 0 Rebuild And Cleanup Decision, Recommended Decision, Stop/Go (+17 more)

### Community 13 - "Natural Language to Option Strategies"
Cohesion: 0.33
Nodes (10): MNQ Deterministic Setup Engine Specification, Acceptance Criteria, Candidate Setups, Core Principle, Deduplication Rules, MNQ Deterministic Setup Engine Specification, Online State Requirements, Reason Codes (+2 more)

### Community 14 - "Reinforcement Learning for Trading"
Cohesion: 0.09
Nodes (40): Decimal, EntrySide, FVGType, Shared constants for Phase 1 market-data processing., Bar, build_h1_fvgs(), FailedFVGSetupEngine, FVG (+32 more)

### Community 15 - "LLM Debiasing Techniques"
Cohesion: 0.23
Nodes (21): DataFrame, Figure, add_horizontal_segment(), build_candles(), build_chart(), detect_fvgs(), first_full_fill_index(), load_candidates() (+13 more)

### Community 16 - "Institutional Liquidity Impact"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 17 - "Out-of-Money RL Trading Models"
Cohesion: 0.29
Nodes (6): Acceptance Rule, Decision Record, dependency-governor, Do Not Trigger, Required Workflow, Trigger

### Community 18 - "Microstructure Regime Detection"
Cohesion: 0.29
Nodes (6): Candidate Tools, Do Not Trigger, out-of-core-data-engineering, Required Outputs, Required Workflow, Trigger

### Community 19 - "Research Corpus Overview"
Cohesion: 0.29
Nodes (6): Acceptance Rule, Do Not Trigger, quant-model-validation, Required Outputs, Required Workflow, Trigger

### Community 20 - "Research Catalog"
Cohesion: 0.29
Nodes (6): Acceptance Rule, Do Not Trigger, Evidence Types, quant-research-scout, Required Workflow, Trigger

### Community 21 - "Research Gaps Identification"
Cohesion: 0.14
Nodes (21): Allowed Feature Families, `auction_rejection_features`, `cvd_delta_features`, Feature Family Contracts, Feature Sidecar, Forbidden Directional Inputs, Global Rules, `intraday_context_features` (+13 more)

### Community 24 - "Riskfolio-Lib GitHub Repository"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 25 - "Nautilus Trader GitHub Repository"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 26 - "Price Formation Features"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 27 - "Bayesian Deep CNN for Order Books"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 28 - "Order-Flow Imbalance Analysis"
Cohesion: 0.67
Nodes (3): Deep Limit Order Book Forecasting, HLOB -- Information Persistence and Structure in Limit Order Books, TLOB: A Novel Transformer Model with Dual Attention for Price Trend Prediction with Limit Order Book Data

### Community 29 - "Community 29"
Cohesion: 0.67
Nodes (3): ATLAS: Adaptive Trading with LLM AgentS Through Dynamic Prompt Optimization and Multi-Agent Coordination, Large Language Models and Stock Investing: Is the Human Factor Required?, Learning to Aggregate Zero-Shot LLM Agents for Corporate Disclosure Classification

### Community 66 - "Community 66"
Cohesion: 0.29
Nodes (10): datetime, float, int, object, Path, str, test_build_failed_fvg_candidates_cli_writes_manifest_and_parquet(), _trade() (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (12): _candidate(), datetime, float, int, object, Path, str, test_phase2_execution_gate_labels_first_barrier_after_entry() (+4 more)

### Community 68 - "Community 68"
Cohesion: 0.17
Nodes (28): backtest_file(), build_bars(), build_h1_fvgs(), calculate_contracts(), detect_failed_fvg_signal(), empty_summary(), execute_trade(), FVG (+20 more)

## Knowledge Gaps
- **199 isolated node(s):** `PreToolUse`, `Namespace`, `Namespace`, `Timestamp`, `int` (+194 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Decimal` connect `Reinforcement Learning for Trading` to `Skill and Algorithm Policies`, `LLM Agents for Trading`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `MNQ Volume Profile AI Master Plan` connect `Limit Order Book Forecasting` to `Community 11`, `LSTM Trend Forecasting`, `Reinforcement Learning Trading`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` connect `Reinforcement Learning Trading` to `Hook Utilities`, `Limit Order Book Forecasting`, `LSTM Trend Forecasting`, `Research Gaps Identification`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Decimal` (e.g. with `main()` and `.from_mapping()`) actually correct?**
  _`Decimal` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Phase1Config` (e.g. with `ArgumentParser` and `float`) actually correct?**
  _`Phase1Config` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `FailedFVGConfig` (e.g. with `ArgumentParser` and `main()`) actually correct?**
  _`FailedFVGConfig` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` (e.g. with `MNQ Volume Profile AI Master Plan` and `mnq_labeling_and_leakage_spec.md`) actually correct?**
  _`Comprehensive Research Report: Volume Profile Analysis in Financial Markets` has 3 INFERRED edges - model-reasoned connections that need verification._