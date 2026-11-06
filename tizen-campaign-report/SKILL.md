---
name: tizen-campaign-report
description: Report campaign state and release recorded disposable-copy protection at terminal states or after explicit abandonment. Not for builds, pushing commits, triggering or accepting QuickBuild builds.
---

# Tizen Campaign Report

## Commands And Inputs

```bash
python -m tizen_campaign_report campaign-report --state-db /work/state.db --output /work/report.md
python -m tizen_campaign_report campaign-finish-unit --state-db /work/state.db --config /work/campaign.yaml --campaign-unit-key '<unit-key>'
python -m tizen_campaign_report campaign-release-worktrees --state-db /work/state.db --config /work/campaign.yaml --campaign-unit-key '<unit-key>' --confirmed-by '<operator>'
```

Use --abandon on campaign-release-worktrees only after the operator decides to
stop pursuing a nonterminal unit. It writes an irreversible abandonment barrier
under the sandbox and three repair locks, then reconciles recorded copies.
It does not cancel a running QuickBuild build or change the unit status.
Do not release a unit reserved for subsequent submission unless the operator
confirms it will no longer proceed to submission.

## Outputs

All commands output JSON. The report optionally writes equivalent Markdown;
it reads only the database, displays the latest request's parent build ID and
latest RESULT reference verbatim, and never opens the result file. An already
bound request without RESULT retains its parent ID and has an empty reference.
An abandonment barrier takes precedence in the copy-status column even after PASS.

finish-unit automatically releases six eligible terminal states; NOT_REPRODUCED
and REJECTED_ARCH_NOT_ALLOWED return an empty list. HELD_FOR_INVESTIGATION,
WORKTREE_LOST and SANDBOX_QB_FAILED retain their copies for investigation.
Without --abandon, explicit release applies only to those three retained states.
Release removes protection markers, not source directories; retries reconcile
interrupted operations. confirmed-by is an audit label, not authentication.

## Errors

- Exit 2: INVALID_ARGS.
- Exit 4: REJECTED_UNIT_NOT_TERMINAL, ReleaseNotAllowed, CAMPAIGN_STATE_BUSY
  or REJECTED_STATE_INCONSISTENT.

Never use these commands to bypass sandbox/review gates, or click Accept or
Ready to Accept. Reported state is not authorization to submit.
