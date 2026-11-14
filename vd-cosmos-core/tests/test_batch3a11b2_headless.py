"""Real Chrome + local server request counts. Missing runtime is NEVER a pass."""
import importlib.util
import os
from pathlib import Path
import shutil
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
from helpers import REPO
from test_batch3a11b1 import B1Case
from test_batch3a11b2a import CTX,Processes
from vd_cosmos_core import submit_model as model,submit_sessions as sessions
from vd_cosmos_core.submit_gate import pattern
from vd_cosmos_submit.playwright_driver import Driver

class Server(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(('127.0.0.1',0),Handler);self.calls=[];self.redirect=None
        self.thread=threading.Thread(target=self.serve_forever,daemon=True);self.thread.start()
    @property
    def origin(self):return 'http://127.0.0.1:'+str(self.server_port)
    def close(self):self.shutdown();self.server_close();self.thread.join()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        self.server.calls.append(('GET',self.path));self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers()
        self.wfile.write(b'<html><body><button id="human">human action</button><input type="password" autocomplete="current-password"></body></html>')
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get('Content-Length','0')));self.server.calls.append(('POST',self.path))
        if self.server.redirect:self.send_response(302);self.send_header('Location',self.server.redirect)
        else:self.send_response(200)
        self.end_headers();self.wfile.write(b'ok')

class HeadlessGateTests(B1Case):
    def setUp(self):
        super().setUp();exe=os.environ.get('VD_COSMOS_CHROME') or next((x for x in ('/opt/google/chrome/chrome','/usr/bin/google-chrome','/usr/bin/chromium') if Path(x).is_file()),None)
        reason='Playwright Python runtime unavailable' if importlib.util.find_spec('playwright') is None else 'existing Chrome/Chromium unavailable' if not exe else None
        if reason:
            if os.environ.get('VD_REQUIRE_HEADLESS')=='1':self.fail('required real-browser test: '+reason)
            self.skipTest(reason)
        self.server=Server();self.addCleanup(self.server.close);self.config.raw['submit']['browser_executable']=exe
        r=model.create_request(self.config,CTX,self.form(),'local browser verification');self.session=sessions.start(self.config,r,CTX,Processes())
        self.driver=Driver(self.config,self.session,headless=True,local_origin=self.server.origin);self.addCleanup(self.driver.close);self.driver.launch(rehearse=True)
        self.page=self.driver._page;url=self.server.origin+'/overview/'+self.config.raw['submit']['target_config_id'];self.driver.gate.navigation(url);self.page.goto(url);self.page.wait_for_timeout(100)
        self.assertEqual(self.driver.gate.phase,'business');self.server.calls.clear()
    def wait(self):self.page.wait_for_timeout(350)
    def test_human_get_post_navigation_popup_and_iframe_never_reach_server(self):
        self.page.evaluate("""base=>{fetch(base+'/write',{method:'POST'}).catch(()=>{});fetch(base+'/run').catch(()=>{});window.open(base+'/popup');let f=document.createElement('iframe');f.src=base+'/iframe';document.body.append(f);} """,self.server.origin)
        self.wait();self.assertEqual(self.server.calls,[])
    def test_recording_callback_and_submit_both_blocked_server_counts_zero(self):
        self.page.evaluate("""base=>{fetch(base+'/wicket/page?1-2.IBehaviorListener.0-form-field',{method:'POST',body:'field=x'}).catch(()=>{});fetch(base+'/wicket/page?1-3.IFormSubmitListener-form',{method:'POST',body:'field=x'}).catch(()=>{});} """,self.server.origin)
        self.wait();self.assertEqual(self.server.calls,[]);self.assertEqual(self.driver.gate.fatal,'submission_during_recording')
    def test_callback_attribution_exact_field_value_count_only_two(self):
        gate=self.driver.gate;gate.recording=False;url=self.server.origin+'/wicket/page?1-2.IBehaviorListener.0-form-field';gate.s['gate_patterns']=[pattern(url,'POST')];gate.filling=('form-field','field','x')
        self.page.evaluate("""url=>{for(let i=0;i<3;i++)fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded','Wicket-Ajax':'true'},body:'field=x'}).catch(()=>{});} """,url)
        self.wait();self.assertEqual(len(self.server.calls),2)
    def test_submit_single_token_real_formdata_and_redirect_not_followed(self):
        gate=self.driver.gate;gate.recording=False;gate.rehearse=False;gate.arm({'field':'x'},'hf',intent_recorded=True);self.server.redirect='/overview/'+self.config.raw['submit']['target_config_id']
        url=self.server.origin+'/wicket/page?1-2.IFormSubmitListener-form'
        self.page.evaluate("""url=>{for(let i=0;i<2;i++){let d=new FormData();d.append('field','x');d.append('hf','');fetch(url,{method:'POST',body:d}).catch(()=>{});}}""",url)
        self.wait();self.assertEqual(self.server.calls,[('POST','/wicket/page?1-2.IFormSubmitListener-form')])
    def test_mismatched_body_burns_token_and_never_sends(self):
        gate=self.driver.gate;gate.recording=False;gate.rehearse=False;gate.arm({'field':'frozen'},'hf',intent_recorded=True)
        self.page.evaluate("""base=>{let d=new FormData();d.append('field','changed');d.append('hf','');fetch(base+'/wicket/page?1-2.IFormSubmitListener-form',{method:'POST',body:d}).catch(()=>{});}""",self.server.origin)
        self.wait();self.assertEqual(self.server.calls,[]);self.assertEqual(gate.fatal,'blocked_before_send')
    def test_same_origin_login_and_cross_origin_mfa_are_not_business_forms(self):
        other=Server();self.addCleanup(other.close)
        self.page.evaluate("""base=>{let f=document.createElement('iframe');f.src=base+'/mfa';document.body.append(f);fetch('/login').catch(()=>{});}""",other.origin)
        self.wait();self.assertEqual(other.calls,[]);self.assertEqual(self.server.calls,[])
        with self.assertRaises(Exception):self.driver.snapshot()
    def test_auth_callback_redirect_to_unregistered_business_is_blocked(self):
        gate=self.driver.gate;gate.phase='auth';gate.s['auth_paths']=[{'host':self.server.origin.split('://')[1],'path':'/auth','method':'POST'}];self.server.redirect='/run'
        self.page.evaluate("""()=>fetch('/auth',{method:'POST',body:'synthetic'}).catch(()=>{})""")
        self.wait();self.assertEqual(self.server.calls,[('POST','/auth')])
    def test_service_worker_and_websocket_cannot_open_channels(self):
        self.page.evaluate("""base=>{try{new WebSocket(base.replace('http:','ws:')+'/socket')}catch(e){};navigator.serviceWorker.register('/worker.js').catch(()=>{});}""",self.server.origin)
        self.wait();self.assertEqual(self.server.calls,[])
