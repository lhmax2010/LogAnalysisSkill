# C2B-06 live-08

2026-10-13, baseline962ad58. FatTank authorized one unchanged rerun, then replied
to the fresh chat start request. live-07 and all earlier archives are unchanged.
This run stopped at configuration registration; it did not open a run form.

## Invocation And Protocol

Repository root, maintained PTY, original script and production agent:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-08 \
  .venv/bin/python full
```

Sent ping, received pong, then browser started and login ran automatically.
600-second limit; human login only in the browser. After successful login,
commands were sent individually in this order:

```jsonl
{"command":"read","path":"/build/1193467/overview"}
{"command":"read","path":"/build/1193467/variables"}
{"command":"read","path":"/build/1193469/overview"}
{"command":"read","path":"/build/1193469/variables"}
{"command":"read","path":"/build/1193469/step_status"}
{"command":"register_config","source_path":"/build/1193467/overview"}
```

Each read returned200/VERIFIED. Parent Child Build supplied child1193469.
The last command stopped the run, exit1:

```json
{"status":"STOPPED","stop":{"reason":"CONFIGURATION_SOURCE_MISMATCH","operation":"register_config","path_shape":"/build/<id>/step_status"},"browser_closed":true,"profile_removed":true,"released":false}
```

The path_shape field retains the last read, not the registration source;
the verified source is explicitly `/build/1193467/overview` above and in
run.json.configuration_sources[0]. No raw record was corrected after the run.

## Stop Evidence

run.json SHA256:
`ebe9226207c9d08ac8b5df0ba03e8a5e614092431f26e65468d2a8d80f902080`.
HTML file hashes are the five entries in run.json.pages.

Four of five source checks passed. sibling_tabs=false because actual hrefs are
`../../pipeline/1917` and `../../children/1917` (01.response.html:711/:715),
but the unchanged helper requires exact `../pipeline/1917` and
`../children/1917`. Overview href, breadcrumb, copy-path and build-name pass.
All three tab ids agree, but this does not bypass the failed exact check.
1917 was extracted, not registered; the configuration page was not fetched.

Child Summary Status is Failed (03.response.html:828); parent Child Build
Result is FAILED (01.response.html:892). The child step page is archived.
Field-level observations and the complete displayed step list are in
../appendix-c.md, with source lines. No historical summary substitutes a page.

One human login POST returned302 to /dashboard200. Login three conditions pass.
Request-stage metadata GET92/POST1, allowed66/denied27; response-stage200x53,
302x1. Denials: ckeditor7, bootstrap-icons.woff6/woff2x6, Wicket XHR8.
Trace/wrapper both27; frame-ownership0. These are interception counts, not
server receipt counts. Denied refreshes and resources were not re-registered.

runtime_failure=null, no WORKER_BLOCKED/NEW_PAGE, cleanup bothtrue.
form_action_releases=0, released=false. No open_form/fill/submit, no Ok/Accept,
no 1186372 read, no retry, no C3. Callback/action/page-version/option changes and
form BUILD_REFERENCE/SNAPSHOT_NUM remain NOT_COLLECTED.

Archive validation: ../live-08-validation/; progress22.8/22.9. Passing offline
gates does not resolve the configuration-source stop or complete C2b.
