# change_41:RC smoke evidence boundary and historical-input scope (CLOSED)

Status: **closed (no design change)**

Resolution: the frozen design and implementation already agree that
REPRODUCE/CONVERGENCE evidence is analyzer JSON. The contradiction was confined
to `e2e-smoke-runbook.md` v1. RC resumes under the v2 rules recorded in
`docs/clang-fix-campaign/review/rc-resolution.md`.

Triggered by: RC E0/E1 reality verification on 2026-08-05.

Scope: smoke protocol and test-input contract only. No runtime code change is
authorized by this proposal.

## A. Contradiction 1: raw GBS log is not convergence evidence

`e2e-smoke-runbook.md` E1 currently says that the captured GBS failure log is
both the CI-evidence substitute and the REPRODUCE baseline evidence, and that
`_primary_fingerprint` is computed against the real log.

The frozen implementation enforces a different type boundary:

1. `verify.convergence._primary_fingerprint` accepts an evidence dictionary;
2. `previous_evidence.resolve` SHA-verifies the bound evidence file, parses it
   as JSON, and requires a top-level object;
3. campaign tests seed REPRODUCE with an analyzer `evidence_packet/v1` JSON
   file, never a raw build log.

Passing the raw `.log` as written in the runbook deterministically fails closed
as `previous evidence is invalid JSON`. Converting it without changing the
runbook would be a silent protocol rewrite.

### 裁决

The existing implementation contract is authoritative. RC E1/E6 shall:

- retain every raw GBS log and SHA-256 as an immutable audit artifact;
- run `gbs_analyzer` against that log with the selected source root;
- retain and SHA-256 the resulting evidence packet JSON;
- bind REPRODUCE `evidence_local`/`evidence_sha256` to the evidence JSON;
- compute `_primary_fingerprint` on the parsed evidence packet;
- for E6, compare fingerprints from analyzer packets generated separately from
  the historical and fresh raw logs;
- keep the raw-log paths and hashes in the REPRODUCE `basis`/report so the
  derivation remains auditable.

Rejected alternative: teach convergence/previous-evidence to parse raw logs.
That duplicates analyzer ownership, enlarges the frozen API, and is unnecessary
because the analyzer already produces the required structured contract.

## B. Historical-input scope after resupply

At the original stop point `tmp/Verification/log/` was empty. The developer
subsequently supplied historical material and explicitly narrowed the
executable E6 scope:

- `multi-assistant.log` is the one historical case to execute after confirming
  package/root cause, source + packaging, and analyzer parseability;
- cynara supplies one E6' real-feeling C++ case under the three quality clauses
  in `rc-resolution.md`;
- an extra `united-servvice.log` is present, but no matching united-service
  source/packaging exists under `tmp/Verification/codes/`; it is therefore
  recorded as paused for missing inputs and is not fabricated into a case.

Any discovered case lacking source or real packaging remains a per-case pause,
not permission to create packaging. The report must preserve that distinction.

## C. Resumption gate (satisfied)

RC resumed at E1 after:

1. the raw-log-to-analyzer-JSON rule was accepted in `rc-resolution.md`;
2. E6 was explicitly re-scoped to one historical case plus one cynara E6'
   case, with missing-input cases paused;
3. RC reporting was required to identify raw-log and analyzer-JSON SHA-256
   values separately.

RD remains prohibited until the resumed RC is all-green or every resulting
deviation is explicitly adjudicated.
