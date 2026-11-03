---
name: tizen-campaign-intake
description: Register a manually selected Clang campaign unit from a local CI log and prepare its source clone. Use before baseline reproduction; not for QuickBuild discovery, compilation, or submission.
---

# Tizen Campaign Intake

## Inputs

Use the campaign configuration, project, branch, spec name, base commit,
QuickBuild source build ID, failed page-name architectures and the primary CI log.
The configuration supplies campaign_workspace, gerrit_ssh_base, max_rounds and
max_build_invocations. Source identity must match the campaign unit.

## Command

```bash
python -m tizen_campaign_intake campaign-add-unit --state-db /work/state.db --config /work/campaign.yaml --project platform/upstream/example --branch tizen_base --spec-name example --base-commit <commit> --source-build-id <build-id> --failed-arches standard-aarch64 --ci-log /work/ci.log
```

## Outputs And Safety

JSON includes campaign_unit_key, primary_arch, failed_arches, ci_evidence_ref,
ci_evidence_sha256, src_clean, created and error_code. Evidence is published
without overwrite. The clone is staged, checked and marked before publication.
Same-input retries reuse existing evidence and validate existing source; do not
repair an identity mismatch manually or overwrite its evidence to force a retry.
The command clones read-only; it does not push, compile or access QuickBuild.
campaign-start-check remains reserved for batch 3, not implemented here.

## Errors

- Exit 2: INVALID_ARGS.
- Exit 4: CAMPAIGN_STATE_BUSY, REJECTED_ARCH_NOT_ALLOWED,
  REJECTED_STATE_INCONSISTENT or REJECTED_IDENTITY_MISMATCH.
- Exit 5: INTAKE_ANALYZER_FAILED, INTAKE_CLONE_FAILED or WORKSPACE_FS_UNSUPPORTED.

Stop on rejection and retain the previous evidence for investigation.
