# C5b Fill Rehearsal: STOPPED

This file is an operator stop record, not output from the rehearsal tool.
At process exit, this directory existed and contained zero files. No run.json,
agent response, trace, callback record or diagnostic HTML was available.

- Source: b134d1603c509ae9247bdb3511dd82f72d4f940c, unchanged tool.
- Date: 2026-10-15 Asia/Shanghai.
- Outer process handle: 4739; exit code: 1.
- Terminal output: fixed browser login prompt followed by EVIDENCE_STOPPED.
- Exact command: ../execution.json, step fill_rehearsal.
- Agent error, failure stage, all 12 field counters/readbacks, release_state,
  form_action_releases: NOT_COLLECTED, not assumed zero.
- No retry or alternate tool. No submit command in the executed tool's command
  path. Static source evidence does not replace missing runtime counters.
- Step 3 was not run after this failure. C6 prerequisites are not met.

The top-level catch in spikes/p5q_fill_rehearsal.mjs:84 discards the failure
category. Early login/open_form errors and other pre-write failures cannot be
distinguished using this transcript alone. See progress.md section 35.4,
P5Q-C5B-01, for the unimplemented candidate evidence-channel change.
