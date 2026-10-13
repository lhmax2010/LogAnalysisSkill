# C2B-09 Production Normalization

Baseline befd9a8. Ruling verbatim in progress25.1; frozen design unchanged.
No live QuickBuild requests. Raw DOM text crosses only into the trusted Node
agent, not the Python protocol. Form/build/refresh decisions normalize in Node;
DOM redaction uses the locally declared two-ended global whitespace regex.
This does not claim isolation from arbitrary overwritten page intrinsics; R1 owns
the isolated-world design. Policy and network permissions are unchanged.

## Reproduction

The runtime fixture imports the archived live-10 form structure in about:blank,
not its scripts/resources, injects the approved broken trim, and tests form,
build identity, redaction and refresh registration for normal/broken cases.
Option labels have surrounding whitespace. Eight subtests plus parent add nine
Node tests; Python nodeids are unchanged. It checks snapshot/HTML parity between
both cases and Python PageRedactor pre/post-write checks with synthetic identities.

before-fix.log includes an initial test harness error (PageRedactor takes no
identities constructor argument). Corrected before production edits and rerun:
before-fix-corrected-fixture.log exit1,45 pass/5 fail, including parent aggregate.
Broken trim causes QB_FORM_CHANGED, null build identity, Triggered By identity
leak. Added option normalization also fails on the old implementation. No failing
expectation was relaxed. After fix: runtime50/50,unit120/120,safety4/4, exit0.

## Commands

All from repo root; outputs are adjacent logs. The pre-fix command has expected
exit1; normal gates must exit0. Final counts are appended after completion.

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  tests/node/test_qb_browser_runtime.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
```

Ruff runs on an exported full staged tree, excluding unrelated pre-existing user
changes and untracked drafts. Tree/path and results recorded when completed.
The spikes consumers of raw formDOM are synchronized in the next separate commit;
live collection is prohibited until that follow-up passes. No live-11 directory
or login exists in this step.

Final gates all exit0: full pytest2165 passed/1 skipped,116.91s; mypy113 files;
Ruff clean; lint-imports6 kept/0 broken; design checker0 problem. Node three
entrypoints3 passed,22.81s (unit120/120,DOM50/50,safety4/4). Python count unchanged;
Node count increases by9. Ruling/frozen design and historical HTML unchanged.

```bash
git archive 5cf878164d9c9b7a983993788a46a70e3e74e40b | tar -x -C /tmp/p5q-c2b09-production-lint-di6avA
# cwd=/tmp/p5q-c2b09-production-lint-di6avA
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```
