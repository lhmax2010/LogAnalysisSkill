"""Synthetic archive controls; no live credentials or network requests."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ef5_redact_archive import encode_json, redact_archive
from ef5_web_probe import PageInventory


class ArchiveTests(unittest.TestCase):
    def test_html_and_derived_json_updated_together(self) -> None:
        raw = (b'<span>Welcome! <span>ArchiveUser</span></span>\n'
               b'<table><tr><th>Triggered By</th></tr><tr><td>ArchiveAccount</td></tr></table>'
               b'<a href="/build/1069540">Child</a><a>Anchor without href</a>')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'page.response.txt').write_bytes(raw)
            parsed = PageInventory()
            parsed.feed(raw.decode())
            (root / 'page.page.json').write_bytes(encode_json({
                'visible_text': parsed.lines, 'form_fields_metadata_only': parsed.inputs,
                'links': [{**link, 'decision': 'NOT_FOLLOWED'}
                          for link in parsed.links if link['href']],
            }))
            (root / 'requests.json').write_bytes(encode_json([{
                'response': 'page.response.txt', 'redacted_sha256': hashlib.sha256(raw).hexdigest(),
            }]))
            report = redact_archive(root)
            self.assertEqual(report['network_requests'], 0)
            for path in root.iterdir():
                self.assertNotIn('ArchiveUser', path.read_text())
                self.assertNotIn('ArchiveAccount', path.read_text())
            records = json.loads((root / 'requests.json').read_text())
            safe = (root / 'page.response.txt').read_bytes()
            self.assertEqual(records[0]['redacted_sha256'], hashlib.sha256(safe).hexdigest())
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            redact_archive(root)
            self.assertEqual(before, {path.name: path.read_bytes() for path in root.iterdir()})

    def test_bad_hash_rejected_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'page.response.txt').write_bytes(b'original')
            (root / 'requests.json').write_bytes(encode_json([{
                'response': 'page.response.txt', 'redacted_sha256': 'incorrect',
            }]))
            with self.assertRaises(ValueError):
                redact_archive(root)
            self.assertEqual((root / 'page.response.txt').read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()
