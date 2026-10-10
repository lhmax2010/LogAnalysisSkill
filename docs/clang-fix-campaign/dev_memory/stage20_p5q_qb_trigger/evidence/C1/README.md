# P5Q C1 Offline Validation

Baseline: `3e073bc`. Frozen input SHA256:
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`.
No QuickBuild/Gerrit requests, browser, live credentials, or new dependencies.
Fixture identities/tokens in test names are artificial, not credentials.

| Command | Exit | Raw output |
|---|---|---|
| `.venv/bin/python -m pytest tests/unit/test_campaign_state.py -q` before refactor | 0 | state-before.log: 36 passed |
| `.venv/bin/python -m pytest tests/unit/test_campaign_state.py tests/unit/test_qb_state.py tests/unit/test_qb_config.py tests/unit/test_qb_redact.py -q` | 0 | focused.log: 140 passed |
| `.venv/bin/python -m pytest -q` | 0 | pytest.log: 2041 passed / 1 skipped |
| `.venv/bin/mypy` | 0 | mypy.log: 112 source files |
| `git ls-files -z -- '*.py' \| xargs -0 .venv/bin/ruff check --force-exclude` | 0 | ruff-tracked.log |
| `.venv/bin/ruff check tizen-ci-triage/scripts/ci_triage/qb_config.py tizen-ci-triage/scripts/ci_triage/qb_redact.py tests/unit/test_qb_config.py tests/unit/test_qb_redact.py tests/unit/test_qb_state.py` | 0 | ruff-new.log |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | 0 | design-check.log: 0 problem |
| `.venv/bin/lint-imports` | 0 | lint-imports.log: 6 kept, 0 broken |
| `.venv/bin/python -m pytest tests/unit/test_qb_config.py tests/unit/test_qb_redact.py tests/unit/test_qb_state.py --collect-only -q` | 0 | new-nodeids.log: 104 collected |

Ruff checks all tracked Python plus every new Python file; unrelated untracked
historical drafts are not part of this delivery.

`api-equivalence.log` is from an in-memory AST comparison: load the old source
using `git show 3e073bc:tizen-ci-triage/scripts/ci_triage/campaign_state.py`, parse
both revisions with `ast.parse`, compare the arguments/returns of the three
public APIs and the old transaction bodies with the moved primitive bodies.
Compare the old/new entire test_campaign_state.py AST after removing only the
new campaign_qb_profiles set member. All comparisons pass. No helper script or
checker modification was required.

Initial targeted tests passed (101, then 25); Ruff initially caught the frozen
SQL comment exceeding the configured width by one character and six new test
lines. The SQL literal has a local E501 suppression preserving verbatim DDL;
test formatting was corrected. Final results above include these corrections.
