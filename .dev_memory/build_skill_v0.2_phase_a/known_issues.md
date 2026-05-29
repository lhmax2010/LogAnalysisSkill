# Known Issues for build_skill v0.2 Phase A

- Phase A intentionally leaves workflow's `select_analysis_log` in place. Phase B will switch workflow to `BuildResult.analysis_log_path` and remove the duplicate selector.
- The extractor supports the documented `Leaving the logs in .../logs/fail/<pkg>/log.txt` format only. Other GBS wording will fall back to compiler log A.
