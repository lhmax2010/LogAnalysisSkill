"""Regressions for Python builds that omit optional C extensions."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from helpers import bundle
from vd_cosmos_core.config import load_config
from vd_cosmos_core.diagnosis import clang_release
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.submit_doctor import doctor


PRIMARY = (b'<metadata xmlns="http://linux.duke.edu/metadata/common">'
           b'<package><name>clang</name><version ver="22.1.8" rel="5.2"/></package></metadata>')


class OptionalStdlibTests(unittest.TestCase):
    def test_optional_compression_is_loaded_only_for_the_requested_format(self):
        with tempfile.TemporaryDirectory() as work:
            for module, suffix, advice in (
                ('lzma', '.xz', 'use the .gz repodata or a Python built with liblzma'),
                ('bz2', '.bz2', 'use the .gz repodata or a Python built with libbz2'),
            ):
                with self.subTest(module=module):
                    path = Path(work) / ('primary.xml' + suffix)
                    try:
                        codec = importlib.import_module(module)
                    except ImportError:
                        codec = None
                    if codec:
                        path.write_bytes(codec.compress(PRIMARY))
                        self.assertEqual(clang_release(path), '22.1.8-5.2')
                        path.write_bytes(b'invalid repodata')
                        with self.assertRaisesRegex(FlowError, '^clang_primary_repodata_invalid$'):
                            clang_release(path)
                    with patch.dict(sys.modules, {module: None}):
                        with self.assertRaises(FlowError) as caught:
                            clang_release(path)
                    self.assertEqual(caught.exception.code, 6)
                    self.assertEqual(caught.exception.reason, module + '_unavailable')
                    self.assertEqual(caught.exception.details['todo'],
                                     {'reason': module + '_unavailable', 'message': advice})
            path = Path(work) / 'primary.xml'
            path.write_bytes(PRIMARY)
            self.assertEqual(clang_release(path), '22.1.8-5.2')

    def test_doctor_reports_missing_modules_as_facts(self):
        with tempfile.TemporaryDirectory() as work:
            config_path, _, _ = bundle(Path(work))
            config = load_config(config_path)
            probe = lambda: {'verified': True, 'count': 0}
            with patch('vd_cosmos_core.submit_doctor.validate_config'), patch.dict(
                    sys.modules, dict.fromkeys(('lzma', 'bz2', 'sqlite3', 'ssl'))):
                result = doctor(config, package_probe=probe)
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(result['optional_stdlib'],
                             dict.fromkeys(('lzma', 'bz2', 'sqlite3', 'ssl'), False))

    def test_missing_sqlite_and_ssl_fail_only_at_operations_that_require_them(self):
        with tempfile.TemporaryDirectory() as work:
            code = '''
from pathlib import Path
from types import SimpleNamespace
import json
import sys
sys.modules['_sqlite3'] = sys.modules['_ssl'] = None
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.transport import HTTPTransport
root = Path(sys.argv[1])
config = SimpleNamespace(raw={'fetch': {'deadline_s': 1, 'timeout_s': 1, 'user_agent': 'fixture'}})
transport = HTTPTransport(config)
transport.opener(None)
for operation in (lambda: EventStore(root), lambda: transport.get('https://example.invalid', 16)):
    try:
        operation()
    except FlowError as error:
        print(json.dumps([error.code, error.reason]))
    else:
        raise AssertionError('operation should fail')
assert not list(root.iterdir())
'''
            result = subprocess.run([sys.executable, '-c', code, work], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([json.loads(line) for line in result.stdout.splitlines()],
                             [[6, 'sqlite3_unavailable'], [6, 'ssl_unavailable']])
