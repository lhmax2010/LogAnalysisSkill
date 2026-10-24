"""Synthetic, explicitly non-production report fixtures."""
from html import escape
import json
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
REPO = CORE.parent


def config_data(root):
    data = json.loads((CORE / "config.sample.json").read_text())
    data["data_root"] = str(root)
    data["cosmos"]["status_source"] = None
    data["cosmos"]["report_markers"]["summary"] = "Summary"
    return data


def pkg(name, category="succeeded", missing=None):
    return {"name": name, "path": "//example/packages/" + name, "cl": "100",
            "shelve": False, "category": category, "missing": missing or []}


def report_html(arch, packages, *, build_conf="//example/config/build.conf@1",
                title="Build Statis Details", include_export=True):
    headers = {"Profile": "fixture-profile", "Arch": arch, "Start Time": "2026-10-24 00:00:00",
               "GBS Version": "fixture-1", "BASE SNAPSHOT": "fixture-base",
               "PRODUCT SNAPSHOT": "fixture-product", "BUILD CONF": build_conf}
    lines = ["<!doctype html><html><body><h1>GBS Local Full Build Report</h1><table>"]
    lines += [f"<tr><td>{key}</td><td>{escape(value)}</td></tr>" for key, value in headers.items()]
    counts = {category: sum(p["category"] == category for p in packages)
              for category in ("succeeded", "build_error", "expansion_error", "export_error")}
    lines += ["</table><h2>Summary</h2><table>",
              "<tr><th>Total</th><th>succeeded</th><th>Export Error</th><th>Expansion Error</th><th>Build Error</th></tr>",
              f'<tr><td>{len(packages)}</td><td>{counts["succeeded"]}</td><td>{counts["export_error"]}</td><td>{counts["expansion_error"]}</td><td>{counts["build_error"]}</td></tr>', "</table>"]
    for heading, categories in [(title, {"succeeded", "build_error"}),
                                ("Expansion Error Details", {"expansion_error"}),
                                ("Export Error Details", {"export_error"})]:
        if "export_error" in categories and not include_export:
            continue
        lines += [f"<h2>{escape(heading)}</h2><table>", "<tr><th>Package</th><th>Path</th><th>Status</th></tr>"]
        for package in packages:
            if package["category"] not in categories:
                continue
            if package["category"] == "expansion_error":
                status = "<br>".join(escape("nothing provides " + value + " needed by " + package["name"]) for value in package["missing"])
            else:
                success = package["category"] == "succeeded"
                status = f'<a href="logs/{"success" if success else "fail"}/{package["name"]}-1.0-1/log.txt">{"Succeeded" if success else "Failed"}</a>'
            raw = package["path"] + "@" + package["cl"] + ("(shelve)" if package["shelve"] else "")
            lines.append(f'<tr><td>{escape(package["name"])}</td><td>{escape(raw)}</td><td>{status}</td></tr>')
        lines.append("</table>")
    lines.append("</body></html>")
    return "\n".join(lines) + "\n"


def bundle(directory, packages_by_arch=None, *, write_config=True):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if packages_by_arch is None:
        packages_by_arch = {"armv7l": [pkg("ok"), pkg("provider", "build_error"),
                                      pkg("consumer", "expansion_error", ["provider >= 2", "other"])],
                            "x86_64": [pkg("host")]}
    config = config_data(directory / "data")
    config_path = directory / "config.json"
    if write_config:
        config_path.write_text(json.dumps(config, indent=2) + "\n")
    manifest = {"schema_version": 1,
                "build_ref": {"backend_id": "fixture", "instance_id": "fixture-instance",
                              "run_id": "fixture-run", "execution_kind": "cosmos"},
                "reports": {}, "expected_packages": {}, "logs": []}
    for arch, packages in packages_by_arch.items():
        html = report_html(arch, packages)
        manifest["reports"][arch] = []
        for index, stamp in enumerate(("2026-10-24T00:00:00Z", "2026-10-24T00:01:00Z")):
            filename = arch + f"-{index}.html"
            (directory / filename).write_text(html)
            manifest["reports"][arch].append({"path": filename, "observed_at": stamp,
                                             "status_code": 200, "source_url": "https://example.invalid/report/"})
        manifest["expected_packages"][arch] = [{"arch": arch, "name": p["name"], "path": p["path"]} for p in packages]
        for p in packages:
            if p["category"] in {"build_error", "export_error"}:
                filename = arch + "-" + p["name"] + "-log.txt"
                (directory / filename).write_text("fixture compiler: example failure\n")
                manifest["logs"].append({"key": {"arch": arch, "name": p["name"], "path": p["path"]}, "path": filename})
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return config_path, manifest_path, manifest
