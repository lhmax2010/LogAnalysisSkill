# P4.9 Skill-3 Gerrit-Fetch Final Review Package

> 评审只读：发现问题报 finding，不得修改被审文件。
> This is the active repository review protocol at `../README.md:3`.

Review request:

> 请确认①实现与 v1.3.1-FROZEN 一致 ②A' 四组断言与 pre/post-shim
> 证据分列充分 ③20 分支闭合 ④DEFERRED 可接受,无异议给 skill-3 CLOSED。

## Inputs

- Frozen contract:
  `../../p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md`.
- DoD account: `../p49-skill3-closeout.md`.
- Stage result:
  `../../dev_memory/stage10_p49_skill3_gerrit_fetch/result.md`.
- Detailed measured output:
  `../../dev_memory/stage10_p49_skill3_gerrit_fetch/progress.md`.

## Five Commits

```text
4612167c6e85040d9ea9a96333d07a8c5974cc31 docs(clang-fix-campaign): finalize skill-3 design as v1.3.1-FROZEN
751e7b4924cade7fb22b6f8e9c58600f05a8a1e5 test(ci-triage): make environment-sensitive tests environment-independent (P4.9 skill-3 commit A)
f4be9e40bb2bbb6a81d0319ef17e98fb2a794920 tools(clang-fix-campaign): track import bindings in consumer analysis (P4.9 skill-3 commit A')
f6544dfb822af3ebd6b001d92f238bc0e9422eff feat(tizen-gerrit-fetch): extract Gerrit fetch skill (P4.9 skill-3 commit B)
c41d15a3e377822fbccdd3165bd4734e9ba34986 feat(tizen-gerrit-fetch): activate gates and audit for skill-3 (P4.9)
```

## Reproduction Commands

Run from the repository root. The delivery-stage commands deliberately clear
the temporary B-stage path variables:

```bash
.venv/bin/python -m pip install -e .
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest -q
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest -q \
  tests/unit/test_gerrit_fetch.py
env -u PYTHONPATH -u MYPYPATH .venv/bin/mypy
env -u PYTHONPATH -u MYPYPATH .venv/bin/ruff check $(git ls-files '*.py')
env -u PYTHONPATH -u MYPYPATH .venv/bin/lint-imports
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m compileall -q \
  tizen-ci-shared/scripts tizen-convergence-judge/scripts \
  tizen-qb-discover/scripts tizen-gerrit-fetch/scripts \
  tizen-ci-triage/scripts docs/clang-fix-campaign/tools
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py
```

Import-binding assertion groups and their old-implementation red proof:

```bash
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --binding-fixture regression-lock
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --binding-fixture aliased-import
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --binding-fixture same-name-import
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --binding-fixture planned-run-git
! .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
  --negative-fixture import-binding-legacy-alias
```

Parser-only and full-bridge checks are separate by design. The full bridge
must print 12 Gerrit rows, not merely a green summary:

```bash
PYTHONPATH=docs/clang-fix-campaign/tools .venv/bin/python - <<'PY'
from pathlib import Path
from table_audit_bridge import parse_design_tables

path = Path(
    "docs/clang-fix-campaign/"
    "p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md"
)
rows = parse_design_tables(path, section_headings=("## §0 ",))
print(f"parser_only_rows={len(rows)}")
for definition, symbol in sorted(rows):
    print(definition, symbol, rows[(definition, symbol)].owner)
PY

.venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py \
  | tee /tmp/p49-skill3-bridge.txt
test "$(rg -c '^tizen_gerrit_fetch/gerrit\.py \|' \
  /tmp/p49-skill3-bridge.txt)" -eq 12
```

The frozen 20-row map resolves every declared test name against the current
collection:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import subprocess

design = Path(
    "docs/clang-fix-campaign/"
    "p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md"
).read_text(encoding="utf-8").splitlines()
start = next(i for i, line in enumerate(design) if line.startswith("| §2.2 契约句 |"))
rows = []
for line in design[start + 2:]:
    if not line.startswith("|"):
        break
    rows.append([cell.strip() for cell in line.strip("|").split("|")])
output = subprocess.run(
    [".venv/bin/python", "-m", "pytest", "--collect-only", "-q",
     "tests/unit/test_gerrit_fetch.py"],
    check=True, text=True, capture_output=True,
).stdout
nodeids = {line for line in output.splitlines() if line.startswith("tests/")}
missing = []
for _, _, test_cell in rows:
    declared = test_cell.strip("`")
    base = declared.split("[", 1)[0]
    if not any(nodeid.split("[", 1)[0].endswith("::" + base) for nodeid in nodeids):
        missing.append(declared)
print(f"contract_rows={len(rows)} mapped_rows={len(rows) - len(missing)} unmapped={len(missing)}")
raise SystemExit(bool(missing))
PY
```

Mechanical delivery, twin, shim, release-boundary, and arch checks:

```bash
test "$(rg -F -c 'mypy tizen-gerrit-fetch/scripts/tizen_gerrit_fetch' \
  .github/workflows/ci.yml)" -eq 1
test "$(rg -F -c '$PWD/tizen-gerrit-fetch/scripts' README.md)" -eq 1
test "$(rg -F -c 'tizen-gerrit-fetch/scripts' pyproject.toml)" -eq 2
test "$(rg -F -c 'tizen_gerrit_fetch' pyproject.toml)" -eq 2

test "$(rg '^def _run_git\(' -c tizen-*/scripts --glob '*.py' \
  | awk -F: '{n += $2} END {print n}')" -eq 3
test "$(rg '^SubprocessRunner = ' -c \
  tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py \
  tizen-ci-triage/scripts/ci_triage/runner.py \
  | awk -F: '{n += $2} END {print n}')" -eq 2
! rg -n '^(def|class) ' tizen-ci-triage/scripts/ci_triage/gerrit.py
grep -c arch tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py
test "$?" -eq 1

git diff --stat 4612167^..c41d15a -- \
  release-v1.4.0 \
  tizen-ci-triage/scripts/ci_triage/gbs_report.py \
  docs/clang-fix-campaign/design.md
.venv/bin/python \
  "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  tizen-gerrit-fetch
```

Source equality is independently reproducible from the immutable commits:

```bash
cmp \
  <(git show f4be9e4:tizen-ci-triage/scripts/ci_triage/gerrit.py) \
  <(git show f6544df:tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py)
```

Expected summaries:

```text
pytest: 883 passed, 1 skipped
targeted Gerrit tests: 38 passed
lint-imports: Contracts: 6 kept, 0 broken
symbol audit: 108 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISMATCH | 0 INCOMPLETE
table bridge: 108 SYMBOL OK | 4 MODULE-SCOPE OK | all differences zero
bridge skill-3 rows: 12
parser-only rows: 12
contract map: 20 rows mapped, 0 unmapped
legacy shim def/class matches: zero
package root: 4 public identities; 8 implementation names and 3 types absent
implementation arch matches: zero (grep exit 1)
protected historical surfaces diff: empty
```

The three import-linter red-phase probes and the pre-shim independent-module
parity necessarily use temporary/migration-time state. Their exact commands,
exit-1 diagnostics, restoration runs, four field comparisons, one positive
normalizer sample, and three red samples are preserved in
`../../dev_memory/stage10_p49_skill3_gerrit_fetch/progress.md`. Repeat mutations
only in a disposable worktree. Post-shim identity tests are current and are not
a substitute for that behavior evidence.

## Deferred Review

Confirm these closing batches are acceptable:

1. Same-name consolidation: `triage-report` extraction.
2. Compatibility-shim deletion: one-shot P4.9 final cleanup. Delete the three
   Gerrit type re-exports only from legacy `ci_triage/gerrit.py`; retain the
   matching imports in `tizen_gerrit_fetch/gerrit.py` because they are real
   signature dependencies. The inherited skill-side shim comments may be
   corrected then.
3. Dangling-symlink normalization: `gerrit-submit` batch.
4. Unified timeout/cancellation, interruption cleanup, and error normalization:
   `gerrit-submit` batch.
