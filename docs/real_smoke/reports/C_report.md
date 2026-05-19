# Real Smoke Test: Error Type C

## Date / Branch
- Date: 2026-05-19 17:24:03 CST
- Branch: real_smoke/C_20260519_171941
- Commit (injection): 6584054e

## Injection Summary
Injected a patch application failure into the `%prep` section.

- Added `bad-patch-test.patch`, which targets `nonexistent-file-zzz.c`.
- Added `/bin/patch --no-backup-if-mismatch -p1 < bad-patch-test.patch` after `%setup -q` in `packaging/ffmpeg.spec`.
- The injected spec command is at `packaging/ffmpeg.spec:137`.
- The bad patch content is in `bad-patch-test.patch:1-5`.
- The change was committed only on the real-smoke branch.

## Build Result
- gbs exit status: 1
- Build failed as expected: yes
- Real buildlog size: 9363 bytes
- Real buildlog location: reports/gbs_buildlog_C.log

## Analyzer Result (Top-1)

From `reports/analyzer_output_C/evidence_packet.json`:

| Field | Actual | Expected | Match |
|-------|--------|----------|-------|
| verdict | direct_answer | direct_answer | yes |
| via | full_path | fast_path | no |
| matched_tier | tier2 | tier1 | no |
| primary_error.kind | rpm_phase | patch | no |
| primary_error.file | null | bad-patch-test.patch or packaging/ffmpeg.spec | no |
| primary_error.line | null (buildlog line_no=182) | packaging/ffmpeg.spec:137 | no |
| primary_error.message | `error: Bad exit status from /var/tmp/rpm-tmp.Ebqobj (%prep)` | patch failure / hunk ignored | no |
| packet_tokens | 2106 | <= 1800 | no |
| failed_phase | %prep | %prep | yes |
| degraded | true (`packet_truncated_to_token_budget`) | false (ideal) | warning |

## Conclusion
- Top-1 correct: no for the C-specific expectation.
- All gates passed: no.
- The build failure itself is a real patch failure: the log contains `can't find file to patch`, `Skipping patch`, and `1 out of 1 hunk ignored`.
- The analyzer returned a direct answer, but it classified the top event as a generic `%prep` `rpm_phase` failure via the full path, not as a `patch` fast-path tier1 match.
- The packet token cap also failed: `packet_tokens=2106`, above the requested `--max-tokens 1800`, even though `packet_truncated_to_token_budget` was recorded.

## Files Produced
- reports/raw_buildlog_C.log
- reports/gbs_buildlog_C.log
- reports/analyzer_output_C/evidence_packet.json
- reports/analyzer_output_C/evidence_packet.md
- reports/analyzer_output_C/perf_report.json
- reports/analyzer_output_C/trace.jsonl

## Notes
- A first attempt used `Patch9999` plus `%patch9999 -p1`, but GBS rewrote the `%patch` area when generating auto patches, so that did not trigger the intended failure. The final injection uses an explicit `patch -p1 < bad-patch-test.patch` command in `%prep`.
- The final buildlog copied for analysis is the current gbs fail log at `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt`.
- `reports/` is ignored via local `.git/info/exclude` so buildlog artifacts are not staged or committed.
- Analyzer evidence collected the `%prep` spec section and included the injected patch command, but the scanner/ranker did not promote the patch failure lines over the terminal `Bad exit status` rpm phase event.
