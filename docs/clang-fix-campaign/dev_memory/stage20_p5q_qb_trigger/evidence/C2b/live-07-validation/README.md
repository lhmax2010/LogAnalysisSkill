# live-07 Archive Validation

2026-10-13, code baseline e683175. Only documentation and redacted evidence
changed. Full commands from repository root, unless indicated:

```bash
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
```

All exit0. Logs: pytest.log (2165 passed/1 skipped,115.49s), mypy.log
(113 source files), lint-imports.log (6 kept/0 broken), design-check.log
(0 problem), node-gates.log (3 passed,19.44s; Node120/120+41/41+safety4/4).
The Node entrypoints use local Chromium and synthetic local fixtures only.

Complete staged-tree Ruff check, exit0, ruff.log:

```bash
git archive 04b17a954d7ec3eb220868c474e5361c4b6e6665 | tar -x -C /tmp/p5q-live-07-lint-B3z2Sf
# cwd=/tmp/p5q-live-07-lint-B3z2Sf
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```

The export excludes unrelated unstaged user changes. Only documentation and
validation logs were added after that tree snapshot; no source changes.

evidence-check.log records exit0 for raw-byte PageRedactor.check_bytes, a
jsessionid-value scan, immutable run/frozen hashes, parsed run assertions
(ping/pong, login-only, no pages/config/form, GET47/POST0, HTTP200x38,
release0/cleanup), and git diff --exit-code HEAD for historical live directories.
The offline redactor has no remembered login identities; live pre/post-write
checks used the process's in-memory identities. No identities were copied out.

Validation success does not mean the live collection succeeded: live-07 exited1
with QB_LOGIN_TIMEOUT after600s, no login POST and no archived build pages.
No retry, no C3.
