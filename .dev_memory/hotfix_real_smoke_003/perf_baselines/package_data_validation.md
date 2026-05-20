# Hotfix 003 Package Data Validation

Date: 2026-05-20

## Arbitrary cwd analyzer

- Command: `cd /tmp && .venv/bin/python -m gbs_analyzer analyze ...`
- Buildlog: `/home/linhao/Toolchain/development/ffmpeg/.gbs_workflow/compiler.log`
- Output: `/tmp/h3_v1`
- Exit: 0
- Primary kind: `compiler`
- Packet tokens: 1477

## Pip-installed analyzer

- Environment: `/tmp/h3_test`
- Created with: `uv venv /tmp/h3_test`
- Installed with:
  `uv pip install --python /tmp/h3_test/bin/python /home/linhao/Toolchain/development/LogAnalysisSkill`
- Command cwd: `/tmp`
- Output: `/tmp/h3_v2`
- Exit: 0
- Installed package root:
  `/tmp/h3_test/lib/python3.12/site-packages/gbs_analyzer`
- Installed pattern files:
  - `README.md`
  - `error_semantics.yaml`
  - `gbs_errors.yaml`
  - `schema.json`

## Workflow smoke from ffmpeg cwd

- Command cwd: `/home/linhao/Toolchain/development/ffmpeg`
- Output: `/tmp/h3_workflow_ffmpeg`
- Workflow exit: 1
- Analyzer primary kind: `compiler`
- Location: `libavcodec/utils.c:109`
- Suggestion: `CompileErrorSuggester`

## Regression

- Full tests: 389 passed
- Analyzer coverage: 96.01%

Note: PR #19 is still open, so this hotfix branch is based on current `main`
with 387 baseline tests plus 2 hotfix regression tests.
