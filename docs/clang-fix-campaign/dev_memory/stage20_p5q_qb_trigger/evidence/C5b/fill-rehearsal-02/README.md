# C5b Fill Rehearsal 02

Tool commit: `5afb645`. FatTank confirmed the existing target and replied
"沿用。开始". One attempt, exit 0, no retry. Login was performed only in the
browser. The tool issued login/open_form/fill/close, never submit.

- `run.json`: original tool output, unchanged. SHA256
  `c975d19eed9ad0e13c7592fb672436ac6f3e255816b921e504197d93757a97e7`.
- `execution.json`: exact command, authorization and exit code.
- `acceptance.json`: mechanical per-field comparison against requirements.
- `validation.json` / `validation.log`: offline closeout checks, no QB access.
- `../archived-analysis-02.json`: production parser outputs for the already
  archived 1193469 overview/step_status pages, including complete Error Message.

## Results

All twelve fields: one allowed callback, zero rejected callbacks, HTTP 200,
readback equals requested value. SNAPSHOT_NUM freezes the unique initial
selection `tizen-base-toolchain_20260924.094908`. Ten fields were already equal
and still triggered one callback each. Each random value is retained in
`acceptance.json` and the per-field table in progress section 36.7.

The page stayed `/wicket/page?4`. The action stayed
`/wicket/page?4-1.IFormSubmitListener-form`, including after readback.
`release_state=not_released`, `form_action_releases=0`.
Twenty identity observations all returned zero; observer errors were empty.
Other rejected requests remain denied (login4/open_form11/fill1). They are not
field callback rejections; no allow rule was modified to bypass them.

The snapshot diagnostics include four early open_form polls without a heading
and fifteen `field_window_or_readback` fallback labels. In production formFacts,
the latter is the default even when structural checks succeed, not a failed
command. A supplemental offline assertion initially assumed it should be null;
that assumption was corrected after reading formFacts, without modifying any
tool, production code, criterion or original run record. Command replies and
all twelve field windows pass the approved criteria.

## Offline Archive Analysis

Only archived redacted files were read. To reproduce without network or CLI:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from ci_triage.qb_result_html import child_overview, failed_steps
p = Path('docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b/raw-active-01')
profile = {'configuration_path': 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER'}
for kind in ('raw', 'active'):
    print(failed_steps((p / f'05.{kind}-redacted.html').read_text()))
    print(child_overview((p / f'03.{kind}-redacted.html').read_text(), profile, 'FAILED'))
PY
```

Both sources return `master > BUILD > Build > Build_GBS` and `Failed` / `FAIL`.
The complete Error Message has 2093 characters. The appendix C13 BUILD sentence
appears at `03.raw-redacted.html:868`; it is an excerpt of the error box beginning
at line848, not a replacement for its four rows and command output.

Successful Ref. Snapshot and nonempty BUILD_NOTES build samples are still open.
No new raw/active run, no state database writes and no build was submitted.
The three technical C6 prerequisites now pass, but FatTank has not authorized
C6; this run stops at C5b. P5Q is not CLOSED.
