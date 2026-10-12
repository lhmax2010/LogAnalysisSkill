# C2b Safety Coverage Before Real Login

Baseline: 09e14c5. Frozen SHA256:
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`.
Production code and frozen design remain unchanged.

| Required group | Existing C2a browser coverage | Missing proof addressed by C2b |
|---|---|---|
| Worker / WebSocket | request-boundary e Worker/SharedWorker; h popup HTTP/WS probes, production guards | Exact production-origin HTTPS fixture; paused worker counts and server-side zero requests/handshakes |
| 307/308 | test_qb_browser_runtime.mjs real HTTP redirect denial and 302 positive | Production origin and certificate policy unchanged; HTTPS legal second hop withheld |
| Credential isolation | Synthetic adapter unit test; real DOM redaction | Actual browser Cookie, Authorization and login password, server-side confirmation; redacted protocol and exception path leak scan |
| Per-hop interception | Real 302-to-REST rejection in runtime test | HTTPS redirects to REST, promote and external origin; 307 POST replay denial |

New entry: `tests/node/p5q_c2b_safety.mjs`. It calls production createRuntime,
Agent and their Policy/guards unchanged. Test-only launch flags map the production
hostname to loopback, deny all other DNS, and trust only the generated certificate
SPKI. An external redirect hostname also maps to this server so DNS failure is
not the reason the forbidden second hop is absent. Every server request is counted.
No live-site login or read is authorized until all four groups pass this run.

## First Run Stop

`safety-first.log`: exit 1. Worker/WebSocket observed zero attack HTTP and zero
WS handshakes, with both worker targets reported paused. The new fixture also
asserted runtime.failure must remain null; this extra condition failed. That
condition is not an explicit requirement of the design's fail-closed worker rule.
No production defect or escaping request is claimed from this evidence.

Remaining three groups are NOT_RUN. Per the requested stop-on-failure boundary,
the fixture was not relaxed or rerun, and real login never began. Correcting the
fixture to verify actual target closure, preserving detailed shutdown evidence,
and rerunning all groups remains required before any real-site action.

## Regression At The Stop

| Command | Exit | Result |
|---|---:|---|
| `.venv/bin/python -m pytest -q` | 0 | [pytest.log](pytest.log): 2152 passed, 1 skipped |
| `.venv/bin/mypy` | 0 | [mypy.log](mypy.log): 113 files |
| `.venv/bin/ruff check .` in the complete staged-tree export | 0 | [ruff-clean-tree.log](ruff-clean-tree.log) |
| `p5q_c2b_safety.mjs` with the existing local Node/Playwright/Chromium paths (progress 16.1) | 1 | [safety-first.log](safety-first.log): first group failed, remaining groups NOT_RUN |

The new manual Node entry is not part of pytest's count. Its failure remains a
separate blocker; regression greens do not certify the four-group prerequisite.
Ruff snapshot `93c73f09a60381deed4e7c31c801f193ef7a8804` was fully exported to
`/tmp/p5q-c2b-lint-RL8iHh` before checking. Unrelated dirty-tree scripts were not
modified, staged or granted exclusions. Production and frozen-document diff is zero.

## C2B-01 Ruling And Complete Rerun

The preceding sections describe the preserved first-run stop, not the current verdict.
The approved ruling replaces the extra null-failure assertion with two branches:
targets successfully closed with no failure, or QB_BROWSER_UNAVAILABLE with the
browser closed and the profile removed by the production agent. The latter is
checked before test-finally cleanup. CDP closeTarget results/exceptions are observed
without changing what the production guard receives.

[safety-c2b-01.log](safety-c2b-01.log), same full Node command as progress 16.1,
exit 0: all four groups rerun, 4 passed / 0 failed.

| Group | Actual result |
|---|---|
| Worker/WebSocket | branch b, attack HTTP 0 / WS handshake 0; shared_worker closeTarget success=true; worker closeTarget exception category Error; failure QB_BROWSER_UNAVAILABLE; browser closed / profile removed before test cleanup |
| 307/308 | Both legal destination second hops blocked; 302 positive reached /build/999 |
| Per-hop | REST, promote and external-origin redirect second hops 0; 307 POST replay 0 |
| Credentials | Actual synthetic cookie/auth/password observed only at local server; redacted agent response and adapter-exception output contain none of their values |

The safety script is now wrapped by pytest's explicit local integration test
`test_node_c2b_local_https_safety`. Missing Node/Playwright/Chromium/display/openssl
is an explicit skip, never a safety pass. A separate static test checks the evidence
entry cannot issue a build submission or pass launch overrides to production.

Live entry: `docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs`, unchanged
production Agent/createRuntime with no test options. It stops on any WORKER_BLOCKED,
NEW_PAGE or runtime.failure; archives only pre-redacted HTML after independent Python
checks, then checks the written bytes again. Live results are separate in appendix-c.md.
