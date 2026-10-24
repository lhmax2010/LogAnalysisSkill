import json
from pathlib import Path
import tempfile
import unittest

from helpers import CORE, bundle, pkg, report_html
from vd_cosmos_core.backends import FixtureReportReader, SavedReportReader
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.fake_browser import DriverCrash, FixtureSubmitter, ScriptedDriver
from vd_cosmos_core.files import digest
from vd_cosmos_core.groups import group_expansion, package_covered
from vd_cosmos_core.models import BuildRef
from vd_cosmos_core.report import parse_report


class ReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.config_path, self.manifest_path, self.manifest = bundle(self.base)
        self.config = load_config(self.config_path)

    def reader(self, cls=FixtureReportReader):
        self.manifest_path.write_text(json.dumps(self.manifest))
        return cls(self.config, self.manifest_path)

    def observed(self):
        reader = self.reader()
        return reader.observe(reader.build_ref)

    def replace(self, arch, text):
        for snapshot in self.manifest["reports"][arch]:
            (self.base / snapshot["path"]).write_text(text)

    def parse(self, html, packages, arch="armv7l", stable=True):
        expected = [{"arch": arch, "name": p["name"], "path": p["path"], "cl": p["cl"], "shelve": p["shelve"]} for p in packages]
        return parse_report(html, arch, self.config.raw["cosmos"], expected, stable=stable)

    def test_complete_reports_result_failure_independent_of_execution(self):
        result = self.observed()
        self.assertEqual(result["report_state"], "完整")
        self.assertEqual(result["header_consistency"], "一致")
        self.assertEqual(result["result_state"], "失败")
        self.assertEqual(result["execution_state"], "未知")
        self.assertIn("终态推定", result["terminal_inference"])
        self.assertFalse(result["terminal_prerequisite_met"])

    def test_all_success_and_only_expansion_or_export_are_failures(self):
        for category, expected in [("succeeded", "成功"), ("expansion_error", "失败"), ("export_error", "失败")]:
            packages = {arch: [pkg("item", category, ["missing >= 1"])] for arch in ("armv7l", "x86_64")}
            self.config_path, self.manifest_path, self.manifest = bundle(self.base, packages)
            result = self.observed()
            self.assertEqual(result["report_state"], "完整")
            self.assertEqual(result["result_state"], expected)

    def test_reduced_architecture_set_result_partial(self):
        self.config.raw["cosmos"]["archs"] = ["armv7l"]
        result = self.observed()
        self.assertEqual(result["report_state"], "完整")
        self.assertEqual(result["result_state"], "部分")
        self.assertEqual(result["reports"]["armv7l"]["result_state"], "失败")

    def test_missing_architecture_is_not_a_reduced_request(self):
        self.manifest["reports"].pop("x86_64")
        result = self.observed()
        self.assertEqual(result["report_state"], "部分")
        self.assertEqual(result["result_state"], "未知")
        self.assertEqual(result["header_consistency"], "未核")

    def test_header_mismatch_is_independent_from_complete_report_state(self):
        content = (self.base / "x86_64-0.html").read_text().replace("build.conf@1", "build.conf@2")
        self.replace("x86_64", content)
        result = self.observed()
        self.assertEqual(result["report_state"], "完整")
        self.assertEqual(result["header_consistency"], "不一致")
        self.assertEqual(result["result_state"], "未知")
        self.assertFalse(result["terminal_prerequisite_met"])
        self.assertTrue(any(t["reason"] == "header_inconsistent" for t in result["todos"]))

    def test_execution_only_from_configured_detail_title(self):
        detail = self.base / "detail.html"
        detail.write_text('fixture-run <div class="build-status" title="Build is failed"></div>')
        self.manifest["detail_page"] = detail.name
        self.assertEqual(self.observed()["execution_state"], "未知")
        self.config.raw["cosmos"]["status_source"] = json.loads((CORE / "config.sample.json").read_text())["cosmos"]["status_source"]
        self.assertEqual(self.observed()["execution_state"], "已结束")
        self.assertFalse(self.observed()["terminal_prerequisite_met"])
        detail.write_text('<script>BUILD_COMPLETE</script><p>Running</p>')
        self.assertEqual(self.observed()["execution_state"], "未知")

    def test_local_simulation_never_satisfies_cosmos_terminal_prerequisite(self):
        self.manifest["build_ref"]["execution_kind"] = "local_simulation"
        (self.base / "detail.html").write_text('<p title="Build is failed"></p>')
        self.manifest["detail_page"] = "detail.html"
        self.config.raw["cosmos"]["status_source"] = json.loads((CORE / "config.sample.json").read_text())["cosmos"]["status_source"]
        self.assertFalse(self.observed()["terminal_prerequisite_met"])

    def test_sha_stability_and_poll_interval_are_both_required(self):
        snapshot = self.manifest["reports"]["armv7l"][-1]
        snapshot["observed_at"] = "2026-10-24T00:00:30Z"
        self.assertEqual(self.observed()["report_state"], "部分")
        snapshot["observed_at"] = "2026-10-24T00:01:00Z"
        path = self.base / snapshot["path"]
        path.write_text(path.read_text() + "\n")
        self.assertEqual(self.observed()["report_state"], "部分")
        (self.base / "armv7l-0.html").write_text(path.read_text())
        self.assertEqual(self.observed()["report_state"], "完整")

    def test_confirmed_404_and_observation_failure_are_distinct(self):
        for arch in self.manifest["reports"]:
            self.manifest["reports"][arch] = [{"status_code": 404, "host_ok": True, "observed_at": "2026-10-24T00:00:00Z"}]
        self.assertEqual(self.observed()["report_state"], "未发布")
        self.manifest["reports"]["armv7l"][0]["host_ok"] = False
        result = self.observed()
        self.assertTrue(result["observation_failed"])
        self.assertIsNone(result["report_state"])
        self.assertEqual(result["execution_state"], "未知")
        self.assertEqual(result["result_state"], "未知")
        self.assertEqual(result["exit_code"], 5)

    def test_proxy_login_or_malformed_response_is_observation_failure(self):
        for text in ("<html>Proxy error</html>", '<html><form>Sign in</form></html>', "bad response"):
            self.replace("armv7l", text)
            result = self.observed()
            self.assertEqual(result["exit_code"], 5)
            self.assertNotIn("report_state", result["reports"]["armv7l"])

    def test_duplicate_row_cannot_replace_missing_row_even_when_counts_match(self):
        originals = [pkg("one"), pkg("two")]
        bad = [pkg("one"), pkg("one")]
        result = self.parse(report_html("armv7l", bad), originals)
        self.assertNotEqual(result["report_state"], "完整")
        self.assertFalse(result["package_keys_unique"])
        self.assertIn("package_set_mismatch", result["issues"])
        self.assertEqual(result["counts"]["succeeded"], 2)

    def test_category_intersection_rejected_even_with_correct_counts(self):
        packages = [pkg("same", "build_error"), pkg("same", "expansion_error", ["missing"])]
        result = self.parse(report_html("armv7l", packages), [packages[0]])
        self.assertFalse(result["categories_disjoint"])
        self.assertNotEqual(result["report_state"], "完整")

    def test_export_nonzero_unknown_table_is_structure_unknown(self):
        packages = [pkg("exported", "export_error")]
        result = self.parse(report_html("armv7l", packages, include_export=False), packages)
        self.assertEqual(result["report_state"], "结构未知")
        self.assertEqual(result["result_state"], "未知")

    def test_closed_build_status_set(self):
        packages = [pkg("item")]
        for status in ("Skipped", "Unresolvable", "succeeded"):
            html = report_html("armv7l", packages).replace(">Succeeded</a>", ">" + status + "</a>")
            result = self.parse(html, packages)
            self.assertEqual(result["report_state"], "结构未知")
            self.assertIn("unknown_build_status", result["issues"])

    def test_summary_totals_and_each_category_reconcile(self):
        packages = [pkg("item"), pkg("bad", "build_error")]
        html = report_html("armv7l", packages)
        for counts in ("<td>3</td><td>1</td><td>0</td><td>0</td><td>1</td>",
                       "<td>2</td><td>0</td><td>0</td><td>0</td><td>2</td>"):
            changed = html.replace("<td>2</td><td>1</td><td>0</td><td>0</td><td>1</td>", counts)
            self.assertEqual(self.parse(changed, packages)["report_state"], "对账失败")

    def test_expected_package_set_required_and_extra_packages_rejected(self):
        packages = [pkg("one"), pkg("two")]
        html = report_html("armv7l", packages)
        changed = self.parse(html, packages[:1])
        self.assertEqual(changed["report_state"], "完整")
        self.assertEqual(changed["package_coverage"], "不一致")
        self.assertEqual(changed["result_state"], "成功")
        result = parse_report(html, "armv7l", self.config.raw["cosmos"], None, stable=True)
        self.assertEqual(result["report_state"], "完整")
        self.assertEqual(result["package_coverage"], "未核")
        self.assertEqual(result["result_state"], "成功")

    def test_prefix_matching_raw_title_line_numbers_and_inputs(self):
        packages = [pkg("item", "build_error")]
        packages[0]["shelve"] = True
        html = report_html("armv7l", packages, title="  BUILD   Statis  Details extra")
        result = self.parse(html, packages)
        self.assertEqual(result["report_state"], "完整")
        package = result["packages"][0]
        self.assertTrue(package["shelve"])
        self.assertEqual(package["cl"], "100")
        self.assertEqual(package["version"], "1.0-1")
        self.assertIn("item", html.splitlines()[package["source_line"] - 1])
        self.assertEqual(result["input_rows"][0]["source_line"], package["source_line"])
        self.assertEqual(result["raw_table_titles"]["build"], "  BUILD   Statis  Details extra")

    def test_title_drift_is_visible_and_does_not_invalidate_correct_structure(self):
        self.manifest["previous_table_titles"] = {"armv7l": {"build": "Build Statis Details old"}}
        result = self.observed()
        self.assertEqual(result["report_state"], "完整")
        self.assertIn("table_title_drift:build", result["reports"]["armv7l"]["issues"])
        self.assertFalse(any(todo["reason"].startswith("table_title_drift") for todo in result["todos"]))

    def test_read_inputs_includes_all_rows_and_header_consistency(self):
        reader = self.reader()
        result = reader.read_inputs(reader.build_ref)
        self.assertEqual(result["header_consistency"], "一致")
        self.assertEqual(len(result["reports"]["armv7l"]["rows"]), 3)
        self.assertIn("build_conf", result["reports"]["x86_64"]["headers"])

    def test_saved_parser_has_no_real_downloader_fixture_log_has_digest(self):
        reader = self.reader()
        package = reader.read_packages(reader.build_ref, "armv7l")["packages"][1]
        artifact = reader.fetch_log(reader.build_ref, "armv7l", package)
        self.assertEqual(artifact["sha256"], digest(Path(artifact["path"]).read_bytes()))
        real = self.reader(SavedReportReader)
        with self.assertRaises(FlowError) as caught:
            real.fetch_log(real.build_ref, "armv7l", package)
        self.assertEqual(caught.exception.reason, "不支持")
        with self.assertRaises(FlowError):
            reader.observe(BuildRef("fixture", "other", "different", "cosmos"))

    def test_fixture_path_escape_is_rejected(self):
        self.manifest["reports"]["armv7l"][-1]["path"] = "../outside.html"
        with self.assertRaises(FlowError) as caught:
            self.observed()
        self.assertEqual(caught.exception.code, 4)

    def test_synthetic_full_size_counts_are_not_real_fixture_evidence(self):
        for arch, success, expansion, failed in [("armv7l", 1479, 759, 6), ("x86_64", 42, 0, 1)]:
            packages = [pkg(f"ok-{i}") for i in range(success)]
            packages += [pkg(f"missing-{i}", "expansion_error", ["absent >= 1"]) for i in range(expansion)]
            packages += [pkg(f"bad-{i}", "build_error") for i in range(failed)]
            result = self.parse(report_html(arch, packages), packages, arch)
            self.assertEqual(result["report_state"], "完整")
            self.assertEqual(result["counts"], {"total": success + expansion + failed, "succeeded": success,
                                               "export_error": 0, "expansion_error": expansion, "build_error": failed})
            self.assertTrue(result["package_keys_unique"])
            self.assertTrue(result["categories_disjoint"])


class GroupTests(ReportTests):
    # Inherit only the fixture setup, not ReportTests' test methods (see load_tests below).
    def packages(self):
        return self.observed()["reports"]["armv7l"]["packages"]

    def test_one_missing_item_one_group_and_all_items_must_be_covered(self):
        packages = self.packages()
        groups = group_expansion(packages)
        consumer = next(p for p in packages if p["category"] == "expansion_error")
        self.assertEqual(len(groups["groups"]), 2)
        self.assertFalse(package_covered(consumer, groups, [("armv7l", "provider >= 2")]))
        self.assertTrue(package_covered(consumer, groups, [("armv7l", "provider >= 2"), ("armv7l", "other")]))
        self.assertFalse(package_covered(consumer, groups, [("x86_64", "provider >= 2"), ("armv7l", "other")]))

    def test_version_constraints_are_different_signatures(self):
        packages = self.packages()
        packages[-1]["missing_dependencies"] = ["pkgconfig(x) >= 2", "pkgconfig(x)", "pkgconfig(x) >= 3"]
        self.assertEqual(len(group_expansion(packages)["groups"]), 3)

    def test_name_similarity_is_not_tool_fact(self):
        packages = self.packages()
        packages[-1]["missing_dependencies"] = ["provider-devel"]
        groups = group_expansion(packages)
        group = groups["groups"][0]
        self.assertFalse(group["certain_blockers"])
        self.assertTrue(group["suspected_blockers"])
        self.assertEqual(groups["blocking_downstream"], [])
        self.assertFalse(package_covered(packages[-1], groups))

    def test_spec_exact_provides_and_repaired_provider_required(self):
        packages = self.packages()
        provider = next(p for p in packages if p["category"] == "build_error")
        consumer = next(p for p in packages if p["category"] == "expansion_error")
        spec = b"Name: provider\nProvides: provider >= 2\n"
        (self.base / "provider.spec").write_bytes(spec)
        self.manifest["provides_evidence"] = [{"key": provider["key"], "source_kind": "spec",
                                               "path": "provider.spec", "sha256": digest(spec)}]
        groups = group_expansion(packages, self.reader().provides())
        self.assertEqual(groups["blocking_downstream"][0]["count"], 1)
        self.assertFalse(package_covered(consumer, groups, [("armv7l", "other")]))
        key = provider["key"]
        self.assertTrue(package_covered(consumer, groups, [("armv7l", "other")], [(key["arch"], key["name"], key["path"])]))
        self.manifest["provides_evidence"][0]["sha256"] = "0" * 64
        with self.assertRaises(FlowError):
            self.reader().provides()


class BrowserFixtureTests(unittest.TestCase):
    def test_success_rejection_login_unknown_and_crash_sequences(self):
        for page, expected in [("success", "accepted"), ("rejected", "rejected"), ("login", "uncertain"), ("unknown", "uncertain")]:
            driver = ScriptedDriver([{"action": "prepare", "page": "form", "fields": {"example": "value"}},
                                     {"action": "release", "page": page},
                                     {"action": "discover", "page": "success", "candidates": ["fixture-build"]},
                                     {"action": "verify", "page": "success"}])
            backend = FixtureSubmitter(driver)
            request = {"request_id": "example"}
            self.assertEqual(backend.prepare(request)["status"], "prepared")
            self.assertEqual(backend.release(request, "intent-1")["status"], expected)
            with self.assertRaises(FlowError):
                backend.release(request, "intent-1")
            self.assertEqual(backend.discover("marker")["candidates"], ["fixture-build"])
            self.assertEqual(backend.verify(request, None)["status"], "一致")
        backend = FixtureSubmitter(ScriptedDriver([{"action": "prepare", "page": "form"}, {"action": "release", "page": "crash"}]))
        backend.prepare(request)
        with self.assertRaises(DriverCrash):
            backend.release(request, "intent-2")
        with self.assertRaises(FlowError):
            backend.release(request, "intent-2")

    def test_login_prepare_and_unexpected_sequence_do_not_release(self):
        backend = FixtureSubmitter(ScriptedDriver([{"action": "prepare", "page": "login"}]))
        request = {"request_id": "example"}
        self.assertEqual(backend.prepare(request)["status"], "auth_required")
        with self.assertRaises(FlowError):
            backend.release(request, "intent")
        self.assertFalse(backend.released)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite([loader.loadTestsFromTestCase(ReportTests), loader.loadTestsFromTestCase(BrowserFixtureTests)])
    for name in GroupTests.__dict__:
        if name.startswith("test_"):
            suite.addTest(GroupTests(name))
    return suite
