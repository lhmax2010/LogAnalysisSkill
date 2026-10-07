# Frozen OBS predicate encoding

Source: `../../p49-terminal-obs-predicates-v1.2.md`. The designer checked the
`c79e893` encoding and FatTank approved it on 2026-09-28. Freeze commit:
`6601cfc60fcbed8d2f8fa91301f7693d52723d94`. No predicate or exemption bytes changed.
After erratum 1 (`32b7f43`), only item3/item4 producers ran, both verified PASS.
Erratum 2 closes DIFF-03; the recorded LIVE_SYMLINK_TO_DIR message passes its exact
shape check. Segment 2 now stops at missing archived reader outcomes and the
marker-write interruption observation (DIFF-04, stage14 progress section 16).
No producer was rerun, the frozen JSON files remain unchanged, and the
expected-diff gate has not run.

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
section 12 for approval, freeze SHA and canonical pins, and section 16 for the
current stop report. Historical control_catalog entries describe segment 1;
the additional freeze-guard tests and raw logs are recorded in section 12.
The batch CLI supports explicit `--claim` selection while checking the complete
frozen registry and requiring exactly the selected output keys. It never emits
PASS for omitted claims. Default invocation still requires all fifteen outputs.
