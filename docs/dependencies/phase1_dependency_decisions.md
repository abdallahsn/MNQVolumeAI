# Phase 1 Dependency Decisions

Verification date: 2026-07-11.

Official sources checked:

- PyPI project pages and JSON metadata for `pyarrow`, `PyYAML`, `pytest`, `ruff`, `mypy`, and `hatchling`.
- Existing repository dependency policy in `docs/dependencies/dependency_policy.md`.

## Decisions

| Package | Purpose | Latest stable observed | Selected | Python | License | Decision |
|---|---:|---:|---:|---|---|---|
| `pyarrow` | Parquet Dataset scanning/writing and Arrow compute | 25.0.0 | `>=25.0.0,<26.0.0` | `>=3.10` | Apache-2.0 | Accept. Required for out-of-core Parquet processing. |
| `PyYAML` | YAML config loading | 6.0.3 | `>=6.0.3,<7.0.0` | `>=3.8` | MIT | Accept. Small runtime dependency. |
| `tzdata` | IANA timezone fallback for Windows/Python `zoneinfo` | 2026.3 | `>=2026.3,<2027.0` | `>=2` | Apache-2.0 | Accept. Required so `ZoneInfo("America/Chicago")` works on Windows hosts without system IANA timezone data. |
| `pytest` | Unit/integration tests | 9.1.1 | `>=9.1.1,<10.0.0` | `>=3.10` | MIT | Accept as dev dependency. |
| `ruff` | Linting | 0.15.21 | `>=0.15.21,<0.16.0` | `>=3.7` | MIT | Accept as dev dependency. |
| `mypy` | Type checking | 2.2.0 | `>=2.2.0,<2.3.0` | `>=3.10` | MIT | Accept as dev dependency with overrides for untyped PyArrow/PyYAML. |
| `hatchling` | PEP 517 build backend for src-layout package | 1.31.0 | `>=1.31.0,<2.0.0` | `>=3.10` | MIT | Accept for packaging and CLI installation. |

## 2026-07-13 Update: `tzdata`

- Package: `tzdata`.
- Purpose: first-party IANA timezone database fallback for Python `zoneinfo`.
- Version before: not present.
- Latest stable version: 2026.3.
- Selected version: `>=2026.3,<2027.0`.
- Release date observed: 2026-07-10.
- Official sources checked: Python `zoneinfo` documentation, PyPI JSON metadata, and the official `python/tzdata` repository description.
- Python compatibility: `>=2`; compatible with this project's `>=3.12,<3.13` policy.
- Transitive risk: low; package supplies timezone data and adds no runtime code path beyond standard-library `zoneinfo` fallback.
- Breaking changes: none expected; timezone database changes reflect civil timezone updates.
- License: Apache-2.0.
- Security notes: no advisory was found in the checked official metadata; lockfile records the wheel and sdist hashes.
- Alternatives considered: relying on operating-system timezone data. Rejected for Windows Server because the test failure showed `America/Chicago` unavailable without `tzdata`.
- Benchmark requirement: none; this is a small data package used during timezone lookup.
- Final decision: accept as a runtime dependency to make CME sessionization portable across Windows, macOS, and Linux.
- Verification date: 2026-07-13.

## Rejected Or Deferred

- `polars`: deferred. Useful later for lazy transformations, but Phase 1 can be implemented with PyArrow only.
- `duckdb`: deferred. Useful for independent validation audits, but not required for current synthetic tests.
- `pydantic`: deferred. Dataclasses are sufficient for Phase 1 config validation.
- Spark, Ray, Dask, TensorFlow, PyTorch: rejected for Phase 1 scope.

## Risk Notes

`pyarrow` 25.0.0 was released shortly before this implementation. It is stable and compatible with Python 3.12, but the full 179M-row job should still begin with schema audit, a row-group smoke test, and a medium subset benchmark before full processing.
