# Phase 1 Performance Plan

The full input is approximately 179M MBO rows. Do not process it first.

Recommended sequence:

1. Schema audit only:

```bash
~/.local/bin/uv run mnq-ai audit-mbo \
  --input <INPUT_PARQUET_OR_DATASET> \
  --config configs/mnq.yaml \
  --output artifacts/phase1_schema_smoke
```

2. Small row-group or copied-file smoke test:

```bash
~/.local/bin/uv run mnq-ai build-trade-tape \
  --input <SMOKE_PARQUET> \
  --config configs/mnq.yaml \
  --output data/trade_tape_smoke \
  --artifacts artifacts/phase1_smoke \
  --overwrite
```

3. Medium subset benchmark:

```bash
/usr/bin/time -l ~/.local/bin/uv run mnq-ai build-trade-tape \
  --input <MEDIUM_PARQUET_OR_DATASET> \
  --config configs/mnq.yaml \
  --output data/trade_tape_medium \
  --artifacts artifacts/phase1_medium \
  --overwrite
```

4. Full extraction only after the previous commands pass:

```bash
/usr/bin/time -l ~/.local/bin/uv run mnq-ai build-trade-tape \
  --input <FULL_INPUT_PARQUET_OR_DATASET> \
  --config configs/mnq.yaml \
  --output data/trade_tape \
  --artifacts artifacts/phase1 \
  --overwrite
```

Record:

- elapsed time;
- rows per second;
- input bytes;
- output bytes;
- peak RSS;
- output file count;
- invalid/quarantined rows;
- ordering anomalies.
