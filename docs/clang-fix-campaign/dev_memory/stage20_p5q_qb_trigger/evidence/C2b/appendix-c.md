# C2b Appendix C Evidence Status

Status: **BLOCKED_LOGIN / NOT_COLLECTED**. C2B-01 corrected the fixture;
all four local safety groups passed before the single live browser session.
See [safety-c2b-01.log](safety-c2b-01.log) and progress section 17.
The live session stopped with QB_LOGIN_ABORTED. No retry, build-page read,
configuration read or form interaction followed. The frozen appendix is unchanged.

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
| Real login conditions, landing and denied static resources | PARTIAL: login aborted; denied shapes above; no successful landing/three-condition evidence |
| BUILD_TYPE Full -> Partial -> Full callbacks/action/version/options | NOT_COLLECTED |

All build/configuration items above remain NOT_COLLECTED: 1193467/1193469,
1186372 and its unknown child, and the RBS overview_id were not read or guessed.
BUILD_TYPE Full -> Partial -> Full was NOT_RUN; there are no observed callbacks,
action versions, refreshes or option changes to report. Form action was never
registered or released. Existing SBS evidence does not fill any missing RBS field.
C3 remains blocked. No frozen behavior discrepancy is claimed as proven from an
unidentified denied destination; the concrete live failure is recorded instead.
