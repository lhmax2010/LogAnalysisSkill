# change_42:RC smoke architecture argument mismatch (PROPOSED)

Status: **adjudication required; not applied to frozen design or runtime code**

Triggered by: resumed RC E1 unit-seed preflight on 2026-08-05.

## A. Contradiction

`e2e-smoke-runbook.md` E2 invokes campaign repair with `--arch armv7l` and E3/E4
inherit that command shape. The frozen public wrapper accepts only keys in
`campaign_state.ARCH_RAW_TO_NORM`:

```python
"standard-armv7l": "armv7l"
```

`armv7l` is the normalized DB/workspace/GBS value, not the public raw input.
A process-level probe with the runbook value returned exit 4,
`REJECTED_IDENTITY_MISMATCH`, `invocations_used=0`, before reading any state or
filesystem input.

The v2 resolution for change_41 explicitly retained every other runbook clause,
so the operator cannot silently replace this argument during RC.

## B. Proposed裁决

Amend the smoke runbook commands only:

- pass `--arch standard-armv7l` to `campaign-repair-step`;
- continue asserting normalized DB/event/workspace fields as `armv7l`;
- continue using `gbs -A armv7l`; build-verify already derives this through
  `_gbs_arch("standard-armv7l")`.

No design or runtime-code change is needed. This is a runbook raw-versus-
normalized architecture correction, analogous to change_41's raw-log-versus-
evidence correction.

## C. Resumption gate

RC may resume at E1 unit seeding after the developer explicitly accepts the
runbook amendment above. The existing broken-baseline raw log and analyzer JSON
remain valid and immutable by SHA-256; no GBS rerun is required for this
adjudication.

RD remains prohibited until the resumed RC completes or later deviations are
separately adjudicated.
