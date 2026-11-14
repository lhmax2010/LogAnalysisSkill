"""Shared header-based variable tables and immutable, credential-checked first reads."""
from urllib.parse import urlsplit

from .errors import FlowError
from .export import check_content
from .files import atomic_write, digest, json_bytes, load_json
from .locks import OperationLock
from .report import Document, Node, cells, normalize


def unrecognized():
    return FlowError(5, 'variables_page_unrecognized',
                     todo={'reason': 'variables_page_unrecognized', 'message': '变量页无法识别'})


def own_rows(table):
    for child in table.children:
        if not isinstance(child, Node) or child.tag == 'table':
            continue
        if child.tag == 'tr':
            yield child
        else:
            yield from own_rows(child)


def value_text(node):
    # A pre contains the value verbatim; do not invent a trailing newline for it.
    value = ''.join(value_text(c) if isinstance(c, Node) else c for c in node.children)
    return value + ('\n' if node.tag in {'br', 'p', 'div', 'li'} else '')


def parse(data, names):
    """Only selected Name cells and their Value cells leave the parser.

    Explicitly supports Name|Value and Name|Display Name|Value, in any order.
    A table wrapper, extra/duplicate headers, row spans and malformed widths
    cannot silently select a different column. Display Name is never a value.
    """
    try:
        doc = Document(data.decode('utf-8'))
    except (UnicodeError, ValueError, RecursionError):
        raise unrecognized() from None
    candidates = []
    for table in (n for n in doc.nodes if n.tag == 'table'):
        rows = list(own_rows(table))
        for i, row in enumerate(rows):
            cs = cells(row)
            # Identify headers by their text, not by a fixed cell position.
            labels = [normalize(c.text()).casefold() for c in cs]
            if 'name' not in labels or 'value' not in labels:
                continue
            if (set(labels) not in ({'name', 'value'}, {'name', 'display name', 'value'})
                    or len(set(labels)) != len(labels)
                    or any(c.attrs.get('colspan', '1') != '1' or c.attrs.get('rowspan', '1') != '1' for c in cs)):
                raise unrecognized()
            candidates.append((rows[i + 1:], labels))
    if len(candidates) != 1:
        raise unrecognized()
    rows, labels = candidates[0]
    name_index, value_index = labels.index('name'), labels.index('value')
    result = {}
    for row in rows:
        cs = cells(row)
        if not cs:
            continue
        if len(cs) != len(labels) or any(c.attrs.get('colspan', '1') != '1' or c.attrs.get('rowspan', '1') != '1' for c in cs):
            raise unrecognized()
        name = normalize(cs[name_index].text())
        if name not in names:
            continue
        if name in result:
            raise FlowError(5, 'variable_duplicate', todo={'reason': 'variable_duplicate', 'message': '变量页重复变量'})
        result[name] = {'value': value_text(cs[value_index]), 'cells': len(cs) - name_index - 1,
                        'value_column': value_index, 'table_columns': len(labels)}
    return result


def remember(config, build_id, page_url, values, names):
    """Freeze each selected value/absence at its first read, across all callers.

    Only safe decoded values are stored, never HTML or unselected cells. The
    per-build lock protects disk reads/writes only, never the network request.
    A mismatch writes a fixed todo with digests, preserves the original and stops.
    """
    for value in values.values():
        if not check_content(value.encode(), config)['allowed']:
            raise FlowError(4, 'variable_credential_blocked')
    scope = {'host': urlsplit(page_url).netloc.lower(), 'build_id': str(build_id)}
    key = digest(json_bytes(scope))
    folder = 'inputs/variable-first-read/' + key
    with OperationLock(config.data_root, 'variables', key, wait_s=config.raw['poll']['lock_wait_s']):
        pending = []
        for name in sorted(names):
            value = values.get(name)
            record = {'scope': scope, 'name': name, 'present': name in values, 'value': value,
                      'sha256': digest(value.encode()) if value is not None else None}
            path = config.output(folder + '/' + digest(name.encode()) + '.json')
            if path.exists():
                old = load_json(path)
                if (old.get('name') != name or old.get('scope') != scope
                        or old.get('sha256') != (digest(old['value'].encode()) if old.get('value') is not None else None)):
                    raise FlowError(4, 'immutable_variable_corrupt')
                if (old['present'], old['sha256']) != (record['present'], record['sha256']):
                    todo = {'reason': 'variable_page_changed', 'message': '变量页已变化',
                            'build_id': str(build_id), 'variable': name,
                            'stored_sha256': old['sha256'], 'observed_sha256': record['sha256']}
                    issue = atomic_write(config.data_root, folder + '/issues/' + digest(json_bytes(todo)) + '.json', json_bytes(todo))
                    raise FlowError(3, 'variable_page_changed', todo=todo, issue=issue)
            else:
                pending.append((path, record))
        for path, record in pending:
            atomic_write(config.data_root, path, json_bytes(record))
    return values
