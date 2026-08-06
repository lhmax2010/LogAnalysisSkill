# RC 阻塞裁决与 runbook v2 修订(2026-08-05)

## 裁决 1:evidence 一律 analyzer JSON,change_41 关闭为"无设计变更"

**定性**:设计与实现**自洽**——REPRODUCE/CONVERGENCE 的
evidence_path/sha256 自始指向 analyzer(tizen-gbs-log-analysis)
产物,`_primary_fingerprint` 的输入是结构化 evidence。矛盾出在
**smoke runbook E1.3/E6.c**:Claude 编写时未对照实现核验 evidence
类型契约(⑥在 runbook 层的违例,已记入方法论账)。

**change_41 处置**:头部状态写为——
> 状态:关闭(无设计变更)。裁决:设计 evidence 链自洽,错误在
> e2e-smoke-runbook v1;由 runbook v2 修订解决。本文件保留作停止-
> 报告协议的正确触发记录。

## Runbook v2 修订(三处,其余条款不变)

1. **E1.2 改**:GBS 基线构建 FAIL 后,**用真实 analyzer 对构建
   日志跑一遍**产出 evidence JSON;`ci_evidence.log` 仍为原始日志
   (unit 层替代物,标注不变),REPRODUCE 的 evidence 一律为
   analyzer JSON(记录其路径与 sha256)。
2. **E1.3 改**:REPRODUCE 事件的 evidence=analyzer JSON;
   fingerprint 经 `_primary_fingerprint` 对该 JSON 计算(权威来源
   不变)。附带收益:smoke 从此覆盖"日志→analyzer→evidence→
   指纹"的**全真管道**,比 v1 的验证面更宽。
3. **E6.c 改**:历史日志同样先过 analyzer 产出 evidence JSON,再
   与新鲜构建的 analyzer JSON 做指纹比对——"历史 vs 新鲜"的
   可比性验证目标不变,比较对象升级为结构化产物。

## 裁决 2:E6 补齐后的执行范围

**复核结果**:
- `tmp/Verification/log/multi-assistant.log` 已补齐,对应
  `tmp/Verification/codes/multi-assistant/` 源码与
  `packaging/multi-assistant.spec`;本例作为 E6 唯一历史真实用例;
- 额外发现 `united-servvice.log`,但 codes 下无 united-service 对应
  源码/packaging,按缺输入规则暂停该 case,不得自造;
- libtpl-egl 源码与 packaging 已补齐,但不扩张本轮已裁定的 E6 范围;
- E6' 在 cynara 上现做 **1 例**,与 multi-assistant 合计 2 例。

**E6 执行规则(裁决,写死)**:
- multi-assistant 先核对日志包名/根因、源码+packaging、analyzer
  parseability,再按原案(+v2 analyzer 修订)执行;
- united-service 缺源码/packaging则只暂停并报告,不计入已执行 case;
- cynara 走 **E6'(现做真实感用例)**。E6' 质量标准三条,防止退化
  成玩具注错:
  ① 用例必须经真实 GBS 构建产生失败(非手工编造日志);
  ② 故障必须属 clang/LLVM 22 真实事故族(候选:-Werror 提升的
     警告、模板两阶段名字查找差异、libc++ 头依赖缺失、C99 inline
     语义——均为本项目历史上真实发生过的类别),在 cynara 的
     C++ 源上构造 1 例;
  ③ 每例照 E6.d/e 全流程:Codex 自写修复、预算内收敛、独立小节
     入报告。
- E6 报告总计两个已执行小节:multi-assistant 真实历史例 + cynara
  E6' 现做例;另列 united-service 暂停项及所缺输入。

## 恢复点

本裁决落盘(change_41 关闭文本 + 本文件入
docs/clang-fix-campaign/review/)后,自 **E1 恢复执行**;RA/RB 的
三个本地 commit 维持不动,与 RC 产物一起在 RD 阶段统一处置。
