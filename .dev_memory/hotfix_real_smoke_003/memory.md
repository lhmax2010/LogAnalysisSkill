# Hotfix Real Smoke 003: package analyzer pattern data

**Status**: in-progress
**Start commit**: 1740233
**Start date**: 2026-05-20
**Completion date**:
**Estimated effort**: 0.5 day
**Actual effort**:

## Trigger

Running `gbs_workflow` from the ffmpeg source tree caused the analyzer subprocess to crash with:

```text
[Errno 2] No such file or directory: 'patterns/gbs_errors.yaml'
```

## Scope

- Move runtime pattern files from repo-root `patterns/` into `gbs_analyzer/patterns/`.
- Anchor default pattern paths with `Path(__file__)`, not cwd.
- Include pattern data in package data for pip installs.
- Update current docs that describe the file structure/path.

## Explicit Non-Scope

- Do not change pattern YAML/JSON content.
- Do not change analyzer matching/ranking/packet logic.
- Do not move or package `templates/` because analyzer runtime does not load it.
- Do not use `importlib.resources`.
- Do not batch-edit historical dev_memory paths.

## Planned Work

- [ ] `git mv patterns/ gbs_analyzer/patterns/`.
- [ ] Update `quick_filter.DEFAULT_PATTERN_PATH` and `SemanticClassifier.DEFAULT_SEMANTICS_PATH`.
- [ ] Add setuptools package data for `gbs_analyzer/patterns`.
- [ ] Update docs: DESIGN, CODEX_PROMPT, pattern authoring, M6 guide.
- [ ] Validate arbitrary cwd analyzer run.
- [ ] Validate pip-installed analyzer run from outside repo.
- [ ] Run full regression.
