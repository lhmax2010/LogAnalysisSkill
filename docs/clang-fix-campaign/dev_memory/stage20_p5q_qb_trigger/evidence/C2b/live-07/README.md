# C2B-06 live-07

2026-10-13; baseline e683175. This is a stopped login observation, not a
completed C2b field/form collection. Fresh chat start was received. No retry.

## Invocation

Executed at repository root in a maintained PTY:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-07 \
  .venv/bin/python full
```

Sent `{"command":"ping"}` and received `{"pong":true}` before the browser
started. Then the fixed login-window prompt was printed. No further commands
were sent; no terminal credential input, input EOF or early termination.
Login timeout stayed at 600 seconds. Credentials were not inspected or stored.

Final protocol output, exit1:

```json
{"status":"STOPPED","stop":{"reason":"QB_LOGIN_TIMEOUT","operation":"login","path_shape":"/signin"},"browser_closed":true,"profile_removed":true,"released":false}
```

## Evidence

`run.json` SHA256:
`79d07795dfa6d54647f9981ff7fe1884e5f860cc1e1e6037f5db5ec3869a533e`.

- Only login ran. GET /signin returned200; no login POST or redirect observed.
- Request-stage metadata: GET47, allowed46/denied1, POST0.
  Response-stage metadata: 38 HTTP200 records. These are interception records,
  not a server-side count; request and response stages are not added together.
- The only denial was Script `/ckeditor/ckeditor.js?v=1701391813000`.
  It remained blocked. trace/wrapper denials both1; frame-ownership denials0.
- Runtime failure null, WORKER_BLOCKED/NEW_PAGE absent, cleanup bothtrue.
- pages=[], form_action_releases=0, released=false. No open_form/fill/submit.
- Parent/child pages, child Summary Status, configuration provenance and
  Full -> Partial -> Full all remain NOT_COLLECTED for this run. No historical
  page or id was substituted. No C3.

Relative timestamps start at script startup, including time before ping:
Document request134390ms, response135905ms, main-frame navigation135911ms,
page close734394ms. They do not mean a 734-second browser login allowance.
Absence of POST is an observation, not an inference about user actions.

Production and frozen documents were not changed. Validation logs are in
`../live-07-validation/`; conclusions and page-by-page pending items are in
`../appendix-c.md` and progress22.6/22.7.
