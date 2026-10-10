# RBS Form Offline Validation

Date: 2026-10-10. Code baseline: `179ce3e` plus the two new spike files.
These checks do not access QuickBuild, execute page JavaScript, load resources,
or submit a form. The requested Git delivery is separate from the probe.
The original `/tmp/qb_rbs_trigger_form.html` remains outside Git and unchanged.

## Commands And Exits

Run from the repository root; all exits below were measured, not inferred.

| Command | Exit | Raw output |
|---|---|---|
| `env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py' -v` | 0 | [offline.log](offline.log): 52 tests, OK; previous 43 plus 9 new |
| `.venv/bin/python -m pytest -q` | 0 | [pytest.log](pytest.log): 1937 passed, 1 skipped in 76.69s |
| `.venv/bin/mypy` | 0 | [mypy.log](mypy.log): no issues in 110 source files |
| `.venv/bin/mypy --follow-imports=silent docs/clang-fix-campaign/spikes/ef5_rbs_form.py` | 0 | [spike-mypy.log](spike-mypy.log): no issues in 1 source file |
| `/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .` | 0 | [ruff.log](ruff.log): All checks passed! |

Full-tree ruff used `/tmp/ef5-rbs-form-179ce3e`, a clean worktree at `179ce3e`
with the two new spike files copied in. Unrelated untracked design drafts in the
main worktree were not included. No production or `tests/` files changed.
The spike unittest count is separate from the production pytest count.

## Archive Execution

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/ef5_rbs_form.py --input /tmp/qb_rbs_trigger_form.html --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/rbs-form-01
{"network_requests": 0, "forms": 2, "redaction_self_check": "PASS", "redacted_sha256": "66dad8500ab37c8be9ce981ef61048aea0a4fef2378b25666288b0a7147bad58", "original_unchanged": true}
exit=0
```

Do not rerun into this evidence directory: the tool refuses to overwrite it.
Only `form.redacted.html` and `form.json` were archived; raw bytes were never
written to a second file. Source line positions and line endings were retained.
The CLI denies socket connection, DNS and UDP send audit events.

## Redaction Recheck

The following offline recheck reads the original only in memory. It prints no
identity or credential. It also checks all four inputs whose type is hidden:
two have redacted value attributes, two originally had no value attribute.

```python
import hashlib
import json
import re
from pathlib import Path
from ef5_probe import MASK
from ef5_rbs_form import DOM, FormRedactor, REDACTED

root = Path("docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/rbs-form-01")
source = Path("/tmp/qb_rbs_trigger_form.html").read_bytes()
redactor = FormRedactor()
safe = redactor.redact(source.decode())
archived = (root / "form.redacted.html").read_bytes()
assert archived == safe.encode()
redactor.check_safe(archived.decode())
data = json.loads((root / "form.json").read_bytes())
assert hashlib.sha256(archived).hexdigest() == data["redacted_sha256"]
assert data["network_requests"] == data["forms_submitted"] == 0
hidden = [n for n in DOM(archived.decode()).root.walk()
          if n.tag == "input" and n.attrs.get("type") == "hidden"]
assert all(n.attrs["value"] == REDACTED for n in hidden if "value" in n.attrs)
for path in root.iterdir():
    text = path.read_bytes().decode()
    redactor.check(text.replace(REDACTED, MASK).replace("&lt;REDACTED&gt;", MASK))
    assert not any(re.search(r"(?<!\w)" + re.escape(i) + r"(?!\w)", text)
                   for i in redactor.identities)
assert Path("/tmp/qb_rbs_trigger_form.html").read_bytes() == source
print("redaction_recheck=PASS; original_unchanged=PASS; network_requests=0")
```

Use the same spike `PYTHONPATH` as the unit test command. The actual recheck also
scanned the five log files, report and stage19 progress available at that time:

```text
archive_byte_equal=PASS; redacted_sha256=66dad8500ab37c8be9ce981ef61048aea0a4fef2378b25666288b0a7147bad58
hidden_inputs=4; hidden_values_masked=2; hidden_without_value=2
credential_and_identity_scan=PASS; checked_files=9; original_unchanged=PASS
network_requests=0; forms_submitted=0; external_scripts_loaded=0; javascript_executed=false
forms=2; controls=19; buttons=25
exit=0
```

The nine new tests cover hidden/session/identity redaction, short display-name
boundaries, unquoted session URLs, field types/options/required markers, palette
recorders, static AJAX/button metadata, no network/raw copying/overwriting,
source positions, and fail-closed diagnostics. All test credentials are synthetic.
No actual submission response or new-build-ID mechanism was obtained.
