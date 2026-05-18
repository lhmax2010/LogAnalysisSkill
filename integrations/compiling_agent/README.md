# Compiling Agent Integration Example

`log_analysis.py` is a small example adapter for build-monitoring agents that call
the analyzer through `subprocess`.

The adapter expects the M8 wrapper contract:

```bash
python -m gbs_analyzer analyze <buildlog_path> \
    --src-root <source_root_or_auto> \
    --max-tokens 1800 \
    --output-format json \
    --output-dir /tmp/gbs_analysis_agent
```

The analyzer writes `evidence_packet.json`; the adapter returns that JSON to the
agent. Timeout and nonzero analyzer exits are converted into degraded packets so
the calling agent can continue its own workflow.

This is example code only. M8 does not deploy, configure, or end-to-end test a real
Compiling Agent runtime.
