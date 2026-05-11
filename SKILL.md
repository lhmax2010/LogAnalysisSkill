---
name: tizen-gbs-log-analysis
description: Analyze Tizen gbs build logs and produce compact Evidence Packets for LLM root-cause diagnosis.
---

# Tizen gbs Log Analysis

## Status

This repository is currently at M0 initialization. The analyzer runtime is not ready for
end-user use until M8 completes.

## Intended Use

When implemented, this skill analyzes Tizen `gbs` build failures and produces:

- `evidence_packet.json` for tools and agents
- `evidence_packet.md` for LLM review
- `perf_report.json` for runtime and token metrics
- `trace.jsonl` for debugging

## Contract

The stable entry point will be:

```bash
python -m gbs_analyzer analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir ./out
```

Until M8, follow `docs/CODEX_PROMPT.md` and the active `.dev_memory/current.yaml`
instead of invoking the analyzer.
