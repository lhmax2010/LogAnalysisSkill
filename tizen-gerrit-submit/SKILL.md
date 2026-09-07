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
- `release_verified_worktree` accepts the state database and verification id
  for the separate marker-release operation.

No subprocess timeout is currently supplied. Local `_run_git` calls propagate
`subprocess.TimeoutExpired`; an `ls-remote` timeout is caught and converted to
a `target_head_unknown:<exception>` warning. This differs from
`tizen-gerrit-fetch`, which propagates subprocess timeouts, and
`tizen-build-verify`, which treats its build wall timeout as a result state.

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
  explicitly returns a mismatch reason. Other runner, filesystem, and JSON
  write exceptions propagate unchanged.
- External interruption is not caught or normalized.

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
