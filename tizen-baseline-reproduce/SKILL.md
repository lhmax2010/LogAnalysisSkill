---
name: tizen-baseline-reproduce
description: Reproduce a registered campaign unit's CI failure in an isolated baseline copy. Use before repair rounds, primary architecture first. Not for editing patches, sandbox pushes or QuickBuild operations.
---

# Tizen Baseline Reproduce

## Inputs

Use the registered unit key, intact intake source, matching base commit/spec/profile,
campaign configuration, configured Clang build configuration and architecture.
The unit's stored CI evidence path and hash are authoritative. An optional
evidence-ci must match both. Run the primary architecture before the other two.

## Command

```bash
python -m tizen_baseline_reproduce baseline-reproduce --campaign-unit-key '<unit-key>' --state-db /work/state.db --config /work/campaign.yaml --src-clean /work/source --base-commit <commit> --gbs-conf /work/clang.conf --package example --arch standard-aarch64 --profile clang --output-dir /work/baseline/aarch64
```

## Outputs

JSON reports matched, different_failure or baseline_pass, local evidence/hash,
configuration hash, build log and reproduction basis. Compilation uses the
existing GBS runner and analyzer, not build-verify. Baseline copies are cleaned
in finally; keep-copy is a debugging option, not a protected verification copy.
Only three recorded architectures with a matched primary establish
BASELINE_REPRODUCED. A secondary baseline_pass provides a synthetic zero-error
evidence file. Baseline runs do not consume repair build budgets.

## Errors And Boundaries

- Exit 2: invalid or mismatching CLI/configuration inputs.
- Exit 4: NOT_REPRODUCED for a non-matched primary;
  REJECTED_PRIMARY_BASELINE_MISSING, REJECTED_CI_EVIDENCE_MISMATCH,
  REJECTED_IDENTITY_MISMATCH, REJECTED_UNIT_ABANDONED or CAMPAIGN_STATE_BUSY.
- Exit 5: BASELINE_TOOLING_FAILED.

Do not bypass an abandonment barrier or alter evidence anchors. This command
does not implement rebaseline, push to Gerrit, or access QuickBuild.
