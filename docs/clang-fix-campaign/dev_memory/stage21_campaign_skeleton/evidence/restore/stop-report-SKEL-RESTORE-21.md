# SKEL-RESTORE-21:离线发现建档与首次源码克隆冲突

2026-11-05,基线0931cb4。RESTORE-19已由RESTORE-20两命令文件交接处置。
本报告不重新质疑分包方案,仅报告新定义的网络边界冲突。

## 1. 条文与代码

- RESTORE-20第一.2.a:qb-discover为“唯一上网的一步”。
- 第一.2.b及第二.2:campaign-discover“不上网”,断言不发起任何网络请求;
  同时必须调用既有`intake.add_unit`完成首次建档。
- 骨架冻结稿§5.1第4步要求源码暂存克隆→身份校验→marker→rename;
  没有改为可省略的步骤。RESTORE-20也没有另行授权省略该步骤。
- `tizen-campaign-intake/scripts/tizen_campaign_intake/intake.py:141`写unit,
  `:152`写CI_EVIDENCE_READY,`:155`调用`_prepare_source`。
- 该函数`:51`仅在已有canonical源码时走本地身份检查;首次`:57`调用
  `SandboxGit.run(None, 'clone', remote, ..., remote=True)`。
- `tizen-campaign-core/scripts/tizen_campaign_core/_sandbox_git.py:43`设置SSH传输,
  `:63`执行git子进程。只禁止Python socket不能阻止这条网络路径。

## 2. 离线复现

[探针](batch3/r20/probe_offline_intake.py)调用真实add_unit和真实analyzer,
输入为现有`tests/fixtures/e2e_clang_compile/buildlog`,配置/库/工作区均临时创建。
在SandboxGit.run边界记录拟执行操作并抛固定OSError,不调用真实git。
没有真实远端访问,没有修改生产源码或现有测试。

[原始结果](batch3/r20/probe.json):

| 观察 | 结果 |
| --- | --- |
| 拟执行Git | clone ssh://gerrit.invalid:29418/platform/upstream/example,remote=true |
| Git子进程/网络请求 | 0/0,测试拦截发生在子进程创建前 |
| clone边界之前 | unit存在、evidence存在、CI_EVIDENCE_READY |
| 被测试阻断后 | exit5 INTAKE_CLONE_FAILED |
| 源码及暂存 | canonical不存在、暂存目录0 |
| 临时材料 | 目录及临时DB均删除 |
| 源码/测试/冻结稿/合约 | hash前后相同 |

该失败是现有可重跑语义,不是建议修改现行建档事务。
它证明在干净工作区调用add_unit不能同时满足“正常建档成功”和“不尝试任何网络请求”。
假SSH映射本地裸库可验证现有建档功能,但不能证明生产命令完全不上网。

## 3. 候选裁定(未实施)

### A. 维持add_unit语义,收窄“不上网”的定义

```diff
- qb-discover是唯一上网的一步;campaign-discover不上网。
+ qb-discover是唯一访问QuickBuild的一步。
+ campaign-discover不访问QuickBuild/HTTP,但允许既有intake.add_unit
+ 从gerrit_ssh_base + project作源码准备所需的只读clone;
+ 不新增fetch/push,不更改身份核验、锁、marker和发布规则。
- 断言campaign-discover不发起任何网络请求。
+ 除既有源码clone外不得联网;离线测试用假SSH加临时裸库,
+ 并阻断其它网络及Git远端操作,核对确切clone地址与次数。
```

副作用:不再是绝对离线消费清单,依赖Gerrit克隆可达性;克隆失败仍按既有
INTAKE_CLONE_FAILED/崩溃重跑语义处置。优点:不变更已验收建档及后续基线输入。
测试:首次假SSH克隆成功、已有副本重跑无clone、身份不符拒绝、远端失败清理、
无QB/HTTP调用、无额外远端操作、原有幂等与崩溃夹具不改。

### B. 维持绝对离线,拆开建档与源码准备

```diff
+ campaign-discover只发布证据并写unit,不调用源码准备。
+ 设计方另行规定可复用的无源码建档API及其锁/幂等/错误/输出契约,
+ 明确何时、由哪个显式命令准备源码,以及baseline-reproduce的前置。
+ 既有手工campaign-add-unit默认行为保持不变;不得通过猴子补丁跳过_prepare_source。
```

副作用:需要改变“调用现有add_unit完成建档”的接口要求,新unit可能尚无src_clean;
必须明确状态报告与下一步操作,不能靠编排猜测已准备源码。
测试:禁网环境首次建档成功、src_clean输出契约、离线幂等、后续源码准备成功/失败与
崩溃恢复、缺源码时baseline拒绝、手工add-unit既有用例不回归。

建议A,因为保持当前完整建档契约改动最小;若“零网络”是硬目标,须先裁定B的接口。
不自行解释“不上网”仅指QB,不把只跑dry-run或已有副本作为首次建档验收替代。

## 4. 当前状态

RESTORE-20已照录progress并追加design§4.6,依赖合约字节不变。
本轮没有实现新命令/修改代理/修改业务代码,未运行真实发现或任何真机命令。
仅运行离线探针和文档/合约检查,未运行全仓门禁;第3/4批保持未完成。
检查输出与命令见[validation.json](batch3/r20/validation.json)。
