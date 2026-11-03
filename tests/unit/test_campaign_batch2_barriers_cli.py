from __future__ import annotations

import importlib
import io
import json
from contextlib import contextmanager

import pytest
from ci_triage import cli
from test_campaign_repair_step import _fixture, campaign_repair_step
from test_qb_trigger import Campaign as QbCampaign
from test_sandbox_submit import Campaign as SandboxCampaign
from tizen_campaign_core import campaign_state as state
from tizen_campaign_report import report
from tizen_qb_verify import qb_trigger
from tizen_sandbox_submit import sandbox_submit


def barrier(db, key, reason="abandoned"):
    state.append_event(
        db, key, "WORKSPACE_RELEASE", dict(paths=[], reason=reason, confirmed_by="Operator")
    )


def test_sandbox_abandoned_zero_push_and_hook(tmp_path, monkeypatch):
    c = SandboxCampaign(tmp_path, monkeypatch)
    barrier(c.db, c.key)
    result = c.run()
    assert result.exit_code == 4 and result.payload["error_code"] == "REJECTED_UNIT_ABANDONED"
    assert not c.pushes() and not c.hooks()


def test_sandbox_barrier_reloaded_after_lock(tmp_path, monkeypatch):
    c = SandboxCampaign(tmp_path, monkeypatch)
    original = sandbox_submit._locks

    @contextmanager
    def acquire(root):
        with original(root):
            barrier(c.db, c.key)
            yield

    monkeypatch.setattr(sandbox_submit, "_locks", acquire)
    assert c.run().payload["error_code"] == "REJECTED_UNIT_ABANDONED"
    assert not c.pushes()


def test_qb_abandoned_zero_start_and_request(tmp_path, monkeypatch):
    c = QbCampaign(tmp_path, monkeypatch)
    barrier(c.db, "u1")
    code, rows = c.run()
    assert code == 4 and rows[0]["error_code"] == "REJECTED_UNIT_ABANDONED"
    assert c.starts == 0 and not c.transcript.read_text()
    assert not c.sql("SELECT * FROM campaign_qb_requests")


def test_qb_batch_abandoned_unit_zero_commands(tmp_path, monkeypatch):
    c = QbCampaign(tmp_path, monkeypatch)
    c.add("u2")
    c.add("u3")
    barrier(c.db, "u2")
    code, rows = c.run(
        c.replies() + c.replies("u3", request=2, build="103"), units=["u1", "u2", "u3"]
    )
    assert code == 4
    assert rows[0]["action"] == "submitted_bound"
    assert rows[1]["error_code"] == "REJECTED_UNIT_ABANDONED"
    assert rows[2]["action"] == "submitted_bound"
    assert c.starts == 1
    assert {r["campaign_unit_key"] for r in c.sql("SELECT * FROM campaign_qb_requests")} == {
        "u1",
        "u3",
    }
    assert [r["command"] for r in c.commands()] == [
        "login",
        "read",
        "open_form",
        "fill",
        "submit",
        "read",
        "read",
        "open_form",
        "fill",
        "submit",
        "read",
        "close",
    ]


@pytest.mark.parametrize("entry", ["repair", "sandbox"])
def test_extra_marker_key_rejected_by_existing_entries(tmp_path, monkeypatch, entry):
    c = _fixture(tmp_path) if entry == "repair" else SandboxCampaign(tmp_path, monkeypatch)
    marker = c.src / ".campaign_clone"
    marker.write_text(json.dumps(dict(json.loads(marker.read_text()), extra="unexpected")))
    if entry == "repair":
        result = campaign_repair_step(
            c.options, build_verify_fn=lambda *a: pytest.fail("build ran")
        )
        assert result.exit_code == 4
        assert result.result.error_code == "REJECTED_IDENTITY_MISMATCH"
    else:
        result = c.run()
        assert result.exit_code == 4
        assert result.payload["error_code"] == "REJECTED_IDENTITY_MISMATCH"
        assert not c.pushes()


def test_qb_abandoned_release_is_not_barrier(tmp_path, monkeypatch):
    c = QbCampaign(tmp_path, monkeypatch)
    barrier(c.db, "u1", "abandoned_release")
    code, rows = c.run()
    assert code == 0 and rows[0]["action"] == "submitted_bound"


def test_qb_after_barrier_check_abandon_is_busy(tmp_path, monkeypatch):
    c = QbCampaign(tmp_path, monkeypatch)
    original = qb_trigger._snapshot

    def snapshot(*args):
        with pytest.raises(sandbox_submit._Reject) as error:
            report.release(c.db, "u1", c.data, "Operator", True)
        assert error.value.code == "CAMPAIGN_STATE_BUSY"
        return original(*args)

    monkeypatch.setattr(qb_trigger, "_snapshot", snapshot)
    assert c.run()[0] == 0


@pytest.mark.parametrize(
    "command,package,function",
    [
        ("qb-trigger", "tizen_qb_verify", "_main_qb_trigger"),
        ("qb-result-fetch", "tizen_qb_verify", "_main_qb_result_fetch"),
        ("sandbox-submit", "tizen_sandbox_submit", "_main_sandbox_submit"),
        ("campaign-repair-step", "tizen_campaign_repair", "_main_campaign_repair_step"),
    ],
)
@pytest.mark.parametrize("args", [[], ["--unknown"], ["--state-db", "db", "--config", "cfg"]])
def test_shared_cli_parser_identical_json_and_exit(command, package, function, args):
    entry = importlib.import_module(package + ".__main__")
    handler = getattr(entry, function)
    assert getattr(cli, function) is handler
    old_out, new_out = io.StringIO(), io.StringIO()
    old = cli.main([command, *args], stdout=old_out, stderr=io.StringIO())
    kw = dict(stdout=new_out)
    if command == "campaign-repair-step":
        kw["extra_pythonpath"] = ()
    else:
        kw["stderr"] = io.StringIO()
    new = handler(args, **kw)
    assert old == new
    assert json.loads(old_out.getvalue()) == json.loads(new_out.getvalue())
