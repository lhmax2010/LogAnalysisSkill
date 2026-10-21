"""Offline agent protocol fixture. Configuration lives in test-only arguments."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    script, transcript = (Path(arg) for arg in sys.argv[1:])
    scenario = json.loads(script.read_text(encoding="utf-8"))
    configuration_pages = (
        scenario.get("configuration_pages", {}) if isinstance(scenario, dict) else {}
    )
    replies = iter(scenario["replies"] if isinstance(scenario, dict) else scenario)
    state = "new"
    allowed = {
        "login": {"new"},
        "read": {"ready", "form", "filled", "invalid"},
        "open_form": {"ready", "form", "filled", "invalid"},
        "fill": {"form"},
        "submit": {"filled"},
    }
    for line in sys.stdin:
        command = json.loads(line)
        with transcript.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(command) + "\n")
        name = command.get("command")
        if name == "close":
            print('{"ok":true}', flush=True)
            return
        if state not in allowed.get(name, set()):
            print('{"ok":false,"error":"AGENT_PHASE"}', flush=True)
            continue
        response = (
            configuration_pages[command["path"]]
            if name == "read" and command.get("path") in configuration_pages
            else next(replies, {"ok": True})
        )
        if response == "EXIT":
            return
        if response == "INVALID_JSON":
            print("not json", flush=True)
            continue
        if isinstance(response, dict) and response.get("ok"):
            state = {
                "login": "ready",
                "read": "ready",
                "open_form": "form",
                "fill": "filled",
                "submit": "invalid",
            }.get(name, state)
        elif name in {"open_form", "fill", "submit"}:
            state = "invalid"
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
