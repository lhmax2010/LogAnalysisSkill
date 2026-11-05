from __future__ import annotations

import hashlib
import io
import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import yaml
from test_campaign_batch2_intake import case as case
from test_campaign_batch3_e2e import flow as base_flow
from test_campaign_batch3_e2e import push_and_request, read_pass, sequence
from test_campaign_batch3_start import ready as ready
from test_campaign_fake_ssh import transport as transport
from test_qb_collect import Browser
from test_qb_config import config as config
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core import kb
from tizen_campaign_core.discovery_manifest import atomic_write
from tizen_campaign_intake.discover import discover
from tizen_campaign_kb import sync
from tizen_campaign_repair import propose_fix
from tizen_campaign_report import report
from tizen_qb_verify import qb_collect
from tizen_review_submit import review_submit as review
from tizen_sandbox_submit import sandbox_submit as sandbox


def test_discovery_precedent_review_offline_chain(ready, monkeypatch, tmp_path, config):
    class DiscoveryBrowser(Browser):
        def command(self, command, **fields):
            if command == "read_text":
                self.trace.append({"command": command})
                path = (
                    self.root
                    / "discovery/101"
                    / fields["run_dir"]
                    / "logs/example.standard-aarch64.txt"
                )
                raw = ready.args.ci_log.read_bytes()
                atomic_write(path, raw)
                return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
            result = super().command(command, **fields)
            if command == "discovery_read" and fields["path"].endswith("index.html"):
                result["discovery"]["packages"][0].update(
                    base_commit=ready.args.base_commit,
                    failed_arches=["standard-aarch64", "standard-x86_64"],
                )
            return result

    ready.settings["qb"] = config
    ready.args.config.write_text(yaml.safe_dump(ready.settings))
    browser = DiscoveryBrowser(config)
    monkeypatch.setattr(qb_collect, "QbBrowser", lambda qb: browser)
    root = tmp_path / "discovered-state"
    produced = qb_collect.collect(
        SimpleNamespace(
            config=ready.args.config,
            state_root=root,
            qb_project="tizen_base",
            build_id="101",
            since=None,
        )
    )
    assert browser.closed
    assert [entry["command"] for entry in browser.trace].count("read_text") == 1
    args = SimpleNamespace(
        manifest=Path(produced["manifests"][0]),
        state_root=root,
        state_db=ready.db.path,
        config=ready.args.config,
        dry_run=False,
        include_non_compile=False,
    )
    discovered = discover(args)
    assert discovered["packages"][0]["status"] == "created"
    assert discovered["packages"][0]["campaign_unit_key"] == ready.key
    ready.args.ci_log = args.manifest.parent / "logs/example.standard-aarch64.txt"
    # Reuse the established baseline/fake-GBS/SSH/QB harness unchanged.
    c = base_flow.__wrapped__(ready, monkeypatch, tmp_path)
    c.settings["kb_db"] = str(tmp_path / "kb.jsonl")
    c.args.config.write_text(yaml.safe_dump(c.settings))
    unit = state.get_unit(c.db, c.key)
    evidence = json.loads(Path(unit.ci_evidence_ref).read_text())
    diff = (
        "diff --git a/src/clang_case.c b/src/clang_case.c\n"
        "--- a/src/clang_case.c\n+++ b/src/clang_case.c\n@@ -1 +1 @@\n"
        "-int main() { return missing; }\n+int main() { return 0; }\n"
    )
    precedent = kb.append(
        Path(c.settings["kb_db"]),
        dict(
            **kb.describe_evidence(evidence),
            package=unit.spec_name,
            gerrit_path=unit.project,
            toolchain_profile="clang",
            baseline_commit=unit.base_commit,
            verified_tree_sha=None,
            fix_strategy_initial="code",
            fix_strategy_final="code",
            fix_summary="Use defined return",
            status="CI_VERIFIED",
            origin="imported_shelve",
            diff=diff,
        ),
    ).id
    out = io.StringIO()
    assert (
        propose_fix.main(
            [
                "--state-db",
                str(c.db.path),
                "--config",
                str(c.args.config),
                "--campaign-unit-key",
                c.key,
                "--round-index",
                "1",
                "--arch",
                "standard-aarch64",
                "--output-dir",
                str(tmp_path / "proposal"),
            ],
            stdout=out,
        )
        == 0
    ), out.getvalue()
    proposal = json.loads(out.getvalue())
    assert proposal["mode"] == "t1" and proposal["needs_generation"] is False
    assert proposal["kb_precedent_ref"] == precedent
    c.edit = Path(proposal["edit_spec_path"])
    c.repair = replace(c.repair, edit_spec_path=c.edit)
    original = sandbox.sandbox_submit

    def t1_push(options):
        result = original(replace(options, edit_source_kind="t1_cherry_pick"))
        assert result.exit_code == 0, result.payload
        added = sync.run(c.db, c.key, c.settings)
        assert added["status"] == "NEW"
        return result

    monkeypatch.setattr(sandbox, "sandbox_submit", t1_push)
    push_and_request(c, monkeypatch)
    event = read_pass(c)
    promoted = sync.run(c.db, c.key, c.settings)
    assert promoted["status"] == "CI_VERIFIED"
    result = review.run(
        review.ReviewOptions(
            c.ids,
            c.db.path,
            c.args.config,
            c.state_root / event["qb_result_ref"],
            "refs/for/tizen_base",
        )
    )
    assert result.exit_code == 0, result.payload
    assert report.finish(c.db, c.key)[0] == 0
    row = report.report(c.db)[0]
    assert row["status"] == "REVIEW_PUSHED" and row["workspace_status"] == "已释放"
    assert row["source_kind"] == "t1_cherry_pick" and row["kb_precedent_ref"] == precedent
    destination = os.environ.get("RESTORE_DISCOVERY_EVIDENCE")
    if destination:
        Path(destination).mkdir(parents=True, exist_ok=True)
        (Path(destination) / "restored-chain.json").write_text(
            json.dumps(
                {
                    "discovery_commands": browser.trace,
                    "states": sequence(c),
                    "source_kind": row["source_kind"],
                    "kb_precedent_ref": precedent,
                    "final_status": row["status"],
                    "workspace_status": row["workspace_status"],
                },
                indent=2,
            )
        )
    print("RESTORED_STATE_SEQUENCE=" + json.dumps(sequence(c)))
