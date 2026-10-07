"""Artificial Section 6 controls, NOT repository observations or before-run evidence."""

from __future__ import annotations

import argparse
import copy
import subprocess
from pathlib import Path
from typing import Any

from terminal_expected_diff import ABSENT, Gate, GateError, load_gate, value

CONTROLS = (
    "normal",
    "extra-change",
    "missed-change",
    "empty-reason",
    "impossible-registration",
    "missing-mode",
    "unknown-mode",
    "no-diff-with-differences",
    "empty-diff-set",
    "readers-empty",
    "readers-missing",
)
ARTIFICIAL_READERS = ["ARTIFICIAL_READER_DO_NOT_USE_AS_ITEM5"]


def artificial_pair(gate: Gate) -> tuple[dict[str, Any], dict[str, Any]]:
    """Independent result construction, not a copy of resolved expected_diff values.

    Archived argv/outcomes supply fixture input; disk/reader values below are
    intentionally made up. Nothing here is submitted to the OBS verifier.
    """
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    for scenario in gate.manifest["scenarios"]:
        obs = gate.sources.fact(scenario["obs_ref"])
        # SIGTERM has no outcome JSON; artificial fixtures explicitly represent no return.
        if obs["outcome"] is None:
            returned, exc = ABSENT, ABSENT
        else:
            returned, exc = obs["outcome"]["return_value"], obs["outcome"]["exception"]
        exception = exc.get("value", {})
        obj = {
            "return_value": copy.deepcopy(returned),
            "exception_type": value(exception["type"]) if "type" in exception else dict(ABSENT),
            "exception_code": copy.deepcopy(exception.get("code", ABSENT)),
            "exception_message": value(exception["message"])
            if "message" in exception
            else dict(ABSENT),
            "warnings": copy.deepcopy(returned)
            if scenario["surface"] == "submit-remote"
            else dict(ABSENT),
            "action": dict(ABSENT),
            "calls": copy.deepcopy(obs["trace"]),
            "destination": value(
                {"exists": True, "kind": "DIRECTORY", "files": {}, "symlink_target": dict(ABSENT)}
            ),
            "worktree": value(
                {"exists": True, "kind": "DIRECTORY", "files": {}, "symlink_target": dict(ABSENT)}
            ),
            "workdir_marker": {"exists": False, "sha256": dict(ABSENT)},
            "protected_marker": {
                "exists": False,
                "sha256": dict(ABSENT),
                "readers": [
                    {
                        "reader": ARTIFICIAL_READERS[0],
                        "return_value": value(False),
                        "exception_type": dict(ABSENT),
                        "exception_code": dict(ABSENT),
                        "exception_message": dict(ABSENT),
                    }
                ],
            },
            "exclude_completed": value(False),
            "exit_code": value(0),
        }
        if scenario["fault"] == "timeout":
            for field in (
                "return_value",
                "exception_type",
                "exception_code",
                "exception_message",
                "warnings",
            ):
                obj[field] = dict(ABSENT)
        before[scenario["id"]] = obj
        changed = copy.deepcopy(obj)
        for call in changed["calls"]:
            call["kwargs"]["timeout"] = scenario["timeout"]
        if scenario["id"] == "DANGLING_SYMLINK":
            changed["exception_type"] = value("GerritError")
            changed["exception_code"] = value("SOURCE_DIR_UNSAFE")
            changed["exception_message"] = value(
                "source directory is a symlink: " + scenario["fixture"]["destination"]
            )
        if scenario["fault"] == "timeout":
            surface = scenario["surface"]
            injection = obs["injection"]
            message = str(subprocess.TimeoutExpired(injection["cmd"], injection["timeout"]))
            if surface == "submit-remote":
                changed["warnings"] = value(["target_head_unknown:timeout"])
                changed["return_value"] = value(["target_head_unknown:timeout"])
            else:
                if surface.startswith("fetch-"):
                    name, code = "GerritError", "FETCH_TIMEOUT"
                elif surface == "submit-git":
                    name, code = "GerritSubmitError", "GIT_TIMEOUT"
                else:
                    name, code = "WorkspaceViolation", None
                    message = "GIT_TIMEOUT: " + message
                changed["exception_type"] = value(name)
                changed["exception_code"] = value(code) if code else dict(ABSENT)
                changed["exception_message"] = value(message)
        after[scenario["id"]] = changed
    return before, after


def run_control(gate: Gate, name: str) -> None:
    before, after = artificial_pair(gate)
    readers: Any = ARTIFICIAL_READERS[:]
    sid = "DANGLING_SYMLINK"
    entry = gate.expected["scenarios"][sid]
    if name == "extra-change":
        after[sid]["action"] = value("UNREGISTERED_ARTIFICIAL_ACTION")
    elif name == "missed-change":
        del after[sid]["calls"][0]["kwargs"]["timeout"]
    elif name == "empty-reason":
        entry["differences"]["/exception_type"]["reason"] = " "
    elif name == "impossible-registration":
        entry["differences"]["/action"] = copy.deepcopy(entry["differences"]["/exception_type"])
    elif name == "missing-mode":
        del entry["mode"]
    elif name == "unknown-mode":
        entry["mode"] = "MAYBE"
    elif name == "no-diff-with-differences":
        entry.update(mode="NO_DIFF", reason="artificial invalid combination")
    elif name == "empty-diff-set":
        entry["differences"] = {}
    elif name == "readers-empty":
        readers = []
    elif name == "readers-missing":
        readers = None
    elif name != "normal":
        raise GateError("UNKNOWN_CONTROL")
    gate.compare(before, after, readers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", choices=CONTROLS)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(f"ARTIFICIAL_CONTROL={args.control}; REAL_BEFORE=PENDING_SEG3; OBS_PRODUCERS=NOT_RUN")
    try:
        run_control(load_gate(args.root), args.control)
    except (ValueError, TypeError, KeyError) as exc:
        print(f"GATE_REJECTED: {exc}")
        return 1
    print("EXACT_DIFF=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
