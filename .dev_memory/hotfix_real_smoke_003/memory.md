# Hotfix Real Smoke 003: package analyzer pattern data

**Status**: completed
**Start commit**: 1740233
**Start date**: 2026-05-20
**Completion date**: 2026-05-20
**Estimated effort**: 0.5 day
**Actual effort**: 0.5 day

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

- [x] `git mv patterns/ gbs_analyzer/patterns/`.
- [x] Update `quick_filter.DEFAULT_PATTERN_PATH` and `SemanticClassifier.DEFAULT_SEMANTICS_PATH`.
- [x] Add setuptools package data for `gbs_analyzer/patterns`.
- [x] Update docs: DESIGN, CODEX_PROMPT, pattern authoring, M6 guide.
- [x] Validate arbitrary cwd analyzer run.
- [x] Validate pip-installed analyzer run from outside repo.
- [x] Run full regression.

## Key Change Details

### 1. Pattern data moved into package

- **Files**: `gbs_analyzer/patterns/*`
- **Reason**: Analyzer must find runtime pattern data outside the repository root.
- **Tests**: Package path assertions in quick-filter and semantic-classifier unit tests.

### 2. Runtime paths anchored by `__file__`

- **Files**: `gbs_analyzer/quick_filter.py`,
  `gbs_analyzer/_utils/semantic_classifier.py`
- **Reason**: Defaults should be independent of caller cwd while preserving explicit
  temp-path overrides in tests.
- **Tests**: Default loaders pass from non-repo cwd.

### 3. Package data included for pip install

- **Files**: `pyproject.toml`
- **Reason**: Wheels/normal installs must include YAML/JSON/README pattern data.
- **Tests**: Clean `/tmp/h3_test` venv installed the package and listed
  `gbs_analyzer/patterns` from site-packages.

### 4. Documentation synchronized

- **Files**: `docs/DESIGN.md`, `docs/CODEX_PROMPT.md`,
  `docs/pattern_authoring.md`, `docs/test_guides/m6_full_match.md`
- **Reason**: Current authoring/runtime docs should point at packaged pattern paths.
- **Tests**: Docs-only change; verified by grep.
