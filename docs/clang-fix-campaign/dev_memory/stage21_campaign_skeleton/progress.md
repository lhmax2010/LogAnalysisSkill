# Stage21 Clang Campaign Skeleton

日期:2026-11-02。状态:**STOPPED_SKEL_B1_04**。
开工基线`accd7f4`,分支`clang-fix-campaign`。本批仅skill拆分及design.md追加修订登记;
完成后停止,等待设计方审读,不开始第2批。

## 1. 冻结输入与开工事实

权威:[campaign-skeleton-design-v1.3-FROZEN.md](../../campaign-skeleton-design-v1.3-FROZEN.md)。
实算SHA256:`1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`。
全文374行已通读,重点核对第0/4/6/7节与附录C。

开工时指定源`/home/toolchain/Downloads/campaign-skeleton-design-v1.3-FROZEN.md`
不存在,仓库目标位置已存在未跟踪文件。本轮没有执行移动或复制,直接保留已就位文件的
原字节并登记上述hash;不声称该移动由本轮完成,没有在Downloads创建副本。
原有`.gitignore`修改、docs下四个删除及其它未跟踪草稿均为无关工作树变更,不纳入交付。
提交署名沿用工作机配置`liushanshan <ss0217.liu@samsung.com>`。

## 2. 批次计划与边界

| 批次 | 范围 | 当前状态 |
|---|---|---|
| 1 | 第4节拆分,先derive_commit全仓验证再批量;第9节第3项修订登记;第4.4节验收 | STOPPED_SKEL_B1_04;拆分前5次已完成,derive试搬全仓出现两项非豁免失败 |
| 2 | 建档、基线复现、生命周期与放弃屏障 | NOT_STARTED |
| 3 | 审核提交、启动检查、编排skill与离线端到端 | NOT_STARTED |
| 3.5 | 经后续批准的真实gbs单包干跑,不推送/不登录QB | NOT_STARTED |
| 4 | 同包sandbox推送、QB与审核提交,另行人工授权 | NOT_STARTED |

本批不新增业务功能、不改函数体、不改断言/参数化/nodeid/运行时补丁目标;
测试只允许机械更新物理路径。历史证据目录脚本不改、不重跑。
不改/移动tizen-ci-shared的state/db.py、state/keys.py、state/records.py及
tizen-build-verify的build_verify.py;浏览器代理只移动、内容不改。
冻结稿正文不改,design.md只追加指定修订节。不推送Gerrit,不运行任何QuickBuild
真机或真实gbs命令;浏览器测试仅本机假服务器并使用现有虚拟显示入口。
任何设计未覆盖或照写失败之处停止报告,不以改测试、放宽合约或安全边界通过。

## 3. 实施裁定 SKEL-B1-01

a. 第 1 批按冻结稿第 4 节执行:八个新 Python 包的目录、文件移动、模块别名转发、三行必改 import、pyproject 与 .importlinter 改动 a–e,验收按第 4.4 节。
b. 冻结稿第 4.3 节合约引用的四个新执行包(tizen_campaign_intake、tizen_baseline_reproduce、tizen_review_submit、tizen_campaign_report)本批先建空壳:只有 __init__.py 与 __main__.py,__main__ 用 argparse 列出空的子命令集合,--help 能成功;不写 SKILL.md、不写业务代码,留给第 2、3 批。理由:依赖合约与打包在第 1 批就要生效,合约引用的包必须存在。
c. tizen-campaign-repair、tizen-sandbox-submit、tizen-qb-verify 三个搬家 skill 本批写 SKILL.md,格式照 tizen-qb-discover/SKILL.md。tizen-campaign-core 不写 SKILL.md。
d. 按冻结稿第 0.2 节,在 design.md 末尾的修订序列追加一节(版本号加一),只写该节列出的五件事,不改动任何已有条目。

## 4. 基线与证据

证据目录:`evidence/batch1/`。先执行全量collect-only、全量pytest与import-linter,
记录命令、UTC起止、exit与输出,再决定是否进入derive_commit试搬。
既有完整全仓记录2891 passed/1 skipped仅供参考,不替代本轮基线实跑。

本轮未拆分基线:

| 检查 | 命令 | exit / 结果 | 证据 |
|---|---|---|---|
| collect-only | `.venv/bin/python -m pytest --collect-only -q` | 0;2903个nodeid,零collect错误 | `baseline/collect.command.json`、`baseline/collect.stdout.log`、`baseline/nodeids.txt` |
| 全仓pytest | `.venv/bin/python tests/run_quiet.py -q --junitxml=docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/batch1/baseline/pytest.xml` | 1;2901 passed / 1 failed / 1 skipped;1012.28秒 | `baseline/pytest.command.json`、`baseline/pytest.stdout.log`、`baseline/pytest.stderr.log`、`baseline/pytest.xml`、`baseline/summary.json` |
| import-linter | `.venv/bin/lint-imports` | 0;6 kept / 0 broken | `baseline/imports.command.json`、`baseline/imports.stdout.log` |

上表路径相对`evidence/batch1/`。唯一skip为
`tests/unit/test_tizen_build_verify.py::test_case_insensitive_bypass_is_platform_specific`,
原因`case-sensitive filesystem`。未拆分后对照不存在,不把这项声明为“零新增skip”的拆分验收。
生产代码、测试、打包/导入配置及design.md无diff;冻结稿、安全核心与代理完整/前缀hash
不变,复核见`evidence/batch1/baseline/unchanged-at-stop.json`。

## 5. 验收台账

| 项目 | 状态 |
|---|---|
| 拆分前后nodeid比较/collect/skip | PARTIAL;基线与derive试搬均2903个nodeid,双向差集为空,collect exit 0,相同1 skip;最终八包对照未执行。`derive-only/nodeid-diff.json`、`gate-comparison.json` |
| 每个旧模块名与新模块对象同一性 | PARTIAL;derive模块对象同一性已直接验证,其余未搬/未新增别名测试。`derive-only/integrity.json` |
| 新权威源码植入禁止调用,既有静态检查红例 | NOT_RUN_STOPPED;尚未搬静态检查对应的生产模块 |
| import-linter全绿与a/b/d/e红例(e直接/间接两例) | PARTIAL;原6合约基线与试搬均6 kept/0 broken,八包合约及红例未实施。`derive-only/imports.stdout.log` |
| .mjs完整hash/前缀hash、四组安全测试 | PARTIAL;原位置hash不变,未迁移/未在新位置重跑。`derive-only/integrity.json` |
| 干净wheel安装、八入口全部子命令help、资源hash | NOT_RUN_STOPPED;尚未拆包 |
| 全仓pytest对照 | FAILED;基线2901 passed/1豁免failed/1 skipped,derive试搬2900 passed/2非豁免failed/1 skipped。`derive-only/pytest.xml`、`summary.json`、`gate-comparison.json` |

上表证据相对`evidence/batch1/`,只记录试搬事实,不表示八包拆分通过。
冻结稿第4.4节第7项“历史证据目录脚本不改、不重跑”遵守;
七项交付验收按原任务顺序在上表列出(全仓对照列为交付第7项)。
测试物理路径改动清单:0条,未修改任何测试,详见第9.2节。当前停止报告见第9节;
第6节保留上轮停止历史。

## 6. 停止报告 SKEL-B1-02:未拆分基线失败

状态:已由SKEL-B1-03裁定处置;以下保留当时事实。

在任何模块移动、包配置修改或测试路径修改之前,全量基线出现失败:
`tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures`。
本次本机假服务器调查运行完成前8个场景,在`configuration-redirect-307`场景中
记录`AGENT_STOPPED / FETCH_CONTINUE_FAILED`,随后`harness_failure`为
`TargetClosedError / OTHER_FRAMEWORK_ERROR`,Node入口以`INVESTIGATION_STOPPED AssertionError`
结束。该记录是现象,不把场景名当成已证实根因,也不声称已经排除时序问题。

证据:[停止报告](evidence/batch1/stop-report.md)、
[场景原始结构化输出](evidence/batch1/baseline/c8-investigation/configuration-redirect-307.json)、
[Node stdout](evidence/batch1/baseline/c8-investigation/node.stdout.txt)、
[Node stderr](evidence/batch1/baseline/c8-investigation/node.stderr.txt)。
这些是本轮全量pytest产生的本机合成数据,不是重跑历史证据目录中的脚本。

按本批停止纪律,不搬derive_commit、不进入批量搬家、不改测试断言或代理。
不追加声称拆分已落地的design.md修订;SKEL-B1-01(d)仍待实施。
候选后续:由设计方先批准独立离线定位/修复该基线失败,在干净的同一输入上重建
全绿基线后再执行本批;若拟接受既有失败,须另给出明确验收裁定,本轮不自行接受。
全量基线已完整结束:exit 1,2901 passed / 1 failed / 1 skipped,无其它失败。
此次交付仅冻结输入登记、INDEX、进度与证据;没有拆分实现,没有design.md修订。

提交检查:`git diff --cached --check`仅报告原始pytest输出的两处尾随空白:
`baseline/pytest.stdout.log:80`与`baseline/pytest.xml:36`的`E         `行。
保留原始字节,不对测试输出做格式化;排除这两份原始输出后的检查通过。
未纳入任何开工前已有的无关工作树变更。

## 7. 实施裁定 SKEL-B1-03:基线失败处置

1. SKEL-B1-02 停止成立。失败用例 tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures 是 C8 离线调查脚本(3ef39c2 引入),不是功能验收用例;其 configuration-redirect-307 场景对时序敏感,与 P5Q 收口文档中"live-01 提交后读取失败根因未定"属同一遗留项。本批不修复、不改该测试、不加 skip 或 xfail 标记。
2. 第 4.4 节第 1、7 条的验收口径调整为:除上述一个 nodeid 外,拆分前后全部用例都必须通过;该 nodeid 仍须被收集(nodeid 集合比较照常),其结果单独按第 3 项判断。
3. 该用例的单独判定:拆分前、拆分后各单独连续运行 5 次(只跑这一个 nodeid,每次输出目录分开)。每次记录通过或失败,失败时记录失败场景名、harness_failure 的 class_name 与 category、AGENT_STOPPED 的 failure_category。拆分后若出现拆分前 5 次中没有出现过的失败形态(新的失败场景、不同的错误类或类别),或拆分前 5 次全部通过而拆分后出现失败,即停止并报告;否则视为与基线一致。
4. 该用例连同其 Node 调查脚本按冻结稿第 4.4 节第 2 条允许机械更新 .mjs 导入路径,与其它测试同样处理并逐条登记。
5. 冻结稿已在目标位置、Downloads 无源文件,未执行移动;sha256 1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9 与设计方发出的文件一致,登记即可。

本轮续做基线`f203aec`。先按序执行5次单nodeid测试,各次证据位于
`evidence/batch1/baseline/flaky-pre/run-01`至`run-05`,不改测试、代理或其它生产文件。

### 7.1 拆分前5次结果

| 次数 | exit | 结果 | 失败场景 | class_name / category / AGENT_STOPPED.failure_category |
|---|---|---|---|---|
| 1 | 0 | PASS | 无 | 无 |
| 2 | 1 | FAIL | racing-meta-refresh | TargetClosedError / OTHER_FRAMEWORK_ERROR / FETCH_CONTINUE_FAILED |
| 3 | 0 | PASS | 无 | 无 |
| 4 | 0 | PASS | 无 | 无 |
| 5 | 0 | PASS | 无 | 无 |

每次命令、时间、输出与场景JSON分别在上述`run-NN`目录;
汇总:`evidence/batch1/baseline/flaky-pre/summary.json`。五次连续运行时生产与测试文件无改动。
拆分后只与这五次的失败形态比较,不使用SKEL-B1-02的更早记录扩大豁免。

## 8. derive_commit试搬

仅移动`derive_commit.py`到`tizen-campaign-core/scripts/tizen_campaign_core/`,函数体不改。
旧位置改为`sys.modules[__name__] = _implementation`模块别名。
只新增core的`__init__.py`及pyproject的包发现/mypy路径登记,其它模块和测试未改。
全仓结果已归档在`evidence/batch1/derive-only/`,判定未通过,不批量搬家。

环境准备:首次`pip install --no-deps --no-build-isolation -e .`因当前虚拟环境缺少
`setuptools.build_meta`失败(exit 2)。安装pyproject已有构建依赖
`setuptools>=69`和`wheel`(实装84.2.1/0.48.0)后,相同editable安装成功(exit 0);
依赖声明没有改动。试搬前置已直接确认`ci_triage.derive_commit is
tizen_campaign_core.derive_commit`。仅测试本机假服务器,未访问真实QuickBuild/Gerrit。

结果:全量exit 1,2900 passed / 2 failed / 1 skipped,pytest报告1422.74秒;
命令包装器总耗时1425.10秒。两项失败均不属于SKEL-B1-03豁免,因此停止,不批量搬家。
C8豁免nodeid在这次全仓运行中为PASS,但此结果不能替代最终拆分后5次独立运行。
后5次全部NOT_RUN_STOPPED,不能给出“与基线一致”的验收结论。

## 9. 停止报告 SKEL-B1-04:derive试搬的非豁免失败

报告:[stop-report-SKEL-B1-04.md](evidence/batch1/stop-report-SKEL-B1-04.md)。
失败均为`tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass`
的参数实例,在第98行`assert 0 <= close_seconds < 5`失败:

| 参数 | 阶段与业务返回 | 关闭到CLI退出 | 现场证据 |
|---|---|---|---|
| build | 假服务器qb-trigger exit 0,submitted_bound | 14.4371337890625秒 | `derive-only/c5a-failures/build/commands.json`、`agent-0.json`、`server-requests.json` |
| no-navigation | 假服务器首次qb-result-fetch exit 0,RUNNING | 8.79266881942749秒 | `derive-only/c5a-failures/no-navigation/commands.json`、`agent-1.json`、`server-requests.json` |

上表路径相对`evidence/batch1/`。原始完整失败输出:
`derive-only/stdout.log`和`derive-only/pytest.xml`;命令及UTC起止/exit:
`derive-only/command.json`。没有重跑失败项、改阈值、加豁免或修改测试。
候选后续是由设计方批准独立离线定位关闭时延,比较未拆分树与试搬树在可比环境下
的代理close/进程退出/Python返回;根因明确后决定修复或验收裁定。本轮不自行
认定是环境负载、拆分回归或既有关闭缺陷。

### 9.1 对照结论

| 项目 | 未拆分基线 | derive-only试搬 | 判定 |
|---|---|---|---|
| 全量pytest | 2901 passed/1 failed/1 skipped | 2900 passed/2 failed/1 skipped | 豁免外失败由0变2,必须停止 |
| C8单nodeid的5次独立运行 | PASS/FAIL/PASS/PASS/PASS,形态见7.1 | 未执行 | 尚未到最终拆分后验收 |
| nodeid集合 | 2903 | 2903 | 试搬双向差集为空,零collect错误 |
| skip | case_sensitive平台用例1项 | 同一项、同一原因 | 试搬零新增skip |
| import-linter | 6 kept/0 broken | 6 kept/0 broken | 只证明原合约;新合约尚未实施 |
| 冻结稿/安全核心/代理hash | 基线登记值 | 全部相同 | `derive-only/integrity.json` |

`derive_commit.py`移动前后完整hash均为
`85265e38bef100e41b8a4d29e99fd44d0417febddecc64fbfe1ec64f0084dbd0`。
代理完整hash仍为`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`,
前缀hash仍为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`。

### 9.2 测试物理路径改动清单与未完成项

清单为空,共0条:`git diff f203aec -- tests`为空。未改变任何断言、参数化集合、
nodeid、补丁目标或skip标记。历史证据目录下脚本未改、未重跑。
只保留derive模块试搬、core初始化文件、旧模块别名与pyproject对应四处登记。
其余模块、三份SKILL、七执行入口、import-linter新增合约、wheel验收均未实施;
`design.md`未改,SKEL-B1-01(d)追加修订仍待批量拆分完成后实施。
没有访问真实QuickBuild/Gerrit,没有运行真实gbs或新增业务功能。

### 9.3 提交前检查

`git diff --cached --check` exit 2,仅4份原始pytest输出的22行尾随空白:
`baseline/flaky-pre/run-02/{pytest.xml,stdout.log}`与
`derive-only/{pytest.xml,stdout.log}`。按既有做法保留原始字节,不格式化证据;
排除这4份原始输出的检查exit 0。逐行清单、命令与结果:
`evidence/batch1/derive-only/diff-check.json`。
此次提交为停止点快照,不是第1批验收通过;不纳入开工前已有的无关工作树变更。
