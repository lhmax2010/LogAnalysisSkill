"""Reproduce the section 6.1.12 mutation survivor without changing either policy."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUTPUT = Path(__file__).resolve().parent
OLD = Path("/tmp/p5-v131-old-policy")
CASE = "add_compile_options($<IF:$<BOOL:1>,-w,>)\n"
PROBE = """
import json
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from ci_triage import suppress_policy as policy

with TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'CMakeLists.txt').write_text('# baseline\\n')
    spec = dict(schema_version='gbs_patch_suggest/edit-spec/v1', patch_name='probe',
                edits=[dict(file='CMakeLists.txt', old='# baseline\\n',
                            new='add_compile_options($<IF:$<BOOL:1>,-w,>)\\n')])
    print(json.dumps(dict(module=policy.__file__, result=asdict(
        policy.evaluate(spec, root, 'generated'))), sort_keys=True))
"""


def main() -> None:
    outputs = {}
    for label, root in (("old", OLD), ("current", ROOT)):
        env = dict(os.environ, PYTHONPATH=str(root / "tizen-ci-triage/scripts"))
        result = subprocess.run(
            [sys.executable, "-c", PROBE], env=env, text=True, capture_output=True, check=True
        )
        outputs[label] = json.loads(result.stdout)
        outputs[label]["exit"] = result.returncode
        source = Path(outputs[label]["module"]).read_bytes()
        outputs[label]["module_sha256"] = hashlib.sha256(source).hexdigest()
    old_result = dict(outputs["old"]["result"])
    new_result = dict(outputs["current"]["result"])
    old_result.pop("rules_version")
    new_result.pop("rules_version")
    assert old_result == new_result
    assert old_result["verdict"] == "forbidden"
    outputs["same_behavior_except_version"] = True
    outputs["case"] = CASE
    (OUTPUT / "if-survivor.json").write_text(json.dumps(outputs, indent=2) + "\n")
    print(json.dumps(outputs, indent=2))

    env = dict(os.environ, PYTHONPATH=str(OLD / "tizen-ci-triage/scripts"))
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(OLD / "tests/unit/test_suppress_policy.py"),
        "-q",
        "-k",
        "review_cmake_value_rejection",
    ]
    result = subprocess.run(
        command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    (OUTPUT / "old-policy-pytest.log").write_text(result.stdout)
    (OUTPUT / "commands.json").write_text(
        json.dumps(
            dict(
                argv=command,
                PYTHONPATH=env["PYTHONPATH"],
                exit=result.returncode,
                test_sha256=hashlib.sha256(
                    (OLD / "tests/unit/test_suppress_policy.py").read_bytes()
                ).hexdigest(),
            ),
            indent=2,
        )
        + "\n"
    )
    print(result.stdout.splitlines()[-1])
    print(f"old_pytest_exit={result.returncode}")
    assert result.returncode == 1 and "10 failed, 1 passed" in result.stdout


if __name__ == "__main__":
    main()
