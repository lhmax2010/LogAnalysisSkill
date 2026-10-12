# C2b Appendix C Evidence Status

Status: **BLOCKED_LOGIN_SCOPE / NOT_COLLECTED**. Latest C2B-02 supplemental
diagnostic is live-02b; live-01/live-02 remain unchanged historical evidence.
C2B-01 corrected the fixture;
all four local safety groups passed before the single live browser session.
See [safety-c2b-01.log](safety-c2b-01.log) and progress section 17.
The live session stopped with QB_LOGIN_ABORTED. No retry, build-page read,
configuration read or form interaction followed. The frozen appendix is unchanged.

## C2B-02 Supplemental Diagnostic (Latest)

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
| RBS overview_id, breadcrumb source and configuration title | NOT_COLLECTED |
| Parent variables: Build Package List, BUILD NOTES, BUILD_TYPE, BUILD_REFERENCE, SNAPSHOT_NUM, PROJECT_BRANCH | NOT_COLLECTED |
| Child configuration suffix and TRIGGER_ID/BUILD_PKG_LIST/FAIL_FAST/EACH_GBS_BUILD_STATUS | NOT_COLLECTED |
| Child Build table and Repository-Architecture comparison | NOT_COLLECTED |
| Failed sample RBS path, child Status and Build Result | NOT_COLLECTED |
| Real login conditions, landing and denied static resources | PARTIAL: live-02b exact metadata above; no302, Wicket POST denied, no successful three-condition snapshot |
| BUILD_TYPE Full -> Partial -> Full callbacks/action/version/options | NOT_COLLECTED |

All build/configuration items above remain NOT_COLLECTED: 1193467/1193469,
1186372 and its unknown child, and the RBS overview_id were not read or guessed.
BUILD_TYPE Full -> Partial -> Full was NOT_RUN; there are no observed callbacks,
action versions, refreshes or option changes to report. Form action was never
registered or released. Existing SBS evidence does not fill any missing RBS field.
C3 remains blocked. No frozen behavior discrepancy is claimed as proven from an
unidentified denied destination; the concrete live failure is recorded instead.
