# SKEL-RESTORE-01 开工停止报告:恢复T1与审核拒绝规则冲突

日期:2026-11-04。基线:`f93b890`,分支`clang-fix-campaign`。
停止依据:本任务第五.2条“design.md契约与骨架现有代码冲突且无法同时满足”及
“需要修改sandbox-submit / qb-trigger / qb-result-fetch / review-submit的安全规则”。
本报告不是新的设计裁定;尚未实现第1批,不宣称任何恢复批次通过。

## 1. 无法同时满足的要求

1. SKEL-RESTORE-01第二.4.b、第四.2条要求导入先例命中T1,输出/保留
   `source_kind=t1_cherry_pick`,然后完整跑至review-submit和收尾。
2. 任务第〇.2条要求review-submit现有行为与拒绝规则不改。
3. `design.md:182-185`的A2与`:1881-1882`要求
   `fix_strategy_final in {code, cherry_pick}`且reproduced;`:1147-1149`要求
   非抑制T1现场重推为cherry_pick,不能以generated重标规避。
4. 当前`review_submit.py:298-299`仅接受generated/suppress来源,否则以
   state_inconsistent拒绝;`:314-316`即使放过来源检查,仍仅接受final=code,
   cherry_pick会写REVIEW_INELIGIBLE并报REJECTED_REVIEW_GATE。
   文件:`tizen-review-submit/scripts/tizen_review_submit/review_submit.py`。
5. 上述实现对应骨架冻结稿第5.3节(`campaign-skeleton-design-v1.3-FROZEN.md:185`)
   的“修法来源只有generated与suppress”。恢复任务取消该范围限制,但未授权调整这两处审核拒绝条件。

因此,T1成功链路与“审核拒绝规则零改动”不能同时满足。不是转换器不支持的正常降级场景,
不能故意令T1转换失败或伪造source_kind/final来把端到端测绿。

## 2. 离线证据

- [probe-review-t1.py](probe-review-t1.py):调用真实suppress_policy.evaluate与其内部真实guard;
  从未修改的review.run AST抽取两条条件原样求值。**未执行review命令,不是完整CLI/E2E探针**。
- [stdout](probe-review-t1.stdout.json)、[argv/UTC/exit](probe-review-t1.command.json)、
  [stderr](probe-review-t1.stderr.txt):exit0,三个向量断言通过,stderr为空。
- 源文件SHA256:`219d2f0095ad75bb0841319a4a345af46e6f11d8cf33c4b30e496b4a4a4d7378`。

| 同一非抑制edit的source_kind | 真实policy | 来源检查拒绝 | 若到达A2则拒绝 |
|---|---|---|---|
| generated | allowed / code | 否 | 否 |
| t1_cherry_pick | allowed / cherry_pick | 是 | 是 |
| suppress | allowed / suppress | 否 | 是 |

探针只有临时源码夹具,退出后已删除;无数据库、网络、编译或推送。
最初探针把仓库parents索引写成7导致FileNotFoundError,未到条件求值;
仅修正证据脚本为6后归档上述有效运行,未修改任何业务代码。

## 3. 候选处理(只提案,未实施)

建议设计方对本次恢复作窄授权,允许review-submit以下两行调整,而非笼统放宽所有安全规则:

```diff
-        if policy is None or policy.get("edit_source_kind") not in {"generated", "suppress"}:
+        if policy is None or policy.get("edit_source_kind") not in {"generated", "suppress", "t1_cherry_pick"}:
             raise sandbox._held("state_inconsistent", "missing or unsupported source kind")
...
-        if verdict.fix_strategy_final != "code" or not view.reproduced:
+        if verdict.fix_strategy_final not in {"code", "cherry_pick"} or not view.reproduced:
```

效果:恢复design.md的原A2范围;T1仍须实际内容现场重推、存量与重推一致、reproduced成立,
并完整通过取锁、放弃屏障、聚合、QB结果绑定、edit字节、TOCTOU与身份检查。
副作用:此前被拒的非抑制T1可进入审核推送,**确实改变现有拒绝规则**,必须显式裁定;
T1中含抑制的final仍为suppress,不应取得审核资格,forbidden依然零推送。

裁定后应补的夹具/测试(本轮不改):
- 复用`tests/unit/test_campaign_batch3_review.py`的本地裸库/假SSH夹具:
  非抑制T1+合法PASS+reproduced通过;T1抑制、forbidden、未复现、未知来源分别拒绝。
- 存量POLICY与现场重推不一致仍拒绝;六道重校验、放弃屏障与TOCTOU用例保持原断言,
  所有拒绝均断言零ref更新、零REVIEW事件。
- SKEL-RESTORE-01第四.2条新增T1导入先例全链路,断言来源与先例引用从提议到报告不被重标;
  原有四条离线端到端继续通过,全仓与静态门禁按任务要求执行。

若设计方坚持review-submit完全不改,则须明确撤回本轮“T1走完审核提交”的验收,
改为T1仅到sandbox并报告审核拒绝;这会削弱恢复目标,不作为实现方默认选择。

## 4. 停点与范围

只登记开工对照、证据与候选修法;生产、既有测试、design.md及冻结稿均未修改。
未运行全仓门禁,未声称第1/2批完成,未进入第3批代理取证或真机操作。
等待设计方裁定后从第1批继续;第3批取证完仍须另行停止。
