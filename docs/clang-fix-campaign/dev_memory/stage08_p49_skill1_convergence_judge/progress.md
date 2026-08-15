# P4.9 Skill-1 Convergence-Judge Progress

Status: **DESIGN FROZEN; IMPLEMENTATION PENDING**.

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
- Both files SHA-256:
  `ef0eda37112dfbcd574b5b17d42de264e2270b07462e6d244cdf5e5f4ff0a4a3`.
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
