from pathlib import Path
import unittest
from unittest.mock import patch

from vd_cosmos_core.analysis_result import accept_result
from vd_cosmos_core.analysis_workspace import inventory
from vd_cosmos_core.commands import command_context
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, json_bytes
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.versions import build_key
from vd_cosmos_workflow.api import tick

import test_batch3a1
from test_batch3a2_package import BUILD, PackageFixture
from test_batch3a2_result import result_fixture


class WorkspaceTests(PackageFixture, unittest.TestCase):
    def test_sealed_skill_and_modified_skill_permanently_invalidate_attempt(self):
        task = self.prepare()
        skill = Path(task['skill']['path'])
        original = skill.read_bytes()
        self.assertEqual(skill.stat().st_mode & 0o777, 0o444)
        self.assertEqual(skill.parent.stat().st_mode & 0o777, 0o555)
        result = result_fixture(task)
        path = self.root / task['directory'] / 'outputs/result.json'
        path.write_bytes(json_bytes(result))
        skill.chmod(0o644)
        skill.write_bytes(b'changed')
        skill.chmod(0o444)
        with self.assertRaisesRegex(FlowError, 'analysis_workspace_skill_changed'):
            accept_result(self.config, BUILD, task['task_id'], task['attempt'])
        skill.chmod(0o644)
        skill.write_bytes(original)
        skill.chmod(0o444)
        with self.assertRaisesRegex(FlowError, 'analysis_attempt_invalidated'):
            accept_result(self.config, BUILD, task['task_id'], task['attempt'])
        self.assertEqual(self.prepare()['attempt'], 2)

    def test_canary_inventory_does_not_open_existing_skill_files(self):
        skill = self.root / 'normal' / 'canary-abc'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('unique marker')
        with patch.object(Path, 'open', side_effect=AssertionError):
            result = inventory(skill.parent, skill.name)
        self.assertTrue(result['present'])
        self.assertIsNotNone(result['manifest_sha256'])

    def test_human_ancestor_guard_is_applied_before_prompt(self):
        from unittest.mock import mock_open
        handle = mock_open()
        handle.return_value.isatty.return_value = True
        with patch('builtins.open', handle), patch(
                'vd_cosmos_core.submit_terminal.ancestors_allowed',
                side_effect=FlowError(4, 'ai_process_ancestor_refused')):
            with self.assertRaisesRegex(FlowError, 'ai_process_ancestor_refused'):
                command_context('confirm-input')
        handle.return_value.write.assert_not_called()


class TickTests(unittest.TestCase):
    # Reuse the pre-existing real-format loopback fixtures, without inheriting tests.
    setUp = test_batch3a1.Reading3a1Tests.setUp
    reader = test_batch3a1.Reading3a1Tests.reader
    observe = test_batch3a1.Reading3a1Tests.observe
    detail = test_batch3a1.Reading3a1Tests.detail

    def test_tick_projects_tasks_and_accepted_results_and_updates_inbox(self):
        from datetime import timedelta
        from vd_cosmos_workflow.api import projection
        self.detail('failed')
        tick(self.config, self.reader)
        self.at += timedelta(seconds=10)
        tick(self.config, self.reader)
        tick(self.config, self.reader)
        self.assertEqual(tick(self.config, self.reader)['phase'], '结果已拉取')
        key = build_key(self.reader())
        with EventStore(self.config.data_root) as store:
            state = projection(self.config, store, key)
            for item in state['logs']['logs']:
                snapshot = {'package': item['key'], 'final_log_sha256': item['sha256'],
                            'files': [], 'mode': '仅诊断'}
                artifact = atomic_write(self.config.data_root,
                    'fixture-snapshot-'+item['sha256']+item['key']['arch']+'.json', json_bytes(snapshot))
                store.append(command_context('analyze.snapshot'), 'snapshot_completed',
                             {'build': key, 'package': item['key'], 'artifact': artifact}, store.head())
            number = len(state['logs']['logs'])
        for _ in range(number):
            out = tick(self.config, self.reader)
            self.assertEqual(out['action'], 'analyze')
            self.assertEqual(out['analysis_phase'], '任务包已生成')
        self.assertEqual(out['analysis_tasks']['pending'], number)
        with EventStore(self.config.data_root) as store:
            tasks = [e['payload'] for e in store.events(key, kinds=['analysis_prepared'])]
        for task in tasks:
            result = result_fixture(task)
            result['provenance']['analyst_type'] = 'manual'
            (self.config.output(task['directory']) / 'outputs/result.json').write_bytes(json_bytes(result))
            accept_result(self.config, key, task['task_id'], task['attempt'])
        out = tick(self.config, self.reader)
        self.assertEqual(out['analysis_phase'], '分析结果已接收')
        self.assertEqual(out['analysis_tasks']['pending'], 0)
        self.assertNotIn('个任务待分析', self.config.output('inbox.md').read_text())
