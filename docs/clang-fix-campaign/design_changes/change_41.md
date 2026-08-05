# change_41:RC smoke evidence boundary and missing historical inputs (PROPOSED)

Status: **adjudication required; not applied to frozen design**

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

### Proposed裁决

Adopt the existing implementation contract and revise RC E1/E6 as follows:

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

## B. Contradiction 2: required historical logs are absent

The remediation task states that `tmp/Verification/log/` contains historical
real bug logs. On the target host the directory exists but is empty. The three
source entries are:

- zlib: source + Git commit + packaging present;
- cynara: source + Git commit + packaging present;
- libtpl-egl: empty initialized Git repository, no commit, source, or packaging.

E6's same-root-cause and historical/fresh fingerprint assertions cannot be
executed without the historical logs. The logs cannot be inferred or recreated
without defeating the purpose of that test.

### Required input裁决

Choose one explicitly before RC resumes:

1. supply the intended historical logs under `tmp/Verification/log/`, with an
   unambiguous mapping to source package; or
2. amend the E6 case inventory to the artifacts actually available and mark
   historical comparison as blocked/waived by the developer.

`libtpl-egl` remains a protocol-defined skip unless a real source tree and real
packaging are supplied. Packaging must not be fabricated.

## C. Resumption gate

RC may resume at E1 only after:

1. the raw-log-to-evidence-JSON rule is accepted and written into the runbook;
2. historical logs are supplied or E6 is explicitly re-scoped;
3. the updated text identifies which SHA-256 belongs to the raw log and which
   belongs to the analyzer evidence JSON.

RD remains prohibited until the resumed RC is all-green or every resulting
deviation is explicitly adjudicated.
