# MNQ Phase 1 Implementation Tasks

Scope: atomic implementation tasks after Phase 0 review. Do not execute these
until approved.

## P1-001 Restore Active Safety Skeleton

Description: restore or recreate active schema, validation, diagnostics, and
tests needed to prevent leakage while rebuilding.

Files affected:

```text
modules/dataset_schema.py
modules/session_features.py
modules/purging_embargo.py
modules/replay_engine/
tools/check_subsystem_boundaries.py
tools/diagnostics/
tests/
validation/
```

Prerequisites: user approves restore-vs-recreate policy.

Acceptance criteria: boundary check and minimal pytest discovery run.

Tests:

```bash
python tools/check_subsystem_boundaries.py
python -m pytest tests/test_subsystem_boundaries.py -q
```

Leakage risks: restoring old code can re-enable depth-direction paths.

Expected artifact: active safety scaffold with tests.

## P1-002 MBO Action-T Trade Extractor

Description: create chunked extractor for executed trades only.

Files affected:

```text
tools/mnq_extract_trades.py
tests/test_mnq_mbo_trade_extraction.py
```

Prerequisites: data audit column sample available.

Acceptance criteria: `T` volume only; `F` not double-counted; `N` signed volume
equals zero.

Tests:

```bash
python -m pytest tests/test_mnq_mbo_trade_extraction.py -q
```

Leakage risks: none direct, but incorrect volume source corrupts all features.

Expected artifact: partitioned trades parquet plus manifest.

## P1-003 CME Session Calendar

Description: derive CME session IDs and partial-session flags.

Files affected:

```text
modules/session_features.py
tests/test_mnq_cme_sessions.py
```

Prerequisites: timestamp parsing pass.

Acceptance criteria: no UTC-date grouping in production feature builders.

Tests:

```bash
python -m pytest tests/test_mnq_cme_sessions.py -q
```

Leakage risks: wrong session close can leak prior/current session levels.

Expected artifact: session calendar helper and session coverage report.

## P1-004 Bar Builder From Trades

Description: build OHLCV, buy/sell volume, signed delta, and trade count from
extracted trades.

Files affected:

```text
tools/mnq_build_bars.py
tests/test_mnq_bar_builder.py
```

Prerequisites: P1-002 and P1-003.

Acceptance criteria: bars reconcile to trade volume and signed volume.

Tests:

```bash
python -m pytest tests/test_mnq_bar_builder.py -q
```

Leakage risks: sorting and duplicate handling.

Expected artifact: partitioned bars parquet.

## P1-005 Wire Feature Families With Session IDs

Description: require `cme_session_id` for Volume Profile, VWAP, CVD, and
intraday context in production mode.

Files affected:

```text
features/volume_profile_features.py
features/vwap_features.py
features/cvd_delta_features.py
features/intraday_context_features.py
volume_profile/session_profile.py
tests/test_mnq_feature_causality.py
```

Prerequisites: P1-003 and P1-004.

Acceptance criteria: truncation tests pass and no UTC-date fallback in strict
mode.

Tests:

```bash
python -m pytest tests/test_mnq_feature_causality.py -q
```

Leakage risks: full-session profile/VWAP, rolling windows, future session highs.

Expected artifact: feature parquet and feature sidecar.

## P1-006 Feature Blacklist And Schema

Description: update dataset schema to include MNQ setup targets and forbidden
feature patterns.

Files affected:

```text
modules/dataset_schema.py
tests/test_mnq_feature_blacklist.py
```

Prerequisites: P1-001.

Acceptance criteria: feature matrix builder fails closed on label/outcome/depth
direction columns.

Tests:

```bash
python -m pytest tests/test_mnq_feature_blacklist.py -q
```

Leakage risks: target columns entering model.

Expected artifact: schema sidecar.

## P1-007 Data Audit CLI

Description: create audit CLI for the five-day engineering fixture.

Files affected:

```text
tools/mnq_audit_mbo.py
tests/test_mnq_data_audit.py
```

Prerequisites: P1-002 and P1-003.

Acceptance criteria: action/side/session/invalid-row reports generated.

Tests:

```bash
python -m pytest tests/test_mnq_data_audit.py -q
```

Leakage risks: none direct.

Expected artifact: `data_audit_summary.json`.

## P1-008 Cleanup Policy Patch

Description: after approval, update `.gitignore` and keep generated/archive
folders out of the active tree.

Files affected:

```text
.gitignore
docs/project_cleanup_candidates.md or successor
```

Prerequisites: user approval.

Acceptance criteria: active files restored; generated duplicates ignored; no
active source accidentally deleted.

Tests:

```bash
git status --short
python -m pytest tests/test_subsystem_boundaries.py -q
```

Leakage risks: deleting tests or schema would increase leakage risk.

Expected artifact: reviewed cleanup manifest.

