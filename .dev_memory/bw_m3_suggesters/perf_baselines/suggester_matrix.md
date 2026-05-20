# BW-M3 Suggester Matrix

Date: 2026-05-20

BW-M3 does not run real gbs builds; BW-M4 owns E2E fixture validation. This
matrix records the unit-level Suggester routing covered before PR.

| Packet kind | Expected Suggester | Confidence | Patch |
| --- | --- | --- | --- |
| `depsolve` missing BuildRequires | `depsolve` | medium | yes |
| `depsolve` already declared | `depsolve` | advisory | no |
| `linker_missing` | `linker_missing` | low | yes, candidate |
| `linker_undef` | `linker_undef` | advisory | no |
| `patch` | `patch_failed` | advisory | no |
| `spec_script` | `spec_script` | advisory | no |
| `rpm_phase` | `spec_script` | advisory | no |
| `compiler` | `compile_error` | advisory | no |
| unknown / `raw_error` | `fallback` | advisory | no |

## Checks

- Focused Suggester tests: 26 passed.
- Focused workflow + Suggester tests: 34 passed, `gbs_workflow` coverage 95%.
- Full regression: 387 passed, analyzer coverage 96.01%.
