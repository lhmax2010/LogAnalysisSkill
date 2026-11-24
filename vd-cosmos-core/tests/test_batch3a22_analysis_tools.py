"""Exercise the analysis subprocess boundary with real interpreters."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import venv

from helpers import config_data
from vd_cosmos_core.analysis_tools import analyze_log, run_tool
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.submit_doctor import doctor


class AnalysisToolTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.path = self.root / 'config.json'
        self.raw = config_data(self.root / 'data')

    def config(self):
        self.path.write_text(json.dumps(self.raw))
        return load_config(self.path)

    def run_failure(self, config, code, **options):
        with self.assertRaises(FlowError) as caught:
            run_tool(config, '-c', [code], self.root, 'tool_failed', **options)
        self.assertEqual((caught.exception.code, caught.exception.reason), (5, 'tool_failed'))
        return caught.exception.details

    def test_nonzero_reports_checked_last_line_without_other_output(self):
        config = self.config()
        result = self.run_failure(config, '''
import sys
sys.stderr.write("earlier line\\nlast diagnostic\\n\\n")
sys.stdout.write("discard this output\\n")
sys.exit(7)
''')
        self.assertEqual(result, {'exit_code': 7, 'stderr_last_line': 'last diagnostic'})

    def test_stderr_tail_is_bounded_and_never_releases_fragment(self):
        self.raw['prepush']['credential_patterns'].append('restricted-fixture-text')
        config = self.config()
        result = self.run_failure(config, '''
import sys
sys.stderr.buffer.write(b'restricted-fixture-text\\n' + b'old\\n' * 250000 + b'last diagnostic\\n')
sys.exit(7)
''')
        self.assertEqual(result, {'exit_code': 7, 'stderr_last_line': 'last diagnostic'})
        partial = self.run_failure(config, '''
import sys
sys.stderr.buffer.write(b'restricted-fixture-text ' + b'x' * 8000 + b'\\n')
sys.exit(7)
''')
        self.assertEqual(partial, {'exit_code': 7})

    def test_blocked_or_undecodable_stderr_drops_the_diagnostic(self):
        self.raw['prepush']['credential_patterns'].append('restricted-fixture-text')
        config = self.config()
        for emitted in (b'restricted-fixture-text\nordinary final line\n', b'\xff\n'):
            with self.subTest(emitted=emitted):
                self.assertEqual(self.run_failure(config, f'''
import sys
sys.stderr.buffer.write({emitted!r})
sys.exit(7)
'''), {'exit_code': 7})

    def test_tools_still_time_out(self):
        detail = self.run_failure(self.config(), 'import time; time.sleep(60)', timeout=0.2)
        self.assertTrue(detail['timed_out'])
        self.assertLess(detail['exit_code'], 0)

    def test_analyzer_python_validates_relative_executable_without_resolving_symlink(self):
        executable = self.root / 'python-link'
        executable.symlink_to(sys.executable)
        self.raw['analyzer']['python'] = './python-link'
        self.assertEqual(self.config().raw['analyzer']['python'], str(executable))
        unavailable = self.root / 'not-executable'
        unavailable.touch(mode=0o600)
        for value in ('', 'missing-python', unavailable.name, str(self.root), 42, 'bad\x00path'):
            with self.subTest(value=value):
                self.raw['analyzer']['python'] = value
                with self.assertRaisesRegex(FlowError, '^invalid_analyzer_python$'):
                    self.config()

    def test_selected_venv_is_used_and_missing_yaml_is_reported_before_analysis(self):
        environment = self.root / 'analysis-venv'
        venv.EnvBuilder(with_pip=False, symlinks=True).create(environment)
        self.raw['analyzer']['python'] = 'analysis-venv/bin/python'
        config = self.config()
        result = self.run_failure(config, 'import sys; print(sys.prefix, file=sys.stderr); sys.exit(7)')
        self.assertEqual(result['stderr_last_line'], str(environment))
        with self.assertRaises(FlowError) as caught:
            analyze_log(config, self.root / 'not-read.log', {'name': 'example', 'arch': 'armv7l'}, 'build_error')
        error = caught.exception
        self.assertEqual((error.code, error.reason), (6, 'log_analyzer_dependency_missing'))
        self.assertEqual(error.details['module'], 'yaml')
        self.assertEqual(error.details['todo']['message'], 'install PyYAML==6.0.1 in the analysis venv')
        result = doctor(config, package_probe=lambda: {'verified': True, 'count': 0})
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['analysis_dependencies'], {'available': False, **error.as_dict()})
