# Patch-suggest Source Candidate Fix-all Roadmap

**Status**: Frozen staged route and Phase 0/1 boundary.
**Date**: 2026-06-09
**Scope**: This document freezes the staged direction for moving patch-suggest
from three trigger-specific modes to a file-oriented coverage framework. It does
not freeze the final Phase 2 implementation shape; that must wait for Phase 1.5
observation data.

## Trigger

The current patch-suggest behavior is split across three modes:

- single: handles `primary_error`.
- cluster: handles large-scale repeated source warning clusters.
- multi-candidate: handles two or more independent terminal candidates.

This creates coverage gaps when analyzer exposes diagnostics outside the mode
trigger boundaries. A real `inference-engine` build showed:

- `primary_error`: `E011` unused-field in `OutputMetadata.h`.
- `CL001`: seven deprecated Werror diagnostics across `profiler.cpp` and
  `tc.cpp`, with `large_scale=false`.
- `root_cause_candidates`: only `E011`.

The old path fixed only `E011`; the seven deprecated diagnostics were visible in
analyzer cluster data but were not handled because the cluster was not
large-scale and multi-candidate mode did not trigger.

## Phase 0. Honest Goal and Naming

### D0.1. Target wording

The target is:

> patch-suggest prepares patches by file for analyzer-exposed structured source
> diagnostic candidates.

This deliberately does not claim raw build-log completeness. If analyzer's
scanner does not recognize a raw diagnostic, patch-suggest cannot see it.

This also does not claim that every candidate is certainly fixable. Fixability
is provisional until analyzer grows a stronger taxonomy.

### D0.2. Sidecar naming

Use `source_candidate` terminology for the new analyzer output. Do not call it
`all_fixable` yet.

Rationale: naming is a contract. `source_candidate` says the diagnostic is
structured, source-located, and potentially relevant for patch-suggest. It does
not over-promise raw log coverage or guaranteed fixability.

When fixability taxonomy matures, naming may be upgraded in a later release.

## Phase 1. Analyzer Additive Source Candidate Sidecar

### D1.1. Additive boundary

Analyzer adds a sidecar containing the complete set of structured source
diagnostic candidates it can expose. This is additive.

Do not change:

- `primary_error`
- `root_cause_candidates`
- ranking
- verdict
- evidence collectors
- patch-suggest behavior
- workflow behavior

The main Evidence Packet contains only a compact summary and a relative sidecar
path. Full candidate locations live in the sidecar and are not truncated by the
packet token budget.

### D1.2. Candidate fields

Each sidecar candidate includes:

- `event_id`
- `kind`
- `file`
- `normalized_file`
- `line`
- `column`
- `message`
- `warning_option`
- `semantic_class`
- `command_id`
- `line_no`
- `source_located`
- `parent`
- `cascade_status`
- `provisional_fixability`
- `fixability_reason`
- `exclusion_reason`
- `dedupe_key`

Fields may be omitted only when truly unavailable. Missing data must be visible
through `source_located`, `provisional_fixability`, or `exclusion_reason` rather
than silently disappearing.

### D1.3. Source-located source diagnostic scope

Eligible source diagnostic event kinds are:

- `compiler`
- `werror`

The event must also pass the severity gate:

- strong signal: `severity == "error"`, recorded as
  `detection_source="severity"`;
- strong signal: `kind == "werror"`, recorded as
  `detection_source="kind"`;
- fallback signal: message contains `-Werror`, recorded as
  `detection_source="werror-message-fallback"`.

Prefer strong signals. The message fallback is intentionally weaker because raw
text may mention `-Werror` in explanatory context. Keeping `detection_source`
makes the fatal-build decision auditable in observation reports and sidecars.

Plain compiler warnings must not enter the sidecar. They can pollute coverage and
fixability statistics but do not represent fatal build failures.

The event must have usable `file` and positive `line` values to be considered
source-located. Non-source-located fatal diagnostics may be counted in scanner
coverage observation, but they are not patch-suggest source candidates.

### D1.4. Explicit cascade handling only

Only events with an explicit `parent` are excluded as cascades.

Events without `parent` are included as coverage candidates, even if they may
look like cascades by message pattern or proximity.

Weak cascade heuristics may be recorded as annotations, but must not drop a
candidate. Missing a real independent diagnostic is more harmful than listing an
extra candidate for review.

### D1.5. Provisional fixability taxonomy

Analyzer assigns a conservative `provisional_fixability`:

- `probably_fixable`
- `unknown`
- `not_fixable`

This is intentionally provisional. Most uncertain cases should be `unknown`, not
forced into `probably_fixable`.

Initial `probably_fixable` requires all of:

- source-located `compiler` or `werror`
- severity-gated fatal source diagnostic per D1.3
- no explicit parent
- project-source path according to the path heuristics in D1.7
- one positive migration signal from D1.6, such as a whitelisted warning option,
  semantic class, or explicit message pattern

If analyzer cannot determine source ownership, generation status, or warning
semantics, use `unknown`.

### D1.6. Initial warning-option whitelist

Initial `probably_fixable` warning options are limited to source migration cases
already seen in Tizen patch-suggest work.

Implementation must use analyzer-normalized warning option strings observed in
real logs or fixtures. Do not rely only on expected spelling. For example,
`-Wunused-field` and `-Wunused-private-field` must be confirmed against actual
analyzer extraction before they become test assertions.

- `-Wdeprecated-declarations`
- `-Wimplicit-enum-enum-cast`
- `-Wpointer-bool-conversion`
- `-Winconsistent-missing-override`
- `-Wunused-private-field`
- `-Wunused-field`

The whitelist is intentionally narrow. It may be expanded only with real-world
evidence and tests.

`unused-field` diagnostics are explicitly in scope for the `inference-engine`
gold case. They must be able to reach `probably_fixable` either through a
confirmed warning option such as `-Wunused-private-field` or through an explicit
semantic/message rule that recognizes unused-field diagnostics. Otherwise the
gold case would be internally inconsistent: `E011` would be counted as a source
candidate but would not receive a per-file skeleton.

Diagnostics without concrete warning options are not automatically
`probably_fixable`; classify them by other explicit rules only when the rule is
tested and source-owned. Otherwise leave them `unknown`.

Phase 1 must add warning-option extraction for every source diagnostic event,
not only for events inside `error_clusters`. The existing cluster extractor can
be reused, but the sidecar candidate must expose `warning_option` for singleton
and non-cluster diagnostics too.

### D1.7. Path ownership heuristics

Path heuristics are conservative:

- Treat source paths under the user source root as project source.
- Exclude system or external paths such as `/usr/include`, `/usr/lib`,
  `/opt/toolchain`, and other absolute toolchain roots.
- Mark paths containing generated or vendored indicators as `unknown` unless
  explicitly proven project-owned. Examples:
  - `generated`
  - `gen`
  - `third_party`
  - `external`
  - `vendor`

`GBS-ROOT` needs special handling in Tizen builds. The string `GBS-ROOT` by
itself is not evidence of generated or vendored code. GBS build logs often point
to package build roots such as:

```text
/home/abuild/rpmbuild/BUILD/<pkg-version>/...
```

or local GBS roots. Files under `BUILD/<pkg-version>` may map back to the user's
project source tree and should be treated as project-owned when suffix/source-root
resolution proves the mapping. Do not mark a candidate `unknown` merely because
the raw build path contains `GBS-ROOT` or a build-root prefix.

If the package BUILD-root to source-root mapping cannot be established, use
`unknown`, not `not_fixable`.

These heuristics are not proof of fixability. They exist to avoid confidently
patching third-party, generated, or toolchain-owned code.

### D1.8. Dedupe key

Use a detailed dedupe key, not only `file:line:message`.

The key must include:

- `normalized_file`
- `line`
- `column`
- `warning_option` or `semantic_class`
- message fingerprint
- `command_id`
- `kind`

Rationale: the same source line may carry multiple diagnostics, the same message
may appear across files, and the same file may be compiled by multiple commands.

Missing optional components must use explicit sentinels rather than disappearing
from the key:

- `column=<unknown>`
- `warning_option=<none>`
- `semantic_class=<unknown>`
- `command_id=<unknown>`

If any key component uses a sentinel, set `degraded_key=true` on the candidate.
This prevents accidental key shortening from merging unrelated diagnostics while
still making degraded identity visible.

## Phase 1.5. Observation Mode

### P1.5.1. Purpose

Before changing patch output behavior, analyzer or patch-suggest must produce
coverage observations that compare old mode coverage with the new source
candidate sidecar.

This phase is data gathering. It does not change generated patch contexts.

### P1.5.2. Coverage diff fields

The observation report records:

- `sidecar_diagnostics`
- `old_path_covered`
- `missed_by_old`
- `extra_by_old`

This makes cases like `inference-engine` measurable: the old path covers `E011`
but misses the non-large-scale deprecated cluster locations.

### P1.5.3. Scanner coverage gap

Observation also records scanner coverage signals:

- raw diagnostic-like line count
- structured event count
- unmatched diagnostic-like line samples
- unmatched categories when inferable

This separates analyzer scanner gaps from patch-suggest consumption gaps. If a
raw diagnostic-like line is not converted into a structured event, it is an
analyzer coverage issue, not a patch-suggest issue.

### P1.5.4. Data gates

Run observation on:

- `inference-engine` gold case
- `515/525` Werror case
- `bt` large repeated diagnostic case
- `libscl-ui`
- `ffmpeg`
- `appcore-agent` multi-candidate case

Phase 2 shape is not finalized until this observation shows acceptable coverage
and unknown/not-fixable rates.

Observation must also report `unknown_by_reason`, including counts for at least:

- source ownership or path mapping cannot be determined
- no concrete warning option
- suspected generated/vendor/third-party path
- no matching fixability rule
- missing structured location

This replaces a subjective "unknown rate is too high" interpretation with
diagnosable reasons. A high unknown count may be acceptable if it reflects
reasonable conservatism, and blocking if it shows the rules are too narrow for
known migration cases.

Phase 2 is blocked if any of these are true:

- `inference-engine` does not expose the expected eight structured source
  candidates.
- `missed_by_old` does not show the seven deprecated diagnostics from the old
  path gap.
- scanner coverage shows obvious Werror-promoted diagnostics that were not
  converted into structured events.
- `unknown_by_reason` shows known migration cases falling into unknown because
  of missing warning-option extraction, missing path mapping, or missing
  fixability rules.
- the sidecar lacks the fields needed for file grouping, dedupe, or provenance.

## Phase 2. Experimental Patch-suggest Fix-all by File

### D2.1. Experimental boundary

Patch-suggest consumes the analyzer sidecar, groups candidates by file, and
prepares per-file patch context.

This mode is experimental and coexists with the old single, cluster, and
multi-candidate paths until Phase 3 validates behavior.

### D2.2. Coverage rules

`large_scale` controls display and token strategy only. It must not decide
coverage.

Non-large-scale clusters and standalone source candidates are eligible if they
are present in the source candidate sidecar.

### D2.3. Fixability routing

- `probably_fixable`: may receive edit-spec skeletons and patch-generation
  guidance.
- `unknown`: listed in overview for human/assistant review, but does not
  automatically receive patch skeletons.
- `not_fixable`: listed as excluded with reason.

Patch count in Phase 2 means the number of file groups containing at least one
`probably_fixable` candidate. `unknown` candidates do not count toward patch
count until the taxonomy or user review upgrades them.

### D2.4. Per-file rendering reuse

Phase 2 should reuse the cluster per-file rendering concepts:

- per-file contexts
- source windows
- edit-spec skeletons
- one file, one patch
- truncation controls
- process one file at a time

Old assumptions to remove:

- same-kind cluster boundary
- `large_scale` trigger
- `cluster_id` as the coverage boundary
- `count >= 3` as a patch-suggest trigger

## Phase 3. Validation and Convergence

### D3.1. Inference-engine gold case

Add a real `inference-engine` fixture before convergence.

Required assertions:

- structured source candidate count is 8:
  - `E011` unused-field
  - seven deprecated Werror diagnostics
- `probably_fixable` count is 8 after the Phase 1 taxonomy recognizes both the
  unused-field diagnostic and the seven deprecated Werror diagnostics.
- file groups count is 3:
  - `OutputMetadata.h`
  - `profiler.cpp`
  - `tc.cpp`
- patch count is 3:
  - one patch for `OutputMetadata.h`
  - one patch for `profiler.cpp`
  - one patch for `tc.cpp`
- `CL001` with `large_scale=false` is still covered.
- `E011` receives a per-file edit-spec skeleton for `OutputMetadata.h`.
- Coverage does not depend on continuous event numbering. Use the real event id
  set from the fixture.
- `root_cause_candidates` containing only `E011` must not hide deprecated
  cluster locations.

### D3.2. Historical regression cases

Before retiring old modes, verify no coverage regression on:

- `515/525` Werror case
- `bt` large repeated diagnostic case
- `libscl-ui`
- `ffmpeg`
- `appcore-agent` multi-candidate case

Assertions should move from "which mode triggered" toward:

- diagnostic coverage
- file grouping
- per-file context count
- edit-spec skeleton count
- patch count

## Non-goals

- Do not claim raw log completeness.
- Do not call the sidecar `all_fixable` in this phase.
- Do not drop candidates by weak cascade heuristics.
- Do not make `large_scale` a coverage gate.
- Do not remove old single/cluster/multi paths before observation and
  validation.

## Frozen Gates

The frozen gates for the next implementation work are:

1. Naming remains honest: `source_candidate`, not `all_fixable`.
2. Analyzer sidecar is additive and does not affect primary/ranking/verdict.
3. Cascade exclusion is explicit-parent only.
4. Fixability is provisional and conservative.
5. Scanner coverage observation comes before patch output behavior changes.
6. Phase 2 remains experimental until Phase 1.5 data validates the final shape.
