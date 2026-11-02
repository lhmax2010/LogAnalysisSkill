"""Batch 3a-1 contract tests: loopback HTTP, fixed synthetic pages and fake P4."""
import base64
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr
from helpers import CORE, REPO, bundle
from http_helpers import FixtureServer
from vd_cosmos_core.backends import FixtureReportReader
from vd_cosmos_core.build_inputs import variables, compare_lists, freeze, package_key
from vd_cosmos_core.commands import Category, CommandContext, command_context
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes, load_json
from vd_cosmos_core.http_reader import HTTPReportReader
from vd_cosmos_core.network_proof import prove_remote
from vd_cosmos_core.observation import detail_state
from vd_cosmos_core.p4 import P4Adapter, depot_path
from vd_cosmos_core.read_ops import fetch_logs
from vd_cosmos_core.receipts import task_input_digest, accepted_result_state
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.stability import advance, maturity, execution_clock
from vd_cosmos_core.versions import build_key
from vd_cosmos_workflow.api import tick, loop, status
from vd_fix_analyze.snapshot import snapshot, merge, compare_source, classify_path, locate
from vd_fix_analyze.api import unclassified_count
from vd_fix_register.api import decide


def header(word='failed', build='19091860', link=True):
    return '<div class="frame build-header"><div><div><i title="Build is '+word+'"></i></div></div>'+('<a href="/build/'+build+'?tab=x">own</a>' if link else '')+'<div title="Promoted to build 999"><a href="/build/999" title="Build is successful">1.2.3456789</a></div></div>'


class Reading3a1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.server=FixtureServer(self.base);self.addCleanup(self.server.close)
        self.config=load_config(self.server.config_path)
        self.config.raw['poll'].update(interval_s=10,settle_s=30,stopped_interval_s=.001,retry_after_event_s=.001)
        self.at=datetime(2026,11,2,tzinfo=timezone.utc)

    def reader(self):
        return HTTPReportReader(self.config,'19091860',clock=lambda:self.at.isoformat())

    def observe(self, delta=0):
        self.at+=timedelta(seconds=delta)
        r=self.reader();return r.observe(r.build_ref)

    def detail(self, word):
        self.server.routes['/build/19091860']=(200,header(word).encode(),{},0)

    def test_terminal_epoch_unknown_since_restart_and_running_never_elapsed(self):
        self.detail('running')
        self.observe();self.assertFalse(self.observe(100)['reports']['armv7l']['settled'])
        self.detail('failed');o=self.observe(1)
        self.assertFalse(o['reports']['armv7l']['settled'])
        epoch=o['execution_evidence']['terminal_epoch']
        o=self.observe(10);self.assertEqual(o['reports']['armv7l']['settled_basis'],'trusted_terminal')
        self.assertEqual(o['execution_evidence']['terminal_epoch'],epoch)
        self.server.routes['/build/19091860']=(500,b'',{},0)
        o=self.observe(1000);unknown=o['execution_evidence']['unknown_since']
        self.assertFalse(o['reports']['armv7l']['settled']);self.assertIsNone(o['execution_evidence']['terminal_epoch'])
        o=self.observe(30);self.assertEqual(o['reports']['armv7l']['settled_basis'],'elapsed_window')
        self.assertEqual(o['execution_evidence']['unknown_since'],unknown)

    def test_header_identity_three_levels_promotion_class_tokens_and_resolved_links(self):
        source=self.config.raw['cosmos']['status_source']
        run=lambda html:detail_state(html.encode(),source,'19091860',self.server.url+'/build/19091860')
        self.assertEqual(run(header())['identity'],'strong')
        self.assertEqual(run(header(link=False))['identity'],'weak')
        for html in [header().replace('build-header','build-header-other'),header()+header(),header(build='123'),header().replace('/build/19091860?tab=x','https://other.invalid/build/19091860'),header().replace('</i>','</i><i title="Build is running"></i>',1)]:
            self.assertEqual(run(html)['identity'],'identity_mismatch')
        self.assertEqual(run(header().replace('/build/19091860?tab=x','19091860'))['identity'],'strong')
        raw=load_json(self.server.config_path);raw['cosmos']['status_source']['header_rule']='ancestor-of-first-status'
        self.server.config_path.write_text(json.dumps(raw))
        with self.assertRaises(FlowError) as e:load_config(self.server.config_path)
        self.assertEqual(e.exception.reason,'header_rule_migration_required')

    def test_elapsed_final_gate_closed_terminal_invalidates_revalidation_result_identity(self):
        self.server.routes['/build/19091860']=(500,b'',{},0)
        tick(self.config,self.reader);self.at+=timedelta(seconds=30)
        tick(self.config,self.reader);tick(self.config,self.reader)
        self.assertEqual(tick(self.config,self.reader)['phase'],'结果已拉取')
        o=self.observe();self.assertFalse(o['terminal_prerequisite_met'])
        logs=fetch_logs(self.reader())['logs'];self.assertTrue(all(l['final'] for l in logs))
        self.assertTrue(all(l['settled_basis']=='elapsed_window' and l['terminal_basis'] is None for l in logs))
        old=logs[0]['sha256'];self.detail('failed');self.at+=timedelta(seconds=1)
        self.assertNotEqual(tick(self.config,self.reader)['phase'],'结果已拉取')
        self.at+=timedelta(seconds=10)
        tick(self.config,self.reader);tick(self.config,self.reader);tick(self.config,self.reader)
        final=fetch_logs(self.reader())['logs'];self.assertEqual(final[0]['sha256'],old)
        package=final[0]['key'];d=task_input_digest(old,'snapshot','segments','rules')
        received={'package':package,'validated':True,'task_input_digest':d}
        self.assertEqual(accepted_result_state(received,package,d),'有效')
        self.assertEqual(accepted_result_state(received,package,task_input_digest('changed','snapshot','segments','rules')),'输入已过期')
        with EventStore(self.config.data_root) as store:
            self.assertEqual(sum(e['payload']['todo']['reason']=='analysis_pending' for e in store.events(kinds=['inbox_opened'])),1)

    def test_manual_window_survives_running_failure_and_expires_on_digest_or_withdraw(self):
        self.detail('running');o=self.observe();key=build_key(self.reader())
        context=CommandContext('confirm-terminal',Category.HUMAN,True)
        with EventStore(self.config.data_root) as store:
            event=store.append(context,'terminal_confirmed',{'build':key,'report_digests':{a:r['evidence']['sha256'] for a,r in o['reports'].items()}},store.head())
            at=store.events(key,latest=True)[0]['created_at']
        self.at=datetime.fromisoformat(at.replace('Z','+00:00'))+timedelta(seconds=1)
        self.observe();o=self.observe(10)
        self.assertEqual(o['reports']['armv7l']['settled_basis'],'manual_terminal')
        self.assertTrue(o['execution_evidence']['manual_conflict'])
        logs=fetch_logs(self.reader())['logs'];self.assertTrue(all(l['final'] and l['terminal_basis']['event_id']==event for l in logs))
        self.server.routes['/build/19091860']=(500,b'',{},0)
        self.assertEqual(self.observe(1)['effective_terminal_basis']['event_id'],event)
        self.detail('failed');self.observe(1)
        self.assertEqual(self.observe(10)['reports']['armv7l']['settled_basis'],'manual_terminal')
        self.detail('running');self.observe(1)
        path=self.server.report_path('armv7l');status,body,headers,delay=self.server.routes[path]
        self.server.routes[path]=(status,body+b' ',headers,delay)
        self.assertIsNone(self.observe(1)['effective_terminal_basis'])
        self.server.routes[path]=(status,body,headers,delay)
        self.assertIsNone(self.observe(1)['effective_terminal_basis'])
        with EventStore(self.config.data_root) as store:
            store.append(context,'terminal_withdrawn',{'build':key},store.head())
        self.assertIsNone(self.observe()['effective_terminal_basis'])

    def test_elapsed_then_running_rejects_old_snapshot_and_changed_log_expires_result(self):
        from vd_fix_analyze.api import create_snapshot
        self.server.routes['/build/19091860']=(500,b'',{},0)
        tick(self.config,self.reader);self.at+=timedelta(seconds=30)
        for _ in range(3):tick(self.config,self.reader)
        old=fetch_logs(self.reader())['logs'][0];content=Path(old['path']).read_bytes()
        original=task_input_digest(old['sha256'],'snapshot','segments','rules')
        result={'package':old['key'],'validated':True,'task_input_digest':original}
        self.detail('running');self.at+=timedelta(seconds=1)
        self.assertNotEqual(tick(self.config,self.reader)['phase'],'结果已拉取')
        with self.assertRaises(FlowError) as error:
            create_snapshot(self.config,self.reader(),old['key']['name'],old['key']['arch'],old['path'])
        self.assertEqual(error.exception.reason,'final_log_required')
        for path in {r['path'] for r in self.server.requests if r['path'].endswith('/log.txt')}:
            self.server.routes[path]=(200,b'new compiler error\n',{},0)
        self.detail('failed');self.at+=timedelta(seconds=1);tick(self.config,self.reader)
        self.at+=timedelta(seconds=10)
        for _ in range(3):tick(self.config,self.reader)
        current=next(l for l in fetch_logs(self.reader())['logs'] if l['key']==old['key'])
        self.assertNotEqual(current['sha256'],old['sha256'])
        self.assertEqual(Path(old['path']).read_bytes(),content)
        self.assertEqual(accepted_result_state(result,old['key'],task_input_digest(current['sha256'],'snapshot','segments','rules')),'输入已过期')
        self.assertIsNotNone(current['first_failure_observed_at'])
        with EventStore(self.config.data_root) as store:
            self.assertEqual(sum(e['payload']['todo']['reason']=='analysis_pending' for e in store.events(kinds=['inbox_opened'])),1)

    def test_wire_strict_trailers_close_delimiting_and_production_not_a_log(self):
        reader=self.reader();path='/wire'
        def route(raw):
            def send(h):
                h.connection.sendall(raw);h.close_connection=True
            self.server.wire_routes[path]=send
        for tail in [b'1\r\nx\r\n0\r\n',b'1\r\nx\r\n0\r\nFoo: bar',b'1\r\nxXX0\r\n\r\n',b'+1\r\nx\r\n0\r\n\r\n']:
            route(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'+tail)
            with self.assertRaises(FlowError):reader.transport.get(self.server.url+path,100,truncate=True)
        route(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nx\r\n0\r\nX-Fixture: yes\r\n\r\n')
        self.assertTrue(reader.transport.get(self.server.url+path,100)['transfer_complete'])
        route(b'HTTP/1.0 200 OK\r\n\r\ncompiler log')
        self.assertFalse(reader.transport.get(self.server.url+path,100,truncate=True)['transfer_complete'])
        with self.assertRaises(FlowError):reader.transport.get(self.server.url+path,100)
        self.server.wire_routes.pop(path)
        self.server.routes[path]=(200,b'<html><form><input type="password"></form></html>',{'Content-Type':'text/html'},0)
        with self.assertRaises(FlowError) as e:reader.transport.get(self.server.url+path,100,truncate=True)
        self.assertEqual(e.exception.reason,'not_a_log')
        self.server.routes[path]=(200,b'compiler: text contains <html> in source',{},0)
        response=reader.transport.get(self.server.url+path,100,truncate=True)
        self.assertEqual(response['response']['peer_ip'],'127.0.0.1')
        self.assertEqual(response['response']['local_ip'],'127.0.0.1')

    def test_completed_log_tamper_invalidates_and_max_limit_changes_evaluation(self):
        self.observe();self.observe(10)
        for _ in range(3):tick(self.config,self.reader)
        logs=fetch_logs(self.reader())['logs'];Path(logs[0]['path']).write_text('tampered')
        self.assertNotEqual(status(self.config,self.reader())['phase'],'结果已拉取')
        result=tick(self.config,self.reader);self.assertNotEqual(result['action'],'none')

    def test_loop_uncounted_and_counted_segments_starvation_and_fatal_errors(self):
        self.config.raw['poll']['interval_s']=.001
        sequence=[FlowError(6,'operation_locked'),FlowError(6,'operation_locked'),FlowError(6,'stale_head',intervening_event=True),FlowError(6,'operation_locked')]
        with patch('vd_cosmos_workflow.api.tick',side_effect=sequence):
            result=loop(self.config,self.reader,max_ticks=4)
        self.assertEqual(result['skip_count'],3)
        self.assertEqual(len({r['contention_id'] for r in result['tick_results']}),1)
        self.config.raw['loop']['max_uncounted_skip_s']=.0001
        with patch('vd_cosmos_workflow.api.tick',side_effect=FlowError(6,'stale_head',intervening_event=True)):
            result=loop(self.config,self.reader,max_ticks=3)
        self.assertEqual(result['skip_count'],0)
        with EventStore(self.config.data_root) as store:
            self.assertEqual(sum(e['payload']['todo']['reason']=='loop_starved' for e in store.events(kinds=['inbox_opened'])),1)
        with patch('vd_cosmos_workflow.api.tick',side_effect=FlowError(6,'corrupt')):
            with self.assertRaises(FlowError):loop(self.config,self.reader,max_ticks=2)

    def test_resolved_local_and_mapped_addresses_are_rejected_without_connection(self):
        for ip in ['127.0.0.1','::1','::ffff:127.0.0.1','0.0.0.0','169.254.1.1','192.0.2.10']:
            from vd_cosmos_core.network_proof import address
            with patch('socket.getaddrinfo',return_value=[(2,1,6,'',(ip,80))]),patch('vd_cosmos_core.network_proof.local_addresses',return_value={address('192.0.2.10')}):
                with self.assertRaises(FlowError):prove_remote('http://fixture.invalid',{'no_proxy_hosts':['fixture.invalid']})
        with self.assertRaises(FlowError):prove_remote('http://fixture.invalid',{'no_proxy_hosts':[]})


class Inputs3a1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);cp,_,_=bundle(self.base)
        self.config=load_config(cp)
        self.config.raw['cosmos']['status_source']=load_json(CORE/'config.sample.json')['cosmos']['status_source']

    def test_appendix_i_2245_base_545_shelve_and_credential_variable_never_written(self):
        base=['//example/[INT]/packages/p%04d/...@100'%i for i in range(2245)]
        shelves=['//example/[INT]/packages/p%04d/...@=200'%i for i in range(545)]
        rows=[{'path':'//example/[INT]/packages/p%04d/...'%i,'cl':'200' if i<545 else '100','shelve':i<545} for i in range(2244)]
        values={'PACKAGE_LIST':'\n'.join(base),'SHELVE_LIST':'\n'.join(shelves),'BASE_REPOS':'https://u:secret@example.invalid/base','BUILD_CONF':'//example/build.conf@1','PRODUCT_REPOS':'https://example.invalid/product'}
        html=header()+'<table>'+''.join('<tr><td>'+k+'</td><td><pre>'+v+'</pre></td></tr>' for k,v in values.items())+'<tr><td>BART_PASSWD</td><td>fixture-do-not-retain-value</td></tr></table>' # credential-test-sample
        safe,note=variables(html.encode(),self.config,'19091860','https://example.invalid/build/19091860/variables')
        result=freeze(self.config,'fixture',safe,{'armv7l':{'input_rows':rows}},source='variables_page',note=note)
        self.assertEqual(len(result['base']),2245);self.assertEqual(len(result['shelve']),545);self.assertEqual(len(result['extra_base_packages']),1)
        self.assertEqual(note['note'],'已去除凭据')
        for path in self.config.data_root.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'BART_PASSWD',path.read_bytes());self.assertNotIn(b'fixture-do-not-retain-value',path.read_bytes()) # credential-test-sample
                self.assertNotIn(b'u:secret@',path.read_bytes())
        with self.assertRaises(FlowError):variables(html.replace('</table>','<tr><td>BUILD_CONF</td><td>other</td></tr></table>').encode(),self.config,'19091860','https://example.invalid/build/19091860/variables')
        safe['PACKAGE_LIST']+='\n//example/new/...@1'
        with self.assertRaises(FlowError) as e:freeze(self.config,'fixture',safe,{'armv7l':{'input_rows':rows}},source='variables_page')
        self.assertEqual(e.exception.reason,'immutable_build_inputs_changed')

    def test_pairing_exact_segments_duplicate_cross_branch_and_shelve_tuple_mismatch(self):
        markers=self.config.raw['cosmos']['branch_markers']
        self.assertEqual(package_key('//example/[INT]//[MAIN]/p/...',markers),'/example/[MAIN]/p')
        self.assertNotEqual(package_key('//example/[MAIN]/p',markers),package_key('//example/[TIZENPROD_Prj]/p',markers))
        rows={'a':{'input_rows':[{'path':'//example/[FET]/p/...','cl':'20','shelve':True}]}}
        base='//example/[INT]/p/...@10'
        self.assertTrue(compare_lists(base,'//example/[FET]/p/...@=20',rows,markers)['shelve_list_verified'])
        self.assertIn('未取得原始',compare_lists(base,None,rows,markers)['note'])
        for bad in [base+'\n'+base,base+'\n//example/[FET]/p/...@11']:
            with self.assertRaises(FlowError):compare_lists(bad,None,rows,markers)
        with self.assertRaises(FlowError):compare_lists(base,'//example/[FET]/p/...@=21',rows,markers)


class Snapshot3a1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);cp,mp,_=bundle(self.base)
        self.config=load_config(cp);self.config.data_root.mkdir()
        self.config.raw['p4']['executable']=str(CORE/'fixtures/p4/fake_p4.py')
        self.root='//example/[INT]/pkg';self.path=self.root+'/src/main.c'
        self.package={'key':{'arch':'armv7l','name':'pkg','path':self.root+'/...'},'cl':'200','shelve':True}
        self.lists={'base':{package_key(self.root,self.config.raw['cosmos']['branch_markers']):{'root':self.root,'cl':'100'}}}
        self.source=b'int value;\nint other;\nint middle;\nint fourth;\nint last;\n'
        self.fixture={'files':{self.path:{'@100':self.item(self.source,2),'#1':self.item(self.source,1)}},
                      'shelves':{'200':{'files':[dict(path=self.path,rev=2,action='edit',type='text',content=self.enc(self.source))]}}}

    def enc(self,b):return base64.b64encode(b).decode()
    def item(self,b,rev=1,kind='text'):return {'rev':rev,'type':kind,'content':self.enc(b)}
    def adapter(self):
        (self.config.data_root/'fake-p4.json').write_text(json.dumps(self.fixture));return P4Adapter(self.config)
    def snap(self):
        with redirect_stderr(io.StringIO()) as err:
            result=snapshot(self.config,self.adapter(),self.package,{'start_time':'2026-11-02 10:00'},b'/x/rpmbuild/BUILD/pkg-1/src/main.c:1:1: error: fixture\nint value;\n^\n', 'snap',build_id='19091860',lists=self.lists)
        return result,err.getvalue()

    def test_fake_p4_context_protocol_real_error_shapes_signal_partial_unknown_and_forbidden(self):
        adapter=self.adapter();self.assertEqual(adapter.info()['clientName'],'*unknown*')
        self.assertEqual(adapter.files(self.path+'missing','@100')['category'],'file_missing')
        self.assertTrue(adapter.describe('999')['historical_missing'])
        self.fixture['shelves']['200']['status']='submitted';self.assertTrue(self.adapter().describe('200')['historical_missing'])
        for mode,expected in [('killed','p4_process_signal'),('truncated','p4_incomplete_output'),('unknown','p4_unclassified'),('not_logged_in','p4_not_logged_in')]:
            self.fixture['mode']=mode
            with self.assertRaises(FlowError) as e:self.adapter().info()
            self.assertEqual(e.exception.reason,expected)
        for args in [['set'],['login'],['client','-i'],['submit']]:
            with self.assertRaises(FlowError):adapter.plan(args)
        self.assertEqual(depot_path('//example/a@#%*'),'//example/a%40%23%25%2A')
        with self.assertRaises(FlowError):depot_path('//example/...')
        self.assertNotIn('command',P4Adapter(self.config,tickets_override='/fixture/empty').login_todo())

    def test_shelve_overlay_merge_conflict_advanced_add_delete_move_and_cross_branch(self):
        result,_=self.snap();self.assertEqual(result['mode'],'可分析');self.assertEqual(result['files'][0]['snapshot_provenance'],'原样叠加')
        shelf=self.fixture['shelves']['200']['files'][0];shelf['rev']=1
        self.fixture['files'][self.path]['@100']=self.item(self.source.replace(b'int other;', b'int changed;'),2)
        shelf['content']=self.enc(self.source.replace(b'int last;', b'int added;'))
        result,notice=self.snap();self.assertEqual(result['files'][0]['snapshot_provenance'],'已合并');self.assertIn('[shelve 已自动合并]',notice);self.assertTrue(result['notices'][0]['hint'])
        shelf['content']=self.enc(self.source.replace(b'int other;', b'int conflict;'));result,_=self.snap();self.assertEqual(result['mode'],'仅诊断');self.assertEqual(result['files'][0]['merge_result'],'内容冲突')
        shelf['rev']=3;result,_=self.snap();self.assertEqual(result['files'][0]['snapshot_provenance'],'shelve 基础版本超前')
        shelf.update(action='add',rev=0,content=self.enc(self.source));result,_=self.snap();self.assertEqual(result['mode'],'仅诊断')
        self.fixture['files'].pop(self.path);result,_=self.snap();self.assertEqual(result['files'][0]['snapshot_provenance'],'原样叠加')
        self.fixture['files'][self.path]={'@100':self.item(self.source,2)};shelf.update(action='delete',rev=2)
        result,_=self.snap();self.assertTrue(result['files'][0]['deleted']);self.assertEqual(result['mode'],'仅诊断')
        shelf.update(action='edit',rev=2)
        self.package['key']['path']=self.root.replace('[INT]','[FET]')+'/...';shelf['path']=self.path.replace('[INT]','[FET]')
        result,_=self.snap();self.assertEqual(result['files'][0]['snapshot_provenance'],'跨分支 shelve，来源无法核实')

    def test_history_time_confirm_digest_keyword_and_exact_nonascii_line_rules(self):
        self.fixture['shelves']['200']['updated']='2026/11/02 10:00:01'
        result,_=self.snap();self.assertEqual(result['mode'],'仅诊断')
        adapter=self.adapter();d=adapter.describe('200')['digest']
        result=snapshot(self.config,adapter,self.package,{'start_time':'2026-11-02 10:00'},b'/x/rpmbuild/BUILD/pkg-1/src/main.c:1:1: error: fixture\nint value;\n^\n','confirmed',build_id='19091860',lists=self.lists,input_confirmations=[d])
        self.assertEqual(result['mode'],'可分析')
        for raw,shown,wanted in [(b'"a  b"','"a b"','不一致'),('u8"中文"'.encode(),'u8"한"','不一致'),(b'\xff','<FF>','源码行一致'),(b'\tvalue','        value','源码行一致')]:
            self.assertEqual(compare_source(raw,{'line':1,'source_line':shown}),wanted)
        self.assertEqual(compare_source(b'$Id$',{'line':1,'source_line':'$Id$'},merged=True),'无法核对')
        self.assertEqual(compare_source(b'x',{'line':1,'source_line':'2 | x'}),'不一致')
        self.assertEqual(compare_source(b'x',{'line':1,'source_line':None}),'未核对')

    def test_paths_limits_symlink_and_merge_tool_error(self):
        external=classify_path('/usr/include/main.c','pkg');self.assertIsNone(locate(external,self.root,{self.path})[0])
        own=classify_path('/x/BUILDROOT/PKG-1/usr/include/p/a.h','pkg');self.assertTrue(own['inferred'])
        self.assertEqual(classify_path('/x/BUILDROOT/other-1/usr/include/a.h','pkg')['kind'],'外部依赖')
        self.assertEqual(locate({'kind':'源码','relative':'build/config.h'},self.root,set())[1],'生成文件')
        self.config.raw['analyzer']['snapshot_max_file_bytes']=1
        result,_=self.snap();self.assertEqual(result['mode'],'仅诊断');self.assertIsNone(result['files'][0]['content'])
        self.config.raw['analyzer']['snapshot_max_file_bytes']=2097152
        self.fixture['files'][self.path]['@100']['type']='symlink';self.fixture['shelves']['200']['files'][0]['type']='symlink'
        result,_=self.snap();self.assertIn('symlink_target',result['files'][0]);self.assertFalse(any(p.is_symlink() for p in self.config.data_root.rglob('*')))
        for code,wanted in [(1,'内容冲突'),(127,'内容冲突'),(128,'工具错误'),(255,'工具错误'),(-9,'工具错误')]:
            with patch('vd_fix_analyze.snapshot.subprocess.run',return_value=subprocess.CompletedProcess([],code,b'',b'')):
                self.assertEqual(merge(self.config,'merge-fixture',b'a',b'b',b'c')['kind'],wanted)

    def test_persisted_unknown_retry_counter_and_manual_done_reset(self):
        package=self.package['key'];context=command_context('analyze.snapshot')
        with EventStore(self.config.data_root) as store:
            for _ in range(3):store.append(context,'snapshot_failed',{'build':'fixture','package':package,'error':'p4_unclassified'},store.head())
        with EventStore(self.config.data_root) as store:
            self.assertEqual(unclassified_count(store.events(),package),3)
            human=CommandContext('inbox.done',Category.HUMAN,True)
            store.append(human,'inbox_closed',{'build':'fixture','package':package,'todo_reason':'p4_unclassified'},store.head())
            self.assertEqual(unclassified_count(store.events(),package),0)

    def test_manual_entrypoints_non_tty_and_closed_database_are_classified(self):
        for command in ['confirm-terminal','confirm-input','bind-base-list','inbox.done']:
            process=subprocess.run([sys.executable,str(REPO/'vd-fix-register/scripts/run.py'),command,'--config','missing','--round','1','--reason','fixture'],capture_output=True,text=True,start_new_session=True)
            self.assertEqual(process.returncode,2,process.stdout)
            self.assertEqual(json.loads(process.stdout)['error'],'terminal_required')
        store=EventStore(self.config.data_root);store.close()
        for call in [store.head,store.events]:
            with self.assertRaises(FlowError) as e:call()
            self.assertEqual(e.exception.reason,'corrupt')
