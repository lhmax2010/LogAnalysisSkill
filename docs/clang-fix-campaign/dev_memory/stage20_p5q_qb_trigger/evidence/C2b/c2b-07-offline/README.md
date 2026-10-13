# C2B-07 Offline Validation

2026-10-13, baseline0f89d4f. Only spike configuration-source validation and its
test inputs changed; production, frozen design and historical evidence unchanged.

## Commands

Repository root; NODE denotes the two-part command
`env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code`.
PW=/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs;
CHROMIUM=/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome.

```bash
NODE tests/node/test_p5q_c2b_config_source.mjs PW CHROMIUM
NODE docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
NODE docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --id-self-test PW CHROMIUM .venv/bin/python
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
```

All exit0. Log results: config-source67/67 (was27, net+40 Node counts including
subtests), self-test22/22, id-self-test14/14, pytest2165/1 in109.30s,
mypy113 files, lint-imports6/0, design-check0 problem, node-gates3 passed in19.48s
(Node120/120+41/41+safety4/4). Pytest wrapper count is unchanged.
The three safety/browser entrypoints only use local synthetic fixtures.

Complete staged-tree Ruff, exit0, ruff.log:

```bash
git archive 9234e0897556f15922df41969375adcfb4785439 | tar -x -C /tmp/p5q-c2b-07-lint-xeWsfZ
# cwd=/tmp/p5q-c2b-07-lint-xeWsfZ
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```

Only documentation/logs were added after that tree snapshot. Unrelated unstaged
user changes were excluded. No new Python dependency, no QuickBuild/Gerrit request.

## Source Controls

Both ../ from a bare build address and ../../ from its overview address pass.
Same-origin absolute/root-relative links follow the approved URL resolution
rule. Each of overview/pipeline/children has separate query, fragment, foreign
origin, suffix, non-positive/non-integer and malformed URL negative cases;
missing/duplicate links and differing ids fail. HTML base cannot override the
archive address. Existing breadcrumb/copy-path/build-name/page/source controls
remain. The archived live-08 parent HTML passes all five new checks offline.

live08-offline-source-check.json separately rechecks the old run's facts with
parentConfigurationChecks and parentRegistration, after asserting both the run
SHA256 and source HTML hash. It records old checks and new checks separately,
mode=offline-only, network_requests=0 and live09_started=false. It does not
register anything in a live browser or rewrite live-08 evidence.

live-09 awaits a new chat start. No live page/form/release conclusion follows
from these offline tests; no C3.
