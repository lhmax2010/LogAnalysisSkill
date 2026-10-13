# C2b Appendix C Evidence Status

Status: **PARTIAL / LIVE07_STOPPED_QB_LOGIN_TIMEOUT**. Latest session: live-07,
2026-10-13, zero archived build pages. Historical observations below are kept,
not substituted for the missing live-07 results.
This document records observations, not permission to start C3.

## C2B-06 live-07 (Latest Session)

Production a364489 and spike e683175 were already pushed and validated before
the fresh chat start. PTY ping/pong passed before browser creation
(live-07/run.json:845). The only command was login with a 600-second timeout
(run.json:4). GET /signin returned200 without a redirect (run.json:778);
no login POST was observed (run.json:869). The process waited for the login
deadline and stopped with QB_LOGIN_TIMEOUT, exit1 (run.json:840/:849).
This was not an EOF stop or a browser runtime failure.

| Requested item | live-07 result | Evidence |
|---|---|---|
| Login three-condition success snapshot | NOT_COLLECTED; timeout at /signin, no successful login result | run.json:840/:849 |
| 1193467 overview / variables | Both NOT_COLLECTED; not requested | run.json:4/:10 |
| 1193469 overview / variables / step_status | All NOT_COLLECTED; not requested | run.json:4/:10 |
| 1193469 Summary Status vs parent Child Build Result | NOT_COLLECTED; do not substitute historical parent summary | run.json:10 |
| Configuration id, five parent checks and two configuration checks | NOT_COLLECTED; no register_config, no historical id reused | run.json:4 |
| Parent/child variable shapes, reference values/options | NOT_COLLECTED in this run; previous R1 facts remain below | run.json:10 |
| Full -> Partial -> Full, callback/action/version/options/rerender/random | NOT_COLLECTED; no open_form/fill/submit | run.json:4 |
| Form action release count / state | 0 / released=false | run.json:863 |
| Browser and temporary directory cleanup | Both true | run.json:853 |

All source references in the table are under `live-07/`. No HTML page was
archived in this run. `run.json` SHA256 is
`79d07795dfa6d54647f9981ff7fe1884e5f860cc1e1e6037f5db5ec3869a533e`.

Request-stage interception records: GET47, allowed46/denied1, POST0;
response-stage records: 38 HTTP200. The only denied resource was
`/ckeditor/ckeditor.js?v=1701391813000`, Script (run.json:807), still denied
without a new registration. Trace/wrapper denials both1, frame-ownership
denials0; WORKER_BLOCKED/NEW_PAGE absent and runtime_failure=null
(run.json:855/:862). These are protocol-stage counts, not server receipt counts.
No 3xx login landing chain was obtained. Absence of POST does not establish why
the human login did not complete. No retry or production-rule changes followed.

Validation and command details: `live-07/README.md`, `live-07-validation/`,
progress22.6/22.7. Offline gates do not turn this stopped session into C2b
completion. The form assumptions remain unverified; C3 is not started.

## C2B-06 Preparation (Before live-07)

The approved ruling is recorded verbatim in progress22.1. The archived selected
Variables tab is visible at live-06/03.id-unverified.response.html:783-784 and
05.id-unverified.response.html:791-792. These are remembered tabs, not a changed
Summary schema. Production commit a364489 moves Summary identity checks to
explicit /build/N/overview and accepts only the exact observed Run button
onclick grammar. Historical live-06 status and bytes are unchanged.

live-07 will use verified overviews for configuration/child-id provenance and
1193469 as the Base failure sample; 1186372 is excluded from the new read plan.
The two reference-field values/options and callback/navigation observations
are added to the spike record. No new live pages, Summary Status, callbacks or
release results are claimed here; these remain NOT_COLLECTED pending a new
chat start and the live run.

The three R1 items remain design followups, not implemented rules: Full child
package list versus target subset; parent Live/reference display versus child
Ref. Snapshot/SNAPSHOT_NUM_URL; and the Unified sample's project/FAIL_FAST/comma
separator differences. C3 remains blocked until the required live evidence and
designer decisions, not unlocked by passing offline tests.

## C2B-05 live-06 (Historical Session)

Baseline93421b1, fresh chat start, PTY maintained throughout. Ping/pong passed
before browser startup (live-06/run.json:2414). One human login POST returned302;
the final /dashboard200 satisfied all three conditions: not_signin=true,
password_inputs=0, sign_out_links=1, empty query (run.json:2421).
No input EOF occurred. The run stopped at production open_form with
QB_FORM_CHANGED (run.json:2409), exit1. Browser/profile cleanup succeeded,
runtime_failure=null; form_action_releases=0, released=false (run.json:2634/:2843).

### Pages And Field Evidence

All references in this section are under `live-06/` unless stated otherwise.

| Requested item | Actual result | Source |
|---|---|---|
| 1193467 main / variables | Both HTTP200, VERIFIED | 01.response.html; 02.response.html; run.json:41 |
| 1193469 main | HTTP200, ID_UNVERIFIED, no Summary in either sample; not a source for ids | 03.id-unverified.response.html; run.json:2486 |
| 1193469 variables | HTTP200, VERIFIED; single Build (id:1193469) | 04.response.html:691; run.json pages |
| 1186372 main | HTTP200, ID_UNVERIFIED, no Summary in either sample | 05.id-unverified.response.html; run.json:2526 |
| 1186372 variables | HTTP200, VERIFIED | 06.response.html; run.json pages |
| 1186372 child | NOT_COLLECTED; skipped because main id was not verified, no child id extracted | run.json:2568 |
| Configuration1917 | HTTP200; five parent checks and two configuration checks passed | run.json:2572/:2591; 07.response.html |
| Child configuration suffix | RBS/build; this comes from VERIFIED variables, not unverified main | 04.response.html:4 |
| Parent Child Build structure | Repository-Architecture / QB Build URL / Build Result / Build Profiling | 01.response.html:882 |
| Parent Child Build row | One colon-joined string standard-armv7l:aarch64:x86_64, child1193469, FAILED | 01.response.html:890/:891/:892 |
| Parent Status | Failed, not a successful sample | 01.response.html:925 |
| Child1193469 Status / separate architecture status | NOT_COLLECTED; no Summary in unverified main, do not substitute parent result | run.json:2486 |
| Failure sample child Status / Build Result | NOT_COLLECTED; no extraction from unverified1186372 | run.json:2568 |
| Steps | NOT_COLLECTED; not in the latest C2B-05 read sequence | progress21.3 |
| Form Full -> Partial -> Full | NOT_COLLECTED; production open_form failed before any field operation | run.json:4/:2409 |
| Callback, form action, page-version change, options refreshed | NOT_COLLECTED; no report.form or form page archive | run.json |

The 1186372 unverified main title is
`QuickBuild - root/CI_TIZEN/TIZEN/Tizen/Tizen-Unified-Toolchain/RBS/TRIGGER - TIZEN_Tizen_Tizen-Unified-Toolchain_RBS_TRIGGER_20260930.020514`
(05.id-unverified.response.html:4), which is a recorded title only, not a
successful main-page verification or authorization to use its Child Build ids.
There is still no independently verified successful child sample in this run.

### Parent And Child Variables

Values are existing-build observations, not defaults for a future submission.
An empty display label below means that cell is actually empty. Presence/absence
refers to variable rows in the named page, not text substrings in other values.

| Build / requested field | Variable name | Display label | Actual value / shape | Source |
|---|---|---|---|---|
| 1193467 Build Package List | BUILD_PKG_LIST_MODIFY | Build Package List | Four git_path@commit rows: ncurses, pam, libtirpc, qemu-accel | 02.response.html:808 |
| 1193467 BUILD NOTES | BUILD_NOTES | BUILD NOTES | Empty | 02.response.html:808 |
| 1193467 BUILD_TYPE | BUILD_TYPE | Empty | Full | 02.response.html:808 |
| 1193467 BUILD_REFERENCE | BUILD_REFERENCE | Empty | Live | 02.response.html:808 |
| 1193467 SNAPSHOT_NUM | SNAPSHOT_NUM | Empty | do not need select | 02.response.html:808 |
| 1193467 PROJECT_BRANCH | PROJECT_BRANCH | Empty | tizen_base | 02.response.html:808 |
| 1193469 parent binding | TRIGGER_ID | Empty | 1193467 | 04.response.html:800 |
| 1193469 packages | BUILD_PKG_LIST | Empty | 245 git_path@commit rows | 04.response.html:800 |
| 1193469 fail-fast | FAIL_FAST | Immediate Stop With Error | yes | 04.response.html:800 |
| 1193469 result rows | EACH_GBS_BUILD_STATUS | Empty | Present, empty string, not parsed as a successful result | 04.response.html:800 |
| 1193469 arches | REPO_ARCH / ARCHITECTURE | Empty | standard-armv7l:aarch64:x86_64 / armv7l:aarch64:x86_64 | 04.response.html:800 |
| 1193469 own trigger variable | QB_TRIGGER_ID | Empty | 1193469; distinct from TRIGGER_ID=1193467 | 04.response.html:800 |
| 1186372 project / reference | PROJECT_NAME / PROJECT_BRANCH / BUILD_REFERENCE | Empty | Tizen-Unified-Toolchain / tizen / Snapshot Number | 06.response.html:813 |
| Failure sample child four variables | TRIGGER_ID / BUILD_PKG_LIST / FAIL_FAST / EACH_GBS_BUILD_STATUS | NOT_COLLECTED | Child skipped; do not substitute its parent's variables | run.json:2568 |

### Configuration Checks And Form Stop

| Check | Actual fact | Source |
|---|---|---|
| One Overview tab, exact relative href | ../overview/1917 | 01.response.html:696/:698 |
| Sibling tabs agree | ../pipeline/1917 and ../children/1917 | 01.response.html:711/:715 |
| Breadcrumb exact, last TRIGGER current | root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER | 01.response.html:640/:672; run.json:2430 |
| Copy-path exact | Same full path | 01.response.html:93 |
| Build-name prefix | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261009.072553 | 01.response.html:736 |
| Config page breadcrumb and copy-path exact | Both match the above path | 07.response.html:93; run.json:2591 |
| Config title | QuickBuild - root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER | 07.response.html:4 |

Only this fresh verified parent supplied register_config. No historical id
was backfilled. Copy-path remains a possible production path-check source,
recorded without changing production behavior.

The archived configuration has a **button**, not an anchor, titled
`Run the configuration`, with no href. Its onclick contains
`window.location.href='../wicket/page?9-1.ILinkListener-run'`
(07.response.html:722). Production `openForm` gets href at
`tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs:509` and raises
QB_FORM_CHANGED if absent at :510. In this run it re-navigated to the overview,
received200, then returned QB_FORM_CHANGED; no form Document navigation is
recorded. The reread DOM was not archived separately, so this is a source/nearby
page comparison, not an invented failure stack. No attempt to click via onclick,
repair production, retry, or register new resources was made. Resolving this
production premise requires designer review; all form observations stay
NOT_COLLECTED. Release count is **0**, not_released.

### Two-Sample Structure Facts (Verbatim Objects)

Source: run.json:2486 and :2526. The 3039ms/3041ms gaps meet the requested
three-second delay; neither diagnostic refreshed or navigated. Empty arrays
are actual samples, not missing evidence. No non-Id cell text was collected.

```json
{
  "path": "/build/1193469",
  "samples": [
    {
      "sample": 1,
      "relative_ms": 201291,
      "main_frame": {
        "protocol": "https:",
        "host": "quickbuild.tizen.org",
        "path": "/build/1193469",
        "query": ""
      },
      "ready_state": "complete",
      "navigation_count": 1,
      "navigation_labels": [
        "Build (id:1193469)"
      ],
      "build_summary_count": 0,
      "build_summaries": []
    },
    {
      "sample": 2,
      "relative_ms": 204330,
      "main_frame": {
        "protocol": "https:",
        "host": "quickbuild.tizen.org",
        "path": "/build/1193469",
        "query": ""
      },
      "ready_state": "complete",
      "navigation_count": 1,
      "navigation_labels": [
        "Build (id:1193469)"
      ],
      "build_summary_count": 0,
      "build_summaries": []
    }
  ],
  "file": "03.id-unverified.response.html"
}
```

```json
{
  "path": "/build/1186372",
  "samples": [
    {
      "sample": 1,
      "relative_ms": 249025,
      "main_frame": {
        "protocol": "https:",
        "host": "quickbuild.tizen.org",
        "path": "/build/1186372",
        "query": ""
      },
      "ready_state": "complete",
      "navigation_count": 1,
      "navigation_labels": [
        "Build (id:1186372)"
      ],
      "build_summary_count": 0,
      "build_summaries": []
    },
    {
      "sample": 2,
      "relative_ms": 252066,
      "main_frame": {
        "protocol": "https:",
        "host": "quickbuild.tizen.org",
        "path": "/build/1186372",
        "query": ""
      },
      "ready_state": "complete",
      "navigation_count": 1,
      "navigation_labels": [
        "Build (id:1186372)"
      ],
      "build_summary_count": 0,
      "build_summaries": []
    }
  ],
  "file": "05.id-unverified.response.html"
}
```

### Denials And Boundaries

Request-stage observations: GET112 (71 allowed,41 denied), POST1 (human login
only). Response observations: 200x59,302x1. These are interception records, not
server-side counts. Denials: ckeditor Script10; bootstrap-icons .woff/.woff2
Font9 each; Wicket XHR13. Trace and wrapper each report41, ownership difference0.
WORKER_BLOCKED/NEW_PAGE=0. Existing random-query refresh rejection remains
unchanged. No resource was newly registered and no causal link between a denied
resource and the form error is asserted. No Ok/Accept/build submission occurred.

Raw report SHA256:
`e13a202e2e245052160d2da140a36b5d1e10ecdf387c3d2901ed7bd5cbd53213`.
All HTML was redacted before writing and checked after writing with in-memory
identities. Archived-byte recheck: `live-06-validation/redaction-check.log`.
Frozen design unchanged; live-01 through live-05 unchanged. No C3.

## C2B-05 live-05 (Historical Login-Only Session)

A fresh chat start preceded login. One human POST /signin returned302,
/dashboard returned200, and all three login conditions passed
(`live-05/run.json:1236`). The assistant launched without a PTY; the execution
tool reported stdin closed when sending the first read command. This is a launch
error, not an identity or QuickBuild failure. See `live-05/README.md` for the
verbatim error and preserved raw report status.

By the approved pre-live-06 supplement (progress21.7), live-05's preserved
`RUNNING` is precisely an input EOF without a close command, now classified as
`STOPPED / EVIDENCE_STDIN_CLOSED`. Its run.json is not rewritten. The evidence
entry now requires ping/pong before any browser startup and records unexpected
EOF explicitly. live-06 remains pending a fresh chat start; no new live facts
are implied by this preparation.

| Requested item | Result | Source |
|---|---|---|
| 1193467 main/variables | NOT_COLLECTED; first read never reached process | run.json:4; :10 |
| 1193469 main/variables | NOT_COLLECTED | run.json:4; :10 |
| 1186372 main/variables and its child | NOT_COLLECTED; child id not obtained | run.json:4; :10 |
| ID_UNVERIFIED samples | NOT_COLLECTED; no build page read, not an empty-facts result | run.json:10 |
| Configuration id and five parent/two config checks | NOT_COLLECTED; not backfilled from live-04 | run.json:4 |
| Form callbacks/action/version/options | NOT_COLLECTED; no open_form or field changes | run.json:4 |
| Release / cleanup | 0 / false; browser and profile removed | run.json:1245; :1295 |

All source references in this table are within `live-05/`. No page HTML was
archived. No runtime failure or WORKER_BLOCKED/NEW_PAGE occurred. The nine
denials were two Script, two Font and five dashboard XHR; no rules were changed.
No automatic retry follows. Existing live artifacts remain unchanged, and the
cause of live-04's identity mismatch is still unobserved.

## C2B-05 Preparation (No New Live Evidence)

The approved C2B-05 evidence-only diagnostic channel is implemented in the spike,
not in production read. Its offline fixtures pass (10/10, network requests=0;
`c2b-05-preparation/id-self-test.log`). Duplicate Build labels, absent Summary,
and delayed Summary each produce two samples, at least three seconds apart.
Unverified pages cannot supply a configuration or child build id; no non-Id
cell text is recorded in the structure samples. The previous failure cause is
not inferred from these synthetic fixtures.

At preparation time live-05 had not started and required a fresh chat "开始".
Its subsequent login-only execution stop is recorded above. Existing
live-01 through live-04 artifacts are unchanged. Exact refresh requests carrying
an appended random query remain rejected; that issue is deferred to C4 design
verification, not changed by this evidence channel.

## C2B-04 live-04 (Historical Build Evidence)

A fresh chat start preceded the single browser login for this session. GET
/signin returned200, the human login POST returned302, /dashboard returned200.
The three conditions passed: non-signin, password_inputs=0, sign_out_links=1,
empty query (live-04/run.json:1673). No terminal credentials or cookies stored.

### Pages And Appendix Fields

| Item | Actual result | Source |
|---|---|---|
| Parent1193467 main and variables | HTTP200; both archived after identity verification | live-04/run.json:23; :29 |
| Child1193469 main | HTTP200 Document then QB_READ_ID_MISMATCH; no HTML returned/archived | live-04/run.json:19; :1648; :1665 |
| Child1193469 variables, path suffix, Status, TRIGGER_ID, BUILD_PKG_LIST, FAIL_FAST, EACH_GBS_BUILD_STATUS | NOT_COLLECTED; not inferred from parent | live-04/run.json commands |
| Failed sample1186372 and its child | NOT_COLLECTED; no request after stop | live-04/run.json commands |
| Configuration id from parent | 1917, all five checks true; not registered before stop | live-04/run.json:1682; :1722 |
| Configuration page title and its breadcrumb/copy checks | NOT_COLLECTED; /overview/1917 not requested | live-04/run.json commands |
| Child Build columns | Repository-Architecture / QB Build URL / Build Result / Build Profiling | live-04/01.response.html:882 |
| Child Build row | Exactly standard-armv7l:aarch64:x86_64; child1193469; Build Result=FAILED | live-04/01.response.html:890; :891; :892 |
| Parent Status | Failed; this does not establish a successful sample or child status | live-04/01.response.html:925 |
| Per-architecture status | NOT_COLLECTED; the parent row is one colon-joined architecture string | live-04/01.response.html:890 |
| Steps pages | NOT_COLLECTED; excluded from the latest C2B-04 read order | progress20.2 |
| Form Full -> Partial -> Full | NOT_COLLECTED; no open_form/fill/submit | live-04/run.json commands |
| Form callback/action/version/options changes | NOT_COLLECTED | live-04/run.json commands |
| Release / cleanup | form_action_releases=0, released=false, browser/profile removed | live-04/run.json:1733; :1843 |

### Configuration Source Checks

| Approved check | Actual result | Source |
|---|---|---|
| One Configuration Overview tab link | ../overview/1917, exact relative shape | live-04/01.response.html:696; :698 |
| Matching Pipelines and Children ids | ../pipeline/1917 and ../children/1917 | live-04/01.response.html:711; :715 |
| Breadcrumb path; last TRIGGER current | root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER; no link on TRIGGER | live-04/01.response.html:640; :672 |
| Copy-path literal matches | Same full configuration path, onCopyClipboardLinkDomReady parameter | live-04/01.response.html:93 |
| Build-name prefix | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261009.072553 | live-04/01.response.html:736 |

All five are from the freshly archived parent (run.json:1722), not live-03.
The build-page title is `QuickBuild - root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER - TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261009.072553`
(01.response.html:4). It is not the unread configuration-page title.
Copy-path strings may be a source for production open_form path checks; recorded
only, with no change to production open_form in this ruling.

### Parent Variable Mapping

All rows are at live-04/02.response.html:808. Empty label means the actual middle
cell is empty. Values below are observations from an existing build, not future
submission defaults or assertions about the unread child variables.

| Form field | Variable name | Display label | Actual value |
|---|---|---|---|
| Build Package List | BUILD_PKG_LIST_MODIFY | Build Package List | Four git_path@commit rows, separated by br: ncurses/pam/libtirpc/qemu-accel |
| BUILD NOTES | BUILD_NOTES | BUILD NOTES | Empty string |
| BUILD_TYPE | BUILD_TYPE | Empty | Full |
| BUILD_REFERENCE | BUILD_REFERENCE | Empty | Live |
| SNAPSHOT_NUM | SNAPSHOT_NUM | Empty | do not need select |
| PROJECT_BRANCH | PROJECT_BRANCH | Empty | tizen_base |
| Immediate Stop With Error | FAIL_FAST | Immediate Stop With Error | yes |
| CHILD_CONFIGURATIONS | CHILD_CONFIGURATIONS | Empty | standard-armv7l:aarch64:x86_64 |

### Stop And Denials

One unresolved stop: **P5Q-C2B-05 / QB_READ_ID_MISMATCH** on child1193469.
The main frame reached /build/1193469 at125744ms and closed at126290ms; browser
disconnected at126568ms (run.json:1648). Production read rejects before returning
redacted HTML. No child DOM or candidate id values were archived, so the evidence
does not distinguish a missing/duplicate/different id or a timing issue. No
selector change, retry, workaround or extra request was made. A diagnostic path
preserving the rejection needs a further ruling before collecting these facts.

Denied requests: ckeditor script5, bootstrap-icons woff/woff2 total8, idle XHR8.
The ckeditor query is v=1701391813000 (run.json:1351); none was registered.
trace DENIED=wrapper_denied=21; frame-ownership difference0; WORKER_BLOCKED=0,
NEW_PAGE=0, runtime_failure=null. Thus this is a read check failure, not target
interception failure. These denials alone do not establish why the id check failed.
Request-stage observations: GET82 (61allowed/21denied), POST1allowed (human login
only); observed responses200 x49 and302 x1. These are interception counts, not
server-receipt measurements. Form action releases0; no build submission.

### Validation

Evidence-only commit, no production/test/spike changes. Full regression:
2165 passed/1 skipped (177.67s), mypy113 files, ruff complete staged tree,
lint-imports6 kept/0 broken and design checker0 problems. Local safety rerun4/4;
all exit0. Logs: c2b-04-live-validation/. Both archived pages and run.json passed
the raw-byte redaction recheck; listener/copy function names remain intact.
Frozen design and live-03 are unchanged. Passing offline gates does not resolve
the live read-id stop.

## C2B-04 Evidence Correction

**live-03 页面存在显示名子串误替换,只作参考,不作为字段形态证据**。
The archived live-03 files remain byte-for-byte unchanged. The historical excerpts
below are reference only, not field-shape evidence. Replacement parent-page
evidence from live-04 is recorded above; the child/configuration/form evidence
remains NOT_COLLECTED after the read-id stop. No configuration id was registered
from live-03. The copy-path string may be a source for production open_form path
verification; this is recorded only, with no production open_form change.

Offline preparation: redaction fix `6028356` (full2164/1, Node120+29,
safety4/4); configuration-source fixture27/27 and diagnostic self-test20/20.
The evidence entry requires a freshly archived parent response and records all
five checks before registering an id. It rechecks the configuration page's
breadcrumb and copy-path string before form_evidence. Fixture results do not
substitute for the separately recorded live-04 results above.

Historical status: **PARTIAL / STOPPED_CONFIG_LINK_SOURCE** for live-03,
after registration commit `3013899`. Login succeeded; the parent main page and
variables page were collected. Historical live-01/live-02/live-02b/live-02c
evidence and the frozen appendix remain unchanged.

## C2B-03 Full Session live-03 (Historical Reference Only)

FatTank replied with a separate chat start for the second session. The existing
production agent and evidence entry were run unchanged, with a 600-second login
timeout. Precondition: Node safety 4/4 and full2155/1 after landing registration
(c2b-03-landing/safety.log, pytest.log). This session stops at a source-location
mismatch; it does not complete C2b or authorize C3.

### Login And Pages

| Observation | Actual result | Source |
|---|---|---|
| GET /signin | HTTP200, 591/1588ms | live-03/run.json:1367, :1381 |
| Human POST /signin?0-1.IFormSubmitListener-content-form | HTTP302, 333660/334620ms | live-03/run.json:1409, :1423 |
| Redirect GET /dashboard, empty query | Allowed, HTTP200, 334624/335055ms | live-03/run.json:1437, :1451 |
| Three login conditions | not_signin=true; password_inputs=0; sign_out_links=1 | live-03/run.json:1754 |
| /build/1193467 | HTTP200, id verified; archived 01.response.html | live-03/run.json:19 |
| /build/1193467/variables | HTTP200, id verified; archived 02.response.html | live-03/run.json:25 |
| /build/1193467/step_status | NOT_COLLECTED, stopped before read | live-03/run.json:4 command list |
| Child 1193469, three pages | NOT_COLLECTED; id observed only in parent link | live-03/01.response.html:891 |
| Failed sample1186372 and its child | NOT_COLLECTED, including RBS path verification | live-03/run.json:4 command list |
| RBS configuration page | NOT_COLLECTED; candidate1917 not registered/requested | live-03/observations.json configuration_tab |

Parent title:
`QuickBuild - root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER - TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261009.072553`
(01.response.html:4). This is the build-page title, not a substitute for the
unread configuration-page title. Parent Summary Status is `Failed` (01:925),
so this session does not establish a successful sample.

### Parent Variable Mapping

Each row is present at live-03/02.response.html:808. Multiple table rows share a
single source line; observations.json retains the parsed row boundaries and values.
Blank display label means the actual middle cell is blank, not an inferred label.

| Form field | Actual variable name | Display label | Observed value |
|---|---|---|---|
| Build Package List | BUILD_PKG_LIST_MODIFY | Build Package List | Four git_path@commit lines: ncurses, pam, libtirpc, qemu-accel; full values in observations.json |
| BUILD NOTES | BUILD_NOTES | BUILD NOTES | Empty string |
| BUILD_TYPE | BUILD_TYPE | Blank | Full |
| BUILD_REFERENCE | BUILD_REFERENCE | Blank | Live |
| SNAPSHOT_NUM | SNAPSHOT_NUM | Blank | do not need select |
| PROJECT_BRANCH | PROJECT_BRANCH | Blank | tizen_base |

The parent also contains FAIL_FAST=yes (display label Immediate Stop With Error)
and CHILD_CONFIGURATIONS=standard-armv7l:aarch64:x86_64 at the same source line.
These are not evidence for the unvisited child's variables. Existing sample
parameters are not asserted to equal future tool-submission parameters.

### Child Build Table

The heading is at01:879. Columns at01:883 are Repository-Architecture,
QB Build URL, Build Result, Build Profiling. There is one body row: exact
`standard-armv7l:aarch64:x86_64` at01:890, child1193469 link at01:891,
`FAILED` at01:892. The architecture cell contains no extra text; this observation
supports exact colon-joined comparison for this sample only. Child Status,
TRIGGER_ID, BUILD_PKG_LIST, FAIL_FAST and EACH_GBS_BUILD_STATUS remain NOT_COLLECTED;
the parent summary/table cannot supply them.

### Stop: P5Q-C2B-04 OPEN

The task prescribes an ordinary overview link from the parent's **breadcrumb**.
Actual `#breadcrumb` starts at01:640, with ancestor `*.latest` links and a plain
TRIGGER span at01:672. DOM enumeration finds zero overview links in that subtree.
A separate Configuration Overview navigation tab at01:698 contains
`../overview/1917`, resolving to `https://quickbuild.tizen.org/overview/1917`.
See observations.json for the complete breadcrumb href list and separate tab.

The script was stopped without substituting the tab for the specified source:
no register_config, no configuration GET, no open_form/fill/submit. Proposed
disposition, NOT implemented: approve the exact ordinary Configuration Overview
tab link from the same archived parent, retaining same-origin HTTPS, empty-query,
literal /overview/<digits> and full configuration-path checks. This is a task
source-location discrepancy, not an asserted unsafe-browser failure.

### Denials, Form Linkage And Cleanup

| Denied group | Count / phase | Source |
|---|---|---|
| /ckeditor/ckeditor.js?v=1701391813000 | 4; login2/read2 | run.json:1395, :1465, :1591, :1647 |
| /images/fonts/bootstrap-icons.woff2 and .woff | 6; login2/read4; non-v query masked | run.json:1479, :1493, :1605, :1619, :1661, :1675 |
| /wicket/page dashboard gadget XHR | 5; login; listener plus masked random | run.json:1507 through :1563 |
| /wicket/page refresh XHR | 3; idle; masked action/random | run.json:1577, :1633, :1689 |

All stayed denied; no post-login registration was added. Rejected dashboard/refresh
XHR with random is not a BUILD_TYPE callback observation and does not authorize
loosening the form rule. Login still met all three conditions.

GET88 attempts (70allowed/18denied); POST1allowed (human login only).
Response observations: HTTP200=58, HTTP302=1. Counts are browser interception
observations, not server receipt counts. TraceDENIED=18, wrapperDENIED=18,
frame-ownership difference=0; no WORKER_BLOCKED or NEW_PAGE, runtime_failure=null.
The observation stop returned exit1, browser_closed=true and profile_removed=true.
Form action releases=0, released=false. BUILD_TYPE Full -> Partial -> Full and all
form callback/action/version/options evidence remain NOT_COLLECTED. No Ok click,
configuration run or build submission occurred. Both authorized sessions are used;
no retry or C3 work follows this stop.

All three source files passed qb_redact byte checks before/after writing and
independent offline rechecking. SHA256 anchors:

| File | SHA256 |
|---|---|
| live-03/01.response.html | 37a6c160ff28b158b9696c1410780d027e1b8bac2f2906755a85d2f0d49871ff |
| live-03/02.response.html | 22a32b0f94c2e6e06ebb38f8692008b5b2132c1bcf14aa25d73952763666147d |
| live-03/run.json | 5840de6fcf50ca272bcc4c0029f84798d4b1dd079d5e6487a61a8acf1dff7597 |

## C2B-03 Diagnostic live-02c (Historical)

The chat start gate was honored. Only login was issued. All Document requests
below have protocol HTTPS and host quickbuild.tizen.org:

| Complete Document chain | Actual result | Source |
|---|---|---|
| GET /signin, empty query | Allowed, HTTP200; 592/1575ms | live-02c/run.json:807, :821 |
| POST /signin?0-1.IFormSubmitListener-content-form | Allowed, HTTP302; 61135/61535ms | live-02c/run.json:849, :863 |
| GET /dashboard, empty query | redirect_hop=true, denied by previous rule; 61539ms | live-02c/run.json:877 |

**Registration permitted by C2B-02:** exact `/dashboard` only, login-stage GET
Document with empty or entirely numeric query. Same origin, literal path,
no semicolon or prohibited prefix; one path out of the approved maximum three.
No static resource was registered. Denied Script `/ckeditor/ckeditor.js` query
`v=1701391813000` (live-02c/run.json:835) is not proven to block login; it remains
denied. Font rules also remain unchanged.

Ending: DIAGNOSTIC_DONE / POST_3XX_DENIED_DOCUMENT_QUIET_5S at66547ms;
the tool closed the browser at the diagnostic stop condition. The consequent
QB_LOGIN_ABORTED reply is not evidence of a human abort or failed authentication.
Three-condition success remains NOT_COLLECTED. Browser/profile removed,
runtime_failure=null, WORKER_BLOCKED=0, NEW_PAGE=0. Sources:
live-02c/run.json:918, :922, :926, :940.

GET48 (46allowed/2denied), POST1allowed; responses HTTP200=38 / HTTP302=1.
These are interception observations, not server receipt counts.
Trace DENIED=2 / wrapper denied=2 / frame-ownership difference=0.
Form action releases=0, released=false (live-02c/run.json:941).
Pre/post-write qb_redact checks passed; run.json SHA256:
`4dba9db4693d8df0ba7e18a22e3b270d67d78e8cd3380f7be57954bcd1f333b6`.

Live-03 requires a separate chat start response after registration verification,
commit and push. No reads or form operations were performed in this diagnostic.

## Previous Stop Context

C2B-01 corrected the fixture;
all four local safety groups passed before the single live browser session.
See [safety-c2b-01.log](safety-c2b-01.log) and progress section 17.
The live session stopped with QB_LOGIN_ABORTED. No retry, build-page read,
configuration read or form interaction followed. The frozen appendix is unchanged.

## C2B-02 Supplemental Diagnostic (Historical live-02b)

The chat start gate was honored; FatTank replied to reopen the QB window before
the single live-02b session. Login ran for 600 seconds and ended QB_LOGIN_TIMEOUT.
There was a login POST, but no HTTP 302 and no successful three-condition snapshot.
All network addresses in the following tables are on `https://quickbuild.tizen.org`.

| Complete Document sequence | Actual result | Evidence |
|---|---|---|
| GET /signin | Allowed, HTTP200; 474/1469ms | live-02b/run.json:852/866 |
| POST /signin?0-1.IFormSubmitListener-content-form | Allowed, HTTP200, not 302; 38966/39449ms | live-02b/run.json:894/908 |
| POST /wicket/page?1-1.IFormSubmitListener-content-form | Denied, no response status; 57776ms | live-02b/run.json:964 |

All redirect_hop fields are false. Main-frame navigation: `/signin`, then
`/signin?0-1.IFormSubmitListener-content-form`, then local browser error page
`chrome-error://chromewebdata/` (not an external network Document).
Sources: live-02b/run.json:980/988/996. No response body was read, so the meaning
or cause of the login POST's HTTP200 is not inferred.

| Denied static resource | Sanitized query | Count / source |
|---|---|---|
| /ckeditor/ckeditor.js | v=1701391813000 | 2; live-02b/run.json:880/922 |
| /images/fonts/bootstrap-icons.woff2 | 8d200481aa7f02a2d63a331fc782cfaf=<REDACTED len=0> | 1; live-02b/run.json:936 |
| /images/fonts/bootstrap-icons.woff | 8d200481aa7f02a2d63a331fc782cfaf=<REDACTED len=0> | 1; live-02b/run.json:950 |

**Registration: none, STOPPED_LOGIN_SCOPE.** The later Wicket POST is outside the
approved GET landing registration and its `/wicket/` path is explicitly excluded.
The ckeditor URL fits the static URL shape, but it is not proven to block the
three login conditions; no registration is justified. Font queries do not meet
the approved empty/numeric-v shape. No production rule was changed or retried.

Counts: 51 GET attempts (47 allowed/4 denied), 2 POST attempts (1 allowed/1 denied),
40 observed HTTP200 responses, 0 HTTP302. These are interception counts, not server
receipt counts. Trace DENIED=5 / wrapper denied=5 / frame-ownership difference=0.
No WORKER_BLOCKED or NEW_PAGE; runtime_failure=null. Browser/profile removed;
form_action_releases=0, released=false (live-02b/run.json:1021/1050/1051).

The report passed pre/post-write qb_redact checks. SHA256:
`7c634c97c4dd780f9ee6af843a7086e4009080372f0e001e1821f79458ad4728`.
Step 2 registration and step 3 live-03 were NOT_RUN. No build/configuration page,
form field interaction or build submission followed; no C3 work was started.

## C2B-02 Diagnostic (Historical live-02)

Only `login` was issued, with a 600-second timeout. Neither successful login nor
the POST-302/denied-Document/5-second-quiet ending condition occurred. The agent
ended with `QB_LOGIN_TIMEOUT`; this is not `DIAGNOSTIC_DONE`.

| Item | Actual fact and source |
|---|---|
| Initial document | `https://quickbuild.tizen.org/signin`, empty query, GET, HTTP 200; live-02/run.json:779 |
| Post-login landing | NOT_COLLECTED. No login POST/302 or rejected Document observed |
| Rejected static resource | `https://quickbuild.tizen.org/ckeditor/ckeditor.js`, GET Script, query `v=<REDACTED len=13>`, redirect_hop=false; live-02/run.json:807 |
| Main-frame navigation | Only `/signin`, 2085ms; live-02/run.json:823 |
| Automatic close | page_close 600469ms; browser_disconnected 600478ms; live-02/run.json:831 |
| Login response | QB_LOGIN_TIMEOUT; live-02/run.json:845 |
| Login three-condition snapshot | NOT_COLLECTED; only the navigation observation above is available |
| Denial reconciliation | trace 1 / allow wrapper 1 / frame-ownership difference 0; live-02/run.json:861 |
| Safety stops | No WORKER_BLOCKED/NEW_PAGE; runtime_failure=null; live-02/run.json:851/858 |
| Cleanup and release | browser_closed/profile_removed=true; action release=0, released=false; live-02/run.json:849/859 |

Request-stage observations: 47 GET (46 allowed, 1 denied), POST 0. Observed
responses: 38 x HTTP 200. These are interception counts, not server receipt counts.
The report passed independent qb_redact byte checks before and after writing.

**Registration decision: NOT_RUN, insufficient observation.** No landing chain
was captured, so its compliance with the approved scope cannot be established.
The rejected same-origin script is not proven to block login. Its masked query
length does not prove a numeric version value. It remains denied; no resource or
landing was registered, and production rules remain unchanged. No downgrade,
session path or foreign Document was observed, which is not proof of an unobserved
post-login chain's safety.

Step 3 / live-03 was not started. All build/configuration facts and form linkage
below remain NOT_COLLECTED. No second login, no Ok click, no build submission.
Previous live-01 evidence is unchanged and does not substitute for this diagnostic.

## Local Safety Prerequisite

| Group | Result and source |
|---|---|
| Worker/WebSocket | PASS, branch (b); attack HTTP=0 / WS handshake=0; shared_worker closeTarget success=true; worker closeTarget exception category Error; browser already closed/profile already removed before test-finally cleanup. safety-c2b-01.log:1 |
| 307/308 | PASS; neither second hop received; legal 302 positive reached /build/999. safety-c2b-01.log:2 |
| Per-hop | PASS; REST/promote/external second hops and 307 POST replay all zero. safety-c2b-01.log:3 |
| Credentials | PASS; actual synthetic credentials observed at local server, absent from redacted protocol and adapter-error output. safety-c2b-01.log:5 |

## Live Observation And Stop

| Observation | Evidence |
|---|---|
| Only login command issued; no page evidence collected | live-01/run.json:3, live-01/run.json:8 |
| Initial GET /signin permitted, HTTP 200 | live-01/run.json:9 |
| One human login POST /signin permitted; HTTP 302 | live-01/run.json:775, live-01/run.json:784 |
| Following Document attempts denied, recorded path shape <other> | live-01/run.json:793; 12 request-stage records in total |
| One denied Script request, recorded path shape <other> | live-01/run.json:280 |
| Final error QB_LOGIN_ABORTED, operation login, initiating path /signin | live-01/run.json:902 |
| Browser closed and profile removed | live-01/run.json:907 |
| WORKER_BLOCKED=0, NEW_PAGE=0; runtime_failure=null | live-01/run.json:909, live-01/run.json:976 |
| Form action releases=0, released=false | live-01/run.json:977 |

The login command was configured for 600 seconds; it returned an abort, not a
timeout. No actor or cause of page closure is inferred. The login-success
three-condition snapshot was not produced, so authentication success and actual
post-login landing remain unverified.

The trace intentionally preserves path shapes only. It does not contain the
actual rejected destination/host/query, so the denied Documents cannot be
retrospectively identified or proposed for allowlisting. The Script's exact
static-resource path likewise was not retained. No attempt was made to broaden
the rules, retry login, or reconstruct these values from other samples.

Request-stage metadata counts: 59 GET attempts (46 permitted, 13 denied),
1 permitted human-login POST; response-stage observations 38 x HTTP 200,
1 x HTTP 302. These are browser interception observations, not server receipt
counts; repeated font attempts are counted separately. Build/form POST=0.

## Appendix C Items

| Required observation | Status |
|---|---|
| RBS overview_id, breadcrumb source and configuration title | PARTIAL: candidate1917 is a separate tab, breadcrumb overview count0; config page NOT_COLLECTED, source approval pending |
| Parent variables: Build Package List, BUILD NOTES, BUILD_TYPE, BUILD_REFERENCE, SNAPSHOT_NUM, PROJECT_BRANCH | COLLECTED for1193467: six mappings in live-03/02.response.html:808; not collected for1186372 |
| Child configuration suffix and TRIGGER_ID/BUILD_PKG_LIST/FAIL_FAST/EACH_GBS_BUILD_STATUS | NOT_COLLECTED |
| Child Build table and Repository-Architecture comparison | COLLECTED for1193467: one row, exact colon string, child1193469, FAILED; child page NOT_COLLECTED |
| Failed sample RBS path, child Status and Build Result | NOT_COLLECTED |
| Real login conditions, landing and denied static resources | COLLECTED in live-03: POST302 -> /dashboard200, three conditions true; static/XHR denials above, no extra registrations |
| BUILD_TYPE Full -> Partial -> Full callbacks/action/version/options | NOT_COLLECTED |

Only1193467 main/variables were collected. The remaining build/configuration items
remain NOT_COLLECTED:1193467 steps,1193469 pages,1186372 and its unknown child,
and the RBS configuration page; the candidate overview_id was not registered.
BUILD_TYPE Full -> Partial -> Full was NOT_RUN; there are no observed callbacks,
action versions, refreshes or option changes to report. Form action was never
registered or released. Existing SBS evidence does not fill any missing RBS field.
C3 remains blocked. The exact source-location mismatch and proposed disposition
are recorded above; no further collection or rule change follows this stop.
