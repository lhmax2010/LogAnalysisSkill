import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from helpers import bundle
from vd_cosmos_core.backends import BuildRef
from vd_cosmos_core.commands import Category, CommandContext
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, json_bytes
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.versions import build_key
from vd_fix_analyze.real_inputs import prepare_real_inputs

BUILD = '19270912'
HUB = '37491096'
PACKAGE = {'name': 'sample', 'arch': 'armv7l', 'path': '//depot/sample'}
BASIS = {'kind': 'trusted_terminal', 'epoch': 'fixture'}


class ReportReader:
    def __init__(self, config, observation):
        self.config = config
        self.build_ref = BuildRef('cosmos-http', 'https://example.invalid', BUILD, 'cosmos')
        self.observation = observation
        self.downloads = 0

    def observe(self, _):
        return self.observation

    def expected_digest(self):
        return 'fixture'

    def require(self, name):
        assert name == 'fetch_log'

    def fetch_log(self, _, arch, package):
        self.downloads += 1
        filename = package['key']['name'] + '.log'
        artifact = atomic_write(self.config.data_root, filename, b'compiler failure\n')
        log = dict(artifact, key=package['key'], final=True,
                   binding={'report_sha256': 'fixture', 'max_log_bytes': self.config.raw['fetch']['max_log_bytes'],
                            'terminal_basis': BASIS, 'settled_basis': 'trusted_terminal'})
        atomic_write(self.config.data_root, filename + '.json', json_bytes(log))
        return log


class PrepareInputTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        config_path, _, _ = bundle(Path(scratch.name))
        self.config = load_config(config_path)
        self.observation = {
            'effective_execution_state': '已结束', 'effective_terminal_basis': BASIS,
            'observation_failed': False, 'exit_code': 0, 'report_state': '完整',
            'header_consistency': '一致', 'result_state': '失败', 'todos': [],
            'reports': {'armv7l': {'settled': True, 'settled_basis': 'trusted_terminal',
                                  'evidence': {'sha256': 'fixture'}, 'headers': {},
                                  'packages': [{'key': PACKAGE, 'category': 'build_error'}]}},
        }
        self.reader = ReportReader(self.config, self.observation)
        self.observation['build_ref'] = self.reader.build_ref.to_dict()
        self.detail = Mock()
        self.detail.detail.return_value = {'build_id': BUILD, 'hub_id': HUB,
                                           'identity': 'strong', 'conflict': False, 'ended': True}

    def prepare(self, hub=HUB, factory=None, sleep=None):
        return prepare_real_inputs(self.config, BUILD, hub, reader_factory=factory or (lambda: self.reader),
                                   detail_reader=lambda _: self.detail, sleep=sleep or Mock())

    def frozen_inputs(self, reader):
        root = reader.config.data_root
        value = {'source': 'variables_page', 'digests': {}, 'files': {}}
        atomic_write(root, f'rounds/{build_key(reader)}/inputs/build-lists/manifest.json', json_bytes(value))
        return value

    def test_settles_then_registers_normal_events_and_reuses_valid_data(self):
        initial = copy.deepcopy(self.observation)
        initial['report_state'] = '部分'
        initial['result_state'] = '未知'
        initial['reports']['armv7l']['settled'] = False
        first = ReportReader(self.config, initial)
        factory = Mock(side_effect=[first, self.reader])
        sleep = Mock()

        def snapshot(config, adapter, package, headers, log, folder, **kwargs):
            src = atomic_write(config.data_root, f'{folder}/source.txt', b'fixture source\n')
            return {'package': package['key'], 'mode': '可分析', 'notices': [],
                    'files': [{'sha256': src['sha256'], 'content': src, 'snapshot_provenance': '版本确定'}]}

        with patch('vd_cosmos_core.build_inputs.fetch_build_inputs', side_effect=self.frozen_inputs) as lists, \
             patch('vd_fix_analyze.api.P4Adapter') as adapter, \
             patch('vd_fix_analyze.api.snapshot', side_effect=snapshot):
            result = self.prepare(factory=factory, sleep=sleep)
            self.assertFalse(result['logs_reused'])
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(result['packages'][0]['status'], 'registered')
            self.assertEqual(result['packages'][0]['log']['size'], 17)
            self.assertEqual(result['packages'][0]['sources'][0]['size'], 15)
            with EventStore(self.config.data_root) as store:
                events = store.events(build_key(self.reader))
                self.assertEqual([(e['command'], e['kind']) for e in events if e['kind'] != 'observation_started'], [
                    ('watch.observe', 'observation_recorded'), ('watch.observe', 'observation_recorded'),
                    ('fetch.logs', 'observation_recorded'), ('fetch.base-list', 'observation_recorded'),
                    ('analyze.snapshot', 'snapshot_started'), ('analyze.snapshot', 'snapshot_completed'),
                ])
                head = store.head()
            repeat = self.prepare()
            self.assertTrue(repeat['logs_reused'])
            self.assertTrue(repeat['packages'][0]['snapshot_reused'])
            self.assertEqual(repeat['packages'][0]['status'], 'reused')
            with EventStore(self.config.data_root) as store:
                self.assertEqual(store.head(), head)
            self.assertEqual(self.reader.downloads, 1)
            adapter.assert_called_once()
            lists.assert_called_once()
        sleep.assert_called_once_with(self.config.raw['poll']['interval_s'])
        self.detail.close.assert_called()

    def test_continues_after_snapshot_and_log_failure(self):
        extra = [dict(PACKAGE, name=name, path=f'//depot/{name}') for name in ('bad-log', 'good')]
        self.observation['reports']['armv7l']['packages'] += [
            {'key': package, 'category': 'build_error'} for package in extra]
        original = self.reader.fetch_log

        def fetch(ref, arch, package):
            if package['key']['name'] == 'bad-log':
                raise FlowError(5, 'fixture_log_unavailable')
            return original(ref, arch, package)

        def snapshot(config, adapter, package, headers, log, folder, **kwargs):
            if package['key'] == PACKAGE:
                raise FlowError(5, 'p4_listing_limit')
            return {'package': package['key'], 'mode': '仅诊断', 'notices': [], 'files': []}

        with patch.object(self.reader, 'fetch_log', side_effect=fetch), \
             patch('vd_cosmos_core.build_inputs.fetch_build_inputs', side_effect=self.frozen_inputs), \
             patch('vd_fix_analyze.api.P4Adapter'), patch('vd_fix_analyze.api.snapshot', side_effect=snapshot):
            result = self.prepare()
        self.assertEqual(result['exit_code'], 5)
        self.assertEqual([(row['package']['name'], row['status'], row.get('reason')) for row in result['packages']], [
            ('sample', 'snapshot_failed', 'p4_listing_limit'),
            ('bad-log', 'snapshot_failed', 'fixture_log_unavailable'),
            ('good', 'registered', None),
        ])
        with EventStore(self.config.data_root) as store:
            completed = store.events(build_key(self.reader), kinds=['snapshot_completed'])
            self.assertEqual([event['payload']['package'] for event in completed], [extra[1]])

    def test_refuses_success_nonterminal_or_hub_mismatch_before_fetch_or_p4(self):
        for updates, hub, reason in [
            ({'result_state': '成功'}, HUB, 'prepare_inputs_build_not_failed'),
            ({'effective_execution_state': '运行'}, HUB, 'prepare_inputs_terminal_not_verified'),
            ({}, '37491095', 'prepare_inputs_hub_mismatch'),
        ]:
            with self.subTest(reason=reason), patch.dict(self.observation, updates), \
                 patch('vd_fix_analyze.api.P4Adapter') as p4:
                with self.assertRaisesRegex(FlowError, reason):
                    self.prepare(hub=hub)
                self.assertEqual(self.reader.downloads, 0)
                p4.assert_not_called()

    def test_refuses_existing_tool_request_by_hub_before_fetch(self):
        context = CommandContext('submit.once', Category.EXTERNAL, True)
        with EventStore(self.config.data_root) as store:
            store.append(context, 'submit_request', {'hub_id': HUB}, store.head(), request_id='fixture')
        with self.assertRaisesRegex(FlowError, 'prepare_inputs_tool_managed_build'):
            self.prepare()
        self.assertEqual(self.reader.downloads, 0)

    def test_expired_ticket_uses_snapshot_todo_and_stops(self):
        error = FlowError(3, 'p4_not_logged_in', todo={'reason': 'p4_login_required'})
        with patch('vd_cosmos_core.build_inputs.fetch_build_inputs', side_effect=self.frozen_inputs), \
             patch('vd_fix_analyze.api.P4Adapter'), patch('vd_fix_analyze.api.snapshot', side_effect=error):
            with self.assertRaisesRegex(FlowError, 'p4_not_logged_in') as caught:
                self.prepare()
        self.assertEqual(caught.exception.details['todo']['reason'], 'p4_login_required')
        self.assertEqual(caught.exception.details['package'], PACKAGE)
        self.assertEqual(caught.exception.details['completed'], [])
