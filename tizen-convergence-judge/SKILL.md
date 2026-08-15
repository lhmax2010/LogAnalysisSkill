---
name: tizen-convergence-judge
description: Compare current and previous analyzer Evidence Packet data to decide whether a source-repair iteration advanced, stalled, or regressed. Use only for convergence decisions between two analyzer evidence states; do not use it for failure classification, denied decisions, build-log parsing, patch generation, compilation, or submission.
compatibility: Requires Python 3.10 or newer and analyzer Evidence Packet JSON shaped for ci-triage convergence checks.
---

# Tizen Convergence Judge

Use this skill after a repair attempt has produced new analyzer evidence and the
workflow must decide whether another source-edit iteration is justified.

## Inputs

- Current analyzer evidence as a JSON object.
- Previous evidence, normally the preceding iteration and the baseline evidence
  for the first repair iteration. It may be `null` only when no baseline exists.
- Optional touched-file paths from the build-verify result.

The skill does not read raw build logs and does not classify whether a failure is
repairable. A denied or confirmation-required decision belongs to the failure
classifier before convergence is evaluated.

## Outputs

`check_convergence` returns `ConvergenceResult` with a verdict of `advance`,
`stalled`, or `regressed`, plus confidence, reason, fingerprints, error counts,
and touched-file availability. `write_convergence_result` writes that result as
deterministic JSON when explicit file output is requested.

## Errors

- Malformed evidence objects may raise normal Python type or value errors from
  the convergence API.
- `touched_files_from_json` raises `ValueError` when the file is not the expected
  JSON object with a list of non-empty string paths.
- File read and write failures propagate to the caller; the skill does not hide
  them or convert them into a convergence verdict.

## Idempotency

`check_convergence` is pure and deterministic for identical inputs. Its only
supported side effect is the caller's explicit use of
`write_convergence_result`, which replaces the requested output with the same
serialized result for the same input.
