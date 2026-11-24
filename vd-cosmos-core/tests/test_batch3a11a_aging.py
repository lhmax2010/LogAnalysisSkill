from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from helpers import REPO, bundle
from vd_cosmos_core import verify_b2, verify_b3a11
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError


class LiveAgingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        cfg, _, _ = bundle(root)
        self.config = load_config(cfg)
        self.directory = self.config.data_root
        self.directory.mkdir(parents=True)
        self.args = SimpleNamespace(saved_dir=str(root / 'saved'), rows='rows', links='links', live_build_id=None)
        self.config_path = cfg

    def test_retirement_needs_terminal_identity_verified_index_and_no_other_error(self):
        report = {'http_status': 404, 'index': {'verified': True}, 'index_response': {'http_status': 200}}
        obs = {'execution_evidence': {'identity_match': True}, 'effective_execution_state': '已结束',
               'reports': {'armv7l': report, 'x86_64': {'http_status': 200}}}
        self.assertTrue(verify_b2.retired(obs))
        self.assertFalse(verify_b2.retired(dict(obs, effective_execution_state='未知')))
        self.assertFalse(verify_b2.retired(dict(obs, execution_evidence={'identity_match': False})))
        self.assertFalse(verify_b2.retired(dict(obs, reports={'armv7l': dict(report, index={})})))
        self.assertFalse(verify_b2.retired(dict(obs, reports={'armv7l': report, 'x86_64': {'http_status': 503}})))

    def test_newest_live_candidate_first_and_saved_baseline_is_independent(self):
        self.config.raw['cosmos']['acceptance_live_builds'] = ['19091860', '19300000', '19270912']
        def saved(args, config, directory, result):
            self.assertEqual(args.run_id, '19091860')
            result['verdict'] = 'PASS'

        def live(args, config, directory, result, *rest, **kwargs):
            self.assertTrue(kwargs['independent_live'])
            result.update(exit_code=0, verdict='RETIRED' if args.build_id == '19300000' else 'PASS')

        with patch.object(verify_b2, 'check_source'), patch.object(verify_b2, 'verify_saved', side_effect=saved) as baseline, \
             patch.object(verify_b2, 'run', side_effect=live):
            result = verify_b3a11.read_side(self.args, self.config, self.directory, REPO, self.config_path)
        baseline.assert_called_once()
        self.assertEqual(result['live_attempts'], [{'build_id': '19300000', 'verdict': 'RETIRED'},
                                                   {'build_id': '19270912', 'verdict': 'PASS'}])
        self.assertEqual(result['live_build_id'], '19270912')
        self.assertEqual(result['C']['verdict'], 'PASS')

    def test_explicit_retired_build_reports_retired_and_saved_failure_still_fails(self):
        self.args.live_build_id = '19091860'
        def retired(args, config, directory, result, *rest, **kwargs):
            result.update(verdict='RETIRED', exit_code=0)
        def saved(args, config, directory, result):
            result['verdict'] = 'FAIL'
        with patch.object(verify_b2, 'check_source'), patch.object(verify_b2, 'verify_saved', side_effect=saved), \
             patch.object(verify_b2, 'run', side_effect=retired) as probe:
            with self.assertRaisesRegex(FlowError, 'read_side_acceptance_failed') as caught:
                verify_b3a11.read_side(self.args, self.config, self.directory, REPO, self.config_path)
        probe.assert_called_once()
        self.assertTrue(Path(caught.exception.details['read_side_result']['path']).is_file())
