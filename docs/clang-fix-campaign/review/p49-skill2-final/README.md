# P4.9 Skill-2 QB-Discover Final Review Package

> 评审只读：发现问题报 finding，不得修改被审文件。
> This is the active repository review protocol at `../README.md:3`.

Review request:

> 请确认①实现与 v1.3-FROZEN 一致 ②四条断言尤其 d 的双键对照充分
> ③八处机械同步无遗漏 ④DEFERRED 可接受,无异议给 skill-2 CLOSED。

## Inputs

- Frozen contract: `../../p49-skill2-qb-discover-design-v1.3-FROZEN.md`.
- DoD account: `../p49-skill2-closeout.md`.
- Stage result: `../../dev_memory/stage09_p49_skill2_qb_discover/result.md`.
- Detailed measured output: `../../dev_memory/stage09_p49_skill2_qb_discover/progress.md`.

## Four Commits

```text
097294fccc668e57d8675c2de93cc4de2b634a17 docs(clang-fix-campaign): freeze P4.9 skill-2 qb-discover design v1.2
95ed5503119f30e5c560a6118c3219477ddfcbb4 tools(clang-fix-campaign): key SPECS and bridge by (module, symbol) with skill-root rule
41152fe27996b5c02509ba11998f5bd508551008 feat(tizen-qb-discover): extract QuickBuild discovery skill (P4.9 skill-2)
812b2132ec20858b07397dea3343d559c4d342e7 feat(tizen-qb-discover): activate gates and audit for skill-2 (P4.9)
```

## Reproduction Commands

Run from the repository root:

```bash
.venv/bin/pytest
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py

.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --key-fixture source-twin-only
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --key-fixture twin-both-binary-key
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py \
  --key-fixture twin-both-binary-key
! .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --negative-fixture duplicate-spec-root-mismatch
! .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --negative-fixture twin-both-name-only
! .venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py \
  --negative-fixture twin-both-name-only

git diff --stat d02a15a..812b213 -- \
  tizen-ci-triage/scripts/ci_triage/gbs_report.py
rg -n '^def (_normalize_text|_attrs_to_map|_class_names)\\b' \
  tizen-qb-discover/scripts/tizen_qb_discover/sources.py \
  tizen-ci-triage/scripts/ci_triage/gbs_report.py
! rg -n '^(def|class) ' \
  tizen-ci-triage/scripts/ci_triage/sources.py
grep -c arch tizen-qb-discover/scripts/tizen_qb_discover/sources.py
test "$?" -eq 1
test -f tizen-qb-discover/SKILL.md
.venv/bin/python \
  "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  tizen-qb-discover

git diff --stat e7900bb..812b213 -- \
  tests/unit/test_build_runner.py tests/unit/test_workflow.py
git diff d02a15a..812b213 -- tests/unit/test_ci_triage.py
```

Fail-closed check for a body table without `definition`:

```bash
PYTHONPATH=docs/clang-fix-campaign/tools .venv/bin/python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from table_audit_bridge import TableParseError, parse_design_tables

body = """### 2.2 ownership

| symbol | owner |
|---|---|
| Example | skill/example |
"""
with TemporaryDirectory() as directory:
    path = Path(directory) / "missing-definition.md"
    path.write_text(body, encoding="utf-8")
    try:
        parse_design_tables(path, section_headings=("### 2.2 ",))
    except TableParseError as exc:
        print(f"PARSE_ERROR | {exc}")
        raise SystemExit(1)
raise SystemExit("missing definition column was accepted")
PY
test "$?" -eq 1
```

Expected summaries:

```text
pytest: 847 passed, 1 skipped
lint-imports: Contracts: 6 kept, 0 broken
symbol audit: 96 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISMATCH | 0 INCOMPLETE
table bridge: 96 SYMBOL OK | 4 MODULE-SCOPE OK | all differences/parse errors zero
binary twin fixtures: two distinct definitions, OK
name-only and wrong-root fixtures: MISMATCH, exit 1
gbs_report diff stat: empty
same-name definitions: two per helper
legacy shim def/class matches: zero
QB-discover implementation arch matches: zero (`grep` exit 1)
```

The three import-linter red-phase probes and byte-level fake-fetcher parity
temporarily mutate or construct controlled state. Their procedures, exact
errors, restoration result, and matching SHA-256 are preserved in
`../../dev_memory/stage09_p49_skill2_qb_discover/progress.md`; reviewers should
use a disposable worktree if repeating mutation-based checks.

## Deferred Review

Confirm these closing batches are acceptable:

1. Same-name helper consolidation decision: `triage-report` extraction batch.
2. Compatibility-shim deletion: one-shot P4.9 cleanup after all six skills.
3. Two residual clean-environment-sensitive tests: next skill batch before
   that batch changes tests.
