# SCAN-09:行级 span 无法区分同一行的多个候选

状态:OPEN,停止报告。SCAN-08 已由 E10 解决,不是原问题重报。
权威为 `p49-terminal-batch-design-v1.31-FROZEN.md`,SHA-256
`37862f4acdc330caa1ebb563885037814256746ae87663e51a64685fe21ccc01`。
取证 HEAD=`43a6aa625f27da46daba190657bf62256080c68e`,
tree=`ca9331190e878af465e7968fe56e735585a5866e`。

## 原文与冲突

- F:1015-1021、1042-1045:四粒度分别发现,每个 re-export binding 有自己的 ID。
- F:626-628、1057-1060:N1 只归并同一 candidate/逻辑 binding 的互斥 producer。
- F:1097-1103:span 为 `(file, line_start, line_end, kind, guard)`,所有 span 同删同留,
  不得跨 candidate 重复;`__all__` 与 import 同步。
- F:1118 SEAL-7:ID 全局唯一且 span 不跨 ID 重复。

固定树旧址 `tizen-ci-triage/scripts/ci_triage/report.py` 是明确的兼容 shim:

```python
# line 3
from tizen_triage_report.report import TriageReportData, _primary_location, render_report
# line 5
__all__ = ["TriageReportData", "_primary_location", "render_report"]
```

三个 ID 的末段分别为 `#REEXPORT#TriageReportData`,
`#REEXPORT#_primary_location`, `#REEXPORT#render_report`。
即使用每个 `ast.alias`/字符串常量的最窄源码区段,它们的冻结 span 仍分别是
同一个 `(path,3,3,import_stmt,TRUE)` 和同一个 `(path,5,5,all_entry,TRUE)`。
列号能区分真实子区段,但不在冻结五字段内;不能自行添加或把名字塞进 guard。
这不是互斥 producer,三个名字也不是同一 binding,N1 不能把它们合为一个候选。
丢弃某个 span、把三个 binding 合为模块候选、修改生产文件拆行,均会改规则或范围。

## 全树收集

未遇首例即停。对全部272个 PY_SOURCE(含release)扫描 import alias、静态
`__all__` 条目、同一行多语句 import、模块级别名赋值与全部 callable 源位置:

```text
raw_same_line_multi_binding_groups=225
by_kind={'import_stmt': 219, 'all_entry': 6}
explicit_reexport_groups=23
explicit_by_context={'release-v1.4.0': 9, '.': 14}
cross_statement_import_groups=0
same_line_assignment_groups=0
same_line_callable_groups=0
```

225 是同型原始语法组,不是225个已判定shim;其中23组由同名 re-export 或
`__all__` 直接证明导出,其余202组不作shim定性。完整逐文件/行/名字/上下文/
原始语句列于 `candidate-span-stop.json` 与 `span-feasibility-probe.json`。
`candidate-span-stop.log` 完整列出23组,并打印上述最小见证的三个ID和相同span。
这次排查覆盖本问题的真实同型实例,不声称其它尚未实现的发现/归并规则均无问题。

复現脚本、argv、环境、输入hash在 `candidate-span-stop.command.json`。
实际末尾输出:

```text
SEAL-7 RED: distinct candidate IDs share the frozen five-field span; N1 cannot merge distinct binding names
candidate_universe=NOT_COMPLETE; shim_inventory=NOT_COMPLETE; E9-5=NOT_RUN; 570 text entries not certified
EXIT=1
```

## 候选处置(均未实施)

1. 由设计方补 span 的精确身份,例如列区间或 AST 子节点地址,并定义 import
   alias 与 `__all__` 条目的区段、共享语句的原子编辑/同删同留规则;同步 SEAL-7 控制。
2. 保留物理 span,另定义 binding 所有权或共享 span 规则,让共享一条语句的不同
   binding 不被误判重复;仍须证明删除一个 binding 不损伤其它 binding。

两者均需勘误,不在实现侧选定。当前没有改变 span schema、N1、生产源码或任何
已冻结predicate。报告停止项1条(SCAN-09)。

## 已完成与未完成

- E10原件校验通过:2处追加/38行新增/0行删除;SCAN-07当前quote与E4..E10范围绿。
- E10编号组件与9项控制通过,5组旧碰撞全部消歧;121个匿名ID唯一,两轮结果一致。
- 全仓pytest最终1300 passed/1 skipped/0 failed,exit0;证据见同目录原始日志。
- 未产出shim_inventory或四级候选全集;对应计数N/A,不能拿语法组代替候选数。
- CTRL-INTRA-PKG-PROXY仍NOT_RUN;E10身份组件控制不能代替该发现能力控制。
- E9-5未执行,570条范围已确认,阻塞/回退边/歧义/动态未决新增计数均N/A而非0。
- 后续8个OBS claim未运行,门禁before_run仍PENDING_SEG3;未改既有OBS产出。
