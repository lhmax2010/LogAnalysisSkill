"""Single-operation preparation. All actual browser effects are injected."""
import json
from .commands import Category
from .errors import FlowError
from .state import EventStore
from . import submit_model as model, submit_sessions as sessions, submit_source


def prepare(config, args, context, reader_factory, confirm, *, processes=None, header_reader=None):
    if context.category!=Category.EXTERNAL or not context.terminal_confirmed:raise FlowError(2,'terminal_required')
    if bool(args.base_list)==bool(args.base_from_hub) or args.bm_build and not args.base_from_hub:raise FlowError(2,'base_source_exclusive')
    if not args.reason or not args.reason.strip():raise FlowError(2,'reason_required')
    if args.shelve_list:
        if config.source(args.shelve_list).read_text().strip():raise FlowError(4,'shelve_requires_batch4')
    if not args.rehearse and config.raw['submit'].get('property_map_confirmed') is not True:
        raise FlowError(4,'property_map_unconfirmed',todo={'reason':'property_map_unconfirmed','message':'属性对应表待 FatTank 确认；仅允许 --rehearse'})
    if not args.rehearse and (not config.raw['submit'].get('gate_patterns_confirmed') or not config.raw['submit'].get('form_fingerprint',{}).get('confirmed')):raise FlowError(4,'browser_contract_unconfirmed')
    sessions.precheck(config,context,processes)
    basis=None
    if args.base_from_hub:
        reader=reader_factory()
        try:
            options={'header_reader':header_reader} if header_reader else {}
            form,basis=submit_source.determine(config,args.base_from_hub,args.bm_build,reader,confirm,context,**options)
        finally:reader.close()
    else:
        form=dict(config.raw['submit']['form']);form['PACKAGE_LIST']=config.source(args.base_list).read_text();form['SHELVE_LIST']=''
    sha=model.request_digest(config,form)
    with EventStore(config.data_root) as store:
        previous=[r for r in model.requests(store.events()).values() if r['digest']==sha and model.was_submitted(r)]
    if args.resubmit_of:
        if not previous or previous[-1]['request_id']!=args.resubmit_of:raise FlowError(6,'invalid_resubmit_reference')
        display={'submissions':[{'request':r['request_id'],'at':r['created_at'],'hub':r['hub_id'],'reruns':r.get('manual_reruns',[])} for r in previous],
                 'next_round':1+sum(1+len(r.get('manual_reruns',[])) for r in previous)}
        if confirm(display)!='resubmit':raise FlowError(3,'resubmit_confirmation_required')
    request=model.create_request(config,context,form,args.reason,resubmit_of=args.resubmit_of)
    if basis and request.get('source')!=basis:
        request=model.mutate(config,request['request_id'],request['version'],context,{'source':basis},kind='submit_outcome')
    return request


def run(config,args,context,reader_factory,confirm,driver_factory=None,*,processes=None,header_reader=None):
    request=prepare(config,args,context,reader_factory,confirm,processes=processes,header_reader=header_reader)
    with sessions.target_lock(config):
        sessions.recover_locked(config,context,processes or sessions.Processes())
        # Recheck concurrent preparation and duplicate-round protection under the browser lock.
        current=model.create_request(config,context,request['form'],args.reason,resubmit_of=args.resubmit_of)
        if current['request_id']!=request['request_id']:raise FlowError(6,'request_changed_during_preparation')
        session=sessions.start(config,current,context,processes)
        try:
            if driver_factory is None:raise FlowError(6,'browser_driver_unavailable')
            return driver_factory(config,session).operate(args,current,context,confirm,reader_factory)
        finally:
            # Browser implementations must confirm shutdown before this normal finish.
            # A failed shutdown raises, leaving the durable exposure for recovery.
            if driver_factory is None:sessions.finish(config,session,context,processes)
