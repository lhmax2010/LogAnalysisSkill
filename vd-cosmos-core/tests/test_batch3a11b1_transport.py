"""Real loopback TLS transport and process checks for the B1 no-login contract."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import copy
import json
import multiprocessing
import os
from pathlib import Path
import signal
import ssl
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from helpers import REPO
from bm_helpers import BASE, DATE, detail, history, overview, pages
from test_batch3a11b1 import B1Case, HUMAN, EXTERNAL, RESOLVE, OBSERVE
from vd_cosmos_core import submit_claim, submit_model, submit_watch, verify_b3a11b1
from vd_cosmos_core.bm_reader import Reader
from vd_cosmos_core.bm_transport import AnonymousTransport
from vd_cosmos_core.commands import Category, CommandContext
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.state import EventStore


def lock_child(root, kind, request, pipe):
    with OperationLock(Path(root),kind,request):
        pipe.send('locked');pipe.recv()


class AnonymousTransportTests(B1Case):
    def start_server(self):
        cert=self.root/'cert.pem';key=self.root/'key.pem'
        result=subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=127.0.0.1',
            '-addext','subjectAltName=IP:127.0.0.1','-keyout',str(key),'-out',str(cert)],capture_output=True)
        self.assertEqual(result.returncode,0)
        owner=self;self.requests=[];self.mode='normal'
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):
                owner.requests.append((self.path,self.headers.get('Cookie')))  # credential-test-sample
                if owner.mode=='failure':
                    body=b'PRIVATE_RESPONSE_MARKER';status=500;headers={}
                elif owner.mode=='redirect':
                    body=b'';status=302;headers={'Location':'https://other.invalid/history/4362'}
                elif self.path=='/history/4362?0-1.ILinkListener-builds-topToolbars-toolbars-1-span-navigator-next':
                    if self.headers.get('Cookie')!='anon=fixture':  # credential-test-sample
                        body=history(['900','899'],total=4,next_url='/history/4362?next')
                        status=200;headers={}
                    else:
                        owner.page2=True;status=302;headers={'Location':'/history/4362'};body=b''
                elif self.path=='/history/4362':
                    if getattr(owner,'page2',False) and self.headers.get('Cookie'):  # credential-test-sample
                        body=history(['898','897'],first=3,total=4);status=200;headers={}
                    else:
                        owner.page2=False
                        body=history(['900','899'],total=4,next_url='/history/4362?0-1.ILinkListener-builds-topToolbars-toolbars-1-span-navigator-next')
                        status=200;headers={'Set-Cookie':'anon=fixture; Path=/; Secure'}  # credential-test-sample
                elif self.path=='/overview/4362':
                    body=overview();status=200;headers={}
                elif self.path.endswith('/variables'):
                    b=self.path.split('/')[2];body=detail(b,str(int(b)-400),variables={'PACKAGE_LIST':BASE,'BART_PASSWD':'PRIVATE_PASSWORD_MARKER'})
                    status=200;headers={}
                else:
                    b=self.path.split('/')[-1];body=detail(b,str(int(b)-400));status=200;headers={}
                self.send_response(status)
                for k,v in headers.items():self.send_header(k,v)
                self.send_header('Content-Length',str(len(body)));self.end_headers()
                try:self.wfile.write(body)
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
        server.socket=context.wrap_socket(server.socket,server_side=True)
        thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
        self.addCleanup(lambda:(server.shutdown(),server.server_close(),thread.join(2)))
        self.config.raw['cosmos']['bm_host']='127.0.0.1:'+str(server.server_port)
        self.config.raw.setdefault('network',{})['ca_file']=str(cert)
        return 'https://'+self.config.raw['cosmos']['bm_host']
    def test_anonymous_in_memory_session_redirects_and_no_body_artifacts(self):
        url=self.start_server();transport=AnonymousTransport(self.config);reader=Reader(self.config,transport=transport,sleep=lambda _:None)
        result=reader.lookup('500');reader.close()
        self.assertEqual(result['result'],'唯一')
        self.assertTrue(any('?0-1.' in p and value=='anon=fixture' for p,value in self.requests))
        self.assertEqual(list(transport.jar),[])
        self.assertFalse(self.config.data_root.exists())
        self.assertNotIn('PRIVATE_PASSWORD_MARKER',json.dumps(result))
        self.mode='redirect';transport=AnonymousTransport(self.config)
        self.fails(5,transport.read,url+'/history/4362',history=True)
        self.fails(4,transport.read,'https://other.invalid/history/4362',history=True)
        self.mode='failure';e=self.fails(5,transport.read,url+'/build/900')
        self.assertNotIn('PRIVATE_RESPONSE_MARKER',json.dumps(e.as_dict()))
        self.assertFalse(self.config.data_root.exists())
    def test_page_shapes_from_evidence_and_error_no_snippet(self):
        self.start_server();reader=Reader(self.config,sleep=lambda _:None)
        reader.overview();self.assertTrue(reader.samples[-1]['valid'])
        self.mode='failure';e=self.fails(5,reader.overview)
        self.assertEqual(e.reason,'bm_http_status');reader.close()


class LifecycleConcurrencyTests(B1Case):
    def test_two_process_observation_lock_and_manual_request_lock(self):
        r=self.accepted();rid=r['request_id'];parent,child=multiprocessing.Pipe()
        proc=multiprocessing.Process(target=lock_child,args=(str(self.config.data_root),'observation',rid,child));proc.start()
        try:
            self.assertTrue(parent.poll(5));self.assertEqual(parent.recv(),'locked')
            self.fails(6,submit_watch.run,self.config,rid,lambda cache:self.reader(),max_scans=1)
            submit_model.mutate(self.config,rid,r['version'],HUMAN,{'resolution_reason':'manual succeeds'})
        finally:
            parent.send('release');proc.join(5)
            if proc.is_alive():proc.terminate();proc.join(5)
        self.assertEqual(proc.exitcode,0)
    def test_target_session_unique_and_explicit_uncertainty(self):
        with EventStore(self.config.data_root) as store:
            h=store.append(EXTERNAL,'submit_session_started',{'target':submit_model.target(self.config)},0,request_id='r1',operation_id='s1')
            self.fails(6,store.append,EXTERNAL,'submit_session_started',{'target':submit_model.target(self.config)},h,request_id='r2',operation_id='s2')
            store.append(EXTERNAL,'hub_page_exposed',{'target':submit_model.target(self.config)},h,request_id='r1',operation_id='s1')
        self.fails(6,submit_model.create_request,self.config,EXTERNAL,self.form(),'different request')
    def test_candidate_membership_change_requires_new_confirmation(self):
        r=self.accepted();rid=r['request_id'];prepared=submit_claim.prepare_attest(self.config,rid,'900',self.reader())
        current=submit_model.read(self.config,rid);scan=copy.deepcopy(current['scan']);scan['candidates'].append(dict(scan['candidates'][0],build_id='901'))
        submit_model.mutate(self.config,rid,current['version'],OBSERVE,{'scan':scan},kind='submit_observation')
        self.fails(3,submit_claim.attest,self.config,rid,prepared,HUMAN,prepared['required_words'],'old input',self.reader())
    def test_concurrent_attest_only_one_binding(self):
        r=self.accepted();rid=r['request_id'];p=submit_claim.prepare_attest(self.config,rid,'900',self.reader())
        barrier=threading.Barrier(2);answers=[]
        def work():
            reader=self.reader();old=reader.variables
            def synchronized(*args):
                result=old(*args);barrier.wait(timeout=5);return result
            reader.variables=synchronized
            try:answers.append(submit_claim.attest(self.config,rid,p,HUMAN,p['required_words'],'checked',reader))
            except FlowError as error:answers.append(error.reason)
        ts=[threading.Thread(target=work) for _ in range(2)]
        for t in ts:t.start()
        for t in ts:t.join(5);self.assertFalse(t.is_alive())
        with EventStore(self.config.data_root) as store:self.assertEqual(len(store.events(kinds=['bind'])),1)
    def test_heartbeat_continues_while_scan_or_terminal_callback_waits(self):
        r=self.accepted();rid=r['request_id'];entered=threading.Event();release=threading.Event();done=[]
        data=pages();old=data['/history/4362']
        def blocked():entered.set();release.wait(3);return old
        data['/history/4362']=blocked
        thread=threading.Thread(target=lambda:done.append(submit_watch.run(self.config,rid,lambda cache:self.reader(data),max_scans=1)))
        thread.start();self.assertTrue(entered.wait(2))
        # Wait for actual heartbeats, not an assumed scheduling interval.
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            with EventStore(self.config.data_root) as store:beats=store.events(kinds=['submit_heartbeat'])
            if len(beats)>=4:break
            time.sleep(.01)
        self.assertGreaterEqual(len(beats),4)
        current=submit_model.read(self.config,rid);submit_model.mutate(self.config,rid,current['version'],HUMAN,{'resolution_reason':'during scan'})
        release.set();thread.join(4);self.assertFalse(thread.is_alive())
        self.assertTrue(done[0]['scan_discarded'])
        self.assertFalse(any(e['payload']['interrupted'] for e in beats[1:]))
    def test_failed_build_later_new_hub_other_account_rerun_and_rebind(self):
        r=self.accepted(click=False);rid=r['request_id'];p=submit_claim.prepare_attest(self.config,rid,'900',self.reader())
        submit_claim.attest(self.config,rid,p,HUMAN,p['required_words'],'checked',self.reader())
        data=pages();data['/history/4362']=history(['902','901','900'],versions={'902':'[other-user] build'})
        data['/build/901']=detail('901','501');data['/build/901/variables']=detail('901','501',variables={'PACKAGE_LIST':BASE})
        data['/build/902']=detail('902','500');data['/build/902/variables']=detail('902','500',variables={'PACKAGE_LIST':BASE})
        result=submit_watch.step(self.config,rid,self.reader(data),now=self.start+6000)
        self.assertIn('疑似同内容的另一轮',result['todos']);self.assertIn('发现重跑',result['todos'])
        self.assertEqual(result['binding']['build_id'],'900')
        result=submit_claim.rebind(self.config,rid,'902',CommandContext('rebind',Category.HUMAN,True),'manual choice',self.reader(data))
        self.assertEqual(result['binding']['build_id'],'902');self.assertEqual(result['binding_history'][0]['build_id'],'900')
    def test_pre_click_snapshot_failure_and_abandon_not_duplicate_bypass(self):
        result=submit_claim.pre_click_evidence(self.reader({'/overview/4362':overview([('900','500'),('901','550')])}))
        self.assertEqual(result['H_pre'],550)
        result=submit_claim.pre_click_evidence(self.reader({'/overview/4362':FlowError(5,'timeout')}))
        self.assertIsNone(result['H_pre'])
        r=self.accepted();submit_claim.abandon(self.config,r['request_id'],CommandContext('round.abandon',Category.HUMAN,True),'stop watching')
        self.fails(6,submit_model.create_request,self.config,EXTERNAL,self.form(),'duplicate')
    def test_watch_cli_readonly_fixture_and_no_click_events(self):
        r=self.accepted();fixture=self.root/'fixture';fixture.mkdir();mapping={}
        for i,(path,body) in enumerate(pages().items()):
            name=str(i)+'.html';(fixture/name).write_bytes(body)
            mapping['https://bm.example.invalid'+path]={'file':name,'clock':{'valid':True,'offset_s':0,'error_s':0,'received_at':self.start,'sent_at':self.start,'server_time':self.start,'rtt_s':0}}
        manifest=fixture/'manifest.json';manifest.write_text(json.dumps({'pages':mapping}))
        run=subprocess.run([sys.executable,str(REPO/'vd-cosmos-submit/scripts/run.py'),'watch','--config',str(self.path),'--request',r['request_id'],'--fixture',str(manifest),'--max-scans','1','--read-only'],capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr);result=json.loads(run.stdout)
        self.assertIsNone(result['binding'])
        with EventStore(self.config.data_root) as store:self.assertEqual(store.events(kinds=['click_intent','bind']),[])


class B1AcceptanceTests(B1Case):
    def test_wrong_head_stops_before_config_and_shell_reports_version(self):
        run=subprocess.run(['bash',str(REPO/'vd-cosmos-core/scripts/verify_b3a11b1_real.sh'),'0'*40,'--config','/nonexistent'],capture_output=True,text=True)
        self.assertEqual(run.returncode,6);self.assertIn('Python',run.stderr);self.assertEqual(json.loads(run.stdout)['error'],'expected_commit_mismatch')
    def test_acceptance_isolated_roots_order_and_lookup_pairs(self):
        head='a'*40;args=SimpleNamespace(verified_commit=head,config=str(self.path));calls=[]
        original=self.path.read_bytes()
        def command(config,repo,directory,env,skill,argv):
            calls.append(argv)
            if argv[0]=='doctor':return {'exit_code':0,'timezone_check':'通过'}
            hub=argv[argv.index('--hub-id')+1]
            return {'result':'唯一','candidates':[{'build_id':'19270912' if hub=='37491096' else '19270877'}],'coverage':False}
        with patch.object(verify_b3a11b1.subprocess,'check_output',side_effect=[head+'\n',b'']), \
             patch.object(verify_b3a11b1,'contracts',return_value=[]), \
             patch.object(verify_b3a11b1,'offline_tests',return_value='fixture offline output'), \
             patch.object(verify_b3a11b1,'command',side_effect=command):
            result=verify_b3a11b1.execute(args,REPO)
        self.assertEqual(result['verdict'],'PASS');self.assertEqual([x[0] for x in calls],['doctor','lookup','lookup'])
        output=Path(result['result_file']['path']);self.assertTrue(output.is_relative_to(self.config.data_root));self.assertEqual(self.path.read_bytes(),original)
        self.assertNotIn('resolve',json.dumps(calls));self.assertNotIn('once',json.dumps(calls))
    def test_offline_failure_prevents_online_and_php_unknown_not_pass(self):
        head='b'*40;args=SimpleNamespace(verified_commit=head,config=str(self.path))
        with patch.object(verify_b3a11b1.subprocess,'check_output',side_effect=[head+'\n',b'']), \
             patch.object(verify_b3a11b1,'contracts',return_value=[]), \
             patch.object(verify_b3a11b1,'offline_tests',side_effect=FlowError(6,'offline_suite_failed')), \
             patch.object(verify_b3a11b1,'command') as command:
            result=verify_b3a11b1.execute(args,REPO)
        self.assertEqual(result['exit_code'],6);command.assert_not_called()

if __name__=='__main__':unittest.main()
