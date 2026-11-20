"""Render the §9.8 review table from journaled facts and accepted AI proposals."""
from html import escape

from .files import atomic_write
from .task_package import checked_file
import json


def cell(value):
    clean = ''.join(' ' if ord(c) < 32 else c for c in str(value))[:512]
    return escape(clean).replace('|', '&#124;').replace('[', '&#91;').replace(']', '&#93;')


def build_comparison(config, store, build, current):
    # Read only the higher-level projection furnished by the receiver, which
    # also verifies the latest final-log digest for each accepted task.
    from .analysis_result import processing_state, registered_task
    lines = ['# 方案对比表', '', '推荐、根因和备选项为分析主张。批准、实际 CL、验证由后续阶段登记。', '',
             '| 包 | 首条诊断 | 根因类别 | 真 bug 定性 | 推荐方案 | 批准方案 | 实际 CL 与内容摘要 | 验证状态 | 改代码 | 只对 Clang 生效 | 删参数 | 备选完整度 | owner 待决项 |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    events = [e['payload'] for e in store.events(build, kinds=['analysis_received'])]
    events.append(current)
    latest = {tuple(r['package'][k] for k in ('name', 'arch', 'path')): r for r in events if not r['fixture']}
    for pkg, row in sorted(latest.items()):
        task = registered_task(store, build, row['task_id'], row['attempt'])
        state = processing_state(config, store, task)
        result = json.loads(checked_file(config, row['artifact']))
        claims = result['proposals']
        plans = {item['type']: item for item in claims['alternatives']}
        locations = task.get('diagnosis', {}).get('locations', [])
        diagnostic = f"{locations[0]['flag']} @ {locations[0]['path']}:{locations[0]['line']}" if locations else '无标志'
        def plan(name):
            if name == 'clang_option' and row.get('confirmed_bug'):
                return '禁用（R28）'
            item = plans.get(name)
            if not item:
                return '未给出'
            if item['state'] == 'available':
                return f"未验证：{item['summary']}"
            label = '待补' if item['state'] == 'pending' else '不适用'
            return f"{label}：{item['reason']}"
        review = row.get('review_state') or '无工具定性'
        values = (f'{pkg[0]} / {pkg[1]}', diagnostic, claims['root_cause'], review,
                  claims.get('recommended', {}).get('type', '无'), '未批准', '无',
                  state if state != '有效' else '未验证', plan('code'), plan('clang_option'),
                  plan('remove_option'), '待补' if any(p['state'] == 'pending' for p in plans.values()) else '已列出',
                  claims['owner_pending'])
        lines.append('| ' + ' | '.join(map(cell, values)) + ' |')
    return atomic_write(config.data_root, f'rounds/{build}/reports/analysis-comparison.md',
                        ('\n'.join(lines)+'\n').encode())
