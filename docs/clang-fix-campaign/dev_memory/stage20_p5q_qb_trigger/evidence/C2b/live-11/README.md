# live-11: Native Flags And Field Callback Stop

2026-10-13; baseline `cbedcf5`, production fix `4a4a727`. New chat start received,
ping/pong before browser startup, one manual login. No retry. Frozen SHA256
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950` unchanged.

## Invocation

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-11 \
  .venv/bin/python full
```

Commands in order, waiting for each response; login starts only after pong:

```jsonl
{"command":"ping"}
{"command":"read","path":"/build/1193467/overview"}
{"command":"read","path":"/build/1193467/variables"}
{"command":"read","path":"/build/1193469/overview"}
{"command":"read","path":"/build/1193469/variables"}
{"command":"read","path":"/build/1193469/step_status"}
{"command":"register_config","source_path":"/build/1193467/overview"}
{"command":"read","path":"/overview/1917"}
{"command":"form_evidence"}
```

1917 was returned from this run's verified source, not guessed. form_evidence
stopped/closed the browser itself, so no later close or field command was sent.

## Outcome

Exit1 STOPPED/QB_FORM_CHANGED during BUILD_TYPE_Partial. Five build pages all
HTTP200/VERIFIED. Source five checks and configuration-page two checks pass.
Initial open_form and validateForm succeed. The earlier PROJECT_NAME whitespace
failure is not reproduced with Node normalization.

Eight native-flag samples (login, six read pages, form) each report trim=false,
the other eight=true: String.replace/split/includes, Array.map/filter/includes,
JSON.stringify, RegExp.exec. Only booleans are recorded, not function source.

The initial callback has no random. Actual fill POST at66421ms has_random=true
and is denied; query is retained only in approved redacted form (run.json:2819).
Its listener token is masked, so exact equality of the remaining query is not
claimed. No successful response follows. A later GET XHR with action/random is
also denied. The30s field wait fails. Local Partial is selected, but there is no
completed after snapshot or attempted return to Full. No field rule is changed.

Stop diagnostics are structurally all green, first_failure=null, empty field
differences; not another validateForm structural failure. Full details, callback,
action, options, page/native source lines: ../appendix-c.md, latest live-11 section.
Initial BUILD_REFERENCE Ref. Snapshot; SNAPSHOT_NUM sole selected option
tizen-base-toolchain_20260924.094908. These remain visible at stop, not proven
post-linkage server results. Initial page version/action unchanged in diagnostics.

form_action_releases0/released=false, runtime_failure=null, no Worker/new page;
browser/profile cleaned. HTTP observations GET110/POST2 (one human login allowed,
one field callback denied), allowed75/denied37; responses200x61/302x2. Denials:
ckeditor10, bootstrap fonts9+9, GET XHR8, POST XHR1; frame-ownership0. Not server
receipt counts. No Ok/submit/new build. No retry, no C3. One new stop awaits ruling.

## Integrity

run.json SHA256 `832cb060ad4dde6b31b081148b4d8e6390ea5dd99cb8532e1c381295690b4cf1`.
All eight HTML files verified against pages[].sha256 and PageRedactor.check_bytes;
integrity.log also asserts stop/cleanup/zero release, native flags, initial form
and failed transition facts. Runtime pre/post-write checks used in-memory
identities. Offline checks never reconstruct or persist those identities.

Form initial/failure HTML SHA256 both `8f8b50258cf0db849b557428cc54479fe764888fa45b64096d9b4c2edefee12e`.
Serialized option attributes are unchanged even though the live selected property
changed; diagnostic selected_texts is authoritative for the local selection.
fields.log uses the existing ef5_rbs_form.DOM offline parser, not network calls,
to extract named parent/child variables and count package lines. Source rows
remain 02.response.html:808 and04.response.html:800.

```bash
sha256sum docs/clang-fix-campaign/p5q-qb-trigger-design-v1.2-FROZEN.md \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-10/run.json \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-11/run.json \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-11/form-initial.html \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-11/form-unverified.response.html
```

The immutable historical live-10 and frozen hashes match. This archival commit
changes only documentation/evidence, not production, spikes, tests or design.

## Post-collection Gates

Commands from repo root, raw output saved in adjacent logs. No further live request.

```bash
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
```

| Gate | Result | Exit |
|---|---|---|
| pytest.log | 2165 passed/1 skipped,111.67s; unchanged count | 0 |
| mypy.log | 113 source files,clean | 0 |
| lint-imports.log | 6 kept/0 broken | 0 |
| design-check.log | 0 problem | 0 |
| node-gates.log | 3 passed,19.93s;unit120/120,DOM50/50,safety4/4 | 0 |
| integrity.log | Hashes/redaction/zero-release/stop/native checks pass | 0 |

Node safety uses local synthetic data only. The Worker branch is b:browser_fail_closed;
shared_worker closeTarget succeeds, worker returns Error; browser/profile are
removed and attack HTTP0/WS0. Other three groups pass. Gate green does not close
the real callback failure.

Ruff on the complete staged tree: All checks passed!, exit0 (ruff.log).
Only final docs/logs appended after this run; unrelated dirty files excluded.
Documentation diff --check is empty. Original redacted HTML whitespace/line
endings are retained, not reformatted to change the raw hashes.

```bash
git archive df3ff86eacd400fd4d11904457cddc22a6f60feb | tar -x -C /tmp/p5q-live11-lint-plJJ6v
# cwd=/tmp/p5q-live11-lint-plJJ6v
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```
