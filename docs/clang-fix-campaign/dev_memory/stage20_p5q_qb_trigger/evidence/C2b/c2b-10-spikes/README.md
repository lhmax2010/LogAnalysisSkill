# C2B-10 Diagnostic Query Recording

Baseline2ee8ab6, production callback fix already pushed. Only spike code changes.
Exact lowercase random with the approved numeric grammar is retained verbatim;
Wicket listener keys are retained even beyond the ordinary 64-character key cap.
Bare listener keys remain bare. Values on listener keys remain redacted.
All other redaction and pre/post-write checks are unchanged.

Observation is not authorization: exponent values and duplicate random parameters
can be recorded, but are still rejected by production. Fourteen new offline
vectors cover these distinctions, long/non-listener keys, secret values, newline,
empty/negative/nonnumeric values and key case. No live requests or login.

```bash
node docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
node docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --form-self-test \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome .venv/bin/python
# Also --id-self-test and --intrinsics-self-test with the same arguments.
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety \
  tests/unit/test_qb_browser_node.py::test_node_c2b_configuration_source_checks
```

Ruff runs against the complete staged export; that temporary copy is removed
afterward. Logs adjacent. live-12 requires a new chat start and ping/pong.

Initial self-test log is retained as self-test-before-count-fix.log: all36
individual cases passed, but the old fixed summary still said22. The summary now
counts actual passing cases, and self-test.log reruns all36 with zero requests.
This is a reporting correction, not a changed assertion or redaction rule.

## Results

All exits0: query/channel36/36,form27/27,ID15/15,intrinsics12/12;
pytest2165 passed/1 skipped(120.89s),mypy113 files,Ruff clean,lint-imports6 kept,
design checker0 problem. Node four entrypoints4 passed(23.49s),unit142/142,
DOM51/51,configuration67/67,safety4/4. Worker approved branch(b): shared_worker
closeTarget succeeds, worker Error; browser/profile removed and attackHTTP0/WS0.
Ruff staged treebb8abe5a9d4a9ffc4b97b9b96810047a1e36fc99; export removed.
Frozen/live-11 hashes unchanged. Python nodeid count unchanged.
No production change after2ee8ab6. live-12 not yet collected; waiting for chat start.
