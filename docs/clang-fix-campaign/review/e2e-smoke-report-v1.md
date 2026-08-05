# E2E Smoke Report v1: stopped at RC input-contract gate

Date: 2026-08-05 (Asia/Shanghai)

Branch: `clang-fix-campaign`

Code under test: `269321820abe0eddb7db345dcb26ffaedc7127c6`
(`checkpoint/p45_code_ready`)

Result: **STOPPED -- adjudication required before E1**

This report follows the frozen stop-and-report protocol. No runtime code or
frozen design text was changed to accommodate the two discrepancies below.
E1-E6 and RD were not entered after the discrepancies were confirmed.

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

## Stop condition 1: raw log versus evidence JSON

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

Silently running the analyzer and substituting its JSON output would be a
reasonable future protocol, but doing so here would change the written smoke
contract. Per the frozen protocol, it requires adjudication first.

## Stop condition 2: historical logs are absent

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

This is missing required test input, not a product failure. It cannot be
reconstructed from the source trees without inventing evidence.

## Execution matrix

| Stage | Result | Notes |
|---|---|---|
| E0 GBS/toolchain | PASS | Real armv7l LLVM 22.1.8 chroot confirmed |
| E0 clean baseline | PASS | zlib built successfully; canonical log captured |
| E1 seed/baseline | NOT RUN | Blocked by raw-log/evidence-JSON contract mismatch |
| E2 repair arc | NOT RUN | Must not consume an unadjudicated baseline contract |
| E3 crash recovery | NOT RUN | Depends on a valid seeded unit |
| E4 edge cases | NOT RUN | Depends on a valid seeded unit |
| E6 historical cases | NOT RUN | Historical logs absent; libtpl-egl also lacks source/packaging |
| RD close-out/PR | NOT ENTERED | RC is not all-green and deviations are not adjudicated |

## Reality observations

- Canonical clean build wall time: 48.13 seconds.
- Canonical clean build max RSS: 136436 KiB.
- Current `tmp/campaign-smoke` size after E0: 116 KiB.
- Source sizes: zlib 9.3 MiB, cynara 4.1 MiB, libtpl-egl 124 KiB.
- Campaign state DB/workspace: not created, because stopping before E1 avoids
  leaving a misleading partially seeded campaign.

## Required adjudication

See `docs/clang-fix-campaign/design_changes/change_41.md`.

The recommended resolution is to make the evidence boundary explicit:
preserve raw logs as immutable audit artifacts, run the existing analyzer on
them, and bind the resulting evidence JSON to REPRODUCE/convergence. Historical
and fresh comparisons should compare fingerprints of their analyzer evidence
packets. The missing historical logs must be supplied, or E6's expected case
set must be explicitly amended.

Until both points are adjudicated, this RC result is **stopped**, not failed and
not waived.
