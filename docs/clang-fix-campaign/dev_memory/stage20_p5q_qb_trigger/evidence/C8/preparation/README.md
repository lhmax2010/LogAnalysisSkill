# C8 Preparation Only

No browser or real QuickBuild request has been made. A new exact confirmation is required.
Unit 2 does not exist yet. `prepared.json` identifies the synthetic unit 1 and its three records.

- `mirror-commands.json`: one read-only Gerrit fetch plus local ref construction, full argv/exits.
- `mirror.json`: target/tree/ref checks. No Gerrit push.
- `config.yaml`: dedicated production configuration, no credentials or test browser overrides.
- `synthetic-basis.json`, `state-before.sql`: explicitly constructed C6-01 prerequisites.
- `c6-tree-before.json`: immutable C6 content inventory, checked after each preparation stage.
- `preflight-before-cleanup.json`: rejected because of an old orphan socket directory.
- `orphan-cleanup.json`: metadata and no-reference proof; link contents were not exposed.
- `preflight.json`: final successful check, including three D-state samples ten seconds apart.

One premature read-only preflight was started while `construct` was still running and returned
`REJECTED_ARCH_AGGREGATE_MISMATCH` (missing or ambiguous link), exit 1. The construct process
subsequently exited 0. This invocation-order error did not start a browser or write QB intent.
The next preflight exited 1 for the orphan profile; after its targeted cleanup, final preflight
exited 0. See progress 49.6. No real submission or retry occurred.

The optional current public manifest request was not performed. No current snapshot has been
frozen; the configuration still requires `@freeze` from the real form after authorization.

External root: `/home/linhao/Toolchain/p5q-live-validation/p5q-c8/`.
State binary is intentionally not committed. The exact production command and twelve proposed
fields are in progress 49.7. This evidence is not submission authorization.
