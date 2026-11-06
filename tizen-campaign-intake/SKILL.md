---
name: tizen-campaign-intake
description: Validate campaign startup and register Clang units from local CI logs or a qb-discover manifest, preparing source clones. Use before baseline reproduction; this skill does not access QuickBuild, compile, or submit.
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
campaign-start-check validates configuration and read-only repository reachability.

## Discovery Handoff

First run authorized `tizen_qb_verify qb-discover` to obtain an immutable manifest.
Then consume that exact path with the same state root:

```bash
python -m tizen_campaign_intake campaign-discover --manifest "$DISCOVERY_MANIFEST" --state-root "$STATE_ROOT" --state-db "$STATE_DB" --config "$CONFIG" --dry-run
```

Remove --dry-run only with authorization to register the reported units and clone
their source. Schema, resolved paths and log hashes are checked before intake.
The default filter keeps compile failures; --include-non-compile is explicit.
Unknown architectures retain the existing arch gate. Output discover.json and
discover.md record every package; source-unresolved/unreadable packages are not
silently retried. This consumer runs only Git through SandboxGit and the local
Python gbs_analyzer, never a browser, Node, HTTP client or real gbs.

## Errors

- Exit 2: INVALID_ARGS.
- Exit 4: CAMPAIGN_STATE_BUSY, REJECTED_ARCH_NOT_ALLOWED,
  REJECTED_STATE_INCONSISTENT or REJECTED_IDENTITY_MISMATCH.
- Exit 5: INTAKE_ANALYZER_FAILED, INTAKE_CLONE_FAILED or WORKSPACE_FS_UNSUPPORTED.

Stop on rejection and retain the previous evidence for investigation.
