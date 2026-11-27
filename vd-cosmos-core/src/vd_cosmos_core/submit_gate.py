"""Deny-by-default request gate; transport supplies EVERY redirect hop."""
import re
import threading
from urllib.parse import urlsplit, parse_qsl, unquote, unquote_plus, urljoin
from .errors import FlowError
from .submit_browser_contract import multipart, verify_parts

WICKET=re.compile(r'^[0-9]+-[0-9]+\.(IFormSubmitListener|ILinkListener|IBehaviorListener)(?:\.([0-9]+))?-([A-Za-z0-9_-]+)$')
WICKET_PREFIX=re.compile(r'^(?:[0-9]+-[0-9]+\.)?I[A-Za-z]+Listener\b')
RUN_QUERY=re.compile(r'[0-9]+-1\.ILinkListener-run')
STATIC_QUERY=re.compile(r'(?:v=[A-Za-z0-9._-]{1,64}|[0-9a-f]{32})')
STATIC_RESOURCES={'script','stylesheet','image','font'}

def request_evidence(url,method,resource,decision):
    """Record only URL fields and query-key shapes, never values or userinfo."""
    host=path=None
    keys=[]
    try:
        u=urlsplit(url)
        host,path=u.hostname,u.path[:512]
        for part in u.query.split('&'):
            if not part:continue
            key,marker,_=part.partition('=')
            key=unquote_plus(key)
            listener=WICKET.fullmatch(key)
            if listener:
                keys.append('<'+listener[1]+'-'+listener[3][:96]+'>')
            elif WICKET_PREFIX.match(key):
                keys.append('<wicket-listener>')
            elif marker and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,63}',key):
                keys.append(key)
            elif key in {'manual-login','redirect-url-after-sign-in'}:
                keys.append(key)
            else:
                keys.append('<bare-hex>' if re.fullmatch(r'[0-9a-f]{32}',key) else '<unrecognized-key>')
    except (TypeError,ValueError):
        pass
    return {'method':method if isinstance(method,str) and re.fullmatch(r'[A-Z]{1,16}',method) else 'other',
            'resource_type':resource if isinstance(resource,str) and re.fullmatch(r'[A-Za-z]{1,32}',resource) else 'Other',
            'host':host,'path':path,'query_keys':keys,'decision':decision}

def static_key(path):
    return re.sub(r'-ver-[0-9]+', '-ver-*', path)

def address(url):
    u=urlsplit(url)
    if u.username or u.password or u.fragment or u.scheme not in ('https','http'):raise FlowError(4,'unregistered_address')
    return u

def pattern(url,method):
    u=address(url);m=WICKET.fullmatch(u.query)
    if u.path!='/wicket/page' or not m:raise FlowError(4,'unregistered_listener')
    return {'method':method,'path':u.path,'listener':m[1],'behavior':m[2],'component':m[3]}

class Gate:
    def __init__(self,config,*,rehearse,local_origin=None):
        self.config=config;self.s=config.raw['submit'];self.origin=local_origin or 'https://'+config.raw['cosmos']['hub_host'];self.rehearse=rehearse
        if local_origin and not re.fullmatch(r'http://127\.0\.0\.1:[0-9]+',local_origin):raise FlowError(4,'local_origin_required')
        self.phase='auth';self.recording=not self.s.get('gate_patterns_confirmed',False);self.allowed=None;self.filling=None;self.callback_count=0;self.submission=None;self.sent=False;self.records=[];self.fatal=None;self.mutex=threading.RLock();self.auth_return=False;self.run_redirect=False;self.run_response=None
        self.auth_entry='/overview/'+self.s['target_config_id']
        self.overview='/overview/'+self.s['target_config_id']
        self.static_keys={static_key(path) for path in self.s.get('static_paths',[])}
        self.manual_login=False;self.dismissing=False;self.request_records=[]
        self.capture_run=False;self.run_candidates=[]
    def is_hub(self,u):
        return u.scheme+'://'+u.netloc==self.origin
    def manual_url(self,u):
        return self.is_hub(u) and u.path=='/signin' and any(
            key=='manual-login' for key,_ in parse_qsl(u.query,keep_blank_values=True))
    def auth_wicket(self,u):
        return self.is_hub(u) and bool(WICKET_PREFIX.match(unquote(u.query)))
    def static_allowed(self,u,method,resource,*,ajax=False):
        return (method=='GET' and resource.lower() in STATIC_RESOURCES and self.is_hub(u) and not ajax
                and (not u.query or STATIC_QUERY.fullmatch(u.query)) and static_key(u.path) in self.static_keys)
    def record_request(self,url,method,resource,decision):
        self.request_records.append(request_evidence(url,method,resource,decision))
    def reject_dismissal(self,url,method,resource):
        self.fatal=self.fatal or 'request_during_notice_dismissal'
        self.record_request(url,method,resource,'request_during_notice_dismissal')
        return False
    def navigation(self,url,*,login_entry=False):
        u=address(url)
        paths={'/','/dashboard'} if login_entry and self.phase=='auth' else {self.overview}
        if not self.is_hub(u) or u.path not in paths or u.query:raise FlowError(4,'navigation_unregistered')
        if login_entry:self.auth_entry='/dashboard'
        elif self.auth_entry=='/dashboard' and self.phase!='account_verified':
            raise FlowError(4,'navigation_unregistered')
        self.allowed=(url,'GET')
    def verify_account(self):
        if self.phase!='account':raise FlowError(4,'navigation_unregistered')
        self.phase='account_verified'
    def allow_run(self,url):
        if self.allowed:raise FlowError(6,'gate_action_busy')
        if self.phase!='business' or self.capture_run or self.run_candidates!=[url]:
            raise FlowError(4,'run_pattern_unregistered')
        self.allowed=(url,'RUN')
    def arm(self,expected,hidden,*,intent_recorded):
        if self.rehearse or self.recording or not intent_recorded or self.sent:raise FlowError(4,'submit_gate_not_armed')
        self.submission=(expected,hidden)
    def block(self,method,u,reason):
        category=u.path if u.path in {'/wicket/page','/dashboard','/overview/'+self.s['target_config_id']} else 'unregistered'
        self.records.append({'method':method if method in {'GET','POST'} else 'other','path_class':category,'reason':reason})
        return False
    def request(self,url,method,*,resource='Document',body=b'',content_type='',ajax=False,main_frame=True):
        with self.mutex:
            try:u=address(url)
            except (FlowError,ValueError):
                return self.reject_dismissal(url,method,resource) if self.dismissing else False
            origin=u.scheme+'://'+u.netloc
            if self.dismissing:
                if not self.fatal and main_frame and self.static_allowed(u,method,resource,ajax=ajax):
                    self.record_request(url,method,resource,'allow_static')
                    return True
                return self.reject_dismissal(url,method,resource)
            if self.fatal=='request_during_notice_dismissal':return self.block(method,u,self.fatal)
            if main_frame and resource=='Document' and self.manual_url(u):
                self.manual_login=True
                self.record_request(url,method,resource,'hub_manual_login_page')
                return self.block(method,u,'hub_manual_login_page')
            if self.phase=='auth' and self.auth_wicket(u):
                return self.block(method,u,'auth_wicket_blocked')
            if self.phase=='auth' and self.is_hub(u) and u.path=='/signin' and method!='GET':
                self.manual_login=True
                self.record_request(url,method,resource,'hub_manual_login_page')
                return self.block(method,u,'hub_manual_login_page')
            # Authentication is a host/path/method allowlist. Never inspect its body or headers.
            auth=[x for x in self.s.get('auth_paths',[]) if x=={'host':u.netloc,'path':u.path,'method':method}]
            if self.phase=='auth' and auth and main_frame and (u.scheme=='https' or self.is_hub(u)):return True
            if origin!=self.origin:return self.block(method,u,'foreign_origin')
            if resource in {'WebSocket','EventSource','Worker','ServiceWorker'}:return self.block(method,u,'active_channel')
            if self.static_allowed(u,method,resource):return True
            if not main_frame:return self.block(method,u,'frame_or_popup')
            if self.allowed==(url,method):self.allowed=None;return True
            if self.phase=='auth' and self.auth_return and method=='GET' and resource=='Document' and u.path==self.auth_entry and not u.query:
                self.auth_return=False;return True
            if self.run_redirect==url and method=='GET' and resource=='Document':
                self.run_redirect=False;return True
            if (self.phase=='business' and method=='GET' and resource=='Document' and not ajax
                    and u.path==self.overview and RUN_QUERY.fullmatch(u.query)):
                if self.capture_run:
                    self.run_candidates.append(url)
                    return self.block(method,u,'run_recorded')
                if self.allowed==(url,'RUN'):
                    self.allowed=None;self.run_response=url;return True
            try:p=pattern(url,method)
            except FlowError:return self.block(method,u,'unregistered')
            if self.phase!='business':return self.block(method,u,'authentication_not_complete')
            is_submit=p['listener']=='IFormSubmitListener' or p['component'].endswith('-submit') or p['component'].endswith('-ok')
            if self.recording:
                if is_submit:
                    self.records.append(dict(p, classification='submit'))
                    self.fatal='submission_during_recording'
                    self.record_request(url,method,resource,self.fatal)
                elif self.filling and p['component'] == self.filling[0] and method == 'POST' and p['listener'] == 'IBehaviorListener':
                    self.records.append(dict(p, control=self.filling[0], classification='callback_candidate'))
                return False
            if is_submit:
                if method!='POST' or p!=self.s.get('submit_pattern') or self.submission is None or self.sent:return self.block(method,u,'submission_not_authorized')
                expected,hidden=self.submission;self.submission=None
                try:verify_parts(self.config,multipart(body,content_type),expected,hidden)
                except FlowError:
                    self.fatal='blocked_before_send';self.record_request(url,method,resource,self.fatal);return False
                self.sent=True;return True
            if self.filling is not None and method=='POST' and ajax and content_type.split(';')[0]=='application/x-www-form-urlencoded' and p in self.s.get('gate_patterns',[]) and p['component']==self.filling[0] and not self.fatal and self.callback_count == 0:
                try:values=parse_qsl(body.decode('utf-8'),keep_blank_values=True,strict_parsing=True,errors='strict')
                except (ValueError,UnicodeError):return self.block(method,u,'callback_encoding')
                if values==[(self.filling[1],self.filling[2])]:
                    self.callback_count += 1
                    self.records.append(dict(p, control=self.filling[0], classification='callback_allowed'))
                    return True
            self.fatal='unregistered_callback';self.record_request(url,method,resource,self.fatal);return self.block(method,u,self.fatal)
    def response(self,url,status,location='',*,main_document=True,method='GET',resource='Document'):
        """Authorize no automatic business redirect. Auth returns are exact and one-use."""
        u=address(url)
        if status in {301,302,303,307,308}:
            if self.dismissing:
                return self.reject_dismissal(url,method,resource)
            try:v=address(urljoin(url,location))
            except FlowError:return False
            if main_document and self.manual_url(v):
                self.manual_login=True
                self.record_request(v.geturl(),'GET','Document','hub_manual_login_page')
                return False
            if self.phase=='auth' and self.auth_wicket(v):return False
            if self.phase=='auth' and main_document:
                auth=any(x['host']==v.netloc and x['path']==v.path for x in self.s.get('auth_paths',[]))
                entry=v.scheme+'://'+v.netloc==self.origin and v.path==self.auth_entry and not v.query
                if auth or entry:self.auth_return=entry;return True
            if self.run_response==url and main_document:
                self.run_response=None
                if status==302 and self.is_hub(v) and v.path=='/wicket/page' and re.fullmatch(r'[0-9]+',v.query):
                    self.run_redirect=v.geturl();return True
            return False
        if main_document and status==200 and self.is_hub(u) and not u.query:
            if self.phase=='auth' and u.path==self.auth_entry:
                self.phase='account' if self.auth_entry=='/dashboard' else 'business'
            elif self.phase=='account_verified' and u.path=='/overview/'+self.s['target_config_id']:
                self.phase='business'
        return True
