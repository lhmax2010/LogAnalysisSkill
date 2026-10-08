"""Run the unchanged webpage probe, recording only allowlisted input errors."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/spikes"))

from ef5_web_probe import main  # noqa: E402

ERRORS = {
    "a nonempty single-line Cookie header is required": "COOKIE_EMPTY_OR_MULTILINE",
    "QB_COOKIE must be a Cookie header: name=value; name2=value2": "COOKIE_HEADER_FORMAT",
    "QB_COOKIE is unset: run in FatTank's terminal for getpass; do not paste in chat":
        "STDIN_NOT_TTY",
    "credential self-check failed; evidence not written": "CREDENTIAL_SELF_CHECK",
    "HTML sensitive-field self-check failed; no evidence written": "HTML_SELF_CHECK",
}


def run() -> int:
    status: dict[str, object] = {"stdin_isatty": sys.stdin.isatty(), "secret_recorded": False}
    sys.argv = ["ef5_web_probe.py", "--build-id", "1069532", "--output", str(
        ROOT / "docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-02"
    )]
    try:
        code = main()
    except (Exception, KeyboardInterrupt) as exc:
        code = 2
        status["error_category"] = ERRORS.get(str(exc), "UNCLASSIFIED_PRIVATE_ERROR")
        status["error_type"] = type(exc).__name__
    status["exit"] = code
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(run())
