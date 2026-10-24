"""Batch 2.1 adversarial wire, maturity, recovery and acceptance tests."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import copy
import json
import multiprocessing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import signal
import select
import socket
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from helpers import CORE, REPO
from http_helpers import FixtureServer
from vd_cosmos_core.baselines import apply_rows_coverage
from vd_cosmos_core.commands import command_context, CommandContext, Category
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes, load_json
from vd_cosmos_core.http_reader import HTTPReportReader, index_fingerprint
from vd_cosmos_core.journal import write_todos, monitor_todos
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.state import EventStore, append_retry
from vd_cosmos_core.transport import HTTPTransport
from vd_cosmos_core.versions import build_key, parsing_digest
from vd_cosmos_workflow.api import tick, loop, projection, status


def isolated_checkout(destination):
    destination.mkdir()
    for name in ['vd-cosmos-core', 'vd-cosmos-watch', 'vd-cosmos-fetch', 'vd-cosmos-workflow']:
        shutil.copytree(REPO/name,destination/name,ignore=shutil.ignore_patterns('.runtime','.devtools','__pycache__','*.pyc'))
    env={**os.environ,'GIT_AUTHOR_NAME':'Hao Lin','GIT_AUTHOR_EMAIL':'hao.lin@samsung.com',
         'GIT_COMMITTER_NAME':'Hao Lin','GIT_COMMITTER_EMAIL':'hao.lin@samsung.com'}
    for cmd in [['git','init','-q','-b','vd-cosmos-loganalyzer'],['git','add','.'],['git','commit','-qm','fixture snapshot']]:
        subprocess.run(cmd,cwd=destination,env=env,check=True,capture_output=True)
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=destination,text=True).strip()


def crash_after_action(config_path, wanted):
    config=load_config(config_path)
    def crash(step):
        if step==wanted:os._exit(29)
    tick(config,lambda:HTTPReportReader(config,'19091860'),after_action=crash)


def hold_lock(root, key, acquired, release):
    with OperationLock(Path(root),'round',key):
        acquired.set();release.wait(10)


class Batch21Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name);self.server=FixtureServer(self.base);self.addCleanup(self.server.close)
        self.config=load_config(self.server.config_path)
        self.at=datetime(2026,10,24,tzinfo=timezone.utc)
        self.config.raw['poll'].update(interval_s=10,settle_s=100,stopped_interval_s=.02)
        original=socket.getaddrinfo
        def guarded(host,*args,**kwargs):
            if host not in {'127.0.0.1','localhost'}:raise AssertionError('non-loopback DNS attempted')
            return original('127.0.0.1' if host=='localhost' else host,*args,**kwargs)
        guard=patch('socket.getaddrinfo',side_effect=guarded);guard.start();self.addCleanup(guard.stop)

    def reader(self, rows=None):
        return HTTPReportReader(self.config,'19091860',rows,clock=lambda:self.at.isoformat())

    def observe(self, seconds=0, rows=None):
        self.at+=timedelta(seconds=seconds)
        r=self.reader(rows);return r.observe(r.build_ref)

    def ready(self):
        self.observe();return self.observe(10)

    def arm(self, data):
        self.server.routes[self.server.report_path('armv7l')]=(200,data,{},0)

    def test_all_document_redirects_refused_before_target_request_and_index_fingerprint(self):
        for page in [self.server.report_path('armv7l'),'/build/19091860']:
            original=self.server.routes.get(page)
            self.server.routes[page]=(302,b'',{'Location':'/login'},0)
            o=self.observe()
            if page.startswith('/build'):
                self.assertEqual(o['execution_evidence']['failure'],'redirect_refused');self.assertEqual(o['exit_code'],0)
            else:self.assertEqual(o['reports']['armv7l']['error'],'redirect_refused')
            self.assertFalse(any(r['path']=='/login' for r in self.server.requests))
            if original:self.server.routes[page]=original
            else:self.server.routes.pop(page)
        self.server.routes[self.server.report_path('armv7l')]=(404,b'',{},0)
        for body in [b'<html>login</html>',b'<form><a href="123/">123</a></form>',b'<a href="123/">123</a><input type=password>']:
            self.server.routes['/reports/b860/']=(200,body,{},0)
            self.assertEqual(self.observe()['reports']['armv7l']['error'],'index_unverified')
        self.server.routes['/reports/b860/']=(302,b'',{'Location':'/login'},0)
        self.assertEqual(self.observe()['reports']['armv7l']['error'],'index_unverified')
        self.assertFalse(any(r['path']=='/login' for r in self.server.requests))

    def test_log_redirect_port_host_and_path_refused_with_zero_target_requests(self):
        other_dir=self.base/'other';other_dir.mkdir();other=FixtureServer(other_dir);self.addCleanup(other.close)
        o=self.ready();r=self.reader();r._observed=o
        package=next(p for p in o['reports']['armv7l']['packages'] if p['category']=='build_error')
        path=urlsplit(package['log_url']).path
        for destination in [other.url+'/log.txt', self.server.url+'/outside/log.txt',
                            self.server.url+'/reports/b860/19091860/html/Build_Report_x86_64/escape/log.txt']:
            self.server.routes[path]=(302,b'',{'Location':destination},0)
            with self.assertRaises(FlowError) as caught:r.fetch_log(r.build_ref,'armv7l',package)
            self.assertEqual(caught.exception.code,4);self.assertIn('todo',caught.exception.details)
        self.assertEqual(other.requests,[])
        self.assertFalse(any(x['path'] in ['/outside/log.txt','/reports/b860/19091860/html/Build_Report_x86_64/escape/log.txt'] for x in self.server.requests))

    def wire(self, headers, body, *, delay=0, drip=False):
        def handler(h):
            try:
                if delay:time.sleep(delay)
                h.send_response(200)
                for key,value in headers.items():h.send_header(key,value)
                h.end_headers()
                if drip:
                    for byte in body:
                        h.wfile.write(bytes([byte]));h.wfile.flush();time.sleep(.025)
                else:h.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError,ssl.SSLError):pass
            finally:h.close_connection=True
        return handler

    def test_content_length_chunked_interruptions_no_cache_and_true_timeouts(self):
        path=self.server.report_path('armv7l')
        for headers,body in [({'Content-Length':'100'},b'abc'),({'Transfer-Encoding':'chunked'},b'5\r\nabc')]:
            self.server.wire_routes[path]=self.wire(headers,body)
            o=self.observe();self.assertEqual(o['reports']['armv7l']['error'],'incomplete_body')
            folder=self.config.output(self.reader().folder+'/pages/armv7l')
            self.assertFalse(list(folder.glob('*.html')))
            self.assertIsNone(load_json(folder/'continuous.json')['continuous'])
        self.config.raw['fetch'].update(timeout_s=.04,deadline_s=.2)
        self.server.wire_routes[path]=self.wire({'Content-Length':'3'},b'abc',delay=.2)
        self.assertEqual(self.observe()['reports']['armv7l']['error'],'timeout')
        self.config.raw['fetch'].update(timeout_s=1,deadline_s=.08)
        self.server.wire_routes[path]=self.wire({'Content-Length':'30'},b'x'*30,drip=True)
        started=time.monotonic();o=self.observe()
        self.assertEqual(o['reports']['armv7l']['error'],'deadline')
        self.assertLess(time.monotonic()-started,.6)

    def test_response_evidence_log_active_truncation_differs_from_incomplete(self):
        o=self.ready();e=o['reports']['armv7l']['response']
        self.assertTrue({'http_status','Date','Last-Modified','ETag','Content-Length','actual_bytes','sha256','started_at','finished_at'}<=e.keys())
        r=self.reader();r._observed=o;p=next(p for p in o['reports']['armv7l']['packages'] if p['category']=='build_error')
        path=urlsplit(p['log_url']).path
        self.server.wire_routes[path]=self.wire({'Content-Length':'500'},b'x'*150)
        log=r.fetch_log(r.build_ref,'armv7l',p)
        self.assertTrue(log['truncated']);self.assertFalse(log['transfer_complete'])
        self.config.raw['fetch']['max_log_bytes']=1000
        with self.assertRaises(FlowError) as caught:r.fetch_log(r.build_ref,'armv7l',p)
        self.assertEqual(caught.exception.reason,'incomplete_body')
        self.assertEqual(Path(log['path']).stat().st_size,100)
        evidence=load_json(caught.exception.details['request_evidence']['path'])
        self.assertEqual(evidence['response']['actual_bytes'],150)
        self.assertEqual(evidence['response']['sha256'],digest(b'x'*150))
        self.assertEqual(len(evidence['responses']),1)
        self.assertNotIn('body',evidence)

    def test_unsettled_malformed_running_then_terminal_or_settle_deadline(self):
        path=self.server.report_path('armv7l');body=self.server.routes[path][1]
        half=body.replace(b'<td>4</td>',b'<td>5</td>',1)
        self.arm(half);self.server.routes['/build/19091860']=(200,b'19091860 <span title="Build is running"></span>',{},0)
        for delta in [0,10,10]:
            o=self.observe(delta);self.assertEqual(o['report_state'],'部分');self.assertFalse(o['todos'])
        self.server.routes['/build/19091860']=(200,b'19091860 <span title="Build is failed"></span>',{},0)
        o=self.observe(1);self.assertEqual(o['report_state'],'对账失败');self.assertEqual(o['exit_code'],3)
        self.server.routes['/build/19091860']=(500,b'',{},0)
        self.arm(half+b' ')
        self.assertEqual(self.observe()['report_state'],'部分')
        self.assertEqual(self.observe(101)['report_state'],'对账失败')

    def test_truncated_structure_to_full_and_missing_summary_settled(self):
        path=self.server.report_path('armv7l');body=self.server.routes[path][1]
        self.arm(body[:500]);o=self.observe();self.assertEqual(o['report_state'],'部分');self.assertFalse(o['todos'])
        self.arm(body);self.assertEqual(self.observe(10)['report_state'],'部分')
        self.assertEqual(self.observe(10)['report_state'],'完整')
        self.arm(body.replace(b'Build Status Summary',b'Other Heading'))
        self.assertEqual(self.observe(10)['report_state'],'部分')
        o=self.observe(10);self.assertEqual(o['report_state'],'对账失败')
        self.assertIn('missing_summary_settled',o['reports']['armv7l']['reconciliation_checks'])

    def test_continuous_reset_failure_404_change_config_clock_and_history_bound(self):
        self.ready();path=self.server.report_path('armv7l');body=self.server.routes[path][1]
        for break_value in [(500,b'',{},0),(404,b'',{},0),(200,body+b' ',{},0)]:
            self.server.routes[path]=break_value;self.observe(10)
            self.arm(body);o=self.observe(10)
            self.assertFalse(o['reports']['armv7l']['stable'])
        self.observe(10)
        self.config.raw['cosmos']['detail_table_title_prefix']+=' '
        self.assertFalse(self.observe(10)['reports']['armv7l']['stable'])
        self.observe(10);self.at-=timedelta(seconds=100)
        self.assertFalse(self.observe()['reports']['armv7l']['stable'])
        self.config.raw['poll'].update(interval_s=100,settle_s=100)
        for _ in range(55):o=self.observe(2)
        self.assertTrue(o['reports']['armv7l']['stable'])
        store=load_json(self.config.output(self.reader().folder+'/pages/armv7l/continuous.json'))
        self.assertEqual(len(store['history']),50);self.assertEqual(store['continuous']['count'],55)
        self.assertEqual(len(list(self.config.output(self.reader().folder+'/pages/armv7l').glob('*.html'))),2)

    def test_header_only_after_both_settled_and_coverage_projection_pure(self):
        o=self.ready();report=o['reports']['armv7l']
        rows=[(r['path'],r['cl'],r['shelve']) for r in report['input_rows']]
        rows[0]=(rows[0][0],str(int(rows[0][1])+1),rows[0][2])
        before=json_bytes(report);a=apply_rows_coverage(report,rows);b=apply_rows_coverage(a,rows)
        self.assertEqual(a,b);self.assertEqual(json_bytes(report),before)
        self.assertEqual(a['package_coverage'],'不一致');self.assertEqual(a['result_state'],'失败')
        self.assertEqual(a['coverage_basis'],'manual_file')
        path=self.server.report_path('x86_64');self.server.routes[path]=(200,self.server.routes[path][1].replace(b'build.conf@14368686',b'build.conf@1'),{},0)
        self.assertEqual(self.observe(10)['header_consistency'],'未核')
        self.assertEqual(self.observe(10)['header_consistency'],'不一致')

    def test_detail_failure_counts_identity_all_candidates_recovery_and_report_failure(self):
        self.server.routes['/build/19091860']=(500,b'',{},0)
        for _ in range(3):o=self.observe(100)
        self.assertFalse(o['observation_failed']);self.assertEqual(o['report_state'],'完整')
        self.assertEqual(o['execution_evidence']['failure_count'],3)
        self.assertEqual(sum(t['reason']=='detail_page_unavailable' for t in o['todos']),1)
        self.server.routes['/build/19091860']=(200,b'123 <span title="Build is failed"></span>',{},0)
        self.assertEqual(self.observe()['execution_evidence']['failure'],'identity_mismatch')
        self.server.routes['/build/19091860']=(200,b'19091860 <a title="Build is successful"></a><span title="Build is failed"></span>',{},0)
        o=self.observe();self.assertEqual(o['execution_evidence']['failure_count'],0)
        self.assertEqual(o['execution_evidence']['subresult'],'successful');self.assertEqual(len(o['execution_evidence']['candidates']),2)
        self.server.routes[self.server.report_path('armv7l')]=(500,b'',{},0)
        o=self.observe();self.assertEqual(o['exit_code'],5);self.assertEqual(o['execution_state'],'已结束')

    def test_rule_errors_are_not_swallowed_and_instance_scopes_do_not_mix(self):
        r=self.reader()
        with patch.object(r.transport,'get',side_effect=FlowError(4,'rule_refused')):
            with self.assertRaises(FlowError) as caught:r.observe(r.build_ref)
        self.assertEqual(caught.exception.code,4)
        a=build_key(self.reader());self.config.raw['cosmos']['report_root']+='/different'
        self.assertNotEqual(a,build_key(self.reader()))


class Workflow21Tests(Batch21Tests):
    def fast(self):
        self.config.raw['poll'].update(interval_s=.02,settle_s=.04,stopped_interval_s=.02)
        self.config.raw['data_root']=str(self.config.data_root)
        self.server.config_path.write_text(json.dumps(self.config.raw))
        return lambda:HTTPReportReader(self.config,'19091860')

    def test_stopped_loop_reobserves_changed_report_and_detail_failure_does_not_block(self):
        factory=self.fast();path=self.server.report_path('armv7l');original=self.server.routes[path]
        self.arm(original[1].replace(b'<td>4</td>',b'<td>5</td>',1))
        sleeps=[]
        def change():
            sleeps.append(1)
            if len(sleeps)==2:self.server.routes[path]=original
        result=loop(self.config,factory,max_ticks=7,on_sleep=change)
        self.assertEqual(result['phase'],'结果已拉取')
        self.assertTrue(any(r['phase']=='停止推进' for r in result['tick_results']))
        with EventStore(self.config.data_root) as store:todos=[e['payload']['todo'] for e in store.events(build_key(factory()),kinds=['inbox_opened'])]
        self.assertEqual(sum(t['reason']=='report_basis_changed' for t in todos),1)
        # Independent build storage, still the same loopback service.
        self.config.raw['cosmos']['report_root']=self.server.url+'/reports/'
        object.__setattr__(self.config,'data_root',self.base/'detail-failure-data')
        self.server.routes['/build/19091860']=(500,b'',{},0)
        result=loop(self.config,factory,max_ticks=8)
        self.assertEqual(result['phase'],'结果已拉取')
        with EventStore(self.config.data_root) as store:todos=store.events(kinds=['inbox_opened'])
        self.assertEqual(sum(e['payload']['todo']['reason']=='detail_page_unavailable' for e in todos),1)

    def test_completed_baseline_change_invalidates_and_missing_artifact_recovers(self):
        factory=self.fast();rows=self.server.fixture/'rows.txt'
        factory=lambda:HTTPReportReader(self.config,'19091860',rows)
        self.assertEqual(loop(self.config,factory,max_ticks=6)['phase'],'结果已拉取')
        rows.write_text(rows.read_text().replace('@100','@99'))
        result=tick(self.config,factory);self.assertEqual(result['action'],'observe');self.assertEqual(result['exit_code'],3)
        with EventStore(self.config.data_root) as store:
            e=next(e for e in reversed(store.events(build_key(factory()))) if e['kind']=='workflow_result' and e['payload']['step']=='observe')
        Path(e['payload']['artifact']['path']).unlink()
        result=tick(self.config,factory);self.assertEqual(result['action'],'observe')
        with EventStore(self.config.data_root) as store:
            self.assertTrue(any(e['payload']['todo']['reason']=='artifact_unavailable' for e in store.events(kinds=['inbox_opened'])))

    def test_logs_refresh_report_and_cache_bound_to_report_and_limit(self):
        factory=self.fast();tick(self.config,factory);time.sleep(.03);tick(self.config,factory)
        path=self.server.report_path('armv7l');self.arm(self.server.routes[path][1]+b' ')
        changed=tick(self.config,factory);self.assertEqual(changed['action'],'observe')
        self.assertFalse(any(r['path'].endswith('/log.txt') for r in self.server.requests))
        time.sleep(.03);tick(self.config,factory);logs=tick(self.config,factory)
        self.assertEqual(logs['action'],'logs')
        r=factory();o=r.observe(r.build_ref);p=next(p for p in o['reports']['armv7l']['packages'] if p['category']=='build_error')
        self.assertTrue(r.fetch_log(r.build_ref,'armv7l',p)['skipped'])
        self.config.raw['fetch']['max_log_bytes']+=1
        self.assertFalse(r.fetch_log(r.build_ref,'armv7l',p)['skipped'])
        self.arm(self.server.routes[path][1]+b' ')
        r=factory();o=r.observe(r.build_ref)
        self.assertFalse(r.fetch_log(r.build_ref,'armv7l',p)['skipped'])

    def test_actual_child_crash_after_observe_logs_notify_result_unique_and_cleanup(self):
        for target in ['observe','logs','notify']:
            owned=self.base/('crash-'+target);object.__setattr__(self.config,'data_root',owned)
            factory=self.fast()
            if target in {'logs','notify'}:
                tick(self.config,factory);time.sleep(.03);tick(self.config,factory)
            if target=='notify':tick(self.config,factory)
            process=multiprocessing.Process(target=crash_after_action,args=(self.server.config_path,target));process.start();process.join(8)
            self.assertEqual(process.exitcode,29,target)
            with EventStore(owned) as store:
                events=store.events(build_key(factory()))
                unfinished=events[-1] if target!='notify' else next(e for e in reversed(events) if e['kind']=='workflow_intent')
                attempt=unfinished['payload']['attempt']
            folder=owned/f'rounds/{build_key(factory())}/attempt-{attempt}'
            self.assertTrue(folder.is_dir())
            before=sum(r['path'].endswith('/log.txt') for r in self.server.requests)
            tick(self.config,factory)
            self.assertFalse(folder.exists())
            with EventStore(owned) as store:
                completed=[e for e in store.events(build_key(factory())) if e['kind']=='workflow_result' and e['payload']['step']==target]
            self.assertEqual(len(completed),1,target)
            if target=='logs':self.assertEqual(sum(r['path'].endswith('/log.txt') for r in self.server.requests),before)

    def test_append_retry_other_build_only_constraint_same_build_and_explicit_no_retry(self):
        factory=self.fast();key=build_key(factory());context=command_context('workflow.tick')
        with EventStore(self.config.data_root) as store:
            store.append(context,'workflow_intent',{'build':'another'},0)
            result=append_retry(store,context,'workflow_result',{'build':key},0,retry=True,operation_id='one')
            self.assertEqual(result,2)
            with self.assertRaises(FlowError) as caught:append_retry(store,context,'workflow_result',{'build':key},0,retry=True,operation_id='two')
            self.assertEqual(caught.exception.reason,'stale_head')
            with patch.object(store,'append',wraps=store.append) as append:
                with self.assertRaises(FlowError) as caught:append_retry(store,context,'workflow_result',{'build':key},store.head(),retry=True,operation_id='one')
                self.assertEqual(caught.exception.reason,'constraint');self.assertEqual(append.call_count,1)
            store.append(context,'workflow_intent',{'build':'another'},store.head())
            with self.assertRaises(FlowError):append_retry(store,context,'workflow_intent',{'build':key},2,retry=False)
        with self.assertRaises(FlowError) as caught:loop(self.config,factory,max_ticks=1,expected_event=0)
        self.assertEqual(caught.exception.reason,'stale_head')

    def test_tick_concurrent_other_build_append_retries_without_repeating_action(self):
        factory=self.fast();context=command_context('workflow.tick')
        def other(step):
            with EventStore(self.config.data_root) as store:
                store.append(context,'workflow_intent',{'build':'another'},store.head())
        result=tick(self.config,factory,after_action=other,loop_driven=True)
        self.assertEqual(result['exit_code'],0)
        with EventStore(self.config.data_root) as store:
            self.assertEqual(sum(e['kind']=='workflow_result' for e in store.events(build_key(factory()))),1)
        self.assertEqual(sum(r['path']==self.server.report_path('armv7l') for r in self.server.requests),1)
        def same(step):
            with EventStore(self.config.data_root) as store:
                store.append(context,'workflow_intent',{'build':build_key(factory())},store.head())
        with self.assertRaises(FlowError) as caught:tick(self.config,factory,after_action=same,loop_driven=True)
        self.assertEqual(caught.exception.reason,'stale_head')

    def test_round_contention_three_skips_one_todo_and_real_two_process_ticks(self):
        factory=self.fast();key=build_key(factory())
        acquired,release=multiprocessing.Event(),multiprocessing.Event()
        process=multiprocessing.Process(target=hold_lock,args=(self.config.data_root,key,acquired,release));process.start()
        self.assertTrue(acquired.wait(3))
        try:
            result=loop(self.config,factory,max_ticks=5)
            self.assertEqual(result['exit_code'],6);self.assertEqual(result['ticks'],3)
            self.assertTrue(all(r['action']=='skipped' for r in result['tick_results']))
        finally:release.set();process.join(3)
        with EventStore(self.config.data_root) as store:
            self.assertEqual(sum(e['payload']['todo']['reason']=='loop_contention' for e in store.events(kinds=['inbox_opened'])),1)
        self.server.routes['/build/19091860']=(200,b'19091860 <span title="Build is failed"></span>',{},.15)
        command=[sys.executable,str(REPO/'vd-cosmos-workflow/scripts/run.py'),'tick','--config',str(self.server.config_path),'--build-id','19091860']
        first=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        deadline=time.monotonic()+3
        while not any(r['path']=='/build/19091860' for r in self.server.requests) and time.monotonic()<deadline:time.sleep(.005)
        second=subprocess.run(command,capture_output=True,text=True)
        out,err=first.communicate(timeout=4)
        self.assertEqual(first.returncode,0,out+err);self.assertEqual(second.returncode,6,second.stdout)
        self.assertEqual(second.stderr,'')

    def test_wal_reader_error_wrapping_and_other_build_history_not_loaded(self):
        factory=self.fast();key=build_key(factory())
        with EventStore(self.config.data_root) as store:
            self.assertEqual(store.connection.execute('PRAGMA journal_mode').fetchone()[0],'wal')
            self.assertEqual(store.connection.execute('PRAGMA busy_timeout').fetchone()[0],2000)
            context=command_context('workflow.tick')
            # Batch fixture insertion still uses the same append-only SQL guards.
            store.connection.execute('BEGIN IMMEDIATE')
            for i in range(10000):
                store.connection.execute('INSERT INTO events(previous_id,kind,command,build_key,payload) VALUES(?,?,?,?,?)',
                    (i,'workflow_intent',context.name,'other',json.dumps({'build':'other'})))
            store.connection.execute('COMMIT')
            self.assertEqual(store.events(key),[])
            plan=store.connection.execute("EXPLAIN QUERY PLAN SELECT * FROM events WHERE COALESCE(build_key,json_extract(payload,'$.build'))=? ORDER BY id",(key,)).fetchall()
            self.assertTrue(any('by_build' in str(tuple(row)) for row in plan))
            queries=[];store.connection.set_trace_callback(queries.append)
            started=time.monotonic()
            projection(self.config,store,key)
            self.assertLess(time.monotonic()-started,.1)
            self.assertTrue(any('COALESCE(build_key' in q and key in q for q in queries))
        reader=sqlite3.connect(self.config.data_root/'state/state.db');reader.execute('BEGIN');reader.execute('SELECT * FROM events LIMIT 1').fetchone()
        try:self.assertEqual(tick(self.config,factory)['exit_code'],0)
        finally:reader.close()
        with EventStore(self.config.data_root) as store:
            store.connection.close()
            for action in [store.head,store.events]:
                with self.assertRaises(FlowError) as caught:action()
                self.assertEqual(caught.exception.reason,'state_busy')

    def test_monitor_404_timeout_live_disk_and_versioned_todo_identity(self):
        factory=self.fast();self.config.raw['poll'].update(expected_hours=.000001,stall_polls=2)
        for arch in ['armv7l','x86_64']:self.server.routes[self.server.report_path(arch)]=(404,b'',{},0)
        loop(self.config,factory,max_ticks=4)
        with EventStore(self.config.data_root) as store:
            todos=[e['payload']['todo'] for e in store.events(kinds=['inbox_opened'])]
            self.assertFalse(any(t['reason']=='report_stalled' for t in todos))
            self.assertEqual(sum(t['reason']=='expected_observation_duration_exceeded' for t in todos),1)
            context=command_context('workflow.tick');key=build_key(factory())
            self.config.raw['budget']['disk_warning_bytes']=100
            for free in [50,40]:
                with patch('vd_cosmos_core.journal.os.statvfs',return_value=type('Stat',(),{'f_bavail':free,'f_frsize':1})()):
                    t=monitor_todos(self.config,store,key,{})
                write_todos(store,context,store.head(),key,t,self.config)
            self.assertEqual(sum(e['payload']['todo']['reason']=='disk_low' for e in store.events(kinds=['inbox_opened'])),1)
            for rows in [[3,1],[2,1]]:
                write_todos(store,context,store.head(),key,[{'reason':'sample','arch':'armv7l','basis_version':'same','rows':rows}],self.config)
            self.assertEqual(sum(e['payload']['todo']['reason']=='sample' for e in store.events(kinds=['inbox_opened'])),1)

    def test_three_log_failures_have_one_todo(self):
        factory=self.fast();tick(self.config,factory);time.sleep(.03);tick(self.config,factory)
        r=factory();o=r.observe(r.build_ref)
        for report in o['reports'].values():
            for p in report['packages']:
                if p['category']=='build_error':self.server.routes[urlsplit(p['log_url']).path]=(500,b'',{},0)
        for _ in range(3):self.assertEqual(tick(self.config,factory)['exit_code'],5)
        with EventStore(self.config.data_root) as store:
            self.assertEqual(sum(e['payload']['todo']['reason']=='log_download_unavailable' for e in store.events(kinds=['inbox_opened'])),1)


class TLS21Tests(Batch21Tests):
    def test_tls_self_signed_extra_ca_hostname_and_downgrade_refused(self):
        binary=shutil.which('openssl')
        if not binary:self.skipTest('openssl missing: real TLS handshake tests skipped')
        certificate=self.base/'certificate.pem';key=self.base/'private.pem'
        proc=subprocess.run([binary,'req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=fixture.invalid',
            '-addext','subjectAltName=IP:127.0.0.1','-keyout',str(key),'-out',str(certificate)],capture_output=True)
        self.assertEqual(proc.returncode,0,'openssl certificate generation failed')
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(certificate,key)
        self.server.server.socket=context.wrap_socket(self.server.server.socket,server_side=True)
        self.server.url=self.server.url.replace('http:','https:')
        self.config.raw['cosmos']['report_root']=self.server.url+'/reports/'
        self.config.raw['cosmos']['status_source']['url_template']=self.server.url+'/build/{build_id}'
        o=self.observe();self.assertEqual(o['reports']['armv7l']['error'],'tls_verify')
        self.config.raw.setdefault('network',{})['ca_file']=str(certificate)
        o=self.ready();self.assertEqual(o['report_state'],'完整')
        # Exercise a real local CONNECT tunnel, verifying the target certificate
        # with the additional CA rather than the proxy's host identity.
        connects=[]
        class Proxy(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_CONNECT(self):
                connects.append(self.path)
                host,port=self.path.rsplit(':',1)
                if host!='127.0.0.1':raise AssertionError('non-loopback tunnel')
                with socket.create_connection((host,int(port))) as upstream:
                    self.send_response(200);self.end_headers()
                    while True:
                        readable,_,_=select.select([self.connection,upstream],[],[],1)
                        if not readable:break
                        for source in readable:
                            data=source.recv(65536)
                            if not data:return
                            (upstream if source is self.connection else self.connection).sendall(data)
        proxy=ThreadingHTTPServer(('127.0.0.1',0),Proxy)
        thread=threading.Thread(target=proxy.serve_forever,daemon=True);thread.start()
        try:
            self.config.raw['network'].update(proxy='http://127.0.0.1:'+str(proxy.server_port),no_proxy_hosts=[])
            self.assertEqual(self.observe(10)['report_state'],'完整')
            self.assertTrue(connects)
        finally:
            proxy.shutdown();proxy.server_close();thread.join(2)
            self.config.raw['network'].update(proxy=None,no_proxy_hosts=[])
        bad=HTTPTransport(self.config)
        with self.assertRaises(FlowError) as caught:bad.get(self.server.url.replace('127.0.0.1','localhost')+'/build/19091860',10000)
        self.assertEqual(caught.exception.reason,'tls_verify')
        r=self.reader();r._observed=o;p=next(p for p in o['reports']['armv7l']['packages'] if p['category']=='build_error')
        path=urlsplit(p['log_url']).path
        self.server.routes[path]=(302,b'',{'Location':self.server.url.replace('https:','http:')+'/outside/log.txt'},0)
        with self.assertRaises(FlowError) as caught:r.fetch_log(r.build_ref,'armv7l',p)
        self.assertEqual(caught.exception.code,4)
        self.assertFalse(any(x['path']=='/outside/log.txt' for x in self.server.requests))


class Acceptance21Tests(Batch21Tests):
    @classmethod
    def setUpClass(cls):
        cls.snapshot_temp=tempfile.TemporaryDirectory()
        cls.snapshot=Path(cls.snapshot_temp.name)/'repo'
        cls.commit=isolated_checkout(cls.snapshot)

    @classmethod
    def tearDownClass(cls):
        cls.snapshot_temp.cleanup()

    def command(self, *, real=False, direct=False, commit=None):
        prefix=([sys.executable,str(self.snapshot/'vd-cosmos-core/scripts/verify_b2_real.py'),'--verified-commit',commit or self.commit] if direct else
                ['bash','--noprofile','--norc',str(self.snapshot/'vd-cosmos-core/scripts/verify_b2_real.sh'),commit or self.commit])
        return prefix+['--config',str(self.server.config_path),'--build-id','19091860','--saved-dir',str(self.server.fixture),
            '--rows',str(self.server.fixture/'rows.txt'),'--links',str(self.server.fixture/'links.txt')]+([] if real else
            ['--mode','fixture','--fixture-counts',str(self.server.fixture/'expected-counts.json')])

    def invoke(self, **kwargs):
        process=subprocess.run(self.command(**kwargs),capture_output=True,text=True,timeout=20)
        self.assertEqual(process.stderr,'')
        output=json.loads(process.stdout.splitlines()[-1])
        result=load_json(output['result_file']['path']) if output.get('result_file') else None
        self.assertEqual(process.returncode,output['exit_code'])
        return output,result

    def test_clean_snapshots_repeated_independent_A_to_F_and_unrelated_changes(self):
        unrelated=self.snapshot/'unrelated.txt';unrelated.write_text('user change')
        self.addCleanup(unrelated.unlink)
        original=self.server.config_path.read_bytes()
        first,a=self.invoke();second,b=self.invoke()
        for output,result in [(first,a),(second,b)]:
            self.assertEqual(output['verdict'],'PASS',result)
            for phase in ['A','B','C','E']:self.assertEqual(result[phase]['exit_code'],0)
            self.assertEqual(result['E']['actions'],['logs','notify','observe'])
            self.assertTrue(result['F']['index']['fingerprint']['verified'])
            self.assertTrue(result['F']['detail_identity_match'])
            self.assertEqual(result['provenance']['backend'],'http-fixture')
            self.assertIn('非真实验收',result['note'])
        self.assertNotEqual(a['provenance']['run_id'],b['provenance']['run_id'])
        self.assertEqual(original,self.server.config_path.read_bytes())
        self.assertTrue(all(not l['skipped'] for r in [a,b] for l in r['B']['logs']))

    def test_direct_commit_dirty_source_and_real_loopback_rejected_before_output(self):
        out,_=self.invoke(direct=True,commit='wrong');self.assertEqual(out['error'],'expected_commit_mismatch')
        marker=self.snapshot/'vd-cosmos-core/untracked.txt';marker.write_text('dirty')
        try:
            out,_=self.invoke();self.assertEqual(out['error'],'owned_source_tree_dirty')
        finally:marker.unlink()
        out,_=self.invoke(real=True);self.assertEqual(out['error'],'real_backend_requires_non_loopback_instance')
        self.assertFalse(self.config.data_root.exists())

    def test_saved_page_difference_fails_A(self):
        path=self.server.fixture/'report_armv7l.html';path.write_bytes(path.read_bytes()+b' ')
        out,r=self.invoke();self.assertEqual(r['A']['verdict'],'FAIL');self.assertNotEqual(out['exit_code'],0)

    def test_truncated_incomplete_and_html_logs_fail_B(self):
        path='/reports/b860/19091860/html/Build_Report_armv7l/logs/fail/provider-1.0-1/log.txt'
        for kind in ['truncated','incomplete','html']:
            if kind=='truncated':self.server.routes[path]=(200,b'x'*200,{},0)
            if kind=='incomplete':
                self.server.routes.pop(path,None)
                self.server.wire_routes[path]=self.wire({'Content-Length':'90'},b'cut')
            if kind=='html':
                self.server.wire_routes.pop(path,None)
                self.server.routes[path]=(200,b'<html><form>login</form></html>',{},0)
            out,r=self.invoke();self.assertEqual(r['A']['verdict'],'PASS')
            self.assertEqual(r['B']['verdict'],'FAIL',kind);self.assertNotEqual(out['exit_code'],0)


def load_tests(loader, tests, pattern):
    suite=unittest.TestSuite()
    for cls in [Batch21Tests,Workflow21Tests,TLS21Tests,Acceptance21Tests]:
        for name in cls.__dict__:
            if name.startswith('test_'):suite.addTest(cls(name))
    return suite
