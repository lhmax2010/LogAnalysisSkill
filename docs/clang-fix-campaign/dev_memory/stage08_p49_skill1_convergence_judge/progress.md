# P4.9 Skill-1 Convergence-Judge Progress

Status: **COMMIT D VALIDATED; READY TO COMMIT**.

- Frozen authority:
  `../../p49-skill1-convergence-judge-design-v1.2-FROZEN.md`.
- Audit record:
  `../../review/p49-skill1-convergence-judge-audit.md`.
- Baseline: step-0 CLOSED at `7e9eb4e`; 846 passed, one skipped.
- Planned implementation commits: A (C21), B (extraction), C (gates/audit).

## Freeze Provenance

The target-machine v1.1 copy and delivered v1.2 differed only by the declared
v1.2 title/provenance update and two residual-wording corrections. The delivered
v1.2 body was used as the freeze source rather than merged with local edits.

## Freeze Evidence

- Canonical/history `cmp`: exit 0, no output.
- Initial v1.2 freeze SHA-256 at commit `d3478ab`:
  `ef0eda37112dfbcd574b5b17d42de264e2270b07462e6d244cdf5e5f4ff0a4a3`.
- Revised v1.3 canonical/history SHA-256:
  `c41427e092a677f45c5cb10a51ccc7dbdaa561459131fe37221e98c62ccb24d0`.
- Residual-wording grep: one hit, line 11, inside the v1.2 revision note.
- Baseline symbol audit: 42 symbol OK + four module-scope OK, zero mismatch,
  zero incomplete.
- Baseline table bridge: 42 symbol OK + four module-scope OK, all difference
  and parse-error counts zero.

## Commit A: C21 Subprocess Anchor

The shared `_subprocess_env()` helper derives the repository root from
`Path(__file__).resolve().parents[2]` and sets an exact five-entry
`PYTHONPATH` for all three CLI subprocess tests in
`tests/unit/test_campaign_repair_step.py`.

Measured path:

```text
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-ci-shared/scripts:/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-ci-triage/scripts:/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-log-analysis/scripts:/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-patch-suggest/scripts:/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-build/scripts
```

Clean-CWD targeted command and result:

```text
cd /tmp && /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/pytest \
  /home/linhao/Toolchain/development/LogAnalysisSkill/tests/unit/test_campaign_repair_step.py \
  -k 'campaign_cli_malformed_args_emit_one_json_and_exit_five or campaign_cli_rejection_emits_one_json_and_exit_four or python_m_campaign_repair_step_emits_one_json_document'
3 passed, 35 deselected in 0.47s
```

Full baseline:

```text
.venv/bin/pytest
846 passed, 1 skipped in 17.69s
.venv/bin/ruff check tests/unit/test_campaign_repair_step.py
All checks passed!
```

## Commit B: Convergence Skill Extraction

Migration proof:

```text
source SHA-256 before copy:
d606f86745c4d57b68a775a393d6adf2ef3c637c9c968cb0aea31ae0906ead3c
cmp old implementation vs new implementation before aliases: exit 0
cmp HEAD implementation vs new implementation without final four lines: exit 0
new-file tail:
primary_fingerprint = _primary_fingerprint
error_count = _error_count
legacy shim def/class count: 0
```

Contract proof:

```text
primary_fingerprint is _primary_fingerprint: True
error_count is _error_count: True
repository definitions:
tizen_convergence_judge/convergence.py:203 def _primary_fingerprint
tizen_convergence_judge/convergence.py:383 def _error_count
```

Validation:

```text
targeted convergence/campaign/entrypoint tests: 71 passed
full suite: 847 passed, 1 skipped in 17.85s
lint-imports: Contracts: 4 kept, 0 broken
mypy: Success: no issues found in 101 source files
changed-path ruff: All checks passed!
py_compile: exit 0
```

The suite count is the unchanged 846/1 baseline plus the required public-alias
identity assertion. A repository-wide local `ruff check .` also saw the
pre-existing untracked `audit_four_sigs.py`; that unrelated file is not staged.
Changed production/test paths pass ruff, and clean-clone CI does not contain the
untracked file.

### Shim Extension

`ci_triage/verify/convergence.py` now re-exports the six public skill symbols
plus the two legacy private bindings, with zero definitions or classes. It is
added to the compatibility-shim ledger and closes in the single P4.9 cleanup
commit after all six skills are extracted.

## v1.3 Audit-Layering Ruling

The frozen body's former “zero criterion changes” statement was invalidated:
the old `multiple consumers require shared ownership` rule had never been dry-run
against the planned skill topology. The implemented order is synchronized with
the root-layers contract:

```text
ci_triage (highest) > registered skills > tizen_ci_shared (lowest)
```

A registered skill API may be consumed by one or more `ci_triage` modules. A
shared consumer is an uplink and a peer-skill consumer is a same-layer edge;
both remain mismatches.

### Criterion negative fixtures

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --negative-fixture skill-owner-shared-consumer
NEGATIVE_FIXTURE | skill-owner-shared-consumer | MISMATCH: skill owner skill/tizen_convergence_judge is above shared consumer tizen_ci_shared.types
exit_code=1

$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --negative-fixture skill-owner-peer-skill-consumer
NEGATIVE_FIXTURE | skill-owner-peer-skill-consumer | MISMATCH: skill owner skill/tizen_convergence_judge has same-layer skill consumer fake_peer_skill.api
exit_code=1
```

### Step-0 regression lock

The pre-change audit output was captured before changing the criterion, then
the verdict maps were compared by symbol/module after the layered rule and
skill sources were active:

```text
step0_symbol_verdicts_compared=42
step0_module_verdicts_compared=4
verdict_changes=0
regression_lock_exit=0
```

## Commit C Import-Linter Evidence

Positive run with `import-linter==2.3`:

```text
Analyzed 34 files, 63 dependencies.
application layers: orchestration -> convergence skill -> shared KEPT
shared internal layers: L1 -> L0 -> types KEPT
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent KEPT
Contracts: 5 kept, 0 broken.
exit_code=0
```

Negative root-layer probe, temporary `tizen_convergence_judge.convergence ->
ci_triage`:

```text
application layers: orchestration -> convergence skill -> shared BROKEN
tizen_convergence_judge is not allowed to import ci_triage:
- tizen_convergence_judge.convergence -> ci_triage (l.14)
Contracts: 4 kept, 1 broken.
exit_code=1
```

Negative forbidden probe, temporary `tizen_ci_shared.types ->
tizen_convergence_judge`:

```text
application layers: orchestration -> convergence skill -> shared BROKEN
shared must not import orchestration BROKEN
tizen_ci_shared is not allowed to import tizen_convergence_judge:
- tizen_ci_shared.types -> tizen_convergence_judge (l.8)
Contracts: 3 kept, 2 broken.
exit_code=1
```

Both temporary imports were removed. The restored positive run again reported
`5 kept, 0 broken`, exit 0. `skill-independence` remains explicitly DEFERRED
until the second skill package exists; that batch must activate it and add its
horizontal negative control.

## Commit C Count Pin, Audit, and Bridge

The four step-0 module-scope pins are `10/3/8/27`. A temporary top-level
function in `classify.py` proved the count guard fail-closed:

```text
classify.py | module-scope | shared/classify | 28/27 symbols covered | MISMATCH: module-scope top-level count drift: expected 27, measured 28
SUMMARY | 77 SYMBOL OK | 3 MODULE-SCOPE OK (49 SYMBOLS COVERED) | 1 MISMATCH | 0 INCOMPLETE
exit_code=1
```

After restoration:

```text
symbol_audit:
SUMMARY | 77 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
exit_code=0

table_audit_bridge:
SUMMARY | 77 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
exit_code=0
```

The bridge parses the skill-1 §1.2 table as its sixth attribution table; the
35 symbols are not duplicated in the tool.

## Commit C Parity and Architecture Evidence

The same evidence fixture was evaluated through the legacy shim and the new
skill API, serialized with sorted compact JSON, and compared byte-for-byte:

```text
shim_is_skill=True
shim_bytes=641 skill_bytes=641
2f881fe8935b8b652c756efac596c2d904c1e45f3b502857b75c3d071d99957b  /tmp/convergence-shim.json
2f881fe8935b8b652c756efac596c2d904c1e45f3b502857b75c3d071d99957b  /tmp/convergence-skill.json
cmp_exit=0
```

Architecture exemption:

```text
$ grep -c arch tizen-convergence-judge/scripts/tizen_convergence_judge/convergence.py
0
grep_exit=1
```

## Commit C Final Validation

```text
pytest: 847 passed, 1 skipped in 21.93s
ruff: All checks passed!
mypy: Success: no issues found in 97 source files
py_compile_ok=34
lint-imports: 5 kept, 0 broken
symbol_audit: 77 SYMBOL OK + 4 MODULE-SCOPE OK, 0 MISMATCH, 0 INCOMPLETE
table_audit_bridge: 77 SYMBOL OK + 4 MODULE-SCOPE OK, all differences zero
canonical/history cmp: exit 0
```

No production implementation or test file changed in commit C. The only
runtime-facing addition is the declarative `SKILL.md`; all Python changes are
confined to the two read-only audit tools.

## Commit D: C21 Dynamic Script-Root Discovery

### Root Cause

Commit A followed the task prompt and hard-coded five repository script roots.
Commit B then added the sixth root, `tizen-convergence-judge/scripts`, to the
subprocess import chain without updating that fixed list. The target machine's
ambient environment masked the omission and reported 847 passing tests, while
a clean environment exposed three failures. The prompt's fixed five-path list
was therefore incorrect: a maintained list plus repository structure evolution
creates silent drift, the same failure class as the sibling-directory list
already deferred from `runner.py` during step-0.

The C21 helper now derives all immediate repository script roots with
`sorted(repo_root.glob("*/scripts"))`, excludes `release-v1.4.0`, and asserts
both a non-empty result and the presence of the `tizen_convergence_judge` and
`ci_triage` import packages. New skill roots are included without another
manual list update.

The three affected Python subprocess tests all use the shared helper:

- `test_campaign_cli_malformed_args_emit_one_json_and_exit_five`;
- `test_campaign_cli_rejection_emits_one_json_and_exit_four`;
- `test_python_m_campaign_repair_step_emits_one_json_document`.

The only other `subprocess.run` in the file belongs to the `_git` fixture
helper. It invokes the `git` executable and does not start a Python import
chain, so it intentionally does not use `_subprocess_env()`.

Measured script roots, in deterministic order:

```text
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-ci-shared/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-ci-triage/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-convergence-judge/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-build/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-build-workflow/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-log-analysis/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-patch-suggest/scripts
count=7
has_tizen_convergence_judge=True
has_ci_triage=True
```

Clean-CWD definition tests:

```text
cd /tmp && /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/pytest \
  /home/linhao/Toolchain/development/LogAnalysisSkill/tests/unit/test_campaign_repair_step.py \
  -k 'campaign_cli_malformed_args_emit_one_json_and_exit_five or campaign_cli_rejection_emits_one_json_and_exit_four or python_m_campaign_repair_step_emits_one_json_document'
3 passed, 35 deselected in 0.48s

cd /tmp && /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/pytest \
  /home/linhao/Toolchain/development/LogAnalysisSkill/tests/unit/test_campaign_repair_step.py
38 passed in 2.07s
```

Target-machine full regression:

```text
.venv/bin/pytest
847 passed, 1 skipped in 17.68s
```

Claude's clean-environment rerun of `test_campaign_repair_step.py` remains the
definition-level external acceptance for this commit; the repository-side
clean-CWD run above is green and no ambient `PYTHONPATH` is required.
