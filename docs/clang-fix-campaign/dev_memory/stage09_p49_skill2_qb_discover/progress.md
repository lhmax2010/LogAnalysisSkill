# P4.9 Skill-2 QB-Discover Progress

## Frozen authority

- Initial freeze commit: `097294f`.
- Current in-place authority: `p49-skill2-qb-discover-design-v1.3-FROZEN.md`.
- Parallel authorities were revised mechanically to expose the bridge key:
  step-0 `v2.1-FROZEN` and skill-1 `v1.4-FROZEN`.
- Canonical/history `cmp` returned exit 0 for all three authorities.

## Commit A: binary attribution keys

The symbol inventory and table bridge now key symbols by
`(definition, symbol)`. Tables without an explicit `definition` column fail
closed with `PARSE_ERROR`; there is no name-only compatibility path.

### Regression lock

Command compared the complete pre-change and post-change symbol verdict maps:

```text
before=81 after=81 verdict_changes=0
```

This consists of 77 per-symbol verdicts and four module-scope verdicts.

### Root ownership negative fixture

```text
$ python3 docs/clang-fix-campaign/tools/symbol_audit.py --negative-fixture duplicate-spec-root-mismatch
NEGATIVE_FIXTURE | duplicate-spec-root-mismatch | MISMATCH: skill-owned symbol defined outside its registered root: ci_triage/gbs_report.py is not under tizen_qb_discover
exit 1
```

### Same-name positive fixtures

The source-only fixture remains independent of the same-spelled report helper:

```text
$ python3 docs/clang-fix-campaign/tools/symbol_audit.py --key-fixture source-twin-only
KEY_FIXTURE | source-twin-only | ci_triage/sources.py:_attrs_to_map | consumers=() | internal=('_BuildsTableParser.handle_starttag@149',) | OK
exit 0
```

Both definitions can be registered simultaneously and retain their own
measured internal consumer sets:

```text
$ python3 docs/clang-fix-campaign/tools/symbol_audit.py --key-fixture twin-both-binary-key
KEY_FIXTURE | twin-both-binary-key | ci_triage/sources.py:_attrs_to_map | consumers=() | internal=('_BuildsTableParser.handle_starttag@149',) | OK
KEY_FIXTURE | twin-both-binary-key | ci_triage/gbs_report.py:_attrs_to_map | consumers=() | internal=('_IframeParser.handle_starttag@199', '_ReportTableParser.handle_starttag@217') | OK
exit 0

$ python3 docs/clang-fix-campaign/tools/table_audit_bridge.py --key-fixture twin-both-binary-key
KEY_FIXTURE | twin-both-binary-key | 2 distinct definitions | OK
exit 0
```

The equivalent name-only indexes reproduce the original collision:

```text
$ python3 docs/clang-fix-campaign/tools/symbol_audit.py --negative-fixture twin-both-name-only
NEGATIVE_FIXTURE | twin-both-name-only | MISMATCH: name-only SPECS key overwrote one definition
exit 1

$ python3 docs/clang-fix-campaign/tools/table_audit_bridge.py --negative-fixture twin-both-name-only
NEGATIVE_FIXTURE | twin-both-name-only | MISMATCH: name-only key overwrote one definition
exit 1
```

### Commit A gates

```text
pytest: 847 passed, 1 skipped
lint-imports: 5 kept, 0 broken
mypy: Success: no issues found in 101 source files
symbol_audit: 77 SYMBOL OK; 4 MODULE-SCOPE OK; 0 MISMATCH; 0 INCOMPLETE
table bridge: 77 SYMBOL OK; 4 MODULE-SCOPE OK; all five difference counters zero
```

The twin guard's known over-skip is documented in `symbol_audit.py`: a module
that defines a same-spelled top-level symbol is intentionally skipped even if
it also imports the original. This is a known limit, not an invitation to
silently change attribution semantics.
