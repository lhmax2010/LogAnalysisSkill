# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2026-06-01

### Added

- `tizen-gbs-build`: auto-recovery from broken build root by detecting the GBS
  broken-root marker and retrying once with `--clean`.
- Downstream token estimation in analyzer `perf_report.json` and workflow
  `workflow_summary.md`, reporting Claude-facing output token estimates.

### Changed

- Unified missing-parameter guidance across the three skills: ask for required
  `gbs.conf` / target architecture when missing, and use sensible defaults for
  output paths where appropriate.

## [1.0.0] - 2026-05-29

First stable release of LogAnalysisSkill: three independent local skills plus
workflow orchestration, verified on real Tizen `gbs` builds.

### Skills Included

- `tizen-gbs-build` v0.2: runs `gbs build`, captures terminal compiler logs,
  and locates the structured GBS failure log for analysis.
- `tizen-gbs-log-analysis` v0.5: analyzes existing build logs and produces
  compact Evidence Packets for LLM root-cause diagnosis.
- `tizen-gbs-build-workflow` v0.1: orchestrates build -> analyze -> suggestion
  generation without auto-applying patches.

### Key Engineering Milestones

- Analyzer M0-M8: delivered the v0.5 analyzer MVP with scan, rank, evidence
  collection, full-match, packet assembly, CLI, and E2E fixtures.
- hotfix_001: adapted scanner behavior to real ffmpeg GBS logs, including
  timestamp prefixes, `Executing(%build)` markers, assembler diagnostics, and
  token caps.
- hotfix_002: fixed real A/B/C/D injection cases across BudgetPool, truncation,
  patch cascade, linker confidence, degraded evidence, and tool gating.
- Build Workflow BW-M1-BW-M4: added build skill, workflow orchestration, seven
  suggesters plus fallback, and workflow E2E validation.
- hotfix_003: moved analyzer pattern data into the package so analyzer works
  from any cwd and after pip install.
- SKILL.md compliance: split and aligned the three skills with Anthropic Agent
  Skills conventions.
- Repo restructure: reorganized the repository into the final three-skill
  publishable layout.
- Build skill v0.2: made build skill the single owner of structured failure-log
  discovery and simplified workflow ownership.

### Verification at 1.0.0

- 408 tests pass with 96.01% coverage.
- Real ffmpeg validation covers success plus five fault classes: compile,
  linker undefined, depsolve, patch failed, and spec/RPM script failure.
- Both usage modes are validated: editable/pip install and direct side-by-side
  skill folders.
- Three `SKILL.md` files are Anthropic-compatible for local Claude Code / Cline
  use.

### Distribution

- Mode 1: install the repository into one Python environment and run
  `python -m gbs_*`.
- Mode 2: keep the three skill folders side by side and run `scripts/run_*.py`.
- Requires a local `gbs` command, `gbs.conf`, and access to a Tizen package
  source tree.

## Earlier Development

Pre-1.0 work is captured in `.dev_memory/`, `docs/real_smoke/`, and the design
documents under `docs/`.
