"""Target-scoped browser leases and conservative crash recovery; no browser APIs."""
import os
from pathlib import Path
import shutil
import signal
import time
import uuid
from .commands import Category
from .errors import FlowError
from .files import digest, json_bytes
from .locks import OperationLock
from .state import EventStore
from . import submit_model as model
from . import browser_temp


class Processes:
    def identity(self, pid):
        try:
            fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
            return fields[19]
        except FileNotFoundError: return None
        except (OSError,IndexError,ValueError): raise FlowError(6,'holder_unverified') from None

    def matching(self, profile):
        found=[]
        for item in Path('/proc').iterdir():
            if not item.name.isdecimal(): continue
            try: args=(item/'cmdline').read_bytes().split(b'\0')
            except FileNotFoundError: continue
            except PermissionError: continue
            if ('--user-data-dir='+str(profile)).encode() in args:
                found.append((int(item.name),self.identity(int(item.name))))
        return found

    def close(self, profile):
        for pid, start in self.matching(profile):
            if self.identity(pid)!=start: raise FlowError(6,'browser_identity_changed')
            os.kill(pid,signal.SIGTERM)
        deadline=time.monotonic()+5
        while self.matching(profile):
            if time.monotonic()>deadline: raise FlowError(6,'browser_cleanup_unverified')
            time.sleep(.05)


def target_lock(config):
    return OperationLock(config.data_root,'profile',digest(json_bytes(model.target(config))))


def active(events, target):
    ended={e['operation_id'] for e in events if e['kind']=='submit_session_finished'}
    return [e for e in events if e['kind']=='submit_session_started' and e['payload']['target']==target and e['operation_id'] not in ended]


def profile_path(config, session):
    path=config.output(session['payload']['profile'])
    expected=config.output('browser/profiles/'+session['operation_id'])
    if path!=expected or path.is_symlink(): raise FlowError(4,'unsafe_profile_path')
    return path


def recover_locked(config, context, processes, *, session_id=None, holder_gone=False, reason=''):
    with EventStore(config.data_root) as store: sessions=active(store.events(),model.target(config))
    if session_id and not any(s['operation_id']==session_id for s in sessions): raise FlowError(6,'session_not_active')
    for session in sessions:
        if session_id and session['operation_id']!=session_id: continue
        if holder_gone:
            if context.category!=Category.HUMAN or not context.terminal_confirmed or not reason.strip(): raise FlowError(2,'recovery_confirmation_required')
        else:
            identity=processes.identity(session['payload']['pid'])
            if identity==session['payload']['start_time']: raise FlowError(6,'previous_session_may_be_alive')
        model.ensure_safe(config,reason)
        sid=session['operation_id'];rid=session['request_id']
        with EventStore(config.data_root) as store:
            head=store.head();events=store.events();owned=[e for e in events if e['operation_id']==sid]
            if not any(e['kind']=='submit_recovery' for e in owned):
                kinds={e['kind'] for e in owned};r=model.requests(events).get(rid)
                changes={};entries=[]
                clicked='click_intent' in kinds
                if r and clicked and r['status']=='prepared': changes['status']='uncertain'
                elif r and 'submit_form_exposed' in kinds and not clicked: changes['status']='manual_submit_pending'
                if 'hub_page_exposed' in kinds or clicked and r and r['status']!='prepared':
                    entries.append(dict(kind='manual_action_pending',request_id=rid,operation_id=sid,payload={'target':model.target(config),'hub_id':r.get('hub_id') if r else None}))
                if changes:
                    entries.append(dict(kind='submit_decision' if context.category==Category.HUMAN else 'submit_outcome',request_id=rid,payload={'changes':changes}))
                entries.append(dict(kind='submit_recovery',request_id=rid,operation_id=sid,payload={'holder_gone':holder_gone,'reason':reason,'state':'准备中断' if not kinds.intersection({'submit_form_exposed','hub_page_exposed','click_intent'}) else '待核实'}))
                store.append_batch(context,entries,head)
        # Recovery evidence is durable before touching the old processes/profile.
        path=profile_path(config,session);processes.close(path)
        browser_temp.cleanup(path)
        if path.exists(): shutil.rmtree(path)
        with EventStore(config.data_root) as store:
            store.append(context,'submit_session_finished',{'target':model.target(config),'normal_close':False,'recovered':True},store.head(),request_id=rid,operation_id=sid)


def precheck(config, context, processes=None):
    with target_lock(config):
        recover_locked(config,context,processes or Processes())
        with EventStore(config.data_root) as store:
            events=store.events()
            if model.unresolved(model.requests(events),events,model.target(config)):raise FlowError(6,'unresolved_submission')


def start(config, request, context, processes=None):
    processes=processes or Processes();sid=uuid.uuid4().hex
    pid=os.getpid();identity=processes.identity(pid)
    if identity is None: raise FlowError(6,'holder_unverified')
    profile='browser/profiles/'+sid
    payload={'target':model.target(config),'pid':pid,'start_time':identity,'profile':profile}
    with EventStore(config.data_root) as store:
        events=store.events();r=model.requests(events).get(request['request_id'])
        if r is None or r['status']!='prepared' or r['version']!=request['version']:raise FlowError(6,'request_version_changed')
        if model.unresolved(model.requests(events),events,model.target(config)):raise FlowError(6,'unresolved_submission')
        store.append(context,'submit_session_started',payload,store.head(),request_id=r['request_id'],operation_id=sid)
    path=config.output(profile);path.mkdir(parents=True,mode=0o700,exist_ok=False);path.chmod(0o700)
    return {'operation_id':sid,'request_id':r['request_id'],'payload':payload}


def expose(config, session, context):
    with EventStore(config.data_root) as store:
        if not any(s['operation_id']==session['operation_id'] for s in active(store.events(),model.target(config))):raise FlowError(6,'session_not_active')
        store.append(context,'submit_form_exposed',{'target':model.target(config)},store.head(),request_id=session['request_id'],operation_id=session['operation_id'])


def finish(config, session, context, processes=None):
    path=profile_path(config,session);(processes or Processes()).close(path)
    browser_temp.cleanup(path)
    if path.exists():shutil.rmtree(path)
    with EventStore(config.data_root) as store:
        store.append(context,'submit_session_finished',{'target':model.target(config),'normal_close':True},store.head(),request_id=session['request_id'],operation_id=session['operation_id'])
