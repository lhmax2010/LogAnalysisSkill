# C3 Review Fixes And Stop Evidence

Baseline: `332878d6e595a139b850c2eac6ceaefb5fcec27d`.
Authority remains the immutable v1.5-FROZEN design, SHA256
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.

Status: **C3_STOPPED, P5Q-C3-01**. Only the two authorized C2c review fixes
are implemented. No qb-trigger CLI, state writes or transaction implementation
is claimed. Progress section 29 records the requirement, evidence and proposed
protocol clarification. Nothing in this directory closes C3 or the C5/C6 debts.

## Reproduction

The probe calls the real `Agent.fill` and `Agent.command` with synthetic DOM
snapshots and locator callbacks. It does not instantiate Chromium, navigate,
perform HTTP, or invoke submit. Both snapshots contain a valid single selected
snapshot, but neither contains the required frozen snapshot. The two distinct
selected values produce identical responses; the driver cannot recover them.

```bash
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD \
  ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C3/snapshot-response-probe.mjs
```

Exit 0; output: `snapshot-response-probe.json`. This means **the gap was
reproduced**, not that the C3 snapshot requirement passed.

Driver reproduction (run at repository root):

```python
import json
from pathlib import Path
from ci_triage.qb_browser import decode_response, QbBrowserError

path = Path('docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C3/snapshot-response-probe.json')
rows = []
for case in json.loads(path.read_text())['cases']:
    try:
        decode_response(json.dumps(case['response']), submit_sent=False, command='fill')
    except QbBrowserError as error:
        assert error.code == 'REJECTED_QB_SNAPSHOT_UNAVAILABLE'
        assert not hasattr(error, 'current') and not hasattr(error, 'current_snapshot')
        assert error.diagnostic is None
        rows.append({'source_current': case['current_in_snapshot'], 'error_attributes': vars(error)})
    else:
        raise AssertionError('expected rejection')
assert len(rows) == 2
assert rows[0]['error_attributes'] == rows[1]['error_attributes']
print(json.dumps({'cases': rows, 'current_value_available_to_cli': False}, indent=2))
```

Run with `.venv/bin/python`; exit 0; output `snapshot-driver-probe.json`.

## Scope

- Configuration rule 7 and derived child configuration path; three negatives
  and one positive. The CLI rejection/no-launch integration remains pending C3.
- Python resets identity columns at each new table header. Shared JSON fixture
  adds `repeated-header-resets-identity-columns`, exercised in Python and Node.
- No changes to the browser agent, driver, allow rules, frozen designs,
  design.md or checkers. No QuickBuild/Gerrit request or manual login.
- Unrelated user modifications and drafts excluded from this commit.

## Verification

All commands run from the repository root using the existing `.venv`, unless
noted. No dependencies were installed.

| Command | Result | Exit | Log |
|---|---|---|---|
| `.venv/bin/python -m pytest -v` | 2282 passed / 0 failed / 1 skipped; 256.98s | 0 | pytest.log |
| `.venv/bin/python -m pytest -v tests/unit/test_qb_config.py tests/unit/test_qb_redact.py` | 154 passed / 0 failed / 0 skipped | 0 | focused.log |
| `.venv/bin/mypy` | 113 source files, no issues | 0 | mypy.log |
| `.venv/bin/lint-imports` | 6 kept / 0 broken | 0 | lint-imports.log |
| `.venv/bin/ruff check .` in complete staged-tree export | All checks passed | 0 | ruff.log |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | 0 problem | 0 | design-check.log |
| Node unit command below | 152 passed / 0 failed / 0 skipped | 0 | node-unit.log |
| DOM/safety command below | 2 pytest entries passed; DOM 64, safety groups 4/4 | 0 | node-dom-safety.log |
| SHA256 and zero-diff check | authority unchanged, agent/driver unchanged | 0 | frozen-hashes.log |

```bash
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD \
  ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code --test \
  tests/node/test_qb_browser_agent.mjs

.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
```

Baseline 2277/1 -> 2282/1: four configuration cases and one shared-vector case.
Node leaf counts are not added to the pytest wrapper count. The repeated-header
vector passes in both implementations. Policy was not changed, but the four
local safety groups were rerun anyway: Worker/WebSocket, 307/308, credentials,
per-hop filtering. Server observations are in `node-dom-safety.log`; no real
QuickBuild endpoint was contacted (DNS maps to the local fake HTTPS server).

Ruff ran against staged tree `511932966057615ffab3ffb7a85202d0cacbb258`, exported
with `git archive` into `/tmp/p5q-c3-ruff-GHlM4b`. Later changes are only evidence
and documentation. This excludes the user's unrelated tracked/untracked work;
the temporary export was removed after validation.

C3 CLI groups (preconditions/idempotency, submission, freeze integration,
diagnostic persistence) and the idempotency-table mappings remain unimplemented.
These green regressions do not constitute C3 acceptance. The one open stop
is P5Q-C3-01; no implicit extension of the error protocol was made.
