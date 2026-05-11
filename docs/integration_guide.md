# Integration Guide

This guide captures the v0.5 integration contract. The analyzer CLI itself is not
implemented during M0.

## Invocation Contract

```bash
python -m gbs_analyzer analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir /tmp/gbs_analysis
```

## Outputs

- `evidence_packet.json`: machine-readable packet
- `evidence_packet.md`: LLM and human-readable packet
- `perf_report.json`: runtime, token, and decision metrics
- `trace.jsonl`: structured debugging trace

## Exit Codes

- `0`: success, including degraded success with packet output
- `1`: fatal error without packet output
- `2`: argument error
- `3`: buildlog unreadable
- `124`: timeout

## Notes

- stdout must remain machine-friendly for callers.
- Human and debug logs go through tracing files.
- Cline and Compiling Agent examples are scheduled for the full phase, but the contract
  above must be preserved from M1 onward.
