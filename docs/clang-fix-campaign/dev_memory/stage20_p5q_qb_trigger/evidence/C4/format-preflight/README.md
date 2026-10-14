# C4 Source Format Preflight

OBSOLETE: P5Q-C4-02 (progress section 33) withdrew source-format alignment.
This historical intentional-red probe is no longer an acceptance criterion.
Its original script and results remain unchanged for the stop-report record.

Baseline: `3ef542a985712c340c333addedde092d818cc8b7`.
Authority SHA256:
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
Stop: P5Q-C4-01, progress section 32. No production implementation delivered.

The new request requires P5's source object-format selection. Frozen section 9.1
(line 692) prohibits **any** git command with the main worktree as `-C`/`--git-dir`.
P5 `_transport` uses exactly such a command to query the source format, with all
existing SandboxGit environment/command overrides. This is a specification
conflict, not evidence of a network leak or a failure of P5 format selection.

## Reproduction

Run at the repository root:

```sh
.venv/bin/python -m pytest -q -s docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C4/format-preflight/test_format_contract.py
.venv/bin/python -m pytest -q tests/unit/test_qb_trigger.py::test_transport_isolation
.venv/bin/ruff check docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C4/format-preflight/test_format_contract.py
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
```

| Command | Exit | Result / log |
|---|---:|---|
| Format probe | 1 (expected) | 2 failed at the final frozen-argv invariant; `format-contract.log` |
| Existing C3 isolation test, unchanged | 0 | 1 passed; `baseline-isolation.log` |
| Evidence script Ruff | 0 | `ruff.log` |
| Design checker | 0 | `design-check.log` |

For both sha1 and sha256, the probe first asserts source/transport format equality
and directory cleanup. It then prints the actual source query argv and checks the
frozen no-source-argv invariant. Both failures are at that last assertion. No
production source is patched or monkeypatched; the probe calls P5's real
`_transport` with a recording wrapper around the existing SandboxGit. No
`ls-remote`, push, browser, or external service is used.

This intentional-red probe lives outside the configured `tests/` collection; it
does not represent a C4 acceptance test or a change to the ordinary suite.
No full C4 acceptance run was performed after this pre-implementation stop.
Raw pytest output is retained, including emitted whitespace.
