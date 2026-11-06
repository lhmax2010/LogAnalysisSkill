"""Record tracked production/test bytes before the full test gate."""

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
files = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
paths = [
    p
    for p in files
    if p
    and (
        p.startswith("tests/")
        or p.startswith("tizen-")
        or p.endswith("FROZEN.md")
        or p in {".importlinter", "pyproject.toml"}
    )
]
result = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
with (HERE / "source-before.json").open("x") as output:
    output.write(json.dumps(result, indent=2) + "\n")
print(json.dumps({"recorded_files": len(result)}))
