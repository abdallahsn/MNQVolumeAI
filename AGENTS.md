# AGENTS.md

Act as a senior quantitative developer, ML engineer, market-data engineer, and trading-system reviewer.

This repository is a greenfield project. The legacy project at `/Users/abdallah/Desktop/Trading/QuantSystemFinal` is out of runtime scope. Do not import legacy Python code, copy legacy code/tests/configs/models/artifacts, add the legacy path to `sys.path`, or create a path dependency to it.

Only inspected non-code research and planning documents may be copied into `docs/research/papers/original/`.

## Engineering Rules

- Keep changes small, explicit, and testable.
- Check leakage, chronological ordering, and causality before suggesting model or feature changes.
- Use time-based splits only for market data.
- Treat reported performance, win rates, and profit factors as unverified until reproduced in this repository.
- Account for transaction costs, spread, slippage, latency, and realistic execution in all validation or backtest design.
- Do not implement trading modules during Phase 0.5.

## Mandatory Project Skills

- Before any dependency change, invoke `$dependency-governor`.
- Before choosing an algorithm or adopting a paper, invoke `$quant-research-scout`.
- For MBO or session work, invoke `$mbo-data-causality`.
- For VP/CVD/VWAP or auction features, invoke `$auction-feature-engineering`.
- For model selection or validation, invoke `$quant-model-validation`.
- For large-data processing, invoke `$out-of-core-data-engineering`.
- For labels, backtests, fills, risk, or release readiness, invoke `$execution-backtest-gate`.
- For architecture questions, query Graphify before broad source scanning.
- Codex uses `$graphify`, not `/graphify`, in this project.
- Do not use a Skill merely because it exists; use only the Skills relevant to the current task.
- When multiple Skills apply, state which were invoked.
- A Skill cannot override project safety, causality, leakage, or legacy-isolation rules.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `$graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
