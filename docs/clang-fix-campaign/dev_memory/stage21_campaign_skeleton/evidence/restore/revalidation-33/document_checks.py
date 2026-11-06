"""Sequential evidence-script and document checks inside the bounded scope."""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
commands = [
    [".venv/bin/ruff", "format", str(HERE)],
    [".venv/bin/ruff", "check", str(HERE)],
    [
        sys.executable,
        "docs/clang-fix-campaign/tools/check_design_doc.py",
        "docs/clang-fix-campaign/design.md",
    ],
    [
        "git",
        "diff",
        "--check",
        "--",
        "docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/progress.md",
        "docs/clang-fix-campaign/review/campaign-skeleton-closeout.md",
    ],
    [sys.executable, str(HERE / "finalize_evidence.py")],
]
results = []
for argv in commands:
    result = subprocess.run(argv, check=False)
    results.append({"argv": argv, "exit": result.returncode})
    (HERE / "document-checks.json").write_text(json.dumps(results, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(result.returncode)
