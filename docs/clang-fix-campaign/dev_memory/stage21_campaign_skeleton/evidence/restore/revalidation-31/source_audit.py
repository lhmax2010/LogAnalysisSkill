"""Read-only byte/AST comparisons supporting the written RESTORE-31 audit."""

import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
BASE = "b7a55d8"
AGENT = "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs"
DRIVER = "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser.py"


def old(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


before, after = old(AGENT), (ROOT / AGENT).read_bytes()
marker = b"export class Agent {"
fill = b"  async fill(fields) {"
assert before.split(marker)[0] == after.split(marker)[0]
assert before.split(fill)[1] == after.split(fill)[1]
before_ast, after_ast = ast.parse(old(DRIVER)), ast.parse((ROOT / DRIVER).read_bytes())


def browser(tree):
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "QbBrowser")


assert ast.dump(browser(before_ast)) == ast.dump(browser(after_ast))
paths = ["tests/node/p5q_cli_agent.mjs", "tests/unit/test_p5q_c5a_integration.py",
         "tests/node/p5q_c8_investigation.mjs", "tests/unit/test_p5q_c8_investigation.py",
         "docs/clang-fix-campaign/campaign-skeleton-design-v1.3-FROZEN.md",
         "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md"]
files = []
for path in paths:
    original, current = old(path), (ROOT / path).read_bytes()
    assert original == current
    files.append({"path": path, "unchanged": True, "sha256": digest(current)})
result = {
    "baseline": BASE, "current": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "agent_prefix_unchanged": True, "prefix_sha256": digest(after.split(marker)[0] + marker),
    "agent_from_fill_to_end_unchanged": True,
    "driver_entire_QbBrowser_class_AST_unchanged": True,
    "agent_before_sha256": digest(before), "agent_after_sha256": digest(after),
    "protected_files": files,
}
(HERE / "source-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
