# E2E Smoke Report v1: RC final under runbook v3

Date: 2026-08-05 (Asia/Shanghai)

Branch: `clang-fix-campaign`

Code under test: `269321820abe0eddb7db345dcb26ffaedc7127c6`
(`checkpoint/p45_code_ready`)

Result: **PASS -- E1-E4 and both E6 cases completed; E5 report finalized**

This report follows the frozen stop-and-report protocol. No runtime code or
frozen design text was changed to accommodate the discrepancies below. The
initial evidence/input stop was adjudicated by `rc-resolution.md` and closed in
change_41. The runbook architecture drift was closed as no design change in
change_42, followed by a full CLI audit. RC then completed E1-E4 and the real
multi-assistant E6 case. The supplied cynara checkout failed its unchanged
baseline, so change_43 correctly stopped fault injection. Developer
adjudication closed it as a test-input issue and authorized one retry at the
accepted Wave 1-era toolchain snapshot. That clean retry passed, allowing E6'
to complete without runtime or frozen-design changes.

## E0 environment preflight

### GBS and toolchain

Commands:

```text
$ gbs --version
gbs 2.0.6

$ gbs build --help
usage: gbs build [-h] [-A ARCH] ... [--include-all] ... [gitdir]
```

Configuration:

```text
path: tmp/gbs_llvm.conf
sha256: 08d31c3499fb0418eee0198a85c240aeefc0c56f20b2213ca0880ac4753f1f77
profile: profile.tizen_unified_standard
buildroot: $REPO/tmp/GBS-ROOT-TIZEN-UNIFIED-LLVM
```

The real build log contains the expected LLVM packages and compiler:

```text
[    8s] [68/105] keeping libllvm-22.1.8-18.1
[    8s] [99/105] keeping llvm-22.1.8-18.1
[    8s] [101/105] keeping clang-22.1.8-18.1
[   11s] + CC=armv7l-tizen-linux-gnueabi-clang
[   11s] + CXX=armv7l-tizen-linux-gnueabi-clang++
```

### Source packages

| Package | HEAD | Packaging | Repository state |
|---|---|---|---|
| zlib | `76eff23cff0a4dfd320fea8ee5884e758c8c74f4` | `packaging/zlib.spec` | clean, branch `tizen_base` |
| cynara (supplied) | `611ff2ecc979bbd9d269e2bc7eb227a895055667` | `packaging/cynara.spec` | clean, branch `tizen`; baseline not buildable |
| cynara (accepted retry) | `9add176aefd99e9274e99f597a15c26e75067429` | `packaging/cynara.spec` | accepted toolchain snapshot; clean baseline passed |
| libtpl-egl | none | none | empty initialized Git repository; no commit or source |

Per RC/E6, `libtpl-egl` is therefore a required skip. No packaging was
fabricated.

### Clean zlib baseline

Canonical rerun command:

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO/tmp/Verification/codes/zlib"
/usr/bin/time -f '\nWALL_SECONDS=%e\nMAX_RSS_KB=%M' \
  gbs -c "$REPO/tmp/gbs_llvm.conf" \
  build -A armv7l --include-all 2>&1 | \
  tee "$REPO/tmp/campaign-smoke/logs/E0-zlib-clean-baseline.log"
```

Result excerpt:

```text
info: *** Build Status Summary ***
=== Total succeeded built packages: (1) ===
info: Done

WALL_SECONDS=48.13
MAX_RSS_KB=136436
```

Artifact:

```text
path: tmp/campaign-smoke/logs/E0-zlib-clean-baseline.log
size: 77957 bytes
sha256: 72f727a862cbb4c38a5ad676336abe9b5b1e487f92e0700a87a169a5692e2ef2
```

The zlib source repository remained clean after the build.

An earlier harness attempt used a relative `tee` destination after changing
the working directory. GBS itself succeeded, but `tee` could not create the
intended repository-level artifact and the pipeline exited 1. That output was
not accepted as evidence. The accidentally created nested `zlib/tmp` directory
was moved to `tmp/campaign-smoke/misplaced-zlib-tmp`; the canonical absolute-
path rerun above is the only accepted E0 artifact.

## Resolved condition 1: raw log versus evidence JSON

The runbook requires:

1. save the baseline GBS failure as `ci_evidence.log`;
2. use that log as the REPRODUCE baseline evidence;
3. compute its fingerprint with
   `convergence.py::_primary_fingerprint`.

The frozen implementation has a different, physically enforced contract:

- `_primary_fingerprint(evidence, ...)` reads `evidence.get(...)`; its input is
  an analyzer evidence object, not text or bytes;
- `previous_evidence._from_payload()` reads the bound file, validates SHA-256,
  calls `json.loads(raw)`, and requires a JSON object;
- a real GBS log therefore returns `MissingEvidence("... evidence is invalid
  JSON ...")` before the first build invocation.

Relevant commands used to verify the contract:

```bash
sed -n '1,300p' tizen-ci-triage/scripts/ci_triage/previous_evidence.py
sed -n '1,285p' tizen-ci-triage/scripts/ci_triage/verify/convergence.py
sed -n '70,230p' tests/unit/test_campaign_repair_step.py
```

The unit fixture confirms the implemented shape: `ci_evidence_ref` may name an
external evidence source, but REPRODUCE `evidence_local` points to
`baseline.json`, an analyzer `evidence_packet/v1` object.

The developer adjudicated this in `rc-resolution.md`: raw logs remain audit
artifacts; real analyzer output JSON is the evidence/fingerprint input. The
decision required no design or runtime-code change.

## Resolved condition 2: historical logs were absent

Commands:

```bash
find tmp/Verification/log -maxdepth 2 -type f -printf '%P %s bytes\n'
find tmp/Verification -maxdepth 2 -type d -printf '%P\n' | sort
```

Observed result:

```text
# first command: no output

codes
codes/cynara
codes/libtpl-egl
codes/zlib
log
```

`tmp/Verification/log/` exists but contains zero files. This contradicts the
remediation task's supplied environment fact that it contains the historical
real bug logs. Consequently E6 cannot:

- confirm that a fresh failure has the same root cause as its historical log;
- seed `ci_evidence` from the historical log;
- compare fingerprints produced from historical and fresh evidence.

The developer subsequently supplied `multi-assistant.log` and matching source
plus packaging, and authorized one cynara E6' case. An extra
`united-servvice.log` has no matching source/packaging under `codes/` and is a
per-case pause. The exact resumed scope is recorded in `rc-resolution.md` and
closed change_41.

## E1 resumed: raw log to analyzer JSON

### Synthetic broken baseline

The zlib smoke repository was branched at the clean baseline and committed with
two independent undeclared identifiers in `adler32.c`:

```text
branch: campaign-smoke/broken-zlib
base_commit_broken: 0bd8e9a0c835b24471eaeba54e606583e5d2dfaa
fault 1: campaign_missing_one
fault 2: campaign_missing_two
```

Canonical build command used `bash -o pipefail`; GBS exited 1 as required:

```text
adler32.c:64:44: error: use of undeclared identifier 'campaign_missing_one'
adler32.c:65:44: error: use of undeclared identifier 'campaign_missing_two'
2 errors generated.
=== Total succeeded built packages: (0) ===
error: <gbs>some packages failed to be built
WALL_SECONDS=12.28
MAX_RSS_KB=100180
```

Artifacts are deliberately identified separately:

```text
raw_log: tmp/campaign-smoke/logs/E1-zlib-broken-baseline.log
raw_log_sha256: d3adb3fd72bf115667a17efa6d7bb000597eab796df5ce5f15b1329fb5ae4154
analyzer_json: tmp/campaign-smoke/analyzer/zlib-baseline/evidence_packet.json
analyzer_json_sha256: d79617226de39f4d16ea703bb320207954309a8c21ff571f86bdcd94a1a593b0
```

Real analyzer command:

```bash
PYTHONPATH=tizen-gbs-log-analysis/scripts:tizen-ci-triage/scripts \
  .venv/bin/python -m gbs_analyzer analyze \
  tmp/campaign-smoke/logs/E1-zlib-broken-baseline.log \
  --src-root tmp/Verification/codes/zlib \
  --spec-path tmp/Verification/codes/zlib/packaging/zlib.spec \
  --package zlib --arch standard-armv7l \
  --profile tizen_unified_standard --output-format json \
  --output-dir tmp/campaign-smoke/analyzer/zlib-baseline
```

The first process attempt did not expose the repository script roots through
`PYTHONPATH` and failed module discovery. It produced no accepted evidence.
The complete command above is the exact successful rerun and is the
reproducible evidence-generation command used for RC.

It exited 0 and produced `evidence_packet/v1`; its primary error is
`adler32.c:64:44`, kind `compiler`, message `use of undeclared identifier
'campaign_missing_one'`. The second identifier is root-cause candidate rank 2.
The v2 evidence pipeline is therefore proven through analyzer output.

An earlier FAIL capture omitted shell `pipefail`, so `tee` masked GBS exit 1 as
pipeline exit 0. That run was rejected as process-status evidence and replaced
by the canonical rerun above; the raw artifact path was overwritten by the
canonical bytes.

## Stop condition 3: runbook arch argument versus public CLI

The unchanged runbook E2 command passes:

```text
--arch armv7l
```

The implementation accepts raw QuickBuild architecture names only:

```python
ARCH_RAW_TO_NORM = {
    "standard-aarch64": "aarch64",
    "standard-armv7l": "armv7l",
    "standard-x86_64": "x86_64",
}
```

A no-build CLI probe using the runbook's argument returned one JSON object and
exit 4:

```json
{"arch_norm":"","convergence_reason":"arch is not in the verified whitelist: 'armv7l'","error_code":"REJECTED_IDENTITY_MISMATCH","invocations_used":0,"result":"FAIL","verdict":"n_a"}
```

This rejection occurs before config, state, edit-spec, or source access. No
state DB was created and no invocation was consumed. Substituting
`standard-armv7l` would align with the implementation and cause build-verify to
derive `gbs -A armv7l`, but v2 said all other runbook clauses were unchanged.
Changing the command without adjudication would therefore violate the same
stop-and-report rule that produced change_41.

### Plan-external validation: architecture fail-closed path

Although the wrong runbook argument stopped RC, it unintentionally exercised a
real safety path end to end. The public CLI returned:

- process exit 4;
- `REJECTED_IDENTITY_MISMATCH`;
- one deterministic JSON object;
- zero DB writes (the DB file was not created);
- `invocations_used=0` and no GBS build.

The architecture whitelist therefore behaved in the real process exactly as
the frozen fail-closed identity gate specifies.

## Runbook v3 CLI audit

Every invocation in the runbook was compared with process-level `--help` and
design §4.1 before resuming:

| Invocation | v1/v2 text | v3 correction | Basis |
|---|---|---|---|
| repair-step unit key | `--unit <key>` | `--campaign-unit-key <key>` | CLI required option |
| repair-step architecture | `--arch armv7l` | `--arch standard-armv7l` | §4.1 `arch_raw` page-name form |
| repair-step required inputs | trailing `...` | explicit `--state-db` and `--config` | CLI required options |
| repair-step round/edit | names already correct | retained | CLI required options |
| repair-step timeout | omitted | retained as optional | CLI `[--wall-timeout]` |
| GBS preflight | `gbs build --help` | retained | real GBS 2.0.6 help |
| DB inspection | read-only `sqlite3` | retained | not a state-writing API |

The nearby E1 seed fields were corrected from normalized `armv7l` to raw
`standard-armv7l`; event queries and workspace assertions retain normalized
`armv7l`. No other CLI invocation mismatch was found.

## E1 unit seed

The first seed used only the frozen `campaign_state` write APIs but copied the
source's original HTTPS Gerrit URL. The identity normalizer correctly produced
`gerrit/a/platform/upstream/zlib`, not the campaign project
`platform/upstream/zlib`. Its R1 therefore exited 4 with
`REJECTED_IDENTITY_MISMATCH` before GBS. It consumed one invocation because the
filesystem identity check occurs after the frozen invocation-consumption step.
This unit was preserved as plan-external fail-closed evidence and never retried.

The smoke preparation was corrected, without runtime changes, by setting the
disposable source origin to the canonical URL used by production source fetch:

```text
ssh://review.tizen.org:29418/platform/upstream/zlib
```

The accepted E1 unit is:

```text
["local-gbs-smoke","zlib-e1-seed2-20260805","platform/upstream/zlib","tizen","zlib","0bd8e9a0c835b24471eaeba54e606583e5d2dfaa"]
unit_hash: d8ee0038f84d
source: tmp/campaign-smoke/ws/d8ee0038f84d/src
```

Its complete `.git` directory, HEAD, canonical origin, clean status, and
private-excluded `.campaign_clone` marker were checked before the public API
seed. The unit and REPRODUCE event bind the raw and normalized arch forms,
analyzer evidence SHA
`d79617226de39f4d16ea703bb320207954309a8c21ff571f86bdcd94a1a593b0`,
raw-log audit SHA
`d3adb3fd72bf115667a17efa6d7bb000597eab796df5ce5f15b1329fb5ae4154`,
and fingerprint `adler32.c / campaign_missing_one / compiler`.

The host lacks the standalone `sqlite3` executable (`exit 127`). All audit
queries therefore used Python's standard `sqlite3` module with a read-only
`file:...?mode=ro` URI. Every write remained on a frozen public API path.

## E2 repair arc

All repair-step invocations used the runbook-v3 process form:

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/python -m ci_triage campaign-repair-step \
  --campaign-unit-key "$(cat tmp/campaign-smoke/unit_key.txt)" \
  --state-db tmp/campaign-smoke/state.db \
  --config tmp/campaign-smoke/campaign.yaml \
  --round-index N --edit-spec tmp/campaign-smoke/ES.json \
  --arch standard-armv7l
```

### R1: FAIL and advance

`es_round1.json` fixed only the first of two undeclared identifiers. The
process exited 0 with one JSON object:

```json
{"result":"FAIL","verdict":"advance","convergence_reason":"fingerprint_changed_or_error_count_changed","failure_class":"source_repairable","failure_stage":"gbs_build_failed","repair_allowed":"auto","invocations_used":1,"previous_basis":"reproduce","arch_norm":"armv7l"}
```

The analyzer evidence SHA is
`8f77fd6383ad1da553900ec19163889e61926f9cbb0ef5e3526630e9ed78b211`.
DB event 4 is the sole R1 BUILD_INVOCATION; event 5 is the sole CONVERGENCE,
references event 4, records `actual_changed_paths=["adler32.c"]`, and has
`previous_basis=reproduce`.

### R2: PASS

`es_round2.json` repaired both identifiers. The process exited 0:

```json
{"result":"PASS","verdict":"n_a","convergence_reason":"build_passed","verification_id":"69ec51ba-b62a-49a4-8deb-93e104f67cf5","invocations_used":2,"arch_norm":"armv7l"}
```

DB event 6 is the only R2 invocation; PASS convergence event 7 references it.
The campaign link binds round 2, `armv7l`, edit-spec SHA
`697a36fd4934812a613b4f70a641dd981edd1e54611cb736082a45e379983d4a`,
and the verification ID above. The verification record contains:

```text
verified_commit_sha: 45cb0ee5294760026acec4383b188b0409c837a9
verified_tree_sha: 0ce9ce50bf0a25098050e00e070b93ac85b820f3
worktree: tmp/campaign-smoke/ws/d8ee0038f84d/armv7l/iter_2
actual_changed_paths: ["adler32.c"]
```

The worktree is clean and contains both `.ci_triage_workdir` and
`.ci_triage_protected`. R1's convergence event is the stored previous chain;
the PASS stdout correctly reports `previous_basis=none` because PASS does not
perform a 6a convergence comparison.

## E3 crash recovery

A new unit `zlib-e3-crash-20260805` was seeded. A watcher polled for a newly
written PASS verification record and sent `SIGKILL` before the campaign link.
The child returned `-9`. Postmortem showed exactly:

- REPRODUCE event 8;
- BUILD_INVOCATION event 9;
- no convergence event and no campaign link;
- unlinked PASS verification `00f34aa5-9b89-4b71-9773-ea427fdfa86a`;
- `invocations_used=1`.

The accepted build log was
`tmp/campaign-smoke/ws/cfc4a1e3659b/armv7l/out/round_1/audit/gbs_build.log`,
size 78129 bytes, SHA
`685ffe1101604620a4d336cf1693d1d037b3c7cd9749c8b90ffb54f30a1ddab3`.

Re-entering the identical round returned one JSON object:

```json
{"result":"PASS","convergence_reason":"relinked","verification_id":"00f34aa5-9b89-4b71-9773-ea427fdfa86a","invocations_used":1,"round_index":1,"arch_norm":"armv7l"}
```

It created convergence event 10 referencing the old invocation event 9 and
linked the existing PASS. The build-log SHA, size, and mtime were unchanged, so
no second GBS call occurred. The watcher initially contained a smoke-only query
for a nonexistent `verification_records.build_id` column; that watcher stopped
without killing or changing the campaign process. It was corrected to detect
new verification IDs, and the accepted experiment above is the rerun.

## E4 edge cases

### Concurrent lock

Two repair-step processes targeted the same unit and arch. The first completed
PASS with verification `4f3cda57-5d11-47c1-89d2-b641ab772d7a`. The second
returned exit 5 and:

```json
{"result":"FAIL","error_code":"CAMPAIGN_STATE_BUSY","convergence_reason":"repair-step lock is already held","invocations_used":0}
```

No round, invocation, or status row was written by the rejected process.

### Round budget and convergence terminal

A unit with `max_rounds=2` produced R1 `advance`, R2 `stalled` with
`previous_basis=prev_build`, then rejected R3 in 0.3 seconds:

```json
{"result":"FAIL","error_code":"RoundsExhausted","convergence_reason":"campaign round budget exhausted","invocations_used":2}
```

The DB has only rounds 1 and 2, only invocation events 15 and 17, and status
rows `STALLED` followed by `ROUNDS_EXHAUSTED`.

### HELD reachability

After an R1 `advance`, its evidence file was renamed. R2 returned exit 4:

```json
{"result":"FAIL","error_code":"REJECTED_PREVIOUS_EVIDENCE_MISSING","invocations_used":1,"repair_allowed":"denied"}
```

The status row is `HELD_FOR_INVESTIGATION`, reason
`previous_evidence_missing`, `arch_norm=armv7l`. No R2 BUILD_INVOCATION was
written. `campaign-rebaseline` is not implemented, so authorization recovery
remains P6 as the runbook allows.

## E6 real cases

### Historical multi-assistant: completed

The historical input was checked before use:

```text
log: tmp/Verification/log/multi-assistant.log
log_sha256: 9185cdafe414dbcc5905b517b305ffc9846142d7f0629dccabed931d4d4b47ff
source HEAD: 5963dfd5eadb18a281ca8bb33af6748979ad3521
packaging: packaging/multi-assistant.spec
root cause: Clang unknown warning options -Wno-stringop-overflow and
            -Wno-stringop-truncation under -Werror
```

The historical log was analyzed with the real analyzer. A fresh unchanged GBS
build then reproduced the same failure and was analyzed separately:

```text
fresh_raw_log: tmp/campaign-smoke/logs/E6-multi-assistant-fresh.log
fresh_raw_sha256: 88e7adbb7d6f0dafb07bb0cec2b5c86ade7123889cc39727359e3a866c9775b5
historical_analyzer_sha256: 7658ebed252ed81524872a92816a141ff1dc56b55942ce4c4bec8ba6111b0ac7
fresh_analyzer_sha256: 0c62ecf0c39d54d446775a85138ce5461003c9cb31b6d6dc803fa8a157e29e62
```

Both real analyzer outputs produced the exact fingerprint:

```json
{"anchor":"unknown","diagnostic_code":"-Wno-stringop-overflow","kind":"werror","message":"error: unknown warning option '-wno-stringop-overflow'; did you mean '-wno-shift-overflow'? [-werror,-wunknown-warning-option]","normalized_file":""}
```

The source has four original GCC-oriented `-Wno-*` flags. The repair retained
all four original CFLAGS/CXXFLAGS entries and, before `%cmake`, added a
`%{toolchain_is clang}` block stripping only the two options Clang rejected.

The patch-suggest output represented this as `operation=insert_after`.
Campaign's frozen guard requires `file/old/new`, so round 1 rejected it as
`apply_failed` in 0.50 seconds, consumed one invocation, made zero source
changes, and did not run GBS. This is a real integration seam, not a guard
bypass. The identical edit was represented as an exact guarded replacement in
round 2; formatter `git apply --check` passed before execution.

Round 2 completed in 28.00 seconds with max RSS 165268 KiB:

```json
{"result":"PASS","verification_id":"cfbadfd8-efec-4503-948b-fbac184ab6e5","invocations_used":2,"convergence_reason":"build_passed","arch_norm":"armv7l"}
```

DB convergence event 26 records only
`actual_changed_paths=["packaging/multi-assistant.spec"]`. The protected PASS
worktree still contains the untouched original four flags plus the Clang-only
two-option removal block. This verifies GCC preservation and Clang
compatibility in one real GBS build.

### united-service: paused for missing source

`tmp/Verification/log/united-servvice.log` exists, SHA
`0bbd657df46073d947b55173bc726f339fad2ba2160d0d4ddc991750ef175e37`,
but `tmp/Verification/codes/` contains no united-service source or packaging.
Per scope adjudication, the case was listed and paused; no source was invented.

### E6' cynara: input stop closed and C++ case completed

Before injecting any fault, the unchanged cynara checkout at
`611ff2ecc979bbd9d269e2bc7eb227a895055667` was built with real GBS:

```bash
cd tmp/Verification/codes/cynara
gbs -c ../../../../tmp/gbs_llvm.conf build -A armv7l --include-all
```

It exited 1 after 90.68 seconds (max RSS 223700 KiB). Clang 22.1.8 reported in
four translation units:

```text
src/service/logic/Logic.h:38:10: fatal error: 'plugin/PluginCache.h' file not found
src/service/main/Cynara.h:35:10: fatal error: 'plugin/PluginCache.h' file not found
```

Accepted log:

```text
path: tmp/campaign-smoke/logs/E6-cynara-clean.log
sha256: a549babe112ed7d73813844c6d180042bde5ab6b31502e80efd7d6e568e4d17b
```

HEAD, its parent, and the full worktree contain no `PluginCache.h` or plugin
directory. There is no submodule and no packaging/CMake generation step for
the header. The source remained clean. A synthetic Clang accident cannot be
attributed or repaired on top of an already failing baseline, so no fault was
injected. RC stopped and opened change_43. Developer adjudication closed it as
no design change: this was a bad test input, and refusing to inject a fault was
the required fail-closed behavior.

The repository contained no explicit Wave 1 pin ledger. The nearest concrete
accepted toolchain record was selected once, without trying multiple revisions:

```text
snapshot: 9add176aefd99e9274e99f597a15c26e75067429
tag: accepted/tizen/unified/toolchain/20260725.092057
subject: Release 0.26.0
relationship: before 611ff2e (Adjust to new plugin management)
```

At this snapshot the source does not reference `PluginCache.h`. An independent
disposable copy built cleanly under the frozen LLVM configuration:

```text
log: tmp/campaign-smoke/logs/E6-cynara-wave1-clean.log
sha256: cbdbe2079b89065bbdd6c7b8b9cf0a10b04a717ee135beace6b025c71addc256
result: 1 package succeeded
wall: 24.84 seconds
max RSS: 223492 KiB
```

A small committed test fault then defined `campaignTemplateProbe(T *)` and
called it with integer `42`. Two independent real GBS failures produced the
Clang 22.1.8 rich diagnostic:

```text
error: no matching function for call to 'campaignTemplateProbe'
note: candidate template ignored: could not match 'T *' against 'int'
```

Each raw log was independently analyzed by the real analyzer. Their artifact
hashes differ, as expected for separate builds, while the extracted
fingerprints are byte-for-byte equal:

```text
first_raw_sha256: a024080fa1725859a45cb038419a137af43001d14025db0a06bf6de9efc13c8f
second_raw_sha256: 7af068bb7d41231d6762954e4988b50bbd154d6c057ce4195bec0bee61aba574
first_analyzer_sha256: e79593858a5730fd815205c51c4da8e508a18b52f5a5bbcbf3588d2015c8e7ef
second_analyzer_sha256: d52da5d36107c1f660ed139e9c53e91087ae1fd615a6cc6356ad9e57ed6ae4f2
```

```json
{"anchor":"campaignTemplateProbe","diagnostic_code":"<none>","kind":"compiler","message":"no matching function for call to 'campaigntemplateprobe'","normalized_file":"src/service/main/CmdlineParser.cpp"}
```

The campaign unit used fault commit
`994e9942b7666c289406935a11b78f30a1b5bf97`. Its only repair changed the
integer argument to `static_cast<int *>(nullptr)`. The public repair-step CLI
completed in one invocation:

```json
{"result":"PASS","verification_id":"ebb7960f-c7d0-4ec4-975f-daaa771b042f","invocations_used":1,"convergence_reason":"build_passed","arch_norm":"armv7l"}
```

The PASS took 27.05 seconds (max RSS 223740 KiB). Gate event 29 references
BUILD_INVOCATION event 28 and records only
`actual_changed_paths=["src/service/main/CmdlineParser.cpp"]`. The verification
record binds commit `0bf6d658d2e6f9a9067681d7bb788437966ba3c4`, tree
`d5a507bd1a614113c1dc5a3c22ceb32e8f746a46`, and edit-spec SHA
`4ce085da23f05b57a8a8b72674f1cbd7832795cd9ec5a1aec998c1af46280c60`.
The protected build copy is clean and both safety markers are present.

### Plan-external validation: fingerprint consistency

The campaign's first-bet risk was that analyzer-derived fingerprints might be
unstable across real builds, especially for multi-line C++ candidate lists.
Two separate Clang/GBS runs and two separate analyzer runs produced the exact
same normalized fingerprint above. For the exercised rich-diagnostic family,
that risk is now reduced to zero rather than merely argued from fixtures.

### Plan-external validation: real repair chain

The E6' case traversed the complete public path: clean baseline, committed
fault, two real reproductions, analyzer evidence, matched REPRODUCE event,
guarded edit spec, disposable build copy, real GBS PASS, verification record,
convergence event, and campaign verification link. No source was edited outside
the test copy and no DB row was written through an audit-only path.

## Execution matrix

| Stage | Result | Notes |
|---|---|---|
| E0 GBS/toolchain | PASS | Real armv7l LLVM 22.1.8 chroot confirmed |
| E0 clean zlib baseline | PASS | Built successfully; canonical log captured |
| E1 failure + analyzer | PASS | Real GBS exit 1; raw and analyzer hashes separated |
| E1 unit seed | PASS | Public APIs only; accepted second seed has canonical source origin |
| E2 repair arc | PASS | R1 advance, R2 PASS, event/link/marker invariants verified |
| E3 crash recovery | PASS | SIGKILL window reproduced; re-entry relinked without rebuild or re-charge |
| E4 concurrent lock | PASS | Loser exit 5, zero writes and zero invocation charge |
| E4 budget terminal | PASS | stalled then ROUNDS_EXHAUSTED; no third invocation |
| E4 HELD | PASS | Missing previous evidence writes HELD before invocation |
| E6 multi-assistant | PASS | Historical/fresh fingerprints equal; dual-compiler-safe repair passed |
| E6 united-service | PAUSED | Historical log exists; source and packaging absent |
| E6' cynara | PASS | Accepted snapshot clean; rich template diagnostic fingerprint stable; R1 repair passed |
| E5 report | PASS | Final evidence, deviations, and plan-external validations recorded |
| RD close-out/PR | READY | RC acceptance complete; no Gerrit/QuickBuild action attempted |

## Reality observations

- zlib clean baseline: 48.13 seconds, max RSS 136436 KiB.
- zlib broken baseline: 12.28 seconds, max RSS 100180 KiB.
- multi-assistant fresh reproduction: 581.25 seconds, max RSS 155948 KiB;
  cached guarded repair: 28.00 seconds, max RSS 165268 KiB.
- supplied cynara unchanged baseline failure: 90.68 seconds, max RSS 223700
  KiB; accepted snapshot clean baseline: 24.84 seconds, max RSS 223492 KiB.
- cynara rich-diagnostic runs: 22.88 and 21.91 seconds; guarded repair PASS:
  27.05 seconds, max RSS 223740 KiB.
- Final smoke directory: 139 MiB; state DB: 180224 bytes.
- Final state DB: 8 units, 12 rounds, 29 gate events, 5 campaign links,
  5 PASS records, and 3 status rows.

## Deviations and planned-external validations

1. `ci_evidence` used locally captured raw logs as CI audit substitutes; real
   analyzer JSON was the only evidence/fingerprint input.
2. Standalone `sqlite3` was unavailable; Python sqlite3 read-only URIs were
   used for audit only.
3. The first zlib source copy preserved a noncanonical HTTPS Gerrit origin and
   was correctly rejected after one invocation charge. The accepted rerun used
   production's canonical SSH origin.
4. The crash watcher needed one smoke-script-only query correction. No runtime
   hook or sleep was added to production code.
5. The architecture whitelist rejected normalized `armv7l` at the public CLI
   with exit 4, zero DB writes, and zero charge. This was a plan-external
   validation of the identity gate.
6. Patch-suggest `insert_after` is formatter-valid but not campaign-guard-valid;
   the guard rejected it before source change or build. E6 then used the same
   semantic edit in the frozen old/new representation.
7. The supplied cynara HEAD is incomplete for the frozen environment. The sole
   authorized retry used the concrete accepted toolchain snapshot `9add176`;
   it passed cleanly and supplied the completed E6' case.
8. The first analyzer command for the second cynara reproduction used an
   invalid audit-stdout destination under `/tmp`; no evidence or source was
   changed. The analyzer was rerun against the already accepted raw GBS log
   with the correct repository-local output path.

## E5 conclusion

Changes 41, 42, and 43 are closed without frozen-design or runtime changes.
E1-E4 and the two-case E6 scope are complete. The synthetic arc, recovery
window, edge guards, historical toolchain case, C++ rich-diagnostic
fingerprint, and real repair-to-verification chain all passed. RC is therefore
**complete and ready for RD close-out**. No Gerrit push, QuickBuild request, or
production source change was attempted.
