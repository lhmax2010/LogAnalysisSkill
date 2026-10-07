"""PHASE1-03 artificial controls; never observations or after-run evidence."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from terminal_diff_controls import ARTIFICIAL_READERS, artificial_pair
from terminal_expected_diff import Gate, GateError, load_gate, pointer

CONTROLS = ("normal", "premature-item3", "missing-item4")


def replace(obj: Any, path: str, value: Any) -> None:
    parent, _, token = path.rpartition("/")
    target = pointer(obj, parent)
    key = token.replace("~1", "/").replace("~0", "~")
    target[int(key) if isinstance(target, list) else key] = copy.deepcopy(value)


def phase_a_pair(gate: Gate) -> tuple[dict[str, Any], dict[str, Any]]:
    before, after = artificial_pair(gate)
    for row in gate.item3_projection():
        sid, path = row["scenario"], row["path"]
        replace(after[sid], path, pointer(before[sid], path))
    return before, after


def run(gate: Gate, control: str) -> None:
    before, after = phase_a_pair(gate)
    if control == "premature-item3":
        row = gate.item3_projection()[0]
        sid, path = row["scenario"], row["path"]
        replace(after[sid], path, gate.validate()[sid][path]["new"])
    elif control == "missing-item4":
        del after["surface1-none"]["calls"][0]["kwargs"]["timeout"]
    elif control != "normal":
        raise GateError("UNKNOWN_PHASE_CONTROL")
    gate.compare(before, after, ARTIFICIAL_READERS, phase="A")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", choices=CONTROLS)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(f"ARTIFICIAL_PHASE_A_CONTROL={args.control}; PRODUCTION_RUN=NO")
    try:
        run(load_gate(args.root), args.control)
    except GateError as exc:
        print(f"GATE_REJECTED: {exc}")
        return 1
    print("PHASE_A=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
