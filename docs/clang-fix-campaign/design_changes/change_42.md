# change_42:RC smoke architecture argument mismatch (CLOSED)

Status: **closed (no design change)**

Resolution: CLI accepts `arch_raw` (`standard-armv7l`) and the whitelist maps
it to `arch_norm` (`armv7l`) for DB/workspace use. This is the existing frozen
contract in design §4.1. The error was confined to e2e-smoke-runbook v1/v2;
runbook v3 corrects it. This file remains as evidence that the stop-and-report
protocol triggered correctly.

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

## B. 裁决

The smoke runbook commands are amended only:

- pass `--arch standard-armv7l` to `campaign-repair-step`;
- continue asserting normalized DB/event/workspace fields as `armv7l`;
- continue using `gbs -A armv7l`; build-verify already derives this through
  `_gbs_arch("standard-armv7l")`.

No design or runtime-code change is needed. This is a runbook raw-versus-
normalized architecture correction, analogous to change_41's raw-log-versus-
evidence correction.

## C. Resumption gate (satisfied)

The developer explicitly accepted the amendment. RC resumes at E1 unit seeding
and reuses the existing broken-baseline raw log and analyzer JSON by their
recorded SHA-256 values; no baseline GBS rerun is required.

RD remains prohibited until the resumed RC completes or later deviations are
separately adjudicated.
