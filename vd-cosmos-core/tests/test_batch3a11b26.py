import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from helpers import CORE, REPO
from test_batch3a11b1 import B1Case
from vd_cosmos_core import submit_source as source, verify_b3a11b2 as verify
from vd_cosmos_core.bm_reader import FixtureTransport, Reader
from vd_cosmos_core.report import parse_report

REPORTS = CORE / 'fixtures/real_format'
PAGES = CORE / 'fixtures/real_pages'
TABLE = PAGES / 'variables_19206687_table.html'
ARCHES = ('armv7l', 'x86_64')
HEADER_KEYS = source.REQUIRED_HEADERS | {'gbs_version', 'profile'}


class SourceHeadersTests(B1Case):
    def test_real_headers_match_full_parser_for_both_architectures(self):
        for arch in ARCHES:
            with self.subTest(arch=arch):
                data = (REPORTS / f'report_{arch}.html').read_bytes()
                headers = source.headers_only(data)
                result = parse_report(data.decode(), arch, self.config.raw['cosmos'], stable=True)
                self.assertEqual(headers, result['headers'])
                self.assertEqual(headers.keys(), HEADER_KEYS)
                self.assertTrue(all(headers[k] for k in source.REQUIRED_HEADERS))

    def test_headers_only_does_not_require_or_parse_summary_or_package_tables(self):
        data = (b'<p><b>Arch:</b> armv7l</p><p>Start Time: now</p><p>Base Snapshot: base</p>'
                b'<p>Product Snapshot: product</p><p>Build Conf: config</p>')
        with patch('vd_cosmos_core.report._summary_counts', side_effect=AssertionError('summary accessed')):
            self.assertEqual(source.headers_only(data)['arch'], 'armv7l')

    def test_missing_blank_conflicting_and_invalid_utf8_headers_fail_closed(self):
        data = (REPORTS / 'report_armv7l.html').read_bytes()
        self.assertEqual(source.headers_only(data + b'<p>Arch: armv7l</p>')['arch'], 'armv7l')
        conflict = self.fails(5, source.headers_only, data + b'<p><b>Arch:</b> x86_64</p>')
        self.assertEqual((conflict.reason, conflict.details['keys']), ('source_header_conflict', ['arch']))
        blank = self.fails(5, source.headers_only, b'<table><tr><td>Arch</td><td> </td></tr></table>')
        self.assertEqual(blank.reason, 'source_header_missing')
        self.assertIn('arch', blank.details['keys'])
        self.assertEqual(self.fails(5, source.headers_only, b'<p>Arch: \xff</p>').reason, 'source_header_unrecognized')


class SourcePreflightTests(B1Case):
    def reader_for(self, *, bad_report=None, table=None):
        self.config.raw['submit']['form'] = self.form()
        c = self.config.raw['cosmos']
        c.update(archs=list(ARCHES), report_root='https://reports.example.invalid',
                 report_path_template='{last3}/{build_id}/report_{arch}.html')
        shell = (PAGES / 'detail_19206687.html').read_bytes()
        table = TABLE.read_bytes() if table is None else table
        prefix, end = shell.rsplit(b'</body>', 1)
        detail = f'https://{c["bm_host"]}/build/19206687'
        bodies = {detail: shell, detail + '/variables': prefix + table + b'</body>' + end}
        for arch in ARCHES:
            bodies[f'https://reports.example.invalid/687/19206687/report_{arch}.html'] = (
                bad_report if arch == 'x86_64' and bad_report is not None else
                (REPORTS / f'report_{arch}.html').read_bytes())
        pages = {}
        for i, (url, data) in enumerate(bodies.items()):
            p = self.root / f'page-{i}'
            p.write_bytes(data)
            pages[url] = {'file': p.name, 'clock': {}}
        manifest = self.root / 'source-pages.json'
        manifest.write_text(json.dumps({'pages': pages}))
        self.path.write_text(json.dumps(self.config.raw))
        return Reader(self.config, transport=FixtureTransport(manifest))

    def test_verifier_preflight_reads_all_four_pages_and_writes_no_state(self):
        reader = self.reader_for()
        evidence = {}
        with patch.object(verify, 'Reader', return_value=reader), patch.object(source, 'EventStore') as store:
            verify.source_preflight(self.config, evidence)
        store.assert_not_called()
        self.assertFalse(self.config.data_root.exists())
        self.assertEqual(len(reader.transport.counts), 4)
        self.assertIn('hub_id', evidence['detail_keys'])
        self.assertEqual(evidence['variable_keys'], sorted(source.COPY_DEFAULT))
        self.assertEqual(evidence['report_header_keys'], {arch: sorted(HEADER_KEYS) for arch in ARCHES})
        self.assertNotIn('fixture-base', json.dumps(evidence))

    def test_read_only_probe_checks_frozen_variables_without_writing_issue_files(self):
        reader = self.reader_for()
        reader.variables('19206687', {'BUILD_CONF'})
        before = {p: p.read_bytes() for p in self.config.data_root.rglob('*') if p.is_file()}
        reader = self.reader_for(table=TABLE.read_bytes().replace(b'fixture-conf', b'changed-conf'))
        with patch.object(verify, 'Reader', return_value=reader):
            self.assertEqual(self.fails(3, verify.source_preflight, self.config, {}).reason, 'variable_page_changed')
        self.assertEqual({p: p.read_bytes() for p in self.config.data_root.rglob('*') if p.is_file()}, before)

    def test_missing_report_header_makes_verifier_fail_with_keys_found_so_far(self):
        reader = self.reader_for(bad_report=b'<p>Arch: x86_64</p>')
        def offline(config, repo, directory, env):
            output = directory / 'offline.txt'
            output.write_text('offline fixture passed')
            return {'path': str(output)}
        args = SimpleNamespace(verified_commit='a'*40, config=self.path, chrome=None)
        with patch.object(verify, 'Reader', return_value=reader), patch.object(verify.subprocess, 'check_output',
                side_effect=['a'*40, b'']), patch.object(verify, 'contracts', return_value=[]), patch.object(verify,
                'process', return_value=SimpleNamespace(stdout=b'PASS', stderr=b'', returncode=0)), patch.object(
                verify, 'offline_tests', side_effect=offline):
            result = verify.execute(args, REPO)
        self.assertEqual((result['verdict'], result['exit_code'], result['failed_stage']),
                         ('FAIL', 5, 'anonymous_source_preflight'))
        self.assertEqual((result['error'], result['details']['arch']), ('source_header_missing', 'x86_64'))
        receipt = result['source_preflight']
        self.assertEqual(receipt['report_header_keys'], {'armv7l': sorted(HEADER_KEYS), 'x86_64': ['arch']})
        self.assertEqual(receipt['status'], 'FAIL')
        self.assertEqual(json.loads(Path(result['result_file']['path']).read_bytes())['source_preflight'], receipt)
        self.assertFalse((self.config.data_root / 'inputs').exists())
