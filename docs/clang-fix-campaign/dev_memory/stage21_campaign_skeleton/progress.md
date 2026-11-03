# Stage21 Clang Campaign Skeleton

日期:2026-11-03。状态:**BATCH1_READY_FOR_REVIEW**。
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
| 1 | 第4节拆分,先derive_commit全仓验证再批量;第9节第3项修订登记;第4.4节验收 | READY_FOR_REVIEW;最终树2921 passed/1 skipped,C8后5次全PASS;等待设计方审读 |
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
| 拆分前后nodeid比较/collect/skip | PASS;旧2903个全部保留,新增19个别名用例;最终树仅原有1 skip,零新增skip。`bulk/nodeid-diff-final.json`、`bulk/skip-comparison.json` |
| 每个旧模块名与新模块对象同一性 | PASS;19 passed。`bulk/aliases.stdout.log` |
| 新权威源码植入禁止调用,既有静态检查红例 | PASS;植入后1 failed,恢复后183 passed。`source-mutant/` |
| import-linter全绿与a/b/d/e红例(e直接/间接两例) | PASS;7 kept/0 broken,五个违规样本均变红且已移除。`bulk/imports-after-cli.stdout.log`、`import-mutants/` |
| .mjs完整hash/前缀hash、四组安全测试 | PASS;字节不变、新位置4/4。`bulk/integrity-final.json`、`bulk/safety-four.stdout.log` |
| 干净wheel安装、八入口全部子命令help、资源hash | PASS;最终wheel在无源码路径venv中8入口21次help成功,资源hash一致。`wheel-final/summary.json` |
| 全仓pytest对照 | PASS(按SKEL-B1-03/05);试搬复核2902/0/1,批量两次均2921/0/1;C8后5次全PASS,无新增失败形态。`derive-recheck/`、`final-gate/`、`final-gate-2/`、`flaky-post/` |

上表证据相对`evidence/batch1/`,七项均完成;本批等待设计方审读,不自行标CLOSED。
冻结稿第4.4节第7项“历史证据目录脚本不改、不重跑”遵守;
七项交付验收按原任务顺序在上表列出(全仓对照列为交付第7项)。
测试物理路径改动清单:28条,见第11.2节;另有活动spike8条。
第6、9节保留原始停止历史,不以重跑覆盖。

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

状态:已按SKEL-B1-05对照结果a处置,原始失败事实与证据保留,不以重跑结果替换。

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

## 10. 实施裁定 SKEL-B1-05:关闭时延失败处置

1. SKEL-B1-04 停止成立。设计方已审读试搬改动(derive_commit 原样移动、旧位置模块别名、pyproject 两行)与失败证据。两例失败中,代理自身记录的关闭耗时分别约 6.5 秒、8.7 秒(close_started/close_finished),即时间耗在浏览器关闭本身,不在派生提交代码路径上;试搬全仓耗时 1423 秒,未拆分基线 1012 秒。初步判断为机器负载导致的计时超限,须经第二步对照确认,本裁定不据此放行。
2. 不修改测试、不提高 5 秒阈值、不加 skip/xfail;原始失败证据保留,不得用重跑结果替换。
3. 设立"计时敏感用例清单",初始为:tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures(处置按 SKEL-B1-03),以及 tests/unit/test_p5q_c5a_integration.py 中 test_real_cli_browser_submit_bind_pending_pass 的全部参数。清单只能由设计方裁定增删。
4. 第 1 批后续每次全仓门禁:清单外任一用例失败 → 立即停止;C5a 清单用例失败 → 在当前树上单独重跑该 nodeid 3 次,3 次全部通过才算门禁通过,任一次失败即停止;C8 用例按 SKEL-B1-03 第 3 项。每次全仓运行前后记录 /proc/loadavg、CPU 核数,以及运行开始时 CPU 占用前 10 的进程(只记进程名与占用,不记命令行参数)。

### 10.1 计时敏感用例清单

仅登记本裁定指定范围,不得自行增删:

- `tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures`,按SKEL-B1-03第3项。
- `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]`。
- `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[error-created]`。
- `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[error-no-build]`。
- `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[no-navigation]`。
- `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[delayed-build]`。
- `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[late-build]`。

### 10.2 两树关闭时延对照计划

当前试搬树`3ea6e7c`,临时未拆分worktree固定在`f203aec`。
两树用当前仓库同一`.venv/bin/python`与同一Playwright/Chromium;
分别按各树的pyproject包目录设置PYTHONPATH,核对实际模块路径后开始。
对`build`和`no-navigation`各交替执行未拆分/试搬3轮,每次独立输出目录。
证据:`evidence/batch1/close-timing/`;保留各次loadavg、命令、UTC起止、exit、
原始pytest输出、CLI与代理关闭时间。本步骤不修改生产、测试或配置文件。
只有两树12次全部通过才进入第三步;未拆分也失败判b,只有试搬失败判c。
结束后移除本次创建的worktree,检查P5Q进程与`/dev/shm/p5q-browser-*`残留。

### 10.3 对照结果与判定

12次均PASS,按裁定第2步第3项a登记为环境负载,允许进入第3步的试搬全仓复核。
两树均未修改生产、测试、配置;同一venv、Playwright与Chromium,实际模块路径
分别指向两树,见`close-timing/unsplit-environment.json`与`derive-environment.json`。
CPU逻辑核数20。下表时间单位秒,每格三个值依次为trigger、首次fetch、终态fetch;
load为运行前/后的1、5、15分钟值。绝对close_started/close_finished时间戳在
各运行`run.json`和`node/<mode>/agent-*.json`中保留。

| 次序 | 树 | nodeid参数/轮次 | 结果 | close_to_cli_exit | 代理close耗时 | load前 / 后 |
|---|---|---|---|---|---|---|
| 1 | f203aec未拆分 | build/1 | PASS | 0.074,0.075,0.073 | 0.038,0.036,0.038 | 0.92 0.98 0.68 / 0.83 0.95 0.68 |
| 2 | 3ea6e7c试搬 | build/1 | PASS | 0.075,0.074,0.077 | 0.046,0.038,0.042 | 0.83 0.95 0.68 / 0.92 0.97 0.69 |
| 3 | f203aec未拆分 | build/2 | PASS | 0.078,0.077,0.080 | 0.046,0.036,0.039 | 0.92 0.97 0.69 / 1.04 0.99 0.71 |
| 4 | 3ea6e7c试搬 | build/2 | PASS | 0.075,0.077,0.076 | 0.042,0.041,0.039 | 1.04 0.99 0.71 / 1.89 1.21 0.79 |
| 5 | f203aec未拆分 | build/3 | PASS | 0.079,0.075,0.074 | 0.040,0.039,0.038 | 1.89 1.21 0.79 / 1.58 1.19 0.80 |
| 6 | 3ea6e7c试搬 | build/3 | PASS | 0.077,0.076,0.079 | 0.042,0.039,0.043 | 1.58 1.19 0.80 / 1.43 1.18 0.80 |
| 7 | f203aec未拆分 | no-navigation/1 | PASS | 0.080,0.074,0.076 | 0.038,0.039,0.038 | 1.43 1.18 0.80 / 0.94 1.15 0.83 |
| 8 | 3ea6e7c试搬 | no-navigation/1 | PASS | 0.078,0.076,0.075 | 0.043,0.039,0.036 | 0.94 1.15 0.83 / 1.15 1.14 0.86 |
| 9 | f203aec未拆分 | no-navigation/2 | PASS | 0.077,0.078,0.077 | 0.042,0.039,0.043 | 1.15 1.14 0.86 / 0.94 1.01 0.83 |
| 10 | 3ea6e7c试搬 | no-navigation/2 | PASS | 0.079,0.075,0.075 | 0.039,0.045,0.042 | 0.94 1.01 0.83 / 0.98 1.11 0.89 |
| 11 | f203aec未拆分 | no-navigation/3 | PASS | 0.076,0.079,0.076 | 0.043,0.037,0.038 | 0.98 1.11 0.89 / 0.42 0.88 0.82 |
| 12 | 3ea6e7c试搬 | no-navigation/3 | PASS | 0.080,0.077,0.079 | 0.043,0.040,0.038 | 0.42 0.88 0.82 / 0.59 0.79 0.79 |

证据根:`evidence/batch1/close-timing/`;汇总`runs.json`、`decision.json`。
临时worktree`/tmp/loganalysisskill-skel-b1-f203aec-20261103`运行后为clean,
`git worktree remove` exit 0;路径已不存在,P5Q进程与profile均为空,
见`worktree-cleanup.json`和`residue-after-tests.json`。
初始化编排时有一次进程检查误把自身shell中的脚本文本当成Chromium,测试尚未启动;
只修正编排检查为实际exe与argv匹配,见`setup-precheck-false-positive.json`。
未改生产或测试,未因此删除任何进程/目录。

### 10.4 试搬全仓复核

证据:`evidence/batch1/derive-recheck/`。保持当前derive试搬源码不变。
沿用`tests/run_quiet.py`的虚拟显示入口;外置pytest观察插件只在清单外失败时
设置停止标志,不修改报告、断言、阈值或skip。运行前后记录loadavg与CPU核数,
开始时只记录CPU前10进程名和占用。全仓结果及必要的独立复跑另行登记。

复核完成:exit 0,2902 passed/0 failed/1 skipped,1030.30秒(编排总计1030.68秒)。
UTC 2026-11-03 00:37:04.692515至00:54:15.386068;CPU 20核,
load前`0.66 0.80 0.80`,后`2.08 1.85 1.50`;CPU前10名单见`cpu-top10.txt`。
C5a六参数与C8调查用例均通过,没有触发3次独立复跑。唯一skip与基线相同,
`test_case_insensitive_bypass_is_platform_specific`(case-sensitive filesystem)。
证据:`command.json`、`summary.json`、`pytest.xml`、`pytest.stdout.log`、
`load-before.json`、`load-after.json`;编排与观察插件原文分别为
`gate-runner.py.txt`、`gate-observer.py.txt`,本轮运行的是外置`/tmp`版本。
此结果只放行批量搬家,不替代最终八包验收或拆分后C8五次对照。
`git diff --check`的告警仅为本地假页面原始HTML的行尾空白,保留证据字节;
文档无空白告警。不纳入pytest-cache,不提交数据库二进制。

## 11. 批量搬家实施与验收记录

### 11.1 实施范围

继59d2e36的试搬全仓复核通过后,按第4.2节归属表完成19个Python模块的所有权迁移,
旧ci_triage位置均为模块对象别名,没有星号转发。core共8模块、repair共1模块、
sandbox共1模块、qb-verify共9模块;新增lifecycle/reproduce业务留给后批,本批未实现。
新包不导入ci_triage;三个qb模块的sandbox依赖指向tizen_sandbox_submit。
搬家文件仅改import,非import AST与f203aec一致,见`bulk/integrity.json`。

七个执行包均有入口;repair/sandbox/qb沿用既有CLI的参数与处理函数,
ci_triage旧入口、verify子包及运行时patch目标保持。intake/baseline/review/report
只有__init__.py与空子命令集合的__main__.py,没有业务代码或SKILL。
三份搬家SKILL采用qb-discover的输入/输出/错误/命令格式;core不写SKILL。
pyproject登记八包发现、mypy路径与包名、qb的.mjs资源;.importlinter保留原六合约并
新增campaign-no-direct-build。CI显式mypy列表、README与开发工作流的源码路径同步。
design.md仅追加4.6节v1.5.25的五条登记,既有条目与冻结稿正文不改。

### 11.2 物理路径改动清单

既有测试28条(24文件),活动spike8条(7文件),合计36条。下表逐条列出原文件行号;
所有改动仅将`tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs`或
`qb_browser.py`的前缀替换为`tizen-qb-verify/scripts/tizen_qb_verify/`。
完整before/after原文见`evidence/batch1/bulk/physical-path-changes.json`。
既有测试断言、参数化、nodeid、补丁目标不变;历史证据脚本不改、不重跑。
另新增19参数的`tests/unit/test_campaign_module_aliases.py`,不改既有测试逻辑。

| 序号 | 文件:原行号 | 类别 | 路径目标 |
|---|---|---|---|
| 1 | `docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs:15` | 活动spike | Node代理 |
| 2 | `docs/clang-fix-campaign/spikes/p5q_c2b_form_diagnostics.mjs:5` | 活动spike | Node代理 |
| 3 | `docs/clang-fix-campaign/spikes/p5q_c2b_form_diagnostics_test.mjs:10` | 活动spike | Node代理 |
| 4 | `docs/clang-fix-campaign/spikes/p5q_c2b_form_diagnostics_test.mjs:38` | 活动spike | Node代理 |
| 5 | `docs/clang-fix-campaign/spikes/p5q_c2b_intrinsics.mjs:20` | 活动spike | Node代理 |
| 6 | `docs/clang-fix-campaign/spikes/p5q_c5_tools.mjs:6` | 活动spike | Node代理 |
| 7 | `docs/clang-fix-campaign/spikes/p5q_compare_raw_active.mjs:4` | 活动spike | Node代理 |
| 8 | `docs/clang-fix-campaign/spikes/p5q_fill_rehearsal.mjs:5` | 活动spike | Node代理 |
| 9 | `tests/fixtures/p5q_node_entry.py:11` | 既有测试 | Node代理 |
| 10 | `tests/node/p5q_c2b_safety.mjs:8` | 既有测试 | Node代理 |
| 11 | `tests/node/p5q_c2c_raw_bytes_probe.mjs:7` | 既有测试 | Node代理 |
| 12 | `tests/node/p5q_c2c_raw_bytes_probe.mjs:34` | 既有测试 | Node代理 |
| 13 | `tests/node/p5q_c8_investigation.mjs:5` | 既有测试 | Node代理 |
| 14 | `tests/node/p5q_cli_agent.mjs:4` | 既有测试 | Node代理 |
| 15 | `tests/node/p5q_fake_quickbuild.mjs:8` | 既有测试 | Node代理 |
| 16 | `tests/node/p5q_h_interception_probe.mjs:8` | 既有测试 | Node代理 |
| 17 | `tests/node/p5q_hung_cdp_agent.mjs:4` | 既有测试 | Node代理 |
| 18 | `tests/node/p5q_login_retry.mjs:7` | 既有测试 | Node代理 |
| 19 | `tests/node/qb_browser_lifecycle.mjs:2` | 既有测试 | Node代理 |
| 20 | `tests/node/test_p5q_c2b_config_source.mjs:4` | 既有测试 | Node代理 |
| 21 | `tests/node/test_p5q_c5_tools.mjs:5` | 既有测试 | Node代理 |
| 22 | `tests/node/test_p5q_c5b_failure_evidence.mjs:6` | 既有测试 | Node代理 |
| 23 | `tests/node/test_qb_agent_source_guards.mjs:9` | 既有测试 | Node代理 |
| 24 | `tests/node/test_qb_agent_source_guards.mjs:10` | 既有测试 | Python驱动 |
| 25 | `tests/node/test_qb_browser_agent.mjs:6` | 既有测试 | Node代理 |
| 26 | `tests/node/test_qb_browser_agent.mjs:452` | 既有测试 | Node代理 |
| 27 | `tests/node/test_qb_browser_fields.mjs:11` | 既有测试 | Node代理 |
| 28 | `tests/node/test_qb_browser_runtime.mjs:8` | 既有测试 | Node代理 |
| 29 | `tests/node/test_qb_browser_trusted.mjs:10` | 既有测试 | Node代理 |
| 30 | `tests/node/test_qb_failure_categories.mjs:5` | 既有测试 | Node代理 |
| 31 | `tests/node/test_qb_login_facts.mjs:4` | 既有测试 | Node代理 |
| 32 | `tests/unit/test_p5q_c6_offline_fix.py:31` | 既有测试 | Node代理 |
| 33 | `tests/unit/test_qb_browser.py:551` | 既有测试 | Node代理 |
| 34 | `tests/unit/test_qb_browser.py:681` | 既有测试 | Python驱动 |
| 35 | `tests/unit/test_qb_browser_node.py:234` | 既有测试 | Python驱动 |
| 36 | `tests/unit/test_qb_driver_budget.py:286` | 既有测试 | Node代理 |

### 11.3 已完成的离线验收

以下证据均相对`evidence/batch1/`:

- collect:2922个nodeid,旧2903个全部存在,missing为空,added恰为19个别名用例;
  `bulk/collect.stdout.log`、`bulk/nodeids.txt`、`bulk/nodeid-diff.json`。
- 别名测试19 passed:`bulk/aliases.stdout.log`。旧新模块对象相同。
- import-linter:7 kept/0 broken;`bulk/imports-final.stdout.log`。
  a/b/d/e五个红例(含e直接、间接)均exit 1,详见`import-mutants/`;
  临时违规文件均已删除,未改安全核心。
- 新权威代理源码植入`arbitraryAlias.evaluate`后既有静态检查变红(1 failed),
  移除后既有源码护栏183 passed/0 failed/0 skipped:`source-mutant/`。
- 代理完整SHA256为`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`,
  前缀为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`,
  均与原位置相同;`bulk/integrity.json`。
- 新位置安全四组4/4通过(pytest入口1 passed):`bulk/safety-four.stdout.log`。
  Worker组走允许的b分支(browser_fail_closed),shared_worker关闭成功、worker关闭错误;
  攻击HTTP与WS均0、profile删除。307/308、凭据隔离、逐跳拦截各组通过。
- 新包mypy:34个文件通过;改动Python范围ruff通过;design检查器0 problem:
  `bulk/mypy-new.stdout.log`、`bulk/ruff.stdout.log`、`bulk/design-check.stdout.log`。
- wheel:干净虚拟环境无源码sys.path,core可导入,8入口21次help均exit 0;
  wheel及安装位置的代理hash等于源码:`wheel/summary.json`、`wheel/commands.json`。
  首次venv创建因系统Python缺ensurepip失败,原stdout保留;用标准
  `venv --without-pip`和既有pip的`--python <新venv>`安装wheel后完成验收,
  未加系统site-packages、未装editable、未改变项目依赖。
- 批量搬家首轮全仓`final-gate/`:2921 passed/0 failed/1 skipped,1020.49秒,
  UTC 01:07:09至01:24:10。C5a六参数与C8均通过,未触发单独重跑;
  load、CPU核数及起始CPU前10记录在该目录,原始证据保留。
- 全包mypy首跑发现旧CLI从模块别名壳取类型导致21条静态错误;
  按旧CLI转发到新位置的要求,其6处import改为权威模块,函数体/参数/旧入口保留。
  repair原有build-verify包根导入也改为同对象的build_verify子模块导入,
  满足本批新包只用子模块写法的约束;没有新增跨包依赖或修改测试。
  原失败输出`bulk/mypy-all.stdout.log`保留;调整后全包153文件mypy通过,
  ruff与7条合约通过:
  `bulk/{mypy-all-final,ruff-final,imports-after-cli}.stdout.log`。
- 按最终代码重建wheel,再次8入口21次help通过,资源hash相同:
  `wheel-final/summary.json`。初次wheel的环境问题与验收仍原样保留。
- 最终树全仓已通过:`final-gate-2/`,2921 passed/0 failed/1 skipped,
  1023.81秒。唯一skip与基线同nodeid、同原因;对照为`bulk/skip-comparison.json`。
  拆分后C8五次对照已完成,见第11.5节。

### 11.4 本轮全仓门禁与负载

均使用同一venv、虚拟显示与外置只观察失败的pytest插件,不修改测试结果。
逻辑CPU核数均20,每次起始CPU前10(仅进程名/占用)在相应目录的`cpu-top10.txt`。

| 树/证据目录 | UTC起止 | pytest通过/失败/跳过 | pytest秒数 | load前(1/5/15分钟) | load后(1/5/15分钟) | 清单结果 |
|---|---|---|---|---|---|---|
| derive-recheck | 00:37:04-00:54:15 | 2902/0/1 | 1030.30 | 0.66/0.80/0.80 | 2.08/1.85/1.50 | C5a六参数与C8均PASS;不触发重跑 |
| final-gate | 01:07:09-01:24:10 | 2921/0/1 | 1020.49 | 1.83/1.34/1.39 | 1.37/1.13/1.22 | C5a六参数与C8均PASS;不触发重跑 |
| final-gate-2(最终代码) | 01:24:50-01:41:54 | 2921/0/1 | 1023.81 | 0.76/1.01/1.17 | 1.39/1.20/1.19 | C5a六参数与C8均PASS;不触发重跑 |

日期均2026-11-03。每次的`command.json`、`summary.json`、`pytest.xml`、
`pytest.stdout.log`、`load-before.json`、`load-after.json`保留原始结果。
没有清单外失败,没有触发C5a单独3次补跑。第7.1节拆分前C8五次与
拆分后独立五次的判定单独登记,不以本表的全仓PASS代替。

### 11.5 C8拆分后独立五次与基线比较

只跑原nodeid,每次独立目录,未改测试/阈值/skip/xfail。下表耗时为命令包装器秒数。

| 次数 | 拆分前结果 | 拆分后结果 | 后次耗时 | 后次失败形态 | 证据 |
|---|---|---|---|---|---|
| 1 | PASS | PASS | 182.787 | 无 | `flaky-post/run-01/` |
| 2 | FAIL(racing-meta-refresh) | PASS | 182.070 | 无 | `flaky-post/run-02/` |
| 3 | PASS | PASS | 181.985 | 无 | `flaky-post/run-03/` |
| 4 | PASS | PASS | 181.609 | 无 | `flaky-post/run-04/` |
| 5 | PASS | PASS | 181.970 | 无 | `flaky-post/run-05/` |

拆分前唯一形态仍为第7.1节的`racing-meta-refresh / TargetClosedError /
OTHER_FRAMEWORK_ERROR / FETCH_CONTINUE_FAILED`。后五次没有失败形态,
按SKEL-B1-03第3项判定与基线一致;
`flaky-post/summary.json`、`flaky-post/decision.json`与各次`node/`保存原始记录。
不声称C8既有时序问题已修复,也不把较早全仓的configuration-redirect-307形态
加入这五次基线的豁免范围。

### 11.6 最终交付核对

- 最终collect exit 0,2922个nodeid,基线减最终的差集为空;反向增加仅19个别名测试。
  两份列表为`baseline/nodeids.txt`与`bulk/nodeids-final.txt`,差集为
  `bulk/nodeid-diff-final.json`;零collect错误、零新增skip。
- 原六合约保留,第七条及新层级均生效:基线6 kept/0 broken,最终7 kept/0 broken;
  a/b/d/e五次红例各exit 1,临时违规文件已移除,恢复后合约全绿。
- 最终非import AST核对含旧CLI,19模块和旧CLI逻辑不变;
  `bulk/integrity-final.json`、`bulk/moved-module-import-diffs.patch`。
  安全核心、冻结稿、代理完整/前缀hash不变;design.md既有文本逐字不变,
  仅插入4.6修订节。最终设计检查器0 problem:
  `bulk/design-check-final.stdout.log`。
- 进程与临时资源检查:本次对照worktree已不存在,P5Q进程与
  `/dev/shm/p5q-browser-*`均为空。仅删除本次创建的两个wheel验收目录,
  未处理其它历史worktree或其它用户资源:
  `bulk/cleanup-final.json`。wheel验收命令、安装路径与资源hash已完整归档。
- 与冻结稿或裁定不一致、做不到的地方:无。保留C8基线时序问题原处置,
  本批未修复它;系统缺ensurepip的环境准备问题已用标准干净venv方式解决。
- 提交前diff检查:代码与文档exit 0;含原始证据时exit 2,仅为测试输出、
  HTML与补丁上下文的行尾空白或末尾空行,保留原始字节不改。
  完整输出见`bulk/diff-check-final.json`。
- 本批提交后停止,等待设计方审读;第2、3、3.5、4批均未开始。
