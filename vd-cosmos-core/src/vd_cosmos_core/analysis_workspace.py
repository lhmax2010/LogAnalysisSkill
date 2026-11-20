"""ClineSR extension workspace setup and metadata-only canary inventory."""
from pathlib import Path
import os
from stat import S_ISDIR, S_ISREG

from .errors import FlowError
from .files import atomic_write, digest, json_bytes


def seal(path, directory):
    mode = path.lstat().st_mode
    if path.is_symlink() or (directory and not S_ISDIR(mode)) or (not directory and not S_ISREG(mode)):
        raise FlowError(4, 'analysis_workspace_skill_changed')
    if (mode & 0o777) != (0o555 if directory else 0o444):
        raise FlowError(4, 'analysis_workspace_skill_changed')


def inventory(root, marker):
    """Hash path, size, and mtime. Do not open any ordinary skill files."""
    if not root.is_dir() or root.is_symlink():
        return {'present': False, 'manifest_sha256': None}
    entries = []
    marker_seen = False
    for directory, subdirs, files in os.walk(root, followlinks=False):
        relative = Path(directory).relative_to(root)
        for name in sorted(subdirs + files):
            path = root / relative / name
            props = path.lstat()
            if path.is_symlink():
                continue
            entries.append(((relative / name).as_posix(), props.st_size, props.st_mtime_ns))
            marker_seen |= relative == Path('.') and name == marker and S_ISDIR(props.st_mode)
    return {'present': marker_seen, 'manifest_sha256': digest(json_bytes(sorted(entries)))}


def inspect_canaries(config):
    options = config.raw['analyzer'].get('cline_extension', {})
    audit = {'mode': '人工监督模式', 'isolation_verified': False, 'inventories': {}, 'config_digests': {}}
    for name in ('normal_skills', 'global_skills'):
        path = options.get(name)
        marker = options.get('canary')
        if path and marker and Path(marker).name == marker and marker not in {'.', '..'}:
            audit['inventories'][name] = inventory(config.source(path), marker)
    for scope, path in options.get('config_files', {}).items():
        target = config.source(path)
        if target.is_file() and not target.is_symlink():
            try:
                with target.open('rb') as stream:
                    data = stream.read(8 * 1024 * 1024 + 1)
                if len(data) <= 8 * 1024 * 1024:
                    audit['config_digests'][scope] = digest(data)
            except OSError:
                audit['config_digests'][scope] = None
    return audit


def validate_skill(config, build, expected):
    work = config.data_root / 'tasks' / build
    cline = work / '.cline'
    skills = cline / 'skills'
    folder = skills / 'vd-fix-analyze'
    path = folder / 'SKILL.md'
    if any(p.is_symlink() for p in (work, cline, skills, folder, path)) or path.resolve() != path:
        raise FlowError(4, 'analysis_workspace_skill_changed')
    try:
        seal(folder, True)
        seal(path, False)
        if {p.name for p in cline.iterdir()} != {'skills'} or {p.name for p in skills.iterdir()} != {folder.name}:
            raise FlowError(4, 'analysis_workspace_extra_skill')
        if {p.name for p in folder.iterdir()} != {'SKILL.md'} or digest(path.read_bytes()) != expected:
            raise FlowError(4, 'analysis_workspace_skill_changed')
    except OSError:
        raise FlowError(4, 'analysis_workspace_skill_changed') from None


def setup_workspace(config, build, raw):
    work = config.data_root / 'tasks' / build
    cline = work / '.cline'
    folder = cline / 'skills' / 'vd-fix-analyze'
    path = folder / 'SKILL.md'
    identity = digest(raw)
    if work.resolve() != work or cline.is_symlink():
        raise FlowError(4, 'analysis_workspace_skill_changed')
    if cline.exists():
        validate_skill(config, build, identity)
    else:
        atomic_write(config.data_root, path, raw)
        path.chmod(0o444)
        folder.chmod(0o555)
        validate_skill(config, build, identity)
    return {'path': str(path), 'sha256': identity, 'audit': inspect_canaries(config)}
