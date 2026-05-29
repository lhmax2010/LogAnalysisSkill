# Decisions for build_skill v0.2 Phase A

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Preserve all v0.1 `BuildResult` and `BuildOptions` fields and append v0.2 fields at the end of `BuildResult`. | Design §4.2, §4.3, §12 and user Phase A confirmation. | Workflow currently consumes `BuildOptions(... output_log=..., cwd=...)`, `result.exit_code`, and `result.log_path`; renaming fields would break Phase A compatibility. | Existing workflow and tests remain valid while new callers can use `analysis_log_path`. |
| d002 | `--src-dir` is implemented through existing `BuildOptions.cwd`; missing directories are argument errors with exit code 2. | Design §4.1/§5 plus user clarification. | No new option field is needed; validating CLI input prevents subprocess `cwd` errors from looking like gbs failures. | Python API remains unchanged; CLI gains explicit source directory control. |
| d003 | Failure log extraction uses only the primary `Leaving the logs in .../logs/fail/<pkg>/log.txt` regex and requires the file to exist. | Design §6. | Avoids guessing GBS root from config and keeps fallback behavior deterministic. | If B is missing or not present on disk, `analysis_log_path` falls back to A. |
