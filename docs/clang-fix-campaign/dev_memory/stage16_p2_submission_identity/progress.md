# Stage16 P2 submission identity

日期: 2026-10-08。状态: **CLOSED**。
设计入库完成: `9b7754e`。P2-01已裁决:本阶段完成组件级验证。
第2至4节保留上一轮停止时记录;第6/9节的hook缺失为历史记录。
真实hook与HEAD变体已补验。第8/10节保留候审记录;本轮评审处置与签批见第11节。

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

状态: **CLOSED_BY_RULING**。2026-10-08设计方采纳候选1,具体移交见第5节。
下文保留停止时的原始诊断,不是当前阻塞。

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

## 5. P2-01裁决与移交清单

来源:2026-10-08用户传达设计方轻量裁决,不修改设计稿。
P2完成组件级验证,以下三项端到端检查不在P2实施:

| 移交检查 | 目标阶段 | 关门要求 |
|---|---|---|
| derive后最终commit message不含X-Campaign-Submission-Key且恰好一个Change-Id trailer | P4 | 真实derive实现后验证最终commit消息 |
| sandbox重推(已有DERIVE)删缓存行后拒绝且不push | P5 | sandbox-submit端到端,不得以API测试代替 |
| review-submit删缓存行后拒绝、不重新生成、不push | P5R | review-submit端到端,不得以API测试代替 |

本阶段保留:已有DERIVE而无缓存,无论generate=None或提供生成函数,
均StateInconsistent、generate调用0次且不写库;hook生成器仅返回Change-Id,
不修改传入message。

## 6. 真实hook登记与实施边界(此前缺失的历史记录)

FatTank指定路径:`/home/linhao/gerrit-hook/commit-msg`。

```text
$ sha256sum /home/linhao/gerrit-hook/commit-msg
sha256sum: /home/linhao/gerrit-hook/commit-msg: No such file or directory
exit=1
```

状态:PENDING。不存在的文件不编造sha256,不下载替代hook、不将替身当真实冒烟。
按裁决继续其余组件实现。基线HEAD=`f9dedce23459e9e01b9cd592df9eb3703da75ef4`,
独立工作树`/tmp/p2-baseline-f9dedce`,避免主工作树无关草稿影响ruff/checker。
生产只新增submission_identity和campaign_change_ids/get_or_create_change_id;
不修改既有表/API行为,不实现推送入口。`ci_triage.state.keys`为历史路径,
实际委托P4.9后的权威`tizen_ci_shared.state.keys.build_submission_key`,公式不变。

## 7. 实施与本地验收

生产新增`ci_triage/submission_identity.py`的两个规范JSON key、既有submission_key
委托与隔离hook生成器;`campaign_state.py`仅加表及get_or_create_change_id和两个
内部查询helper。所有旧函数/类(除docstring)AST一致,旧schema对象逐项一致。
不提供缓存update/delete API,不实现sandbox/review push,不修改冻结设计。

测试新增`test_submission_identity.py`、`test_campaign_change_ids.py`;
既有schema精确表集合仅增新表一项;`test_campaign_repair_step.py`增加RD-1两例,
其它既有测试不删除、不弱化断言。

### 7.1 命令与实跑结果

证据目录`evidence/`。baseline为`/tmp/p2-baseline-f9dedce`,current为
`/tmp/p2-validation-f9dedce`(基线HEAD加本次六个生产/测试文件的精确git patch)。
两者均为干净tree,不带主工作树无关草稿。以仓库`.venv/bin/python`执行,
PYTHONPATH/MYPYPATH仅由各自工作树`*/scripts`排序派生,PATH前置同venv的bin。
完整argv、cwd、路径列表、exit与输出sha256逐条落在
`evidence/{baseline,current}/commands.json`;未继承历史结果数字。

| 实跑命令(解释器/命令均取.venv/bin) | baseline | current | 原始输出 |
|---|---|---|---|
| `python -m pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80 --junitxml=…` | exit0,1349 passed/1 skipped | exit0,1410 passed/1 skipped | 两侧`pytest.log`/`pytest.xml` |
| `python -m mypy` | exit0 | exit0,104 source files | 两侧`mypy.log` |
| `python -m ruff check .` | exit0 | exit0 | 两侧`ruff.log` |
| `lint-imports` | exit0 | exit0 | 两侧`lint-imports.log` |
| 90条既有设计checker与控制(沿用C13R命令全集,解释器替换为当前venv) | 3项既有不符 | 相同3项,exit无变化 | 两侧`commands.json`及逐条同名`.log` |

定向命令:

```sh
.venv/bin/python -m pytest tests/unit/test_submission_identity.py tests/unit/test_campaign_change_ids.py tests/unit/test_campaign_state.py tests/unit/test_campaign_repair_step.py -v
```

原始输出摘录:

```text
============================= 135 passed in 9.05s ==============================
exit=0
```

完整命令与输出:`evidence/targeted.command.json` / `targeted.log`。
全量与门禁原始输出摘录:

```text
======================= 1410 passed, 1 skipped in 31.36s =======================
Success: no issues found in 104 source files
All checks passed!
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
```

### 7.2 基线不缩小与遗留

`evidence/comparison.json`从本轮两次JUnit结果按(classname,name)逐项比较:
1350个既有用例全部仍在且结果不变,新增61个通过用例,无新skip。
94条命令(全仓/类型/lint/import+90checker)exit_changes=[]。
以下三条沿用既有遗留状态,不是P2新增失败,没有放宽判据或修改检查器:

| 命令 | 预期exit | baseline/current exit |
|---|---|---|
| `check_design_doc.py --self-test` | 0 | 1/1 |
| `symbol_audit.py --negative-fixture duplicate-spec-root-mismatch` | 1 | 0/0 |
| `symbol_audit.py --key-fixture twin-both-binary-key` | 0 | 1/1 |

背景见stage14 `carried-over-issues.md`;本轮只核对基线不增加失败,不销去历史问题。

### 7.3 轻量实现说明与取证修正

- 原设计中的`ci_triage.state.keys`已在P4.9迁移,委托真实权威路径,
  无新key公式;固定向量及委托实测均已覆盖。
- 临时hook目录固定在Linux `/tmp`,不接受可能指向业务worktree的TMPDIR;
  PATH/LANG按冻结白名单传入,其余git/HOME相关变量显式隔离。
- 准备git命令与hook共用隔离运行helper(新进程组、30秒上限),
  准备失败仍归CHANGE_ID_HOOK_FAILED,不新增业务入口或推送能力。
- 首次范围核对脚本误把“只新增一张表”等同于sqlite_master只多一个对象,
  触发AssertionError(exit1);PRIMARY KEY和UNIQUE自动产生两个索引。
  更正取证脚本为“一张表及其两个隐式约束索引”,生产代码未因此改动。
  复跑exit0:93个旧函数/类AST相同、21个旧schema对象相同,证据
  `evidence/production-scope.json`。此为取证脚本修正,非放宽生产门禁。

## 8. Phase 2 DoD 逐条对照(当前)

下列用例简称均可在`tests/unit/`对应文件与`evidence/targeted.log`定位。

| DoD | 状态 | 用例/证据 |
|---|---|---|
| 两key段数/成分、JSON碰撞反例、Unicode | PASS | `test_keys_fixed_vectors_and_dimensions`; `test_keys_json_encoding_avoids_slash_collision_and_keeps_unicode` |
| 委托既有build_submission_key、固定向量字节一致 | PASS | `test_compute_key_delegates`; 固定向量用例 |
| 缓存幂等、跨build复用、hook升级不比对、审计字段 | PASS | `test_cached_identity_reused_across_builds_hook_upgrades_and_derive` |
| 并发两连接只一行、同值返回 | PASS | `test_two_connections_first_get_insert_one_row_and_return_same_value` |
| 不同key相同Change-Id冲突 | PASS | `test_change_id_collision_rolls_back_without_replacing_existing` |
| 只读空表/删行拒绝且不写库 | PASS | `test_read_only_cache_miss_does_not_write`; `test_deleted_cache_without_derive_read_only_refuses` |
| 已有DERIVE + 无缓存,generate=None或传入函数均拒绝、调用0次 | PASS | `test_deleted_cache_with_derive_never_regenerates`两参数例 |
| 生成期间另连接写DERIVE,事务内重查拒绝 | PASS | `test_derive_inserted_by_other_connection_during_generate_refuses` |
| 事务内先重查缓存,已被并发填入则优先复用 | PASS | `test_cache_race_winner_takes_precedence_over_new_derive` |
| hook生成失败不落库 | PASS | `test_invalid_hook_output_does_not_write_cache`; `test_generation_failure_does_not_write` |
| 无效输出/两行/非0退出,CRLF成功41字符 | PASS | `test_invalid_hook_output_does_not_write_cache`; `test_crlf_output_is_stored_as_41_characters` |
| message已有身份行各大小写/Gerrit Link拒绝,普通Link通过 | PASS | `test_reject_existing_identity_before_reading_hook`; `test_hook_returns_only_id_without_mutating_message` |
| hook摘要不符/不可读拒绝;校验后源文件替换不影响执行副本 | PASS | `test_hash_mismatch_and_missing_hook`; `test_verified_bytes_execute_after_original_hook_replaced` |
| 超时杀进程组、无运行的子进程、临时目录移除 | PASS | `test_timeout_kills_process_group_and_removes_temporary_directory`;生产值30秒,测试显式缩短至0.5秒 |
| 业务仓库对象与配置不变;成功与失败临时目录移除 | PASS | `test_git_configuration_and_business_repository_are_isolated`; temporary_dirs fixture及失败用例 |
| 环境仅白名单、HOME/GIT_DIR/全局git配置隔离 | PASS | `test_process_environment_is_exact_whitelist`; 配置隔离用例 |
| 缺git/临时目录不可写/进程启动失败归统一错误 | PASS | `test_no_git_in_path_maps_to_hook_error`; `test_unwritable_temporary_directory_maps_to_hook_error`; `test_hook_process_start_failure_maps_and_cleans` |
| 清理失败仅WARN,不改变成功值 | PASS | `test_cleanup_failure_warns_without_changing_success` |
| 新表非法change_id/source/submission_key/hook_sha256拒绝 | PASS | `test_new_table_rejects_invalid_values`22参数例 |
| 只有apply_failed/analyzer_failed的n_a历史回退REPRODUCE | PASS | `test_previous_only_na_outcomes_fall_back_to_reproduce`两参数例 |
| 不同submission_key同message产生不同ID,hook要求HEAD可用 | PASS | `test_submission_key_is_hook_input_and_head_exists` |
| 生成器只返回Change-Id、不修改传入message | PASS | `test_hook_returns_only_id_without_mutating_message` |
| 最终derive消息 / sandbox重推 / review-submit端到端 | APPROVED_TRANSFER | 第5节移交清单,目标P4/P5/P5R |
| FatTank登记的真实hook冒烟与无HEAD兜底变体 | PASS | 第10节;`evidence/real-hook/result.json`:真实hook仅一行合法ID;变体无commit退出1、生成器空初始commit后退出0;网络系统调用0 |

## 9. 提交与远端验收(此前组件验收的历史记录)

实现提交:`3d48877ea13a129ce6e3868e59f9d45327371b41`,已推送。
本地组件与回归已验收,真实hook仍PENDING,不声称P2完整CLOSED。

远端CI: https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37740889109

```text
$ gh run watch 37740889109 --exit-status --interval 10
test in 1m20s: success
Lint: success
Type check: success
Tests: success
exit=0
```

上段为状态摘要;未经改写的job metadata与完整输出已分别归档到
`evidence/remote-ci.json`、`evidence/remote-ci.log.gz`(保留原始空白,无损压缩),获取命令及exit在
`evidence/remote-ci-commands.json`。远端Tests输出原文:

```text
======================= 1410 passed, 1 skipped in 48.83s =======================
```

两台环境的全量计数一致。再次核查FatTank指定hook仍不存在(sha256sum exit1),
见`evidence/real-hook-presence.log`。测试配置`real-hook-config.json`保留sha256=null。
本轮停在组件验收完成,等待该文件在当前执行机可读后计算真实摘要并补冒烟。
三个移交项仍按第5节绑定后续阶段,不提前声称已通过。

## 10. 真实hook补验与收口候审(2026-10-08)

FatTank本轮确认文件已下载。实际文件为Gerrit Code Review 3.10.5的
`commit-msg`,未修改原文件;配置`real-hook-config.json`已登记真实摘要并转VERIFIED。
第6/9节及`evidence/real-hook-presence.log`保留旧时点证据,不覆盖为成功输出。

```text
$ sha256sum /home/linhao/gerrit-hook/commit-msg
3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50  /home/linhao/gerrit-hook/commit-msg
exit=0
```

### 10.1 实际执行与无网络证据

仓库根执行(下列`E`仅为缩短命令,实际argv见`smoke.command.json`):

```sh
E=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/real-hook
env -u PYTHONPATH -u MYPYPATH strace -f -e trace=network -o "$E/network.trace" .venv/bin/python "$E/run_smoke.py"
```

原始输出(`smoke.log`,exit0):

```text
hook_sha256=3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50
Change-Id: I79e948ab08b03dc50822a0c798ba01c77a0c6360
real_hook: valid_change_id_lines=1; initial_commits=1; initial_tree_entries=0; exit=0
no_head_variant_without_initial_commit: exit=1; change_id_lines=0
head_required_variant: Change-Id: I79e948ab08b03dc50822a0c798ba01c77a0c6360; exit=0
original_hook_unchanged=true; input_message_unchanged=true; temporary_directories_removed=true
```

`run_smoke.py`为本轮取证脚本,调用现有生产`generate_change_id_via_hook`。
对`_run_isolated`只加观察包装并原样执行原函数,未替换命令或环境。
在hook返回且清理前采集实际message,断言恰一行合法`Change-Id: I<40hex>`;
执行副本摘要等于登记摘要。临时仓库`git rev-list --count HEAD`为`1`,
`git ls-tree HEAD`为空;业务message输入不变,临时目录最终删除。
`result.json`保存调用argv、隔离环境、实际hook输出、输入key与message。

`strace -f -e trace=network`跟踪包含hook后代进程;完整`network.trace`非空,
没有网络系统调用,`network-check.json`记录`network_syscalls=0, exit=0`。
没有访问Gerrit。复现时Change-Id可随git时间身份改变,不将本轮ID当固定向量。

### 10.2 无HEAD处理的变体

从真实hook原字节派生临时副本,仅将HEAD存在性分支替换为:

```sh
refhash="$(git rev-parse --verify HEAD)" || exit 1
```

无初始commit的隔离仓库中运行该变体:exit1、无Change-Id行,
stderr原文`fatal: Needed a single revision`。
同一变体通过生产生成器调用:exit0、恰一行合法ID。
`result.json`记录替换前后完整片段、变体sha256、负例stderr与成功现场;
证明成功依赖已创建的空初始commit,不是变体自己兼容无HEAD。
既有`test_submission_key_is_hook_input_and_head_exists`本轮同时复跑通过。

### 10.3 本轮验证与改动边界

命令、unset环境与exit全部存`evidence/real-hook/validation.json`,原始输出为同目录日志:

```text
$ env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest tests/unit/test_submission_identity.py tests/unit/test_campaign_change_ids.py tests/unit/test_campaign_state.py tests/unit/test_campaign_repair_step.py -v
============================= 135 passed in 9.09s ==============================
exit=0
$ env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
Required test coverage of 80% reached. Total coverage: 94.62%
======================= 1410 passed, 1 skipped in 32.32s =======================
exit=0
$ .venv/bin/ruff check docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/real-hook/run_smoke.py
All checks passed!
exit=0
```

取证脚本初次ruff检查报一条E501(104>100);仅拆分相邻字符串字面量,
未改取证语义,随后重跑冒烟和ruff通过。生产源码/单测/设计权威本轮零改动。
design.md/change_47摘要仍分别为第1节钉值。本收口提交不自记自身SHA。

补跑主工作树`ruff check .`时,四份既有untracked脚本报53条错误(exit1):
`audit_four_sigs.py`、`docs/clang-fix-campaign/{hashobj2,ident_check3,norm_diff5}.py`。
这四份未跟踪文件未改动、未入本提交;`workspace-only-ruff.json`记录其Git状态与摘要,
`ruff.log`/`quality.json`保留失败原文与命令,不隐去失败。
随后在`/tmp/p2-hook-closeout-3e1ea18`独立工作树检出`3e1ea18`,
施加本轮待提交diff(不带主工作树杂项),按该树scripts根设置PYTHONPATH,
重新实跑全部交付检查。命令/环境/exit见`clean-validation.json`,输出见`clean-*.log`:

```text
ruff: All checks passed!                                      exit=0
mypy: Success: no issues found in 104 source files             exit=0
lint-imports: Contracts: 6 kept, 0 broken.                     exit=0
symbol_audit: SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
exit=0
bridge: SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
exit=0
======================= 1410 passed, 1 skipped in 31.25s =======================
exit=0
```

上段前五项为原始日志对应行摘录加命令标签,非伪称一条命令的合成输出。
独立树复验与主工作树pytest结果一致;未通过修改无关脚本或ruff配置取得绿。

本阶段组件DoD全部通过,无剩余P2实施PENDING;三项端到端检查仍为第5节
APPROVED_TRANSFER,非已执行。既有三条checker问题的两树exit未变,见
`evidence/comparison.json`及收口文档遗留表,本轮不修改判据或历史输入。

收口文档:[P2 submission identity closeout](../../review/p2-submission-identity-closeout.md)。
当前状态仅**READY_FOR_REVIEW**,待设计方核验与评审签批。

## 11. 评审次要意见处置与签批(2026-10-08)

来源:设计方本轮轻量裁决;外部评审Claude Code结论CLOSED、零阻断、4条次要。
本节更新当前状态,不改写第10节的候审历史。设计正文保持原字节,待同步项见第12节。

| 意见 | 处置与验证 |
|---|---|
| 1 | 两API入口用`re.fullmatch(r"[0-9a-f]{64}", submission_key)`拒绝非法key,分别抛`ChangeIdHookError`/`StateInconsistent`;发生于读hook、建临时目录、连接DB及调用generate之前。两文件各覆盖换行注入、63位、大写三例;断言mkdtemp/generate未调用、缓存无写入 |
| 2(a) | `_require_no_derive`先调用既有`_require_unit`;unit不存在则拒绝。空库+generate用例零调用/零缓存写入;两个原裸库测试函数通过`campaign_db`fixture补create_unit,原有hook失败/CRLF断言保留。缓存命中分支和生成后事务内再次检查顺序不变 |
| 2(b) | 按裁决不修跨unit带外清库:共用submission_key的缓存被带外删除后,当前unit无DERIVE而其它unit有DERIVE时,当前unit仍可能重新生成。存在性检查不宣称解决这一边界;见收口“已知边界” |
| 3 | hook入口拒绝首行匹配`^[a-z]+! `,错误明确说明Gerrit hook对fixup!/squash!类提交不生成Change-Id;`fix! x`/`fixup! x`均在mkdtemp前拒绝。`Fix! x`大小写正例有单测及真实hook实跑 |
| 4 | `ec6c331`已完成真实hook与无HEAD变体补验,证据`evidence/real-hook/`;本轮不重写历史证据 |

### 11.1 命令、结果与证据

本轮证据根:`evidence/review-minors/`。基线`d2c93b2`,两个独立工作树分别为
`/tmp/p2-review-baseline-d2c93b2`与`/tmp/p2-review-current-d2c93b2`。
后者仅施加本轮2生产文件/2测试文件diff及取证脚本,不携带工作区原有改动。
每树以自身`*/scripts`派生PYTHONPATH/MYPYPATH;精确命令、环境路径、exit与
原始日志sha256记录在各自`commands.json`,全部日志原文随附。
`tested.patch`锚定实测代码;`production-scope.json`证明只有3个既有函数体变更,
定义集合不变、旧schema实现不变、design.md摘要仍为第1节钉值。

复现全套命令(基线实际首跑使用等价的`/tmp/p2_validate.py`,其逐条argv在JSON内):

```sh
E=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors
.venv/bin/python "$E/run_validation.py" /tmp/p2-review-baseline-d2c93b2 "$E/baseline"
.venv/bin/python "$E/run_validation.py" /tmp/p2-review-current-d2c93b2 "$E/current"
.venv/bin/python -m pytest tests/unit/test_submission_identity.py tests/unit/test_campaign_change_ids.py -v
env -u PYTHONPATH -u MYPYPATH strace -f -e trace=network -o "$E/network.trace" .venv/bin/python "$E/run_real_hook.py"
```

实测摘录:

```text
============================== 69 passed in 1.41s ==============================
targeted: exit=0
hook_sha256=3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50
Change-Id: I545bce8a248182290512b59d0b0d1a1629812e4c
subject='Fix! x'; valid_change_id_lines=1; input_unchanged=true; exit=0
network_syscalls=0
======================= 1420 passed, 1 skipped in 32.16s =======================
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
completed=94 unexpected=3
```

最后一行保留既有失败,不解释为“全部checker符合期望”。`comparison.json`逐条对照:
基线1410 passed/1 skipped,当前1420 passed/1 skipped;旧1411例全部仍在且结果不变,
新增10例全通过;`missing_nodeids=[]`、`changed_outcomes=[]`、`exit_changes=[]`。
90项既有设计门禁/控制+4项全仓验收在两树均实跑;三条遗留仍为
design-doc-controls(1)、duplicate-spec-root-mismatch(0)、twin-both-binary-key(1),
与原期望的偏差未新增。原因沿用closeout遗留表,没有放宽判据。
双道审计仍198 SYMBOL + 4 MODULE-SCOPE,零差异;六条import契约全绿。
真实hook调用与stdout原文见`real-hook.json`/`real-hook.log`,无网络证据见
`network.trace`/`smoke-validation.json`;本机hook路径不成为CI单测前提。

### 11.2 最终签批

- 设计方:2026-10-08核验通过,本轮轻量裁决批准上述处置。
- 外部评审:Claude Code,2026-10-08 CLOSED、零阻断;4条次要已按裁决处置。
- P2状态:**CLOSED**。三项P4/P5/P5R移交仍按第5节执行,不冒称端到端已验。
- 本签批提交与远端CI由Git/GitHub外部锚定,不在文件内自记本提交SHA;
  推送后核验对应CI完成结果并在回报中给出链接,不拿旧CI替代本轮验收。

## 12. 设计正文待同步

本轮不修改`design.md`。供设计方下次修订§4.2时并入:

| 条目 | 待同步措辞 |
|---|---|
| 次要1 | `generate_change_id_via_hook`与`get_or_create_change_id`入口先验证submission_key为64位小写十六进制,分别抛ChangeIdHookError/StateInconsistent;在临时目录/generate之前拒绝 |
| 次要2(a) | 缓存未命中后的`_require_no_derive`先确认campaign_unit_key存在,不存在即StateInconsistent,不得调用generate;生成后事务内复查沿用此规则 |
| 次要3 | hook前置拒绝补首行匹配`^[a-z]+! `,说明Gerrit hook跳过fixup!/squash!类提交;首行大写不属于该拒绝范围 |
| 次要2(b) | DERIVE检查按传入unit执行,不扩成跨unit搜索;带外删除共享缓存行的跨unit场景不在本轮保护范围,按收口已知边界登记 |

本轮未遇需另裁决的实现缺口。后续P3/P4原任务书未在当前会话、仓内任务文件
与可见文本附件中找到,已请求补发;不以设计中的阶段摘要自行替代原任务范围。
