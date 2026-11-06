"""RESTORE-29 serial offline gates, always through run_limited.py."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").is_dir())


def main():
    sources = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    sources += [str(p) for p in Path("tests").rglob("*discovery*") if p.is_file()]
    hashes = {
        p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
        for p in sorted(set(sources))
        if Path(p).is_file() and (p.endswith((".py", ".mjs", "FROZEN.md")) or p == ".importlinter")
    }
    (HERE / "gate-inputs.json").write_text(json.dumps(hashes, indent=2) + "\n")
    pytest = [".venv/bin/python", "tests/run_quiet.py"]
    commands = {
        "mypy": [".venv/bin/mypy"],
        "ruff": [
            ".venv/bin/ruff",
            "check",
            "--force-exclude",
            *[p for p in hashes if p.endswith(".py")],
            str(HERE),
        ],
        "imports": [".venv/bin/lint-imports"],
        "design": [
            ".venv/bin/python",
            "docs/clang-fix-campaign/tools/check_design_doc.py",
            "docs/clang-fix-campaign/design.md",
        ],
        "static": [
            *pytest,
            "tests/unit/test_qb_browser_node.py::test_node_c2c_source_guard_mutations",
            "-q",
            "-s",
        ],
        "safety": [
            *pytest,
            "tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety",
            "-q",
            "-s",
        ],
        "collect": [".venv/bin/python", "-m", "pytest", "tests/", "--collect-only", "-q"],
        "full": [*pytest, "tests/", "-q", f"--junitxml={HERE / 'full/pytest.xml'}"],
    }
    # An explicit list lets failed development lint runs be retained without
    # overwriting evidence. The full suite is always one complete non-x run.
    selected = sys.argv[1:] or list(commands)
    for name in selected:
        code = subprocess.call(
            [sys.executable, str(HERE / "run_limited.py"), str(HERE / name), *commands[name]],
            cwd=ROOT,
        )
        print(json.dumps({"gate": name, "exit": code}), flush=True)
        if code:
            return code
    changed = [
        p
        for p, digest in hashes.items()
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest
    ]
    (HERE / "gate-integrity.json").write_text(json.dumps({"changed": changed}, indent=2) + "\n")
    return 4 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
