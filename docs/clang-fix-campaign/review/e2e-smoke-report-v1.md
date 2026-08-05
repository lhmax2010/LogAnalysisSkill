# E2E Smoke Report v1: RC resumed under runbook v3

Date: 2026-08-05 (Asia/Shanghai)

Branch: `clang-fix-campaign`

Code under test: `269321820abe0eddb7db345dcb26ffaedc7127c6`
(`checkpoint/p45_code_ready`)

Result: **IN PROGRESS -- change_42 adjudicated, resuming at E1 unit seed**

This report follows the frozen stop-and-report protocol. No runtime code or
frozen design text was changed to accommodate the discrepancies below. The
initial evidence/input stop was adjudicated by `rc-resolution.md` and closed in
change_41; RC then resumed at E1 and stopped again before unit seeding when the
runbook's architecture argument was proven incompatible with the public CLI.

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
buildroot: /home/linhao/Toolchain/development/LogAnalysisSkill/tmp/GBS-ROOT-TIZEN-UNIFIED-LLVM
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
| cynara | `611ff2ecc979bbd9d269e2bc7eb227a895055667` | `packaging/cynara.spec` | clean, branch `tizen` |
| libtpl-egl | none | none | empty initialized Git repository; no commit or source |

Per RC/E6, `libtpl-egl` is therefore a required skip. No packaging was
fabricated.

### Clean zlib baseline

Canonical rerun command:

```bash
cd /home/linhao/Toolchain/development/LogAnalysisSkill/tmp/Verification/codes/zlib
/usr/bin/time -f '\nWALL_SECONDS=%e\nMAX_RSS_KB=%M' \
  gbs -c /home/linhao/Toolchain/development/LogAnalysisSkill/tmp/gbs_llvm.conf \
  build -A armv7l --include-all 2>&1 | \
  tee /home/linhao/Toolchain/development/LogAnalysisSkill/tmp/campaign-smoke/logs/E0-zlib-clean-baseline.log
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

## Execution matrix

| Stage | Result | Notes |
|---|---|---|
| E0 GBS/toolchain | PASS | Real armv7l LLVM 22.1.8 chroot confirmed |
| E0 clean baseline | PASS | zlib built successfully; canonical log captured |
| E1 raw failure + analyzer | PASS | Real GBS exit 1; analyzer JSON and separate hashes captured |
| E1 unit seed | PENDING | change_42 closed; resumes under audited v3 command |
| E2 repair arc | PENDING | Starts after the resumed E1 unit seed succeeds |
| E3 crash recovery | NOT RUN | Depends on a valid seeded unit |
| E4 edge cases | NOT RUN | Depends on a valid seeded unit |
| E6 historical cases | NOT RUN | Deferred by the E1 stop; resumed scope and inputs are recorded |
| RD close-out/PR | NOT ENTERED | RC is not all-green and deviations are not adjudicated |

## Reality observations

- Canonical clean build wall time: 48.13 seconds.
- Canonical clean build max RSS: 136436 KiB.
- Current `tmp/campaign-smoke` size after the resumed E1 work: 352 KiB.
- Source sizes: zlib 9.3 MiB, cynara 4.1 MiB, libtpl-egl 5.5 MiB,
  multi-assistant 1.4 MiB.
- Campaign state DB/workspace: not created, because the E1 architecture gate
  was found before unit seeding.

## Required adjudication

Evidence/input adjudication is closed in change_41 and architecture-input
adjudication is closed in change_42. The authoritative smoke procedure is now
the v3 header and corrected command in `e2e-smoke-runbook.md`.

RC resumes from E1 unit seeding using the already captured raw log and analyzer
JSON hashes. Later reality/design differences remain subject to the unchanged
stop-and-report protocol.
