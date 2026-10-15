# P5Q-C5B-02 Tool Repair (Offline)

Baseline: 78212fe. Design SHA256:
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
Only the two spikes tools and their shared library changed executable behavior.
Production code, Policy, installGuards and the frozen design are unchanged.
Historical raw-active-01 was not rerun or modified (19 hashes unchanged).

## Reproduce

Run from the repository root with the existing .venv and local Chromium:

```bash
.venv/bin/pytest -q -s tests/unit/test_qb_browser_node.py::test_node_c5b_failure_evidence tests/unit/test_qb_browser_node.py::test_c5a_tools_are_readonly_and_not_production_test_overrides tests/unit/test_qb_browser_node.py::test_node_c5a_evidence_tools
```

The tests launch only the C5a loopback HTTPS server, using its test certificate
and DNS override. Login is simulated only by the test entry, never by the
production login method. No real QB/Gerrit or campaign database is involved.
Full regression includes the pre-existing local CLI/database fixtures only.

Set P5Q_C5B_EVIDENCE to a fresh absolute directory to retain fault-case artifacts;
P5Q_C5A_EVIDENCE retains the existing comparison/rehearsal tool fixtures.
Without these settings the test-owned temporary directories are cleaned up.
Never reuse an existing evidence directory. Runtime profiles are removed in
both success and failure cases and checked by the new tests.

## Matrix

The final full-suite artifacts are in full-injections/; the targeted rerun is
in injections-02/. Each case contains run.json except the intentional storage
failure, plus synthetic server request records and fixed terminal output.
Diagnostic cases also contain diagnostic.html and diagnostic.json, passed
through the same checkedWrite pipeline as ordinary evidence.

| Case | Expected result |
|---|---|
| login_timeout | STOPPED, login / QB_LOGIN_TIMEOUT, run.json exists |
| open_form | STOPPED, open_form / QB_FORM_CHANGED, diagnostic pair exists |
| third_field | STOPPED, fill / QB_FORM_CHANGED, third field BUILD_REFERENCE rejected; two earlier callbacks reached server |
| identity_goto | EVIDENCE_INCOMPLETE; production fill succeeds; only TypeError recorded |
| identity_snapshot | EVIDENCE_INCOMPLETE; production fill succeeds; only TypeError recorded |
| adapter | EVIDENCE_INCOMPLETE; one ADAPT_FAILED; observer does not throw; production fill succeeds |
| write_failure | EVIDENCE_WRITE_FAILED only on stderr; run.json intentionally unwritable; browser/profile cleaned up |
| normal | PASSED; 12 fields each 1 allowed / 0 denied / HTTP 200; not_released; action releases 0 |
| assembly | STOPPED, assemble / TypeError; existing snapshots, callbacks and successful fill response retained |
| compare_read_failure | STOPPED, read / QB_READ_REDIRECTED; response/trace retained |

The intentional storage failure uses a directory at the run.json path. It
cannot simultaneously produce a valid file there; the explicitly approved
EVIDENCE_WRITE_FAILED path is the assertion, not fabricated evidence. All other
failures assert that run.json exists. Raw exception text, arbitrary all-caps
exception messages, passwords and protocol events are not serialized.

## Run Records

- focused-01.log: development run, 1 failed / 1 passed. The extra assembly
  injection correctly saved the error, but the test incorrectly attempted the
  successful-registration assertion afterward. Only that test branch changed.
- focused-02.log: 3 pytest passed; new Node matrix 12/12; existing tool Node
  matrix 12/12. Both include their outer test in the Node count.
- full.log / full.xml / full-command.json: final full regression, 2639 passed,
  0 failed, 1 skipped; local Node browser groups ran, not skipped.
- test-set-audit.json: one added pytest wrapper and no removed baseline cases;
  the existing filesystem-specific skip is unchanged.
- log-redaction.json: before/after hashes for full.log and full.xml. Synthetic
  negative-fixture parameters are masked before archiving; the console log is
  HTML-escaped to keep fixture tags as text. JUnit totals are unchanged. The
  testcase-set comparison ran before log redaction; raw logs are not committed.
- artifact-audit.json: redaction, normal twelve-field rehearsal, frozen hash
  and original C5b artifact integrity checks.
- node-selftest.log: standalone Node unit/source guards, 346/346.
- gate-commands.json: mypy, Ruff worktree scan, lint-imports, design checker.
- ruff-pending-tree-command.json: complete pending-tree export and Ruff check.

The direct worktree Ruff scan reports 53 issues in four pre-existing untracked
drafts only: audit_four_sigs.py, hashobj2.py, ident_check3.py, norm_diff5.py.
They are not edited or included. As in C5a, git checkout-index exports the full
pending commit tree and Ruff checks that tree without exclusions added to the
checker. Both results are preserved; the exported tree passes.

## Live Gate

No live window was opened in this repair. After the tool commit is pushed,
FatTank must confirm the target line and reply "开始" before fill-rehearsal-02.
Successful Ref. Snapshot and nonempty BUILD_NOTES samples remain open. No C6.
