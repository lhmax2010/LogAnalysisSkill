"""Real Chrome + local server request counts. Missing runtime is NEVER a pass."""
import importlib.util
import os
from pathlib import Path
import shutil
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
from helpers import REPO
from headless_watchdog import HeadlessWatchdog
from test_batch3a11b1 import B1Case
from test_batch3a11b2a import CTX,Processes
from vd_cosmos_core import submit_model as model,submit_sessions as sessions
from vd_cosmos_core.submit_gate import pattern
from vd_cosmos_core.browser_executable import resolve as resolve_browser
from vd_cosmos_core import browser_temp
from vd_cosmos_submit.playwright_driver import Driver

def browser_runtime(case):
    exe=resolve_browser()
    print('Chrome executable (selected): '+str(exe),flush=True)
    reason='Playwright Python runtime unavailable' if importlib.util.find_spec('playwright') is None else 'existing Chrome/Chromium unavailable' if not exe else None
    if reason:
        if os.environ.get('VD_REQUIRE_HEADLESS')=='1':case.fail('required real-browser test: '+reason)
        case.skipTest(reason)
    return exe


class HeadlessTempTests(HeadlessWatchdog,B1Case):
    def test_long_inherited_tmpdir_starts_with_short_browser_only_temp(self):
        exe=browser_runtime(self)
        inherited=self.root/('long-'+('x'*130));inherited.mkdir()
        self.config.raw['submit']['browser_executable']=exe
        r=model.create_request(self.config,CTX,self.form(),'local temp verification')
        session=sessions.start(self.config,r,CTX,Processes())
        driver=Driver(self.config,session,headless=True);self.addCleanup(driver.close)
        profile=sessions.profile_path(self.config,session)
        with patch.dict(os.environ,dict.fromkeys(('TMPDIR','TMP','TEMP'),str(inherited))):
            driver.launch(rehearse=True)
            print('Chrome executable (launched): '+exe,flush=True)
            import json
            temp=Path(json.loads((profile/browser_temp.MARKER).read_text())['path'])
            self.assertTrue(browser_temp.fits(temp));self.assertNotEqual(temp,inherited)
            self.assertEqual(driver._page.url,'about:blank')
            self.assertEqual(os.environ['TMPDIR'],str(inherited))
            self.assertEqual(temp.stat().st_mode & 0o777,0o700)
            driver.close();self.assertFalse(temp.exists())
            self.assertEqual(os.environ['TMPDIR'],str(inherited))


class Server(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(('127.0.0.1',0),Handler);self.calls=[];self.redirect=None;self.responses={}
        self.thread=threading.Thread(target=self.serve_forever,daemon=True);self.thread.start()
    @property
    def origin(self):return 'http://127.0.0.1:'+str(self.server_port)
    def close(self):self.shutdown();self.server_close();self.thread.join()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        self.server.calls.append(('GET',self.path))
        status,location,body=self.server.responses.get(self.path,(200,None,b'<html><body><button id="human">human action</button><input type="password" autocomplete="current-password"></body></html>'))
        self.send_response(status)
        if location:self.send_header('Location',location)
        self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get('Content-Length','0')));self.server.calls.append(('POST',self.path))
        if self.server.redirect:self.send_response(302);self.send_header('Location',self.server.redirect)
        else:self.send_response(200)
        self.end_headers();self.wfile.write(b'ok')

class HeadlessGateTests(HeadlessWatchdog,B1Case):
    def setUp(self):
        super().setUp();exe=browser_runtime(self)
        self.server=Server();self.addCleanup(self.server.close);self.config.raw['submit']['browser_executable']=exe
        r=model.create_request(self.config,CTX,self.form(),'local browser verification');self.session=sessions.start(self.config,r,CTX,Processes())
        self.expect_pause_fault=False
        self.driver=Driver(self.config,self.session,headless=True,local_origin=self.server.origin);self.addCleanup(self.close_driver);self.driver.launch(rehearse=True)
        print('Chrome executable (launched): '+exe,flush=True)
        self.page=self.driver._page;url=self.server.origin+'/overview/'+self.config.raw['submit']['target_config_id'];self.driver.gate.navigation(url);self.page.goto(url,wait_until='domcontentloaded');self.page.wait_for_timeout(100)
        self.assertEqual(self.driver.gate.phase,'business');self.server.calls.clear()
    def close_driver(self):
        self.driver.close()
        if not self.expect_pause_fault:self.driver._check_pause_fault()
        counts=self.driver.pause_counts()
        self.assertEqual(counts['pending'],0)
        self.assertEqual(counts['paused'],counts['resolved']+counts['closed_unconfirmed'])
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
    def test_undecided_subresource_expires_without_reaching_server(self):
        driver=self.driver;driver.pause_timeout_s=.35
        self.expect_pause_fault=True
        driver.gate.static_keys.add('/stalled.js')
        before=driver.pause_counts();defer=driver._defer
        held=[]
        def withhold(owner,method,*args,pause=None,continuing=False):
            if continuing and pause.stage=='fetch_request' and pause.shape['path']=='registered_static':
                held.append(pause)
                return
            return defer(owner,method,*args,pause=pause,continuing=continuing)
        with patch.object(driver,'_defer',side_effect=withhold):
            self.page.evaluate("""()=>{let s=document.createElement('script');s.src='/stalled.js?v=private-fixture';document.head.append(s);}""")
            self.page.wait_for_timeout(800)
        self.assertEqual(len(held),1)
        self.assertEqual(self.server.calls,[])
        e=self.fails(4,driver._check_pause_fault)
        self.assertEqual(e.reason,'paused_request_unresolved')
        records=[r for r in driver.records() if r.get('reason')=='paused_request_unresolved']
        self.assertEqual(records,[{'reason':'paused_request_unresolved','stage':'fetch_request',
                'url_shape':{'scheme':'http','origin':'hub','path':'registered_static','has_query':True}}])
        after=driver.pause_counts()
        self.assertGreater(after['paused'],before['paused'])
        self.assertEqual((after['paused'],after['pending'],after['closed_unconfirmed']),(after['resolved'],0,0))
    def test_same_origin_login_and_cross_origin_mfa_are_not_business_forms(self):
        other=Server();self.addCleanup(other.close)
        self.page.evaluate("""base=>{let f=document.createElement('iframe');f.src=base+'/mfa';document.body.append(f);fetch('/login').catch(()=>{});}""",other.origin)
        self.wait();self.assertEqual(other.calls,[]);self.assertEqual(self.server.calls,[])
        with self.assertRaises(Exception):self.driver.snapshot()
    def test_auth_callback_redirect_to_unregistered_business_is_blocked(self):
        gate=self.driver.gate;gate.phase='auth';gate.s['auth_paths']=[{'host':self.server.origin.split('://')[1],'path':'/auth','method':'POST'}];self.server.redirect='/run'
        self.page.evaluate("""()=>fetch('/auth',{method:'POST',body:'synthetic'}).catch(()=>{})""")
        self.wait();self.assertEqual(self.server.calls,[('POST','/auth')])
    def test_dashboard_account_must_match_once_before_target_navigation(self):
        account='fixture.user';self.config.raw['submit']['account']=account
        signout='<a id="logout" class="menu-link"> Sign Out </a>'
        self.server.calls.clear()
        self.driver.gate.phase='auth'
        self.server.responses['/']=(302,'/dashboard',b'')
        self.server.responses['/dashboard']=(200,None,b'<header>no account match</header>')
        with patch.object(self.driver,'launch'):
            error=self.fails(3,self.driver.open,lambda:None,lambda _:None)
        self.assertEqual(error.reason,'hub_account_mismatch')
        self.assertEqual(self.server.calls,[('GET','/'),('GET','/dashboard')])
        dashboard=self.server.origin+'/dashboard'
        self.page.set_content(f'<div id="greeting" class="profile">Welcome!  {account} {signout}</div>')
        self.driver._check_account(dashboard)
        evidence=self.driver.gate.records[-1]['account_check']
        self.assertEqual(evidence,{'matched':True,'element':{'tag':'a','id':'logout','class':'menu-link'},
                                  'container':{'tag':'div','id':'greeting','class':'profile'},
                                  'container_text':f'Welcome! {account} Sign Out'})
        self.page.set_content(f'<nav><span>{account}</span> <button> SIGN OUT </button>'
                              '<button hidden>Sign Out</button></nav>')
        self.driver._check_account(dashboard)
        self.assertEqual(self.driver.gate.records[-1]['account_check']['container']['tag'],'nav')
        self.page.set_content(f'<div id="outer">{account}<div id="near">({account}), {signout}</div></div>')
        self.driver._check_account(dashboard)
        self.assertEqual(self.driver.gate.records[-1]['account_check']['container']['id'],'near')
        self.page.set_content(f'<div>{"x"*81} <span>{account}</span> {signout}</div>')
        self.driver._check_account(dashboard)
        self.assertNotIn('container_text',self.driver.gate.records[-1]['account_check'])

        for label,greeting in (
            ('trailing',f'<div>{account}x {signout}</div>'),
            ('leading',f'<div>x{account} {signout}</div>'),
            ('literal dot','<div>fixtureXuser '+signout+'</div>'),
            ('wrong account',f'<div>another-user {signout}</div>'),
            ('case-sensitive account',f'<div>{account.upper()} {signout}</div>'),
            ('hidden account',f'<div><span hidden>{account}</span> {signout}</div>'),
            ('too distant',f'<div>{account}<div><div><div>{signout}</div></div></div></div>'),
            ('duplicate',f'<div>{account} {signout} <a>Sign Out</a></div>'),
            ('no Sign Out',f'<nav>{account}</nav>'),
            ('not a control',f'<div>{account} <span>Sign Out</span></div>'),
        ):
            with self.subTest(label=label):
                self.page.set_content(greeting)
                mismatch=self.fails(3,self.driver._check_account,dashboard)
                self.assertEqual(mismatch.reason,'hub_account_mismatch')
                evidence=mismatch.details['account_check']
                self.assertFalse(evidence['matched'])
                self.assertIsNone(evidence['container'])
                self.assertNotIn('container_text',evidence)
                if label in ('duplicate','no Sign Out','not a control'):
                    self.assertIsNone(evidence['element'])

    def test_manual_login_redirect_and_password_document_refuse_sso_fallback(self):
        from unittest.mock import patch
        self.driver.gate.phase='auth'
        self.server.responses['/']=(302,'/signin?manual-login',b'')
        with patch.object(self.driver,'launch'):
            e=self.fails(3,self.driver.open,lambda:None,lambda _:None)
        self.assertEqual(e.reason,'hub_manual_login_page')
        self.assertEqual(self.server.calls,[('GET','/')])
        self.server.calls.clear();self.driver.gate.manual_login=False
        self.server.responses['/']=(302,'/dashboard',b'')
        with patch.object(self.driver,'launch'):
            e=self.fails(3,self.driver.open,lambda:None,lambda _:None)
        self.assertEqual(e.details['todo']['message'],'log in through SSO only; restart')
        self.assertEqual(self.server.calls,[('GET','/'),('GET','/dashboard')])

    def test_notice_style_only_and_exact_run_sends_once(self):
        from unittest.mock import patch
        path=self.driver.gate.overview
        run=path+'?7-1.ILinkListener-run'
        self.server.responses[run]=(302,'/wicket/page?9',b'')
        self.server.responses['/wicket/page?9']=(200,None,b'<main>editor</main>')
        self.page.set_content(f'<a href="{run}">Run the configuration</a>'
                              '<div id="myNav" class="overlay" style="position:fixed;inset:0">'
                              '<a onclick="fetch(\'/should-not-run\')">close</a></div>')
        entry=self.server.origin+path
        self.driver._dismiss_notice(entry)
        self.assertEqual(self.server.calls,[])
        self.assertFalse(self.page.locator('#myNav').is_visible())
        def confirm(details):
            self.assertEqual(self.server.calls,[])
            self.assertEqual(details['run_pattern']['path'],path)
            return 'allow-run'
        with patch.object(self.driver,'_window'):
            self.driver._run_editor(entry,confirm)
        self.assertEqual(self.server.calls,[('GET',run),('GET','/wicket/page?9')])

    def test_wrong_run_answer_gives_expected_word_and_never_navigates(self):
        path=self.driver.gate.overview
        self.page.set_content(f'<a href="{path}?7-1.ILinkListener-run">Run the configuration</a>')
        with patch.object(self.driver,'_window'):
            error=self.fails(3,self.driver._run_editor,self.server.origin+path,lambda _:'yes')
        self.assertEqual(error.reason,'run_confirmation_required')
        self.assertEqual(error.details['todo']['expected'],'allow-run')
        self.assertEqual(self.server.calls,[])

    def test_notice_cannot_hide_other_obstructions_or_send_mutation_requests(self):
        entry=self.page.url
        self.page.set_content('<button>Run the configuration</button>'
                              '<div style="position:fixed;inset:0"></div>')
        self.assertEqual(self.fails(4,self.driver._dismiss_notice,entry).reason,'run_button_obscured')
        self.page.set_content('<button>Run the configuration</button>'
                              '<div id="myNav" class="overlay" style="position:fixed;inset:0"></div>'
                              '<script>new MutationObserver(()=>fetch("/leak")).observe('
                              'document.querySelector("#myNav"),{attributes:true});</script>')
        e=self.fails(4,self.driver._dismiss_notice,entry)
        self.assertEqual(e.reason,'request_during_notice_dismissal')
        self.assertEqual(self.server.calls,[])

    def test_form_breadcrumb_segments_allow_optional_root_and_capture_mismatch(self):
        from html import escape
        from vd_cosmos_core.submit_browser_contract import SEED
        self.driver.gate.run_redirect=self.server.origin+'/wicket/page?1'
        self.page.goto(self.server.origin+'/wicket/page?1')
        rows=[]
        for seed in SEED:
            name=seed['name']
            if seed['kind']=='ks':
                prefix=name.removesuffix('recorder')
                control=(f'<input type="hidden" name="{name}"><select name="{prefix}choices"></select>'
                         f'<select name="{prefix}selection"></select>')
            elif seed['kind'] in {'select','textarea'}:
                control=f'<{seed["kind"]} name="{name}"></{seed["kind"]}>'
            else:
                control=f'<input type="{seed["kind"]}" name="{name}">'
            rows.append(f'<tr><td>{escape(seed["label"])}</td><td>{control}</td></tr>')
        form='<form id="form" enctype="multipart/form-data"><input type="hidden" name="form_hf_0"><table>'+''.join(rows)+'</table></form>'
        for breadcrumb, segments in (('root / PRODUCT &gt; fixture » RELEASE', ['root','PRODUCT','fixture','RELEASE']),
                                     ('PRODUCT › fixture\nRELEASE',['PRODUCT','fixture','RELEASE'])):
            self.page.set_content(f'<div class="breadcrumbs">{breadcrumb}</div>'+form)
            snapshot=self.driver.snapshot()
            self.assertEqual(snapshot['breadcrumb_segments'], segments)
            self.assertEqual(len(snapshot['controls']),18)
        self.driver._script('fill',index=17,value='fixture-knob')
        submitted=dict(self.driver._script('serialize'))
        self.assertEqual(submitted[SEED[17]['name']],'fixture-knob')
        self.assertIn('form_hf_0',submitted)
        self.page.set_content('<div class="breadcrumb">PRODUCT / wrong / RELEASE</div>'+form)
        error=self.fails(5,self.driver.snapshot)
        self.assertEqual(error.reason,'form_unrecognized')
        self.assertEqual(error.details['breadcrumb_segments'],['PRODUCT','wrong','RELEASE'])

    def test_service_worker_and_websocket_cannot_open_channels(self):
        self.page.evaluate("""base=>{try{new WebSocket(base.replace('http:','ws:')+'/socket')}catch(e){};navigator.serviceWorker.register('/worker.js').catch(()=>{});}""",self.server.origin)
        self.wait();self.assertEqual(self.server.calls,[])

    def test_browser_process_tree_never_disables_sandbox(self):
        from vd_cosmos_core.submit_sessions import Processes
        profile=sessions.profile_path(self.config,self.session)
        roots={pid for pid,_ in Processes().matching(profile)}
        self.assertTrue(roots,'browser PID with this profile must exist')
        processes={}
        for item in Path('/proc').iterdir():
            if not item.name.isdecimal():continue
            try:
                fields=(item/'stat').read_text().rsplit(')',1)[1].split()
                processes[int(item.name)]=(int(fields[1]),(item/'cmdline').read_bytes().split(b'\0'))
            except OSError:continue
        selected=set(roots)
        while True:
            children={pid for pid,(parent,_) in processes.items() if parent in selected}
            if children<=selected:break
            selected|=children
        self.assertTrue(selected)
        for pid in selected:
            if pid in processes:self.assertNotIn(b'--no-sandbox',processes[pid][1],'sandbox disabled in browser tree PID '+str(pid))
