import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from helpers import CORE, REPO
from vd_cosmos_core.backends import SavedReportReader
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest
from vd_cosmos_core.groups import group_expansion, package_covered
from vd_cosmos_core.report import parse_report
from vd_cosmos_core.verify import compare


class RealFormatTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.fixture = self.base / "fixture"
        shutil.copytree(CORE / "fixtures/real_format", self.fixture)
        self.raw = json.loads((CORE / "config.sample.json").read_text())
        self.raw["data_root"] = str(self.base / "owned")
        self.config_path = self.base / "config.json"
        self.config_path.write_text(json.dumps(self.raw))
        self.config = load_config(self.config_path)
        self.manifest_path = self.fixture / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text())

    def reader(self):
        return SavedReportReader(self.config, self.manifest_path)

    def observe(self):
        reader = self.reader()
        return reader.observe(reader.build_ref)

    def parse(self, html, arch="armv7l"):
        return parse_report(html, arch, self.raw["cosmos"], self.manifest["expected_packages"][arch], stable=True)

    def test_real_format_complete_summary_suffix_and_unquoted_link(self):
        observed = self.observe()
        self.assertEqual(observed["report_state"], "完整")
        self.assertEqual(observed["result_state"], "失败")
        expected = json.loads((self.fixture / "expected-counts.json").read_text())
        for arch, report in observed["reports"].items():
            self.assertEqual(report["counts"], expected[arch])
            self.assertTrue(report["package_keys_unique"])
            self.assertTrue(report["categories_disjoint"])
            self.assertEqual(report["result_state"], "失败")
        package = observed["reports"]["x86_64"]["packages"][0]
        self.assertEqual(package["version"], "1.23-0")
        self.assertEqual(package["category"], "build_error")
        self.assertEqual(package["raw_status"], "Failed")

    def test_nested_paragraph_headers_do_not_merge(self):
        observed = self.observe()
        self.assertEqual(observed["header_consistency"], "一致")
        for arch, report in observed["reports"].items():
            source = (self.fixture / ("report_" + arch + ".html")).read_text()
            for label, key in (("BASE SNAPSHOT", "base"), ("PRODUCT SNAPSHOT", "product"), ("BUILD CONF", "build_conf")):
                line = next(line for line in source.splitlines() if "<B>" + label + ":" in line)
                expected = line.split("</B>", 1)[1].removesuffix("<p>").strip()
                self.assertEqual(report["headers"][key], expected)
            self.assertEqual(report["headers"]["profile"], "tizen.393")

    def test_summary_case_whitespace_and_counts_still_reconcile(self):
        html = (self.fixture / "report_armv7l.html").read_text()
        changed = html.replace("Total Packages", "TOTAL   PACKAGES").replace("succeeded Packages", " succeeded    packages ")
        self.assertEqual(self.parse(changed)["report_state"], "完整")
        bad = changed.replace("<td>4</td>", "<td>5</td>", 1)
        self.assertIn("summary_total_mismatch", self.parse(bad)["issues"])
        self.assertEqual(self.parse(bad)["report_state"], "对账失败")

    def test_supplied_head120_snippets_never_count_as_complete(self):
        expected_counts = {"armv7l": {"total": 2244, "succeeded": 1479, "export_error": 0, "expansion_error": 759, "build_error": 6},
                           "x86_64": {"total": 43, "succeeded": 42, "export_error": 0, "expansion_error": 0, "build_error": 1}}
        for arch in expected_counts:
            source = REPO / "docs/enhance/batch1/real-snippets" / ("report_" + arch + "_head120.html")
            result = parse_report(source.read_text(), arch, self.raw["cosmos"], None, stable=False)
            self.assertEqual(result["counts"], expected_counts[arch])
            self.assertNotEqual(result["report_state"], "完整")
            self.assertEqual(result["result_state"], "未知")

    def test_own_failed_title_precedes_successful_promotion(self):
        observed = self.observe()
        self.assertEqual(observed["execution_state"], "已结束")
        evidence = observed["execution_evidence"]
        self.assertEqual(evidence["subresult"], "failed")
        self.assertEqual(evidence["title"], "Build is failed")
        self.assertEqual(evidence["source_line"], 2)
        self.assertEqual(evidence["basis"], "first_build_status_title")
        self.assertFalse(observed["terminal_prerequisite_met"])  # local_simulation

    def test_running_queued_and_all_terminal_words(self):
        for word, state in [("running", "运行"), ("queued", "排队"), ("waiting", "排队"),
                            *[(w, "已结束") for w in self.raw["cosmos"]["status_source"]["terminal_words"]]]:
            (self.fixture / "detail.html").write_text('<i title="Build is ' + word + '"></i><i title="Build is successful"></i>')
            observed = self.observe()
            self.assertEqual(observed["execution_state"], state)
            self.assertEqual(observed["execution_evidence"]["subresult"], word)

    def test_unknown_or_absent_title_never_falls_through_or_uses_text(self):
        for html in ('<i title="Build is unrecognized"></i><i title="Build is failed"></i>',
                     '<p>Build is failed</p><a class="build-status successful">[downstream:BUILD_COMPLETE]</a>',
                     '<script>const markup = \'<i title="Build is failed"></i>\';</script>'):
            (self.fixture / "detail.html").write_text(html)
            result = self.observe()
            self.assertEqual(result["execution_state"], "未知")
            self.assertIn("终态推定", result["terminal_inference"])
            self.assertFalse(result["terminal_prerequisite_met"])

    def test_configured_regex_does_not_select_a_later_status(self):
        self.config.raw["cosmos"]["status_source"]["status_title_regex"] = "^Build is (successful)$"
        self.assertEqual(self.observe()["execution_state"], "未知")

    def test_new_status_schema_accepts_and_rejects_malformed_old_or_overlap(self):
        valid = self.raw["cosmos"]["status_source"]
        invalid = [None, {"kind": "detail_page", "complete_markers": ["BUILD_COMPLETE"]}]
        # None remains the documented no-source configuration; the old shape is refused.
        self.config.raw["cosmos"]["status_source"] = None
        self.assertEqual(self.observe()["execution_state"], "未知")
        invalid = invalid[1:]
        for key, value in [("status_title_regex", "["), ("status_title_regex", "^Build is failed$"),
                           ("terminal_words", "failed"), ("queued_words", []),
                           ("running_words", ["failed"]), ("url_template", "file:///unused")]:
            bad = copy.deepcopy(valid); bad[key] = value; invalid.append(bad)
        extra = copy.deepcopy(valid); extra["complete_markers"] = ["BUILD_COMPLETE"]; invalid.append(extra)
        for status in invalid:
            config = copy.deepcopy(self.raw); config["cosmos"]["status_source"] = status
            self.config_path.write_text(json.dumps(config))
            with self.assertRaises(FlowError) as caught:
                load_config(self.config_path)
            self.assertEqual(caught.exception.code, 2)

    def test_other_message_is_preserved_complete_manual_only_and_todo(self):
        observed = self.observe()
        packages = observed["reports"]["armv7l"]["packages"]
        consumer = next(p for p in packages if p["key"]["name"] == "odd-consumer")
        provider = next(p for p in packages if p["category"] == "build_error")
        message = "conflict detected: alpha versus beta"
        self.assertEqual(consumer["other_expansion_messages"], [message])
        self.assertEqual(consumer["missing_dependencies"], [message])
        self.assertEqual(observed["report_state"], "完整")
        self.assertIn({"arch": "armv7l", "reason": "other_expansion_message_format"}, observed["todos"])
        evidence = [{"key": provider["key"], "source_kind": "spec", "sha256": "a" * 64,
                     "evidence_path": "fixture.spec", "verified": True, "provides": [message]}]
        groups = group_expansion(packages, evidence)
        group = next(g for g in groups["groups"] if g["signature"] == message)
        self.assertEqual(group["message_format"], "其它格式")
        self.assertTrue(group["requires_manual_confirmation"])
        self.assertFalse(group["certain_blockers"])
        self.assertFalse(groups["blocking_downstream"])
        key = provider["key"]
        self.assertFalse(package_covered(consumer, groups, repaired_providers=[(key["arch"], key["name"], key["path"])]))
        self.assertTrue(package_covered(consumer, groups, [("armv7l", message)]))

    def test_mixed_known_and_other_messages_require_both_covered(self):
        html = (self.fixture / "report_armv7l.html").read_text().replace(
            'nothing provides other needed by consumer', 'unexpected dependency conflict')
        report = self.parse(html)
        consumer = next(p for p in report["packages"] if p["key"]["name"] == "consumer")
        groups = group_expansion(report["packages"])
        self.assertEqual(report["report_state"], "完整")
        self.assertFalse(package_covered(consumer, groups, [("armv7l", "provider >= 2")]))
        self.assertTrue(package_covered(consumer, groups, [("armv7l", "provider >= 2"), ("armv7l", "unexpected dependency conflict")]))

    def test_same_signature_other_format_cannot_inherit_standard_blocker(self):
        packages = self.observe()["reports"]["armv7l"]["packages"]
        other = next(p for p in packages if p["other_expansion_messages"])
        standard = next(p for p in packages if p["key"]["name"] == "consumer")
        provider = next(p for p in packages if p["category"] == "build_error")
        signature = other["other_expansion_messages"][0]
        standard["missing_dependencies"] = [signature]
        evidence = [{"key": provider["key"], "source_kind": "spec", "sha256": "b" * 64,
                     "evidence_path": "fixture.spec", "verified": True, "provides": [signature]}]
        groups = group_expansion(packages, evidence)
        group = next(g for g in groups["groups"] if g["signature"] == signature)
        self.assertEqual(len(group["members"]), 2)
        self.assertTrue(group["requires_manual_confirmation"])
        self.assertFalse(group["certain_blockers"])
        self.assertFalse(groups["blocking_downstream"])

    def test_expansion_source_line_wrap_is_whitespace_br_separates_messages(self):
        html = (self.fixture / "report_armv7l.html").read_text()
        html = html.replace('provider &gt;= 2', 'provider &gt;=\n  2')
        html = html.replace('conflict detected: alpha   versus beta',
                            'conflict detected:\n alpha versus beta<br>conflict detected: alpha versus beta')
        report = self.parse(html)
        self.assertEqual(report["report_state"], "完整")
        consumer = next(p for p in report["packages"] if p["key"]["name"] == "consumer")
        other = next(p for p in report["packages"] if p["key"]["name"] == "odd-consumer")
        self.assertEqual(consumer["missing_dependencies"], ["provider >= 2", "other"])
        self.assertEqual(other["missing_dependencies"], ["conflict detected: alpha versus beta"])
        self.assertEqual(len(other["other_expansion_messages"]), 2)

    def test_other_format_does_not_mask_bad_column_count_or_path(self):
        source = (self.fixture / "report_armv7l.html").read_text()
        for html in (source.replace('<td>odd-consumer</td>', '<td>odd-consumer</td><td>extra</td>'),
                     source.replace('//example/packages/odd-consumer/...@101', 'bad-revision')):
            self.assertEqual(self.parse(html)["report_state"], "结构未知")

    def test_unknown_format_todo_is_written_by_watch(self):
        process = subprocess.run([sys.executable, str(REPO / 'vd-cosmos-watch/scripts/run.py'), 'observe',
                                  '--config', str(self.config_path), '--manifest', str(self.manifest_path),
                                  '--backend', 'real'], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["report_state"], "完整")
        self.assertIn("other_expansion_message_format", (self.config.data_root / "inbox.md").read_text())


class VerifyScriptTests(RealFormatTests):
    def invoke(self, *extra, commit=None):
        head = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        command = ['bash', '--noprofile', '--norc', str(CORE / 'scripts/verify_b1_real.sh'), commit or head,
                   '--config', str(self.config_path), '--arm-report', str(self.fixture / 'report_armv7l.html'),
                   '--x86-report', str(self.fixture / 'report_x86_64.html'), '--detail-page', str(self.fixture / 'detail.html'),
                   '--rows', str(self.fixture / 'rows.txt'), '--links', str(self.fixture / 'links.txt'),
                   '--run-id', 'fixture-run', '--mode', 'fixture', '--fixture-counts', str(self.fixture / 'expected-counts.json')]
        process = subprocess.run(command + list(extra), capture_output=True, text=True, cwd=self.base)
        self.assertEqual(process.stderr, '')
        self.assertEqual(process.stdout.splitlines()[0], head)
        output = json.loads(process.stdout.splitlines()[-1])
        self.assertEqual(process.returncode, output['exit_code'])
        return output

    def test_verify_pass_export_reassembly_and_source_immutability(self):
        before = {p.name: digest(p.read_bytes()) for p in self.fixture.iterdir()}
        output = self.invoke()
        self.assertEqual(output['verdict'], 'PASS')
        result_path = Path(output['result_file']['path'])
        result = json.loads(result_path.read_text())
        self.assertTrue(result['rows_comparison']['equal'])
        self.assertTrue(result['links_comparison']['equal'])
        self.assertTrue(result['arm_path_set_comparison']['equal'])
        self.assertEqual(result['baselines']['x86_64'], '自基线，未独立核验')
        self.assertEqual(result['other_format_message_count'], 1)
        self.assertEqual(result['execution_evidence']['subresult'], 'failed')
        self.assertGreater(result['snapshot_interval_s'], self.raw['poll']['interval_s'])
        bundle = output['export']; folder = Path(bundle['path']).parent
        blocks = [folder / b['file'] for b in bundle['blocks']]
        self.assertEqual(b''.join(p.read_bytes() for p in blocks), result_path.read_bytes())
        for block, path in zip(bundle['blocks'], blocks):
            self.assertEqual(block['sha256'], digest(path.read_bytes()))
        self.assertEqual(before, {p.name: digest(p.read_bytes()) for p in self.fixture.iterdir()})

    def test_verify_wrong_commit_stops_before_any_output_directory(self):
        output = self.invoke(commit='0' * 40)
        self.assertEqual(output['exit_code'], 6)
        self.assertFalse(self.config.data_root.exists())

    def test_verify_rows_cl_shelve_and_duplicate_replacements_rejected(self):
        path = self.fixture / 'rows.txt'; source = path.read_text()
        for replacement in (source.replace('@102(shelve)', '@999(shelve)'),
                            source.replace('@102(shelve)', '@102'),
                            source.replace(source.splitlines()[1], source.splitlines()[0])):
            path.write_text(replacement)
            output = self.invoke()
            self.assertEqual(output['verdict'], 'FAIL')
            result = json.loads(Path(output['result_file']['path']).read_text())
            self.assertFalse(result['rows_comparison']['equal'])
            self.assertTrue(result['rows_comparison']['differences_first20'])

    def test_verify_links_multiplicity_and_version_checked(self):
        path = self.fixture / 'links.txt'; source = path.read_text()
        for replacement in (source.replace('provider-1.0-1', 'provider-1.0-2'), source + source.splitlines()[0] + '\n'):
            path.write_text(replacement)
            output = self.invoke()
            self.assertEqual(output['verdict'], 'FAIL')
            result = json.loads(Path(output['result_file']['path']).read_text())
            self.assertFalse(result['links_comparison']['equal'])

    def test_verify_unknown_execution_and_header_mismatch_fail(self):
        detail = self.fixture / 'detail.html'; original = detail.read_text()
        detail.write_text('<p>No status element</p>')
        self.assertEqual(self.invoke()['verdict'], 'FAIL')
        detail.write_text(original)
        report = self.fixture / 'report_x86_64.html'
        report.write_text(report.read_text().replace('build.conf@14368686', 'build.conf@14368687'))
        self.assertEqual(self.invoke()['verdict'], 'FAIL')

    def test_verify_real_counts_cannot_use_fixture_override(self):
        output = self.invoke('--mode', 'real')
        self.assertEqual(output['verdict'], 'FAIL')
        self.assertEqual(output['exit_code'], 2)

    def test_verify_credentials_block_copy_and_never_echo_content(self):
        path = self.fixture / 'detail.html'
        path.write_text('Cookie' + ': synthetic-private-value\n')
        output = self.invoke()
        self.assertEqual(output['exit_code'], 4)
        result_path = Path(output['result_file']['path'])
        self.assertNotIn('synthetic-private-value', result_path.read_text())
        self.assertFalse((result_path.parent / 'detail-page.html').exists())

    def test_difference_list_is_limited_and_retains_total_count(self):
        result = compare([(str(i),) for i in range(30)], [])
        self.assertEqual(result['difference_count'], 30)
        self.assertEqual(len(result['differences_first20']), 20)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite([loader.loadTestsFromTestCase(RealFormatTests)])
    for name in VerifyScriptTests.__dict__:
        if name.startswith('test_'):
            suite.addTest(VerifyScriptTests(name))
    return suite
