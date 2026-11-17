"""Deterministic event interleavings: no sleep window and no stale evidence merge."""
from unittest.mock import patch
from test_batch3a11b1 import B1Case,HUMAN,EXTERNAL,OBSERVE
from vd_cosmos_core import submit_model as model,submit_watch,submit_claim,submit_sessions
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.state import EventStore


class MutationRaceTests(B1Case):
    def chain(self):
        with EventStore(self.config.data_root) as store:events=store.events()
        self.assertEqual([e['previous_id'] for e in events],[0]+[e['id'] for e in events[:-1]])
        return events
    def inject(self,action):
        original=EventStore.append_batch;calls=[]
        def append(store,context,entries,head):
            calls.append(head)
            if len(calls)==1:action(original)
            return original(store,context,entries,head)
        return patch.object(EventStore,'append_batch',append),calls
    def test_heartbeat_between_head_and_append_retries_without_losing_chain(self):
        r=self.accepted();rid=r['request_id']
        hook,calls=self.inject(lambda original:submit_watch.heartbeat(self.config,rid,now=self.start+1))
        with hook:
            updated=model.mutate(self.config,rid,r['version'],OBSERVE,{'seen':{'fixture':True}},kind='submit_observation')
        self.assertEqual(len(calls),2);self.assertGreater(calls[1],calls[0]);self.assertEqual(updated['version'],r['version']+1)
        events=self.chain();self.assertEqual([e['kind'] for e in events[-2:]],['submit_heartbeat','submit_observation'])
    def test_request_version_change_between_head_and_append_rejects_stale_scan(self):
        r=self.accepted();rid=r['request_id']
        def change(original):
            with EventStore(self.config.data_root) as other:
                original(other,HUMAN,[{'kind':'submit_decision','request_id':rid,'payload':{'changes':{'status':'abandoned'}}}],other.head())
        hook,calls=self.inject(change)
        with hook:error=self.fails(6,model.mutate,self.config,rid,r['version'],OBSERVE,{'seen':{'stale':True}},kind='submit_observation')
        self.assertEqual(error.reason,'request_version_changed');self.assertEqual(len(calls),1)
        fresh=model.read(self.config,rid);self.assertEqual(fresh['status'],'abandoned');self.assertNotIn('stale',fresh['seen'])
        self.assertFalse(any(e['kind']=='submit_observation' for e in self.chain()))
    def test_other_request_binding_between_head_and_append_rechecks_ownership(self):
        r=self.accepted();other=model.create_request(self.config,EXTERNAL,self.form()|{'EXTRA_BUILD_PARAMETER':'other'},'fixture')
        binding={'build_id':'901','hub_id':'501'}
        def claim(original):
            with EventStore(self.config.data_root) as store:
                original(store,HUMAN,[{'kind':'submit_decision','request_id':other['request_id'],'payload':{'changes':{'binding':binding,'hub_id':'501'}}}],store.head())
        hook,calls=self.inject(claim)
        with hook:error=self.fails(4,model.mutate,self.config,r['request_id'],r['version'],HUMAN,{'binding':binding,'hub_id':'501'})
        self.assertEqual(error.reason,'candidate_owned_by_other_request');self.assertEqual(len(calls),1)
        self.assertIsNone(model.read(self.config,r['request_id'])['binding']);self.chain()
    def test_busy_retries_are_bounded_and_observed_checks_repeat(self):
        r=self.accepted();rid=r['request_id'];changes={'seen':{}}
        with patch.object(EventStore,'append_batch',side_effect=FlowError(6,'state_busy')) as append:
            error=self.fails(6,model.mutate,self.config,rid,r['version'],OBSERVE,changes,kind='submit_observation')
        self.assertEqual(error.reason,'state_busy');self.assertEqual(append.call_count,4)
        changes={'seen':{}}
        def busy(store,context,entries,head):
            changes['status']='accepted';raise FlowError(6,'state_busy')
        with patch.object(EventStore,'append_batch',busy):
            error=self.fails(4,model.mutate,self.config,rid,r['version'],OBSERVE,changes,kind='submit_observation')
        self.assertEqual(error.reason,'observation_cannot_authorize');self.chain()
    def test_step_discards_scan_when_version_changes_during_merge(self):
        r=self.accepted();rid=r['request_id']
        def change(original):
            with EventStore(self.config.data_root) as store:
                original(store,HUMAN,[{'kind':'submit_decision','request_id':rid,'payload':{'changes':{'status':'abandoned'}}}],store.head())
        hook,_=self.inject(change)
        with hook:result=submit_watch.step(self.config,rid,self.reader())
        self.assertTrue(result['scan_discarded']);self.assertEqual(result['status'],'abandoned');self.chain()
    def test_record_outcome_and_abandon_tolerate_heartbeat(self):
        r=model.create_request(self.config,EXTERNAL,self.form(),'fixture');rid=r['request_id']
        def beat(original):
            with EventStore(self.config.data_root) as store:
                store.append(OBSERVE,'submit_heartbeat',{'at':self.start},store.head(),request_id=rid)
        hook,_=self.inject(beat)
        with hook:result=model.record_outcome(self.config,rid,EXTERNAL,'accepted',now=self.start)
        hook,_=self.inject(beat)
        with hook:result=submit_claim.abandon(self.config,rid,HUMAN,'stop')
        self.assertEqual(result['status'],'abandoned');self.chain()

    def test_resolve_rechecks_pending_reruns_that_do_not_bump_request_version(self):
        for mode in ('build-id','not-submitted'):
            r=model.create_request(self.config,EXTERNAL,self.form()|{'EXTRA_BUILD_PARAMETER':mode},'fixture')
            def rerun(original):
                with EventStore(self.config.data_root) as store:
                    store.append(HUMAN,'submit_rerun_resolved',{'target':model.target(self.config),'hub_id':'500','at':self.start,'pending':True},store.head(),operation_id=mode)
            hook,_=self.inject(rerun)
            if mode=='build-id':
                with hook:result=model.resolve(self.config,HUMAN,request_id=r['request_id'],hub_id='500',mode=mode,reason='checked')
                self.assertEqual(len(result['manual_reruns']),1)
            else:
                # The earlier pending record is acknowledged; create a distinct
                # target so the new pending record alone triggers the retry guard.
                self.config.raw['submit']['target_config']='different-target'
                r=model.create_request(self.config,EXTERNAL,self.form(),'fixture')
                with hook:error=self.fails(3,model.resolve,self.config,HUMAN,request_id=r['request_id'],mode=mode,reason='checked',checked_at='2026-11-17')
                self.assertEqual(error.reason,'rerun_records_confirmation_required')
                self.assertEqual(model.read(self.config,r['request_id'])['status'],'prepared')
        self.chain()


class AtomicStateTests(B1Case):
    def test_immediate_transaction_blocks_other_writer_and_preserves_expected_guard(self):
        with EventStore(self.config.data_root) as first,EventStore(self.config.data_root) as other:
            other.connection.execute('PRAGMA busy_timeout=0')
            with first.transaction():
                head=first.head()
                error=self.fails(6,other.append,OBSERVE,'submit_heartbeat',{'at':1},other.head(),request_id='r')
                self.assertEqual(error.reason,'state_busy')
                first.append(OBSERVE,'submit_heartbeat',{'at':2},head,request_id='r')
            self.assertEqual(other.head(),1)
            error=self.fails(6,other.append,OBSERVE,'submit_heartbeat',{'at':3},head,request_id='r')
            self.assertEqual(error.reason,'stale_head')
    def test_outer_transaction_and_nested_batch_rollback_are_atomic(self):
        with EventStore(self.config.data_root) as store:
            with self.assertRaises(RuntimeError):
                with store.transaction():
                    store.append(OBSERVE,'submit_heartbeat',{'at':1},store.head(),request_id='r')
                    raise RuntimeError('rollback')
            self.assertEqual(store.head(),0)
            with store.transaction():
                store.append(OBSERVE,'submit_heartbeat',{'at':2},store.head(),request_id='r')
                # The second entry violates bind identity; the first must roll back too.
                error=self.fails(6,store.append_batch,HUMAN,[{'kind':'submit_decision','request_id':'r','payload':{'changes':{}}},
                    {'kind':'bind','payload':{}}],store.head())
                self.assertEqual(error.reason,'constraint');self.assertEqual(store.head(),1)
            self.assertFalse(store.connection.in_transaction);self.assertEqual(len(store.events()),1)


class HeartbeatOnlyRebaseTests(B1Case):
    def beat(self):
        with EventStore(self.config.data_root) as store:
            store.append(OBSERVE,'submit_heartbeat',{'at':1},store.head(),request_id='watcher')
    def test_only_heartbeats_rebase_while_explicit_heads_and_real_changes_refuse(self):
        from vd_cosmos_core.state import append_retry
        with EventStore(self.config.data_root) as store:
            expected=store.head();self.beat()
            error=self.fails(6,append_retry,store,HUMAN,'inbox_closed',{'build':'b','todo_key':'t'},expected)
            self.assertEqual(error.reason,'stale_head')
            result=append_retry(store,HUMAN,'inbox_closed',{'build':'b','todo_key':'t'},expected,heartbeat_retry=True)
            self.assertEqual(result,store.head())
            expected=store.head()
            store.append(HUMAN,'submit_decision',{'changes':{'status':'abandoned'}},expected,request_id='r')
            error=self.fails(6,append_retry,store,HUMAN,'inbox_closed',{'build':'b','todo_key':'t'},expected,heartbeat_retry=True)
            self.assertEqual(error.reason,'stale_head');self.assertTrue(error.details['intervening_event'])
    def fixture(self):
        from helpers import bundle
        from vd_cosmos_core.backends import FixtureReportReader
        _,manifest,_=bundle(self.root/'fixture')
        return FixtureReportReader(self.config,manifest)
    def test_workflow_tick_heartbeats_during_action_do_not_repeat_external_read(self):
        from vd_cosmos_workflow.api import tick
        reader=self.fixture();calls=[];observe=reader.observe
        def reading(ref):calls.append(ref);return observe(ref)
        reader.observe=reading
        result=tick(self.config,lambda:reader,after_intent=self.beat,after_action=lambda _:self.beat())
        self.assertEqual(result['exit_code'],0);self.assertEqual(len(calls),1)
        with EventStore(self.config.data_root) as store:
            self.assertEqual(len(store.events(kinds=['workflow_result'])),1)
    def test_fix_register_inbox_done_rebases_heartbeat_but_not_explicit_head(self):
        from vd_fix_register.api import decide
        from vd_cosmos_core.commands import CommandContext,Category
        from vd_cosmos_core.versions import build_key
        reader=self.fixture();context=CommandContext('inbox.done',Category.HUMAN,True)
        with EventStore(self.config.data_root) as store:
            store.append(OBSERVE,'inbox_opened',{'build':build_key(reader),'todo_key':'t','todo':{'reason':'fixture'}},store.head())
        original=EventStore.append;injected=[]
        def append(store,ctx,kind,payload,expected,**kwargs):
            if kind=='inbox_closed' and not injected:
                injected.append(True)
                with EventStore(self.config.data_root) as other:
                    original(other,OBSERVE,'submit_heartbeat',{'at':1},other.head(),request_id='watcher')
            return original(store,ctx,kind,payload,expected,**kwargs)
        with patch.object(EventStore,'append',append):
            result=decide(self.config,reader,'inbox.done',reason='checked',todo_key='t',context=context)
        self.assertEqual(result['exit_code'],0)
        injected.clear()
        with EventStore(self.config.data_root) as store:expected=store.head()
        with patch.object(EventStore,'append',append):
            error=self.fails(6,decide,self.config,reader,'inbox.done',reason='checked',todo_key='t',context=context,expected_event=expected)
        self.assertEqual(error.reason,'stale_head')
        with EventStore(self.config.data_root) as store:self.assertEqual(len(store.events(kinds=['inbox_closed'])),1)
