"""Checkpoint A regressions. Network dependencies are loopback or replaced."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from helpers import CORE, REPO, bundle
import test_batch3a1 as fixtures
from vd_cosmos_core.build_inputs import parse_list, validate_root
from vd_cosmos_core.config import load_config
from vd_cosmos_core.dates import parse_datetime
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes
from vd_cosmos_core.journal import monitor_todos, write_todos
from vd_cosmos_core.commands import command_context
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.p4 import depot_path
from vd_cosmos_core import verify_b3a11 as verify
from vd_fix_analyze.snapshot import snapshot, classify_path
from vd_fix_analyze.source_check import diagnostics, compare_source, display
from vd_fix_analyze.api import review_basis


class SourceLineTests(unittest.TestCase):
    def diagnostic(self, source='x', caret='^', *, path='/p/a.cc', number=1, column=1, gutter=True, prefix='[  123s] '):
        return (prefix+f'{path}:{number}:{column}: error: example\n'+prefix+
                (f'{number} | ' if gutter else '')+source+'\n'+prefix+
                (' '*len(str(number))+' | ' if gutter else '')+caret+'\n').encode()

    def test_prefix_gutter_pair_caret_and_preserved_whitespace(self):
        for gutter in (True, False):
            d=diagnostics(self.diagnostic(' x', ' ^', column=2, gutter=gutter))[0]
            self.assertEqual(d['path'],'/p/a.cc')
            self.assertEqual(d['source_line'],' x')
            self.assertEqual(compare_source(b' x',d),'源码行一致')
        d=diagnostics(self.diagnostic('1 | x','^',gutter=False))[0]
        self.assertEqual(d['source_line'],'1 | x')
        self.assertEqual(compare_source(b'1 | x',d),'源码行一致')
        for caret in ['expression ^ other','^ text','| ^','~~~']:
            d=diagnostics(self.diagnostic(caret=caret,gutter=False))[0]
            self.assertIsNone(d['source_line'])
        d=diagnostics(self.diagnostic(prefix='TIME '),{'log_line_prefix_regex':r'^TIME '})[0]
        self.assertEqual(compare_source(b'x',d),'源码行一致')
        d=diagnostics(self.diagnostic(source='',caret='^'))[0]
        self.assertEqual(compare_source(b'',d),'源码行一致')

    def test_content_before_column_and_directional_trailing_whitespace(self):
        d=diagnostics(self.diagnostic(column=999))[0]
        self.assertEqual(compare_source(b'other',d),'不一致')
        self.assertEqual(compare_source(b'x',d),'未核对')
        d=diagnostics(self.diagnostic())[0]
        self.assertEqual(compare_source(b'x  ',d),'无法核对')
        d=diagnostics(self.diagnostic(source='x  '))[0]
        self.assertEqual(compare_source(b'x',d),'不一致')
        d=diagnostics(self.diagnostic(source='"a b"'))[0]
        self.assertEqual(compare_source(b'"a  b"',d),'不一致')
        self.assertEqual(compare_source(b'x',dict(d,line=99)),'不一致')

    def test_note_interleaving_and_source_ownership_restricted_candidates(self):
        prefix=b'[  12s] /p/other.cc:19:5: warning: first\n'
        d=diagnostics(prefix+self.diagnostic(path='/p/a.cc',source='mine'))[0]
        self.assertTrue(d['restricted'])
        candidates={'/p/a.cc':(b'mine',False),'/p/other.cc':(b'other',False)}
        self.assertEqual(compare_source(b'mine',d,candidates=candidates),'源码行一致')
        candidates['/p/other.cc']=(b'mine',False)
        self.assertEqual(compare_source(b'mine',d,candidates=candidates),'未核对')
        candidates={'/p/a.cc':(b'wrong',False),'/p/other.cc':(b'also wrong',False)}
        self.assertEqual(compare_source(b'wrong',d,candidates=candidates),'不一致')
        self.assertEqual(compare_source(b'mine',d,candidates={}), '未核对')
        self.assertEqual(compare_source(b'mine',d,candidates=candidates,max_candidates=1), '未核对')
        d=diagnostics(prefix+self.diagnostic(gutter=False))[0]
        self.assertEqual(compare_source(b'x',d,candidates=candidates),'未核对')
        # The note's own source must not be assigned to the preceding error.
        log=b'/p/a.cc:1:1: error: macro\n/p/b.cc:9:1: note: expanded\n9 | x\n  | ^\n'
        self.assertIsNone(diagnostics(log)[0]['source_line'])

    def test_half_lines_duplicate_position_line_mapping_and_orphan_source(self):
        d=diagnostics(self.diagnostic(source='x [  9s] y'))[0]
        self.assertEqual(compare_source(b'x [  9s] y',d),'未核对')
        for prefix in [b'broken /p/b.cc:1:1: error: cut\n',b'9:4: error: cut\n',b'with spaces: error: cut\n']:
            d=diagnostics(prefix+self.diagnostic())[0]
            self.assertEqual(compare_source(b'x',d),'未核对')
        ds=diagnostics(self.diagnostic()+self.diagnostic(source='y'))
        self.assertTrue(all(d.get('unchecked_reason') for d in ds))
        d=diagnostics(self.diagnostic(path='/p/grammar.y'))[0]
        self.assertEqual(compare_source(b'x',d),'未核对')
        d=diagnostics(self.diagnostic()+b'1 | other\n  | ^\n')[0]
        self.assertTrue(d['restricted'])

    def test_clang_byte_based_tabs_unicode_invalid_bytes_and_columns(self):
        raw='int 中;\tX'.encode()
        rendered,positions=display(raw)
        self.assertEqual(rendered,'int 中;'+' '*8+'X')
        self.assertEqual(positions[10],16)
        d=diagnostics(self.diagnostic(source=rendered,caret=' '*15+'^',column=10))[0]
        self.assertEqual(compare_source(raw,d),'源码行一致')
        self.assertEqual(display(b'\xff\x01')[0],'<FF><U+0001>')
        self.assertEqual(display('a\u0301中'.encode())[1][7],4)
        self.assertEqual(display(b'ab\tx',4)[0],'ab  x')

    def test_relative_paths_not_external_dependencies(self):
        for path in ('src/a.cc','../a.cc','./a.cc'):
            self.assertEqual(classify_path(path,'pkg')['kind'],'无法定位（相对路径）')
        self.assertEqual(classify_path('/usr/include/a.h','pkg')['kind'],'外部依赖')


class SnapshotFixTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.Snapshot3a1Tests();self.f.setUp();self.addCleanup(self.f.doCleanups)

    def test_real_shelve_notation_synonym_and_root_validation(self):
        markers=self.f.config.raw['cosmos']['branch_markers']
        path='//example/project/[INT]/packages/pkg/...'
        for sep in ('@','@='):
            entry=next(iter(parse_list(path+sep+'123',markers,shelved=True).values()))
            self.assertEqual(entry['cl'],'123');self.assertEqual(entry['notation'],sep)
        for root in ('//short/pkg','//a/b/c/d/...','//a/b/c/d/*','//a/b/c/d/p@x','//a/b/c/d/p%%x'):
            with self.assertRaises(FlowError):validate_root(root,5)
        self.assertEqual(validate_root('//a/b/c/d/pkg',5),'//a/b/c/d/pkg')

    def test_single_recursive_listing_limit_and_escaped_return_paths(self):
        f=self.f;adapter=f.adapter()
        self.assertEqual(len(adapter.list_files(f.root,'@100')),1)
        calls=[json.loads(x)['args'][7:] for x in (f.config.data_root/'fake-p4-calls.jsonl').read_text().splitlines()]
        self.assertEqual(calls,[['files','-m','20000',f.root+'/...@100']])
        f.config.raw['analyzer']['root_list_max_files']=1
        with self.assertRaises(FlowError) as e:f.adapter().list_files(f.root,'@100')
        self.assertEqual(e.exception.reason,'p4_listing_limit')
        f.config.raw['analyzer']['root_list_max_files']=20000
        path=f.root+'/src/a@b#c%d*.c'
        f.fixture['files']={path:{'@100':f.item(f.source,1)}}
        adapter=f.adapter();returned=adapter.list_files(f.root,'@100')[0]['depotFile']
        self.assertIn('%40',returned)
        self.assertEqual(adapter.print_file(returned,'@100',encoded=True),f.source)
        self.assertEqual(adapter.file_size(returned,'@100',encoded=True),len(f.source))
        self.assertEqual(adapter.files(returned,'@100',encoded=True)['records'][0]['depotFile'],returned)
        with self.assertRaises(FlowError):adapter.plan(['files',f.root+'/...@100'])

    def test_final_budget_does_not_count_merge_inputs_and_conflict_count(self):
        f=self.f;shelf=f.fixture['shelves']['200']['files'][0];shelf['rev']=1
        f.fixture['files'][f.path]['@100']=f.item(f.source.replace(b'int other;',b'int changed;'),2)
        shelf['content']=f.enc(f.source.replace(b'int last;',b'int added;'))
        f.config.raw['analyzer']['snapshot_max_total_bytes']=len(f.source)+20
        result,_=f.snap()
        self.assertEqual(result['files'][0]['snapshot_provenance'],'已合并')
        self.assertIsNotNone(result['files'][0]['content'])
        self.assertLess(sum(x.get('size',0) for x in result['files']),f.config.raw['analyzer']['snapshot_max_total_bytes'])
        shelf['content']=f.enc(f.source.replace(b'int other;',b'int conflict;'))
        result,notice=f.snap();self.assertIn('冲突 1 处',notice)
        from vd_fix_analyze import snapshot as module
        with patch.object(module,'merge',return_value={'kind':'内容冲突','content':None,'returncode':127,'inputs':[]}):
            result,notice=f.snap();self.assertIn('冲突 127 处（达到计数上限）',notice)
        f.fixture['files'][f.path]['#1']=f.item(b'x'*5000,1)
        f.config.raw['analyzer']['snapshot_max_file_bytes']=1000
        with self.assertRaises(FlowError) as e:f.snap()
        self.assertEqual(e.exception.reason,'merge_input_size_limit')

    def test_base_label_basis_and_review_blocks_edits(self):
        f=self.f;f.fixture['shelves']['200']['files'][0]['path']=f.root+'/other.c'
        timestamp='@2026/10/22:14:05:00'
        f.fixture['files'][f.path][timestamp]=f.item(f.source,2)
        def run():
            return snapshot(f.config,f.adapter(),f.package,{'start_time':'2026-11-02 10:00','profile':'target','build_conf':'conf'},
                b'[  99s] /x/rpmbuild/BUILD/pkg/src/main.c:1:1: error: fixture\n[  99s] 1 | int value;\n[  99s]   | ^\n',
                'basis',build_id='19091860',lists=f.lists,log_metadata={'Last-Modified':'Thu, 22 Oct 2026 05:00:00 GMT'})
        data=run();entry=data['files'][0]
        self.assertEqual(entry['snapshot_provenance'],'版本确定（base 清单）')
        self.assertEqual(entry['basis'],'list_cl_equals_build_time')
        f.fixture['files'][f.path][timestamp]['rev']=3
        data=run();entry=data['files'][0]
        self.assertEqual(entry['basis'],'vd_practice');self.assertEqual(entry['basis_note'],'依据 VD 线做法')
        previous=deepcopy(data);previous['files'][0]['basis_scope']['profile']='another-target'
        review_basis(data,previous)
        self.assertFalse(data['files'][0]['edits_eligible']);self.assertEqual(data['mode'],'仅诊断')
        self.assertEqual(data['files'][0]['basis_review'],'待复核')
        f.fixture['files'][f.path]['@100']=f.item(b'int WRONG;\n',2)
        data=run();self.assertEqual(data['files'][0]['basis_review'],'待复核')

    def test_expanded_login_command_checked_and_override_never_logs_in(self):
        f=self.f;f.config.raw['p4'].update(port='p4.example.invalid:1666',user='fixture-user')
        self.assertIn('-p p4.example.invalid:1666 -u fixture-user login',f.adapter().login_todo()['command'])
        f.config.raw['p4']['tickets_file']='/fixture/nondefault tickets'
        self.assertTrue(f.adapter().login_todo()['command'].startswith("P4TICKETS='/fixture/nondefault tickets' "))
        f.config.raw['p4']['user']='Cookie: prohibited-fixture' # credential-test-sample
        with self.assertRaises(FlowError) as e:f.adapter().login_todo()
        self.assertEqual(e.exception.code,4)


class TimestampTests(unittest.TestCase):
    def test_py310_compact_offset_and_parse_failure_is_recorded(self):
        expected=datetime(2026,10,22,4,26,tzinfo=timezone.utc).timestamp()
        self.assertEqual(parse_datetime('2026-10-22 13:26 +0900').timestamp(),expected)
        self.assertEqual(parse_datetime('2026-10-22T04:26:00Z').timestamp(),expected)
        f=fixtures.Reading3a1Tests();f.setUp();self.addCleanup(f.doCleanups)
        f.config.raw['poll']['expected_hours']=.00001
        observed=f.observe();f.detail('running');observed=f.observe(31)
        key='fixture'
        with EventStore(f.config.data_root) as store:
            for report in observed['reports'].values():report['headers']['start_time']='not-a-time'
            todos=monitor_todos(f.config,store,key,observed)
            self.assertIn('report_start_time_invalid',{t['reason'] for t in todos})
            write_todos(store,command_context('watch.observe'),store.head(),key,todos,f.config)
            self.assertTrue(any(e['payload']['todo']['reason']=='report_start_time_invalid' for e in store.events(kinds=['inbox_opened'])))

    def test_elapsed_manual_confirmation_waits_for_new_window(self):
        from vd_cosmos_core.stability import advance, maturity
        from vd_cosmos_core.receipts import log_binding
        clock = {'effective_state': '未知', 'unknown_since': '2026-11-01T00:00:00Z'}
        poll = {'interval_s': 10, 'settle_s': 30}
        record = advance(None,'sha','2026-11-01T00:00:00Z','parser',clock)
        record = advance(record,'sha','2026-11-01T00:01:00Z','parser',clock)
        self.assertEqual(maturity(record,poll,clock),(True,True))
        self.assertEqual(record['settled_basis'],'elapsed_window')
        manual = {'confirmed_at':'2026-11-01T00:01:00Z'}
        self.assertEqual(maturity(record,poll,clock,manual),(True,False))
        self.assertIsNone(record['settled_basis'])
        record=advance(record,'sha','2026-11-01T00:01:10Z','parser',clock)
        self.assertEqual(maturity(record,poll,clock,manual),(True,True))
        self.assertEqual(record['settled_basis'],'manual_terminal')



class AcceptanceScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);cp,_,_=bundle(self.root);self.config=load_config(cp)
        self.config.data_root.mkdir();self.env=verify.child_env(self.config.data_root)

    def test_hash_gate_before_config_or_network_and_all_help_contracts(self):
        run=subprocess.run(['bash',str(CORE/'scripts/verify_b3a11_real.sh'),'0'*40,'--config','missing'],capture_output=True,text=True)
        self.assertEqual(run.returncode,6);self.assertEqual(json.loads(run.stdout)['error'],'expected_commit_mismatch')
        self.assertIn('Python',run.stderr)
        result=verify.contracts(self.config,REPO,self.config.data_root,self.env)
        self.assertEqual({x['skill'] for x in result},set(verify.ROOTS))

    def test_offline_suite_same_interpreter_owned_tmp_and_output_gate(self):
        good=subprocess.CompletedProcess([],0,b'Python 3.10.12\nOK\n',b'')
        with patch.object(verify,'process',return_value=good) as runner:
            artifact=verify.offline_tests(self.config,REPO,self.config.data_root,self.env)
            self.assertEqual(Path(artifact['path']).read_bytes(),good.stdout)
            env=runner.call_args.args[2]
            self.assertEqual(env['PATH'].split(':')[0],str(Path(sys.executable).parent))
            self.assertEqual(Path(env['VD_COSMOS_TEST_TMPDIR']).parent,self.config.data_root)
        bad=subprocess.CompletedProcess([],0,b'Cookie: fixture-must-not-save',b'') # credential-test-sample
        with patch.object(verify,'process',return_value=bad):
            with self.assertRaises(FlowError) as e:verify.offline_tests(self.config,REPO,self.config.data_root,self.env)
        self.assertEqual(e.exception.code,4)
        self.assertEqual(Path(artifact['path']).read_bytes(),good.stdout)

    def test_seven_snapshots_login_failure_stops_without_login(self):
        logs=[{'key':{'arch':'armv7l','name':'p'+str(i),'path':'//fixture/'+str(i)},'path':'log'+str(i)} for i in range(7)]
        with patch.object(verify,'P4Adapter') as adapter,patch.object(verify,'command') as command:
            adapter.return_value.login_status.side_effect=FlowError(3,'p4_not_logged_in',todo={'reason':'p4_login_required','command':'p4 -p example.invalid -u fixture login'})
            with self.assertRaises(FlowError) as e:verify.snapshots(self.config,REPO,self.config.data_root,self.env,self.root/'config.json',logs)
            self.assertEqual(e.exception.code,3);command.assert_not_called()
        with patch.object(verify,'P4Adapter'),patch.object(verify,'command') as command:
            raw=json_bytes({'mode':'仅诊断','files':[{'diagnostic_line_match':'未核对','snapshot_provenance':'历史输入不可还原'}],
                            'locations':[{'classification':{'kind':'源码'}}]})
            path=self.config.data_root/'manifest.json';path.write_bytes(raw)
            command.return_value={'artifact':{'path':str(path),'sha256':digest(raw)}}
            rows=verify.snapshots(self.config,REPO,self.config.data_root,self.env,self.root/'config.json',logs)
            self.assertEqual(len(rows),7);self.assertEqual(command.call_count,8)
            self.assertTrue(all(r['status']=='仅诊断' for r in rows))
            self.assertEqual(command.call_args_list[0].args[-1][0],'base-list')
            self.assertTrue(all(c.args[-1][0]=='snapshot' for c in command.call_args_list[1:]))

    def test_acceptance_orchestration_fresh_roots_and_expanded_login_output(self):
        cp=self.root/'config.json';original=cp.read_bytes();head='a'*40
        args=SimpleNamespace(verified_commit=head,config=str(cp),saved_dir='saved',rows='rows.txt',links='links.txt',live_build_id=None,budget_s=None)
        logs=[{'key':{'arch':'armv7l','name':'p'+str(i),'path':'//fixture/'+str(i)}} for i in range(7)]
        def git(argv,**kw):return head+'\n' if 'rev-parse' in argv else b''
        order=[]
        def contract(*a):order.append('contracts');return []
        def tests(*a):order.append('tests');return {'checked':True}
        def read(*a):order.append('read');return {'exit_code':0,'B':{'logs':logs}}
        def no_login(*a):
            order.append('snapshots')
            raise FlowError(3,'p4_not_logged_in',todo={'reason':'p4_login_required','command':'p4 -p example.invalid -u fixture login'})
        with patch.object(verify.subprocess,'check_output',side_effect=git),patch.object(verify,'contracts',side_effect=contract),patch.object(verify,'offline_tests',side_effect=tests),patch.object(verify,'read_side',side_effect=read),patch.object(verify,'snapshots',side_effect=no_login),redirect_stderr(io.StringIO()) as output:
            first=verify.execute(args,REPO);second=verify.execute(args,REPO)
        self.assertEqual(first['exit_code'],3)
        self.assertEqual(len(first['summary']),7)
        self.assertIn('p4 -p example.invalid -u fixture login',output.getvalue())
        self.assertEqual(order,['contracts','tests','read','snapshots']*2)
        self.assertNotEqual(first['result_file']['path'],second['result_file']['path'])
        self.assertEqual(cp.read_bytes(),original)
        for result in [first,second]:
            path=Path(result['result_file']['path'])
            self.assertTrue(path.is_relative_to(self.config.data_root))
            self.assertEqual(json.loads(path.read_text())['commit'],head)
        # Prohibited values fail before copying the runtime configuration.
        raw=json.loads(original);raw['p4']['user']='Cookie: prohibited-fixture' # credential-test-sample
        cp.write_text(json.dumps(raw));before=set(self.config.data_root.rglob('*'))
        with patch.object(verify.subprocess,'check_output',side_effect=git):
            with self.assertRaises(FlowError) as e:verify.execute(args,REPO)
        self.assertEqual(e.exception.code,4)
        self.assertEqual(set(self.config.data_root.rglob('*')),before)

    def test_offline_failure_prevents_real_reads_and_p4(self):
        head='b'*40
        args=SimpleNamespace(verified_commit=head,config=str(self.root/'config.json'),saved_dir='saved',rows='rows',links='links',live_build_id=None,budget_s=None)
        def git(argv,**kw):return head+'\n' if 'rev-parse' in argv else b''
        with patch.object(verify.subprocess,'check_output',side_effect=git),patch.object(verify,'contracts',return_value=[]),patch.object(verify,'offline_tests',side_effect=FlowError(6,'offline_suite_failed')),patch.object(verify,'read_side') as read,patch.object(verify,'snapshots') as snap,redirect_stderr(io.StringIO()):
            result=verify.execute(args,REPO)
        self.assertEqual(result['exit_code'],6);read.assert_not_called();snap.assert_not_called()

    def test_mid_snapshot_login_expiry_retains_completed_rows_and_secret_keys_block(self):
        logs=[{'key':{'arch':'armv7l','name':'p'+str(i),'path':'//fixture/'+str(i)},'path':'log'+str(i)} for i in range(7)]
        raw=json_bytes({'mode':'可分析','files':[],'locations':[]})
        path=self.config.data_root/'manifest.json';path.write_bytes(raw)
        calls=[]
        def command(*args):
            if args[-1][0]=='base-list':return {}
            calls.append(1)
            if len(calls)==3:
                raise FlowError(3,'acceptance_skill_failed',todo={'reason':'p4_login_required','command':'p4 -p example.invalid -u fixture login'})
            return {'artifact':{'path':str(path),'sha256':digest(raw)}}
        with patch.object(verify,'P4Adapter'),patch.object(verify,'command',side_effect=command):
            with self.assertRaises(FlowError) as e:verify.snapshots(self.config,REPO,self.config.data_root,self.env,self.root/'config.json',logs)
        rows=e.exception.details['summary_rows']
        self.assertEqual(len(rows),7);self.assertEqual([r['status'] for r in rows],['可分析']*2+['未执行']*5)
        for name in ('password','access_token','BART_PASSWD'):
            with self.assertRaises(FlowError) as e:verify.reject_secret_settings({'p4':{name:'synthetic-private-value'}})
            self.assertEqual(e.exception.code,4)
        verify.reject_secret_settings({'p4':{'tickets_file':'/fixture/tickets','user':'fixture'},'prepush':{'credential_patterns':['secret']}})
