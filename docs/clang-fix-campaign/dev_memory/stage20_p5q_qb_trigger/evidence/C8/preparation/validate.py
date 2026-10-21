"""Read-only validation of prepared C8 evidence and immutable C6 files."""

import json
import subprocess

from ci_triage.qb_browser import _check_diagnostic_strings
from ci_triage.qb_redact import PageRedactor
from prepare_c8 import HERE, REPO, ROOT, digest, immutable, stamp, write


def main():
    preflight = json.loads((HERE / "preflight.json").read_text())
    assert preflight["ready_without_user_authorization"]
    assert digest(ROOT / "state.db") == preflight["db_sha256"]
    results = []
    for argv in [
        [".venv/bin/ruff", "check", str(HERE)],
        [
            ".venv/bin/python",
            "docs/clang-fix-campaign/tools/check_design_doc.py",
            "docs/clang-fix-campaign/design.md",
        ],
        ["git", "diff", "--cached", "--check"],
    ]:
        started = stamp()
        run = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
        results.append(
            dict(
                argv=argv,
                started=started,
                ended=stamp(),
                exit=run.returncode,
                stdout=run.stdout,
                stderr=run.stderr,
            )
        )
        assert run.returncode == 0
    files = []
    redactor = PageRedactor()
    for p in sorted(HERE.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or p.name == "validation.json":
            continue
        raw = p.read_bytes()
        redactor.check_bytes(raw)
        if p.suffix == ".json":
            _check_diagnostic_strings(json.loads(raw), redactor)
        files.append(dict(path=str(p.relative_to(HERE)), sha256=digest(p)))
    write(
        "validation.json",
        dict(
            at=stamp(),
            immutable=immutable(),
            gates=results,
            files=files,
            redaction_failed=0,
            c6_tree_unchanged=True,
            live_authorization="NOT_RECEIVED",
        ),
    )
    print(json.dumps(dict(result="PASS", files=len(files), gates=len(results))))


if __name__ == "__main__":
    main()
