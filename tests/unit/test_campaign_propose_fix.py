from __future__ import annotations

import hashlib
import importlib
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import tizen_campaign_core
import yaml
from test_campaign_batch2_intake import case as case
from test_campaign_fake_ssh import transport as transport
from tizen_build_verify.edit_spec_guard import validate_edit_spec
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._sandbox_git import SandboxGit
from tizen_campaign_intake import intake
from tizen_campaign_repair import propose_fix
from tizen_campaign_repair.campaign_repair_step import _read_edit_spec

KEYS = {
    "mode", "needs_generation", "edit_spec_path", "source_kind", "kb_precedent_ref",
    "context_dir", "t2_records", "downgrade_reason",
}
DIFF = (
    "diff --git a/src/clang_case.c b/src/clang_case.c\n"
    "--- a/src/clang_case.c\n+++ b/src/clang_case.c\n@@ -1 +1 @@\n"
    "-int main() { return missing; }\n+int main() { return 0; }\n"
)


@pytest.fixture
def proposal(case, monkeypatch, tmp_path):
    intake.add_unit(case.args)
    case.settings["kb_db"] = str(tmp_path / "knowledge.jsonl")
    case.args.config.write_text(yaml.safe_dump(case.settings))
    case.source = case.root / "src"
    case.output = tmp_path / "proposal"
    case.t1 = []
    case.t2 = []
    case.queries = []
    case.described = []

    def describe(evidence):
        case.described.append(evidence)
        return dict(
            diagnosed_flag="-Werror", root_cause_category="undeclared_identifier",
            warning_flags=[], error_signature_raw="missing identifier",
        )

    def query(db, **kwargs):
        case.queries.append((db, kwargs))
        return SimpleNamespace(t1=case.t1, t2=case.t2)

    monkeypatch.setattr(
        tizen_campaign_core, "kb", SimpleNamespace(describe_evidence=describe, query=query),
        raising=False,
    )
    return case


def invoke(case, *, arch="standard-x86_64", round_index=1):
    before = case.db.path.read_bytes()
    source = (case.source / "src/clang_case.c").read_bytes()
    stream = io.StringIO()
    code = propose_fix.main([
        "--state-db", str(case.args.state_db), "--config", str(case.args.config),
        "--campaign-unit-key", case.key, "--arch", arch, "--round-index", str(round_index),
        "--output-dir", str(case.output),
    ], stdout=stream)
    assert case.db.path.read_bytes() == before
    assert (case.source / "src/clang_case.c").read_bytes() == source
    result = json.loads(stream.getvalue())
    if code == 0:
        assert set(result) == KEYS
        if result["mode"] == "t1":
            assert result["needs_generation"] is False
            assert result["source_kind"] == "t1_cherry_pick"
            assert Path(result["edit_spec_path"]).is_file()
            assert result["context_dir"] is None
        else:
            assert result["mode"] == "generate"
            assert result["needs_generation"] is True
            assert result["source_kind"] is result["edit_spec_path"] is None
            assert Path(result["context_dir"]).is_dir()
            assert not list(case.output.rglob("*edit_spec*"))
    return code, result


def imported(diff=DIFF):
    return dict(id="kb-1", origin="imported_shelve", diff=diff, baseline_commit="b" * 40)


def test_imported_t1_guard_provenance_and_readonly_state(proposal):
    proposal.t1 = [imported()]
    code, result = invoke(proposal)
    assert code == 0 and result["mode"] == "t1"
    assert result["kb_precedent_ref"] == "kb-1"
    path = Path(result["edit_spec_path"])
    spec = json.loads(path.read_bytes())
    assert spec["kb_precedent_ref"] == "kb-1"
    validate_edit_spec(spec, str(proposal.source))
    raw, digest = _read_edit_spec(path)
    assert raw == path.read_bytes()
    assert digest == hashlib.sha256(raw).hexdigest()
    assert spec["edits"][0]["new"] == "int main() { return 0; }\n"
    assert proposal.queries == [(Path(proposal.settings["kb_db"]), dict(
        diagnosed_flag="-Werror", package="example", gerrit_path="platform/upstream/example",
        category="undeclared_identifier", warning_flags=[], toolchain_profile="clang",
        error_signature="missing identifier", min_status="CI_VERIFIED", limit_t2=5,
    ))]


def test_no_t1_context_only_and_t2_limit_preserves_query_order(proposal):
    proposal.t2 = [dict(id=f"seed-{i}", fix_summary=f"strategy-{i}") for i in range(8)]
    code, result = invoke(proposal)
    assert code == 0 and result["mode"] == "generate"
    assert result["kb_precedent_ref"] is result["downgrade_reason"] is None
    assert result["t2_records"] == proposal.t2[:5]
    context = Path(result["context_dir"])
    assert "did not call an LLM" in (context / "context.md").read_text()
    assert json.loads((context / "t2_records.json").read_text()) == proposal.t2[:5]
    assert json.loads((context / "evidence_packet.json").read_text()) == proposal.described[0]


@pytest.mark.parametrize("diff,reason", [
    (DIFF.replace("return missing", "return different"), "guard_rejected"),
    ("diff --git a/x b/y\nrename from x\nrename to y\n", "rename"),
    (None, "imported_diff_missing"),
])
def test_t1_conversion_downgrades_without_partial_spec(proposal, diff, reason):
    proposal.t1 = [imported(diff)]
    code, result = invoke(proposal)
    assert code == 0 and result["mode"] == "generate"
    assert reason in result["downgrade_reason"]
    assert result["kb_precedent_ref"] == "kb-1"


def prepare_change(proposal):
    git = SandboxGit()
    seed = proposal.args.config.parent / "seed"
    (seed / "src/clang_case.c").write_text("int main() { return 0; }\n")
    git.run(seed, "add", ".")
    git.run(seed, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "-m", "fix")
    ref = "refs/changes/12/312/1"
    git.run(seed, "push", str(proposal.transport[1]), "HEAD:" + ref)
    return dict(
        id="kb-change", change_ref=ref, gerrit_path="platform/upstream/example",
        baseline_commit=proposal.args.base_commit,
        gerrit_url="ssh://must-not-be-contacted.invalid/poison?secret=yes",
    )


def test_change_ref_uses_derived_remote_and_isolated_git(proposal, monkeypatch):
    proposal.t1 = [prepare_change(proposal)]
    original = SandboxGit.run
    calls = []

    def record(self, cwd, *args, **kwargs):
        calls.append((cwd, args, kwargs))
        return original(self, cwd, *args, **kwargs)

    monkeypatch.setattr(SandboxGit, "run", record)
    code, result = invoke(proposal)
    assert code == 0 and result["mode"] == "t1"
    fetch = [call for call in calls if call[1][0] == "fetch"]
    assert len(fetch) == 1
    assert fetch[0][0] is None
    assert fetch[0][1][-2:] == (
        "ssh://gerrit.invalid:29418/platform/upstream/example", "refs/changes/12/312/1",
    )
    assert fetch[0][2]["remote"] is True
    assert not fetch[0][2]["git_dir"].exists()
    assert all(call[0] is None for call in calls if call[1][0] in {"fetch", "diff"})
    assert "must-not-be-contacted" not in repr(calls)
    requests = [json.loads(line) for line in proposal.transport[2].read_text().splitlines()]
    assert requests[-1] == dict(command="git-upload-pack", path=str(proposal.transport[1]))
    assert json.loads(Path(result["edit_spec_path"]).read_text())["kb_precedent_ref"] == "kb-change"


@pytest.mark.parametrize("ref", [
    "refs/heads/main", "refs/for/main", "refs/changes/1/312/1", "--upload-pack=evil",
    "refs/changes/12/312/1;evil", "refs/changes/12/312/1\n", None,
    "refs/changes/12/312/\u0661",
])
def test_invalid_ref_downgrades_without_transport(proposal, monkeypatch, ref):
    proposal.t1 = [dict(id="kb-1", change_ref=ref, gerrit_path="platform/upstream/example",
                        baseline_commit="b" * 40)]
    original = SandboxGit.run

    def forbid_fetch(self, cwd, *args, **kwargs):
        assert args[0] != "fetch"
        return original(self, cwd, *args, **kwargs)

    monkeypatch.setattr(SandboxGit, "run", forbid_fetch)
    code, result = invoke(proposal)
    assert code == 0 and result["downgrade_reason"] == "invalid_change_ref"


def test_fetch_failure_downgrades_and_cleans_transport(proposal):
    proposal.t1 = [dict(
        id="kb-1", change_ref="refs/changes/12/999/1", gerrit_path="platform/upstream/example",
        baseline_commit="b" * 40,
    )]
    before = set(Path("/tmp").glob("campaign-propose-*"))
    code, result = invoke(proposal)
    assert code == 0 and result["downgrade_reason"] == "t1_material_unavailable"
    assert set(Path("/tmp").glob("campaign-propose-*")) == before


def test_first_round_corrupt_anchor_rejected_before_kb_and_outputs(proposal):
    unit = state.get_unit(proposal.db, proposal.key)
    Path(unit.ci_evidence_ref).write_text("{}")
    code, result = invoke(proposal)
    assert code == 4 and result["error_code"] == "REJECTED_CI_EVIDENCE_MISMATCH"
    assert proposal.queries == [] and not proposal.output.exists()


def reproduce(case, arch, message):
    packet = dict(primary_error=dict(kind="compiler", message=message))
    path = case.root / f"{arch}-reproduce.json"
    path.write_text(json.dumps(packet))
    unit = state.get_unit(case.db, case.key)
    state.append_event(case.db, case.key, "REPRODUCE", dict(
        arch_norm=arch, outcome="matched", evidence_local=str(path),
        evidence_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        synthetic_zero_error=False, gbs_conf_sha256="a" * 64,
        ci_evidence_sha256_used=unit.ci_evidence_sha256, build_log="offline.log", basis="test",
    ))
    return packet, path


def test_later_round_resolves_previous_same_arch_not_latest_other_arch(proposal):
    x86, _ = reproduce(proposal, "x86_64", "x86 previous")
    reproduce(proposal, "aarch64", "other arch latest")
    code, result = invoke(proposal, round_index=2)
    assert code == 0 and result["mode"] == "generate"
    assert proposal.described == [x86]


def test_later_round_uses_convergence_instead_of_ci_or_baseline(proposal):
    reproduce(proposal, "x86_64", "baseline")
    state.create_round(proposal.db, proposal.key, round_index=1,
                       edit_spec_ref=str(proposal.root / "prior.json"), edit_spec_sha256="b" * 64)
    invocation = state.consume_build_invocation(
        proposal.db, proposal.key, round_index=1, arch_norm="x86_64",
    )
    previous = dict(primary_error=dict(kind="compiler", message="previous build"))
    path = proposal.root / "previous.json"
    path.write_text(json.dumps(previous))
    state.append_event(proposal.db, proposal.key, "CONVERGENCE", dict(
        round_index=1, arch_norm="x86_64", invocation_event_id=invocation.event_id,
        result="FAIL", verdict="advance", reason="build_failed", evidence_path=str(path),
        evidence_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), verification_id=None,
        actual_changed_paths=["src/clang_case.c"], previous_basis="reproduce",
        at="2026-11-04T00:00:00+00:00",
    ))
    reproduce(proposal, "aarch64", "other arch newer")
    code, _ = invoke(proposal, round_index=2)
    assert code == 0 and proposal.described == [previous]


@pytest.mark.parametrize("failure", ["missing", "digest"])
def test_later_round_missing_or_corrupt_evidence_does_not_fall_back_to_ci(proposal, failure):
    if failure == "digest":
        _, path = reproduce(proposal, "x86_64", "before")
        path.write_text("{}")
    code, result = invoke(proposal, round_index=2)
    assert code == 4 and result["error_code"] == "REJECTED_STATE_INCONSISTENT"
    assert not proposal.described and not proposal.output.exists()


@pytest.mark.parametrize("part", ["marker", "origin", "head"])
def test_source_identity_reused_without_writes(proposal, part):
    git = SandboxGit()
    if part == "marker":
        (proposal.source / ".campaign_clone").write_text("{}")
    elif part == "origin":
        git.run(proposal.source, "remote", "set-url", "origin", "ssh://gerrit.invalid/other")
    else:
        git.run(proposal.source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "--allow-empty", "-m", "other")
    code, result = invoke(proposal)
    assert code == 4 and result["error_code"] == "REJECTED_IDENTITY_MISMATCH"
    assert not proposal.queries and not proposal.output.exists()


@pytest.mark.parametrize("arch,round_index", [("x86_64", 1), ("standard-x86_64", 0)])
def test_invalid_arguments_before_queries(proposal, arch, round_index):
    code, result = invoke(proposal, arch=arch, round_index=round_index)
    assert code == 2 and result["error_code"] == "INVALID_ARGS"
    assert not proposal.queries


def test_output_cannot_target_source(proposal):
    proposal.output = proposal.source / "new-directory"
    code, result = invoke(proposal)
    assert code == 2 and result["error_code"] == "INVALID_ARGS"
    assert not proposal.output.exists()


def test_cli_missing_arguments_json():
    output = io.StringIO()
    assert propose_fix.main([], stdout=output) == 2
    assert json.loads(output.getvalue())["error_code"] == "INVALID_ARGS"


@pytest.mark.parametrize("kind", ["imported", "change_ref", "none"])
def test_real_kb_dataclass_query_and_all_three_paths(proposal, monkeypatch, kind):
    kb = importlib.import_module("tizen_campaign_core.kb")
    monkeypatch.setattr(tizen_campaign_core, "kb", kb)
    unit = state.get_unit(proposal.db, proposal.key)
    evidence = json.loads(Path(unit.ci_evidence_ref).read_text())
    record = dict(
        **kb.describe_evidence(evidence), package=unit.spec_name, gerrit_path=unit.project,
        toolchain_profile=unit.toolchain_profile, baseline_commit=unit.base_commit,
        verified_tree_sha="a" * 40, fix_strategy_initial="code", fix_strategy_final="code",
        fix_summary="Use a defined return value", status="CI_VERIFIED",
    )
    precedent = None
    if kind == "imported":
        record.update(origin="imported_shelve", diff=DIFF, verified_tree_sha=None,
                      baseline_commit="b" * 40)
    elif kind == "change_ref":
        change = prepare_change(proposal)
        record.update(change_ref=change["change_ref"], gerrit_url=change["gerrit_url"])
    db = Path(proposal.settings["kb_db"])
    if kind != "none":
        precedent = kb.append(db, record).id
    before = db.read_bytes() if db.exists() else None
    code, result = invoke(proposal)
    assert code == 0
    assert result["mode"] == ("generate" if kind == "none" else "t1")
    assert result["kb_precedent_ref"] == precedent
    assert (db.read_bytes() if db.exists() else None) == before
    provenance = json.loads((proposal.output / "provenance.json").read_text())
    if kind == "imported":
        assert provenance["baseline_drift"] is True
    elif kind == "change_ref":
        assert provenance["baseline_drift"] is False
    else:
        assert provenance["baseline_drift"] is None


@pytest.mark.parametrize("raw", [b"invalid json\n", b"\xff\n", b'{"secret":"KB_SECRET"}\n'])
def test_corrupt_kb_is_not_silently_treated_as_no_precedent(proposal, monkeypatch, raw):
    kb = importlib.import_module("tizen_campaign_core.kb")
    monkeypatch.setattr(tizen_campaign_core, "kb", kb)
    path = Path(proposal.settings["kb_db"])
    path.write_bytes(raw)
    code, result = invoke(proposal)
    assert code == 4 and result == dict(error_code="KB_SCHEMA_INVALID", reason="kb_corrupt")
    assert path.read_bytes() == raw
    assert not proposal.output.exists()


def test_existing_output_is_not_overwritten(proposal):
    proposal.output.mkdir()
    prior = proposal.output / "edit_spec.json"
    prior.write_bytes(b"existing bound artifact")
    code, result = invoke(proposal)
    assert code == 2 and result["error_code"] == "INVALID_ARGS"
    assert prior.read_bytes() == b"existing bound artifact"


def test_unknown_unit_rejected_before_queries(proposal):
    proposal.key = "unknown"
    code, result = invoke(proposal)
    assert code == 4 and result["error_code"] == "REJECTED_IDENTITY_MISMATCH"
    assert not proposal.queries and not proposal.output.exists()


@pytest.mark.parametrize("drift", [False, True])
@pytest.mark.parametrize("path", ["imported", "change_ref", "downgrade"])
def test_baseline_drift_report_is_not_a_t1_gate(proposal, path, drift):
    record = prepare_change(proposal) if path == "change_ref" else imported()
    record["baseline_commit"] = "b" * 40 if drift else proposal.args.base_commit
    if path == "downgrade":
        record["diff"] = DIFF.replace("return missing", "return stale")
    proposal.t1 = [record]
    code, result = invoke(proposal)
    assert code == 0
    assert result["mode"] == ("generate" if path == "downgrade" else "t1")
    baseline = dict(
        unit_base_commit=proposal.args.base_commit,
        precedent_base_commit=record["baseline_commit"], baseline_drift=drift,
    )
    report = json.loads((proposal.output / "provenance.json").read_text())
    assert report == dict(
        **baseline, kb_precedent_ref=record["id"], mode=result["mode"],
        downgrade_reason=result["downgrade_reason"],
    )
    if result["mode"] == "t1":
        spec_path = Path(result["edit_spec_path"])
        spec = json.loads(spec_path.read_text())
        assert spec["kb_provenance"] == baseline
        validate_edit_spec(spec, str(proposal.source))
        raw, digest = _read_edit_spec(spec_path)
        assert digest == hashlib.sha256(raw).hexdigest()
        del spec["kb_provenance"]
        assert digest != hashlib.sha256(propose_fix._json_bytes(spec)).hexdigest()
    assert "must-not-be-contacted" not in (proposal.output / "provenance.json").read_text()


def test_no_precedent_drift_is_unknown_not_false(proposal):
    code, _ = invoke(proposal)
    assert code == 0
    report = json.loads((proposal.output / "provenance.json").read_text())
    assert report["unit_base_commit"] == proposal.args.base_commit
    assert report["precedent_base_commit"] is report["baseline_drift"] is None


@pytest.mark.parametrize("baseline", [None, "", "not-a-commit"])
def test_invalid_precedent_baseline_fails_closed(proposal, baseline):
    proposal.t1 = [dict(imported(), baseline_commit=baseline)]
    code, result = invoke(proposal)
    assert code == 4 and result["error_code"] == "REJECTED_STATE_INCONSISTENT"
    assert not proposal.output.exists()


@pytest.mark.parametrize("base", [
    "/tmp/local", "https://gerrit.invalid", "ssh:///missing-host",
    "ssh://user:password@gerrit.invalid", "ssh://gerrit.invalid?command=bad",
    "ssh://gerrit.invalid#fragment", "ssh://gerrit.invalid/ with-space",
])
def test_invalid_remote_configuration_never_fetches(proposal, monkeypatch, base):
    proposal.settings["gerrit_ssh_base"] = base
    proposal.args.config.write_text(yaml.safe_dump(proposal.settings))
    proposal.t1 = [dict(
        id="kb-1", baseline_commit="b" * 40, gerrit_path="platform/upstream/example",
        change_ref="refs/changes/12/312/1", gerrit_url="ssh://poison.invalid/repository",
    )]
    original = SandboxGit.run

    def forbid_fetch(self, cwd, *args, **kwargs):
        assert args[0] != "fetch"
        return original(self, cwd, *args, **kwargs)

    monkeypatch.setattr(SandboxGit, "run", forbid_fetch)
    code, result = invoke(proposal)
    assert code == 2 and result["error_code"] == "INVALID_ARGS"
    assert not list(proposal.output.rglob("*edit_spec*"))


def test_precedent_remote_path_must_equal_unit_project(proposal, monkeypatch):
    proposal.t1 = [dict(
        id="kb-1", baseline_commit="b" * 40, gerrit_path="other/project",
        change_ref="refs/changes/12/312/1",
    )]
    original = SandboxGit.run

    def forbid_fetch(self, cwd, *args, **kwargs):
        assert args[0] != "fetch"
        return original(self, cwd, *args, **kwargs)

    monkeypatch.setattr(SandboxGit, "run", forbid_fetch)
    code, result = invoke(proposal)
    assert code == 0 and result["downgrade_reason"] == "precedent_project_mismatch"


def test_imported_diff_never_uses_even_valid_change_ref_or_poisoned_url(proposal, monkeypatch):
    proposal.t1 = [dict(imported(), gerrit_url="ssh://poison.invalid/repository",
                        change_ref="refs/changes/12/312/1")]
    monkeypatch.setattr(propose_fix, "_fetch_diff", lambda *args: pytest.fail("unexpected fetch"))
    code, result = invoke(proposal)
    assert code == 0 and result["mode"] == "t1"


@pytest.mark.parametrize("fault", ["yaml", "workspace_type", "ssh_secret"])
def test_configuration_errors_emit_fixed_json_without_secrets(proposal, fault, capsys):
    secret = "CONFIG_SECRET_DO_NOT_ECHO"
    if fault == "yaml":
        proposal.args.config.write_text("campaign_workspace: [" + secret)
    else:
        if fault == "workspace_type":
            proposal.settings["campaign_workspace"] = {"password": secret}
        else:
            proposal.settings["gerrit_ssh_base"] = f"ssh://user:{secret}@gerrit.invalid"
            proposal.t1 = [dict(
                id="kb-1", baseline_commit="b" * 40, gerrit_path="platform/upstream/example",
                change_ref="refs/changes/12/312/1",
            )]
        proposal.args.config.write_text(yaml.safe_dump(proposal.settings))
    code, result = invoke(proposal)
    assert code == 2 and result == dict(error_code="INVALID_ARGS", reason="invalid_arguments")
    captured = capsys.readouterr()
    assert secret not in captured.out + captured.err + json.dumps(result)
    assert not (proposal.output / "context").exists()


@pytest.mark.parametrize("fault", ["git_failure", "git_timeout", "marker_error"])
def test_source_errors_never_echo_exception_text(proposal, monkeypatch, fault, capsys):
    secret = "SOURCE_SECRET_DO_NOT_ECHO"
    if fault == "marker_error":
        original = Path.read_text

        def reject_marker(self, *args, **kwargs):
            if self.name == ".campaign_clone":
                raise OSError(secret)
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", reject_marker)
    else:
        def fail_git(self, cwd, *args, **kwargs):
            if fault == "git_timeout":
                raise subprocess.TimeoutExpired(["git", secret], 60)
            raise subprocess.CalledProcessError(128, ["git", secret], stderr=secret)

        monkeypatch.setattr(SandboxGit, "run", fail_git)
    code, result = invoke(proposal)
    assert code == 4 and result == dict(
        error_code="REJECTED_IDENTITY_MISMATCH", reason="rejected_identity_mismatch",
    )
    captured = capsys.readouterr()
    assert secret not in captured.out + captured.err + json.dumps(result)
    assert not proposal.output.exists()


def test_guard_failure_detail_not_exposed_in_downgrade_or_report(proposal, monkeypatch):
    secret = "GUARD_SOURCE_SECRET_DO_NOT_ECHO"
    proposal.t1 = [imported()]

    def reject(*args):
        raise propose_fix.DiffUnsupported("guard_rejected: symlink escapes " + secret)

    monkeypatch.setattr(propose_fix, "convert", reject)
    code, result = invoke(proposal)
    assert code == 0 and result["mode"] == "generate"
    assert result["downgrade_reason"] == "guard_rejected"
    assert secret not in json.dumps(result)
    assert secret not in (proposal.output / "provenance.json").read_text()
