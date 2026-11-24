from pathlib import Path
import subprocess
import json
import unittest

from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, digest, json_bytes
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.verify_b3a2 import main, verify
from test_batch3a2_package import KEY, PackageFixture, ROOT


class VerifierTests(PackageFixture, unittest.TestCase):
    def input_run(self, with_snapshot):
        ref = {'backend_id': 'fixture', 'instance_id': 'https://cosmos.example.invalid',
               'run_id': '19270912', 'execution_kind': 'cosmos'}
        key = digest(json_bytes(ref))
        report = {'settled': True, 'settled_basis': 'elapsed_window', 'evidence': {'sha256': 'a'},
                  'packages': [{'key': KEY, 'category': 'build_error'}]}
        receipt = {'logs': [self.item], 'observation': {'build_ref': ref, 'reports': {KEY['arch']: report}}}
        self.register('observation_recorded', 'fetch.logs', {'build': key,
                      'artifact': atomic_write(self.root, 'real-logs.json', json_bytes(receipt))})
        if with_snapshot:
            snapshot = atomic_write(self.root, 'real-snapshot.json', json_bytes(self.snapshot))
            self.register('snapshot_completed', 'analyze.snapshot', {'build': key, 'package': KEY,
                          'artifact': snapshot})
        target = self.root / 'verification'
        target.mkdir()
        return key, target

    def test_verifier_copies_existing_inputs_and_only_accepts_fixture_in_scratch(self):
        build, target = self.input_run(True)
        db = self.root / 'state/state.db'
        filename = Path(self.item['path'])
        with EventStore(self.root) as store:
            old = store.head()
            db_bytes, log = db.read_bytes(), filename.read_bytes()
            result = verify(self.config, '19270912', target)
            self.assertEqual(result['verdict'], 'PASS')
            self.assertEqual(len(result['tasks']), 1)
            self.assertTrue(result['fixture_receiver']['fixture'])
            self.assertEqual(store.head(), old)
            self.assertEqual(db.read_bytes(), db_bytes)
            self.assertEqual(filename.read_bytes(), log)
            self.assertFalse(store.events(build, kinds=['analysis_prepared', 'analysis_received']))
        with EventStore(target) as isolated:
            events = isolated.events(build, kinds=['analysis_received'])
            self.assertTrue(events[0]['payload']['fixture'])

    def test_missing_snapshot_refuses_without_fetch(self):
        _, target = self.input_run(False)
        with self.assertRaisesRegex(FlowError, 'analysis_verifier_snapshot_inputs_required') as caught:
            verify(self.config, '19270912', target)
        self.assertEqual(caught.exception.details['candidate_count'], 1)
        self.assertEqual(caught.exception.details['packages'][0]['snapshot'], 'registered_snapshot_required')

    def test_verifier_checks_complete_packages_and_lists_incomplete_packages(self):
        build, target = self.input_run(True)
        receipt = json.loads((self.root / 'real-logs.json').read_text())
        absent = dict(KEY, name='missing-log', path='//depot/missing-log')
        missing_snapshot = dict(KEY, name='missing-snapshot', path='//depot/missing-snapshot')
        report = receipt['observation']['reports'][KEY['arch']]
        report['packages'] += [{'key': key, 'category': 'build_error'} for key in (absent, missing_snapshot)]
        receipt['logs'].append(dict(self.item, key=missing_snapshot))
        self.register('observation_recorded', 'fetch.logs', {'build': build,
                      'artifact': atomic_write(self.root, 'partial-logs.json', json_bytes(receipt))})

        result = verify(self.config, '19270912', target)
        self.assertEqual((result['verdict'], result['exit_code']), ('PARTIAL', 0))
        self.assertEqual((result['packages_total'], result['packages_verified']), (3, 1))
        self.assertEqual(result['verification_scope'], 'packages_with_valid_final_log_snapshot_and_declared_sources')
        self.assertEqual([task['package'] for task in result['tasks']], [KEY])
        rows = {row['package']['name']: row for row in result['packages']}
        self.assertTrue(rows[KEY['name']]['usable'])
        self.assertEqual(rows[absent['name']]['registered_final_log'], 'missing_or_invalid')
        self.assertEqual(rows[missing_snapshot['name']]['snapshot'], 'registered_snapshot_required')
        self.assertFalse(rows[missing_snapshot['name']]['usable'])

    def test_zero_candidates_reports_exact_prepare_command(self):
        import contextlib
        import io
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(['--verified-commit', '0'*40, '--config', str(self.root / 'config.json')])
        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 6)
        self.assertEqual(result['details']['candidate_count'], 0)
        self.assertIn('prepare-inputs --config ', result['details']['next_command'])
        self.assertTrue(result['details']['next_command'].endswith('--build 19270912'))

    def test_watch_only_reports_missing_log_and_snapshot_per_package(self):
        _, target = self.input_run(False)
        old = json.loads((self.root / 'real-logs.json').read_text())
        build_ref = dict(old['observation']['build_ref'], run_id='19270913')
        observation = dict(old['observation'], build_ref=build_ref)
        other_key = digest(json_bytes(build_ref))
        self.register('observation_recorded', 'watch.observe', {'build': other_key,
                      'artifact': atomic_write(self.root, 'watch-only.json', json_bytes(observation))})
        with self.assertRaisesRegex(FlowError, 'analysis_verifier_final_logs_required') as caught:
            verify(self.config, '19270913', target)
        package = caught.exception.details['packages'][0]
        self.assertEqual(package['registered_final_log'], 'missing_or_invalid')
        self.assertEqual(package['snapshot'], 'registered_snapshot_required')

    def test_multiple_candidates_are_reported_without_auto_selection(self):
        build, target = self.input_run(True)
        old = json.loads((self.root / 'real-logs.json').read_text())
        different = dict(old['observation']['build_ref'], instance_id='https://other.example.invalid')
        second_key = digest(json_bytes(different))
        observation = dict(old['observation'], build_ref=different)
        self.register('observation_recorded', 'watch.observe', {'build': second_key,
                      'artifact': atomic_write(self.root, 'other-observation.json', json_bytes(observation))})
        with self.assertRaisesRegex(FlowError, 'analysis_verifier_unique_build_required') as caught:
            verify(self.config, '19270912', target)
        self.assertEqual(caught.exception.details['candidate_count'], 2)
        self.assertCountEqual(caught.exception.details['build_keys'], [build, second_key])
        selected = target / 'selected'
        selected.mkdir()
        self.assertEqual(verify(self.config, '19270912', selected, selected=build)['verdict'], 'PASS')

    def test_missing_registered_source_is_reported_per_package(self):
        build, target = self.input_run(False)
        missing = {'path': str(self.root / 'deleted-source.txt'), 'sha256': 'unavailable', 'size': 5}
        snapshot = dict(self.snapshot, files=[{'depotFile': '//depot/fixture.c', 'content': missing}])
        self.register('snapshot_completed', 'analyze.snapshot', {'build': build, 'package': KEY,
                      'artifact': atomic_write(self.root, 'missing-source-snapshot.json', json_bytes(snapshot))})
        with self.assertRaisesRegex(FlowError, 'analysis_verifier_snapshot_inputs_required') as caught:
            verify(self.config, '19270912', target)
        package = caught.exception.details['packages'][0]
        self.assertEqual(package['registered_final_log'], 'available')
        self.assertEqual(package['snapshot'], 'available')
        self.assertEqual(package['sources'], [{'file': '//depot/fixture.c', 'status': 'registered_input_missing'}])

    def test_wrapper_refuses_wrong_head_before_loading_config(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/verify_b3a2_real.sh'),
                                 '0'*40, '--config', '/does-not-exist'], capture_output=True)
        self.assertEqual(result.returncode, 6)
        self.assertIn(b'expected_commit_mismatch', result.stdout)
