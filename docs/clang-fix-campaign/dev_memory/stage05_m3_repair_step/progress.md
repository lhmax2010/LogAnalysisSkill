# Stage 05 Progress: M3 Repair Step

- Added `campaign_repair_step.py` and `previous_evidence.py`.
- Wired `campaign-repair-step` through `ci_triage.cli` and `python -m
  ci_triage`.
- Preserved create-round before reconciliation so an old edit-spec hash cannot
  bypass round identity.
- Made previous-evidence preflight append arch-scoped HELD before exit, keeping
  rebaseline reachable.
- Added post-build TOCTOU checks and fail-closed `n_a`/HELD recording.
- Fixed stdout to one JSON object with always-present `reconciliation` and
  `warnings`, structured non-empty entries, and deterministic ordering.
