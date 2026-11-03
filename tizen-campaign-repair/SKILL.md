---
name: tizen-campaign-repair
description: Run one locked, budgeted Clang campaign repair step for a registered unit and architecture. Use after campaign evidence and the edit specification are ready; do not use for discovery, direct compilation outside the repair workflow, sandbox pushes, QuickBuild submission, or review submission.
---

# Tizen Campaign Repair

Use this skill for the campaign's existing repair-step workflow. It owns the
repair command, not the shared campaign state implementation.

## Inputs

- Campaign unit key, state database, and campaign configuration.
- Round index, edit specification, and raw architecture name.
- Optional build wall timeout.

## Outputs

The command emits the existing repair result JSON, including verification and
evidence references, reconciliation, convergence, budget usage, and error code.
It records work through the existing campaign state APIs.

## Errors

Preserve the command's existing rejection and held-state handling. In particular,
`INVALID_ARGS` rejects malformed arguments, `CAMPAIGN_STATE_BUSY` rejects lock
contention, and identity, evidence, or budget failures must not be bypassed by
calling build-verify directly. Inspect the result's `error_code` and reason.

## Commands

```bash
python -m tizen_campaign_repair campaign-repair-step --help
python -m tizen_campaign_repair campaign-repair-step \
  --campaign-unit-key "$UNIT_KEY" --state-db "$STATE_DB" --config "$CONFIG" \
  --round-index "$ROUND" --edit-spec "$EDIT_SPEC" --arch "$ARCH"
```

## Idempotency

The existing locking, reconciliation, and budget rules remain authoritative.
Do not create worktree paths or verification records outside that workflow.
