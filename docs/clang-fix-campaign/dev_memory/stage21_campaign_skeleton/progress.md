# Stage21 Clang Campaign Skeleton

日期:2026-11-03。状态:**STOPPED_SKEL_R_05**;SKEL-R-02诊断已验收,SKEL-R-04新停止规则与三个不可改既有断言冲突,等待裁定。
第1批开工基线`accd7f4`,第2批开工基线`5b9ecea`,分支`clang-fix-campaign`。
第1批已由SKEL-B2-01验收;第2批已由SKEL-B3-01验收;第3批已由SKEL-R-01验收。

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
| 1 | 第4节拆分,先derive_commit全仓验证再批量;第9节第3项修订登记;第4.4节验收 | ACCEPTED;SKEL-B2-01验收通过 |
| 2 | 建档、基线复现、生命周期与放弃屏障,CLI解析去重 | ACCEPTED;SKEL-B3-01验收通过 |
| 3 | 审核提交、启动检查、编排skill与离线端到端 | ACCEPTED;SKEL-R-01验收,3087 passed/1 skipped |
| 3.5 | 经后续批准的真实gbs单包干跑,不推送/不登录QB | NOT_STARTED |
| 4 | 同包sandbox推送、QB与审核提交,另行人工授权 | NOT_STARTED |

第1批边界(历史记录):不新增业务功能、不改函数体、不改断言/参数化/nodeid/运行时补丁目标;
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

## 12. 实施裁定 SKEL-B2-01:第 1 批验收与第 2 批范围

1. 第 1 批验收通过。设计方已逐个比对 18 个搬迁模块与 3ea6e7c 原文件(仅 import 行不同)、旧位置别名、三行必改 import、.importlinter 新合约与 a/b/d/e 红例输出、代理 sha256、安全核心零改动、design.md 第 4.6 节、nodeid 前后比较、wheel 汇总与最终全仓汇总。
2. 补登记:8 个 docs/clang-fix-campaign/spikes/ 下脚本的 .mjs 物理路径更新,性质同测试物理路径机械改动,予以认可。
3. 第 2 批须修:各执行包的 __main__ 与 ci_triage/cli.py 对 qb-trigger、qb-result-fetch、sandbox-submit、campaign-repair-step 各有一份独立的参数解析副本。改为 ci_triage/cli.py 的这些子命令直接调用对应执行包入口中的同一函数,只保留一份解析代码;新增测试断言两种入口对同一非法参数输出相同的 JSON 与退出码。
4. 第 2 批范围:冻结稿第 7 节第 2 批(5.1 建档、5.2 基线复现、5.4 生命周期最小版与放弃屏障,含 sandbox-submit 与 qb-trigger 的屏障检查),以及 tizen-campaign-intake、tizen-baseline-reproduce、tizen-campaign-report 的 SKILL.md(格式照 tizen-qb-discover/SKILL.md)和本裁定第 3 项。campaign-start-check 归第 3 批,本批只在 tizen-campaign-intake 中保留其位置。

### 12.1 第2批开工与边界

- 基线`5b9ecea`,冻结稿实算SHA256仍为
  `1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`。
- 重读冻结稿第0、3、5、6节与附录C,以及本进度的既有裁定、停止记录和验收。
- 本批只做离线/本机测试;不改安全核心、冻结稿、代理.mjs,不访问真实
  QuickBuild/Gerrit,不运行真实gbs,不写既有真机状态库。
- 全仓门禁沿用SKEL-B1-05清单与负载记录;保留第1批2922个nodeid,
  新用例单列。review-submit和campaign-start-check相关验收留第3批。
- 现有用户工作树变更原样保留,不纳入本批。证据根为`evidence/batch2/`。

### 12.2 停止报告 SKEL-B2-02:本地克隆origin与身份校验冲突

状态:已由SKEL-B2-03裁定处置;下文保留原始事实,候选扩展身份校验未采纳。

冻结稿5.1要求本地裸仓库克隆并复用现有`_validate_source_identity`;
该函数却将本地origin完整目录前缀也保留在归一化项目名中,不能与unit.project相等。
离线实测:真实本地clone/checkout成功,HEAD与三键marker正确,校验仍报
`REJECTED_IDENTITY_MISMATCH`(exit 4)。只在临时仓库改为SSH项目形态origin
的对照通过,未访问该地址。这一对照不是正式实施或测试绕过。

- 报告及候选文字diff、影响与需补用例:
  `evidence/batch2/stop-report-SKEL-B2-02.md`。
- 可复跑探针:`evidence/batch2/probe-local-origin.py.txt`;
  实测argv/结果/UTC/清理事实:`evidence/batch2/probe-local-origin.json`。
- 候选为受信配置确定的本地远端精确比较,须设计方授权共享校验API及各调用方
  语义,不自行去前缀或后缀匹配。冻结稿、生产代码、既有测试均未改。
- 本批命令/API与CLI去重尚未实现;sandbox-submit与qb-trigger屏障diff均0行。
  第6节本批业务用例、CLI非法参数对照、全仓门禁与安全四组均NOT_RUN,
  未增加nodeid或skip,不以第1批2921/0/1冒充本批验收。
- 只执行离线规格探针、设计文档检查和完整性核对(见`evidence/batch2/checks.json`),
  没有真实QuickBuild/Gerrit/gbs访问,没有修改真实状态库。停止等待裁定,不进入第3批。

## 13. 实施裁定 SKEL-B2-03:本地远端与身份校验

1. SKEL-B2-02 停止成立。设计方不采纳"扩展共享身份校验的本地远端分支":它会改动已验收的 repair-step、sandbox-submit 身份判断,而冲突只出现在离线测试的搭法上。_validate_source_identity 与 _normalize_project 保持不变,所有调用点不变。
2. 离线测试改用 ssh 形式的 gerrit_ssh_base(固定为 ssh://gerrit.invalid:29418),传输由测试专用的假 ssh 程序承担:git 通过 GIT_SSH_COMMAND(或等效的测试环境变量)调用该程序,程序只接受 git-upload-pack 与 git-receive-pack 两种命令,把远端路径映射到本次测试临时目录下的裸仓库根,路径规范化后必须仍在该根之内;其它命令、根外路径、带 ..、符号链接逃逸一律非零退出。该程序放在 tests/fixtures/,只在测试中启用,生产代码不得引用。
3. 冻结稿 5.1"离线测试从本地裸仓库克隆"按本裁定理解为"经假 ssh 传输读取本地裸仓库";克隆出的 origin 原文是 ssh 形式,归一化后等于 project,与正式运行一致。
4. campaign-add-unit 第 4 步在暂存目录中、写 marker 之前,用现有 _validate_source_identity 所用的同一 HEAD 与 origin 判据核验(可直接复用其 HEAD/origin 部分的同一实现,不另写一套规则);不通过即 exit 4 REJECTED_IDENTITY_MISMATCH,删除暂存目录,不发布。因此 gerrit_ssh_base 为绝对本地路径时,建档在暂存阶段被拒且不留产物。
5. 前置确认:先核对生产代码执行 git 时的统一环境(_sandbox_git 及 campaign-add-unit 将使用的同一机制)是否会清除或覆盖测试注入的 ssh 程序设置。若会清除,且只有修改生产代码才能注入,则不改生产代码,停止并报告;若不会,按本裁定实施。
6. 现有 sandbox-submit 测试中"手工设 ssh origin + 另配本地裸仓库传输"的旧搭法不改;新命令与第 3 批离线端到端统一用本裁定的假 ssh 搭法。

### 13.1 前置核对

基线51513bd。`_sandbox_git.py:42-48`清除外部GIT_*并把GIT_SSH_COMMAND设为
实例的ssh_command(默认ssh),但保留PATH与非GIT_变量。测试通过PATH中的ssh
假程序与SKEL_FAKE_SSH_ROOT注入,不改生产代码。建档将复用SandboxGit同一机制。
必须先在该真实调用路径实测,不能只凭静态检查认定通过。
原probe-local-origin的拒绝结果不作废:它对应本裁定第4项要求的本地路径负例,
新正例改用SSH形式origin与假传输,不再修改共享身份校验。

### 13.2 假SSH实测与保留交付

前置确认PASS。`tests/fixtures/campaign_fake_ssh.py`只在测试PATH中作为ssh启用,
非GIT_变量SKEL_FAKE_SSH_ROOT提供临时裸仓库根。现行SandboxGit覆盖外部
GIT_SSH_COMMAND后仍能通过PATH调用该程序。upload-pack与receive-pack实测均通过,
没有修改统一环境或身份判据。生产代码没有引用此测试夹具。

| 裁定项 | 测试(均在tests/unit/test_campaign_fake_ssh.py) | 结果 |
|---|---|---|
| upload-pack与环境注入 | test_upload_pack_via_unmodified_sandbox_environment | PASS |
| receive-pack | test_receive_pack_via_unmodified_sandbox_environment | PASS;只写临时本地裸仓库 |
| 非白名单命令 | test_fake_ssh_rejects_unsafe_requests[uname -a] | PASS;拒绝 |
| 根外路径 | test_fake_ssh_rejects_unsafe_requests[git-upload-pack /outside/not-a-repository] | PASS;拒绝 |
| ..路径 | test_fake_ssh_rejects_unsafe_requests[git-upload-pack ../outside]与[git-upload-pack platform/../upstream/example] | 2 PASS;拒绝 |
| 符号链接逃逸 | test_fake_ssh_rejects_unsafe_requests[git-upload-pack escape] | PASS;拒绝 |

建档草稿曾初跑5例(首次假SSH克隆/三键marker/共享身份校验及重跑;
绝对本地路径暂存拒绝并清理;分析器失败;证据不覆盖;建档锁忙),
连同假SSH共12 passed/1.19秒。尚未验收,遇到13.3节缺口后已撤回源码与这5例,
不宣称baseline-reproduce/repair-step端到端或本批建档验收完成。
未验收草稿仅归档`evidence/batch2/ssh-resume/implementation-wip.patch`,
文件清单与性质见`wip-manifest.json`,后续不得直接恢复为交付。

### 13.3 停止报告 SKEL-B2-04:报告子构建号缺少数据源

状态:已由SKEL-B2-05裁定处置;删除子构建号列,只输出父构建号及结果文件引用,
不打开结果文件。下文保留原停止事实。

冻结稿5.4的campaign-report只有state-db与output参数、要求只读状态库并报告
QuickBuild父/子构建号。现行库没有子构建号列,P5Q写入的qb_result_ref又是相对
独立state_root的路径;报告无法从现有入口可靠定位结果文件。
临时数据库探针通过生产状态API证明该情形,不猜目录、不静默空值、不扩展schema。

- 事实、代码行号、候选文字diff、影响和新增夹具要求:
  `evidence/batch2/stop-report-SKEL-B2-04.md`。
- 探针:`evidence/batch2/ssh-resume/probe-report-source.py.txt`;
  输出:`report-source.stdout.log`,exit 0,SPEC_GAP_CONFIRMED。
- 候选A为显式state-root及受约束的结果文件读取,候选B为纯DB报告缩减子构建列;
  均只建议,等待设计方裁定。冻结稿和design.md未改。
- 本轮未验收业务改动全部撤回,生产文件与51513bd逐字一致;
  sandbox-submit/qb-trigger屏障diff各0行,CLI去重和3份SKILL尚未交付。
  共享身份函数及所有既有调用点不变。

### 13.4 停止时验收快照

证据根:`evidence/batch2/ssh-resume/`;所有命令、UTC起止和exit见commands.json。

| 检查 | 结果 | 证据 |
|---|---|---|
| 假SSH交付用例重跑 | 7 passed/0 failed/0 skipped,0.27秒 | fake-ssh.stdout.log、fake-ssh.xml |
| 交付fixture/test的ruff | PASS | ruff.stdout.log |
| collect-only | 2929 collected,exit 0;原2922全部保留,新增仅假SSH7例 | collect.stdout.log、nodeid-diff.json |
| import-linter | 7 kept/0 broken | import-linter.stdout.log |
| design.md检查器 | 0 problem | design-check.stdout.log |
| 冻结稿/安全核心/共享身份/统一Git环境/代理 | 与HEAD字节相同;生产diff为空 | integrity.json |
| 全量pytest、mypy、全仓ruff、四组安全测试 | NOT_RUN;按设计缺口停下,不是第2批验收通过 | 本节 |

冻结稿SHA256仍为`1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`;
代理完整SHA256仍为`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`,
前缀仍为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`。
没有运行全仓门禁,故没有本轮全仓负载记录或计时清单重跑;不以历史通过替代。
没有真实QuickBuild/Gerrit/gbs访问,没有修改既有真实状态库;第3批不开始。
提交前diff检查:排除WIP补丁时exit 0;完整检查exit 2,仅为补丁上下文空行的
空格,保留补丁原字节。记录见`ssh-resume/diff-check.json`。

## 14. 实施裁定 SKEL-B2-05:campaign-report 列定义

1. SKEL-B2-04 停止成立,属冻结稿 5.4 自身矛盾(要求子构建号又要求只读状态库)。采用候选 B 的变体:
   a. campaign-report 删除"QuickBuild 子构建号"列,保留"QuickBuild 父构建号"(取该 unit 最新 request 的 BUILD_BOUND/RESULT 事件中的 qb_build_id,无则为空)。
   b. 新增"结果文件引用"列,原样输出最新 RESULT 事件的 qb_result_ref 字符串(相对 state_root 的路径),无 RESULT 则为空;报告不解析、不打开该文件。
   c. 命令签名不变:campaign-report --state-db [--output <md>];仍只读状态库,不增加参数,不增加文件读取与相应失败规则。
   d. 其余列与 JSON 对应关系照冻结稿 5.4。
2. ssh-resume/implementation-wip.patch 只作定位资料,不得直接套用;第 2 批业务代码按冻结稿与各裁定重新实现。
3. 假 SSH 经 PATH 注入的方式(_sandbox_git 覆盖 GIT_SSH_COMMAND 但保留 PATH)予以认可,不改生产代码。

### 14.1 开工核对

基线a7c2337,分支clang-fix-campaign。重读本进度及
`evidence/batch2/stop-report-SKEL-B2-04.md`,核对冻结稿5.4与现行
campaign_state的BUILD_BOUND校验。冻结稿SHA256仍为
`1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`。
不恢复WIP,不改生产代码或既有测试;用户既有无关工作树改动保留。

### 14.2 停止报告 SKEL-B2-06:已绑定无RESULT的父构建号期望冲突

状态:已由FatTank在第15节的澄清关闭,下文保留停止时事实。

本轮任务第二步用例原文为“已绑定无 RESULT 时两列为空”。
但裁定第1(a)条明确允许从最新request的BUILD_BOUND取qb_build_id;
合法BUILD_BOUND必须有非空qb_build_id,因此两种要求不能同时满足。

最小状态:最新request只有SUBMITTED与BUILD_BOUND(qb_build_id=101),没有RESULT。
按1(a)(b)两列为(101,空);按第二步用例为(空,空)。未自行选取一种解释。
已在对话询问设计方:是否改用例为“父构建号显示已绑定值,仅结果文件引用为空”。

报告、精确条文与候选文字diff:
`evidence/batch2/stop-report-SKEL-B2-06.md`。
本轮只登记文档,未开始业务实现;各新命令/API、CLI去重与测试对照仍待完成,
sandbox-submit与qb-trigger屏障diff各0行。未新增或修改测试/nodeid。
全仓pytest、负载采样、计时敏感用例、四组安全测试、mypy/ruff/import-linter
本轮均NOT_RUN,不得把上轮结果算作本轮验收。冻结稿、安全核心、代理、身份函数、
P5Q写入与schema均未改。没有真实QB/Gerrit/gbs操作,不进入第3批。
文档检查:design.md检查器0 problem,本轮文档diff检查通过,生产/测试diff为空;
命令与输出见`evidence/batch2/checks-SKEL-B2-06.json`。

## 15. SKEL-B2-05补充澄清与第2批续做

FatTank对“已绑定但无RESULT时是否显示父构建号、仅结果引用为空”的原话:
“显示父构建号，仅结果引用为空”。据此关闭SKEL-B2-06;未绑定无RESULT时两列为空。
本轮从8326fb4继续,不恢复WIP;按冻结稿与SKEL-B2-01/03/05重新实现。
证据放`evidence/batch2/implementation/`,不覆盖历史停止证据。边界和门禁沿用前述裁定。

### 15.1 实现落点

| 冻结条目/裁定 | 落点(仓库相对路径) |
|---|---|
| 5.1建档锁、规范化、不可覆盖证据、unit与源码暂存发布 | `tizen-campaign-intake/scripts/tizen_campaign_intake/intake.py:91`、`:44`;入口`:168` |
| 5.2主架构先行、三态基线、独立副本、finally清理、标准架构锁 | `tizen-baseline-reproduce/scripts/tizen_baseline_reproduce/baseline.py:42`;入口`:182` |
| design 4.2 reproduce.check | `tizen-campaign-core/scripts/tizen_campaign_core/reproduce.py:17` |
| 5.4 terminal/held/abandoned释放API、双来源枚举与对账 | `tizen-campaign-core/scripts/tizen_campaign_core/campaign_lifecycle.py:47`、`:98`、`:104`、`:112` |
| finish-unit / release-worktrees / report | `tizen-campaign-report/scripts/tizen_campaign_report/report.py:17`、`:31`、`:51`;入口`:170` |
| sandbox持锁后屏障 | `tizen-sandbox-submit/scripts/tizen_sandbox_submit/sandbox_submit.py:527`;仅+4/-0行 |
| qb-trigger持锁后、该unit代理命令前屏障 | `tizen-qb-verify/scripts/tizen_qb_verify/qb_trigger.py:636`;仅+4/-0行 |
| SKEL-B2-01四命令解析去重 | `tizen-ci-triage/scripts/ci_triage/cli.py:20`、`:39`、`:40`直接导入执行包同一handler;不再复制解析逻辑 |
| 三份SKILL | `tizen-campaign-intake/SKILL.md`、`tizen-baseline-reproduce/SKILL.md`、`tizen-campaign-report/SKILL.md` |

解析权威函数仍为执行包`__main__.py`中的`_main_campaign_repair_step:44`、
`_main_sandbox_submit:32`、`_main_qb_trigger:21`和`_main_qb_result_fetch:41`。
12条旧/新入口非法参数对照同时断言handler对象相同、JSON相同、exit相同。
intake仅保留campaign-start-check帮助位置,实际执行明确报未实现,不虚报启动检查通过。

新增内部辅助模块`_campaign_io.py`集中建档/基线共用的JSON参数错误、配置加载、
sha256、文件锁、原子证据发布与analyzer子进程封装;不改既有helper或业务判据。
首次克隆在marker之前复用共享身份函数的HEAD/origin判据,已有源码直接调用原函数;
`_validate_source_identity`、`_normalize_project`与其既有调用点不变。
secondary的分类与basis使用primary REPRODUCE本地证据,CI hash仍只记录unit级锚点。
假gbs经测试PATH替换,分析使用真实gbs_analyzer;假SSH沿用已交付fixture,不访问真实远端。

### 15.2 覆盖与验收进行记录

第6节本批逐条对应:`evidence/batch2/implementation/coverage.md`;
精确用例位置:`test-locations.json`;收集列表:`nodeids-final.txt`。
新增业务用例99,此前假SSH7例一并重跑:106 passed/0 failed/0 skipped。
2922个第1批nodeid全部保留,新增106=99+7,总计3028;差集见`nodeid-comparison.json`。
第3批的review-submit、start-check与完整端到端部分明确留待第3批,不伪装成本批覆盖。

四组P5Q本机安全测试从头重跑4/4,pytest包装1 passed,输出在`safety/`。
CI同口径mypy的18个包128文件通过;另按pyproject完整包集合运行mypy,
159文件通过(`mypy-all/`);import-linter 7 kept/0 broken;
design检查器0 problem。三个SKILL均经quick_validate验证通过。
全仓原始结果与清单处理见15.3节,不以定向测试替代全仓。

完整脏工作区`ruff check .`首次报告55项:53项来自用户原有未跟踪草稿,
另2项是第1批机械路径增长留下的E501。原始失败输出`ruff/stdout.log`仅本机保留,
不把含无关草稿源码片段的诊断原文提交;提交`ruff/diagnostics-summary.json`登记
文件/行号/规则/计数。不修改、不提交无关草稿。只对`tests/fixtures/p5q_node_entry.py:11`与
`tests/unit/test_p5q_c6_offline_fix.py:31`换行,不改参数、断言或nodeid;
两文件去行号AST相同的证明见`format-only-proof.json`。
完整待提交集合(全部已跟踪Python+本轮新增Python,遵守仓库既有exclude)ruff通过,
见`ruff-candidate-2/`;首次换行仍超长的输出也保留于`ruff-candidate/`。
不把脏工作区全目录ruff称为通过。

`integrity.json`核对冻结稿、design.md、安全核心、共享身份/统一Git环境、
campaign_state与qb-result-fetch均与8326fb4字节相同。代理全文件sha256:
`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`;
前缀sha256:`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`。

### 15.3 全仓门禁、负载与计时清单

证据根为`evidence/batch2/implementation/`;每次运行的argv、UTC起止、exit、
前后/proc/loadavg、CPU核数与起始CPU前10(仅名称/占用)见相应`command.json`。
全仓UTC 2026-11-03 05:24:20至05:41:58,20逻辑核,负载前
1.04/1.13/1.04,后3.71/3.05/2.29。原始pytest结果:
**3026 passed / 1 failed / 1 skipped**,1056.89秒,exit 1。
唯一失败是清单内
`tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[late-build]`。
无清单外失败;C5a其余5参数与C8调查用例均通过。唯一skip为
`test_case_insensitive_bypass_is_platform_specific`,原因`case-sensitive filesystem`,
与第1批同nodeid同原因,见`skip-comparison.json`。

原失败是提交后配置页读取返回`QB_BROWSER_UNAVAILABLE/FETCH_CONTINUE_FAILED`,
lookup_reads实际1次、期望10次;关闭尾段0.045197秒,并非关闭超5秒。
保留`full/pytest.xml`、`full/stdout.log`和`full/c5a/late-build/`原始记录,
不声称已查明根因,不改代理、测试、5秒阈值、skip/xfail。
按SKEL-B1-05第4项在同一代码树单独连续运行原nodeid三次:

| 次数 | 结果 | 命令总耗时秒 | 负载前(1/5/15分钟) | 负载后 | 三次CLI关闭尾段秒 | 证据 |
|---|---|---|---|---|---|---|
| 1 | 1 passed/0 failed/0 skipped | 26.230 | 2.96/2.94/2.27 | 2.68/2.86/2.27 | 0.0831/0.1275/0.0749 | timing-1/ |
| 2 | 1 passed/0 failed/0 skipped | 27.684 | 3.14/2.94/2.32 | 3.94/3.16/2.42 | 0.0818/0.0751/0.0813 | timing-2/ |
| 3 | 1 passed/0 failed/0 skipped | 26.095 | 5.67/3.72/2.64 | 5.97/3.95/2.74 | 0.0760/0.0759/0.0806 | timing-3/ |

判定:3/3通过,按既定裁定接受本轮门禁;不是“全仓零失败”。
原始失败不被重跑覆盖,汇总为`timing-decision.json`。
C8在本轮全仓为PASS,未触发失败形态比较与补跑;第1批既有前后5次原证据不变。

| 门禁 | 本轮结论 | 证据 |
|---|---|---|
| 新业务用例 | intake20、baseline18、lifecycle41、barriers/CLI20,共99全部PASS | focused/、new-test-counts.json |
| 已交付假SSH | 7/7 PASS;upload/receive/非白名单/根外/两类.. /符号链接 | focused/pytest.xml |
| 全仓 | 按SKEL-B1-05第4项通过,原始3026/1/1 + 单独3/3 PASS | full/、timing-1至3/ |
| 四组安全 | 4/4 PASS,loopback-only,临时目录清理完成 | safety/stdout.log |
| mypy | 完整配置包集合159文件通过 | mypy-all/ |
| import-linter | 7 kept/0 broken | imports/ |
| ruff | 完整待提交Python集合通过;无关未跟踪草稿53项未纳入 | ruff-candidate-2/、ruff/diagnostics-summary.json |
| design检查 | 0 problem | design/ |
| nodeid | 2922个原用例全部保留;当前3028;新增106含此前7例 | nodeid-comparison.json |
| 入口与SKILL | 6项help成功,3份SKILL校验通过 | skills-and-help.json |
| 保护文件/代理 | 全部字节不变,代理完整与前缀hash如上 | integrity.json |

### 15.4 交付边界与移交

- SKEL-B2-06已由本节用户澄清关闭:已绑定无RESULT显示父号,结果引用为空。
- 本批没有新的设计冲突或安全边界变更。内部`_campaign_io`封装与两行路径换行
  属不改变行为的实现/格式细节,已登记。旧CLI业务handler仅转发到原执行包实现。
- 测试路径本批未修改;仅两处已登记的格式换行,另新增4个测试文件99例。
- `review-submit`的屏障、六道校验、启动检查、剧本与离线端到端仍留第3批。
- 未运行真实QuickBuild/真实gbs,未访问真实Gerrit,未推送Gerrit,未改真实状态库。
- 状态为READY_FOR_REVIEW,等待设计方审读,不自行标CLOSED,不开始第3批。
- 提交前`git diff --cached --check`仅报告原始HTML、pytest日志/XML中的行尾空白;
  为保留证据原始字节不做格式化。排除evidence目录后的同项检查exit 0。

## 16. 实施裁定 SKEL-B3-01:第 2 批验收与第 3 批范围

以下照录设计方裁定:

1. 第 2 批验收通过。设计方已审读 sandbox-submit、qb-trigger 的屏障检查(各 +4 行,取锁后、业务动作前,精确匹配)、campaign_lifecycle 三个释放 API、campaign-release-worktrees --abandon 的取锁与写序、campaign-add-unit 的暂存克隆核验与 os.link 发布、baseline-reproduce 的取锁,以及 late-build 原始失败与 3 次重跑记录。SKEL-B2-06 由用户澄清关闭(已绑定无 RESULT:显示父构建号,结果引用为空)。
2. late-build 原始失败形态为"lookup_reads 期望 10 实际 1;FETCH_CONTINUE_FAILED",不是关闭时延;与 live-01 提交后读取失败同一错误类别。按 SKEL-B1-05 第 4 项放行有效,但登记为"离线可偶发复现的读取失败",在第 3.5 批之前另行安排定位任务,本批不处理。
3. SKEL-B1-05 第 4 项补充:清单内 C5a 用例若因关闭时延以外的原因失败,3 次重跑全部通过仍可放行,但须在 progress.md 单独登记失败形态(断言原文、AGENT_STOPPED 的 failure_category、harness_failure 类别)并汇总到一张"读取失败观测表",每批累加。
4. 冻结稿第 6 节第 1 条"同一份本地路径配置下 campaign-add-unit 克隆成功而 campaign-start-check 失败"一条,因 SKEL-B2-03 第 4 项已改为建档在暂存阶段拒绝本地路径,改为"本地路径配置下两者都拒绝(add-unit 为 REJECTED_IDENTITY_MISMATCH 且无产物,start-check 为 PREFLIGHT_FAILED)"。
5. 离线测试 gerrit_ssh_base 统一为 SKEL-B2-03 的 ssh://gerrit.invalid:29418 加假 SSH;冻结稿第 6 节第 2 条"离线端到端不含启动检查"相应改为:离线端到端第一步运行 campaign-start-check,其 ls-remote 经假 SSH 完成;gbs 子进程仍用假件。
6. 第 3 批范围:冻结稿第 7 节第 3 批(5.3 review-submit 含取锁、5.5 campaign-start-check 与编排 skill tizen-clang-campaign、第 6 节离线端到端),tizen-review-submit 的 SKILL.md,以及第 2 批延后的"放弃后取到 PASS → review-submit 被拒"用例中 review-submit 部分。

### 16.1 开工核对与读取失败观测表

开工HEAD `1a4ed25`,分支`clang-fix-campaign`;已重读冻结稿第3/5.3/5.5/6节、
附录C及本进度。冻结稿SHA256仍为
`1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`。
代理SHA256仍为`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`。
用户已有脏文件不改、不提交。技能编写规范已读取skill-creator,但停止前未创建SKILL或业务代码。

| 批次/用例 | 断言原文 | AGENT_STOPPED failure_category | harness_failure | 处置与证据 |
|---|---|---|---|---|
| 第2批 C5a late-build | `AssertionError: assert 1 == 10`;`1 = len([{'command': 'read', 'path': '/overview/1917'}])` | `FETCH_CONTINUE_FAILED` | 归档中未记录该字段,不推断类别 | 原`evidence/batch2/implementation/full/stdout.log:160`与`full/c5a/late-build/agent-0.json:312`;独立3/3通过,SKEL-B3-01第2/3项登记为离线可偶发复现的读取失败,第3.5批前另行定位 |
| 第3批 | NOT_RUN | NOT_RUN | NOT_RUN | 契约核对停止,无新全仓观测 |

### 16.2 停止报告 SKEL-B3-02:无RESULT提示缺少state_root输入

状态更新:已由SKEL-B3-03裁定关闭;以下保留原停止事实。

冻结稿5.3要求固定message里的`<state_root>`填实际路径,但继承的design.md
4.1 review-submit签名没有`--state-root`;campaign_config模板未定义此键;
QB请求/事件表不存储这个根目录。生产QB命令通过独立的`--state-root`接收它,
不要求它等于state DB父目录或campaign_workspace。
尤其无RESULT时,无法从`qb_result_ref`反推,`--qb-result`也不承诺位于该目录。
新增参数、要求配置新增必填键或改写固定提示均属契约选择,本轮不自行决定。

证据与候选处置:`evidence/batch3/stop-report-SKEL-B3-02.md`;
离线探针:`evidence/batch3/probe-state-root.py`,结果`probe-state-root.json`。
该探针只在临时目录构造unit/request并调用生产trace写入函数,证明同一库与request
可对应不同trace根且库字节不变,不运行浏览器、网络、gbs或git远端命令。

本轮停止在业务实现前。review-submit与start-check未实现,取锁位置未新增;
三条端到端均NOT_RUN,不虚构状态序列。全量pytest/负载/mypy/import-linter及
计时重跑均NOT_RUN,不能沿用第2批结果充当本批验收。nodeid未新增或修改;
四组安全测试按本批边界不重跑。不进入第3.5批。

## 17. 实施裁定 SKEL-B3-03:无 RESULT 提示文字

1. SKEL-B3-02 停止成立,属冻结稿 5.3 的规格缺口。采用候选 C 的变体:review-submit 签名不变,不新增 --state-root,不新增配置键,不改 schema。
2. 无 RESULT 时仍为 exit 4 REJECTED_QB_REQUEST_PENDING,message 固定为:"该 unit 最新的验证请求(request_id=<request_id>)还没有结果。若 qb-result-fetch 曾报告结果无法识别(QB_RESULT_UNRECOGNIZED,例如各架构状态非空或快照漂移;可在运行 qb-result-fetch 时所用的 state_root 下查看该 request 的 trace 确认),重读不会改变结果,请按其输出的指引处置,或用 campaign-release-worktrees --abandon 放弃该 unit;否则稍后重跑 qb-result-fetch。"其中 <request_id> 取该 unit 最新 request 的 request_id;本命令不读 trace、不推定目录。
3. 第 6 节对应用例改为断言该 message 与实际 request_id 逐字一致。
4. 编排 skill 的剧本与启动模板中写明 state_root 是所有 QuickBuild 命令共用的同一目录,由启动模板填写。

本轮基线`0417ff3`;其余范围、边界、读取失败观测与门禁按SKEL-B3-01。
不恢复任何未验收草稿,不改冻结稿/代理/安全核心/共享身份规则/状态库schema。

### 17.1 停止报告 SKEL-B3-04:基线到修复轮的状态推进缺口

状态更新:已由SKEL-B3-05裁定关闭;以下保留原停止事实。

本轮review-submit/start-check草稿定向25项通过,包括六道拒绝门、精确request_id提示、
放弃屏障、两类锁互斥、目标分支与启动五项检查。尚未完成全部契约/全仓验收。
在新离线端到端首次串联中,建档与三架构基线成功,随后repair-step立即exit4:
`REJECTED_STATE_INCONSISTENT`,原文
`campaign unit status is not executable: 'BASELINE_REPRODUCED'`。

已验收baseline写BASELINE_REPRODUCED,已验收repair-step只接受REPAIR_ROUND_RUNNING;
当前生产命令没有两者之间的状态写入者。独立探针确认零round、零预算、零编译调用,
DB原始字节不变。另静态查明LOCAL_3ARCH_PASS当前由sandbox-submit写入,
与第3.5批不运行sandbox-submit而要求到达该状态的目标也需要一并明确职责。
没有在夹具/剧本中直接补写状态,没有修改repair-step或baseline。

报告:`evidence/batch3/stop-report-SKEL-B3-04.md`。证据根:
`evidence/batch3/handoff/`,含定向25PASS、端到端1FAIL、独立探针1PASS及原始命令元数据。
探针PASS仅表示确认拒绝事实,不表示端到端成功。
候选A为授权现有repair-step承担带校验的入轮与聚合推进;候选B为新增本地编排入口,
均须明确policy/锁/事务/重入,均未实施。

未验收实现与新测试移出生产路径,仅存`handoff/implementation-wip.patch`作定位资料;
不得直接套用当交付。两份入口恢复0417ff3。未写SKILL/启动模板。
全仓pytest、import-linter、mypy、计时敏感重跑NOT_RUN,三条端到端未完成;
读取失败观测表本批无新P5Q观测。未改代理/未改qb-trigger,四组安全按批次边界不重跑。
节点收集、冻结稿/代理/安全核心字节核对和文档检查见`handoff/checks.json`。
停止树3028个nodeid全部保留且零新增;设计检查0 problem,证据脚本ruff通过。
独立探针在撤下草稿后再次1/1通过。代理完整SHA256仍为
`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`,
前缀(不含`export class Agent {`)仍为
`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`。
证据脚本初次ruff的未使用导入已修正,原日志保留;不声称已跑全仓ruff/mypy等门禁。
暂存diff检查仅报告原始pytest失败日志和参考patch上下文行的尾随空白;
保留原始证据字节,排除这两个证据文件后的diff检查通过。
完成停止登记后等待设计方裁定,不进入第3.5批。

## 18. 实施裁定 SKEL-B3-05:基线与修复轮衔接

用户消息重复粘贴的裁定按完整内容登记一次。

1. SKEL-B3-04 停止成立。原设计中 BASELINE_REPRODUCED → REPAIR_ROUND_RUNNING 的推进属 P10,骨架裁剪时遗漏。采用候选 A 的收窄版本。
2. campaign-repair-step 首轮推进:在现有锁内、只读身份校验之后、create_round 之前,若 latest_status 为 BASELINE_REPRODUCED,且同时满足 a) 本次 round_index == 1 且该 unit 尚无任何 round;b) 三个架构的最新 REPRODUCE 事件齐备;c) primary_arch 的 outcome 为 matched;则 append_status(REPAIR_ROUND_RUNNING),随后完全按现有流程继续。任一条件不满足 → exit 4 REJECTED_STATE_INCONSISTENT,零 round、零预算、库不变。推进后在 create_round 前崩溃的,重跑看到 REPAIR_ROUND_RUNNING 且零 round,按现有流程进行。除 BASELINE_REPRODUCED 外,可执行状态集合不变;九步顺序、编译预算、对账、保护标记语义不变。
3. 策略预检:编排剧本在每次 campaign-repair-step 之前调用 suppress-policy check(既有命令,source_kind 按冻结稿只用 generated 或 suppress);在 tizen_campaign_repair 入口下增加同名子命令,与 ci_triage/cli.py 的 suppress-policy 共用同一解析与执行函数(按 SKEL-B2-01 第 3 项的去重做法);剧本可执行命令集合相应增加该子命令。forbidden 即停,不调用 repair-step。sandbox-submit 与 review-submit 内部的权威策略重推不变。
4. LOCAL_3ARCH_PASS 仍由 sandbox-submit 在聚合与副本校验通过后写入,不改。冻结稿第 5.4 节与第 7 节中"第 3.5 批止于 LOCAL_3ARCH_PASS"一律理解为:同一最终 round_index 下三个架构的 campaign-repair-step 均返回 PASS 且三条 verification 已 link,状态为 REPAIR_ROUND_RUNNING。第 3.5 批后不得释放副本、不得放弃的约束改为针对这一情形;第 4 批从 sandbox-submit 开始,由它写入 LOCAL_3ARCH_PASS。
5. 既有 repair-step 测试中若有断言"BASELINE_REPRODUCED 在第 1 轮被拒"的用例,允许按本裁定改为新行为,逐条登记 nodeid 与改动前后断言;其它既有断言不改。若改动涉及第 2 项以外的状态,停止并报告。
6. design.md 第 4.6 节之后追加一条:campaign-repair-step 首轮推进与 suppress-policy 子命令按骨架设计文件的实施裁定 SKEL-B3-05 执行。不改已有条目。

基线`43c2c99`;不直接套用handoff草稿。repair-step仅改本裁定两项,
安全核心/身份规则/schema/代理/冻结稿保持原字节,全部运行限本地假件。

### 18.1 实施落点与定向验证

| 项 | 落点 | 说明 |
|---|---|---|
| 首轮推进 | `tizen-campaign-repair/scripts/tizen_campaign_repair/campaign_repair_step.py:165,727,744` | 现有arch锁内、身份检查后,重用gate_view三架构+primary判据;BEGIN IMMEDIATE内再次查状态/round,只追加一次REPAIR_ROUND_RUNNING;原九步不改 |
| suppress-policy共享入口 | `tizen-campaign-repair/scripts/tizen_campaign_repair/__main__.py:119`; `tizen-ci-triage/scripts/ci_triage/cli.py:19` | 同一函数同一解析器,旧CLI仅导入;原兼容参数保留,编排仅用generated/suppress |
| review-submit | `tizen-review-submit/scripts/tizen_review_submit/review_submit.py:218` | 第248行取sandbox四锁,先查放弃屏障,到push与REVIEW落库后finally释放;六道检查+Change-Id缓存+隔离传输 |
| QB gate | 同上`:101,192` | 最新request内最新RESULT;原字节hash/schema/绑定;判据取DB,不接受人工降级;SKEL-B3-03精确message在`:52` |
| campaign-start-check | `tizen-campaign-intake/scripts/tizen_campaign_intake/start_check.py:29,130` | 五项检查,项目名先校验,完整ssh地址ls-remote,配置与可达性错误分开 |
| 编排与启动输入 | `tizen-clang-campaign/SKILL.md`; `references/campaign-kickoff-template.md` | 命令确定顺序、每次repair前policy &&、放弃出口、统一STATE_ROOT、适用P11条款;第3.5批保留三份PASS副本 |
| 设计指引 | `design.md:2776` | 仅在4.6之后追加裁定要求的一条,原条目不改 |

repair-step本体diff为+52/-1;repair包入口+30/-1,ci_triage转发+2/-26。
按裁定第5项改动的既有测试清单:**无**。旧节点及旧断言均未修改。
新增60例:handoff 13、review 26、start 12、E2E 4、script 5。
条目到nodeid的映射见`evidence/batch3/implementation/coverage.md`;
新增清单见`nodeids-added.txt`。3028个既有nodeid全部保留,最终收集3088个,
零收集错误;差集与受保护文件hash见`audit.json`。

定向首跑58/58通过(当时尚未添加两条superseded用例),完整状态序列在
`focused/stdout.log`。两条新增superseded定向复跑2/2通过。
开发过程中修正了新夹具的HELD arch、aggregate错误码期望、最新request缺少
BUILD_BOUND前置等搭建错误;未修改任何既有断言,未作为全仓门禁失败处理。
未套用历史patch,历史停止证据均保留。

三条离线链路均使用生产命令实现、真实本地Git/SQLite/workspace与gbs_analyzer,
仅gbs与QB代理是假件,远端通过SKEL-B2-03假SSH。成功序列比任务简写多了
初始DISCOVERED,BASELINE_RUNNING因三个arch各写一次而重复三次;未改代码对齐。
放弃屏障是事件而非状态,之后fetch可以写SANDBOX_QB_PASS,review仍被拒,
报告显示已放弃且无WORKTREE_LOST。完整序列见coverage。

已通过:ruff完整候选树、mypy(161源文件)、import-linter(7/7)、design检查
(0 problem)、两个新SKILL格式检查、新命令及新旧policy入口help。原始输出
和argv/UTC/负载见`implementation/`相应子目录。全仓最终结果
在下一节登记,不以定向结果替代全仓。

### 18.2 最终门禁与读取失败观测

证据根:`evidence/batch3/implementation/`。原始输出、JUnit、命令与起止UTC
分别在对应目录的`stdout.log`、`stderr.log`、`pytest.xml`、`command.json`;
聚合结果为`summary.json`。

| 门禁 | 结果 | 证据 |
|---|---|---|
| 全仓pytest | 3087 passed / 0 failed / 1 skipped;1078.44s | `full/` |
| 新增handoff/review/start/script/E2E | 13/26/12/5/4,全部PASS | `summary.json`、`full/pytest.xml` |
| mypy | 161 source files,0 issue | `mypy/` |
| ruff完整候选树 | all checks passed,无关未跟踪草稿不纳入 | `ruff/` |
| import-linter | 7 kept / 0 broken | `imports/` |
| design.md检查 | 0 problem | `design/` |
| nodeid | 3028既有全部保留,新增60,共3088,零collect错误 | `collect/`、`audit.json` |
| 安全核心/身份规则/schema/P5Q writer/代理/冻结稿 | 与43c2c99逐字节一致 | `audit.json` |

唯一skip仍是`test_case_insensitive_bypass_is_platform_specific`,原因为
`case-sensitive filesystem`,零新增skip。全仓07:25:21–07:43:21 UTC,
20个逻辑CPU,loadavg由`2.46 2.51 2.09`到`3.23 2.23 2.06`;
开始时CPU前10进程仅记录名称与占用,没有argv,见`full/command.json`。
stderr为Xvfb的非致命xkbcomp键位警告,不隐去原始日志。

计时敏感清单全过:build(31.954s)、error-created(23.224s)、error-no-build(16.664s)、
no-navigation(83.153s)、delayed-build(23.230s)、late-build(23.254s),以及
C8 `test_post_submit_read_signatures`(180.957s)。这里是整例耗时,不是关闭耗时。
没有触发C5a三次重跑规则,没有触发新的C8失败形态核对,未加skip/xfail或改阈值。

| 批次 | 读取失败观测 | AGENT_STOPPED / harness | 处置与证据 |
|---|---|---|---|
| 第2批(沿用) | late-build: `lookup_reads`期望10实际1 | FETCH_CONTINUE_FAILED;其余原文见第16.1节 | 原始失败保留,单独3/3通过;SKEL-B3-01认可,仍待第3.5批前另行定位 |
| 第3批本轮 | 无新失败;上述7个敏感例全部PASS | 无失败类别 | `full/pytest.xml`、`summary.json` |

代理全文件SHA256仍为`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`,
前缀SHA256仍为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`。
本批未改单独安全组覆盖的生产路径,按SKEL-B3-01不另开四组安全验收轮;
全仓所含既有Node/安全用例原样执行且通过。

### 18.3 交付边界

与冻结稿/有效裁定不一致、做不到之处:**无**。
既有状态序列差异已在18.1与coverage逐项列出,不视为未裁定的新状态。
全部外部动作均由本地假件承接,未访问真实Gerrit/QuickBuild或运行真实gbs;
未改安全核心、共享身份判据、冻结稿、代理或状态库schema。
stage21停在第3批待审读,不开始第3.5批。第2批读取失败遗留仍开放,不声称已修复。

## 19. 实施裁定 SKEL-R-01:第 3 批验收与读取失败定位

1. 第 3 批验收通过。设计方已审读 repair-step 首轮推进(锁内、身份校验后、SQLite 独占事务内推进,依据 gate_view.reproduced)与 review-submit 的取锁与屏障位置。
2. 新任务:离线定位 FETCH_CONTINUE_FAILED。已知样本:第 2 批全仓中 C5a late-build 一次(lookup_reads 期望 10 实际 1);第 1 批拆分前 C8 调查 racing-meta-refresh 一次(TargetClosedError);live-01 真机提交后读取失败一次。本任务只定位,不修复。

基线`a58494b`,当前分支`clang-fix-campaign`。已重读第16.1/18.2节读取失败观测表、
P5Q收口R11/R13/R14及stage20 `evidence/C8/investigation/README.md`。
历史真机UNKNOWN与离线FETCH_CONTINUE_FAILED仅有相似读失败表象,本轮不预先合并根因。
采样计划:原树late-build独立50次,C8原调查用例独立20次;若常规late-build 0/50失败,
再启一个半核数、仅CPU的多线程负载进程,late-build独立50次。全程串行测试,
每次独立证据/pytest临时目录、虚拟显示,保留原断言与完整场景集合。
不进入第3.5批,不改生产/测试/冻结稿/安全核心;诊断副本若需要只放仓库外并销毁。

### 19.1 采样方法与运行中事实

`evidence/read-failure/sample.py.txt`只串行调用原有两个nodeid,不修改测试、断言或参数集合。
每次使用独立pytest basetemp及证据目录,`tests/run_quiet.py`提供独立虚拟显示;
不弹真实窗口、不访问真实QuickBuild/Gerrit、不运行真实gbs。每2秒记录loadavg,
完整argv、UTC、exit、断言原文、AGENT_STOPPED与harness_failure存入各次`command.json`。

第一次包装器因没有预建basetemp父目录,产生27次pytest设置错误(夹具未运行),
另一次启动被主动终止。已保留在`setup-errors-late/`与`setup-errors-start.json`,
不计入读取失败采样。只修复证据包装器的父目录创建,加入设置错误即停,
随后使用新的临时根和新证据目录正式执行;没有覆盖上述失败证据。

常规late-build已完成50次:47通过、3失败、0跳过,1分钟load范围1.17–40.77。
run-40:关闭尾段5.487秒超5秒;run-41:submit返回QB_BROWSER_UNAVAILABLE/UNKNOWN,
服务器收到0次提交,关闭尾段13.620秒超限;run-42:CLI子进程超过原测试150秒上限。
三例均非已复现的FETCH_CONTINUE_FAILED,不能与第2批lookup_reads失败直接合并。
期间发现主机D状态进程及负载上升,见`environment-disturbance.json`;本任务未启动CPU加压,
未操作其它任务。按SKEL-R-01的条件,常规50次已有失败,不启动条件性50次加压组。
C8完整调查用例20次仍在执行,最终结果另记,不以中途结果作交付结论。

### 19.2 最终采样结果与失败观测

证据根:`evidence/read-failure/`;汇总`summary.json`、`sampling-results.md`,
逐例事件摘要`failure-facts.json`,完整分析与候选文字diff见`README.md`。

| 采样组 | 次数 | 通过/失败/跳过 | 失败率 | FETCH_CONTINUE_FAILED | 1分钟负载区间 |
|---|---:|---|---|---:|---|
| 常规late-build | 50 | 47/3/0 | 6% | 0 | 1.17–40.77 |
| 常规C8完整调查 | 20 | 19/1/0 | 5% | 1 | 0.47–14.14 |
| 条件性半核CPU加压 | 0 | 未触发 | 不适用 | 不适用 | 不适用 |

正式70次共66通过/4失败/0跳过。C8第15次在第6场景提前停止,最终5场景未执行;
其余19次完整11场景,合计215个场景记录。预期故障注入产生的UNKNOWN不计作pytest失败。
初始27次包装器设置错误与中止的第28次另存,不混入正式分母。没有修改断言、超时、skip/xfail。

| 批次/样本 | 失败位置与断言 | AGENT_STOPPED / harness | 证据与结论 |
|---|---|---|---|
| 第2批late-build(沿用) | 第一条lookup read返回失败,lookup_reads期望10实际1 | FETCH_CONTINUE_FAILED | 原服务器仅2次配置GET(基线/open_form),无lookup GET;属于先前关闭的后果 |
| 第1批C8(沿用) | submit后Page.getFrameTree失败,reads=[] | FETCH_CONTINUE_FAILED / TargetClosedError,OTHER_FRAMEWORK_ERROR | 原racing-meta-refresh样本未进入read |
| 本轮late-build 40 | `assert 5.487124443054199 < 5` | 无 / 无 | 10条lookup read均成功;代理close 4.224s,CLI尾段5.487s |
| 本轮late-build 41 | `assert 13.619728326797485 < 5` | UNKNOWN / 无 | submit返回released=false、服务器0提交;代理close 12.587s;无提交后read |
| 本轮late-build 42 | subprocess.TimeoutExpired,原CLI上限150s | 未取得 / 无 | 服务器0请求、无agent transcript,不能进一步判定启动内部等待点 |
| 本轮C8 15 | injected-missing-root-membership场景提前停止 | FETCH_CONTINUE_FAILED / TargetClosedError,OTHER_FRAMEWORK_ERROR | 无injected_fault、reads=[];帧仍owned;POST302→落地GET200→submit阶段GET拒绝→关闭→harness失败 |

本轮C8失败在故障注入之前,不能归咎于人工移除帧归属。历史meta-refresh样本与本轮
共同指向提交导航交界,不证明read导航冲突。live-01 UNKNOWN仍不能并入同一根因。

### 19.3 补充观测、候选方案与清理

仓库外`/tmp/skel-read-observe-Z6JSX8`复制agent、driver、调查入口;driver副本未改未执行,
agent只加协议方法/阶段/路径形态/请求ID/固定错误类别日志,入口只调整副本导入。
未修改任何仓库内生产或测试文件。副本10轮(每轮control、racing-meta-refresh、307),
30场景全部跑完,没有捕获CDP发送异常;307均正常执行Fetch.failRequest后得到预期UNKNOWN。
副本日志可能扰动时序,不合并入正式失败率。创建来源与hash见`observation-copy.json`,
输出在`instrumented/`,运行汇总在`observation-results.json`。

根因判断:**定位到自然失败发生于提交导航交界,但底层CDP拒绝根因未唯一确定**。
过期/已取消刷新请求的拦截ID是候选,现有证据不能证明;自然帧归属丢失没有证据支持。
README列四个候选:A固定化CDP操作诊断,B仅在可靠取消证据闭合后的窄化处理,
C读取阶段固定错误分类,D关闭/环境诊断;各含位置、文字diff、安全影响和新增/复跑测试。
尤其B需额外设计裁定,不得无条件吞掉invalid-ID错误。全部只写方案,未实施。

`cleanup.json`:2026-11-03 10:08:54 UTC已删除两个本任务pytest临时根与全部副本,
删除前无引用进程、删除后路径不存在;CPU加压未启动;无p5q-browser profile残留,
未操作无关进程。`integrity-before/after.json`:全部已跟踪skill/test/frozen文件
均与a58494b逐字节一致;代理全文与前缀hash不变。design检查0 problem。
`final-checks.json`:本轮人工文档的git diff --check通过;全证据diff返回2,
仅为原始pytest输出、夹具HTML及其逐字引用的行尾空白,按证据原样保留,不宣称全diff全绿。
本任务是采样定位,未另跑全仓门禁,不将66/4当作功能门禁放行。

与裁定不一致或做不到之处:**无**。包装器设置错误已完整披露;根因未唯一确定属于
调查结论的限制,不声称已修复。第3批已验收,本任务停止于离线定位报告,
不进入第3.5批或第4批。

## 20. 实施裁定 SKEL-R-02:读取失败只加诊断

1. SKEL-R-01 调查结论认可:late-build 三次失败与主机高负载相关(负载峰值 40.77/20 核、swap 用满),不是读取失败;C8 一次自然 FETCH_CONTINUE_FAILED 发生在提交导航阶段、首次 read 之前,底层被拒调用未定。该问题按 P5Q 设计安全停止,且读取时补绑定已在 C8 live-02 真机验证,不阻塞第 3.5、4 批。
2. 实施报告中的候选 A(拦截操作失败时记录固定元数据)、C(read 导航失败的固定分类)、D(驱动关闭耗时观测),只增加诊断,不改变任何放行/拒绝判定、停止条件、错误码、返回结构与重试行为。候选 B 不实施。
3. 诊断字段一律为封闭枚举或固定形态:操作名(Fetch.failRequest / Fetch.continueRequest / Fetch.continueResponse 等)、阶段、脱敏路径形态、导航代次、固定错误类别(请求 ID 无效 / 目标或会话已关闭 / 导航中断 / 被客户端阻止 / 连接失败 / 超时 / 其它);不得写入原始错误文本、URL 查询值、请求头、请求体或页面内容。多次失败只保留第一条起因。
4. 本次授权修改 qb_browser_agent.mjs 的 installGuards 拦截回调、Agent.read 导航段与 Agent.command 的 catch,以及 qb_browser.py 的关闭段;代理完整 sha256 与前缀 hash 随之变化,登记改动前后值。P5Q 冻结稿中"代理只改两处"的约束以本裁定为准作一次性例外。
5. design.md 第 4.6 节之后追加一条:按骨架设计文件实施裁定 SKEL-R-02 为代理与驱动增加只读诊断,不改变安全规则。

基线`6c5f640`。只实施A/C/D;诊断保存在代理runtime.trace与驱动close_observation,
不新增协议应答字段或CLI输出字段。原错误传播、停止调用、关闭等待及Policy判定保持。
证据目录:`evidence/read-failure/diagnostics/`。既有无关工作树改动不纳入。

### 20.1 实施落点与边界核对

只新增诊断,实现保留供审读,**未通过全仓验收**。报告:
`evidence/read-failure/diagnostics/stop-report-SKEL-R-03.md`。

| 落点 | 内容 | diff |
|---|---|---|
| `tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs:189`、`:222`、`:236` | installGuards第一起固定分类、操作调度时的阶段/路径/代次;仍调用原onStop | 代理合计+52/-4 |
| 同文件`:652`、`:758` | command catch的read/submit观察;read导航捕获后原异常继续抛出 | 同上 |
| `tizen-qb-verify/scripts/tizen_qb_verify/qb_browser.py:478`、`:501` | close结束时记录elapsed_ms/returncode,诊断异常不覆盖原结果 | +15/-5 |
| `docs/clang-fix-campaign/design.md:2776`之后 | 追加SKEL-R-02授权,不改已有条目 | 只追加 |

新增trace固定键为action/operation/phase/stage/path/generation/category。
七类为REQUEST_ID_INVALID、TARGET_OR_SESSION_CLOSED、NAVIGATION_INTERRUPTED、
BLOCKED_BY_CLIENT、CONNECTION_FAILED、TIMEOUT、OTHER;其余字段的完整枚举与
固定形态见`diagnostics/README.md`。导航代次只观察主帧提交,不参与帧归属判定;
调度时捕获,后续失败不覆盖第一条。close_observation是驱动内部属性,
不扩展协议应答/CLI stdout/数据库,未擅自增加CLI trace落盘代码。

`integrity.json`与`production.diff`核对:Policy、TrustedPage、原有测试、其它skill、
安全核心、共享身份判据、结果写入、schema及冻结稿无改动;Python AST除close外不变。
候选B未实施,未吞掉任何拦截错误,未增加重试或放宽任何等待阈值。

| SHA256 | 改前6c5f640 | 本轮未验收实现 |
|---|---|---|
| 代理全文 | `7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c` | `d0e99f7e4caf11104920ddfe7a569a75e100c5a1dc44a3a916d73ef2bacbf823` |
| 代理前缀(截至export class Agent之前) | `40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16` | `3bb1c0cc2fbfcb20aef324c8b8a703f06f40a438211317e0e96f2ba30f2be4c2` |

### 20.2 测试与停止事实

| 门禁 | 结果 | diagnostics下证据 |
|---|---|---|
| 新增诊断 | Node17/17;新增pytest10/10 | `focused/`;用例逐项对照见README |
| 定向pytest | 221 passed/0 failed/0 skipped | `focused/pytest.xml` |
| 既有Node | 矩阵163/163、停止类别16/16、静态与负例183/183 | `focused/stdout.log` |
| 四组本机拦截安全 | 4/4;Worker走原b分支fail-closed,攻击HTTP/WS均0,profile已删 | `safety/stdout.log` |
| mypy/ruff/import-linter/design | 161文件无错/通过/7 kept 0 broken/0 problem | 各同名目录(依赖为`imports/`) |
| nodeid | 第3批3088全保留;新增10;总3098;删除0,collect错误0 | `collect/`、`integrity.json` |
| 全仓 | **901 passed/1 failed/0 skipped;余2196未运行;不通过** | `full/`,`results.json` |

全仓2026-11-03 10:38:29至10:44:28 UTC;pytest353.98s,包装器358.893s。
20核,运行前loadavg 1.37/0.94/0.90,后1.40/1.28/1.07;
启动CPU前10仅进程名与占用见`full/command.json`。C5a六参数全通过,无单独重跑。
C8失败场景为racing-script-navigation,与第7.1节五次基线唯一失败场景
racing-meta-refresh不同,触发SKEL-B1-03第3项及SKEL-B1-05第4项停止条件。
不以SKEL-R-02对历史问题不阻塞后续批次的认可,擅自扩大本轮门禁豁免。
未继续余下全仓用例,未重跑C8以覆盖现场,不宣称零新增skip已完成全仓核对。

### 20.3 读取失败观测表增量与SKEL-R-03停止报告

| 观测 | 断言/原类别 | 本轮新增第一起诊断 | 处置 |
|---|---|---|---|
| SKEL-R-02全仓C8 racing-script-navigation | `assert result.returncode == 0`,实际1;harness TargetClosedError/OTHER_FRAMEWORK_ERROR;AGENT_STOPPED FETCH_CONTINUE_FAILED | Fetch.failRequest / submit / request / /wicket/page / generation=4 / REQUEST_ID_INVALID | 基线外失败场景,立即停止;无重跑豁免 |

`full/c8/racing-script-navigation.json:913`首次捕获具体操作与封闭类别;
其后仍是原FETCH_CONTINUE_FAILED。模拟提交POST302、落地GET200,随后submit阶段
被拒GET的failRequest失败;`reads=[]`(:721),harness读取提交后帧树时已关闭(:1036)。
这是首次read之前的失败,不是read导航错误。样本能确定“拒绝请求的操作报告ID无效”,
不能确定ID失效原因或证明安全取消;不据此实施候选B,不认定已修复或已证实拆分回归。

候选下一步仅供裁定:如允许,在父树与本树交替运行同一未改测试作对照,
分别归档,再决定是否扩充已接受失败形态;本轮不执行。详情见停止报告。
`results.json`确认无P5Q自身进程与/dev/shm profile残留;无临时代理副本、无加压进程。
未运行真实QuickBuild/Gerrit/gbs,未进入第3.5或第4批。唯一未完成要求是全仓门禁;
按裁定停止并保留实现与证据,待设计方审读。

收尾核对见`diagnostics/final-checks.json`:设计检查仍0 problem,人工源码/文档
diff --check通过;全暂存树检查返回2,仅原始夹具HTML、pytest失败输出及逐字
production.diff的行尾空白,按原证据保留。新自然失败诊断记录键集合/敏感值扫描通过。

## 21. 实施裁定 SKEL-R-04:拒绝已失效请求不再停止

1. SKEL-R-02 的诊断实现验收通过(设计方已审读代理 diff:只增加观测,observeFailure 与 generation 计数自身异常被吞掉,不影响原停止与拒绝)。SKEL-R-03 停止成立。
2. 诊断确认了一种失败机制:对一个按规则应拒绝的请求调用 Fetch.failRequest 时,该请求已被浏览器取消(导航切换),CDP 返回请求 ID 无效,随后整体停止并关闭浏览器;后续 read 失败、TargetClosedError 均为其下游。
3. 设计方批准一处窄化(用户已同意):installGuards 中,仅当 operation 为 Fetch.failRequest 且 observeFailure 的分类结果为 REQUEST_ID_INVALID 时,不调用 onStop,改为向 trace 追加 {action: 'DENY_TARGET_GONE', phase, stage, path(pathShape), generation};其它任何操作(Fetch.continueRequest、Fetch.continueResponse)的任何失败,以及 Fetch.failRequest 的其它任何类别,一律照旧 onStop('FETCH_CONTINUE_FAILED')。理由:failRequest 只用于被拒请求;暂停中的请求未经放行不会发出,ID 已失效说明浏览器已丢弃它,不会到达服务器。
4. 为此 observeFailure 需返回分类结果,或另提供同一分类函数供判断;"只保留第一条起因"的规则只约束 OPERATION_FAILED 记录,DENY_TARGET_GONE 每次都记。
5. 该改动变更 P5Q 冻结稿的一条停止条件,作为本裁定的一次性例外登记;design.md 第 4.6 节之后追加一条说明。代理 sha256 与前缀 hash 随之变化,登记前后值。
6. 计时与调查用例规则补充:C8 调查用例的任一场景若出现 OPERATION_FAILED 且 operation=Fetch.failRequest、category=REQUEST_ID_INVALID,视为本裁定已处理的已知形态;修复后该形态不应再导致停止,若仍导致停止即为缺陷。

### 21.1 SKEL-R-05:既有代理测试不可改与新规则冲突

基线`46db465`;开工已重读第20节与`diagnostics/stop-report-SKEL-R-03.md`。
第20节未验收状态为当时事实,其诊断实现现由SKEL-R-04第1项验收。
本轮在改生产代码之前发现:第二步第3项要求“既有代理测试与允许/拒绝矩阵不改且全部通过”,
但`tests/node/test_qb_read_failure_diagnostics.mjs`有三处既有断言与第3项新规则相反:

| 既有Node用例 | 当前断言 | 按本裁定的新结果 |
|---|---|---|
| `rejected Fetch.failRequest still stops and records fixed metadata` | :40,stops为[FETCH_CONTINUE_FAILED] | stops应为[];两个continue参数仍应停止 |
| `capture scheduling phase and generation, keep first rejection only` | :60,目标关闭后再请求ID无效,stops为两个FETCH_CONTINUE_FAILED | 只有第一次停止,第二次记DENY_TARGET_GONE |
| `read navigation cancellation concurrent with a rejected Fetch keeps initiating failure` | :96,无效ID的failRequest触发停止 | 该Fetch不停止;导航取消原异常路径不变 |

这三项均由既有pytest nodeid
`tests/unit/test_qb_read_failure_diagnostics.py::test_node_read_failure_diagnostics`
执行。不能通过添加新测试使相反的旧断言同时成立;也不能按调用者/测试名特殊处理。
停止报告与离线原树验证证据在`evidence/read-failure/fix/`。
候选最小裁定:允许只更新上述三处停止次数期望及新增DENY_TARGET_GONE断言,
保留原参数集合、pytest nodeid及其它断言,尤其两个continue与其它类别仍停止;
其余既有矩阵不改。候选文字diff在停止报告中,本轮未实施。

生产/测试/代理/驱动/design.md/冻结稿均未修改;尚未启动40次采样、四组安全或
完整全仓门禁,不以局部验证代替用户要求的完整门禁。未使用-x运行全仓。
未运行真实QuickBuild/Gerrit/gbs。等待设计方澄清后再执行实现与全部验收。

原树离线验证:`fix/baseline-node.stdout.log`为17 passed/0 failed/0 skipped;
`fix/baseline-facts.json`记录三处原断言、20核负载前后0.58/0.89/1.04及
所有已跟踪skill/test/frozen/design文件与46db465逐字节一致。代理diff为0行;
全文hash前后均`d0e99f7e4caf11104920ddfe7a569a75e100c5a1dc44a3a916d73ef2bacbf823`,
前缀hash前后均`3bb1c0cc2fbfcb20aef324c8b8a703f06f40a438211317e0e96f2ba30f2be4c2`。
尚未执行的新用例、安全组、40次采样和完整门禁不计作通过。
