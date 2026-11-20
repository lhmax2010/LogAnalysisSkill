import gzip
from pathlib import Path
import unittest

from vd_cosmos_core.diagnosis import classify, import_family, normalize, seed_tiers
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes

from test_batch3a2_package import BUILD, PackageFixture
from test_batch3a2_result import result_fixture
from vd_cosmos_core.analysis_result import accept_result


class DiagnosisTests(PackageFixture, unittest.TestCase):
    def test_version_release_exact_match_and_prefix_only_upgrades(self):
        log = (b'[  12s] clang -Warray-bounds -Wformat-future input.c\n'
               b'[  13s] src.c:12:2: error: failed [-Werror,-Wformat-future]\n'
               b'[  14s] src.c:13:1: warning: warning [-Werror=format-security]\n'
               b'[  15s] src.c:14:1: error: repeated [-Wuninitialized]\n'
               b'[  16s] src.c:15:1: error: different [-Wformat-future]\n')
        data = classify(self.config, log, {}, digest(log), '22.1.8-5.2')
        self.assertEqual([r['tier'] for r in data['locations']],
                         ['mandatory', 'peek', 'mandatory', 'mandatory'])
        self.assertTrue(data['locations'][0]['temporary_prefix_upgrade'])
        self.assertEqual(len({r['location_id'] for r in data['locations']}), 4)
        path = self.root / 'primary.xml.gz'
        with gzip.open(path, 'wb') as stream:
            stream.write(b'<metadata xmlns="http://linux.duke.edu/metadata/common">'
                         b'<package><name>clang</name><version ver="22.1.8" rel="5.2"/></package></metadata>')
        family = self.root / 'family.json'
        tiers = {k: sorted(v) for k, v in seed_tiers().items()}
        family.write_bytes(json_bytes({'schema_version': 1, 'clang_release': '22.1.8-5.1', 'tiers': tiers}))
        with self.assertRaisesRegex(FlowError, 'diagnosis_family_release_mismatch'):
            import_family(self.config, BUILD, family, path)
        family.write_bytes(json_bytes({'schema_version': 1, 'clang_release': '22.1.8-5.2', 'tiers': tiers}))
        self.assertTrue(Path(import_family(self.config, BUILD, family, path)['path']).is_file())
        result = classify(self.config, log, {}, digest(log), '22.1.8-5.2')
        self.assertEqual([r['tier'] for r in result['locations']],
                         ['ordinary', 'peek', 'mandatory', 'ordinary'])
        self.assertFalse(any(r['temporary_prefix_upgrade'] for r in result['locations']))
        self.assertIsNone(normalize('-Werror'))

    def test_comparison_table_labeling_and_escaped_text(self):
        task = self.prepare()
        path = self.root / task['directory'] / 'outputs/result.json'
        result = result_fixture(task)
        result['provenance']['analyst_type'] = 'manual'
        result['proposals']['root_cause'] = 'Text | <iframe>'
        result['proposals']['alternatives'] = [
            {'type': 'code', 'state': 'pending', 'summary': '', 'advantages': '', 'risks': '', 'reason': 'Needs review.'}]
        path.write_bytes(json_bytes(result))
        accept_result(self.config, BUILD, task['task_id'], task['attempt'])
        table = (self.root / f'rounds/{BUILD}/reports/analysis-comparison.md').read_text()
        self.assertIn('Text &#124; &lt;iframe&gt;', table)
        self.assertIn('待补：Needs review.', table)
        self.assertIn('未批准', table)
