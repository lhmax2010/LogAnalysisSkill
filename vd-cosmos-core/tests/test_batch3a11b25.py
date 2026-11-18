import json

from bm_helpers import BASE, detail, history, pages
from test_batch3a11b1 import B1Case, EXTERNAL, HUMAN, RESOLVE
from vd_cosmos_core import bm_pages, submit_claim, submit_model
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.submit_gate import Gate


class AccountGateTests(B1Case):
    def test_dashboard_callbacks_stay_blocked_without_poisoning_form_gate(self):
        self.config.raw['submit']['gate_patterns_confirmed'] = True
        gate = Gate(self.config, rehearse=True)
        dashboard = gate.origin + '/dashboard'
        overview = gate.origin + '/overview/' + self.config.raw['submit']['target_config_id']
        gate.navigation(dashboard, login_entry=True)
        self.assertTrue(gate.request(dashboard, 'GET'))
        self.assertTrue(gate.response(dashboard, 200))
        self.assertEqual(gate.phase, 'account')
        self.fails(4, gate.navigation, overview)
        self.assertFalse(gate.request(overview, 'GET'))
        callback = gate.origin + '/wicket/page?1-2.IBehaviorListener.0-widget'
        self.assertFalse(gate.request(callback, 'GET'))
        self.assertIsNone(gate.fatal)
        gate.verify_account()
        gate.navigation(overview)
        self.assertTrue(gate.request(overview, 'GET'))
        self.assertTrue(gate.response(overview, 200))
        self.assertEqual(gate.phase, 'business')


class TargetEvidenceTests(B1Case):
    # diag34 values with internal path segments replaced consistently.
    cases = (
        ('19206687', '37376237', '35367', 'root/PRODUCT/SERIES/target-a/RELEASE'),
        ('19270912', '37491096', '35367', 'root/PRODUCT/SERIES/target-a/RELEASE'),
        ('19344434', '37619264', '26400', 'root/PRODUCT/SERIES/target-b/RELEASE'),
    )

    def fixture(self, case, *, omit=(), **changes):
        build, hub, config_id, path = case
        values = dict(PACKAGE_LIST=BASE, SHELVE_LIST='', HUB_CONFIG_ID=config_id, HUB_CONFIG_PATH=path,
                      FROM_HUB_ID=hub, HUB_DOMAIN='https://hub.example.invalid')
        values.update(changes)
        for name in omit:
            del values[name]
        data = pages(build, hub)
        data[f'/build/{build}/variables'] = detail(build, hub, variables=values)
        return data

    def configure(self, case):
        self.config.raw['submit'].update(target_config_id=case[2], target_config=case[3])

    def test_diag34_candidates_use_three_independent_target_variables(self):
        for case in self.cases:
            with self.subTest(build=case[0]):
                self.configure(case)
                scan = self.reader(self.fixture(case)).lookup(case[1])
                self.assertEqual(scan['result'], '唯一')
                evidence = scan['candidates'][0]['build_target']
                self.assertEqual(set(evidence), bm_pages.BUILD_TARGET_VARS)
                self.assertTrue(all(item['status'] == 'verified' for item in evidence.values()))
                self.assertTrue(all(len(item['sha256']) == 64 for item in evidence.values()))
        records = [json.loads(f.read_bytes()) for f in (self.config.data_root / 'inputs/variable-first-read').glob('*/*.json')]
        self.assertEqual(sum(r['name'] in bm_pages.BUILD_TARGET_VARS for r in records), 9)
        self.assertFalse(any(r['name'] == 'HUB_DOMAIN' for r in records))

    def test_lookup_rejects_each_wrong_value_without_binding(self):
        case = self.cases[1]
        self.configure(case)
        for i, field in enumerate(sorted(bm_pages.BUILD_TARGET_VARS)):
            alternate = (str(800 + i), *case[1:])
            with self.subTest(field=field):
                error = self.fails(4, self.reader(self.fixture(alternate, **{field: 'wrong'})).lookup, case[1])
                self.assertEqual((error.reason, error.details['variable']), ('build_target_mismatch', field))
        with EventStore(self.config.data_root) as store:
            self.assertFalse(store.events(kinds=['bind']))

    def test_absence_is_unverified_and_cannot_bypass_required_target(self):
        case = self.cases[1]
        self.configure(case)
        data = self.fixture(case, omit=('HUB_CONFIG_PATH', 'FROM_HUB_ID'))
        evidence = self.reader(data).lookup(case[1])['candidates'][0]['build_target']
        self.assertEqual(evidence['FROM_HUB_ID'], {'status': 'unverified'})
        self.assertEqual(evidence['HUB_CONFIG_PATH'], {'status': 'unverified'})
        r = self.accepted(click=False)
        error = self.fails(4, submit_claim.prepare_attest, self.config, r['request_id'], case[0], self.reader(data))
        self.assertEqual(error.reason, 'build_target_unverified')
        self.assertIsNone(submit_model.read(self.config, r['request_id'])['binding'])

    def test_claim_binds_with_unlisted_optional_from_hub_id_and_freezes_it(self):
        case = self.cases[1]
        self.configure(case)
        data = self.fixture(case, omit=('FROM_HUB_ID',))
        r = self.accepted(click=False)
        prepared = submit_claim.prepare_attest(self.config, r['request_id'], case[0], self.reader(data))
        bound = submit_claim.attest(self.config, r['request_id'], prepared, HUMAN, prepared['required_words'],
                                    'checked', self.reader(data))
        self.assertEqual(bound['binding']['build_target']['FROM_HUB_ID']['status'], 'unverified')
        changed = self.reader(self.fixture(case)).lookup(case[1])
        self.assertEqual(changed['exit_code'], 3)
        self.assertIn('variable_page_changed', changed['issues'])

    def test_both_resolve_modes_refuse_mismatch_and_leave_request_untouched(self):
        case = self.cases[1]
        self.configure(case)
        request = submit_model.create_request(self.config, EXTERNAL, self.form(), 'fixture')
        rid = request['request_id']
        data = self.fixture(case, HUB_CONFIG_ID='26400')
        for mode in ('build-id', 'manual-submit'):
            error = self.fails(4, submit_model.resolve, self.config, RESOLVE, request_id=rid,
                               hub_id=case[1], mode=mode, reason='checked', reader=self.reader(data))
            self.assertEqual(error.reason, 'build_target_mismatch')
            self.assertEqual(submit_model.read(self.config, rid)['version'], request['version'])

    def test_rerun_chain_checks_each_member_against_target_before_returning(self):
        first = self.cases[1]
        second = (self.cases[2][0], first[1], *self.cases[2][2:])
        self.configure(first)
        data = self.fixture(first)
        data.update({k: v for k, v in self.fixture(second).items() if k.startswith('/build/')})
        data['/history/4362'] = history([second[0], first[0]])
        error = self.fails(4, self.reader(data).lookup, first[1])
        self.assertEqual((error.reason, error.details['build_id']), ('build_target_mismatch', second[0]))

    def test_unrelated_same_account_build_is_not_a_target_candidate(self):
        first, second = self.cases[1:]
        self.configure(first)
        data = self.fixture(first)
        data.update({k: v for k, v in self.fixture(second, PACKAGE_LIST=BASE.replace('@100', '@101')).items()
                     if k.startswith('/build/')})
        data['/history/4362'] = history([second[0], first[0]])
        scan = submit_claim.collect(self.config, self.accepted(click=False), self.reader(data))
        self.assertEqual([c['build_id'] for c in scan['candidates']], [first[0]])
