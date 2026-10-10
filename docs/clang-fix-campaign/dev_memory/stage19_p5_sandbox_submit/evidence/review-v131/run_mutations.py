"""Run approved review mutants in an isolated tree and restore exact source bytes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def function(text: str, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def replace_function(text: str, name: str, replacement: str, *, body_only: bool = False) -> str:
    current = function(text, name)
    if body_only:
        old = function(replacement, name)
        replacement = "".join(
            replacement.splitlines(keepends=True)[old.body[0].lineno - 1 : old.end_lineno]
        )
        start = current.body[0].lineno - 1
    else:
        start = current.lineno - 1
    lines = text.splitlines(keepends=True)
    return "".join(lines[:start]) + replacement + "".join(lines[current.end_lineno :])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path)
    args = parser.parse_args()
    root = args.tree.resolve()
    output = Path(__file__).resolve().parent / "mutations"
    output.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in sorted(root.glob("*/scripts")))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    policy = root / "tizen-ci-triage/scripts/ci_triage/suppress_policy.py"
    sandbox = root / "tizen-ci-triage/scripts/ci_triage/sandbox_submit.py"
    original_policy, original_sandbox = policy.read_bytes(), sandbox.read_bytes()
    old_policy = subprocess.check_output(
        ["git", "show", "72a5806:" + str(policy.relative_to(root))]
    )
    old_sandbox = subprocess.check_output(
        ["git", "show", "72a5806:" + str(sandbox.relative_to(root))]
    ).decode()
    results = []

    def run(label: str, test: str, selection: str, expected: int) -> None:
        # Avoid timestamp/size cache collisions when replacing old/new modules quickly.
        for path in (policy, sandbox):
            for cache in path.parent.glob("__pycache__/" + path.stem + ".*.pyc"):
                cache.unlink()
        argv = [
            sys.executable,
            "-m",
            "pytest",
            test,
            "-q",
            "-k",
            selection,
            f"--junitxml={output / (label + '.xml')}",
        ]
        result = subprocess.run(
            argv, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        (output / (label + ".log")).write_bytes(result.stdout)
        cases = list(ET.parse(output / (label + ".xml")).iter("testcase"))
        failed = [c.attrib["name"] for c in cases if c.find("failure") is not None]
        passed = [c.attrib["name"] for c in cases if len(c) == 0]
        row = dict(
            name=label,
            argv=argv,
            cwd=str(root),
            exit=result.returncode,
            failed=failed,
            passed=passed,
            PYTHONPATH=env["PYTHONPATH"],
            policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
            sandbox_sha256=hashlib.sha256(sandbox.read_bytes()).hexdigest(),
        )
        results.append(row)
        (output / "commands.json").write_text(json.dumps(results, indent=2) + "\n")
        print(
            f"{label}: exit={result.returncode}, failed={len(failed)}, passed={len(passed)}",
            flush=True,
        )
        assert result.returncode == expected
        assert failed and not passed if expected == 1 else passed and not failed

    try:
        run("current", "tests/unit/test_suppress_policy.py", "review", 0)
        policy.write_bytes(old_policy)
        run(
            "old-raw-cmake", "tests/unit/test_suppress_policy.py", "review_cmake_value_rejection", 1
        )
        run(
            "old-if-recursion",
            "tests/unit/test_suppress_policy.py",
            "review_if_recursive_rejection",
            1,
        )
        run(
            "old-if-literal-control",
            "tests/unit/test_suppress_policy.py",
            "review_if_literal_regression",
            0,
        )
        policy.write_bytes(original_policy)
        text = original_sandbox.decode()
        condition = "if (old.worktree_path, old.arch) != (new.worktree_path, new.arch):"
        assert text.count(condition) == 1
        sandbox.write_text(
            text.replace(condition, "if False:  # mutation: removed path/arch guard")
        )
        run(
            "removed-path-guard",
            "tests/unit/test_sandbox_submit.py",
            "review_toctou_record_path_same_tree",
            1,
        )
        sandbox.write_bytes(original_sandbox)
        text = replace_function(original_sandbox.decode(), "_publish", old_sandbox, body_only=True)
        node = function(old_sandbox, "_remote_sha")
        old_read = "".join(old_sandbox.splitlines(keepends=True)[node.lineno - 1 : node.end_lineno])
        text = replace_function(text, "_remote_sha", old_read)
        sandbox.write_text(text)
        run(
            "old-primary-transport",
            "tests/unit/test_sandbox_submit.py",
            "review_transport_config_race",
            1,
        )
    finally:
        policy.write_bytes(original_policy)
        sandbox.write_bytes(original_sandbox)
        assert policy.read_bytes() == original_policy and sandbox.read_bytes() == original_sandbox
        print("exact_source_restoration=PASS", flush=True)
    run("restored-policy", "tests/unit/test_suppress_policy.py", "review", 0)
    run("restored-sandbox", "tests/unit/test_sandbox_submit.py", "review", 0)


if __name__ == "__main__":
    main()
