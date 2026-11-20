from pathlib import Path
import subprocess
import unittest

from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, digest, json_bytes
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.verify_b3a2 import verify
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
        with self.assertRaisesRegex(FlowError, 'registered_snapshot_required'):
            verify(self.config, '19270912', target)

    def test_wrapper_refuses_wrong_head_before_loading_config(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/verify_b3a2_real.sh'),
                                 '0'*40, '--config', '/does-not-exist'], capture_output=True)
        self.assertEqual(result.returncode, 6)
        self.assertIn(b'expected_commit_mismatch', result.stdout)
