# P4.9 Skill-1 Convergence-Judge Final Review Package

> 评审只读：发现问题报 finding，不得修改被审文件。
> This is the active repository review protocol at `../README.md:3`.

Review request:

> Skill-1 is complete against the v1.3-FROZEN design, including the v1.3
> layered audit ruling. The DoD account is in `../p49-skill1-closeout.md`.
> 请确认①实现与 v1.3-FROZEN 一致 ②v1.3 判据层化的三条防滥用断言充分
> ③DEFERRED 可接受,无异议给 skill-1 CLOSED。

## Inputs

- Frozen contract: `../../p49-skill1-convergence-judge-design-v1.4-FROZEN.md`.
- DoD account: `../p49-skill1-closeout.md`.
- Audit record: `../p49-skill1-convergence-judge-audit.md`.
- Stage result: `../../dev_memory/stage08_p49_skill1_convergence_judge/result.md`.
- Detailed measured output: `../../dev_memory/stage08_p49_skill1_convergence_judge/progress.md`.

## Five Commits

```text
d3478ab5f790ade52d49644919872b844f9f9820 docs(clang-fix-campaign): freeze skill-1 convergence-judge design v1.2
f4c8142bc20616cad822f53e6dbbf9956e575ee8 test(ci-triage): anchor subprocess PYTHONPATH via __file__ (C21)
f7194ae20ea842eb71d4f8803ba4f41373d3a04b feat(tizen-convergence-judge): extract convergence skill with public alias contract (P4.9 skill-1)
954bbcda61c489ea77b4c74e005ede589e4a5f4d feat(tizen-convergence-judge): activate gates and audit for skill-1 (P4.9)
9bf1af06dff31b5440e2b8e29dca5cc13f3a8307 test(ci-triage): derive subprocess PYTHONPATH by globbing script roots
```

## Reproduction Commands

Run from the repository root:

```bash
SCRIPT_ROOTS=$(.venv/bin/python - <<'PY'
from pathlib import Path
import os

root = Path.cwd()
paths = sorted(
    path for path in root.glob("*/scripts")
    if path.parent.name != "release-v1.4.0"
)
print(os.pathsep.join(str(path) for path in paths))
PY
)
export PYTHONPATH="$SCRIPT_ROOTS"

.venv/bin/pytest

env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/bin:/bin" \
  PYTHONPATH="$SCRIPT_ROOTS" \
  .venv/bin/pytest tests/unit/test_campaign_repair_step.py \
  -k 'campaign_cli_malformed_args_emit_one_json_and_exit_five or campaign_cli_rejection_emits_one_json_and_exit_four or python_m_campaign_repair_step_emits_one_json_document'

.venv/bin/pytest tests/unit/test_convergence.py \
  -k public_fingerprint_and_error_count_aliases_are_identical

.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py

! .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --negative-fixture skill-owner-shared-consumer
! .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --negative-fixture skill-owner-peer-skill-consumer

rg -n '^def (_primary_fingerprint|_error_count|primary_fingerprint|error_count)\b' \
  --glob '*.py' --glob '!release-v1.4.0/**' .
! rg -n '^(def|class) ' \
  tizen-ci-triage/scripts/ci_triage/verify/convergence.py
grep -c arch \
  tizen-convergence-judge/scripts/tizen_convergence_judge/convergence.py
test "$?" -eq 1
test -f tizen-convergence-judge/SKILL.md
```

Expected summaries:

```text
pytest: 847 passed, 1 skipped
C21: 3 passed, 35 deselected
alias identity: 1 passed, 14 deselected
lint-imports: Contracts: 5 kept, 0 broken
symbol audit: 77 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISMATCH | 0 INCOMPLETE
table bridge: 77 SYMBOL OK | 4 MODULE-SCOPE OK | all difference counts zero
both layered-rule negative fixtures: MISMATCH, exit 1
legacy shim def/class matches: zero
convergence implementation arch matches: zero (`grep` exit 1)
```

The import-linter boundary probes, module-count drift probe, step-0 verdict
lock, and byte-level parity procedure mutate temporary working copies during
their red-phase checks. Their complete red/restore/green outputs are preserved
in `../../dev_memory/stage08_p49_skill1_convergence_judge/progress.md`; reviewers
should not alter the canonical working tree to repeat them.

## Deferred Review

Confirm these named closing batches are acceptable:

1. `skill-independence`: second skill extraction batch.
2. Compatibility-shim deletion: single P4.9 final cleanup after all six skills.
3. Seven inherited GBS report constraints: `triage-report` extraction batch.
