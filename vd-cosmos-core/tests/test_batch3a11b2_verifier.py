"""Verifier never calls live doctor, lookup, once or P4."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from test_batch3a11b1 import B1Case
from helpers import REPO
from vd_cosmos_core import verify_b3a11b2 as verify
from vd_cosmos_core.errors import FlowError

class B2VerifierTests(B1Case):
    def args(self):return SimpleNamespace(verified_commit='a'*40,config=str(self.path),chrome='/opt/google/chrome/chrome')
    def test_config_auth_or_static_cannot_whitelist_business_endpoints(self):
        from vd_cosmos_core.config import load_config
        raw=json.loads(self.path.read_text())
        raw.setdefault('submit',{})['auth_paths']=[{'host':'hub.example.invalid','path':'/wicket/page','method':'POST'}]
        self.path.write_text(json.dumps(raw));self.fails(2,load_config,self.path)
        raw['submit']['auth_paths']=[];raw['submit']['static_paths']=['/overview/123']
        self.path.write_text(json.dumps(raw));self.fails(2,load_config,self.path)
    def test_wrong_head_never_reads_config_or_creates_output(self):
        with patch.object(verify.subprocess,'check_output',return_value='b'*40),patch.object(verify,'load_config') as load:
            self.fails(6,verify.execute,self.args(),REPO);load.assert_not_called()
    def test_requires_real_browser_tests_in_fresh_root_no_live_calls(self):
        seen=[]
        def suite(config,repo,directory,env):
            self.assertEqual(env['VD_REQUIRE_HEADLESS'],'1');self.assertEqual(env['VD_COSMOS_CHROME'],'/opt/google/chrome/chrome');seen.append(directory)
            p=directory/'test.txt';p.write_text('Python 3.10.12\nlocal tests\n');return {'path':str(p),'sha256':'fixture'}
        with patch.object(verify.subprocess,'check_output',side_effect=['a'*40,b'','a'*40,b'']),patch.object(verify,'contracts',return_value=[]),patch.object(verify,'process',return_value=SimpleNamespace(stdout=b'PASS',stderr=b'',returncode=0)),patch.object(verify,'offline_tests',side_effect=suite):
            first=verify.execute(self.args(),REPO);second=verify.execute(self.args(),REPO)
        self.assertEqual(first['exit_code'],0);self.assertFalse(first['live_operations']);self.assertNotEqual(first['data_root'],second['data_root']);self.assertEqual(len(seen),2)
        self.assertTrue(all(p.is_relative_to(self.config.data_root) for p in seen))
    def test_missing_browser_suite_fails_and_preserves_safe_reason(self):
        with patch.object(verify.subprocess,'check_output',side_effect=['a'*40,b'']),patch.object(verify,'contracts',return_value=[]),patch.object(verify,'process',return_value=SimpleNamespace(stdout=b'PASS',stderr=b'',returncode=0)),patch.object(verify,'offline_tests',side_effect=FlowError(6,'offline_suite_failed')):
            result=verify.execute(self.args(),REPO)
        self.assertEqual(result['exit_code'],6);self.assertEqual(result['failed_stage'],'offline_suite_with_required_headless');self.assertEqual(result['verdict'],'FAIL')
