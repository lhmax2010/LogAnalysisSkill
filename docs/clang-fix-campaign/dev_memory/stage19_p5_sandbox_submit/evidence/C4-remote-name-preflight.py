"""Reproduce the P5 configured-remote-name precondition without any transport."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "tizen-ci-triage/scripts"))

from ci_triage._sandbox_git import SandboxGit  # noqa: E402


def main() -> None:
    git = SandboxGit()
    print("All commands are local config/remote/get-url inspection; no push or network.")
    with tempfile.TemporaryDirectory(prefix="p5-remote-name-") as directory:
        root = Path(directory)
        for label, remote in (
            ("absolute", str(root / "bare")),
            ("ssh", "ssh://unused.example/project"),
        ):
            repo = root / label
            repo.mkdir()
            git.run(repo, "init", "-q")
            print(json.dumps({"case": label, "remote": remote}, sort_keys=True))
            for args in (
                ("config", f"remote.{remote}.url", remote),
                ("config", "--get-regexp", r"^remote\..*\.url$"),
                ("remote",),
                ("ls-remote", "--get-url", remote),
            ):
                result = git.run(repo, *args, check=False)
                print(json.dumps(dict(
                    argv=result.args, exit=result.returncode, stdout=result.stdout,
                    stderr=result.stderr,
                ), ensure_ascii=False, sort_keys=True))
            listed = git.run(repo, "remote").stdout.splitlines()
            resolved = git.run(repo, "ls-remote", "--get-url", remote).stdout.rstrip("\n")
            print(json.dumps(dict(
                case=label, listed_same_name=remote in listed,
                resolved_url_equal=resolved == remote,
                unsafe_reason=git.unsafe_reason(repo),
            ), sort_keys=True))


if __name__ == "__main__":
    main()
