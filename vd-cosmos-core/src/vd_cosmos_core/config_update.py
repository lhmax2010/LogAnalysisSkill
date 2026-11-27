"""Atomically update only approved submit keys and keep a private backup."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile

from .config import load_config
from .errors import FlowError


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


def sync_write(stream, data):
    stream.write(data)
    stream.flush()
    os.fsync(stream.fileno())


def update_submit(path, plan):
    """Run the planner under the config update lock, then apply its approved edits."""
    try:
        import fcntl
    except ImportError:
        raise FlowError(6, 'fcntl_unavailable') from None
    path = Path(path)
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
        text = original.decode('utf-8')
        submit = json.loads(text).get('submit', {})
        updates, changes = plan(config, submit)
        if not updates:
            return changes
        mode = stat.S_IMODE(path.stat().st_mode)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.submit-config-', delete=False) as output:
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
