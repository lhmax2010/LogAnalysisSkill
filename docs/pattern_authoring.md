# Pattern Authoring Guide

Pattern authoring follows `docs/DESIGN.md` v0.5, especially §3.2, §3.5, and §4.

## Rules

- Tier1 patterns are limited to the central allowlist:
  `depsolve_failure`, `patch_failed`, `linker_missing_lib`, and `install_file_missing`.
- Tier1 fix templates must be conservative and use uncertain language such as
  "may", "usually", or "check".
- Tier1 fix templates are limited to 300 characters, except `patch_failed` templates,
  which are limited to 150 characters.
- `undefined_reference`, `compile_error`, `werror_triggered`, `rpm_phase_failure`, and
  `spec_script_error` must not become tier1 patterns.
- Required context should include phase, severity, tool, negative patterns, and warning
  block exclusions when applicable.

## Lifecycle

1. Add a fixture that demonstrates the pattern.
2. Add the pattern to `patterns/gbs_errors.yaml`.
3. Add or update pattern-library tests.
4. Record the decision in the active milestone dev_memory.

The actual pattern schema and pattern tests are introduced in later milestones.
