"""HLD 6.1: adjacent diagnostic triples, ownership checks and Clang display."""
import posixpath
import re
import unicodedata

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
PREFIX = r'^\[\s*\d+s\] '
HEAD = re.compile(r'(?P<path>[^\s:]+):(?P<line>\d+):(?:(?P<column>\d+):)?\s*(?P<level>fatal error|error|warning|note):')
MAPPED = ['.y', '.yy', '.ypp', '.l', '.ll', '.lex', '.re', '.rl', '.gperf']


def normalized_lines(log, pattern=PREFIX):
    return [re.sub(pattern, '', ANSI.sub('', line), count=1).rstrip('\r')
            for line in log.decode('utf-8', errors='surrogateescape').split('\n')]


def pair(source, caret, number=None):
    gutter = re.match(r'^\s*(\d+) \|( |$)', source)
    if gutter:
        bar = source.index('|')
        if (len(caret) > bar and caret[bar] == '|'
                and not caret[:bar].strip() and re.fullmatch(r'[\s~^]*\^[\s~^]*', caret[bar+1:])):
            if number is not None and int(gutter[1]) != number:
                return None
            tail = caret[bar+1:]
            return {'source_line': source[gutter.end():], 'caret': tail[1:] if tail.startswith(' ') else tail,
                    'gutter': True}
    if re.fullmatch(r'[\s~^]*\^[\s~^]*', caret):
        return {'source_line': source, 'caret': caret, 'gutter': False}
    return None


def diagnostics(log, options=None):
    options = options or {}
    lines = normalized_lines(log, options.get('log_line_prefix_regex', PREFIX))
    matches = [(i, HEAD.match(line)) for i, line in enumerate(lines)]
    triples, consumed = {}, set()
    for i, match in matches:
        if match and i+2 < len(lines):
            triple = pair(lines[i+1], lines[i+2], int(match['line']))
            if triple:
                triples[i] = triple
                consumed.update((i+1, i+2))
    previous, isolated, unknown, found = [], False, False, []
    for i, match in matches:
        text = lines[i]
        heads = list(HEAD.finditer(text))
        if i not in consumed and ((heads and (heads[0].start() != 0 or len(heads) > 1))
                or (not match and (re.match(r'^\d+(?::\d+)?: (?:fatal error|error|warning|note):', text)
                    or re.match(r'^\S+:\d+:', text) or re.search(r': (?:fatal error|error|warning|note): ', text)))):
            unknown = True
        if not match:
            continue
        triple = triples.get(i)
        d = {'path': match['path'], 'line': int(match['line']),
             'column': int(match['column']) if match['column'] else None,
             'level': match['level'], 'source_line': None, 'log_line': i+1,
             'candidate_paths': sorted(set(previous + [match['path']]))}
        if triple:
            d.update(triple)
            following = i+3
            while following < len(lines) and (lines[following].startswith('fix-it:')
                    or re.match(r'^\s*\|[ \t]*[^~^\s|]', lines[following])):
                following += 1
            orphan_pair = following+1 < len(lines) and pair(lines[following], lines[following+1]) is not None
            d['restricted'] = isolated or orphan_pair
            if (re.search(r'\[\s*\d+s\] ', lines[i+1]+lines[i+2])
                    or HEAD.search(lines[i+1]) or HEAD.search(lines[i+2])):
                d['unchecked_reason'] = '半行交错'
            elif unknown:
                d['unchecked_reason'] = '归属有歧义（孤立诊断行号未知）'
            elif posixpath.splitext(d['path'])[1] in options.get('line_mapped_exts', MAPPED):
                d['unchecked_reason'] = '位置经 #line 映射'
            elif d['restricted'] and not d['gutter']:
                d['unchecked_reason'] = '归属有歧义（无行号栏）'
        else:
            d['unchecked_reason'] = '交错 / note / 缺少紧邻三行'
            isolated = True
        previous.append(d['path'])
        found.append(d)
    groups = {}
    for d in found:
        if d['level'] in {'error', 'fatal error'} and d['source_line'] is not None:
            groups.setdefault((d['path'], d['line'], d['column']), []).append(d)
    for group in groups.values():
        if len({d['source_line'] for d in group}) > 1:
            for d in group:
                d['unchecked_reason'] = '交错（同位置不同源码）'
    # Warnings and notes contribute ownership candidates but aren't check targets.
    return [d for d in found if d['level'] in {'error', 'fatal error'}]


def display(raw, tabstop=8):
    text = raw.decode('utf-8', errors='surrogateescape')
    out, byte_column, screen_column, since_tab = [], 1, 1, 0
    positions = {1: 1}
    for char in text:
        length = len(char.encode('utf-8', errors='surrogateescape'))
        code = ord(char)
        if char == '\t':
            width = tabstop - since_tab % tabstop
            shown = ' ' * width
            since_tab = 0
        else:
            since_tab += length
            if 0xdc80 <= code <= 0xdcff:
                shown = '<%02X>' % (code - 0xdc00)
                width = 4
            elif not char.isprintable() and not unicodedata.combining(char):
                shown = '<U+%04X>' % code
                width = len(shown)
            else:
                shown = char
                width = 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {'W', 'F'} else 1
        out.append(shown)
        byte_column += length
        screen_column += width
        positions[byte_column] = screen_column
    return ''.join(out), positions


def clang_display(raw, tabstop=8):
    return display(raw, tabstop)[0]


def content_match(content, diagnostic, *, merged=False, transcoded=False, tabstop=8):
    source = diagnostic.get('source_line')
    if source is None or diagnostic.get('unchecked_reason'):
        return '未核对'
    if transcoded:
        return '无法核对'
    lines = content.split(b'\n')
    number = diagnostic['line']
    if not 0 < number <= len(lines):
        return '不一致'
    raw = lines[number-1].rstrip(b'\r')
    if merged and re.search(rb'\$(?:Id|Header|Revision|Date|DateTime|Author|File|Change)(?::[^$]*)?\$', raw):
        return '无法核对'
    shown = clang_display(raw, tabstop)
    if shown == source:
        return '源码行一致'
    if shown.rstrip(' \t') == source.rstrip(' \t') and shown.startswith(source):
        return '无法核对'
    return '不一致'


def compare_source(content, diagnostic, *, merged=False, transcoded=False, tabstop=8, candidates=None, max_candidates=50):
    result = content_match(content, diagnostic, merged=merged, transcoded=transcoded, tabstop=tabstop)
    if diagnostic.get('restricted') and not diagnostic.get('unchecked_reason'):
        paths = diagnostic['candidate_paths']
        if not candidates or len(paths) > max_candidates or any(p not in candidates for p in paths):
            return '未核对'
        results = []
        for path in paths:
            candidate, candidate_merged = candidates[path]
            if len(candidate.split(b'\n')) < diagnostic['line']:
                return '未核对'
            results.append((path, content_match(candidate, diagnostic, merged=candidate_merged, tabstop=tabstop)))
        if any(r in {'无法核对', '未核对'} for _, r in results):
            return '未核对'
        if all(r == '不一致' for _, r in results):
            return '不一致'
        if result != '源码行一致' or any(p != diagnostic.get('canonical_path', diagnostic['path']) and r != '不一致' for p, r in results):
            return '未核对'
    if result != '源码行一致' or diagnostic.get('column') is None or diagnostic.get('non_clang'):
        return result
    raw = content.split(b'\n')[diagnostic['line']-1].rstrip(b'\r')
    _, positions = display(raw, tabstop)
    wanted = positions.get(diagnostic['column'])
    actual = len(diagnostic.get('caret', '').split('^', 1)[0])+1
    return '源码行一致' if wanted == actual else '未核对'
