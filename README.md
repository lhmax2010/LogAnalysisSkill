# gbs-compile-log-analyzer v1.3.0

Tizen `gbs` build assistance skills for local AI assistants such as Claude Code
or Cline. This release contains four publishable skills that work together to
build, analyze, and prepare reviewable patch suggestions for Tizen package build
failures.

This repository does not run an LLM by itself and never applies patches. It
collects deterministic build evidence and writes context files that an outer
assistant can read. Any generated patch is a review draft for a human to inspect.

## Included Skills

| Skill | Purpose | Entry Point |
| --- | --- | --- |
| `tizen-gbs-build` | Runs `gbs build`, captures compiler logs, finds GBS failure logs, and retries once with `--clean` when the build root is broken. | `python3 -m gbs_build_skill` or `tizen-gbs-build/scripts/run_build.py` |
| `tizen-gbs-log-analysis` | Analyzes build logs and produces compact Evidence Packets, token metrics, error clusters, and source candidate sidecars. | `python3 -m gbs_analyzer analyze` or `tizen-gbs-log-analysis/scripts/run_analyzer.py analyze` |
| `tizen-gbs-build-workflow` | Orchestrates build -> analyze -> advisory suggestions -> optional patch context. | `python3 -m gbs_workflow` or `tizen-gbs-build-workflow/scripts/run_workflow.py` |
| `tizen-gbs-patch-suggest` | Prepares patch-generation context, edit-spec skeletons, and deterministic patch-formatting helpers. | `python3 -m gbs_patch_suggest` or `tizen-gbs-patch-suggest/scripts/run_patch_suggest.py` |

## Main Features

### Build Skill

- Runs `gbs build` with explicit `gbs.conf` and target architecture.
- Captures terminal compiler output into `compiler.log`.
- Locates structured GBS package failure logs for downstream analysis.
- Detects broken GBS build roots and retries exactly once with `--clean`.
- Uses non-interactive stdin so broken-root prompts do not hang automation.

### Analyzer Skill

- Scans Tizen `gbs` build logs and extracts structured diagnostics.
- Ranks likely root causes and produces `evidence_packet.json` and
  `evidence_packet.md`.
- Emits `perf_report.json` with downstream Claude-facing token estimates.
- Emits `error_clusters.json` for repeated Werror classes.
- Emits `source_candidates.json` and observation reports for structured source
  diagnostic coverage.
- Includes analyzer support for Clang `unknown warning option` diagnostics
  without `file:line`, and avoids mistaking compiler command lines containing
  `-Werror` for diagnostics.

### Workflow Skill

- Runs the local build -> analyze -> suggestion flow.
- Keeps verdicts and exit codes deterministic.
- Adds optional patch context output without calling an LLM in subprocesses.
- Reports downstream token estimates in `workflow_summary.md`.
- Does not apply patches or modify package source trees.

### Patch Suggest Skill

- Consumes analyzer evidence or a build log and writes LLM-ready patch context.
- Defaults to fix-all-by-file when analyzer source candidates are available.
- Groups patch-ready diagnostics by file and writes one per-file context.
- Generates edit-spec skeletons with tab-preserving original lines.
- Suppresses misleading skeleton rows when diagnostics point to structural
  closing lines rather than the real edit site.
- Provides a deterministic `format-patch` helper that turns edit specs into
  standard `git apply` compatible patch files.
- Supports insert-after edit specs with anchor validation for `.spec` changes.
- Includes a `.spec` toolchain-flag compatibility path for Clang
  `-Wunknown-warning-option` failures caused by GCC-only CFLAGS/CXXFLAGS. This
  path preserves original GCC flags and inserts a `%{toolchain_is clang}`
  stripping block for Clang.

## v1.3.0 Status

### Completed and Verified

- Four-skill layout is present and publishable.
- `tizen-gbs-build` broken-root recovery is implemented and tested.
- Analyzer Evidence Packet, token metrics, error clusters, source candidates,
  and observation reports are implemented.
- Workflow integration is implemented and keeps subprocess LLM calls disabled.
- Patch-suggest can run from `--evidence` or `--buildlog`.
- Patch-suggest fix-all-by-file is default, with `--no-fix-all` as a fallback.
  This path has been validated on an example inference-package Cline flow where it
  produced three file-group patch contexts and covered the previous missed
  diagnostics.
- Fix-all-by-file has also been validated on a large example network-package case:
  54 source diagnostics across 11 files produced 11 file-scoped FIXALL patch
  contexts, with generated patches passing `git apply --check`.
- Multi-candidate behavior was validated on an-example-app-package: patch-ready
  diagnostics stay covered, while conservative `type=unknown` diagnostics remain
  visible without being patched automatically.
- Patch-suggest deterministic formatter supports replacement and insert-after
  edit operations for the validated source-diagnostic paths.
- Analyzer unknown-warning-option handling and patch-suggest `.spec` toolchain
  flag compatibility were validated end to end on an-example-media-package:
  the analyzer primary diagnostic is the real Clang unknown-warning-option error,
  patch-suggest emits an insert-after edit spec, original GCC flag lines remain
  intact, and the Clang-only branch strips only the unsupported stringop flags.
- Workflow build -> analyze -> patch-suggest chaining was validated on the same
  an-example-media-package case. When patch-suggest produces a patch-ready context, the
  workflow summary surfaces `patch_context/` first and keeps generic fallback
  only as a fallback.

### Known Boundaries

- The tools do not apply patches. Users must review patch files and run
  `git apply --check` / `git apply` themselves.
- The tools do not call an LLM. Patch semantics are still decided by the outer
  assistant and human reviewer.
- Source fixability is conservative. Uncertain ownership, generated files,
  third-party code, system headers, and missing source roots degrade to advisory
  output.
- Non-source failures such as depsolve, linker, RPM phase, patch application,
  and environment failures remain advisory rather than automatic patch context.
- `.spec` toolchain flag handling currently targets unknown Clang warning
  options proven to come from `.spec` CFLAGS/CXXFLAGS. Unknown flag sources such
  as CMakeLists, environment variables, or toolchain files degrade to advisory.
- an-example-app-package E003/E005 remain `type=unknown` under the current conservative
  fixability whitelist. They are visible to the user but not patched
  automatically.
- Direction-2 fallback strategies such as compiler-specific `-Wno-error=...`
  exemptions are not implemented in v1.3.0.

## Install Mode

Use editable install when developing or when `python3 -m ...` entry points are
preferred:

```bash
git clone <your-repo-url>
cd gbs-compile-log-analyzer
python3 -m pip install -e .
```

System dependency:

```bash
sudo apt install universal-ctags
```

Examples:

```bash
python3 -m gbs_build_skill \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --output-log .gbs_workflow/compiler.log

python3 -m gbs_analyzer analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir ./out

python3 -m gbs_workflow \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root . \
    --output-dir .gbs_workflow

python3 -m gbs_patch_suggest \
    --buildlog .gbs_workflow/compiler.log \
    --src-root . \
    --output-dir .gbs_patch_suggest
```

## Direct Folder Mode

Use this mode when a skill hub checks out or copies the skill folders directly.
Keep all four folders side by side:

```text
skills/
├── tizen-gbs-build/
├── tizen-gbs-log-analysis/
├── tizen-gbs-build-workflow/
└── tizen-gbs-patch-suggest/
```

Run direct launchers:

```bash
python3 /path/to/skills/tizen-gbs-build/scripts/run_build.py \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --output-log .gbs_workflow/compiler.log

python3 /path/to/skills/tizen-gbs-log-analysis/scripts/run_analyzer.py analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir ./out

python3 /path/to/skills/tizen-gbs-build-workflow/scripts/run_workflow.py \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root . \
    --output-dir .gbs_workflow

python3 /path/to/skills/tizen-gbs-patch-suggest/scripts/run_patch_suggest.py \
    --buildlog .gbs_workflow/compiler.log \
    --src-root . \
    --output-dir .gbs_patch_suggest
```

If the workflow or patch-suggest skill is not next to sibling skills, set the
needed discovery variables:

```bash
export TIZEN_GBS_BUILD_SKILL_DIR=/path/to/tizen-gbs-build
export TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR=/path/to/tizen-gbs-log-analysis
export TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR=/path/to/tizen-gbs-patch-suggest
```

## Release Artifacts

For release or release-server review, publish the four skill folders as separate
artifacts:

```text
tizen-gbs-build/
tizen-gbs-log-analysis/
tizen-gbs-build-workflow/
tizen-gbs-patch-suggest/
```

Each folder contains its own `SKILL.md` and `scripts/` runtime. If the release
server expects archives, zip each skill folder independently rather than
uploading the whole repository as one skill.

Recommended review prompts:

- Build only: "Run a Tizen gbs build and capture the compiler log."
- Analyze only: "Analyze this gbs buildlog and find the root cause."
- Full workflow: "Run the gbs build, analyze it if it fails, and generate
  suggestion files."
- Patch context: "Use patch-suggest on this buildlog and prepare reviewable
  patch context."

## Outputs

Analyzer output:

- `evidence_packet.json`: machine-readable root-cause packet
- `evidence_packet.md`: compact LLM-facing packet
- `perf_report.json`: runtime and token metrics
- `error_clusters.json`: full locations for repeated source warning classes
- `source_candidates.json`: structured source diagnostic candidates
- `source_candidate_observation.json`: coverage and old-path comparison report
- `trace.jsonl`: optional structured debug trace

Workflow output:

```text
.gbs_workflow/
├── compiler.log
├── analyzer_output/
├── suggestions/
├── patch_context/
└── workflow_summary.md
```

Patch-suggest output:

```text
.gbs_patch_suggest/
├── README.md
├── context.md
├── meta.json
├── fix_all_context/
├── cluster_context/
├── candidate_context/
└── spec_toolchain_flag_context/
```

Actual output depends on the selected diagnostic path. Read `README.md` and
`meta.json` in the output directory first, then open only the relevant per-file
context files.

## Safety Rules

- The tools never call an LLM.
- The tools never run `git apply` or `patch`.
- The tools never modify source trees.
- Generated `.patch` files are suggestions only.
- Users should review patches and run `git apply --check` before applying.
