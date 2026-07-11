# MNQVolumeAI

Greenfield project shell for an MNQ Volume Profile AI research and trading-system build.

Current status: **Phase 0.5 bootstrap only**.

This repository intentionally contains no trading implementation modules yet. Phase 0.5 establishes:

- project-scoped Codex and Graphify instructions;
- a structured research/planning corpus;
- repository-scoped Codex Skills for dependency governance, research review, causality, feature design, validation, large-data engineering, and execution gates;
- strict Graphify exclusions for raw market data and generated artifacts.

## Boundaries

The legacy project at `/Users/abdallah/Desktop/Trading/QuantSystemFinal` is not a runtime dependency. Do not import, copy, or restore legacy Python code, tests, configs, models, datasets, or artifacts into this repository.

Only inspected non-code research and planning documents may be copied into `docs/research/papers/original/`.

## Python Policy

Use `uv` for package management. The project targets Python 3.12 and starts with no runtime dependencies. Developer tools such as Graphify are installed as isolated `uv tool` environments, not as project dependencies.

## Phase 1 Gate

Do not begin Phase 1 data processing until [docs/phases/phase1_entry_gate.md](docs/phases/phase1_entry_gate.md) is GO.
