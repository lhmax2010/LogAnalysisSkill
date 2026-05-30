# Memory for build skill broken-root clean retry

## Status

Completed; waiting for review.

## Scope

Add one automatic `--clean` retry in `tizen-gbs-build` when the first `gbs build`
fails after reporting a broken build root.

Strictly out of scope: workflow changes, analyzer changes, pattern changes,
BuildResult/BuildOptions field changes, feeding interactive stdin, and repeated
retries.

## Baseline

- Branch: `feature/build-skill-broken-root-clean-retry`
- Starting commit: `31d909f` (`Merge pull request #33`)
- Source: user request after real Cline/build usage exposed broken-root prompts.

## Progress

- Created dev_memory scaffold.
- Added a `BROKEN_BUILD_ROOT_MARKER` check for the fixed GBS/OBS phrase
  `Your build system is broken`.
- Extended `build_command` with an opt-in `clean=True` flag that appends
  `--clean` at the end of the existing GBS command.
- Extracted a single-run helper that preserves v0.2 streaming, timeout, and
  missing-command behavior while adding `stdin=subprocess.DEVNULL`.
- Updated `run_gbs_build` to retry exactly once with `--clean` only after a
  non-timeout failed run whose compiler log contains the broken-root marker.
- Kept `BuildResult` and `BuildOptions` fields unchanged; `BuildResult.command`
  records the final command that produced the returned result.
- Added focused unit coverage for marker detection, clean command construction,
  stdin EOF behavior, retry success, retry failure, no retry for ordinary
  failures, and no retry after timeout.

## Validation Summary

- Focused build runner tests: `24 passed`.
- Full regression with coverage: `417 passed`, coverage `96.01%`.
- Ruff: `ruff check .` passed.
- Mypy: `mypy tizen-gbs-build/scripts/gbs_build_skill` passed.
- Real broken-root reproduction: not available in this run; behavior is covered
  with fake GBS scripts that exercise the subprocess path.
