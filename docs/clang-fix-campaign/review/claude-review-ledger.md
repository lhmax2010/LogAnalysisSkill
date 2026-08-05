# Claude Review Ledger (Reconstructed)

## Provenance Warning

The remediation task states that an original ledger was delivered, but no
standalone ledger was present in the repository or available attachment tree
when RA ran. This file is therefore reconstructed only from machine-resident
`change_32.md` through `change_40.md`, Git commit metadata, and the P0 signature
audit. It is not a verbatim transcript and does not invent missing quotations.

## Review Rounds

| Change | Recorded review input | Material outcome |
|---|---|---|
| 32 | dual review, details retained in the change ledger | convergence uniqueness, evidence tuple integrity, checker work identified |
| 33 | external: 1 BLOCKER, 4 MAJOR, 1 MINOR; Claude: four execution gaps, 1 MAJOR, 2 MINOR | relink-before-orphan recovery; HELD precheck reachability; authority cleanup |
| 34 | external: 3 BLOCKER, 2 MAJOR; Claude: 4 MINOR | atomic reconciliation API; remove impossible compensation; recovery before precheck |
| 35 | external: 2 BLOCKER, 3 MAJOR, 1 MINOR; Claude: no new finding | per-round pairing; deterministic PASS payload reconstruction |
| 36 | external: 2 BLOCKER, 2 MAJOR, 1 MINOR; Claude review recorded in source | edit-spec based round attribution; unified group handling |
| 37 | external: 4 BLOCKER/MAJOR; Claude: 1 BLOCKER plus additional findings | ledger repair separated from current exit; impossible attribution treated as corruption |
| 38 | external: 1 BLOCKER, 3 MAJOR, 1 MINOR; Claude: 1 MINOR, 1 NIT | create-round authority restored before reconcile; A0 integrity precheck; fixed stdout schema |
| 39 | Codex stop-and-report; subsequent reviews recorded as v1-v3 revisions | executable API/index checker rules, prompt authority, signature audit requirement |
| 40 | Codex stop-and-report on checker contradiction; v2 closes prompt pointer conflicts | checker uses `compile`, exact prompt SHA gate, v1.5.16 freeze |

## Closure Evidence

- `review/p0-signature-audit-v1.5.16.md`: complete 45-item audit and independent
  high-risk signature PASS 4/4.
- `tools/check_design_doc.py --self-test`: 33/33 at P0.
- Frozen design and snapshot SHA:
  `ff73f5e3c6d54a75ae60771b98eadcfc1a4d1422ca8faf337a3de09eee4346ff`.
- Authoritative prompt SHA:
  `e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`.

## Outstanding Closure

This reconstructed ledger does not claim final three-way review of the code.
RB generates the self-contained packages for that review, and RD must close
BLOCKER/MAJOR findings before merge.
