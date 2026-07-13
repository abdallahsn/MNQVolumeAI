# MNQVolumeAI

Greenfield MNQ data foundation for an eventual Volume Profile / auction AI trading-system build.

Current status: **Phase 1 data foundation and deterministic Failed FVG setup-candidate generation implemented**.

Phase 1 implements Databento MBO audit, canonical trade-tape extraction, and a server-runnable Failed FVG candidate builder:

- `action == "T"` is the sole executed-trade volume source.
- `action == "F"` is audited but never included in canonical trade volume.
- signed volume is `+size` for `side == "B"`, `-size` for `side == "A"`, and `0` with `unknown_aggressor=true` for `side == "N"`.
- timestamps remain UTC internally; CME trading dates and RTH flags are derived with `America/Chicago`.
- output is partitioned Parquet by `symbol` and `trading_date`.
- Failed FVG setup candidates are built from causal OHLCV bars derived from the canonical trade tape.
- no Volume Profile features, VWAP/CVD feature families beyond signed trade volume, labels, model training, backtesting, or live trading are implemented.

## Boundaries

The legacy project at `/Users/abdallah/Desktop/Trading/QuantSystemFinal` is not a runtime dependency. Do not import, copy, or restore legacy Python code, tests, configs, models, datasets, or artifacts into this repository.

Only inspected non-code research and planning documents may be copied into `docs/research/papers/original/`.

## Python Policy

Use `uv` for package management. The project targets Python `>=3.12,<3.13`.

On Windows Server, run through `uv sync` before tests or CLI jobs. The project
depends on `tzdata` so Python `zoneinfo` can resolve `America/Chicago` on hosts
that do not ship an IANA timezone database.

PowerShell setup:

```powershell
$env:PYTHONUTF8="1"
py -3.12 -m uv sync
py -3.12 -m uv run pytest
```

If `py -3.12` is not available:

```powershell
uv python install 3.12
uv sync --python 3.12
uv run pytest
```

## CLI

```bash
~/.local/bin/uv run mnq-ai audit-mbo \
  --input <INPUT_PARQUET_OR_DATASET> \
  --config configs/mnq.yaml \
  --output artifacts/phase1

~/.local/bin/uv run mnq-ai build-trade-tape \
  --input <INPUT_PARQUET_OR_DATASET> \
  --config configs/mnq.yaml \
  --output data/trade_tape \
  --artifacts artifacts/phase1 \
  --overwrite

~/.local/bin/uv run mnq-ai validate-trade-tape \
  --input data/trade_tape \
  --manifest artifacts/phase1/phase1_manifest.json

~/.local/bin/uv run mnq-ai build-failed-fvg-candidates \
  --trade-tape data/trade_tape \
  --config configs/mnq.yaml \
  --output data/setup_candidates \
  --artifacts artifacts/setup_candidates \
  --overwrite
```

Run schema-only and bounded smoke tests before attempting the full 179M-row fixture.

## Windows Five-Day Fixture

After validating `data\trade_tape_phase1_5days`, build deterministic Failed FVG candidates with:

```powershell
$env:PYTHONUTF8="1"; uv run mnq-ai build-failed-fvg-candidates --trade-tape data\trade_tape_phase1_5days --config configs\mnq.yaml --output data\setup_candidates_5days --artifacts artifacts\setup_candidates_5days --overwrite
```

Expected outputs:

- `data\setup_candidates_5days\setup_candidates.parquet`
- `artifacts\setup_candidates_5days\failed_fvg_manifest.json`
- `artifacts\setup_candidates_5days\failed_fvg_summary.md`

This command is still Phase 1 research plumbing. It produces deterministic setup candidates only; it does not validate edge, train a model, calibrate probabilities, or run a backtest.
