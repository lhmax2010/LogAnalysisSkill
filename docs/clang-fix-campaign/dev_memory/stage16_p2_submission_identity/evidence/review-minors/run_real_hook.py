"""Observe the registered real hook accepting an uppercase autosquash-like subject."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from unittest.mock import patch

from ci_triage import submission_identity as identity


def main() -> None:
    output = Path(__file__).resolve().parent
    config = json.loads((output.parent.parent / "real-hook-config.json").read_text())
    hook = Path(config["gerrit_commit_msg_hook"])
    before = hook.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    assert digest == config["gerrit_commit_msg_hook_sha256"]
    message = "Fix! x\n"
    calls = []
    trailers: list[str] = []
    original = identity._run_isolated

    def observe(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        calls.append({"argv": command, "cwd": str(cwd), "env": env})
        original(command, cwd=cwd, env=env)
        if command[0] == "sh":
            text = Path(command[2]).read_text()
            assert text.splitlines()[0] == "Fix! x"
            trailers.extend(line for line in text.splitlines() if line.startswith("Change-Id:"))
            assert len(trailers) == 1
            assert re.fullmatch(r"Change-Id: I[0-9a-f]{40}", trailers[0])

    with patch.object(identity, "_run_isolated", side_effect=observe):
        result = identity.generate_change_id_via_hook(
            hook_path=hook, hook_sha256=digest, submission_key="b" * 64, message=message,
        )
    assert trailers == [f"Change-Id: {result}"]
    assert message == "Fix! x\n" and hook.read_bytes() == before
    assert all(not Path(str(call["cwd"])).parent.exists() for call in calls)
    (output / "real-hook.json").write_text(json.dumps({
        "hook_path": str(hook), "hook_sha256": digest, "input_message": message,
        "change_id": result, "trailers": trailers, "calls": calls,
        "input_unchanged": True, "hook_unchanged": True, "temporary_removed": True,
        "exit": 0,
    }, indent=2) + "\n")
    print(f"hook_sha256={digest}")
    print(trailers[0])
    print("subject='Fix! x'; valid_change_id_lines=1; input_unchanged=true; exit=0")


if __name__ == "__main__":
    main()
