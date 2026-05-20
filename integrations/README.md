# Integration Examples

This repository provides example contracts for external callers:

- `cline/`: custom command configuration for Cline-style invocation.
  - `analyze_gbs.json`: analyze an existing buildlog with `gbs_analyzer`.
  - `build_workflow.json`: run `gbs_workflow` to build, analyze failures, and
    write suggestions.
- `compiling_agent/`: subprocess adapter for unattended build-monitoring agents.

These examples are not live integrations and are not deployed by this repository.
Workflow examples never auto-apply patches or auto-retry builds.
