# P4.9 skill-5 gerrit-submit progress

## A0 inherited design drift ledger

Status: COMPLETE, awaiting independent review before extraction commit A.

Authority under test:
`docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3-FROZEN.md`
at freeze commit `f2bc050`.

### Parameterization

`design_drift_ledger.py` no longer embeds a skill-4 corpus directory, version
sequence, draft-name pattern, frozen target, admission snapshot, or required
binding IDs. Each data file now supplies:

- `corpus_dir`, `version_sequence`, and the exact `version_files` mapping;
- `target_design`, `target_version`, and generated target SHA-256;
- `excluded_sections` and `dod_section`;
- `admission.snapshot_version`, `minimum_drift_count`, and `required`;
- existing wrong-section targets used by each `REF_ONLY` negative fixture.

The skill-4 data remains
`docs/clang-fix-campaign/tools/design_drift_ledger.json`. Skill-5 has the
independent data file
`docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json`; bootstrap does
not overwrite the skill-4 file.

### Skill-4 non-regression

The shared execution path was checked against every inherited positive and
negative gate.

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=130 | retained=83 | ignored=47 | bindings=22 | binding_candidates=1410
exit=0

$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py admission-v19 \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
ADMISSION_V19 | snapshot=v1.9 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
exit=1

$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py \
    negative-fixture out-of-scope-misuse \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
OUT_OF_SCOPE_SUMMARY | items=47 | RED_AS_EXPECTED
exit=1

$ for each of 22 binding IDs: ... negative-binding <id> --data <skill4-data>
NEGATIVE_BINDING_SUMMARY | bindings=22 | unexpected=0
each exit=1
```

Full outputs and every exit code:

- [skill4-check.txt](a0-evidence/skill4-check.txt)
- [skill4-admission-v19.txt](a0-evidence/skill4-admission-v19.txt)
- [skill4-out-of-scope-negative.txt](a0-evidence/skill4-out-of-scope-negative.txt)
- [skill4-binding-negatives.txt](a0-evidence/skill4-binding-negatives.txt)

The generic `REF_ONLY` negative fixture selects an existing wrong section from
the data file rather than a skill-4 section hardcode. All 22 inherited fixtures
still fail for their intended reasons.

### Skill-5 corpus and gates

The Git-anchored corpus contains the continuous sequence v1.0, v1.1, v1.2,
and v1.3-FROZEN under `history/skill5/`.

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py bootstrap \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
BOOTSTRAP | candidates=34 retained=30 ignored=4 binding_candidates=348 bindings=8
exit=0

$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=34 | retained=30 | ignored=4 | bindings=8 | binding_candidates=348
exit=0
```

The eight forward bindings cover the branch-table contract, fabricated branch
removal, timeout's two observed paths in both section 4 and the DoD, the
section 3.2 result mapping, the private-member count, gate-member expansion,
and the three negative controls. Every DoD is either bound or explicitly
registered as `PROCESS_ONLY`.

Full outputs:

- [skill5-bootstrap.txt](a0-evidence/skill5-bootstrap.txt)
- [skill5-check.txt](a0-evidence/skill5-check.txt)

Bootstrap is deterministic:

```text
before=da1db91465d58031a1ade170d9d9f9aeb5c7c152f31f07ebb0952252bb9cf7c8
after=da1db91465d58031a1ade170d9d9f9aeb5c7c152f31f07ebb0952252bb9cf7c8
deterministic=yes
```

### v1.2 admission falsification

The selected snapshot is v1.2. Its required set contains exactly the two
defects proved to exist in that snapshot:

```text
246:  推送成功 / 推送失败 / 目标 HEAD 未知警告(:185)/ verification 不匹配
251:  skill-3 N2 教训);②`TimeoutExpired` **原样传播**(不归一化);
```

The admission run returns expected exit 1 and includes both required binding
IDs, `B-BRANCH-FABRICATION` and `B-TIMEOUT-TWO-PATHS`:

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py admission \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
BINDING_DRIFT | B-BRANCH-FABRICATION | missing_definition=['本 skill 不执行 push', '推送成功/失败'], leaked_snippets=[], parsed_targets=[], expected=§4
BINDING_DRIFT | B-TIMEOUT-TWO-PATHS | missing_definition=[], missing_reference=['_run_git', 'ls-remote']
ADMISSION | snapshot=v1.2 | BINDING_DRIFT=7 | required_known=2 | RED_AS_EXPECTED
exit=1
```

The five additional drifts are valid but are not part of the required set.
Full evidence:

- [admission-v12-required-presence.txt](a0-evidence/admission-v12-required-presence.txt)
- [skill5-admission-v12.txt](a0-evidence/skill5-admission-v12.txt)

### Member-count reverse ledger

The v1.1 `6 -> 7` member-count error is deliberately not an admission required
item because it does not exist in the selected v1.2 snapshot. The reverse
ledger independently retains the v1.1-to-v1.2 deletion:

```text
matching_retained_candidates=1
candidate_id=v1.1|old:145-145,new:167-167|e8557589352edbd8e91510a8a5a4014525249827d095586b77fc7c7bb9a3369c
recorded_replay_count=1
v1.1_matches=1 sections={'§2': 1}
v1.2_matches=0 sections={}
v1.3_matches=0 sections={}
```

Full evidence:
[member-count-reverse-ledger.txt](a0-evidence/member-count-reverse-ledger.txt).

### Per-item falsification

```text
$ ... negative-fixture out-of-scope-misuse --data <skill5-data>
OUT_OF_SCOPE_SUMMARY | items=4 | RED_AS_EXPECTED
exit=1

$ for each of 8 binding IDs: ... negative-binding <id> --data <skill5-data>
NEGATIVE_BINDING_SUMMARY | bindings=8 | unexpected=0
each exit=1
```

Full mutation output and exit codes:

- [skill5-out-of-scope-negative.txt](a0-evidence/skill5-out-of-scope-negative.txt)
- [skill5-binding-negatives.txt](a0-evidence/skill5-binding-negatives.txt)

### Cross-batch rule

The skill batch template now states that every admission required item must be
proved present in the selected snapshot. Defects that exist only in another
version belong to the reverse ledger, not to admission.

### Regression and tool quality

```text
$ .venv/bin/pytest -q
897 passed, 1 skipped in 18.41s

$ .venv/bin/mypy
Success: no issues found in 109 source files

$ python3 -m py_compile \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
exit=0

$ .venv/bin/ruff check \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
All checks passed!
```

The first Ruff pass found one 102-character generic error message introduced
by parameterization. It was split across lines without changing behavior; the
recorded final command above is green.

## Commit A: mode-one extraction and pre-shim parity

Status: COMPLETE, pending commit and independent review.

Authority:
`docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3-FROZEN.md`
at `f2bc050`; A0 gate commit `31a91cb`.

### Migration and source identity

The implementation was copied while the legacy module was still an independent
implementation. The pre-shim comparison was empty. After installing the shim,
the same result remains independently reproducible from the Git-anchored source:

```text
$ git show HEAD:tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py \
    > /tmp/skill5-gerrit-submit-before.py
$ cmp /tmp/skill5-gerrit-submit-before.py \
    tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py
(no output)
CMP_EXIT=0
$ sha256sum /tmp/skill5-gerrit-submit-before.py \
    tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py
ead701d0e943f395225729be5daef94f53912002d97534f2309cc264e037107f  /tmp/skill5-gerrit-submit-before.py
ead701d0e943f395225729be5daef94f53912002d97534f2309cc264e037107f  tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py
```

AST inventory of the skill copy:

```text
top_level_migration_symbols=23
SubprocessRunner,GerritSubmitOptions,GerritSubmitResult,ReleaseWorktreeResult,gerrit_submit,_target_head_unknown_warning,release_verified_worktree,write_gerrit_submit_result,write_release_result,exit_code_for_submit,exit_code_for_release,_verification_mismatch,_dirty_reason,_target_warnings,_target_branch,_push_command,_remote_url,_git_stdout,_run_git,_result,_record_result,_build_id_from_failure_key,_subprocess_env
```

The inherited module docstring and comments remain accurate in the skill copy.
There are no inherited `shim`, `temporary`, or deletion comments whose meaning
reversed after migration:

```text
$ rg -n 'P4\.9 shim|removed at|temporary|delete at|will be deleted' \
    tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py
(no output)
exit=1
```

### B-stage scaffolding

No project/package entrypoint was changed in commit A. The temporary
`PYTHONPATH` and `MYPYPATH` used for tests and checks contained these script
roots, in this order:

```text
$PWD/tizen-gerrit-submit/scripts
$PWD/tizen-ci-shared/scripts
$PWD/tizen-ci-triage/scripts
$PWD/tizen-gbs-log-analysis/scripts
$PWD/tizen-gbs-patch-suggest/scripts
$PWD/tizen-gbs-build/scripts
$PWD/tizen-convergence-judge/scripts
$PWD/tizen-qb-discover/scripts
$PWD/tizen-gerrit-fetch/scripts
$PWD/tizen-build-verify/scripts
```

This is extraction scaffolding only. The three installation entrypoints remain
commit C work.

### Pre-shim parity

Volatile-source discovery was run against this module rather than copied from a
previous skill:

```text
$ rg -n 'uuid|datetime|\btime\b|random' \
    tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py
(no output)
exit=1
```

No volatile source exists in this module, so no freeze was needed. Before the
legacy file became a shim, the old and new implementations were loaded as
distinct module objects and explicitly reloaded. Independent state databases,
worktrees, protected markers, and fake runners were used. The fake runner
observed five ordered calls across submit and release.

The payload has exactly five partitions:

1. every field of both result objects, including null fields;
2. ordered fake-runner argv and kwargs traces;
3. worktree, symlink, and protected-marker state before submit, after submit,
   and after release;
4. controlled environment inputs `PYTHONPATH` and `GIT_SSH_COMMAND` only;
5. submit and release exit codes.

Masking was applied only to named path carriers: result command tokens,
`command_argv` elements, release `worktree_path`, runner argv elements, and the
symlink target. No payload-wide replacement was used. Full evidence is in
[pre-shim-parity.txt](commit-a-evidence/pre-shim-parity.txt).

```text
isolation.importlib_reload=True
isolation.distinct_modules=True
isolation.distinct_functions=True
field_equal[result_objects]=True
field_equal[runner_trace]=True
field_equal[worktree_marker_state]=True
field_equal[controlled_environment]=True
field_equal[exit_codes]=True
payload_equal=True
old_sha256=b0f5a5dcdec7d25afd72737e0ca12e34a00ee06a0108867f1d5c9fb4baf14d40
new_sha256=b0f5a5dcdec7d25afd72737e0ca12e34a00ee06a0108867f1d5c9fb4baf14d40
mask_scope=result.command tokens,result.command_argv elements,release.worktree_path,runner argv elements,symlink target
payload_wide_replacement=False
runner_calls=5
normalizer_positive.destination_only=True
normalizer_negative.action=True
normalizer_negative.command_order=True
normalizer_negative.exit_code=True
exit_code=0
COMMAND_EXIT=0
```

The positive fixture changes destination paths only and normalizes equal. The
three negative fixtures independently change `action`, command order, and an
exit code outside masked path content; each compares unequal.

### Shim, consumers, and package API

The only production consumer was and remains the CLI. It now imports the seven
consumed public symbols directly from `tizen_gerrit_submit`. The two public
result types have no production consumer. Test imports were flipped directly;
there were no string monkeypatch targets to rewrite.

```text
OLD_SHIM_DEF_CLASS_COUNT=0
VERIFY_INIT_GERRIT_SUBMIT_COUNT=0
PRODUCTION_DIRECT_CONSUMERS
tizen-ci-triage/scripts/ci_triage/cli.py
LEGACY_IMPORTS_OUTSIDE_SHIM_AND_EVIDENCE
(no output)
```

The package root exports exactly nine public symbols. Its fourteen internal
symbols remain absent, while the compatibility module re-exports all 23
migration symbols by object identity:

```text
root_all_count=9
root_all_exact=True
public_identity=True
internal_absent=True
post_shim_identity_9_plus_14=True
```

`tests/unit/test_gerrit_submit.py` contains the package-surface and post-shim
identity assertions. Post-shim identity is wiring evidence only; it does not
replace the pre-shim behavioral comparison above.

### Baseline preservation and verification

Collection was compared before and after the test additions:

```text
COLLECT_EXIT=0
BEFORE=898
AFTER=900
MISSING_BASELINE=0
ADDED=2
tests/unit/test_gerrit_submit.py::test_legacy_shim_preserves_all_symbol_identities
tests/unit/test_gerrit_submit.py::test_package_root_exports_only_public_api
```

All 898 baseline nodeids remain collected. The new actual baseline is 899
passed and one skipped:

```text
$ pytest -q
899 passed, 1 skipped in 18.43s

$ pytest -q tests/unit/test_gerrit_submit.py \
    tests/integration/test_gerrit_submit_real_git.py \
    tests/unit/test_ci_triage_entrypoints.py
40 passed in 1.15s
```

Static and architecture checks:

```text
$ mypy
Success: no issues found in 109 source files
$ mypy tizen-gerrit-submit/scripts/tizen_gerrit_submit
Success: no issues found in 2 source files
$ ruff check <commit-A Python surface>
All checks passed!
$ python -m py_compile <commit-A Python surface>
PY_COMPILE_EXIT=0
$ lint-imports
Contracts: 6 kept, 0 broken.
```

Both inherited design ledgers remain green:

```text
skill-4: SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=130 | retained=83 | ignored=47 | bindings=22 | binding_candidates=1410
skill-5: SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=34 | retained=30 | ignored=4 | bindings=8 | binding_candidates=348
```

Restricted surfaces are untouched:

```text
$ git diff --name-only HEAD -- \
    tizen-ci-triage/scripts/ci_triage/gbs_report.py \
    docs/clang-fix-campaign/design.md release-v1.4.0
(no output)
```

## Commit B: test ownership, branch matrix, and status locks

Status: COMPLETE, pending commit and independent review.

### Test ownership

`tests/unit/test_gerrit_submit.py` was the legacy owner of 19 test functions.
It was renamed to `tests/unit/test_tizen_gerrit_submit.py`; all 19 function
names remain present. Six delta tests were added for the uncovered frozen
branches and status locks.

The three boundaries are explicit:

- skill behavior and package surface:
  `tests/unit/test_tizen_gerrit_submit.py`;
- orchestration integration: the Gerrit submit/release CLI section in
  `tests/unit/test_ci_triage_entrypoints.py`;
- legacy wiring: the final identity-only section in
  `tests/unit/test_tizen_gerrit_submit.py`.

The real-Git integration tests remain in
`tests/integration/test_gerrit_submit_real_git.py`; they already import the
skill directly and retain their integration marker.

```text
old_test_functions=19
new_test_functions=25
missing_moved_functions=0
new_functions=6
```

### Frozen section 4 branch table

The use-case column was written back to both the authority and its history
snapshot. A parser checked every row against actual top-level test functions:

```text
branch_rows=14
rows_with_use_cases=14
unresolved=0
```

| Frozen branch | Test coverage |
|---|---|
| `record_not_found` | `test_gerrit_submit_record_not_found` |
| `rejected_not_ready`, both entries | `test_gerrit_submit_rejects_latest_non_ready`; `test_gerrit_submit_rejects_ready_for_different_verification_id` |
| `rejected_worktree_missing` | `test_gerrit_submit_rejects_missing_worktree_without_patch_fallback` |
| `rejected_verification_mismatch` | `test_gerrit_submit_rejects_commit_or_tree_mismatch` |
| `rejected_worktree_dirty` | tracked and staged dirty tests |
| `rejected_submit_not_enabled` | `test_gerrit_submit_submit_mode_is_rejected_without_push` |
| `skipped_duplicate` | duplicate and duplicate-before-unverified tests |
| `dry_run` | `test_gerrit_submit_dry_run_returns_command_without_push` |
| `dry_run_unverified_remote` | rc, OSError, TimeoutExpired, not-found, and sandbox tests |
| `_target_warnings` five branches | sandbox, exception, rc, empty output, and drift tests |
| release `record_not_found` | `test_release_verified_worktree_reports_record_not_found` |
| release `released` | `test_release_verified_worktree_removes_protection` |
| release `not_protected` | `test_release_verified_worktree_reports_not_protected` |
| both exit-code functions | `test_exit_code_mappings_cover_success_missing_and_rejected_actions` |

`test_gerrit_submit_dry_run_returns_command_without_push` locks the no-push
contract. The fake runner sees only validation and `ls-remote` calls; the push
argv is constructed in the result but never executed.

### Section 3 current-state locks

Each injection point and assertion is recorded separately:

| Point | Injection/observation | Assertion |
|---|---|---|
| all subprocess paths | `SubmitRunner.calls` records every argv and kwargs pair from both local `_run_git` and remote `ls-remote` paths | both path classes were observed; every kwargs object lacks `timeout`; every executed argv lacks `push` |
| local `_run_git` timeout | runner raises one preconstructed `subprocess.TimeoutExpired` object | `pytest.raises` receives the same object by identity, proving bare propagation |
| remote `ls-remote` timeout | `SubmitRunner` raises `TimeoutExpired` only for `git ls-remote` | action is `dry_run_unverified_remote`; warnings contain exact `target_head_unknown:<exception>` text |
| dangling symlink | existing skill-3 fixture points destination at a missing target | `FileExistsError` propagates; symlink remains; missing target remains absent; runner has only its initial call |

The referenced symlink lock is
`tests/unit/test_gerrit_fetch.py::test_fetch_source_dangling_symlink_propagates_file_exists_error`;
it was not copied or rewritten.

```text
$ pytest -q \
    tests/unit/test_tizen_gerrit_submit.py::test_gerrit_submit_all_subprocess_paths_omit_timeout \
    tests/unit/test_tizen_gerrit_submit.py::test_run_git_propagates_timeout_expired_unchanged \
    tests/unit/test_tizen_gerrit_submit.py::test_gerrit_submit_converts_ls_remote_timeout_to_unverified_warning \
    tests/unit/test_gerrit_fetch.py::test_fetch_source_dangling_symlink_propagates_file_exists_error
4 passed in 0.11s
```

### Frozen-body writeback and A0 rerun

The authority and history snapshot remain byte-identical after the test-name
writeback:

```text
$ cmp <authority> <history-snapshot>
(no output)
CMP_EXIT=0
sha256=e7e490daf680c11f69c8a775edb5573d6afe3dd00214a8df3b7a6244ac9b742f
```

The skill-5 data file was regenerated through the A0 bootstrap command rather
than edited around the gate. Counts did not change; only final-version spans,
captured text, and the Git-external target SHA moved:

```text
$ design_drift_ledger.py bootstrap --data design_drift_ledger.skill5.json
BOOTSTRAP | candidates=34 retained=30 ignored=4 binding_candidates=348 bindings=8

$ design_drift_ledger.py check --data design_drift_ledger.skill5.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=34 | retained=30 | ignored=4 | bindings=8 | binding_candidates=348

$ design_drift_ledger.py admission --data design_drift_ledger.skill5.json
ADMISSION | snapshot=v1.2 | BINDING_DRIFT=7 | required_known=2 | RED_AS_EXPECTED
ADMISSION_EXIT=1
```

All four skill-5 `OUT_OF_SCOPE` misuse fixtures and all eight per-binding
fixtures still turn red for their intended predicates. The inherited skill-4
check also remains green:

```text
OUT_OF_SCOPE_SUMMARY | items=4 | RED_AS_EXPECTED
OUT_OF_SCOPE_NEGATIVE_EXIT=1
NEGATIVE_BINDING_EXIT | B-BRANCH-DOD | 1
NEGATIVE_BINDING_EXIT | B-BRANCH-FABRICATION | 1
NEGATIVE_BINDING_EXIT | B-TIMEOUT-BRANCH-LOCK | 1
NEGATIVE_BINDING_EXIT | B-TIMEOUT-TWO-PATHS | 1
NEGATIVE_BINDING_EXIT | B-RESULT-MAPPING | 1
NEGATIVE_BINDING_EXIT | B-PRIVATE-COUNT | 1
NEGATIVE_BINDING_EXIT | B-GATE-MEMBERS | 1
NEGATIVE_BINDING_EXIT | B-GATE-CONTROLS | 1
skill-4: SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=130 | retained=83 | ignored=47 | bindings=22 | binding_candidates=1410
```

### Baseline and quality gates

Nodeids were compared after normalizing only the deliberate ownership rename:

```text
COLLECT_EXIT=0
BEFORE=900
AFTER=906
MISSING_AFTER_OWNERSHIP_RENAME=0
ADDED=6
```

The commit-A baseline set is intact. The new baseline is 905 passed and one
skipped:

```text
$ pytest -q
905 passed, 1 skipped in 18.60s

$ pytest -q tests/unit/test_tizen_gerrit_submit.py
25 passed in 0.78s

$ ruff check <changed test surface>
All checks passed!
$ python -m py_compile <changed test surface>
exit=0
$ mypy
Success: no issues found in 109 source files
$ lint-imports
Contracts: 6 kept, 0 broken.
```

Production code is unchanged, including all restricted surfaces:

```text
$ git diff --name-only HEAD -- ':(glob)tizen-*/scripts/**'
(no output)
$ git diff --name-only HEAD -- \
    tizen-ci-triage/scripts/ci_triage/gbs_report.py \
    docs/clang-fix-campaign/design.md release-v1.4.0/
(no output)
```
