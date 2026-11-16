"""Short browser-only temp roots, persisted for crash recovery beside the profile."""
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from .errors import FlowError
from .files import atomic_write, json_bytes, load_json

MARKER = 'browser-temp.json'
SOCKET_SUFFIX = '/.org.chromium.Chromium.XXXXXX/SingletonSocket'


def fits(path):
    return len(os.fsencode(str(path) + SOCKET_SUFFIX)) < 100


def private_directory(path):
    try:
        info = path.lstat()
        return (path.is_absolute() and path.resolve() == path and stat.S_ISDIR(info.st_mode)
                and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700)
    except OSError:
        return False


def create(profile):
    """Never reads inherited TMPDIR; only this child's environment uses the result."""
    marker = profile / MARKER
    if marker.exists() or marker.is_symlink():
        raise FlowError(6, 'browser_tmpdir_already_registered')
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    parent = Path(runtime) if runtime else None
    if parent is None or not private_directory(parent) or not fits(parent / 'vdc-XXXXXXXX'):
        parent = Path('/tmp')
    try:
        path = Path(tempfile.mkdtemp(prefix='vdc-', dir=str(parent)))
    except OSError:
        raise FlowError(6, 'browser_tmpdir_create_failed') from None
    try:
        path.chmod(0o700)
        if not fits(path):
            raise FlowError(6, 'browser_tmpdir_too_long')
        info = path.lstat()
        record = {'path': str(path), 'device': info.st_dev, 'inode': info.st_ino, 'uid': info.st_uid}
        atomic_write(profile, marker, json_bytes(record))
        return path
    except BaseException:
        shutil.rmtree(path)
        raise


def cleanup(profile):
    """Delete only the generated root with its recorded filesystem identity."""
    marker = profile / MARKER
    if not marker.exists() and not marker.is_symlink():
        return
    if marker.is_symlink():
        raise FlowError(6, 'browser_tmpdir_cleanup_unverified')
    try:
        record = load_json(marker); path = Path(record['path'])
        if (not path.is_absolute() or not re.fullmatch(r'vdc-[a-z0-9_]{8}', path.name)
                or record['uid'] != os.getuid()
                or path.parent != Path('/tmp') and not private_directory(path.parent)):
            raise ValueError()
        try:
            info = path.lstat()
        except FileNotFoundError:
            marker.unlink(); return
        if (not private_directory(path) or (info.st_dev, info.st_ino, info.st_uid)
                != (record['device'], record['inode'], record['uid'])):
            raise ValueError()
        shutil.rmtree(path)
        marker.unlink()
    except (OSError, KeyError, TypeError, ValueError):
        raise FlowError(6, 'browser_tmpdir_cleanup_unverified') from None
