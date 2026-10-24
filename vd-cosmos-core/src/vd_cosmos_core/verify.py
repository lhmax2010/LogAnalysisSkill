"""Saved report acceptance against separately generated rows/links baselines.

No network, P4, browser, or writes to source files. The x86 package set is
explicitly self-derived, while its failed packages participate in links.txt.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import shutil
import uuid

from .backends import SavedReportReader
from .config import load_config
from .errors import FlowError
from .export import check_content, export_file
from .files import atomic_write, digest, json_bytes, load_json
from .groups import group_expansion


REAL_COUNTS = {
    "armv7l": {"total": 2244, "succeeded": 1479, "export_error": 0,
               "expansion_error": 759, "build_error": 6},
    "x86_64": {"total": 43, "succeeded": 42, "export_error": 0,
               "expansion_error": 0, "build_error": 1},
}


def baseline_revision(line):
    """Parse the prototype's line format independently of the report parser."""
    value = line.strip()
    shelved = value.endswith("(shelve)")
    if shelved:
        value = value[:-len("(shelve)")].rstrip()
    path, separator, revision = value.rpartition("@")
    if not separator or not path.strip() or not revision.isascii() or not revision.isdecimal():
        raise FlowError(2, "invalid_baseline_revision")
    return path.strip(), revision, shelved


def read_baselines(rows_data, links_data):
    rows, links = [], []
    for line in rows_data.decode("utf-8").splitlines():
        if line.strip():
            rows.append(baseline_revision(line))
    for line in links_data.decode("utf-8").splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) != 3 or not fields[0].strip() or not fields[1].strip():
            raise FlowError(2, "invalid_links_baseline")
        name, nvr = fields[0].strip(), fields[1].strip()
        if not nvr.startswith(name + "-"):
            raise FlowError(2, "invalid_links_baseline")
        links.append((name, nvr, *baseline_revision(fields[2])))
    if not rows or not links:
        raise FlowError(2, "empty_acceptance_baseline")
    return rows, links


def compare(expected, actual):
    """Preserve multiplicity, including identical packages from different arches."""
    expected, actual = Counter(expected), Counter(actual)
    missing, extra = expected - actual, actual - expected
    differences = ([{"kind": "missing", "value": list(k), "count": v} for k, v in sorted(missing.items())] +
                   [{"kind": "extra", "value": list(k), "count": v} for k, v in sorted(extra.items())])
    return {"equal": not differences, "result": "相等" if not differences else "不相等",
            "expected_count": sum(expected.values()), "actual_count": sum(actual.values()),
            "difference_count": sum(missing.values()) + sum(extra.values()),
            "differences_first20": differences[:20]}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--verified-commit", required=True)
    result.add_argument("--config", required=True)
    for name in ("arm-report", "x86-report", "detail-page", "rows", "links"):
        result.add_argument("--" + name, required=True)
    result.add_argument("--run-id", required=True)
    result.add_argument("--mode", choices=("real", "fixture"), default="real")
    result.add_argument("--fixture-counts")
    return result


def run(args, config, directory, result):
    if set(config.raw["cosmos"]["archs"]) != {"armv7l", "x86_64"}:
        raise FlowError(2, "acceptance_requires_both_architectures")
    if not config.raw["cosmos"].get("status_source"):
        raise FlowError(6, "acceptance_requires_status_source")
    counts = REAL_COUNTS
    if args.mode == "fixture":
        if not args.fixture_counts:
            raise FlowError(2, "fixture_counts_required")
        counts = load_json(args.fixture_counts)
        if set(counts) != set(REAL_COUNTS) or any(
                set(counts[a]) != set(REAL_COUNTS[a]) or
                any(type(n) is not int or n < 0 for n in counts[a].values()) for a in counts):
            raise FlowError(2, "invalid_fixture_counts")
    elif args.fixture_counts:
        raise FlowError(2, "real_counts_cannot_be_overridden")
    sources = {"arm-report": args.arm_report, "x86-report": args.x86_report,
               "detail-page": args.detail_page, "rows": args.rows, "links": args.links}
    copied, blobs = {}, {}
    evidence = []
    for name, source in sources.items():
        source = Path(source).resolve()
        content = source.read_bytes()
        checks = check_content(content, config)
        if not checks["allowed"]:
            raise FlowError(4, "credential_pattern_blocked", source_role=name,
                            hits=checks["credential_hits"])
        target = config.output(directory / (name + (".txt" if name in {"rows", "links"} else ".html")))
        # Copy only after the full input passes the credential gate. No symlink
        # targets or existing files can be reused in the fresh verification dir.
        if target.exists():
            raise FlowError(6, "acceptance_copy_already_exists")
        shutil.copyfile(source, target)
        if digest(target.read_bytes()) != digest(content) or digest(source.read_bytes()) != digest(content):
            raise FlowError(6, "source_changed_during_copy")
        evidence.append({"role": name, "source": str(source), "copy": target.name,
                         "sha256": digest(content), "source_unchanged": True})
        copied[name], blobs[name] = target, content
    result["source_evidence"] = evidence
    rows, links = read_baselines(blobs["rows"], blobs["links"])
    now = datetime.now(timezone.utc)
    previous = now - timedelta(seconds=config.raw["poll"]["interval_s"] + 1)
    manifest = {"schema_version": 1, "build_ref": {
        "backend_id": "saved-report", "instance_id": "local-saved-pages", "run_id": args.run_id,
        "execution_kind": "local_simulation" if args.mode == "fixture" else "cosmos"},
        "reports": {}, "expected_packages": {}, "detail_page": copied["detail-page"].name}
    for arch, role in (("armv7l", "arm-report"), ("x86_64", "x86-report")):
        first = config.output(directory / (arch + "-previous.html"))
        shutil.copyfile(copied[role], first)
        manifest["reports"][arch] = [
            {"path": first.name, "observed_at": previous.isoformat(), "status_code": 200},
            {"path": copied[role].name, "observed_at": now.isoformat(), "status_code": 200}]
    manifest_path = directory / "manifest.json"
    atomic_write(config.data_root, manifest_path, json_bytes(manifest))
    reader = SavedReportReader(config, manifest_path)
    first_packages = {arch: reader.read_packages(reader.build_ref, arch)["packages"] for arch in counts}
    expected_paths = {r[0] for r in rows}
    # Report names supplement the independent arm paths; they do not establish
    # an independent name baseline. Counter comparison below verifies CL/shelve.
    manifest["expected_packages"]["armv7l"] = [p["key"] for p in first_packages["armv7l"]
                                                 if p["key"]["path"] in expected_paths]
    manifest["expected_packages"]["x86_64"] = [p["key"] for p in first_packages["x86_64"]]
    atomic_write(config.data_root, manifest_path, json_bytes(manifest))
    reader = SavedReportReader(config, manifest_path)
    observation = reader.observe(reader.build_ref)
    parsed = {arch: reader.read_packages(reader.build_ref, arch) for arch in counts}
    inputs = reader.read_inputs(reader.build_ref)
    packages = [p for r in parsed.values() for p in r["packages"]]
    groups = group_expansion(packages, reader.provides())
    actual_rows = [(r["path"], r["cl"], r["shelve"]) for r in inputs["reports"]["armv7l"]["rows"]]
    actual_links = [(p["key"]["name"], p["key"]["name"] + "-" + (p["version"] or ""),
                     p["key"]["path"], p["cl"], p["shelve"])
                    for p in packages if p["category"] == "build_error"]
    row_check, link_check = compare(rows, actual_rows), compare(links, actual_links)
    path_check = compare([(p,) for p in sorted(expected_paths)],
                         [(p,) for p in sorted({r[0] for r in actual_rows})])
    other = [{"key": p["key"], "source_line": p["source_line"], "message": message}
             for p in packages for message in p.get("other_expansion_messages", [])]
    result.update(
        simulation_note="离线小规模夹具，不是真实验收" if args.mode == "fixture" else "保存的真实文件；未联网；稳定性为复制模拟",
        stability_simulated=True, snapshot_interval_s=(now - previous).total_seconds(),
        baselines={"armv7l": "rows.txt 独立路径/CL/shelve 多重集合；包名来自报告",
                   "x86_64": "自基线，未独立核验", "failures": "links.txt 跨架构多重集合"},
        reports={arch: {"counts": r["counts"], "expected_counts": counts[arch],
                        "counts_match": r["counts"] == counts[arch],
                        "report_state": r["report_state"], "result_state": r["result_state"],
                        "issues": r["issues"], "package_keys_unique": r["package_keys_unique"],
                        "categories_disjoint": r["categories_disjoint"]} for arch, r in parsed.items()},
        report_state=observation["report_state"], result_state=observation["result_state"],
        header_consistency=observation["header_consistency"], execution_state=observation["execution_state"],
        execution_evidence=observation["execution_evidence"], todos=observation["todos"],
        rows_comparison=row_check, links_comparison=link_check, arm_path_set_comparison=path_check,
        expansion_group_count=len(groups["groups"]),
        expansion_groups_top15=sorted(groups["groups"], key=lambda g: (-len(g["members"]), g["arch"], g["signature"]))[:15],
        other_format_message_count=len(other), other_format_messages_first10=other[:10])
    passed = (all(r["report_state"] == "完整" and r["counts"] == counts[a] for a, r in parsed.items())
              and observation["header_consistency"] == "一致"
              and observation["execution_state"] == "已结束"
              and observation["execution_evidence"].get("subresult") == "failed"
              and row_check["equal"] and link_check["equal"] and path_check["equal"])
    result.update(verdict="PASS" if passed else "FAIL", exit_code=0 if passed else 6)
    # Full observations and all rows remain local, alongside the compact exported result.
    for name, value in (("observe", observation), ("packages", parsed), ("inputs", inputs), ("groups", groups)):
        atomic_write(config.data_root, directory / (name + ".json"), json_bytes(value))


def main(argv=None):
    args = parser().parse_args(argv)
    result = {"schema_version": 1, "git_commit": args.verified_commit, "mode": args.mode,
              "network_access": False, "verdict": "FAIL"}
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", args.verified_commit):
            raise FlowError(2, "invalid_verified_commit")
        config = load_config(args.config)
        identifier = "b1-real-" + uuid.uuid4().hex
        directory = config.output("verification/" + identifier)
        directory.mkdir(parents=True, exist_ok=False)
    except FlowError as error:
        print(json.dumps({**result, "exit_code": error.code, "error": error.reason}, ensure_ascii=False))
        return error.code
    try:
        run(args, config, directory, result)
    except FlowError as error:
        result.update(exit_code=error.code, error=error.reason, error_details=error.details)
    except (OSError, UnicodeError, KeyError, ValueError, TypeError):
        result.update(exit_code=5, error="acceptance_input_failed")
    result_file = directory / "result.json"
    artifact = atomic_write(config.data_root, result_file, json_bytes(result))
    try:
        bundle = export_file(config, result_file, "verification", identifier)
    except FlowError as error:
        print(json.dumps({"exit_code": error.code, "error": error.reason,
                          "result_file": artifact, "verdict": "FAIL"}, ensure_ascii=False))
        return error.code
    print(json.dumps({"exit_code": result["exit_code"], "verdict": result["verdict"],
                      "mode": args.mode, "result_file": artifact, "export": bundle}, ensure_ascii=False))
    return result["exit_code"]
