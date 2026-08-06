# P4.9 step-0 symbol attribution audit

## Round 3 Result (v1.3 shared internal layering)

**PASS - the v1.3 design may proceed to second-round step-0 review.**

This pass refines shared ownership labels without changing any measured
consumer declarations:

- `shared/types`: cross-skill data contracts
- `shared/quickbuild_http`: QuickBuild HTTP primitives and GBS fetch
- `shared/workspace`: disposable-copy and marker authority
- `shared/classify`: failure classification

Result: **59/59 OK, 0 MISMATCH, 0 INCOMPLETE**.

## Round 3 Inputs And Method

- Design SHA-256: `66d3cf9925e7bdcf590b14ba9f1f8fa67dcab263bb8158ef3a47d28bc2c4a7ab`
- Audit script SHA-256: `fdb8cb6c54e03302d216d51cae321a2c3a4e061a4d1c1302845e8d1bdaaa7fa8`
- Round-2 report anchor: commit `4b3029a`, SHA-256
  `54ab1b5cc5c7eac59f38475e85620c2e10ebeda813bf40a11c5f1324b25a37dc`
- Command: `.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py`
- Audited source root: `tizen-ci-triage/scripts/`
- Analysis remains source-text and AST only; no audited module is imported
  or executed.
- Completeness guards cover the top-level function, class, and constant
  surfaces of both `gbs_report.py` and `quickbuild.py`.
- The planned `write_workdir_marker` primitive now checks the exact expected
  owner `shared/workspace`; it does not merely accept any shared label.

Negative controls:

- Removing `QuickBuildError` from the inventory produces
  `58 OK / 0 MISMATCH / 1 INCOMPLETE` and exit 1.
- Relabeling `write_workdir_marker` as bare `shared` produces
  `58 OK / 1 MISMATCH / 0 INCOMPLETE` and exit 1.

## Round 3 Raw Output

The following is the complete stdout from the command above.

```text
symbol | declared | measured_consumers | verdict
SourceFetchResult | sections=§2; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.report]; internal=[-] | definition=ci_triage/gerrit.py:43; consumers=[ci_triage.report]; internal=[fetch_source_for_commit@157,231,239,247] | OK
FailedPackage | sections=§2; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.orchestrator,ci_triage.report,ci_triage.runner]; internal=[-] | definition=ci_triage/quickbuild_log.py:11; consumers=[ci_triage.orchestrator,ci_triage.report,ci_triage.runner]; internal=[parse_failed_packages@56,59,74,select_failed_package@89,92] | OK
DisposableWorktree | sections=§2+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:31; consumers=[-]; internal=[_oldest_worktrees@220,221,236,_verify_cleanup_handle@204,cleanup_disposable_copy@114,cleanup_worktree@92,create_worktree@47,82,mark_worktree_protected@128] | OK
WorkspaceViolation | sections=§2+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/workspace.py:26; consumers=[ci_triage.campaign_repair_step]; internal=[_read_marker@251,_verify_cleanup_handle@207,215,217,check_disk_and_maybe_cleanup@187,cleanup_disposable_copy@110,123,create_worktree@57] | OK
FailureClassification | sections=§2; status=existing; owner=shared/classify; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/failure_classify.py:43; consumers=[ci_triage.verify.build_verify]; internal=[_heuristic_classification@213,219,230,_match_denylist@193,203,_source_diagnostic_classification@239,241,250,259,268,279,classify_failure@133,146,159,173] | OK
GbsReportPackage | sections=§2+§4; status=existing; owner=shared/types; expected_owner=-; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:30; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[GbsReport@49,GbsReport.failed_packages@52,_row_to_package@312,326,download_gbs_package_buildlog@104,parse_gbs_report_packages@139,144] | OK
GbsReport | sections=§2+§4; status=existing; owner=shared/types; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:42; consumers=[-]; internal=[fetch_gbs_report@63,94] | OK
create_worktree | sections=§3.2; status=existing; owner=build-verify; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:42; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
check_disk_and_maybe_cleanup | sections=§3.2; status=existing; owner=build-verify; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:166; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_copy_repository | sections=§3.2; status=existing; owner=build-verify; expected_owner=-; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:267; consumers=[-]; internal=[create_worktree@58] | OK
cleanup_worktree | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[cleanup_disposable_copy,check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:92; consumers=[ci_triage.verify.build_verify]; internal=[check_disk_and_maybe_cleanup@186,cleanup_disposable_copy@124] | OK
cleanup_disposable_copy | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/workspace.py:99; consumers=[ci_triage.campaign_repair_step]; internal=[-] | OK
is_protected | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.campaign_repair_step]; internal=[cleanup_disposable_copy,check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:160; consumers=[ci_triage.campaign_repair_step]; internal=[check_disk_and_maybe_cleanup@182,cleanup_disposable_copy@109] | OK
release_worktree_protection | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | definition=ci_triage/verify/workspace.py:150; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | OK
mark_worktree_protected | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:127; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_oldest_worktrees | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:220; consumers=[-]; internal=[check_disk_and_maybe_cleanup@181] | OK
_run_git | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:263; consumers=[-]; internal=[create_worktree@68,69,70] | OK
_verify_cleanup_handle | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[cleanup_worktree,mark_worktree_protected] | definition=ci_triage/verify/workspace.py:204; consumers=[-]; internal=[cleanup_worktree@95,mark_worktree_protected@135] | OK
_exclude_private_files | sections=§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[create_worktree,mark_worktree_protected] | definition=ci_triage/verify/workspace.py:273; consumers=[-]; internal=[create_worktree@59,mark_worktree_protected@137] | OK
MARKER_FILENAME | sections=§3.1+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:21; consumers=[-]; internal=[_exclude_private_files@287,_oldest_worktrees@225,cleanup_disposable_copy@111,create_worktree@53,77]; marker_reads=[_oldest_worktrees@226,_oldest_worktrees@229,_verify_cleanup_handle@206,_verify_cleanup_handle@209,cleanup_disposable_copy@112]; marker_writes=[create_worktree@67] | OK
PROTECTED_FILENAME | sections=§3.1+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:22; consumers=[-]; internal=[_exclude_private_files@287,create_worktree@79,is_protected@163,mark_worktree_protected@144,release_worktree_protection@153]; marker_reads=[is_protected@163,release_worktree_protection@154]; marker_writes=[mark_worktree_protected@144,release_worktree_protection@156] | OK
_read_marker | sections=§3.1+§3.2; status=existing; owner=shared/workspace; expected_owner=-; consumers=[-]; internal=[cleanup_disposable_copy,_verify_cleanup_handle,_oldest_worktrees] | definition=ci_triage/verify/workspace.py:248; consumers=[-]; internal=[_oldest_worktrees@229,_verify_cleanup_handle@209,cleanup_disposable_copy@112] | OK
write_workdir_marker | sections=§3.2+S-1; status=to-be-created; owner=shared/workspace; expected_owner=shared/workspace; consumers=[-]; internal=[create_worktree] | definition=TO_BE_CREATED; consumers=[-]; internal=[-] | OK
fetch_gbs_report | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:56; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
download_gbs_package_buildlog | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:103; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
DEFAULT_ARCHES | sections=§4; status=existing; owner=orchestrator; expected_owner=-; consumers=[ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:20; consumers=[ci_triage.orchestrator]; internal=[-] | OK
HttpFetcher | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:35; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@111,download_package_buildlog@174] | OK
QuickBuildError | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:56; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@198,_urllib_fetch@225,download_full_log@123,download_package_buildlog@183,load_cookie_jar@70,75,81,98] | OK
_raise_if_login_page | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:190; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@119,131] | OK
_urllib_fetch | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:205; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@116,download_package_buildlog@181] | OK
DEFAULT_COOKIE_PATH | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:16; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@201,download_full_log@109,load_cookie_jar@64] | OK
DEFAULT_QUICKBUILD_BASE_URL | sections=§4; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:15; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@110] | OK
load_cookie_jar | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:64; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@115] | OK
DOWNLOAD_LINK_MARKER | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[find_download_href] | definition=ci_triage/quickbuild.py:17; consumers=[-]; internal=[find_download_href@145] | OK
DOWNLOAD_TIZEN_BASE_URL | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[derive_package_buildlog_url] | definition=ci_triage/quickbuild.py:18; consumers=[-]; internal=[derive_package_buildlog_url@166] | OK
HttpResponse | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/quickbuild.py:22; consumers=[-]; internal=[_raise_if_login_page@190,_urllib_fetch@205,211,218] | OK
QuickBuildDownload | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/quickbuild.py:39; consumers=[-]; internal=[download_full_log@112,132] | OK
PackageBuildLog | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/quickbuild.py:49; consumers=[-]; internal=[download_package_buildlog@175,187] | OK
download_full_log | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | definition=ci_triage/quickbuild.py:106; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
find_download_href | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[download_full_log] | definition=ci_triage/quickbuild.py:140; consumers=[-]; internal=[download_full_log@121] | OK
derive_package_buildlog_url | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[download_package_buildlog] | definition=ci_triage/quickbuild.py:150; consumers=[-]; internal=[download_package_buildlog@178] | OK
download_package_buildlog | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[ci_triage.runner]; internal=[-] | definition=ci_triage/quickbuild.py:171; consumers=[ci_triage.runner]; internal=[-] | OK
normalize_quickbuild_url | sections=§4+v1.2-A; status=existing; owner=shared/quickbuild_http; expected_owner=-; consumers=[-]; internal=[_urllib_fetch] | definition=ci_triage/quickbuild.py:228; consumers=[-]; internal=[_urllib_fetch@206] | OK
find_iframe_src | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[fetch_gbs_report] | definition=ci_triage/gbs_report.py:125; consumers=[-]; internal=[fetch_gbs_report@72] | OK
parse_gbs_report_packages | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[fetch_gbs_report] | definition=ci_triage/gbs_report.py:133; consumers=[-]; internal=[fetch_gbs_report@88] | OK
_Anchor | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:156; consumers=[-]; internal=[_Cell@165,_CellBuilder@181,_ReportTableParser.handle_endtag@245,_status_from_anchor@336] | OK
_Cell | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:163; consumers=[-]; internal=[_ReportTableParser.__init__@211,_ReportTableParser.handle_endtag@259,_Row@170] | OK
_Row | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:169; consumers=[-]; internal=[_ReportTableParser.__init__@210,_ReportTableParser.handle_endtag@268,_Table@175,_row_to_package@307] | OK
_Table | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:174; consumers=[-]; internal=[_ReportTableParser.__init__@214,_ReportTableParser.handle_endtag@275,_looks_like_build_status_table@287] | OK
_CellBuilder | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:179; consumers=[-]; internal=[_ReportTableParser.__init__@212,_ReportTableParser.handle_starttag@232] | OK
_AnchorBuilder | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:185; consumers=[-]; internal=[_ReportTableParser.__init__@213,_ReportTableParser.handle_starttag@235] | OK
_IframeParser | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[find_iframe_src] | definition=ci_triage/gbs_report.py:191; consumers=[-]; internal=[find_iframe_src@128] | OK
_ReportTableParser | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:205; consumers=[-]; internal=[parse_gbs_report_packages@142] | OK
_looks_like_build_status_table | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:287; consumers=[-]; internal=[parse_gbs_report_packages@146] | OK
_row_to_package | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:306; consumers=[-]; internal=[parse_gbs_report_packages@149] | OK
_status_from_anchor | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[_row_to_package] | definition=ci_triage/gbs_report.py:336; consumers=[-]; internal=[_row_to_package@322] | OK
_attrs_to_map | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[_IframeParser.handle_starttag,_ReportTableParser.handle_starttag] | definition=ci_triage/gbs_report.py:349; consumers=[-]; internal=[_IframeParser.handle_starttag@199,_ReportTableParser.handle_starttag@217] | OK
_class_names | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[_ReportTableParser.handle_starttag] | definition=ci_triage/gbs_report.py:353; consumers=[-]; internal=[_ReportTableParser.handle_starttag@236] | OK
_normalize_text | sections=§4; status=existing; owner=triage-report; expected_owner=-; consumers=[-]; internal=[_ReportTableParser.handle_endtag] | definition=ci_triage/gbs_report.py:357; consumers=[-]; internal=[_ReportTableParser.handle_endtag@248,260] | OK
SUMMARY | 59 OK | 0 MISMATCH | 0 INCOMPLETE
```

---


## Round 2 Result

**PASS - the attribution tables may proceed to three-party review.**

The round-2 inventory applies the final v1.2 rulings and expands the
completeness guard to both `gbs_report.py` and `quickbuild.py`. The inventory
length is dynamic; this run audited 59 unique symbols:

- 59 OK
- 0 MISMATCH
- 0 INCOMPLETE

Sections 1.2, 2, 3.2, and 4 of the design body now carry the same ownership
decisions as the audit inventory. The freeze gate is no longer a hard-coded
symbol count: every inventoried symbol must be OK, and both mismatch and
incomplete counts must be zero.

## Inputs And Method

- Design input: `docs/clang-fix-campaign/p49-step0-design-v1.0-draft.md`
- Authoritative correction: the final v1.2 correction section
- Design SHA-256: `65049462118dbb9f5c3ca0b93577ebba3c5a820d21061471ebef70dd90a3c50f`
- Audit script SHA-256: `06a0b11b47a92b7577c87a9bb998c81f68e0daf10e63a03b33faf773db6c256e`
- Audited source root: `tizen-ci-triage/scripts/`
- Excluded: tests, `__pycache__`, and `release-v1.4.0/` snapshots
- Analysis mode: Python source text plus AST only; audited modules are never
  imported or executed
- Marker audit: function-body reads and writes of `MARKER_FILENAME` and
  `PROTECTED_FILENAME` are listed separately
- Planned primitive policy: a `status=to-be-created` symbol validates its
  declared shared ownership without requiring a current definition
- Completeness guards:
  - all 21 top-level symbols in `ci_triage/gbs_report.py`
  - all 17 top-level functions, classes, constants, and type aliases in
    `ci_triage/quickbuild.py`

Command:

```bash
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
```

## Round 2 Raw Output

The following is the complete stdout from the command above.

```text
symbol | declared | measured_consumers | verdict
SourceFetchResult | sections=§2; status=existing; owner=shared/types; consumers=[ci_triage.report]; internal=[-] | definition=ci_triage/gerrit.py:43; consumers=[ci_triage.report]; internal=[fetch_source_for_commit@157,231,239,247] | OK
FailedPackage | sections=§2; status=existing; owner=shared/types; consumers=[ci_triage.orchestrator,ci_triage.report,ci_triage.runner]; internal=[-] | definition=ci_triage/quickbuild_log.py:11; consumers=[ci_triage.orchestrator,ci_triage.report,ci_triage.runner]; internal=[parse_failed_packages@56,59,74,select_failed_package@89,92] | OK
DisposableWorktree | sections=§2+§3.2; status=existing; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:31; consumers=[-]; internal=[_oldest_worktrees@220,221,236,_verify_cleanup_handle@204,cleanup_disposable_copy@114,cleanup_worktree@92,create_worktree@47,82,mark_worktree_protected@128] | OK
WorkspaceViolation | sections=§2+§3.2; status=existing; owner=shared; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/workspace.py:26; consumers=[ci_triage.campaign_repair_step]; internal=[_read_marker@251,_verify_cleanup_handle@207,215,217,check_disk_and_maybe_cleanup@187,cleanup_disposable_copy@110,123,create_worktree@57] | OK
FailureClassification | sections=§2; status=existing; owner=shared; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/failure_classify.py:43; consumers=[ci_triage.verify.build_verify]; internal=[_heuristic_classification@213,219,230,_match_denylist@193,203,_source_diagnostic_classification@239,241,250,259,268,279,classify_failure@133,146,159,173] | OK
GbsReportPackage | sections=§2+§4; status=existing; owner=shared/types; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:30; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[GbsReport@49,GbsReport.failed_packages@52,_row_to_package@312,326,download_gbs_package_buildlog@104,parse_gbs_report_packages@139,144] | OK
GbsReport | sections=§2+§4; status=existing; owner=shared/types; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:42; consumers=[-]; internal=[fetch_gbs_report@63,94] | OK
create_worktree | sections=§3.2; status=existing; owner=build-verify; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:42; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
check_disk_and_maybe_cleanup | sections=§3.2; status=existing; owner=build-verify; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:166; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_copy_repository | sections=§3.2; status=existing; owner=build-verify; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:267; consumers=[-]; internal=[create_worktree@58] | OK
cleanup_worktree | sections=§3.2; status=existing; owner=shared; consumers=[ci_triage.verify.build_verify]; internal=[cleanup_disposable_copy,check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:92; consumers=[ci_triage.verify.build_verify]; internal=[check_disk_and_maybe_cleanup@186,cleanup_disposable_copy@124] | OK
cleanup_disposable_copy | sections=§3.2; status=existing; owner=shared; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/workspace.py:99; consumers=[ci_triage.campaign_repair_step]; internal=[-] | OK
is_protected | sections=§3.2; status=existing; owner=shared; consumers=[ci_triage.campaign_repair_step]; internal=[cleanup_disposable_copy,check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:160; consumers=[ci_triage.campaign_repair_step]; internal=[check_disk_and_maybe_cleanup@182,cleanup_disposable_copy@109] | OK
release_worktree_protection | sections=§3.2; status=existing; owner=shared; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | definition=ci_triage/verify/workspace.py:150; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | OK
mark_worktree_protected | sections=§3.2; status=existing; owner=shared; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:127; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_oldest_worktrees | sections=§3.2; status=existing; owner=shared; consumers=[-]; internal=[check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:220; consumers=[-]; internal=[check_disk_and_maybe_cleanup@181] | OK
_run_git | sections=§3.2; status=existing; owner=shared; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:263; consumers=[-]; internal=[create_worktree@68,69,70] | OK
_verify_cleanup_handle | sections=§3.2; status=existing; owner=shared; consumers=[-]; internal=[cleanup_worktree,mark_worktree_protected] | definition=ci_triage/verify/workspace.py:204; consumers=[-]; internal=[cleanup_worktree@95,mark_worktree_protected@135] | OK
_exclude_private_files | sections=§3.2; status=existing; owner=shared; consumers=[-]; internal=[create_worktree,mark_worktree_protected] | definition=ci_triage/verify/workspace.py:273; consumers=[-]; internal=[create_worktree@59,mark_worktree_protected@137] | OK
MARKER_FILENAME | sections=§3.1+§3.2; status=existing; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:21; consumers=[-]; internal=[_exclude_private_files@287,_oldest_worktrees@225,cleanup_disposable_copy@111,create_worktree@53,77]; marker_reads=[_oldest_worktrees@226,_oldest_worktrees@229,_verify_cleanup_handle@206,_verify_cleanup_handle@209,cleanup_disposable_copy@112]; marker_writes=[create_worktree@67] | OK
PROTECTED_FILENAME | sections=§3.1+§3.2; status=existing; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:22; consumers=[-]; internal=[_exclude_private_files@287,create_worktree@79,is_protected@163,mark_worktree_protected@144,release_worktree_protection@153]; marker_reads=[is_protected@163,release_worktree_protection@154]; marker_writes=[mark_worktree_protected@144,release_worktree_protection@156] | OK
_read_marker | sections=§3.1+§3.2; status=existing; owner=shared; consumers=[-]; internal=[cleanup_disposable_copy,_verify_cleanup_handle,_oldest_worktrees] | definition=ci_triage/verify/workspace.py:248; consumers=[-]; internal=[_oldest_worktrees@229,_verify_cleanup_handle@209,cleanup_disposable_copy@112] | OK
write_workdir_marker | sections=§3.2+S-1; status=to-be-created; owner=shared; consumers=[-]; internal=[create_worktree] | definition=TO_BE_CREATED; consumers=[-]; internal=[-] | OK
fetch_gbs_report | sections=§4; status=existing; owner=shared; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:56; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
download_gbs_package_buildlog | sections=§4; status=existing; owner=shared; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:103; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
DEFAULT_ARCHES | sections=§4; status=existing; owner=orchestrator; consumers=[ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:20; consumers=[ci_triage.orchestrator]; internal=[-] | OK
HttpFetcher | sections=§4; status=existing; owner=shared; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:35; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@111,download_package_buildlog@174] | OK
QuickBuildError | sections=§4; status=existing; owner=shared; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:56; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@198,_urllib_fetch@225,download_full_log@123,download_package_buildlog@183,load_cookie_jar@70,75,81,98] | OK
_raise_if_login_page | sections=§4; status=existing; owner=shared; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:190; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@119,131] | OK
_urllib_fetch | sections=§4; status=existing; owner=shared; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:205; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@116,download_package_buildlog@181] | OK
DEFAULT_COOKIE_PATH | sections=§4; status=existing; owner=shared; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:16; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@201,download_full_log@109,load_cookie_jar@64] | OK
DEFAULT_QUICKBUILD_BASE_URL | sections=§4; status=existing; owner=shared; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:15; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@110] | OK
load_cookie_jar | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[-] | definition=ci_triage/quickbuild.py:64; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@115] | OK
DOWNLOAD_LINK_MARKER | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[find_download_href] | definition=ci_triage/quickbuild.py:17; consumers=[-]; internal=[find_download_href@145] | OK
DOWNLOAD_TIZEN_BASE_URL | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[derive_package_buildlog_url] | definition=ci_triage/quickbuild.py:18; consumers=[-]; internal=[derive_package_buildlog_url@166] | OK
HttpResponse | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/quickbuild.py:22; consumers=[-]; internal=[_raise_if_login_page@190,_urllib_fetch@205,211,218] | OK
QuickBuildDownload | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/quickbuild.py:39; consumers=[-]; internal=[download_full_log@112,132] | OK
PackageBuildLog | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/quickbuild.py:49; consumers=[-]; internal=[download_package_buildlog@175,187] | OK
download_full_log | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | definition=ci_triage/quickbuild.py:106; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | OK
find_download_href | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[download_full_log] | definition=ci_triage/quickbuild.py:140; consumers=[-]; internal=[download_full_log@121] | OK
derive_package_buildlog_url | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[download_package_buildlog] | definition=ci_triage/quickbuild.py:150; consumers=[-]; internal=[download_package_buildlog@178] | OK
download_package_buildlog | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[ci_triage.runner]; internal=[-] | definition=ci_triage/quickbuild.py:171; consumers=[ci_triage.runner]; internal=[-] | OK
normalize_quickbuild_url | sections=§4+v1.2-A; status=existing; owner=shared; consumers=[-]; internal=[_urllib_fetch] | definition=ci_triage/quickbuild.py:228; consumers=[-]; internal=[_urllib_fetch@206] | OK
find_iframe_src | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[fetch_gbs_report] | definition=ci_triage/gbs_report.py:125; consumers=[-]; internal=[fetch_gbs_report@72] | OK
parse_gbs_report_packages | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[fetch_gbs_report] | definition=ci_triage/gbs_report.py:133; consumers=[-]; internal=[fetch_gbs_report@88] | OK
_Anchor | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:156; consumers=[-]; internal=[_Cell@165,_CellBuilder@181,_ReportTableParser.handle_endtag@245,_status_from_anchor@336] | OK
_Cell | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:163; consumers=[-]; internal=[_ReportTableParser.__init__@211,_ReportTableParser.handle_endtag@259,_Row@170] | OK
_Row | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:169; consumers=[-]; internal=[_ReportTableParser.__init__@210,_ReportTableParser.handle_endtag@268,_Table@175,_row_to_package@307] | OK
_Table | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:174; consumers=[-]; internal=[_ReportTableParser.__init__@214,_ReportTableParser.handle_endtag@275,_looks_like_build_status_table@287] | OK
_CellBuilder | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:179; consumers=[-]; internal=[_ReportTableParser.__init__@212,_ReportTableParser.handle_starttag@232] | OK
_AnchorBuilder | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:185; consumers=[-]; internal=[_ReportTableParser.__init__@213,_ReportTableParser.handle_starttag@235] | OK
_IframeParser | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[find_iframe_src] | definition=ci_triage/gbs_report.py:191; consumers=[-]; internal=[find_iframe_src@128] | OK
_ReportTableParser | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:205; consumers=[-]; internal=[parse_gbs_report_packages@142] | OK
_looks_like_build_status_table | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:287; consumers=[-]; internal=[parse_gbs_report_packages@146] | OK
_row_to_package | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:306; consumers=[-]; internal=[parse_gbs_report_packages@149] | OK
_status_from_anchor | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[_row_to_package] | definition=ci_triage/gbs_report.py:336; consumers=[-]; internal=[_row_to_package@322] | OK
_attrs_to_map | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[_IframeParser.handle_starttag,_ReportTableParser.handle_starttag] | definition=ci_triage/gbs_report.py:349; consumers=[-]; internal=[_IframeParser.handle_starttag@199,_ReportTableParser.handle_starttag@217] | OK
_class_names | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[_ReportTableParser.handle_starttag] | definition=ci_triage/gbs_report.py:353; consumers=[-]; internal=[_ReportTableParser.handle_starttag@236] | OK
_normalize_text | sections=§4; status=existing; owner=triage-report; consumers=[-]; internal=[_ReportTableParser.handle_endtag] | definition=ci_triage/gbs_report.py:357; consumers=[-]; internal=[_ReportTableParser.handle_endtag@248,260] | OK
SUMMARY | 59 OK | 0 MISMATCH | 0 INCOMPLETE
```

## Round 1 History

Commit `d06ad9a` recorded the first mechanical pass as
`32 OK / 16 MISMATCH / 0 INCOMPLETE` and correctly stopped the freeze. The
v1.2 design rulings classify those differences into A-E, add
`load_cookie_jar`, and replace the fixed 48-symbol assumption with dynamic
public-surface completeness.

## Freeze-Gate Decision

Sections 2, 3.2, and 4 are mechanically consistent with the round-2 inventory:
**59/59 OK, 0 MISMATCH, 0 INCOMPLETE**. They may proceed to three-party review.
