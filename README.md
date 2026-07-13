# MNQVolumeAI

Greenfield MNQ data foundation for an eventual Volume Profile / auction AI trading-system build.

Current status: **Phase 1 data foundation, deterministic Failed FVG and QEP technical setup-candidate generation, and Phase 2 execution-gate labeling implemented**.

The implemented pipeline provides Databento MBO audit, canonical trade-tape extraction, server-runnable setup candidate builders, and a deterministic first-barrier execution-label gate:

- `action == "T"` is the sole executed-trade volume source.
- `action == "F"` is audited but never included in canonical trade volume.
- signed volume is `+size` for `side == "B"`, `-size` for `side == "A"`, and `0` with `unknown_aggressor=true` for `side == "N"`.
- timestamps remain UTC internally; CME trading dates and RTH flags are derived with `America/Chicago`.
- output is partitioned Parquet by `symbol` and `trading_date`.
- Failed FVG setup candidates are built from causal OHLCV bars derived from the canonical trade tape.
- QEP technical setup candidates translate the executable RSI/MACD/ATR core of the supplied MT5 EA into causal Python; placeholder RL, Elliott Wave, harmonic-pattern, and crypto modules are not implemented.
- Phase 2 labels candidates by the first executed trade that reaches stop or target after the candidate entry timestamp.
- Phase 2 applies configurable commission, entry slippage, stop slippage, max-hold exit slippage, and entry latency assumptions.
- no Volume Profile features, VWAP/CVD feature families beyond signed trade volume, model training, calibrated probabilities, backtesting, or live trading are implemented.

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

~/.local/bin/uv run mnq-ai build-qep-technical-candidates \
  --trade-tape data/trade_tape \
  --config configs/mnq.yaml \
  --output data/qep_technical_candidates \
  --artifacts artifacts/qep_technical_candidates \
  --overwrite

~/.local/bin/uv run mnq-ai build-phase2-labels \
  --trade-tape data/trade_tape \
  --setup-candidates data/setup_candidates/setup_candidates.parquet \
  --config configs/mnq.yaml \
  --output data/phase2_labels \
  --artifacts artifacts/phase2_gate \
  --commission-per-side 0.35 \
  --entry-slippage-ticks 1 \
  --stop-slippage-ticks 1 \
  --time-exit-slippage-ticks 1 \
  --point-value 2 \
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

Then build Phase 2 execution labels and the fail-closed gate artifacts:

```powershell
$env:PYTHONUTF8="1"; uv run mnq-ai build-phase2-labels --trade-tape data\trade_tape_phase1_5days --setup-candidates data\setup_candidates_5days\setup_candidates.parquet --config configs\mnq.yaml --output data\phase2_labels_5days --artifacts artifacts\phase2_gate_5days --commission-per-side 0.35 --entry-slippage-ticks 1 --stop-slippage-ticks 1 --time-exit-slippage-ticks 1 --point-value 2 --overwrite
```

Expected outputs:

- `data\phase2_labels_5days\setup_labels.parquet`
- `artifacts\phase2_gate_5days\phase2_gate_manifest.json`
- `artifacts\phase2_gate_5days\phase2_gate_summary.md`

The Phase 2 manifest intentionally reports `gate_recommendation: NO-GO`. This is correct for the current five-day engineering fixture because it has not passed walk-forward validation, paper-trading parity, doubled-cost stress, or production release checks.

### QEP Technical Five-Day Fixture

Build deterministic QEP technical candidates from the same five-day trade tape:

```powershell
$env:PYTHONUTF8="1"; uv run mnq-ai build-qep-technical-candidates --trade-tape data\trade_tape_phase1_5days --config configs\mnq.yaml --output data\qep_technical_candidates_5days --artifacts artifacts\qep_technical_candidates_5days --rsi-period 14 --macd-fast 12 --macd-slow 26 --macd-signal 9 --atr-window 14 --atr-stop-mult 2 --take-profit-r "1.5,3,4.5" --max-holding-bars 12 --overwrite
```

Expected outputs:

- `data\qep_technical_candidates_5days\setup_candidates.parquet`
- `artifacts\qep_technical_candidates_5days\qep_technical_manifest.json`
- `artifacts\qep_technical_candidates_5days\qep_technical_summary.md`

Then label the QEP candidates through the same Phase 2 execution gate:

```powershell
$env:PYTHONUTF8="1"; uv run mnq-ai build-phase2-labels --trade-tape data\trade_tape_phase1_5days --setup-candidates data\qep_technical_candidates_5days\setup_candidates.parquet --config configs\mnq.yaml --output data\qep_phase2_labels_5days --artifacts artifacts\qep_phase2_gate_5days --commission-per-side 0.35 --entry-slippage-ticks 1 --stop-slippage-ticks 1 --time-exit-slippage-ticks 1 --point-value 2 --overwrite
```

This is a research translation of the EA's RSI/MACD/ATR decision core only. It does not use the EA's placeholder RL, synthetic confidence, sentiment, Elliott Wave, harmonic-pattern, or crypto-volatility modules.

Generate a QEP failure-mode diagnostic report from the Phase 2 labels:

```powershell
uv run python scripts\qep_failure_report.py --labels data\qep_phase2_labels_5days\setup_labels.parquet --output artifacts\qep_phase2_gate_5days\qep_failure_report.md --m30-bar-count 226 --print
```

The report summarizes hit rate, net R, exit reasons, side counts, candidate density, and dominant failure modes such as overtrading, weak target conversion, and MAX_HOLD-heavy exits.

## Diagnostic Failed FVG Chart

`scripts\Fail FVG.py` is a standalone diagnostic runner. It is not the official Phase 2 gate, but it can draw each simulated trade on M30 candles with entry, exit, FVG zone, PnL, and gross points.

```powershell
uv run python "scripts\Fail FVG.py" "C:\Users\Administrator\PycharmProjects\MNQVolumeAI\data\trade_tape\MNQ_clean_20260406_20260410.parquet" --output-dir artifacts\fail_fvg_mnq_clean_5days --chart-output artifacts\fail_fvg_mnq_clean_5days\fail_fvg_trades_chart.html --point-value 2 --cost 2.50 --slip 2.50 --market-tz America/New_York --log-level INFO
```

By default, this runner adapts its diagnostic parameters by prior-day volatility regime. The current day's parameters are selected from the previous completed day's range versus the trailing median range, avoiding same-day high/low lookahead. Use `--disable-volatility-regimes` to force the original static parameters.

Expected outputs:

- `artifacts\fail_fvg_mnq_clean_5days\fail_fvg_trades.csv`
- `artifacts\fail_fvg_mnq_clean_5days\fail_fvg_summary.csv`
- `artifacts\fail_fvg_mnq_clean_5days\fail_fvg_trades_chart.html`
