# P4.9 skill-6 triage-report progress

## Freeze prerequisites and A0 gates

Status: A0 COMPLETE, awaiting independent review before extraction commit A.

Authority under test:
`docs/clang-fix-campaign/p49-skill6-triage-report-design-v1.8-FROZEN.md`.
The design was frozen by commit `bdb5a55` only after the parser and branch
inventory had run successfully in the worktree. The exact script used for that
run is the A0 artifact with SHA-256
`6fcb8036f158d80ad48ec965b4cb99f16ce3cc4218c7f39f529738e14fc663df`.
After the first pre-freeze run, the external-branch check was strengthened to
inspect the shared source AST at lines 193 and 198 instead of trusting the
design text alone. The parser and complete branch check were rerun before A0
staging with the strengthened version; the freeze commit message was amended
to carry this final script SHA and rerun result.

### Parser-only and branch inventory

```text
$ python3 docs/clang-fix-campaign/tools/branch_inventory.py check \
    --design docs/clang-fix-campaign/p49-skill6-triage-report-design-v1.8-FROZEN.md \
    --data docs/clang-fix-campaign/tools/branch_inventory.skill6.json
PARSER_ONLY | 24/24 | missing=0 | extra=0 | OWNER_MISMATCH=0 | OK
BRANCH_TABLE | rows=25 | referenced_ids=62 | unreferenced_ids=7 | external_rows=2 | OK
MODULE | gbs_report | decision_points=19 | terminal_outcomes=24 | ids=43 | unique=YES
MODULE | report | decision_points=22 | terminal_outcomes=4 | ids=26 | unique=YES
SUMMARY | modules=2 | ids=69 | collisions=0 | unknown_refs=0 | missing_reasons=0 | OK
exit=0
```

The inventory uses only the selectors frozen in section 11. It excludes
`_ReportTableParser` and `_IframeParser`, treats bare returns as terminal
outcomes, counts each comprehension `if`, and gives `match_case` its pattern
line with the enclosing match line as fallback. Duplicate IDs fail closed.

The section 5 table has 25 rows. Its 23 local rows name exact branch IDs; its
two `EXTERNAL_BRANCH` rows each bind one real local call, the external
`tizen_ci_shared.quickbuild_http:193:if` / `:198:raise` pair, and the expected
`QuickBuildError` code `COOKIE_EXPIRED`. Seven internal IDs are not cited by a
table row; `branch_inventory.skill6.json` records a non-empty reason for each,
and the checker requires exact set equality between those IDs and the reason
map.

Full output: [branch-check.txt](a0-evidence/branch-check.txt).

### v1.7 admission falsification

The selected v1.7 snapshot contains both required defects: the hand-written
BoolOp count and the missing v1.7 revision block.

```text
$ python3 docs/clang-fix-campaign/tools/branch_inventory.py admission-v17 \
    --snapshot docs/clang-fix-campaign/history/skill6/p49-skill6-triage-report-design-v1.7-draft.md
ADMISSION | HANDWRITTEN_BOOL_COUNT | DRIFT
ADMISSION | MISSING_V17_REVISION_BLOCK | DRIFT
ADMISSION | snapshot=v1.7 | required=2/2 | RED_AS_EXPECTED
exit=1
```

Full output: [branch-admission-v17.txt](a0-evidence/branch-admission-v17.txt).

### Skill-6 design drift ledger

The independent corpus is the continuous sequence v1.0 through v1.8 under
`history/skill6/`. Bootstrap generated 57 raw candidates and partitioned every
candidate into 56 retained and 1 mechanically out-of-scope item. The five
forward bindings cover symbol/parser ownership, the step-0 constraint close,
the three twin decisions, parity/delivery, and the branch inventory. Every DoD
is either bound or explicitly marked `PROCESS_ONLY`.

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill6.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=57 | retained=56 | ignored=1 | bindings=5 | binding_candidates=435
exit=0

$ ... negative-fixture out-of-scope-misuse --data <skill6-data>
OUT_OF_SCOPE_SUMMARY | items=1 | RED_AS_EXPECTED
exit=1

$ for each of 5 binding IDs: ... negative-binding <id> --data <skill6-data>
NEGATIVE_BINDING_SUMMARY | bindings=5 | expected=5 | unexpected=0
each exit=1
```

Full outputs:

- [skill6-ledger-check.txt](a0-evidence/skill6-ledger-check.txt)
- [skill6-out-of-scope.txt](a0-evidence/skill6-out-of-scope.txt)
- [skill6-binding-negatives.txt](a0-evidence/skill6-binding-negatives.txt)

### Skill-4 inherited gate regression

```text
check: SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=131 | retained=84 | ignored=47 | bindings=22 | binding_candidates=1410
admission-v19: BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED | exit=1
OUT_OF_SCOPE_SUMMARY | items=47 | RED_AS_EXPECTED | exit=1
NEGATIVE_BINDING_SUMMARY | bindings=22 | expected=22 | unexpected=0 | each exit=1
```

Full outputs:

- [skill4-check.txt](a0-evidence/skill4-check.txt)
- [skill4-admission-v19.txt](a0-evidence/skill4-admission-v19.txt)
- [skill4-out-of-scope.txt](a0-evidence/skill4-out-of-scope.txt)
- [skill4-binding-negatives.txt](a0-evidence/skill4-binding-negatives.txt)

### Skill-5 inherited gate regression

```text
check: SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=40 | retained=36 | ignored=4 | bindings=8 | binding_candidates=348
admission-v12: BINDING_DRIFT=7 | required_known=2 | RED_AS_EXPECTED | exit=1
OUT_OF_SCOPE_SUMMARY | items=4 | RED_AS_EXPECTED | exit=1
NEGATIVE_BINDING_SUMMARY | bindings=8 | expected=8 | unexpected=0 | each exit=1
```

Full outputs:

- [skill5-check.txt](a0-evidence/skill5-check.txt)
- [skill5-admission-v12.txt](a0-evidence/skill5-admission-v12.txt)
- [skill5-out-of-scope.txt](a0-evidence/skill5-out-of-scope.txt)
- [skill5-binding-negatives.txt](a0-evidence/skill5-binding-negatives.txt)

### Freeze-prerequisite sequencing clarification

For this batch, “parser-only and branch inventory are freeze prerequisites”
means their real execution preceded the freeze commit. Their artifact commit
follows the freeze commit so the first lifecycle commit remains the frozen
design. The freeze commit message records the exact outputs and script SHA;
this progress record and the A0 commit preserve the same script and complete
outputs. The one hardening change between the initial freeze run and A0 was
therefore rerun and disclosed rather than silently replacing the evidence.

### Tool and repository regression

```text
skill6 ledger bootstrap before=3df8cb8799ed2da79cec67ee9bd6664ed1585c479393dd2b80600b4d44b115ec
skill6 ledger bootstrap after =3df8cb8799ed2da79cec67ee9bd6664ed1585c479393dd2b80600b4d44b115ec
deterministic=yes

$ .venv/bin/ruff check docs/clang-fix-campaign/tools/branch_inventory.py
All checks passed!
$ .venv/bin/ruff format --check docs/clang-fix-campaign/tools/branch_inventory.py
1 file already formatted
$ .venv/bin/mypy docs/clang-fix-campaign/tools/branch_inventory.py
Success: no issues found in 1 source file
$ python3 -m py_compile docs/clang-fix-campaign/tools/branch_inventory.py
exit=0
$ .venv/bin/pytest -q
912 passed, 1 skipped in 18.54s
```
