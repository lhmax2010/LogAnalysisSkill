# C2B-10 Current Field Callback Suffix

Baseline56b6d2b. Ruling verbatim: progress26.1. Frozen design unchanged.
Only Policy.allow fill POST matching changes. No query parsing/reordering,
stripping, prefix permissions, submit or refresh broadening. One-shot registration
is consumed for both exact and decimal-suffix requests; response processing is unchanged.

## Offline Coverage

22 added Node unit cases: four positives (including 1/20 fractional digits),
16 invalid suffixes, current-field/phase/POST isolation, and submit/refresh exclusion.
Invalid suffixes include duplicates, misplaced parameter, empty/negative/exponent/
alphabetic values, extra parameter, 21 digits, newline and encoding differences.
Every rejection retains the valid registration; every success consumes it.

One added real Chromium DOM/network case: local-only HTTP server, synthetic form,
current field registration and selectOption, two actual Math.random callback POSTs,
server echoes Partial then Full, one-shot completion and zero form-action release.
The test-only policy wrapper maps only its loopback server to the production origin;
all other hosts are rejected and external DNS is disabled. No QuickBuild requests.

## Commands

```bash
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
```

Logs are adjacent. Ruff checks the complete staged export, not a selection of
changed files; pre-existing unrelated user edits/drafts are excluded from the commit.
Generated lint export is removed after verification to avoid accumulating copies.
No live-12 session is started in this step. Next commit updates diagnostic recording.

## Results

All exits0: pytest2165 passed/1 skipped(119.15s), mypy113 files,
Ruff clean, lint-imports6 kept/0 broken, design checker0 problem.
Node entrypoints3 passed(28.92s): unit142/142(+22), DOM51/51(+1), safety4/4.
Python nodeid count unchanged. Worker safety follows approved branch(b):
shared_worker closeTarget succeeds, worker reports Error, browser/profile removed,
attackHTTP0/WS0. The other three groups pass unchanged.
Ruff tree303ab28330205afa574af59278201ef159ff1a64, exported directory removed.
hashes.log preserves frozen/live-11 hashes. No credentials or live responses added.
