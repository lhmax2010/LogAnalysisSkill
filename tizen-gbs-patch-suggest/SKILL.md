---
name: tizen-gbs-patch-suggest
description: Prepares LLM-ready patch-generation context from analyzer Evidence Packet JSON or a Tizen gbs build log for compiler or Werror source diagnostics. Use when the user wants help generating a source fix patch, candidate unified diff, or repair strategy for a compiler error, -Werror failure, warnings-as-errors diagnostic, and has an Evidence Packet, analyzer output directory, or buildlog. This skill writes context.md for Claude to read; it is not a patch generator and never applies changes.
compatibility: Requires local access to analyzer Evidence Packet JSON or a Tizen gbs build log and the gbs_patch_suggest Python package or this skill folder. Buildlog mode also requires gbs_analyzer installed or a sibling tizen-gbs-log-analysis skill folder. Optional source context collection requires access to the Tizen package source tree. Built for local AI assistants such as Claude Code or Cline.
---

# Tizen gbs Patch Suggest Context

Use this skill when the user wants a source patch suggestion for a Tizen `gbs`
compiler or Werror source diagnostic and analyzer evidence or a build log is available.

This skill is a context preparer, not a patch generator. It reads analyzer
`evidence_packet.json`, or runs analyzer on a build log to create that evidence,
writes `context.md`, `README.md`, and `meta.json`, then stops. The outer Claude
or Cline assistant reads `context.md` and generates candidate patches manually
from that context.

This skill does not call an LLM, does not generate the final patch itself, does
not apply patches, and does not modify the source tree.

## Triggers

Invoke patch-suggest when any of these are true:

- The user has analyzer output and asks for a source patch or candidate fix for a
  compiler or Werror source diagnostic.
- The user mentions `evidence_packet.json`, a Tizen `gbs` build log, `context.md`,
  patch context, `-Werror`, warnings treated as errors, or generating a unified
  diff from a compiler failure.
- The user asks Claude or Cline to prepare enough context to fix a compiler or
  Werror diagnostic without applying changes.
- The analyzer primary error is `compiler` or `werror` and the next step is patch
  drafting rather than more log analysis.

Do not use this skill for linker, dependency-resolution, patch-application,
spec-script, or install failures. Use the workflow suggesters for those fault
classes.

## Examples

### Example 1: User has analyzer evidence and wants a patch suggestion

User says: "Use this evidence packet to suggest a fix patch for this source
diagnostic."

Actions:

1. Confirm the `evidence_packet.json` path. If it was not provided, ask:
   "Which evidence_packet.json should I use?"
2. If the user provides the package source root, pass it with `--src-root`.
3. If the user does not provide a source root, do not ask and do not guess.
   Omit `--src-root`; the skill may produce a Level B advisory, and Claude will
   read the reported file itself before generating a patch.
4. If the user did not specify an output directory, use `./.gbs_patch_suggest`.
5. Run the skill, then read `README.md` and `context.md`.
6. Generate 1-3 candidate unified diffs from `context.md`, with approach,
   assumption, and confidence for each candidate.
7. Write each candidate to `.gbs_patch_suggest/candidate_N.patch` as a standard
   unified diff using project-root-relative `a/...` and `b/...` paths.
8. Do not apply the patch. Tell the user to review the file and optionally run
   `git apply --check <path>` before applying it themselves.

Result: `context.md` guides Claude to generate patch files for review without
changing the source tree.

### Example 2: User only points to an analyzer output directory

User says: "The analyzer output is in .gbs_analysis. Help me patch this source
diagnostic."

Actions:

1. Use `.gbs_analysis/evidence_packet.json` if it exists. If not, ask for the
   evidence path.
2. Run patch-suggest with that evidence and default output directory
   `./.gbs_patch_suggest`.
3. If the resulting `context.md` says source context is unavailable, Claude must
   open the reported `file:line` itself, read the source, and only then generate
   candidate patches.
4. Follow the `How to generate the patch` and `Instructions — MUST follow`
   sections in `context.md`.
5. If a patch candidate is generated, save it as `candidate_N.patch`; do not run
   `git apply` or edit the source tree.

Result: Claude uses the context package as a disciplined patch-generation prompt,
including Level B fallback when the skill could not read source context.

### Example 3: User has a build log but no Evidence Packet

User says: "Here is the failed buildlog. Prepare patch context for the -Werror failure."

Actions:

1. Use `--buildlog /path/to/buildlog` instead of `--evidence`.
2. If the user provides the package source root, pass it with `--src-root`.
3. The skill runs analyzer internally and writes analyzer evidence under
   `.gbs_patch_suggest/analyzer_output/`.
4. Read `.gbs_patch_suggest/context.md`, then generate candidate patch files as
   the outer assistant. Do not apply them.

Result: One command turns a build log into patch-generation context.

### Example 4: Evidence is not a compiler or Werror source diagnostic

User says: "Generate a source patch from this depsolve evidence."

Actions:

1. Run patch-suggest only if the user explicitly asks to check applicability, or
   inspect the evidence directly.
2. If the output status is `not_applicable`, do not generate a source patch from
   this skill.
3. Use `tizen-gbs-build-workflow` suggestion files or the relevant workflow
   suggester instead.

Result: Non-source-diagnostic failures are routed away from patch-suggest.

## Required Workflow

### Run the skill

1. Identify the input. Use exactly one of:
   - `--evidence /path/to/evidence_packet.json`
   - `--buildlog /path/to/buildlog`
2. If the user provided neither evidence nor build log, ask:
   "Which evidence_packet.json or build log should I use?" Do not guess; the
   skill cannot run without one of these inputs.
3. Identify optional source root. If the user provided a package source root,
   pass it with `--src-root`.
4. If the user did not provide a source root, do not ask and do not guess. Omit
   `--src-root`. This is intentional: the skill can produce a Level B advisory,
   and Claude can then open the reported `file:line` itself to read source before
   generating the patch.
5. Identify output directory. If the user did not specify one, use
   `./.gbs_patch_suggest` without asking.
6. Run patch-suggest through one of the stable entry points. `--evidence` and
   `--buildlog` are mutually exclusive; do not pass both.

   If `gbs_patch_suggest` is installed in the current Python environment:

   ```bash
   python -m gbs_patch_suggest \
       --evidence /path/to/evidence_packet.json \
       --src-root /path/to/source \
       --output-dir .gbs_patch_suggest
   ```

   To start from a build log, let patch-suggest run analyzer internally:

   ```bash
   python -m gbs_patch_suggest \
       --buildlog /path/to/buildlog \
       --src-root /path/to/source \
       --output-dir .gbs_patch_suggest
   ```

   If the source root is unavailable, omit `--src-root`:

   ```bash
   python -m gbs_patch_suggest \
       --evidence /path/to/evidence_packet.json \
       --output-dir .gbs_patch_suggest
   ```

   If using the skill folder directly without installing the Python package:

   ```bash
   python /path/to/tizen-gbs-patch-suggest/scripts/run_patch_suggest.py \
       --buildlog /path/to/buildlog \
       --src-root /path/to/source \
       --output-dir .gbs_patch_suggest
   ```

### After the skill finishes

1. Read `.gbs_patch_suggest/README.md` first for the selected diagnostic and
   output summary.
2. Read `.gbs_patch_suggest/context.md` as the primary patch-generation prompt.
3. Read `.gbs_patch_suggest/meta.json` if machine-readable status, level,
   source-context availability, or candidate paths are needed.
4. If `context.md` says source context is unavailable or ambiguous, Claude must
   inspect the reported file or candidate paths before generating any patch.
5. Generate candidate patches yourself as the outer assistant, following
   `context.md` exactly:
   - produce unified diff candidate(s)
   - include approach, explicit assumption, and confidence
   - question whether the reported error is only a symptom
   - verify referenced functions or symbols exist before preserving them
   - do not fabricate functions or headers
6. When you generate a patch candidate, write it to
   `.gbs_patch_suggest/candidate_N.patch` as a standard unified diff. Use paths
   relative to the project root with `a/...` and `b/...` prefixes when possible,
   so the user can run `git apply` from the project root.
7. Tell the user where each `candidate_N.patch` file was written and recommend
   `git apply --check <path>` as a verification step before applying.
8. Writing a `.patch` file only saves the suggestion to disk for review. It does
   not mean the patch should be applied. Writing the file and applying it are
   completely separate actions.
9. Do not apply patches. Do not run `git apply` or `patch`. Do not modify the
   source tree. The user reviews the patch file and decides whether to apply it.

## Output Contract

The skill writes a `.gbs_patch_suggest/` directory:

```text
.gbs_patch_suggest/
├── analyzer_output/
│   └── evidence_packet.json
├── README.md
├── context.md
└── meta.json
```

Files:

- `README.md`: short summary of the selected diagnostic and which file to read.
- `analyzer_output/`: present when `--buildlog` was used; contains analyzer output
  including `evidence_packet.json`.
- `context.md`: the primary LLM-facing patch-generation context. It includes the
  diagnostic, source context or fallback advisory, `How to generate the patch`,
  and final `Instructions — MUST follow`.
- `meta.json`: machine-readable status, level, fault class, semantic class,
  primary error, source-context metadata, candidate paths, and output paths.

`candidate_N.patch` files are not produced by the skill subprocess. They may be
written later by the outer Claude after reading `context.md`. These files are
suggestion drafts for user review and must not be auto-applied.

Statuses:

- `source_context_available`: Level A. Source context is included.
- `source_context_unavailable`: Level B. File and line are known, but source
  context was not read by the skill.
- `source_context_ambiguous`: Level B. Multiple source candidates were found.
- `diagnostic_only`: Level C. No usable file and line were available.
- `not_applicable`: the Evidence Packet primary error is not a compiler or Werror
  source diagnostic.

Exit codes:

- `0`: context output was written, including degraded or not-applicable output.
- `1`: fatal patch-suggest error.
- `3`: evidence file was unreadable.

## Relationship to Other Skills

Patch-suggest consumes `tizen-gbs-log-analysis` output. You can provide an
existing `evidence_packet.json`, or use `--buildlog` so patch-suggest runs
analyzer as a subprocess and consumes the generated evidence.

Patch-suggest can also be used after `tizen-gbs-build-workflow` by reading
`.gbs_workflow/analyzer_output/evidence_packet.json`. It does not replace the
workflow suggesters and does not handle non-source-diagnostic fault classes.

Patch-suggest has no direct relationship to `tizen-gbs-build` except that build
or workflow runs may produce the logs that analyzer later converts into evidence.

## Disclaimer

This skill prepares context only. It does not call an LLM, does not generate the
final patch itself, does not apply patches, and does not modify source files.
Claude may write `.patch` suggestion files after reading `context.md`, but that
is only saving a draft for review. The user decides whether to apply it.
