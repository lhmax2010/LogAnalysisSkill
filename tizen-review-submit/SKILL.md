---
name: tizen-review-submit
description: Publish an authorized campaign unit to Gerrit review only after bound local verification and first-party QuickBuild PASS evidence. Use for review-submit, not sandbox pushes, manual result fabrication, or QuickBuild triggering.
---

# Tizen Review Submit

## Inputs

Three linked verification IDs for one final unit round, state database, campaign
configuration, the result JSON produced by qb-result-fetch, and refs/for/<branch>.
The branch must equal the unit branch. Confirm authorization for the external
review push before running the command.

```bash
python -m tizen_review_submit review-submit --verification-ids "$VERIFICATION_IDS" --state-db "$STATE_DB" --config "$CONFIG" --qb-result "$QB_RESULT" --review-target "$REVIEW_TARGET"
```

## Gates And Outputs

The command holds the sandbox/three repair locks through REVIEW recording. An
abandonment barrier rejects before copy checks. It revalidates aggregation, the
latest QB RESULT and raw file hash, bound edit bytes, suppression policy, review eligibility and
TOCTOU before pushing the derived commit with the cached hook Change-Id.
Only generated/suppress sources are accepted; suppress is never review eligible.

Stdout is JSON with action/status/error_code/message, review_url, qb_event_id,
change_id, derived_commit_sha, snapshot_used and snapshot_drift_accepted. A missing
Gerrit change URL is null and explained in the unit's review-trace.jsonl.

## Errors And Idempotency

Exit 0 means pushed/already_pushed; 2 means invalid arguments; 4 is a gate/lock
refusal; 5 is a tooling or push failure. A pending latest request includes its ID
and a fixed recovery message. No manual-result fallback or manual push printing
exists. Do not replace missing or damaged evidence by hand. The same derived
commit and Change-Id are reused for retry. Release worktrees only through the
campaign lifecycle commands after their state permits it.
