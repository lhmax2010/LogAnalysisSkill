# OBS predicate candidate encoding

Source: `../../p49-terminal-obs-predicates-v1.2.md`. This is a candidate
transcription awaiting designer review and FatTank's separate freeze approval.
No OBS producer has been implemented or invoked by this segment.

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
an untrusted replacement registry is not a valid integrity check. This commit
records the candidate hash only; it does not supply the pending human approval.

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

See stage14 `progress.md` section 11 for document/condition counts, current
hashes, the clean baseline, the original logs, and remaining approval gates.
