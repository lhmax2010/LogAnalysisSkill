"""Read-only handoff observation using the accepted batch-2 offline fixtures."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(ROOT / "tests/unit"))

from test_campaign_batch2_baseline import prepared as prepared  # noqa: E402
from test_campaign_batch2_intake import case as case  # noqa: E402
from test_campaign_fake_ssh import transport as transport  # noqa: E402
from tizen_baseline_reproduce import baseline  # noqa: E402
from tizen_campaign_core import campaign_state as state  # noqa: E402
from tizen_campaign_repair.campaign_repair_step import (  # noqa: E402
    CampaignRepairStepOptions,
    campaign_repair_step,
)


def test_accepted_baseline_cannot_enter_first_repair(prepared, tmp_path):
    c, args = prepared
    baselines = []
    for arch in ("aarch64", "armv7l", "x86_64"):
        args.arch = "standard-" + arch
        args.output_dir = tmp_path / ("baseline-" + arch)
        code, payload = baseline.run(args)
        assert code == 0 and payload["outcome"] == "matched"
        baselines.append(dict(arch=arch, exit=code, outcome=payload["outcome"]))
    before = hashlib.sha256(c.db.path.read_bytes()).hexdigest()
    status_before = state.latest_status(c.db, c.key)
    edit = tmp_path / "edit.json"
    edit.write_text(
        json.dumps(
            dict(
                schema_version="gbs_patch_suggest/edit-spec/v1",
                patch_name="repair",
                edits=[dict(file="src/clang_case.c", old="return missing", new="return 0")],
            )
        )
    )
    calls = []

    def forbidden_build(options):
        calls.append(options)
        raise AssertionError("unexpected build invocation")

    outcome = campaign_repair_step(
        CampaignRepairStepOptions(
            c.key,
            c.db,
            c.args.config,
            1,
            edit,
            "standard-aarch64",
            10,
        ),
        build_verify_fn=forbidden_build,
    )
    after = hashlib.sha256(c.db.path.read_bytes()).hexdigest()
    conn = state._read_connection(c.db)
    try:
        rounds = conn.execute("SELECT count(*) FROM campaign_rounds").fetchone()[0]
    finally:
        conn.close()
    facts = dict(
        baselines=baselines,
        status_before=status_before,
        status_after=state.latest_status(c.db, c.key),
        exit_code=outcome.exit_code,
        response=outcome.result.to_dict(),
        rounds=rounds,
        invocations_used=state.invocations_used(c.db, c.key),
        build_calls=len(calls),
        db_sha256_before=before,
        db_sha256_after=after,
    )
    print("HANDOFF_FACTS=" + json.dumps(facts, sort_keys=True))
    assert status_before == "BASELINE_REPRODUCED"
    assert outcome.exit_code == 4
    assert outcome.result.error_code == "REJECTED_STATE_INCONSISTENT"
    assert (
        outcome.result.convergence_reason
        == "campaign unit status is not executable: 'BASELINE_REPRODUCED'"
    )
    assert not calls and rounds == 0 and state.invocations_used(c.db, c.key) == 0
    assert before == after
