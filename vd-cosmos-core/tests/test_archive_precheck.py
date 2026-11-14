"""Q02: archive exceptions cannot change runtime credential decisions."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from helpers import REPO, config_data
from vd_cosmos_core.archive_precheck import check_file, REGISTRY
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.export import check_content, export_file
from vd_cosmos_core.files import digest
from vd_cosmos_core.verify_b3a11 import safe_bytes


class ArchivePrecheckTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config_path=self.root/'config.json'
        self.config_path.write_text(json.dumps(config_data(self.root/'data')))
        self.config=load_config(self.config_path)
        self.registry=json.loads((REPO/REGISTRY).read_text())
        self.entry=self.registry['entries'][0]
        self.path=self.root/self.entry['path'];self.path.parent.mkdir(parents=True)
        self.original=(REPO/self.entry['path']).read_bytes()
        self.path.write_bytes(self.original)
        self.registry_path=self.root/REGISTRY
        self.write_registry()

    def write_registry(self):
        self.registry_path.write_text(json.dumps(self.registry).replace('jsessionid=',r'jsessionid\u003d')) # credential-test-sample

    def check(self,path=None):
        return check_file(path or self.path,self.config,repo_root=self.root)

    def test_registered_original_hash_line_text_rule_passes_repository_cli(self):
        self.assertEqual(digest(self.original),'b8781bd49d91512f0d2c0b6b8a4e92a0900658aa04487f54b1bca7152232ff81')
        result=self.check()
        self.assertTrue(result['allowed'])
        self.assertEqual([(e['line'],e['pattern_index']) for e in result['archive_exemptions']],[(45,2)])
        self.assertTrue(check_content((REPO/REGISTRY).read_bytes(),self.config)['allowed'])
        process=subprocess.run([sys.executable,str(REPO/'vd-cosmos-core/scripts/run.py'),'prepush',
            '--config',str(self.config_path),'--files',str(REPO/self.entry['path'])],
            capture_output=True,text=True,timeout=10)
        self.assertEqual(process.returncode,0,process.stdout)
        self.assertEqual(len(process.stdout.splitlines()),1)
        self.assertTrue(json.loads(process.stdout)['files'][0]['archive_exemptions'])

    def test_one_byte_change_and_inline_marker_cannot_keep_exemption(self):
        for content in (self.original+b' ',self.original+b'\n# credential-test-sample\n',
                        self.original.replace(b'jsessionid',b'jsessionIx',1)):
            self.path.write_bytes(content)
            result=self.check()
            self.assertFalse(result['allowed'])
            self.assertEqual(result['archive_error'],'archive_hash_mismatch')
        self.path.write_bytes(self.original)
        self.assertTrue(self.check()['allowed'])

    def test_same_text_in_unregistered_file_or_wrong_path_is_blocked(self):
        for path in (self.path.with_name('unregistered.py'),self.root/'outside.py'):
            path.write_bytes(self.original)
            self.assertFalse(self.check(path)['allowed'])
        linked=self.path.with_name('link.py');linked.symlink_to(self.path)
        self.assertFalse(self.check(linked)['allowed'])

    def test_real_session_value_still_blocked_and_never_exempted(self):
        text='jsessionid=actual-session-value' # credential-test-sample
        self.path.write_text(text)
        self.assertFalse(self.check()['allowed'])
        outside=self.root/'actual.txt';outside.write_text(text)
        self.assertFalse(self.check(outside)['allowed'])
        self.assertFalse(check_content(text.encode(),self.config)['allowed'])

    def test_each_constraint_required_and_unapproved_other_match_not_hidden(self):
        for field,value in [('line',44),('matched_text','other'),('credential_rule','not-the-rule')]:
            self.registry['entries'][0][field]=value;self.write_registry()
            self.assertFalse(self.check()['allowed'])
            self.registry=json.loads((REPO/REGISTRY).read_text())
        # Same registered hash does not license another rule matching the same bytes.
        self.write_registry()
        self.config.raw['prepush']['credential_patterns'].append('jsessionid')
        result=self.check()
        self.assertFalse(result['allowed'])
        self.assertIn(8,{x['pattern_index'] for x in result['credential_hits']})

    def test_registry_never_changes_runtime_export_or_verifier(self):
        before=copy.deepcopy(self.config.raw)
        with patch('vd_cosmos_core.archive_precheck.entries',side_effect=AssertionError('runtime read registry')):
            self.assertFalse(check_content(self.original,self.config)['allowed'])
            self.config.data_root.mkdir()
            (self.config.data_root/'recon23.py').write_bytes(self.original)
            with self.assertRaises(FlowError) as caught:
                export_file(self.config,'recon23.py',self.config.raw['export']['allow_types'][0],'archive')
            self.assertEqual(caught.exception.code,4)
            with self.assertRaises(FlowError) as caught:safe_bytes(self.config,self.original)
            self.assertEqual(caught.exception.code,4)
        self.assertEqual(self.config.raw,before)
        self.assertFalse((self.config.data_root/'export/archive').exists())
