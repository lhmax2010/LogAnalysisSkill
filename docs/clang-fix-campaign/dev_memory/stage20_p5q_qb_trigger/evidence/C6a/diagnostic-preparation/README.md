# P5Q-C6A-03 Offline Diagnostic Evidence

Baseline: `66485ca`. These browser tests use only synthetic local HTTPS; the
production probe is not run against QuickBuild by this validation runner.
The dedicated C6 state database is not an input to the probe.

## Coverage

| Requirement | Test |
|---|---|
| Nine categories, fixed stderr, error response and runtime trace | `tests/node/test_qb_failure_categories.mjs`: one case per enum value |
| Actual guard call sites, no changed stop condition | Same file: new page, unpaused Worker, closeTarget false/throw, adapter and continuation failures; successful paused Worker still does not stop |
| Driver error metadata and invalid categories | `tests/unit/test_qb_browser.py::test_stop_category_driver_metadata`, `test_invalid_stop_category_is_protocol_error`, `test_exited_process_is_recorded_without_raw_exception` |
| Both CLI traces, unchanged result mapping and state | `tests/unit/test_p5q_c6_diagnostics.py::test_cli_failure_trace_preserves_category`: nine categories for each CLI |
| Real browser/production driver, no final action | `test_probe_local_real_driver`: normal, new page, disconnected browser, closed page |
| Probe source restriction | `test_probe_source_is_non_mutating` |
| Existing allow/deny matrix and static negative controls | `tools-01/node.log`; also invoked by full pytest |
| Four interception groups, actual server requests | `safety-01/safety.log`; also invoked by full pytest |

## Evidence Layout

- `full-02/pytest.log`, `pytest.xml`, `commands.json`: full regression and Node
  tests invoked through pytest. `artifacts/` holds four local probe runs, server
  request lists, agent transcripts, command results and the probe's `result.json`.
- `tools-01/`: mypy, import contracts, design checker and explicit Node matrix.
- `ruff-01/`: entire intended commit tree exported from the index, excluding
  unrelated user changes and untracked drafts; production and test files included.
- `safety-01/`: explicit rerun of all four safety groups after guard annotations.
- `audit.json`: gate summary and mechanical comparison with baseline. `Policy`
  is byte-identical; reversing only the diagnostic category annotations makes
  `installGuards` byte-identical as well.
- `environment.json`: later environment sampling and cleanup, after the first
  diagnostic implementation commit. No browser profile contents are archived.

Initial `full-01` did not start pytest: the new recorder selected the parent of
the repository for its executable path. Corrected to the repository root before
`full-02`; no test result is attributed to `full-01`.

Runtime trace and driver trace are separate: the agent records the fixed stop
category in its runtime trace; the standalone Python probe records safe command
metadata in its driver trace. No raw protocol events, headers, bodies or user
credentials are added to the production protocol.

`WORKER_BLOCKED` is an allowed diagnostic category and is covered by propagation
tests. The existing guard records a paused Worker as `WORKER_BLOCKED` in trace;
successful closure does not become a stop. Its existing failure branches report
`WORKER_NOT_PAUSED` or `CLOSE_TARGET_FAILED`, preserving the original decisions.

## Commands

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/run_validation.py full-02 full
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/run_validation.py tools-01 tools
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/run_validation.py safety-01 safety
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/run_validation.py ruff-01 ruff
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/audit.py
```

Each output label is exclusive; subsequent runs must use a new label. No live
diagnosis is authorized by running these commands. A fresh FatTank reply of
`开始` is required after gates, push and environment checks.
