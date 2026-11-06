from __future__ import annotations

import json
import os
import select
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from test_qb_browser_node import ROOT, browser_paths, node_command


def test_discovery_scope_node():
    command, env = node_command()
    result = subprocess.run(
        [*command, "--test", str(ROOT / "tests/node/test_qb_discovery_scope.mjs")],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("script", ["diagnostics", "archives"])
def test_discovery_closed_diagnostics_and_real_archives(script):
    command, env = node_command()
    result = subprocess.run(
        [*command, str(ROOT / f"tests/node/test_qb_discovery_{script}.mjs"), *browser_paths()],
        env=env,
        capture_output=True,
        text=True,
        timeout=150,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "mode", ["ok", "ambiguous", "status", "redirect", "encoding", "attachment", "binary", "large"]
)
def test_discovery_local_https_browser(mode):
    command, env = node_command()
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/test_qb_discovery_browser.mjs"), *browser_paths(), mode],
        env=env,
        capture_output=True,
        text=True,
        timeout=150,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_qb_discover_cli_manifest(tmp_path):
    command, env = node_command()
    playwright, chromium = browser_paths()
    overrides, requests = tmp_path / "server.json", tmp_path / "requests.json"
    server = subprocess.Popen(
        [
            *command,
            str(ROOT / "tests/node/p5q_discovery_server.mjs"),
            str(overrides),
            str(requests),
        ],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert select.select([server.stdout], [], [], 30)[0]
        assert json.loads(server.stdout.readline()) == {"ready": True}
        config = tmp_path / "config.yaml"
        config.write_text(
            yaml.safe_dump(
                {
                    "qb": {
                        "base_url": "https://quickbuild.tizen.org",
                        "browser": {
                            "node": str(ROOT / "tests/fixtures/p5q_node_entry.py"),
                            "playwright_module": playwright,
                            "chromium": chromium,
                            "login_timeout_seconds": 30,
                        },
                        "projects": {
                            "tizen_base": {
                                "enabled": True,
                                "overview_id": 1917,
                                "configuration_path": (
                                    "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"
                                ),
                                "project_name": "Tizen-Base-Toolchain",
                                "qb_pass_requires_accept": False,
                                "form": {
                                    "BUILD_TYPE": "Full",
                                    "REPO_TYPE": "ALL",
                                    "BUILD_REFERENCE": "Ref. Snapshot",
                                    "SNAPSHOT_NUM": "@freeze",
                                    "PROJECT_BRANCH": "tizen_base",
                                    "Immediate Stop With Error": True,
                                    "CHILD_CONFIGURATIONS": ["standard-armv7l:aarch64:x86_64"],
                                    "TARGET_IMAGE": [],
                                    "Add Package List": "",
                                    "Remove Package List": "",
                                },
                            }
                        },
                    }
                }
            )
        )
        env.update(
            P5Q_TEST_NODE=json.dumps(command),
            P5Q_TEST_SERVER=str(overrides),
            P5Q_TEST_AGENT_LOG=str(tmp_path / "agent.json"),
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tizen_qb_verify",
                "qb-discover",
                "--config",
                str(config),
                "--state-root",
                str(tmp_path / "state"),
                "--qb-project",
                "tizen_base",
                "--build-id",
                "1193467",
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        output = json.loads(result.stdout)
        manifest = json.loads(Path(output["manifests"][0]).read_text())
        assert manifest["build_id"] == "1193467" and manifest["child_build_id"] == "1193469"
        assert manifest["packages"][0]["status"] == "ok"
        assert not list(tmp_path.rglob("*.db"))
        assert (Path(output["manifests"][0]).parent / manifest["packages"][0]["log_path"]).is_file()
        record = json.loads((tmp_path / "agent.json").read_text())
        assert all(
            row["input"]["command"] not in {"submit", "fill", "open_form"}
            for row in record["transcript"]
        )
        destination = os.environ.get("RESTORE_DISCOVERY_EVIDENCE")
        if destination:
            Path(destination).mkdir(parents=True, exist_ok=True)
            (Path(destination) / "cli.json").write_text(
                json.dumps(
                    {"output": output, "manifest": manifest, "trace": record["trace"]}, indent=2
                )
            )
    finally:
        if server.poll() is None:
            server.stdin.write('{"close":true}\n')
            server.stdin.flush()
        server.communicate(timeout=30)
        assert server.returncode == 0
    assert all(
        r["method"] == "GET" or r["path"].startswith("/signin?")
        for r in json.loads(requests.read_text())
    )
    if destination:
        (Path(destination) / "producer-requests.json").write_text(requests.read_text())
