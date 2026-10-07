# PHASE2-01:历史键不是运行时调用方

状态:OPEN,等待设计方轻量裁决。A/B已完成并push,本停止不回退其批准行为。
阶段二没有删除或改写任何兼容壳、调用方、测试、审计工具。

## 原文与冲突

- 终止F `p49-terminal-batch-design-v1.31-FROZEN.md:2497-2502`:
  E11-3(2)要求全部文本字面命中恰归一类,代码/配置旧址引用REWRITE,
  历史记录与证据文件HISTORICAL,其它OTHER停报。
- 同稿 `:2505-2509`:每组删除后既有设计门禁仍须绿,名字复扫只可剩
  HISTORICAL/RELEASE。不能只让生产导入通过而破坏原门禁。
- `tools/table_audit_bridge.py:35-63`三条relocation源键包含
  `ci_triage/verify/workspace.py`,是step-0冻结表的历史主键;
  `p49-step0-design-v2.1-FROZEN.md:236-238`恰为其独立输入。
  `table_audit_bridge.py:436-440`用这些键做relocation,并非import旧址文件。

这些字符串处于活动工具代码,不是列举的历史文档/证据文件;按字面
REWRITE换成新位置会使冻结表匹配失败。若按HISTORICAL保留,则需要
明确允许“活动代码内的历史证据键”及其逐项边界,不能自行给tools/全局豁免。
这是分类规则对事实用途未明示的缺口,不是借路径改动修改门禁判据的理由。

## 实测反例

`anchor-conflict.command.json`含完整诊断源码/argv/env/hash,从固定
43a6aa6导入原bridge,不改任何文件;只在内存复制mapping并改源路径。

```text
UNCHANGED_HISTORICAL_KEYS consumed=3 produced=3 verdicts=0 PASS
PATH_ONLY_REWRITE consumed=0 produced=0
UNMAPPED_SOURCE: ('tizen_build_verify/workspace.py', 'create_worktree', 'build-verify')
UNMAPPED_SOURCE: ('tizen_build_verify/workspace.py', 'check_disk_and_maybe_cleanup', 'build-verify')
UNMAPPED_SOURCE: ('tizen_build_verify/workspace.py', '_copy_repository', 'build-verify')
PHASE2-01: E11 literal REWRITE cannot be applied to these historical keys
EXIT=1
```

该exit1为“路径改写后契约不成立”的构造证据,不是已将工具修改到失败状态。
原始输出见`anchor-conflict.log`。发现此口径缺口后停止后续准备,
未运行OBS-5,未修改分类规则使其通过。

## 候选处置

1. 建议:批准对**逐项证实为历史键**的命中登记HISTORICAL,附宿主位置、
   读取用途、对应不可变历史输入、保留理由;不按文件/目录一概放行。
   运行时import/patch/入口字符串仍REWRITE。删除后复扫使用同一逐项清单。
2. 将历史输入与映射键一并迁为独立的不可变历史数据载体,活动工具只读它;
   需要明确允许的工具改动范围和等价验收,本轮不自行实施。

## 已产出与尚未产出

固定树只读草案`preparation/`:

- deletion-inventory.draft.json:13宿主/183绑定,11次实测顶层def/class到零跃迁;
  每项含来源原文或抽取commit,规范位置由实际import链解析,不是凭名字推定。
- caller-classification.draft.json:846 tracked文件,4二进制;619个
  candidate×名字形态命中记录(非去重调用数),路径粗分485 HISTORICAL /
  30 REWRITE / 104 RELEASE / 0 OTHER。**用途复核尚未完成**;
  上述三条历史键就在REWRITE草案中,因此该草案不是最终可批准归类表。
- `quickbuild_log.py:8`的FailedPackage为真实本地依赖,读取点
  `:48/:51/:66/:81/:84`已记录,不得直接删import。skill侧三类型真依赖
  与新包根导出、release均明确排除。
- runner.discover_sibling_pythonpath只见step-0 closeout,未在E11-3(a)
  指定的step-0 §6.2中,也不满足整模块跃迁;本轮未擅自扩删除来源。
  该差异在inventory excluded登记,供设计方审阅范围,不默认删除。

项2私有件范围/拟删nodeid表、OBS-5入口全集与烟测尚未完成。
第二阶段人工闸门状态NOT_READY;A/B验收完整证据分别见phase1/commit-a、commit-b。
