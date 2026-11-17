"""Driver-independent single-submit protocol; durable intent precedes the token."""
import time
from .errors import FlowError
from .state import EventStore
from . import submit_model as model, submit_sessions as sessions
from .submit_browser_contract import structure, readback, wire_values, verify_parts

def intent(config,request,session,context,H_pre,clock):
    with model.lock(config,request['request_id']):
        with EventStore(config.data_root) as store, store.transaction():
            events=store.events();all_requests=model.requests(events);r=all_requests.get(request['request_id'])
            if r is None or r['version']!=request['version'] or r['status']!='prepared' or model.request_digest(config,r['form'])!=r['digest']:raise FlowError(6,'request_changed_before_click')
            if not any(s['operation_id']==session['operation_id'] for s in sessions.active(events,model.target(config))):raise FlowError(6,'session_not_active')
            filtered=[e for e in events if not(e['operation_id']==session['operation_id'] and e['kind']=='submit_form_exposed')]
            if model.unresolved(all_requests,filtered,model.target(config)) or any(e['kind']=='click_intent' and e['request_id']==r['request_id'] for e in events):raise FlowError(6,'click_already_or_uncertain')
            history=[x for x in all_requests.values() if x['digest']==r['digest'] and model.was_submitted(x)]
            if history and r['previous_request']!=history[-1]['request_id']:raise FlowError(6,'duplicate_round')
            at=time.time();payload={'click_time':at,'H_pre':H_pre,'click_clock':clock}
            store.append_batch(context,[dict(kind='click_intent',payload=payload,request_id=r['request_id'],operation_id=session['operation_id']),dict(kind='submit_outcome',payload={'changes':payload},request_id=r['request_id'])],store.head())
    return model.read(config,request['request_id'])

def execute(config,request,session,context,driver,confirm,reader_factory,*,rehearse):
    clicked=False
    try:
        driver.open(lambda:sessions.expose(config,session,context),confirm)
        first=driver.snapshot();fingerprint=structure(config,first)
        for index,name in enumerate(request['form']):
            # The index comes from the immutable property order, never dictionary order.
            from .submit_config import PROPERTIES
            driver.fill(PROPERTIES.index(name),request['form'][name])
        snapshot=driver.snapshot();values=readback(config,snapshot,request['form'])
        if structure(config,snapshot)['controls']!=fingerprint['controls']:
            # Default states change during filling; control names/types/options must not.
            def stable(fp):return [{k:v for k,v in c.items() if k!='default'} for c in fp['controls']]
            if stable(structure(config,snapshot))!=stable(fingerprint):raise FlowError(5,'form_changed_during_fill')
        evidence=driver.serialize_check(snapshot,request['form'],rehearse=rehearse)
        model.ensure_safe(config,{'values':values,'fingerprint':fingerprint,'serialization':evidence})
        answer=confirm({'target':request['target'],'request':request['request_id'],'digest_prefix':request['digest'][:12],'values':values,'fingerprint':fingerprint,'serialization':evidence,'rehearse':rehearse})
        if answer!=request['digest'][:12]:raise FlowError(3,'digest_confirmation_required')
        with EventStore(config.data_root) as store:
            matches={r['digest'] for r in model.requests(store.events()).values() if r['digest'].startswith(answer)}
        if matches!={request['digest']}:raise FlowError(3,'digest_prefix_not_unique')
        if rehearse:return {'exit_code':0,'request':request['request_id'],'rehearsed':True,'clicked':False,'evidence':evidence,'fingerprint':fingerprint,'gate_records':driver.records()}
        if config.raw['submit'].get('property_map_confirmed') is not True:raise FlowError(4,'property_map_unconfirmed')
        reader=reader_factory();H_pre=None;clock={}
        try:
            overview=reader.overview();ids=[int(r['hub_id']) for r in overview['rows'] if r.get('hub_id')];H_pre=max(ids) if ids else None;clock=reader.samples[-1] if reader.samples else {}
        except FlowError:pass
        finally:reader.close()
        final=driver.snapshot();readback(config,final,request['form'])
        def stable(fp):return [{k:v for k,v in c.items() if k not in {'default','value'}} for c in fp['controls']]
        if stable(structure(config,final))!=stable(structure(config,snapshot)):raise FlowError(5,'form_changed_before_click')
        expected=wire_values(config,final,request['form']);request=intent(config,request,session,context,H_pre,clock);clicked=True
        status=driver.release(expected,final['hidden'])
        if status not in {'accepted','rejected','blocked_before_send'}:status='uncertain'
        result=model.record_outcome(config,request['request_id'],context,status,click_time=request['click_time'],click_clock=clock,H_pre=H_pre)
        return {'exit_code':3 if status=='uncertain' else 4 if status=='blocked_before_send' else 0,'status':status,'request':result['request_id'],'follow_up':'watch --request '+result['request_id'] if status=='accepted' else 'resolve' if status=='uncertain' else None}
    except BaseException:
        if clicked:
            current=model.read(config,request['request_id'])
            if current['status']=='prepared':model.record_outcome(config,request['request_id'],context,'uncertain',click_time=current['click_time'],click_clock=current['click_clock'],H_pre=current['H_pre'])
        raise
    finally:
        driver.close()
        sessions.finish(config,session,context)
