"""The only optional Playwright adapter. No public page/context escape hatch."""
# Callback rule: never call a sync Playwright method from a registered callback.
# WebSockets remain unconnected. Other callbacks schedule coroutine work on the
# adapter's existing loop and return immediately; only the main flow may wait.
import asyncio
from dataclasses import dataclass
import inspect
import os
import re
from pathlib import Path
import time
from urllib.parse import urlsplit
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core import submit_sessions, submit_flow, submit_model, browser_temp
from vd_cosmos_core.export import check_content
from vd_cosmos_core.submit_gate import Gate, address, request_evidence, static_key
from vd_cosmos_core.submit_browser_contract import accepted_location, wire_values, verify_parts
from vd_cosmos_core.submit_terminal import confirmation_error
from vd_cosmos_core.files import digest, json_bytes
from .browser_scripts import SCRIPT, DIGEST, arguments


POPUP_SANDBOX = 'sandbox allow-scripts allow-forms allow-same-origin'
POPUP_GUARD = """(() => {
    const opensWindow = target => !["", "_self", "_top", "_parent"].includes((target || "").toLowerCase());
    const baseTarget = () => document.querySelector("base[target]")?.target;
    Object.defineProperty(window, "open", {
        value: () => null, configurable: false, writable: false
    });
    const preventNewWindow = event => {
        const target = event.composedPath().find(node => node instanceof HTMLAnchorElement
            || node instanceof HTMLAreaElement);
        if (target && (opensWindow(target.target || baseTarget())
            || event.ctrlKey || event.metaKey || event.shiftKey || event.button === 1)) {
            event.preventDefault();
        }
    };
    window.addEventListener("click", preventNewWindow, true);
    window.addEventListener("auxclick", preventNewWindow, true);
    window.addEventListener("submit", event => {
        if (opensWindow(event.submitter?.formTarget || event.target.target || baseTarget())) {
            event.preventDefault();
        }
    }, true);
})();"""


def environment(config,profile,temp_dir=None):
    # DEBUG can cause protocol traffic to be printed by the driver itself.
    env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('DEBUG','TRACE','HAR','PLAYWRIGHT','PW_'))}
    env['VD_BROWSER_EXECUTABLE']=config.raw['submit']['browser_executable']
    env['VD_BROWSER_OWNER']=str(os.getpid());env['VD_BROWSER_START']=submit_sessions.Processes().identity(os.getpid())
    if temp_dir is not None:
        env.update(TMPDIR=str(temp_dir), TMP=str(temp_dir), TEMP=str(temp_dir))
    return env


def settings(config,*,headless=False):
    s=config.raw['submit'];exe=Path(s.get('browser_executable',''))
    if not exe.is_file() or not os.access(exe,os.X_OK):raise FlowError(6,'existing_browser_required')
    if not headless and not os.environ.get('DISPLAY'):raise FlowError(6,'display_required')
    if any(s.get(k) for k in ('record_har_path','record_video_dir','trace','tracing','storage_state','debug','screenshots')):raise FlowError(4,'browser_recording_forbidden')
    return exe


def launch_diagnostic(config, error, stage):
    """Pre-navigation errors only; check the whole message before truncation."""
    kind=type(error).__name__
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}',kind):kind='Exception'
    try:
        message=str(error)
        allowed=check_content(message.encode('utf-8'),config)['allowed']
        if not check_content(kind.encode('utf-8'),config)['allowed']:kind='Exception'
        if re.search(r'(?i)(?:password|passwd|token|secret|authorization)\s*[=:]',message):allowed=False
        # Even unregistered query parameters and cookie diagnostics are withheld.
        if re.search(r'(?i)\bcookies?\b|(?:https?|wss?)://[^\s<>]+[?#]|["\'](?:profile|credentials_enable_service)["\']\s*:',message):allowed=False
        detail='\n'.join(line[:600] for line in message.splitlines()[:3]) if allowed else 'detail withheld'
        if not check_content(detail.encode('utf-8'),config)['allowed']:detail='detail withheld'
    except Exception:
        detail='detail withheld'
    return {'exception_type':kind,'stage':stage,'detail':detail}


@dataclass
class Pause:
    owner: object
    stage: str
    request_id: object
    shape: dict
    deadline: float
    evidence: dict
    timer: object = None
    task: object = None
    timeline: dict = None
    started: bool = False
    reported: bool = False
    teardown: bool = False


class Driver:
    pause_timeout_s = 10
    quiet_window_s = 1.5
    quiet_timeout_s = 30

    def __init__(self,config,session,*,headless=False,local_origin=None):
        self.config=config;self.session=session;self.headless=headless;self.local_origin=local_origin
        self._pw=None;self._context=None;self._browser=None;self._targets=None;self._page=None;self._cdp=None;self.gate=None;self._result=None;self._fatal=None;self._submission_id=None
        self._pauses={};self._seen_pauses=set();self._paused_count=0;self._resolved_count=0;self._forced_closed=0
        self._pause_fault=False;self._closing=False;self._tearing_down=False;self._emergency_close=False;self._cancelled_on_close=0
        self._deferred=set();self._pause_timeline=[];self._response_redirects=set()
        self._in_flight=set();self._network_started=0;self._network_finished=0
        self._last_activity=time.monotonic()
    def operate(self,args,request,context,confirm,reader_factory):
        self.gate=Gate(self.config,rehearse=args.rehearse,local_origin=self.local_origin)
        try:
            result=submit_flow.execute(self.config,request,self.session,context,self,confirm,reader_factory,rehearse=args.rehearse)
            self._check_pause_fault()
            return dict(result,**self._operation_evidence())
        except FlowError as error:
            self._check_pause_fault()
            raise FlowError(error.code,error.reason,**{**error.details,**self._operation_evidence()}) from None
        except Exception:
            self._check_pause_fault()
            raise FlowError(5,'browser_operation_failed',**self._operation_evidence()) from None
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
        temp_dir=browser_temp.create(profile)
        stage='start'
        try:
            self._pw=sync_playwright().start()
            wrapper=Path(__file__).resolve().parents[2]/'scripts/browser_child.py'
            stage='launch'
            self._browser=self._pw.chromium.launch(executable_path=str(wrapper),headless=self.headless,chromium_sandbox=True,
                env={**environment(self.config,profile,temp_dir),'VD_BROWSER_PROFILE':str(profile)},
                ignore_default_args=['--password-store=basic','--use-mock-keychain'],
                args=['--disable-save-password-bubble','--disable-background-networking','--disable-sync','--disable-default-apps','--disable-quic','--disable-http2','--disable-session-crashed-bubble'])
            self._context=self._browser.new_context(service_workers='block',accept_downloads=False)
            self._context.add_init_script(script=POPUP_GUARD)
            stage='new_page'
            self._page=self._context.pages[0] if self._context.pages else self._context.new_page()
            self._page.on('request',self._request_started)
            self._page.on('requestfinished',self._request_finished)
            self._page.on('requestfailed',self._request_finished)
            stage='route'
            self._context.route_web_socket('**/*',self._websocket)
            self._context.on('page',self._new_page)
            stage='cdp'
            self._cdp=self._context.new_cdp_session(self._page)
            self._frame=self._cdp.send('Page.getFrameTree')['frameTree']['frame']['id']
            self._target_id=self._cdp.send('Target.getTargetInfo')['targetInfo']['targetId']
            self._cdp.on('Fetch.requestPaused',self._paused)
            self._targets=self._browser.new_browser_cdp_session()
            self._targets.on('Target.attachedToTarget',self._attached_target)
            self._targets.send('Target.setAutoAttach',{'autoAttach':True,'waitForDebuggerOnStart':True,
                'flatten':True,'filter':[{'type':'page'}]})
            stage='fetch_enable'
            self._cdp.send('Fetch.enable',{'patterns':[{'urlPattern':'*','requestStage':'Request'}]})
        except Exception as error:
            details=launch_diagnostic(self.config,error,stage)
            try:self.close()
            except FlowError:details['cleanup']='unverified; recovery required'
            if stage=='launch' and re.search(r'(?i)sandbox|zygote_host_impl_linux|operation not permitted.*user.?namespace',str(error)):
                raise FlowError(6,'browser_sandbox_unavailable',**details) from None
            raise FlowError(5,'browser_start_failed',**details) from None
    def _defer(self, owner, method, *args, pause=None, continuing=False):
        """One guarded bridge to Playwright's coroutine implementation, no _sync.

        The sync facade has no public non-waiting send. Fail closed if the
        installed adapter lacks this bridge; never fall back to a blocking call.
        """
        coroutine=None
        try:
            if method not in {'close','send'}:raise ValueError()
            impl=owner._impl_obj;function=getattr(impl,method)
            if not inspect.iscoroutinefunction(function) or not impl._loop.is_running():raise ValueError()
            coroutine=function(*args) if pause is None else self._dispatch_pause(pause,function,args,continuing)
            task=impl._loop.create_task(coroutine)
            self._deferred.add(task)
            if pause is None:
                task.add_done_callback(self._deferred_done)
            else:
                pause.timeline['decision_at']=time.monotonic()
                pause.task=task
                task.add_done_callback(lambda done:self._pause_done(pause,done))
        except Exception:
            if coroutine is not None:coroutine.close()
            if pause is None:self._fatal='browser_callback_dispatch_failed'
            elif continuing:self._expire_pause(pause)
            else:self._lose_pause(pause)
    def _deferred_done(self,task):
        self._deferred.discard(task)
        if task.cancelled():return
        if task.exception() is not None and not self._closing:self._fatal='browser_callback_dispatch_failed'
    def pause_counts(self):
        return {'paused':self._paused_count,'resolved':self._resolved_count,
                'pending':len(self._pauses),'closed_unconfirmed':self._forced_closed,
                'cancelled_on_close':self._cancelled_on_close}
    def _operation_evidence(self):
        details={'pause_counts':self.pause_counts(),'pause_timeline':self._pause_timeline}
        if self.gate is not None:
            if self.gate.request_records:details['request_records']=self.gate.request_records
            for record in reversed(self.gate.records):
                if 'account_check' in record:
                    details['account_check']=record['account_check']
                    break
        return details
    def _check_pause_fault(self):
        if self._pause_fault:
            raise FlowError(4,'paused_request_unresolved',**self._operation_evidence(),
                            gate_records=self.gate.records if self.gate is not None else [])
    def _url_shape(self,url):
        u=urlsplit(url)
        hub=self.gate is not None and self.gate.is_hub(u)
        path='unregistered'
        if hub:
            if u.path in {'/','/dashboard','/signin','/sso-initiate','/sso-login','/wicket/page'}:path=u.path
            elif re.fullmatch(r'/overview/[0-9]+',u.path):path='/overview/<id>'
            elif static_key(u.path) in self.gate.static_keys:path='registered_static'
        return {'scheme':u.scheme if u.scheme in {'http','https'} else 'other','origin':'hub' if hub else 'other',
                'path':path,'has_query':bool(u.query)}
    def _request_started(self,request):
        key=id(request._impl_obj)
        if key not in self._in_flight:
            self._in_flight.add(key)
            self._network_started+=1
            self._last_activity=time.monotonic()
    def _request_finished(self,request):
        key=id(request._impl_obj)
        if key in self._in_flight:
            self._in_flight.remove(key)
            self._network_finished+=1
            self._last_activity=time.monotonic()
    def _begin_pause(self,owner,stage,request_id,url,method='GET',resource='Other'):
        key=(stage,request_id)
        if key in self._seen_pauses:
            return None
        self._seen_pauses.add(key)
        loop=asyncio.get_running_loop()
        try:shape=self._url_shape(url)
        except (TypeError,ValueError):shape={'path':'unrecognized'}
        pause=Pause(owner,stage,request_id,shape,loop.time()+self.pause_timeout_s,
                    request_evidence(url,method,resource,'paused_request_unresolved'),teardown=self._tearing_down)
        label=shape['path']
        if label=='registered_static':
            label=pause.evidence['path']
        pause.timeline={'paused_at':time.monotonic(),'decision_at':None,'sent_at':None,
                        'acked_at':None,'stage':stage,'path':label,'origin':shape.get('origin','other'),
                        'method':pause.evidence['method'],'resource_type':pause.evidence['resource_type']}
        self._pause_timeline.append(pause.timeline)
        self._last_activity=time.monotonic()
        self._paused_count+=1
        self._pauses[key]=pause
        pause.timer=loop.call_at(pause.deadline,self._expire_pause,pause)
        return pause
    async def _dispatch_pause(self,pause,function,args,continuing):
        if continuing:
            if asyncio.get_running_loop().time()>=pause.deadline:
                self._expire_pause(pause)
                return
            if self._pause_fault or self._closing:
                self._fail_pause(pause)
                return
        pause.started=True
        pause.timeline.update(sent_at=time.monotonic(), command=args[0])
        await function(*args)
        pause.timeline['acked_at']=time.monotonic()
    def _forget_pause(self,pause):
        self._pauses.pop((pause.stage,pause.request_id))
        pause.timer.cancel()
        self._last_activity=time.monotonic()
    def _resolve_pause(self,pause,*,cancelled_on_close=False):
        self._forget_pause(pause)
        self._resolved_count+=1
        if cancelled_on_close:self._cancelled_on_close+=1
    def _pause_done(self,pause,task):
        self._deferred.discard(task)
        error=None if task.cancelled() else task.exception()
        if self._pauses.get((pause.stage,pause.request_id)) is not pause or pause.task is not task:
            return
        if task.cancelled():
            self._lose_pause(pause)
        elif error:
            if pause.teardown and type(error).__name__=='TargetClosedError':
                self._resolve_pause(pause,cancelled_on_close=True)
            else:
                self._lose_pause(pause)
        else:
            self._resolve_pause(pause)
    def _report_pause(self,pause):
        self._pause_fault=True
        self._fatal='paused_request_unresolved'
        if not pause.reported and self.gate is not None:
            self.gate.records.append({'reason':'paused_request_unresolved','stage':pause.stage,'url_shape':pause.shape})
            self.gate.request_records.append(pause.evidence)
        pause.reported=True
    def _fail_pause(self,pause):
        self._defer(pause.owner,'send','Fetch.failRequest',{'requestId':pause.request_id,'errorReason':'BlockedByClient'},pause=pause)
    def _expire_pause(self,pause):
        if self._pauses.get((pause.stage,pause.request_id)) is not pause:return
        if pause.task is not None and pause.task.done() and not pause.task.cancelled():
            self._pause_done(pause,pause.task)
            return
        self._report_pause(pause)
        if pause.started or self._emergency_close:
            self._lose_pause(pause)
            return
        if pause.task is not None and pause.task is not asyncio.current_task():pause.task.cancel()
        pause.timer.cancel()
        loop=asyncio.get_running_loop()
        pause.timer=loop.call_later(self.pause_timeout_s,self._lose_pause,pause)
        self._fail_pause(pause)
    def _lose_pause(self,pause):
        if self._pauses.get((pause.stage,pause.request_id)) is not pause:return
        self._report_pause(pause)
        self._forget_pause(pause)
        self._forced_closed+=1
        if pause.task is not None and not pause.task.done() and not pause.task.get_loop().is_closed():pause.task.cancel()
        # An acknowledgement can be lost after delivery. The main flow
        # closes the context rather than issuing another decision on this ID.
        self._emergency_close=True
    def _websocket(self,route):
        # Not connecting is the mock/block operation.
        if self.gate is not None and self.gate.dismissing:
            self.gate.reject_dismissal(route.url,'GET','WebSocket')
    def _new_page(self,page):
        if page!=self._page:self._defer(page,'close')
    def _attached_target(self,event):
        # Related targets are paused before executing page/worker code. Keep
        # them fail-closed, including their initial network request.
        target=event['targetInfo']
        if target['type']=='page' and target['targetId']!=self._target_id:
            self._defer(self._targets,'send','Target.closeTarget',{'targetId':target['targetId']})
    def _paused(self,event):
        rid=event['requestId'];r=event.get('request',{});url=r.get('url','');allow=False;blocked='BlockedByClient'
        response_stage='responseStatusCode' in event or 'responseErrorReason' in event
        resource=event.get('resourceType','Other')
        pause=self._begin_pause(self._cdp,'fetch_response' if response_stage else 'fetch_request',rid,url,r.get('method',''),resource)
        if pause is None:return
        try:
            if self._pause_fault or self._closing:
                if self.gate.dismissing and not response_stage:
                    self.gate.record_request(url,r.get('method',''),resource,'gate_closed')
                self._fail_pause(pause);return
            if 'responseErrorReason' in event:
                self._fail_pause(pause);return
            method=r['method']
            previous=event.get('redirectedRequestId')
            if previous and previous not in self._response_redirects and not response_stage:
                if self.gate.dismissing:self.gate.reject_dismissal(url,method,resource)
                self._fail_pause(pause);return
            if previous and not response_stage:self._response_redirects.discard(previous)
            if response_stage:
                status=event['responseStatusCode']
                location=next((x['value'] for x in event.get('responseHeaders',[]) if x['name'].lower()=='location'),'')
                if self.gate.sent and rid==self._submission_id:
                    self._result='accepted' if status==302 and accepted_location(self.config,url,location) else 'uncertain'
                    allow=False
                else:allow=self.gate.response(url,status,location,main_document=event.get('frameId')==self._frame and resource=='Document',method=method,resource=resource)
                if allow and status in {301,302,303,307,308}:self._response_redirects.add(rid)
            elif self.gate.dismissing:
                ajax=any(k.lower()=='wicket-ajax' for k in r.get('headers',{}))
                allow=self.gate.request(url,method,resource=resource,ajax=ajax,main_frame=event.get('frameId')==self._frame)
            else:
                business=self.gate.phase=='business';u=urlsplit(url)
                # Authentication values are never accessed. Only the business form endpoint is decoded.
                inspect=business and u.path=='/wicket/page' and u.netloc==urlsplit(self.gate.origin).netloc
                headers={k.lower():v for k,v in r.get('headers',{}).items() if k.lower() in {'content-type','wicket-ajax'}} if inspect else {}
                run_ajax=business and self.gate.is_hub(u) and u.path==self.gate.overview and any(
                    k.lower()=='wicket-ajax' for k in r.get('headers',{}))
                body=r.get('postData','').encode() if inspect else b''
                captured=len(self.gate.run_candidates)
                allow=self.gate.request(url,method,resource=event.get('resourceType',''),body=body,content_type=headers.get('content-type',''),ajax=run_ajax or headers.get('wicket-ajax','').lower()=='true',main_frame=event.get('frameId')==self._frame)
                if len(self.gate.run_candidates)>captured:blocked='Aborted'
                if allow and self.gate.sent and self._submission_id is None:self._submission_id=rid
            if not allow:
                self._defer(self._cdp,'send','Fetch.failRequest',
                            {'requestId':rid,'errorReason':blocked},pause=pause)
            elif response_stage:
                options={'requestId':rid}
                if (event['responseStatusCode']==200 and resource=='Document'
                        and event.get('frameId')==self._frame):
                    # Chrome enforces this even if a popup would start its first
                    # navigation before the target attachment notification.
                    # Return original headers unchanged. No values are logged.
                    headers=[*event.get('responseHeaders',[]),
                        {'name':'Content-Security-Policy','value':POPUP_SANDBOX}]
                    options.update(responseCode=200,responsePhrase=event.get('responseStatusText') or 'OK',
                                   responseHeaders=headers)
                self._defer(self._cdp,'send','Fetch.continueResponse',options,pause=pause,continuing=True)
            else:
                options={'requestId':rid}
                if resource=='Document' or rid==self._submission_id:
                    options['interceptResponse']=True
                self._defer(self._cdp,'send','Fetch.continueRequest',options,pause=pause,continuing=True)
        except Exception:
            self._fatal='request_gate_failed'
            self.gate.record_request(url,r.get('method',''),resource,self._fatal)
            self._fail_pause(pause)
    def _check_gate(self):
        self._check_pause_fault()
        if self._fatal or self.gate.fatal:
            raise FlowError(4,self._fatal or self.gate.fatal,**self._operation_evidence())
    def _check(self):
        self._check_gate()
        self._check_manual_login()
        u=urlsplit(self._page.url)
        if self.gate.phase!='business' or u.scheme+'://'+u.netloc!=self.gate.origin or u.path!='/wicket/page' or not u.query.isdecimal():raise FlowError(4,'business_page_required')
    def open(self,expose,confirm):
        self.launch();expose()
        dashboard=self.gate.origin+'/dashboard';start=self.gate.origin+'/'
        self.gate.navigation(start,login_entry=True)
        try:self._page.goto(start,wait_until='domcontentloaded')
        except Exception:
            self._check_manual_login()
            if self._fatal:raise FlowError(5,self._fatal) from None
        deadline=time.monotonic()+self.config.raw['submit']['login_wait_s']
        while self.gate.phase!='account' or self._page.url!=dashboard:
            self._check_manual_login()
            if self._fatal or self.gate.fatal:raise FlowError(4,self._fatal or self.gate.fatal)
            if time.monotonic()>deadline:raise FlowError(3,'login_wait_expired')
            self._page.wait_for_timeout(100)
        self._page.wait_for_load_state('domcontentloaded')
        self._check_manual_login()
        self._check_account(dashboard)
        self.gate.verify_account()
        entry=self.gate.origin+'/overview/'+self.config.raw['submit']['target_config_id'];self.gate.navigation(entry)
        try:self._page.goto(entry,wait_until='domcontentloaded')
        except Exception:
            self._check_manual_login()
            raise FlowError(5,'target_navigation_failed') from None
        if self._page.url!=entry or self.gate.phase!='business':raise FlowError(5,'target_navigation_failed')
        self._wait_for_quiet(load=True)
        self._dismiss_notice(entry)
        self._run_editor(entry,confirm)
        self._check()
    def _manual_login_error(self):
        return FlowError(3,'hub_manual_login_page',todo={'reason':'hub_manual_login_page',
                        'message':'log in through SSO only; restart'})
    def _check_manual_login(self):
        url=self._page.url
        u=urlsplit(url)
        if self.gate.manual_login or self.gate.manual_url(u):raise self._manual_login_error()
        if self.gate.is_hub(u):
            try:probe=self._fixed_script('login_probe')
            except FlowError as err:
                # During auth, the document may be replaced as the probe runs.
                if err.reason=='fixed_script_failed' and self.gate.phase=='auth':return
                raise
            if probe['manual_login']:raise self._manual_login_error()
    def _run_position(self,entry,operation='run_position'):
        self._check_manual_login()
        self._check_gate()
        if self._page.url!=entry:raise FlowError(5,'target_navigation_failed')
        position=self._fixed_script(operation)
        if not position['clear']:raise FlowError(4,'run_button_obscured')
        return position['x'],position['y']
    def _wait_for_quiet(self,*,load=False):
        """Require a quiet window after load, counting network work between Fetch pauses."""
        start=time.monotonic()
        deadline=start+self.quiet_timeout_s
        def not_quiet():
            return FlowError(5,'target_page_not_quiet',**self._operation_evidence(),
                             in_flight=len(self._in_flight),requests_started=self._network_started,
                             requests_finished=self._network_finished)
        self._check_gate()
        try:
            if load:
                self._page.wait_for_load_state('load',timeout=max(1,int((deadline-time.monotonic())*1000)))
                start=time.monotonic()
            while True:
                self._check_gate()
                now=time.monotonic()
                if now>=deadline:raise not_quiet()
                if not self._in_flight and not self._pauses and now-max(start,self._last_activity)>=self.quiet_window_s:
                    return
                self._page.wait_for_timeout(min(50,max(1,int((deadline-now)*1000))))
        except FlowError:raise
        except Exception:
            self._check_gate()
            raise not_quiet() from None
    def _dismiss_notice(self,entry):
        self.gate.dismissing=True
        try:
            self._run_position(entry,'dismiss_notice')
            self._wait_for_quiet()
        finally:self.gate.dismissing=False
    def _run_editor(self,entry,confirm):
        # The first click is observed but never sent. Permission is for the exact GET only.
        self._wait_for_quiet(load=True)
        self._window('minimized')
        self.gate.capture_run=True
        try:
            self._page.mouse.click(*self._run_position(entry))
            deadline=time.monotonic()+5
            while not self.gate.run_candidates and not (self._fatal or self.gate.fatal) and time.monotonic()<deadline:
                self._page.wait_for_timeout(20)
        finally:self.gate.capture_run=False
        self._check_gate()
        if len(self.gate.run_candidates)!=1:raise FlowError(4,'run_pattern_unregistered')
        candidate={'method':'GET','path':self.gate.overview,'listener':'ILinkListener','behavior':None,'component':'run'}
        if confirm({'confirmation':'run','target':submit_model.target(self.config),'run_pattern':candidate,'confirm':'allow-run'})!='allow-run':
            raise confirmation_error('run','allow-run')
        position=self._run_position(entry)
        self.gate.allow_run(self.gate.run_candidates[0])
        self._page.mouse.click(*position)
        try:self._page.wait_for_url(re.compile(re.escape(self.gate.origin)+r'/wicket/page\?[0-9]+$'),timeout=5000)
        except Exception:
            self._check_manual_login()
            raise FlowError(5,'run_navigation_failed') from None
    def _window(self,state):
        # Fixed window-only CDP calls; no runtime evaluation/network data extraction.
        info=self._cdp.send('Browser.getWindowForTarget')
        self._cdp.send('Browser.setWindowBounds',{'windowId':info['windowId'],'bounds':{'windowState':state}})
    def _check_account(self, dashboard):
        account=self.config.raw['submit']['account']
        unmatched={'matched':False,'element':None,'container':None}
        evidence=unmatched
        if self.gate.phase=='account' and self._page.url==dashboard and not (self._fatal or self.gate.fatal):
            evidence=self._fixed_script('account',account=account)
            if evidence.get('password_present'):raise self._manual_login_error()
            if self._page.url!=dashboard:evidence=unmatched
        self.gate.records.append({'account_check':evidence})
        if not evidence['matched']:
            raise FlowError(3,'hub_account_mismatch',account_check=evidence,
                            todo={'reason':'hub_account_mismatch','message':f'log in as {account} or change submit.account'})
    def _fixed_script(self,operation,**kw):
        args=arguments(operation,target=self.config.raw['submit']['target_config'],**kw)
        if digest(SCRIPT.encode())!=DIGEST:raise FlowError(4,'fixed_script_digest_changed')
        try:value=self._page.evaluate(SCRIPT,args)
        except Exception:raise FlowError(5,'fixed_script_failed') from None
        submit_model.ensure_safe(self.config,value);return value
    def _script(self,operation,**kw):
        self._check();value=self._fixed_script(operation,**kw)
        if isinstance(value,dict) and value.get('form_unrecognized'):
            raise FlowError(5,'form_unrecognized',breadcrumb_segments=value['breadcrumb_segments'])
        if isinstance(value,dict) and value.get('password_present'):raise self._manual_login_error()
        return value
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
        while not self._result and not self.gate.fatal and not self._pause_fault and time.monotonic()<deadline:self._page.wait_for_timeout(50)
        self._check_pause_fault()
        return 'blocked_before_send' if self.gate.fatal=='blocked_before_send' else self._result or 'uncertain'
    async def _join_deferred(self):
        tasks=tuple(self._deferred)
        if tasks:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)

    def close(self):
        failed=False
        self._closing=True
        try:
            deadline=time.monotonic()+2*self.pause_timeout_s
            while self._deferred and self._page is not None and time.monotonic()<deadline:
                try:self._page.wait_for_timeout(20)
                except Exception:break
            self._tearing_down=True
            if self._context:
                if self._deferred:self._context._sync(self._join_deferred())
                self._context.close()
                if self._deferred:self._context._sync(self._join_deferred())
        except Exception:
            failed=True
        finally:
            self._context=None
            if self._browser:
                try:self._browser.close()
                except Exception:failed=True
                self._browser=None
            if self._pw:
                try:self._pw.stop()
                except Exception:failed=True
                self._pw=None
            for pause in tuple(self._pauses.values()):
                if not failed and pause.teardown:self._resolve_pause(pause,cancelled_on_close=True)
                else:self._lose_pause(pause)
        profile=submit_sessions.profile_path(self.config,self.session)
        # Process identity/shutdown must be checked before deleting socket files.
        submit_sessions.Processes().close(profile)
        browser_temp.cleanup(profile)
        if failed:raise FlowError(6,'browser_cleanup_unverified')
