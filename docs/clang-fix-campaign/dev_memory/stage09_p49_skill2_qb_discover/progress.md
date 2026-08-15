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

## Commit B: extraction body

The production module was copied before the move and compared immediately
after `git mv`:

```text
$ cmp /tmp/qb_sources_before_move.py tizen-qb-discover/scripts/tizen_qb_discover/sources.py
exit 0
$ sha256sum /tmp/qb_sources_before_move.py tizen-qb-discover/scripts/tizen_qb_discover/sources.py
c5fd0c5b1d715aedee508bbd69211e73e05ca4183f13ff303924f9053c5a5830  /tmp/qb_sources_before_move.py
c5fd0c5b1d715aedee508bbd69211e73e05ca4183f13ff303924f9053c5a5830  tizen-qb-discover/scripts/tizen_qb_discover/sources.py
```

The legacy `ci_triage.sources` module is a pure four-name re-export shim with
zero `def` or `class` statements. `batch_cli`, `orchestrator`, and the existing
source tests import directly from `tizen_qb_discover.sources`; their diffs are
limited to import lines.

Commit B runs before the pyproject and root-linter registration assigned to
commit C. Its checks therefore use an explicit temporary path prefix rather
than pulling commit C configuration forward:

```text
PYTHONPATH=$PWD/tizen-qb-discover/scripts .venv/bin/pytest
847 passed, 1 skipped
MYPYPATH=$PWD/tizen-qb-discover/scripts .venv/bin/mypy
Success: no issues found in 101 source files
lint-imports: 5 kept, 0 broken
ruff: All checks passed
```

## Commit C: gates, audit, and skill contract

### Mechanical registration sync

The seven `tizen_ci_shared.quickbuild_http` inventory entries that previously
named `ci_triage.sources` now name `tizen_qb_discover.sources`:

1. `HttpFetcher`
2. `QuickBuildError`
3. `_raise_if_login_page`
4. `_urllib_fetch`
5. `DEFAULT_COOKIE_PATH`
6. `DEFAULT_QUICKBUILD_BASE_URL`
7. `load_cookie_jar`

The eighth stale reference was handled explicitly rather than left inert:
`MODULE_OWNERS["ci_triage.sources"]` became
`MODULE_OWNERS["tizen_qb_discover.sources"] = "skill/tizen_qb_discover"`.
`REGISTERED_SKILL_ROOTS`, `ROOT_LAYERS_HIGH_TO_LOW`, setuptools package
discovery, and mypy paths/packages all include the new skill.

The first linter run after editing `pyproject.toml` failed closed because the
existing editable installation still exposed the old package map:

```text
Could not find package 'tizen_qb_discover' in your Python path.
```

After `.venv/bin/python -m pip install -e .`, import-linter 2.3 loaded the new
root and the positive run was:

```text
Analyzed 36 files, 65 dependencies.
application layers: orchestration -> skills -> shared KEPT
extracted skills are independent KEPT
shared internal layers: L1 -> L0 -> types KEPT
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent KEPT
Contracts: 6 kept, 0 broken.
exit 0
```

### Negative controls

Each violation was introduced temporarily, measured, removed, and followed by
the positive `6 kept, 0 broken` run above.

```text
qb-discover -> ci_triage:
tizen_qb_discover is not allowed to import ci_triage
tizen_qb_discover.sources -> ci_triage (l.5)
root-layers BROKEN; exit 1

qb-discover -> convergence-judge:
tizen_qb_discover is not allowed to import tizen_convergence_judge
tizen_qb_discover.sources -> tizen_convergence_judge (l.5)
skill-independence BROKEN; exit 1

shared -> qb-discover:
tizen_ci_shared is not allowed to import tizen_qb_discover
tizen_ci_shared.types -> tizen_qb_discover (l.5)
shared-no-uplink BROKEN; exit 1
```

`skill-independence` is a symmetric independence contract, so the measured
qb-discover-to-convergence violation activates the same rule in both peer
directions.

### Audit and behavioral parity

```text
symbol_audit: 96 SYMBOL OK; 4 MODULE-SCOPE OK (48 symbols covered);
              0 MISMATCH; 0 INCOMPLETE
table bridge: 96 SYMBOL OK; 4 MODULE-SCOPE OK;
              0 MISSING_FROM_INVENTORY; 0 MISSING_FROM_BODY;
              0 OWNER_MISMATCH; 0 PARSE_ERROR
```

The legacy shim and extracted skill ran the existing `OVERVIEW_HTML` fixture
through the same fake fetcher without network access. Their normalized JSON
bytes were identical:

```text
shim_sha256=96783e837cd25f76f79134c31edc5c4faee195ae302a4d84b62b360fe56f0d01
skill_sha256=96783e837cd25f76f79134c31edc5c4faee195ae302a4d84b62b360fe56f0d01
byte_equal=True
build_count=5
```

The arch exemption probe was also explicit:

```text
$ grep -c arch tizen-qb-discover/scripts/tizen_qb_discover/sources.py
0
exit 1
```

The source-side and report-side `_normalize_text` helpers remain separate,
and `tizen-ci-triage/scripts/ci_triage/gbs_report.py` has zero diff from commit
`41152fe`. The legacy `ci_triage.sources` file remains a four-name re-export
shim for deletion at P4.9 end.

### Commit C gates

```text
pytest: 847 passed, 1 skipped in 17.69s
lint-imports: 6 kept, 0 broken
mypy: Success: no issues found in 103 source files
ruff (tracked Python files): All checks passed
py_compile: exit 0
skill validator: Skill is valid!
symbol_audit: 96 + 4, all green
table bridge: 96 + 4, all green
```

An unscoped `ruff check .` also inspected the unrelated untracked
`audit_four_sigs.py` and reported its pre-existing style issues. That file was
not modified or staged; the repository's complete tracked Python set passed.
