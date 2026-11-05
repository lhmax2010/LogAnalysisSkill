"""Check the actual root-layers contract with an in-memory proposed import only."""

from __future__ import annotations

import configparser
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

import grimp
from importlinter.contracts.layers import LayersContract

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent


def hashes() -> dict[str, str]:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0")
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in names
        if (name.endswith((".py", ".mjs", "-FROZEN.md")) or name == ".importlinter")
        and (ROOT / name).is_file()
    }


def main() -> None:
    before = hashes()
    config = configparser.ConfigParser()
    config.read(ROOT / ".importlinter")
    section = config["importlinter:contract:root-layers"]
    options = dict(section)
    for key in ("layers", "ignore_imports"):
        options[key] = [line.strip() for line in section[key].splitlines() if line.strip()]
    roots = config["importlinter"]["root_packages"].split()
    contract = LayersContract(section["name"], {"root_packages": roots}, options)
    results = []
    for target in (None, "tizen_qb_verify.qb_browser", "tizen_qb_verify.qb_config",
                   "tizen_qb_verify.qb_redact"):
        graph = grimp.build_graph(*roots, cache_dir=None)
        if target is not None:
            importer = "tizen_campaign_intake.campaign_discover"
            graph.add_module(importer)
            graph.add_import(importer=importer, imported=target, line_number=1,
                             line_contents=f"from {target} import placeholder")
        checked = contract.check(graph, verbose=False)
        results.append({"proposed_target": target, "kept": checked.kept,
                        "metadata": checked.metadata})
        assert checked.kept == (target is None)
    after = hashes()
    assert before == after
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "method": "actual LayersContract.check; fresh graph; one in-memory edge per negative",
        "source_files_created_or_edited": False,
        "results": results,
        "protected_count": len(before), "unchanged": before == after, "hashes": before,
    }
    (HERE / "probe.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps({"cases": len(results), "expected_results": True,
                      "production_unchanged": before == after}))


if __name__ == "__main__":
    main()
