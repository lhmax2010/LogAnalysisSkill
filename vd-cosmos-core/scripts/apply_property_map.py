#!/usr/bin/env python3
"""Install only the approved property map in an existing configuration."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
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


def rewrite(text, replacement):
    root, root_end = object_members(text, len(text) - len(text.lstrip()))
    value = json.dumps(replacement, ensure_ascii=False, indent=2).replace('\n', '\n    ')
    if 'submit' not in root:
        return text[:root_end] + ',"submit":{"property_map":' + value + '}' + text[root_end:]
    submit, submit_end = object_members(text, root['submit'][0])
    if 'property_map' not in submit:
        return text[:submit_end] + (',' if submit else '') + '"property_map":' + value + text[submit_end:]
    start, end = submit['property_map']
    return text[:start] + value + text[end:]


def sync_write(stream, data):
    stream.write(data)
    stream.flush()
    os.fsync(stream.fileno())


def apply(path):
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
        text = original.decode('utf-8')
        old = json.loads(text).get('submit', {}).get('property_map', {})
        new = property_map_defaults()
        changes = {'added': sorted(new.keys() - old.keys()),
                   'changed': sorted(k for k in new.keys() & old.keys() if new[k] != old[k])}
        if not any(changes.values()):
            return changes
        mode = stat.S_IMODE(path.stat().st_mode)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.property-map-', delete=False) as output:
            pending = Path(output.name)
            try:
                sync_write(output, rewrite(text, new).encode('utf-8'))
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
    try:
        args = parser.parse_args()
        print(json.dumps({'ok': True, 'submit.property_map': apply(args.config)}))
        return 0
    except (OSError, ValueError):
        result = FlowError(6, 'config_update_failed')
    except FlowError as error:
        result = error
    print(json.dumps({'ok': False, 'error': result.reason, 'exit_code': result.code}))
    return result.code


if __name__ == '__main__':
    raise SystemExit(main())
