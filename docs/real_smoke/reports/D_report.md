# Real Smoke Test: Error Type D

## Date / Branch
- Date: 2026-05-19 17:35:29 CST
- Branch: real_smoke/D_20260519_173333
- Commit (injection): e58db6b1

## Injection Summary
Injected a `%install` script failure into `packaging/ffmpeg.spec`.

- Added `cp /nonexistent/source/file-xxxyzz /tmp/dest-zzz` after `%make_install`.
- The injected command is at `packaging/ffmpeg.spec:260`.
- gbs completed `%build`, entered `%install`, then failed on the injected `cp` command.
- The change was committed only on the real-smoke branch.

## Build Result
- gbs exit status: 1
- Build failed as expected: yes
- Real buildlog size: 72702 bytes
- Real buildlog location: reports/gbs_buildlog_D.log

## Analyzer Result (Top-1)

From `reports/analyzer_output_D/evidence_packet.json`:

| Field | Actual | Expected | Match |
|-------|--------|----------|-------|
| verdict | direct_answer | needs_llm or direct_answer | yes |
| via | full_path | full_path | yes |
| matched_tier | tier2 | tier2 acceptable | yes |
| primary_error.kind | rpm_phase | spec_script or rpm_phase | yes |
| primary_error.file | null | packaging/ffmpeg.spec | no |
| primary_error.line | null (buildlog line_no=1430) | 260 | no |
| primary_error.message | `error: Bad exit status from /var/tmp/rpm-tmp.eSH7Gc (%install)` | %install script failure | yes |
| packet_tokens | 795 | <= 1800 | yes |
| failed_phase | %install | %install | yes |
| degraded | false | false (ideal) | yes |

## Conclusion
- Top-1 correct: yes for the D-specific expectation.
- All D-specific gates passed: yes, except direct source file/line attribution is not present on `primary_error`.
- The analyzer correctly identified the failure as an `%install` rpm phase issue and returned a tier2 direct answer through the full path.
- Evidence includes the injected command in `spec_section_text`: `cp /nonexistent/source/file-xxxyzz /tmp/dest-zzz`.

## Files Produced
- reports/raw_buildlog_D.log
- reports/gbs_buildlog_D.log
- reports/analyzer_output_D/evidence_packet.json
- reports/analyzer_output_D/evidence_packet.md
- reports/analyzer_output_D/perf_report.json
- reports/analyzer_output_D/trace.jsonl

## Notes
- The buildlog contains the concrete command failure: `cp: cannot stat '/nonexistent/source/file-xxxyzz': No such file or directory`.
- The primary error selected by analyzer is the terminal `Bad exit status` line, while the spec evidence carries the injected failing command.
- The final buildlog copied for analysis is the current gbs fail log at `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt`.
- `reports/` is ignored via local `.git/info/exclude` so buildlog artifacts are not staged or committed.
- Analyzer performance was fine: `total_ms=21.6409`, `packet_tokens=795`, `degraded=false`.
