# Analyzer Error Clusters — Design Decision

**Status**: Proposed frozen design for review.
**Date**: 2026-06-04
**Trigger**: Real `capi-network-bluetooth` build log contained 57
`-Wimplicit-enum-enum-cast` errors across 11 files plus
`too many errors emitted`. The analyzer only surfaced `primary_error` plus
Top-K candidates, which led downstream patching to fix only a few locations.

## Goal

Add a compact, factual group view for large repeated source diagnostics without
changing existing root-cause behavior.

The analyzer must continue to expose:

- `primary_error`: one representative Top-1 root cause.
- `root_cause_candidates`: existing Top-K ranked candidates.

The new `error_clusters` view is additive. It tells users and downstream skills
when the log contains a repeated class of source diagnostics, how large it is,
which files are involved, and whether compiler output was truncated.

## D1. Packet Schema

When at least one cluster passes the emit threshold, `evidence_packet.json`
gets a new top-level field:

```json
{
  "error_clusters": {
    "schema_version": "error_clusters/v1",
    "truncated": true,
    "truncation_signals": [
      {
        "line_no": 1234,
        "message": "fatal error: too many errors emitted, stopping now"
      }
    ],
    "full_locations_path": "error_clusters.json",
    "clusters": [
      {
        "id": "CL001",
        "kind": "source_warning_option",
        "diagnostic_kinds": ["werror"],
        "warning_option": "-Wimplicit-enum-enum-cast",
        "count": 57,
        "file_count": 11,
        "files": [
          "device/foo.c",
          "common/bar.c"
        ],
        "locations_sample": [
          {
            "event_id": "E001",
            "file": "device/foo.c",
            "line": 10,
            "column": 5
          }
        ],
        "locations_truncated": true,
        "advisory": "Large repeated source diagnostic cluster. Patching only the primary error is likely incomplete; consider a class-wide fix strategy.",
        "large_scale": true
      }
    ]
  }
}
```

Field definitions:

- `schema_version`: fixed string, `error_clusters/v1`.
- `truncated`: `true` if the build log contains compiler truncation signals.
- `truncation_signals`: up to 5 raw signal summaries. Empty list if none.
- `full_locations_path`: relative path to sidecar `error_clusters.json` when
  clusters are emitted.
- `clusters`: compact summaries.

Cluster fields:

- `id`: stable local id, `CL001`, `CL002`, ...
- `kind`: fixed `source_warning_option` for v1.
- `diagnostic_kinds`: sorted unique event kinds in the cluster, e.g.
  `["compiler", "werror"]`.
- `warning_option`: canonical warning option key, e.g.
  `-Wimplicit-enum-enum-cast`.
- `count`: number of matching diagnostic events.
- `file_count`: number of distinct source files.
- `files`: at most 20 files, ordered by first occurrence in the log. If
  `file_count > len(files)`, the list is implicitly truncated.
- `locations_sample`: at most 10 representative locations.
- `locations_truncated`: `true` if `count > len(locations_sample)`.
- `advisory`: factual warning about repeated diagnostics. It must not prescribe
  a specific code fix.
- `large_scale`: threshold result from D3.

## D2. Cluster Key Rules

Only source diagnostics are eligible:

- `kind == "compiler"`
- `kind == "werror"`

Only diagnostics with a concrete warning option are clustered in v1.

Warning option extraction:

1. Search the event `message` for bracketed warning flags, for example:
   `[-Werror,-Wimplicit-enum-enum-cast]`.
2. Split the bracket content by comma.
3. Keep tokens beginning with `-W`.
4. Ignore the generic promotion flag `-Werror`.
5. The first remaining warning option is the cluster key.

Examples:

| Message suffix | Cluster key |
|---|---|
| `[-Werror,-Wimplicit-enum-enum-cast]` | `-Wimplicit-enum-enum-cast` |
| `[-Wpointer-bool-conversion]` | `-Wpointer-bool-conversion` |
| `[-Werror]` | no cluster |
| no bracketed warning option | no cluster |

No-option diagnostics are intentionally not clustered in v1. In particular:

- `-Werror` without a concrete warning option is not enough.
- Generic compiler errors without a warning option are not clustered by
  `semantic_class`.

Rationale: semantic-class grouping risks merging unrelated compiler errors. The
real large-scale cases motivating this feature are clang/GCC warning-option
migrations where the option is the stable class key.

## D3. Thresholds

Emit threshold:

- Emit a cluster only when `count >= 3`.
- If no cluster reaches `count >= 3`, omit the top-level `error_clusters` field
  unless a truncation signal exists.

Large-scale threshold:

- `large_scale = true` when `count >= 10` OR `file_count >= 3`.
- Otherwise `large_scale = false`.

Representative locations:

- `locations_sample` contains up to 10 events.
- Selection is deterministic:
  1. first occurrence per file, in build-log order, until the sample reaches 10;
  2. then earliest remaining events in build-log order until the sample reaches
     10.

Files:

- `files` contains up to 20 distinct files ordered by first occurrence.

Rationale:

- `count >= 3` avoids clutter for ordinary one-off and two-off diagnostics.
- `count >= 10` or `file_count >= 3` catches cases where individual patching is
  likely incomplete.
- Sample size 10 gives enough evidence without threatening the 1800-token target.

## D4. Sidecar Strategy

When `error_clusters` is emitted, the analyzer also writes
`error_clusters.json` in the analyzer output directory.

The packet stores only cluster summaries and `locations_sample`. The sidecar
stores full per-location data for each emitted cluster:

```json
{
  "schema_version": "error_clusters_locations/v1",
  "clusters": [
    {
      "id": "CL001",
      "warning_option": "-Wimplicit-enum-enum-cast",
      "locations": [
        {
          "event_id": "E001",
          "kind": "werror",
          "file": "device/foo.c",
          "line": 10,
          "column": 5,
          "line_no": 200,
          "message": "implicit conversion from enumeration type ..."
        }
      ]
    }
  ]
}
```

`full_locations_path` in the packet points to this sidecar. The sidecar is for
humans or downstream tools that explicitly need the full list. It is not part of
the default Claude-facing markdown unless a later design explicitly opts in.

## D5. Token Budget

`error_clusters` summary is part of the Evidence Packet and therefore counts
toward the packet token budget.

`error_clusters.json` sidecar does not count toward `token_budget.used` because
it is not embedded in the packet or `evidence_packet.md`.

Token control rules:

- packet cluster summaries cap `files` at 20 and `locations_sample` at 10;
- full location lists live only in the sidecar;
- if final packet truncation is needed, existing final-size guard may truncate
  soft sections, but it must not change `primary_error` or existing candidate
  semantics.

## D6. Degeneration Boundaries

Small logs should behave like today.

- If no warning-option cluster reaches `count >= 3` and no truncation signal is
  present, omit `error_clusters`.
- If a cluster has `3 <= count < 10` and `file_count < 3`, emit it with
  `large_scale = false`.
- If `count >= 10` or `file_count >= 3`, emit it with `large_scale = true`.

This keeps single-root-cause cases, two-location cases, and ordinary Top-K
diagnostics visually unchanged unless a repeated warning-option class is
actually present.

## D7. Relationship To Primary Error

`primary_error` and `root_cause_candidates` remain unchanged.

`error_clusters` is a supplementary group view:

- it does not affect ranking;
- it does not choose the primary error;
- it does not change `verdict`, `matched_tier`, or `direct_answer`;
- it does not change evidence collector selection.

Downstream tools may use `error_clusters` to decide whether a patch plan should
cover a whole diagnostic class, but the analyzer itself only reports facts.

## D8. Truncation Signal

Recognize compiler truncation with a case-insensitive search for:

```text
too many errors emitted
```

When present:

- set `error_clusters.truncated = true`;
- add up to 5 entries to `truncation_signals`;
- include an advisory in large repeated clusters that actual occurrences may be
  higher than `count`;
- do not create or rank a root-cause candidate from the truncation signal.

If a truncation signal exists but no cluster reaches the emit threshold, emit:

```json
{
  "error_clusters": {
    "schema_version": "error_clusters/v1",
    "truncated": true,
    "truncation_signals": [...],
    "full_locations_path": null,
    "clusters": []
  }
}
```

Rationale: truncation is global log metadata, not the root cause.

## D9. Implementation Scope For Follow-Up PR

The implementation PR should be additive:

- add an analyzer-side cluster builder module;
- call it after scan/rank and before output writing;
- attach summary data to the packet;
- write `error_clusters.json` sidecar when clusters exist;
- add unit tests for warning-option extraction, thresholds, samples, sidecar,
  truncation signal, and primary/candidate non-regression.

Do not change:

- scanner event extraction semantics except where needed to expose truncation
  signal data additively;
- ranking formula;
- `primary_error`;
- `root_cause_candidates`;
- patch-suggest or workflow behavior.
