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

- Independent Claude clean-environment full suite: pending after push; this is
  the definition-of-done signal required before commit A-prime.
- Production source diff: zero.
