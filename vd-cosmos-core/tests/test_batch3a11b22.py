"""Callback non-blocking contract, sandbox and verifier timeout regressions."""
import asyncio
import ast
import json
import io
from contextlib import redirect_stderr
import unittest
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
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
            route=Facade();driver._route(route);self.assertEqual(called,[])
            await asyncio.sleep(0);self.assertEqual(called,['continue'])
            route.request=SimpleNamespace(frame='iframe');driver._route(route)
            driver._new_page(route);driver._websocket(route)
            driver._cdp=route;driver._frame='main'
            from vd_cosmos_core.submit_gate import Gate
            driver.gate=Gate(self.config,rehearse=True);driver.gate.phase='business'
            driver._paused({'requestId':'id','frameId':'other','request':{'url':'https://hub.example.invalid/blocked','method':'GET'}})
            await asyncio.sleep(0)
            self.assertEqual(called[1:3],['abort','close']);self.assertEqual(called[3][0],'Fetch.failRequest')
        asyncio.run(scenario())
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
    def test_registered_callbacks_have_no_sync_calls_or_websocket_connection(self):
        path=REPO/'vd-cosmos-submit/src/vd_cosmos_submit/playwright_driver.py';tree=ast.parse(path.read_text())
        names={'_route','_paused','_new_page','_websocket','_deferred_done'}
        for method in (n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names):
            for call in (n for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)):
                self.assertNotIn(call.func.attr,{'send','close','abort','continue_','connect_to_server','_sync'})


class SandboxTests(B1Case):
    def test_launch_enables_sandbox_and_known_sandbox_failure_is_exit_6(self):
        self.config.raw['submit']['browser_executable']='/bin/true'
        r=model.create_request(self.config,CTX,self.form(),'fixture');s=sessions.start(self.config,r,CTX,Processes())
        helper=diagnostics.LaunchDiagnosticTests();api=helper.fake_api('launch_persistent_context','No usable sandbox!')
        with patch.dict(sys.modules,{'playwright':MagicMock(),'playwright.sync_api':api}):
            error=self.fails(6,Driver(self.config,s,headless=True).launch)
        self.assertEqual(error.reason,'browser_sandbox_unavailable')
        options=api.sync_playwright().start.return_value.chromium.launch_persistent_context.call_args.kwargs
        self.assertIs(options['chromium_sandbox'],True);self.assertNotIn('--no-sandbox',options['args'])


class VerificationProcessTests(B1Case):
    def test_timeout_kills_group_and_detached_browser_and_preserves_stream(self):
        directory=self.root/'verify';directory.mkdir();transcript=directory/'offline-tests.txt'
        # Both descendants ignore TERM, one escapes the child's process group.
        grand="import os,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('READY',os.getpid(),flush=True);time.sleep(100)"
        code="import subprocess,sys,time,signal;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('Python fixture',flush=True);subprocess.Popen([sys.executable,'-c',sys.argv[1]]);subprocess.Popen([sys.executable,'-c',sys.argv[1]],start_new_session=True);time.sleep(100)"
        observed=[]
        def inspect_live():
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                if transcript.exists() and transcript.read_text().count('READY')==2:observed.append(True);return
                time.sleep(.01)
        thread=threading.Thread(target=inspect_live);thread.start()
        error=self.fails(5,vp.process,[sys.executable,'-u','-c',code,grand],directory,os.environ,timeout=.8,terminate_grace=.15,config=self.config,artifact=transcript)
        thread.join();self.assertTrue(observed,'output must reach disk before timeout')
        self.assertEqual(error.reason,'acceptance_process_timeout');self.assertEqual(error.details['output_artifact']['path'],str(transcript))
        pids=[int(line.split()[1]) for line in transcript.read_text().splitlines() if line.startswith('READY')]
        self.assertEqual(len(pids),2)
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
