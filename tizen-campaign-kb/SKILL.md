---
name: tizen-campaign-kb
description: Import, query and synchronize Clang repair precedents with an offline campaign knowledge base. Does not build, push, or access QuickBuild.
---

# Campaign Knowledge Base

Use an absolute external JSONL path for `kb_db`; knowledge records do not belong
in this repository. Human-reviewed seeds are T2 strategy references, never T1.

## Commands

```bash
python -m tizen_campaign_kb kb query --db /absolute/knowledge.jsonl --diagnosed-flag=<flag>
python -m tizen_campaign_kb kb append --db /absolute/knowledge.jsonl --record seed.json
python -m tizen_campaign_kb kb promote --db /absolute/knowledge.jsonl --id <id> --to CI_VERIFIED
python -m tizen_campaign_kb kb import-diff --db /absolute/knowledge.jsonl --diff fix.diff --ci-log buildlog --package <package> --gerrit-path <project> --toolchain-profile clang --fix-summary <summary> --baseline-commit <40-hex-commit>
python -m tizen_campaign_kb campaign-kb-sync --state-db <db> --config <yaml> --campaign-unit-key <key>
```

Supply the actual parent/source commit for imports, not a blob ID from the diff.
An optional `--quickbuild-id` marks imported history CI_VERIFIED; otherwise it is
NEW and excluded from retrieval. Never infer successful validation from a diff.

Run sync after sandbox push and again after the latest QuickBuild result. It
records KB_SYNC without advancing campaign state; only a matching PASS promotes
the instance. Repeated execution is idempotent.

T1 requires all identity and diagnostic keys to match. `gerrit_url` is display-only;
T1 fetch uses configured SSH base plus matching project and a whitelisted change
ref. A precedent does not bypass guard, compilation, policy or review gates.
Use `python -m tizen_campaign_repair propose-fix` to prepare a guarded T1 edit or
a context-only generation handoff. It does not invoke an LLM or apply edits.

Exit 2 means invalid input; corrupt JSONL or state inconsistency stops with exit 4.
Do not drop corrupt rows, recreate the database, or downgrade records to proceed.
