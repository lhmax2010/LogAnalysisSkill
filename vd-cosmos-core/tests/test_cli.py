import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from helpers import REPO, bundle


class CLITests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.config_path, self.manifest_path, self.manifest = bundle(self.base)

    def cli(self, skill, command, *extra):
        args = [sys.executable, str(REPO / f"vd-cosmos-{skill}/scripts/run.py"), command,
                "--config", str(self.config_path)]
        if skill != "core":
            args += ["--manifest", str(self.manifest_path)]
        process = subprocess.run(args + list(extra), cwd=self.base, capture_output=True,
                                 text=True, start_new_session=True)
        data = json.loads(process.stdout)
        self.assertEqual(len(process.stdout.splitlines()), 1)
        self.assertEqual(process.stderr, "")
        self.assertEqual(process.returncode, data.get("exit_code", 0))
        return data, process.returncode

    def test_install_free_entrypoints_work_from_unrelated_directory(self):
        for skill in ("core", "watch", "fetch"):
            result, code = self.cli(skill, "--help")
            self.assertEqual(code, 0)
            self.assertIn("commands", result)
        result, code = self.cli("watch", "observe", "--backend", "fixture")
        self.assertEqual(code, 0)
        self.assertEqual(result["result_state"], "失败")
        self.assertTrue(Path(result["artifact"]["path"]).is_file())

    def test_all_fetch_commands_produce_files(self):
        for command in ("packages", "inputs", "groups", "logs"):
            result, code = self.cli("fetch", command, "--arch", "armv7l")
            self.assertEqual(code, 0)
            output = json.loads(Path(result["artifact"]["path"]).read_text())
            if command == "logs":
                self.assertEqual(len(output["logs"]), 1)
                self.assertTrue(Path(output["logs"][0]["path"]).exists())

    def test_real_backend_parses_saved_html_but_download_is_unsupported(self):
        result, code = self.cli("watch", "observe", "--backend", "real")
        self.assertEqual(code, 0)
        result, code = self.cli("fetch", "logs", "--backend", "real")
        self.assertEqual(code, 6)
        self.assertEqual(result["error"], "不支持")

    def test_invalid_args_and_non_tty_guards_exit_two(self):
        self.assertEqual(self.cli("watch", "not-a-command")[1], 2)
        self.assertEqual(self.cli("fetch", "packages")[1], 2)
        for command in ("approve", "bind", "submit", "p4.shelve"):
            result, code = self.cli("core", command)
            self.assertEqual(code, 2)
            self.assertEqual(result["error"], "terminal_required")

    def test_stale_expected_event_exits_six_without_new_artifact(self):
        first, code = self.cli("watch", "observe", "--expected-event", "0")
        self.assertEqual(code, 0)
        before = list((self.base / "data/rounds").rglob("watch-observe.json"))
        result, code = self.cli("watch", "observe", "--expected-event", "0")
        self.assertEqual(code, 6)
        self.assertEqual(list((self.base / "data/rounds").rglob("watch-observe.json")), before)

    def test_observation_failures_exit_five_and_todo_after_three(self):
        self.manifest["reports"]["armv7l"][-1]["status_code"] = 503
        self.manifest_path.write_text(json.dumps(self.manifest))
        for index in range(3):
            result, code = self.cli("watch", "observe")
            self.assertEqual(code, 5)
            inbox = (self.base / "data/inbox.md").read_text()
            self.assertEqual("three_consecutive_observation_failures" in inbox, index == 2)
        self.cli("watch", "observe")
        self.assertEqual((self.base / "data/inbox.md").read_text().count("three_consecutive_observation_failures"), 1)

    def test_header_inconsistency_writes_todo_without_advancing_ready_state(self):
        for entry in self.manifest["reports"]["x86_64"]:
            path = self.base / entry["path"]
            path.write_text(path.read_text().replace("fixture-base", "other-base"))
        result, code = self.cli("watch", "observe")
        self.assertEqual(code, 3)
        self.assertEqual(result["header_consistency"], "不一致")
        self.assertEqual(result["result_state"], "未知")
        self.assertIn("header_inconsistent", (self.base / "data/inbox.md").read_text())

    def test_stall_detection_requires_distinct_observations_without_changing_state(self):
        self.manifest["reports"].pop("x86_64")
        config = json.loads(self.config_path.read_text())
        config["poll"]["stall_polls"] = 2
        self.config_path.write_text(json.dumps(config))
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.cli("watch", "observe")
        self.cli("watch", "observe")
        self.assertNotIn("report_stalled", (self.base / "data/inbox.md").read_text())
        self.manifest["reports"]["armv7l"][-1]["observed_at"] = "2026-10-24T00:02:00Z"
        self.manifest_path.write_text(json.dumps(self.manifest))
        result, code = self.cli("watch", "observe")
        self.assertEqual(code, 0)
        self.assertEqual(result["report_state"], "部分")
        self.assertIn("report_stalled", (self.base / "data/inbox.md").read_text())

    def test_export_and_prepush_cli_contract(self):
        source = self.base / "data/reports/example.txt"
        source.parent.mkdir(parents=True)
        source.write_text("example report\n")
        result, code = self.cli("core", "export", "--source", "reports/example.txt", "--type", "report", "--name", "example")
        self.assertEqual(code, 0)
        self.assertTrue(Path(result["path"]).exists())
        self.assertEqual(self.cli("core", "prepush", "--files", str(source))[1], 0)
        source.write_text("Cookie" + ": fake\n")
        result, code = self.cli("core", "prepush", "--files", str(source))
        self.assertEqual(code, 4)
        self.assertNotIn("fake", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
