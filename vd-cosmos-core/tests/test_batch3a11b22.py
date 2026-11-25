"""Callback non-blocking contract, sandbox and verifier timeout regressions."""
import asyncio
import ast
import json
import io
from contextlib import redirect_stderr, redirect_stdout
import unittest
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from test_batch3a11b1 import B1Case
import test_batch3a11b21 as diagnostics
from test_batch3a11b2a import CTX,Processes
from helpers import REPO
from vd_cosmos_core import submit_model as model,submit_sessions as sessions,verification_process as vp
from vd_cosmos_core import verify_b3a11 as verify
from vd_cosmos_core.errors import FlowError
from vd_cosmos_submit.playwright_driver import Driver


class CallbackTests(B1Case):
    def test_callbacks_never_invoke_sync_facade_and_coroutines_complete(self):
        async def scenario():
            driver=Driver(self.config,{})
            driver._page=SimpleNamespace(main_frame='main')
            called=[]
            class Impl:
                _loop=asyncio.get_running_loop()
                async def abort(self):called.append('abort')
                async def continue_(self):called.append('continue')
                async def close(self):called.append('close')
                async def send(self,*args):called.append(args)
            class Facade:
                _impl_obj=Impl()
                request=SimpleNamespace(frame='main')
                def __getattr__(self,name):raise AssertionError('sync facade called: '+name)
            route=Facade()
            driver._new_page(route);driver._websocket(route)
            driver._cdp=route;driver._frame='main'
            from vd_cosmos_core.submit_gate import Gate
            driver.gate=Gate(self.config,rehearse=True);driver.gate.phase='business'
            driver._paused({'requestId':'id','frameId':'other','request':{'url':'https://hub.example.invalid/blocked','method':'GET'}})
            self.assertEqual(called,[])
            await asyncio.sleep(0)
            self.assertEqual(called[0],'close')
            self.assertEqual(called[1][0],'Fetch.failRequest')
            await asyncio.sleep(0)
            self.assertEqual(driver.pause_counts(),{'paused':1,'resolved':1,'pending':0,'closed_unconfirmed':0,'cancelled_on_close':0})
        asyncio.run(scenario())
    def test_network_redirect_and_late_start_use_exact_hop_identity(self):
        from vd_cosmos_core.submit_gate import Gate
        driver = Driver(self.config, {})
        driver.gate = Gate(self.config, rehearse=True)
        hub = driver.gate.origin
        hidden = 'https://idp.example.invalid/auth-only-path?opaque=fixture'
        first = {'requestId': 'same', 'request': {'url': hub+'/', 'method': 'GET'}, 'type': 'Document'}
        driver._network_start(first)
        previous = driver._flight_for_pause({'requestId': 'fetch-1', 'networkId': 'same'}, hub+'/', 'GET', 'Document', False)
        previous.decision = 'continued'
        second = driver._flight_for_pause({'requestId': 'fetch-2', 'networkId': 'same', 'redirectedRequestId': 'fetch-1'},
                                          hidden, 'POST', 'Document', False)
        driver._network_start({**first, 'request': {'url': hidden, 'method': 'POST'}, 'redirectResponse': {}})
        driver._finish_flight(previous)  # A delayed completion cannot remove the redirected hop.
        self.assertEqual(list(driver._in_flight.values()), [second])
        self.assertEqual(driver._in_flight_evidence(second.started_at + 1),
                         [{'origin': 'other', 'path': 'unregistered', 'method': 'POST', 'resource_type': 'Document',
                           'age_s': 1, 'paused': False, 'decision': 'none'}])
        driver._network_end({'requestId': 'same'})

        early = driver._flight_for_pause({'requestId': 'fetch-3', 'networkId': 'late'}, hub+'/a42?key3=opaque',
                                         'GET', 'Other', False)
        self.assertEqual(early.evidence['path_shape'], '/aN?keyN')
        driver._finish_flight(early)
        driver._network_start({**first, 'requestId': 'late'})
        self.assertFalse(driver._in_flight)
        self.assertEqual((driver._network_started, driver._network_finished), (3, 3))

    def test_missing_async_bridge_and_async_failure_fail_closed(self):
        driver=Driver(self.config,{})
        driver._defer(object(),'close');self.assertEqual(driver._fatal,'browser_callback_dispatch_failed')
        async def scenario():
            async def close():raise RuntimeError('fixture')
            owner=SimpleNamespace(_impl_obj=SimpleNamespace(_loop=asyncio.get_running_loop(),close=close))
            driver._fatal=None;driver._defer(owner,'close')
            await asyncio.sleep(0);await asyncio.sleep(0)
            self.assertEqual(driver._fatal,'browser_callback_dispatch_failed')
        asyncio.run(scenario())
    def test_inflight_unacknowledged_decision_closes_context_without_second_command(self):
        from vd_cosmos_core.submit_gate import Gate
        async def scenario():
            loop=asyncio.get_running_loop()
            driver=Driver(self.config,{})
            driver.gate=Gate(self.config,rehearse=True);driver.pause_timeout_s=.025
            sent=[]
            async def send(*args):
                sent.append(args)
                await asyncio.Event().wait()
            driver._cdp=SimpleNamespace(_impl_obj=SimpleNamespace(_loop=loop,send=send))
            url=driver.gate.origin+'/overview/35367'
            driver._frame='main';driver.gate.navigation(url)
            event={'requestId':'fixture','frameId':'main','resourceType':'Document','request':{'url':url,'method':'GET'}}
            driver._paused(event);driver._paused(event)
            await asyncio.sleep(.05)
            self.assertTrue(driver._emergency_close)
            self.assertEqual(sent,[('Fetch.continueRequest',{'requestId':'fixture','interceptResponse':True})])
            self.assertEqual(driver.pause_counts(),{'paused':1,'resolved':0,'pending':0,'closed_unconfirmed':1,'cancelled_on_close':0})
            e=self.fails(4,driver._check_pause_fault)
            self.assertEqual(e.reason,'paused_request_unresolved')
            self.assertEqual(e.details['gate_records'][0]['url_shape']['path'],'/overview/<id>')
        asyncio.run(scenario())

    def test_undecided_fetch_times_out_to_fail_only(self):
        from vd_cosmos_core.submit_gate import Gate
        async def scenario():
            loop=asyncio.get_running_loop();driver=Driver(self.config,{})
            driver.gate=Gate(self.config,rehearse=True);driver.pause_timeout_s=.015
            sent=[];finished=asyncio.Event()
            async def send(command,options):
                sent.append(command);finished.set()
            cdp=SimpleNamespace(_impl_obj=SimpleNamespace(_loop=loop,send=send))
            driver._begin_pause(cdp,'fetch_request','one',driver.gate.origin+'/fixture?v=private')
            await asyncio.wait_for(finished.wait(),2)
            await asyncio.sleep(0)
            self.assertEqual(sent,['Fetch.failRequest'])
            self.assertEqual(driver.pause_counts(),{'paused':1,'resolved':1,'pending':0,'closed_unconfirmed':0,'cancelled_on_close':0})
            self.assertNotIn('private',str(self.fails(4,driver._check_pause_fault).details))
        asyncio.run(scenario())
    def test_late_abort_after_intentional_teardown_is_resolved_as_cancellation(self):
        class TargetClosedError(Exception):
            pass
        async def scenario():
            driver=Driver(self.config,{})
            driver._closing=True;driver._tearing_down=True
            calls=[];done=asyncio.Event()
            async def send(command,options):
                calls.append(command);done.set()
                raise TargetClosedError()
            driver._cdp=SimpleNamespace(_impl_obj=SimpleNamespace(_loop=asyncio.get_running_loop(),send=send))
            from vd_cosmos_core.submit_gate import Gate
            driver.gate=Gate(self.config,rehearse=True)
            driver._paused({'requestId':'fixture','request':{'url':driver.gate.origin+'/favicon.ico','method':'GET'}})
            await asyncio.wait_for(done.wait(),2);await asyncio.sleep(0)
            self.assertEqual(calls,['Fetch.failRequest'])
            self.assertEqual(driver.pause_counts(),{'paused':1,'resolved':1,'pending':0,'closed_unconfirmed':0,'cancelled_on_close':1})
            driver._check_pause_fault()
        asyncio.run(scenario())

    def test_fetch_response_error_never_reenters_request_policy(self):
        from vd_cosmos_core.submit_gate import Gate
        async def scenario():
            driver=Driver(self.config,{})
            driver.gate=Gate(self.config,rehearse=True)
            sent=[];finished=asyncio.Event()
            async def send(*args):
                sent.append(args);finished.set()
            driver._cdp=SimpleNamespace(_impl_obj=SimpleNamespace(_loop=asyncio.get_running_loop(),send=send))
            event={'requestId':'fixture','responseErrorReason':'Failed',
                   'request':{'url':driver.gate.origin+'/app.js','method':'GET'}}
            with patch.object(driver.gate,'request',side_effect=AssertionError('ran request policy')) as policy:
                driver._paused(event)
                await asyncio.wait_for(finished.wait(),2);await asyncio.sleep(0)
            policy.assert_not_called()
            self.assertEqual(sent,[('Fetch.failRequest',{'requestId':'fixture','errorReason':'BlockedByClient'})])
            self.assertEqual(driver.pause_counts()['resolved'],1)
            driver._paused(event)
            await asyncio.sleep(0)
            self.assertEqual(len(sent),1)
        asyncio.run(scenario())
    def test_registered_callbacks_have_no_sync_calls_or_websocket_connection(self):
        path=REPO/'vd-cosmos-submit/src/vd_cosmos_submit/playwright_driver.py';tree=ast.parse(path.read_text())
        names={'_paused','_new_page','_websocket','_deferred_done','_attached_target'}
        for method in (n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names):
            for call in (n for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)):
                self.assertNotIn(call.func.attr,{'send','close','abort','continue_','connect_to_server','_sync'})


class SandboxTests(B1Case):
    def test_launch_enables_sandbox_and_known_sandbox_failure_is_exit_6(self):
        self.config.raw['submit']['browser_executable']='/bin/true'
        r=model.create_request(self.config,CTX,self.form(),'fixture');s=sessions.start(self.config,r,CTX,Processes())
        helper=diagnostics.LaunchDiagnosticTests();api=helper.fake_api('launch','No usable sandbox!')
        with patch.dict(sys.modules,{'playwright':MagicMock(),'playwright.sync_api':api}):
            error=self.fails(6,Driver(self.config,s,headless=True).launch)
        self.assertEqual(error.reason,'browser_sandbox_unavailable')
        options=api.sync_playwright().start.return_value.chromium.launch.call_args.kwargs
        self.assertIs(options['chromium_sandbox'],True);self.assertNotIn('--no-sandbox',options['args'])


class ProcessRaceTests(B1Case):
    def test_disappearing_proc_entry_is_ignored_during_browser_cleanup(self):
        proc=MagicMock()
        proc.name='123'
        proc.__truediv__.return_value.read_bytes.side_effect=ProcessLookupError
        profile=self.root/'test-profile'
        with patch.object(Path,'iterdir',return_value=[proc]):
            self.assertEqual(sessions.Processes().matching(profile),[])


class PauseReceiptTests(B1Case):
    def test_once_result_file_keeps_pause_counters_even_on_failure(self):
        from vd_cosmos_submit import cli
        counts={'paused':2,'resolved':1,'pending':0,'closed_unconfirmed':1,'cancelled_on_close':0}
        err=FlowError(4,'paused_request_unresolved',pause_counts=counts,gate_records=[
            {'reason':'paused_request_unresolved','stage':'fetch_request','url_shape':{'path':'registered_static'}}],
            request_records=[{'method':'GET','resource_type':'Image','host':'hub.example.invalid',
                              'path':'/asset.png','query_keys':['v'],'decision':'paused_request_unresolved'}])
        for outcome in (err,{'exit_code':0,'pause_counts':dict(counts,resolved=2,closed_unconfirmed=0)}):
            with self.subTest(outcome=type(outcome).__name__), redirect_stdout(io.StringIO()) as out:
                action={'side_effect':outcome} if isinstance(outcome,FlowError) else {'return_value':outcome}
                with patch.object(cli.submit_terminal,'human_context',return_value=CTX), patch.object(cli.submit_once,'run',**action):
                    code=cli.main(['once','--config',str(self.path),'--rehearse'])
            result=json.loads(out.getvalue())
            artifact=json.loads(Path(result['artifact']).read_bytes())
            if isinstance(outcome,FlowError):
                self.assertEqual((code,artifact['error'],artifact['details']['pause_counts']),(4,err.reason,counts))
                self.assertEqual(artifact['details']['gate_records'],err.details['gate_records'])
                self.assertEqual(artifact['details']['request_records'],err.details['request_records'])
            else:
                self.assertEqual((code,artifact['pause_counts']),(0,outcome['pause_counts']))


class VerificationProcessTests(B1Case):
    def test_timeout_kills_group_and_detached_browser_and_preserves_stream(self):
        directory=self.root/'verify';directory.mkdir();transcript=directory/'offline-tests.txt'
        # Both descendants ignore TERM, one escapes the child's process group.
        # Each marker must be a single pipe write; concurrent print() calls can interleave fields.
        grand="import os,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);os.write(1,f'READY {os.getpid()}\\n'.encode());time.sleep(100)"
        code="import subprocess,sys,time,signal;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('Python fixture',flush=True);subprocess.Popen([sys.executable,'-c',sys.argv[1]]);subprocess.Popen([sys.executable,'-c',sys.argv[1]],start_new_session=True);time.sleep(100)"
        def read_pids():
            return [int(line.split()[1]) for line in transcript.read_text().splitlines() if line.startswith('READY ')]
        budget=.8;start=time.monotonic();elapsed_from=None;observed=[]
        def clock():
            nonlocal elapsed_from
            now=time.monotonic()
            if elapsed_from is None and transcript.exists():
                pids=read_pids()
                if len(pids)==2:
                    observed.extend(pids);elapsed_from=now
            if elapsed_from is None and now-start>=10:elapsed_from=now
            return 0 if elapsed_from is None else budget+now-elapsed_from
        with patch.object(vp,'time',SimpleNamespace(monotonic=clock,sleep=time.sleep)):
            error=self.fails(5,vp.process,[sys.executable,'-u','-c',code,grand],directory,os.environ,timeout=budget,terminate_grace=.15,config=self.config,artifact=transcript)
        self.assertEqual(len(observed),2,'both complete markers must reach disk before timeout')
        self.assertEqual(error.reason,'acceptance_process_timeout');self.assertEqual(error.details['output_artifact']['path'],str(transcript))
        pids=read_pids()
        self.assertEqual(observed,pids)
        deadline=time.monotonic()+3
        while any(vp.identity(pid) is not None for pid in pids) and time.monotonic()<deadline:time.sleep(.01)
        self.assertTrue(all(vp.identity(pid) is None for pid in pids))
    def test_streaming_never_persists_split_credential(self):
        directory=self.root/'verify';directory.mkdir();out=directory/'out.txt'
        code="import sys,time;print('safe line',flush=True);sys.stdout.write('Coo');sys.stdout.flush();time.sleep(.1);print('kie: fixture-value',flush=True)"  # credential-test-sample
        error=self.fails(4,vp.process,[sys.executable,'-u','-c',code],directory,os.environ,config=self.config,artifact=out,terminate_grace=.1)
        self.assertEqual(error.reason,'acceptance_credential_blocked');self.assertEqual(out.read_text(),'safe line\n')
    def test_timeout_artifact_propagates_through_offline_suite(self):
        artifact={'path':str(self.root/'offline-tests.txt'),'sha256':'fixture'}
        with patch.object(verify,'process',side_effect=FlowError(5,'acceptance_process_timeout',output_artifact=artifact)):
            error=self.fails(5,verify.offline_tests,self.config,REPO,self.root,os.environ)
        self.assertEqual(error.details['test_output'],artifact)
    def test_detached_path_only_match_does_not_select_unrelated_process(self):
        directory=self.root/'verify';directory.mkdir()
        code='import time;time.sleep(100)'
        child=subprocess.Popen([sys.executable,'-c',code,'--user-data-dir='+str(directory/'browser/profiles/fixture')],start_new_session=True)
        other=subprocess.Popen([sys.executable,'-c',code],start_new_session=True)
        try:
            selected={pid for pid,_ in vp.owned_processes(directory)}
            self.assertIn(child.pid,selected);self.assertNotIn(other.pid,selected)
        finally:
            child.kill();other.kill();child.wait();other.wait()


class WatchdogTests(B1Case):
    def test_hung_test_has_deadline_stack_dump_and_failure(self):
        import headless_watchdog as watchdog
        class Probe(watchdog.HeadlessWatchdog,unittest.TestCase):
            watchdog_seconds=.35
            def runTest(self):pass
        worker="import faulthandler,time;faulthandler.enable();faulthandler.dump_traceback_later(.1);time.sleep(100)"
        output=io.StringIO();result=unittest.TestResult()
        with patch.object(watchdog,'WORKER',worker),redirect_stderr(output):Probe().run(result)
        self.assertEqual(len(result.failures),1)
        self.assertIn('watchdog expired',result.failures[0][1]);self.assertIn('Timeout',output.getvalue())
        self.assertIn('Thread',output.getvalue())
