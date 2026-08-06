# E2E-SMOKE:真实环境最小 campaign(P4.5 现实验证)

> **v3 修订(2026-08-05)**:合并 change_41/42 的真实环境裁决。
> 原始 GBS log 先经真实 analyzer 生成 evidence JSON,REPRODUCE 与
> fingerprint 只消费 JSON;campaign-repair-step 使用完整公开参数名,
> `--arch`/unit 字段传 raw 页名 `standard-armv7l`,DB/workspace 中的
> `arch_norm` 仍为 `armv7l`。其余验收语义不变。

## 0. 定位与协议

**目标**:在 GBS 构建主机上,用**真实 GBS chroot(armv7l,LLVM
22.1.8)+ 真实 build_verify + 真实文件系统**,把 P4.5 的九步序走完
一条完整弧:FAIL 收敛(6a)→ PASS 落链(6b)→ 崩溃恢复(reconcile
b 分支),外加并发/预算/HELD 三个边角。**不触碰 Gerrit 与
QuickBuild**——smoke 止于闸一,任何 push/QB 提交属 P5,本任务禁止。

**协议不变**:停止-报告(现实与设计不符 → 停,立案 change_41+,
禁止顺手改代码迁就现实);实测验证不脑补(所有断言贴命令+输出
原文+文件 sha256);工作全部在**独立 smoke 目录与独立 state DB**
进行,不碰任何生产状态。

**说明两点**:①unit 创建与 baseline-reproduce CLI 属 P6 未实现,
本 smoke 用**种子脚本**经冻结公开 API 播 unit 与 REPRODUCE——只许
`campaign_state` 公开 API,**禁止直写 SQL**(种子脚本因此也是这些
API 吃真实数据的首次检验);②ci_evidence 用本地捕获的失败日志
替代真实 QuickBuild 证据,在报告显著标注该替代(P5 前用真实 CI
证据重验一次)。

## E0. 环境预检(全部贴输出)

1. GBS armv7l chroot 可用:`gbs build --help`;确认 LLVM 22.1.8
   profile(沿用 libc++ Wave 1 的冻结配置,列出 gbs.conf 路径与
   sha256);
2. 选定 smoke 包:**小、快、C++**。推荐从 libc++ 迁移工作里挑一个
   单次构建 < 5 分钟的真实包;记录其 git 仓库、base_commit;
3. smoke 目录:`tmp/campaign-smoke/{state.db, ws/, logs/}`;
4. 干净基线:该包在当前 chroot 下**能构建通过**(贴尾部日志)——
   这是注入故障前的对照锚。

## E1. 目标构造与基线(合成故障,受控全弧)

1. **注入故障**:在包源码加一个确定性 clang 错误(建议:C++ 源里
   引一个未定义符号或删一个必要 `#include`),commit 到本地分支,
   记 `base_commit_broken`;
2. **捕获基线失败**:GBS 构建一次 → FAIL,保存完整 raw log 为
   `ci_evidence.log` 并记 sha256;随后用真实 `gbs_analyzer` 分析该
   log,保存 `evidence_packet.json` 并另记 sha256。raw log 是 unit 层
   CI evidence 替代物与审计锚;REPRODUCE/convergence 只消费 analyzer
   evidence JSON;
3. **种子脚本 `seed_unit.py`**(冻结 API only):
   - `ensure_schema` → `create_unit`(真实身份字段、
     primary_arch=standard-armv7l、failed_arches=["standard-armv7l"]、
     max_rounds=3、max_build_invocations=6、ci_evidence 三元组);
   - `append_event(REPRODUCE, ...)`:evidence=analyzer JSON 真实路径+
     sha256,outcome=matched,fingerprint 按
     `convergence.py::_primary_fingerprint` 对该 JSON 计算(权威
     来源,不许自算);payload `basis` 另记 raw log 路径+sha256;
   - 跑后用 sqlite3 只读查询贴出 unit 行与 REPRODUCE 事件原文。
4. **准备两份 edit_spec**:
   - `es_round1.json`:**不完全修复**(改了但引入另一个确定性
     编译错误)→ 预期 FAIL 且指纹与基线不同 → 6a 应判 advance;
   - `es_round2.json`:**正确修复** → 预期 PASS。

## E2. 修复弧(核心验证)

**R1(FAIL→6a)**:

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/python -m ci_triage campaign-repair-step \
  --campaign-unit-key <key> \
  --state-db tmp/campaign-smoke/state.db \
  --config tmp/campaign-smoke/campaign.yaml \
  --round-index 1 \
  --edit-spec tmp/campaign-smoke/es_round1.json \
  --arch standard-armv7l
```

R2/E3/E4 的 repair-step 调用复用以上完整参数集合,只替换 unit、round
和 edit_spec;`--arch` 始终传 raw `standard-armv7l`。实现映射后的
`arch_norm=armv7l` 用于 DB 事件、workspace 与 `gbs -A armv7l`。

断言(逐条贴原文):
- exit=0(FAIL 但流程正常),stdout 为**单个可 `jq` 解析的 JSON**,
  固定字段齐(含空 `reconciliation`/`warnings`);
- `result=FAIL`,`verdict=advance`(指纹异于基线;若判 stalled/
  regressed,停止报告——说明指纹或 previous 语义与现实有出入);
- DB:恰 1 条 BUILD_INVOCATION、恰 1 条引用其 event_id 的
  CONVERGENCE;`invocations_used=1`;
- evidence 文件存在且 sha256 重算与事件记录一致;
- worktree 布局 `ws/<unit_hash>/armv7l/iter_1` 与设计一致。

**R2(PASS→6b)**:round 2 + `es_round2.json`。断言:
- exit=0,`result=PASS`,`verification_id` 非空;
- link 行存在;PASS CONVERGENCE 占 R2 invocation 唯一槽,
  verdict=n_a、evidence=null;
- **previous 链**:6a→6b 间,R2 的 previous 应解析到 R1 evidence
  (查 resolver 实际取值贴出);
- protected marker 在 worktree 上真实存在。

## E3. 崩溃恢复实验(本 smoke 的核心价值)

新种一个 unit(同包同故障),直接跑正确修复的 round 1,但:
1. 起一个 watcher:轮询 PASS record 落盘(verification_records 出现
   未 link 行)即 `kill -9` repair-step 进程——精确打进"PASS 已写、
   link 前"窗口(如窗口太窄打不中,允许在 wrapper 外用环境变量
   注入 link 前 sleep,**仅限 smoke,不进主干代码**;用了必须报告);
2. 验尸:DB 有 BUILD_INVOCATION 无 CONVERGENCE、有未 link PASS、
   `invocations_used=1`;
3. **重入同一 round**:断言 `branch=relinked`、exit=0、
   `invocations_used` 仍=1(不重复计费)、不重复 build(日志无第二
   次 gbs 调用)、PASS CONVERGENCE 落座**旧** invocation 的
   event_id、stdout 的 `verification_id` 与 DB link 一致。
   ——这是 v1.5.9–v1.5.13 四轮探针战场的现实复验。

## E4. 边角三件(各一条)

1. **并发锁**:同 unit/arch 同时起两个 repair-step(不同 round 亦
   可)→ 一方 `CAMPAIGN_STATE_BUSY` exit 5,DB 无该方任何写入;
2. **预算终态**:一次性 unit(max_rounds=2)连跑三轮失败修复 →
   第三轮 RoundsExhausted exit 4,status_log 落 ROUNDS_EXHAUSTED;
3. **HELD 可达**:R1 后手工改名 R1 evidence 文件 → 跑 R2 → 预检
   HELD(previous_evidence_missing, armv7l)且 exit 4;若
   campaign-rebaseline CLI 已实现则顺带验授权(同 arch 可、异 arch
   拒),未实现则注明留待 P6。

## E5. 报告格式

`docs/clang-fix-campaign/review/e2e-smoke-report-v1.md`:
- 每步命令 + stdout 原文 + 关键 DB 查询原文 + 文件 sha256;
- **现实观测数**:单轮墙钟时间、DB 尺寸、worktree 尺寸;
- 偏差清单:凡"现实行为 ≠ 设计预期"逐条列出(哪怕最终判无害),
  含 ci_evidence 替代、sleep 注入等全部妥协项;
- 结论三选一:全绿 / 有偏差但判无害(附裁决请求)/ 停止报告
  (候选 change_41)。

**完成定义**:E2 全弧 + E3 恢复 + E4 三件全部有实测输出;任何一处
现实与设计冲突 → 停在那里,这正是本任务存在的目的。
