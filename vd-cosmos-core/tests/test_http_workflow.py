import copy
import json
import multiprocessing
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

from helpers import CORE, REPO
from http_helpers import FixtureServer
from vd_cosmos_core.config import load_config, FETCH_DEFAULTS
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes, load_json
from vd_cosmos_core.http_reader import HTTPReportReader, HTTPTransport, direct_host
from vd_cosmos_core.observation import summarize
from vd_cosmos_core.report import parse_report
from vd_cosmos_core.state import EventStore
from vd_cosmos_workflow.api import tick, loop, status, inbox
from vd_cosmos_core.read_ops import fetch_logs, read_action
from vd_cosmos_core.commands import command_context


def crash_intent(config_file):
    config = load_config(config_file)
    tick(config, lambda: HTTPReportReader(config, '19091860'), after_intent=lambda: os._exit(23))


class HTTPTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.server = FixtureServer(self.base);self.addCleanup(self.server.close)
        self.config = load_config(self.server.config_path)
        original = socket.getaddrinfo
        def local_only(host, *args, **kwargs):
            if host not in {'127.0.0.1', 'localhost'}:
                raise AssertionError('Test attempted non-loopback DNS')
            return original(host, *args, **kwargs)
        guard = patch('socket.getaddrinfo', side_effect=local_only);guard.start();self.addCleanup(guard.stop)

    def reader(self, rows=False):
        return HTTPReportReader(self.config, self.server.build_id, self.server.fixture / 'rows.txt' if rows else None)

    def observed(self, rows=False):
        reader = self.reader(rows);return reader.observe(reader.build_ref)

    def stable(self, rows=False):
        self.observed(rows);time.sleep(self.config.raw['poll']['interval_s'] + .01)
        return self.observed(rows)

    def test_http_states_no_cache_headers_coverage_and_detail_evidence(self):
        first = self.observed()
        self.assertEqual(first['report_state'], '部分')
        self.assertFalse(any(t['reason'] in {'not_stable', 'missing_summary'} for t in first['todos']))
        result = self.stable(True)
        self.assertEqual(result['report_state'], '完整')
        self.assertEqual(result['package_coverage'], '未核')
        self.assertEqual(result['reports']['armv7l']['package_coverage'], '一致')
        self.assertEqual(result['reports']['x86_64']['package_coverage'], '未核')
        self.assertEqual(result['result_state'], '失败')
        self.assertEqual(result['execution_evidence']['subresult'], 'failed')
        self.assertFalse(result['execution_evidence']['raw_retained'])
        for request in self.server.requests:
            self.assertEqual(request['headers']['Cache-Control'], 'no-cache')
            self.assertEqual(request['headers']['Pragma'], 'no-cache')
            self.assertEqual(request['headers']['User-Agent'], self.config.raw['fetch']['user_agent'])
        self.assertFalse(list(self.config.data_root.rglob('*detail*.html')))

    def test_404_requires_readable_bucket_index(self):
        for arch in self.config.raw['cosmos']['archs']:
            self.server.routes[self.server.report_path(arch)] = (404, b'missing', {}, 0)
        self.assertEqual(self.observed()['report_state'], '未发布')
        self.server.routes['/reports/b860/'] = (500, b'bad', {}, 0)
        result = self.observed();self.assertEqual(result['exit_code'], 5);self.assertIsNone(result['report_state'])

    def test_500_timeout_proxy_page_size_limit_and_cross_host_redirect(self):
        path = self.server.report_path('armv7l')
        for route in [(500,b'bad',{},0), (200,b'delayed',{},.5), (200,b'<html>proxy failure</html>',{},0),
                      (200,b'x'*5000,{},0), (302,b'',{'Location':'http://authentication.invalid/login'},0)]:
            self.config.raw['fetch']['max_page_bytes'] = 4500
            self.server.routes[path] = route
            result = self.observed()
            self.assertEqual(result['exit_code'], 5)
            self.assertIsNone(result['report_state'])
        self.assertFalse(list((self.config.data_root / 'rounds/19091860/pages/armv7l').glob('*.html')))

    def test_same_host_redirect_limit_and_no_cookie_storage_or_return(self):
        path = self.server.report_path('armv7l')
        body = self.server.routes[path][1]
        self.server.routes[path] = (302,b'',{'Location':'/alias1','Set-Cookie':'fake-session=value'},0)
        self.server.routes['/alias1'] = (200,body,{'Set-Cookie':'another=value'},0)
        self.observed();self.observed()
        self.assertTrue(all('Cookie' not in r['headers'] for r in self.server.requests))
        for i in range(1,5):self.server.routes['/alias'+str(i)] = (302,b'',{'Location':'/alias'+str(i+1)},0)
        self.assertEqual(self.observed()['exit_code'], 5)

    def test_detail_session_parameters_never_persist_raw(self):
        marker = 'wicket' + ':interface=synthetic-session'
        body = ('19091860 <span title="Build is failed"></span><a href="?' + marker + '">next</a>').encode()
        self.server.routes['/build/19091860'] = (200,body,{},0)
        result = self.observed()
        evidence = result['execution_evidence']
        self.assertEqual(evidence['subresult'], 'failed')
        self.assertEqual(evidence['sha256'], digest(body))
        self.assertEqual(evidence['retention_note'], '原文未保留（命中凭据模式）')
        for path in self.config.data_root.rglob('*'):
            if path.is_file():self.assertNotIn(b'synthetic-session', path.read_bytes())

    def test_page_credentials_refused_without_file_and_with_todo(self):
        path = self.server.report_path('armv7l')
        self.server.routes[path] = (200,self.server.routes[path][1]+('Cookie'+': synthetic-secret').encode(),{},0)
        result = self.observed()
        self.assertEqual(result['exit_code'], 5)
        self.assertTrue(any(t['reason']=='report_credential_pattern_blocked' and t['arch']=='armv7l' for t in result['todos']))
        self.assertFalse(list((self.config.data_root/'rounds/19091860/pages/armv7l').glob('*.html')))

    def test_changing_then_stable_inconsistent_report(self):
        self.observed()
        path = self.server.report_path('armv7l');body = self.server.routes[path][1].replace(b'<td>4</td>',b'<td>5</td>',1)
        self.server.routes[path] = (200,body,{},0)
        time.sleep(.04)
        changing = self.observed();self.assertEqual(changing['report_state'], '部分')
        self.assertFalse(any(t['reason']=='reconciliation_failed' for t in changing['todos']))
        time.sleep(.04)
        stable = self.observed();self.assertEqual(stable['report_state'],'对账失败')
        todo = next(t for t in stable['todos'] if t['reason']=='reconciliation_failed')
        self.assertIn('summary_total_mismatch',todo['checks']);self.assertLessEqual(len(todo['rows']),20)
        self.assertTrue(todo['rows'][0]['source_line']);self.assertIn('<tr>',todo['rows'][0]['raw'])

    def test_missing_expected_package_is_coverage_only_invalid_baseline_is_argument_error(self):
        rows = self.server.fixture/'rows.txt';rows.write_text(rows.read_text()+'//example/missing/...@9\n')
        result = self.stable(True)
        self.assertEqual(result['report_state'],'完整');self.assertEqual(result['package_coverage'],'不一致')
        self.assertEqual(result['result_state'],'失败')
        self.assertTrue(any(t['reason']=='package_coverage_mismatch' for t in result['todos']))
        rows.write_text('invalid-row\n')
        with self.assertRaises(FlowError) as caught:self.reader(True)
        self.assertEqual(caught.exception.code,2)
        html=(self.server.fixture/'report_armv7l.html').read_text()
        with self.assertRaises(FlowError) as caught:parse_report(html,'armv7l',self.config.raw['cosmos'],[{'name':'x'}],stable=True)
        self.assertEqual(caught.exception.code,2)

    def test_aggregate_all_priority_branches(self):
        ref=self.reader().build_ref;cosmos=self.config.raw['cosmos']
        for values,expected in [(['完整','完整'],'完整'),(['部分','完整'],'部分'),(['未知','未知'],'未知'),
                                (['未发布','未发布'],'未发布'),(['对账失败','部分'],'对账失败'),
                                (['结构未知','对账失败'],'结构未知'),([None,'结构未知'],None)]:
            reports={arch:{'report_state':state,'result_state':'成功','package_coverage':'未核','headers':dict.fromkeys(cosmos['header_must_match'],'same'),
                           'observation_failed':state is None} for arch,state in zip(cosmos['archs'],values)}
            result=summarize(ref,cosmos,reports,{'state':'未知'},backend='test')
            self.assertEqual(result['report_state'],expected)

    def test_logs_boundary_truncation_credential_flag_cache_and_concurrency(self):
        result=self.stable();reader=self.reader()
        packages=[p for r in result['reports'].values() for p in r['packages'] if p['category']=='build_error']
        package=copy.deepcopy(packages[0]);arch=package['key']['arch']
        for url in ['http://elsewhere.invalid/log.txt',self.server.url+'/outside/log.txt',
                    self.server.url+'/reports/b860/19091860/html/Build_Report_armv7l/%2e%2e/out/log.txt']:
            package['log_url']=url
            with self.assertRaises(FlowError) as caught:reader.fetch_log(reader.build_ref,arch,package)
            self.assertEqual(caught.exception.code,4);self.assertIn('todo',caught.exception.details)
        for p in packages:
            path=urlsplit(p['log_url']).path
            self.server.routes[path]=(200,('Cookie'+': fake\n').encode()+b'x'*200,{},.04)
        logs=reader.fetch_logs(packages)
        self.assertEqual(len(logs),2);self.assertLessEqual(self.server.max_active_logs,2)
        self.assertTrue(all(l['truncated'] and l['size']==100 and not l['export_allowed'] for l in logs))
        count=len(self.server.requests)
        cached=reader.fetch_logs(packages)
        self.assertTrue(all(l['skipped'] for l in cached));self.assertEqual(len(self.server.requests),count)

    def test_log_redirect_refused_tampered_cache_redownloaded_and_export_error_included(self):
        observed=self.stable();reader=self.reader()
        packages=[p for r in observed['reports'].values() for p in r['packages'] if p['category']=='build_error']
        package=packages[0];path=urlsplit(package['log_url']).path
        for destination in ['http://authentication.invalid/login', self.server.url+'/outside/log.txt']:
            self.server.routes[path]=(302,b'',{'Location':destination},0)
            with self.assertRaises(FlowError) as caught:reader.fetch_log(reader.build_ref,package['key']['arch'],package)
            self.assertEqual(caught.exception.code,4);self.assertIn('todo',caught.exception.details)
            self.assertFalse(list(self.config.data_root.rglob('log.txt')))
        self.server.routes.pop(path)
        # Dispatch must include both error categories, without guessing an
        # unverified real Export table layout.
        packages[1]['category']='export_error'
        result=fetch_logs(reader,observed)
        self.assertEqual(len(result['logs']),2)
        target=Path(result['logs'][0]['path']);target.write_bytes(b'tampered')
        result=fetch_logs(reader,observed)
        self.assertFalse(result['logs'][0]['skipped']);self.assertTrue(result['logs'][1]['skipped'])
        self.assertEqual(digest(target.read_bytes()),result['logs'][0]['sha256'])

    def test_packages_error_exit_and_original_detail_title(self):
        self.server.routes['/build/19091860']=(200,b'19091860 <span title="Build   is   failed"></span>',{},0)
        self.assertEqual(self.observed()['execution_evidence']['title'],'Build   is   failed')
        self.server.routes[self.server.report_path('armv7l')]=(500,b'bad',{},0)
        result=read_action('fetch','packages',self.reader(),'armv7l')
        self.assertEqual(result['exit_code'],5)

    def test_proxy_config_only_and_tls_defaults(self):
        with patch.dict(os.environ,{'http_proxy':'http://invalid.invalid:1','https_proxy':'http://invalid.invalid:1','no_proxy':'','NO_PROXY':''}):
            self.assertEqual(self.observed()['exit_code'],0)
        self.config.raw['network'].update(proxy=self.server.url,no_proxy_hosts=[])
        self.config.raw['cosmos']['report_root']='http://must-not-resolve.invalid/reports/'
        self.config.raw['cosmos']['status_source']['url_template']='http://must-not-resolve.invalid/build/{build_id}'
        with patch.dict(os.environ,{'no_proxy':'*','NO_PROXY':'*'}):self.assertEqual(self.observed()['exit_code'],0)
        self.assertTrue(any(r['request_target'].startswith('http://must-not-resolve.invalid') for r in self.server.requests))
        self.assertTrue(direct_host('127.0.0.1',['127.0.0.0/8']))
        self.assertTrue(direct_host('a.example.invalid',['.example.invalid']))
        context=HTTPTransport(self.config).context
        self.assertTrue(context.check_hostname);self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)

    def test_fetch_defaults_template_validation_and_real_cli(self):
        raw=json.loads(self.server.config_path.read_text());raw.pop('fetch')
        self.server.config_path.write_text(json.dumps(raw));self.assertEqual(load_config(self.server.config_path).raw['fetch'],FETCH_DEFAULTS)
        for template in ['http://127.0.0.1/{run_id}','http://127.0.0.1/{build_id.x}']:
            raw['cosmos']['status_source']['url_template']=template;self.server.config_path.write_text(json.dumps(raw))
            with self.assertRaises(FlowError) as caught:load_config(self.server.config_path)
            self.assertEqual(caught.exception.code,2)
        raw=self.config.raw;self.server.config_path.write_text(json.dumps(raw))
        for skill,command in [('watch','observe'),('fetch','packages'),('fetch','inputs'),('fetch','groups'),('fetch','logs')]:
            proc=subprocess.run([sys.executable,str(REPO/f'vd-cosmos-{skill}/scripts/run.py'),command,'--config',str(self.server.config_path),
                                 '--backend','real','--build-id','19091860','--arch','armv7l'],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr);self.assertEqual(len(proc.stdout.splitlines()),1)
        with self.assertRaises(FlowError) as caught:HTTPReportReader(self.config,'../bad')
        self.assertEqual(caught.exception.code,2)


class WorkflowTests(HTTPTests):
    def test_notification_result_failure_recovers_without_duplicate_or_missing_todo(self):
        self.stable();time.sleep(.04)
        self.assertEqual(tick(self.config,lambda:self.reader())['action'],'observe')
        self.assertEqual(tick(self.config,lambda:self.reader())['action'],'logs')
        append=EventStore.append
        def interrupt_result(store,context,kind,payload,*args,**kwargs):
            if kind=='workflow_result' and payload.get('step')=='notify':
                raise FlowError(6,'simulated_interruption_before_commit_point')
            return append(store,context,kind,payload,*args,**kwargs)
        with patch.object(EventStore,'append',interrupt_result):
            with self.assertRaises(FlowError):tick(self.config,lambda:self.reader())
        self.assertNotEqual(status(self.config,self.reader())['phase'],'结果已拉取')
        final=tick(self.config,lambda:self.reader())
        self.assertEqual(final['phase'],'结果已拉取')
        with EventStore(self.config.data_root) as store:
            events=store.events()
        self.assertEqual(sum(e['kind']=='inbox_opened' and e['payload']['todo']['reason']=='analysis_pending' for e in events),1)
        self.assertEqual(sum(e['kind']=='workflow_result' and e['payload']['step']=='notify' for e in events),1)
        self.assertEqual(sum(r['path'].endswith('/log.txt') for r in self.server.requests),2)

    def test_views_do_not_append_and_stale_event_and_duplicate_result_rejected(self):
        first=tick(self.config,lambda:self.reader())
        before=status(self.config)['last_event_id']
        self.assertEqual(inbox(self.config)['last_event_id'],before)
        self.assertEqual(status(self.config,self.reader())['last_event_id'],before)
        with self.assertRaises(FlowError) as caught:tick(self.config,lambda:self.reader(),expected_event=0)
        self.assertEqual(caught.exception.code,6)
        with EventStore(self.config.data_root) as store:
            result=next(e for e in store.events() if e['kind']=='workflow_result')
            with self.assertRaises(FlowError) as caught:
                store.append(command_context('workflow.tick'),'workflow_result',result['payload'],store.head(),
                             operation_id=result['operation_id'])
            self.assertEqual(caught.exception.code,6)
        self.assertEqual(status(self.config)['last_event_id'],first['last_event_id'])

    def test_workflow_each_stop_condition_and_three_failures_todo(self):
        for condition in ['count','structure','header','coverage']:
            with tempfile.TemporaryDirectory(dir=self.base) as directory:
                config=copy.deepcopy(self.config);object.__setattr__(config,'data_root',Path(directory)/'data')
                original=self.server.routes[self.server.report_path('armv7l')]
                body=original[1]
                if condition=='count':body=body.replace(b'<td>4</td>',b'<td>5</td>',1)
                if condition=='structure':body=body.replace(b'> Failed </a>',b'> Skipped </a>')
                if condition=='header':body=body.replace(b'build.conf@14368686',b'build.conf@1')
                self.server.routes[self.server.report_path('armv7l')]=(200,body,{},0)
                rows=self.server.fixture/'extra-rows.txt';rows.write_text((self.server.fixture/'rows.txt').read_text()+'//example/missing@9\n')
                factory=lambda:HTTPReportReader(config,'19091860',rows if condition=='coverage' else None)
                first=tick(config,factory)
                time.sleep(.04)
                result=tick(config,factory)
                self.assertEqual(result['exit_code'],3,condition)
                self.server.routes[self.server.report_path('armv7l')]=original
        self.server.routes[self.server.report_path('armv7l')]=(500,b'bad',{},0)
        result=loop(self.config,lambda:self.reader(),max_ticks=3)
        self.assertEqual(result['ticks'],3);self.assertEqual(result['exit_code'],5)
        with EventStore(self.config.data_root) as store:
            todos=[e['payload']['todo'] for e in store.events() if e['kind']=='inbox_opened']
        self.assertEqual(sum(t['reason']=='three_consecutive_observation_failures' for t in todos),1)

    def test_crash_after_intent_redoes_action_and_has_one_result(self):
        process=multiprocessing.Process(target=crash_intent,args=(self.server.config_path,));process.start();process.join(5)
        self.assertEqual(process.exitcode,23)
        result=tick(self.config,lambda:self.reader());self.assertEqual(result['exit_code'],0)
        with EventStore(self.config.data_root) as store:
            events=store.events()
        self.assertEqual(sum(e['kind']=='workflow_intent' for e in events),2)
        self.assertEqual(sum(e['kind']=='workflow_result' for e in events),1)

    def test_sleep_allows_manual_tick_instance_lock_still_excludes_second_loop(self):
        self.config.raw['poll']['interval_s']=1
        self.stable();time.sleep(1.01)
        sleeping=threading.Event();results=[]
        thread=threading.Thread(target=lambda:results.append(loop(self.config,lambda:self.reader(),max_ticks=4,on_sleep=sleeping.set)))
        thread.start();self.assertTrue(sleeping.wait(3))
        with self.assertRaises(FlowError) as caught:loop(self.config,lambda:self.reader(),max_ticks=1)
        self.assertEqual(caught.exception.code,6)
        manual=tick(self.config,lambda:self.reader());self.assertEqual(manual['action'],'logs');self.assertEqual(manual['exit_code'],0)
        thread.join(5);self.assertFalse(thread.is_alive());self.assertEqual(results[0]['phase'],'结果已拉取')
        self.assertEqual(sum(r['path'].endswith('/log.txt') for r in self.server.requests),2)
        with EventStore(self.config.data_root) as store:
            events=store.events()
        self.assertEqual(sum(e['kind']=='inbox_opened' and e['payload']['todo']['reason']=='analysis_pending' for e in events),1)
        self.assertEqual(tick(self.config,lambda:self.reader())['action'],'none')

    def test_sigterm_and_sigint_clean_exit_release_instance_lock(self):
        for sig in [signal.SIGTERM,signal.SIGINT]:
            self.server.requests.clear()
            self.config.raw['poll']['interval_s']=.5;self.server.config_path.write_text(json.dumps(self.config.raw))
            proc=subprocess.Popen([sys.executable,str(REPO/'vd-cosmos-workflow/scripts/run.py'),'loop','--config',str(self.server.config_path),
                                   '--build-id','19091861','--max-ticks','100'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                if any(r['path'].startswith('/reports/b861/') for r in self.server.requests):break
                time.sleep(.01)
            time.sleep(.04);proc.send_signal(sig);out,err=proc.communicate(timeout=3)
            self.assertEqual(err,'');self.assertEqual(proc.returncode,0,out);self.assertTrue(json.loads(out)['interrupted'])
            self.assertEqual(loop(self.config,lambda:HTTPReportReader(self.config,'19091861'),max_ticks=1)['exit_code'],0)

    def test_b2_script_A_to_E_and_summary_size(self):
        from test_batch21 import isolated_checkout
        snapshot=self.base/'checkout';head=isolated_checkout(snapshot)
        cmd=['bash','--noprofile','--norc',str(snapshot/'vd-cosmos-core/scripts/verify_b2_real.sh'),head,'--config',str(self.server.config_path),
             '--build-id','19091860','--saved-dir',str(self.server.fixture),'--rows',str(self.server.fixture/'rows.txt'),
             '--links',str(self.server.fixture/'links.txt'),'--live-build-id','19091861','--mode','fixture',
             '--fixture-counts',str(self.server.fixture/'expected-counts.json')]
        process=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(process.stderr,'');self.assertEqual(process.returncode,0,process.stdout)
        output=json.loads(process.stdout.splitlines()[-1]);self.assertEqual(output['verdict'],'PASS');self.assertTrue(output['two_block_target_met'])
        result=load_json(output['result_file']['path'])
        for phase in ['A','B','C','E']:self.assertEqual(result[phase]['verdict'],'PASS')
        self.assertFalse(result['D']['evaluated_for_pass'])
        self.assertNotIn('members',result['A']['expansion_groups_top15'][0])
        self.assertEqual(result['A']['links_comparison']['expected_count'],1)
        self.assertEqual(result['A']['reports']['x86_64']['package_coverage'],'未核')

    def test_b2_wrong_commit_stops_before_loading_or_writing(self):
        proc=subprocess.run(['bash','--noprofile','--norc',str(CORE/'scripts/verify_b2_real.sh'),'wrong',
                             '--config',str(self.base/'missing.json')],capture_output=True,text=True)
        self.assertEqual(proc.returncode,6)
        self.assertEqual(json.loads(proc.stdout.splitlines()[-1])['error'],'expected_commit_mismatch')
        self.assertFalse(self.config.data_root.exists())


def load_tests(loader, tests, pattern):
    suite=unittest.TestSuite([loader.loadTestsFromTestCase(HTTPTests)])
    for name in WorkflowTests.__dict__:
        if name.startswith('test_'):suite.addTest(WorkflowTests(name))
    return suite
