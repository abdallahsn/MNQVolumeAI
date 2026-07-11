# Dependency Policy

Verification date: 2026-07-11

Before selecting, adding, removing, upgrading, or pinning a dependency, invoke `$dependency-governor`.

Every dependency decision must verify official sources first:

- official documentation;
- official package index metadata;
- official release notes or repository tags;
- supported Python versions;
- license and security posture;
- compatibility with the locked dependency graph.

Use `uv` for project dependencies, regenerate `uv.lock`, and run the relevant tests after dependency changes. Do not perform unreviewed bulk upgrades, unbounded dependency additions, or popularity-based selections.

Record every dependency decision under `docs/dependencies/` with package, purpose, previous version, latest stable version, selected version, release date, sources checked, Python compatibility, transitive risk, breaking changes, license, security notes, alternatives, benchmark requirement, final decision, and verification date.

“Latest” is not an acceptance criterion.

“Stable, compatible, causal, reproducible, and empirically superior” is the acceptance criterion.
