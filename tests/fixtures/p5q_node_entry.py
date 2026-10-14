#!/usr/bin/env python3
"""Test-only executable adapter; the real Python driver passes its normal argv."""

import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
assert (
    Path(sys.argv[1]).resolve() == root / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"
)
node = json.loads(os.environ["P5Q_TEST_NODE"])
os.execvpe(node[0], [*node, str(root / "tests/node/p5q_cli_agent.mjs"), *sys.argv[2:]], os.environ)
