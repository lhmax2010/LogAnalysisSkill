# gbs_build_skill

`gbs_build_skill` is the build-only entrypoint for GbsBuildWorkflow v0.1.

It does exactly one thing: run `gbs build`, stream combined stdout/stderr into a buildlog,
and return the original gbs exit code.

## Usage

Installed package mode:

```bash
python -m gbs_build_skill \
  --conf ~/Toolchain/gbs.conf \
  --arch armv7l \
  --include-all \
  --output-log ./.gbs_workflow/compiler.log \
  --timeout 1800
```

Direct skill-folder mode:

```bash
python /path/to/tizen-gbs-build/scripts/run_build.py \
  --conf ~/Toolchain/gbs.conf \
  --arch armv7l \
  --include-all \
  --output-log ./.gbs_workflow/compiler.log \
  --timeout 1800
```

## Boundaries

- Does not parse buildlogs.
- Does not call `gbs_analyzer`.
- Does not generate suggestions.
- Does not apply patches.
- Does not retry builds.
