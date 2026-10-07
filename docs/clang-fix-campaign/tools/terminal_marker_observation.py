"""Item5 facts: interrupt real marker writes, then invoke isolated reader copies."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

from protected_marker_readers import collect
from terminal_predicates import EVIDENCE_PREFIX, load_json
from verify_anchors import TREE, WORKSPACE, digest, guard, marker_state, write_json

CLAIM = "OBS-1.item5-order"
EXPECTED = {
    "clean_repository_preserving_markers",
    "release_worktree_protection",
    "is_protected",
    "_exclude_private_files",
}


def workspace_module(root: Path) -> Any:
    module = importlib.import_module("tizen_ci_shared.workspace")
    if module.__file__ is None or Path(module.__file__).resolve() != (root / WORKSPACE).resolve():
        raise ValueError("workspace import provenance differs")
    return module


def read_copies(module: Any, source: Path, copies: Path, names: list[str]) -> list[dict[str, Any]]:
    rows = []
    for name in names:
        destination = copies / name
        shutil.copytree(source, destination, symlinks=True)
        row: dict[str, Any] = {"reader": name, "copy": str(destination)}
        before = marker_state(destination / module.PROTECTED_FILENAME)
        try:
            result = getattr(module, name)(worktree_path=destination)
            row.update(result_kind="RETURN", result_value_or_type=repr(result))
        except Exception as exc:
            row.update(
                result_kind="EXCEPTION",
                result_value_or_type=f"{type(exc).__module__}.{type(exc).__qualname__}",
            )
        row["marker_before"] = before
        row["marker_after"] = marker_state(destination / module.PROTECTED_FILENAME)
        rows.append(row)
    return rows


def probe(root: Path, directory: Path, scenario: str) -> None:
    module = workspace_module(root)
    path = directory / "worktree"
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
    marker = module.write_workdir_marker(
        path,
        workspace_root=directory,
        baseline_repo=directory / "baseline",
        base_commit="a" * 40,
        iter_index=1,
    )
    handle = module.DisposableWorktree(
        str(path), str(directory / "baseline"), "a" * 40, str(directory), 1, str(marker)
    )
    order: list[str] = []
    original_verify = module._verify_cleanup_handle
    original_exclude = module._exclude_private_files
    original_write = Path.write_text

    def note(step: str) -> None:
        order.append(step)
        write_json(directory / "order.json", order)

    def verify(value: Any) -> None:
        note("_verify_cleanup_handle")
        original_verify(value)

    def exclude(value: Path) -> None:
        note("_exclude_private_files")
        if scenario == "EXCLUDE_INTERRUPTED":
            os.kill(os.getpid(), signal.SIGINT)
        original_exclude(value)

    def write(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
        if self == path / module.PROTECTED_FILENAME:
            note("write_protected_marker")
            self.write_bytes(b'{"protected_reason":')
            os.kill(os.getpid(), signal.SIGINT)
        return original_write(self, data, *args, **kwargs)

    with (
        patch.object(module, "_verify_cleanup_handle", verify),
        patch.object(module, "_exclude_private_files", exclude),
        patch.object(Path, "write_text", write),
    ):
        module.mark_worktree_protected(handle, verification_id="fixture-v", failure_key="fixture-f")


def produce(root: Path, rules_root: Path, out: Path) -> None:
    context = guard(root, rules_root)
    context["producer_sha256"] = digest(Path(__file__))
    anchors = collect(root, rules_root)
    names = anchors["protected_marker_readers"]
    if len(names) != 4 or set(names) != EXPECTED:
        raise ValueError(f"PHASE1_READER_UNIVERSE: {names}")
    out.mkdir(parents=True, exist_ok=False)
    anchors_path = rules_root / EVIDENCE_PREFIX / "B-1-anchors.json"
    if anchors_path.exists():
        raise ValueError("independent anchors already exist; do not overwrite evidence")
    write_json(anchors_path, anchors)
    fixtures = Path(tempfile.mkdtemp(prefix="p49-item5-"))
    module = workspace_module(root)
    raw: dict[str, Any] = {"context": context, "fixture_root": str(fixtures), "observations": []}
    scenarios = []
    for name in ("EXCLUDE_INTERRUPTED", "MARKER_WRITE_INTERRUPTED"):
        directory = fixtures / name
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--root",
            str(root),
            "--rules-root",
            str(rules_root),
            "--probe",
            name,
            "--directory",
            str(directory),
        ]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
        if result.returncode != -signal.SIGINT:
            raise ValueError(f"signal did not propagate: {result.returncode}: {result.stderr}")
        protected = directory / "worktree" / module.PROTECTED_FILENAME
        state = marker_state(protected)
        if protected.is_file():
            try:
                json.loads(protected.read_bytes())
            except json.JSONDecodeError:
                state["state"] = "PARTIAL"
        readers = read_copies(module, directory / "worktree", directory / "copies", names)
        observation = {
            "scenario_id": name,
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "call_order": load_json(directory / "order.json"),
            "readers": readers,
            "protected_marker": state,
        }
        raw["observations"].append(observation)
        scenarios.append(
            {
                "scenario_id": name,
                "protected_marker": state,
                "readers": [
                    {k: r[k] for k in ("reader", "result_kind", "result_value_or_type")}
                    for r in readers
                ],
            }
        )
    write_json(out / "raw.json", raw)
    claim = {
        "claim_id": CLAIM,
        "snapshot": TREE,
        "call_order": raw["observations"][1]["call_order"],
        "scenarios": scenarios,
        "evidence": [
            {"kind": "FILE", "path": str(path), "sha256": digest(path), "selector": selector}
            for path, selector in (
                (out / "raw.json", "/observations"),
                (anchors_path, "/protected_marker_readers"),
                (root / WORKSPACE, "mark_worktree_protected"),
            )
        ],
    }
    write_json(out / "output.json", {CLAIM: claim})
    write_json(out / "context.json", {"head": context["head"], "tree": TREE, "run_id": out.name})
    print(f"FACTS_WRITTEN claim={CLAIM} readers={len(names)} scenarios={len(scenarios)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rules-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--probe", choices=("EXCLUDE_INTERRUPTED", "MARKER_WRITE_INTERRUPTED"))
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    guard(args.root, args.rules_root)
    if args.probe:
        if args.directory is None:
            parser.error("probe requires directory")
        probe(args.root, args.directory, args.probe)
    else:
        if args.out is None:
            parser.error("out required")
        produce(args.root, args.rules_root, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
