# Real Smoke Test: Error Type A

## Date / Branch
- Date: 2026-05-19 14:46:40 CST
- Branch: real_smoke/A_20260519_144141
- Commit (injection): b4ad0be9

## Injection Summary
Injected a linker undefined reference into `libavcodec/utils.c`.

- Added `extern int nonexistent_helper_xxxyzz(int a, int b);` near the top of the file.
- Added a call to `nonexistent_helper_xxxyzz(frame_bytes, channels)` inside `av_get_audio_frame_duration()`.
- The injected call is at `libavcodec/utils.c:796`; the declaration is at `libavcodec/utils.c:53`.
- The change was committed only on the real-smoke branch.

## Build Result
- gbs exit status: 1
- Build failed as expected: yes
- Real buildlog size: 61994 bytes
- Real buildlog location: reports/gbs_buildlog_A.log

## Analyzer Result (Top-1)

| Field | Actual | Expected | Match |
|-------|--------|----------|-------|
| verdict | needs_llm | direct_answer | no |
| via | full_path | full_path | yes |
| matched_tier | null | tier2 | no |
| primary_error.kind | linker_undef | linker_undef | yes |
| primary_error.file | null | libavcodec/utils.c | no |
| primary_error.line | null (buildlog line_no=1173) | 796 | no |
| primary_error.message | `/usr/bin/ld ... libavcodec.so: undefined reference to nonexistent_helper_xxxyzz` | contains "undefined reference to" | yes |
| packet_tokens | 1453 | <= 1800 | yes |
| failed_phase | %build | %build | yes |
| degraded | true (`budget_pool_partial`, `packet_truncated_to_token_budget`) | false (ideal) | warning |

## Conclusion
- Top-1 correct: yes for the linker undefined-reference root event and injected symbol.
- All gates passed: no.
- The analyzer correctly ranked the injected undefined symbol as Top-1 (`primary_error.kind=linker_undef`, symbol `nonexistent_helper_xxxyzz`, `%build` phase), but it did not produce the expected tier2 direct answer. `matched_tier` stayed null and `verdict` stayed `needs_llm`.
- The packet remained within the requested 1800-token cap.
- Source attribution is partial: evidence `symbol_context.path` points to `/home/linhao/Toolchain/development/ffmpeg/libavcodec/utils.c`, but `primary_error` itself does not contain `file` or source line `796`.

## Files Produced
- reports/raw_buildlog_A.log
- reports/gbs_buildlog_A.log
- reports/analyzer_output_A/evidence_packet.json
- reports/analyzer_output_A/evidence_packet.md
- reports/analyzer_output_A/perf_report.json
- reports/analyzer_output_A/trace.jsonl

## Notes
- The structured buildlog copied for analysis is the gbs failure log at `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt`. The scratch `.build.log` path was not present after this build.
- `reports/` is ignored via local `.git/info/exclude` so buildlog artifacts are not staged or committed.
- A first build attempt before ignoring `reports/` was discarded because gbs would have included the untracked `reports/` directory in the source package. The final reported build was rerun after `reports/` was ignored.
- Analyzer evidence shows `symbol_context.path` as `/home/linhao/Toolchain/development/ffmpeg/libavcodec/utils.c`, extracted with `line_window`, but no tier2 pattern matched.
