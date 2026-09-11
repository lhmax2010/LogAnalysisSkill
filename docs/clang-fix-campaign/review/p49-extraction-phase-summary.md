# P4.9 Extraction Phase Summary

This ledger covers the foundation and all six extracted skills. It is a
navigation and closure record, not a second authority; each FROZEN design and
its closeout remain authoritative for that batch.

## Batch Overview

| Batch | Frozen authority | Convergence range | Lifecycle anchors | Status |
|---|---|---|---|---|
| Step-0 shared foundation | `p49-step0-design-v2.1-FROZEN.md` | v1.0 through v2.1 | v2.0 freeze `698bd7c`; implementation `8dca6c1`/`ab58bfd`/`6def1ed`; v2.1 attribution update `95ed550`; closeout/sign-off `eb6438b`/`7e9eb4e` | CLOSED |
| Skill-1 convergence-judge | `p49-skill1-convergence-judge-design-v1.4-FROZEN.md` | v1.0 through v1.4 | initial freeze `d3478ab`; implementation `f4c8142`/`f7194ae`/`954bbcd`/`9bf1af0`; v1.4 attribution update `95ed550`; closeout/sign-off `e7900bb`/`d02a15a` | CLOSED |
| Skill-2 qb-discover | `p49-skill2-qb-discover-design-v1.3-FROZEN.md` | v1.0 through v1.3 | initial freeze `097294f`; v1.3/tool gate `95ed550`; extraction/gates `41152fe`/`812b213`; closeout/sign-off `90b90e4`/`57c04e2` | CLOSED |
| Skill-3 gerrit-fetch | `p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md` | v1.0 through v1.3.1 | freeze `4612167`; implementation `751e7b4`/`f4be9e4`/`f6544df`/`c41d15a`; closeout `1ca2206`; sign-off `92111c4` | CLOSED |
| Skill-4 build-verify | `p49-skill4-build-verify-design-v1.12.1-FROZEN.md` | v1.0 through v1.12.1 | A0/freeze `148b7f6`/`09da87d`; implementation `3da2529`/`f85bd58`/`da6d503`; closeout `7bfa070`; sign-off `8ed7588` | CLOSED |
| Skill-5 gerrit-submit | `p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md` | v1.0 through v1.3.2 | freeze/A0 `f2bc050`/`31a91cb`; implementation `a97c40b`/`0dfa5f1`/`a8620f1`; closeout/amendment `d51145f`/`c6f734b`; sign-off `81ada54` | CLOSED |
| Skill-6 triage-report | `p49-skill6-triage-report-design-v1.8-FROZEN.md` | v1.0 through v1.8 | freeze/A0 `bdb5a55`/`3dc0466`; implementation `3da12a4`/`2cc3dd3`/`dfbbf3b`; closeout `9a74c0b` | CLOSED |

All seven work batches (step-0 plus six skills) are CLOSED. The extraction work
is complete; no further extraction batch may be inserted as a way to postpone
the terminal work below.

## 阶段签批

- Step-0 and skills 1-5 retain their signed closeout anchors in the table above.
- Skill-6 is signed CLOSED at `9a74c0b`: Claude independently reproduced each
  clean-environment commit result and reran the `197+4` audits, four gate
  families, bridge `21/3`, and invariant branch inventory; reviewers A and B
  both returned CLOSED with zero findings. Two reviewers were the complete
  planned review set for this batch, not a missing-third-reviewer condition.
- **P4.9 抽取阶段：CLOSED（2026-09-11）。**

The next stage has exactly one permitted entry point: **the P4.9 terminal
batch**, consisting of the five items and terminal clause below.

## Extraction Outcome

- Seven installable roots now obey the orchestration > independent skills >
  shared dependency direction under six active import-linter contracts.
- The final symbol audit reports `197 SYMBOL OK + 4 MODULE-SCOPE OK`, with zero
  mismatch and zero incomplete. The independent bridge reports the same
  population with every difference class at zero.
- Every new package has packaging, CI mypy, and README source-tree entrypoints.
- Each migration retains a named compatibility shim until one-shot cleanup;
  behavioral parity was captured before shim convergence from skill-3 onward.
- The full regression baseline rose through additive coverage to
  `941 passed, 1 skipped`, with nodeid/function-set preservation checked at
  each ownership move.

## P4.9 Terminal Batch Ledger

| # | Blocking obligation | Required closure |
|---|---|---|
| 1 | Delete all legacy compatibility shims | One explicit final cleanup commit after behavior unification. First classify every caller/import as compatibility-shim use or real dependency and archive the evidence; if a real dependency is misclassified and removed as a shim, roll back. Then update callers and prove no legacy imports remain. |
| 2 | Narrow tests that consume implementation-private symbols | Keep private names out of package-root APIs; remove or relocate test-only access in the final cleanup. |
| 3 | Normalize dangling-symlink handling | Implement the frozen cross-skill outcome rather than preserving the current `FileExistsError` divergence. |
| 4 | Unify timeout, cancellation, interruption, residual state, and result mapping | Implement and validate every row of skill-5 frozen §3.2 across gerrit-fetch, gerrit-submit, and shared workspace paths. |
| 5 | Decide protected-marker write order | Design review must explicitly choose reorder or retain-with-rationale for `_verify_cleanup_handle -> _exclude_private_files -> marker write`; “recorded” is not a decision. |

**Terminal clause:** all five items must close within the P4.9 terminal work.
Any unfinished item blocks P4.9 closure and may not be deferred, transferred,
or silently relabeled. `EDIT_SPEC_SCHEMA` remains a named patch-suggest owner
item outside this five-entry terminal ledger. BoolOp per-operand obligations
remain a template-design question, not implementation debt.

## Methodology Index

| Method | Applied rule |
|---|---|
| ⑩ | Measure ownership cuts from real definitions, imports, calls, and complete public surfaces. |
| ⑪ | Give shared code an enforced downward internal layering rather than a flat namespace. |
| ⑫ | Make the body mechanically enumerable and bridge it independently to inventory. |
| ⑬ | Put integrity anchors outside the artifact; Git commits anchor reports and designs. |
| ⑭ | A guard exists only after its own positive and destructive negative runs. |
| ⑮ | Give each audit category a structural anti-abuse assertion. |
| ⑯ | Treat transitional states and delayed controls as debts with named promotion gates. |
| ⑰ | Move or retain the complete call, type-field, and data-source closure. |
| ⑱ | Require admission falsification for the gate and every registered item. |
| ⑲ | Keep the checked object, evidence artifact, and immutable Git anchor separate. |

Skill-6 adds four operational rules, recorded in
`dev_memory/methodology.md`: reverse-account every structured rewrite; admit
branch tables only through selector/ID/external-binding/closed-set checks;
derive first numeric declarations from the first real script run; and combine
multi-party review conclusions by intersection, never by optimistic union or
inference from unseen reviews.
