"""Offline fixtures only: saved HTML must never execute or disclose credentials."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ef5_rbs_form import DOM, FormRedactor, action_info, archive_form, inspect_form, main

FORM = '''<title>QuickBuild - root/Test/RBS/TRIGGER</title>
<div>Welcome! Fixture User</div>
<form id="search" method="post" action="page?1.IFormSubmitListener-search">
<input name="search"><button type="submit">Search</button></form>
<form id="run" method="post" action="page?1.IFormSubmitListener-form">
<table><tr><td class="name"><span class="form-label">PROJECT_NAME</span></td>
<td>Test Project</td></tr>
<tr><td class="name"><span class="form-label">BUILD_REFERENCE</span></td><td>
<span class="required" title="This field is required">*</span>
<select id="reference" name="property:select"
onchange="wicketAjaxPost('page?1.IBehaviorListener-reference',serialize(this))">
<option value="0">Live</option><option selected value="1">Ref. Snapshot</option>
<option value="2">Snapshot Number</option></select></td></tr>
<tr><td class="name"><span class="form-label">CHILD_CONFIGURATIONS</span></td><td>
<input type="hidden" name="property:palette:recorder" id="recorder" value="61"
onchange="wicketAjaxPost('page?1.IBehaviorListener-recorder',serialize(this))">
<table><tr><td><select id="choices" name="property:palette:choices" multiple></select></td>
<td><button type="button"
onclick="Wicket.Palette.add('choices','selection','recorder')"></button></td>
<td><select id="selection" name="property:palette:selection" multiple>
<option value="61">a</option></select></td></tr></table>
<script>Wicket.Form.excludeFromAjaxSerialization.choices='true';
Wicket.Form.excludeFromAjaxSerialization.selection='true';</script></td></tr>
<tr><td class="name"><span class="form-label">Build Package List</span></td><td>
<textarea name="packages">repo@commit\nrepo2@commit2</textarea></td></tr></table>
<input type="hidden" name="empty" value=""><input type="hidden" name="absent">
<label for="stop">Immediate Stop</label><input id="stop" name="stop" type="checkbox" checked>
<input name="radio" type="radio" value="x"><input name="required" required value="text">
<button type="submit" onclick="this.closest('form').submit()">Ok</button>
<a class="btn" href="page?1.ILinkListener-form-cancel">Cancel</a></form>
<script src="https://example.invalid/palette.js"></script>
'''


class FormTests(unittest.TestCase):
    def test_redaction_secrets_identity_urls_and_hidden_values(self):
        source = FORM + '''<input type="hidden" name="JSESSIONID_8810" value="session-private">
<a href="/wicket/page;jsessionid=session-private?csrf=csrf-private">link</a>
<script>var token = 'token-private'; var sessionValue = "session-private";</script>
<input type="hidden" name="ordinary" value="1"><option value="1">business</option>
'''
        r = FormRedactor()
        safe = r.redact(source)
        for secret in ('session-private', 'csrf-private', 'token-private', 'Fixture User'):
            self.assertNotIn(secret, safe)
        self.assertIn('value="1">business', safe)
        self.assertIn('&lt;USER&gt;', safe)
        self.assertIn('&lt;REDACTED&gt;', safe)
        r.check_safe(safe)
        self.assertEqual(r.redact(safe), safe)
        self.assertEqual(safe.count('\n'), source.count('\n'))

    def test_identity_is_not_removed_from_listener_or_function_identifiers(self):
        r = FormRedactor()
        safe = r.redact('<div>Welcome! Link</div><a href="page?1.ILinkListener-form-cancel">'
                        'Cancel</a><script>onCopyClipboardLinkDomReady()</script>')
        self.assertIn('ILinkListener', safe)
        self.assertIn('onCopyClipboardLinkDomReady', safe)
        self.assertNotIn('Welcome! Link', safe)

    def test_unquoted_session_values_and_explicit_accept_prohibition(self):
        source = ('<a href="/x;jsessionid=private-session?csrf=private-csrf'
                  '&amp;token=private-token">'
                  'x</a><script>sessionKey=private-session; tokenKey="private-token";</script>')
        safe = FormRedactor().redact(source)
        for secret in ('private-session', 'private-csrf', 'private-token'):
            self.assertNotIn(secret, safe)
        self.assertIn('?csrf=&lt;REDACTED&gt;', safe)
        self.assertIn('&amp;token=&lt;REDACTED&gt;', safe)
        action = action_info('page?1.ILinkListener-content-buildHead-promote')
        self.assertTrue(action['permanently_forbidden'])
        self.assertFalse(action_info('page?1.IFormSubmitListener-form')['permanently_forbidden'])

    def test_forms_fields_required_defaults_and_all_options(self):
        data = inspect_form(FormRedactor().redact(FORM))
        self.assertEqual(len(data['forms']), 2)
        run = data['forms'][1]
        self.assertEqual(run['method'], 'post')
        self.assertEqual(run['action']['listeners'], ['IFormSubmitListener'])
        fields = {f['html_name']: f for f in run['fields']}
        ref = fields['property:select']
        self.assertEqual(ref['label'], 'BUILD_REFERENCE')
        self.assertTrue(ref['required_marker_observed'])
        self.assertEqual(ref['default'], ['1'])
        self.assertEqual([o['value'] for o in ref['options']], ['0', '1', '2'])
        self.assertEqual([o['text'] for o in ref['options']], ['Live', 'Ref. Snapshot',
                                                              'Snapshot Number'])
        self.assertEqual(fields['stop']['default'], {'checked': True, 'value_attribute': None})
        self.assertFalse(fields['radio']['default']['checked'])
        self.assertTrue(fields['required']['required_marker_observed'])
        self.assertEqual(fields['empty']['default'], '<REDACTED>')
        self.assertFalse(fields['absent']['value_attribute_present'])
        self.assertEqual(fields['packages']['default'], 'repo@commit\nrepo2@commit2')
        self.assertEqual(run['read_only_fields'][0]['value'], 'Test Project')

    def test_palette_nested_rows_labels_and_no_invented_serialization(self):
        data = inspect_form(FormRedactor().redact(FORM))
        palette = data['forms'][1]['palettes'][0]
        self.assertEqual(palette['label'], 'CHILD_CONFIGURATIONS')
        self.assertEqual(palette['recorder_name'], 'property:palette:recorder')
        self.assertEqual(len(palette['excluded_from_ajax_serialization']), 2)
        self.assertEqual(palette['members'][2]['options'][0]['value'], '61')
        self.assertEqual(palette['recorder_value'], '<REDACTED>')
        self.assertIn('NOT_OBSERVED', palette['multi_value_serialization'])
        self.assertEqual(palette['actual_submission'], 'NOT_PERFORMED')

    def test_ajax_and_buttons_are_metadata_not_executed_or_inferred(self):
        data = inspect_form(FormRedactor().redact(FORM))
        ref = next(f for f in data['forms'][1]['fields'] if f['label'] == 'BUILD_REFERENCE')
        event = ref['events'][0]
        self.assertTrue(event['server_callback'])
        self.assertEqual(event['urls'][0]['listeners'], ['IBehaviorListener'])
        self.assertEqual(event['refreshed_fields'], 'NOT_OBSERVED_IN_SAVED_HTML')
        cancel = next(b for b in data['buttons'] if b['text'] == 'Cancel')
        self.assertEqual(cancel['href']['listeners'], ['ILinkListener'])
        ok = next(b for b in data['buttons'] if b['text'] == 'Ok')
        self.assertIsNone(ok['name'])
        self.assertEqual(ok['form_action']['value'], 'page?1.IFormSubmitListener-form')
        self.assertFalse(data['javascript_executed'])

    def test_archive_no_network_no_raw_copy_exact_bytes_original_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'source.html'
            raw = FORM.replace('\n', '\r\n').encode()
            source.write_bytes(raw)
            with patch('socket.socket.connect', side_effect=AssertionError('network')) as connect, \
                    patch('urllib.request.OpenerDirector.open',
                          side_effect=AssertionError('network')) as request:
                result = archive_form(source, root/'out')
            connect.assert_not_called()
            request.assert_not_called()
            self.assertEqual(result['network_requests'], 0)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual({p.name for p in (root/'out').iterdir()},
                             {'form.redacted.html', 'form.json'})
            safe = (root/'out/form.redacted.html').read_bytes()
            self.assertIn(b'\r\n', safe)
            self.assertNotIn(b'Fixture User', safe)
            data = json.loads((root/'out/form.json').read_bytes())
            self.assertEqual(hashlib.sha256(safe).hexdigest(), data['redacted_sha256'])
            self.assertTrue(data['hidden_palette_value_shapes'][0]['single_hex_value'])
            self.assertTrue(data['hidden_palette_value_shapes'][0]['matches_visible_option_value'])
            shape = data['hidden_palette_value_shapes'][0]
            self.assertTrue(shape['hex_decodes_to_visible_option_text'])
            with self.assertRaises(FileExistsError):
                archive_form(source, root/'out')

    def test_source_positions_match_redacted_lines(self):
        safe = FormRedactor().redact(FORM)
        nodes = DOM(safe).root.walk()
        for node in nodes:
            if node.tag != 'document':
                self.assertTrue(safe[node.start:].startswith(node.raw_tag))
                self.assertEqual(safe.count('\n', 0, node.start) + 1, node.line)
        data = inspect_form(safe)
        for form in data['forms']:
            for f in form['fields']:
                line = int(f['source'].rsplit(':', 1)[1])
                self.assertIn('name="'+f['html_name']+'"', safe.splitlines()[line-1])

    def test_redaction_fail_closed_and_missing_file_fixed_diagnostic(self):
        r = FormRedactor()
        for bad in ('<input type="hidden" value="private">',
                    '<a href="/;jsessionid=private">x</a>'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                r.check_safe(bad)
        out = io.StringIO()
        args = ['probe', '--input', '/missing-fixture.html', '--output', '/unused']
        with patch('sys.argv', args), \
                patch('sys.addaudithook') as hook, contextlib.redirect_stdout(out):
            self.assertEqual(main(), 1)
        self.assertNotIn('/missing-fixture.html', out.getvalue())
        guard = hook.call_args.args[0]
        for event in ('socket.connect', 'socket.getaddrinfo', 'socket.sendto'):
            with self.assertRaises(RuntimeError):
                guard(event, ())


if __name__ == '__main__':
    unittest.main()
