# P4.9 step-0 symbol attribution audit

## Result

**STOP - design-side ruling required before freeze.**

The mechanical audit checked 48 symbols transcribed from the final v1.1
corrections to design sections 2, 3.2, and 4:

- 32 OK
- 16 MISMATCH
- 0 INCOMPLETE

The `gbs_report.py` public-surface completeness guard found no omitted
top-level function, class, or constant. Because mismatches remain, this report
does not claim that the three attribution tables can be frozen. Per the
stop-and-report protocol, neither the design tables nor production source were
changed.

## Inputs And Method

- Design input: `docs/clang-fix-campaign/p49-step0-design-v1.0-draft.md`
- Authoritative correction: the final v1.1 correction section
- Design SHA-256: `031c0ab30c52e304dacf44505983d691d800efb4021808c91da230c553e4c635`
- Audited source root: `tizen-ci-triage/scripts/`
- Excluded: tests, `__pycache__`, and `release-v1.4.0/` snapshots
- Analysis mode: Python source text plus AST only; audited modules are never
  imported or executed
- Marker audit: function-body reads and writes of `MARKER_FILENAME` and
  `PROTECTED_FILENAME` are listed separately
- Completeness guard: every top-level function/class/constant in
  `ci_triage/gbs_report.py` must appear in the hard-coded inventory

Command (the nonzero exit is expected when a mismatch exists):

```bash
.venv/bin/python docs/clang-fix-campaign/tools/symbol_audit.py
```

## Raw Output

The following is the complete stdout from the command above.

```text
symbol | declared | measured_consumers | verdict
SourceFetchResult | sections=§2; owner=shared/types; consumers=[ci_triage.report]; internal=[-] | definition=ci_triage/gerrit.py:43; consumers=[ci_triage.report]; internal=[fetch_source_for_commit@157,231,239,247] | OK
FailedPackage | sections=§2; owner=shared/types; consumers=[ci_triage.report]; internal=[-] | definition=ci_triage/quickbuild_log.py:11; consumers=[ci_triage.orchestrator,ci_triage.report,ci_triage.runner]; internal=[parse_failed_packages@56,59,74,select_failed_package@89,92] | MISMATCH: undeclared consumer ci_triage.orchestrator; undeclared consumer ci_triage.runner
DisposableWorktree | sections=§2+§3.2; owner=shared; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:31; consumers=[-]; internal=[_oldest_worktrees@220,221,236,_verify_cleanup_handle@204,cleanup_disposable_copy@114,cleanup_worktree@92,create_worktree@47,82,mark_worktree_protected@128] | MISMATCH: declared consumer ci_triage.verify.build_verify not found
WorkspaceViolation | sections=§2+§3.2; owner=shared; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/workspace.py:26; consumers=[ci_triage.campaign_repair_step]; internal=[_read_marker@251,_verify_cleanup_handle@207,215,217,check_disk_and_maybe_cleanup@187,cleanup_disposable_copy@110,123,create_worktree@57] | OK
FailureClassification | sections=§2; owner=shared; consumers=[ci_triage.verify.build_verify,ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/failure_classify.py:43; consumers=[ci_triage.verify.build_verify]; internal=[_heuristic_classification@213,219,230,_match_denylist@193,203,_source_diagnostic_classification@239,241,250,259,268,279,classify_failure@133,146,159,173] | MISMATCH: declared consumer ci_triage.campaign_repair_step not found
GbsReportPackage | sections=§2+§4; owner=shared/types; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:30; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[GbsReport@49,GbsReport.failed_packages@52,_row_to_package@312,326,download_gbs_package_buildlog@104,parse_gbs_report_packages@139,144] | OK
GbsReport | sections=§2+§4; owner=UNRESOLVED(parse-or-shared/types); consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:42; consumers=[-]; internal=[fetch_gbs_report@63,94] | MISMATCH: declared owner is unresolved: UNRESOLVED(parse-or-shared/types)
create_worktree | sections=§3.2; owner=build-verify; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:42; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
check_disk_and_maybe_cleanup | sections=§3.2; owner=build-verify; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:166; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_copy_repository | sections=§3.2; owner=build-verify; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:267; consumers=[-]; internal=[create_worktree@58] | OK
cleanup_worktree | sections=§3.2; owner=shared; consumers=[ci_triage.verify.build_verify]; internal=[cleanup_disposable_copy,check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:92; consumers=[ci_triage.verify.build_verify]; internal=[check_disk_and_maybe_cleanup@186,cleanup_disposable_copy@124] | OK
cleanup_disposable_copy | sections=§3.2; owner=shared; consumers=[ci_triage.campaign_repair_step]; internal=[-] | definition=ci_triage/verify/workspace.py:99; consumers=[ci_triage.campaign_repair_step]; internal=[-] | OK
is_protected | sections=§3.2; owner=shared; consumers=[ci_triage.campaign_repair_step]; internal=[cleanup_disposable_copy,check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:160; consumers=[ci_triage.campaign_repair_step]; internal=[check_disk_and_maybe_cleanup@182,cleanup_disposable_copy@109] | OK
release_worktree_protection | sections=§3.2; owner=shared; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | definition=ci_triage/verify/workspace.py:150; consumers=[ci_triage.verify.gerrit_submit]; internal=[-] | OK
mark_worktree_protected | sections=§3.2; owner=shared; consumers=[ci_triage.verify.build_verify]; internal=[-] | definition=ci_triage/verify/workspace.py:127; consumers=[ci_triage.verify.build_verify]; internal=[-] | OK
_oldest_worktrees | sections=§3.2; owner=shared; consumers=[-]; internal=[check_disk_and_maybe_cleanup] | definition=ci_triage/verify/workspace.py:220; consumers=[-]; internal=[check_disk_and_maybe_cleanup@181] | OK
_run_git | sections=§3.2; owner=shared; consumers=[-]; internal=[create_worktree] | definition=ci_triage/verify/workspace.py:263; consumers=[-]; internal=[create_worktree@68,69,70] | OK
_verify_cleanup_handle | sections=§3.2; owner=shared; consumers=[-]; internal=[cleanup_worktree,mark_worktree_protected] | definition=ci_triage/verify/workspace.py:204; consumers=[-]; internal=[cleanup_worktree@95,mark_worktree_protected@135] | OK
_exclude_private_files | sections=§3.2; owner=shared; consumers=[-]; internal=[create_worktree,mark_worktree_protected] | definition=ci_triage/verify/workspace.py:273; consumers=[-]; internal=[create_worktree@59,mark_worktree_protected@137] | OK
MARKER_FILENAME | sections=§3.1+§3.2; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:21; consumers=[-]; internal=[_exclude_private_files@287,_oldest_worktrees@225,cleanup_disposable_copy@111,create_worktree@53,77]; marker_reads=[_oldest_worktrees@226,_oldest_worktrees@229,_verify_cleanup_handle@206,_verify_cleanup_handle@209,cleanup_disposable_copy@112]; marker_writes=[create_worktree@67] | OK
PROTECTED_FILENAME | sections=§3.1+§3.2; owner=shared; consumers=[-]; internal=[-] | definition=ci_triage/verify/workspace.py:22; consumers=[-]; internal=[_exclude_private_files@287,create_worktree@79,is_protected@163,mark_worktree_protected@144,release_worktree_protection@153]; marker_reads=[is_protected@163,release_worktree_protection@154]; marker_writes=[mark_worktree_protected@144,release_worktree_protection@156] | OK
_read_marker | sections=§3.1+§3.2; owner=shared; consumers=[-]; internal=[cleanup_disposable_copy,_verify_cleanup_handle,_oldest_worktrees] | definition=ci_triage/verify/workspace.py:248; consumers=[-]; internal=[_oldest_worktrees@229,_verify_cleanup_handle@209,cleanup_disposable_copy@112] | OK
write_workdir_marker | sections=§3.2+S-1; owner=shared; consumers=[-]; internal=[create_worktree] | definition=NOT_FOUND; consumers=[-]; internal=[-] | MISMATCH: definition write_workdir_marker not found in ci_triage/verify/workspace.py
fetch_gbs_report | sections=§4; owner=quickbuild; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:56; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | MISMATCH: multiple consumers require shared ownership
download_gbs_package_buildlog | sections=§4; owner=quickbuild; consumers=[ci_triage.runner,ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:103; consumers=[ci_triage.orchestrator,ci_triage.runner]; internal=[-] | MISMATCH: multiple consumers require shared ownership
DEFAULT_ARCHES | sections=§4; owner=quickbuild; consumers=[ci_triage.orchestrator]; internal=[-] | definition=ci_triage/gbs_report.py:20; consumers=[ci_triage.orchestrator]; internal=[-] | MISMATCH: single consumer ci_triage.orchestrator belongs to orchestrator, not declared owner quickbuild
HttpFetcher | sections=§4; owner=quickbuild; consumers=[ci_triage.gbs_report]; internal=[-] | definition=ci_triage/quickbuild.py:35; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@111,download_package_buildlog@174] | MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
QuickBuildError | sections=§4; owner=quickbuild; consumers=[ci_triage.gbs_report]; internal=[-] | definition=ci_triage/quickbuild.py:56; consumers=[ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@198,_urllib_fetch@225,download_full_log@123,download_package_buildlog@183,load_cookie_jar@70,75,81,98] | MISMATCH: undeclared consumer ci_triage.orchestrator; undeclared consumer ci_triage.runner; undeclared consumer ci_triage.sources; multiple consumers require shared ownership
_raise_if_login_page | sections=§4; owner=quickbuild; consumers=[ci_triage.gbs_report]; internal=[-] | definition=ci_triage/quickbuild.py:190; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@119,131] | MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
_urllib_fetch | sections=§4; owner=quickbuild; consumers=[ci_triage.gbs_report]; internal=[-] | definition=ci_triage/quickbuild.py:205; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@116,download_package_buildlog@181] | MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
DEFAULT_COOKIE_PATH | sections=§4; owner=quickbuild; consumers=[ci_triage.gbs_report]; internal=[-] | definition=ci_triage/quickbuild.py:16; consumers=[ci_triage.batch_cli,ci_triage.cli,ci_triage.gbs_report,ci_triage.orchestrator,ci_triage.runner,ci_triage.sources]; internal=[_raise_if_login_page@201,download_full_log@109,load_cookie_jar@64] | MISMATCH: undeclared consumer ci_triage.batch_cli; undeclared consumer ci_triage.cli; undeclared consumer ci_triage.orchestrator; undeclared consumer ci_triage.runner; undeclared consumer ci_triage.sources; multiple consumers require shared ownership
DEFAULT_QUICKBUILD_BASE_URL | sections=§4; owner=quickbuild; consumers=[ci_triage.gbs_report]; internal=[-] | definition=ci_triage/quickbuild.py:15; consumers=[ci_triage.gbs_report,ci_triage.sources]; internal=[download_full_log@110] | MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
find_iframe_src | sections=§4; owner=triage-report; consumers=[-]; internal=[fetch_gbs_report] | definition=ci_triage/gbs_report.py:125; consumers=[-]; internal=[fetch_gbs_report@72] | MISMATCH: cross-boundary internal access from fetch_gbs_report owned by quickbuild
parse_gbs_report_packages | sections=§4; owner=triage-report; consumers=[-]; internal=[fetch_gbs_report] | definition=ci_triage/gbs_report.py:133; consumers=[-]; internal=[fetch_gbs_report@88] | MISMATCH: cross-boundary internal access from fetch_gbs_report owned by quickbuild
_Anchor | sections=§4; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:156; consumers=[-]; internal=[_Cell@165,_CellBuilder@181,_ReportTableParser.handle_endtag@245,_status_from_anchor@336] | OK
_Cell | sections=§4; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:163; consumers=[-]; internal=[_ReportTableParser.__init__@211,_ReportTableParser.handle_endtag@259,_Row@170] | OK
_Row | sections=§4; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:169; consumers=[-]; internal=[_ReportTableParser.__init__@210,_ReportTableParser.handle_endtag@268,_Table@175,_row_to_package@307] | OK
_Table | sections=§4; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:174; consumers=[-]; internal=[_ReportTableParser.__init__@214,_ReportTableParser.handle_endtag@275,_looks_like_build_status_table@287] | OK
_CellBuilder | sections=§4; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:179; consumers=[-]; internal=[_ReportTableParser.__init__@212,_ReportTableParser.handle_starttag@232] | OK
_AnchorBuilder | sections=§4; owner=triage-report; consumers=[-]; internal=[-] | definition=ci_triage/gbs_report.py:185; consumers=[-]; internal=[_ReportTableParser.__init__@213,_ReportTableParser.handle_starttag@235] | OK
_IframeParser | sections=§4; owner=triage-report; consumers=[-]; internal=[find_iframe_src] | definition=ci_triage/gbs_report.py:191; consumers=[-]; internal=[find_iframe_src@128] | OK
_ReportTableParser | sections=§4; owner=triage-report; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:205; consumers=[-]; internal=[parse_gbs_report_packages@142] | OK
_looks_like_build_status_table | sections=§4; owner=triage-report; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:287; consumers=[-]; internal=[parse_gbs_report_packages@146] | OK
_row_to_package | sections=§4; owner=triage-report; consumers=[-]; internal=[parse_gbs_report_packages] | definition=ci_triage/gbs_report.py:306; consumers=[-]; internal=[parse_gbs_report_packages@149] | OK
_status_from_anchor | sections=§4; owner=triage-report; consumers=[-]; internal=[_row_to_package] | definition=ci_triage/gbs_report.py:336; consumers=[-]; internal=[_row_to_package@322] | OK
_attrs_to_map | sections=§4; owner=triage-report; consumers=[-]; internal=[_IframeParser.handle_starttag,_ReportTableParser.handle_starttag] | definition=ci_triage/gbs_report.py:349; consumers=[-]; internal=[_IframeParser.handle_starttag@199,_ReportTableParser.handle_starttag@217] | OK
_class_names | sections=§4; owner=triage-report; consumers=[-]; internal=[_ReportTableParser.handle_starttag] | definition=ci_triage/gbs_report.py:353; consumers=[-]; internal=[_ReportTableParser.handle_starttag@236] | OK
_normalize_text | sections=§4; owner=triage-report; consumers=[-]; internal=[_ReportTableParser.handle_endtag] | definition=ci_triage/gbs_report.py:357; consumers=[-]; internal=[_ReportTableParser.handle_endtag@248,260] | OK
SUMMARY | 32 OK | 16 MISMATCH | 0 INCOMPLETE
EVIDENCE
[FailedPackage] MISMATCH: undeclared consumer ci_triage.orchestrator; undeclared consumer ci_triage.runner
  ci_triage/orchestrator.py:22:FailedPackage,
  ci_triage/orchestrator.py:492:selected_package=FailedPackage(
  ci_triage/quickbuild_log.py:11:class FailedPackage:
  ci_triage/quickbuild_log.py:56:def parse_failed_packages(full_log: str) -> tuple[FailedPackage, ...]:
  ci_triage/quickbuild_log.py:59:packages: list[FailedPackage] = []
  ci_triage/quickbuild_log.py:74:FailedPackage(
  ci_triage/quickbuild_log.py:89:failed_packages: tuple[FailedPackage, ...],
  ci_triage/quickbuild_log.py:92:) -> FailedPackage:
  ci_triage/report.py:10:from ci_triage.quickbuild_log import FailedPackage
  ci_triage/report.py:22:selected_package: FailedPackage | None = None
  ci_triage/runner.py:28:FailedPackage,
  ci_triage/runner.py:53:selected_package: FailedPackage | None = None
  ci_triage/runner.py:127:FailedPackage(fail_pkg=options.spec_name, spec_name=options.spec_name),
  ci_triage/runner.py:281:) -> tuple[FailedPackage, GbsReportPackage]:
  ci_triage/runner.py:312:def _failed_package_from_gbs(package: GbsReportPackage) -> FailedPackage:
  ci_triage/runner.py:313:return FailedPackage(
[DisposableWorktree] MISMATCH: declared consumer ci_triage.verify.build_verify not found
  ci_triage/verify/__init__.py:15:DisposableWorktree,
  ci_triage/verify/__init__.py:26:"DisposableWorktree",
  ci_triage/verify/workspace.py:5:file. The public API intentionally keeps the ``DisposableWorktree`` naming from
  ci_triage/verify/workspace.py:31:class DisposableWorktree:
  ci_triage/verify/workspace.py:47:) -> DisposableWorktree:
  ci_triage/verify/workspace.py:82:return DisposableWorktree(
  ci_triage/verify/workspace.py:92:def cleanup_worktree(handle: DisposableWorktree) -> None:
  ci_triage/verify/workspace.py:114:handle = DisposableWorktree(
  ci_triage/verify/workspace.py:128:handle: DisposableWorktree,
  ci_triage/verify/workspace.py:204:def _verify_cleanup_handle(handle: DisposableWorktree) -> None:
  ci_triage/verify/workspace.py:220:def _oldest_worktrees(root: Path) -> list[DisposableWorktree]:
  ci_triage/verify/workspace.py:221:handles: list[DisposableWorktree] = []
  ci_triage/verify/workspace.py:236:DisposableWorktree(
[FailureClassification] MISMATCH: declared consumer ci_triage.campaign_repair_step not found
  ci_triage/verify/__init__.py:10:FailureClassification,
  ci_triage/verify/__init__.py:28:"FailureClassification",
  ci_triage/verify/build_verify.py:38:FailureClassification,
  ci_triage/verify/build_verify.py:427:classification: FailureClassification,
  ci_triage/verify/failure_classify.py:43:class FailureClassification:
  ci_triage/verify/failure_classify.py:133:) -> FailureClassification:
  ci_triage/verify/failure_classify.py:146:return FailureClassification(
  ci_triage/verify/failure_classify.py:159:return FailureClassification(
  ci_triage/verify/failure_classify.py:173:return FailureClassification(
  ci_triage/verify/failure_classify.py:193:) -> FailureClassification | None:
  ci_triage/verify/failure_classify.py:203:return FailureClassification(
  ci_triage/verify/failure_classify.py:213:def _heuristic_classification(primary: Mapping[str, Any]) -> FailureClassification:
  ci_triage/verify/failure_classify.py:219:return FailureClassification(
  ci_triage/verify/failure_classify.py:230:return FailureClassification(
  ci_triage/verify/failure_classify.py:239:def _source_diagnostic_classification(primary: Mapping[str, Any]) -> FailureClassification:
  ci_triage/verify/failure_classify.py:241:return FailureClassification(
  ci_triage/verify/failure_classify.py:250:return FailureClassification(
  ci_triage/verify/failure_classify.py:259:return FailureClassification(
  ci_triage/verify/failure_classify.py:268:return FailureClassification(
  ci_triage/verify/failure_classify.py:279:return FailureClassification(
[GbsReport] MISMATCH: declared owner is unresolved: UNRESOLVED(parse-or-shared/types)
  ci_triage/gbs_report.py:42:class GbsReport:
  ci_triage/gbs_report.py:63:) -> GbsReport:
  ci_triage/gbs_report.py:94:return GbsReport(
[write_workdir_marker] MISMATCH: definition write_workdir_marker not found in ci_triage/verify/workspace.py
  (no source matches)
[fetch_gbs_report] MISMATCH: multiple consumers require shared ownership
  ci_triage/gbs_report.py:56:def fetch_gbs_report(
  ci_triage/orchestrator.py:18:fetch_gbs_report,
  ci_triage/orchestrator.py:519:return fetch_gbs_report(build_id, arch, cookie_path=cookie_path).failed_packages
  ci_triage/runner.py:18:fetch_gbs_report,
  ci_triage/runner.py:282:report = fetch_gbs_report(build_id, arch, cookie_path=cookie_path)
[download_gbs_package_buildlog] MISMATCH: multiple consumers require shared ownership
  ci_triage/gbs_report.py:103:def download_gbs_package_buildlog(
  ci_triage/orchestrator.py:17:download_gbs_package_buildlog,
  ci_triage/orchestrator.py:523:return download_gbs_package_buildlog(package, cookie_path=cookie_path)
  ci_triage/runner.py:17:download_gbs_package_buildlog,
  ci_triage/runner.py:104:package_buildlog_text = download_gbs_package_buildlog(
[DEFAULT_ARCHES] MISMATCH: single consumer ci_triage.orchestrator belongs to orchestrator, not declared owner quickbuild
  ci_triage/gbs_report.py:20:DEFAULT_ARCHES = (
  ci_triage/orchestrator.py:15:DEFAULT_ARCHES,
  ci_triage/orchestrator.py:70:arches: tuple[str, ...] = DEFAULT_ARCHES
[HttpFetcher] MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
  ci_triage/gbs_report.py:13:HttpFetcher,
  ci_triage/gbs_report.py:62:fetcher: HttpFetcher | None = None,
  ci_triage/gbs_report.py:107:fetcher: HttpFetcher | None = None,
  ci_triage/quickbuild.py:35:HttpFetcher = Callable[[str, Mapping[str, str]], HttpResponse]
  ci_triage/quickbuild.py:111:fetcher: HttpFetcher | None = None,
  ci_triage/quickbuild.py:174:fetcher: HttpFetcher | None = None,
  ci_triage/sources.py:15:HttpFetcher,
  ci_triage/sources.py:53:fetcher: HttpFetcher | None = None
[QuickBuildError] MISMATCH: undeclared consumer ci_triage.orchestrator; undeclared consumer ci_triage.runner; undeclared consumer ci_triage.sources; multiple consumers require shared ownership
  ci_triage/gbs_report.py:14:QuickBuildError,
  ci_triage/gbs_report.py:74:raise QuickBuildError(
  ci_triage/gbs_report.py:83:raise QuickBuildError(
  ci_triage/gbs_report.py:112:raise QuickBuildError(
  ci_triage/gbs_report.py:118:raise QuickBuildError(
  ci_triage/orchestrator.py:20:from ci_triage.quickbuild import DEFAULT_COOKIE_PATH, QuickBuildError, download_full_log
  ci_triage/orchestrator.py:272:except QuickBuildError as exc:
  ci_triage/orchestrator.py:345:except QuickBuildError as exc:
  ci_triage/orchestrator.py:470:except QuickBuildError as exc:
  ci_triage/quickbuild.py:56:class QuickBuildError(RuntimeError):
  ci_triage/quickbuild.py:70:raise QuickBuildError(
  ci_triage/quickbuild.py:75:raise QuickBuildError(
  ci_triage/quickbuild.py:81:raise QuickBuildError("COOKIE_UNREADABLE", "QuickBuild cookie JSON must be a list")
  ci_triage/quickbuild.py:98:raise QuickBuildError(
  ci_triage/quickbuild.py:123:raise QuickBuildError(
  ci_triage/quickbuild.py:183:raise QuickBuildError(
  ci_triage/quickbuild.py:198:raise QuickBuildError(
  ci_triage/quickbuild.py:225:raise QuickBuildError("QUICKBUILD_DOWNLOAD_FAILED", str(exc)) from exc
  ci_triage/runner.py:23:QuickBuildError,
  ci_triage/runner.py:111:raise QuickBuildError(
  ci_triage/runner.py:140:except QuickBuildError as exc:
  ci_triage/runner.py:233:except QuickBuildError as exc:
  ci_triage/sources.py:16:QuickBuildError,
  ci_triage/sources.py:61:raise QuickBuildError(
  ci_triage/sources.py:75:raise QuickBuildError(
[_raise_if_login_page] MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
  ci_triage/gbs_report.py:15:_raise_if_login_page,
  ci_triage/gbs_report.py:70:_raise_if_login_page(page, action="open GBS reports page")
  ci_triage/gbs_report.py:81:_raise_if_login_page(iframe, action="download GBS report iframe")
  ci_triage/quickbuild.py:119:_raise_if_login_page(page, action="open build log page")
  ci_triage/quickbuild.py:131:_raise_if_login_page(full_log_response, action="download full log")
  ci_triage/quickbuild.py:190:def _raise_if_login_page(response: HttpResponse, *, action: str) -> None:
  ci_triage/sources.py:17:_raise_if_login_page,
  ci_triage/sources.py:71:_raise_if_login_page(response, action="open QuickBuild overview")
[_urllib_fetch] MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
  ci_triage/gbs_report.py:16:_urllib_fetch,
  ci_triage/gbs_report.py:67:fetch = fetcher or _urllib_fetch
  ci_triage/gbs_report.py:116:response = (fetcher or _urllib_fetch)(package.buildlog_url, load_cookie_jar(cookie_path))
  ci_triage/quickbuild.py:116:fetch = fetcher or _urllib_fetch
  ci_triage/quickbuild.py:181:response = (fetcher or _urllib_fetch)(url, {})
  ci_triage/quickbuild.py:205:def _urllib_fetch(url: str, cookies: Mapping[str, str]) -> HttpResponse:
  ci_triage/sources.py:18:_urllib_fetch,
  ci_triage/sources.py:69:fetch = self.fetcher or _urllib_fetch
[DEFAULT_COOKIE_PATH] MISMATCH: undeclared consumer ci_triage.batch_cli; undeclared consumer ci_triage.cli; undeclared consumer ci_triage.orchestrator; undeclared consumer ci_triage.runner; undeclared consumer ci_triage.sources; multiple consumers require shared ownership
  ci_triage/batch_cli.py:12:from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
  ci_triage/batch_cli.py:49:default=DEFAULT_COOKIE_PATH,
  ci_triage/batch_cli.py:50:help=f"Browser-exported QuickBuild cookie JSON. Defaults to {DEFAULT_COOKIE_PATH}.",
  ci_triage/cli.py:16:from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
  ci_triage/cli.py:66:default=DEFAULT_COOKIE_PATH,
  ci_triage/cli.py:67:help=f"Browser-exported QuickBuild cookie JSON. Defaults to {DEFAULT_COOKIE_PATH}.",
  ci_triage/gbs_report.py:11:DEFAULT_COOKIE_PATH,
  ci_triage/gbs_report.py:60:cookie_path: Path = DEFAULT_COOKIE_PATH,
  ci_triage/gbs_report.py:106:cookie_path: Path = DEFAULT_COOKIE_PATH,
  ci_triage/orchestrator.py:20:from ci_triage.quickbuild import DEFAULT_COOKIE_PATH, QuickBuildError, download_full_log
  ci_triage/orchestrator.py:64:cookie_path: Path = DEFAULT_COOKIE_PATH
  ci_triage/quickbuild.py:16:DEFAULT_COOKIE_PATH = Path("/tmp/quickbuild_cookies.json")
  ci_triage/quickbuild.py:64:def load_cookie_jar(cookie_path: Path = DEFAULT_COOKIE_PATH) -> dict[str, str]:
  ci_triage/quickbuild.py:109:cookie_path: Path = DEFAULT_COOKIE_PATH,
  ci_triage/quickbuild.py:201:f"please log in and export cookies to {DEFAULT_COOKIE_PATH}.",
  ci_triage/runner.py:22:DEFAULT_COOKIE_PATH,
  ci_triage/runner.py:47:cookie_path: Path = DEFAULT_COOKIE_PATH
  ci_triage/sources.py:13:DEFAULT_COOKIE_PATH,
  ci_triage/sources.py:50:cookie_path: Path = DEFAULT_COOKIE_PATH
[DEFAULT_QUICKBUILD_BASE_URL] MISMATCH: undeclared consumer ci_triage.sources; multiple consumers require shared ownership
  ci_triage/gbs_report.py:12:DEFAULT_QUICKBUILD_BASE_URL,
  ci_triage/gbs_report.py:61:base_url: str = DEFAULT_QUICKBUILD_BASE_URL,
  ci_triage/quickbuild.py:15:DEFAULT_QUICKBUILD_BASE_URL = "https://quickbuild.tizen.org"
  ci_triage/quickbuild.py:110:base_url: str = DEFAULT_QUICKBUILD_BASE_URL,
  ci_triage/sources.py:14:DEFAULT_QUICKBUILD_BASE_URL,
  ci_triage/sources.py:51:base_url: str = DEFAULT_QUICKBUILD_BASE_URL
[find_iframe_src] MISMATCH: cross-boundary internal access from fetch_gbs_report owned by quickbuild
  ci_triage/gbs_report.py:72:iframe_src = find_iframe_src(page.text)
  ci_triage/gbs_report.py:125:def find_iframe_src(html_text: str) -> str | None:
[parse_gbs_report_packages] MISMATCH: cross-boundary internal access from fetch_gbs_report owned by quickbuild
  ci_triage/gbs_report.py:88:packages = parse_gbs_report_packages(
  ci_triage/gbs_report.py:133:def parse_gbs_report_packages(
```

## Freeze Decision

The three attribution tables are **not freeze-ready** under methodology gate
10. The 16 differences above are design-versus-reality evidence only. Their
disposition belongs to the design owner; the audit criteria and source tree
were not adjusted to force a passing result.

