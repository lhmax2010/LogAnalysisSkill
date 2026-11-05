from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from test_qb_trigger import Campaign as Campaign
from tizen_campaign_core.discovery_manifest import atomic_write, load
from tizen_qb_verify import qb_collect
from tizen_qb_verify.qb_browser import QbBrowserError, decode_response


class Browser:
    def __init__(self, qb):
        self.trace = []
        self.paths = []
        self.root = None
        self.failure = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def login(self):
        return {"ok": True}

    def command(self, command, **fields):
        self.trace.append({"command": command})
        if command == "discovery_start":
            self.root = Path(fields["output_dir"])
            return {
                "path": "/overview/1917" if fields["build_id"] is None else "/build/101/overview"
            }
        if command == "read_text":
            if self.failure:
                error = QbBrowserError(
                    "DISCOVERY_LOG_UNREADABLE", agent_code="DISCOVERY_LOG_UNREADABLE"
                )
                error.reason = self.failure
                raise error
            path = (
                self.root
                / "discovery/101"
                / fields["run_dir"]
                / "logs/example.standard-aarch64.txt"
            )
            raw = b"error: compiler failure\n"
            atomic_write(path, raw)
            return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
        path = fields["path"]
        self.paths.append(path)
        facts = {"paths": []}
        if path == "/overview/1917":
            facts.update(
                builds=[
                    {"build_id": "100", "begin_date": "2026-01-01"},
                    {"build_id": "101", "begin_date": "2026-11-05 01:02:03"},
                ]
            )
        elif path == "/build/101/overview":
            facts.update(
                child=False, build_id="101", paths=["/build/101/variables", "/build/102/overview"]
            )
        elif path == "/build/102/overview":
            facts.update(child=True, build_id="102")
        elif path == "/build/102/html_report":
            facts.update(paths=["/download/102/html/HTML%20REPORT/index.html"])
        elif path.endswith("index.html"):
            facts.update(
                build_id="101",
                child_build_id="102",
                report_dir="HTML REPORT",
                packages=[
                    dict(
                        spec_name="example",
                        failed_arches=["standard-aarch64"],
                        primary_arch="standard-aarch64",
                        project="platform/upstream/example",
                        branch="tizen_base",
                        base_commit="a" * 40,
                        log_path=None,
                        log_sha256=None,
                        status="ok",
                        reason=None,
                    )
                ],
            )
        return {"ok": True, "discovery": facts, "outside_identity_count": 0}


@pytest.mark.parametrize("since", [None, "2026-10-01"])
@pytest.mark.parametrize("failure", [None, "ENCODING", "DOWNLOAD", "TOO_LARGE"])
def test_producer_manifest_repeat_no_database_or_analyzer(tmp_path, monkeypatch, since, failure):
    c = Campaign(tmp_path, monkeypatch)
    config = yaml.safe_load(c.config.read_text())
    browser = Browser(config["qb"])
    browser.failure = failure
    monkeypatch.setattr(qb_collect, "QbBrowser", lambda qb: browser)
    before = c.db.path.read_bytes()
    args = SimpleNamespace(
        config=c.config,
        state_root=tmp_path / "output",
        qb_project="tizen_base",
        build_id=None if since else "101",
        since=since,
    )
    first = qb_collect.collect(args)
    second = qb_collect.collect(args)
    assert first["manifests"] != second["manifests"]
    manifest, logs = load(Path(first["manifests"][0]), args.state_root)
    row = manifest["packages"][0]
    assert row["status"] == ("ok" if failure is None else "DISCOVERY_LOG_UNREADABLE")
    assert bool(logs) == (failure is None)
    assert row["reason"] == failure
    assert c.db.path.read_bytes() == before
    assert "/build/100/overview" not in browser.paths
    assert first["outside_recent_window"] == (["100"] if since else [])
    assert browser.closed


@pytest.mark.parametrize(
    "code,reason",
    [
        ("QB_TEXT_ENCODING_UNSUPPORTED", "ENCODING"),
        ("QB_DOWNLOAD_UNSUPPORTED", "DOWNLOAD"),
        ("DISCOVERY_LOG_UNREADABLE", "TOO_LARGE"),
    ],
)
def test_read_text_driver_fixed_errors(code, reason):
    import json

    with pytest.raises(QbBrowserError) as error:
        decode_response(
            json.dumps(dict(ok=False, error=code, reason=reason)),
            submit_sent=False,
            command="read_text",
        )
    assert error.value.code == code and error.value.reason == reason


def test_discovery_driver_error_does_not_change_ordinary_read():
    import json

    raw = json.dumps(dict(ok=False, error="DISCOVERY_LOG_UNREADABLE", reason="ENCODING"))
    with pytest.raises(QbBrowserError) as error:
        decode_response(raw, submit_sent=False, command="read")
    assert error.value.code == "INTERNAL_ERROR" and error.value.reason is None


@pytest.mark.parametrize("consumer", [False, True])
def test_discovery_invalid_yaml_is_fixed_json(tmp_path, consumer, monkeypatch):
    import io
    import json

    from tizen_campaign_intake.discover import main as consume

    path = tmp_path / "config.yaml"
    path.write_text("private-config-value: [unterminated")
    monkeypatch.setattr(qb_collect, "QbBrowser", lambda *a: pytest.fail("browser on invalid YAML"))
    argv = ["--config", str(path), "--state-root", str(tmp_path / "state")]
    if consumer:
        argv += ["--state-db", str(tmp_path / "db"), "--manifest", str(tmp_path / "manifest")]
    else:
        argv += ["--qb-project", "tizen_base", "--build-id", "101"]
    out = io.StringIO()
    assert (consume if consumer else qb_collect.main)(argv, stdout=out) == 2
    assert json.loads(out.getvalue()) == {
        "error_code": "INVALID_DISCOVERY_MANIFEST" if consumer else "INVALID_DISCOVERY_INPUT"
    }
    assert "private-config-value" not in out.getvalue()
