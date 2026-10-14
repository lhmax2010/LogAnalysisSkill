"""Offline proof of the source-format query versus the frozen argv invariant."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from ci_triage._sandbox_git import SandboxGit
from ci_triage.sandbox_submit import _transport


@pytest.mark.parametrize("object_format", ["sha1", "sha256"])
def test_p5_format_selection_and_frozen_invariant(tmp_path: Path, object_format: str) -> None:
    source = tmp_path / "primary-worktree"
    source.mkdir()
    git = SandboxGit()
    format_args = ("--object-format=sha256",) if object_format == "sha256" else ()
    git.run(None, "init", *format_args, str(source))
    calls: list[list[str]] = []

    class RecordingGit:
        def run(self, *args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            result = git.run(*args, **kwargs)
            calls.append(result.args)
            return result

    snapshot = SimpleNamespace(
        git=RecordingGit(), derive_inputs=SimpleNamespace(worktree=source)
    )
    with _transport(snapshot, tmp_path) as transport:
        actual = git.run(
            None, "rev-parse", "--show-object-format", git_dir=transport
        ).stdout.strip()
        assert actual == object_format
    assert not (tmp_path / ".transport").exists()
    source_calls = [
        argv for argv in calls
        if any(argv[i:i + 2] == ["-C", str(source)] for i in range(len(argv) - 1))
        or "--git-dir=" + str(source) in argv
    ]
    format_calls = [argv for argv in source_calls if "--show-object-format" in argv]
    assert len(format_calls) == 1
    print(json.dumps({
        "source_format": object_format,
        "transport_format": actual,
        "source_format_argv": format_calls[0],
        "transport_cleaned": True,
        "network_commands": [argv for argv in calls if "ls-remote" in argv or "push" in argv],
    }, sort_keys=True))
    # Evaluate the exact frozen section 9.1 invariant against P5's real command.
    assert not format_calls, "FROZEN_9_1: no git command may use the primary copy via -C/--git-dir"
