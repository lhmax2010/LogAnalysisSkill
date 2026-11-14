#!/usr/bin/env python3
"""Checkpoint B1 must not acquire a browser/PHP runtime or implement submission."""
import ast
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
paths = list((repo / 'vd-cosmos-submit').rglob('*.py'))
core = repo / 'vd-cosmos-core/src/vd_cosmos_core'
paths += list(core.glob('bm_*.py')) + list(core.glob('submit_*.py')) + [core / 'verify_b3a11b1.py']
for path in paths:
    tree = ast.parse(path.read_text(), feature_version=10)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or '']
            assert not any(n.startswith(('playwright', 'selenium')) for n in names), str(path)
        if isinstance(node, ast.List) and node.elts and isinstance(node.elts[0], ast.Constant):
            assert node.elts[0].value not in {'php', 'php-cli'}, str(path)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert 'playwright install' not in node.value, str(path)
print('Checkpoint B1 browser/PHP command boundary: PASS (' + str(len(paths)) + ' files)')
