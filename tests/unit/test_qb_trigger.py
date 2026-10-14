from __future__ import annotations

import copy
import fcntl
import hashlib
import html
import io
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml
from ci_triage import campaign_state as state
from ci_triage import cli
from ci_triage import qb_trigger as trigger
from ci_triage.qb_config import ARCHITECTURES, canonical_profile_json
from tizen_ci_shared.state import StateDatabase, VerificationRecord, write_pass_record

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-12"


def git(path, *args, input=None):
    return subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        text=True,
        capture_output=True,
        input=input,
        env={
            **os.environ,
            "GIT_AUTHOR_DATE": "2026-10-14T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-10-14T00:00:00Z",
        },
    ).stdout.strip()


def variables(target, marker, changes=None):
    parser = trigger._VariableRows()
    parser.feed((ARCHIVE / "02.response.html").read_text())
    replacements = {"BUILD_PKG_LIST_MODIFY": target, "BUILD_NOTES": marker, **(changes or {})}
    rows = []
    for row in parser.rows:
        if len(row) != 3:
            continue
        if row[0] in replacements:
            if replacements[row[0]] is None:
                continue
            row[2] = replacements[row[0]]
        rows.append(
            "<tr>"
            + "".join("<td>" + html.escape(cell).replace("\n", "<br>") + "</td>" for cell in row)
            + "</tr>"
        )
    return "<table>" + "".join(rows) + "</table>"


class Campaign:
    def __init__(self, root, monkeypatch, object_format="sha1"):
        self.root, self.mp = root, monkeypatch
        self.object_format = object_format
        self.db = StateDatabase(root / "state.db")
        self.remotes = root / "remotes"
        self.remotes.mkdir()
        self.project = dict(
            enabled=True,
            overview_id=1917,
            configuration_path="root/Tizen-Base-Toolchain/RBS/TRIGGER",
            project_name="Tizen-Base-Toolchain",
            qb_pass_requires_accept=False,
            form={
                "BUILD_TYPE": "Full",
                "REPO_TYPE": "ALL",
                "BUILD_REFERENCE": "Ref. Snapshot",
                "SNAPSHOT_NUM": "@freeze",
                "PROJECT_BRANCH": "tizen_base",
                "Immediate Stop With Error": True,
                "CHILD_CONFIGURATIONS": [ARCHITECTURES],
                "TARGET_IMAGE": [],
                "Add Package List": "",
                "Remove Package List": "",
            },
        )
        self.data = dict(
            campaign_workspace=str(root / "ws"),
            gerrit_ssh_base=str(self.remotes),
            git_author_identity="Test <test@example.com>",
            git_committer_identity="Test <test@example.com>",
            gerrit_commit_msg_hook=str(root / "hook"),
            gerrit_commit_msg_hook_sha256="a" * 64,
            qb=dict(
                base_url="https://quickbuild.tizen.org",
                browser=dict(
                    node=sys.executable,
                    playwright_module=sys.executable,
                    chromium=sys.executable,
                    login_timeout_seconds=60,
                ),
                projects={"tizen_base": self.project},
            ),
        )
        self.config = root / "config.yaml"
        self.save()
        self.units = {}
        self.add("u1")
        self.calls = []
        self.starts = 0
        self.script, self.transcript = root / "replies.json", root / "commands.jsonl"
        original = subprocess.Popen

        def popen(argv, *args, **kwargs):
            self.calls.append((list(argv), kwargs.get("env", {})))
            assert "push" not in argv
            if "ls-remote" in argv:
                assert any(str(arg).startswith(str(self.remotes) + "/") for arg in argv)
            if any(str(arg).endswith("qb_browser_agent.mjs") for arg in argv):
                self.starts += 1
                argv = [
                    sys.executable,
                    str(ROOT / "tests/fixtures/qb_fake_agent.py"),
                    str(self.script),
                    str(self.transcript),
                ]
            return original(argv, *args, **kwargs)

        monkeypatch.setattr(subprocess, "Popen", popen)
        numbers = iter(range(1, 100))
        monkeypatch.setattr(trigger.uuid, "uuid4", lambda: uuid.UUID(int=next(numbers)))

    def save(self):
        self.config.write_text(yaml.safe_dump(self.data))

    def sql(self, sql, args=()):
        conn = self.db.connect()
        try:
            with conn:
                return [dict(r) for r in conn.execute(sql, args)]
        finally:
            conn.close()

    def add(self, key, branch="tizen_base"):
        remote = self.remotes / key
        remote.mkdir()
        git(remote, "init", "--bare", "-q", "--object-format=" + self.object_format)
        git(remote, "config", "user.name", "Test")
        git(remote, "config", "user.email", "test@example.com")
        tree = git(remote, "mktree", input="")
        sha = git(remote, "commit-tree", tree, input="derived\n")
        git(remote, "update-ref", "refs/heads/sandbox/test", sha)
        state.create_unit(
            self.db,
            campaign_unit_key=key,
            submission_identity_key=key,
            ci_system="quickbuild",
            source_build_id="1",
            project=key,
            branch=branch,
            spec_name=key,
            base_commit=sha,
            primary_arch="standard-aarch64",
            failed_arches=["standard-aarch64"],
            toolchain_profile="clang",
            ci_evidence_ref="evidence",
            ci_evidence_sha256="a" * 64,
            max_rounds=3,
            max_build_invocations=9,
        )
        state.create_round(
            self.db, key, round_index=1, edit_spec_ref="edit", edit_spec_sha256="e" * 64
        )
        for i, arch in enumerate(("aarch64", "armv7l", "x86_64")):
            record = VerificationRecord(
                verification_id=f"{key}-v{i}",
                result="PASS",
                timestamp="2026-10-14T00:00:00Z",
                failure_key=f"{key}-{arch}",
                base_commit=sha,
                verified_commit_sha=sha,
                verified_tree_sha=tree,
                canonical_diff_sha256="d" * 64,
                patch_sha256="d" * 64,
                edit_spec_sha256="e" * 64,
                project=key,
                branch=branch,
                spec_name=key,
                arch="standard-" + arch,
                gbs_conf_sha256="f" * 64,
                build_log_sha256="b" * 64,
                worktree_path=str(self.root / key / arch),
                command_line="gbs",
            )
            write_pass_record(self.db, record)
            self.sql(
                "INSERT INTO campaign_verifications (campaign_unit_key,arch_raw,arch_norm,"
                "verification_id,round_index,edit_spec_sha256,campaign_schema_version,created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    key,
                    record.arch,
                    arch,
                    record.verification_id,
                    1,
                    "e" * 64,
                    "campaign/v1",
                    "2026-10-14T00:00:00Z",
                ),
            )
        state.append_event(
            self.db,
            key,
            "DERIVE",
            dict(
                message_brief="fix",
                author_identity="Test <test@example.com>",
                committer_identity="Test <test@example.com>",
                author_date="2026-10-14T00:00:00Z",
                committer_date="2026-10-14T00:00:00Z",
                derived_commit_sha=sha,
                verified_tree_sha=tree,
            ),
        )
        push = dict(
            ref="refs/heads/sandbox/test",
            ref_class="sandbox",
            pushed_sha=sha,
            result="ok",
            url=None,
            at="2026-10-14T00:00:00Z",
        )
        state.append_event(self.db, key, "PUSH", push)
        state.append_status(self.db, key, "SANDBOX_PUSHED")
        self.units[key] = dict(sha=sha, remote=remote, push=push, branch=branch)

    def commands(self):
        return [json.loads(line) for line in self.transcript.read_text().splitlines()]

    def snapshot(self):
        return {
            table: self.sql("SELECT * FROM " + table)
            for table in (
                "campaign_qb_profiles",
                "campaign_qb_requests",
                "campaign_qb_events",
                "campaign_gate_events",
                "campaign_status_log",
            )
        }

    def replies(self, key="u1", request=1, build="100", current="snap-A", count=1, changes=None):
        fields = copy.deepcopy(self.data["qb"]["projects"][self.units[key]["branch"]]["form"])
        target = key + "@" + self.units[key]["sha"]
        marker = "clang-fix-campaign request=" + uuid.UUID(int=request).hex
        fields.update(
            {"SNAPSHOT_NUM": current, "Build Package List": target, "BUILD NOTES": marker}
        )
        readback = {
            f"{k}/{'selection' if k in trigger._PALETTES else 'value'}": v
            for k, v in fields.items()
        }
        return [
            {"ok": True, "released": False},
            dict(
                ok=True,
                released=False,
                readback=readback,
                fingerprint="a" * 64,
                snapshot_option_count=count,
            ),
            dict(ok=True, released=True, landed="build", build_id=build),
            dict(ok=True, status=200, html_redacted=variables(target, marker, changes)),
        ]

    def run(self, replies=None, *, units=None, retrigger=False, login=None):
        self.calls.clear()
        self.transcript.write_text("")
        self.script.write_text(
            json.dumps([login or {"ok": True}, *(self.replies() if replies is None else replies)])
        )
        args = [
            "qb-trigger",
            "--state-db",
            str(self.db.path),
            "--state-root",
            str(self.root / "evidence"),
            "--config",
            str(self.config),
        ]
        if units is None:
            args += ["--verification-ids", "u1-v0,u1-v1,u1-v2"]
        else:
            path = self.root / "units.json"
            path.write_text(
                json.dumps(
                    [dict(verification_ids=[f"{key}-v{i}" for i in range(3)]) for key in units]
                )
            )
            args += ["--units-file", str(path)]
        if retrigger:
            args += ["--retrigger"]
        out, self.err = io.StringIO(), io.StringIO()
        code = cli.main(args, stdout=out, stderr=self.err)
        return code, json.loads(out.getvalue())

    def seed(self, kind, key="u1"):
        if kind == "none":
            return
        seq = state.create_qb_request(
            self.db, key, request_id="old-" + key, sbs_target=key + "@" + self.units[key]["sha"]
        )
        status = "QB_SUBMIT_FAILED" if kind == "failed-submit" else "QB_REQUESTED"
        if kind in {"bound", "pass", "fail"}:
            state.append_qb_event(
                self.db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id="99"
            )
            status = "QB_TRIGGERED"
        if kind in {"pass", "fail"}:
            state.append_qb_event(
                self.db,
                request_seq=seq,
                event_type="RESULT",
                qb_build_id="99",
                status=kind.upper(),
                sbs_target_echo=key + "@" + self.units[key]["sha"],
                qb_result_sha256="a" * 64,
                qb_result_ref="unchanged.json",
            )
            status = "SANDBOX_QB_PASS" if kind == "pass" else "SANDBOX_QB_FAILED"
        state.append_status(self.db, key, status)


@pytest.fixture
def c(tmp_path, monkeypatch):
    return Campaign(tmp_path, monkeypatch)


def test_submitted_bound_and_profile(c):
    code, rows = c.run()
    assert (code, rows[0]["action"], rows[0]["status"]) == (0, "submitted_bound", "QB_TRIGGERED"), (
        c.err.getvalue()
    )
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == [
        "SUBMITTED",
        "BUILD_BOUND",
    ]
    profile = state.qb_profile(c.db, "tizen_base")
    assert profile["profile_sha256"] == hashlib.sha256(profile["profile_json"].encode()).hexdigest()
    assert json.loads(profile["profile_json"])["form"]["SNAPSHOT_NUM"] == "snap-A"
    assert [x["command"] for x in c.commands()] == [
        "login",
        "open_form",
        "fill",
        "submit",
        "read",
        "close",
    ]


@pytest.mark.parametrize("kind", ["none", "failed-submit", "uncertain", "bound", "pass", "fail"])
@pytest.mark.parametrize("retrigger", [False, True])
def test_idempotency_every_cell(c, kind, retrigger):
    c.seed(kind)
    old_requests = c.sql("SELECT * FROM campaign_qb_requests")
    old_events = c.sql("SELECT * FROM campaign_qb_events")
    submit = kind in {"none", "failed-submit"} or retrigger and kind in {"uncertain", "fail"}
    reject = retrigger and kind in {"bound", "pass"}
    code, rows = c.run(retrigger=retrigger)
    assert code == (4 if reject else 0), c.err.getvalue()
    assert rows[0]["action"] == (
        "submitted_bound"
        if submit
        else "rejected"
        if reject
        else "already_passed"
        if kind == "pass"
        else "already_requested"
    )
    assert sum(x["command"] == "submit" for x in c.commands()) == int(submit)
    assert len(c.sql("SELECT * FROM campaign_qb_requests")) == len(old_requests) + int(submit)
    assert c.sql("SELECT * FROM campaign_qb_requests")[: len(old_requests)] == old_requests
    assert c.sql("SELECT * FROM campaign_qb_events")[: len(old_events)] == old_events
    if reject:
        assert rows[0]["error_code"] == "REJECTED_QB_REQUEST_PENDING"
    if not submit:
        assert c.starts == 0


@pytest.mark.parametrize("fault", ["status", "derive", "push", "result", "sha", "ref"])
def test_precondition_rejections(c, fault):
    if fault == "status":
        state.append_status(c.db, "u1", "REPAIR_ROUND_RUNNING")
    elif fault in {"derive", "push"}:
        c.sql("DELETE FROM campaign_gate_events WHERE event_type=?", (fault.upper(),))
    else:
        push = dict(c.units["u1"]["push"])
        push.update(
            {"result": "failed"}
            if fault == "result"
            else {"pushed_sha": "f" * 40}
            if fault == "sha"
            else {"ref": "refs/heads/main"}
        )
        state.append_event(c.db, "u1", "PUSH", push)
    before = c.snapshot()
    code, rows = c.run()
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_SANDBOX_NOT_BOUND"), c.err.getvalue()
    assert c.snapshot() == before and c.starts == 0


def test_three_units_middle_fill_failure(c):
    c.add("u2")
    c.add("u3")
    before = c.snapshot()
    replies = (
        c.replies()
        + [c.replies("u2", 2)[0], {"ok": False, "error": "QB_FORM_READBACK_MISMATCH"}]
        + c.replies("u3", 3, "102")
    )
    code, rows = c.run(replies, units=["u1", "u2", "u3"])
    assert code == 4, c.err.getvalue()
    assert [r["action"] for r in rows] == ["submitted_bound", "rejected", "submitted_bound"]
    names = [x["command"] for x in c.commands()]
    assert (names.count("login"), names.count("open_form"), names.count("submit")) == (1, 3, 2)
    assert len(c.sql("SELECT * FROM campaign_qb_requests")) == 2
    after = c.snapshot()
    for table in before:
        assert [r for r in before[table] if r.get("campaign_unit_key") == "u2"] == [
            r for r in after[table] if r.get("campaign_unit_key") == "u2"
        ]


@pytest.mark.parametrize("frozen", ["@freeze", "snap-A"])
@pytest.mark.parametrize(
    "selected,display",
    [
        (["snap-B"], "snap-B"),
        (["snap-C"], "snap-C"),
        ([], "无"),
        (["a", "b"], "a,b"),
        (None, "形态不在登记范围"),
    ],
)
def test_snapshot_templates_and_other_unit_unchanged(c, frozen, selected, display):
    c.add("u2")
    c.seed("pass", "u2")
    artifact = c.root / "unchanged.json"
    artifact.write_text('{"status":"PASS"}\n')
    if frozen != "@freeze":
        with trigger._write(c.db) as conn:
            state._insert_qb_profile_on_connection(
                conn,
                "tizen_base",
                profile_json=canonical_profile_json(c.project, frozen_snapshot=frozen),
            )
    before, raw = c.snapshot(), artifact.read_bytes()
    code, rows = c.run(
        [
            c.replies()[0],
            dict(
                ok=False,
                error="QB_FORM_VALUE_UNAVAILABLE",
                field="SNAPSHOT_NUM",
                released=False,
                snapshot_state=dict(selected=selected, option_count=3),
            ),
        ]
    )
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_SNAPSHOT_UNAVAILABLE")
    expected = (
        f"参考快照已从 snap-A 变为 {display},需在新 campaign 中处理"
        if frozen != "@freeze" and selected is not None and len(selected) == 1
        else f"参考快照不可用:冻结值 {'尚无' if frozen == '@freeze' else frozen},"
        f"当前选中项 {display},共 3 个选项;"
        + (
            "请人工核对 SNAPSHOT_NUM 下拉框后重跑"
            if frozen == "@freeze"
            else "需在新 campaign 中处理"
        )
    )
    assert rows[0]["message"] == expected
    assert c.snapshot() == before and artifact.read_bytes() == raw
    trace = next((c.root / "evidence/qb_traces").glob("*.jsonl")).read_text()
    assert expected in trace and "qb_snapshot_unavailable" in trace
    assert not any(x["command"] == "submit" for x in c.commands())


@pytest.mark.parametrize("count", [1, 4])
def test_freeze_selected_and_option_count(c, count):
    assert c.run(c.replies(count=count))[0] == 0
    trace = json.loads(next((c.root / "evidence/qb_traces").glob("*.jsonl")).read_text())
    assert trace["snapshot_option_count"] == count and trace["first_freeze"] is True


@pytest.mark.parametrize("field", sorted(trigger.FORM_KEYS | {"Build Package List", "BUILD NOTES"}))
def test_each_field_readback_mismatch(c, field):
    replies = c.replies()
    key = field + ("/selection" if field in trigger._PALETTES else "/value")
    old = replies[1]["readback"][key]
    if field == "SNAPSHOT_NUM":
        c.project["form"][field] = "snap-A"
        c.save()
    replies[1]["readback"][key] = (
        old + ["extra"]
        if isinstance(old, list)
        else not old
        if isinstance(old, bool)
        else old + " "
    )
    code, rows = c.run(replies)
    assert code == 4
    assert rows[0]["error_code"] == (
        "REJECTED_QB_SNAPSHOT_UNAVAILABLE"
        if field == "SNAPSHOT_NUM"
        else "REJECTED_QB_FORM_MISMATCH"
    )
    assert c.sql("SELECT * FROM campaign_qb_requests") == []


@pytest.mark.parametrize(
    "fault", ["marker", "target-two", "target-missing", "marker-missing", "bound-elsewhere"]
)
def test_landed_binding_mismatch(c, fault):
    changes = {
        "marker": {"BUILD_NOTES": "wrong"},
        "target-two": {"BUILD_PKG_LIST_MODIFY": "x@y\nz@q"},
        "target-missing": {"BUILD_PKG_LIST_MODIFY": None},
        "marker-missing": {"BUILD_NOTES": None},
    }
    if fault == "bound-elsewhere":
        c.add("u2")
        seq = state.create_qb_request(c.db, "u2", request_id="other", sbs_target="u2@sha")
        state.append_qb_event(c.db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id="100")
    code, rows = c.run(c.replies(changes=changes.get(fault)))
    assert (code, rows[0]["action"], rows[0]["error_code"]) == (
        5,
        "submit_uncertain",
        "REJECTED_QB_BINDING_MISMATCH",
    )
    assert rows[0]["status"] == "QB_REQUESTED"
    assert not c.sql(
        "SELECT 1 FROM campaign_qb_events WHERE request_seq=? AND event_type='BUILD_BOUND'",
        (rows[0]["request_seq"],),
    )


@pytest.mark.parametrize(
    "reply",
    [
        dict(ok=True, released=True, landed="unknown", observed="<other>", messages=[]),
        "EXIT",
        "INVALID_JSON",
    ],
)
def test_uncertain_and_rerun(c, reply):
    code, rows = c.run(c.replies()[:2] + [reply])
    assert (code, rows[0]["error_code"]) == (5, "QB_SUBMIT_UNCERTAIN")
    assert "--request-id" in rows[0]["message"] and "<other>" in rows[0]["message"]
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == ["SUBMITTED"]
    assert c.run()[1][0]["action"] == "already_requested"
    assert not any(x["command"] == "submit" for x in c.commands())


def test_not_released_allows_new_request(c):
    code, rows = c.run(c.replies()[:2] + [dict(ok=False, released=False, error="QB_FORM_CHANGED")])
    assert code == 5 and rows[0]["status"] == "QB_SUBMIT_FAILED"
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == ["SUBMITTED"]
    assert c.run(c.replies(request=2))[0] == 0
    assert len(c.sql("SELECT * FROM campaign_qb_requests")) == 2
    assert sum(x["command"] == "submit" for x in c.commands()) == 1


@pytest.mark.parametrize("error", ["QB_LOGIN_TIMEOUT", "QB_LOGIN_ABORTED"])
def test_login_failure_all_remaining_no_writes(c, error):
    c.add("u2")
    before = c.snapshot()
    code, rows = c.run(units=["u1", "u2"], login=dict(ok=False, error=error))
    assert code == 5 and all(
        r["action"] == "submit_failed" and r["error_code"] == error for r in rows
    )
    assert c.snapshot() == before and c.starts == 1


@pytest.mark.parametrize("point", ["status", "request", "push", "same-profile", "other-profile"])
def test_intent_concurrent_recheck(c, point):
    original = trigger._intent

    def race(db, snap, profile, request_id, target):
        if point == "status":
            state.append_status(db, "u1", "KB_APPENDED")
        elif point == "request":
            state.create_qb_request(db, "u1", request_id="racer", sbs_target=target)
        elif point == "push":
            state.append_event(db, "u1", "PUSH", c.units["u1"]["push"])
        else:
            with trigger._write(db) as conn:
                state._insert_qb_profile_on_connection(
                    conn,
                    "tizen_base",
                    profile_json=profile
                    if point == "same-profile"
                    else profile.replace("snap-A", "snap-B"),
                )
        before = c.snapshot()
        try:
            return original(db, snap, profile, request_id, target)
        except trigger._Rejected:
            assert c.snapshot() == before
            raise

    c.mp.setattr(trigger, "_intent", race)
    code, rows = c.run()
    expected = (
        None
        if point == "same-profile"
        else "REJECTED_QB_PARAMS_CHANGED"
        if point == "other-profile"
        else "REJECTED_STATE_INCONSISTENT"
    )
    assert rows[0]["error_code"] == expected, c.err.getvalue()
    assert sum(x["command"] == "submit" for x in c.commands()) == (point == "same-profile")


@pytest.mark.parametrize("point", ["intent-mid", "before-submit", "after-submit", "after-bind"])
def test_crash_windows(c, point):
    class Crash(BaseException):
        pass

    with c.mp.context() as patch:
        if point == "intent-mid":
            original = state._append_status_on_connection

            def status(conn, key, value, *args, **kwargs):
                if value == "QB_REQUESTED":
                    raise Crash()
                return original(conn, key, value, *args, **kwargs)

            patch.setattr(state, "_append_status_on_connection", status)
        elif point == "after-bind":
            original_bind = trigger._bind

            def bind(*args):
                original_bind(*args)
                raise Crash()

            patch.setattr(trigger, "_bind", bind)
        else:
            original_command = trigger.QbBrowser.command

            def command(agent, name, **fields):
                if name == "submit":
                    if point == "after-submit":
                        original_command(agent, name, **fields)
                    raise Crash()
                return original_command(agent, name, **fields)

            patch.setattr(trigger.QbBrowser, "command", command)
        with pytest.raises(Crash):
            c.run()
    expected = (
        []
        if point == "intent-mid"
        else ["SUBMITTED", "BUILD_BOUND"]
        if point == "after-bind"
        else ["SUBMITTED"]
    )
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == expected
    assert len(c.sql("SELECT * FROM campaign_qb_requests")) == (point != "intent-mid")
    assert len(c.sql("SELECT * FROM campaign_qb_profiles")) == (point != "intent-mid")
    code, rows = c.run(c.replies(request=2))
    assert code == 0
    assert rows[0]["action"] == (
        "submitted_bound" if point == "intent-mid" else "already_requested"
    )


def test_transport_isolation(c):
    main = c.root / "ws" / trigger._unit_hash("u1") / "src"
    main.mkdir(parents=True)
    git(main, "init", "-q")
    c.add("wrong")
    wrong_repo = c.units["wrong"]["remote"]
    wrong_sha = git(
        wrong_repo, "commit-tree", git(wrong_repo, "mktree", input=""), input="forged\n"
    )
    git(wrong_repo, "update-ref", "refs/heads/sandbox/test", wrong_sha)
    assert wrong_sha != c.units["u1"]["sha"]
    remote, wrong = str(c.units["u1"]["remote"]), str(c.units["wrong"]["remote"])
    git(main, "config", "remote." + remote + ".url", wrong)
    git(main, "config", "url." + wrong + ".insteadOf", remote)
    git(main, "config", "url." + wrong + ".pushInsteadOf", remote)
    assert c.run()[0] == 0, c.err.getvalue()
    calls = [(args, env) for args, env in c.calls if args[0] == "git"]
    assert any("ls-remote" in args for args, _ in calls)
    for args, env in calls:
        assert str(main) not in args and "--git-dir=" + str(main) not in args
        for item in (
            "core.hooksPath=/dev/null",
            "core.fsmonitor=false",
            "core.askPass=",
            "credential.helper=",
            "push.followTags=false",
            "push.recurseSubmodules=no",
            "push.gpgSign=false",
            "push.pushOption=",
        ):
            assert item in args
        assert env["GIT_CONFIG_NOSYSTEM"] == "1" and env["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert not (main.parent / ".transport").exists()


def test_sha256_remote_residual(tmp_path, monkeypatch):
    campaign = Campaign(tmp_path, monkeypatch, object_format="sha256")
    code, rows = campaign.run()
    if code == 0:
        assert rows[0]["action"] == "submitted_bound"
        assert rows[0]["sbs_target"] == "u1@" + campaign.units["u1"]["sha"]
        outcome = "SHA_MATCHED"
    else:
        assert (code, rows[0]["error_code"]) == (4, "REJECTED_SANDBOX_NOT_BOUND")
        assert campaign.sql("SELECT * FROM campaign_qb_requests") == []
        outcome = "REJECTED_SANDBOX_NOT_BOUND"
    calls = [args for args, _ in campaign.calls if args[0] == "git"]
    assert any("ls-remote" in args for args in calls)
    for args in calls:
        assert "--show-object-format" not in args
        assert not any(arg.startswith("--object-format") for arg in args)
        for index, arg in enumerate(args):
            if arg == "-C":
                assert Path(args[index + 1]).name == ".transport"
            if arg.startswith("--git-dir="):
                assert Path(arg.split("=", 1)[1]).name == ".transport"
    assert not (campaign.root / "ws" / trigger._unit_hash("u1") / ".transport").exists()
    print(json.dumps(dict(sha256_remote_outcome=outcome, git_argv=calls), sort_keys=True))


def test_wrong_remote_sha_after_fill(c):
    command = trigger.QbBrowser.command

    def changed(agent, name, **fields):
        result = command(agent, name, **fields)
        if name == "fill":
            remote = c.units["u1"]["remote"]
            other = git(remote, "commit-tree", git(remote, "mktree", input=""), input="other\n")
            git(remote, "update-ref", "refs/heads/sandbox/test", other)
        return result

    c.mp.setattr(trigger.QbBrowser, "command", changed)
    code, rows = c.run()
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_SANDBOX_NOT_BOUND")
    assert c.sql("SELECT * FROM campaign_qb_requests") == []


def test_sandbox_lock_rejects_before_agent(c):
    root = c.root / "ws" / trigger._unit_hash("u1")
    root.mkdir(parents=True)
    with (root / ".sandbox_submit.lock").open("a+") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, rows = c.run()
    assert code == 4 and rows[0]["error_code"] == "CAMPAIGN_STATE_BUSY" and c.starts == 0


@pytest.mark.parametrize(
    "fault",
    ["extra", "missing", "palette-role", "duplicate-control", "duplicate_option_text", "form"],
)
@pytest.mark.parametrize("write_failure", [False, True])
def test_form_diagnostics_preserve_error(c, fault, write_failure):
    diagnostic = dict(
        html_redacted=variables("u1@sha", "marker"), facts=dict(first_failed_check=fault)
    )
    if write_failure:
        (c.root / "evidence").write_text("not a directory")
    before = c.snapshot()
    code, rows = c.run([dict(ok=False, error="QB_FORM_CHANGED", diagnostic=diagnostic)])
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_CHANGED")
    assert c.snapshot() == before and not any(x["command"] == "submit" for x in c.commands())
    if write_failure:
        assert rows[0]["diagnostic_dir"] is None
    else:
        path = Path(rows[0]["diagnostic_dir"])
        assert (path / "page.html").read_text() == diagnostic["html_redacted"]
        assert (
            json.loads((path / "structure.json").read_text())["facts"]["first_failed_check"]
            == fault
        )


@pytest.mark.parametrize(
    "leak",
    [
        "JSESSIONID_8810=fixture-secret",
        '<input type="hidden" value="fixture-secret">',
        '<a href="/x;jsessionid=fixture-secret">x</a>',
        "<span>Welcome! fixture-secret</span>",
    ],
)
def test_sensitive_agent_page_never_written(c, leak):
    replies = c.replies()
    replies[-1]["html_redacted"] = leak
    code, rows = c.run(replies)
    assert (code, rows[0]["error_code"]) == (5, "QB_EVIDENCE_REDACTION_FAILED")
    assert rows[0]["action"] == "submit_uncertain"
    assert "fixture-secret" not in json.dumps(rows) + c.err.getvalue()
    for path in (c.root / "evidence").rglob("*"):
        if path.is_file():
            assert b"fixture-secret" not in path.read_bytes()
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == ["SUBMITTED"]


@pytest.mark.parametrize(
    "key,new",
    [
        ("BUILD_TYPE", "Partial"),
        ("REPO_TYPE", "NEW"),
        ("BUILD_REFERENCE", "Live"),
        ("SNAPSHOT_NUM", "snap-B"),
        ("overview_id", 1918),
        ("project_name", "Other"),
        ("configuration_path", "root/other/RBS/TRIGGER"),
        ("qb_pass_requires_accept", True),
    ],
)
def test_changed_config_rejected_before_agent(c, key, new):
    assert c.run()[0] == 0
    c.add("u2")
    (c.project["form"] if key in c.project["form"] else c.project)[key] = new
    c.save()
    before, starts = c.snapshot(), c.starts
    code, rows = c.run(units=["u2"])
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_PARAMS_CHANGED")
    assert c.starts == starts and c.snapshot() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("CHILD_CONFIGURATIONS", ["aarch64"]),
        ("CHILD_CONFIGURATIONS", ["aarch64:x86_64"]),
        ("CHILD_CONFIGURATIONS", [ARCHITECTURES, ARCHITECTURES]),
        ("CHILD_CONFIGURATIONS", [ARCHITECTURES, "other"]),
        ("Immediate Stop With Error", False),
        ("TARGET_IMAGE", ["image"]),
        ("configuration_path", "root/wrong/TRIGGER"),
        ("configuration_path", "wrong/RBS/TRIGGER"),
        ("overview_id", 0),
        ("overview_id", True),
        ("extra", "x"),
        ("missing", None),
        ("PROJECT_BRANCH", "wrong"),
        ("Add Package List", "x"),
        ("Remove Package List", "x"),
    ],
)
def test_invalid_config_never_starts_agent(c, field, value):
    if field == "missing":
        del c.project["form"]["REPO_TYPE"]
    else:
        (c.project if field in {"configuration_path", "overview_id"} else c.project["form"])[
            field
        ] = value
    c.save()
    before = c.snapshot()
    code, rows = c.run()
    assert (code, rows[0]["error_code"]) == (2, "INVALID_ARGS")
    assert c.starts == 0 and c.snapshot() == before


@pytest.mark.parametrize("enabled", [None, False])
def test_project_not_ready(c, enabled):
    if enabled is None:
        c.data["qb"]["projects"] = {}
    else:
        c.project["enabled"] = False
    c.save()
    code, rows = c.run([])
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_PROJECT_NOT_READY") and c.starts == 0


def test_two_branches_freeze_separately_and_reuse(c):
    c.add("u2")
    c.add("u3", "tizen")
    other = copy.deepcopy(c.project)
    other["form"].update(PROJECT_BRANCH="tizen", SNAPSHOT_NUM="snap-C")
    c.data["qb"]["projects"]["tizen"] = other
    c.save()
    code, rows = c.run(
        c.replies() + c.replies("u2", 2, "101") + c.replies("u3", 3, "102", "snap-C"),
        units=["u1", "u2", "u3"],
    )
    assert code == 0, c.err.getvalue()
    assert len(c.sql("SELECT * FROM campaign_qb_profiles")) == 2
    assert (
        json.loads(state.qb_profile(c.db, "tizen")["profile_json"])["form"]["SNAPSHOT_NUM"]
        == "snap-C"
    )


def test_new_campaign_changed_config(c):
    c.project["form"].update(BUILD_TYPE="Partial", SNAPSHOT_NUM="snap-B")
    c.save()
    assert c.run(c.replies(current="snap-B"))[0] == 0


@pytest.mark.parametrize(
    "fault",
    [
        "unlinked",
        "old-round",
        "different-arch",
        "different-unit",
        "base_commit",
        "project",
        "spec_name",
        "branch",
    ],
)
def test_selection_matches_unit_without_held(c, fault):
    if fault == "unlinked":
        c.sql("DELETE FROM campaign_verifications WHERE verification_id='u1-v0'")
    elif fault == "old-round":
        state.create_round(
            c.db, "u1", round_index=2, edit_spec_ref="new", edit_spec_sha256="f" * 64
        )
    elif fault == "different-arch":
        state.create_round(
            c.db, "u1", round_index=2, edit_spec_ref="new", edit_spec_sha256="f" * 64
        )
        c.sql(
            "UPDATE campaign_verifications SET round_index=2,arch_norm='x86_64',edit_spec_sha256=? "
            "WHERE verification_id='u1-v0'",
            ("f" * 64,),
        )
    elif fault == "different-unit":
        c.add("u2")
        c.sql("DELETE FROM campaign_verifications WHERE verification_id='u2-v0'")
        c.sql(
            "UPDATE campaign_verifications SET campaign_unit_key='u2' WHERE verification_id='u1-v0'"
        )
    else:
        c.sql(f"UPDATE campaign_units SET {fault}='other' WHERE campaign_unit_key='u1'")
    before = c.snapshot()
    code, rows = c.run()
    assert code == 4 and c.snapshot() == before and c.starts == 0
    assert rows[0]["error_code"] == (
        "REJECTED_ROUND_SUPERSEDED" if fault == "old-round" else "REJECTED_ARCH_AGGREGATE_MISMATCH"
    )


@pytest.mark.parametrize("point", ["intent", "not-released", "binding"])
def test_write_transaction_rollback(c, point):
    original = state._append_status_on_connection

    def fail(conn, key, status, *args, **kwargs):
        if (
            status
            == {
                "intent": "QB_REQUESTED",
                "not-released": "QB_SUBMIT_FAILED",
                "binding": "QB_TRIGGERED",
            }[point]
        ):
            raise RuntimeError("injected transaction failure")
        return original(conn, key, status, *args, **kwargs)

    c.mp.setattr(state, "_append_status_on_connection", fail)
    replies = c.replies()
    if point == "not-released":
        replies[2] = dict(ok=False, released=False, error="QB_FORM_CHANGED")
    code, rows = c.run(replies)
    assert code == 5 and rows[0]["error_code"] == "INTERNAL_ERROR"
    assert rows[0]["action"] == ("rejected" if point == "intent" else "submit_uncertain")
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == (
        [] if point == "intent" else ["SUBMITTED"]
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {},
        [1],
        [{"verification_ids": ["a", "a", "b"]}],
        [{"verification_ids": ["a", "b", "c"], "extra": 1}],
    ],
)
def test_invalid_units_file_before_agent(c, bad):
    path = c.root / "invalid.json"
    path.write_text(json.dumps(bad))
    before = c.snapshot()
    code, rows = trigger.qb_trigger(
        trigger.QbTriggerOptions(c.db.path, c.root / "evidence", c.config, units_file=path),
        stderr=io.StringIO(),
    )
    assert code == 2 and rows[0]["error_code"] == "INVALID_ARGS"
    assert c.snapshot() == before and c.starts == 0


def test_cli_missing_arguments():
    out = io.StringIO()
    assert cli.main(["qb-trigger"], stdout=out, stderr=io.StringIO()) == 2
    assert json.loads(out.getvalue())[0]["error_code"] == "INVALID_ARGS"


@pytest.mark.parametrize(
    "field,value",
    [
        ("Build Package List", "u1@sha\nother@sha"),
        ("Add Package List", "pkg"),
        ("CHILD_CONFIGURATIONS", [ARCHITECTURES, "other"]),
    ],
)
def test_readback_extra_payloads(c, field, value):
    replies = c.replies()
    replies[1]["readback"][field + ("/selection" if field in trigger._PALETTES else "/value")] = (
        value
    )
    before = c.snapshot()
    code, rows = c.run(replies)
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_MISMATCH")
    assert c.snapshot() == before


def test_palette_recorder_mismatch_from_agent(c):
    before = c.snapshot()
    code, rows = c.run(
        [
            c.replies()[0],
            dict(ok=False, error="QB_FORM_READBACK_MISMATCH", field="CHILD_CONFIGURATIONS"),
        ]
    )
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_MISMATCH")
    assert c.snapshot() == before


def test_diagnostic_post_write_check_removes_files(c):
    original = trigger.PageRedactor.check_bytes
    html_checks = 0

    def check(redactor, raw):
        nonlocal html_checks
        if raw.startswith(b"<table>"):
            html_checks += 1
            if html_checks == 3:
                raise trigger.EvidenceRedactionError("synthetic")
        return original(redactor, raw)

    c.mp.setattr(trigger.PageRedactor, "check_bytes", check)
    code, rows = c.run(
        [
            dict(
                ok=False,
                error="QB_FORM_CHANGED",
                diagnostic=dict(html_redacted=variables("pkg@sha", "marker"), facts={}),
            )
        ]
    )
    assert html_checks == 3
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_CHANGED")
    assert rows[0]["diagnostic_dir"] is None
    assert not list((c.root / "evidence").rglob("*.html"))


@pytest.mark.parametrize("fault", ["superseded", "already-bound"])
def test_binding_transaction_rechecks(c, fault):
    original = trigger._bind

    def race(db, key, seq, build):
        if fault == "superseded":
            state.create_qb_request(db, key, request_id="racer", sbs_target="u1@sha")
        else:
            state.append_qb_event(db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id="101")
        before = c.snapshot()
        with pytest.raises(trigger._Rejected) as error:
            original(db, key, seq, build)
        assert c.snapshot() == before
        raise error.value

    c.mp.setattr(trigger, "_bind", race)
    code, rows = c.run()
    assert (code, rows[0]["error_code"]) == (5, "REJECTED_QB_BINDING_MISMATCH")


@pytest.mark.parametrize("phase", ["open_form", "fill"])
def test_duplicate_option_diagnostic_is_written_without_snapshot_state(c, phase):
    response = dict(
        ok=False,
        error="QB_FORM_CHANGED",
        diagnostic=dict(
            html_redacted=variables("u1@sha", "marker"),
            facts=dict(first_failed_check="duplicate_option_text"),
        ),
    )
    before = c.snapshot()
    code, rows = c.run(([c.replies()[0]] if phase == "fill" else []) + [response])
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_CHANGED")
    assert rows[0]["message"] is None and c.snapshot() == before
    assert (
        json.loads((Path(rows[0]["diagnostic_dir"]) / "structure.json").read_text())["facts"][
            "first_failed_check"
        ]
        == "duplicate_option_text"
    )


def test_correct_sha_only_in_other_repository_rejected(c):
    c.add("other")
    assert c.units["other"]["sha"] == c.units["u1"]["sha"]
    remote = c.units["u1"]["remote"]
    other = git(remote, "commit-tree", git(remote, "mktree", input=""), input="target mismatch\n")
    git(remote, "update-ref", "refs/heads/sandbox/test", other)
    code, rows = c.run()
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_SANDBOX_NOT_BOUND")
    assert not any(x["command"] == "submit" for x in c.commands())


def test_first_freeze_with_explicit_config_snapshot_uses_no_frozen_value(c):
    c.project["form"]["SNAPSHOT_NUM"] = "configured-snapshot"
    c.save()
    before = c.snapshot()
    code, rows = c.run(
        [
            c.replies()[0],
            dict(
                ok=False,
                error="QB_FORM_VALUE_UNAVAILABLE",
                field="SNAPSHOT_NUM",
                released=False,
                snapshot_state=dict(selected=["current-snapshot"], option_count=1),
            ),
        ]
    )
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_SNAPSHOT_UNAVAILABLE")
    assert rows[0]["message"] == (
        "参考快照不可用:冻结值 尚无,当前选中项 current-snapshot,共 1 个选项;"
        "请人工核对 SNAPSHOT_NUM 下拉框后重跑"
    )
    assert c.snapshot() == before
