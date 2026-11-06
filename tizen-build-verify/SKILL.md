---
name: tizen-build-verify
description: Apply a bounded edit specification to a disposable Tizen source copy, run GBS verification, and persist a verified result. Use only for the build-verification safety gate; do not use it for failure discovery, patch ideation, Gerrit source fetch, convergence decisions, or submission.
compatibility: Requires Python 3.10 or newer, git, GBS, analyzer and formatter package roots, and a configured Tizen GBS profile.
---

# Tizen Build Verify

Use this skill after a candidate edit specification has been reviewed and the
workflow must prove the exact source change against a clean disposable copy.
The package root exposes only the nine symbols documented by `__all__`.

## Inputs

- `BuildVerifyOptions` with the clean source, exact base commit, edit-spec
  path, GBS configuration, package, raw architecture name, workspace root,
  baseline evidence, output location, iteration, wall timeout, state database,
  and build provenance.
- An optional subprocess runner. The wall timeout is passed to the GBS build;
  unlike `tizen-gerrit-fetch`, timeout is part of this skill's contract and is
  converted to the `build_timeout` failure stage.
- `validate_edit_spec` may be used independently to validate the bounded edit
  document against a source root before verification.

## Outputs

`build_verify` returns `BuildVerifyResult`. A successful result is `PASS` and
contains the actual changed paths, verification id, verified commit and tree,
and disposable copy path. Failures contain a stable stage, classification,
repair decision, and any evidence or log path produced before that stage.

`build_verify_to_json` serializes the result for CLI consumers.
`create_worktree` and `check_disk_and_maybe_cleanup` are public workspace
primitives used by the verification flow.

## Errors

- Invalid or unappliable edits return `apply_failed`; effective-path and
  whitespace checks return their documented failure stages before GBS runs.
- A GBS timeout or tracked-source mutation returns `REPAIR_DENIED`.
- A normal GBS failure is analyzed and classified as `gbs_build_failed`.
- Analyzer nonzero exit or missing evidence leaves evidence unavailable; the
  build result remains a failure rather than being promoted to PASS.
- Marker and state-database write exceptions propagate unchanged. They are not
  converted into a successful or repairable result.

## Side Effects

The skill creates and cleans disposable repository copies, applies the edit,
creates a verification commit, invokes `git`, `cp -a`, `gbs`, the formatter,
and `python -m gbs_analyzer`, writes logs/evidence, marks a passing copy as
protected, and appends the PASS record. Import-linter cannot see subprocess
dependencies; the campaign subprocess-boundary ledger records them explicitly.

## Idempotency

The operation is deterministic for fixed repository content, edit spec,
environment, toolchain, and external repositories, but it is not side-effect
free. Each iteration owns a distinct disposable directory and state record.
Callers must not reuse an iteration path for unrelated inputs or bypass the
verification id when consuming a PASS.
