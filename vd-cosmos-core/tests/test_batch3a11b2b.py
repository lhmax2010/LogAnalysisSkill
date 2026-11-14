"""Scripted protocol and pure gate checks. Browser request counts live in B2c."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from test_batch3a11b2a import CTX,REC,Processes
from test_batch3a11b1 import B1Case
from helpers import REPO
from vd_cosmos_core import submit_once as once, submit_sessions as sessions, submit_flow as flow, submit_model as model
from vd_cosmos_core.submit_browser_contract import SEED,structure,readback,multipart,verify_parts,accepted_location
from vd_cosmos_core.submit_gate import Gate,pattern
from vd_cosmos_core.submit_config import PROPERTIES
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.errors import FlowError
from vd_cosmos_submit.browser_scripts import arguments
from vd_cosmos_submit.playwright_driver import settings,environment

class FakeDriver:
    def __init__(self,case,status='accepted'):
        self.case=case;self.status=status;self.closed=False;self.clicks=0;self.bad_last=False;self.reads=0
        self.snap={'target':case.config.raw['submit']['target_config'],'hidden':'id1_hf_0','controls':[]}
        for seed in SEED:
            c=dict(seed,name='editor:content:basicProperties:'+str(seed['index'])+':property:editor:editor:input',value=case.form()[seed['label']])
            self.snap['controls'].append(c)
    def open(self,expose,confirm):expose()
    def snapshot(self):
        self.reads+=1;s=copy.deepcopy(self.snap)
        if self.bad_last and self.reads>=3:s['controls'][0]['value']='changed'
        return s
    def fill(self,i,value):self.snap['controls'][i]['value']=value
    def serialize_check(self,*a,**kw):return {'verified':False,'reason':'fixture_encoding_pending'}
    def records(self):return []
    def release(self,*args):
        with EventStore(self.case.config.data_root) as store:self.case.assertEqual(len(store.events(kinds=['click_intent'])),1)
        self.clicks+=1
        if self.status=='crash':raise RuntimeError('fixture')
        return self.status
    def close(self):self.closed=True

class B2bTests(B1Case):
    def setup_flow(self):
        r=model.create_request(self.config,CTX,self.form(),'fixture');s=sessions.start(self.config,r,CTX,Processes());return r,s,FakeDriver(self)
    def test_rehearsal_never_clicks_and_closes_profile(self):
        r,s,d=self.setup_flow();result=flow.execute(self.config,r,s,CTX,d,lambda _:r['digest'][:12],self.reader,rehearse=True)
        self.assertTrue(result['rehearsed']);self.assertEqual(d.clicks,0);self.assertTrue(d.closed)
        with EventStore(self.config.data_root) as store:self.assertFalse(store.events(kinds=['click_intent']))
    def test_form_extra_control_wrong_target_and_sensitive_form_rejected(self):
        r,s,d=self.setup_flow()
        for snap in (dict(d.snap,target='other'),dict(d.snap,password_present=True),dict(d.snap,controls=d.snap['controls'][:-1])):self.fails(4 if snap.get('password_present') else 5,structure,self.config,snap)
        self.fails(4,arguments,'snapshot',target='x',selector='input')
    def test_confirmation_refusal_and_last_readback_change_never_click(self):
        r,s,d=self.setup_flow();self.fails(3,flow.execute,self.config,r,s,CTX,d,lambda _:'wrong',self.reader,rehearse=True);self.assertTrue(d.closed)
    def test_intent_rechecks_version_session_duplicate_and_foreign_exposure(self):
        r,s,d=self.setup_flow();sessions.expose(self.config,s,CTX)
        changed=model.mutate(self.config,r['request_id'],r['version'],CTX,{'reason':'change'},kind='submit_outcome')
        self.fails(6,flow.intent,self.config,r,s,CTX,None,{})
        flow.intent(self.config,changed,s,CTX,None,{})
        self.fails(6,flow.intent,self.config,model.read(self.config,r['request_id']),s,CTX,None,{})
    def test_result_crash_is_uncertain_no_second_click(self):
        r,s,d=self.setup_flow();d.status='crash';self.config.raw['submit']['property_map_confirmed']=True
        with patch('vd_cosmos_core.submit_flow.wire_values',return_value={}):
            with self.assertRaises(RuntimeError):flow.execute(self.config,r,s,CTX,d,lambda _:r['digest'][:12],self.reader,rehearse=False)
        self.assertEqual(model.read(self.config,r['request_id'])['status'],'uncertain');self.assertTrue(d.closed);self.assertEqual(d.clicks,1)
        self.fails(6,model.create_request,self.config,CTX,self.form(),'again')
    def test_accepted_records_mapping_task_and_final_readback_blocks_change(self):
        r,s,d=self.setup_flow();self.config.raw['submit']['property_map_confirmed']=True;d.bad_last=True
        self.fails(5,flow.execute,self.config,r,s,CTX,d,lambda _:r['digest'][:12],self.reader,rehearse=False);self.assertEqual(d.clicks,0)
        s=sessions.start(self.config,r,CTX,Processes());d=FakeDriver(self)
        with patch('vd_cosmos_core.submit_flow.wire_values',return_value={}):result=flow.execute(self.config,r,s,CTX,d,lambda _:r['digest'][:12],self.reader,rehearse=False)
        self.assertEqual(result['status'],'accepted');self.assertTrue(model.read(self.config,r['request_id'])['mapping_pending'])
    def test_browser_settings_env_and_static_negatives(self):
        self.config.raw['submit']['browser_executable']='/bin/true'
        with patch.dict('os.environ',{'DEBUG':'fixture','PWDEBUG':'fixture','DISPLAY':':9'}):
            env=environment(self.config,self.root);self.assertNotIn('DEBUG',env);self.assertNotIn('PWDEBUG',env);self.assertEqual(env['DISPLAY'],':9')
        for key in ('trace','record_har_path','record_video_dir'):
            self.config.raw['submit'][key]='enabled';self.fails(4,settings,self.config,headless=True);del self.config.raw['submit'][key]
        spec=importlib.util.spec_from_file_location('boundary',REPO/'vd-cosmos-core/scripts/check_submit_boundary.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        for code in ('page.screenshot()','page.evaluate(source)','context.cookies()','context.new_cdp_session(page)','launch(record_har_path="file")'):
            with self.assertRaises(ValueError):mod.validate(code)
    def test_manual_action_resolution_preserves_history(self):
        r,s,d=self.setup_flow()
        with EventStore(self.config.data_root) as store:store.append(CTX,'manual_action_pending',{'target':model.target(self.config)},store.head(),operation_id=s['operation_id'])
        model.resolve(self.config,REC,session=s['operation_id'],mode='no-manual-action',reason='checked history',checked_at='2026-11-14')
        with EventStore(self.config.data_root) as store:self.assertEqual(len(store.events(kinds=['manual_action_pending'])),1)

class GateTests(B1Case):
    def gate(self,rehearse=True):
        g=Gate(self.config,rehearse=rehearse);g.phase='business';return g
    def test_default_blocks_human_navigation_popups_iframe_ws(self):
        g=self.gate();origin=g.origin
        for kw in ({},{'main_frame':False},{'resource':'WebSocket'},{'resource':'ServiceWorker'}):self.assertFalse(g.request(origin+'/overview/1','GET',**kw))
        self.assertFalse(g.request('https://foreign.example.invalid/path','GET'))
    def test_auth_callback_only_host_path_no_body_or_secret_records(self):
        g=Gate(self.config,rehearse=True);self.config.raw['submit']['auth_paths']=[{'host':'auth.example.invalid','path':'/callback','method':'POST'}]
        self.assertTrue(g.request('https://auth.example.invalid/callback?opaque=value','POST',body=b'NEVER_READ'))
        self.assertEqual(g.records,[]);g.phase='business';self.assertFalse(g.request('https://auth.example.invalid/callback','POST'))
    def test_recording_blocks_even_exact_callbacks_and_submit_fatal(self):
        g=self.gate();url=g.origin+'/wicket/page?1-2.IBehaviorListener.0-form-editor-content-basicProperties-1-property-editor-editor-input'
        self.assertFalse(g.request(url,'POST',ajax=True));self.assertEqual(g.records[-1]['classification'],'callback_candidate')
        self.assertFalse(g.request(g.origin+'/wicket/page?1-3.IFormSubmitListener-form','POST'));self.assertEqual(g.fatal,'submission_during_recording')
    def test_callback_scope_values_duplicates_and_two_request_budget(self):
        g=self.gate();g.recording=False;url=g.origin+'/wicket/page?1-2.IBehaviorListener.0-form-field';p=pattern(url,'POST');g.s['gate_patterns']=[p];g.filling=('form-field','field','x')
        for _ in range(2):self.assertTrue(g.request(url,'POST',body=b'field=x',content_type='application/x-www-form-urlencoded',ajax=True))
        self.assertFalse(g.request(url,'POST',body=b'field=x',content_type='application/x-www-form-urlencoded',ajax=True))
        g.callback_count=0;self.assertFalse(g.request(url,'POST',body=b'field=x&field=x',content_type='application/x-www-form-urlencoded',ajax=True))
    def test_one_intent_token_and_multipart_content_check(self):
        g=self.gate(False);g.recording=False;body=b'--B\r\nContent-Disposition: form-data; name="field"\r\n\r\nx\r\n--B\r\nContent-Disposition: form-data; name="hf"\r\n\r\n\r\n--B--\r\n'
        url=g.origin+'/wicket/page?1-2.IFormSubmitListener-form';kw={'body':body,'content_type':'multipart/form-data; boundary=B'}
        self.assertFalse(g.request(url,'POST',**kw));g.arm({'field':'x'},'hf',intent_recorded=True);self.assertTrue(g.request(url,'POST',**kw));self.assertFalse(g.request(url,'POST',**kw))
        g=self.gate(False);g.recording=False;g.arm({'field':'changed'},'hf',intent_recorded=True);self.assertFalse(g.request(url,'POST',**kw));self.assertEqual(g.fatal,'blocked_before_send')
    def test_multipart_duplicate_file_parts_and_hidden_registration(self):
        body=b'--B\r\nContent-Disposition: form-data; name="x"; filename="f"\r\n\r\nx\r\n--B--\r\n';self.fails(4,multipart,body,'multipart/form-data; boundary=B')
        self.fails(4,verify_parts,self.config,{'x':'v','hf':'changed'},{'x':'v'},'hf')
        self.fails(4,verify_parts,self.config,{'x':'v','hf':'','other':'x'},{'x':'v'},'hf')
    def test_redirect_never_accepts_post_or_wrong_host_and_no_follow_success(self):
        g=self.gate(False);url=g.origin+'/wicket/page?1-2.IFormSubmitListener-form';target='/overview/'+g.s['target_config_id']
        self.assertTrue(accepted_location(self.config,url,target));self.assertFalse(accepted_location(self.config,url,target+'?x=1'));self.assertFalse(accepted_location(self.config,url,'https://foreign.example.invalid'+target))
        self.assertFalse(g.response(url,302,target));self.assertFalse(g.response(url,307,url))
