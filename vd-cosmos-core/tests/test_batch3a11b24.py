import json
from pathlib import Path
import stat
import subprocess
import sys

from helpers import REPO
from test_batch3a11b1 import B1Case
from test_batch3a11b2a import CTX, Processes
from test_batch3a11b2b import FakeDriver
from vd_cosmos_core import bm_pages, submit_claim, submit_flow, submit_model, submit_once, submit_sessions
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.submit_browser_contract import readback
from vd_cosmos_core.submit_config import NOT_LISTED, PROPERTIES, property_map_defaults


class PropertyPolicyTests(B1Case):
    def test_approved_map_defaults_and_sample_agree(self):
        expected = ('BUILD_TYPE', 'BASE_REPOS', 'BUILD_CONF', 'PRODUCT_REPOS', 'ARCH', 'PACKAGE_LIST',
                    'not_listed', 'SHELVE_LIST', 'KS_LIST', 'KS_PRODUCT_VERSION', 'KS_PACKAGE_ADD',
                    'DELETE_PACKAGE_LIST', 'not_listed', 'BUILD_CONTINUOUS', 'not_listed',
                    'DO_NOT_CREATE_IMAGE', 'not_listed', 'EXTRA_BUILD_PARAMETER')
        sample = json.loads((REPO / 'vd-cosmos-core/config.sample.json').read_text())['submit']
        props = property_map_defaults()
        self.assertEqual(tuple(e['variable'] for e in props.values()), expected)
        self.assertEqual(sample['property_map'], props)
        self.assertEqual(self.config.raw['submit']['property_map'], props)
        self.assertTrue(all(e['evidence'] for e in props.values()))
        self.assertFalse(sample['property_map_confirmed'])
        self.assertFalse(self.config.raw['submit']['property_map_confirmed'])
        self.assertNotIn('record_value', props['KS_LIST'])

    def assert_policy(self, field, rule, call, *args, **kw):
        with self.assertRaises(FlowError) as caught:
            call(*args, **kw)
        error = caught.exception
        self.assertEqual((error.code, error.reason), (4, 'first_release_submit_policy'))
        self.assertEqual((error.details['todo']['field'], error.details['todo']['rule']), (field, rule))

    def test_each_forbidden_field_refused_before_request_creation(self):
        from types import SimpleNamespace
        form = self.form()
        base = self.root / 'base'
        base.write_text(form['PACKAGE_LIST'])
        args = SimpleNamespace(base_list=str(base), base_from_hub=None, bm_build=None, reason='fixture',
                               shelve_list=None, rehearse=True, resubmit_of=None)
        for i in (6, 9, 10, 11, 12):
            field = PROPERTIES[i]
            with self.subTest(field=field):
                self.config.raw['submit']['form'] = dict(form, **{field: ' ' if i == 12 else 'invalid'})
                self.assert_policy(field, 'must_be_empty', submit_once.prepare, self.config, args, CTX,
                                   self.reader, lambda _: 'unused', processes=Processes())
        with EventStore(self.config.data_root) as store:
            self.assertFalse(store.events(kinds=['submit_request', 'click_intent']))

    def test_each_changed_default_is_refused_before_fill(self):
        for index, value in ((13, 'false'), (14, 'false'), (15, 'yes')):
            field = PROPERTIES[index]
            with self.subTest(field=field):
                request = submit_model.create_request(self.config, CTX, self.form(), 'fixture')
                session = submit_sessions.start(self.config, request, CTX, Processes())
                driver = FakeDriver(self)
                driver.snap['controls'][index]['value'] = value
                self.assert_policy(field, 'must_keep_default', submit_flow.execute, self.config, request,
                                   session, CTX, driver, lambda _: 'unused', self.reader, rehearse=True)
                self.assertEqual(driver.reads, 1)
                self.assertEqual(driver.clicks, 0)
                self.assertTrue(driver.closed)

    def test_readback_checks_all_restricted_controls_and_allows_either_preselected_option(self):
        for i in range(18):
            if i not in (6, 9, 10, 11, 12, 13, 14, 15):
                continue
            with self.subTest(control=i):
                driver = FakeDriver(self)
                driver.snap['controls'][i]['value'] = 'changed'
                self.assert_policy(PROPERTIES[i], 'must_keep_default' if i >= 13 else 'must_be_empty',
                                   readback, self.config, driver.snap, self.form())
        driver = FakeDriver(self)
        driver.snap['controls'][15]['value'] = 'yes'
        form = dict(self.form(), **{'Image Skip?': 'yes'})
        self.assertEqual(readback(self.config, driver.snap, form, defaults={name: form[name] for name in PROPERTIES[13:16]})['Image Skip?'], 'yes')

    def test_not_listed_never_compared_and_checked_encoding_is_variable_specific(self):
        form = self.form()
        values = {key: {'value': 'different'} for key in NOT_LISTED}
        values.update(BUILD_CONTINUOUS={'value': 'yes'}, DO_NOT_CREATE_IMAGE={'value': 'no'},
                      KS_LIST={'value': 'unknown recorder encoding'}, PACKAGE_LIST={'value': form['PACKAGE_LIST']})
        result = bm_pages.compare({'form': form}, values, self.config)
        self.assertTrue(result['matches'])
        for key in NOT_LISTED:
            self.assertNotIn(key, submit_claim.variable_names(self.config))
            self.assertEqual(result['fields'][key], '未核验')
        self.assertEqual(result['fields']['KS_LIST'], '未核验')
        self.assertEqual(result['fields'][PROPERTIES[13]], '一致')
        self.assertEqual(result['fields'][PROPERTIES[15]], '一致')
        values['BUILD_CONTINUOUS']['value'] = 'true'
        self.assertEqual(bm_pages.compare({'form': form}, values, self.config)['fields'][PROPERTIES[13]], '不一致')


class ApplyPropertyMapTests(B1Case):
    def apply(self, path):
        return subprocess.run([sys.executable, str(REPO / 'vd-cosmos-core/scripts/apply_property_map.py'),
                               '--config', str(path)], capture_output=True, text=True, timeout=60)

    def config_for_update(self, submit):
        path = self.root / 'migrate.json'
        raw = json.loads(self.path.read_text())
        if submit is None:
            raw.pop('submit', None)
        else:
            raw['submit'] = submit
        raw['unrelated'] = {'private_input': 'DO_NOT_PUBLISH_SAMPLE', 'property_map': {}}
        path.write_bytes((json.dumps(raw, indent=2) + '\n').replace('\n', '\r\n').encode())
        path.chmod(0o640)
        return path

    def test_only_property_map_changes_exact_backup_and_idempotence(self):
        path = self.config_for_update({'property_map': {'BUILD_TYPE': {'variable': None}},
                                       'property_map_confirmed': False, 'target_config': 'fixture-target'})
        original = path.read_bytes()
        result = self.apply(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        changed = json.loads(result.stdout)['submit.property_map']
        self.assertEqual(changed['changed'], ['BUILD_TYPE'])
        self.assertEqual(set(changed['added']), set(PROPERTIES) - {'BUILD_TYPE'})
        self.assertNotIn('DO_NOT_PUBLISH_SAMPLE', result.stdout + result.stderr)
        self.assertNotIn('fixture-target', result.stdout + result.stderr)
        new = path.read_bytes()
        start = original.index(b'{', original.index(b'"property_map"', original.index(b'"submit"')))
        end = original.index(b',\r\n    "property_map_confirmed"', start)
        self.assertTrue(new.startswith(original[:start]))
        self.assertTrue(new.endswith(original[end:]))
        self.assertEqual(load_config(path).raw['submit']['property_map'], property_map_defaults())
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        backup, = self.root.glob('migrate.json.bak-*')
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertEqual(json.loads(self.apply(path).stdout)['submit.property_map'], {'added': [], 'changed': []})
        self.assertEqual(path.read_bytes(), new)
        self.assertEqual(list(self.root.glob('migrate.json.bak-*')), [backup])

    def test_missing_submit_is_created_without_persisting_loader_defaults(self):
        path = self.config_for_update(None)
        self.assertEqual(self.apply(path).returncode, 0)
        self.assertEqual(json.loads(path.read_text())['submit'], {'property_map': property_map_defaults()})

    def test_confirmed_and_invalid_configs_are_not_touched(self):
        path = self.config_for_update({'property_map_confirmed': True})
        for raw, reason, code in ((path.read_bytes(), 'property_map_already_confirmed', 4),
                                  (b'{"invalid": "DO_NOT_PUBLISH_SAMPLE"}', 'invalid_config', 2)):
            path.write_bytes(raw)
            result = self.apply(path)
            self.assertEqual(result.returncode, code)
            self.assertEqual(json.loads(result.stdout)['error'], reason)
            self.assertNotIn('DO_NOT_PUBLISH_SAMPLE', result.stdout + result.stderr)
            self.assertEqual(path.read_bytes(), raw)
        self.assertFalse(list(self.root.glob('migrate.json.bak-*')))
