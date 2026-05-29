# Decisions for build_skill v0.2 Phase B

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Workflow consumes `BuildResult.analysis_log_path` and falls back to `BuildResult.log_path` if it is absent. | Design §13 and user Phase B confirmation. | Phase A made build skill responsible for finding the structured failure log; the fallback keeps unit-test fakes and old-style build results compatible. | Workflow no longer duplicates GBS failure-log parsing while preserving existing behavior for callers that only provide v0.1 fields. |
| d002 | Remove workflow-local `select_analysis_log` and `GBS_FAILURE_LOG_PATTERN`, but keep build skill's `GBS_FAILURE_LOG_PATTERN`. | Pre-change grep requested by user. | The workflow selector became duplicate ownership after Phase A; build skill's pattern is the new canonical implementation. | `select_analysis_log` disappears from active source/tests; structured-log selection has one owner. |
| d003 | Real validation keeps A/B/C/D/E routing expectations unchanged after the ownership transfer. | User Phase B validation requirement. | The risk in Phase B is not code volume but log-source ownership: D/E must still use B logs, while A/B/C must not regress. | PR validation records all five real workflow cases and confirms build skill `analysis_log_path` is sufficient. |
