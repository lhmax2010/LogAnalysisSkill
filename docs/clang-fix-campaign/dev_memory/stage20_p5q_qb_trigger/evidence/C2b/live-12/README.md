# P5Q C2B-10 live-12

Date: 2026-10-14. Baseline19792bb, production2ee8ab6. FatTank replied "开始"
before this session. One manual browser login; ping/pong preceded browser launch.
Result: **COLLECTED**, exit0, stop=null. No Ok/submit/Accept; no C3.
This archive does not close the outstanding R1 design differences.

## Invocation And Order

```bash
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD \
  ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-12 \
  .venv/bin/python full
```

The controller sent each command only after the preceding response. Login was
automatically sent after pong. Configuration1917 was obtained from this session's
verified parent archive before the read command, not guessed.

```jsonl
{"command":"ping"}
{"command":"read","path":"/build/1193467/overview"}
{"command":"read","path":"/build/1193467/variables"}
{"command":"read","path":"/build/1193469/overview"}
{"command":"read","path":"/build/1193469/variables"}
{"command":"read","path":"/build/1193469/step_status"}
{"command":"register_config","source_path":"/build/1193467/overview"}
{"command":"read","path":"/overview/1917"}
{"command":"form_evidence"}
{"command":"close"}
```

Final response:

```json
{"status":"COLLECTED","stop":null,"browser_closed":true,"profile_removed":true,"released":false}
```

## Observations

| Observation | Result | Evidence |
|---|---|---|
| Login | POST /signin302,GET /dashboard200;three conditions true | run.json:2442;diagnostics |
| Parent1193467 | overview/variables200,VERIFIED | 01.response.html;02.response.html |
| Child1193469 | overview/variables/step_status200,VERIFIED | 03.response.html;04.response.html;05.response.html |
| Child status | Summary Failed;parent Child Build FAILED | 03.response.html:828;01.response.html:892 |
| Config1917 | five source checks plus two config-page checks pass | run.json:2737/:2756;06.response.html |
| Initial form | Passed;PROJECT_NAME Tizen-Base-Toolchain | form-initial.html;run.json:2944 |
| Full -> Partial | field POST147147ms,response200147435ms,random0.3453609721766676 | run.json:2878/:2885/:2898 |
| Partial -> Full | field POST148678ms,response200148963ms,random0.6594204778800775 | run.json:2911/:2924 |
| Release / cleanup | form_action_releases0,released=false,runtime_failure=null;browser/profile removed | run.json:3870/:4064 |

All snapshots use `/wicket/page?10`, version10, action
`/wicket/page?10-1.IFormSubmitListener-form`. Registered callback:

```text
/wicket/page?10-1.IBehaviorListener.0-form-editor-content-basicProperties-1-property-editor-editor-wrapper-select
```

Actual requests append exactly one final `&random=<value>` as above. Original
callback/action/version do not change. No main-frame navigation or Document GET
in either transition window (run.json:3599/:3600/:3865/:3866). This does not prove
there was no DOM replacement; it proves no observed whole-page navigation.
Option text/value lists are unchanged; only BUILD_TYPE selected flags change.
BUILD_REFERENCE remains Ref. Snapshot, options Live/Ref. Snapshot/Snapshot Number;
SNAPSHOT_NUM remains the only option tizen-base-toolchain_20260924.094908.

The three serialized HTML files have the same hash. Runtime selection properties
need not update serialized selected attributes; run.json's three snapshots and
the two successful callback responses are the transition evidence.

Eight native-code samples: trim=false, other eight flags=true. Interceptor
request events: GET112/POST3,allowed77/denied38; responses200x63/302x2. POSTs are
one login and two field callbacks, zero build submissions. Denials: ckeditor10,
two bootstrap fonts9+9,refresh XHR10. Trace/wrapper38/38,ownership refusals0;
WORKER_BLOCKED/NEW_PAGE0. These are not server-receipt counts. No added allowlist.

`fields.log` mechanically extracts original names/display labels and source lines.
Parent target variable BUILD_PKG_LIST_MODIFY has four lines; child
BUILD_PKG_LIST245 lines includes all four. Child TRIGGER_ID1193467,FAIL_FAST=yes,
EACH_GBS_BUILD_STATUS present/empty. Parent Live/do not need select differs from
child Ref. Snapshot/SNAPSHOT_NUM_URL, as already recorded for R1.

## Integrity And Privacy

All nine HTML files were redacted in memory before archival and checked after
writing. Credentials/identity sets are not saved. Offline `PageRedactor.check_bytes`
was repeated on all HTML and run.json; it checks visible user fields and secret
markers but does not reconstruct the in-memory identity set from redacted pages.
`integrity-final.log` recomputes each pages[].sha256 and checks exact transitions,
config checks,native flags,traffic,cleanup and zero release. `hashes.log` includes
run.json and every HTML; historical live-11 and the frozen file remain unchanged.

run.json SHA256:
`e74fa531d4f8857912a0fbbf9f70ccbca4479a226ce8b41ef094f40c1d271a08`.

The initial ad-hoc offline check wrongly required a status key on form snapshots;
`integrity.log` preserves KeyError/exit1. Only read-page entries have that field.
The corrected check uses read-page HTTP status and separate field response events,
with raw archive unchanged; `integrity-final.log` exit0. No new QuickBuild request.

## Archive Gates

Commands below run from the repository root. Each log records its command and exit.
After live browser close, all browser tests use synthetic/local servers only.

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

| Gate | Result | Log |
|---|---|---|
| pytest | 2165 passed/1 skipped,118.52s,exit0 | pytest.log |
| mypy | 113 files,no issues,exit0 | mypy.log |
| lint-imports | 6 kept/0 broken,exit0 | lint-imports.log |
| design checker | 0 problem,exit0 | design-check.log |
| Node unit/DOM/safety | 142/142,51/51,4/4;3 pytest entries passed20.07s,exit0 | node-gates.log |
| Ruff complete staged tree | All checks passed!,exit0 | ruff.log |

Safety Worker group followed approved branchb: shared_worker closeTarget success,
worker Error, browser/profile cleaned,attackHTTP0/WS0. Other three groups passed.
No production,spike,test,frozen document,design.md or checker changes in this
archival commit; unrelated workspace edits/drafts are excluded.

Ruff checked staged tree80058cb1811f0422d813802e34c0641fd3b9006c exported to
/tmp/p5q-live12-lint-XClBU8; the export was removed afterwards. Only documentation
and logs were updated after that check. Original redacted HTML whitespace is
preserved, not reformatted to silence diff whitespace warnings.

R1 design review remains pending. A successful Base child sample and real submit
response/build-id mapping remain NOT_COLLECTED here. No new build was submitted.
