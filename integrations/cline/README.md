# Cline Integration Example

This directory contains a sample custom command configuration for calling the M8
wrapper from Cline.

The example command runs:

```bash
python -m gbs_analyzer analyze <buildlog_path> \
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

This is an example contract only. The M8 repository does not deploy or validate a
live Cline extension environment.
