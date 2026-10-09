"""Consume only this isolated browser's QuickBuild cookies through an anonymous pipe."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from http.cookies import SimpleCookie
from pathlib import Path

from ef5_web_probe import WebProbe

BASE = "https://quickbuild.tizen.org"


def cookie_header(rows: Sequence[Mapping[str, object]]) -> str:
    if not rows:
        raise ValueError("No scoped browser cookie")
    parts = []
    for row in rows:
        domain = str(row["domain"]).lstrip(".")
        if domain not in {"quickbuild.tizen.org", "tizen.org"}:
            raise ValueError("Cookie outside the authorized host")
        name, value = str(row["name"]), str(row["value"])
        if any(char in name + value for char in "\r\n"):
            raise ValueError("Invalid cookie field")
        cookie = SimpleCookie()
        cookie[name] = value
        parts.append(cookie[name].OutputString())
    return "; ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.load(sys.stdin)
    probe = WebProbe(BASE, args.output, cookie_header(rows), {"1069532", "1069540"})
    for row in rows:
        probe.redactor.remember(str(row["value"]))
    results: dict[str, str] = {}
    for build_id, paths in (
        ("1069532", ("/build/1069532/step_status",)),
        ("1069540", ("/build/1069540", "/build/1069540/overview",
                     "/build/1069540/variables", "/build/1069540/step_status")),
    ):
        results[build_id] = probe.inspect_build(build_id, paths, follow_links=False)
        if results[build_id] != "READ_PAGES_COLLECTED":
            break
    code = 0 if all(result == "READ_PAGES_COLLECTED" for result in results.values()) else 4
    probe.finish({
        "builds": results, "exit_code": code,
        "auth_mode": "isolated_manual_browser_cookie_in_memory",
        "cookie_stored": False, "trigger_confirmation": "NOT_GRANTED",
        "automatic_parent_inference": False,
    })
    print(json.dumps({"results": results, "exit_code": code}), flush=True)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt):
        print("Read-only probe stopped; credentials and raw errors are not printed.")
        sys.exit(2)
