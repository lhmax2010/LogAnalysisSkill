"""B2a process-table, recovery and source-isolation tests; no browser starts."""
import json
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch
from helpers import REPO
from bm_helpers import BASE, detail, pages
from test_batch3a11b1 import B1Case, HUMAN, EXTERNAL
from vd_cosmos_core import submit_model as model, submit_sessions as sessions, submit_source as source, submit_once as once, submit_terminal
from vd_cosmos_core.commands import CommandContext, Category
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.errors import FlowError

CTX=CommandContext('submit.once',Category.EXTERNAL,True)
REC=CommandContext('recover',Category.HUMAN,True)

class Processes:
    def __init__(self):self.alive=True;self.unknown=False;self.cleaned=[]
    def identity(self,pid):
        if self.unknown:raise FlowError(6,'holder_unverified')
        return 'start' if self.alive else None
    def close(self,path):self.cleaned.append(str(path))

class B2aTests(B1Case):
    def args(self,**updates):
        p=self.root/'base';p.write_text(BASE)
        self.config.raw['submit']['form']=self.form()
        return SimpleNamespace(**(dict(base_list=str(p),base_from_hub=None,bm_build=None,shelve_list=None,reason='fixture',rehearse=True,resubmit_of=None)|updates))
    def test_cli_non_tty_and_argument_shelve_rejections(self):
        for command in ('once','recover'):
            r=subprocess.run([sys.executable,str(REPO/'vd-cosmos-submit/scripts/run.py'),command,'--config',str(self.path)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stdout)['error'],'terminal_required')
        p=self.root/'shelve';p.write_text('//example/a@123')
        for args in (self.args(base_from_hub='500'),self.args(shelve_list=str(p)),self.args(rehearse=False)):
            self.fails(4 if args.shelve_list or not args.rehearse else 2,once.prepare,self.config,args,CTX,self.reader,lambda _: 'yes')
        with EventStore(self.config.data_root) as store:self.assertFalse(store.events(kinds=['submit_request']))
    def test_fake_ancestor_table_blocks_cline_and_unreadable(self):
        proc=self.root/'proc';p=proc/'2';p.mkdir(parents=True)
        (p/'cmdline').write_bytes(b'sshd\0');(p/'stat').write_text('2 (ssh) S 1')
        submit_terminal.ancestors_allowed(proc,2)
        (p/'cmdline').write_bytes(b'node\0extensionHost\0')
        self.fails(4,submit_terminal.ancestors_allowed,proc,2)
        self.fails(4,submit_terminal.ancestors_allowed,proc,3)
    def test_profile_lock_and_session_unique_and_mode(self):
        args=self.args();r=once.prepare(self.config,args,CTX,self.reader,lambda _:'yes');proc=Processes()
        with sessions.target_lock(self.config):
            self.fails(6,sessions.precheck,self.config,CTX,proc)
            session=sessions.start(self.config,r,CTX,proc)
            self.assertEqual(sessions.profile_path(self.config,session).stat().st_mode & 0o777,0o700)
            self.fails(6,sessions.start,self.config,r,CTX,proc)
            sessions.finish(self.config,session,CTX,proc)
        self.assertFalse(sessions.profile_path(self.config,session).exists())
    def test_recovery_alive_unknown_and_pre_exposure(self):
        r=once.prepare(self.config,self.args(),CTX,self.reader,lambda _:'yes');proc=Processes();s=sessions.start(self.config,r,CTX,proc)
        with EventStore(self.config.data_root) as store:head=store.head()
        self.fails(6,sessions.recover_locked,self.config,CTX,proc)
        proc.unknown=True;self.fails(6,sessions.recover_locked,self.config,CTX,proc)
        with EventStore(self.config.data_root) as store:self.assertEqual(store.head(),head)
        proc.unknown=False;proc.alive=False;sessions.recover_locked(self.config,CTX,proc)
        self.assertEqual(model.read(self.config,r['request_id'])['status'],'prepared')
        with EventStore(self.config.data_root) as store:self.assertEqual(len(store.events(kinds=['submit_recovery'])),1)
    def test_exposed_no_click_survives_cleanup_crash_and_manual_override(self):
        r=once.prepare(self.config,self.args(),CTX,self.reader,lambda _:'yes');proc=Processes();s=sessions.start(self.config,r,CTX,proc);sessions.expose(self.config,s,CTX)
        with patch.object(proc,'close',side_effect=FlowError(6,'cleanup_failed')):
            self.fails(6,sessions.recover_locked,self.config,REC,proc,session_id=s['operation_id'],holder_gone=True,reason='confirmed')
        self.assertEqual(model.read(self.config,r['request_id'])['status'],'manual_submit_pending')
        sessions.recover_locked(self.config,REC,proc,session_id=s['operation_id'],holder_gone=True,reason='confirmed')
        self.fails(6,sessions.precheck,self.config,CTX,proc)
        with EventStore(self.config.data_root) as store:self.assertEqual(len(store.events(kinds=['submit_recovery'])),1)
    def test_click_crash_uncertain_and_accepted_crash_keeps_result(self):
        for status in ('prepared','accepted'):
            self.config=replace(self.config,data_root=self.root/status)
            r=once.prepare(self.config,self.args(),CTX,self.reader,lambda _:'yes');proc=Processes();s=sessions.start(self.config,r,CTX,proc);sessions.expose(self.config,s,CTX)
            with EventStore(self.config.data_root) as store:store.append(CTX,'click_intent',{},store.head(),request_id=r['request_id'],operation_id=s['operation_id'])
            if status=='accepted':model.record_outcome(self.config,r['request_id'],CTX,'accepted')
            proc.alive=False;sessions.recover_locked(self.config,CTX,proc)
            self.assertEqual(model.read(self.config,r['request_id'])['status'],'uncertain' if status=='prepared' else 'accepted')
            self.fails(6,sessions.precheck,self.config,CTX,proc)
    def test_source_whitelist_header_only_and_no_bind_round_or_shelve_artifact(self):
        self.args();values={'PACKAGE_LIST':BASE,'BASE_REPOS':'base','BUILD_CONF':'conf','PRODUCT_REPOS':'product','ARCH':'armv7l','BUILD_TYPE':'Full','KS_LIST':'a.ks,b.ks','EXTRA_BUILD_PARAMETER':'--threads 32','SHELVE_LIST':'FORBIDDEN_SHELVE','BART_PASSWD':'FORBIDDEN_PASSWORD'}
        data=pages();data['/build/900/variables']=detail(variables=values)
        def headers(config,build,arch,reader):
            return source.headers_only(('<pre>Arch: '+arch+'\nStart Time: 2026-11-01\nBase snapshot: base\nProduct snapshot: product\nBuild.conf: conf</pre><table><tr><td>package</td><td>FORBIDDEN_SHELVE</td></tr></table>').encode())
        form,basis=source.determine(self.config,'500','900',self.reader(data),lambda d:'900',CTX,headers)
        self.assertEqual(form['SHELVE_LIST'],'');self.assertEqual(form['PACKAGE_LIST'],BASE)
        self.assertEqual(basis['build_id'],'900')
        with EventStore(self.config.data_root) as store:
            self.assertFalse(store.events(kinds=['bind','submit_request']));self.assertEqual(len(store.events(kinds=['base_source_attest'])),1)
        for p in self.config.data_root.rglob('*'):
            if p.is_file():self.assertNotIn(b'FORBIDDEN_SHELVE',p.read_bytes());self.assertNotIn(b'FORBIDDEN_PASSWORD',p.read_bytes())
        self.assertFalse((self.config.data_root/'rounds').exists())
    def test_source_invalid_identity_missing_values_and_confirmation_never_create_request(self):
        self.args()
        for hub,build in [('501','900'),('500','19270877')]:self.fails(4,source.determine,self.config,hub,build,self.reader(),lambda _:'900',CTX)
        self.fails(5,source.determine,self.config,'500','900',self.reader(),lambda _:'900',CTX)
    def test_duplicate_parsed_list_and_wrong_resubmit_reference(self):
        args=self.args();r=once.prepare(self.config,args,CTX,self.reader,lambda _:'yes')
        model.record_outcome(self.config,r['request_id'],CTX,'accepted')
        Path(args.base_list).write_text('\n'+BASE.rstrip()+'  \n')
        self.fails(6,once.prepare,self.config,args,CTX,self.reader,lambda _:'yes')
        args.resubmit_of='wrong';self.fails(6,once.prepare,self.config,args,CTX,self.reader,lambda _:'resubmit')
        args.resubmit_of=r['request_id'];replacement=once.prepare(self.config,args,CTX,self.reader,lambda _:'resubmit')
        self.assertNotEqual(replacement['request_id'],r['request_id'])
