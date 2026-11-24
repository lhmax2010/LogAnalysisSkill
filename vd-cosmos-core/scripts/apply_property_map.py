#!/usr/bin/env python3
"""Install the approved property map or import local browser settings."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import load_json
from vd_cosmos_core.submit_config import property_map_defaults


def object_members(text, start):
    """Locate value spans in an already validated JSON object."""
    decoder = json.JSONDecoder()

    def next_token(index):
        while text[index] in ' \t\n\r':
            index += 1
        return index

    index = next_token(start + 1)
    members = {}
    while text[index] != '}':
        key, end = decoder.raw_decode(text, index)
        value_start = next_token(next_token(end) + 1)
        _, value_end = decoder.raw_decode(text, value_start)
        members[key] = (value_start, value_end)
        index = next_token(value_end)
        if text[index] == ',':
            index = next_token(index + 1)
    return members, index


def rewrite(text, updates):
    root, root_end = object_members(text, len(text) - len(text.lstrip()))
    def encode(value):
        return json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\n    ')
    if 'submit' not in root:
        return text[:root_end] + ',"submit":' + encode(updates) + text[root_end:]
    submit, submit_end = object_members(text, root['submit'][0])
    added = [json.dumps(key) + ':' + encode(updates[key]) for key in updates.keys() - submit.keys()]
    if added:
        text = text[:submit_end] + (',' if submit else '') + ','.join(sorted(added)) + text[submit_end:]
    for (start, end), key in sorted(((submit[k],k) for k in updates.keys() & submit.keys()), reverse=True):
        text = text[:start] + encode(updates[key]) + text[end:]
    return text


BROWSER_KEYS = {'auth_paths', 'static_paths', 'target_config', 'target_config_id', 'account'}


def browser_updates(path):
    data = load_json(path)
    if not isinstance(data, dict) or data.keys() - BROWSER_KEYS:
        raise FlowError(2, 'invalid_browser_input_keys')
    for key in data.keys() & {'target_config', 'target_config_id', 'account'}:
        value = data[key]
        if not isinstance(value, str) or not value or value != value.strip() or re.search(r'[\x00-\x1f\x7f]', value):
            raise FlowError(2, 'invalid_browser_input_value')
        if key == 'target_config_id' and not re.fullmatch(r'[0-9]+', value):
            raise FlowError(2, 'invalid_browser_input_value')
        if key == 'target_config' and any(not part.strip() or part != part.strip() or part in {'.','..'}
                                          for part in value.split('/')):
            raise FlowError(2, 'invalid_browser_input_value')
    return data


def sync_write(stream, data):
    stream.write(data)
    stream.flush()
    os.fsync(stream.fileno())


def apply(path, browser_input=None):
    try:
        import fcntl
    except ImportError:
        raise FlowError(6, 'fcntl_unavailable') from None
    if path.is_symlink() or not path.is_file():
        raise FlowError(2, 'existing_regular_config_required')
    path = path.resolve()
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise FlowError(6, 'config_update_busy') from None
        original = path.read_bytes()
        config = load_config(path)
        if config.raw['submit']['property_map_confirmed']:
            raise FlowError(4, 'property_map_already_confirmed')
        if config.raw['submit']['gate_patterns_confirmed']:
            raise FlowError(4, 'gate_patterns_already_confirmed')
        text = original.decode('utf-8')
        submit = json.loads(text).get('submit', {})
        if browser_input is None:
            old = submit.get('property_map', {})
            new = property_map_defaults()
            updates = {'property_map':new}
        else:
            new = browser_updates(browser_input)
            old = submit
            updates = {key:value for key,value in new.items() if key not in old or old[key]!=value}
        changes = {'added': sorted(new.keys() - old.keys()),
                   'changed': sorted(k for k in new.keys() & old.keys() if new[k] != old[k])}
        if not any(changes.values()):
            return changes
        mode = stat.S_IMODE(path.stat().st_mode)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.property-map-', delete=False) as output:
            pending = Path(output.name)
            try:
                sync_write(output, rewrite(text, updates).encode('utf-8'))
                load_config(pending)
                if path.read_bytes() != original:
                    raise FlowError(6, 'config_changed_during_update')
                stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                backup = path.with_name(path.name + '.bak-' + stamp)
                fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'wb') as stream:
                    sync_write(stream, original)
                os.fsync(directory)
                os.fchmod(output.fileno(), mode)
                os.replace(pending, path)
                os.fsync(directory)
            finally:
                pending.unlink(missing_ok=True)
        return changes
    finally:
        os.close(directory)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise FlowError(2, 'config_path_required')


def main():
    parser = Parser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--browser-input', type=Path)
    try:
        args = parser.parse_args()
        section = 'submit' if args.browser_input is not None else 'submit.property_map'
        print(json.dumps({'ok': True, section: apply(args.config, args.browser_input)}))
        return 0
    except (OSError, ValueError):
        result = FlowError(6, 'config_update_failed')
    except FlowError as error:
        result = error
    print(json.dumps({'ok': False, 'error': result.reason, 'exit_code': result.code}))
    return result.code


if __name__ == '__main__':
    raise SystemExit(main())
