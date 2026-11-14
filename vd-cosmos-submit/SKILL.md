---
name: vd-cosmos-submit
description: Read-only anonymous management lookup, local diagnostics and request observation.
---

# Read-only commands

Use Python 3.10 or newer. Runtime dependencies are Python standard library only.

```bash
python3 vd-cosmos-submit/scripts/run.py doctor --config /absolute/config.json
python3 vd-cosmos-submit/scripts/run.py doctor --online --config /absolute/config.json --backend real
python3 vd-cosmos-submit/scripts/run.py lookup --hub-id H --config /absolute/config.json --backend real
python3 vd-cosmos-submit/scripts/run.py watch --request R --read-only --config /absolute/config.json --backend real
```

For offline replay use `--backend fixture --fixture /absolute/manifest.json`. The fixture manifest maps full management URLs to files and clock samples; a list of entries scripts successive observations. No fixture contacts a server.

Each invocation prints one JSON object. Detailed results are written below the configured data root. Lookup conclusions are candidates only, restricted to currently retained records; missing results never prove a submission did not happen. Watch resumes an existing observation task and does not create a request or submit a build. Always include `--read-only` when invoking watch from an analysis workflow.

Default doctor performs no network access and does not start a browser. Online doctor visits only the management host. This checkpoint contains no browser or submission implementation. Return codes: 0 success; 2 argument/non-terminal misuse; 3 human attention; 4 rule refusal; 5 backend/parser failure; 6 unmet prerequisite or lock contention.

Variable tables require Name/Value headers; only Value is used. Selected values are immutable from the first read. A later change raises “变量页已变化” for human handling. Multiple consistent builds for one Hub ID are reported as a rerun chain, never automatically selected.
