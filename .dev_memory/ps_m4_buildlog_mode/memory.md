# Memory for PS-M4 Buildlog Mode

## Status

Completed; ready for review.

## Scope

PS-M4 adds `--buildlog` convenience mode to `tizen-gbs-patch-suggest`:

- `--evidence` and `--buildlog` are mutually exclusive and required as a group
- buildlog mode runs `python -m gbs_analyzer analyze` as a subprocess
- analyzer output is written under `.gbs_patch_suggest/analyzer_output/`
- generated `evidence_packet.json` feeds the existing patch-suggest ingest/resolver/render flow
- direct-folder mode discovers sibling `tizen-gbs-log-analysis` by env var or sibling layout

No analyzer, workflow, build skill, Suggester, or pattern code changed.

## Baseline

- Starting branch: `main`
- Starting commit: `3d7eeae` (`Merge pull request #40`)
- Branch: `feature/ps-m4-buildlog-mode`

## Validation

- `ruff check tizen-gbs-patch-suggest tests/unit/test_patch_suggest.py` passed.
- `mypy tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` passed.
- `pytest tests/unit/test_patch_suggest.py -q` passed: `23 passed`.
- Full regression passed: `440 passed`, coverage `95.97%`.
