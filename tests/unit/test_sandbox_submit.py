from __future__ import annotations

import fcntl
import hashlib
import io
import json
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from ci_triage import campaign_state as state
from ci_triage import cli
from ci_triage import sandbox_submit as submit
from tizen_ci_shared.state import StateDatabase, VerificationRecord, write_pass_record
from tizen_ci_shared.workspace import PROTECTED_FILENAME


def git(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args], check=True, text=True, capture_output=True
    ).stdout.strip()


class Campaign:
    def __init__(self, root, monkeypatch):
        self.root = root
        self.key = "sandbox-unit"
        self.db = StateDatabase(root / "state.sqlite3")
        self.ws = root / "workspace"
        self.unit_root = self.ws / submit._unit_hash(self.key)
        self.src = self.unit_root / "src"
        self.src.mkdir(parents=True)
        git(self.src, "init", "-q")
        git(self.src, "config", "user.name", "Test")
        git(self.src, "config", "user.email", "test@example.com")
        (self.src / "file.c").write_text("int value = 1;\n")
        git(self.src, "add", "file.c")
        git(self.src, "commit", "-qm", "base")
        self.base = git(self.src, "rev-parse", "HEAD")
        git(self.src, "remote", "add", "origin", "ssh://unused.example/project")
        (self.src / ".campaign_clone").write_text(
            json.dumps(
                dict(
                    unit_key=self.key,
                    project="project",
                    base_commit=self.base,
                )
            )
        )
        self.spec = root / "edit.json"
        self.spec.write_text(
            json.dumps(
                dict(
                    schema_version="gbs_patch_suggest/edit-spec/v1",
                    patch_name="patch",
                    edits=[dict(file="file.c", old="int value = 1;", new="int value = 2;")],
                )
            )
        )
        self.spec_sha = hashlib.sha256(self.spec.read_bytes()).hexdigest()
        state.create_unit(
            self.db,
            campaign_unit_key=self.key,
            submission_identity_key="a" * 64,
            primary_arch="standard-aarch64",
            failed_arches=["standard-aarch64"],
            toolchain_profile="clang",
            ci_evidence_ref="evidence.json",
            ci_evidence_sha256="e" * 64,
            max_rounds=5,
            max_build_invocations=15,
            ci_system="quickbuild",
            source_build_id="1",
            project="project",
            branch="tizen",
            spec_name="project",
            base_commit=self.base,
        )
        state.create_round(
            self.db,
            self.key,
            round_index=1,
            edit_spec_ref=str(self.spec),
            edit_spec_sha256=self.spec_sha,
        )
        state.append_status(self.db, self.key, "REPAIR_ROUND_RUNNING")
        self.copies = []
        for index, arch in enumerate(submit.ARCH_ORDER):
            path = self.unit_root / arch / "copy"
            path.parent.mkdir(parents=True)
            shutil.copytree(self.src, path)
            (path / "file.c").write_text("int value = 2;\n")
            git(path, "add", "file.c")
            git(path, "commit", "-qm", "verified")
            (path / PROTECTED_FILENAME).write_text("protected\n")
            self.tree = git(path, "rev-parse", "HEAD^{tree}")
            record = VerificationRecord(
                verification_id=f"v{index}",
                result="PASS",
                timestamp="2026-10-09T00:00:00Z",
                failure_key=f"failure-{arch}",
                base_commit=self.base,
                verified_commit_sha=git(path, "rev-parse", "HEAD"),
                verified_tree_sha=self.tree,
                canonical_diff_sha256="d" * 64,
                patch_sha256="d" * 64,
                edit_spec_sha256=self.spec_sha,
                project="project",
                branch="tizen",
                spec_name="project",
                arch=f"standard-{arch}",
                gbs_conf_sha256="f" * 64,
                build_log_sha256="b" * 64,
                worktree_path=str(path),
                command_line="gbs build",
            )
            write_pass_record(self.db, record)
            self.sql(
                "INSERT INTO campaign_verifications "
                "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
                "edit_spec_sha256, campaign_schema_version, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    self.key,
                    record.arch,
                    arch,
                    record.verification_id,
                    1,
                    self.spec_sha,
                    "campaign/v1",
                    "2026-10-09T00:00:00Z",
                ),
            )
            self.copies.append(path)
        self.remote_base = root / "remotes"
        self.remote = self.remote_base / "project"
        self.remote.mkdir(parents=True)
        git(self.remote, "init", "--bare", "-q")
        self.hook = root / "commit-msg"
        self.hook.write_text(
            '#!/bin/sh\nprintf "\\nChange-Id: I'
            '1111111111111111111111111111111111111111\\n" >> "$1"\n'
        )
        self.config = root / "config.yaml"
        self.config.write_text(
            yaml.safe_dump(
                dict(
                    campaign_workspace=str(self.ws),
                    gerrit_ssh_base=str(self.remote_base),
                    git_author_identity="Author <author@example.com>",
                    git_committer_identity="Committer <committer@example.com>",
                    gerrit_commit_msg_hook=str(self.hook),
                    gerrit_commit_msg_hook_sha256=hashlib.sha256(
                        self.hook.read_bytes()
                    ).hexdigest(),
                )
            )
        )
        self.options = submit.SandboxSubmitOptions(
            "v0,v1,v2", self.db.path, self.config, "sandbox/test", "correct value", "generated"
        )
        self.calls = []
        original = subprocess.Popen

        def counted(command, *args, **kwargs):
            self.calls.append(list(command))
            return original(command, *args, **kwargs)

        monkeypatch.setattr(subprocess, "Popen", counted)

    def sql(self, sql, params=(), *, foreign_keys=True):
        conn = self.db.connect()
        if not foreign_keys:
            conn.execute("PRAGMA foreign_keys=OFF")
        try:
            with conn:
                return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def statuses(self):
        return [
            tuple(r)
            for r in self.sql(
                "SELECT status,reason,arch_norm FROM campaign_status_log ORDER BY log_id"
            )
        ]

    def events(self):
        return [
            tuple(r)
            for r in self.sql(
                "SELECT event_type,payload_json FROM campaign_gate_events ORDER BY event_id"
            )
        ]

    def run(self, **kwargs):
        self.calls.clear()
        return submit.sandbox_submit(replace(self.options, **kwargs))

    def pushes(self):
        return [c for c in self.calls if "push" in c]

    def hooks(self):
        return [c for c in self.calls if c[0] == "sh"]


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    return Campaign(tmp_path, monkeypatch)


def test_normal_path_and_idempotent_rerun(campaign, monkeypatch):
    c = campaign
    append = state.append_event

    def cache_first(db, key, kind, payload):
        if kind == "DERIVE":
            assert c.sql("SELECT count(*) FROM campaign_change_ids")[0][0] == 1
        return append(db, key, kind, payload)

    monkeypatch.setattr(state, "append_event", cache_first)
    result = c.run()
    assert result.exit_code == 0, result.payload
    assert result.payload["action"] == "pushed"
    sha = result.payload["derived_commit_sha"]
    assert git(c.remote, "rev-parse", "refs/heads/sandbox/test") == sha
    assert git(c.remote, "rev-parse", f"{sha}^{{tree}}") == c.tree
    raw = git(c.remote, "cat-file", "commit", sha).split("\n\n", 1)[1]
    assert raw == "Fix build error for clang compiler: correct value\n\nChange-Id: I" + "1" * 40
    assert [r[0] for r in c.statuses()] == [
        "REPAIR_ROUND_RUNNING",
        "LOCAL_3ARCH_PASS",
        "SANDBOX_PUSHING",
        "SANDBOX_PUSHED",
    ]
    assert [r[0] for r in c.events()] == ["POLICY", "DERIVE", "PUSH"]
    assert all((p / PROTECTED_FILENAME).is_file() for p in c.copies)
    assert len(c.pushes()) == len(c.hooks()) == 1
    before = c.statuses(), c.events()
    result = c.run(message_brief="ignored", edit_source_kind="suppress")
    assert result.exit_code == 0 and result.payload["action"] == "already_pushed"
    assert result.payload["reused"] == dict(message_brief=True, edit_source_kind=True)
    assert result.payload["derived_commit_sha"] == sha
    assert (c.statuses(), c.events()) == before
    assert not c.pushes() and not c.hooks()


def assert_rejected(c, result, code, *, reason=None, arch=None, states=None, events=None):
    assert result.exit_code == 4, result.payload
    assert result.payload["error_code"] == code
    assert not c.pushes() and not c.hooks()
    if reason:
        assert c.statuses()[-1] == ("HELD_FOR_INVESTIGATION", reason, arch)
        assert result.payload["action"] == "held"
        assert result.payload["held"]["arch_norm"] == arch
    else:
        assert not any(row[0] == "HELD_FOR_INVESTIGATION" for row in c.statuses())
    if states is not None:
        assert [row[0] for row in c.statuses()] == states
    if events is not None:
        assert [row[0] for row in c.events()] == events


@pytest.mark.parametrize(
    "field,value",
    [
        ("message_brief", None),
        ("edit_source_kind", None),
        ("message_brief", "a\nb"),
        ("message_brief", "a\tb"),
        ("message_brief", "x" * 101),
        ("edit_source_kind", "unknown"),
        ("verification_ids", "v0,v1"),
        ("verification_ids", "v0,v1,v1"),
        ("verification_ids", "v0,,v2"),
    ],
)
def test_invalid_parameters_are_zero_write(campaign, field, value):
    c = campaign
    before = c.statuses(), c.events()
    result = c.run(**{field: value})
    assert result.exit_code == 2
    assert result.payload["action"] == "invalid_args"
    assert result.payload["error_code"] == "INVALID_ARGS"
    assert (c.statuses(), c.events()) == before
    assert not c.pushes() and not c.hooks()
    assert not c.sql("SELECT * FROM campaign_change_ids")
    assert git(c.remote, "for-each-ref") == ""


@pytest.mark.parametrize(
    "branch",
    [
        "master",
        "refs/heads/sandbox/a",
        "sandbox/",
        "sandbox//a",
        "sandbox/a/../b",
        "sandbox/a b",
        "sandbox/a.lock",
        "sandbox/a@{1}",
    ],
)
def test_branch_rejected_before_writing(campaign, branch):
    before = campaign.statuses(), campaign.events()
    result = campaign.run(sandbox_branch=branch)
    assert result.exit_code == 2 and result.payload["error_code"] == "INVALID_BRANCH_NAME"
    assert (campaign.statuses(), campaign.events()) == before
    assert not campaign.pushes() and not campaign.hooks()


@pytest.mark.parametrize(
    "edit,code",
    [
        ("missing", "REJECTED_ARCH_AGGREGATE_MISMATCH"),
        ("round", "REJECTED_ARCH_AGGREGATE_MISMATCH"),
        ("unit", "REJECTED_ARCH_AGGREGATE_MISMATCH"),
        ("superseded", "REJECTED_ROUND_SUPERSEDED"),
        ("HELD_FOR_INVESTIGATION", "REJECTED_STATE_INCONSISTENT"),
        ("KB_APPENDED", "REJECTED_STATE_INCONSISTENT"),
        ("DENIED", "REJECTED_STATE_INCONSISTENT"),
    ],
)
def test_selection_errors_do_not_freeze_unit(campaign, edit, code):
    c = campaign
    if edit == "missing":
        c.sql("DELETE FROM campaign_verifications WHERE verification_id='v1'")
    elif edit == "round":
        c.sql(
            "UPDATE campaign_verifications SET round_index=2 WHERE verification_id='v1'",
            foreign_keys=False,
        )
    elif edit == "unit":
        conn = c.db.connect()
        conn.execute("PRAGMA foreign_keys=OFF")
        with conn:
            conn.execute(
                "UPDATE campaign_verifications SET campaign_unit_key='other' "
                "WHERE verification_id='v1'"
            )
        conn.close()
    elif edit == "superseded":
        state.create_round(
            c.db,
            c.key,
            round_index=2,
            edit_spec_ref=str(c.root / "new.json"),
            edit_spec_sha256="2" * 64,
        )
    else:
        state.append_status(
            c.db,
            c.key,
            edit,
            "state_inconsistent" if edit.startswith("HELD") else None,
            "aarch64" if edit.startswith("HELD") else None,
        )
    before = c.statuses(), c.events()
    result = c.run()
    assert result.exit_code == 4 and result.payload["error_code"] == code
    assert (c.statuses(), c.events()) == before
    assert not c.pushes() and not c.hooks()


@pytest.mark.parametrize(
    "relative",
    [".sandbox_submit.lock", *[arch + "/.repair_step.lock" for arch in submit.ARCH_ORDER]],
)
def test_four_locks_are_shared_and_nonblocking(campaign, relative):
    c = campaign
    path = c.unit_root / relative
    before = c.statuses(), c.events()
    with path.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = c.run()
        assert result.exit_code == 4 and result.payload["action"] == "busy"
    assert (c.statuses(), c.events()) == before
    assert not c.pushes() and not c.hooks()


def test_lock_selection_is_reread_and_repair_step_contends(campaign, monkeypatch):
    from ci_triage.campaign_repair_step import _repair_step_lock

    c = campaign
    original = submit._locks

    @contextmanager
    def modified(root):
        with original(root):
            with pytest.raises(BlockingIOError), _repair_step_lock(root / "armv7l"):
                pytest.fail("repair-step acquired sandbox lock")
            c.sql("DELETE FROM campaign_verifications WHERE verification_id='v1'")
            yield

    monkeypatch.setattr(submit, "_locks", modified)
    result = c.run()
    assert_rejected(c, result, "REJECTED_ARCH_AGGREGATE_MISMATCH", events=[])


@pytest.mark.parametrize("field,all_rows", [("base_commit", False), ("branch", True)])
def test_aggregate_rejection_before_policy(campaign, field, all_rows):
    c = campaign
    c.sql(
        f"UPDATE verification_records SET {field}='other'"
        + ("" if all_rows else " WHERE verification_id='v1'")
    )
    result = c.run()
    assert_rejected(
        c, result, "REJECTED_ARCH_AGGREGATE_MISMATCH", reason="aggregate_mismatch", events=[]
    )


def test_rebinding_before_evaluate(campaign, monkeypatch):
    campaign.spec.write_text("{}")
    monkeypatch.setattr(submit, "evaluate", lambda *a: pytest.fail("unbound evaluate"))
    result = campaign.run()
    assert_rejected(
        campaign,
        result,
        "REJECTED_EDIT_SPEC_REBIND_MISMATCH",
        reason="edit_spec_rebind_mismatch",
        events=[],
    )


def test_forbidden_policy_is_recorded_without_derive(campaign, monkeypatch):
    c = campaign
    (c.src / "CMakeLists.txt").write_text("add_compile_options(-Werror)\n")
    git(c.src, "add", "CMakeLists.txt")
    # Rebind this fixture's base and edit before invoking the submission.
    git(c.src, "commit", "--amend", "--no-edit", "-q")
    base = git(c.src, "rev-parse", "HEAD")
    c.sql("UPDATE campaign_units SET base_commit=?", (base,))
    c.sql("UPDATE verification_records SET base_commit=?", (base,))
    marker = json.loads((c.src / ".campaign_clone").read_text())
    marker["base_commit"] = base
    (c.src / ".campaign_clone").write_text(json.dumps(marker))
    spec = json.loads(c.spec.read_text())
    spec["edits"] = [
        dict(
            file="CMakeLists.txt",
            old="add_compile_options(-Werror)",
            new="add_compile_options(-Werror -Wno-foo)",
        )
    ]
    c.spec.write_text(json.dumps(spec))
    digest = hashlib.sha256(c.spec.read_bytes()).hexdigest()
    for table in ("campaign_rounds", "campaign_verifications", "verification_records"):
        c.sql(f"UPDATE {table} SET edit_spec_sha256=?", (digest,), foreign_keys=False)
    monkeypatch.setattr(submit, "derive", lambda **kw: pytest.fail("forbidden derive"))
    result = c.run()
    assert_rejected(
        c, result, "REJECTED_SUPPRESS_POLICY", reason="suppress_policy_recheck", events=["POLICY"]
    )
    assert json.loads(c.events()[0][1])["verdict"] == "forbidden"


@pytest.mark.parametrize(
    "mutation,held",
    [
        ("tracked", "worktree_dirty"),
        ("staged", "worktree_dirty"),
        ("tree", "verification_mismatch"),
        ("marker", "verification_mismatch"),
        ("two", "worktree_dirty"),
    ],
)
def test_copy_scene_is_held_with_arch(campaign, mutation, held):
    c = campaign
    path = c.copies[1]
    if mutation == "marker":
        (path / PROTECTED_FILENAME).unlink()
    elif mutation == "tree":
        git(path, "reset", "--hard", c.base)
    else:
        (path / "file.c").write_text("changed\n")
        if mutation == "staged":
            git(path, "add", "file.c")
        if mutation == "two":
            (c.copies[2] / "file.c").write_text("changed\n")
    result = c.run()
    assert_rejected(c, result, "REJECTED_" + held.upper(), reason=held, arch="armv7l")
    if mutation == "two":
        assert "x86_64" in result.payload["reason"]


def test_missing_copy_is_worktree_lost_not_held(campaign):
    c = campaign
    shutil.rmtree(c.copies[1])
    result = c.run()
    assert_rejected(c, result, "REJECTED_WORKTREE_MISSING", events=[])
    assert result.payload["action"] == "worktree_lost"
    assert result.payload["surviving_worktrees"] == [str(c.copies[0]), str(c.copies[2])]
    assert c.statuses()[-1] == ("WORKTREE_LOST", "armv7l", None)


@pytest.mark.parametrize("mutation", ["head", "origin", "marker", "dirty"])
def test_src_identity_rejected_without_held(campaign, mutation):
    c = campaign
    if mutation == "head":
        git(c.src, "commit", "--allow-empty", "-qm", "other")
    elif mutation == "origin":
        git(c.src, "remote", "set-url", "origin", "ssh://unused.example/wrong")
    elif mutation == "marker":
        (c.src / ".campaign_clone").write_text("{}")
    else:
        (c.src / "file.c").write_text("dirty\n")
    assert_rejected(c, c.run(), "REJECTED_IDENTITY_MISMATCH", events=[])


def test_deleted_cache_rejects_without_regeneration(campaign):
    c = campaign
    first = c.run()
    assert first.exit_code == 0
    c.sql("DELETE FROM campaign_change_ids")
    result = c.run()
    assert_rejected(
        c, result, "REJECTED_STATE_INCONSISTENT", reason="state_inconsistent", arch="aarch64"
    )
    assert not c.sql("SELECT * FROM campaign_change_ids")
    assert (
        git(c.remote, "rev-parse", "refs/heads/sandbox/test") == first.payload["derived_commit_sha"]
    )


@pytest.mark.parametrize("keep_push", [False, True])
def test_remote_success_missing_bookkeeping(campaign, keep_push):
    c = campaign
    assert c.run().exit_code == 0
    c.sql("DELETE FROM campaign_status_log WHERE status='SANDBOX_PUSHED'")
    if not keep_push:
        c.sql("DELETE FROM campaign_gate_events WHERE event_type='PUSH'")
    before = len(c.events()), len(c.statuses())
    result = c.run()
    assert result.exit_code == 0 and result.payload["action"] == "pushed"
    assert len(c.events()) == before[0] + (not keep_push)
    assert len(c.statuses()) == before[1] + 1
    assert not c.hooks() and not c.pushes()


def test_remote_ref_changed_is_forced_back(campaign):
    c = campaign
    first = c.run()
    git(c.remote, "update-ref", "refs/heads/sandbox/test", c.base)
    before = len(c.events()), len(c.statuses())
    result = c.run()
    assert result.exit_code == 0
    assert result.payload["derived_commit_sha"] == first.payload["derived_commit_sha"]
    assert len(c.events()) == before[0] + 1 and len(c.statuses()) == before[1] + 2
    assert len(c.pushes()) == 1 and not c.hooks()


@pytest.mark.parametrize(
    "mutation,reason,arch",
    [
        ("branch", "aggregate_mismatch", None),
        ("gbs_conf_sha256", "aggregate_mismatch", None),
        ("link", "state_inconsistent", "aarch64"),
        ("round", "state_inconsistent", "aarch64"),
        ("unit", "state_inconsistent", "aarch64"),
        ("status", "state_inconsistent", "aarch64"),
        ("cache", "state_inconsistent", "aarch64"),
        ("dirty", "worktree_dirty", "aarch64"),
        ("edit", "edit_spec_rebind_mismatch", None),
        ("src", None, None),
        ("config", None, None),
    ],
)
def test_toctou_each_snapshot_component(campaign, monkeypatch, mutation, reason, arch):
    c = campaign
    original = submit.toctou_recheck

    def changed(*args, **kwargs):
        if mutation in {"branch", "gbs_conf_sha256"}:
            c.sql(
                f"UPDATE verification_records SET {mutation}='changed' WHERE verification_id='v1'"
            )
        elif mutation == "link":
            c.sql(
                "UPDATE campaign_verifications SET round_index=2 WHERE verification_id='v1'",
                foreign_keys=False,
            )
        elif mutation == "round":
            state.create_round(
                c.db,
                c.key,
                round_index=2,
                edit_spec_ref=str(c.root / "round2"),
                edit_spec_sha256="2" * 64,
            )
        elif mutation == "unit":
            c.sql("UPDATE campaign_units SET spec_name='changed'")
        elif mutation == "status":
            state.append_status(c.db, c.key, "DENIED")
        elif mutation == "cache":
            c.sql("DELETE FROM campaign_change_ids")
        elif mutation == "dirty":
            (c.copies[0] / "file.c").write_text("dirty\n")
        elif mutation == "edit":
            c.spec.write_text("{}")
        elif mutation == "src":
            git(c.src, "commit", "--allow-empty", "-qm", "changed")
        elif mutation == "config":
            git(c.copies[0], "config", "url./tmp/other.pushInsteadOf", str(c.remote))
        return original(*args, **kwargs)

    monkeypatch.setattr(submit, "toctou_recheck", changed)
    result = c.run()
    assert result.exit_code == 4
    assert not c.pushes()
    assert git(c.remote, "for-each-ref") == ""
    if reason:
        assert c.statuses()[-1] == ("HELD_FOR_INVESTIGATION", reason, arch)
    else:
        assert result.payload["error_code"] == (
            "REJECTED_IDENTITY_MISMATCH" if mutation == "src" else "REJECTED_UNSAFE_GIT_CONFIG"
        )


@pytest.mark.parametrize("kind", ["policy", "derive"])
def test_stored_gate_tampering_is_held(campaign, kind):
    c = campaign
    assert c.run().exit_code == 0
    if kind == "policy":
        raw = json.loads(
            c.sql("SELECT payload_json FROM campaign_gate_events WHERE event_type='POLICY'")[0][0]
        )
        raw.update(fix_strategy_final="suppress", rules_version="previous-version")
        c.sql(
            "UPDATE campaign_gate_events SET payload_json=? WHERE event_type='POLICY'",
            (json.dumps(raw),),
        )
    else:
        raw = json.loads(
            c.sql("SELECT payload_json FROM campaign_gate_events WHERE event_type='DERIVE'")[0][0]
        )
        raw["derived_commit_sha"] = "f" * 40
        c.sql(
            "INSERT INTO campaign_gate_events "
            "(campaign_unit_key,event_type,payload_json,created_at) VALUES (?,?,?,?)",
            (c.key, "DERIVE", json.dumps(raw), "2026-10-09T00:00:00Z"),
        )
    result = c.run()
    assert_rejected(
        c, result, "REJECTED_STATE_INCONSISTENT", reason="state_inconsistent", arch="aarch64"
    )
    if kind == "policy":
        assert (
            "previous-version" in result.payload["reason"]
            and "p5-policy/v1" in result.payload["reason"]
        )


def test_hook_hash_failure_then_retry(campaign):
    c = campaign
    original = c.config.read_text()
    config = yaml.safe_load(original)
    config["gerrit_commit_msg_hook_sha256"] = "0" * 64
    c.config.write_text(yaml.safe_dump(config))
    assert_rejected(c, c.run(), "CHANGE_ID_HOOK_FAILED", events=["POLICY"])
    assert not c.sql("SELECT * FROM campaign_change_ids")
    c.config.write_text(original)
    assert c.run().exit_code == 0


@pytest.mark.parametrize(
    "mode", ["unwritable", "missing", "ls-timeout", "push-timeout", "post-read"]
)
def test_push_failure_then_recovery(campaign, monkeypatch, mode):
    c = campaign
    original = submit.SandboxGit.run
    reads = 0

    def run(self, cwd, *args, **kwargs):
        nonlocal reads
        if args[:2] == ("ls-remote", "--exit-code"):
            reads += 1
            if mode == "ls-timeout" or mode == "post-read" and reads == 2:
                raise subprocess.TimeoutExpired(["git", *args], 300)
        if args and args[0] == "push":
            if mode == "push-timeout":
                raise subprocess.TimeoutExpired(["git", *args], 300)
        return original(self, cwd, *args, **kwargs)

    if mode == "missing":
        c.remote.rename(c.remote.with_name("saved"))
    if mode == "unwritable":
        (c.remote / "objects").chmod(0o500)
    monkeypatch.setattr(submit.SandboxGit, "run", run)
    try:
        result = c.run()
    finally:
        if mode == "unwritable":
            (c.remote / "objects").chmod(0o755)
    assert result.exit_code == 5 and result.payload["action"] == "push_failed"
    assert c.statuses()[-1][0] == "SANDBOX_PUSH_FAILED"
    assert json.loads(c.events()[-1][1])["result"] == "failed"
    if mode in {"missing", "ls-timeout"}:
        assert not c.pushes()
    if mode == "missing":
        c.remote.with_name("saved").rename(c.remote)
    monkeypatch.setattr(submit.SandboxGit, "run", original)
    recovered = c.run()
    assert recovered.exit_code == 0
    assert recovered.payload["change_id"] == result.payload["change_id"]
    assert not c.hooks()


def test_cli_snapshot_and_malformed_args(campaign):
    c = campaign
    output = io.StringIO()
    result = cli.main(
        [
            "sandbox-submit",
            "--verification-ids",
            "v0,v1,v2",
            "--state-db",
            str(c.db.path),
            "--config",
            str(c.config),
            "--sandbox-branch",
            "sandbox/test",
            "--message-brief",
            "correct value",
            "--edit-source-kind",
            "generated",
        ],
        stdout=output,
    )
    assert result == 0
    payload = json.loads(output.getvalue())
    assert set(payload) == set(submit.empty_payload())
    assert payload["action"] == "pushed" and payload["push"]["url"] == str(c.remote)
    output = io.StringIO()
    assert cli.main(["sandbox-submit", "--unknown"], stdout=output) == 2
    assert json.loads(output.getvalue())["action"] == "invalid_args"


@pytest.mark.parametrize(
    "key",
    [
        "core.sshCommand",
        "core.fsmonitor",
        "credential.helper",
        "url./tmp/other.insteadOf",
        "url./tmp/other.pushInsteadOf",
        "filter.x.clean",
        "diff.external",
        "protocol.file.allow",
    ],
)
def test_unsafe_config_prevents_commands_and_preserves_remotes(campaign, key):
    c = campaign
    sentinel = c.root / "executed"
    target = c.src if key == "filter.x.clean" else c.copies[0]
    other = c.root / "other"
    other.mkdir()
    git(other, "init", "--bare", "-q")
    git(target, "config", key, f"touch {sentinel}")
    if key == "filter.x.clean":
        (target / ".gitattributes").write_text("file.c filter=x\n")
    result = c.run()
    assert_rejected(c, result, "REJECTED_UNSAFE_GIT_CONFIG")
    assert not sentinel.exists()
    assert git(c.remote, "for-each-ref") == git(other, "for-each-ref") == ""


def test_include_and_old_git_reject_via_command(campaign, monkeypatch):
    c = campaign
    included = c.root / "included"
    included.write_text("[core]\n sshCommand = touch /must-not-run\n")
    git(c.copies[0], "config", "include.path", str(included))
    assert_rejected(c, c.run(), "REJECTED_UNSAFE_GIT_CONFIG")
    git(c.copies[0], "config", "--unset", "include.path")
    original = submit.SandboxGit.run

    def run(self, cwd, *args, **kwargs):
        if args == ("--version",):
            return subprocess.CompletedProcess(["git", *args], 0, "git version 2.25.0\n", "")
        return original(self, cwd, *args, **kwargs)

    monkeypatch.setattr(submit.SandboxGit, "run", run)
    result = c.run()
    assert_rejected(c, result, "REJECTED_UNSAFE_GIT_CONFIG")
    assert "2.26" in result.payload["reason"]


def test_named_remote_is_rejected(campaign):
    c = campaign
    config = yaml.safe_load(c.config.read_text())
    config["gerrit_ssh_base"] = "ssh://unused.example"
    c.config.write_text(yaml.safe_dump(config))
    git(c.copies[0], "config", "remote.ssh://unused.example/project.url", str(c.remote))
    result = c.run()
    assert result.exit_code == 4 and result.payload["error_code"] == "REJECTED_REF_NOT_ALLOWED"
    assert not c.pushes() and git(c.remote, "for-each-ref") == ""
    assert not any(c[:1] == ["ssh"] for c in c.calls)


@pytest.mark.parametrize("bypass", [False, True])
def test_mandatory_overrides_disable_hook_and_fsmonitor(campaign, monkeypatch, bypass):
    c = campaign
    sentinel = c.root / "executed"
    script = c.root / "danger"
    script.write_text(f"#!/bin/sh\ntouch {sentinel}\n")
    script.chmod(0o700)
    hook = c.copies[0] / ".git/hooks/pre-push"
    hook.write_bytes(script.read_bytes())
    hook.chmod(0o700)
    git(c.copies[0], "config", "core.fsmonitor", str(script))
    git(c.copies[0], "config", "core.sshCommand", str(script))
    if bypass:
        monkeypatch.setattr(submit.SandboxGit, "unsafe_reason", lambda *a: None)
    result = c.run()
    assert result.exit_code == (0 if bypass else 4)
    assert not sentinel.exists()
    if bypass:
        assert git(c.remote, "for-each-ref", "--format=%(refname)") == "refs/heads/sandbox/test"


def test_follow_tags_disabled_and_only_one_refspec(campaign, monkeypatch):
    c = campaign
    git(c.copies[0], "config", "push.followTags", "true")
    original = submit.toctou_recheck

    def tag(db, snapshot, **kwargs):
        git(c.copies[0], "tag", "-a", "must-not-push", snapshot.derived, "-m", "tag")
        return original(db, snapshot, **kwargs)

    monkeypatch.setattr(submit, "toctou_recheck", tag)
    assert c.run().exit_code == 0
    assert git(c.remote, "for-each-ref", "--format=%(refname)") == "refs/heads/sandbox/test"
    command = c.pushes()[0]
    assert command[-1].endswith(":refs/heads/sandbox/test")
    assert command[-1].startswith("+")
    assert "--no-follow-tags" in command and "--recurse-submodules=no" in command


def test_submodule_remote_untouched(campaign):
    c = campaign
    child = c.root / "child"
    child.mkdir()
    git(child, "init", "-q")
    git(child, "config", "user.name", "Test")
    git(child, "config", "user.email", "test@example.com")
    git(child, "commit", "--allow-empty", "-qm", "base")
    child_remote = c.root / "child.git"
    git(c.root, "clone", "--bare", str(child), str(child_remote))
    git(child, "commit", "--allow-empty", "-qm", "unpublished")
    child_sha = git(child, "rev-parse", "HEAD")
    before = git(child_remote, "for-each-ref")
    for path in c.copies:
        git(path, "clone", str(child), "child")
        git(path / "child", "remote", "set-url", "origin", str(child_remote))
        (path / ".gitmodules").write_text(
            f'[submodule "child"]\n path = child\n url = {child_remote}\n'
        )
        git(path, "add", ".gitmodules")
        git(path, "update-index", "--add", "--cacheinfo", f"160000,{child_sha},child")
        git(path, "commit", "-qm", "with submodule")
        git(path, "config", "push.recurseSubmodules", "on-demand")
    tree = git(c.copies[0], "rev-parse", "HEAD^{tree}")
    c.sql("UPDATE verification_records SET verified_tree_sha=?", (tree,))
    assert c.run().exit_code == 0
    assert git(child_remote, "for-each-ref") == before


def test_hostile_git_environment_is_removed(campaign, monkeypatch):
    c = campaign
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        monkeypatch.setenv(key, str(c.root / "hostile"))
    result = c.run()
    assert result.exit_code == 0, result.payload
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        monkeypatch.delenv(key)
    assert (
        git(c.remote, "rev-parse", "refs/heads/sandbox/test")
        == result.payload["derived_commit_sha"]
    )


def test_remote_mutation_after_toctou_and_post_toctou_config_guard(campaign, monkeypatch):
    c = campaign
    assert c.run().exit_code == 0
    original = submit.toctou_recheck

    def changed(db, snapshot, **kwargs):
        result = original(db, snapshot, **kwargs)
        git(c.remote, "update-ref", "refs/heads/sandbox/test", c.base)
        return result

    monkeypatch.setattr(submit, "toctou_recheck", changed)
    assert c.run().exit_code == 0 and len(c.pushes()) == 1
    run = submit.SandboxGit.run

    def unsafe(self, cwd, *args, **kwargs):
        result = run(self, cwd, *args, **kwargs)
        if args[:2] == ("ls-remote", "--exit-code"):
            git(c.copies[0], "config", "core.sshCommand", "unsafe")
        return result

    monkeypatch.setattr(submit.SandboxGit, "run", unsafe)
    result = c.run()
    assert_rejected(c, result, "REJECTED_UNSAFE_GIT_CONFIG")


@pytest.mark.parametrize(
    "window",
    [
        "policy",
        "hook",
        "cache",
        "derive",
        "pushing",
        "push-ok",
        "push-fail",
        "failed-event",
        "ok-event",
    ],
)
def test_nine_crash_windows_converge(campaign, monkeypatch, window):
    c = campaign
    event = state.append_event
    status = state.append_status
    cache = state.get_or_create_change_id
    hook = submit.generate_change_id_via_hook
    run = submit.SandboxGit.run

    class Crash(Exception):
        pass

    def append_event(db, key, kind, payload):
        result = event(db, key, kind, payload)
        if (
            window == "policy"
            and kind == "POLICY"
            or window == "derive"
            and kind == "DERIVE"
            or window == "ok-event"
            and kind == "PUSH"
            and payload["result"] == "ok"
            or window == "failed-event"
            and kind == "PUSH"
            and payload["result"] == "failed"
        ):
            raise Crash(window)
        return result

    def append_status(db, key, value, *args, **kwargs):
        result = status(db, key, value, *args, **kwargs)
        if window == "pushing" and value == "SANDBOX_PUSHING":
            raise Crash(window)
        return result

    def get_cache(*args, **kwargs):
        result = cache(*args, **kwargs)
        if window == "cache":
            raise Crash(window)
        return result

    def generate(**kwargs):
        result = hook(**kwargs)
        if window == "hook":
            raise Crash(window)
        return result

    def git_run(self, cwd, *args, **kwargs):
        if args[0] == "push" and window in {"push-fail", "failed-event"}:
            if window == "push-fail":
                raise Crash(window)
            raise subprocess.CalledProcessError(128, ["git", *args])
        result = run(self, cwd, *args, **kwargs)
        if args[0] == "push" and window == "push-ok":
            raise Crash(window)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(state, "append_event", append_event)
        patch.setattr(state, "append_status", append_status)
        patch.setattr(state, "get_or_create_change_id", get_cache)
        patch.setattr(submit, "generate_change_id_via_hook", generate)
        patch.setattr(submit.SandboxGit, "run", git_run)
        with pytest.raises(Crash):
            c.run()
        first_hooks = len(c.hooks())
    result = c.run()
    assert result.exit_code == 0, result.payload
    assert c.statuses()[-1][0] == "SANDBOX_PUSHED"
    assert sum(row[0] == "DERIVE" for row in c.events()) == 1
    assert len(c.sql("SELECT * FROM campaign_change_ids")) == 1
    assert result.payload["change_id"] == c.sql("SELECT change_id FROM campaign_change_ids")[0][0]
    assert first_hooks + len(c.hooks()) == (2 if window == "hook" else 1)


def test_toctou_db_queries_share_snapshot(campaign, monkeypatch):
    c = campaign
    original = submit._SnapshotDatabase.get_verification_record
    called = False

    def second_connection(self, key):
        nonlocal called
        value = original(self, key)
        assert self.connection.in_transaction
        if not called:
            called = True
            c.sql(
                "UPDATE campaign_gate_events SET payload_json="
                "json_set(payload_json, '$.message_brief', 'changed') WHERE event_type='DERIVE'"
            )
        return value

    monkeypatch.setattr(submit._SnapshotDatabase, "get_verification_record", second_connection)
    assert c.run().exit_code == 0
    assert called


def test_held_requires_arch_and_lock_remains_held_during_write(campaign, monkeypatch):
    c = campaign
    c.sql("UPDATE verification_records SET base_commit='changed' WHERE verification_id='v1'")
    original = state.append_status

    def append(db, key, status, reason=None, arch_norm=None):
        if status == "HELD_FOR_INVESTIGATION":
            with (c.unit_root / ".sandbox_submit.lock").open("a+") as lock:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return original(db, key, status, reason, arch_norm)

    monkeypatch.setattr(state, "append_status", append)
    assert c.run().payload["action"] == "held"
    with pytest.raises(state.PayloadSchemaError):
        original(c.db, c.key, "HELD_FOR_INVESTIGATION", "state_inconsistent", None)


@pytest.mark.parametrize(
    "ref,expected",
    [
        ("refs/heads/sandbox/a", submit.RefClass.SANDBOX),
        ("refs/for/tizen", submit.RefClass.REVIEW),
        ("refs/for/tizen%topic=x", submit.RefClass.FORBIDDEN),
        ("refs/heads/master", submit.RefClass.FORBIDDEN),
        ("refs/for/-x", submit.RefClass.FORBIDDEN),
    ],
)
def test_ref_classes(ref, expected):
    assert submit.check_push_ref(ref) is expected


@pytest.mark.parametrize(
    "action",
    [
        "pushed",
        "already_pushed",
        "rejected",
        "held",
        "worktree_lost",
        "push_failed",
        "invalid_args",
        "busy",
    ],
)
def test_all_action_json_snapshots(campaign, monkeypatch, action):
    c = campaign
    if action == "already_pushed":
        assert c.run().exit_code == 0
    elif action == "rejected":
        state.append_status(c.db, c.key, "DENIED")
    elif action == "held":
        c.sql("UPDATE campaign_units SET branch='other'")
    elif action == "worktree_lost":
        shutil.rmtree(c.copies[1])
    elif action == "push_failed":

        def failure(*args):
            raise ValueError("fixture read failure")

        monkeypatch.setattr(submit, "_remote_sha", failure)
    lock = (c.unit_root / ".sandbox_submit.lock").open("a+")
    try:
        if action == "busy":
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = c.run(**({"verification_ids": "v0,v1"} if action == "invalid_args" else {}))
    finally:
        lock.close()
    expected = {
        "action": action,
        "status": None,
        "aggregate": {"ok": None, "verified_tree_sha": None, "base_commit": None, "reasons": []},
        "policy_verdict": None,
        "fix_strategy_final": None,
        "change_id": None,
        "derived_commit_sha": None,
        "push": {"ref": None, "result": None, "url": None},
        "reused": {"message_brief": None, "edit_source_kind": None},
        "held": {"reason": None, "arch_norm": None, "scope": None},
        "surviving_worktrees": [],
        "error_code": None,
        "reason": None,
    }
    if action in {"pushed", "already_pushed", "held", "worktree_lost", "push_failed"}:
        expected["aggregate"] = dict(
            ok=True, verified_tree_sha=c.tree, base_commit=c.base, reasons=[]
        )
    if action in {"pushed", "already_pushed", "push_failed"}:
        derived = json.loads(
            c.sql("SELECT payload_json FROM campaign_gate_events WHERE event_type='DERIVE'")[0][0]
        )
        expected.update(
            policy_verdict="allowed",
            fix_strategy_final="code",
            change_id="I" + "1" * 40,
            derived_commit_sha=derived["derived_commit_sha"],
            status="SANDBOX_PUSHED",
        )
        expected["push"] = dict(ref="refs/heads/sandbox/test", result="ok", url=str(c.remote))
        expected["reused"] = dict(
            message_brief=action == "already_pushed", edit_source_kind=action == "already_pushed"
        )
    if action == "push_failed":
        expected.update(
            status="SANDBOX_PUSH_FAILED", error_code="PUSH_FAILED", reason="fixture read failure"
        )
        expected["push"]["result"] = "failed"
    elif action == "held":
        expected.update(
            status="HELD_FOR_INVESTIGATION",
            error_code="REJECTED_ARCH_AGGREGATE_MISMATCH",
            reason="aggregate differs from unit",
            held=dict(reason="aggregate_mismatch", arch_norm=None, scope="unit"),
        )
    elif action == "worktree_lost":
        expected.update(
            status="WORKTREE_LOST",
            error_code="REJECTED_WORKTREE_MISSING",
            reason="armv7l",
            surviving_worktrees=[str(c.copies[0]), str(c.copies[2])],
        )
    elif action == "rejected":
        expected.update(
            status="DENIED",
            error_code="REJECTED_STATE_INCONSISTENT",
            reason="not executable: DENIED",
        )
    elif action == "invalid_args":
        expected.update(
            error_code="INVALID_ARGS", reason="exactly three distinct verification ids required"
        )
    elif action == "busy":
        expected.update(
            error_code="CAMPAIGN_STATE_BUSY", reason=str(c.unit_root / ".sandbox_submit.lock")
        )
    assert json.loads(json.dumps(result.payload)) == expected
    assert result.exit_code == {
        "pushed": 0,
        "already_pushed": 0,
        "push_failed": 5,
        "invalid_args": 2,
    }.get(action, 4)
    if action not in {"pushed", "push_failed"}:
        assert not c.pushes() and not c.hooks()


def test_repair_primitives_moved_without_source_changes():
    import ast

    from ci_triage import _campaign_workspace

    root = Path(__file__).resolve().parents[2]
    old = subprocess.check_output(
        [
            "git",
            "show",
            "68338dc:tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py",
        ],
        cwd=root,
        text=True,
    )
    new = Path(_campaign_workspace.__file__).read_text()

    def segments(source):
        return {
            node.name: ast.get_source_segment(source, node)
            for node in ast.parse(source).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }

    before, after = segments(old), segments(new)
    for name in (
        "_StepError",
        "_unit_hash",
        "_validate_source_identity",
        "_git_stdout",
        "_normalize_project",
    ):
        assert before[name] == after[name], name
