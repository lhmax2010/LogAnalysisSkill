# PHASE2-02: E11-4 与包根版本接口

状态: STOP, 等设计方裁决。没有删除兼容壳、修改生产或测试、运行 OBS-5。

## 原文与实测

权威 `p49-terminal-batch-design-v1.31-FROZEN.md:2514-2516`:

- 范围包含 tests/ 中经包根 `__init__` 导入以下划线开头名字的全部位置;
- 私有名字不得出现在任何包根导出中,测试须从定义模块直接导入;
- 拟删测试只能是兼容壳本身的存在或同一性测试,其余一律保留。

固定 HEAD `43a6aa625f27da46daba190657bf62256080c68e`,
tree `ca9331190e878af465e7968fe56e735585a5866e`,工作区 clean。
逐个解析全部 52 个 tests/ Python 文件的 ImportFrom,仅就已登记兼容绑定
与实际包根过滤,命中:

```text
tests/unit/test_package_metadata.py:1 | gbs_analyzer.__version__ | PACKAGE_ROOT
ROOT_DEFINITION tizen-gbs-log-analysis/scripts/gbs_analyzer/__init__.py:3 | __version__ = "0.5.0-dev"
RUNTIME module=/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6/tizen-gbs-log-analysis/scripts/gbs_analyzer/__init__.py version=0.5.0-dev
TEST_CONTRACT tests/unit/test_package_metadata.py:5 | assert __version__ == "0.5.0-dev"
```

这不是 shim:定义文件仅 docstring 与赋值,没有转出 import。
其唯一现有定义模块就是包根。该用例锁定版本接口而非兼容壳同一性。
`__version__` 符合“以下划线开头”的字面范围,但冻结稿没有双下划线
公开元数据的豁免或分类规则。自行跳过它会缩小范围;按移除包根导出执行
则不能同时保留该接口、保持用例契约并从当前定义模块直取。

这是处置口径缺口,不是生产回归失败。不把特殊名字自动当作私有或自动豁免。

## 复现与证据

```text
/tmp/p49-a0-regression-43a6aa6/bin/python /tmp/p49-phase2-record.py private-scope-binding-refinement /tmp/p49-a0-regression-43a6aa6/bin/python /tmp/p49-phase2-private-scope-check.py
TEST_AST files=52 ImportFrom_scope_matches=1 status=PARTIAL_STOPPED_NOT_FINAL
PHASE2-02 STOP: E11-4 lexical scope includes the package-defined version API; no dunder exception has been approved.
EXIT=1
```

`private-scope-binding-refinement.command.json` 包含完整诊断程序、argv、环境、
输入 hash;同名 `.log` 是原始 stdout;
`private-scope-binding-refinement/facts.json` 包含定义/测试 sha256 与逐行位置。
诊断只枚举 ImportFrom,不能冒充最终项 2 全范围清单。

初轮 `private-scope-review.*` 按宿主模块做粗筛,额外列出了 runner 自定义的
`_safe_pkg_dir`。修正为**登记绑定**范围后排除该项:runner 只有
`discover_sibling_pythonpath` 被登记为兼容绑定,不能将整个 runner 当兼容壳。
两轮原始输出均保留,最终停止项只来自 `__version__`。

## 候选处置

1. 最小具名裁决:将 `gbs_analyzer.__version__` 登记为真实包根公开元数据,
   不纳入项 2 私有件移除;保留测试,不自动推广到其它双下划线名字。
2. 在 E11-4 明确特殊名字与普通私有名字的统一边界,按该边界重新枚举,
   每项仍留证;这是设计侧规则澄清,本轮不自行制定。

## 准备状态

- 文档修复独立提交 `f65949f` 已 push。PHASE2-01 已按批准新增
  HISTORICAL_KEY 规则关闭,但逐项归类表尚未定稿,不得称已完成登记。
- 新批准来源实测:runner.py:15 为 env 原语 re-export,import=1、Load=0,
  符合兼容壳;来源 step-0 closeout:56。应加入下一版删除清单,尚未删除。
- 历史草案仍为 13 宿主/183 绑定/11 跃迁,619 个候选乘形态命中:
  485 HISTORICAL、30 REWRITE、104 RELEASE。是**上轮粗分**,未加入本轮
  runner 或逐项 HISTORICAL_KEY,不是本轮最终数字。
- 删除清单、逐项用途归类、项 2 范围、拟删 nodeid、OBS-5 均未完成;
  人工闸门 NOT_READY。遇新缺口即停,不以部分结果申报就绪。

仅为交付留档复跑全仓,未继续准备或删除:

```text
env P49_CODE_ROOT=/tmp/p49-terminal-implementation-be73825 /tmp/p49-a0-regression-43a6aa6/bin/python /tmp/p49-phase2-record.py rulings-stop-full-regression /tmp/p49-a0-regression-43a6aa6/bin/python -m pytest /home/linhao/Toolchain/development/LogAnalysisSkill/tests -vv -p no:cacheprovider
======================= 1340 passed, 1 skipped in 25.68s =======================
EXIT=0
```

完整逐 nodeid 输出与命令/环境分别为 `rulings-stop-full-regression.log` 与
`rulings-stop-full-regression.command.json`。生产副本与文档修复提交时相同;
没有用测试通过覆盖本停止项。待裁决后继续,本轮新增停止项 1 条。
