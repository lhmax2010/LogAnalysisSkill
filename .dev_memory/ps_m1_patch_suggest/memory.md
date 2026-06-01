# Memory for PS-M1 Patch Suggest

## Status

Completed; waiting for review.

## Scope

PS-M1 introduces the `tizen-gbs-patch-suggest` package skeleton and the minimum
Evidence Packet path:

- read `--evidence` JSON
- select the first analyzer diagnostic via `primary_error`
- accept only `primary_error.kind == "compiler"`
- resolve source context through levels A/B/C
- write `context.md` and `meta.json`

The skill does not call an LLM, does not apply patches, and does not write the
source tree.

## Baseline

- Starting branch: `docs/patch-suggest-design`
- Starting main commit: `bcf2b7f` (`Merge pull request #35`)
- Design commits:
  - `53c3c0f` docs: add tizen-gbs-patch-suggest design (frozen)
  - `9def9fc` docs: add context.md mandatory instructions (D13/D14)

## Implementation Notes

- PS-M1 intentionally supports `--evidence` only. `--buildlog` is PS-M4.
- `SKILL.md` is a placeholder only. Full Anthropic Skill instructions are PS-M5.
- `README.md` output is deferred to PS-M3; PS-M1 writes `context.md` and
  `meta.json` per the PS-M1 acceptance scope.
- All `context.md` outputs include the D13/D14 mandatory instruction tail.

## Validation

- `ruff check .` passed.
- `mypy tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-build-workflow/scripts/gbs_workflow tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` passed.
- `python tizen-gbs-patch-suggest/scripts/run_patch_suggest.py --help` passed.
- `pytest tests/unit/test_patch_suggest.py -q` passed: `8 passed`.
- Full regression passed: `425 passed`, coverage `95.97%`.
