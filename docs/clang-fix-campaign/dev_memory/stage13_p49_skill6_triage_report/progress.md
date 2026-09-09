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

## Commit A: two-module extraction and pre-shim parity

Status: COMPLETE, pending commit and independent review.

Authority:
`docs/clang-fix-campaign/p49-skill6-triage-report-design-v1.8-FROZEN.md`
at `bdb5a55`; A0 gate commit `3dc0466`.

### Migration source evidence

The skill copies were created while both legacy modules were still independent
implementations. The report module remained byte-identical. The GBS report
module's zero-context diff contains exactly the one frozen import whitelist:

```text
$ git show 3dc0466:tizen-ci-triage/scripts/ci_triage/report.py > /tmp/report-before.py
$ cmp /tmp/report-before.py tizen-triage-report/scripts/tizen_triage_report/report.py
(no output)
exit=0
sha256(old)=a8138cb73ffa23cd58cb073dbc95d7add94db0866202a3a42d9eb3b1b158602e
sha256(new)=a8138cb73ffa23cd58cb073dbc95d7add94db0866202a3a42d9eb3b1b158602e

$ diff --unified=0 /tmp/gbs-report-before.py \
    tizen-triage-report/scripts/tizen_triage_report/gbs_report.py
@@ -10 +10 @@
-from ci_triage.quickbuild import (
+from tizen_ci_shared.quickbuild_http import (
exit=1 (the expected single diff)
```

The migrated module/function comments remain accurate. A scan for inherited
`shim`, `removed at`, `temporary`, `delete at`, `will be deleted`, and `legacy`
annotations returned no matches (`rg` exit 1).

### B-stage scaffolding

No packaging, CI, or README entrypoint is changed in commit A. Commands used the
same temporary `PYTHONPATH` and `MYPYPATH`, with these script roots in order:

```text
$PWD/tizen-triage-report/scripts
$PWD/tizen-ci-shared/scripts
$PWD/tizen-ci-triage/scripts
$PWD/tizen-gbs-log-analysis/scripts
$PWD/tizen-gbs-patch-suggest/scripts
$PWD/tizen-gbs-build/scripts
$PWD/tizen-gbs-build-workflow/scripts
$PWD/tizen-convergence-judge/scripts
$PWD/tizen-qb-discover/scripts
$PWD/tizen-gerrit-fetch/scripts
$PWD/tizen-build-verify/scripts
$PWD/tizen-gerrit-submit/scripts
```

This is extraction scaffolding only; permanent delivery entrypoints belong to
commit C.

### Pre-shim behavioral parity

The parity command ran before either legacy implementation became a shim. A
migration-only driver loaded and explicitly reloaded four distinct module
objects (`ci_triage.gbs_report`, `tizen_triage_report.gbs_report`,
`ci_triage.report`, and `tizen_triage_report.report`). It used JSON cookie files
and fake `HttpResponse` objects only; no real QuickBuild request was made. The
complete output is preserved in
[pre-shim-parity.txt](commit-a-evidence/pre-shim-parity.txt).

The six closed payload partitions were:

1. every `GbsReport` field, every package field, and the separately materialized
   ordered `failed_packages` property;
2. ordered fake-fetcher URL/cookie/kwargs traces;
3. every `TriageReportData` field and the complete `render_report` text;
4. `cookie_path`, `DEFAULT_COOKIE_PATH`, and `DEFAULT_QUICKBUILD_BASE_URL`;
5. exception type, `QuickBuildError.code`, and full message;
6. the exact `download_gbs_package_buildlog` return text.

Only `controlled_environment.cookie_path` was replaced with `<PATH>`, directly
at that named field. No payload-wide replacement was performed. Volatile-source
discovery against both modules (`uuid|datetime|time|random`) returned no match
(`rg` exit 1), so no source freeze was required.

```text
isolation.importlib_reload=True
isolation.distinct_gbs_modules=True
isolation.distinct_report_modules=True
field_equal[gbs_report]=True
field_equal[fake_fetcher_trace]=True
field_equal[triage_render]=True
field_equal[controlled_environment]=True
field_equal[error]=True
field_equal[download_gbs_package_buildlog]=True
payload_equal=True
payload_sha256=3b48576e287920556366413926a16451f56883b944b2a8bb7cafd48c3879c2a1
mask_scope=controlled_environment.cookie_path only
payload_wide_replacement=False
fake_fetcher_calls=4
failed_packages_count=1
normalizer_positive.cookie_path_only=True
normalizer_negative.failed_packages=True
normalizer_negative.http_call_order=True
normalizer_negative.iframe_url=True
exit_code=0
```

The migration-only driver was intentionally not retained after the shim
convergence point: rerunning it from the final tree would compare a shim with
its target and could be mistaken for independent pre-shim evidence. The output
above is the Git-anchored migration-time evidence; commit parent `3dc0466`
retains both original implementations for source replay.

### Shim, consumers, and package surface

The two old locations are pure re-export shims with zero top-level `def` or
`class`. Runner and orchestrator diffs contain import-path changes only. The
package root exports exactly the nine names frozen by section 1.2 and does not
export the fifteen implementation names. Permanent tests also prove all 24
legacy names are identical to their skill definitions.

```text
$ pytest -q tests/unit/test_ci_triage.py \
    -k 'triage_report_package_root or triage_report_legacy_shims'
2 passed, 59 deselected in 0.05s

$ rg -n '^(def|class) ' \
    tizen-ci-triage/scripts/ci_triage/{gbs_report,report}.py
(no output)
exit=1

package_public_identity=9/9
package_internal_absent=15/15
post_shim_identity=9+15
```

Post-shim identity is wiring evidence only and does not replace the independent
pre-shim behavior comparison.

### Branch-inventory evidence-path migration

The first final-state check correctly failed closed because `branch_inventory`
still scanned the two legacy paths and therefore saw each shim's `__all__`
rather than the 24 implementation symbols. Work stopped under the protocol.
The subsequent ruling classified the fix as a gate evidence-path migration,
not a predicate change. Exactly two `MODULES` paths and the matching two JSON
`source` fields now point to `tizen-triage-report`; selector logic, branch-ID
rules, subset checks, `EXTERNAL_BRANCH` bindings, and uniqueness checks are
byte-unchanged. The tool no longer contains either legacy source path.

Final output exactly matches the pre-freeze run:

```text
PARSER_ONLY | 24/24 | missing=0 | extra=0 | OWNER_MISMATCH=0 | OK
BRANCH_TABLE | rows=25 | referenced_ids=62 | unreferenced_ids=7 | external_rows=2 | OK
MODULE | gbs_report | decision_points=19 | terminal_outcomes=24 | ids=43 | unique=YES
MODULE | report | decision_points=22 | terminal_outcomes=4 | ids=26 | unique=YES
SUMMARY | modules=2 | ids=69 | collisions=0 | unknown_refs=0 | missing_reasons=0 | OK
exit=0

ADMISSION | HANDWRITTEN_BOOL_COUNT | DRIFT
ADMISSION | MISSING_V17_REVISION_BLOCK | DRIFT
ADMISSION | snapshot=v1.7 | required=2/2 | RED_AS_EXPECTED
exit=1
```

The cross-batch template now records that any gate enumerating implementation
AST/source must migrate its scan path in the same commit as the implementation,
alongside declared-consumer and bridge-path synchronization.

### Baseline preservation and verification

The collected-nodeid sets were compared directly. All 913 baseline cases remain
and the two package-surface/wiring tests are the only additions:

```text
before=913
after=915
missing=0
added=2
tests/unit/test_ci_triage.py::test_triage_report_legacy_shims_preserve_all_symbol_identities
tests/unit/test_ci_triage.py::test_triage_report_package_root_exports_only_public_api

$ pytest -q
914 passed, 1 skipped in 18.86s

$ mypy tizen-triage-report/scripts/tizen_triage_report
Success: no issues found in 3 source files

$ ruff check <commit-A Python files>
All checks passed!

$ python3 -m py_compile <five new/shim module files>
exit=0
```

All three drift ledgers remain green:

```text
skill-4: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=22
skill-5: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=8
skill-6: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=5
```

`docs/clang-fix-campaign/design.md` and `release-v1.4.0/` have zero task diff.

## Commit B: test ownership and branch matrix

Status: COMPLETE, pending commit and independent review.

### Test ownership and baseline preservation

The seven existing pure triage-report tests moved from `test_ci_triage.py` to
`test_tizen_triage_report.py`. Their function ASTs are unchanged; orchestration
coverage remains in `test_ci_triage.py`, while legacy wiring identity stays in
the final section of the new skill-owned file. The 27 delta tests cover the
frozen branch table and report renderer.

```text
$ <AST comparison of HEAD tests against the worktree>
baseline_test_functions=784
current_test_functions=811
missing_function_names=[]
added_function_count=27
moved_tests_ast_equal=7/7

$ pytest --collect-only -q
942 tests collected in 0.24s

$ pytest -q tests/unit/test_tizen_triage_report.py tests/unit/test_ci_triage.py
88 passed in 0.11s

$ pytest -q
941 passed, 1 skipped in 18.79s
```

The B-stage test commands used an explicit temporary `PYTHONPATH` containing:

```text
tizen-ci-shared/scripts
tizen-ci-triage/scripts
tizen-convergence-judge/scripts
tizen-qb-discover/scripts
tizen-gerrit-fetch/scripts
tizen-build-verify/scripts
tizen-gerrit-submit/scripts
tizen-triage-report/scripts
tizen-gbs-log-analysis/scripts
tizen-gbs-patch-suggest/scripts
tizen-gbs-build/scripts
```

This remains test scaffolding; commit C owns the installed three-entry delivery
surface for `tizen-triage-report`.

### Four render fixtures and branch-table closure

The nested renderer conditions remain four independent fixtures:

| fixture | test | frozen sides |
|---|---|---|
| A, all optional fields present | `test_render_report_fixture_a_all_optional_fields_present` | ordinary true sides, nested true sides, outer `:53/:70` false sides |
| B, all optional fields absent | `test_render_report_fixture_b_all_optional_fields_absent` | ordinary false sides and outer `:53/:70` true sides only |
| C, outer present and inner absent | `test_render_report_fixture_c_outer_present_inner_absent` | `:62/:77/:85` false sides |
| D, middle present and leaf absent | `test_render_report_fixture_d_middle_present_leaf_absent` | `:81/:83` false sides |

The malformed-row contract has five inputs for four `None` exits: short cells,
empty `spec_name`, header-row `spec_name`, missing status anchor, and unknown
status. The two line-317 BoolOp operands therefore have distinct tests. The
class-priority fixture uses `class_names=("failed",)` with text `Succeeded`, so
a text-first implementation would fail. Both login-state fixtures assert
`QuickBuildError.code == "COOKIE_EXPIRED"`. The arch pair uses the same raw
`standard-armv7l` value; the success case first proves packages are non-empty,
then checks the URL, report arch, and every package arch, while the missing
iframe case checks the raw arch in `str(QuickBuildError)`.

The frozen section 5 table now names only collected tests:

```text
branch_rows=25
test_functions=34
rows_with_existing_tests=25/25
missing=[]
```

### Version-pinned A0 rerun

The updated frozen body is byte-identical to both history snapshots and has
SHA-256 `b7af458a505c47c28a9fecf038e1f9e28590dc4ba806d2ec6fe164c0419a9930`.
The skill-6 ledger was regenerated from the version corpus, then checked; the
branch inventory data records the same design SHA.

```text
$ design_drift_ledger.py --data design_drift_ledger.skill6.json bootstrap
BOOTSTRAP | candidates=57 retained=56 ignored=1 binding_candidates=435 bindings=5

$ design_drift_ledger.py --data design_drift_ledger.skill6.json check
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=57 | retained=56 | ignored=1 | bindings=5 | binding_candidates=435
exit=0

$ branch_inventory.py parser-only
PARSER_ONLY | 24/24 | missing=0 | extra=0 | OWNER_MISMATCH=0 | OK
exit=0

$ branch_inventory.py check
PARSER_ONLY | 24/24 | missing=0 | extra=0 | OWNER_MISMATCH=0 | OK
BRANCH_TABLE | rows=25 | referenced_ids=62 | unreferenced_ids=7 | external_rows=2 | OK
MODULE | gbs_report | decision_points=19 | terminal_outcomes=24 | ids=43 | unique=YES
MODULE | report | decision_points=22 | terminal_outcomes=4 | ids=26 | unique=YES
SUMMARY | modules=2 | ids=69 | collisions=0 | unknown_refs=0 | missing_reasons=0 | OK
exit=0

$ branch_inventory.py admission-v17
ADMISSION | HANDWRITTEN_BOOL_COUNT | DRIFT
ADMISSION | MISSING_V17_REVISION_BLOCK | DRIFT
ADMISSION | snapshot=v1.7 | required=2/2 | RED_AS_EXPECTED
exit=1
```

The inherited skill-4 and skill-5 ledger checks remain green:

```text
skill-4: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=22
skill-5: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=8
```

### Static and scope checks

```text
$ mypy tests/unit/test_tizen_triage_report.py
Success: no issues found in 1 source file

$ ruff check tests/unit/test_tizen_triage_report.py tests/unit/test_ci_triage.py
All checks passed!

$ python3 -m py_compile tests/unit/test_tizen_triage_report.py
exit=0

$ git diff --name-only -- tizen-*/scripts/
(no output)
```

Production code, the P4.5 `design.md`, and `release-v1.4.0/` have zero task
diff. The observed `QuickBuildError` interface exposes its message through
`str(error)`, not a `.message` attribute; the frozen requirement is satisfied
through that public exception representation without any production change.
