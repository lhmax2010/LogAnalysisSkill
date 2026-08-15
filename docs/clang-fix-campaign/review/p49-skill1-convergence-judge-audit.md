# P4.9 Skill-1 Convergence-Judge Audit

Frozen authority:
`docs/clang-fix-campaign/p49-skill1-convergence-judge-design-v1.2-FROZEN.md`.
The authority's body is revised in place to v1.3-FROZEN by the commit C
layered-audit ruling; the path remains stable for existing references.

## Freeze Provenance

- Delivered source: `p49-skill1-convergence-judge-design-v1.2.md`.
- Target-machine v1.1 to delivered v1.2 delta: title/version provenance plus the
  two declared residual-wording fixes; no additional edits were found before
  the delivered v1.2 body was frozen.
- Canonical and history snapshot are byte-identical; their integrity is anchored
  by the freeze commit rather than a self-recorded hash.
- Initial v1.2 frozen design SHA-256 at commit `d3478ab`:
  `ef0eda37112dfbcd574b5b17d42de264e2270b07462e6d244cdf5e5f4ff0a4a3`.
- Revised v1.3 canonical/history SHA-256:
  `c41427e092a677f45c5cb10a51ccc7dbdaa561459131fe37221e98c62ccb24d0`.

Implementation audit results are appended by commits A, B, and C.

## Freeze Baseline Audit

Commands:

```bash
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py
```

Results:

```text
symbol audit: 42 SYMBOL OK + 4 MODULE-SCOPE OK (48 SYMBOLS COVERED),
0 MISMATCH, 0 INCOMPLETE
table bridge: 42 SYMBOL OK + 4 MODULE-SCOPE OK,
0 MISSING_FROM_INVENTORY, 0 MISSING_FROM_BODY, 0 OWNER_MISMATCH, 0 PARSE_ERROR
```

## Commit A: C21

All three campaign CLI subprocess tests now share an exact five-path,
`__file__`-anchored `PYTHONPATH`. A run launched from `/tmp` passed all three
tests, and the full suite remained at 846 passed and one skipped.

## Commit B: Extraction

- Pre-alias source copy was byte-identical at SHA-256
  `d606f86745c4d57b68a775a393d6adf2ef3c637c9c968cb0aea31ae0906ead3c`.
- Removing the final two aliases and their separating blank lines restores the
  exact original 439-line implementation (`cmp` exit 0).
- Public/private function bindings are object-identical; only the two private
  definitions remain in the repository.
- The legacy module is a zero-def/class shim and is registered for the P4.9
  final compatibility cleanup.
- Full suite: 847 passed, one skipped (the baseline plus one identity test).

## Commit C: Layered Audit, Gates, and Parity

The previous multi-consumer rule was replaced by the root-layer order
`ci_triage > registered skill > shared`. `check_convergence` now passes with
its two measured orchestration consumers, while explicit skill-to-shared and
skill-to-peer-skill fixtures both return MISMATCH with exit 1. Comparing all
pre-change step-0 verdicts reports 42 symbol and four module-scope verdicts
checked, with zero changes.

The activated import-linter configuration reports five kept contracts and zero
broken. Its two required negative controls return exit 1 for skill importing
`ci_triage` and shared importing `tizen_convergence_judge`, then return to five
kept after restoration.

The final audits report:

```text
symbol_audit: 77 SYMBOL OK + 4 MODULE-SCOPE OK (48 SYMBOLS COVERED),
0 MISMATCH, 0 INCOMPLETE
table bridge: 77 SYMBOL OK + 4 MODULE-SCOPE OK,
0 MISSING_FROM_INVENTORY, 0 MISSING_FROM_BODY, 0 OWNER_MISMATCH, 0 PARSE_ERROR
```

Module-scope counts are pinned at 10/3/8/27; a temporary 28th classify symbol
produced the expected count-drift mismatch and exit 1. Shim/new-skill result
JSON has identical SHA-256
`2f881fe8935b8b652c756efac596c2d904c1e45f3b502857b75c3d071d99957b`
and `cmp` exit 0. The skill implementation has zero `arch` occurrences.

Final validation: `847 passed, 1 skipped`; import-linter `5 kept, 0 broken`;
ruff clean; mypy clean across 97 source files; 34 shared/skill/triage Python
files compiled successfully. Canonical/history design comparison returned exit
0. Commit C changes no production implementation or test file.
