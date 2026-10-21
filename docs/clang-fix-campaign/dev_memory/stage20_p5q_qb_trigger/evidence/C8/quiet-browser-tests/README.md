# Quiet Browser Test Validation

Date: 2026-10-21. Production baseline: bce9052. No real QuickBuild operation.

Command (repository root):

```bash
.venv/bin/python tests/run_quiet.py tests/unit/test_quiet_runner.py tests/unit/test_qb_browser_node.py tests/unit/test_p5q_c5a_integration.py tests/unit/test_p5q_c6_diagnostics.py tests/unit/test_p5q_c6_offline_fix.py -q --junitxml=docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/quiet-browser-tests/pytest.xml
```

Exit 0: **60 passed, 0 failed, 0 skipped**, 604.40 seconds. JUnit: `pytest.xml`.

| Group | Cases | Result |
|---|---:|---|
| Quiet runner and accidental desktop guard | 7 | passed |
| Node, DOM, redaction, lifecycle and safety wrappers | 17 | passed |
| Real CLI against local HTTPS, all six modes | 6 | passed |
| Failure/login diagnostics and local driver | 27 | passed |
| Production-entry close regressions | 3 | passed |

The safety wrapper asserts all four groups pass: Worker/WebSocket, 307/308,
credential isolation, and per-hop interception. No assertion was relaxed.
This is targeted regression coverage, not a new full-repository pytest run.

During execution, the parent desktop was `:0`, Xvfb was `:99`. A read-only
`xwininfo -root -tree` on `:99` showed the local synthetic-fields Chrome window
and its clipboard/helper windows there. After completion, the Xvfb process,
`/tmp/.X11-unix/X99`, its temporary Xauthority directory, browser processes,
and `/dev/shm/p5q-browser-*` profiles were absent. No desktop environment changes
were exported to the parent process. XKEYBOARD emitted nonfatal keysym warnings.

Additional checks (all exit 0): mypy on 119 production files and on the new runner;
ruff on tracked Python plus the new files; lint-imports (6 kept, 0 broken);
design checker (0 problem); git diff --check.

The production agent and all other production files are byte-identical to baseline.
The frozen design hashes are unchanged. External database hashes after the run:

- C6: `08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30`
- C8: `dd43219d2964e23d711e904ab640a73eb3c328e6685940dc7711beb4f7563ff2`

The local Xvfb package was verified against the configured Ubuntu apt index:
`2011271eabcc2eb460e99995c5ef26e46633e87d04f570e305b62f178f7b452c`.
It was unpacked only into `~/.local/share/p5q-test-display` (2.2 MB), not installed
system-wide. No frozen design, production launch mode, credential handling,
login contract, or real submission authorization was changed.
