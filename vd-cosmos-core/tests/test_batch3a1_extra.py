"""Additional independent boundary fixtures for batch 3a-1."""
from datetime import timedelta
import io
import json
import os
from pathlib import Path
import pty
import select
import sys
import time
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch
import test_batch3a1 as fixture
from helpers import bundle, CORE, REPO, detail_html
from vd_cosmos_core.backends import FixtureReportReader
from vd_cosmos_core.build_inputs import fetch_build_inputs, variables, compare_lists
from bm_helpers import variable_table
from vd_cosmos_core.commands import Category, CommandContext, command_context
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes, load_json
from vd_cosmos_core.journal import monitor_todos
from vd_cosmos_core.p4 import P4Adapter
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.versions import build_key
from vd_fix_analyze.snapshot import snapshot, merge
from vd_fix_register.api import decide


class SnapshotEdgeTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Snapshot3a1Tests();self.f.setUp();self.addCleanup(self.f.doCleanups)

    def test_appendix_i_real_timelines_plusplayer_requires_current_digest_confirmation(self):
        f=self.f
        cases = [('AT-HUB', '14288393', '14288668', 2, '2026/09/28 17:47:00'),
                 ('aria-engine', '14288396', '13372612', 1, '2026/09/28 17:47:00'),
                 ('plusplayer', '14329096', '14274649', 32, '2026/10/23 20:28:00')]
        for name, scl, cl, count, updated in cases:
            with self.subTest(package=name):
                f.package['cl'] = scl
                f.fixture['files'] = {}
                shelf = {'updated': updated, 'files': []}
                f.fixture['shelves'] = {scl: shelf}
                for entry in f.lists['base'].values(): entry['cl'] = cl
                for index in range(count):
                    path=f.path if index==0 else f.root+'/file%d.spec'%index
                    f.fixture['files'][path]={'@'+cl:f.item(f.source,2)}
                    shelf['files'].append({'path':path,'rev':2,'action':'edit','type':'text','content':f.enc(f.source)})
                def run(confirmations=()):
                    with redirect_stderr(io.StringIO()):
                        return snapshot(f.config,f.adapter(),f.package,{'start_time':'2026-10-22 13:26 +0900'},
                            b'[  123s] /x/rpmbuild/BUILD/pkg/src/main.c:1:1: error: fixture\n[  123s] 1 | int value;\n[  123s]   | ^\n',
                            'timeline-'+name,build_id='19091860',lists=f.lists,input_confirmations=confirmations)
                result=run()
                self.assertFalse(result['cross_branch']);self.assertEqual(result['cross_package_files'],[])
                self.assertEqual(len(result['files']),count)
                if name == 'plusplayer':
                    self.assertEqual(result['mode'],'仅诊断')
                    self.assertTrue(result['historical_input_unrecoverable'])
                    self.assertEqual(run(['old-digest'])['mode'],'仅诊断')
                    result=run([f.adapter().describe(scl)['digest']])
                self.assertEqual(result['mode'],'可分析')
                self.assertTrue(all(r['snapshot_provenance']=='原样叠加' for r in result['files']))

    def test_move_pair_other_actions_cross_package_and_mid_snapshot_mutation(self):
        f=self.f;shelf=f.fixture['shelves']['200'];new=f.root+'/src/moved.c'
        shelf['files']=[{'path':f.path,'action':'move/delete','rev':2,'type':'text','movedFile':new,'content':''},
            {'path':new,'action':'move/add','rev':0,'type':'text','movedFile':f.path,'content':f.enc(f.source)},
            {'path':'//example/another/source.c','action':'edit','rev':1,'type':'text','content':f.enc(b'foreign')}]
        adapter=f.adapter();log=b'/x/rpmbuild/BUILD/pkg-1/src/moved.c:1:1: error: fixture\nint value;\n^\n'
        result=snapshot(f.config,adapter,f.package,{'start_time':'2026-11-02 10:00'},log,'move',build_id='19091860',lists=f.lists)
        self.assertEqual(result['files'][0]['snapshot_provenance'],'原样叠加');self.assertEqual(len(result['cross_package_files']),1)
        shelf['files'][0]['rev']=1
        with redirect_stderr(io.StringIO()):
            result=snapshot(f.config,f.adapter(),f.package,{'start_time':'2026-11-02 10:00'},log,'bad-move',build_id='19091860',lists=f.lists)
        self.assertEqual(result['mode'],'仅诊断')
        shelf['files']=[{'path':f.path,'action':'integrate','rev':2,'type':'text','content':f.enc(f.source)}]
        result,_=f.snap();self.assertEqual(result['files'][0]['snapshot_provenance'],'原样叠加')
        shelf['files'][0]['rev']=1;result,_=f.snap();self.assertEqual(result['mode'],'仅诊断')
        adapter=f.adapter();real=adapter.describe;calls=[]
        def changed(scl):
            value=real(scl);calls.append(1)
            if len(calls)>1:value['digest']='changed'
            return value
        with patch.object(adapter,'describe',side_effect=changed),redirect_stderr(io.StringIO()):
            with self.assertRaises(FlowError) as e:snapshot(f.config,adapter,f.package,{'start_time':'2026-11-02 10:00'},log.replace(b'moved',b'main'),'changed',build_id='19091860',lists=f.lists)
        self.assertEqual(e.exception.reason,'shelve_changed_during_snapshot')

    def test_keywords_merge_keeps_unexpanded_input_and_corrupt_digest_fails(self):
        f=self.f;ancestor=b'int value;\n$Id$\nint middle;\nint fourth;\nint last;\n'
        f.fixture['files'][f.path]['#1']=f.item(ancestor,1)
        f.fixture['files'][f.path]['@100']=f.item(ancestor.replace(b'middle',b'changed'),2)
        shelf=f.fixture['shelves']['200']['files'][0];shelf.update(rev=1,type='text+k',content=f.enc(ancestor.replace(b'last',b'newlast')))
        result,_=f.snap();entry=result['files'][0]
        self.assertEqual(entry['snapshot_provenance'],'已合并');self.assertIn(b'$Id$',Path(entry['content']['path']).read_bytes())
        self.assertEqual(entry['keywords'],'关键字未展开')
        adapter=f.adapter();real=adapter.print_file
        def broken(path,revision,**kw):return b'bad' if revision=='@=200' else real(path,revision,**kw)
        with patch.object(adapter,'print_file',side_effect=broken):
            with self.assertRaises(FlowError) as e:snapshot(f.config,adapter,f.package,{'start_time':'2026-11-02 10:00'},b'/x/rpmbuild/BUILD/pkg/src/main.c:1:1: error: bad','bad-digest',build_id='19091860',lists=f.lists)
        self.assertEqual(e.exception.reason,'shelve_print_digest_mismatch')

    def test_info_mismatch_ticket_short_and_override_does_not_offer_login(self):
        f=self.f
        f.fixture['client']='existing-client'
        with self.assertRaises(FlowError) as e:f.adapter().info()
        self.assertEqual(e.exception.reason,'p4_context_mismatch')
        f.fixture['client']='*unknown*';f.fixture['ticket_seconds']=100
        with self.assertRaises(FlowError) as e:f.adapter().login_status()
        self.assertEqual(e.exception.reason,'p4_ticket_expiring')
        self.assertEqual(f.adapter().login_status(require_minimum=False),100)
        f.fixture['mode']='not_logged_in';f.adapter()
        with self.assertRaises(FlowError) as e:P4Adapter(f.config,tickets_override='/fixture/empty').login_status()
        self.assertNotIn('command',e.exception.details['todo']);self.assertIn('撤掉',e.exception.details['todo']['message'])

    def test_deleted_base_is_absent_for_shelve_add_and_interval_uses_earliest_cl(self):
        f=self.f
        f.fixture['files'][f.path]['@100']['action']='delete'
        f.fixture['shelves']['200']['files'][0].update(action='add',rev=0)
        result,_=f.snap();self.assertEqual(result['files'][0]['snapshot_provenance'],'原样叠加')
        f.fixture['files'][f.path]={'@90':f.item(f.source,1),'@200':f.item(f.source,2),
            '@2026/11/02:10:05:00':f.item(f.source,1)}
        f.fixture['shelves']['200']['files'][0].update(path=f.root+'/other.c',action='edit',rev=1)
        result=snapshot(f.config,f.adapter(),f.package,{'start_time':'2026-11-02 10:00'},
            b'/x/rpmbuild/BUILD/pkg/src/main.c:1:1: error: fixture\nint value;\n^\n','interval',build_id='19091860',
            log_metadata={'Last-Modified':'Mon, 02 Nov 2026 01:00:00 GMT','known_sync_cls':[150,90]})
        entry=result['files'][0]
        self.assertEqual(entry['candidate_interval'],['@90','@2026/11/02:10:05:00'])
        self.assertEqual(entry['snapshot_provenance'],'区间内一致');self.assertEqual(result['mode'],'仅诊断')


class ReadingEdgeTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Reading3a1Tests();self.f.setUp();self.addCleanup(self.f.doCleanups)

    def test_three_stall_conditions_without_old_poll_count_false_alarm(self):
        f=self.f;f.config.raw['poll'].update(expected_hours=.00001,arch_lag_s=10)
        o=f.observe();key=build_key(f.reader())
        with EventStore(f.config.data_root) as store:
            store.append(command_context('watch.observe'),'observation_recorded',{'build':key,'observed_at':o['observed_at'],'content_fingerprint':'old'},store.head())
            f.detail('running');o=f.observe(31)
            self.assertIn('running_but_stable',{t['reason'] for t in monitor_todos(f.config,store,key,o)})
            f.server.routes[f.server.report_path('armv7l')]=(200,f.server.routes[f.server.report_path('armv7l')][1]+b' ',{},0)
            f.observe(1)
            f.server.routes[f.server.report_path('armv7l')]=(200,f.server.routes[f.server.report_path('armv7l')][1]+b' ',{},0)
            o=f.observe(1);self.assertIn('report_continuously_changing',{t['reason'] for t in monitor_todos(f.config,store,key,o)})
            f.detail('failed');f.observe(1);o=f.observe(10)
            f.server.routes[f.server.report_path('x86_64')]=(404,b'',{},0)
            o=f.observe(11);self.assertNotIn('architecture_lag',{t['reason'] for t in monitor_todos(f.config,store,key,o)})
            o=f.observe(11);self.assertIn('architecture_lag',{t['reason'] for t in monitor_todos(f.config,store,key,o)})

    def test_variables_template_https_exact_placeholder_and_credential_block(self):
        f=self.f;raw=load_json(f.server.config_path)
        for url in ['http://127.0.0.1/build/{build_id}/variables','https://127.0.0.1/build/1/variables','https://127.0.0.1/{build_id}/build/{build_id}/variables','https://elsewhere.invalid/build/{build_id}/variables']:
            raw['cosmos']['variables_url_template']=url;f.server.config_path.write_text(json.dumps(raw))
            with self.assertRaises(FlowError):load_config(f.server.config_path)
        values={'PACKAGE_LIST':'Cookie: synthetic-value','SHELVE_LIST':'','BASE_REPOS':'base','BUILD_CONF':'conf','PRODUCT_REPOS':'product'} # credential-test-sample
        html=fixture.header()+variable_table(values)
        with self.assertRaises(FlowError) as e:variables(html.encode(),f.config,'19091860',f.server.url+'/build/19091860/variables')
        self.assertEqual(e.exception.reason,'build_input_credential_blocked')
        self.assertFalse(any(p.name=='PACKAGE_LIST.txt' for p in f.config.data_root.rglob('*')))

    def test_input_binding_and_inbox_done_are_human_events_and_immutable(self):
        f=self.f;f.observe();o=f.observe(10);key=build_key(f.reader())
        base=f.base/'base.txt';base.write_text('\n'.join(r['path']+'@'+r['cl'] for r in o['reports']['armv7l']['input_rows']))
        # Include unique host-side inputs as well; duplicated cross-arch rows are collapsed.
        rows={r['path']:r for report in o['reports'].values() for r in report['input_rows']}
        base.write_text('\n'.join(path+'@'+r['cl'] for path,r in rows.items()))
        result=decide(f.config,f.reader(),'bind-base-list',reason='fixture',base_file=str(base),context=CommandContext('bind-base-list',Category.HUMAN,True))
        self.assertEqual(result['kind'],'base_list_bound')
        with EventStore(f.config.data_root) as store:
            e=store.events(key,kinds=['base_list_bound'])[0];self.assertEqual(e['command'],'bind-base-list')
            store.append(command_context('workflow.tick'),'inbox_opened',{'build':key,'todo_key':'fixture-todo','todo':{'reason':'p4_unclassified','package':{'name':'x'}}},store.head())
        result=decide(f.config,f.reader(),'inbox.done',reason='fixture',todo_key='fixture-todo',context=CommandContext('inbox.done',Category.HUMAN,True))
        self.assertEqual(result['kind'],'inbox_closed')
        self.assertNotIn('fixture-todo',(f.config.data_root/'inbox.md').read_text())

class ManualAndRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Snapshot3a1Tests();self.f.setUp();self.addCleanup(self.f.doCleanups)

    def test_confirm_input_checks_current_describe_and_unknown_retry_gate_recovers(self):
        from types import SimpleNamespace
        from vd_cosmos_core.models import BuildRef
        from vd_fix_analyze.api import create_snapshot
        from vd_cosmos_core.read_ops import fetch_logs
        f=self.f;adapter=f.adapter();description=adapter.describe('200')
        reader=SimpleNamespace(build_ref=BuildRef('fixture','manual','19091860','cosmos'),
            observe=lambda _: {'reports':{'armv7l':{'packages':[f.package]}}})
        ctx=CommandContext('confirm-input',Category.HUMAN,True)
        result=decide(f.config,reader,'confirm-input',reason='fixture',package=f.package['key'],shelve_digest=description['digest'],context=ctx)
        self.assertEqual(result['kind'],'input_confirmed')
        with self.assertRaises(FlowError):decide(f.config,reader,'confirm-input',reason='fixture',package=f.package['key'],shelve_digest='stale',context=ctx)
        factory=lambda:FixtureReportReader(f.config,f.base/'manifest.json')
        logs=fetch_logs(factory())['logs'];log=logs[0]['path'];f.fixture['mode']='unknown';f.adapter()
        for _ in range(3):
            with self.assertRaises(FlowError) as e:create_snapshot(f.config,factory(),'provider','armv7l',log)
            self.assertEqual(e.exception.reason,'p4_unclassified')
        calls=(f.config.data_root/'fake-p4-calls.jsonl').read_bytes()
        with self.assertRaises(FlowError) as e:create_snapshot(f.config,factory(),'provider','armv7l',log)
        self.assertEqual(e.exception.reason,'p4_unclassified_retry_exhausted');self.assertEqual(calls,(f.config.data_root/'fake-p4-calls.jsonl').read_bytes())
        with EventStore(f.config.data_root) as store:
            todo=next(e['payload']['todo_key'] for e in store.events(build_key(factory()),kinds=['inbox_opened']) if e['payload']['todo']['reason']=='p4_unclassified')
        decide(f.config,factory(),'inbox.done',reason='fixture fixed',todo_key=todo,context=CommandContext('inbox.done',Category.HUMAN,True))
        f.fixture.pop('mode');f.adapter()
        self.assertEqual(create_snapshot(f.config,factory(),'provider','armv7l',log)['exit_code'],0)

    def test_archive_requires_actual_source_and_interval_stays_diagnostic(self):
        from vd_fix_analyze.snapshot import archive_sources
        f=self.f
        spec=f.root+'/packaging/pkg.spec';archive=f.root+'/pkg-1.tar.gz'
        f.fixture['files'][spec]={'@100':f.item(b'Name: pkg\nVersion: 1\nSource0: %{name}-%{version}.tar.gz\n')}
        adapter=f.adapter();inventory={r['depotFile']:r for r in adapter.list_files(f.root,'@100')}
        self.assertEqual(archive_sources(adapter,inventory,f.root,'@100',2097152),[])
        f.fixture['files'][archive]={'@100':f.item(b'fixture archive')};adapter=f.adapter()
        inventory={r['depotFile']:r for r in adapter.list_files(f.root,'@100')}
        self.assertEqual(archive_sources(adapter,inventory,f.root,'@100',2097152),[archive])
        f.fixture['files'][f.path]['@200']=f.item(f.source,2)
        f.fixture['files'][f.path]['@2026/11/02:10:05:00']=f.item(f.source,2)
        with redirect_stderr(io.StringIO()):
            result=snapshot(f.config,f.adapter(),f.package,{'start_time':'2026-11-02 10:00'},b'/x/rpmbuild/BUILD/pkg/src/main.c:1:1: error: fixture','no-list',build_id='19091860',lists=None,log_metadata={'first_failure_observed_at':'2026-11-02T10:00:00+09:00'})
        self.assertEqual(result['mode'],'仅诊断');self.assertEqual(result['files'][0]['snapshot_provenance'],'shelve 基础版本无法比对')

    def test_confirm_terminal_pty_override_echoes_build_and_records_withdraw(self):
        f=self.f
        cp=f.base/'config.json';raw=load_json(cp);raw['cosmos']['status_source']=load_json(CORE/'config.sample.json')['cosmos']['status_source'];cp.write_text(json.dumps(raw))
        config=load_config(cp);manifest=load_json(f.base/'manifest.json');manifest['detail_page']='detail.html'
        (f.base/'detail.html').write_text(detail_html('running','fixture-run'));(f.base/'manifest.json').write_text(json.dumps(manifest))
        reader=FixtureReportReader(config,f.base/'manifest.json');observed=reader.observe(reader.build_ref)
        from vd_cosmos_core.receipts import report_digests
        args=[sys.executable,str(REPO/'vd-fix-register/scripts/run.py'),'confirm-terminal','--config',str(cp),'--round','fixture-run','--manifest',str(f.base/'manifest.json'),'--reason','fixture','--report-digests',json.dumps(report_digests(observed['reports']))]
        def run(extra):
            pid,fd=pty.fork()
            if pid==0:
                os.execv(sys.executable,args+extra)
            output=b'';sent=False;build_sent=False;deadline=time.monotonic()+10
            try:
                while time.monotonic()<deadline:
                    readable,_,_=select.select([fd],[],[],.1)
                    if readable:
                        try:chunk=os.read(fd,65536)
                        except OSError:break
                        if not chunk:break
                        output+=chunk
                        if b'Confirm command' in output and not sent:
                            os.write(fd,b'yes\n');sent=True
                        if '输入构建号确认'.encode() in output and not build_sent:
                            os.write(fd,b'fixture-run\n');build_sent=True
                else:
                    os.kill(pid,9);self.fail('PTY command timed out')
                _,status=os.waitpid(pid,0)
                return os.waitstatus_to_exitcode(status),output.decode(errors='replace')
            finally:os.close(fd)
        code,out=run([]);self.assertEqual(code,4,out);self.assertIn('override_running_required',out)
        code,out=run(['--override-running']);self.assertEqual(code,0,out);self.assertIn('fixture-run',out)
        code,out=run(['--withdraw']);self.assertEqual(code,0,out)
        with EventStore(config.data_root) as store:
            events=store.events(build_key(reader),kinds=['terminal_confirmed','terminal_withdrawn'])
            self.assertEqual([e['kind'] for e in events],['terminal_confirmed','terminal_withdrawn'])
            self.assertTrue(events[0]['payload']['override_running'])
