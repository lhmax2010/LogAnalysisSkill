---
name: tizen-gerrit-submit
description: Validate a previously verified Tizen worktree, generate a dry-run Gerrit push command, or release its protection marker. Use only for the final Gerrit submission safety gate; do not use it for source fetch, repair, build verification, or executing a push.
compatibility: Requires Python 3.10 or newer, git, a campaign state database, and access to the configured Gerrit host for remote-head checks.
---

# Tizen Gerrit Submit

Use this skill only after build verification has produced a ready record. It
checks that the protected worktree still matches that record and returns the
command a human or later service may run. This skill performs validation and
dry-run command generation only; it never executes `git push`.

## Inputs

- `GerritSubmitOptions` with the verification id, state database, Gerrit
  connection fields, submit target, submit mode, and optional SSH command.
- An optional subprocess runner used for local git validation and the Gerrit
  `ls-remote` check.
- `gerrit_submit` accepts keyword-only `timeout: float | None = None`, passed
  to every local git validation call and the `ls-remote` call. `None` imposes no
  subprocess timeout; a value applies per call, not to the whole operation.
- `release_verified_worktree` accepts the state database and verification id
  for the separate marker-release operation.

Local `_run_git` timeouts raise `GerritSubmitError("GIT_TIMEOUT", str(exc))`;
an `ls-remote` timeout becomes the fixed `target_head_unknown:timeout` warning.
For comparison, `tizen-gerrit-fetch` raises `GerritError("FETCH_TIMEOUT", str(exc))`,
while `tizen-build-verify` treats its build wall timeout as a result state.

## Outputs

`gerrit_submit` returns `GerritSubmitResult`. A valid request produces either
`dry_run` or `dry_run_unverified_remote` with `command_argv`; rejected,
duplicate, and missing-record paths return their documented action without
executing the command. `write_gerrit_submit_result` serializes that result.

`release_verified_worktree` returns `ReleaseWorktreeResult`, and
`write_release_result` serializes it. The exit-code helpers map result actions
for CLI consumers.

## Errors

- Missing, stale, dirty, mismatched, or submit-enabled requests are represented
  by explicit result actions rather than a push attempt.
- Gerrit remote-state failures become `target_head_unknown` warnings and
  `dry_run_unverified_remote`; the generated command remains present but the
  remote drift and duplicate assumptions are unverified.
- Local git `CalledProcessError` is converted only where the implementation
  explicitly returns a mismatch reason. Local git `TimeoutExpired` is wrapped
  as `GerritSubmitError` (defined in `tizen_gerrit_submit.gerrit_submit`), with
  code `GIT_TIMEOUT`, the exact original message, and the original exception as
  its cause. Other runner, filesystem, and JSON write exceptions retain their
  existing propagation behavior.
- An `ls-remote` timeout yields `dry_run_unverified_remote` with warning
  `target_head_unknown:timeout`, not a raised `GerritSubmitError`.
- SIGINT and SIGTERM are not caught or normalized; no automatic rollback or
  cleanup is performed on timeout or interruption.

## Side Effects

Submission validation reads the state database, executes read-only local git
commands and optionally `git ls-remote`, and constructs a push argv without
running it. Result-writer functions create parent directories and write JSON.
The release operation removes the protection marker from the recorded
worktree; it does not delete the worktree.

## Idempotency

Dry-run validation is repeatable for fixed state, worktree, and remote HEAD,
but its result can change when any of them changes. It does not register or
push a Gerrit change. Marker release is idempotent at the result level: the
first successful call reports `released`, while later calls report
`not_protected`.
