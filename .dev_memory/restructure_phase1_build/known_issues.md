# Known Issues for Restructure Phase 1

- Phase 1 only moves the build skill. The analyzer and workflow packages still live at their current paths until later phases.
- Direct sibling discovery for workflow is intentionally deferred to Phase 3.
- `gbs_workflow` still imports `gbs_build_skill.runner`; Phase 1 validation confirmed the import works after package discovery was updated.
