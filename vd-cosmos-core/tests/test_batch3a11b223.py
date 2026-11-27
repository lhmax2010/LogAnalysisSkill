"""Registration inputs are private verified rehearsal records; only reviewed keys are written."""
from copy import deepcopy
import io
import json
import stat
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

from helpers import REPO
from test_batch3a11b1 import B1Case
from vd_cosmos_core.config import load_config
from vd_cosmos_core.files import digest
from vd_cosmos_core.submit_browser_contract import SEED
from vd_cosmos_submit import cli, contract_registration


OBSERVED = (0, 4, 6, 1, 2, 3, 5, 7, 9, 10, 11, 12, 16, 17)
ENUMS = {0: ({'Partial': '0', 'Full': '1'}, 'Full'),
         4: ({'armv7l': '0'}, 'armv7l'),
         6: ({'': '', 'CODE': '0', 'ECODE': '1'}, ''),
         15: ({'yes': '0', 'no': '1'}, 'no')}


def part(name, value):
    raw = value.encode()
    return {'name': name, 'length': len(raw), 'sha256': digest(raw)}


class ContractRegistrationTests(B1Case):
    def result(self):
        controls = []
        parts = []
        for seed in SEED:
            index = seed['index']
            control = dict(seed, default=True, options=[])
            value = ''
            if index in ENUMS:
                mapping, label = ENUMS[index]
                control['options'] = [{'text': text, 'value': value} for text, value in mapping.items()]
                control['default'] = label
                value = mapping[label]
            if seed['kind'] == 'checkbox':
                control['checked_value'] = value = 'on'
            if index == 5:
                value = 'fixture-package-list\r\n'
            controls.append(control)
            parts.append(part(seed['name'], value))
        callbacks = []
        for index in OBSERVED:
            component = 'form-' + controls[index]['name'].replace(':', '-')
            callbacks.append({'method': 'POST', 'path': '/wicket/page', 'listener': 'IBehaviorListener',
                              'behavior': '0', 'component': component, 'control': component,
                              'classification': 'callback_candidate'})
        hidden = 'id16f_hf_0'
        return {'ok': True, 'exit_code': 0, 'rehearsed': True, 'clicked': False,
                'contract_source': {**contract_registration.binding(self.config),
                                    'backend': 'real', 'source_commit': 'a' * 40},
                'fingerprint': {'target': self.config.raw['submit']['target_config'], 'controls': controls},
                'evidence': {'verified': True, 'ks_encoding': 'ids', 'parts': parts + [part(hidden, '')],
                             'hidden_name': hidden},
                'account_check': {'matched': True}, 'gate_records': callbacks}

    def test_failed_legacy_non_rehearsal_or_wrong_target_account_refused(self):
        for section, key, value in (
            (None, 'ok', False), (None, 'exit_code', 5), (None, 'clicked', True),
            (None, 'rehearsed', False), ('evidence', 'verified', False),
            ('account_check', 'matched', False), ('contract_source', 'source_commit', '66fbc66'),
            ('contract_source', 'backend', 'fixture'), ('contract_source', 'target_config', 'other/config'),
            ('contract_source', 'account', 'other-account'), ('contract_source', 'target_instance', 'other.example.invalid'),
        ):
            with self.subTest(key=key, value=value):
                result = self.result()
                (result if section is None else result[section])[key] = value
                self.fails(4, contract_registration.proposal, self.config, result)
        legacy = self.result()
        del legacy['ok'], legacy['contract_source']
        self.fails(4, contract_registration.proposal, self.config, legacy)

    def test_registration_refuses_malformed_or_unattributed_callbacks_and_nonempty_hidden(self):
        for key, value in (('behavior', 'not-decimal'), ('component', 'unexpected'),
                           ('method', 'GET'), ('control', None)):
            result = self.result()
            result['gate_records'][0][key] = value
            error = self.fails(4, contract_registration.proposal, self.config, result)
            self.assertEqual(error.reason, 'unverified_rehearsal_callback')
        result = self.result()
        result['evidence']['parts'][-1] = part('id16f_hf_0', 'nonempty')
        self.fails(4, contract_registration.proposal, self.config, result)

    def test_terminal_review_and_exact_private_atomic_write_then_idempotent(self):
        result = self.result()
        result['private_return_value'] = 'fixture-package-list'
        result['gate_records'][0]['ignored'] = 'fixture-unrelated-request-body'
        path = self.root / 'rehearsal.json'
        path.write_text(json.dumps(result))
        original = self.path.read_bytes()
        self.path.chmod(0o640)

        def answer(prompt):
            self.assertNotIn('fixture-package-list', prompt)
            self.assertNotIn('fixture-unrelated-request-body', prompt)
            self.assertIn('Type confirm', prompt)
            review = json.loads(prompt.split('\n', 1)[1].rsplit('\n', 1)[0])
            self.assertEqual(review['source_commit'], 'a' * 40)
            self.assertEqual(review['encodings'][0]['option_values'], {'Partial': '0', 'Full': '1'})
            self.assertEqual(review['encodings'][13]['checked_value'], 'on')
            self.assertEqual(review['encodings'][8]['encoding'], 'ids')
            self.assertEqual(review['fingerprint']['controls'], 18)
            self.assertEqual(review['hidden_registered_value'], '')
            self.assertEqual(len(review['gate_patterns']), 14)
            return 'confirm'

        args = ['confirm-contract', '--config', str(self.path), '--from-result', str(path)]
        with patch.object(contract_registration.submit_terminal, 'available', return_value=True), \
             patch.object(contract_registration.submit_terminal, 'ancestors_allowed'), \
             patch.object(contract_registration.submit_terminal, 'ask', side_effect=answer), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(args), 0)
            self.assertEqual(cli.main(args), 0)
        first, second = map(json.loads, output.getvalue().splitlines())
        self.assertEqual(second, {'ok': True, 'exit_code': 0, 'changed': []})
        changed_keys = {'property_map', 'gate_patterns', 'form_fingerprint', 'hidden_registered_value',
                        'property_map_confirmed', 'gate_patterns_confirmed'}
        self.assertEqual(set(first['changed']), {'submit.' + key for key in changed_keys})
        raw = json.loads(original)
        new = json.loads(self.path.read_bytes())
        expected_properties = deepcopy(self.config.raw['submit']['property_map'])
        for index, seed in enumerate(SEED):
            entry = expected_properties[seed['label']]
            if index in ENUMS:
                entry['option_values'] = ENUMS[index][0]
            if index == 8:
                entry['encoding'] = 'ids'
        expected_callbacks = [{key: row[key] for key in ('method', 'path', 'listener', 'behavior', 'component')}
                              for row in result['gate_records']]
        raw['submit'].update(property_map=expected_properties, gate_patterns=expected_callbacks,
                             form_fingerprint={'controls': result['fingerprint']['controls'], 'confirmed': True},
                             hidden_registered_value='', property_map_confirmed=True, gate_patterns_confirmed=True)
        self.assertEqual(new, raw)
        self.assertTrue(load_config(self.path).raw['submit']['gate_patterns_confirmed'])
        backup, = self.root.glob('config.json.bak-*')
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o640)

    def test_confirmation_refusal_and_non_tty_leave_config_untouched(self):
        path = self.root / 'rehearsal.json'
        path.write_text(json.dumps(self.result()))
        original = self.path.read_bytes()
        with patch.object(contract_registration.submit_terminal, 'available', return_value=True), \
             patch.object(contract_registration.submit_terminal, 'ancestors_allowed'), \
             patch.object(contract_registration.submit_terminal, 'ask', return_value='yes'):
            self.fails(3, contract_registration.run, self.path, path)
        child = subprocess.run([sys.executable, str(REPO / 'vd-cosmos-submit/scripts/run.py'), 'confirm-contract',
                                '--config', str(self.path), '--from-result', str(path)], capture_output=True,
                               stdin=subprocess.DEVNULL, text=True, timeout=30)
        self.assertEqual(child.returncode, 2)
        self.assertEqual(json.loads(child.stdout)['error'], 'terminal_required')
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(list(self.root.glob('config.json.bak-*')))

    def test_successful_real_rehearsal_cli_writes_result_with_checkout_identity(self):
        result = self.result()
        del result['ok'], result['contract_source']
        with patch.object(cli.submit_once, 'run', return_value=result), \
             patch.object(cli.submit_terminal, 'human_context'), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(['once', '--rehearse', '--backend', 'real', '--config', str(self.path)]), 0)
        published = json.loads(output.getvalue())
        with open(published['artifact'], encoding='utf-8') as saved:
            record = json.load(saved)
        head = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        self.assertTrue(record['ok'])
        self.assertEqual(record['contract_source'],
                         dict(contract_registration.binding(self.config), backend='real', source_commit=head))
        contract_registration.proposal(self.config, record)
