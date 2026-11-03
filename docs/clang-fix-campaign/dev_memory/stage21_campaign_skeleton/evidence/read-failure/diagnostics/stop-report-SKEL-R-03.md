# SKEL-R-03: C8 Gate Has A New Failure Scenario

Status: **STOPPED, NOT ACCEPTED**. No retry, threshold change, xfail, skip or
candidate-B implementation. The diagnostic implementation is retained for
design review, not reported as a completed/green gate.

## Facts

- Full regression: **901 passed / 1 failed / 0 skipped**, stopped at first
  failure after 353.98 seconds (wrapper 358.893 seconds). Of 3098 collected
  nodeids, 2196 were not run in this full-regression attempt.
- Nodeid: `tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures`.
- Assertion: `assert result.returncode == 0`, actual `1 == 0`, at
  `tests/unit/test_p5q_c8_investigation.py:26`; see `full/stdout.log` and JUnit.
- Failed scenario: `racing-script-navigation`; harness `TargetClosedError` /
  `OTHER_FRAMEWORK_ERROR`; agent `FETCH_CONTINUE_FAILED`.
- Original five-run baseline in stage21 section 7.1 had only
  `racing-meta-refresh` / `TargetClosedError` / `OTHER_FRAMEWORK_ERROR` /
  `FETCH_CONTINUE_FAILED`. A different failed scenario is explicitly a stop
  condition in SKEL-B1-03(3), carried forward by SKEL-B1-05(4).
- This does not establish that diagnostics caused a regression. It does mean
  the existing acceptance exception does not authorize passing this run.

## New First-Cause Observation

`full/c8/racing-script-navigation.json:913`:

```json
{"action":"OPERATION_FAILED","operation":"Fetch.failRequest","phase":"submit","stage":"request","path":"/wicket/page","generation":4,"category":"REQUEST_ID_INVALID"}
```

Only one first-cause entry appears; next is the original
`AGENT_STOPPED/FETCH_CONTINUE_FAILED` at line 922. No raw exception, request ID,
query, headers or body is included in this new entry.

Sequence in the same file:

1. The fake server received the one authorized synthetic form POST, returned
   302, then served the landing GET with 200 (lines 1019-1028).
2. The last observed request-stage GET on `/wicket/page` was in submit phase,
   with `frame_owned=true` (lines 679-686). It was denied; the subsequent
   Fetch failure was classified as `REQUEST_ID_INVALID`.
3. The original fail-closed callback closed the browser. Submit's existing
   released/unknown reply is unchanged (lines 1029-1035).
4. `reads=[]` (line 721); no `root_after_submit` was obtained. The harness next
   tries `Page.getFrameTree` at `tests/node/p5q_c8_investigation.mjs:73` and
   records `TargetClosedError` (JSON lines 1036-1040).
5. `synthetic_submissions=1`, `profile_removed=true` (lines 1041-1042).

This narrows the observed failing operation to rejecting a request during
submit, not continuing a response or navigating the first read. The trace
does not establish why its ID became invalid or prove a safe cancellation
exception. No interpretation changes the existing stopping rule.

## Completed Checks

- New 17 Node diagnostic cases and 10 pytest nodeids passed in focused tests.
- Focused gate: 221 passed, 0 failed, 0 skipped. Unchanged Node matrices:
  163 policy/agent, 16 stop-category, 183 static/negative-control cases, all pass.
- Local safety: 4/4 pass; forbidden Worker/WebSocket traffic zero, existing
  fail-closed branch retained; all temporary profiles removed.
- C5a six full-regression parameters all pass, including late-build.
- mypy: 161 files, no issues; ruff pass; import-linter 7 kept/0 broken;
  design checker 0 problem.
- Nodeids: all 3088 Batch3 nodeids retained, 10 added, no removals or
  collection errors. No old test changed.
- Full-gate load (20 CPUs): before `1.37 0.94 0.90`, after `1.40 1.28 1.07`;
  startup top ten process names/CPU only in `full/command.json`.
- `results.json`: no remaining P5Q process/profile, no instrumented temporary
  copy and no CPU stress process. No real QuickBuild/Gerrit/gbs operation.

## Candidate Disposition, Not Implemented

Keep the captured diagnostic and request a design decision on whether/how to
compare this additional scenario. If comparative sampling is authorized,
run the unchanged failing test on the parent and current trees in alternating
order with independent evidence; do not relax the test or silently extend
the allowed baseline. Any cancellation-tolerant production change still
requires separate evidence and authorization. No such work is performed here.
