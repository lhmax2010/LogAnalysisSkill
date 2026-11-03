# SKEL-B2-06: 已绑定无RESULT时的父构建号要求冲突

状态:STOPPED,等待澄清。基线a7c2337,2026-11-03。
仅条文核对,未改业务代码,未执行真机操作。

## 相互冲突的要求

- SKEL-B2-05第1(a)条:“保留QuickBuild父构建号(取该unit最新request的
  BUILD_BOUND/RESULT事件中的qb_build_id,无则为空)”。
- 同一任务第二步测试要求:“已绑定无 RESULT 时两列为空”。
- 第1(b)条对结果文件引用无歧义:无RESULT则为空,不打开任何结果文件。

现行实现依据:
`tizen-campaign-core/scripts/tizen_campaign_core/campaign_state.py:1798`
的BUILD_BOUND校验要求非空qb_build_id,并禁止携带结果字段。
BUILD_BOUND可以先于RESULT独立存在,不是不一致库。

| 合法数据库状态 | 第1(a)(b)条要求 | 第二步用例要求 |
|---|---|---|
| 最新request含SUBMITTED、BUILD_BOUND(parent=101),无RESULT | 父=101,结果引用=空 | 父=空,结果引用=空 |

这不需要运行时探针即可确认,是同一输入的输出契约不一致。
没有为了通过测试而删掉BUILD_BOUND回退,也没有擅自修改用例期望。

## 候选处置(未实施)

建议保留列定义,修正第二步用例文字:

```diff
- 已绑定无 RESULT 时两列为空
+ 已绑定无 RESULT 时父构建号为该最新request的BUILD_BOUND.qb_build_id,
+ 结果文件引用为空;尚未绑定且无RESULT时两列为空
```

副作用:无额外参数或文件访问,不改数据库及P5Q写入;报告在构建进行中也能显示父构建号。
需补两个独立夹具:已绑定无RESULT、未绑定无RESULT;均检查Markdown/JSON一致和DB字节不变。
另保留多request/多RESULT不串位及引用只原样输出的用例。

备选(如确实要求两列同时出现):把第1(a)条改成“父构建号只取最新request的最新RESULT,
无RESULT则为空”。副作用是进行中的已绑定构建不显示父号,这是可见行为变化,必须裁定。

## 停止范围

本轮仅登记SKEL-B2-05、把旧停止点标为已处置、登记本冲突。
WIP未套用,没有修改生产代码、测试、冻结稿、安全核心、代理、身份函数或schema。
尚未执行第2批全仓及专项验收;原有7个假SSH测试的上轮结果不作为本轮新验收。
设计方澄清后从实现继续,不开始第3批。
