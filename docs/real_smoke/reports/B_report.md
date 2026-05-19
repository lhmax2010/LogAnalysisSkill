# Real Smoke Test: Error Type B

## Date / Branch
- Date: 2026-05-19 17:17:31 CST
- Branch: real_smoke/B_20260519_171554
- Commit (injection): a8fb2c17

## Injection Summary
Injected a missing build dependency into `packaging/ffmpeg.spec`.

- Added `BuildRequires: pkgconfig(nonexistent-pkg-xxxyzz)` to the package metadata block.
- The injected line is `packaging/ffmpeg.spec:16`.
- gbs failed during package dependency resolving before rpmbuild started.
- The change was committed only on the real-smoke branch.

## Build Result
- gbs exit status: 1
- Build failed as expected: yes
- Real buildlog size: 2412 bytes
- Real buildlog location: reports/gbs_buildlog_B.log

## Analyzer Result (Top-1)

From `reports/analyzer_output_B/evidence_packet.json`:

| Field | Actual | Expected | Match |
|-------|--------|----------|-------|
| verdict | direct_answer | direct_answer | yes |
| via | fast_path | fast_path | yes |
| matched_tier | tier1 | tier1 | yes |
| primary_error.kind | depsolve | depsolve | yes |
| primary_error.file | null | N/A for depsolve fast path | N/A |
| primary_error.line | null (buildlog line_no=31) | N/A for depsolve fast path | N/A |
| primary_error.message | `nothing provides pkgconfig(nonexistent-pkg-xxxyzz)` | contains missing dependency | yes |
| packet_tokens | 237 | <= 1800 | yes |
| failed_phase | null | N/A; failure happened before rpmbuild phase | N/A |
| degraded | false | false (ideal) | yes |

## Conclusion
- Top-1 correct: yes.
- All B-specific gates passed: yes.
- The analyzer correctly used the fast path and returned a tier1 direct answer for the missing dependency.
- Source file/line attribution is not expected here because gbs reports the depsolve failure as repository dependency output, not as a spec source span.

## Files Produced
- reports/raw_buildlog_B.log
- reports/gbs_buildlog_B.log
- reports/analyzer_output_B/evidence_packet.json
- reports/analyzer_output_B/evidence_packet.md
- reports/analyzer_output_B/perf_report.json
- reports/analyzer_output_B/trace.jsonl

## Notes
- gbs did not generate a new rpmbuild fail log for this case because dependency resolution failed before rpmbuild started.
- To avoid reusing the previous A-case fail log, `reports/gbs_buildlog_B.log` is a copy of the complete `tee` output in `reports/raw_buildlog_B.log`.
- `reports/` is ignored via local `.git/info/exclude` so buildlog artifacts are not staged or committed.
- Analyzer performance was fast: `total_ms=6.9382`, `fast_path_hit=true`, `packet_tokens=237`.
