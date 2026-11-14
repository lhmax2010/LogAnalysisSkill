"""diag27 regressions; all P4 processes use the offline fake executable."""
import copy
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stderr

from helpers import CORE, REPO, config_data
from bm_helpers import overview, history
from test_batch3a11b1 import B1Case
from vd_cosmos_core import bm_pages, verify_b3a11 as verify, verify_b3a11b1 as verify_b1
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.p4 import P4Adapter, validate_config
from vd_cosmos_core.submit_doctor import doctor


class Diag27Tests(B1Case):
    def fake(self, mode=None, **extra):
        self.config.data_root.mkdir(exist_ok=True)
        self.config.raw['p4']['executable']=str(CORE/'fixtures/p4/fake_p4.py')
        (self.config.data_root/'fake-p4.json').write_text(json.dumps(dict(mode=mode,**extra)))
        return P4Adapter(self.config)

    def logs(self):
        return [{'key':{'arch':'armv7l','name':'p'+str(i),'path':'//fixture/'+str(i)},'path':'log'+str(i)} for i in range(7)]

    def test_real_overview_three_tables_queue_eight_headers_only(self):
        page=overview([('900','500')],sample=True)
        tables=[n for n in bm_pages.document(page).nodes if n.tag=='table']
        self.assertEqual(len(tables),3)
        self.assertEqual([len(bm_pages.cells(bm_pages.own_rows(t)[0])) for t in tables],[3,8,6])
        self.assertEqual(tables[1].attrs['class'],'table table-sm datatable')
        result=bm_pages.listing(page,self.config,'overview')
        self.assertEqual([(r['build_id'],r['hub_id']) for r in result['rows']],[('900','500')])
        self.assertEqual(len(result['samples']),1)
        self.config.raw['cosmos']['bm_overview_headers']=['Id','Next Build Version','Schedule']+self.config.raw['cosmos']['bm_overview_headers']
        self.assertEqual(self.fails(5,bm_pages.listing,page,self.config,'overview').reason,'bm_table_unrecognized')

    def test_real_history_five_tables_nested_settings_do_not_become_rows(self):
        page=history(['902','901','900'])
        tables=[n for n in bm_pages.document(page).nodes if n.tag=='table']
        self.assertEqual(len(tables),5)
        self.assertEqual([len(bm_pages.own_rows(t)) for t in tables],[6,1,1,0,4])
        self.assertEqual(tables[0].attrs['class'],'table table-settings table-sm')
        result=bm_pages.listing(page,self.config,'history')
        self.assertEqual([r['build_id'] for r in result['rows']],['902','901','900'])
        self.assertEqual(result['total'],3)

    def test_p4_plain_stderr_connection_text_and_incomplete_protocol(self):
        for mode,reason in [('connect_failed','p4_connect_failed'),('text_error','p4_text_error'),('garbled','p4_incomplete_output'),('truncated','p4_incomplete_output'),('killed','p4_process_signal')]:
            error=self.fails(5,self.fake(mode).info)
            self.assertEqual(error.reason,reason)
            if mode in {'connect_failed','text_error'}:
                self.assertTrue(error.details['message'].startswith('Perforce client error:'))
                self.assertNotIn('\n',error.details['message'])
                self.assertEqual(error.details['todo']['assignee'],'FatTank')
        self.assertEqual(self.fake().info()['userName'],'fixture-user')

    def test_p4_stderr_credentials_blocked_before_message_or_todo(self):
        secret='Cookie: synthetic-not-to-log' # credential-test-sample
        for stderr in (secret,'Perforce client error:\nConnect to server failed\n'+secret):
            error=self.fails(4,self.fake('text_secret',stderr=stderr).info)
            self.assertEqual(error.reason,'p4_stderr_credential_blocked')
            self.assertNotIn(secret,json.dumps(error.as_dict()))
            self.assertEqual(error.details,{})

    def test_p4_missing_placeholder_validation_only_at_use_sites(self):
        for values in ({},{'port':'example.invalid:1666','user':'configure-user','expected_server_address':'<server>'}):
            raw=config_data(self.root/'data')
            for key in ('port','user','expected_server_address'):raw['p4'].pop(key)
            raw['p4'].update(values);self.path.write_text(json.dumps(raw))
            config=load_config(self.path)
            if not values:self.assertNotIn('port',config.raw['p4'])
            self.assertEqual(bm_pages.listing(overview(),config,'overview')['rows'],[])
            error=self.fails(2,P4Adapter,config)
            self.assertEqual(error.reason,'p4_config_incomplete')
            self.assertEqual(error.details['missing'],['port','user','expected_server_address'])
            with patch('vd_cosmos_core.p4.subprocess.run') as run:
                result=doctor(config,package_probe=lambda:{'verified':True,'count':0})
            run.assert_not_called();self.assertEqual(result['exit_code'],2)
            self.assertEqual(result['error'],'p4_config_incomplete')

    def test_p4_legacy_config_loads_read_side_and_doctor_gives_migration(self):
        raw=config_data(self.root/'data');raw['p4']={'config_file':'settings/p4.conf','env':{}}
        self.path.write_text(json.dumps(raw));config=load_config(self.path)
        error=self.fails(2,P4Adapter,config)
        self.assertEqual(error.reason,'p4_config_legacy_format')
        for key in ('port','user','expected_server_address','tickets_file','fix_config_file'):
            self.assertIn(key,error.details['message'])
        self.assertEqual(doctor(config,package_probe=lambda:{'verified':True,'count':0})['error'],'p4_config_legacy_format')
        self.assertEqual(bm_pages.listing(history(['900']),config,'history')['total'],1)

    def test_preflight_info_failure_once_before_any_package_or_fetch(self):
        self.fake('connect_failed')
        with patch.object(verify,'command') as command:
            error=self.fails(5,verify.snapshots,self.config,REPO,self.config.data_root,{},self.path,self.logs())
        self.assertEqual(error.reason,'p4_connect_failed');self.assertEqual(error.details['stage'],'p4_preflight')
        command.assert_not_called()
        calls=[json.loads(l)['args'][7:] for l in (self.config.data_root/'fake-p4-calls.jsonl').read_text().splitlines()]
        self.assertEqual(calls,[['info']])

    def test_preflight_info_then_login_failure_with_command(self):
        adapter=self.fake(ticket_seconds=0)
        with patch.object(verify,'P4Adapter',return_value=adapter),patch.object(verify,'command') as command:
            error=self.fails(3,verify.snapshots,self.config,REPO,self.config.data_root,{},self.path,self.logs())
        command.assert_not_called();self.assertIn(' login',error.details['todo']['command'])
        calls=[json.loads(l)['args'][7:] for l in (self.config.data_root/'fake-p4-calls.jsonl').read_text().splitlines()]
        self.assertEqual(calls,[['info'],['login','-s']])

    def test_a_preflight_failure_summary_has_single_reason_and_no_seven_errors(self):
        head='a'*40;args=SimpleNamespace(verified_commit=head,config=str(self.path),saved_dir='saved',rows='rows',links='links')
        with patch.object(verify.subprocess,'check_output',side_effect=[head+'\n',b'']),patch.object(verify,'contracts',return_value=[]),patch.object(verify,'offline_tests',return_value='offline'),patch.object(verify,'read_side',return_value={'B':{'logs':self.logs()}}),patch.object(verify,'snapshots',side_effect=FlowError(5,'p4_connect_failed',stage='p4_preflight',message='Perforce client error:')),redirect_stderr(io.StringIO()):
            result=verify.execute(args,REPO)
        self.assertEqual(result['error'],'p4_connect_failed');self.assertEqual(result['summary'],[])
        saved=json.loads(Path(result['result_file']['path']).read_text())
        self.assertEqual(saved['details']['stage'],'p4_preflight');self.assertEqual(saved['summary'],[])

    def test_b1_child_failure_keeps_doctor_or_lookup_hub_and_error_in_both_outputs(self):
        for fail_at in (0,1,2):
            head='a'*40;args=SimpleNamespace(verified_commit=head,config=str(self.path));calls=[]
            def child(config,repo,directory,env,skill,argv):
                self.assertEqual(config.raw['p4']['port'],self.config.raw['p4']['port'])
                calls.append(argv)
                if len(calls)-1==fail_at:raise FlowError(5,'acceptance_skill_failed',child_error='bm_table_unrecognized',child_details={'scope':'queue'})
                if argv[0]=='doctor':return {'exit_code':0}
                return {'result':'唯一','candidates':[{'build_id':'19270912'}],'coverage':True}
            with patch.object(verify_b1.subprocess,'check_output',side_effect=[head+'\n',b'']),patch.object(verify_b1,'contracts',return_value=[]),patch.object(verify_b1,'offline_tests',return_value='offline'),patch.object(verify_b1,'command',side_effect=child):
                result=verify_b1.execute(args,REPO)
            failure=result['failed_command'];self.assertEqual(failure['command'],'doctor' if fail_at==0 else 'lookup')
            if fail_at:self.assertEqual(failure['hub_id'],('37491096','37491058')[fail_at-1])
            self.assertEqual(failure['details']['child_error'],'bm_table_unrecognized')
            saved=json.loads(Path(result['result_file']['path']).read_text())
            self.assertEqual(saved['failed_command'],failure);self.assertEqual(result['exit_code'],5)

    def test_child_command_keeps_credential_checked_details(self):
        payload={'exit_code':2,'error':'p4_config_incomplete','details':{'missing':['port']}}
        run=subprocess.CompletedProcess([],2,json.dumps(payload).encode(),b'')
        with patch.object(verify,'process',return_value=run):
            error=self.fails(2,verify.command,self.config,REPO,self.root,{},'vd-cosmos-submit',['doctor'])
        self.assertEqual(error.details['child_error'],'p4_config_incomplete')
        self.assertEqual(error.details['child_details'],payload['details'])
