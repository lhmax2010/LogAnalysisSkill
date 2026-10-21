# C8 Offline Fix Evidence

Authority: progress section 49, P5Q-C8-01. Baseline: `0b27c49`.
No real QuickBuild access, Gerrit interaction or C6 state writes occur in these gates.

- `focused/`: discovery regression including ten new cases.
- `full/`: complete pytest run and JUnit; `cli-artifacts/` contains all six local HTTPS modes.
- `collection/`: exact collected test set, checked against full JUnit by `audit.py`.
- `mypy/`, `imports/`, `design/`, `ruff-final/`: final static gates.
- `ruff/`: first evidence-script lint attempt, two overlong lines; retained as history.
- `audit.json`: final counts, per-group totals, redaction audit and input hashes.

All command records include argv, UTC start/end, exit and immutable hashes.
`run_checks.py` asserts the complete agent equals `0b27c49`, not only its protected prefix.
The source prefix hash remains
`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`.

## New Cases

| Rule | Test in tests/unit/test_qb_discovery.py | Cases |
|---|---|---|
| Dropdown and stop links do not count as build links | test_configuration_dropdown_and_stop_links_are_not_build_links | 1 |
| Non-200 (403/404/500), redirect, trusted-context failure use identity message | test_baseline_identity_failure_does_not_submit | 5 |
| Driver timeout, unavailable reply, exit, invalid JSON stop the batch without restart | test_baseline_driver_failure_stops_batch_without_restart | 4 |

The existing baseline HTTP/redirect cases now also assert the identity message.
Timeout injection goes through the real Python driver queue/deadline and termination path,
with a virtual queue timeout; it does not change production timing.
The batch cases retain the already-requested unit, perform no new database writes,
and make no open-form/fill/submit calls.

## Publication

Synthetic parametrized HTML is represented in collected/JUnit test names by a stable
SHA256 of the parameter portion; function names and totals are retained and cross-checked.
Archived HTML bytes are not reformatted. Their original trailing whitespace is documented
as the only exception to the complete staged diff whitespace check.
These files are evidence, not production tooling or an approval for a live submission.
