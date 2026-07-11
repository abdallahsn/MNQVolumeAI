# Graph Report - .  (2026-07-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 445 nodes · 516 edges · 62 communities (33 shown, 29 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3d19ada2`
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

## God Nodes (most connected - your core abstractions)
1. `Phase1Config` - 18 edges
2. `MNQ Volume Profile AI Master Plan` - 18 edges
3. `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` - 17 edges
4. `Phase 0.5 Skill Trigger Tests` - 15 edges
5. `ConfigurationError` - 14 edges
6. `MNQVolumeAI` - 14 edges
7. `What You Must Do When Invoked` - 12 edges
8. `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` - 12 edges
9. `MNQAIError` - 11 edges
10. `MNQ Phase 0 Rebuild And Cleanup Decision` - 11 edges

## Surprising Connections (you probably didn't know these)
- `MNQVolumeAI` --references--> `graphify`  [EXTRACTED]
  README.md → AGENTS.md
- `float` --uses--> `Phase1Config`  [INFERRED]
  tests/test_phase1_trade_extractor.py → src/mnq_ai/config.py
- `object` --uses--> `Phase1Config`  [INFERRED]
  tests/test_phase1_trade_extractor.py → src/mnq_ai/config.py
- `int` --uses--> `Phase1Config`  [INFERRED]
  tests/test_phase1_trade_extractor.py → src/mnq_ai/config.py
- `Path` --uses--> `Phase1Config`  [INFERRED]
  tests/test_phase1_trade_extractor.py → src/mnq_ai/config.py

## Import Cycles
- None detected.

## Communities (62 total, 29 thin omitted)

### Community 0 - "Skill Validation and Parsing"
Cohesion: 0.05
Nodes (36): auction-feature-engineering Skill, dependency-governor Skill, execution-backtest-gate Skill, mbo-data-causality Skill, out-of-core-data-engineering Skill, quant-model-validation Skill, quant-research-scout Skill, Ablation Requirement (+28 more)

### Community 1 - "Skill and Algorithm Policies"
Cohesion: 0.11
Nodes (22): ArgumentParser, Exception, _config_from_args(), main(), _parser(), Command-line interface for MNQ Phase 1 jobs., Run the ``mnq-ai`` CLI., MNQAIError (+14 more)

### Community 2 - "MNQ Project Specifications"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 3 - "Limit Order Book Forecasting"
Cohesion: 0.08
Nodes (24): MNQ Volume Profile AI Master Plan, Current Architecture Inventory, Current Issues And Risks, Data Readiness Assessment, Deleted but required before implementation, Deleted or generated paths that should not block the rebuild, Dependency Graph, Exact Module Boundaries (+16 more)

### Community 4 - "LLM Agents for Trading"
Cohesion: 0.16
Nodes (16): Any, bool, _load_yaml_with_extends(), _parse_hms(), Configuration loading and validation for Phase 1 jobs., Return a validated copy with common CLI overrides., Fail closed on invalid configuration., Load a config file, following a single optional ``extends`` reference. (+8 more)

### Community 5 - "Hook Utilities"
Cohesion: 0.09
Nodes (20): MNQ Walk-Forward And Backtest Specification, Acceptance Criteria, Automated Leakage Tests, Execution Assumptions, Label Philosophy, Leakage Blacklist, Purging Metadata, Repeated Event Prevention (+12 more)

### Community 6 - "Reinforcement Learning Trading"
Cohesion: 0.09
Nodes (21): Comprehensive Research Report: Volume Profile Analysis in Financial Markets, 1. Concepts and Historical Origin of Volume-by-Price Studies, 2. Microeconomic Foundations and Continuous Auction Theory, 3. Mathematical Structure and Calculation of Volume Profile Levels, 4.1 Price Interaction with POC Levels on Poland's WIG20 Index, 4.2 Taiwan Market Profile Study and Weak-Form Market Efficiency, 4.3 Volume-Centred Range Bars (VCRB) for Machine Learning Pattern Extraction, 4.4 Fair Value Gaps and Linear Regression Slope of Liquidity (+13 more)

### Community 7 - "Decentralized Market Microstructure"
Cohesion: 0.09
Nodes (21): 1. Concepts and Historical Origin of Volume-by-Price Studies, 2. Microeconomic Foundations and Continuous Auction Theory, 3. Mathematical Structure and Calculation of Volume Profile Levels, 4.1 Price Interaction with POC Levels on Poland's WIG20 Index, 4.2 Taiwan Market Profile Study and Weak-Form Market Efficiency, 4.3 Volume-Centred Range Bars (VCRB) for Machine Learning Pattern Extraction, 4.4 Fair Value Gaps and Linear Regression Slope of Liquidity, 4. Major Academic Studies and Empirical Analyses (+13 more)

### Community 8 - "MNQVolumeAI Utility Scripts"
Cohesion: 0.30
Nodes (18): float, Phase1Config, Validated runtime configuration for MBO auditing and trade extraction., DataValidationError, Raised when raw rows violate fail-closed data-quality rules., object, _config(), int (+10 more)

### Community 9 - "MNQVolumeAI Test Utilities"
Cohesion: 0.12
Nodes (10): Engineering Rules, graphify, Mandatory Project Skills, Decisions, Rejected Or Deferred, Risk Notes, Phase 1 Dependency Decisions, Phase 1 Entry Gate (+2 more)

### Community 10 - "Survival Analysis in Order Books"
Cohesion: 0.31
Nodes (9): int, Path, load_skill(), main(), parse_front_matter(), SkillDoc, validate(), str (+1 more)

### Community 11 - "Price Prediction with Deep Learning"
Cohesion: 0.15
Nodes (12): Acceptance Criteria, Checks, Chunking Strategy, MBO Trade Semantics, Objectives, Price and size checks, Required Audit Outputs, Session checks (+4 more)

### Community 12 - "LSTM Trend Forecasting"
Cohesion: 0.20
Nodes (9): MNQ Phase 1 Implementation Tasks, P1-001 Restore Active Safety Skeleton, P1-002 MBO Action-T Trade Extractor, P1-003 CME Session Calendar, P1-004 Bar Builder From Trades, P1-005 Wire Feature Families With Session IDs, P1-006 Feature Blacklist And Schema, P1-007 Data Audit CLI (+1 more)

### Community 13 - "Natural Language to Option Strategies"
Cohesion: 0.20
Nodes (9): MNQ Deterministic Setup Engine Specification, Acceptance Criteria, Candidate Setups, Core Principle, Deduplication Rules, Online State Requirements, Reason Codes, Setup Candidate Schema (+1 more)

### Community 14 - "Reinforcement Learning for Trading"
Cohesion: 0.22
Nodes (7): MNQ Phase 0 Rebuild And Cleanup Decision, Current Finding, Exact Next Patch After Approval, Files Not To Edit In The First Implementation Patch, Recommended Decision, Stop/Go, Current Stop/Go

### Community 15 - "LLM Debiasing Techniques"
Cohesion: 0.22
Nodes (8): Acceptance Criteria, Artifact Contract, Calibration, Class Imbalance, Decision Thresholds, Feature Inputs, Initial Model Set, Model Role

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
Cohesion: 0.33
Nodes (6): `auction_rejection_features`, `cvd_delta_features`, Feature Family Contracts, `intraday_context_features`, `volume_profile_features`, `vwap_features`

### Community 22 - "StockSharp GitHub Repository"
Cohesion: 0.33
Nodes (5): Allowed Feature Families, Feature Sidecar, Forbidden Directional Inputs, Global Rules, Leakage Tests Required

### Community 23 - "TradeMaster GitHub Repository"
Cohesion: 0.33
Nodes (5): Contradicted Claims, Current Registry, Independently Verified Claims, Rejected Claims, Status Definitions

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

## Knowledge Gaps
- **252 isolated node(s):** `PreToolUse`, `str`, `Trigger`, `Do Not Trigger`, `Required Workflow` (+247 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MNQ Volume Profile AI Master Plan` connect `Limit Order Book Forecasting` to `Price Prediction with Deep Learning`, `TradeMaster GitHub Repository`, `Reinforcement Learning for Trading`, `Reinforcement Learning Trading`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` connect `Reinforcement Learning Trading` to `Limit Order Book Forecasting`, `Hook Utilities`, `Reinforcement Learning for Trading`, `StockSharp GitHub Repository`, `TradeMaster GitHub Repository`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `MNQ Walk-Forward And Backtest Specification` connect `Hook Utilities` to `TradeMaster GitHub Repository`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Phase1Config` (e.g. with `ArgumentParser` and `float`) actually correct?**
  _`Phase1Config` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Comprehensive Research Report: Volume Profile Analysis in Financial Markets` (e.g. with `MNQ Volume Profile AI Master Plan` and `mnq_labeling_and_leakage_spec.md`) actually correct?**
  _`Comprehensive Research Report: Volume Profile Analysis in Financial Markets` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ConfigurationError` (e.g. with `Any` and `bool`) actually correct?**
  _`ConfigurationError` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PreToolUse`, `Utility scripts for MNQVolumeAI.`, `MNQ Phase 1 data-foundation package.` to the rest of the system?**
  _272 weakly-connected nodes found - possible documentation gaps or missing edges._