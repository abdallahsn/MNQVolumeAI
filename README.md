# MNQVolumeAI

Greenfield MNQ data foundation for an eventual Volume Profile / auction AI trading-system build.

Current status: **Phase 1 data foundation implemented**.

Phase 1 implements only Databento MBO audit and canonical trade-tape extraction:

- `action == "T"` is the sole executed-trade volume source.
- `action == "F"` is audited but never included in canonical trade volume.
- signed volume is `+size` for `side == "B"`, `-size` for `side == "A"`, and `0` with `unknown_aggressor=true` for `side == "N"`.
- timestamps remain UTC internally; CME trading dates and RTH flags are derived with `America/Chicago`.
- output is partitioned Parquet by `symbol` and `trading_date`.
- no bars, Volume Profile features, CVD families beyond signed trade volume, labels, model training, backtesting, or live trading are implemented.

## Boundaries

The legacy project at `/Users/abdallah/Desktop/Trading/QuantSystemFinal` is not a runtime dependency. Do not import, copy, or restore legacy Python code, tests, configs, models, datasets, or artifacts into this repository.

Only inspected non-code research and planning documents may be copied into `docs/research/papers/original/`.

## Python Policy

Use `uv` for package management. The project targets Python `>=3.12,<3.13`.

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
```

Run schema-only and bounded smoke tests before attempting the full 179M-row fixture.
