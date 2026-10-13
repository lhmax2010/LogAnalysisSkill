# live-08 Archive Validation

2026-10-13, code baseline962ad58; no source or test changes. Commands from
repository root unless indicated; all below exit0:

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

Logs: pytest.log (2165 passed/1 skipped,117.49s), mypy.log (113 source files),
lint-imports.log (6 kept/0 broken), design-check.log (0 problem), node-gates.log
(3 passed,19.38s; Node120/120+41/41+safety4/4). Browser tests use local fixtures.

Complete staged-tree Ruff check, exit0, ruff.log:

```bash
git archive 3aace796a64a902a944829a24566581d193b2ab3 | tar -x -C /tmp/p5q-live-08-lint-biq1PI
# cwd=/tmp/p5q-live-08-lint-biq1PI
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```

Only documentation and validation logs were added after that snapshot.
Unrelated unstaged user changes are not part of the staged tree.

evidence-check.log: exit0 for PageRedactor.check_bytes on six raw files,
jsessionid-value scans, five archived HTML hashes, run/frozen/live-07 hashes,
and structured checks of run order, login, config source (four pass/one fail),
no registration/form/release, cleanup, request/response counts and trace.
An offline stdlib HTMLParser verified child Summary Failed, parent FAILED,
four target lines contained in245 child package lines, required child variables,
reference observations and the21 displayed step names/statuses with line numbers.
Historical live directories passed git diff --exit-code HEAD.

Offline redaction has no remembered login identities. Live pre/post-write
checks used in-memory identities; none were exported. HTML is preserved without
reformatting. Whitespace checks apply to authored Markdown, not rewritten HTML.

The live evidence process exited1 with CONFIGURATION_SOURCE_MISMATCH. Offline
validation does not resolve that stop: no form was opened, release0, no retry/C3.
