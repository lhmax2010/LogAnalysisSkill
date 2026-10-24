#!/usr/bin/env python3
"""Complement import-linter with a standard-library/own-modules source allowlist."""
import ast
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[2]
allowed = set(sys.stdlib_module_names) | {"vd_cosmos_core", "vd_cosmos_watch", "vd_cosmos_fetch", "vd_cosmos_workflow"}
failures = []
count = 0
for directory in ("vd-cosmos-core", "vd-cosmos-watch", "vd-cosmos-fetch", "vd-cosmos-workflow"):
    for subdir in ("src", "scripts"):
        for path in (repo / directory / subdir).rglob("*.py"):
            count += 1
            tree = ast.parse(path.read_text(), filename=str(path), feature_version=10)
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [n.name for n in node.names]
                elif isinstance(node, ast.ImportFrom) and not node.level:
                    names = [node.module or ""]
                for name in names:
                    if name.split(".")[0] not in allowed:
                        failures.append(f"{path.relative_to(repo)}:{node.lineno}: forbidden import {name}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                    failures.append(f"{path.relative_to(repo)}:{node.lineno}: dynamic loading forbidden")
print(f"Python 3.10 syntax / standard-library import check: {count} files")
for failure in failures:
    print(failure)
raise SystemExit(bool(failures))
