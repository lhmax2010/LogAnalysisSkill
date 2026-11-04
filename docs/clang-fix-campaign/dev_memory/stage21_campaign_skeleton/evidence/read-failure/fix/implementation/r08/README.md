# SKEL-R-08 Validation Resume

Baseline: `5b41ee9`. The sole source change is observation-only metadata in
`tests/node/p5q_c8_investigation.mjs`, committed separately as `fb549ea`.
`integrity.json` lists every changed line hunk and confirms the production
agent, original assertions and scenario list are unchanged.

Status: **VALIDATED under SKEL-R-08**, no next-batch work started.

| Check | Result |
|---|---|
| C8 formal attempts | 19 PASS / 1 preserved historical FAIL (attempt 04, accepted observation); all resumed 05-20 passed |
| late-build | 20 PASS / 0 FAIL, no repeats needed |
| FETCH_CONTINUE_FAILED | 0 across all formal attempts |
| Natural DENY_TARGET_GONE | 3: two preserved in 04, one in 11; no resulting stop |
| Full pytest, no fail-fast | 3099 PASS / 0 FAIL / 1 existing platform skip, 1061.027 seconds including wrapper |
| Full C8 / C5a / four safety groups | Passed; no gate exception or retry used |
| Static gates | mypy, ruff, all seven import contracts, design checker passed |
| Nodeids | 3100 before and after, no additions or removals |
| Residue | No P5Q profiles or agent/Chromium processes |

`final.json` is the final structured summary. All 36 new formal attempts
started below load 6 and waited zero seconds. The first four historical runs
retain NOT_COLLECTED for waiting; their metadata was not rewritten. The full
suite's load was 0.53/0.62/0.72 before, 1.17/1.00/0.98 after on 20 cores.
Source/document whitespace checks pass. The staged evidence check reports
103 trailing-whitespace lines solely in original fake-server qb_evidence HTML;
these raw bytes are preserved. No database binaries or certificate keys are staged.

## Evidence Preservation

The 133 files already tracked below `implementation/` at the baseline are
unchanged. In particular, `c8-01` through `c8-04`, the prior wrapper error,
the SKEL-R-07 report and its failed pytest output are retained, not replaced.
The old `results.json` describes the historical stopped run; this directory's
`results.json` is the new cumulative view. The fourth attempt is the first
failure observation and remains a raw FAIL, accepted by SKEL-R-08 I.2.

## Sampling

`resume.py.txt` reuses the original runner and unmodified test argv, records
load waiting, and starts new independent directories `../c8-05` through
`../c8-20`, then `../late-01` through `../late-20`.

- Before every attempt, 1-minute load must be below 6. Waiting is sampled
  every 10 seconds, saved in `load-waits/`, then attached to that attempt's
  `command.json`. At 30 minutes the run pauses without starting a browser.
- Tests remain serial and use the existing private virtual display, local
  HTTPS fake server, test certificate and test resolver rules. No real
  QuickBuild, Gerrit or gbs. No extra CPU load and no other process termination.
- Every attempt records before/after load, CPU core count, initial top-ten
  process names/CPU only, raw pytest exit and JUnit, all scenario trace action
  counts, failure shape and P5Q profile/process leftovers.
- First failure Fetch.failRequest/REQUEST_ID_INVALID followed by stop,
  three occurrences of a non-exempt failure shape, or profile/process leftovers
  stop the runner. The only explicitly exempt login shape is the original
  racing-wicket-navigation/login/TargetClosedError/OTHER_FRAMEWORK_ERROR.
- late-build requires zero FETCH_CONTINUE_FAILED. An assertion failure is
  retained and may be exempted only after all three independent repeats pass.

## Full Gate

After the sampling checks, `../full-r08/` runs the full pytest suite, with no
`-x` or `--maxfail`. Raw failures are never edited. `full-verdict.json` records
the SKEL-R-08 C8 observation exception and any three-run C5a timing exception
separately. Other failures stop delivery. Static gates are under `gates/`.

`sampling-results.md` and `results.json` retain the complete per-attempt view;
the latter also records every scenario's action counts. Login observation data
is checked for exact key sets and synthetic-secret absence after each run.
Only fixed step names, response enums and monotonic elapsed milliseconds are
added to the harness; it still propagates the same exceptions and asserts the
same outcomes with the same time limits.
