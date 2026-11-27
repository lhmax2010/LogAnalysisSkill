import json
from pathlib import Path
from unittest.mock import patch

from test_batch3a11b1 import B1Case
from vd_cosmos_core import submit_terminal as terminal
from vd_cosmos_core.files import digest, json_bytes


class ConfirmationPromptTests(B1Case):
    def test_four_prompts_are_bounded_and_save_full_unabridged_payloads(self):
        package_list = ''.join(f'//example/private-fixture-package-{i}/...@123\n' for i in range(5300))
        target = {'config': 'root/example/verified-target'}
        sha = 'a'*64
        history = [{'request': f'private-fixture-request-{i}', 'hub': str(i)} for i in range(4500)]
        cases = (
            ('source', dict(hub_id='37376237',build_id='19206687',config_id='4362',package_count=5300,
                            package_digest=sha,variables_sha256='b'*64,conditions_sha256='c'*64,
                            variables={'PACKAGE_LIST':package_list},
                            headers={'armv7l':{'start_time':'fixture-time','build_conf':'fixture.conf'},
                                     'x86_64':{'base':'very-long-header-'*1000}}),
             '19206687', '输入构建号 19206687 以确认 / type 19206687 to confirm',
             ('37376237','BM build 19206687','Packages: 5300','fixture.conf',digest(package_list.encode()))),
            ('run', dict(run_pattern={'method':'GET','path':'/overview/35367','listener':'ILinkListener',
                                      'behavior':None,'component':'run'}, omitted=package_list),
             'allow-run', 'type allow-run to confirm', ('GET /overview/35367 ILinkListener run',)),
            ('digest', dict(request='request-1',digest=sha,digest_prefix=sha[:12],rehearse=True,
                            values={'PACKAGE_LIST':package_list,'KS_LIST':'one.ks\ntwo.ks'},
                            fingerprint={},serialization={'ks_encoding': 'texts', 'callbacks_sent': 14}),
             sha[:12], f'type the 12-character digest prefix {sha[:12]} to confirm',
             ('request-1','mode: rehearsal','PACKAGE_LIST: 5300 nonblank lines',
              'KS_LIST encoding observed: texts', 'callbacks sent: 14', digest(package_list.encode()))),
            ('resubmit', dict(digest=sha,resubmit_of='request-2',next_round=4501,submissions=history),
             'resubmit', 'type resubmit to confirm', ('request-2','next round: 4501',digest(json_bytes(history)))),
        )
        for kind, data, answer, instruction, fragments in cases:
            with self.subTest(kind=kind):
                payload = dict(data, target=target, confirmation=kind)
                def ask(prompt):
                    self.assertLessEqual(len(prompt.encode()), terminal.CONFIRM_PROMPT_BYTES)
                    self.assertEqual(prompt.splitlines()[-2:], [instruction, '> '])
                    self.assertIn(target['config'], prompt)
                    for fragment in fragments:
                        self.assertIn(fragment, prompt)
                    self.assertNotIn('private-fixture-package-', prompt)
                    self.assertNotIn('private-fixture-request-', prompt)
                    self.assertNotIn('very-long-header-', prompt)
                    path, = [Path(line.removeprefix('Full JSON: ')) for line in prompt.splitlines()
                             if line.startswith('Full JSON: ')]
                    self.assertTrue(path.is_relative_to(self.config.data_root / 'submit/confirmations'))
                    self.assertEqual(json.loads(path.read_bytes()), payload)
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                    return answer
                with patch.object(terminal, 'ask', side_effect=ask) as mocked:
                    self.assertEqual(terminal.confirm_once(self.config,payload), answer)
                mocked.assert_called_once()

    def test_credential_check_blocks_unprintable_payload_before_artifact_or_prompt(self):
        self.config.raw['prepush']['credential_patterns'] = ['FIXTURE_BLOCKED_VALUE']
        payload = {'confirmation':'run','run_pattern':{},'hidden_value':'FIXTURE_BLOCKED_VALUE'}
        with patch.object(terminal, 'ask') as ask:
            self.assertEqual(self.fails(4,terminal.confirm_once,self.config,payload).reason,'output_credential_blocked')
        ask.assert_not_called()
        self.assertFalse((self.config.data_root / 'submit/confirmations').exists())
