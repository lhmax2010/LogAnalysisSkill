# SKEL-B3-04: 基线与修复轮之间缺少状态推进的生产者

状态:STOPPED,待设计方裁定。基线:`0417ff3`。SKEL-B3-02已由SKEL-B3-03关闭,
本报告不是重新提出state_root问题。

## 已复现的停止点

1. 骨架冻结稿第3节第3/4步(63-64行)及第7节第3.5批(281行)规定:
   `baseline-reproduce`三架构之后直接运行`campaign-repair-step`。
2. 已验收的`baseline.py:165-169`在三架构REPRODUCE齐备且主架构matched时,
   写入`BASELINE_REPRODUCED`;本轮探针三次基线均exit0/outcome=matched。
3. 已有`campaign_repair_step.py:81`的可执行状态集合仅含
   `REPAIR_ROUND_RUNNING`;`:683-689`在入口只读校验时拒绝其它状态。
4. 首次修复因而返回exit4/`REJECTED_STATE_INCONSISTENT`,原文:

```text
campaign unit status is not executable: 'BASELINE_REPRODUCED'
```

5. 独立探针确认:状态前后均为BASELINE_REPRODUCED;round数0;编译调用预算0;
   修复build_verify调用0;调用前后DB SHA256相同。尚未执行任何审核提交或QB命令。
6. `design.md:1091-1092`写有
   `BASELINE_REPRODUCED -> REPAIR_ROUND_RUNNING`以及“edit_spec vN过policy”的进入条件,
   但本批允许的命令链中没有实现该推进的调用点。
   生产源码检索中REPAIR_ROUND_RUNNING只有声明、读取或白名单,没有写入者;
   既有repair-step测试在夹具中直接append该状态,不能代替生产入口。

因此端到端无法按指定命令序列继续。修改测试夹具直接append_status会掩盖缺口;
给编排skill加一条Python/SQL写库命令违反第6节的可执行命令集合约束;
擅自让baseline跳过BASELINE_REPRODUCED,或修改repair-step接受状态集合,都在改变既有契约。
本轮均未实施。

## 相关静态事实(未绕过停止点运行)

`LOCAL_3ARCH_PASS`的现有生产写入者是`sandbox_submit.py:592-594`,
它在聚合及副本检查通过后从REPAIR_ROUND_RUNNING推进。
repair-step的PASS路径写verification/link并返回,不写LOCAL_3ARCH_PASS。
因此冻结稿第3.5批“不运行sandbox-submit、止于LOCAL_3ARCH_PASS”也需要明确推进归属。
这只是代码核对,不冒充已通过首个停止点的端到端实测。

## 证据与执行

证据根:`handoff/`。

| 项 | 结果 | 路径 |
|---|---|---|
| 未验收review/start草稿定向测试 | 25 passed;不是本批验收 | `draft-focused/stdout.log` |
| 新端到端首条 | 1 failed,首轮repair被拒,其余因-x未运行 | `e2e-stop/stdout.log` |
| 独立已验收代码探针 | 1 passed,断言上述拒绝、零round/零预算/DB不变 | `probe/stdout.log` |
| 撤下草稿后同一探针 | 1 passed,与草稿无依赖 | `restored-probe-final/stdout.log` |
| 调用点/源码引用 | 静态搜索输出 | `source-facts.txt` |
| 未验收实现 | 只作定位参考,不得直接套用当交付 | `implementation-wip.patch` |

各次命令argv、UTC起止、退出码、前后loadavg见对应`command.json`。
最初开发中的25项定向测试已通过;归档运行是停止后为留存完整输出的同树复现,
不作为以重跑覆盖失败。端到端原失败与归档复现均为上述同一形态。
探针仅使用临时库/裸仓库、已验收假SSH与假gbs、真实analyzer;
不访问真实Gerrit/QuickBuild,不运行真实gbs。

## 候选处理(未实施)

推荐A:由设计方明确扩展`campaign-repair-step`的状态推进职责:

- 首次接受BASELINE_REPRODUCED,在适当的既有锁/事务边界内重新校验三架构基线、
  主架构matched、源码身份及本轮edit_spec/policy后,才写REPAIR_ROUND_RUNNING;
  不应只扩大状态白名单或无条件写状态。
- 明确同一最终round三架构PASS聚合成功时由哪个现有命令写LOCAL_3ARCH_PASS,
  使第3.5批不必调用有推送能力的sandbox-submit;同时规定并发最后两个架构、
  崩溃重入、重复调用和已终态时的行为。
- 保留编译预算、对账、保护标记与屏障既有语义,不放开其它终态/held状态。

副作用:将修改已验收repair-step行为,超出本轮原边界,须显式授权。
新增测试:完整基线首次进入;缺一个基线或主架构不匹配拒绝;policy拒绝不进入;
推进前后崩溃重跑;同round三PASS才推进、跨round/树不一致拒绝;并发与重复推进幂等;
终态/held不能借入口恢复;原有repair-step用例原样通过;三条端到端和第3.5批停止状态。

候选B:新增独立的本地修复轮编排入口负责上述两次推进,保留底层repair-step不变。
副作用:增加命令/签名与剧本白名单,改变冻结的“只经现有命令”范围;
需明确锁、policy时机、事务与崩溃恢复,并新增同样的负例和端到端测试。

不采纳为实现捷径:在测试或AI剧本中直接补写状态,或把baseline最终状态改成
REPAIR_ROUND_RUNNING。这些做法不能证明冻结命令链可运行,且绕过edit_spec过policy条件。

## 交付边界

未验收review-submit/start-check与测试草稿已撤下并归档为patch;
生产模块/入口恢复到0417ff3,没有改旧测试断言。SKEL-B3-03原文已登记。
编排skill与模板未交付,三条端到端未通过,不开始第3.5批。
本轮没有跑全仓pytest/import-linter/mypy及计时敏感用例,不能把25项定向结果当全仓通过。
不改安全核心、共享身份规则、schema、P5Q写入、代理或冻结稿。
收集、保护文件hash及文档检查结果见`handoff/checks.json`。
停止树收集3028个nodeid,与第2批最终集合双向差集为空;设计检查0 problem。
证据脚本初次ruff报一个未使用的Path导入,已删除并在`ruff-evidence-final/`复验通过;
原输出保留在`ruff-evidence/`,不属于生产或全仓测试失败。
