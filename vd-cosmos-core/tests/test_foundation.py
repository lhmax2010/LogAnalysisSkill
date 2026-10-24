import io
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from helpers import bundle, config_data
from vd_cosmos_core.commands import Category, CommandContext, command_context
from vd_cosmos_core.config import check_filesystem, load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.export import check_content, export_file, utf8_chunks
from vd_cosmos_core.files import atomic_write, digest
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.models import BuildRef
from vd_cosmos_core.p4 import P4Adapter
from vd_cosmos_core.state import EventStore


def contend_lock(root, queue):
    try:
        with OperationLock(root, "round", "round-1"):
            queue.put(0)
    except FlowError as error:
        queue.put(error.code)


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.config_path, self.manifest, _ = bundle(self.base)
        self.config = load_config(self.config_path)

    def assert_code(self, code, callable_, *args, **kwargs):
        with self.assertRaises(FlowError) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_config_relative_paths_and_local_filesystem(self):
        data = config_data("owned")
        self.config_path.write_text(json.dumps(data))
        config = load_config(self.config_path)
        self.assertEqual(config.data_root, self.base / "owned")
        self.assertTrue(config.filesystem["type"])
        self.assertFalse(config.data_root.exists())

    def test_config_missing_invalid_and_duplicate_keys_rejected(self):
        for transform in (lambda x: x.pop("data_root"),
                          lambda x: x["export"].update(chunk_bytes=3),
                          lambda x: x["cosmos"].update(archs=["armv7l", "armv7l"]),
                          lambda x: x["prepush"].update(credential_patterns=["["])):
            data = config_data(self.base / "owned")
            transform(data)
            self.config_path.write_text(json.dumps(data, default=str))
            self.assert_code(2, load_config, self.config_path)
        self.config_path.write_text('{"data_root":"a","data_root":"b"}')
        self.assert_code(2, load_config, self.config_path)

    def test_nfs_cifs_and_stat_failure_refused_before_writes(self):
        for kind in ("nfs", "nfs4", "cifs", "smb2", "unknown"):
            with patch("vd_cosmos_core.config.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = kind
                self.assert_code(6, load_config, self.config_path)
            self.assertFalse(self.config.data_root.exists())
        with patch("vd_cosmos_core.config.subprocess.run", side_effect=OSError()):
            self.assert_code(6, check_filesystem, self.base)

    def test_path_escape_and_symlink_escape_refused(self):
        self.config.data_root.mkdir()
        (self.config.data_root / "escape").symlink_to(self.base)
        for path in ("../escape.txt", "escape/out.txt", str(self.base / "out.txt")):
            self.assert_code(4, atomic_write, self.config.data_root, path, b"no")
        self.assertFalse((self.base / "out.txt").exists())
        artifact = atomic_write(self.config.data_root, "reports/a.txt", b"yes")
        self.assertEqual(Path(artifact["path"]).read_bytes(), b"yes")

    def test_flock_contention_across_processes_and_release(self):
        queue = multiprocessing.Queue()
        with OperationLock(self.config.data_root, "round", "round-1"):
            process = multiprocessing.Process(target=contend_lock, args=(self.config.data_root, queue))
            process.start()
            process.join(10)
            self.assertEqual(process.exitcode, 0)
            self.assertEqual(queue.get(timeout=2), 6)
        with OperationLock(self.config.data_root, "round", "round-1"):
            pass
        with OperationLock(self.config.data_root, "profile", "profile-1"):
            self.assert_code(6, OperationLock(self.config.data_root, "profile", "profile-1").__enter__)

    def test_command_categories_receive_cannot_write_authorization(self):
        context = command_context("analyze.accept")
        with EventStore(self.config.data_root) as store:
            first = store.append(context, "analysis_received", {}, 0)
            second = store.append(context, "analysis_rejected", {}, first)
            for kind in ("approved", "bind", "click_intent", "terminal_confirmed", "observation_recorded"):
                self.assert_code(4, store.append, context, kind, {}, second)
            self.assertEqual(store.head(), second)

    def test_non_tty_manual_and_external_commands_refused(self):
        with patch("builtins.open", side_effect=OSError()):
            for name in ("approve", "bind", "submit", "p4.shelve"):
                self.assert_code(2, command_context, name)
        self.assert_code(2, command_context, "unknown")

    def test_terminal_yes_required(self):
        class TTY(io.StringIO):
            def isatty(self): return True
            def write(self, text): return len(text)
        with patch("builtins.open", return_value=TTY("no\n")):
            self.assert_code(3, command_context, "approve")
        with patch("builtins.open", return_value=TTY("yes\n")):
            self.assertTrue(command_context("approve").terminal_confirmed)

    def test_optimistic_conflict_and_sqlite_immediate_transaction(self):
        context = command_context("watch.observe")
        with EventStore(self.config.data_root) as a, EventStore(self.config.data_root) as b:
            old_head = b.head()
            a.append(context, "observation_recorded", {"sample": 1}, old_head)
            self.assert_code(6, b.append, context, "observation_recorded", {}, old_head)
            a.connection.execute("BEGIN IMMEDIATE")
            self.assert_code(6, b.append, context, "observation_recorded", {}, a.head())
            a.connection.execute("ROLLBACK")
            self.assertEqual(len(b.events()), 1)

    def test_event_journal_cannot_update_or_delete(self):
        with EventStore(self.config.data_root) as store:
            store.append(command_context("watch.observe"), "observation_recorded", {}, 0)
            for sql in ("UPDATE events SET payload='{}'", "DELETE FROM events"):
                with self.assertRaises(sqlite3.IntegrityError):
                    store.connection.execute(sql)
            self.assertEqual(store.head(), 1)

    def test_session_and_click_uniqueness_preserve_failed_preparation_history(self):
        context = CommandContext("submit", Category.EXTERNAL, True)
        with EventStore(self.config.data_root) as store:
            head = store.append(context, "submit_session_started", {}, 0, request_id="r", operation_id="op1")
            self.assert_code(6, store.append, context, "submit_session_started", {}, head, request_id="r", operation_id="op2")
            head = store.append(context, "submit_session_finished", {"result": "preparation_failed"}, head, request_id="r", operation_id="op1")
            head = store.append(context, "submit_session_started", {}, head, request_id="r", operation_id="op2")
            head = store.append(context, "click_intent", {}, head, request_id="r", operation_id="op2")
            self.assert_code(6, store.append, context, "click_intent", {}, head, request_id="r", operation_id="op2")
            head = store.append(context, "submit_session_finished", {}, head, request_id="r", operation_id="op2")
            self.assert_code(6, store.append, context, "submit_session_started", {}, head, request_id="r", operation_id="op3")
            self.assertEqual(len(store.events()), 5)

    def test_bind_uniqueness_includes_backend_instance_and_execution_kind(self):
        context = CommandContext("bind", Category.HUMAN, True)
        ref = BuildRef("fixture", "instance", "123", "cosmos")
        with EventStore(self.config.data_root) as store:
            head = store.append(context, "bind", {}, 0, request_id="r1", build_ref=ref)
            self.assert_code(6, store.append, context, "bind", {}, head, request_id="r2", build_ref=ref)
            local = BuildRef("fixture", "instance", "123", "local_simulation")
            store.append(context, "bind", {}, head, request_id="r2", build_ref=local)
            self.assertEqual(len(store.events()), 2)
        self.assert_code(2, BuildRef, "fixture", "i", "1", "unknown")

    def test_p4_environment_plan_and_forbidden_commands(self):
        adapter = P4Adapter(self.config)
        with patch.dict(os.environ, {"P4PORT": "inherited-connection", "P4CONFIG": "inherited-config"}):
            plan = adapter.plan(["print", "//example/package@1"])
            self.assertNotIn("P4PORT", plan.env)
            self.assertEqual(plan.env["P4CONFIG"], str(self.config.data_root / "settings/p4.conf"))
            self.assertTrue(plan.cwd.startswith(str(self.config.data_root)))
        for args in (["set"], ["login"], ["client", "-i"], ["submit"], ["-p", "server", "info"]):
            self.assert_code(4, adapter.plan, args)
        self.assert_code(6, adapter.execute, ["info"])

    def test_export_utf8_long_line_roundtrip_sizes_and_full_digests(self):
        content = ("很长的一行😀" * 40 + "\nnext line\n").encode()
        self.config.raw["export"]["chunk_bytes"] = 17
        atomic_write(self.config.data_root, "reports/input.txt", content)
        result = export_file(self.config, "reports/input.txt", "report", "example")
        chunks = []
        for block in result["blocks"]:
            data = (Path(result["path"]).parent / block["file"]).read_bytes()
            data.decode("utf-8")
            self.assertLessEqual(len(data), 17)
            self.assertEqual(block["size"], len(data))
            self.assertEqual(block["sha256"], digest(data))
            self.assertEqual(len(block["sha256"]), 64)
            chunks.append(data)
        self.assertEqual(b"".join(chunks), content)
        self.assertEqual(result["total_blocks"], len(chunks))

    def test_export_credentials_at_end_block_every_artifact(self):
        secret_example = ("safe\n" * 100 + "Cookie" + ": synthetic-example\n").encode()
        atomic_write(self.config.data_root, "reports/input.txt", secret_example)
        self.assert_code(4, export_file, self.config, "reports/input.txt", "report", "blocked")
        self.assertFalse((self.config.data_root / "export").exists())

    def test_word_hits_warn_credential_examples_never_bypass_export(self):
        wordlist = self.base / "words.txt"
        wordlist.write_text("private-name\n")
        self.config.raw["prepush"]["words_file"] = str(wordlist)
        checks = check_content(b"private-name", self.config)
        self.assertTrue(checks["allowed"])
        self.assertEqual(len(checks["warnings"]), 1)
        sample = ("Cookie" + ": fake # credential-test-sample").encode()
        self.assertTrue(check_content(sample, self.config, test_exemptions=True)["allowed"])
        self.assertFalse(check_content(sample, self.config)["allowed"])
        self.assert_code(4, export_file, self.config, "browser/profile.txt", "report", "blocked")
        self.assert_code(4, export_file, self.config, "reports/a", "authentication", "blocked")

    def test_authentication_page_with_empty_field_cannot_be_relabelled_report(self):
        html = '<form><input type="password"></form>'
        atomic_write(self.config.data_root, "reports/login.html", html.encode())
        self.assert_code(4, export_file, self.config, "reports/login.html", "report", "blocked")
        self.assertFalse((self.config.data_root / "export").exists())

    def test_credential_pattern_families_block_without_echoing_content(self):
        samples = ["-----BEGIN " + "RSA PRIVATE KEY-----", "Set-" + "Cookie: fake",  # credential-test-sample
                   "jsessionid" + "=fake", "SAML" + "Response=fake", "Relay" + "State=fake",
                   "wicket" + ":interface=fake", '<input type="hidden" name="wicket-session" value="fake">',  # credential-test-sample
                   '<input type="password" value="fake">', "example:1666=user:" + "a" * 32]  # credential-test-sample
        for sample in samples:
            checks = check_content(sample.encode(), self.config)
            self.assertFalse(checks["allowed"], sample.split("=")[0])
            self.assertNotIn(sample, json.dumps(checks))


if __name__ == "__main__":
    unittest.main()
