# P4.9 skill-4 build-verify progress

## A0 design drift ledger

Status: COMPLETE, awaiting independent review before the design freeze.

Authority under test:
`docs/clang-fix-campaign/p49-skill4-build-verify-design-v1.12.md`.

The A0 precondition ruling is applied directly to the candidate body:

- checked scope is every normative section except the revision block, section
  5.4, and section 5.5;
- `OUT_OF_SCOPE` is a mechanical ignored category whose complete old-line span
  must lie in those exclusions;
- all thirteen source designs, v1.0 through v1.12, are stored under
  `docs/clang-fix-campaign/history/skill4/` and pinned by SHA-256 in the data
  file.

The target design SHA-256 recorded by the data file is
`6b5a6654f1e1141cc7a64de57597607bb9f890083e33c4d783b0ebc9042626a1`.
The v1.12 candidate and its corpus copy are byte-identical (`cmp` exit 0).

### First baseline generation

Command:

```text
python3 docs/clang-fix-campaign/tools/design_drift_ledger.py bootstrap \
  --data docs/clang-fix-campaign/tools/design_drift_ledger.json
```

Result (`exit 0`):

```text
BOOTSTRAP | candidates=128 retained=81 ignored=47 binding_candidates=1410 bindings=22
```

The generated candidate ledger is
`docs/clang-fix-campaign/tools/design_drift_ledger.json`. Its reverse-gate
partition is 81 retained regression patterns and 47 mechanically ignored
`OUT_OF_SCOPE` spans. There are no hand-added patterns. The binding exporter
produced a conservative cross-product superset of every changed definition
section with every DoD/section reference; 22 reviewed bindings were retained
and the remainder are explicitly present in `ignored_binding_candidates`.

Full output: [bootstrap.txt](a0-evidence/bootstrap.txt).

### Frozen-candidate gates

Command:

```text
python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
  --data docs/clang-fix-campaign/tools/design_drift_ledger.json
```

Result (`exit 0`):

```text
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=128 | retained=81 | ignored=47 | bindings=22 | binding_candidates=1410
```

The check independently parses every raw diff deletion line, then compares
that external line set with the candidate spans. It also verifies the exact
candidate partition, replay counts and checked sections, frozen target match
counts, complete binding-candidate partition, and the DoD binding or
`PROCESS_ONLY` partition.

Full output, including all 128 candidates and 22 bindings:
[check.txt](a0-evidence/check.txt).

### Admission falsification

Command:

```text
python3 docs/clang-fix-campaign/tools/design_drift_ledger.py admission-v19 \
  --data docs/clang-fix-campaign/tools/design_drift_ledger.json
```

Result: expected `exit 1`. It reports three historical drifts and includes both
required known defects:

```text
BINDING_DRIFT | B-RAW-DIFF | binding B-RAW-DIFF reference selector did not match v1.9
BINDING_DRIFT | B-X-PRESERVE | missing_definition=[], missing_reference=['X 原样保留']
ADMISSION_V19 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
```

Full output: [admission-v19.txt](a0-evidence/admission-v19.txt).

### Per-binding falsification

All 22 bindings were run independently with `negative-binding <binding-id>`.
Every command returned expected `exit 1`; no command returned 0 or 2.
For each `TEXT_CONTAINS` binding, every registered carrying snippet was
removed. Every `COUNT_EQUAL` binding rejected numeral deletion, numeral
change, and a selector-covered definition mutation while accepting a
selector-external interference mutation. The `REF_ONLY` binding rejected both
a restated carrying clause and a reference to another existing section.

Full commands, mutation outcomes, and all 22 exit codes:
[binding-negatives.txt](a0-evidence/binding-negatives.txt).

### OUT_OF_SCOPE anti-abuse falsification

Every one of the 47 `OUT_OF_SCOPE` ledger items was independently changed to
point at an in-scope old line. Every item returned gate exit 1; the aggregate
command returned expected `exit 1`:

```text
OUT_OF_SCOPE_SUMMARY | items=47 | RED_AS_EXPECTED
exit=1
```

Full per-item output:
[out-of-scope-negative.txt](a0-evidence/out-of-scope-negative.txt).

### Implementation findings

Two parser defects were found by running the gate rather than reasoning about
it and were corrected before recording the evidence above:

1. A zero-context diff hunk can cross a revision/body or top-level section
   boundary. Candidate export now splits the deleted side at each scope
   boundary while preserving the raw new-side span as provenance. Otherwise a
   checked pattern spanning two separately scanned sections has a false replay
   count of zero.
2. Once inside a hunk, a Markdown content line beginning with `---` or `+++` is
   a deletion/addition, not a diff file header. Header filtering now relies on
   hunk state, so the independent raw-deletion anchor cannot silently lose
   horizontal-rule lines.

Neither correction changes the design or weakens a predicate. Both make the
raw-diff external anchor account for the bytes Git actually reports.

### Regression and tool quality

```text
$ .venv/bin/pytest -q
883 passed, 1 skipped in 17.52s

$ .venv/bin/mypy
Success: no issues found in 105 source files

$ .venv/bin/lint-imports
Contracts: 6 kept, 0 broken.

$ .venv/bin/ruff check <all tracked Python files> \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
All checks passed!

$ python3 -m py_compile \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
exit=0
```

Running `ruff check .` also sees the pre-existing untracked root file
`audit_four_sigs.py` and reports its existing compact-style violations. That
unrelated file is outside A0 and was not modified or staged. The complete
tracked Python surface plus the new ledger script is green under the same Ruff
configuration.

Bootstrap determinism was checked by hashing the data file before and after a
second generation:

```text
bootstrap_sha_before=ebafd3f176530a99fe6ff82376866c02601b792da5a1145a2d52cabf76e0d2ff
bootstrap_sha_after=ebafd3f176530a99fe6ff82376866c02601b792da5a1145a2d52cabf76e0d2ff
deterministic=yes
```
