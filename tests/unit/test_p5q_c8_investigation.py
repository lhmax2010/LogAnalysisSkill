"""Offline-only C8 diagnosis with production guards and synthetic HTTPS responses."""

import json
import os
import select
import shutil
import signal
import subprocess
import time
from pathlib import Path

import pytest
from test_qb_browser_node import ROOT, browser_paths, node_command


@pytest.mark.integration
def test_post_submit_read_signatures(tmp_path: Path) -> None:
    node, env = node_command()
    paths = browser_paths()
    output = Path(os.environ.get("P5Q_C8_INVESTIGATION", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    command = [*node, str(ROOT / "tests/node/p5q_c8_investigation.mjs"), *paths, str(output)]
    result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=600)
    (output / "node.stdout.txt").write_text(result.stdout)
    (output / "node.stderr.txt").write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["normal", "SIGTERM", "SIGINT"])
def test_signal_cleanup_observation(tmp_path: Path, mode: str) -> None:
    node, env = node_command()
    paths = browser_paths()
    output = Path(os.environ.get("P5Q_C8_INVESTIGATION", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    argv = [
        *node,
        str(ROOT / "tests/node/qb_browser_lifecycle.mjs"),
        "normal" if mode == "normal" else "signal",
        *paths,
    ]
    process = subprocess.Popen(
        argv,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    profile = None
    facts = {"mode": mode, "argv": argv, "pid": process.pid}
    try:
        assert process.stdout is not None
        assert select.select([process.stdout], [], [], 40)[0]
        ready = json.loads(process.stdout.readline())
        profile = Path(ready["profile"])
        assert ready["ready"] and profile.parent == Path("/dev/shm")
        assert profile.name.startswith("p5q-browser-")
        started = time.monotonic()
        if mode != "normal":
            process.send_signal(getattr(signal, mode))
        stdout, stderr = process.communicate(timeout=40)
        facts.update(
            exit_code=process.returncode,
            elapsed_seconds=time.monotonic() - started,
            profile=str(profile),
            profile_exists=profile.exists(),
            entries=[],
            stderr_categories=[
                line
                for line in stderr.splitlines()
                if line.startswith("QB_AGENT_STOPPED category=")
            ],
        )
        if profile.exists():
            for path in sorted(profile.rglob("*")):
                info = path.lstat()
                facts["entries"].append(
                    {
                        "path": str(path.relative_to(profile)),
                        "size": info.st_size,
                        "mode": info.st_mode,
                    }
                )
        if mode in {"normal", "SIGTERM"}:
            assert process.returncode == 0 and not profile.exists()
        facts["stdout_sanitized"] = stdout
    finally:
        if process.poll() is None:
            process.terminate()
            process.communicate(timeout=40)
        if profile is not None and profile.exists():
            # Only the path announced by this test child, never a pre-existing profile.
            assert profile.parent == Path("/dev/shm") and profile.name.startswith("p5q-browser-")
            references = subprocess.run(["lsof", "+D", str(profile)], capture_output=True)
            facts["lsof_exit"] = references.returncode
            assert references.returncode == 1 and not references.stdout and not references.stderr
            shutil.rmtree(profile)
            facts["own_residue_removed"] = True
        (output / f"cleanup-{mode}.json").write_text(json.dumps(facts, indent=2) + "\n")
