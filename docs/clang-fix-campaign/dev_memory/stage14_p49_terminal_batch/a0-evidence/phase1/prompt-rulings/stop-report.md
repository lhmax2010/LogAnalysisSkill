# PHASE1-03:分提交实施与全量终态差异门禁冲突

状态:OPEN,2026-10-07。PHASE1-01/02 已按本轮提示词裁决闭合;
本项是新的规格可满足性问题,不修改冻结稿或门禁自行取舍。

## 原文与实现锚

| 位置 | 要求 |
|---|---|
| `p49-terminal-batch-design-v1.31-FROZEN.md:1526`,§6 形态第3项 | 实际差异精确等于登记差异;登记但未出现也必须红 |
| 同稿`:1568`,§7 commit划分 | A只实施项4;B才实施项3+项5 |
| 同稿`:2487`,E11-2 | A、B均按§3/4/5/6验收,改后与登记差异逐项相等 |
| `tools/terminal_expected_diff.py:667` | 结果对象须包含manifest全部场景,不能以仅传A场景绕过 |
| 同工具`:687` | compare遍历全部登记,无阶段参数或尚未实施差异的出口 |

冲突:最终登记的`DANGLING_SYMLINK`异常type/code/message属于项3,
按§7须留到B。但在A只完成timeout时,§6会因这三项尚未出现而红。
直接提前实现项3、过滤登记或把精确相等改为子集,均不是本轮授权。

## 构造式证据

命令与程序全文在`stage-a-satisfiability.command.json`,原始输出在
`stage-a-satisfiability.log`。使用已有人工正常对照,先确认完整终态绿;
再只将悬空链接异常三字段恢复改前,保留全部timeout登记差异。
未改生产,不是实际改后运行,不冒充A的行为验证。

```text
FULL_TARGET_ARTIFICIAL=PASS
POST_A_ARTIFICIAL: all timeout deltas present; item3 exception triple unchanged
PRODUCTION_EDITS=0; not a real after run
POST_A_ARTIFICIAL=REJECTED: DIFF_PATHS: extra=[] missing=['/exception_code', '/exception_message', '/exception_type']
EXIT=1
```

## 候选处置(待设计方)

1. 明确分阶段期望:保留冻结的最终登记,为A定义受设计方批准的阶段投影;
   只要求项4差异兑现,项3三字段必须保持改前,B再要求完整终态。
   投影不能由实际差异反推,必须显式列明字段及来源,并配漏改/多改控制。
2. 调整A/B验收时点:各自范围测试,累计完整§6只在B后验收。
   这会修订当前“A验收后才能提交B”的口径,需设计方明确批准。

推荐1,但未实施任一方案。A/B生产代码均NOT_STARTED;第二阶段准备与OBS-5
也未启动。固定树30场景改前已完成,不需要为此重跑OBS或更改其事实。
