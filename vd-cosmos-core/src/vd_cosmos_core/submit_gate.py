"""Deny-by-default request gate; transport supplies EVERY redirect hop."""
import re
import threading
from urllib.parse import urlsplit, parse_qsl
from .errors import FlowError
from .submit_browser_contract import multipart, verify_parts

WICKET=re.compile(r'^[0-9]+-[0-9]+\.(IFormSubmitListener|ILinkListener|IBehaviorListener)(?:\.([0-9]+))?-([A-Za-z0-9_-]+)$')

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
    def navigation(self,url):
        u=address(url)
        if u.scheme+'://'+u.netloc!=self.origin or u.path!='/overview/'+self.s['target_config_id'] or u.query:raise FlowError(4,'navigation_unregistered')
        self.allowed=(url,'GET')
    def action(self,registered):
        if self.allowed:raise FlowError(6,'gate_action_busy')
        self.allowed=registered
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
            except FlowError:return False
            origin=u.scheme+'://'+u.netloc
            # Authentication is a host/path/method allowlist. Never inspect its body or headers.
            auth=[x for x in self.s.get('auth_paths',[]) if x=={'host':u.netloc,'path':u.path,'method':method}]
            if self.phase=='auth' and auth and (u.scheme=='https' or self.origin.startswith('http://127.0.0.1:')):return True
            if origin!=self.origin:return self.block(method,u,'foreign_origin')
            if resource in {'WebSocket','EventSource','Worker','ServiceWorker'}:return self.block(method,u,'active_channel')
            if resource in {'Script','Stylesheet','Image','Font'} and method=='GET' and not u.query and u.path in self.s.get('static_paths',[]):return True
            if not main_frame:return self.block(method,u,'frame_or_popup')
            if self.allowed==(url,method):self.allowed=None;return True
            if self.phase=='auth' and self.auth_return and method=='GET' and u.path=='/overview/'+self.s['target_config_id'] and not u.query:
                self.auth_return=False;return True
            if self.run_redirect and method=='GET' and u.path=='/wicket/page' and u.query.isdecimal():
                self.run_redirect=False;return True
            try:p=pattern(url,method)
            except FlowError:return self.block(method,u,'unregistered')
            if self.allowed==p:
                self.allowed=None;self.run_response=url;return True
            if self.phase!='business':return self.block(method,u,'authentication_not_complete')
            is_submit=p['listener']=='IFormSubmitListener' or p['component'].endswith('-submit') or p['component'].endswith('-ok')
            if self.recording:
                self.records.append(dict(p,control=self.filling[0] if self.filling else None,classification='submit' if is_submit else 'callback_candidate'))
                if is_submit:self.fatal='submission_during_recording'
                return False
            if is_submit:
                if method!='POST' or p!=self.s.get('submit_pattern') or self.submission is None or self.sent:return self.block(method,u,'submission_not_authorized')
                expected,hidden=self.submission;self.submission=None
                try:verify_parts(self.config,multipart(body,content_type),expected,hidden)
                except FlowError:self.fatal='blocked_before_send';return False
                self.sent=True;return True
            if self.filling is not None and method=='POST' and ajax and content_type.split(';')[0]=='application/x-www-form-urlencoded' and p in self.s.get('gate_patterns',[]) and p['component']==self.filling[0] and self.callback_count<2:
                try:values=parse_qsl(body.decode('utf-8'),keep_blank_values=True,strict_parsing=True,errors='strict')
                except (ValueError,UnicodeError):return self.block(method,u,'callback_encoding')
                if values==[(self.filling[1],self.filling[2])]:self.callback_count+=1;return True
            self.fatal='unregistered_callback';return self.block(method,u,'unregistered_callback')
    def response(self,url,status,location=''):
        """Authorize no automatic business redirect. Auth returns are exact and one-use."""
        u=address(url)
        if status in {301,302,303,307,308}:
            from urllib.parse import urljoin
            try:v=address(urljoin(url,location))
            except FlowError:return False
            if self.phase=='auth':
                auth=any(x['host']==v.netloc and x['path']==v.path for x in self.s.get('auth_paths',[]))
                entry=v.scheme+'://'+v.netloc==self.origin and v.path=='/overview/'+self.s['target_config_id'] and not v.query
                if auth or entry:self.auth_return=entry;return True
            if self.run_response==url and status==302 and v.scheme+'://'+v.netloc==self.origin and v.path=='/wicket/page' and v.query.isdecimal():self.run_redirect=True;self.run_response=None;return True
            return False
        if self.phase=='auth' and status==200 and u.scheme+'://'+u.netloc==self.origin and u.path=='/overview/'+self.s['target_config_id'] and not u.query:self.phase='business'
        return True
