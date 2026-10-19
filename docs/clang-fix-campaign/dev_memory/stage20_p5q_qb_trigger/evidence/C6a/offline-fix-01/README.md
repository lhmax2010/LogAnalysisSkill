# P5Q-C6A-05 Offline Repair

Baseline: `243df59`. No real QuickBuild, Gerrit, interactive login or dedicated
campaign DB writes. Local HTTPS fixtures use C5a certificate/DNS overrides only
through test entry points. The production-entry close tests never navigate to QB.

## Evidence Index

| Directory | Evidence |
|---|---|
| baseline-close | Before-fix production entry: close replied ok but process did not exit within 5 seconds with stdin open. Expected red. |
| close-fixed | Production entry fixed; initial driver test exposed an uninitialized response variable in the new diagnostic decoder. Corrected before focused/full acceptance. |
| focused-01 | 242 passed; real local login cases, strict Python protocol validation, both CLI traces, unchanged integration scenarios and measured closure times. |
| full | Full pytest output and JUnit; all local browser integrations, failure probes and synthetic CLI request/response artifacts. |
| node-unit | Node unit matrix, failure categories and every section 9.2 static guard mutation. |
| safety | Fresh four-group loopback safety run, actual received-request lists and Worker fail-closed branch. |
| mypy / lint-imports / design | Original output and command metadata. |
| ruff / ruff-final | Full staged-tree exports, not just changed Python files. Final run includes evidence scripts. |
| summary.json | Mechanical gate totals, closure times, secret-value checks and immutable input hashes. |

Each `command.json` records argv, UTC start/end, exit, elapsed seconds and the
frozen design/dedicated DB SHA256 before and after. `run_checks.py` reproduces the
invocation; `summarize.py` checks the final evidence and scope. Intermediate
failures are retained, not substituted for final gate results.

## Login Facts

Four actual Chromium/C5a HTTPS scenarios are archived under both focused/full
`artifacts/login-*.json`. Facts contain no synthetic account, password, session
value or query value. Login body logging in the fake server remains redacted.

| Scenario | Error | Final Path Shape | Last Signin / Password / Sign Out | Login POSTs | Channel Closed | Denied |
|---|---|---|---|---:|---|---|
| signin | QB_LOGIN_TIMEOUT | /signin | true / true / false | 0 | false | empty |
| unregistered | QB_LOGIN_TIMEOUT | / | false / false / false | 1 | true | `<other>`: 1 |
| no-signout | QB_LOGIN_TIMEOUT | /dashboard | false / false / false | 1 | true | empty |
| closed | QB_LOGIN_ABORTED, PAGE_CLOSED | /signin | true / true / false | 0 | false | empty |

The unregistered redirect ends on Chromium's error document, whose pathname is
`/`; the existing pathShape function intentionally does not report scheme/host.
This is not evidence that the site's home page loaded. `checks` counts completed
production polls; zero means no poll completed, not an observed absence of fields.

## Timing Definitions

- `production-close.json`: after close response, wait for actual production main
  to exit while stdin is deliberately held open. Exit must be 0 within 5 seconds.
- `driver-close.json`: actual QbBrowser.close wall duration after startup; assert
  stdin is already closed on entry to wait, exit0, terminate calls0.
- `cli-artifacts/build/commands.json`: test-entry close-command start to real
  Python CLI exit. Includes runtime cleanup, transport pipe cleanup and CLI tail;
  excludes browser startup, login, filling and business operations. Both trigger
  and fetch must finish this tail in less than 5 seconds.
- Historical diag-01 measured 35.070 seconds and agent exit -15. Live-05 tails
  were approximately 34.969/35.042 seconds, but agent exit codes were not collected;
  do not retrofit -15 onto those historical records.

`Policy`, `installGuards`, pathShape and all preceding helpers are byte-identical
to baseline (prefix checked by summarize.py). CLI modules, design.md and the
frozen design remain byte-identical. No new stop report or design deviation.
This repair does not perform C6b or closeout.
