# P4.9 Skill-3 Gerrit-Fetch Result

Status: **CLOSED**. Detailed DoD account:
`../../review/p49-skill3-closeout.md`.

Frozen authority:
`../../p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md`.

## Delivered

| Commit | Result |
|---|---|
| `4612167` | Finalized and froze the v1.3.1 design and history snapshot |
| `751e7b4` | Removed the two environment-sensitive test assumptions and established the clean 847/1 baseline |
| `f4be9e4` | Added import-binding attribution and its four assertion groups |
| `f6544df` | Extracted the unchanged Gerrit implementation with pre-shim parity and 36 new cases |
| `c41d15a` | Activated delivery entry points, import gates, 12-symbol audit coverage, and SKILL.md |

## Final Contract State

- `tizen_gerrit_fetch.gerrit` owns 12 frozen implementation symbols. The
  package root exports exactly four; the legacy shim preserves all 12 plus the
  three shared Gerrit types.
- Import-binding analysis now attributes module-scope `ImportFrom` uses by
  `(source module, source symbol, local name)`. Its real alias regression keeps
  `ci_triage.campaign_state` on public `primary_fingerprint`, not the private
  implementation name.
- This is the first real production use of the binary `(definition, symbol)`
  key: the Gerrit and shared/workspace `_run_git` twins remain independently
  registered and measure different consumer sets.
- Pre-shim parity compares four closed payload partitions on distinct module
  objects. Post-shim 12+3 identity is retained only as wiring evidence.
- The authoritative §5.1 table closes all 20 contract/branch/test rows. The
  dedicated skill file collects 38 tests.
- Six import contracts are green; three deliberate upward/sideways edges each
  fail with exit 1.
- Symbol audit and body bridge are green at 108 per-symbol entries plus four
  module scopes. Bridge output explicitly names all 12 skill-3 rows.
- Commit B established the new baseline: **883 passed, 1 skipped**. It preserves
  all 848 existing tests: 846 nodeids are unchanged and two moved from
  `test_ci_triage.py` to `test_gerrit_fetch.py` under section 5.3 with
  byte-identical function bodies. It adds 36 cases.

## Methods Applied

- Import-binding fixtures include a non-degenerate aliased name and an old-
  implementation red result, so the change has an existence proof.
- Baseline acceptance compares test-set membership before totals.
- Parity masking is limited to named path-bearing fields; one positive and
  three negative samples demonstrate both effectiveness and restraint.
- Exact function-count probes include syntactic boundaries and are executed
  against the current repository before becoming evidence.
- A green bridge must print the changed authority's rows; a summary alone is
  not accepted.

## Downstream Inputs

1. Revisit same-name helper consolidation in the `triage-report` extraction.
2. Remove every legacy compatibility shim in the one-shot P4.9 final cleanup.
   For Gerrit types, delete only the three re-exports in
   `ci_triage/gerrit.py`; retain
   `tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:14-16`, which are
   real signature dependencies. Their inherited `P4.9 shim` comments may be
   corrected in that cleanup commit because the wording is stale in the skill
   copy, but the imports must remain.
3. In the `gerrit-submit` batch, design dangling-symlink normalization.
4. In the `gerrit-submit` batch, jointly design timeout/cancellation,
   interruption cleanup, and error normalization for Gerrit external calls.
