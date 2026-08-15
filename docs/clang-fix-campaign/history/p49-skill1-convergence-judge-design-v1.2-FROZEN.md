# P4.9 skill-1 设计:tizen-convergence-judge 抽取(v1.2-FROZEN)

> **v1.1 修订(两家评审)**:①【MAJOR,Kimi】弃 module-scope、改纯逐
> 符号注册(v1.0 的同文件双重注册撞死修订-7 互斥断言③);33 符号表
> 由脚本自源码机械生成(⑩,非手抄);module-scope 断言(a)的 skill
> root 扩展**本批不启用**,留待首个真正整模块迁移的 skill 批次;
> ②【NIT】别名落点定死 convergence.py 末尾;③【NIT】campaign_state
> 用 `import ... as` 保持调用点零改动;④【NIT】§1.2 表注措辞更正。
> ChatGPT 确认三重点成立;Kimi 消费图独立复核吻合(439 行/零内部
> import/零 arch)。**v1.2**:两家 delta 双 freeze-ready;修 Kimi 两处
> v1.0 残留文字(§7 "skill 注册表"、附录"唯一判据变更")。

- 阶段:P4.9 首个 skill 批次(step-0 CLOSED @7e9eb4e 之后)
- 前置输入:stage07 result.md"下游输入"四项(本稿全部承接)
- **总铁律**:行为等价——整体搬移 + 公开契约别名 + import 翻转,零语义
  变更;基线 == step-0 收口全量数(846/1),原样全绿。
- 消费图证据(⑩,Claude 实测 @7e9eb4e):convergence.py **零 ci_triage
  内部 import(纯 stdlib)**;消费方——`check_convergence` ←
  cli.py / campaign_repair_step.py / test_convergence.py;
  `_primary_fingerprint`/`_error_count` ← campaign_state.py(唯二私有
  跨界);`ConvergenceResult` ← campaign_repair_step.py /
  test_campaign_repair_step.py。

---

## §1 skill 物理形态与迁移方式

### 1.1 布局

```
tizen-convergence-judge/
  SKILL.md
  scripts/tizen_convergence_judge/
    __init__.py        # 仅导出公开契约(§2),不聚合内部件
    convergence.py     # 现 verify/convergence.py 整体迁入(439 行,逐行搬移)
```

PYTHONPATH 前缀加 `tizen-convergence-judge/scripts`;pyproject packages
加 `tizen_convergence_judge`。

### 1.2 迁移方式:纯逐符号注册(v1.1 改,弃 module-scope)

convergence.py 整体迁入 skill 包,但审计登记走**逐符号表**(33 现存
+ 2 待建别名 = 35 行),不用 module-scope——理由:①v1.0 的"module-
scope 行 + §2.1 六公开符号逐符号行"违反修订-7 互斥断言③(同文件
不得两制并存),实现期必 MISMATCH;②公开契约六符号本就有逐行冻结
诉求,符合 step-0"发生逐行裁决诉求的走逐符号"先例;③单文件 33
符号穷举成本极低、保证更强。**module-scope 断言(a)的 skill root
注册表扩展本批不启用**(纯逐符号用不上),作为备述留待首个真正整
模块迁移的 skill 批次;`expected_top_level_count` 计数钉定**仍溯及
step-0 既有四模块**(批次输入第 1 项,不随本项取消)。

**逐符号归属表(脚本自源码机械生成 @7e9eb4e,33 现存符号,owner
全部 = skill/tizen_convergence_judge)**:

| symbol | owner |
|---|---|
| DEFAULT_BUILD_PREFIXES | skill/tizen_convergence_judge |
| SOURCE_CLUSTER_KINDS | skill/tizen_convergence_judge |
| SOURCE_DIAGNOSTIC_KINDS | skill/tizen_convergence_judge |
| ERROR_DIAGNOSTIC_KINDS | skill/tizen_convergence_judge |
| _WARNING_OPTION_RE | skill/tizen_convergence_judge |
| _IDENTIFIER_RE | skill/tizen_convergence_judge |
| _BUILD_PACKAGE_RE | skill/tizen_convergence_judge |
| ConvergenceResult | skill/tizen_convergence_judge |
| _Fingerprint | skill/tizen_convergence_judge |
| _ClusterView | skill/tizen_convergence_judge |
| check_convergence | skill/tizen_convergence_judge |
| write_convergence_result | skill/tizen_convergence_judge |
| touched_files_from_json | skill/tizen_convergence_judge |
| _fingerprint_dict | skill/tizen_convergence_judge |
| _primary_fingerprint | skill/tizen_convergence_judge |
| _diagnostic_code | skill/tizen_convergence_judge |
| _anchor | skill/tizen_convergence_judge |
| _regression_reason | skill/tizen_convergence_judge |
| _regression_suspected | skill/tizen_convergence_judge |
| _clusters | skill/tizen_convergence_judge |
| _cluster_view | skill/tizen_convergence_judge |
| _cluster_diagnostic_code | skill/tizen_convergence_judge |
| _cluster_files | skill/tizen_convergence_judge |
| _location_dicts | skill/tizen_convergence_judge |
| _is_source_level_cluster | skill/tizen_convergence_judge |
| _error_count | skill/tizen_convergence_judge |
| _is_error_cluster | skill/tizen_convergence_judge |
| _normalize_file | skill/tizen_convergence_judge |
| _normalize_message | skill/tizen_convergence_judge |
| _stable_hash | skill/tizen_convergence_judge |
| _string | skill/tizen_convergence_judge |
| _int | skill/tizen_convergence_judge |
| _string_list | skill/tizen_convergence_judge |
| primary_fingerprint(to-be-created,§2.2 别名) | skill/tizen_convergence_judge |
| error_count(to-be-created,§2.2 别名) | skill/tizen_convergence_judge |

旧址 `verify/convergence.py`(v1.1 更正表注:与 step-0 的
workspace.py **同款处理方式**,非改 workspace.py)变纯 re-export
shim(零 def/class),入 §6.2 shim 删除清单;INCOMPLETE 公共面护栏
覆盖 skill 包内 convergence.py(护栏跟模块走,⑩终补)。

## §2 公开契约(SKILL.md 的机器侧)

### 2.1 公共面(逐符号表,bridge 在册)

| symbol | 契约 |
|---|---|
| ConvergenceResult | 输出类型,字段冻结如现状 |
| check_convergence | 核心判定,verdict ∈ {advance, stalled, regressed}(denied 属 failure_classify,不在此) |
| write_convergence_result | 结果落盘 |
| touched_files_from_json | 输入辅助 |
| **primary_fingerprint**(新) | `_primary_fingerprint` 的公开别名(§2.2) |
| **error_count**(新) | `_error_count` 的公开别名(§2.2) |

### 2.2 私有 import 契约重定义(排险清单头号项)

**裁决:公开别名 + 对象同一性断言,消灭跨包私有 import,零转录风险**:

```python
# tizen_convergence_judge/convergence.py 末尾追加两行(v1.1 定死:不放 __init__,其保持 §1.1 薄导出):
primary_fingerprint = _primary_fingerprint
error_count = _error_count
```

- campaign_state.py 的 import 翻转(v1.1 改,调用点**零改动**):
  `from tizen_convergence_judge.convergence import primary_fingerprint as _primary_fingerprint, error_count as _error_count`
  ——本地绑定名保持原样,diff 严格限于 import 行(§5.1 字面达标);
  本地名去下划线的美化改名**不做**,留 P4.9 末 shim 清理 commit 顺带;
- **签名冻结方式 = 对象同一性,不抄签名**:测试断言
  `primary_fingerprint is _primary_fingerprint`(id 级同一)——别名即
  原函数,签名/行为天然逐字节一致,**杜绝转录漂移这条事故族**
  (write_workdir_marker 三轮签名裁决的教训:凡可用同一性替代转录的,
  一律同一性);
- **第二权威零风险自证**:实现只有一份(别名非拷贝),grep 全仓
  `def _primary_fingerprint|def primary_fingerprint` 恰一处定义。

### 2.3 SKILL.md(人读侧)

name=tizen-convergence-judge;description 触发边界收窄至"两份
analyzer evidence 的收敛判定"(不含失败分类/不含 denied/不含日志
解析);inputs(当前 evidence + previous basis + touched_files)、
outputs(ConvergenceResult)、errors、幂等性声明(纯函数,唯一副作用
= write_convergence_result 显式落盘)。

## §3 门禁激活(step-0 DEFERRED 关门项)

1. **root-layers 启用**(真实行,不再注释):
   `ci_triage > tizen_convergence_judge > tizen_ci_shared`;
   `containers` 写法按 **import-linter==2.3 钉版实测**定(⑭:落盘
   即跑,语法不符停止报告,不猜);
2. **shared-no-uplink 的 forbidden 清单**加 `tizen_convergence_judge`
   (shared 不得 import skill,§1.3 演进点第一次兑现);
3. **skill-independence 维持 DEFERRED**:independence contract 需 ≥2
   模块,当前仅一个 skill——显式登记"第二个 skill 批次启用",非
   本批遗漏;
4. **负控制(⑭,exit code 入 dev_memory)**:
   ①skill 内临时 `import ci_triage` → root-layers 红;
   ②shared 内临时 `import tizen_convergence_judge` → forbidden 红;
   ③既有四契约正向仍绿(激活不回退)。

## §4 C21 子进程锚定(批次输入第 3 项,先行)

convergence-judge 测试变更前完成:两个子进程测试
(test_campaign_cli_*)的 PYTHONPATH 由 CWD 相对改为 **`__file__`
锚定拼装全部 sibling scripts 路径**——修后任何干净 clone 环境复跑
不再假阴性(验收信号:Claude 的核验环境此前稳定 2 failed,修后应
0 failed)。仅测试基建,零生产改动。

## §5 审计与 parity

- SPECS/bridge 扩展:§1.2 的 35 行逐符号表进 SPECS;本稿 §1.2 单表进
  bridge 解析域(第六张表;§2.1 为 §1.2 的公开子集,不重复入表);双道全绿为冻结/收口双闸;
- parity:同 fixture 双跑 `check_convergence`,输出 JSON 掩码
  (§5.2 规则沿用)后逐字节一致;别名走同一性断言(§2.2),免掩码;
- **⑧三架构声明**:convergence.py 零 arch 分支(grep `arch` 实测为
  证据,实现时贴)——⑧的基数维度在本 skill 为
  verdict×previous_basis×truncated,由既有 test_convergence 矩阵覆盖,
  arch 维度**有据豁免**而非静默跳过。

## §6 commit 划分(三个,每 commit 全量+lint 双绿)

- **A(测试基建)**:C21 锚定,零生产改动;
- **B(抽取主体)**:建 skill 包 + convergence 整体迁移 + 两公开
  别名 + 旧址纯 shim + 消费方翻转(cli/campaign_repair_step/
  campaign_state/测试)+ 同一性断言测试;
- **C(门禁与审计)**:root-layers 激活 + forbidden 扩列 + 负控制
  ①②③ + SPECS/bridge 扩展(35 行逐符号)+ module-scope 计数钉定(仅溯及 step-0 四模块)
  + SKILL.md。

## §7 DoD

- [ ] 全量 == 基线(846/1),且 **C21 修后干净环境 0 failed**;
- [ ] 别名同一性断言绿;grep 全仓两函数各恰一处定义;
- [ ] 旧址 convergence.py 零 def/class(纯 shim);
- [ ] root-layers/forbidden 激活,负控制①②红 + 四契约正向绿,
  exit code 入 dev_memory;
- [ ] 双道审计全绿(35 行逐符号 + 计数钉定溯及 step-0 四模块);
- [ ] parity 掩码一致;⑧ arch 豁免证据(grep)在档;
- [ ] SKILL.md 落盘;shim 清单更新;
- [ ] 测试 diff 仅 §5.1 两类(C21 的 A commit 除外,其性质为测试
  基建修复,单独 commit 隔离)。

---
## 附:与 step-0 的机制复用清单
module-scope(修订-7/7a)+ 计数钉定(评审 B)+ 双道审计 + ⑭ 实测
纪律 + §5.1/§5.2 边界 + shim 生命周期——全部直接复用,本稿零新
机制;**本批零判据变更**(module-scope 断言(a)的 skill root 扩展留
备述、未启用,待首个真正整模块迁移的 skill 批次)。
