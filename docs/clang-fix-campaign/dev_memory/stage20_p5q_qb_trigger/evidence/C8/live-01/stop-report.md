# C8 live-01: Post-Submit Discovery Read Failed

Status: STOPPED_READ_FAILURE, 2026-10-21. This is not a successful C8 acceptance.

## Authorization And Execution

The new user reply was exactly `确认提交`, recorded in [authorization.json](authorization.json).
Read-only preflight passed, including three D-state samples of 0/0/0,
no agent/Chromium/profile/transport leftovers and immutable C6/frozen-design inputs.
Only one production qb-trigger invocation was made. No retry or retrigger was made.

Full argv, UTC times, exit code, DB hashes and closing observations are in
[execution.json](trigger/execution.json). Start: 2026-10-21T11:02:05.864429+00:00.
End: 2026-10-21T11:07:21.457775+00:00. CLI exit: 5.

- Target: `platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`.
- Request: `202711dfe6b34472b6b8dc23f3a74a6e`, sequence 1.
- Full marker: `clang-fix-campaign request=202711dfe6b34472b6b8dc23f3a74a6e`.
- Result: `submit_uncertain` / `QB_SUBMIT_UNCERTAIN`.
- Observed landing: `/wicket/page`; messages: `[]`.
- Baseline W: 1203402. No build ID was obtained.
- Frozen snapshot: `tizen-base-toolchain_20261013.024319`.

## Failure Evidence

[trace-new.jsonl](trigger/trace-new.jsonl):2 records one post_submit discovery round.
It started 0.002617 seconds after the submit reply. Its first read was
`/overview/1917`, taking 579 ms before failure:

```json
{
  "agent_error_code": "QB_BROWSER_UNAVAILABLE",
  "agent_exit_code": null,
  "agent_exited": false,
  "command": "read",
  "failure_category": "UNKNOWN"
}
```

Configuration status and row_count are null; candidates are empty. No candidate
was inspected, so this is NOT evidence that no matching build exists.
[stderr.txt](trigger/stderr.txt):2 contains `QB_AGENT_STOPPED category=UNKNOWN`.
No HTTP status, response body, original exception or stack was recorded.
The precise source of UNKNOWN cannot be determined from these facts.

The build may already have been created. The CLI's generic follow-up message in
[stdout.json](trigger/stdout.json) does not override the C8 task's stop rule.
No qb-result-fetch, manual binding, further browser session or unit-2 creation
was performed. No Gerrit push or Accept/Ready to Accept action was performed.

## State And Cleanup

SQL snapshots: [before](trigger/state-before.sql), [after](trigger/state-after.sql).

| Item | Before | After |
|---|---|---|
| DB SHA256 | dd43219d2964e23d711e904ab640a73eb3c328e6685940dc7711beb4f7563ff2 | c346b6b8d065ad14a5dbab2bb9e9d66f370234e8ac73133426789002075b2c63 |
| QB requests/profiles/events | 0/0/0 | 1/1/1 |
| Unit status | SANDBOX_PUSHED | QB_REQUESTED |
| QB events | None | SUBMITTED only |

Only qb_traces/7383e5c48f62.jsonl was added under state_root. No result or page
evidence was produced. Parent echo comparison and terminal verification are
NOT_COLLECTED; zero-submission e1/e2/e3a/e3b are NOT_STARTED.
The closing tail (last observed Chromium to CLI exit) was 0.285600 seconds.
Final agent exit code is NOT_COLLECTED; the null in the failure response must
not be interpreted as an exit code. Immutable C6 files and both frozen designs
remain unchanged. Offline validation and final residual checks are recorded in
[validation.json](validation.json).

## Candidate Next Action, Not Executed

First reproduce the production submit-to-read transition offline. If UNKNOWN
still prevents attribution, seek approval for fixed, sanitized subcategories at
the existing error boundary. Do not log raw exceptions, protocol headers or
credentials. Any further live read or manual binding needs a separate decision;
do not resubmit based on this uncertain result.

No production or frozen-design changes were made in this run. C8 remains open.
