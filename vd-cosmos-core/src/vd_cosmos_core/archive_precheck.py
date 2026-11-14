"""Repository-only, designer-approved archive exceptions. Never used at runtime."""
from collections import Counter
from pathlib import Path, PurePosixPath
import re

from .errors import FlowError
from .export import check_content
from .files import digest, load_json

ARCHIVE_PREFIX = 'docs/enhance/evidence/scripts/'
REGISTRY = 'docs/enhance/evidence/archive-exemptions.json'


def entries(root):
    path = root / REGISTRY
    if not path.exists():
        return []
    if path.is_symlink() or path.resolve() != path:
        raise FlowError(4, 'archive_registry_invalid')
    try:
        data = load_json(path)
        if data.get('schema_version') != 1 or not isinstance(data.get('entries'), list):
            raise ValueError()
        seen = set()
        for entry in data['entries']:
            if set(entry) != {'path', 'sha256', 'line', 'matched_text', 'credential_rule',
                              'reason', 'date', 'approved_by'}:
                raise ValueError()
            relative = PurePosixPath(entry['path'])
            if (not entry['path'].startswith(ARCHIVE_PREFIX)
                    or str(relative) != entry['path'] or '..' in relative.parts
                    or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])
                    or type(entry['line']) is not int or entry['line'] < 1
                    or not entry['matched_text'] or '\n' in entry['matched_text']
                    or not all(isinstance(entry[k], str) and entry[k]
                               for k in ('credential_rule', 'reason', 'date', 'approved_by'))):
                raise ValueError()
            identity = (entry['path'], entry['sha256'], entry['line'],
                        entry['matched_text'], entry['credential_rule'])
            if identity in seen:
                raise ValueError()
            seen.add(identity)
        return data['entries']
    except (FlowError, KeyError, TypeError, ValueError, AttributeError):
        raise FlowError(4, 'archive_registry_invalid') from None


def check_file(path, config, *, repo_root=None):
    """Apply only exact hash/path/line/text/rule registrations to archive files.

    File bytes are read once for both hashing and credential scanning. Archive
    files cannot use fixture inline exemptions; a registered hash mismatch is a
    blocking error even if the edit removes the original regex match entirely.
    """
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[3]
    requested = Path(path).absolute()
    try:
        relative = requested.relative_to(root).as_posix()
    except ValueError:
        relative = None
    archive = bool(relative and relative.startswith(ARCHIVE_PREFIX))
    content = requested.read_bytes()
    result = check_content(content, config, test_exemptions=not archive)
    if not archive:
        return result
    result['archive_exemptions'] = []
    if requested.resolve() != requested:
        return dict(result, allowed=False, archive_error='archive_path_not_canonical')
    registered = [e for e in entries(root) if e['path'] == relative]
    if not registered:
        return result
    sha = digest(content)
    registered = [e for e in registered if e['sha256'] == sha]
    if not registered:
        return dict(result, allowed=False, archive_error='archive_hash_mismatch')
    text = content.decode('utf-8')
    approved = Counter()
    for index, rule in enumerate(config.raw['prepush']['credential_patterns']):
        for match in re.finditer(rule, text, re.I | re.M):
            line = text.count('\n', 0, match.start()) + 1
            if any(e['credential_rule'] == rule and e['line'] == line
                   and e['matched_text'] == match.group() for e in registered):
                approved[index, line] += 1
                # Do not echo the matched text: registries never license logging secrets.
                result['archive_exemptions'].append(
                    {'path': relative, 'sha256': sha, 'line': line, 'pattern_index': index})
    remaining = []
    for hit in result['credential_hits']:
        key = hit['pattern_index'], hit['line']
        if approved[key]:
            approved[key] -= 1
        else:
            remaining.append(hit)
    result['credential_hits'] = remaining
    result['allowed'] = not remaining
    return result
