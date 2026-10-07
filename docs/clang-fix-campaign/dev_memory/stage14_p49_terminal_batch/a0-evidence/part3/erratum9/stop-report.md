# E9 停止报告与输入缺口

状态: C7e 局部已实跑;E9-5 全量预检未运行。SCAN-06 CLOSED;SCAN-07 OPEN。
本报告不宣告第3段任何一块整体完成,不宣告 SEAL/consumer closure 通过。

## E9-5 输入缺口(不是新增裁决)

冻结稿 E9-5(2416-2421)明确允许候选全集尚不能产出时如实报告缺项。
完整条目输入已取得:846 条,live 736 / release 110;其中非 Python 文本570条。
`non-python-preflight-inputs.json` 保存每个条目的 mode/hash/context/kind,
以及候选产物可用性检查。所有名字命中计数为 null/NOT_RUN,不是零。

| 类别 | 条目数 | 名字命中/UNKNOWN/多去处 | 新动态未决 |
|---|---:|---|---|
| PTH | 0 | 未测 | 未测 |
| PACKAGING | 2 | 未测 | 未测 |
| CI_CONFIG | 1 | 未测 | 未测 |
| SHELL | 0 | 未测 | 未测 |
| BUILD | 13 | 未测 | 未测 |
| IMPORT_LINTER | 1 | 仅模块位与SCAN-06见证实跑,不是全候选 | 局部0 |
| DOC | 431 | 未测 | 未测 |
| OTHER_TEXT | 122 | 未测 | 未测 |

缺项逐级列出(冻结稿 §1.1c:1008-1099;progress A05/A06/A09):

1. `#MODULE`:整模块候选发现尚无完整扫描产物。打包模块索引不是shim候选全集。
2. `#REEXPORT`:尚无全部模块的binding、`__all__`同步span与guard枚举。
   现有SCAN-06见证只有一个binding,不能充当此级全集。
3. `#INLINE`:尚无内联import的完整lexical qualname、public bound name和guard产物。
4. `#PROXY`:尚无纯委托callable发现器及部分转发/类方法/装饰器生成/宿主副作用
   四类假阴控制,也没有CTRL-INTRA-PKG-PROXY的全引擎实跑。

`shim_inventory.py`、`ledger_sources.json`、三段`ledger_inventory.json`、
`raw_findings.json`、`B-9-shapes.json`均不存在;现有terminal工具顶层定义清单
同存JSON供复核。`terminal_consumers.py`亦未落地,四种名字形态的全树兜底与
解释器行完整文法没有统一执行管线。现有Python预检、别名不动点、C7e组件
不能替代它们。本轮不拿部分候选跑“全量绿”,不继续第1块后续与第2–5块。

下一步仍须按既定§1.1c补齐四级发现及相应控制,并完成全部非Python兜底,
再对完整570条目收集全部阻塞后一次性报告。这里没有提出缩面/豁免请求。

## SCAN-07:预期差异门禁的来源锚与当前权威不一致

原文/实现定位:

- 冻结稿 §6 及勘误1–3要求登记项来源可复核;本轮批准的新文件SHA为
  `b5c2dce6568b722a70ceb92ed7860ecda4417ca8895310df4bdbf7ae9158cec3`。
- `tools/terminal_expected_diff.py:23` 的 `DOC_HASH` 仍钉勘误3
  `7b8531fdd9bcb4b2ecf8f3576eab6285f09f4b22fb1b212775939dbe72d19200`。
- `tools/terminal_expected_diff.py:96` 逐文件校验来源SHA;
  `tools/p49_terminal_data/expected_diff.json:20` 起的来源引用仍指同一路径的旧SHA。

实测命令与原文: `tests-final.command.json` / `tests-final.log` / `tests-final.xml`。

```text
51 failed, 288 passed in 1.99s
terminal_expected_diff.GateError: SOURCE_HASH: docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md
EXIT=1
```

51条失败均为该来源锚冲突,完整nodeid在`source-anchor-mismatch.json`。
门禁脚本与expected_diff.json相对8338889逐字节未改;旧权威66b33ef6也已不是
登记的7b8531fd。此为本轮扩展回归暴露的既存锚点失配,未重放上一提交全套测试,
不把“既存”推断成“此前全量实跑也有51个失败”。不把本次扩大测试范围的失败
隐去,不以扫描组件253绿冒充整体绿。

候选处置(未自行采用):

1. 对原登记所引条款逐段核对未变化后,经批准同步门禁及登记的当前文档SHA/位置;
   不改变旧值、消息派生规则、predicates或OBS。
2. 把来源显式锚到勘误3的Git blob,工具按该不可变版本校验;涉及来源寻址规则,
   需设计侧明确后实施。

保留原检查、原登记及失败输出,不绕过SOURCE_HASH。新规范裁决需求计1条;
E9-5候选输入未齐计1项实施缺口,二者分开。

## 边界

E9-4十项控制已登记,组件25个参数化测试通过;完整扫描管线状态仍NOT_RUN。
INI采用ConfigParser;来源无法精确定位(如defaults/插值引入的模块值)时当前组件
抛C7E_VALUE_PROVENANCE,不生成猜测边;固定树真实.importlinter没有此情形。
全量consumer对账未通过前不得把这个组件声称为通用INI覆盖已闭合。

无新OBS、无门禁改前实跑;before_run=PENDING_SEG3。生产、既有OBS和冻结
predicates/exemptions未改。没有生成scan completion标记。
