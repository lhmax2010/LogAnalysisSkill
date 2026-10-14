# P5Q C4 Completion Evidence

Baseline: `ec3be749ab7681c9ff45631c6ab58a25c336c070`.
Authority: `p5q-qb-trigger-design-v1.5-FROZEN.md`, sha256
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
P5Q-C4-02 withdraws object-format alignment. The old format-preflight remains
historical evidence, explicitly OBSOLETE; its failed expectation is not reused.

## Implementation Map

Paths below are relative to `tizen-ci-triage/scripts/ci_triage/`.

| Requirement | Implementation |
|---|---|
| C4-02 default bare transport, no source git context | `qb_trigger.py::_remote_check` unchanged; `tests/unit/test_qb_trigger.py::test_sha256_remote_residual` |
| 5.1 selection, latest request, unit lock, single login | `cli.py::_main_qb_result_fetch`; `qb_result_fetch.py::_selections/_view/qb_result_fetch` |
| 5.2 binding + transaction recheck | `qb_result_fetch.py::_binding_allowed/_manual_bind` |
| 5.3 parent/child HTML and snapshot checks | `qb_result_html.py::parent_overview/parent_variables/child_overview/child_variables/snapshot_kind`; `qb_result_fetch.py::_collect` |
| 5.3 optional step_status | `qb_result_fetch.py::_read_page`; `qb_result_html.py::failed_steps`; original agent error preserved on `QbBrowserError.agent_code` |
| 3.7 evidence/identity counts | `qb_result_fetch.py::_read_page`; agent `read` returns the existing computed `outside_identity_count`, driver validates its type |
| 5.4 result schema + durable publication | `qb_result_fetch.py::RESULT_KEYS/_publish` |
| 5.4 result recheck, idempotency, 6.3 transitions | `qb_result_fetch.py::_persist` |
| Python HTML only, no main-world parsing | `qb_result_html.py::Document` uses standard-library HTMLParser on driver-returned redacted HTML |

No new Python dependency; no changes to `Policy`, `installGuards`, campaign state
DDL/APIs, qb_trigger production code, qb_redact, design.md or the frozen design.
No QuickBuild/Gerrit request or push. The sha256 case creates a local bare remote
and local git objects; its actual result and every git argv are in `focused.log`.
`ls-remote` can match the sha256 remote on this host: `SHA_MATCHED`.

## Section 5.3 Negative-Case Map

All test names in this table are in `tests/unit/test_qb_result_fetch.py`.
`audit.json` contains every expanded nodeid and its actual source line, generated
from JUnit and AST (no hand-maintained case counts).

| Frozen clause | Tests |
|---|---|
| 1a three exact link IDs, origin, query, fragment, uniqueness | `test_parent_configuration_checks[id/duplicate/external/query/fragment/pipeline/children]` |
| Verified request URL, not page base | `test_request_url_not_page_base` |
| 1b breadcrumb/current item | `test_parent_configuration_checks[breadcrumb/current_link]` |
| 1c copy path | `test_parent_configuration_checks[copy]` |
| 1d build prefix | `test_parent_configuration_checks[name]` |
| Parent status/SR_STATUS record only | `test_pass_schema_and_parent_child_echo`, `test_accepted_is_record_only` |
| Child Build headers/row count/arch/absolute link/unique link | `test_child_table_checks[header/two_rows/arch/href/two_links]` |
| Missing/empty Child Build still checks parent variables | `test_child_pending_checks_parent_then_binds_once` (four independent cases) |
| 2 QB_TRIGGER_ID, target/marker, TYPE/REFERENCE/BRANCH, FAIL_FAST, architectures | `test_required_variables` parent cases, both missing and unequal |
| 2 required display labels | `test_parent_display_name` |
| 2 target exactly one line | `test_target_uniqueness[parent-duplicate]` |
| Parent snapshot observational only | `test_parent_snapshot_only_recorded` |
| 3 child breadcrumb/copy path | `test_child_configuration` |
| 3 status table/fallback/invalid spelling | `test_status_table`, `test_not_finished_parent_fallback`, `test_unrecognized_status` |
| 4 child IDs/FAIL_FAST/REPO_ARCH/CHILD_CONFIGURATIONS required | `test_required_variables` child missing/unequal cases |
| 4 full-list target once and no other commit | `test_target_uniqueness[child-duplicate/child-other_commit]`, `test_required_variables` missing/wrong target |
| 4 BUILD_REFERENCE missing / Live is record-only | `test_required_variables` child BUILD_REFERENCE cases |
| 4 EACH_GBS_BUILD_STATUS missing / nonempty guide / retrigger refusal | `test_required_variables`, `test_each_status_blocks_retrigger` |
| 4 snapshot invalid host/root/product/file/userinfo/query/fragment/slash/segments/shape/missing | `test_snapshot_negative_not_overridden` (eleven inputs, each with and without flag) |
| 4 drift with/without flag and previously accepted repeat | `test_drift_accept_and_repeat` |
| Drift flag invalid CLI modes, zero browser starts | `test_accept_drift_invalid_modes` |
| 5 optional 404/redirect/ID/structure failures | `test_optional_steps_ordinary_failure`, `test_read_failure_categories` |
| 5 optional redaction/agent exit/trusted-world failures remain fatal | `test_read_failure_categories` |
| Required-page error does not become optional | `test_read_failure_categories`, `test_required_http_failure` |

## Persistence, Privacy and Reference Controls

| Requirement | Tests |
|---|---|
| Closed schema and correct parent/child echo ownership | `test_pass_schema_and_parent_child_echo`, `test_result_schema_closed` |
| Existing RESULT: same fields/new accepted/different status | `test_terminal_idempotent_changed_fields_and_status` |
| Binding rejects stale/not-released/other binding; reverse lookup | `test_entry_refusals_no_browser`, `test_reverse_build_lookup`, `test_reverse_build_ambiguous` |
| One batch login, independent results | `test_batch_single_login_independent` |
| Unit lock throughout network, no SQLite transaction held during read | `test_lock_held_network_outside_transaction` |
| Bind/pending/result event/result status rollback | `test_write_point_rollback` |
| Bind write-transaction rechecks | `test_manual_binding_transaction_recheck` |
| Result recheck + new-file removal | `test_transaction_rechecks_and_removes_file` |
| file fsync -> rename -> directory fsync -> RESULT | `test_result_publication_fsync_order` |
| Each publication failure removes temporary/final file | `test_publication_failure_removes_temp_and_final` |
| Successful/Full/root, Requested By, unregistered Owner, credentials | `test_redacted_identity_keeps_business_fields`, `test_registered_user_residue_rejected` |
| Write-after-check failure removes evidence | `test_write_after_check_failure_removes_evidence` |
| Diagnostic archiving, including optional ID mismatch | `test_read_diagnostic_is_archived` |
| Diagnostic I/O failure preserves original category; post-write redaction failure remains fatal | `test_diagnostic_io_preserves_original_but_redaction_stops` |
| Sensitive protocol keys rejected, no evidence | `test_agent_sensitive_keys_never_archived` |

`tests/unit/test_qb_browser.py` additionally checks original read-error category
retention and nonnegative integer identity counts. The trusted browser test asserts
the agent returns the count while main-world hostile builtins remain ineffective.

## Reproduction

From repository root, use `.venv/bin/python <this-directory>/run_validation.py`
with each of `pytest`, `focused`, `tools`, `node`. The corresponding
`commands-*.json` records exact argv, cwd, elapsed time and exit; raw logs are kept
alongside JUnit. `audit_completion.py` verifies immutable boundaries, counts cases
and checks the baseline collection is a subset of the final collection.
Ruff runs on the complete staged-tree export, excluding unrelated user worktree
changes/untracked drafts; export tree/path are recorded in `ruff.log`.

No real build evidence is claimed. C5/C6 raw/live-document comparison, successful
sample, BUILD_NOTES sample and confirmed real submission remain open.

## Recorded Gates

| Command group | Result | Evidence |
|---|---|---|
| full pytest, final | 2632 passed, 0 failed, 1 skipped; +194, zero removed | `pytest.log`, `pytest.xml`, `commands-pytest.json`, `audit.json` |
| focused | 354 passed, 0 failed, 0 skipped | `focused.log`, `focused.xml`, `commands-focused.json` |
| mypy | exit 0, 116 source files | `mypy.log` |
| lint-imports | exit 0, 6 kept, 0 broken | `lint-imports.log` |
| design checker | exit 0, 0 problem | `design-check.log` |
| Ruff complete staged tree | exit 0 | `ruff.log`, `commands-ruff.json` |
| Node pytest wrappers | 13 passed, 0 failed, 0 skipped | `node-gates.log`, `node-gates.xml` |
| Node internal counts | unit 163; static guards/mutations 183; trusted reads 37; fields 16; DOM 64; config source 67, all passed | `node-gates.log` |
| Local interception safety | 4/4; Worker branch b fail-closed, attack HTTP=0, WS=0, browser/profile removed | `node-gates.log:616` |

The initial full-suite run (`pytest-initial.log`: 2628 passed/1 skipped) preceded
four additional diagnostic I/O-versus-redaction controls. It is not the final
acceptance run; use `pytest.log` and `commands-pytest.json` for the final tree.

The fetch cases are partitioned without double counting: reading/persistence 155,
transactions/primitives 15, credentials/redaction 14. The 184 fetch cases, nine
new driver cases and one sha256 case give 194 new pytest nodeids. The 169 driver
cases in the focused run include existing regressions. The sole full-suite skip
is the existing case-insensitive-filesystem platform-specific test.
