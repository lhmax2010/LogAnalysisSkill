# Stage16 P2 submission identity

日期: 2026-10-08。状态: **STOPPED_PENDING_RULING**。
设计入库完成: `9b7754e`。生产代码、测试与既有检查器均未修改。
停止项 P2-01 见第3节;真实 hook 为 PENDING,不以测试替身冒充。

## 1. 权威与入库

- 权威: `../../design.md` v1.5.19-FROZEN,§3.4/§4.2/§7 Phase 2。
- 批准来源: FatTank 批准 change_47;本轮提示词授权原字节移动变更记录。
- design.md SHA-256: `6623f9cae95dbc07bdc8a4408808813eb2b9a54057df82c51b8b9d0cdce11b16`。
- change_47.md SHA-256: `ca493892ab2aa2149af3fb115c64adef90ae19094f1431eaee455a9d7c8d9336`。
- 原 `docs/clang-fix-campaign/change_47.md` 已原字节移动至
  `docs/clang-fix-campaign/design_changes/change_47.md`,移动前后hash一致。
- 入库提交仅含这两份设计文件与 INDEX,不含实现代码。
- 原有无关改动(.gitignore及其它文档删除/未跟踪草稿)未处理、未提交。

## 2. 入库前实测

执行目录为仓库根,解释器为 `.venv/bin/python`。

### 2.1 设计检查

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
== check_design_doc: docs/clang-fix-campaign/design.md ==
-- OK: 0 problem --
exit=0
```

### 2.2 SQLite DDL 与固定向量

以下为实际执行命令。DDL直接从权威设计稿提取,不是手工重写副本。

```sh
.venv/bin/python - <<'PY'
import re
import sqlite3
from pathlib import Path
from tizen_ci_shared.state.keys import build_submission_key
text = Path('docs/clang-fix-campaign/design.md').read_text()
m = re.search(r'CREATE TABLE IF NOT EXISTS campaign_change_ids \(.*?\n\);', text, re.S)
assert m
conn = sqlite3.connect(':memory:')
conn.executescript(m.group())
sql = 'INSERT INTO campaign_change_ids VALUES (?, ?, ?, ?, ?)'
valid = ['a'*64, 'I'+'b'*40, 'commit_msg_hook', 'c'*64, '2026-10-08T00:00:00+00:00']
conn.execute(sql, valid)
print('DDL execute: PASS; valid row: ACCEPTED')
conn.rollback()
cases = {
 'submission_key': (0, [None, '', 'a'*63, 'a'*65, 'A'*64, 'g'*64]),
 'change_id': (1, [None, '', 'i'+'b'*40, 'I'+'B'*40, 'I'+'g'*40, 'I'+'b'*39, 'I'+'b'*41]),
 'source': (2, [None, '', 'computed_hash']),
 'hook_sha256': (3, [None, '', 'c'*63, 'c'*65, 'C'*64, 'g'*64]),
}
n = 0
for column, (index, invalids) in cases.items():
 for invalid in invalids:
  row = valid.copy()
  row[index] = invalid
  try:
   conn.execute(sql, row)
  except sqlite3.IntegrityError as e:
   print(f'{column}={invalid!r}: REJECTED ({e})')
   n += 1
  else:
   raise AssertionError(f'accepted {column}={invalid!r}')
  conn.rollback()
print(f'invalid rows rejected: {n}/{n}')
key = 'quickbuild/1118258/platform/core/multimedia/inference-engine-interface/tizen/standard-armv7l/inference-engine-interface/' + 'a'*40
result = build_submission_key(failure_key=key, verified_tree_sha='c'*40)
assert re.fullmatch('[0-9a-f]{64}', result)
print('fixed failure_key:', key)
print('fixed verified_tree_sha:', 'c'*40)
print('build_submission_key:', result)
print('64 lowercase hex: PASS')
PY
```

原始输出摘录(退出码0):

```text
DDL execute: PASS; valid row: ACCEPTED
submission_key=None: REJECTED (NOT NULL constraint failed: campaign_change_ids.submission_key)
source='computed_hash': REJECTED (CHECK constraint failed: source = 'commit_msg_hook')
invalid rows rejected: 22/22
fixed failure_key: quickbuild/1118258/platform/core/multimedia/inference-engine-interface/tizen/standard-armv7l/inference-engine-interface/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
fixed verified_tree_sha: cccccccccccccccccccccccccccccccccccccccc
build_submission_key: bfbe817287b94c8a6fa38f8610f41a56347befa7b157b214fd62aacf9235a104
64 lowercase hex: PASS
```

非法值覆盖:submission_key 6例、change_id 7例、source 3例、hook_sha256 6例。
NULL由NOT NULL拒绝,其它非法长度/字符/固定source值由CHECK拒绝。

## 3. P2-01: Phase 2 DoD 的后续阶段依赖

状态: **OPEN,等待设计方裁决**。不是生产代码缺陷,不修改已批准设计。

| 原文位置(design.md) | 当前要求 | 与阶段范围的冲突 |
|---|---|---|
| :2729-2731 | review-submit端到端:删缓存行后拒绝、不得重新生成、不得push | review-submit在:3026的Phase 5R,依赖P5/P4.5/P5Q;仓内尚无该入口 |
| :2743-2748 | sandbox重推删行后拒绝且不push;derive后的最终commit message不含辅助行且恰含一个Change-Id | sandbox-submit在:3007的Phase 5;derive_commit在:2765的Phase 4,两者均依赖P2 |
| :2684-2689 | DAG为P2→P4→P5→P5Q→P5R | 若上述端到端项必须在P2全部完成,会反向依赖尚未实施的后续阶段 |

实测定位命令:

```text
$ git ls-files '*derive*' '*submission_identity*' '*sandbox*' '*review_submit*' '*commit-msg*'
(空输出)
exit=0
$ rg -n 'add_parser\(|def main|sandbox|review|derive' tizen-ci-triage/scripts/ci_triage/cli.py
177:def main(
exit=0
```

另外检查了 `tizen-ci-triage/scripts/ci_triage` 与 `tests/unit` 中的
review-submit/sandbox-submit/derive实现:只有campaign_state现存的身份字段,
没有这些CLI或derive实现。既有gerrit-submit skill是dry-run,不能代替P5/P5R。

候选处置(待批准,未自行执行):

1. P2先完成key、hook生成、缓存API与组件级全量验证;上述端到端条目具名绑定
   P4/P5/P5R实施后补做,明确P2当期的签批条件。不得把模拟调用或API单测称作端到端。
2. 若坚持P2完成全部端到端条目,须显式扩大范围并调整DAG;这会引入提交/推送流程,
   涉及安全边界,不能作为无行为影响的轻量实现补缺。

本轮停在实现前,未选择方案,未创建假入口或补写推送代码。

## 4. DoD 对照与待恢复计划

| Phase 2 DoD | 本轮状态 / 下一步 |
|---|---|
| 两个JSON key成分/段数与碰撞反例 | NOT_RUN,待实现 |
| compute_submission_key委托与字节一致性 | 入库前既有函数固定向量PASS;新委托尚未实现 |
| 缓存幂等、并发、UNIQUE冲突、审计字段及hook升级复用 | NOT_RUN,待新增API与表 |
| generate=None只读与删行拒绝 | NOT_RUN;review-submit端到端受P2-01阻塞 |
| hook失败形态、CRLF、副本执行、仓库隔离与清理 | NOT_RUN,待实现与替身测试 |
| campaign_change_ids CHECK | 设计DDL内存实跑PASS,实现ensure_schema尚未变更 |
| previous的n_a边界(RD-1) | NOT_RUN,后续复用现有状态/repair测试固化,不改既有行为 |
| DERIVE生成许可与事务内重查 | NOT_RUN;sandbox重推端到端受P2-01阻塞 |
| X-Campaign-Submission-Key | NOT_RUN;最终derive message端到端受P2-01阻塞 |
| 身份行拒绝、普通Link正例 | NOT_RUN |
| 环境与git配置隔离 | NOT_RUN |
| 准备失败、删除失败只WARN | NOT_RUN |
| 真实hook冒烟与HEAD变体 | PENDING:未发现登记配置,需FatTank提供路径与sha256;变体测试待实现 |

真实hook检索:在仓内yaml/yml/json/toml中查找
`gerrit_commit_msg_hook|commit-msg`,排除历史release与末批a0-evidence,
`rg`退出1、无命中。此结果只说明当前检索范围无登记,不推断外部环境没有hook。

待P2-01裁决后,按§4.2实现,只新增campaign_change_ids表和新API,
不ALTER既有表、不改既有API行为。真实hook仍按任务要求独立挂PENDING,
不以其缺失阻止其余已获准工作。

本轮未运行全仓回归/mypy/ruff/lint-imports/全部设计门禁/远端CI验收;
只有第2节入库前验证已实跑,不得以历史基线数字充作P2结果。
