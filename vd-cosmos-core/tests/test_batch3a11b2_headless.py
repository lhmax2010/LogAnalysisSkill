"""Real Chrome + local server request counts. Missing runtime is NEVER a pass."""
from base64 import b64decode
import importlib.util
import os
from pathlib import Path
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
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
        self.holds={};self.delays={};self.completed={}
        self.thread=threading.Thread(target=self.serve_forever,daemon=True);self.thread.start()
    @property
    def origin(self):return 'http://127.0.0.1:'+str(self.server_port)
    def close(self):self.shutdown();self.server_close();self.thread.join()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        self.server.calls.append(('GET',self.path))
        if self.path in self.server.holds:self.server.holds[self.path].wait(5)
        if self.path in self.server.delays:time.sleep(self.server.delays[self.path])
        status,location,body=self.server.responses.get(self.path,(200,None,b'<html><body><button id="human">human action</button><input type="password" autocomplete="current-password"></body></html>'))
        self.send_response(status)
        if location:self.send_header('Location',location)
        self.send_header('Content-Type','text/html');self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):return
        self.server.completed[self.path]=time.monotonic()
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
        self.driver.quiet_window_s=.18
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
    def test_blocked_icon_and_prefetch_quiet_without_network_terminal_callback(self):
        driver = self.driver
        # Chrome really blocks these requests. Drop the accounting notification
        # to reproduce the missing terminal callback independently of timing.
        driver._cdp.remove_listener('Network.loadingFailed', driver._network_failed)
        page_started, page_failed = set(), set()
        self.page.on('request', lambda request: page_started.add(request.url))
        self.page.on('requestfailed', lambda request: page_failed.add(request.url))
        path = driver.gate.overview
        url = self.server.origin + path
        driver.gate.navigation(url)
        self.server.responses[path] = (200, None, b'<link rel="icon" href="/favicon.ico">'
            b'<link rel="prefetch" href="/future42.html?mode=opaque-fixture-value">'
            b'<script>fetch("/denied123.ico").catch(()=>{});</script>')
        start = len(driver._pause_timeline)
        self.page.goto(url, wait_until='load')
        shapes = {'/favicon.ico', '/futureN.html?mode', '/deniedN.ico'}
        deadline = time.monotonic() + 5
        while not shapes <= {row.get('path_shape') for row in driver._pause_timeline[start:]}:
            self.assertLess(time.monotonic(), deadline)
            self.page.wait_for_timeout(25)
        driver._wait_for_quiet(load=True)
        timeline = driver._pause_timeline[start:]
        blocked = [row for row in timeline if row.get('path_shape') in shapes]
        self.assertCountEqual([row['path_shape'] for row in blocked], shapes)
        self.assertTrue(all(row['command'] == 'Fetch.failRequest' and row['acked_at'] is not None for row in blocked))
        self.assertTrue(all(row['path'] == 'unregistered' for row in blocked))
        self.assertNotIn('opaque-fixture-value', str(timeline))
        for path in ('/future42.html?mode=opaque-fixture-value', '/denied123.ico'):
            self.assertIn(self.server.origin + path, page_started)
            self.assertIn(self.server.origin + path, page_failed)
        self.assertNotIn(self.server.origin + '/favicon.ico', page_started | page_failed)
        self.assertEqual(self.server.calls, [('GET', driver.gate.overview)])
        self.assertEqual(driver._network_started, driver._network_finished)

    def cancelled_fetch(self, command):
        driver = self.driver
        path = '/cancel-before-decision.png'
        if command == 'Fetch.continueRequest':
            # One exact loopback request is allowed for this fixture.
            driver.gate.allowed = (self.server.origin + path, 'GET')
        deferred, terminal = [], set()
        original = driver._defer

        def hold(owner, method, *args, pause=None, continuing=False):
            if pause and pause.evidence['path'] == path:
                deferred.append((owner, method, args, pause, continuing))
            else:
                original(owner, method, *args, pause=pause, continuing=continuing)

        driver._cdp.on('Network.loadingFailed', lambda event: terminal.add(event['requestId']))
        # The CDP event proves cancellation. Production accounting must also
        # work if that event was not available to the accounting listener.
        driver._cdp.remove_listener('Network.loadingFailed', driver._network_failed)
        with patch.object(driver, '_defer', side_effect=hold):
            self.page.evaluate("""url => {
                window.fixtureAbort = new AbortController();
                fetch(url, {signal: fixtureAbort.signal}).catch(() => {});
            }""", path)
            deadline = time.monotonic() + 5
            while not deferred:
                self.assertLess(time.monotonic(), deadline)
                self.page.wait_for_timeout(25)
            owner, method, args, pause, continuing = deferred[0]
            self.assertEqual(args[0], command)
            self.assertEqual(pause.flight.key[0], 'network')
            self.page.evaluate('() => window.fixtureAbort.abort()')
            while pause.flight.key[1] not in terminal:
                self.assertLess(time.monotonic(), deadline)
                self.page.wait_for_timeout(25)
            self.assertIn(pause.flight.key, driver._in_flight)
        original(owner, method, *args, pause=pause, continuing=continuing)
        driver._wait_for_quiet(load=True)
        self.assertEqual(len(deferred), 1)
        self.assertEqual(driver.pause_counts()['gone_before_decision'], 1)
        self.assertEqual(driver.pause_counts()['paused'], driver.pause_counts()['resolved'])
        self.assertEqual(driver._network_started, driver._network_finished)
        self.assertEqual(pause.timeline['command'], command)
        self.assertEqual(pause.timeline['resolution'], 'gone_before_decision')
        self.assertEqual(pause.timeline['error_type'], 'Error')
        self.assertEqual(pause.timeline['error_message'], 'Invalid InterceptionId.')
        self.assertIsNotNone(pause.timeline['sent_at'])
        self.assertIsNone(pause.timeline['acked_at'])
        self.assertEqual(self.server.calls, [])

        # An unrelated registered asset can still load after the cancellation.
        driver.gate.static_keys.add('/after-cancel.png')
        self.page.evaluate("""() => {
            const image = new Image();
            image.onload = image.onerror = () => { window.fixtureImageDone = true; };
            image.src = '/after-cancel.png';
            document.body.append(image);
        }""")
        self.page.wait_for_function('window.fixtureImageDone === true', timeout=5000)
        driver._wait_for_quiet()
        self.assertEqual(self.server.calls, [('GET', '/after-cancel.png')])

    def test_cancelled_request_fail_command_is_gone_and_reaches_quiet(self):
        self.cancelled_fetch('Fetch.failRequest')

    def test_cancelled_request_continue_command_is_gone_and_reaches_quiet(self):
        self.cancelled_fetch('Fetch.continueRequest')

    def test_sixty_static_files_with_slow_response_have_one_pause_each(self):
        paths=[f'/asset/fixture-{index}.png' for index in range(60)]
        self.driver.gate.static_keys.update(paths)
        slow=paths[-1]
        self.server.delays[slow]=2
        target='/overview/'+self.config.raw['submit']['target_config_id']
        self.driver.gate.navigation(self.server.origin+target)
        self.server.responses[target]=(200,None,('<html><body>' +
            ''.join(f'<img src="{path}">' for path in paths) + '</body></html>').encode())
        start=len(self.driver._pause_timeline)
        self.page.reload(wait_until='load',timeout=20000)
        self.driver._wait_for_quiet(load=True)
        timeline=[r for r in self.driver._pause_timeline[start:] if r['path'] in paths]
        self.assertCountEqual([r['path'] for r in timeline],paths)
        self.assertTrue(all(r['stage']=='fetch_request' and r['command']=='Fetch.continueRequest'
            and r['paused_at']<=r['decision_at']<=r['sent_at']<=r['acked_at'] for r in timeline))
        self.assertCountEqual([path for method,path in self.server.calls if path in paths],paths)
        self.assertEqual(self.driver.pause_counts()['closed_unconfirmed'],0)
        self.assertEqual(self.driver.pause_counts()['pending'],0)

    def test_human_get_post_navigation_popup_and_iframe_never_reach_server(self):
        self.assertFalse(self.page.evaluate('Object.getOwnPropertyDescriptor(window, "open").writable'))
        self.page.evaluate("""base=>{fetch(base+'/write',{method:'POST'}).catch(()=>{});fetch(base+'/run').catch(()=>{});window.open(base+'/popup');let a=document.createElement('a');a.target='_blank';a.href=base+'/popup-link';document.body.append(a);a.click();let f=document.createElement('iframe');f.src=base+'/iframe';document.body.append(f);} """,self.server.origin)
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

    def test_run_obscured_reasons_include_only_safe_geometry_facts(self):
        driver = self.driver
        button = '<button>Run the configuration</button>'
        overlay = '<div id="cover" class="' + 'x'*80 + '" style="position:fixed;inset:0"></div>'
        secret_shape = ('<div id="https://local.invalid/hidden" class="https://local.invalid/hidden"'
                        ' style="position:fixed;inset:0">fixture-private-text</div>')
        cases = [
            ('notices_multiple', button + '<div id="myNav" class="overlay">One</div>'*2, 2, 1, None),
            ('button_count', '<button>Different label</button>', 0, 0, None),
            ('button_count', button*2, 0, 2, None),
            ('hit_outside_viewport', '<style>button{position:fixed;top:200vh}</style>' + button, 0, 1, None),
            ('hit_other_element', button + overlay, 0, 1, {'tag': 'div', 'id': 'cover', 'class': 'x'*60}),
            ('hit_other_element', button + secret_shape, 0, 1,
             {'tag': 'div', 'id': '<redacted>', 'class': '<redacted>'}),
            ('hit_null', '<script>document.elementFromPoint = () => null;</script>' + button, 0, 1, None),
        ]
        for reason, html, notices, count, hit in cases:
            with self.subTest(reason=reason, notices=notices, count=count):
                self.page.set_content(html)
                raised = self.fails(4, driver._dismiss_notice, self.page.url)
                self.assertEqual(raised.reason, 'run_button_obscured')
                info = raised.details
                self.assertEqual(info['hit_reason'], reason)
                operation = 'run_position' if reason == 'hit_outside_viewport' else 'dismiss_notice'
                self.assertEqual(info['operation'], operation)
                self.assertFalse(info['clear'])
                self.assertEqual(info['window_state'], 'normal')
                self.assertIn(info['visibility_state'], {'visible', 'hidden'})
                self.assertEqual((info['notices_visible'], info['button_count'], info['hit']), (notices, count, hit))
                self.assertGreater(info['viewport']['innerHeight'], 0)
                self.assertGreater(info['viewport']['innerWidth'], 0)
                if count == 1:
                    self.assertEqual(set(info['rect']), {'x', 'y', 'w', 'h'})
                    self.assertTrue(all(type(value) is int for value in info['rect'].values()))
                else:
                    self.assertIsNone(info['rect'])
                self.assertNotIn('local.invalid', str(info))
                self.assertNotIn('fixture-private-text', str(info))
        self.assertEqual(self.server.calls, [])

    def test_run_label_whitespace_is_collapsed_before_the_exact_match(self):
        for label in ('Run<br>the configuration', 'Run&nbsp;the configuration', 'Run  the configuration',
                      'Run\t the configuration'):
            with self.subTest(label=label):
                self.page.set_content(f'<button style="white-space:pre">{label}</button>')
                result = self.driver._run_position(self.page.url)
                self.assertTrue(result['clear'])
                self.assertEqual(result['button_count'], 1)
                self.assertEqual(result['hit']['tag'], 'button')
                self.assertNotIn('near_matches', result)

        self.page.set_content('<input type="button" value="Run&#160;the configuration">')
        self.assertEqual(self.driver._run_position(self.page.url)['hit']['tag'], 'input')
        self.page.set_content('<button>Run&nbsp;the configuration</button>'
                              '<button>Run<br>the configuration</button>')
        error = self.fails(4, self.driver._run_position, self.page.url)
        self.assertEqual((error.details['hit_reason'], error.details['button_count']), ('button_count', 2))
        self.assertEqual([row['visible']['new'] for row in error.details['near_matches']], [True, True])
        self.assertEqual(self.server.calls, [])

    def test_run_match_excludes_hidden_and_transparent_buttons_and_still_checks_hit(self):
        button = '<button>Run the configuration</button>'
        for style in ('opacity:0', 'visibility:hidden', 'display:none'):
            for ancestor in (False, True):
                with self.subTest(style=style, ancestor=ancestor):
                    markup = f'<div style="{style}">{button}</div>' if ancestor else button.replace('<button>', f'<button style="{style}">')
                    self.page.set_content(markup)
                    error = self.fails(4, self.driver._run_position, self.page.url)
                    self.assertEqual((error.details['hit_reason'], error.details['button_count']), ('button_count', 0))

        self.page.set_content('<button style="pointer-events:none">Run the configuration</button>')
        error = self.fails(4, self.driver._run_position, self.page.url)
        self.assertEqual(error.details['button_count'], 1)
        self.assertIn(error.details['hit_reason'], ('hit_other_element', 'hit_null'))
        self.assertEqual(self.server.calls, [])

    def test_run_near_match_diagnostics_are_bounded_and_sanitized(self):
        self.page.set_content(
            '<button>Run ' + 'a'*41 + '</button>'
            '<button style="opacity:0;white-space:pre">Run&nbsp;the\t\nconfiguration extra</button>'
            '<a title="RUN&#9;helper" href="https://local.invalid/private">Other label</a>'
            '<input type="text" value="Run editable private value" aria-label="Run&nbsp;setup">'
            '<button title="Run https://local.invalid/x" onclick="void \'private-handler\'">Another label</button>'
            '<div id="myNav"><button>Run status</button></div>'
            '<button>Run beyond the cap</button>')
        error = self.fails(4, self.driver._run_position, self.page.url)
        self.assertEqual((error.details['hit_reason'], error.details['button_count']), ('button_count', 0))
        rows = error.details['near_matches']
        self.assertEqual([(row['tag'], row['field'], row['label']) for row in rows], [
            ('button', 'text', 'Run⍽the⇥⏎configuration␠extra'),
            ('a', 'title', 'RUN⇥helper'),
            ('input', 'aria-label', 'Run⍽setup'),
            ('button', 'title', '<non-label>'),
            ('button', 'text', 'Run␠status'),
        ])
        self.assertEqual([row['visible'] for row in rows], [{'old': False, 'new': False}] + [{'old': True, 'new': True}]*4)
        self.assertEqual([row['inside_notice'] for row in rows], [False, False, False, False, True])
        self.assertTrue(all(set(row['rect']) == {'x', 'y', 'w', 'h'} for row in rows))
        for private in ('local.invalid', 'editable', 'private-handler', 'onclick', 'href', 'beyond'):
            self.assertNotIn(private, str(error.details))
        self.assertEqual(self.server.calls, [])

    def test_offscreen_run_scrolls_then_waits_and_hits_before_capture(self):
        driver = self.driver
        path = driver.gate.overview
        run = path + '?7-1.ILinkListener-run'
        self.page.set_content(f'<div style="height:240vh"></div><a href="{run}">Run the configuration</a>')
        checks = []
        run_script = driver._run_probe
        wait = driver._wait_for_quiet

        def probe(entry, operation):
            result = run_script(entry, operation)
            checks.append((operation, result['clear'], driver._window_state()))
            return result

        def quiet(**kwargs):
            checks.append(('quiet',))
            return wait(**kwargs)

        with patch.object(driver, '_run_probe', side_effect=probe), \
                 patch.object(driver, '_wait_for_quiet', side_effect=quiet):
            error = self.fails(3, driver._run_editor, self.page.url, lambda _: 'decline')
        self.assertEqual(error.reason, 'run_confirmation_required')
        self.assertEqual(checks[:5], [('quiet',), ('run_position', False, 'normal'),
                                     ('scroll_run', False, 'normal'), ('quiet',),
                                     ('run_position', True, 'normal')])
        self.assertEqual(len(driver.gate.run_candidates), 1)
        self.assertEqual(self.server.calls, [])

    def test_minimize_rechecks_normal_hit_first_and_falls_back_on_changed_rect(self):
        driver = self.driver
        path = driver.gate.overview
        run = path + '?7-1.ILinkListener-run'
        self.page.set_content(f'<a href="{run}">Run the configuration</a>')
        self.server.responses[run] = (302, '/wicket/page?9', b'')
        self.server.responses['/wicket/page?9'] = (200, None, b'<main>editor</main>')
        win = 'normal'
        checks = []
        run_script = driver._run_probe
        click = self.page.mouse.click

        def move(state):
            nonlocal win
            win = state
            checks.append(('window', state))

        def probe(entry, operation):
            result = run_script(entry, operation)
            self.assertTrue(result['clear'])
            checks.append(('probe', win))
            if win == 'minimized':
                result['click_rect'][0] += 0.25  # Same rounded evidence, different actual rectangle.
            return result

        def record_click(*coords):
            checks.append(('click', win, driver.gate.capture_run))
            return click(*coords)

        def confirm(_):
            checks.append(('confirm', win))
            self.assertEqual(self.server.calls, [])
            return 'allow-run'

        with patch.object(driver, '_window_state', side_effect=lambda: win), \
                 patch.object(driver, '_window', side_effect=move), \
                 patch.object(driver, '_run_probe', side_effect=probe), \
                 patch.object(self.page.mouse, 'click', side_effect=record_click):
            driver._run_editor(self.page.url, confirm)
        self.assertEqual(checks, [('probe', 'normal'), ('window', 'minimized'), ('probe', 'minimized'),
                                  ('window', 'normal'), ('probe', 'normal'), ('click', 'normal', True),
                                  ('confirm', 'normal'), ('probe', 'normal'), ('click', 'normal', False),
                                  ('window', 'minimized')])
        self.assertEqual(self.server.calls, [('GET', run), ('GET', '/wicket/page?9')])

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
        record,=[r for r in e.details['request_records'] if r['path']=='/leak']
        self.assertIn(record['resource_type'].lower(),{'xhr','fetch'})
        self.assertEqual(record['decision'],e.reason)
        self.assertEqual(self.server.calls,[])

    def slow_target(self):
        path=self.driver.gate.overview;url=self.server.origin+path
        image='/slow.png?v=fixture-value'
        release=threading.Event();self.addCleanup(release.set)
        self.server.holds[image]=release
        self.server.responses[path]=(200,None,b'<button>Run the configuration</button><img src="/slow.png?v=fixture-value">'
                                             b'<div id="myNav" class="overlay" style="position:fixed;inset:0"></div>')
        self.driver.gate.static_keys.add('/slow.png')
        self.driver.gate.navigation(url)
        self.page.goto(url,wait_until='domcontentloaded')
        self.assertNotIn(image,self.server.completed)
        return url,image,release

    def test_navigation_retires_slow_image_without_a_loading_failed_event(self):
        _, image, release = self.slow_target()
        driver = self.driver
        driver._cdp.remove_listener('Network.loadingFailed', driver._network_failed)
        self.assertTrue(any(row['path_shape'] == '/slow.png?v' for row in driver._in_flight_evidence(time.monotonic())
                            if row['origin'] == 'hub'))
        target = '/second-document'
        self.server.responses[target] = (200, None, b'<p>Second document</p>')
        driver.gate.allowed = (self.server.origin + target, 'GET')
        self.page.goto(self.server.origin + target, wait_until='load')
        try:
            driver._wait_for_quiet(load=True)
            self.assertNotIn(image, self.server.completed)
            evidence = driver._operation_evidence()
            self.assertEqual(evidence['superseded_by_navigation'], 1)
            row, = evidence['superseded_requests']
            self.assertEqual((row['loader'], row['decision'], row['paused'], row['from_cache']),
                             ('previous', 'continued', False, False))
            self.assertEqual(row['path_shape'], '/slow.png?v')
            self.assertEqual(row['resolution'], 'superseded_by_navigation')
            self.assertEqual(row['network_events_seen'], ['requestWillBeSent'])
            self.assertEqual(driver._network_started, driver._network_finished)
        finally:
            release.set()

    def test_auth_request_without_network_id_blocks_current_then_is_superseded(self):
        driver = self.driver
        auth = Server()
        self.addCleanup(auth.close)
        release = threading.Event()
        self.addCleanup(release.set)
        path = '/fixture-held-image.png'
        auth.holds[path] = release
        auth.responses['/fixture-auth'] = (200, None, b'<p>Loopback auth</p>')
        held_url = auth.origin + path
        auth_urls = {held_url, auth.origin + '/fixture-auth'}
        driver.gate.s['auth_paths'] = [{'host': urlsplit(auth.origin).netloc, 'path': urlsplit(url).path, 'method': 'GET'}
                                      for url in auth_urls]
        original_gate = driver.gate.request
        original_pause = driver._flight_for_pause

        def gate(url, method, **options):
            if method == 'GET' and url in auth_urls:
                return True  # Loopback HTTP test exception, never used in the adapter.
            return original_gate(url, method, **options)

        driver._cdp.remove_listener('Network.requestWillBeSent', driver._network_start)

        def network_start(event):
            if event['request']['url'] != held_url:
                driver._network_start(event)

        def hide_id(event, url, *args):
            if url == held_url:
                event = {key: value for key, value in event.items() if key != 'networkId'}
            return original_pause(event, url, *args)

        driver._cdp.on('Network.requestWillBeSent', network_start)
        with patch.object(driver.gate, 'request', side_effect=gate), \
                 patch.object(driver, '_flight_for_pause', side_effect=hide_id):
            self.page.goto(auth.origin + '/fixture-auth', wait_until='load')
            driver._wait_for_quiet(load=True)
            generation = driver._document_generation
            self.page.evaluate('path => { const img = new Image(); img.src = path; document.body.append(img); }', path)
            deadline = time.monotonic() + 5
            while ('GET', path) not in auth.calls:
                self.assertLess(time.monotonic(), deadline)
                self.page.wait_for_timeout(25)
            driver.quiet_timeout_s = .4
            error = self.fails(5, driver._wait_for_quiet)
            self.assertEqual((error.reason, error.details['wait_phase']), ('target_page_not_quiet', 'quiet'))
            row, = error.details['in_flight_requests']
            self.assertEqual({key: row[key] for key in ('host_class', 'loader', 'generation', 'current_generation',
                                                        'network_id_present', 'decision', 'path', 'network_events_seen')},
                             {'host_class': 'auth', 'loader': 'unknown', 'generation': generation,
                              'current_generation': generation, 'network_id_present': False, 'decision': 'continued',
                              'path': 'unregistered', 'network_events_seen': []})
            self.assertNotIn(auth.origin, str(row))
            self.assertNotIn(path, str(row))

        driver.quiet_timeout_s = 5
        for target in ('/fixture-dashboard', '/fixture-overview'):
            self.server.responses[target] = (200, None, b'<p>Loopback hub</p>')
            driver.gate.allowed = (self.server.origin + target, 'GET')
            self.page.goto(self.server.origin + target, wait_until='load')
            driver._wait_for_quiet(load=True)
        self.assertEqual(driver._document_generation, generation + 2)
        row, = driver._operation_evidence()['superseded_requests']
        self.assertEqual((row['generation'], row['current_generation'], row['network_id_present'],
                          row['resolution']), (generation, generation + 1, False, 'superseded_by_navigation'))
        self.assertFalse(driver._in_flight)

    def test_cached_image_reaches_quiet_without_loading_finished(self):
        image = '/cacheable.gif'
        content = b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        normal_get = Handler.do_GET

        def cacheable_asset(handler):
            if handler.path != image:
                return normal_get(handler)
            handler.server.calls.append(('GET', image))
            handler.send_response(200)
            handler.send_header('Content-Type', 'image/gif')
            handler.send_header('Cache-Control', 'public, max-age=3600')
            handler.send_header('Content-Length', str(len(content)))
            handler.end_headers()
            handler.wfile.write(content)

        driver = self.driver
        driver.gate.static_keys.add(image)
        body = b'<img src="/cacheable.gif">'
        for path in ('/warm-cache', '/reuse-cache'):
            self.server.responses[path] = (200, None, body)

        def navigate(path):
            url = self.server.origin + path
            driver.gate.allowed = (url, 'GET')
            self.page.goto(url, wait_until='load')

        with patch.object(Handler, 'do_GET', cacheable_asset):
            navigate('/warm-cache')
            driver._wait_for_quiet(load=True)

            ids, cache_events, suppressed = set(), set(), set()
            driver._cdp.on('Network.requestWillBeSent', lambda event: ids.add(event['requestId'])
                           if event['request']['url'] == self.server.origin + image else None)
            driver._cdp.on('Network.requestServedFromCache', lambda event: cache_events.add(event['requestId']))
            driver._cdp.remove_listener('Network.loadingFinished', driver._network_end)

            def finish(event):
                if event['requestId'] in ids:
                    suppressed.add(event['requestId'])
                else:
                    driver._network_end(event)

            driver._cdp.on('Network.loadingFinished', finish)
            navigate('/reuse-cache')
            driver._wait_for_quiet(load=True)
        self.assertEqual(len(ids), 1)
        self.assertEqual(ids, suppressed)
        self.assertLessEqual(ids, cache_events)
        self.assertEqual(self.server.calls.count(('GET', image)), 1)
        self.assertEqual(driver._network_started, driver._network_finished)

    def test_slow_static_finishes_and_target_quiet_window_precedes_dismissal(self):
        url,image,release=self.slow_target()
        timer=threading.Timer(.25,release.set);timer.start();self.addCleanup(timer.join)
        self.driver._wait_for_quiet(load=True)
        self.assertIn(image,self.server.completed)
        self.assertGreaterEqual(time.monotonic()-self.server.completed[image],self.driver.quiet_window_s)
        self.driver._dismiss_notice(url)
        self.assertFalse(self.page.locator('#myNav').is_visible())
        self.assertEqual(self.driver.gate.request_records,[])

    def test_dismissal_allows_late_registered_image_and_records_only_query_key(self):
        entry=self.page.url
        self.driver.gate.static_keys.add('/revealed.png')
        self.page.set_content('<button>Run the configuration</button>'
                              '<div id="myNav" class="overlay" style="position:fixed;inset:0"></div>'
                              '<script>new MutationObserver(()=>{const image=new Image();'
                              'image.src="/revealed.png?v=private-fixture";document.body.append(image);}).observe('
                              'document.querySelector("#myNav"),{attributes:true});</script>')
        self.driver._dismiss_notice(entry)
        self.assertEqual(self.server.calls,[('GET','/revealed.png?v=private-fixture')])
        self.assertEqual(self.driver.gate.request_records,[{'method':'GET','resource_type':'Image','host':'127.0.0.1',
            'path':'/revealed.png','query_keys':['v'],'decision':'allow_static'}])

    def test_dismissal_wicket_timer_fails_and_preserves_redacted_shape(self):
        entry=self.page.url
        self.page.set_content('<button>Run the configuration</button>'
                              '<div id="myNav" class="overlay" style="position:fixed;inset:0"></div>'
                              '<script>new MutationObserver(()=>setTimeout(()=>{'
                              'const x=new XMLHttpRequest();x.open("GET","/wicket/page?8-1.ILinkListener-run&v=private-fixture");'
                              'x.setRequestHeader("Wicket-Ajax","true");x.send()},10)).observe('
                              'document.querySelector("#myNav"),{attributes:true});</script>')
        error=self.fails(4,self.driver._dismiss_notice,entry)
        record,=[r for r in error.details['request_records'] if r['path']=='/wicket/page']
        self.assertEqual((record['resource_type'].lower(),record['query_keys']),('xhr',['<ILinkListener-run>','v']))
        self.assertEqual(record['decision'],'request_during_notice_dismissal')
        self.assertNotIn('private-fixture',str(error.details))
        self.assertEqual(self.server.calls,[])

    def test_target_that_never_reaches_load_fails_with_inflight_and_pause_counts(self):
        _,_,release=self.slow_target()
        self.driver.quiet_timeout_s=.32
        try:
            error=self.fails(5,self.driver._wait_for_quiet,load=True)
        finally:
            release.set()
        self.assertEqual(error.reason,'target_page_not_quiet')
        self.assertGreater(error.details['in_flight'],0)
        self.assertGreater(error.details['requests_started'],error.details['requests_finished'])
        self.assertIn('pause_counts',error.details)
        self.assertEqual(error.details['wait_phase'], 'load')
        image = next(row for row in error.details['in_flight_requests'] if row['resource_type'] == 'Image')
        self.assertEqual({k: v for k, v in image.items() if k != 'age_s'},
                         {'origin': 'hub', 'method': 'GET', 'resource_type': 'Image',
                          'paused': False, 'decision': 'continued', 'path_shape': '/slow.png?v',
                          'loader': 'current', 'network_events_seen': ['requestWillBeSent'],
                          'generation': self.driver._document_generation, 'current_generation': self.driver._document_generation,
                          'network_id_present': True, 'host_class': 'hub', 'http_status': None, 'from_cache': False})
        self.assertGreaterEqual(image['age_s'], 0)
        self.assertNotIn('fixture-value', str(error.details))

    def test_activity_after_load_times_out_before_run_recording(self):
        entry=self.page.url
        self.page.set_content('<button>Run the configuration</button>')
        self.driver.gate.static_keys.add('/late.png')
        release=threading.Event();self.addCleanup(release.set)
        self.server.holds['/late.png']=release
        self.page.evaluate("""()=>{const image=new Image();image.src='/late.png';document.body.append(image);}""")
        self.driver.quiet_timeout_s=.35
        try:
            error=self.fails(5,self.driver._run_editor,entry,lambda _:self.fail('Run was offered before quiet'))
        finally:
            release.set()
        self.assertEqual(error.reason,'target_page_not_quiet')
        self.assertGreater(error.details['in_flight'],0)
        self.assertEqual(error.details['wait_phase'], 'quiet')
        self.assertTrue(any(row.get('path_shape') == '/late.png' and row['decision'] == 'continued'
                            for row in error.details['in_flight_requests']))
        self.assertFalse(self.driver.gate.capture_run)
        self.assertFalse(self.driver.gate.run_candidates)

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
