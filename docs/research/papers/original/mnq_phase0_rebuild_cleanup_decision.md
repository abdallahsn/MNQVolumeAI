# MNQ Phase 0 Rebuild And Cleanup Decision

This file maps the current deleted working tree to a safe rebuild decision.

## Current Finding

The deletion is too broad to accept as "unused file cleanup". Deleted active
paths include:

```text
modules/
tests/
tools/
docs/
self_supervised/
setups/
labeling/
validation/
backtesting/
scripts/
```

Some deleted paths are likely safe/generated/archive:

```text
_archive/
graphify-code-scope/
graphify-scope/
most graphify-out/cache/
```

## Recommended Decision

1. Do not restore `_archive/`, `graphify-code-scope/`, or `graphify-scope` into
   the active tree unless explicitly needed.
2. Restore or recreate active safety files before any production code edit.
3. Keep the new `features/` and `volume_profile/` work, but harden sessions and
   leakage tests.
4. Treat DeepLOB/SSL as deferred/experimental for the MNQ baseline because the
   attached project objective says no deep learning initial baseline and no
   depth-derived direction.
5. Use the five-day MNQM6 file as engineering fixture only.

## Exact Next Patch After Approval

Recommended first implementation patch:

```text
restore/recreate:
  modules/dataset_schema.py
  modules/session_features.py
  modules/purging_embargo.py
  tools/check_subsystem_boundaries.py
  validation/
  tests/test_mnq_*.py

create:
  tools/mnq_extract_trades.py
  tools/mnq_audit_mbo.py
  tools/mnq_build_bars.py

edit:
  features/* to require cme_session_id in strict mode
  volume_profile/session_profile.py to avoid UTC-date fallback in strict mode
```

## Files Not To Edit In The First Implementation Patch

```text
production trading runner
live inference
DeepLOB/SSL training
hybrid fusion model
archive folders
research corpus
```

## Stop/Go

Stop on deleting more active files.

Go on Phase 1 only after approving the cleanup/restore split above.

