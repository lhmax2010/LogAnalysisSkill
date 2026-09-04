# P4.9 Skill-4 Build-Verify Final Review Package

> 评审只读：发现问题报 finding，不得修改被审文件。
> This is the active repository review protocol at `../README.md:3`.

Review request:

> 请确认①实现与 v1.12.1-FROZEN 一致 ②三迁移模式各自验收充分
> ③具名例外四负控制与双门禁有效 ④DEFERRED 可接受，无异议给
> skill-4 CLOSED。

## Inputs

- Frozen contract:
  `../../p49-skill4-build-verify-design-v1.12.1-FROZEN.md`.
- DoD account: `../p49-skill4-closeout.md`.
- Stage result:
  `../../dev_memory/stage11_p49_skill4_build_verify/result.md`.
- Detailed measured output:
  `../../dev_memory/stage11_p49_skill4_build_verify/progress.md`.
- A0 raw evidence:
  `../../dev_memory/stage11_p49_skill4_build_verify/a0-evidence/`.

## Six Lifecycle Commits

```text
148b7f66dddbe7cfebe58a4f16996acc4815c4b5 tools(clang-fix-campaign): add design drift ledger with reverse and forward gates (P4.9 skill-4 A₀)
09da87d7a4a4ca927d59a86a9615f8eb201280b4 docs(clang-fix-campaign): freeze P4.9 skill-4 build-verify design v1.12
3da25296660eda55bce3072e9b5c75be66637a57 feat(tizen-build-verify): extract build-verify skill in three migration modes (P4.9 skill-4 commit A)
f85bd5850e89988dc5bfb3e9dd49224988b9d710 test(tizen-build-verify): establish skill test ownership and branch matrix (P4.9 skill-4 commit B)
da6d5039869249bee8e2b5ee210fe85981b0b90a feat(tizen-build-verify): activate gates and audit for skill-4 (P4.9)
Git-anchored containing commit             docs(clang-fix-campaign): close out P4.9 skill-4 build-verify
```

The sixth SHA is deliberately not self-recorded. Git anchors this review
package and the closeout result outside their own contents (`⑬/⑲`).

## Reproduction Commands

Run from the repository root. Delivery-stage commands explicitly remove the
temporary commit-A scaffolding:

```bash
.venv/bin/python -m pip install -e .
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest -q
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest -q \
  tests/unit/test_tizen_build_verify.py \
  tests/unit/test_build_verify_legacy_wiring.py \
  tests/integration/test_build_verify_real_git.py
env -u PYTHONPATH -u MYPYPATH .venv/bin/mypy
env -u PYTHONPATH -u MYPYPATH .venv/bin/mypy \
  docs/clang-fix-campaign/tools/symbol_audit.py \
  docs/clang-fix-campaign/tools/table_audit_bridge.py
git ls-files -z '*.py' | xargs -0 .venv/bin/ruff check
git ls-files -z '*.py' | xargs -0 .venv/bin/python -m py_compile
env -u PYTHONPATH -u MYPYPATH .venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py
```

Relocation and exact-surface controls:

```bash
for case in missing-destination wrong-definition wrong-owner source-remains \
  mapping-contract source-table-mismatch; do
  ! .venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py \
    --relocation-negative "$case"
done

for case in one two three; do
  .venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py \
    --relocation-synthetic "$case"
done

! .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --surface-fixture mixed-case-alias
```

Design drift gates and their admission controls:

```bash
.venv/bin/python docs/clang-fix-campaign/tools/design_drift_ledger.py check
! .venv/bin/python docs/clang-fix-campaign/tools/design_drift_ledger.py \
  admission-v19
! .venv/bin/python docs/clang-fix-campaign/tools/design_drift_ledger.py \
  negative-fixture out-of-scope-misuse
```

All 22 per-binding commands and all 47 OUT_OF_SCOPE item outcomes are retained
verbatim in `a0-evidence/binding-negatives.txt` and
`a0-evidence/out-of-scope-negative.txt`. The first file lists each
`negative-binding <id>` invocation; every gate mutation exits red while the
selector-external COUNT_EQUAL interference remains green.

Mechanical entry-point checks:

```bash
test "$(rg -F -c 'mypy tizen-build-verify/scripts/tizen_build_verify' \
  .github/workflows/ci.yml)" -eq 1
test "$(rg -F -c '$PWD/tizen-build-verify/scripts' README.md)" -eq 1
test "$(rg -F -c 'tizen-build-verify/scripts' pyproject.toml)" -eq 2
test "$(rg -F -c 'tizen_build_verify' pyproject.toml)" -eq 2
! rg -n 'include_external_packages' .importlinter
test "$(rg -c '^unmatched_ignore_imports_alerting = error$' \
  .importlinter)" -eq 2
```

Bridge authority and exact 29/12/4 split:

```bash
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py \
  > /tmp/p49-skill4-bridge.txt
test "$(rg -c '^tizen_build_verify/build_verify\.py \|' \
  /tmp/p49-skill4-bridge.txt)" -eq 29
test "$(rg -c '^tizen_build_verify/edit_spec_guard\.py \|' \
  /tmp/p49-skill4-bridge.txt)" -eq 12
test "$(rg -c '^tizen_build_verify/workspace\.py \|' \
  /tmp/p49-skill4-bridge.txt)" -eq 4
rg '^RELOCATION|^SUMMARY' /tmp/p49-skill4-bridge.txt
```

Scoped twin and protected-surface checks:

```bash
rg -n '^SubprocessRunner = ' --glob '*.py' tizen-*/scripts
rg -n '^def _git_stdout\(' --glob '*.py' tizen-*/scripts
rg -n '^def _read_json\(' --glob '*.py' tizen-*/scripts
rg -n '^def _sha256_file\(' --glob '*.py' tizen-*/scripts
rg -n '^def _build_subprocess_env\(' --glob '*.py' tizen-*/scripts
rg -n '^def _is_relative_to\(' --glob '*.py' tizen-*/scripts
rg -n '^EDIT_SPEC_SCHEMA = ' --glob '*.py' tizen-*/scripts
rg -n '^def _locate_edit\(' --glob '*.py' tizen-*/scripts

git diff --stat 148b7f6^..da6d503 -- \
  release-v1.4.0 \
  tizen-ci-triage/scripts/ci_triage/gbs_report.py \
  docs/clang-fix-campaign/design.md
```

The four import-linter exception negatives and the pre-shim parity necessarily
use temporary or migration-time state. Their exact mutations, exit-1 output,
restoration checks, five field comparisons, and one-positive/three-negative
normalizer results are preserved in `progress.md:269-374` and
`progress.md:649-701`. Repeat those mutations only in a disposable worktree.

## Expected Summaries

```text
pytest: 897 passed, 1 skipped
targeted build-verify unit + wiring + real-git integration: 53 passed, 1 skipped
lint-imports: 6 kept, 0 broken
symbol audit: 150 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISMATCH | 0 INCOMPLETE
table bridge: relocation 3/3 consumed and 3/3 produced; 150+4; all differences zero
bridge skill-4 rows: 29/12/4
design check: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0
admission v1.9: BINDING_DRIFT=3 | RED_AS_EXPECTED
entry counts: 1/1/2/2
protected historical surfaces diff: empty
```

## Deferred Review

Confirm these closing batches are acceptable:

1. `EDIT_SPEC_SCHEMA` single authority: `patch-suggest` extraction.
2. Same-name helper consolidation: `triage-report` extraction.
3. Compatibility-shim deletion: one-shot P4.9 final cleanup.
4. Private test-consumer narrowing: one-shot P4.9 final cleanup.
