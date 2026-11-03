---
name: tizen-qb-verify
description: Trigger and read campaign QuickBuild RBS verification with the guarded browser agent, frozen parameters, and request binding. Use only for authorized campaign verification; do not use for general browsing, REST fallback, Accept or Ready to Accept actions, or Gerrit pushes.
---

# Tizen QuickBuild Verify

Use `qb-trigger` for an authorized verification request and `qb-result-fetch`
for binding and reading its result. The browser agent is packaged beside its
Python driver. Module relocation does not authorize a live operation.

## Inputs

- State database, state root, and campaign configuration.
- Trigger: verification ids or a units file; retrigger only under the existing
  explicit authorization rules.
- Fetch: request id or requests file; optional manual build binding and the
  existing single-request snapshot-drift acceptance option.
- Interactive login performed by the user in the browser, never credentials
  supplied through chat or recorded in evidence.

## Outputs

Both commands emit the existing per-unit JSON array. They retain request/event
records, redacted evidence, traces, frozen profiles, and result-file contracts.
A failed Full build does not by itself identify the target package as failing.

## Errors

- `INVALID_ARGS` rejects invalid command combinations before browser startup.
- `QB_BROWSER_UNAVAILABLE` and login errors stop the affected browser workflow.
- `REJECTED_QB_FORM_CHANGED`, `REJECTED_QB_SNAPSHOT_UNAVAILABLE`, and binding
  mismatch codes require the existing documented handling, not relaxed checks.
- `QB_SUBMIT_UNCERTAIN` is not authorization to submit again. Follow request
  lookup and binding results; never bypass the request's idempotency guard.
- Redaction failures stop evidence publication.

## Commands

```bash
python -m tizen_qb_verify qb-trigger --help
python -m tizen_qb_verify qb-result-fetch --help
python -m tizen_qb_verify qb-trigger \
  --verification-ids "$VERIFICATION_IDS" --state-db "$STATE_DB" \
  --state-root "$STATE_ROOT" --config "$CONFIG"
python -m tizen_qb_verify qb-result-fetch \
  --request-id "$REQUEST_ID" --state-db "$STATE_DB" \
  --state-root "$STATE_ROOT" --config "$CONFIG"
```

## Idempotency

Keep the existing latest-request checks, frozen parameters, and RESULT re-read
semantics. Never click Accept or Ready to Accept. Do not store browser sessions
or introduce an alternate transport around the guarded agent.
