# P4.9 Skill-3 Gerrit-Fetch Progress

## Frozen authority

- Authority: `p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md` at commit
  `4612167`.
- Commit A is test infrastructure only. Production code under `tizen-*/scripts/`
  and `ci_triage/` must have zero diff.

## Commit A execution clarification

The execution-time clarification defines the original diff restriction by its
safety intent: production code diff is zero; test changes are limited to
`tests/unit/test_build_runner.py` and `tests/unit/test_workflow.py`; this
dev-memory evidence file accompanies the commit and is outside that test-file
restriction. This is a wording correction, not a scope expansion. It must be
recorded again in the skill-3 closeout under "frozen-design execution
clarifications".

## Root-cause diagnosis

### Build-runner module subprocess

The test passed in the repository virtual environment because the editable
installation exposed `gbs_build_skill`. A clean-style parent could import the
package after changing its own `sys.path`, but the child process changed cwd to
`tmp_path` and inherited only environment variables, not the parent's
in-process `sys.path` mutation.

Reproduction:

```text
$ env -u PYTHONPATH -u MYPYPATH /usr/bin/python3 - <<'PY'
import sys
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / 'tizen-gbs-build/scripts'))
import pytest
raise SystemExit(pytest.main([
    '-q',
    'tests/unit/test_build_runner.py::test_python_module_invocation_runs_fake_gbs',
]))
PY
/usr/bin/python3: No module named gbs_build_skill
1 failed
```

Fix: derive every repository `*/scripts` directory from `__file__`, exclude the
release snapshot, assert that discovery is non-empty and includes
`gbs_build_skill`, and pass the resulting absolute list in the child process's
`PYTHONPATH`.

Derived paths:

```text
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-ci-shared/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-ci-triage/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-convergence-judge/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-build/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-build-workflow/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-log-analysis/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-gbs-patch-suggest/scripts
/home/linhao/Toolchain/development/LogAnalysisSkill/tizen-qb-discover/scripts
TOTAL=8
HAS_GBS_BUILD=True
```

### Workflow fallback assertion

The test asserted that the broad substring `fallback` was absent. Without the
optional `tiktoken` module, the valid report metadata contains
`**Token estimate method**: fallback`, so the assertion failed even though the
generic fallback suggestion was correctly suppressed.

Reproduction ended with:

```text
assert "fallback" not in summary
E AssertionError: assert 'fallback' not in ...
... **Token estimate method**: fallback ...
1 failed
```

Fix: assert that the exact generic suggestion row `| 001 | fallback |` is
absent. This preserves the behavioral contract while allowing the documented
token-estimation fallback.

## Targeted verification

Repository virtual environment:

```text
$ .venv/bin/python -m pytest -q \
    tests/unit/test_build_runner.py::test_python_module_invocation_runs_fake_gbs \
    tests/unit/test_workflow.py::test_workflow_werror_patch_ready_context_suppresses_generic_fallback
..                                                                       [100%]
2 passed in 0.22s
```

Clean-style `/usr/bin/python3` reproductions after the fixes:

```text
build-runner: 1 passed in 0.10s
workflow without tiktoken: 1 passed in 0.07s
```

## Acceptance status

- Target-machine full suite:

  ```text
  $ .venv/bin/python -m pytest -q
  847 passed, 1 skipped in 18.93s
  exit 0
  ```

- Targeted lint:

  ```text
  $ .venv/bin/ruff check tests/unit/test_build_runner.py tests/unit/test_workflow.py
  All checks passed!
  exit 0
  ```

- Mechanical scope checks:

  ```text
  $ git diff --name-only -- ':(glob)tizen-*/scripts/**' ':(glob)**/ci_triage/**'
  <no output>

  $ git diff --name-only -- tests/
  tests/unit/test_build_runner.py
  tests/unit/test_workflow.py
  ```

- Independent Claude clean-environment output was not supplied in this
  session; the developer's explicit commit A-prime task authorized proceeding.
- Production source diff: zero.

## Commit A-prime: import-binding consumer attribution

### Rule implementation

`symbol_audit._actual_consumers` now parses named, module-scope `ImportFrom`
bindings as `(source module, source symbol, local name)`. References are
visited using the local name and attributed to the resolved source pair. Pure
re-export chains are followed so existing legacy shims retain their measured
consumers.

The intentionally unsupported forms are documented next to the parser:
`import X; X.S`, `ImportFrom` nested in a function or class, and
`from X import *`. The existing twin guard's deliberate over-skip also remains
documented and unchanged.

The convergence inventory now attributes `ci_triage.campaign_state` to the
public aliases `primary_fingerprint` and `error_count`, not to their private
implementation definitions. This changes measured attribution while keeping
every audit verdict unchanged.

### Assertion group a: regression lock and real alias

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --binding-fixture regression-lock
BINDING_FIXTURE | regression-lock | symbols=96 | verdict_changes=0
BINDING_FIXTURE | campaign-state-alias | primary_fingerprint consumers=('ci_triage.campaign_state',) | _primary_fingerprint consumers=()
exit 0
```

The legacy and binding-aware runs use their corresponding pre/post attribution
inventories. All 96 per-symbol verdicts remain unchanged; the four
module-scope verdicts do not consume `_actual_consumers` and are unaffected.

### Assertion group b: aliased import, including old implementation red

The synthetic consumer contains `from fixture.a import S as LocalS`, uses
`LocalS`, defines no top-level `S`, and coexists with `fixture.b.S`.

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --binding-fixture aliased-import
BINDING_FIXTURE | aliased-import | new A.S=('fixture.consumer',) | new B.S=()
BINDING_FIXTURE | aliased-import | legacy A.S=() | legacy B.S=() | OLD_VERDICT=MISMATCH
exit 0

$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --negative-fixture import-binding-legacy-alias
NEGATIVE_FIXTURE | import-binding-legacy-alias | MISMATCH: legacy consumers for fixture.a:S were (), expected ('fixture.consumer',)
exit 1
```

### Assertion group c: same-name import

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --binding-fixture same-name-import
BINDING_FIXTURE | same-name-import | A.S=('fixture.consumer',) | degenerate same-name case only; not alias-generalization evidence
exit 0
```

This fixture covers only the `from A import S as S` degenerate form. It is not
used as evidence for general alias handling; group b supplies that proof.

### Assertion group d: planned gerrit `_run_git`

The planned `tizen_gerrit_fetch.gerrit` definition is supplied as a synthetic
source while all current repository sources remain real. This makes the
post-extraction attribution testable before production migration.

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py \
    --binding-fixture planned-run-git
BINDING_FIXTURE | planned-run-git | gerrit._run_git=() | workspace._run_git=('ci_triage.verify.workspace',)
exit 0
```

### Double audit

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
SUMMARY | 96 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
exit 0

$ .venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py
SUMMARY | 96 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
exit 0
```

### Commit A-prime gates

```text
pytest: 847 passed, 1 skipped in 17.53s
ruff (all tracked Python files): All checks passed!
mypy: Success: no issues found in 103 source files
py_compile symbol_audit.py: exit 0
```

An unscoped `ruff check .` also inspected the unrelated, pre-existing
untracked `audit_four_sigs.py` and reported its existing style errors. As in
stage09, the complete tracked Python set is the repository gate and is green.

Production code under `tizen-*/scripts/` and `ci_triage/` has zero diff.

## Commit B: extraction and pre-shim parity

### Execution-time count clarification

The commit B acceptance count is set membership, not a frozen total. All 847
passing commit A tests and its one skipped test must remain collected with no
new failure or skip; every new test must pass; the resulting actual total is
the commit C baseline. This is an execution-time wording clarification and
must be copied into the skill-3 closeout under "frozen-design execution
clarifications" without creating v1.3.2.

Collection evidence before the extraction:

```text
$ .venv/bin/python -m pytest -q --collect-only | tee /tmp/skill3-commit-b-before-collect.txt | wc -l
850
848 tests collected in 0.23s
baseline nodeids: 848
```

Collection evidence after the extraction:

```text
$ PYTHONPATH="$PWD/tizen-gerrit-fetch/scripts${PYTHONPATH:+:$PYTHONPATH}" \
    .venv/bin/python -m pytest -q --collect-only \
    | tee /tmp/skill3-commit-b-after-collect.txt | wc -l
886
884 tests collected in 0.24s
```

The nodeid comparison maps only the two tests intentionally moved from
`test_ci_triage.py` to `test_gerrit_fetch.py`; after that path-only mapping it
reports:

```text
baseline_nodeids=848
current_nodeids=884
missing_after_two_expected_relocations=0
new_nodeids=36
```

Thus every prior case remains and all 36 net-new cases are separately
collectable. The new commit B baseline is:

```text
$ PYTHONPATH="$PWD/tizen-gerrit-fetch/scripts${PYTHONPATH:+:$PYTHONPATH}" \
    .venv/bin/python -m pytest -q
883 passed, 1 skipped in 17.57s
exit 0
```

The final `-rs` replay reported the same sole pre-existing skip and no new
skip:

```text
SKIPPED [1] tests/unit/test_edit_spec_guard.py:97: case-sensitive filesystem
883 passed, 1 skipped in 17.71s
```

An AST source-segment comparison against `HEAD:tests/unit/test_ci_triage.py`
also proves that the two relocated legacy tests retained their complete
function bodies:

```text
MOVED_TEST_BODY_EQUAL test_find_patchset_by_revision_uses_matching_revision_not_current=True
MOVED_TEST_BODY_EQUAL test_fetch_source_for_new_change_fetches_matching_patchset_ref=True
```

### Source move before modification

The skill implementation was copied while the legacy module was still an
independent implementation. Before replacing the legacy file with a shim:

```text
$ cmp tizen-ci-triage/scripts/ci_triage/gerrit.py \
    tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py
exit 0
$ sha256sum <both files>
5df43c509fffe76ecaa37914fb07db0e86056a81b98f849321e390a43fd5d82a
5df43c509fffe76ecaa37914fb07db0e86056a81b98f849321e390a43fd5d82a
```

After the shim replacement, the immutable source-side check remains
reproducible with `git show HEAD:.../ci_triage/gerrit.py | cmp -
tizen-gerrit-fetch/.../gerrit.py`; it also exits zero with the same SHA.

### Pre-shim behavioral parity

The parity run occurred before the legacy module became a shim. It used
`importlib.reload` on two different module objects and two independent
destinations. Normalization was applied only to argv elements,
`SourceFetchResult.src_root`, and symlink targets. Python mapping equality is
recursive, so each `field_equal` result compares every nested field in that
closed payload section, rather than comparing a serialized hash alone.

```text
isolation.old=.../tizen-ci-triage/scripts/ci_triage/gerrit.py
isolation.new=.../tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py
isolation.distinct_modules=True
field_equal.result=True
field_equal.runner_trace=True
field_equal.controlled_environment=True
field_equal.destination_state=True
payload_equal=True
old_sha256=840b9e8ccbaa94a2a1ae253c3644d245e5be3cb27a887b5a006278537ac2655a
new_sha256=840b9e8ccbaa94a2a1ae253c3644d245e5be3cb27a887b5a006278537ac2655a
normalizer_positive.destination_only=PASS
normalizer_negative.error_non_path=RED_AS_EXPECTED
normalizer_negative.command_order=RED_AS_EXPECTED
normalizer_negative.status=RED_AS_EXPECTED
exit_code=0
```

The compared result contains all five `SourceFetchResult` fields and every
nested Gerrit field. The ordered runner trace has six calls (query, init,
remote-add, depth-1 fetch, depth-50 fallback fetch, checkout), including all
argv/check/capture_output/text values. The controlled environment is
`GIT_SSH_COMMAND=ssh -i /tmp/parity-key`; the destination comparison includes
the complete file tree, content hashes, absolute symlink target after the
field-scoped mask, and ordered stage markers. The error negative sample is
`DIFFERENT_ERROR_CODE: non-path message`, outside every path mask.

### Frozen branch table and destructive evidence

A parser read the frozen §5.1 mapping table and matched each declared test to
the post-extraction collection:

```text
SUMMARY | contract_rows=20 | mapped_rows=20 | unmapped=0
exit 0
```

The exceptional and destructive cases are pinned as follows:

| case id | injection point | asserted destination state |
|---|---|---|
| `query/timeout` | direct query runner raises `TimeoutExpired` | existing directory and sentinel unchanged; exactly the query call occurred |
| `timeout-after-init` | git `remote add` raises `TimeoutExpired` | directory and fake `.git` exist; only `01-init`; no source file |
| `interrupt-during-fetch` | NEW fetch raises `ControlledInterruption` | directory and fake `.git` exist; `01-init`,`02-remote-add`; no source file |
| `timeout-before-checkout` | NEW checkout raises `TimeoutExpired` | directory and fake `.git` exist; init/remote/fetch markers; no source file |
| `rmtree` | `shutil.rmtree` raises `OSError` | original directory and sentinel content remain |
| `unlink` | `Path.unlink` raises `OSError` | original ordinary file and content remain |
| `mkdir` | destination `Path.mkdir` raises `OSError` | destination remains absent |

The six terminal `CalledProcessError` fixtures separately cover init,
remote-add, NEW fetch, NEW checkout, branch-fallback fetch, and non-NEW
checkout, asserting each exact partial stage set. The focused exception run
reported `11 passed in 0.03s` for all query outcomes, three interruption
fixtures, and three filesystem failures.

The no-timeout fixture uses the one injected runner for both the direct query
call and every `_run_git` call, asserts that both ssh and git were observed,
and rejects a `timeout` keyword on any captured call.

### Shim and package wiring

The legacy module contains zero `def`/`class` statements (`rg` exit 1). Its 12
implementation names and three shared types are identity-equal to their
authoritative definitions:

```text
SUMMARY implementation=12 shared_types=3 all_identical=True
```

The package root exports only
`fetch_source_for_commit`, `GerritError`, `GERRIT_HOST`, and `GERRIT_PORT`.
Tests assert that all eight implementation-only names and all three shared
types are absent from the package root.

### Commit B temporary paths and gates

Formal packaging and mypy registration belong to commit C. Commit B used the
following explicit temporary scaffolding:

```text
PYTHONPATH=$PWD/tizen-gerrit-fetch/scripts${PYTHONPATH:+:$PYTHONPATH}
MYPYPATH=$PWD/tizen-gerrit-fetch/scripts${MYPYPATH:+:$MYPYPATH}
```

Gate outputs:

```text
targeted Gerrit + orchestration tests: 97 passed in 0.23s
full suite: 883 passed, 1 skipped in 17.57s
mypy configured packages: Success: no issues found in 103 source files
mypy new skill: Success: no issues found in 2 source files
ruff tracked Python + commit B files: All checks passed!
py_compile: exit 0
lint-imports: 6 kept, 0 broken
git diff --check: exit 0
```
