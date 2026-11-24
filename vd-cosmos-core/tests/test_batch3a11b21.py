"""Browser temp isolation, durable cleanup and pre-navigation diagnostics."""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from unittest.mock import MagicMock, patch

from test_batch3a11b1 import B1Case
from test_batch3a11b2a import CTX, Processes
from vd_cosmos_core import browser_temp, browser_executable, submit_sessions as sessions, submit_model as model
from vd_cosmos_core.errors import FlowError
from vd_cosmos_submit.playwright_driver import Driver, environment, launch_diagnostic


class BrowserTempTests(B1Case):
    def profile(self):
        p=self.root/'profile';p.mkdir(exist_ok=True);return p
    def runtime(self):
        temp=tempfile.TemporaryDirectory(prefix='vct-',dir='/tmp');self.addCleanup(temp.cleanup)
        p=Path(temp.name);p.chmod(0o700);return p
    def test_private_owned_xdg_preferred_and_environment_child_only(self):
        runtime=self.runtime();profile=self.profile()
        with patch.dict(os.environ,{'XDG_RUNTIME_DIR':str(runtime),'TMPDIR':'unchanged','TMP':'unchanged','TEMP':'unchanged'}):
            temp=browser_temp.create(profile)
            try:
                self.assertEqual(temp.parent,runtime);self.assertTrue(browser_temp.fits(temp))
                self.assertEqual(temp.stat().st_mode & 0o777,0o700)
                child=environment(self.config,profile,temp)
                for key in ('TMPDIR','TMP','TEMP'):
                    self.assertEqual(child[key],str(temp));self.assertEqual(os.environ[key],'unchanged')
            finally:browser_temp.cleanup(profile)
        self.assertFalse(temp.exists());self.assertFalse((profile/browser_temp.MARKER).exists())
    def test_xdg_missing_public_long_relative_and_symlink_fall_back(self):
        runtime=self.runtime();runtime.chmod(0o755)
        long=self.root/('x'*130);long.mkdir(mode=0o700)
        link=self.root/'runtime-link';link.symlink_to(runtime,target_is_directory=True)
        for value in ('',str(self.root/'missing'),str(runtime),str(long),'relative',str(link)):
            with self.subTest(value=value),patch.dict(os.environ,{'XDG_RUNTIME_DIR':value}):
                profile=self.profile();temp=browser_temp.create(profile)
                self.assertEqual(temp.parent,Path('/tmp'));browser_temp.cleanup(profile)
    def test_xdg_wrong_owner_falls_back(self):
        runtime=self.runtime();uid=os.getuid();profile=self.profile()
        with patch.dict(os.environ,{'XDG_RUNTIME_DIR':str(runtime)}),patch.object(browser_temp.os,'getuid',return_value=uid+1):
            temp=browser_temp.create(profile)
        self.assertEqual(temp.parent,Path('/tmp'));browser_temp.cleanup(profile)
    def test_socket_length_is_bytes_strictly_under_100_and_refuses_before_launch(self):
        suffix=len(os.fsencode(browser_temp.SOCKET_SUFFIX))
        self.assertTrue(browser_temp.fits('x'*(99-suffix)))
        self.assertFalse(browser_temp.fits('x'*(100-suffix)))
        self.assertFalse(browser_temp.fits('界'*30))
        long=self.root/('x'*130);long.mkdir();profile=self.profile()
        with patch.object(browser_temp.tempfile,'mkdtemp',return_value=str(long)),patch.dict(os.environ,{'XDG_RUNTIME_DIR':''}):
            error=self.fails(6,browser_temp.create,profile)
        self.assertEqual(error.reason,'browser_tmpdir_too_long');self.assertFalse(long.exists())
        self.assertFalse((profile/browser_temp.MARKER).exists())
    def test_cleanup_identity_mismatch_refuses_then_valid_cleanup_is_idempotent(self):
        profile=self.profile();temp=browser_temp.create(profile);marker=profile/browser_temp.MARKER
        original=marker.read_text();record=json.loads(original);record['inode']+=1;marker.write_text(json.dumps(record))
        self.fails(6,browser_temp.cleanup,profile);self.assertTrue(temp.is_dir())
        marker.write_text(original);browser_temp.cleanup(profile);browser_temp.cleanup(profile)
        self.assertFalse(temp.exists())
    def test_finish_and_recovery_close_processes_before_removing_short_temp(self):
        for recovery in (False,True):
            with self.subTest(recovery=recovery):
                r=model.create_request(self.config,CTX,self.form()|{'EXTRA_BUILD_PARAMETER':str(recovery)},'fixture')
                proc=Processes();session=sessions.start(self.config,r,CTX,proc)
                profile=sessions.profile_path(self.config,session);temp=browser_temp.create(profile)
                proc.alive=False
                def close(path):
                    self.assertEqual(path,profile);self.assertTrue(temp.exists())
                proc.close=close
                if recovery:sessions.recover_locked(self.config,CTX,proc)
                else:sessions.finish(self.config,session,CTX,proc)
                self.assertFalse(temp.exists());self.assertFalse(profile.exists())
    def test_failed_process_cleanup_keeps_marker_and_temp_for_recovery(self):
        r=model.create_request(self.config,CTX,self.form(),'fixture');session=sessions.start(self.config,r,CTX,Processes())
        profile=sessions.profile_path(self.config,session);temp=browser_temp.create(profile)
        with patch.object(sessions.Processes,'close',side_effect=FlowError(6,'browser_cleanup_unverified')):
            self.fails(6,Driver(self.config,session).close)
        self.assertTrue(temp.exists());self.assertTrue((profile/browser_temp.MARKER).exists())
        browser_temp.cleanup(profile)


class LaunchDiagnosticTests(B1Case):
    def test_three_lines_only_with_full_message_credential_check(self):
        self.assertEqual(launch_diagnostic(self.config,RuntimeError('one\ntwo\nthree\nfour'),'start'),
            {'exception_type':'RuntimeError','stage':'start','detail':'one\ntwo\nthree'})
        for message in ('one\ntwo\nthree\nPassword=fixture-secret',  # credential-test-sample
                        'https://example.invalid/path?unlisted=value',
                        'Cookie: fixture',  # credential-test-sample
                        '{"profile":{"password_manager_enabled":false}}'):
            with self.subTest(message=message):
                self.assertEqual(launch_diagnostic(self.config,RuntimeError(message),'start')['detail'],'detail withheld')
    def fake_api(self,stage,message):
        api=ModuleType('playwright.sync_api');manager=MagicMock();pw=manager.start.return_value
        context=pw.chromium.launch.return_value.new_context.return_value;context.pages=[]
        cdp=context.new_cdp_session.return_value
        cdp.send.return_value={'frameTree':{'frame':{'id':'main'}},'targetInfo':{'targetId':'main'}}
        failure=RuntimeError(message)
        if stage=='start':manager.start.side_effect=failure
        elif stage=='launch':pw.chromium.launch.side_effect=failure
        elif stage=='new_page':context.new_page.side_effect=failure
        elif stage=='route':context.route_web_socket.side_effect=failure
        elif stage=='cdp':context.new_cdp_session.side_effect=failure
        elif stage=='fetch_enable':
            def send(command,*args):
                if command=='Fetch.enable':raise failure
                return {'frameTree':{'frame':{'id':'main'}},'targetInfo':{'targetId':'main'}}
            cdp.send.side_effect=send
        api.sync_playwright=lambda:manager
        return api
    def test_each_launch_stage_is_reported_and_failed_launch_cleans_temp(self):
        self.config.raw['submit']['browser_executable']='/bin/true'
        for stage in ('start','launch','new_page','route','cdp','fetch_enable'):
            with self.subTest(stage=stage):
                r=model.create_request(self.config,CTX,self.form()|{'EXTRA_BUILD_PARAMETER':stage},'fixture')
                s=sessions.start(self.config,r,CTX,Processes());driver=Driver(self.config,s,headless=True)
                profile=sessions.profile_path(self.config,s);created=[];create=browser_temp.create
                def track(p):
                    result=create(p);created.append(result);return result
                with patch.dict(sys.modules,{'playwright':ModuleType('playwright'),'playwright.sync_api':self.fake_api(stage,'safe startup failure')}),patch.object(browser_temp,'create',side_effect=track):
                    error=self.fails(5,driver.launch)
                self.assertEqual(error.reason,'browser_start_failed');self.assertEqual(error.details['stage'],stage)
                self.assertEqual(error.details['exception_type'],'RuntimeError');self.assertEqual(error.details['detail'],'safe startup failure')
                self.assertFalse(created[0].exists());self.assertFalse((profile/browser_temp.MARKER).exists())
                sessions.finish(self.config,s,CTX,Processes())
    def test_successful_launch_passes_private_env_and_close_removes_temp(self):
        self.config.raw['submit']['browser_executable']='/bin/true'
        r=model.create_request(self.config,CTX,self.form(),'fixture');s=sessions.start(self.config,r,CTX,Processes())
        api=self.fake_api(None,'unused');driver=Driver(self.config,s,headless=True)
        with patch.dict(os.environ,dict.fromkeys(('TMPDIR','TMP','TEMP'),'inherited-'+('x'*130))),patch.dict(sys.modules,{'playwright':ModuleType('playwright'),'playwright.sync_api':api}):
            driver.launch()
            kwargs=driver._pw.chromium.launch.call_args.kwargs
            temp=Path(kwargs['env']['TMPDIR']);self.assertTrue(browser_temp.fits(temp))
            for key in ('TMPDIR','TMP','TEMP'):
                self.assertEqual(kwargs['env'][key],str(temp));self.assertTrue(os.environ[key].startswith('inherited-'))
            driver.close();self.assertFalse(temp.exists());driver.close()
    def test_forced_launch_failure_with_credential_withholds_detail(self):
        self.config.raw['submit']['browser_executable']='/bin/true'
        r=model.create_request(self.config,CTX,self.form(),'fixture');s=sessions.start(self.config,r,CTX,Processes())
        api=self.fake_api('launch','Password=fixture-secret')  # credential-test-sample
        with patch.dict(sys.modules,{'playwright':ModuleType('playwright'),'playwright.sync_api':api}):
            error=self.fails(5,Driver(self.config,s,headless=True).launch)
        self.assertEqual(error.details['stage'],'launch');self.assertEqual(error.details['detail'],'detail withheld')
    def test_executable_override_and_default_use_resolved_wrapper(self):
        wrapper=self.root/'google-chrome';wrapper.write_text('#!/bin/sh\nexit 0\n');wrapper.chmod(0o700)
        link=self.root/'wrapper-link';link.symlink_to(wrapper)
        with patch.dict(os.environ,{'VD_COSMOS_CHROME':''}),patch.object(browser_executable.shutil,'which',return_value=str(link)):
            self.assertEqual(browser_executable.resolve(),str(wrapper))
            self.assertEqual(browser_executable.resolve('/bin/true'),str(Path('/bin/true').resolve()))
        with patch.dict(os.environ,{'VD_COSMOS_CHROME':str(link)}):self.assertEqual(browser_executable.resolve(),str(wrapper))
        with patch.dict(os.environ,{'VD_COSMOS_CHROME':'/does-not-exist'}):self.assertIsNone(browser_executable.resolve())
