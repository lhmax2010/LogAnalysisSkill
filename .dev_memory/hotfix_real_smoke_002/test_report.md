# Hotfix Real Smoke 002 - PR1 Test Report

Date: 2026-05-19
Branch: `hotfix/real-smoke-002-pr1`

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | 26 source files checked. |
| `.venv/bin/pytest tests/unit/test_full_match.py tests/unit/test_packet_assembler.py -q` | pass | Focused PR1 tests passed. |
| `.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q` | pass | 21 passed; M8 20-fixture suite has 0 regression. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96` | pass | 333 passed; total coverage 96.03%. |

## PR1 Real-Smoke Validation

Full analyzer outputs were generated locally under
`.dev_memory/hotfix_real_smoke_002/perf_baselines/pr1_{A,B,D}/`.
The raw JSON/trace files are ignored by repository rules, so the committed baseline is summarized
below and in `perf_baselines/pr1_validation_summary.md`.

### A: linker undefined reference

Validation command used ffmpeg branch `real_smoke/A_20260519_144141` for `--src-root`, then restored
the ffmpeg tree to `tizen`.

| Field | Actual | PR1 Expected | Match |
| --- | --- | --- | --- |
| verdict | `needs_llm` | `needs_llm` | yes |
| via | `full_path` | `full_path` | yes |
| matched_tier | `null` | `null` | yes |
| primary_error.kind | `linker_undef` | `linker_undef` | yes |
| degraded | `false` | `false` | yes |
| degraded_reasons | `[]` | `[]` | yes |
| packet_tokens | `1786` | `<= 1800` | yes |
| matched_patterns | `linker_undefined_reference_tier2` | present | yes |
| near-match confidence | `0.84` | around `0.84` | yes |
| near-match failure_reason | `confidence_below_tier2_threshold` | present | yes |

### B: depsolve no-regression gate

| Field | Actual | Expected | Match |
| --- | --- | --- | --- |
| verdict | `direct_answer` | `direct_answer` | yes |
| via | `fast_path` | `fast_path` | yes |
| matched_tier | `tier1` | `tier1` | yes |
| primary_error.kind | `depsolve` | `depsolve` | yes |
| degraded | `false` | `false` | yes |
| packet_tokens | `332` | `<= 1800` | yes |

### D: `%install` no-regression gate

| Field | Actual | Expected | Match |
| --- | --- | --- | --- |
| verdict | `direct_answer` | `direct_answer` | yes |
| via | `full_path` | `full_path` | yes |
| matched_tier | `tier2` | `tier2` | yes |
| primary_error.kind | `rpm_phase` | `rpm_phase` | yes |
| failed_phase | `%install` | `%install` | yes |
| degraded | `false` | `false` | yes |
| packet_tokens | `1134` | `<= 1800` | yes |

## Conclusion

PR1 gates passed. A remains `needs_llm` as expected because Fix 5 is not implemented in PR1.
B and D did not regress.

---

# Hotfix Real Smoke 002 - PR2 Test Report

Date: 2026-05-19
Branch: `hotfix/real-smoke-002-pr2`

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/unit/test_scan_and_extract.py tests/unit/test_quick_filter.py tests/unit/test_rank_causes.py -q` | pass | 89 patch/scanner/ranker focused tests passed. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | 26 source files checked. |
| `.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q` | pass | 21 passed; M8 20-fixture suite has 0 regression. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96` | pass | 338 passed; total coverage 96.07%. |

## PR2 Real-Smoke Validation

Full analyzer outputs were generated locally under
`.dev_memory/hotfix_real_smoke_002/perf_baselines/pr2_{C,B,D}/`.
The raw JSON/trace files are ignored by repository rules, so the committed baseline is summarized
below and in `perf_baselines/pr2_validation_summary.md`.

### C: patch failed

| Field | Actual | PR2 Expected | Match |
| --- | --- | --- | --- |
| verdict | `direct_answer` | `direct_answer` | yes |
| via | `fast_path` | `fast_path` | yes |
| matched_tier | `tier1` | `tier1` | yes |
| primary_error.kind | `patch` | `patch` | yes |
| primary_error.message | `error: patch failed: can't find file to patch at input line 3` | patch failure | yes |
| failed_phase | `%prep` | `%prep` | yes |
| degraded | `false` | `false` | yes |
| packet_tokens | `338` | `<= 1800` | yes |
| matched_patterns | `patch_failed_rpm` | tier1 patch pattern | yes |

Scanner cascade check:

- `E001 patch`: `can't find file to patch`
- `E002 patch`: `Hunk #1 FAILED: 1 out of 1 hunk ignored`
- `E003 rpm_phase`: parent `E002`, details include `derived_from=patch_failed`

### B: depsolve no-regression gate

| Field | Actual | Expected | Match |
| --- | --- | --- | --- |
| verdict | `direct_answer` | `direct_answer` | yes |
| via | `fast_path` | `fast_path` | yes |
| matched_tier | `tier1` | `tier1` | yes |
| primary_error.kind | `depsolve` | `depsolve` | yes |
| degraded | `false` | `false` | yes |
| packet_tokens | `332` | `<= 1800` | yes |

### D: `%install` no-regression gate

| Field | Actual | Expected | Match |
| --- | --- | --- | --- |
| verdict | `direct_answer` | `direct_answer` | yes |
| via | `full_path` | `full_path` | yes |
| matched_tier | `tier2` | `tier2` | yes |
| primary_error.kind | `rpm_phase` | `rpm_phase` | yes |
| failed_phase | `%install` | `%install` | yes |
| degraded | `false` | `false` | yes |
| packet_tokens | `1134` | `<= 1800` | yes |

## PR2 Conclusion

PR2 gates passed. C is fixed as patch fast-path tier1; B and D did not regress.
PR3 remains responsible for A linker undefined-reference confidence.
