# P4.9 step-0 Symbol Audit

## Scope

This audit covers only modules and symbols changed by step-0: the QuickBuild
HTTP surface, workspace functions and markers, failure classification,
state/types moves, and `discover_sibling_pythonpath`. `gbs_report.py` remains
out of scope and is deferred as a whole to the triage-report extraction batch.

## Revision

- Design: `p49-step0-design-v2.0-FROZEN.md`, including revisions 1 through 7a.
- Design SHA-256: `18ac1b7f7cc977f988ebafbef00cf7415a18cf2b21b45d9809b4db01c59040ce`.
- Audit round: revision-7a closeout working tree.
- Result: 42 symbol OK + 4 module-scope OK covering 48 symbols;
  0 MISMATCH, 0 INCOMPLETE.
- Commit ② reached 42/42 but its stdout was not written back promptly; this
  round corrects that bookkeeping gap with the current complete output.
- Report integrity is anchored by the Git commit containing this report; the
  report does not record its own hash.

## Method

The audit is read-only and uses Python AST/source analysis; it does not import
or execute production modules. Run both checks from the repository root:

```bash
PYTHONPATH=tizen-ci-shared/scripts:tizen-ci-triage/scripts \
  .venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
PYTHONPATH=tizen-ci-shared/scripts:tizen-ci-triage/scripts \
  .venv/bin/python docs/clang-fix-campaign/tools/table_audit_bridge.py
```

The first command verifies definitions, measured consumers, internal access,
format authority, public-surface completeness, L-1 type closure, and the
module-scope anti-abuse rules. The bridge parses the frozen design's §1.2a,
§2, §3.2, §3.3, and §4.1 tables fail-closed and performs a complete
bidirectional ownership diff against `symbol_audit.SPECS`.

## Commit ③ Historical Symbol Audit Output (Before Revisions 6/7a)

```text
symbol | declared | measured_consumers | verdict
GerritPatchSet | sections=§2+v2.0-revision-1; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.gerrit]; internal=[-] | definition=tizen_ci_shared/types.py:10; consumers=[ci_triage.gerrit]; internal=[GerritChange@28] | OK
GerritChange | sections=§2+v2.0-revision-1; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.gerrit]; internal=[-] | definition=tizen_ci_shared/types.py:19; consumers=[ci_triage.gerrit]; internal=[SourceFetchResult@38] | OK
SourceFetchResult | sections=§2+v2.0-revision-1; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.gerrit,ci_triage.report]; internal=[-] | definition=tizen_ci_shared/types.py:32; consumers=[ci_triage.gerrit,ci_triage.report]; internal=[-] | OK
FailedPackage | sections=§2; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.orchestrator,ci_triage.quickbuild_log,ci_triage.report,ci_triage.runner]; internal=[-] | definition=tizen_ci_shared/types.py:43; consumers=[ci_triage.orchestrator,ci_triage.quickbuild_log,ci_triage.report,ci_triage.runner]; internal=[-] | OK
DisposableWorktree | sections=§2+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.workspace]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:22; consumers=[ci_triage.verify.workspace]; internal=[_oldest_worktrees@162,163,178,_verify_cleanup_handle@146,cleanup_disposable_copy@94,cleanup_worktree@72,mark_worktree_protected@108] | OK
WorkspaceViolation | sections=§2+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.campaign_repair_step,ci_triage.verify.workspace]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:17; consumers=[ci_triage.campaign_repair_step,ci_triage.verify.workspace]; internal=[_read_marker@193,_verify_cleanup_handle@149,157,159,cleanup_disposable_copy@90,103] | OK
FailureClassification | sections=§2; status=existing; owner=shared/classify; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=tizen_ci_shared/classify.py:43; consumers=[ci_triage.verify.build_verify]; internal=[_heuristic_classification@213,219,230,_match_denylist@193,203,_source_diagnostic_classification@239,241,250,259,268,279,classify_failure@133,146,159,173] | OK
discover_sibling_pythonpath | sections=§3.3; status=existing; owner=shared/env; expected_owner=-; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.orchestrator,ci_triage.verify.build_verify]; internal=[-] | definition=tizen_ci_shared/env.py:8; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.orchestrator,ci_triage.verify.build_verify]; internal=[-] | OK
create_worktree | sections=§3.2; status=existing; owner=build-verify; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:42; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
check_disk_and_maybe_cleanup | sections=§3.2; status=existing; owner=build-verify; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:79; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_copy_repository | sections=§3.2; status=existing; owner=build-verify; expected_owner=-; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:117; consumers=[-]; internal=[create_worktree@57] | OK
cleanup_worktree | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.build_verify,ci_triage.verify.workspace]; internal=[cleanup_disposable_copy] | definition=tizen_ci_shared/workspace/__init__.py:72; consumers=[ci_triage.verify.build_verify,ci_triage.verify.workspace]; internal=[cleanup_disposable_copy@104] | OK
cleanup_disposable_copy | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:79; consumers=[ci_triage.campaign_repair_step]; internal=[-] | OK
is_protected | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.campaign_repair_step,ci_triage.verify.workspace]; internal=[cleanup_disposable_copy] | definition=tizen_ci_shared/workspace/__init__.py:140; consumers=[ci_triage.campaign_repair_step,ci_triage.verify.workspace]; internal=[cleanup_disposable_copy@89] | OK
release_worktree_protection | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:130; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | OK
mark_worktree_protected | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:107; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_oldest_worktrees | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.workspace]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:162; consumers=[ci_triage.verify.workspace]; internal=[-] | OK
_run_git | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.workspace]; internal=[clean_repository_preserving_markers] | definition=tizen_ci_shared/workspace/__init__.py:205; consumers=[ci_triage.verify.workspace]; internal=[clean_repository_preserving_markers@58] | OK
_verify_cleanup_handle | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[cleanup_worktree,mark_worktree_protected] | definition=tizen_ci_shared/workspace/__init__.py:146; consumers=[-]; internal=[cleanup_worktree@75,mark_worktree_protected@115] | OK
_exclude_private_files | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.workspace]; internal=[mark_worktree_protected] | definition=tizen_ci_shared/workspace/__init__.py:209; consumers=[ci_triage.verify.workspace]; internal=[mark_worktree_protected@117] | OK
MARKER_FILENAME | sections=§3.1+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:13; consumers=[-]; internal=[_exclude_private_files@223,_oldest_worktrees@167,clean_repository_preserving_markers@65,cleanup_disposable_copy@91,write_workdir_marker@43]; marker_reads=[_oldest_worktrees@168,_oldest_worktrees@171,_verify_cleanup_handle@148,_verify_cleanup_handle@151,cleanup_disposable_copy@92]; marker_writes=[write_workdir_marker@51] | OK
PROTECTED_FILENAME | sections=§3.1+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:14; consumers=[-]; internal=[_exclude_private_files@223,clean_repository_preserving_markers@67,is_protected@143,mark_worktree_protected@124,release_worktree_protection@133]; marker_reads=[is_protected@143,release_worktree_protection@134]; marker_writes=[mark_worktree_protected@124,release_worktree_protection@136] | OK
_read_marker | sections=§3.1+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[cleanup_disposable_copy,_verify_cleanup_handle,_oldest_worktrees] | definition=tizen_ci_shared/workspace/__init__.py:190; consumers=[-]; internal=[_oldest_worktrees@171,_verify_cleanup_handle@151,cleanup_disposable_copy@92] | OK
write_workdir_marker | sections=§3.2+S-1; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.workspace]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:33; consumers=[ci_triage.verify.workspace]; internal=[-] | OK
clean_repository_preserving_markers | sections=§3.2+S-1+v2.0-revision-3; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.workspace]; internal=[-] | definition=tizen_ci_shared/workspace/__init__.py:55; consumers=[ci_triage.verify.workspace]; internal=[-] | OK
HttpFetcher | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:35; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@111,download_package_buildlog@174] | OK
QuickBuildError | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:56; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@198,_urllib_fetch@225,download_full_log@123,download_package_buildlog@183,load_cookie_jar@70,75,81,98] | OK
_raise_if_login_page | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:190; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@119,131] | OK
_urllib_fetch | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:205; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@116,download_package_buildlog@181] | OK
DEFAULT_COOKIE_PATH | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:16; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@201,download_full_log@109,load_cookie_jar@64] | OK
DEFAULT_QUICKBUILD_BASE_URL | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:15; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@110] | OK
load_cookie_jar | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:64; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@115] | OK
DOWNLOAD_LINK_MARKER | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[find_download_href] | definition=tizen_ci_shared/quickbuild_http.py:17; consumers=[-]; internal=[find_download_href@145] | OK
DOWNLOAD_TIZEN_BASE_URL | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[derive_package_buildlog_url] | definition=tizen_ci_shared/quickbuild_http.py:18; consumers=[-]; internal=[derive_package_buildlog_url@166] | OK
HttpResponse | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:22; consumers=[-]; internal=[_raise_if_login_page@190,_urllib_fetch@205,211,218] | OK
QuickBuildDownload | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:39; consumers=[-]; internal=[download_full_log@112,132] | OK
PackageBuildLog | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:49; consumers=[-]; internal=[download_package_buildlog@175,187] | OK
download_full_log | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:106; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
find_download_href | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[download_full_log] | definition=tizen_ci_shared/quickbuild_http.py:140; consumers=[-]; internal=[download_full_log@121] | OK
derive_package_buildlog_url | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[download_package_buildlog] | definition=tizen_ci_shared/quickbuild_http.py:150; consumers=[-]; internal=[download_package_buildlog@178] | OK
download_package_buildlog | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.runner]; internal=[-] | definition=tizen_ci_shared/quickbuild_http.py:171; consumers=[ci_triage.runner]; internal=[-] | OK
normalize_quickbuild_url | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[_urllib_fetch] | definition=tizen_ci_shared/quickbuild_http.py:228; consumers=[-]; internal=[_urllib_fetch@206] | OK
SUMMARY | 42 OK | 0 MISMATCH | 0 INCOMPLETE
```

## Commit ③ Historical Table Bridge Output (Before Revisions 6/7a)

```text
symbol | body_owner | inventory_owner | verdict
DEFAULT_COOKIE_PATH | shared/quickbuild_http | shared/quickbuild_http | OK
DEFAULT_QUICKBUILD_BASE_URL | shared/quickbuild_http | shared/quickbuild_http | OK
DOWNLOAD_LINK_MARKER | shared/quickbuild_http | shared/quickbuild_http | OK
DOWNLOAD_TIZEN_BASE_URL | shared/quickbuild_http | shared/quickbuild_http | OK
DisposableWorktree | shared/workspace | shared/workspace | OK
FailedPackage | shared/types | shared/types | OK
FailureClassification | shared/classify | shared/classify | OK
GerritChange | shared/types | shared/types | OK
GerritPatchSet | shared/types | shared/types | OK
HttpFetcher | shared/quickbuild_http | shared/quickbuild_http | OK
HttpResponse | shared/quickbuild_http | shared/quickbuild_http | OK
MARKER_FILENAME | shared/workspace | shared/workspace | OK
PROTECTED_FILENAME | shared/workspace | shared/workspace | OK
PackageBuildLog | shared/quickbuild_http | shared/quickbuild_http | OK
QuickBuildDownload | shared/quickbuild_http | shared/quickbuild_http | OK
QuickBuildError | shared/quickbuild_http | shared/quickbuild_http | OK
SourceFetchResult | shared/types | shared/types | OK
WorkspaceViolation | shared/workspace | shared/workspace | OK
_copy_repository | build-verify | build-verify | OK
_exclude_private_files | shared/workspace | shared/workspace | OK
_oldest_worktrees | shared/workspace | shared/workspace | OK
_raise_if_login_page | shared/quickbuild_http | shared/quickbuild_http | OK
_read_marker | shared/workspace | shared/workspace | OK
_run_git | shared/workspace | shared/workspace | OK
_urllib_fetch | shared/quickbuild_http | shared/quickbuild_http | OK
_verify_cleanup_handle | shared/workspace | shared/workspace | OK
check_disk_and_maybe_cleanup | build-verify | build-verify | OK
clean_repository_preserving_markers | shared/workspace | shared/workspace | OK
cleanup_disposable_copy | shared/workspace | shared/workspace | OK
cleanup_worktree | shared/workspace | shared/workspace | OK
create_worktree | build-verify | build-verify | OK
derive_package_buildlog_url | shared/quickbuild_http | shared/quickbuild_http | OK
discover_sibling_pythonpath | shared/env | shared/env | OK
download_full_log | shared/quickbuild_http | shared/quickbuild_http | OK
download_package_buildlog | shared/quickbuild_http | shared/quickbuild_http | OK
find_download_href | shared/quickbuild_http | shared/quickbuild_http | OK
is_protected | shared/workspace | shared/workspace | OK
load_cookie_jar | shared/quickbuild_http | shared/quickbuild_http | OK
mark_worktree_protected | shared/workspace | shared/workspace | OK
normalize_quickbuild_url | shared/quickbuild_http | shared/quickbuild_http | OK
release_worktree_protection | shared/workspace | shared/workspace | OK
write_workdir_marker | shared/workspace | shared/workspace | OK
SUMMARY | 42 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
```

## Negative Controls

The commit ③ controls are recorded verbatim in
`dev_memory/stage07_p49_step0/progress.md`:

1. Change one design-table owner: `OWNER_MISMATCH`, exit 1.
2. Remove one inventory symbol: `MISSING_FROM_INVENTORY`, exit 1.
3. Import env from quickbuild_http: L0 independence broken, exit 1.
4. Import quickbuild_http from env: L0 independence broken, exit 1.

After every temporary violation was removed, symbol audit and the table bridge
both returned exit 0, and import-linter reported 4 kept / 0 broken.

## Revision-6 Closeout Audit: STOP

Command:

```text
python3 docs/clang-fix-campaign/tools/symbol_audit.py
```

Revision-6 added `_is_relative_to` to the body and inventory, then changed the
INCOMPLETE guard from selected modules to every physical module under
`tizen_ci_shared`. The workspace, types, env, and quickbuild_http surfaces are
complete. The newly active guard found 47 unaudited symbols in classify and
state, so closeout stopped before producing a CLOSED claim.

```text
classify.py (26 INCOMPLETE):
CONFIDENCE_THRESHOLD, DENYLIST_RULES, EXPLICIT_NON_REPAIR_CLASSES,
NON_BUILD_STAGE_CLASSES, RAW_KINDS, REPAIR_AUTO, REPAIR_DENIED,
REPAIR_NEEDS_CONFIRMATION, SOURCE_KINDS, SUSPECT_PATH_PARTS, SYSTEM_PREFIXES,
_DenyRule, _has_source_location, _heuristic_classification, _kind,
_looks_project_source_path, _match_denylist, _message_has_source_symbol,
_primary_error, _probably_fixable, _source_diagnostic_classification,
_source_file, _source_owned, _source_reachable, _string, classify_failure

state/db.py (10 INCOMPLETE):
GERRIT_READY, StateDatabase, _VERIFICATION_COLUMNS, _configure_connection,
_initialize_schema, _insert_status, _insert_verification_record, _now_iso8601,
_row_optional_string, _row_string

state/keys.py (3 INCOMPLETE):
build_failure_key, build_submission_key, failure_key_sha12

state/records.py (8 INCOMPLETE):
LatestStatusRow, VerificationRecord, _record_to_values, get_latest_status,
get_latest_status_row, get_record, record_status, write_pass_record

SUMMARY | 43 OK | 0 MISMATCH | 47 INCOMPLETE
exit_code=1
```

The corresponding four-table bridge already accepts the revision-6 body and
inventory addition:

```text
SUMMARY | 43 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY |
0 OWNER_MISMATCH | 0 PARSE_ERROR
exit_code=0
```

No owner or consumer declaration has been invented for the 47 newly exposed
symbols. They require a design-side ruling and explicit body-table entries
before the audit inventory can be expanded.

## Revision-7a Resolution

Revision-7a resolved the stop by adding four closed module-scope entries. The
module rows cover every top-level symbol in an intact migrated file and reject
per-symbol overlap. The final measured module output is:

```text
state/db.py | module-scope | shared/state | 10 symbols covered; consumers=[ci_triage.campaign_repair_step,ci_triage.campaign_state,ci_triage.cli,ci_triage.previous_evidence,ci_triage.verify.build_verify,ci_triage.verify.gerrit_submit] | OK
state/keys.py | module-scope | shared/state | 3 symbols covered; consumers=[ci_triage.campaign_repair_step,ci_triage.campaign_state,ci_triage.cli,ci_triage.previous_evidence,ci_triage.verify.build_verify,ci_triage.verify.gerrit_submit] | OK
state/records.py | module-scope | shared/state | 8 symbols covered; consumers=[ci_triage.campaign_repair_step,ci_triage.campaign_state,ci_triage.cli,ci_triage.previous_evidence,ci_triage.verify.build_verify,ci_triage.verify.gerrit_submit] | OK
classify.py | module-scope | shared/classify | 27 symbols covered; consumers=[ci_triage.campaign_repair_step,ci_triage.verify.build_verify,ci_triage.verify.failure_classify] | OK
SUMMARY | 42 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
exit_code=0
```

The fifth-table bridge is also green:

```text
SUMMARY | 42 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
exit_code=0
```

Two revision-7 negative controls proved the new category fail-closed:

```text
# Remove the classify.py row from §1.2a
classify.py | - | shared/classify | MISSING_FROM_BODY
SUMMARY | 42 SYMBOL OK | 3 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 1 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
exit_code=1

# Add a function definition to the legacy classify shim
classify.py | module-scope | shared/classify | 27 symbols covered; ... | MISMATCH: legacy pure-shim contains non-re-export FunctionDef at ci_triage/verify/failure_classify.py:18
SUMMARY | 42 SYMBOL OK | 3 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 1 MISMATCH | 0 INCOMPLETE
exit_code=1
```

Both temporary violations were removed. The positive commands above were run
again after restoration and returned exit 0.
