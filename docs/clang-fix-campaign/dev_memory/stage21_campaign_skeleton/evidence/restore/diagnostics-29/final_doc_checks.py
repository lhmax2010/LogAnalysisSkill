"""Evidence/document checks only after the functional gate stop."""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMANDS = [
    [sys.executable, str(HERE / "check_evidence.py")],
    [".venv/bin/ruff", "check", str(HERE / "check_evidence.py"),
     str(HERE / "sanitize_test_identifiers.py"), str(HERE / "final_doc_checks.py")],
    [sys.executable, "docs/clang-fix-campaign/tools/check_design_doc.py",
     "docs/clang-fix-campaign/design.md"],
    ["git", "diff", "--check", "--", "docs/clang-fix-campaign/design.md",
     "docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/progress.md",
     "tizen-qb-verify", "tests/unit/test_qb_discovery_node.py"],
]

results = []
for argv in COMMANDS:
    completed = subprocess.run(argv, check=False)
    results.append({"argv": argv, "exit": completed.returncode})
    (HERE / "final-document-checks.json").write_text(json.dumps(results, indent=2) + "\n")
    if completed.returncode:
        raise SystemExit(completed.returncode)
