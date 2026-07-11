---
name: dependency-governor
description: "Use before selecting, adding, removing, upgrading, or pinning Python dependencies or tools; do not run for ordinary code edits with no dependency impact."
---

# dependency-governor

## Trigger

Use this Skill before selecting, adding, removing, upgrading, pinning, or replacing any Python dependency, numerical library, ML framework, file format library, calendar library, or development tool.

## Do Not Trigger

Do not run this Skill for ordinary source edits, documentation edits, local file inspection, or conceptual explanations that do not change or select dependencies.

## Required Workflow

1. Check the current date and record the verification date.
2. Search official documentation, official package indexes, official release notes, and official repositories.
3. Identify the latest stable release and distinguish stable, release candidate, beta, alpha, nightly, yanked, and abandoned versions.
4. Inspect supported Python versions and platform constraints.
5. Inspect compatibility with the locked dependency graph.
6. Inspect breaking changes, deprecations, and migration notes.
7. Inspect relevant security advisories.
8. Inspect license compatibility.
9. Prefer the newest stable compatible version, not the numerically newest release.
10. Reject prereleases unless the user explicitly authorizes them.
11. Reject unmaintained packages when a maintained alternative exists.
12. Add dependencies through `uv`; never edit dependency lock state manually.
13. Regenerate and validate `uv.lock`.
14. Run relevant tests after dependency changes.
15. Never perform an unreviewed bulk upgrade.
16. Record a dependency decision document under `docs/dependencies/`.

## Decision Record

Every dependency decision must record:

- package;
- purpose;
- version before;
- latest stable version;
- selected version;
- release date;
- official sources checked;
- Python compatibility;
- transitive risk;
- breaking changes;
- license;
- security notes;
- alternatives considered;
- benchmark requirement;
- final decision;
- verification date.

## Acceptance Rule

A library must not be selected solely because it is popular or new.

“Latest” is not an acceptance criterion.

“Stable, compatible, causal, reproducible, and empirically superior” is the acceptance criterion.
