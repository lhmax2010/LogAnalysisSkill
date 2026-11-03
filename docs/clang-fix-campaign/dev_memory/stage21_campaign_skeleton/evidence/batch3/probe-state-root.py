"""Offline evidence: the pending QB request does not persist its trace root."""

import hashlib
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_workspace import _unit_hash
from tizen_ci_shared.state import StateDatabase
from tizen_qb_verify.qb_trigger import _trace


def main() -> None:
    with TemporaryDirectory(prefix="skel-b3-root-") as directory:
        root = Path(directory)
        db = StateDatabase(root / "database/state.db")
        key = "synthetic-unit"
        state.create_unit(
            db,
            campaign_unit_key=key,
            submission_identity_key="synthetic-submission",
            ci_system="quickbuild",
            source_build_id="101",
            project="platform/upstream/example",
            branch="tizen_base",
            spec_name="example",
            base_commit="a" * 40,
            primary_arch="standard-aarch64",
            failed_arches=("standard-aarch64",),
            toolchain_profile="clang",
            ci_evidence_ref=str(root / "ci.json"),
            ci_evidence_sha256="c" * 64,
            max_rounds=3,
            max_build_invocations=9,
        )
        state.create_qb_request(
            db, key, request_id="synthetic-request",
            sbs_target="platform/upstream/example@" + "b" * 40,
        )
        with sqlite3.connect(db.path) as conn:
            columns = {
                table: [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
                for table in ("campaign_qb_requests", "campaign_qb_events", "campaign_qb_profiles")
            }
            results = conn.execute(
                "SELECT count(*) FROM campaign_qb_events WHERE event_type='RESULT'"
            ).fetchone()[0]
        before = hashlib.sha256(db.path.read_bytes()).hexdigest()
        locations = []
        for name in ("first-state-root", "second-state-root"):
            actual_root = root / name
            _trace(actual_root, key, {"action": "ROOT_LOCATION_PROBE"})
            path = actual_root / "qb_traces" / (_unit_hash(key) + ".jsonl")
            assert path.is_file()
            locations.append(str(path.relative_to(root)))
        after = hashlib.sha256(db.path.read_bytes()).hexdigest()
        assert before == after and results == 0
        assert all("state_root" not in names for names in columns.values())
        print(json.dumps({
            "qb_columns": columns,
            "result_rows": results,
            "trace_locations": locations,
            "database_sha256_before": before,
            "database_sha256_after": after,
            "database_unchanged": before == after,
            "network_requests": 0,
            "browser_starts": 0,
            "conclusion": "pending request does not identify the actual trace root",
        }, indent=2))


if __name__ == "__main__":
    main()
