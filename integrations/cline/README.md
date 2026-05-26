# Cline Integration Examples

This directory contains sample custom command configurations for Cline-style
invocation. They are example contracts only; this repository does not deploy or
validate a live Cline extension environment.

## Analyze An Existing Buildlog

`analyze_gbs.json` uses installed mode and runs:

```bash
python -m gbs_analyzer analyze <buildlog_path> \
    --src-root <workspace> \
    --max-tokens 1800 \
    --output-format both \
    --output-dir <workspace>/.gbs_analysis
```

Direct skill-folder mode uses the same arguments with the launcher:

```bash
python /path/to/tizen-gbs-log-analysis/scripts/run_analyzer.py analyze <buildlog_path> \
    --src-root <workspace> \
    --max-tokens 1800 \
    --output-format both \
    --output-dir <workspace>/.gbs_analysis
```

Expected outputs:

- `.gbs_analysis/evidence_packet.json`
- `.gbs_analysis/evidence_packet.md`
- `.gbs_analysis/perf_report.json`
- `.gbs_analysis/trace.jsonl`

## Run Build Workflow

`build_workflow.json` uses installed mode and runs:

```bash
python -m gbs_workflow \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root <workspace> \
    --output-dir <workspace>/.gbs_workflow \
    --timeout 1800
```

Direct skill-folder mode requires the three skill folders side by side:

```text
skills/
├── tizen-gbs-build/
├── tizen-gbs-log-analysis/
└── tizen-gbs-build-workflow/
```

Then run:

```bash
python /path/to/skills/tizen-gbs-build-workflow/scripts/run_workflow.py \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root <workspace> \
    --output-dir <workspace>/.gbs_workflow \
    --timeout 1800
```

Expected outputs:

- `.gbs_workflow/compiler.log`
- `.gbs_workflow/analyzer_output/evidence_packet.json` when the build fails
- `.gbs_workflow/analyzer_output/evidence_packet.md` when the build fails
- `.gbs_workflow/suggestions/*.md`
- `.gbs_workflow/suggestions/*.patch` for patch-capable suggestions
- `.gbs_workflow/workflow_summary.md`

Workflow suggestions are advisory. The command never applies patches or retries
the build automatically.
