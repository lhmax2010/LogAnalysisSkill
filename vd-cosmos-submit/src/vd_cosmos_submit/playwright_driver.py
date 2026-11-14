"""The only optional Playwright adapter. No public page/context escape hatch."""
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core import submit_sessions, submit_flow, submit_model
from vd_cosmos_core.submit_gate import Gate, pattern
from vd_cosmos_core.submit_browser_contract import accepted_location, wire_values, verify_parts
from vd_cosmos_core.files import digest, json_bytes
from .browser_scripts import SCRIPT, DIGEST, arguments


def environment(config,profile):
    # DEBUG can cause protocol traffic to be printed by the driver itself.
    env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('DEBUG','TRACE','HAR','PLAYWRIGHT','PW_'))}
    env['VD_BROWSER_EXECUTABLE']=config.raw['submit']['browser_executable']
    env['VD_BROWSER_OWNER']=str(os.getpid());env['VD_BROWSER_START']=submit_sessions.Processes().identity(os.getpid())
    return env


def settings(config,*,headless=False):
    s=config.raw['submit'];exe=Path(s.get('browser_executable',''))
    if not exe.is_file() or not os.access(exe,os.X_OK):raise FlowError(6,'existing_browser_required')
    if not headless and not os.environ.get('DISPLAY'):raise FlowError(6,'display_required')
    if any(s.get(k) for k in ('record_har_path','record_video_dir','trace','tracing','storage_state','debug','screenshots')):raise FlowError(4,'browser_recording_forbidden')
    return exe


class Driver:
    def __init__(self,config,session,*,headless=False,local_origin=None):
        self.config=config;self.session=session;self.headless=headless;self.local_origin=local_origin
        self._pw=None;self._context=None;self._page=None;self._cdp=None;self.gate=None;self._result=None;self._fatal=None;self._submission_id=None
    def operate(self,args,request,context,confirm,reader_factory):
        self.gate=Gate(self.config,rehearse=args.rehearse,local_origin=self.local_origin)
        try:return submit_flow.execute(self.config,request,self.session,context,self,confirm,reader_factory,rehearse=args.rehearse)
        except FlowError:raise
        except Exception:raise FlowError(5,'browser_operation_failed') from None
    def launch(self,*,rehearse=True):
        settings(self.config,headless=self.headless)
        profile=submit_sessions.profile_path(self.config,self.session)
        profile.mkdir(mode=0o700,parents=True,exist_ok=True);profile.chmod(0o700)
        default=profile/'Default';default.mkdir(mode=0o700,exist_ok=True)
        (default/'Preferences').write_text('{"credentials_enable_service":false,"profile":{"password_manager_enabled":false},"autofill":{"profile_enabled":false,"credit_card_enabled":false}}')
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:raise FlowError(6,'playwright_runtime_missing') from None
        self.gate=self.gate or Gate(self.config,rehearse=rehearse,local_origin=self.local_origin)
        try:
            self._pw=sync_playwright().start()
            wrapper=Path(__file__).resolve().parents[2]/'scripts/browser_child.py'
            self._context=self._pw.chromium.launch_persistent_context(str(profile),executable_path=str(wrapper),headless=self.headless,
                env=environment(self.config,profile),service_workers='block',accept_downloads=False,
                ignore_default_args=['--password-store=basic','--use-mock-keychain'],
                args=['--disable-save-password-bubble','--disable-background-networking','--disable-sync','--disable-default-apps','--disable-quic','--disable-http2','--disable-session-crashed-bubble'])
            self._page=self._context.pages[0] if self._context.pages else self._context.new_page()
            self._context.route('**/*',self._route)
            self._context.route_web_socket('**/*',lambda route:route.close())
            self._context.on('page',lambda page:page.close() if page!=self._page else None)
            self._cdp=self._context.new_cdp_session(self._page)
            self._frame=self._cdp.send('Page.getFrameTree')['frameTree']['frame']['id']
            self._cdp.on('Fetch.requestPaused',self._paused)
            self._cdp.send('Fetch.enable',{'patterns':[{'urlPattern':'*','requestStage':'Request'},{'urlPattern':'*','requestStage':'Response'}]})
        except Exception:
            self.close();raise FlowError(5,'browser_start_failed') from None
    def _route(self,route):
        try:
            if route.request.frame!=self._page.main_frame:route.abort();return
            route.continue_()
        except Exception:
            try:route.abort()
            except Exception:pass
    def _paused(self,event):
        rid=event['requestId'];r=event['request'];url=r['url'];method=r['method'];allow=False
        try:
            if 'responseStatusCode' in event:
                status=event['responseStatusCode']
                location=next((x['value'] for x in event.get('responseHeaders',[]) if x['name'].lower()=='location'),'')
                if self.gate.sent and rid==self._submission_id:
                    self._result='accepted' if status==302 and accepted_location(self.config,url,location) else 'uncertain'
                    allow=False
                else:allow=self.gate.response(url,status,location)
            else:
                business=self.gate.phase=='business';u=urlsplit(url)
                # Authentication values are never accessed. Only the business form endpoint is decoded.
                inspect=business and u.path=='/wicket/page' and u.netloc==urlsplit(self.gate.origin).netloc
                headers={k.lower():v for k,v in r.get('headers',{}).items() if k.lower() in {'content-type','wicket-ajax'}} if inspect else {}
                body=r.get('postData','').encode() if inspect else b''
                allow=self.gate.request(url,method,resource=event.get('resourceType',''),body=body,content_type=headers.get('content-type',''),ajax=headers.get('wicket-ajax','').lower()=='true',main_frame=event.get('frameId')==self._frame)
                if allow and self.gate.sent and self._submission_id is None:self._submission_id=rid
            self._cdp.send('Fetch.continueRequest' if allow else 'Fetch.failRequest',{'requestId':rid} if allow else {'requestId':rid,'errorReason':'BlockedByClient'})
        except Exception:
            self._fatal='request_gate_failed'
            try:self._cdp.send('Fetch.failRequest',{'requestId':rid,'errorReason':'BlockedByClient'})
            except Exception:pass
    def _check(self):
        if self._fatal or self.gate.fatal:raise FlowError(4,self._fatal or self.gate.fatal)
        u=urlsplit(self._page.url)
        if self.gate.phase!='business' or u.scheme+'://'+u.netloc!=self.gate.origin or u.path!='/wicket/page' or not u.query.isdecimal():raise FlowError(4,'business_page_required')
    def open(self,expose,confirm):
        self.launch();expose()
        entry=self.gate.origin+'/overview/'+self.config.raw['submit']['target_config_id'];self.gate.navigation(entry)
        try:self._page.goto(entry,wait_until='domcontentloaded')
        except Exception:
            if self._fatal:raise FlowError(5,self._fatal) from None
        deadline=time.monotonic()+self.config.raw['submit']['login_wait_s']
        while self.gate.phase!='business':
            if time.monotonic()>deadline:raise FlowError(3,'login_wait_expired')
            self._page.wait_for_timeout(100)
        # Run is intentionally recorded with no permission, then separately confirmed.
        self._window('minimized')
        try:self._page.get_by_text('Run the configuration',exact=True).click(timeout=5000)
        except Exception:pass
        records=[x for x in self.gate.records if x.get('listener')=='ILinkListener' and x.get('classification')=='callback_candidate']
        if len(records)!=1:raise FlowError(4,'run_pattern_unregistered')
        candidate={k:records[0][k] for k in ('method','path','listener','behavior','component')}
        if candidate['method']!='GET' or confirm({'run_pattern':candidate,'confirm':'allow-run'})!='allow-run':raise FlowError(3,'run_confirmation_required')
        self.gate.action(candidate)
        try:self._page.get_by_text('Run the configuration',exact=True).click(timeout=5000)
        except Exception:raise FlowError(5,'run_navigation_failed') from None
        self._check()
    def _window(self,state):
        # Fixed window-only CDP calls; no runtime evaluation/network data extraction.
        info=self._cdp.send('Browser.getWindowForTarget')
        self._cdp.send('Browser.setWindowBounds',{'windowId':info['windowId'],'bounds':{'windowState':state}})
    def _script(self,operation,**kw):
        self._check();args=arguments(operation,target=self.config.raw['submit']['target_config'],**kw)
        if digest(SCRIPT.encode())!=DIGEST:raise FlowError(4,'fixed_script_digest_changed')
        try:value=self._page.evaluate(SCRIPT,args)
        except Exception:raise FlowError(5,'fixed_script_failed') from None
        submit_model.ensure_safe(self.config,value);return value
    def snapshot(self):return self._script('snapshot')
    def fill(self,index,value):
        snap=self.snapshot();c=snap['controls'][index]
        self.gate.filling=('form-'+c['name'].replace(':','-'),c['name'],value.replace('\r\n','\n').replace('\n','\r\n'));self.gate.callback_count=0
        try:
            self._script('fill',index=index,value=value);self._page.wait_for_timeout(100)
            if self.gate.fatal:raise FlowError(4,self.gate.fatal)
        finally:self.gate.filling=None
    def serialize_check(self,snapshot,form,*,rehearse):
        pairs=self._script('serialize')
        if len(dict(pairs))!=len(pairs):raise FlowError(4,'submit_parts_invalid')
        try:expected=wire_values(self.config,snapshot,form,rehearsal=rehearse)
        except FlowError as e:
            if not rehearse:raise
            # No automatic registration. Record only digests, never guess encoding.
            return {'verified':False,'reason':e.reason,'parts':[{'name':k,'length':len(v),'sha256':digest(v.encode())} for k,v in pairs]}
        return {'verified':True,'parts':verify_parts(self.config,dict(pairs),expected,snapshot['hidden'],rehearsal=rehearse)}
    def records(self):return self.gate.records
    def release(self,expected,hidden):
        self._check();self.gate.arm(expected,hidden,intent_recorded=True)
        try:self._page.get_by_role('button',name='Ok',exact=True).click(timeout=10000)
        except Exception:pass
        deadline=time.monotonic()+15
        while not self._result and not self.gate.fatal and time.monotonic()<deadline:self._page.wait_for_timeout(50)
        return 'blocked_before_send' if self.gate.fatal=='blocked_before_send' else self._result or 'uncertain'
    def close(self):
        try:
            if self._context:self._context.close()
        except Exception:raise FlowError(6,'browser_cleanup_unverified') from None
        finally:
            self._context=None
            if self._pw:
                try:self._pw.stop()
                except Exception:pass
                self._pw=None
