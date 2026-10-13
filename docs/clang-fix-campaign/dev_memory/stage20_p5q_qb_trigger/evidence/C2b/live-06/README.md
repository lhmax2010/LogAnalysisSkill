# C2b live-06

Date: 2026-10-13. Baseline: 93421b1. Status: STOPPED / QB_FORM_CHANGED.
Fresh chat authorization preceded this single login session. No automatic retry.

## Execution

The execution tool used `tty=true` to maintain stdin. Before browser startup,
the driver sent `{"command":"ping"}` and received `{"pong":true}`. The same
channel remained open through login, seven reads and the form stop.

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-06 \
  .venv/bin/python full
```

Exit: **1**, the intended stop result, not a completed C2b.

After automatic login success the driver sent reads in the approved order,
then `register_config` with source_path=/build/1193467, read /overview/1917,
and form_evidence. Registration was derived from fresh evidence, not a guessed
id. 1186372 main was ID_UNVERIFIED, so its child was skipped. No close command
was necessary after the script stopped and cleaned up on QB_FORM_CHANGED.

## Evidence

`run.json` contains exact command sequence, request/response metadata, login
conditions, diagnostic samples, config checks, stop and cleanup. Its SHA256 is
`e13a202e2e245052160d2da140a36b5d1e10ecdf387c3d2901ed7bd5cbd53213`.
Page hashes are stored under `pages`. Five of seven archived pages passed their
applicable checks; `03` and `05` are explicitly ID_UNVERIFIED and are not id
sources. Both had one correct Build label and zero build-summary elements in
the immediate and three-second samples. Raw objects are reproduced in
[appendix-c.md](../appendix-c.md#two-sample-structure-facts-verbatim-objects).

The config page Run control is a button with onclick, no href (:722). The
production openForm still requires href. It returned QB_FORM_CHANGED after
re-reading the overview; no form page or field-change result was collected.
See [appendix-c.md](../appendix-c.md#configuration-checks-and-form-stop) for
the evidence limits and source comparison. Production was not changed.

Login passed; form_action_releases=0; released=false; runtime_failure=null;
browser_closed=true; profile_removed=true. No Ok, Accept or build submission.
GET112 interception records (71 allowed/41 denied), POST1 (human login only).
Responses200x59/302x1; not server-side counts. No WORKER_BLOCKED or NEW_PAGE.

All pages used production redaction plus pre/post-write identity-aware checks.
Offline archived-byte verification is in `../live-06-validation/`.
Prior live evidence and the frozen design are unchanged. C3 is not started.
