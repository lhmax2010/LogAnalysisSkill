---
name: tizen-sandbox-submit
description: Submit a three-architecture verified Clang campaign unit to an approved sandbox ref using the existing guarded submission workflow. Use only with verified campaign inputs and explicit push authorization; do not use for repair builds, QuickBuild actions, review pushes, or arbitrary git pushes.
---

# Tizen Sandbox Submit

Use this skill after local verification is ready for sandbox submission.
Batch 1 changes module ownership only; it grants no permission for a live push.

## Inputs

- Three verification ids, state database, and campaign configuration.
- Sandbox branch selected within the configured allowlist.
- Optional message brief and edit-source kind.

## Outputs

The existing JSON payload reports the action, derived commit, sandbox ref,
submission identity, state updates, and rejection details. Submission retains
the existing isolated git transport, locks, and final rechecks.

## Errors

- `INVALID_ARGS` rejects malformed input before submission.
- `CAMPAIGN_STATE_BUSY` reports lock or state contention.
- `REJECTED_UNSAFE_GIT_CONFIG` and `REJECTED_SUPPRESS_POLICY` stop unsafe inputs.
- Other existing rejection codes remain unchanged; do not replace rejection
  with an unguarded git command.

## Commands

```bash
python -m tizen_sandbox_submit sandbox-submit --help
python -m tizen_sandbox_submit sandbox-submit \
  --verification-ids "$VERIFICATION_IDS" --state-db "$STATE_DB" \
  --config "$CONFIG" --sandbox-branch "$SANDBOX_BRANCH"
```

## Idempotency

Change-Id generation and reuse follow the campaign cache and Gerrit hook rules.
Do not regenerate identity or delete cache rows to force another submission.
