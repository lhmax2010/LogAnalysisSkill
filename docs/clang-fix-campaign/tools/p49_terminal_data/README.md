# Frozen OBS predicate encoding

Source: `../../p49-terminal-obs-predicates-v1.2.md`. The designer checked the
`c79e893` encoding and FatTank approved it on 2026-09-28. Freeze commit:
`6601cfc60fcbed8d2f8fa91301f7693d52723d94`. No predicate or exemption bytes changed.
After erratum 1 (`32b7f43`), only item3/item4 producers ran, both verified PASS.
Erratum 2 closes DIFF-03; the recorded LIVE_SYMLINK_TO_DIR message passes its exact
shape check. DIFF-04 is CLOSED by the designer/FatTank's segment split: unchanged
fields come from the gate's own paired execution, not OBS difference sources.
Segment 2 structure, registration and artificial controls are complete; the real
before-run is PENDING_SEG3, waiting for the item5 reader universe. No producer was
rerun, and the frozen predicate/exemption JSON files remain unchanged.
Erratum 3 updates only timeout scenario plans and registrations: old results now
reference the same item4 outcome, not Section 4's superseded absence convention.
Stage14 progress section 18 records the intake hash and revision evidence.

## Representation

`predicates.json` is an ordered array of the fifteen claim objects. Each retains
the six source fields. Predicate nodes use `op`, `args`, `source`; `count` also
uses `cmp`. One numbered requirement is one direct child of the claim's `all`:
multiple explicit expressions in that requirement are grouped by `all`, in
source order. Every descendant repeats the same condition identifier. G1-G4
are the first four children. The root `all` only assembles these requirements.

Paths are strings. Constant RHS values/arrays stay literal. `$ref` and `$file`
are two-argument operands; `union`, `keys`, `values`, `$value` retain the source
language's argument-only restrictions. No host-language expression evaluation,
shell command, production import or producer callback is available.

Schemas use `record(required, optional)`, `array(items)`, `map(values)` and
`union(tag, variants)` dictionaries. Scalars are `str`, `int`, `bool`; `literal`
represents only the document's discriminator strings. Common/Evidence/CodeState/
MarkerState are expanded into each schema. Closed records are checked at every
depth; a map permits arbitrary string keys but still checks every value. `bool`
does not satisfy `int`. Predicates, not schemas, supply other value restrictions.

The canonical hash covers the whole registry, including subjects and schemas:
UTF-8, sorted object keys, compact JSON separators, preserved array order. It
excludes `renderer_version`. A verifier invocation must receive an external
expected hash and the saved generated block. Recomputing the expected hash from
an untrusted replacement registry is not a valid integrity check. The batch CLI
additionally checks both approved canonical pins before evaluation or rendering;
`--expected-hash` cannot replace them. Any mismatch refuses execution. Changes to
these files require the frozen design's erratum/approval process. The low-level
evaluator is retained for artificial language tests, not as the batch entry point.

`measurement_exemptions.json` is `[]`. The batch boundary rejects nonempty
exemptions. The generic upper-bound comparison is tested with artificial
reference sets, not with fabricated SEAL-16 observations.

## Reproduction

From the repository root, in an environment with the project development tools:

```bash
python docs/clang-fix-campaign/tools/terminal_predicates.py docs/clang-fix-campaign/tools/p49_terminal_data/predicates.json
python docs/clang-fix-campaign/tools/terminal_predicates.py docs/clang-fix-campaign/tools/p49_terminal_data/predicates.json --render
python -m pytest tests/unit/test_terminal_predicates.py -vv
```

Compare the render command's stdout byte-for-byte with `predicates.generated.md`.
`control_catalog.json` maps the artificial controls to test nodeids and recorded
results. `CTRL-INTRA-PKG-PROXY` remains `NOT_RUN`: that scanner control is outside
this segment. The synthetic fixture is explicitly not an observation of the
repository. Test exit 0 means the expected positive/negative behavior was
asserted, not that a negative input was accepted.

See stage14 `progress.md` section 11 for document/condition counts and baseline,
section 12 for approval, freeze SHA and canonical pins, and section 17 for the
segment-2 closeout. Historical control_catalog entries describe segment 1;
the additional freeze-guard tests and raw logs are recorded in section 12.
The batch CLI supports explicit `--claim` selection while checking the complete
frozen registry and requiring exactly the selected output keys. It never emits
PASS for omitted claims. Default invocation still requires all fifteen outputs.

## Section 6 Expected-Difference Gate

`scenario_manifest.json`, `result_schema.json` and `expected_diff.json` belong to
the expected-difference gate, not the frozen OBS predicate registry. The current
scope is segment-2 structure and artificial controls only. The real before-run
is **PENDING_SEG3**; this is not an assertion that Section 6 or A0 is complete.

The manifest covers four source-directory cases, six call surfaces with each of
none/timeout/SIGINT/SIGTERM, and the two marker interruption points. All thirty
currently use DIFF_SET: every scenario traverses a signature covered by E2-2.
NO_DIFF is implemented and tested separately with artificial unchanged objects;
no fictitious production scenario is added merely to obtain a nonzero count.
Unlisted fields always compare exactly equal, with no normalization or masks.

`expected_diff_sources.md` is a generated view of every registration, not a second
authority. Each JSON recipe retains the original document quote/section/SHA or
the archived OBS JSON Pointer/SHA. Under E3-1, before timeout runs inject the same
TimeoutExpired at the same call with the same fixture, without passing timeout.
Under E3-2, old timeout results come from that scenario's item4 outcome; the gate
checks the entire projected before outcome, including unchanged messages.
Fetch query/git and submit git messages remain equal and cannot be registered as
differences. Shared git/exclude messages gain the E1-2 prefix; remote return and
warning lists change to the fixed warning code. Missing old kwargs are checked
on the exact archived call. The Section 5 OBS
references establish only that kwarg's absence, not an observed marker-write
interruption or reader result. Default/interruption timeout null is a real value,
not the ABSENT tag. All derived strings are calculated from fixed fixture inputs
and compared in full.

From the repository root, using an isolated tooling environment:

```bash
python docs/clang-fix-campaign/tools/build_terminal_diff_data.py --check
python docs/clang-fix-campaign/tools/terminal_expected_diff.py check
python docs/clang-fix-campaign/tools/terminal_diff_controls.py normal
python -m pytest tests/unit/test_terminal_expected_diff.py -vv
```

Replace `normal` with any of the following; each must exit 1:
`extra-change`, `missed-change`, `empty-reason`, `impossible-registration`,
`missing-mode`, `unknown-mode`, `no-diff-with-differences`, `empty-diff-set`,
`readers-empty`, `readers-missing`. The missing/unknown-mode pair covers one of
the seven normative controls. The additional `unchanged-timeout-message` control
must also exit 1: it registers an unchanged fetch timeout message as a change.
Stage14 progress section 18 records the revised exact commands,
exits and the final code/data hashes. No control invokes an OBS producer.

### Segment-3 Integration Boundary

`readers_from_item5(output)` extracts the nonempty common reader universe from
the already-verified `OBS-1.item5-order` artifact. It does not infer outcomes or
replace the frozen verifier. Pass that list into `Gate.collect(runner, readers)`
or `Gate.dual_run(before_runner, after_runner, readers)`. Missing/empty/duplicate
lists fail before callbacks. Every result must contain exactly those readers,
including returned values or exception type/code/message; marker existence and
raw-byte SHA cannot substitute for the reader results.

A collector accepts `(scenario, sorted_reader_ids)` and returns a complete
`result_schema` object. Before and after collectors are independent, use the same
fixed fixture inputs, and must freeze volatile inputs rather than mask outputs.
The framework snapshots returned objects to avoid cross-run aliasing, validates
the complete result set, and compares the exact registered differences. The
concrete production collectors and their **real execution are deferred to segment
3**. Artificial disk/reader values from `terminal_diff_controls.py` must never be
used to fill a real result or submitted as OBS facts.

Once actual before/after files and the verified item5 output exist, the comparison
entry is `terminal_expected_diff.py compare --before <file> --after <file>
--item5-output <file>`. It rejects missing files/fields/scenarios, unknown envelope
fields, incomplete reader membership, wrong old/new values and any extra or
missing difference. It does not collect observations itself on this CLI path.
