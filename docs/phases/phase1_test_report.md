# Phase 1 Test Report

Verification commands:

```bash
~/.local/bin/uv run pytest -q
~/.local/bin/uv run ruff check .
~/.local/bin/uv run mypy src
```

Observed results:

- `pytest`: 11 passed.
- `ruff`: all checks passed.
- `mypy`: no issues found in 14 source files.
- CLI smoke: audit/build/validate passed on a tiny Parquet fixture in `/tmp/mnq_phase1_smoke`.

Covered invariants:

- schema/config validation;
- `T` extraction only;
- `F` rows are not double counted;
- signed-volume mapping for `B`, `A`, and `N`;
- invalid tick handling under fail policy;
- quarantine output under quarantine policy;
- deterministic manifest checksum across identical reruns;
- CME session assignment across a DST date;
- no source dependency on `QuantSystemFinal`.

Not run:

- real dataset schema audit;
- limited row-group smoke test on the 179M-row fixture;
- medium subset benchmark;
- full extraction.
