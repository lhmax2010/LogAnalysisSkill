# P4.9 skill-4 build-verify progress

## A0 design drift ledger

Status: COMPLETE, awaiting independent review before the design freeze.

Authority under test:
`docs/clang-fix-campaign/p49-skill4-build-verify-design-v1.12.1-FROZEN.md`.

The A0 precondition ruling is applied directly to the frozen body:

- checked scope is every normative section except the revision block, section
  5.4, and section 5.5;
- `OUT_OF_SCOPE` is a mechanical ignored category whose complete old-line span
  must lie in those exclusions;
- all thirteen source designs, v1.0 through v1.12, are stored under
  `docs/clang-fix-campaign/history/skill4/` and pinned by SHA-256 in the data
  file.

The target design SHA-256 recorded by the data file is
`c0f730ab378b97b1f0a5483e508c9003d864248c7225db2405c71e955f618408`.
The v1.12 frozen design and its corpus copy are byte-identical (`cmp` exit 0).

### First baseline generation

Command:

```text
python3 docs/clang-fix-campaign/tools/design_drift_ledger.py bootstrap \
  --data docs/clang-fix-campaign/tools/design_drift_ledger.json
```

Result (`exit 0`):

```text
BOOTSTRAP | candidates=128 retained=81 ignored=47 binding_candidates=1410 bindings=22
```

The generated candidate ledger is
`docs/clang-fix-campaign/tools/design_drift_ledger.json`. Its reverse-gate
partition is 81 retained regression patterns and 47 mechanically ignored
`OUT_OF_SCOPE` spans. There are no hand-added patterns. The binding exporter
produced a conservative cross-product superset of every changed definition
section with every DoD/section reference; 22 reviewed bindings were retained
and the remainder are explicitly present in `ignored_binding_candidates`.

Full output: [bootstrap.txt](a0-evidence/bootstrap.txt).

### Frozen-design gates

Command:

```text
python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
  --data docs/clang-fix-campaign/tools/design_drift_ledger.json
```

Result (`exit 0`):

```text
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=128 | retained=81 | ignored=47 | bindings=22 | binding_candidates=1410
```

The check independently parses every raw diff deletion line, then compares
that external line set with the candidate spans. It also verifies the exact
candidate partition, replay counts and checked sections, frozen target match
counts, complete binding-candidate partition, and the DoD binding or
`PROCESS_ONLY` partition.

Full output, including all 128 candidates and 22 bindings:
[check.txt](a0-evidence/check.txt).

### Admission falsification

Command:

```text
python3 docs/clang-fix-campaign/tools/design_drift_ledger.py admission-v19 \
  --data docs/clang-fix-campaign/tools/design_drift_ledger.json
```

Result: expected `exit 1`. It reports three historical drifts and includes both
required known defects:

```text
BINDING_DRIFT | B-RAW-DIFF | binding B-RAW-DIFF reference selector did not match v1.9
BINDING_DRIFT | B-X-PRESERVE | missing_definition=[], missing_reference=['X 原样保留']
ADMISSION_V19 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
```

Full output: [admission-v19.txt](a0-evidence/admission-v19.txt).

### Per-binding falsification

All 22 bindings were run independently with `negative-binding <binding-id>`.
Every command returned expected `exit 1`; no command returned 0 or 2.
For each `TEXT_CONTAINS` binding, every registered carrying snippet was
removed. Every `COUNT_EQUAL` binding rejected numeral deletion, numeral
change, and a selector-covered definition mutation while accepting a
selector-external interference mutation. The `REF_ONLY` binding rejected both
a restated carrying clause and a reference to another existing section.

Full commands, mutation outcomes, and all 22 exit codes:
[binding-negatives.txt](a0-evidence/binding-negatives.txt).

### OUT_OF_SCOPE anti-abuse falsification

Every one of the 47 `OUT_OF_SCOPE` ledger items was independently changed to
point at an in-scope old line. Every item returned gate exit 1; the aggregate
command returned expected `exit 1`:

```text
OUT_OF_SCOPE_SUMMARY | items=47 | RED_AS_EXPECTED
exit=1
```

Full per-item output:
[out-of-scope-negative.txt](a0-evidence/out-of-scope-negative.txt).

### Implementation findings

Two parser defects were found by running the gate rather than reasoning about
it and were corrected before recording the evidence above:

1. A zero-context diff hunk can cross a revision/body or top-level section
   boundary. Candidate export now splits the deleted side at each scope
   boundary while preserving the raw new-side span as provenance. Otherwise a
   checked pattern spanning two separately scanned sections has a false replay
   count of zero.
2. Once inside a hunk, a Markdown content line beginning with `---` or `+++` is
   a deletion/addition, not a diff file header. Header filtering now relies on
   hunk state, so the independent raw-deletion anchor cannot silently lose
   horizontal-rule lines.

Neither correction changes the design or weakens a predicate. Both make the
raw-diff external anchor account for the bytes Git actually reports.

### Regression and tool quality

```text
$ .venv/bin/pytest -q
883 passed, 1 skipped in 17.52s

$ .venv/bin/mypy
Success: no issues found in 105 source files

$ .venv/bin/lint-imports
Contracts: 6 kept, 0 broken.

$ .venv/bin/ruff check <all tracked Python files> \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
All checks passed!

$ python3 -m py_compile \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
exit=0
```

Running `ruff check .` also sees the pre-existing untracked root file
`audit_four_sigs.py` and reports its existing compact-style violations. That
unrelated file is outside A0 and was not modified or staged. The complete
tracked Python surface plus the new ledger script is green under the same Ruff
configuration.

Bootstrap determinism was checked by hashing the data file before and after a
second generation:

```text
bootstrap_sha_before=ebafd3f176530a99fe6ff82376866c02601b792da5a1145a2d52cabf76e0d2ff
bootstrap_sha_after=ebafd3f176530a99fe6ff82376866c02601b792da5a1145a2d52cabf76e0d2ff
deterministic=yes
```

## v1.12 freeze stamping

The canonical design and the v1.12 corpus entry were originally frozen under
the v1.12 filename. Their byte content was equal (`cmp` exit 0), and that
frozen design SHA-256 was
`c0f730ab378b97b1f0a5483e508c9003d864248c7225db2405c71e955f618408`.
The ledger `target_design`, `generated_from`, corpus path, and SHA were rebuilt
from that frozen path; bootstrap retained the reviewed inventory:

```text
BOOTSTRAP | candidates=128 retained=81 ignored=47 binding_candidates=1410 bindings=22
```

The four freeze checks completed as follows:

```text
APPENDIX_SUMMARY | 4/4 PASS
COUNT_SUMMARY | 10/10 PASS
CONTRACT_TEST_SUMMARY | contracts=13 | mapped_rows=13 | unmapped=0 | PASS
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=128 | retained=81 | ignored=47 | bindings=22 | binding_candidates=1410
ADMISSION_V19 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
```

The v1.9 admission command returned expected exit 1 and included both required
historical defects, `B-RAW-DIFF` and `B-X-PRESERVE`. The frozen-design check
returned exit 0. The appendix check reconciled the four declaration clauses;
the count check covered the authority total and 29/12/4 split, three migration
modes, four exception negatives, ten mechanical-sync items, eight twins,
thirteen contract/test rows, and seventeen DoD items.

## Commit A: three-mode extraction

### v1.12.1-FROZEN post-stamp revision 1

The first targeted post-shim run exposed a Python name-resolution conflict in
the frozen test-edit wording: the required package-root `build_verify`
function shadows the same-named implementation submodule, so pytest cannot
resolve a string target such as
`tizen_build_verify.build_verify._analyze_failure`. Per the explicit ruling,
the authority and corpus snapshot were renamed to v1.12.1-FROZEN; six listed
patches now obtain the authoritative module with `importlib.import_module` and
pass that object to `monkeypatch.setattr`. The public package contract is
unchanged.

The ledger bootstrap keeps the established thirteen-node logical corpus
v1.0..v1.12 while pointing its final node at the in-place v1.12.1 artifact.
Only that terminal-path lookup changed in the tool; predicates are unchanged.
The canonical design and history snapshot compare byte-for-byte:

```text
$ cmp p49-skill4-build-verify-design-v1.12.1-FROZEN.md \
    history/skill4/p49-skill4-build-verify-design-v1.12.1-FROZEN.md
exit 0
```

A0 was rebuilt because the checked text changed:

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/design_drift_ledger.py bootstrap \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
BOOTSTRAP | candidates=129 retained=82 ignored=47 binding_candidates=1410 bindings=22
exit 0

$ .venv/bin/python docs/clang-fix-campaign/tools/design_drift_ledger.py check \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=129 | retained=82 | ignored=47 | bindings=22 | binding_candidates=1410
exit 0

$ .venv/bin/python docs/clang-fix-campaign/tools/design_drift_ledger.py admission-v19 \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
BINDING_DRIFT | B-CORPUS-REFERENCE | missing_definition=['每一相邻版本对做原始 git diff'], leaked_snippets=[], parsed_targets=['§5.4.4'], expected=§5.4.4
BINDING_DRIFT | B-RAW-DIFF | binding B-RAW-DIFF reference selector did not match v1.9
BINDING_DRIFT | B-X-PRESERVE | missing_definition=[], missing_reference=['X 原样保留']
ADMISSION_V19 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
exit 1 (expected)
```

### Pre-shim source evidence

The three skill files were created while all legacy modules were still
independent implementations. Initial byte comparisons all returned exit 0:

```text
cmp ci_triage/verify/build_verify.py tizen_build_verify/build_verify.py: exit 0
cmp ci_triage/verify/edit_spec_guard.py tizen_build_verify/edit_spec_guard.py: exit 0
cmp ci_triage/verify/workspace.py tizen_build_verify/workspace.py: exit 0
```

The build-verify copy was then changed only at the three frozen whitelist
locations: the edit-spec import, the workspace import, and
`default_extra_pythonpath`'s `parents[2]` to `parents[1]` anchor. The workspace
copy retained byte-identical AST source segments for its four owned
definitions and replaced the old 17-name compatibility header with exactly
the nine shared bindings in S9. The edit-spec copy remained byte-identical.

### Pre-shim behavioral parity

The parity run occurred before any legacy module was replaced by a shim. It
used `importlib.reload` to load distinct old and new module objects, fixed UUID
and shared-workspace UTC sources, exported fixed Git author/committer dates,
and replaced formatter `TemporaryDirectory` with one deterministic directory.
The only normalizer mask replaced each run's destination root in named result
path fields, individual argv elements, marker path fields, and symlink target
fields; no payload-wide string replacement was used. DB rows were not part of
the payload, so the independent state DB clock was outside the comparison.

Temporary B-stage roots used by the command:

```text
PYTHONPATH=$PWD/tizen-build-verify/scripts:$PWD/tizen-ci-shared/scripts:$PWD/tizen-ci-triage/scripts:$PWD/tizen-gbs-log-analysis/scripts:$PWD/tizen-gbs-patch-suggest/scripts:$PWD/tizen-gbs-build/scripts:$PWD/tizen-convergence-judge/scripts:$PWD/tizen-qb-discover/scripts:$PWD/tizen-gerrit-fetch/scripts
GIT_AUTHOR_DATE=2000-01-01T00:00:00+00:00
GIT_COMMITTER_DATE=2000-01-01T00:00:00+00:00
```

Actual output (`exit 0`):

```text
old_module=.../tizen-ci-triage/scripts/ci_triage/verify/build_verify.py
new_module=.../tizen-build-verify/scripts/tizen_build_verify/build_verify.py
isolation=importlib.reload distinct_modules=True
field_equal[result]=True
field_equal[runner_trace]=True
field_equal[destination_tree]=True
field_equal[default_extra_pythonpath]=True
field_equal[controlled_environment]=True
default_extra_pythonpath_nonempty=True
payload_sha256=375af83385970d797523956485d3e1b81cda8933273af698895be49d50883c8e
normalizer_positive_destination_only=True
normalizer_negative[failure_class]=True
normalizer_negative[command_order]=True
normalizer_negative[repair_allowed]=True
```

The payload's five sections are the complete `BuildVerifyResult`, ordered fake
runner argv/timeout trace, normalized destination tree plus workdir/protected
stage markers, ordered `default_extra_pythonpath` tuple, and the explicitly
controlled environment fields (`PYTHONPATH`, `GIT_AUTHOR_DATE`, and
`GIT_COMMITTER_DATE`). The three negative mutations were all outside path
fields.

### Three migration modes after wiring

Mode 2's external zero-context diff contains only the frozen three changes:

```diff
@@ -41,2 +41,2 @@
-from ci_triage.verify.edit_spec_guard import EditSpecViolation, validate_edit_spec
-from ci_triage.verify.workspace import (
+from tizen_build_verify.edit_spec_guard import EditSpecViolation, validate_edit_spec
+from tizen_build_verify.workspace import (
@@ -635 +635 @@
-        launcher_path=Path(__file__).resolve().parents[2] / "run_ci_triage.py"
+        launcher_path=Path(__file__).resolve().parents[1] / "run_ci_triage.py"
```

The mode-specific mechanical checker returned exit 0:

```text
MODE1_CMP_EQUAL=True
MODE3_DEFINITION_SET_EXACT=True
MODE3_SEGMENT_EQUAL[DEFAULT_MIN_FREE_BYTES]=True
MODE3_SEGMENT_EQUAL[_copy_repository]=True
MODE3_SEGMENT_EQUAL[check_disk_and_maybe_cleanup]=True
MODE3_SEGMENT_EQUAL[create_worktree]=True
MODE3_CHANGED_HUNKS_HEADER_ONLY=True old_first_def=39 new_first_def=29
MODE3_S9_EXACT=True count=9
MODE3_S9_ALIASES=[]
MODE3_PACKAGE_ROOT_S9_LEAKS=[]
```

A semantic-comment scan of all three skill copies found no inherited `shim`,
`removed at`, `legacy`, or `ci_triage.verify` annotation. Their existing
module/function comments continue to describe the moved implementation.

### Shim and consumer wiring

The build-verify and edit-spec old locations are pure re-export shims. The old
workspace location is a combination shim with exactly 17 shared bindings and
four skill bindings. An AST/grep check reported:

```text
LEGACY_SHIM_ZERO_DEF_CLASS=True
WORKSPACE_SHIM_SHARED_COUNT=17
WORKSPACE_SHIM_SKILL_COUNT=4
rg_def_class_exit=1 (no matches)
```

All six monkeypatch calls listed by v1.12.1 revision 1 now patch the module
object returned by
`importlib.import_module("tizen_build_verify.build_verify")`. The targeted
unit/integration set passed:

```text
109 passed, 1 skipped in 3.98s
```

Permanent tests cover the ordered/nonempty Python-path equivalence, all 45
migrated symbol identities plus the 17 shared workspace identities, the exact
nine-name package `__all__`, and absence of every S9 symbol from the package
root.

### Baseline preservation and gates

A detached HEAD worktree supplied the pre-change collection. Comparing sorted
nodeids against the working tree produced:

```text
baseline_nodeids=884
current_nodeids=887
missing_baseline_nodeids=0
new_nodeids=3
tests/unit/test_build_verify.py::test_default_extra_pythonpath_matches_legacy_anchor_and_is_nonempty
tests/unit/test_build_verify.py::test_legacy_shims_preserve_all_migrated_symbol_identities
tests/unit/test_build_verify.py::test_package_root_exports_only_public_contract_and_not_workspace_s9
```

The baseline was `883 passed, 1 skipped`; commit A establishes the new total:

```text
886 passed, 1 skipped in 17.80s
SKIPPED [1] tests/unit/test_edit_spec_guard.py:97: case-sensitive filesystem
```

Temporary B-stage execution used all repository `*/scripts` roots, including
`$PWD/tizen-build-verify/scripts`, in both `PYTHONPATH` and `MYPYPATH` where
applicable. Packaging/README/CI registration remains deferred to commit C.

```text
mypy configured surface: Success: no issues found in 105 source files
mypy tizen_build_verify: Success: no issues found in 4 source files
ruff tracked Python plus tizen_build_verify: All checks passed!
py_compile changed Python surface: exit 0
lint-imports: Contracts: 6 kept, 0 broken.
```

The final design-gate replay remained pinned to v1.12.1:

```text
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=129 | retained=82 | ignored=47 | bindings=22 | binding_candidates=1410
check_exit=0
ADMISSION_V19 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
admission_exit=1 (expected)
```

`git diff --stat` and `git status` scoped to `gbs_report.py`, the P4.5
`design.md`, and `release-v1.4.0/` were empty. No production behavior changed
outside the three frozen mode-2 lines, the mode-3 import header, compatibility
shims, and direct consumer imports.
