"""Fresh-process negative controls; no source files or real remotes are changed."""

import json
import subprocess
import sys
from pathlib import Path

from ci_triage._sandbox_git import OVERRIDES

directory = Path(__file__).resolve().parent
results = []
for index, override in enumerate(OVERRIDES):
    script = (
        "import sys, pytest; from ci_triage import _sandbox_git as g; "
        "g.OVERRIDES=tuple(x for x in g.OVERRIDES if x != sys.argv[1]); "
        "sys.exit(pytest.main(['-q','tests/unit/test_qb_trigger.py::test_transport_isolation']))"
    )
    run = subprocess.run([sys.executable, "-c", script, override], capture_output=True, text=True)
    log = directory / f"transport-mutation-{index + 1}.log"
    log.write_text(run.stdout + run.stderr, encoding="utf-8")
    assert run.returncode == 1 and "1 failed" in run.stdout, override
    results.append(dict(removed=override, exit=run.returncode, log=log.name))
print(json.dumps(results, indent=2))
