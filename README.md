# LogAnalysisSkill

Tizen `gbs` build assistance skills for local AI assistants. The repository is
organized in the same shape as the publishable skills: three independent skill
folders, each with its own `SKILL.md` and `scripts/` runtime.

## Skill Layout

```text
LogAnalysisSkill/
├── tizen-gbs-build/
│   ├── SKILL.md
│   └── scripts/
│       └── gbs_build_skill/
├── tizen-gbs-log-analysis/
│   ├── SKILL.md
│   └── scripts/
│       └── gbs_analyzer/
│           └── patterns/
├── tizen-gbs-build-workflow/
│   ├── SKILL.md
│   └── scripts/
│       └── gbs_workflow/
├── tests/
├── integrations/
└── docs/
```

## What Each Skill Does

| Skill | Use It When | Entry Point |
| --- | --- | --- |
| `tizen-gbs-build` | You only want to run `gbs build` and capture a log plus exit code. | `python -m gbs_build_skill` or `tizen-gbs-build/scripts/run_build.py` |
| `tizen-gbs-log-analysis` | You already have a buildlog and want a compact root-cause Evidence Packet. | `python -m gbs_analyzer analyze` or `tizen-gbs-log-analysis/scripts/run_analyzer.py analyze` |
| `tizen-gbs-build-workflow` | You want the full local flow: build, analyze failures, and generate suggestion files. | `python -m gbs_workflow` or `tizen-gbs-build-workflow/scripts/run_workflow.py` |

The workflow skill depends on the build and log-analysis skills. Install all
three into the same Python environment, or keep the three skill folders next to
each other and use the direct launchers.

## Install Mode

Use this mode when developing or when you want the normal `python -m ...`
commands.

```bash
git clone https://github.com/lhmax2010/LogAnalysisSkill.git
cd LogAnalysisSkill
python -m pip install -e .
```

System dependency:

```bash
sudo apt install universal-ctags
```

Examples:

```bash
python -m gbs_build_skill \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --output-log .gbs_workflow/compiler.log

python -m gbs_analyzer analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir ./out

python -m gbs_workflow \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root . \
    --output-dir .gbs_workflow
```

## Direct Folder Mode

Use this mode when a skill hub checks out or copies the skill folders directly.
Keep the three folders side by side:

```text
skills/
├── tizen-gbs-build/
├── tizen-gbs-log-analysis/
└── tizen-gbs-build-workflow/
```

Run the launchers from any working directory:

```bash
python /path/to/skills/tizen-gbs-build/scripts/run_build.py \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --output-log .gbs_workflow/compiler.log

python /path/to/skills/tizen-gbs-log-analysis/scripts/run_analyzer.py analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir ./out

python /path/to/skills/tizen-gbs-build-workflow/scripts/run_workflow.py \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root . \
    --output-dir .gbs_workflow
```

If the workflow skill is not next to the other two folders, set:

```bash
export TIZEN_GBS_BUILD_SKILL_DIR=/path/to/tizen-gbs-build
export TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR=/path/to/tizen-gbs-log-analysis
```

## Company Hub Deployment & Cline Integration

For company-machine deployment, clone the stable release branch and publish the
three skill folders as the reviewable artifacts:

```bash
git clone --branch release/v1.0 https://github.com/lhmax2010/LogAnalysisSkill.git
```

Upload `tizen-gbs-build/`, `tizen-gbs-log-analysis/`, and
`tizen-gbs-build-workflow/` to the company skill hub as separate skills. Each
folder is self-contained for skill review because it includes its own
`SKILL.md` and `scripts/` runtime. If the hub expects archives, zip each skill
folder independently rather than uploading the whole repository as one skill.

For Cline or another local assistant, point the tool at the three `SKILL.md`
files directly, or install them through the company hub if that is how your
environment exposes skills. The workflow skill depends on the build and
log-analysis skills, so make all three available when users want the full
build -> analyze -> suggestions flow.

After installation, verify routing with three simple prompts:

- Build only: "Run a Tizen gbs build and capture the compiler log."
- Analyze only: "Analyze this gbs buildlog and find the root cause."
- Full workflow: "Run the gbs build, analyze it if it fails, and generate
  suggestion files."

## Outputs

Analyzer output:

- `evidence_packet.json`: machine-readable root-cause packet
- `evidence_packet.md`: compact LLM-facing packet
- `perf_report.json`: runtime and token metrics
- `trace.jsonl`: structured debug trace

Workflow output:

```text
.gbs_workflow/
├── compiler.log
├── analyzer_output/
├── suggestions/
└── workflow_summary.md
```

Workflow suggestions are advisory. The workflow never applies patches and never
retries builds automatically.

## Development

Read these first before making code changes:

1. `docs/CODEX_PROMPT.md`
2. `docs/DESIGN.md`
3. `.dev_memory/current.yaml`

Useful links:

- User guide: `docs/README_FOR_USER.md`
- Analyzer design baseline: `docs/DESIGN.md`
- Build workflow design: `docs/build_workflow/DESIGN.md`
- Cline examples: `integrations/cline/README.md`
- Historical decisions: `.dev_memory/`

## License

TBD
