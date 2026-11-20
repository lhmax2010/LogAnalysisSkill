"""Strict analysis-result receiver. Its only journal operations are accept/reject."""
from collections import defaultdict
from difflib import SequenceMatcher
import json
import os
import re
import stat
import tempfile

from .analysis_tools import ROOT, run_tool
from .commands import command_context
from .errors import FlowError
from .files import atomic_write, digest, json_bytes
from .locks import OperationLock
from .state import EventStore, append_retry
from .task_package import checked_task, verify_text

SCHEMA = 'vd-cosmos/analysis-result/v1'
OUTCOMES = {'repair_candidate', 'diagnostic_only', 'disposition_proposal', 'cross_package_handoff'}
METHODS = {'code', 'clang_option', 'remove_option'}
PLAN_STATES = {'available', 'not_applicable', 'pending'}
HASH = re.compile(r'[0-9a-f]{64}')
CLANG_IF = '%if "%{?_toolchain}" == "clang"'
BAD_OPTION = re.compile(r"(?<![\w-])-Wno-error(?=[\s\"']|$)|%\{\s*\??toolchain_is\b", re.I)
INJECTION = re.compile(r'read the credential file|读取凭据文件', re.I)


def invalid(reason='analysis_schema_invalid'):
    raise FlowError(4, reason)


def obj(value, required, optional=()):
    if type(value) is not dict or set(required) - value.keys() or value.keys() - set(required) - set(optional):
        invalid()


def text(value, limit=2048, *, empty=False, pattern=None):
    if (not isinstance(value, str) or (not empty and not value.strip()) or len(value) > limit
            or '\x00' in value or any(0xD800 <= ord(c) <= 0xDFFF for c in value)
            or (pattern and not pattern.fullmatch(value))):
        invalid()


def array(value, maxlen):
    if not isinstance(value, list) or len(value) > maxlen:
        invalid()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            invalid('analysis_duplicate_json_key')
        result[key] = value
    return result


def reject_constant(value):
    invalid()


def read_result(config, task):
    directory = config.data_root / task['directory']
    result = directory / 'outputs/result.json'
    if result.parent.is_symlink() or result.parent.resolve() != result.parent or result.is_symlink():
        invalid('analysis_result_symlink')
    limit = config.raw['analyzer'].get('result_max_bytes', 262144)
    try:
        with os.fdopen(os.open(result, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                invalid('analysis_result_invalid_file')
            raw = stream.read(limit + 1)
            if len(raw) > limit:
                invalid('analysis_result_too_large')
    except OSError:
        raise FlowError(4, 'analysis_result_unavailable') from None
    try:
        if INJECTION.search(raw.decode('utf-8')):
            invalid('analysis_result_untrusted_instruction')
        verify_text(config, raw)
        parsed = json.loads(raw, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
        # Also detect literal text hidden behind JSON escapes.
        if INJECTION.search(json_bytes(parsed).decode('utf-8')):
            invalid('analysis_result_untrusted_instruction')
        return parsed
    except (UnicodeError, ValueError, RecursionError):
        invalid()


def validate(value, task, raw, evidence_ids):
    obj(value, ('schema_version', 'task_id', 'input_digest', 'attempt', 'facts',
                'outcome', 'proposals', 'provenance'), ('handoff',))
    if (value['schema_version'] != SCHEMA or type(value['attempt']) is not int
            or not isinstance(value['outcome'], str) or value['outcome'] not in OUTCOMES):
        invalid()
    if (value['task_id'], value['input_digest'], value['attempt']) != (
            task['task_id'], task['task_input_digest'], task['attempt']):
        invalid('analysis_attempt_binding_mismatch')
    facts = value['facts']
    array(facts, 512)
    for evidence in facts:
        text(evidence, 96)
    if len(set(facts)) != len(facts) or set(facts) - evidence_ids:
        invalid('analysis_evidence_unregistered')
    provenance = value['provenance']
    obj(provenance, ('analyst_type', 'analyst_version', 'model', 'task_sha256', 'prompt_sha256'))
    if provenance['analyst_type'] not in ('clinesr_extension', 'manual', 'fixture'):
        invalid()
    text(provenance['analyst_version'], 96)
    text(provenance['model'], 96)
    text(provenance['task_sha256'], 64, pattern=HASH)
    text(provenance['prompt_sha256'], 64, pattern=HASH)
    if provenance['task_sha256'] != digest(raw['TASK.md']):
        invalid('analysis_task_digest_mismatch')
    proposals = value['proposals']
    obj(proposals, ('root_cause', 'responsible', 'bug_assessment', 'alternatives',
                    'owner_pending', 'knowledge_refs'), ('recommended',))
    text(proposals['root_cause'])
    if proposals['responsible'] is not None and type(proposals['responsible']) is not bool:
        invalid()
    assessment = proposals['bug_assessment']
    obj(assessment, ('value', 'basis'))
    if type(assessment['value']) is not bool and assessment['value'] != 'unknown':
        invalid()
    text(assessment['basis'])
    text(proposals['owner_pending'], empty=True)
    array(proposals['knowledge_refs'], 0)
    alternatives = proposals['alternatives']
    array(alternatives, len(METHODS))
    methods = []
    for plan in alternatives:
        obj(plan, ('type', 'state', 'summary', 'advantages', 'risks'), ('reason',))
        text(plan['type'], 32)
        text(plan['state'], 32)
        if plan['type'] not in METHODS or plan['state'] not in PLAN_STATES or plan['type'] in methods:
            invalid()
        methods.append(plan['type'])
        for key in ('summary', 'advantages', 'risks'):
            text(plan[key], empty=plan['state'] != 'available')
        if plan['state'] != 'available' or 'reason' in plan:
            text(plan.get('reason'))
    if value['outcome'] == 'repair_candidate':
        if 'recommended' not in proposals or task['mode'] != '可分析':
            invalid('analysis_edits_in_diagnostic_only')
        if not {'code', 'clang_option'}.issubset(methods):
            invalid('analysis_missing_alternatives')
        plan = proposals['recommended']
        obj(plan, ('type', 'reason', 'edits'))
        if not isinstance(plan['type'], str) or plan['type'] not in METHODS:
            invalid()
        text(plan['reason'])
        array(plan['edits'], 100)
        if not plan['edits']:
            invalid()
    elif 'recommended' in proposals:
        invalid('analysis_edits_in_diagnostic_only')
    if value['outcome'] == 'cross_package_handoff':
        handoff = value.get('handoff')
        obj(handoff, ('package', 'reason'))
        obj(handoff['package'], ('name', 'arch', 'path'))
        for field in handoff['package'].values():
            text(field, 512)
        text(handoff['reason'])
        if handoff['package'] == task['package']:
            invalid()
    elif 'handoff' in value:
        invalid()


def check_r08(before, after):
    intervals = SequenceMatcher(None, before.splitlines(), after.splitlines(), autojunk=False)
    new_lines = after.splitlines()
    changed = {i for kind, _, _, start, end in intervals.get_opcodes()
               if kind in ('insert', 'replace') for i in range(start, end)}
    conditions = []
    for index, line in enumerate(new_lines):
        clean = line.strip()
        if re.match(r'^%if(?:\s|arch\b|narch\b|os\b|nos\b)', clean):
            conditions.append(clean == CLANG_IF)
            if index in changed and 'clang' in clean.lower() and not conditions[-1]:
                invalid('analysis_r08')
        elif re.match(r'^%el(?:se|if)\b', clean) and conditions:
            conditions[-1] = False
        elif re.match(r'^%endif\b', clean) and conditions:
            conditions.pop()
        if index in changed and (BAD_OPTION.search(line) or
                                 ('-Wno-error=' in line and not any(conditions))):
            invalid('analysis_r08')


def edits_spec(plan, task, inputs):
    if plan is None:
        return None
    groups = defaultdict(list)
    path_index = {value['path']: name for name, value in task['editable_sources'].items()}
    for edit in plan['edits']:
        obj(edit, ('path', 'old', 'new'))
        text(edit['path'], 512)
        text(edit['old'], 32768, empty=False)
        text(edit['new'], 32768, empty=True)
        path = path_index.get(edit['path'])
        if not path or not task['editable_sources'][path]['editable']:
            invalid('analysis_edit_source_not_editable')
        try:
            original = inputs[path].decode('utf-8')
        except UnicodeError:
            invalid('analysis_edit_source_not_utf8')
        old, new = edit['old'], edit['new']
        start = original.find(old)
        if start < 0 or original.find(old, start + 1) >= 0 or old == new:
            invalid('analysis_edit_original_mismatch')
        groups[path].append((start, start + len(old), old, new))
    edits = []
    for path, changes in sorted(groups.items()):
        source = inputs[path].decode('utf-8')
        cursor = 0
        pieces = []
        for start, end, old, new in sorted(changes):
            if start < cursor:
                invalid('analysis_edit_overlap')
            pieces.extend((source[cursor:start], new))
            edits.append({'file': path, 'operation': 'replace', 'old': old, 'new': new})
            cursor = end
        pieces.append(source[cursor:])
        final = ''.join(pieces)
        if task['editable_sources'][path]['path'].endswith('.spec'):
            check_r08(source, final)
    return {'schema_version': 'gbs_patch_suggest/edit-spec/v1', 'edits': edits}


def check_r28(plan, confirmed):
    if not plan or not confirmed:
        return
    if plan['type'] != 'code' or not any('PLEASE CHECK' in change['new'] for change in plan['edits']):
        invalid('analysis_r28')


def latest_final_digest(config, store, build, package):
    from .task_package import checked_file
    for event in reversed(store.events(build, kinds=['observation_recorded', 'workflow_result'])):
        payload = event['payload']
        if (event['command'] != 'fetch.logs' and payload.get('step') != 'logs'
                or payload.get('exit_code') or not payload.get('artifact')):
            continue
        data = json.loads(checked_file(config, payload['artifact']))
        for item in data.get('logs', []):
            if item.get('key') == package and item.get('final'):
                checked_file(config, item)
                return item['sha256']
    return None


def registered_task(store, build, task_id, attempt):
    for event in reversed(store.events(build, kinds=['analysis_prepared'])):
        task = event['payload']
        if (task['task_id'], task['attempt']) == (task_id, attempt):
            return task
    raise FlowError(4, 'analysis_attempt_unregistered')


def processing_state(config, store, task):
    matching = [e['payload'] for e in store.events(task['build'], kinds=['analysis_prepared'])
                if e['payload']['package'] == task['package']]
    if matching and matching[-1]['task_input_digest'] != task['task_input_digest']:
        return '输入已过期'
    current = latest_final_digest(config, store, task['build'], task['package'])
    if current != task['final_log']['sha256']:
        return '输入已过期'
    if matching and matching[-1]['attempt'] != task['attempt']:
        return '旧尝试'
    return '有效'


def record(store, kind, task, **payload):
    summary = {field: task[field] for field in (
        'build', 'package', 'task_id', 'attempt', 'task_input_digest')}
    return append_retry(store, command_context('analyze.accept'), kind, {**summary, **payload},
                        store.head(), retry=True)


def has_result(store, task):
    return any((event['payload']['task_id'], event['payload']['attempt']) ==
               (task['task_id'], task['attempt'])
               for event in store.events(task['build'], kinds=['analysis_received']))


def accept_result(config, build, task_id, attempt):
    if not HASH.fullmatch(build) or not HASH.fullmatch(task_id) or type(attempt) is not int or attempt < 1:
        raise FlowError(2, 'invalid_analysis_task')
    with OperationLock(config.data_root, 'round', build), EventStore(config.data_root) as store:
        task = registered_task(store, build, task_id, attempt)
        try:
            if has_result(store, task):
                invalid('analysis_result_already_received')
            if processing_state(config, store, task) != '有效':
                invalid('analysis_input_expired')
            raw, refs = checked_task(config, task)
            result = read_result(config, task)
            validate(result, task, raw, refs)
            plan = result['proposals'].get('recommended')
            decisions = store.events(build, kinds=['confirmed'])
            confirmed = any(e['command'] == 'confirm-bug' and e['payload'].get('real') is True
                            and e['payload'].get('task_input_digest') == task['task_input_digest']
                            and e['payload'].get('package') == task['package'] for e in decisions)
            check_r28(plan, confirmed)
            spec = edits_spec(plan, task, raw)
            output = f"rounds/{build}/analysis/{task_id}/attempt-{attempt}"
            if spec:
                checked = atomic_write(config.data_root, f'{output}/edit-spec.json', json_bytes(spec))
                folder = config.output(output)
                # The existing formatter copies source modes before editing a
                # scratch copy. Give it private writable copies of verified bytes.
                with tempfile.TemporaryDirectory(prefix='format-', dir=folder) as temporary:
                    for name in {edit['file'] for edit in spec['edits']}:
                        atomic_write(temporary, name, raw[name])
                    run_tool(ROOT / 'tizen-gbs-patch-suggest/scripts/run_patch_suggest.py',
                             ['format-patch', '--src-root', temporary, '--edit-spec', checked['path'],
                              '--output', folder / 'candidate.patch', '--check'],
                             folder, 'analysis_patch_format_failed')
            artifact = atomic_write(config.data_root, f'{output}/received.json', json_bytes(result))
            eid = record(store, 'analysis_received', task, validated=True, artifact=artifact,
                         outcome=result['outcome'], fixture=result['provenance']['analyst_type'] == 'fixture')
            return {'task_id': task_id, 'attempt': attempt, 'outcome': result['outcome'],
                    'artifact': artifact, 'last_event_id': eid}
        except FlowError as error:
            record(store, 'analysis_rejected', task, reason=error.reason)
            raise
        except (OSError, KeyError, ValueError, TypeError, RecursionError):
            record(store, 'analysis_rejected', task, reason='analysis_receiver_invalid_input')
            raise FlowError(4, 'analysis_receiver_invalid_input') from None
