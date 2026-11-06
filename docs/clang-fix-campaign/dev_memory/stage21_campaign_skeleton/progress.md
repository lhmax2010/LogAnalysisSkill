# Stage21 Clang Campaign Skeleton

日期:2026-11-05。状态:**恢复第1至4批离线完成;RESTORE-24关闭RESTORE-23,第三/四批最终树3501 passed、0 failed、1既有skip(第45、46节);首次真实发现待另行裁定**。RESTORE-19由RESTORE-20两命令文件交接处置;RESTORE-21由RESTORE-22处置;RESTORE-17由RESTORE-18处置,live-04原证据保留;RESTORE-15由RESTORE-16处置(第40节),live-03原失败证据保留;RESTORE-13由RESTORE-14处置(第38节);RESTORE-11由RESTORE-12裁定处置(第37节),泄漏正文已后处理;SKEL-RESTORE-09由RESTORE-10处置(第36节);SKEL-RESTORE-03/05分别由SKEL-RESTORE-04/06关闭(第30/32节);审核两处修改与D2E补修已随恢复第2批同轮验收。此前骨架离线收尾结论保留,真实第3.5/4批仍延后。[收尾记录](../../review/campaign-skeleton-closeout.md)。
第1批开工基线`accd7f4`,第2批开工基线`5b9ecea`,分支`clang-fix-campaign`。
最新真机试运行:RESTORE-25/27唯一一次qb-discover以DISCOVERY_REPORT_AMBIGUOUS/REPORT_STRUCTURE停止(第49节);未运行dry-run,不重试。RESTORE-26已由RESTORE-27处置。
当前任务:RESTORE-33重新验收通过:三次单独重跑全过,完整pytest 3549 passed/0 failed/1既有skip(第52节)。RESTORE-30/32原始证据保留;证据提交推送后等待用户确认开始,未执行真机r02。
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
| 3.5 | 经后续批准的真实gbs单包干跑,不推送/不登录QB | 延后;SKEL-CLOSE-01,未执行、未验收通过 |
| 4 | 同包sandbox推送、QB与审核提交,另行人工授权 | 延后;SKEL-CLOSE-01,未执行、未验收通过 |

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
- `tests/unit/test_qb_browser_node.py::test_node_c2c_trusted_reads_and_fields[test_qb_browser_fields.mjs]`,由SKEL-RESTORE-14(第38节)新增,三次单独重跑全部通过方可放行。C8后续改为观测项,按SKEL-R-08。

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

## 22. 实施裁定 SKEL-R-06:诊断测试期望更新

1. SKEL-R-05 停止成立。tests/node/test_qb_read_failure_diagnostics.mjs 第 40、60、96 行附近的断言来自 SKEL-R-02 本轮新增(46db465),记录的是旧停止规则,不属于 P5Q 冻结时的既有安全测试;按 SKEL-R-04 允许更新,仅限这三处:
   a. 第 40 行所在参数化用例:仅 method 为 Fetch.failRequest 时,期望改为 stops 为空、trace 含一条 DENY_TARGET_GONE(phase、stage、path、generation 与原诊断一致);Fetch.continueRequest 与 Fetch.continueResponse 两个参数的期望不变(仍停止、仍记 OPERATION_FAILED)。敏感值扫描保留。
   b. 第 60 行用例:第一次 Session closed 仍停止;第二次 Invalid requestId 改为不停止、记 DENY_TARGET_GONE;stops 期望从两次改为一次;OPERATION_FAILED 仍只一条且为 TARGET_OR_SESSION_CLOSED。
   c. 第 96 行用例:failRequest 的请求 ID 无效不再停止,记 DENY_TARGET_GONE;read 仍以 QB_BROWSER_UNAVAILABLE 失败;OPERATION_FAILED 的第一条起因改为 page.goto 的 NAVIGATION_INTERRUPTED;stops 期望为空。用例名可改为反映新语义,nodeid 变化逐条登记。
2. 这三处之外的任何既有测试仍不得改;若还有其它冲突,停止并报告。

基线`8d60851`;已重读`fix/stop-report-SKEL-R-05.md`,其测试冲突由本裁定关闭。
继续SKEL-R-04全部实施与验收;证据在`evidence/read-failure/fix/implementation/`,
原停止报告与原树验证保留。完整全仓不带-x,每次采样使用独立目录。

### 22.1 实现边界与三处断言更新

生产仅修改`tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs`的
`installGuards`(:191的observeFailure与:229的guarded),diff为+25/-16。
分类正则不变;先分类再决定是否记录,使已失效的拒绝对象不占用首条
OPERATION_FAILED。仅Fetch.failRequest/REQUEST_ID_INVALID记DENY_TARGET_GONE
并跳过onStop,其它操作和类别照旧。诊断写入异常仍不改变判断结果。
Policy、FrameOwnership、阶段文法、installGuards之外的代理字节、驱动和
所有其它生产模块保持与8d60851一致。`integrity.json`与`production.diff`为证。
design.md仅在第4.6节后的修订序列追加本次例外,冻结稿不改。

| tests/node/test_qb_read_failure_diagnostics.mjs | 原断言 | 按SKEL-R-06更新 |
|---|---|---|
| :40 参数化Fetch用例 | 三种方法均stops=[FETCH_CONTINUE_FAILED],记OP | 仅failRequest为stops=[],记一条精确DENY;两种continue仍停止并记OP;敏感值扫描保留 |
| :63 两次失败 | 两次停止,仅首条OP | 第一次Session closed停止;第二次Invalid requestId不停止并记DENY;stops只有一次,首条OP仍TARGET_OR_SESSION_CLOSED |
| :91 导航取消与拒绝 | failRequest无效ID停止并占首条OP | stops=[],拒绝记DENY;read仍QB_BROWSER_UNAVAILABLE,首条OP为page.goto/NAVIGATION_INTERRUPTED |

该文件diff为+14/-6,三段之外逐字节不变。仅Node用例名从
`read navigation cancellation concurrent with a rejected Fetch keeps initiating failure`
改为`read navigation cancellation after a gone deny records navigation as first failure`;
pytest nodeid不变,不改参数化集合。其它既有测试不改。

新增用例映射:
- `tests/node/test_qb_deny_target_gone.mjs:31`:3种Fetch操作乘7种固定错误类别,
  21例矩阵;仅一格不停止,含敏感值扫描。
- 同文件:49、:64:重复DENY逐次记录且不占首条OP;诊断写入抛错不影响结果。
- `tests/node/p5q_deny_target_gone_browser.mjs:45`:真实Chromium中取消暂停导航,
  再调用真实Fetch.failRequest,两次均返回失效ID;假服务器实收这两请求均为0。
  同会话继续校验普通拒绝、禁止动作、未知帧与307/308,不以伪造CDP错误代替零请求证据。
- `tests/unit/test_qb_deny_target_gone.py`:新增2个pytest入口,既有3098个nodeid全部保留,
  collect总数3100。新增Node矩阵23例,真实浏览器场景1例。

| SHA256 | 改前8d60851 | 本轮实现 |
|---|---|---|
| 代理全文 | `d0e99f7e4caf11104920ddfe7a569a75e100c5a1dc44a3a916d73ef2bacbf823` | `044ae065ee223093b4d63e3444f37a812dd2831266e6334fac526bf116ec7723` |
| 代理前缀(截至export class Agent之前) | `3bb1c0cc2fbfcb20aef324c8b8a703f06f40a438211317e0e96f2ba30f2be4c2` | `9b7796f02f3e65f97c6f68bbe169109b8bd885854c98bb976d4d55ae5a2bc006` |

### 22.2 验收结果与采样停止

以下路径相对`evidence/read-failure/fix/implementation/`。

| 项目 | 结果 | 证据 |
|---|---|---|
| 定向pytest | 223 passed/0 failed/0 skipped | focused/pytest.xml |
| Node新增/授权更新/既有矩阵 | 新增23、更新后的诊断17、既有矩阵163、停止类别16、静态与负例183全部通过 | focused/stdout.log |
| 新增真实浏览器场景 | 两次真实failRequest失效且服务器0请求;后续拒绝与307/308仍有效 | focused/deny-gone/browser.json |
| P5Q四组安全 | 4/4,本机HTTPS与虚拟显示,无真机访问 | safety/stdout.log |
| mypy/ruff/import-linter/design | 161文件无错/通过/7 kept 0 broken/0 problem | mypy/、ruff-recheck/、imports/、design/ |
| nodeid | 3098全部保留,新增2,共3100;collect无错误 | collect/、integrity.json |
| C8独立采样 | 4/20已运行:3 PASS、1 FAIL;停止,余16未运行 | c8-01至c8-04、sampling-results.md |
| C5a late-build独立采样 | 0/20,NOT_RUN_STOPPED | results.json |
| 全仓完整门禁 | NOT_RUN_STOPPED;未用-x,不以定向数量代替完整门禁 | 本节及停止报告 |

| C8轮次 | 结果 | 秒 | DENY_TARGET_GONE | FETCH_CONTINUE_FAILED | loadavg前/后(1,5,15分钟) |
|---|---|---:|---:|---:|---|
| 01 | PASS | 182.39 | 0 | 0 | 0.70/0.92/1.08 -> 0.46/0.77/0.99 |
| 02 | PASS | 182.92 | 0 | 0 | 0.46/0.77/0.99 -> 1.96/1.19/1.10 |
| 03 | PASS | 184.38 | 0 | 0 | 1.96/1.19/1.10 -> 3.76/2.48/1.64 |
| 04 | FAIL | 203.52 | 2 | 0 | 3.76/2.48/1.64 -> 9.94/6.42/3.37 |

20核,每次CPU前10进程仅名与占用、UTC起止、argv、exit均在各command.json。
第4轮停于第5场景racing-wicket-navigation,只收到GET /signin 200,
无登录POST、无submit、无read;harness为TargetClosedError/OTHER_FRAMEWORK_ERROR。
trace只有框架自检,没有AGENT_STOPPED,其failure_category记NOT_COLLECTED。
第4轮余6场景没有运行;不将用例名中的racing推断为已进入提交后的导航竞争。
原5次基线仅racing-meta-refresh/FETCH_CONTINUE_FAILED,此为新形态,
不在SKEL-R-04第6项的已知失效请求停止范围内。按既有门禁规则停止,不重跑。
报告:[SKEL-R-07](evidence/read-failure/fix/stop-report-SKEL-R-07.md)。

### 22.3 读取失败观测表增量

| 观测 | 固定错误/断言 | 新诊断与位置 | 处置 |
|---|---|---|---|
| c8-04/racing-meta-refresh(场景完成) | read QB_BROWSER_UNAVAILABLE/UNKNOWN;runtime_failure=null,浏览器仍连接 | page.goto/NAVIGATION_INTERRUPTED为首条OP;随后idle/request /wicket/page generation6的DENY两条;无FETCH_CONTINUE_FAILED | 自然观察到本次窄化有效;保留原导航失败语义 |
| c8-04/racing-wicket-navigation(用例失败) | assert result.returncode==0实际1;内部harness_failure应未定义,实际TargetClosedError/OTHER_FRAMEWORK_ERROR | login阶段,无OP/AGENT_STOPPED;category NOT_COLLECTED;reads=[]、synthetic_submissions=0 | 新失败形态,SKEL-R-07停止,未归因于负载或修复 |

新增诊断完整键集合仍为action/phase/stage/path/generation;无query或错误原文。
两条自然DENY的来源为`c8-04/c8/racing-meta-refresh.json:1161`及:1168;
失败场景另见`racing-wicket-navigation.json:50`,不能串用两个场景的诊断。

证据包装器有两次独立错误,不隐去:ruff首次错误附加了pytest的junit参数(exit2),
修复包装器识别后ruff-recheck通过;第一次C8的pytest通过,包装器因summary.json为
列表而汇总失败。该原始目录保留为wrapper-error-c8-01,不计正式4次,包装器修复
仅跳过非对象汇总文件,没有修改测试、断言、阈值或生产代码。

最终收尾:`implementation/final-checks.json`记录源码/文档diff --check通过,
设计检查0 problem;4条DENY(本机专门场景2条+自然采样2条)与34条OP的
键集合/封闭类别/敏感值扫描通过。/dev/shm中P5Q profile与本轮证书夹具残留均0,
P5Q代理/Chromium进程0;未创建临时代理副本或加压进程,无额外清理动作。
未完成的40次采样与完整全仓门禁明确留待裁定,未进入下一批。
全暂存树diff --check返回2,仅逐字authorized-test.diff中的两条空上下文行、
原始pytest.xml与stdout.log各一条断言输出行的行尾空白;为保留证据不改原字节。
人工源码与文档检查为0,两者不混报。

## 23. 实施裁定 SKEL-R-08:调查观测与验收续跑

### 一、结论
1. 接受 5b41ee9 的窄化实现:仅 Fetch.failRequest 且类别为 REQUEST_ID_INVALID 时不停止、逐次记 DENY_TARGET_GONE、不占第一条 OPERATION_FAILED;其它操作与类别保持原停止规则。不再修改 installGuards。
2. SKEL-R-07 的失败(racing-wicket-navigation 登录阶段 TargetClosedError,无 OPERATION_FAILED/DENY_TARGET_GONE/AGENT_STOPPED)判定为调查用竞争测试自身在负载下的不稳定,与本次修复无因果证据。原始失败证据保留,不得覆盖或删除。

### 二、C8 调查测试改为观测项(覆盖 SKEL-B1-03 第3项、SKEL-B1-05 第4项中对 C8 的“新形态即停”约束)
1. tests/unit/test_p5q_c8_investigation.py 及其 Node 入口的断言、场景、时限一律不改。它的失败不再阻断门禁,改为逐次登记到“读取失败观测表”,记录:采样序号、场景、阶段、harness_failure 类别、trace 中各 action 计数、采样前后 loadavg。
2. 授权只对调查 harness(tests/node/p5q_c8_investigation.mjs)增加离线观测字段:固定的模拟登录步骤名、login 命令应答的固定字段、页面关闭与浏览器断开的时间点。不记录错误原文、页面内容或任何凭据;不改断言、不改超时、不吞异常。改动单独提交,并在 integrity.json 中列明改了哪几行。
3. 以下任一情况仍必须停止并出报告:
   a) 任何采样出现 AGENT_STOPPED 或 FETCH_CONTINUE_FAILED,且其 trace 中第一条导致停止的失败是 Fetch.failRequest/REQUEST_ID_INVALID(说明窄化失效);
   b) 同一种非豁免新形态(场景+阶段+harness_failure 类别相同)在 20 次中出现 3 次或以上;
   c) 任何采样出现 profile_removed=false 或残留浏览器进程。

### 三、继续执行(使用 5b41ee9 + 上面第二.2项 harness 观测改动后的树)
1. 负载约束:每次采样开始前读取 1 分钟 loadavg,超过 6 则等待至低于 6 再开始,等待时间写入 command.json。不得结束他人进程、不得新增加压进程。如果连续等待超过 30 分钟仍降不下来,暂停并报告当前机器状态。
2. C8 采样:从第 5 次继续到第 20 次(前 4 次结果原样计入,第 4 次记为观测表首条)。全部 20 次的通过/失败逐次留存。
3. C5a late-build 采样 20 次,按严格标准:FETCH_CONTINUE_FAILED 必须为 0;任何失败只有在属于既有 timing-sensitive 名单、且 3 次单独重跑全部通过时才可豁免,否则停止。
4. 以上完成且无第二.3项停止条件后,跑一次完整全仓门禁(不加 -x)。全仓中 C8 调查测试若失败,按第二.1项登记,不计入门禁失败;其余用例按原规则。

### 四、交付
1. progress.md 更新:本裁定、C8 20 次与 late-build 20 次汇总、观测表、全仓结果、各次 loadavg。
2. 证据放 evidence/read-failure/fix/ 下按次分目录,命名延续现有规则。
3. 完成后报告是否满足 SKEL-R-04 验收;不进入第 3.5 批,等待下一步裁定。
4. 不运行真机 QuickBuild、Gerrit 或真实 gbs。

### 23.1 本轮边界与观测字段

基线5b41ee9,已重读第22节与SKEL-R-07停止报告。旧报告与implementation中
已归档的c8-01至c8-04全部原样保留。新增元数据与汇总在
`evidence/read-failure/fix/implementation/r08/`;采样仍用implementation/c8-05至20、
late-01至20,全仓full-r08,均新建目录,不覆盖历史证据。

唯一测试源改动为`tests/node/p5q_c8_investigation.mjs`:
- login_observation.steps:LOGIN_COMMAND_STARTED/FILL_USER/FILL_PASSWORD/
  CLICK_LOGIN/AWAIT_LOGIN/LOGIN_COMPLETE,每项附场景开始后的单调毫秒。
- login_observation.response:elapsed_ms、ok、error、failure_category;错误与停止类别
  只取固定枚举,未取得为null,不记录login应答中的自由文本或页面内容。
- lifecycle_observation:PAGE_CLOSED/BROWSER_DISCONNECTED、当前phase与单调毫秒。
  只监听事件,不改变关闭、异常传播、等待或测试断言。

代理与全部生产代码不改;assert语句、main场景列表、超时与模拟登录操作原样。
单独提交前以node --check与`r08/integrity.json`校验;运行结果后续单独登记。
首次核对:Node语法检查exit0,harness为+23/-4,8个diff hunk逐项列入integrity.json;
assert行、场景列表、open_form之后全部代码逐字相同,133个历史证据文件未改。
代理全文hash仍044ae065ee223093b4d63e3444f37a812dd2831266e6334fac526bf116ec7723,
前缀仍9b7796f02f3e65f97c6f68bbe169109b8bd885854c98bb976d4d55ae5a2bc006。

### 23.2 40次采样与读取失败观测表

harness观测单独提交并推送为`fb549ea`。本轮证据路径下文相对
`evidence/read-failure/fix/implementation/`。
C8从05续到20,16次全PASS;连同原01至04,累计19 PASS/1 FAIL/0 skip。
第04次仍为原始FAIL,只按本裁定一.2计作不阻断观测,不改其exit或原日志。
20次共214份场景记录;第04次余6场景原本未运行,本轮不补写。
late-build 01至20全部PASS,0失败/0 skip,每次FETCH_CONTINUE_FAILED均0,
没有触发三次单独重跑豁免。两组均无profile_removed=false或P5Q进程残留。

| 采样 | 场景/阶段 | harness_failure | trace各action计数 | loadavg前 -> 后(1/5/15分钟) | 判定 |
|---|---|---|---|---|---|
| c8-04(观测首条,原证据) | racing-wicket-navigation/login | TargetClosedError/OTHER_FRAMEWORK_ERROR | FRAMEWORK_SELF_TEST=1;其它0 | 3.76/2.48/1.64 -> 9.94/6.42/3.37 | SKEL-R-08一.2已接受;不重跑、不覆盖 |
| c8-11(新增有效窄化观测) | delay-only-control/submit | 无 | DENIED=41,DENY_TARGET_GONE=1,FRAMEWORK_SELF_TEST=1,IDENTITY_OUTSIDE_REGISTERED=1;其它0 | 4.47/1.61/1.27 -> 3.70/2.65/1.74 | 后续read成功HTTP200,runtime_failure=null,浏览器保持连接 |

完整每场景action计数、阶段、harness类别、登录步骤与关闭时点在
`r08/results.json`的rows/cases;失败观测在observations。非豁免新形态计数为空,
没有任何失效failRequest引起停止的样本。c8-11的DENY来源为
`c8-11/c8/delay-only-control.json:988`,submit/request,/wicket/page,generation4。
加上原c8-04其它场景的2条,累计自然DENY=3,FETCH_CONTINUE_FAILED=0。

所有新采样在开始前重新读取1分钟loadavg,均低于6,实际等待均0秒;
每次command.json有load_wait字段,等待采样原文另存`r08/load-waits/`。
原01至04的等待时间未采集,保持NOT_COLLECTED,不倒填0。没有终止他人进程,
没有新增加压进程。下表列每次1分钟loadavg前后,完整1/5/15分钟值与耗时见
`r08/sampling-results.md`和各次command.json;CPU为20核,top10只记录名称与占用。

| 序号 | C8结果 | C8 load前 -> 后 | late-build结果 | late load前 -> 后 |
|---|---|---|---|---|
| 01 | PASS | 0.70 -> 0.46 | PASS | 0.04 -> 0.41 |
| 02 | PASS | 0.46 -> 1.96 | PASS | 0.41 -> 0.49 |
| 03 | PASS | 1.96 -> 3.76 | PASS | 0.49 -> 0.98 |
| 04 | FAIL(已接受观测) | 3.76 -> 9.94 | PASS | 0.98 -> 0.83 |
| 05 | PASS | 0.85 -> 0.69 | PASS | 0.83 -> 0.59 |
| 06 | PASS | 0.69 -> 0.64 | PASS | 0.59 -> 0.53 |
| 07 | PASS | 0.64 -> 0.48 | PASS | 0.53 -> 0.64 |
| 08 | PASS | 0.48 -> 0.60 | PASS | 0.64 -> 0.91 |
| 09 | PASS | 0.60 -> 0.46 | PASS | 0.91 -> 0.65 |
| 10 | PASS | 0.46 -> 4.47 | PASS | 0.65 -> 0.65 |
| 11 | PASS | 4.47 -> 3.70 | PASS | 0.65 -> 0.80 |
| 12 | PASS | 3.70 -> 1.32 | PASS | 0.80 -> 0.72 |
| 13 | PASS | 1.32 -> 0.69 | PASS | 0.72 -> 0.88 |
| 14 | PASS | 0.69 -> 0.55 | PASS | 0.88 -> 0.91 |
| 15 | PASS | 0.55 -> 0.88 | PASS | 0.91 -> 0.85 |
| 16 | PASS | 0.88 -> 0.87 | PASS | 0.85 -> 0.61 |
| 17 | PASS | 0.87 -> 0.69 | PASS | 0.61 -> 0.91 |
| 18 | PASS | 0.69 -> 0.33 | PASS | 0.91 -> 0.75 |
| 19 | PASS | 0.33 -> 0.24 | PASS | 0.75 -> 0.71 |
| 20 | PASS | 0.24 -> 0.04 | PASS | 0.71 -> 0.58 |

### 23.3 完整门禁与交付结论

全仓命令:`.venv/bin/python tests/run_quiet.py -q --junitxml=<implementation/full-r08/pytest.xml>`。
原始完整argv、UTC起止、exit、CPU前10、负载与stdout/stderr在`full-r08/`。
没有-x/--maxfail,没有跳过调查用例或计时名单;原始exit=0,
**3099 passed/0 failed/0 error/1 skipped**,3100用例全部运行到结尾。
UTC 2026-11-04 02:28:07.588938起,包装器1061.027秒;pytest1060.65秒。
20核,loadavg前0.53/0.62/0.72,后1.17/1.00/0.98;启动无需负载等待。
唯一skip仍为`test_case_insensitive_bypass_is_platform_specific`,理由
`case-sensitive filesystem`;非新增skip。全仓C8调查通过,未调用观测豁免;
6个C5a参数全部通过,未调用3次重跑豁免,`r08/full-verdict.json`的decisions为空。

| 门禁 | 结果 | 证据 |
|---|---|---|
| 完整pytest | 3099/0/1(通过/失败/跳过),exit0 | full-r08/pytest.xml、stdout.log |
| P5Q四组本机安全 | 全仓再次运行test_node_c2b_local_https_safety并通过,内部断言4 passed/0 failed | full-r08/pytest.xml;先前专跑原始四组日志safety/保持不变 |
| 代理矩阵、诊断、静态负例、新增DENY用例 | 既有包装用例全部包含在完整pytest且通过 | full-r08/pytest.xml |
| mypy | 161 source files,无错 | r08/gates/mypy/ |
| ruff | All checks passed | r08/gates/ruff/ |
| import-linter | 7 kept/0 broken | r08/gates/imports/ |
| design检查器 | 0 problem | r08/gates/design/ |
| collect/nodeid | 前后均3100,新增0/删除0,collect错误0 | r08/gates/collect/、r08/final.json |
| 生产与冻结稿 | 全部未改,代理全文/前缀同5b41ee9 | r08/integrity.json、r08/final.json |
| 原证据保留 | 133个旧implementation证据文件未修改,SKEL-R-07原报告保留 | r08/integrity.json |
| 最终残留 | P5Q profile=0,代理/Chromium进程=0 | r08/final.json |

全仓计时名单耗时:build22.944s,error-created23.060s,error-no-build16.718s,
no-navigation83.062s,delayed-build22.947s,late-build23.333s,均原次PASS;
这些是用例总耗时,不是关闭耗时,不据83秒推断关闭失败。
本轮所有模拟浏览器均在私有虚拟显示中,只访问本机假HTTPS服务;
未运行真机QuickBuild、真实Gerrit或真实gbs,未启动额外负载或终止他人进程。

结论:**按SKEL-R-08的验收口径满足SKEL-R-04**。C8历史第04次原始失败不改写为
PASS,其非阻断处置有明确裁定;新采样、late-build及完整门禁没有新增失败。
没有窄化失效、没有3次非豁免同形态、没有残留条件。未放宽任何额外规则,
未再修改installGuards。交付停在本阶段,等待下一步裁定,不进入第3.5批。
收尾diff检查:源码与文档exit0;全暂存树exit2,仅103条本机假服务器原始
qb_evidence HTML的行尾空白,为保留原字节不改写。详见`r08/final.json`的
whitespace字段。暂存文件无state.db二进制、证书私钥或凭据文件。

## 24. SKEL-B3.5-01:选包候选筛选与环境摸底

2026-11-04上午(Asia/Shanghai),基线`fd4c6f6`;按用户裁定只读筛选,
不是第3.5批开工。权威冻结稿第7节的包选择要求保持不变。
范围:本仓库历史证据、开发机既有CI日志/修复报告/本地shelve记录;
最多5个对象,真实gbs_analyzer离线解析,环境只读查询。
禁止gbs build、所有campaign命令、浏览器/QB登录、Gerrit访问与推送、
结束进程、清缓存/GBS-ROOT/swap;不往llvm-optimize写任何内容。
本轮实际符合上述边界,Git交付仅本仓库clang-fix-campaign。

证据根:`evidence/batch3.5/selection/`。
详细目录搜索范围见[search.md](evidence/batch3.5/selection/search.md),
预筛表与来源行号见[candidates.md](evidence/batch3.5/selection/candidates.md),
资源见[environment.md](evidence/batch3.5/selection/environment.md)。

### 24.1 筛选事实

**没有找到同时满足全部条件的包;不选一个不合格包凑数。**
已解析三个Base预筛对象,均来自父QB1204735/子1204736:

| 补证排序 | 包 | analyzer exit / verdict / primary | 未入选原因 |
|---|---|---|---|
| 1 | elfutils | 0 / needs_llm / raw_error,%build,autopoint失败 | 另有OBS r2的2行源码修法,但不是shelve,也不对应这份日志的首错 |
| 2 | zlib | 0 / needs_llm / rpm_phase,%install | 原日志toybox find/xargs不存在,未证实Clang编译首错,没有对应shelve/diff |
| 3 | libtirpc | 0 / needs_llm / rpm_phase,%install | 同类安装工具失败;320处非致命warning不作编译失败;没有对应shelve/diff |

每包真实analyzer只运行一次,未改代码、未改原始日志;argv/UTC/exit/stdout/stderr与
原始JSON/Markdown/trace/perf在`selection/analyzer/<包>/`。
`source-facts.json`有三个输入前后hash、三架构状态与历史成功耗时的原行;
`source-excerpts.json`有配置/人工修法/CL汇总的限定摘录与源文件hash。
base可确定为`tizen-base-toolchain_20261013.024319`,但实际`./build.conf`字节缺失;
已有base发布配置与输出仓库配置hash不同,不能任选一份声称完全一致。

实际shelve汇总主要来自VD产品线;libdeflate14337558等不能直接迁移成Base候选,
其报告指向的`/home1/chengkai/.../quickbuild`在本机不存在。
glibc/GCC部分链接、Unified的lld失败、历史故障注入或合成PASS均没有冒充合格证据。
推荐执行包:暂无。仅建议优先补elfutils同源材料,不授权编辑/建档/编译。
缺失:同一Base编译首错的QB号+本地日志、对应shelve完整diff与源码revision、
实际build.conf原文/等价性证据;不能把文件数写成改动行数,未知行数明确UNKNOWN。

### 24.2 环境与资源

采样约11:29:20核,loadavg1.09/1.30/0.82;RAM30Gi,available16Gi,
swap4Gi已用3.9Gi、余109Mi;/home盘余133G、已用93%。仓库与所列GBS-ROOT同盘。
进程只记名称与RSS前15,无命令行参数。vmstat后两个1秒区间si/so为4/0、0/0,
不据满swap推断正在持续换出,也不据两秒采样保证未来无压力。
三个既有scratch可读du共约14.7GiB;受限目录Permission denied导致exit1,
只作为下界,没有提权或清理。

尚无所选包实测峰值。对zlib/libtirpc级小包的顺序三架构初步规划为
预留8GiB available和40GiB新增磁盘,不是已测上限/开跑参数;
当前余量在此规划之上,本轮无需用户清内存或swap。选包后仍须重测,
swap余量很小、依赖闭包未确定;如执行前持续换出,由用户先释放自己的负载。
不会因为顺序编译而释放后续第4批需要保留的副本。

### 24.3 交付边界与停点

仅新增筛选证据与本节,未改生产/测试/冻结稿/状态库,未运行全仓测试或campaign命令。
三次analyzer输入hash不变,三次exit0但均needs_llm;源码与文档差异检查、
JSON可解析性、限定凭据扫描见`selection/validation.json`。
手写文档diff检查通过;全暂存树diff检查exit2,仅三个analyzer原始
evidence_packet.md的EOF多空行,按原始输出要求保留,未改写。
搜索不是穷尽所有机器,结论仅对实际本地材料有效。
资源估算因未选包只能是有明确假设的规划,不伪造真实峰值。
停止于筛选交付,等待用户选包与第3.5批执行裁定。

## 25. 实施裁定 SKEL-CLOSE-01:骨架收尾

### 25.1 设计方裁定

1. 第 3.5 批(真实 gbs 单包干跑)与第 4 批(真实 sandbox 推送、QuickBuild、review-submit)本阶段不执行,状态记为“延后”,不是“通过”。
2. 延后理由:SKEL-B3.5-01 预筛合格候选为 0(96b5776);对应 QuickBuild 实际使用的 build.conf 原件在本地不可得,无法满足“本地验证条件须与 QuickBuild 一致”;后续构建后端将接入 COSMOS build,真实端到端届时在真实包上一并执行。
3. 骨架阶段以离线验收收尾:第 1、2、3 批验收(5b9ecea、1a4ed25、a58494b)+ 读取失败修复验收(5b41ee9、fb549ea、fd4c6f6,按 SKEL-R-08 口径)。
4. 冻结稿 v1.3 不改正文;在 design.md 第 4.6 节末尾追加“收尾状态”小段,写明第 3.5、4 批延后及本裁定编号。

### 25.2 收尾交付与边界

[campaign-skeleton-closeout.md](../../review/campaign-skeleton-closeout.md)分六节登记交付、裁剪、
验收、未经真机验证项、遗留与观测项、以后补跑的进入条件。INDEX与本文件状态已同步。
最后一次全仓结果沿用`fd4c6f6`的3099 passed/0 failed/1既有skip,不是本轮重新执行的结果。
第2批原始失败与3次重跑、第4次C8历史失败及全部采样证据均保留,未以收尾改写历史结论。
资源8GiB available/40GiB新增磁盘仅为selection/environment.md的小包规划估算,
不是实测下限;选包与后续执行裁定必须重新校准。真实analyzer三次均needs_llm,
不把“解析进程exit0”登记为真实Clang失败分类已验证。

本轮只改四份文档,不改生产代码、测试、冻结稿、状态库或历史证据。
不运行gbs build、任何campaign命令、QuickBuild登录、Gerrit推送或refs/for fetch;
不向llvm-optimize写入内容。提交署名沿用本机全局配置。
文档检查结果在本节末尾登记后,同一commit推送clang-fix-campaign并停止。

### 25.3 本轮检查

- `check_design_doc.py docs/clang-fix-campaign/design.md`:exit0,0 problem。
- 新收尾文档27个仓内链接逐个检查,全部存在;本次四份文档的`git diff --cached --check`通过。
- v1.3冻结稿SHA256仍为`1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`,正文零改动。
- 本轮不运行pytest或任何业务命令;生产与测试零改动。与SKEL-CLOSE-01不一致或做不到之处:无。
- SKEL-CLOSE-02:在收尾记录第3节第2批结论后按裁定补充原始FETCH_CONTINUE_FAILED签名、读取失败缺陷而非计时问题及5b41ee9修复并按SKEL-R-08验收的说明;其余内容不改,不运行任何业务命令。

## 26. SKEL-RESTORE-01:恢复项开工对照与停止

### 26.1 权威输入与计划

收到四批离线恢复任务,以design.md指定契约与本次明确偏差为准;已通读所列章节。
基线`f93b890`,此前SKEL-CLOSE-01/02记录不删除,真实第3.5/4批仍延后。
恢复批次不同于此前骨架批次:恢复1=D2E,恢复2=KB/sync/propose-fix,
恢复3=发现(先URL取证、提交后停等裁定),恢复4=剧本/模板/E2E/文档。
各批须独立提交推送并通过全仓门禁,未验收不得声称已恢复。

| 权威条文 | 本轮逐条核对与实施落点 | 当前结论 |
|---|---|---|
| design 3.3第1步 | failed_arches/primary → 日志 → analyzer证据/sha → create_unit同事务锚定;恢复3复用intake | 已读,尚未实现 |
| design 3.4 kb schema | clang_kb/v1、七元dedupe、JSONL锁/原子写与promote;恢复2 core.kb | 已读,尚未实现 |
| design 3.4 guard | 真实tizen_build_verify.edit_spec_guard;路径/符号链接/唯一性/line/重叠;恢复1 core.diff_to_edit_spec | 已读,不自建guard |
| design 3.4 arch门 | 非白名单整unit拒绝、规范化优先序与拒绝落库;恢复3 | 已读,尚未实现 |
| design 3.5 T1/T2 | instance+CI_VERIFIED完整键、NEW不匹配、T2限5与稳定排序 | 已读,恢复2待实施 |
| design 3.5取材 | gerrit_ssh_base+gerrit_path与change_ref白名单,gerrit_url不执行 | 已读,仅本地假SSH验证 |
| design 4.1 D2E | repair执行包入口,0/2/4与DIFF_CONVERT_UNSUPPORTED;不支持形态显式reason | 已读,恢复1未启动实现 |
| design 4.1 kb query/append/promote | 固定双列表、幂等写入与单向promote;恢复2新执行包 | 已读,待实施 |
| design 7 Phase7 DoD | 全部不支持形态、真实guard拒绝/符号链接正例、多hunk与p4/git头 | 已读,未运行 |
| design 7 Phase8 DoD | 黄金向量parity、自建非私有归一化、normalizer_version、并发与损坏fail-closed | 已读,以该节D-5的细化为准,未实现 |
| design 7 Phase9 DoD | 发现加法扩展与旧模式回归;新人工浏览器会话先本地URL证据审批 | 已读,不得提前改代理 |
| design A2/3.7/4.1审核契约 | T1非抑制应为cherry_pick并有review资格;现有review仅接受generated/suppress且final仅code | 冲突,触发本任务第五.2条停止 |

本任务批准的有意偏差仅登记为待落地:KB_APPENDED改独立campaign-kb-sync与KB_SYNC事件;
历史人工修法允许origin=imported_shelve及该origin的verified_tree_sha为空;
发现不用Cookie文件而用人工登录的只读代理会话。尚未实现,不在design.md或收尾记录写成已恢复。
依赖合约不放宽、不加状态;不改四个提交/读取命令的现有拒绝规则;
不运行真实Gerrit/gbs/QuickBuild,不向llvm-optimize写内容。

### 26.2 开工停止与证据

状态:已由SKEL-RESTORE-02裁定关闭;以下原始停止事实与证据保留。

[停止报告](evidence/restore/stop-report-SKEL-RESTORE-01.md):T1全链路目标与review拒绝规则零改动不能同时满足。
review_submit.py第298行拒绝t1_cherry_pick来源,第314行拒绝cherry_pick最终策略;
design.md第182/1881/1147行与恢复任务第二.4.b、第四.2条要求该路径。
未把T1标成generated,未故意使转换失败,未改审核安全规则。

[只读探针](evidence/restore/probe-review-t1.py)真实调用guard/policy,随后求值未修改的两条AST条件:
generated→code通过两条件;t1_cherry_pick→cherry_pick被两条件拒绝;
suppress仍被A2拒绝。3向量断言通过,exit0,临时夹具已删除。
不是完整review CLI执行,无数据库/网络/推送。argv、UTC、stdout、stderr同目录归档。
候选是对review来源集合与A2集合授权两行窄修改,保留其它所有拒绝与抑制优先级;
具体diff、副作用、待补测试见报告,仅提案不实施。

尚未实施任何恢复批次,不运行全仓门禁;本次只提交登记/停止证据,等待设计方裁定。
检查:探针3向量通过、证据脚本ruff通过、design检查0 problem、暂存差异检查通过;
冻结稿SHA256仍为1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9。

## 27. 实施裁定 SKEL-RESTORE-02:T1审核资格与继续恢复

1. 停止报告属实,冲突源于 SKEL-RESTORE-01 第〇.2 条与第二.4.b/第四.2 条自相矛盾,责任在设计方。
2. 授权且仅授权 tizen-review-submit/scripts/tizen_review_submit/review_submit.py 两处改动,按停止报告第 3 节候选 diff:
   a) 来源检查接受 {"generated", "suppress", "t1_cherry_pick"};
   b) A2 质量门接受 fix_strategy_final ∈ {"code", "cherry_pick"} 且 reproduced。
   依据:design.md §1.4 A2(:182-185)与 §4.1 review-submit 第 3 步(:1881-1882)。其余检查(取锁、放弃屏障、聚合、QB 结果绑定、edit 字节、存量/重推一致、forbidden 零推送、TOCTOU、身份)一律不变。
3. SKEL-RESTORE-01 第〇.2 条修订为:除上述两处外,sandbox-submit、qb-trigger、qb-result-fetch、review-submit 的现有行为与拒绝规则不改;第三批浏览器代理改动仍按原第三.1 条先取证后停止。
4. 记录:design.md 第 4.6 节“恢复项落地裁定”小段加一条,说明骨架冻结稿第 5.3 节“修法来源只有 generated 与 suppress”随 T1 恢复而撤销,审核资格回到 design.md 原 A2;tizen-clang-campaign/SKILL.md 中“Source kind is only generated or suppress”一句在第四批同步改为三种来源及各自去向。

审核改动与指定6类测试随恢复第2批提交,不提前改动。原有六道重校验、放弃屏障、TOCTOU断言不改。
从恢复第1批开始按原顺序实施;恢复第3批URL形态取证完成后仍停止等裁定。

## 28. 恢复第1批:diff-to-edit-spec

基线56e74f0;权威为SKEL-RESTORE-01第一批、design.md第3.4/4.1/7节Phase7。
只实现转换器、共享CLI与新增离线测试;产物必须经真实edit_spec_guard,不改guard。
证据目录:evidence/restore/batch1/。

### 28.1 实施与覆盖

`tizen_campaign_core/diff_to_edit_spec.py`严格解析统一diff,统一判定唯一strip层级,
每hunk保留context/删除/新增原文,重复old保留line;拒绝模糊匹配与未支持元数据。
`tizen_campaign_repair/diff_cli.py`为共享命令适配,repair与ci_triage入口均调用同一函数。
输出前调用真实`edit_spec_guard`,原子发布JSON;不修改或应用到源码。
两份既有入口仅新增4行与3行,既有业务与测试断言不改。

新增`tests/unit/test_diff_to_edit_spec.py`最终64个用例,逐项见
[coverage.md](evidence/restore/batch1/coverage.md)。最初61个用例定向通过后,
补3个P4元数据用例(双路径重命名/binary拒绝、同路径revision对通过),最终定向64 passed。
第一轮全仓`full/`为3160 passed/0 failed/1既有skip,1129.84秒;
它在补3个用例前收集,不作为最终树的唯一验收,原证据保留。

最终collect为3164,原3100全部保留,新增64,删除0,见`integrity-final.json`与
`nodeids-*-final.txt`。mypy-final、ruff-final、imports-final、design-final均exit0;
依赖合约7 kept/0 broken,design检查0 problem。最终全仓`full-final/`为
3163 passed/0 failed/1既有skip,pytest耗时1076.48秒,包装进程1079.27秒;
负载(20核)从`1.98 4.83 6.87`到`2.90 2.65 3.91`。
skip仍是大小写敏感文件系统上的`test_case_insensitive_bypass_is_platform_specific`,无新增skip。
每轮完整运行,不加-x,command.json记录前后负载与CPU进程名。
冻结稿、design.md、代理、review-submit、安全核心与真实guard均与56e74f0字节一致。

### 28.2 观测项

两轮C8调查场景均未记录harness_failure,场景profile_removed均true。
独立的`test_signal_cleanup_observation[SIGINT]`两轮均观察到已知瞬时目录残留:
exit130、profile_exists=true、lsof_exit=1、own_residue_removed=true;
测试自身已回收,未修改断言或生产清理规则。原始记录分别为
`batch1/full/c8/cleanup-SIGINT.json`与`batch1/full-final/c8/cleanup-SIGINT.json`。
normal/SIGTERM两轮均exit0且profile_exists=false。此记录不等于新的读取失败,
也不把已有SIGINT清理待办登记为已修复。

### 28.3 本批交付

实现入口:core转换器`convert`、repair共享适配`diff_cli.main`、repair/ci_triage两入口。
新增64个测试,既有3100个全部保留,门禁无失败、无需计时敏感用例豁免或单独重跑。
最终检查`/dev/shm/p5q-browser-*`为空。受保护文件前后hash一致,
证据索引见[batch1/README.md](evidence/restore/batch1/README.md)。
只运行离线测试与本地假服务器,不访问真实QuickBuild/Gerrit,不运行真实gbs。
按本机全局署名提交推送恢复第1批;其余批次未实现,不提前写成已恢复。
暂存差异仅HTML原始字节的尾空白告警,保留不清洗;其它文件diff检查通过,
详见batch1/whitespace-check.json。

## 29. SKEL-RESTORE-03:恢复第2批契约核对停止

状态:已由SKEL-RESTORE-04裁定关闭;以下原始停止记录保留。

恢复第1批已以`b92573f`提交并推送origin/clang-fix-campaign,
最终3163 passed/1既有skip、64新增用例、其余门禁全部通过(第28节)。
第2批开始前核对新增CLI与clang_kb/v1时发现两处未闭合的契约,
按SKEL-RESTORE-01第五.2条停止,不自行选择解释。

1. 第二.4.c要求输出`needs_generation=true`,4.d固定七字段却不含它。
   需要明确是新增第八字段,还是以mode=generate替代独立布尔字段。
2. import-diff无baseline_commit输入,而design第3.4节将其列入schema与七元去重,
   第3.5节要求instance完整溯源;本次仅明确允许imported_shelve的verified_tree_sha为空。
   真实analyzer对现有3行编译日志夹具exit0但不产出commit/revision。
   需要明确新增baseline输入,或该origin可空及其去重/冲突语义;不能从diff的blob ID猜commit。

[停止报告与候选文字diff](evidence/restore/stop-report-SKEL-RESTORE-03.md)逐项列出来源、
副作用与所需测试。[离线探针](evidence/restore/batch2/probe-contract.py)真实调用analyzer,
归档全部结构键与两种JSON形状,命令/UTC/输出见`batch2/contract-probe/`,
原始analyzer产物见`batch2/contract-facts/analyzer/`;探针exit0,ruff通过。
两处问题已在对话中提出,截至本次记录尚未收到设计方澄清。

本次停止记录不增加业务代码,不写KB或state DB;未实施第二批两处审核改动,
未进入第三批URL取证或第四批剧本。SKEL-RESTORE-02的T1资格裁定继续有效,
不重开原停点。设计与骨架冻结稿、代理、安全核心、所有既有拒绝规则保持原字节。
第二次提交仅为本停点记录与离线事实证据,不声称第二批验收完成。
停止记录的design检查0 problem;analyzer原始Markdown保留末尾空行,
差异检查仅此生成证据告警,手写文档与探针无空白告警。通用忽略规则中的
analyzer产物已显式纳入证据提交,不改.gitignore。

## 30. 实施裁定 SKEL-RESTORE-04:第二批接口与第一批补修

### 30.1 裁定原文

一、第二批接口裁定

① propose-fix 输出 JSON 增加布尔字段 needs_generation,固定字段变为 8 个:mode、needs_generation、edit_spec_path、source_kind、kb_precedent_ref、context_dir、t2_records、downgrade_reason。mode=t1 时 needs_generation=false,edit_spec_path 与 source_kind=t1_cherry_pick 必填;mode=generate 时 needs_generation=true,edit_spec_path 与 source_kind 为 null,context_dir 必填。补字段一致性测试。

② kb import-diff 新增必填参数 --baseline-commit(该 diff 所基于的源码 commit,40 位十六进制,格式不符 exit 2;来源由导入人提供,如 shelve/Gerrit change 的 parent 或 QuickBuild 构建所用 commit)。instance 的 baseline_commit 对所有 origin 保持非空,不开 null 例外。去重仍为 design.md §3.4 七元 dedupe_key;仅 origin=imported_shelve 时 verified_tree_sha 为 null,计算 dedupe_key 时该槽位用字符串 "imported:" + sha256(diff 原始字节) 代替。baseline_commit 不作 T1 匹配硬键(按 §3.5),只用于溯源与漂移报告。补测试:缺 --baseline-commit 拒绝;同 diff 重复导入命中既有 id;同失败不同 diff 各存一条;非 imported_shelve 记录的 dedupe 与原规则逐字节一致。
两处偏差写入 design.md 第 4.6 节“恢复项落地裁定”。

二、第一批补修(tizen_campaign_core/diff_to_edit_spec.py 与 tizen_campaign_repair/diff_cli.py)

1. git format-patch 尾部签名:最后一个文件的最后一个 hunk 之后,允许且仅允许出现形如 "-- \n" 加一行版本号(可再跟空行)的签名块,直到文件结束;签名块之后再出现任何内容仍按 unparsed_patch_content 拒绝。签名块出现在两个文件之间或 hunk 之前也拒绝。
2. diff 文件非 UTF-8 可解码时,返回 exit 4 DIFF_CONVERT_UNSUPPORTED、reason=unsupported_encoding,不再归为 INVALID_ARGS。
3. 补测试:真实 git format-patch 产物(单文件、多文件、带邮件头与 Signed-off-by)转换成功并过真实 guard;签名块后追加内容被拒;签名块夹在文件之间被拒;latin-1 diff 返回 unsupported_encoding。

三、继续

补修随第二批同一轮门禁验证(全仓 pytest 不加 -x、mypy、ruff、lint-imports、design 检查);然后按 SKEL-RESTORE-01/02 继续第二批,第三批取证完成后仍按原第三.1.c 条停止等待裁定。

### 30.2 本轮范围

基线aecf55a;原3164个nodeid保留,只新增用例。第二批的KB、sync、propose-fix与
SKEL-RESTORE-02两处审核资格变更及本次D2E补修一起验收。第三批仅做本地URL证据,
提交后停止。历史无关工作树改动不纳入;不访问真实Gerrit/QuickBuild,不运行真实gbs,
不改代理或安全核心,不写知识库实际数据到仓库。

## 31. SKEL-RESTORE-05:恢复第2批seed去重停点

状态:已由SKEL-RESTORE-06裁定关闭;原始事实与证据保留。

design.md第818行的七元串拼接,与第1053行seed实例字段置null之间缺少编码规则。
SKEL-RESTORE-04仅为imported_shelve规定了tree槽位替代值,不覆盖seed。
这是持久化去重身份的选择,没有自行以空串/null字面量/伪造SHA代替,
也没有通过拒绝所有seed来缩减Phase8验收。

[停止报告](evidence/restore/stop-report-SKEL-RESTORE-05.md)含原文定位、候选文字diff、
副作用与补测清单。[独立探针](evidence/restore/batch2/probe-seed-dedupe.py)
仅试算三种候选得到不同hash,不调用草稿库、不写KB或state DB;exit0,
原始stdout和命令/UTC/负载在`batch2/seed-contract-probe/`。

本轮实现草稿已存`batch2/seed-stop/implementation-wip.patch`,只作定位资料;
撤回本轮9个既有文件改动与12个新增实现/测试文件,逐项hash清单及恢复核验同目录。
无关用户改动原样保留。editable安装已离线恢复为基线pyproject配置。
局部D2E99、审核33、propose-fix32通过均不等于本批门禁;
sync后续运行主动中断、KB CLI有3个草稿校验失败也如实列于报告。
未完成全仓pytest/mypy/ruff/import验收,未单独交付D2E或审核改动,
符合补修必须随第二批同轮验收的要求。design.md与冻结稿仍为基线原字节,
不提前写成恢复完成。第三批取证与第四批未进入,无真实网络业务操作。

停止交付核验:collect-only exit0、3164个nodeid与恢复第1批最终集合完全一致;
9个受保护文件hash不变、21个草稿涉及路径已恢复至基线或移除。
design检查0 problem、独立契约探针exit0、探针ruff-final通过。
首轮探针ruff的两处zip缺strict告警保留,补strict=True后重跑通过,
不影响探针结论;两轮原始输出都保留。证据索引见`batch2/seed-stop/README.md`。
暂存差异检查仅两份归档patch的空白上下文行告警,保留统一diff所需前导空格;
排除这两份生成patch后exit0,详见`seed-stop/whitespace-check.json`。

## 32. 实施裁定 SKEL-RESTORE-06:seed 专用去重

一、裁定:采用候选 B,为 seed 另定专用去重公式;instance(含 imported_shelve)公式保持不变。
1. 适用范围:仅 record_type=seed。instance 继续使用 design.md §3.4 原七元公式;imported_shelve 的 tree 槽位仍按 SKEL-RESTORE-04。
2. seed 专用公式:
   dedupe_key = sha256( UTF-8 编码的 JSON 数组,json.dumps(..., ensure_ascii=False, separators=(",", ":")) )
   数组固定 5 项且顺序固定:
   ["clang_kb/seed/v1", diagnosed_flag, root_cause_category, toolchain_profile, fix_summary_sha256]
   - diagnosed_flag、root_cause_category:字符串或 null,null 按 JSON null 序列化;两者不得同时为 null(否则 seed 无法参与 T2,append 拒绝 exit 2);
   - toolchain_profile:必填非空字符串;
   - fix_summary_sha256:fix_summary 先做 Unicode NFC 归一化并去掉首尾空白,再对其 UTF-8 字节取 sha256 十六进制;fix_summary 归一化后为空则拒绝。
3. 去重粒度(明确接受):告警类型、错误类别、工具链、策略正文全部相同才命中既有 id;正文不同则各存一条。
4. seed 在 JSONL 中照原设计保存 instance 字段为 null,不伪造包名、仓库路径、baseline_commit 或 tree;instance 的非空校验不因 seed 放宽。
5. 停止报告提到的草稿问题(误拒历史策略空值)由实现方按原条文修正:design.md 未要求 seed 的 fix_strategy_initial/final 非空,seed 允许为 null;instance 仍按原规则。

二、测试(随第二批提交)
seed append 成功;同五元重复返回既有 id;并发 append 幂等(与既有锁用例同形态);flag 与 category 同为 null 拒绝;fix_summary 首尾空白差异命中同一 id、正文不同各存一条;seed 只出现在 t2 且按 §3.5 排序;固定黄金向量(至少 3 组 seed 的期望 hash 写死在测试里);普通 instance 与 imported_shelve 的 dedupe 逐字节不变。

三、记录与继续
本条写入 design.md 第 4.6 节“恢复项落地裁定”。按 SKEL-RESTORE-01/02/04 继续第二批(含 D2E 补修与 T1 审核两处改动同一轮全仓门禁);第三批取证完成后仍按原第三.1.c 条停止等待裁定。

## 33. 恢复第2批:知识库、建议与补修

### 33.1 实现与边界

以f5f748e为基线重新核对实现,没有套用seed-stop的未验收patch。
权威为design第3.4/3.5/4.1/4.2节、Phase8与RESTORE-01/02/04/06。
本轮受保护文件与既有测试核对见`evidence/restore/batch2/r06/integrity-before.json`,
最终核验随门禁归档;不改真实业务状态库,合成KB只写测试临时目录。

| 交付 | 代码落点 | 条文/裁定 |
| --- | --- | --- |
| JSONL schema、原子写、锁、去重、单向promote | `tizen-campaign-core/scripts/tizen_campaign_core/kb.py:137,234,266,297,320,337` | design 3.4、RESTORE-04/06 |
| 归一化parity、T1全部键、T2排序/限流 | 同文件`:65,72,356` | design 3.5、Phase8 |
| kb query/append/promote/import-diff、sync CLI | `tizen-campaign-kb/scripts/tizen_campaign_kb/cli.py:21,57,94` | design 4.1、RESTORE-01第二.3、RESTORE-04 |
| KB_SYNC独立审计、绑定溯源、最新PASS晋级 | 同包`sync.py:36,152`;core `campaign_state.py` 的KB_SYNC分支 | RESTORE-01第二.3.c,不新增状态 |
| propose-fix三条路径、八字段、漂移事实 | `tizen-campaign-repair/scripts/tizen_campaign_repair/propose_fix.py:40,62,83,125,149,228` | RESTORE-01第二.4、RESTORE-04 |
| D2E终端签名与非UTF-8处理 | core `diff_to_edit_spec.py`;repair `diff_cli.py` | RESTORE-04第二 |
| T1来源与A2质量门 | `tizen-review-submit/scripts/tizen_review_submit/review_submit.py:298,316` | RESTORE-02,仅两处表达式(+4/-2) |
| 报告先例/来源两列 | `tizen-campaign-report/scripts/tizen_campaign_report/report.py` | RESTORE-01第二.5 |
| 同层包与旧入口共享解析 | `.importlinter`, `pyproject.toml`, `ci_triage/cli.py`,repair `__main__.py` | RESTORE-01第二.1 |

seed仅在T2出现,3组固定hash覆盖null、Unicode NFC和中文UTF-8;正文归一化只用于
去重,存储保留原始策略文字。普通instance七元拼接与imported原始diff哈希另测,
CRLF不被读文件时的换行转换改变。seed策略可null;历史导入未经过内容策略重推,
不伪造initial/final,在实际复用审核时仍重推并执行A2。普通instance完整溯源校验不变。

sync使用unit锁和状态库事务快照,核对PUSH/DERIVE/POLICY/三架构verification、
edit字节、CI锚点、Change-Id与最新请求的PASS绑定。先写幂等KB再写KB_SYNC审计,
三处崩溃注入均验证重跑不重复;不推进KB_APPENDED或其它状态。
propose-fix第一轮使用CI锚点,后续使用previous_evidence同架构证据;
取材在隔离bare仓库,配置SSH基址+匹配project+白名单ref,永不执行gerrit_url。
生成分支只复用gbs_patch_suggest上下文原语,不写修法、不调用LLM。
新skill位于`tizen-campaign-kb/SKILL.md`;编排skill和开局模板留恢复第4批。

### 33.2 测试与验收记录

[覆盖对照](evidence/restore/batch2/r06/coverage.md)逐项列出条文与测试函数。
新增246个用例:core KB 83、KB CLI 25、sync 35、propose-fix 61、D2E补修35、T1审核7。
原3164个nodeid全部保留,最终3410个、删除0,无既有测试文件改动;
见`nodeids-final.json`与`nodeids-added-final.txt`。
局部组合335 passed,末尾公开promote关键字与配置固定错误提示复核108 passed;
这些局部结果不替代全仓验收。

最终静态门禁已通过:`mypy-complete`为169个源文件success;
`ruff-complete`完整待提交Python树通过;`imports-complete`为7 kept/0 broken;
`design-complete`为0 problem。`package-check-final.json`记录离线wheel四文件字节一致、
六个新旧入口help成功、临时wheel目录已删除。
全仓首轮`full/`和最终树重跑`full-final/`各保留独立原始日志,均不加-x。
首轮3407 passed/0 failed/1既有skip,pytest 1265.12秒;
20核机器loadavg前9.94/11.21/10.31、后4.75/5.26/7.42。
最终树重跑**3409 passed/0 failed/1既有skip**,pytest 1171.56秒、包装1179.34秒,
UTC 09:09:48至09:29:28;20核loadavg前4.61/5.22/7.40、后5.48/5.10/5.71。
skip仍为大小写敏感文件系统上的`test_case_insensitive_bypass_is_platform_specific`,
没有新增skip、没有timing-sensitive重跑或C8观测豁免。
两轮C8各11个场景均无harness_failure且profile_removed=true;
action计数见`c8-observations.json`,注入故障按既有断言处理,不误记为自然回归。
本轮无新增读取失败观测;既有四条离线端到端与Node代理/安全测试由全仓原样执行。

第二批已完成离线门禁。`integrity-final.json`中的实现hash在最终全仓期间未变化;
代理SHA256仍为`044ae065ee223093b4d63e3444f37a812dd2831266e6334fac526bf116ec7723`,
骨架及P5Q冻结稿、驱动、sandbox/QB提交与读取、安全核心和身份判据均为基线原字节。
本轮没有发现新增规格冲突;seed编码按RESTORE-06,八字段与导入槽位按RESTORE-04,
审核两处按RESTORE-02,没有推广这些例外。实际开发者审定的生产seed数据未导入,
只提交合成测试夹具与工具,不宣称建立了真实知识库。
暂存差异检查的告警仅位于生成证据,保留HTML原字节中的空白行;
排除本轮生成证据后exit0,见`whitespace-check.json`,不改写测试证据来消除告警。
先提交推送本批,再按RESTORE-01第三.1完成本地URL形态文档并停止,
不在本轮实施发现命令、浏览器扩展或恢复第4批剧本。

## 34. 恢复第3批首步:URL形态取证与规定停点

恢复第2批已由`7484f58`提交并推送`origin/clang-fix-campaign`。
随后仅按SKEL-RESTORE-01第三.1检索本地资料,结果为
[discovery-url-shapes.md](evidence/restore/discovery-url-shapes.md)。
该文第1节列实际搜索目录,第2节逐项列来源文件与行号并区分真实页面、
历史采集记录、代码/合成夹具;第4节给出待批准的最小策略文字diff,
第5节列未来Node正负例及服务器实收判据。本轮没有执行这些未来测试。

已确认Base配置1917的Recent Builds、父子变量页及子页的html_report导航链接。
旧夹具为单架构`gbs_reports/<arch>`与`logs/fail/.../log.txt`,本地历史采集
记录则为多架构`logfiles/standard/<arch>/<package>.txt`,不能互相替代。
当前Base报告正文、真实iframe src、正文类型与下载行为、精确URL编码及
历史分页为UNKNOWN。现有代理只取得主帧导航正文并按HTML解析,
因此不能仅加路径就宣称支持无损编译日志读取。

依第三.1.c在此停止等待设计方确认:精确登记来源与构建归属引导、
html_report永久禁止的窄例外、iframe/编码补证方式、纯文本日志读取与脱敏契约。
这是原任务预定的审批停点,没有将候选diff应用到代理,没有新增发现命令,
没有进入恢复第4批。全部URL仅来自本地文字,没有访问QuickBuild/Gerrit、
启动浏览器、运行真实gbs、读取Cookie文件或写真实状态库。

本次第三批提交仅含取证文档、progress与INDEX;design检查器0 problem,
这三份文档的`git diff --check`通过。代理完整SHA256仍为
`044ae065ee223093b4d63e3444f37a812dd2831266e6334fac526bf116ec7723`。
第二批全仓与静态门禁以第33.2节原始证据为准,不将其说成第三批功能验收。

## 35. 实施裁定 SKEL-RESTORE-08:发现页面真机只读取证

本节登记对第34节停点的裁定;以下为裁定原文。

一、原则裁定(对 discovery-url-shapes.md 第 4、6 节)
1. 采用“发现会话专用精确路径表”方案:discoveryScope 未启用时 P5Q 现有行为逐字节不变;表项只能由代理在已核验的上一层页面中解析产生,CLI 不能直接注入 URL;不开放目录前缀、任意构建号、任意 /download/、Wicket 监听器。
2. 永久禁止列表只批准一项例外:discoveryScope 内、read 阶段、无 query/fragment 的 GET /build/<已核验 id>/html_report。/log、/artifacts、REST、外站、HTTP、WebSocket、全部破坏性监听器、307/308 继续拒绝。
3. 构建号引导:
   a) --build-id:先用现有只读路径读 /build/<id>/overview,核验其配置路径属于所选 qb.projects 项目(父构建为 RBS/TRIGGER,子构建为 RBS/build);父构建只登记页面中 Child Build 链接给出的子构建;核验失败即停,不登记任何下游。
   b) --since:只登记该项目 /overview/<overview_id> 的 Recent Builds 普通链接;本轮不做历史分页,早于窗口的部分在报告中标注 outside_recent_window。
4. 报告子页面与包日志:不读取子帧,改为对“上一层已核验文档中唯一的 iframe src / 日志 href”所解析出的精确同源 URL 发起一次显式主帧导航读取;解析用标准 URL 解析器一次完成,登记与比较按浏览器实际请求的 path 字节;禁止路径穿越、编码的路径分隔符、跨构建号。只登记主架构所需的那一份日志。
5. 纯文本日志读取:新增受控应答类型(如 read_text),不经 DOMParser;原始字节按 UTF-8 严格解码,失败则返回 QB_TEXT_ENCODING_UNSUPPORTED,不降级;单份上限 64 MiB,超限拒绝;正文落盘到 <state-root>/discovery/<build_id>/logs/ 后返回路径与 sha256,不把全文放进 trace;沿用 qb_redact 对已登记身份的脱敏。触发浏览器下载(Content-Disposition attachment 或 Download 事件)本轮不支持,返回 QB_DOWNLOAD_UNSUPPORTED。

二、真机只读取证(一次,需要用户在弹出的浏览器窗口登录)
1. 写一个独立取证脚本放 evidence/restore/discovery-capture/,复用现有浏览器代理的登录流程;不改生产代理,只在该脚本内用硬编码的精确路径清单。
2. 只读以下页面,全部 GET、不点击任何按钮、不提交任何表单:/overview/1917;/build/1204735/overview 与 /variables;/build/1204736/overview 与 /variables;/build/1204736/html_report;该页面中唯一 iframe src 指向的页面;该报告中一个失败包的日志链接(优先 zlib,主架构 armv7l)。构建号取自 batch3.5 预筛记录;若页面显示与预期不符,立即停止,不改读其它构建。
3. 每一跳记录:请求 URL(原样字节)、响应状态、Content-Type、Content-Disposition、重定向链、是否触发 Download 事件、所在帧;正文脱敏后归档。不记录 Cookie、账号、请求头值。
4. 取证结束即关闭浏览器并删除临时 profile;结果写 discovery-capture/README.md,并逐项回填 discovery-url-shapes.md 第 2 节的 UNKNOWN。

三、实施分叉
1. 取证事实同时满足以下 4 条:iframe 与日志均为 https://quickbuild.tizen.org 同源;无 307/308 和异源 302;日志为纯文本且无 Download 事件;路径符合文档第 4 节候选文法。此时不必停,直接按 SKEL-RESTORE-01 第三.2 至第三.4 条与本裁定第一条实施 campaign-discover、代理精确表、pathShape 新类别与第 5 节全部 Node 正负例,完成后继续第四批。
2. 任一条不满足:停止并写停止报告,附实测事实与候选调整,不擅自扩大放行。

四、其余要求不变:除本裁定外不改 sandbox-submit、qb-trigger、qb-result-fetch、review-submit 的规则;每批全仓门禁;不推送 Gerrit、不运行真实 gbs;若推送报 Permission denied,提交后停止并回报,由用户本机推送。

### 35.1 取证准备

`evidence/restore/discovery-capture/capture.mjs`独立包装生产runtime/Agent.login,
生产代理文件未修改。固定六页逐次导航,iframe与唯一zlib/armv7l失败链接只从
上一层响应惰性文档提取;不执行页面内脚本来取数。自动子帧Document拒绝,
只有当前精确主帧GET可读。字段操作、运行与提交入口均未调用。
只读取获准的Content-Type/Content-Disposition响应字段,不读取任何请求头。
`redact_capture.py`在单个内存上下文中复用生产PageRedactor,写前写后自检,
纯文本另对已登记身份做单词边界遮蔽,原始正文与身份集合不落盘。
离线夹具使用私有虚拟显示、回环HTTPS与合成登录,不在用户桌面弹窗。

`discovery-capture/offline-01/`记录首次离线验证:7 passed/0 failed/0 skipped,
20.21秒,包括完整八页、外站iframe、307与attachment停止;profile全部删除。
当前尚未执行真机,已在对话中请用户回复“开始”,等待现场登录准备。

### 35.2 唯一一次真机执行与SKEL-RESTORE-09停止

用户确认原话:“开始”。预检本地HEAD=6d73a9f,输出live-01不存在,
/dev/shm无p5q-browser残留;生产代理完整hash仍为第34节值。
运行`/home/linhao/.local/bin/node docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/discovery-capture/capture.mjs --live`一次。
UTC 2026-11-04 12:27:40.533至12:28:41.214,exit4,60.681秒;
命令、stdout/stderr与run.json分别在`discovery-capture/live-01.command.json`、
`live-01.stdout.log`、`live-01.stderr.log`和`live-01/run.json`。

login ok=true。首个/overview/1917主帧GET返回HTTP200响应元数据,
Content-Type=text/html;charset=utf-8,未观察到Content-Disposition/Download;
随后第一条OPERATION_FAILED为Fetch.continueRequest/read/request/<other>/
generation=2/REQUEST_ID_INVALID,AGENT_STOPPED=FETCH_CONTINUE_FAILED。
工具返回STOPPED/CAPTURE_ERROR;配置页正文未归档,其它页面全部未读取。
页面59447ms关闭,浏览器59965ms断开,profile_removed=true;
事后/dev/shm再次确认无p5q-browser目录。

该continue操作不在SKEL-R-04/R-08的failRequest窄例外内,没有改变停止条件。
新增读取失败观测见下表。无论其是否与历史读取失败同源,本轮均不重试。

| 样本 | 场景/阶段 | 首条失败与停止 | 结论/证据 |
| --- | --- | --- | --- |
| RESTORE-08 live-01 | 登录成功后的首个配置页导航/read | Fetch.continueRequest/REQUEST_ID_INVALID,generation2,path=<other>;AGENT_STOPPED=FETCH_CONTINUE_FAILED;包装CAPTURE_ERROR | 安全停止;`discovery-capture/live-01/run.json:84`;不使用调查测试豁免 |

[停止报告](evidence/restore/discovery-capture/stop-report-SKEL-RESTORE-09.md)列事实、
不能确定的底层生命周期、离线观测与有上限等待的候选方案,均未实施。
`discovery-url-shapes.md`第2.1节逐项回填NOT_COLLECTED/UNKNOWN;
RESTORE-08第三.1四项前提未齐,不进入第三批实现或第四批。

交付复核:新增7份运行记录逐文件通过生产PageRedactor自检,源代理与6d73a9f
逐字节相同,/dev/shm残留为空,见`discovery-capture/validation.json`。
取证辅助Python的ruff通过,design检查0 problem,本轮文档diff检查通过。
本批在规定的真机异常停点结束,没有运行或宣称通过第三批功能的全仓门禁。

## 36. 实施裁定 SKEL-RESTORE-10:continueRequest失效先复现再窄化

一、裁定
1. 停止正确;R-04 豁免只覆盖 Fetch.failRequest,本次 continueRequest 失败按原规则停止无误。
2. 处置路线:离线复现 → 窄化豁免 → 全量门禁 → 再做一次真机只读取证。不在真机上试错。

二、离线复现(先做,复现不出则停止报告,不改代理)
1. 用现有 P5Q 假 HTTPS 服务器与真实 Chromium:登录后页面带若干静态资源(css/js/图片,其中至少一个延迟响应),在这些资源请求处于 Fetch 暂停期间触发对 /overview/<id> 的主帧导航,使旧页面资源被浏览器取消;记录每个被取消资源上 continueRequest 的返回类别。
2. 只用于定位的临时观测字段(资源类型、匿名请求序号、导航代次、相对时间)可放在测试入口或临时副本,不进生产代理,不记录 URL 查询值或正文。
3. 判定:若稳定复现出 Fetch.continueRequest 返回 REQUEST_ID_INVALID 且来源为已被取消的请求,进入第三条;否则停止并写报告。

三、窄化(复现成立后实施,仅改 installGuards 的失败分类,其余不动)
1. 仅 operation=Fetch.continueRequest 且 category=REQUEST_ID_INVALID:不调用 onStop,逐次记 trace 动作 CONTINUE_TARGET_GONE(字段同 DENY_TARGET_GONE:phase、stage、path 形态、generation),不占第一条 OPERATION_FAILED。
2. Fetch.continueResponse 的任何失败、continueRequest 的其它类别、failRequest 以外的其它操作失败,一律保持原停止规则。
3. 被读取的主帧文档若因此没有正文,read 必须按现有正文/地址/Build 标签核对失败返回错误,不得把“请求已失效”当成功;为此补断言。

四、测试
1. 新增真实 Chromium 用例:导航取消静态资源 → continueRequest 失效被记录且不停止,后续 read 成功;主帧目标文档的 continue 失效 → read 失败、不产出正文。
2. Node 矩阵补:continueRequest 其它类别仍停止;continueResponse/REQUEST_ID_INVALID 仍停止;failRequest 豁免行为不变;trace 不含 URL 查询与正文。
3. 既有 C5a、C8(按 SKEL-R-08 观测规则)、四组安全测试与全部代理静态断言不改并通过;全仓 pytest(不加 -x)、mypy、ruff、lint-imports、design 检查通过。
4. 改动单独 commit,写入 progress 与 design.md 第 4.6 节(“恢复项落地裁定”下加一条,说明与 R-04 同类、范围与理由)。

五、再做一次真机只读取证
门禁全过后,按 SKEL-RESTORE-08 第二条原样再执行一次(需用户在弹出窗口登录);之后按 SKEL-RESTORE-08 第三条分叉。若再次出现任何未豁免的失败,停止报告,不再自行重跑。

六、其余要求不变。推送报 Permission denied 时提交后停止回报,由用户本机推送。

### 36.1 复现设计

基线c68b800。只在P5Q假服务器增加默认关闭的dashboard资源与静态资源夹具,
不改生产代理。测试入口暂缓三份资源的真实Fetch.continueRequest调用,
待Network.loadingFailed(canceled=true)确认取消后才送出原CDP调用;
资源类型、匿名序号、导航代次、相对时间留测试证据,不记录原始错误文本。
另一路图片在服务器延迟响应,所有流量经测试证书/解析规则限制到回环。
拟在原树独立重复三次,稳定成立前不修改代理。

### 36.2 复现成立与最小实现

`evidence/restore/continue-gone/reproduce-01/`原树连续3次均复现,
每次3个真实资源(Stylesheet/Script/Image)都先有Network.loadingFailed且
canceled=true,再调用真实CDP,9/9返回REQUEST_ID_INVALID,服务器实收这三条资源为0。
各次AGENT_STOPPED=FETCH_CONTINUE_FAILED,read返回QB_BROWSER_UNAVAILABLE且无正文;
所有profile删除。另一路图片确实到假服务器且延迟3000ms响应。
证据只记录匿名序号、类型、代次、时间与类别,没有伪造CDP返回或记录原始错误文本。
复现窗口的请求在login代次2被暂停、read切换到代次3后调用continue;
这坐实取消机制,不宣称还原了真机<other>资源的具体路径与全部调度时序。

复现成立后,生产仅`qb_browser_agent.mjs`的installGuards两处判断及动作名称
共+3/-3行:observeFailure为continueRequest失效逐次记CONTINUE_TARGET_GONE,
guarded只对此组合不停止。Policy、FrameOwnership、Agent.read、驱动与其它生产文件
完全未改。动作字段仍仅action/phase/stage/path/generation;其它类别枚举不变。
详见`integrity.json`;代理完整hash:
`044ae065ee223093b4d63e3444f37a812dd2831266e6334fac526bf116ec7723`
→`431b27137c857f5089053737b320ea35f2317d66493892b3dec5f7608db2e26c`;
以export class Agent之前为前缀:
`9b7796f02f3e65f97c6f68bbe169109b8bd885854c98bb976d4d55ae5a2bc006`
→`1708c9567418043345c6f8a1e875aff93e1f21ce627540583f734fc5eeafb2ed`。

`fixed-01/`复跑3次9个资源均CONTINUE_TARGET_GONE,不占OPERATION_FAILED,
当前配置页及下一次build overview均读取成功。主文档取消另测1次:
确认浏览器取消后真实continue同样失效,read仍QB_BROWSER_UNAVAILABLE/无正文,
服务器实收该文档为0;首条OPERATION_FAILED为page.goto/NAVIGATION_INTERRUPTED,
UNKNOWN停止分类来自原命令错误映射,没有因豁免伪造成功。

旧诊断矩阵只更新continueRequest/REQUEST_ID_INVALID对应期望:
`tests/node/test_qb_deny_target_gone.mjs`从停止/OPERATION_FAILED改为
不停止/CONTINUE_TARGET_GONE;`test_qb_read_failure_diagnostics.mjs`同一参数期望同步。
failRequest、continueResponse与其它类别旧期望不变,nodeid不改;
新增逐次记录不占首因与诊断写入异常两例。真实浏览器回归新增一个pytest入口,
3410个既有nodeid全部保留,最终collect3411;见`nodeids.json`。
既有C5a/C8入口、四组安全脚本与代理静态断言均逐字节未改。

### 36.3 门禁与观测

静态门禁mypy、ruff(完整tracked Python+新增入口)、7项import合约、design全部通过;
Node矩阵、既有允许/拒绝测试与静态负例共388 passed/0 failed/0 skipped,
原始输出与完整argv分别在`mypy/`、`ruff/`、`imports/`、`design/`、`node-matrix/`。
完整全仓不加-x,3410 passed/0 failed/1 skipped,1211.96秒;
既有跳过为大小写敏感文件系统上的
`test_tizen_build_verify.py::test_case_insensitive_bypass_is_platform_specific`。
输出与JUnit在`full/`;20核,开始负载15.78/14.25/10.71,
结束8.29/6.28/7.38,开始时CPU前10名称与占用见`full/command.json`。
3410个旧nodeid保留,只新增1个,无新增skip;没有使用计时豁免或重跑覆盖结果。

四组安全测试独立重跑4/4,Worker/WebSocket、307/308、逐跳拦截、凭据隔离
全部通过,假服务器请求/握手清单与原始trace见`safety/stdout.log`;
临时目录删除,全程回环HTTPS。全部门禁结束后P5Q进程与profile残留均为空,
68份归档HTML逐文件通过生产PageRedactor自检,见`validation.json`。
代码与说明文档diff检查通过;23份原始脱敏HTML的行尾空白原样保留,
例外清单见`diff-check.json`,不为清理格式而改证据字节。

读取失败观测表本轮增量见`observations.json`:
C5a六个落点场景通过,OPERATION_FAILED/AGENT_STOPPED均0,
可观测关闭尾段0.074–2.183秒(error-no-build的无浏览器命令为null)。
C8调查11个场景全部完成,harness_failure均为空,各场景profile_removed=true;
竞争导航的可信环境失败与主动注入的UNKNOWN失败按原断言通过,
没有自然FETCH_CONTINUE_FAILED或新的失败豁免。
独立SIGINT清理探针仍复现已知短暂目录残留,own_residue_removed=true,
其记录`full/c8/cleanup-SIGINT.json`原样保留,不宣称修复该既有遗留。

### 36.4 后续边界

本次生产仅上述installGuards窄例外,未扩大任何URL/动作白名单,
未改冻结稿、安全核心、身份判据、P5Q结果写入或schema。
修复及离线证据单独提交推送后,再请用户确认开始一次只读取证;
使用原capture工具输出到新`discovery-capture/live-02`,live-01不覆盖。
此处尚未进行真机操作,第三批发现功能与第四批编排未宣称完成。

### 36.5 live-02执行与SKEL-RESTORE-11停止

上段为修复提交时的边界记录。`b29d6f3`已推送后,用户再次确认原话“开始”,
于2026-11-04 14:26:36.495–14:29:46.590 UTC执行唯一一次只读取证,
exit4,190.095秒。原capture工具未修改,只调用其导出函数并使用新目录;
命令与stdout/stderr在`evidence/restore/discovery-capture/live-02/command.json`等文件。
前置确认目录不存在、无P5Q进程/profile残留、代理与冻结稿hash符合已验收值。

登录ok,六个固定页面均200、text/html;charset=utf-8、无Content-Disposition,
无重定向/Download;六份脱敏HTML归档。前五页配置/构建/父子关系核验通过。
登记位置外身份计数依次0/2/0/0/0/0,父overview的2需人工确认是否新身份位置,
不输出名字、不自行扩大脱敏范围。

第六页唯一iframe原文(`06.response.html:803`)为
`/download/1204736/html/HTML REPORT/index.html`。
capture.mjs:23在调用标准URL解析器前拒绝空格,报CAPTURE_PATH_UNSUPPORTED;
未执行iframe/日志的显式主帧导航。离线HTMLParser+标准URL对照确认解析后为
同源`/download/1204736/html/HTML%20REPORT/index.html`,无query/fragment,
但原exactLink拒绝;这只是离线计算,不是实际iframe响应或wire URL证据。
探针与输出为`probe-live-02-path.py`、`live-02/path-probe.json`,零网络。

trace只有自检1与DENIED28(login9/read19),无OPERATION_FAILED/AGENT_STOPPED,
也未出现CONTINUE_TARGET_GONE;不能宣称此次现场触发验证了新豁免。
PAGE_CLOSED=173269ms,disconnected=173794ms,profile_removed=true;
事后P5Q进程/profile无残留。新归档逐文件脱敏检查通过,
正文hash与run.json一致,live-01/原capture/生产代理逐字节未变,见validation.json。

按RESTORE-10第五条停止,不重试、不换路径、不实施恢复第三/四批。
报告`evidence/restore/discovery-capture/stop-report-SKEL-RESTORE-11.md`
记录已取得与仍UNKNOWN的四项条件、候选工具预检查调整及所需离线用例;
候选只写方案,等待设计方裁定。本轮没有运行表单/提交/真实gbs/Gerrit推送。
本次仅证据与文档收尾:离线路径探针、该探针ruff、design检查(0 problem)
全部通过,见`live-02/offline-checks.json`;13份输出加validation本身逐文件
通过脱敏检查。不重跑或冒称完成第三批业务功能的全仓验收。

## 37. 实施裁定 SKEL-RESTORE-12:会话身份脱敏与iframe空格

一、脱敏缺陷(先修,修完再做任何真机读取)
1. 事实:live-02/02.response.html 第 930 行构建表“触发人”列原样保留了登录账号与显示名;同文件 </thead> 被改写成 </thea&lt;USER&gt;。即登记位置外身份未脱敏,且替换误伤了 HTML 标签。
2. 修复取证脱敏(capture 工具与其 PageRedactor;生产 qb_redact 若有同类问题一并修):对本次会话已登录用户的账号名与显示名,在整页任意位置(不止登记位置)替换为固定占位符;只按完整的身份字符串匹配,不得匹配到标签或属性名的片段;查清 </thead> 被改写的原因并修正。
3. 存档清理:对 discovery-capture 下 live-01、live-02 全部已归档正文做一次修复后的脱敏后处理,新 commit 提交;无法从存档恢复的被误改标签保持原样并在 README 注明。不改写 git 历史、不强推。
4. 补测试:身份出现在表格单元格、标题栏、链接文本、属性值中均被替换;含 "d>"、"thead"、"<td>" 等片段的正常标签不被改动;替换前后除占位符外字节一致;outside_identity_count 改为“替换次数”并要求归档后复检为 0。

二、iframe 路径空格(批准候选)
1. 取证工具:路径段内允许 ASCII 空格;仍拒绝控制字符(0x00–0x1f、0x7f)、反斜线、首尾空白、路径穿越、编码的路径分隔符、跨构建号、外站、userinfo、query、fragment;用标准 URL 解析器解析一次,把解析结果(空格为 %20)登记为唯一主帧读取地址,与浏览器实际请求的 path 逐字节比较。
2. 第三批正式实现的精确路径表按同一规则处理;目录名以真实页面为准(本次为 HTML REPORT),不得用历史 GBS Reports 夹具拼接替代地址。
3. 补离线用例:字面空格与等价 %20 的唯一 src 正例;上述各类负例;服务器只收到登记的那一次主帧请求。

三、补做一次真机只读取证(第一、二条门禁通过后;需用户在弹出窗口登录)
1. 只读:/build/1204736/html_report → 其唯一 iframe src 页面 → 该页中 zlib(主架构 armv7l)失败日志的唯一链接;若 iframe 页中找不到 zlib 或链接不唯一,立即停止,不改读其它包。前六页不重复读取,沿用 live-02 事实。
2. 每一跳记录要求、结束清理要求同 SKEL-RESTORE-08 第二.3、二.4 条;所有正文经修复后的脱敏并复检身份替换后为 0 才能归档。
3. 之后按 SKEL-RESTORE-08 第三条分叉:四条件全部满足则直接实施 campaign-discover 与第四批;任一不满足则停止报告。

四、其余要求不变。全仓门禁、单独 commit、推送报 Permission denied 时提交后停止由用户本机推送。

### 37.1 根因与实施范围

基线57cac6e,日期2026-11-05。尚未进行任何真机读取。
生产`qb_redact.py`的_UserFields与_Fields均用splitlines构建源码偏移,
而HTMLParser.updatepos只以LF更新行号。父构建归档含394个CR,其中10个独立CR,
导致位置错位。`evidence/restore/redaction-12/root-cause-before.json`
用无凭据合成HTML稳定复现“标签损坏且身份仍在”的同类问题。
两处共用LF偏移函数,生产默认登记位置规则不变。

新增显式选用的SessionPageRedactor供取证worker使用:从Welcome区域仅在内存
登记本会话身份及account(display)两部分,全页文本/注释/脚本文本/属性值作完整
身份匹配;HTMLParser识别结构,源码区间替换不重新序列化,不替换标签名或属性名。
解码HTML实体仅用于匹配并映射回原始区间,除占位符外保留原字节。
凭据仍按原规则清除。固定结构JSON不做身份键名替换,不包含身份值;
HTML/日志应答计数改为identity_replacement_count,新增identity_remaining_count=0,
写前写后均验证残留为0。其它生产调用仍使用PageRedactor原规则。

取证exactLink允许路径段内ASCII空格,其它拒绝规则不变;标准URL只解析一次,
scope.current仍精确匹配实际请求。新增remaining三页入口,只允许既定html_report
作为起始页,不能由CLI注入其它路径。尚未启用正式discoveryScope或改生产代理。

### 37.2 存档后处理

`discovery-capture/sanitize_archives.py`只从裁定指定的历史单元格在内存取得
账号/显示名,不打印、不存身份值。live-01无正文;live-02六份正文全部处理和复检,
只有02.response.html替换一处完整复合身份,其余五份字节不变。
坏标签原样保留,没有猜测补回被覆盖的字节。前后hash、替换次数与残留0见
`discovery-capture/archive-redaction-12.json`。旧run.json/validation.json是历史记录,
不篡改当时计数和hash,当前正文hash以新后处理清单为准;旧“自检通过”不能证明
没有此次缺陷,本裁定明确撤回这一推断。不改git历史、不强推。

### 37.3 门禁与停止 SKEL-RESTORE-13

证据根:`evidence/restore/redaction-12/`。实现位置:
`tizen-qb-verify/scripts/tizen_qb_verify/qb_redact.py`(LF偏移、SessionPageRedactor),
`discovery-capture/redact_capture.py`(完整会话身份要求、双重检查、计数),
`capture.mjs`(空格URL与仅剩三页入口),`sanitize_archives.py`(一次性后处理)。
未改生产代理、驱动、四个提交/读取命令、安全核心、冻结稿,见`integrity-final.json`。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 最终脱敏专项 | 115 passed,0 failed,0 skipped(91既有+24新增) | `final-focused/` |
| 本机HTTPS取证 | Node 9 passed,0 failed,0 skipped;字面空格/%20、唯一主帧请求、仅剩三页、脱敏与负例 | `capture-node/`;全仓新增browser封装用例亦通过 |
| 全仓,不加-x | **3433 passed,1 failed,1既有skip**,1147.496秒,exit 1 | `full/command.json`, `full/stdout.log`, `full/pytest.xml` |
| C5a/C8 | C5a六参数与C8调查均通过,无豁免重跑 | `gate-summary.json`, `full/c5a/`, `full/c8/` |
| 安全矩阵/静态负例/四组安全测试 | 对应pytest封装全部通过;没有改允许/拒绝逻辑 | `gate-summary.json`, `full/pytest.xml` |
| mypy / ruff | 169源码通过 / 通过(新行长错误已仅换行修正,原失败留存) | `final-mypy/`, `final-ruff-format/`;原`final-ruff/` |
| import-linter / design | 7 kept,0 broken / 0 problem | `imports/`, `design/` |
| nodeid | 最终3436,原3411全部保留,新增25,无collect错误 | `final-collect/`, `final-nodeids.json` |
| 历史正文最终复检 | 六份,身份残留全部0 | `final-archive-check.json` |
| 清理 | profile 0,本仓代理/该profile浏览器0 | `cleanup.json` |

全仓前后loadavg为2.95/2.94/4.57与3.69/3.73/3.98,20核;
开跑CPU前十只记进程名/占用,见`full/command.json`。
失败nodeid:`tests/unit/test_qb_browser_node.py::test_node_c2c_trusted_reads_and_fields[test_qb_browser_fields.mjs]`。
Node子例`continuous denied refresh GETs do not extend quiet; uncheck and @freeze still complete`
在`tests/node/test_qb_browser_fields.mjs:530`断言
`Build Package List: denied refresh must not extend quiet`失败(字段窗口须小于3000ms)。
实际单字段时长未输出;不能据此认定负载或放行规则故障。
它不在计时敏感名单中,按SKEL-B1-05停止,未改断言、未重跑放行。
详细事实与候选处理见`stop-report-SKEL-RESTORE-13.md`。

完整运行收集后,新增脱敏代码由逐字符偏移改为只映射实际匹配边界,
并增加多码点HTML实体部分匹配的失败负例(避免64MiB日志的逐字符辅助对象开销)。
因此全仓收集3435与最终3436差1;最后实现的专项115通过,
但本次全仓**不能作为最终树完整验收**。原计划最终树再跑门禁,
因上述非豁免失败取消,必须待裁定后重新完整验证。
未执行RESTORE-12第三条真机读取,live-03不存在;未进入正式discovery实现或第四批。
源码/文档diff-check通过;29处原始合成HTML/pytest输出/JUnit行尾空白原样保留,
未把证据格式化来掩盖原始失败。停止报告与修复同一提交,不作为最终门禁验收。

## 38. 实施裁定 SKEL-RESTORE-14:既有字段窗口计时断言失败

一、裁定
1. 该失败为既有 Node 计时断言(test_qb_browser_fields.mjs:530,3000ms 静默窗口),本次改动未触及生产代理与该用例;同类于 SKEL-B1-05 计时敏感项。不另做定位调查。
2. 将 nodeid tests/unit/test_qb_browser_node.py::test_node_c2c_trusted_reads_and_fields[test_qb_browser_fields.mjs] 加入计时敏感名单,规则与 C5a 相同:失败原样留证,在当前树上单独重跑 3 次,3 次全部通过才算门禁通过,任一次失败即停止并按停止报告第 3 节候选方式调查。不改断言、不调阈值、不加 skip/xfail。名单变更写入 progress 与 design.md 第 4.6 节“恢复项落地裁定”。

二、门禁(最终树)
1. 因全仓开始后脱敏实现又有改动,必须在最终树上重新完整运行全仓 pytest(tests/run_quiet.py tests/ -q,不加 -x),并重跑 mypy、ruff、lint-imports、design 检查;运行前后记录 loadavg 与 CPU 前十进程(只记进程名与占用)。
2. 全仓若该 nodeid 失败,按第一.2 条处理;计时敏感名单外的任何失败即停止。
3. 本次 RESTORE-13 失败证据原样保留,不覆盖。

三、门禁通过后
按 SKEL-RESTORE-12 第三条执行唯一一次真机只读取证(html_report → iframe 页 → zlib armv7l 日志;需用户在弹出窗口登录),之后按 SKEL-RESTORE-08 第三条分叉:四条件全满足则直接实施 campaign-discover 与第四批,任一不满足则停止报告。

四、其余要求不变。推送报 Permission denied 时提交后停止,由用户本机推送。

### 38.1 执行登记

基线f6216ec。先重跑RESTORE-13失败nodeid三次,再做最终树完整门禁;
新证据仅写`evidence/restore/redaction-14/`,不覆盖redaction-12。
各次运行前后记录loadavg、CPU核数、CPU前十进程名/占用,不记录命令行。
本轮目前只改名单说明与门禁记录,不改生产代码或既有测试。
尚未启动真机,第三条唯一一次三页取证仍待全部门禁通过和用户开始确认。

### 38.2 最终树门禁通过

RESTORE-13历史停止已按RESTORE-14处置:先在f6216ec最终实现上单独三次,
全部通过;随后完整全仓中该字段nodeid亦通过,无需门禁后追加重跑。
测试断言、3000ms阈值与skip/xfail均未改,未另作定位调查。
证据根:`evidence/restore/redaction-14/`,运行器`run_gates.py`仅调用既有离线入口。

| 运行 | 结果 | wrapper耗时(s) | 前/后loadavg(1/5/15分钟) | 证据子目录 |
| --- | --- | --- | --- | --- |
| 字段独立1 | 1通过,0失败 | 122.118 | 5.49/4.37/4.35 → 2.78/3.74/4.12 | `fields-rerun-01/` |
| 字段独立2 | 1通过,0失败 | 117.935 | 2.78/3.74/4.12 → 3.12/3.48/3.97 | `fields-rerun-02/` |
| 字段独立3 | 1通过,0失败 | 118.226 | 3.12/3.48/3.97 → 1.75/2.94/3.72 | `fields-rerun-03/` |
| 全仓,不加-x | **3435通过,0失败,1既有跳过** | 1163.983 | 1.75/2.94/3.72 → 2.25/2.49/3.49 | `full/` |

全仓pytest自身耗时1158.44秒,共3436 nodeid;唯一跳过为
`test_case_insensitive_bypass_is_platform_specific`(case-sensitive filesystem),与此前相同。
每个`command.json`均有完整argv、UTC起止、exit、前后CPU前十(只有进程名/占用)
及20核记录。额外中间负载见`load-samples.jsonl`,非连续采样,不宣称是完整峰值。
C5a六参数、C8调查、代理允许/拒绝矩阵、源码负例、可信读取/字段、
四组本机拦截安全测试封装、新capture空格/三页用例均通过,见`summary.json`。
没有新的失败观测或豁免结果,没有改变全仓断言。

| 其它门禁 | 结果 | 证据 |
| --- | --- | --- |
| mypy | 169源码,0错误 | `mypy/` |
| ruff | 通过;证据运行器另作不忽略路径的检查亦通过 | `ruff/`, `runner-ruff/` |
| import-linter | 7 kept,0 broken | `imports/` |
| design检查 | 0 problem | `design/` |
| 源码与原失败证据 | 526份既有.py/.mjs、193份redaction-12文件前后hash相同 | `inputs.json`, `unchanged-after.json` |
| 清理 | P5Q profile 0,自身代理/该profile浏览器0 | `cleanup.json` |

代理、驱动、冻结稿与安全核心仍为第37节已登记hash。本轮只改名单/进度说明,
新增门禁运行器和证据;用户原有其它脏树文件未碰。
门禁通过不代表RESTORE-08的四项真机事实已齐备。下一步仅允许
`/build/1204736/html_report` → 唯一iframe → zlib/armv7l唯一失败日志,
新目录`discovery-capture/live-03`尚不存在;须用户回复“开始”后执行一次。
不重复前六页,不打开运行表单、不提交、不访问真实Gerrit或运行真实gbs。

## 39. RESTORE-14唯一一次三页取证:live-03与停止SKEL-RESTORE-15

基线41ce708已推送,最终树门禁见第38节。用户确认原话:“开始”。
本次没有改生产代码、取证工具或测试,也没有重跑/覆盖旧现场证据。
新证据在`evidence/restore/discovery-capture/live-03/`;
同级`live-03.preflight.json`、`live-03.command.json`、`live-03.stdout.log`、
`live-03.stderr.log`记录完整前置、argv、UTC起止、exit与固定输出。
只调用capture导出入口,paths为`[PATHS.at(-1)]`,没有测试解析器/证书启动参数。
前置与41ce708源码hash一致,冻结稿hash一致,P5Q进程/profile无残留。

| 项目 | 实测 | 来源 |
| --- | --- | --- |
| 一次执行 | 2026-11-05 06:03:42.545–06:04:35.243 UTC,52.698秒,exit4 | `live-03.command.json` |
| 登录 | ok=true | `live-03/run.json:61` |
| 唯一业务主帧页 | GET /build/1204736/html_report,HTTP200,text/html;charset=utf-8 | `run.json:7`,`:23`,`:32` |
| 重定向/下载 | 单跳最终地址一致,Content-Disposition=null,Download=false | `run.json:11`,`:12`,`:15` |
| 停止 | QB_EVIDENCE_REDACTION_FAILED | `run.json:64`;`live-03.stderr.log` |
| 正文 | 0份;没有body/hash/替换次数应答,身份残留检查结果NOT_COLLECTED,不写0 | `live-03/validation.json` |
| iframe/日志 | 没有显式主帧读取;一个未登记other帧Document请求被拒 | `run.json:40` |
| 关闭 | PAGE_CLOSED=48386ms,disconnected=48428ms,profile_removed=true | `run.json:53`,`:57`,`:116` |
| 事后检查 | P5Q自身进程/profile均0,6份元数据逐文件检查通过,validation自身也检查通过 | `live-03/validation.json` |

trace只有FRAMEWORK_SELF_TEST 1与DENIED 8(login4/read4),没有OPERATION_FAILED、
AGENT_STOPPED、CONTINUE_TARGET_GONE或DENY_TARGET_GONE。没有放宽拦截或重试。
前六页没有重复读取,仅从获准html_report开始,未运行任何表单/提交命令。

停止位于`capture.mjs:219`的正文writer调用。worker将身份登记、脱敏映射、
写前/写后检查及文件操作异常统一折叠为一个错误码,因此具体失败分支未知。
一个实现限制值得核对:SessionPageRedactor目前只从Welcome片段中识别
`account (display)`复合格式,才把session_identity_complete设为true;
这不是由现场已知事实证明的唯一身份展示格式。离线纯合成探针:
复合格式通过,只有单项则同样返回QB_EVIDENCE_REDACTION_FAILED且不归档。
见`live-03/offline-worker-probe.json`;它只证明候选机制存在,不证明本次根因。
不从旧会话猜本次身份,不保存原始正文,不重新请求来补原因。

按RESTORE-12第三.3/RESTORE-08第三.2停止。四项实施前提未取齐,
iframe/日志的同源、跳转、Content-Type/Download、href/wire path仍UNKNOWN。
`discovery-url-shapes.md`第2.3节已回填;具体停止事实和未实施的候选诊断方案见
`discovery-capture/stop-report-SKEL-RESTORE-15.md`。没有进入正式发现CLI或第四批。
本次仅归档与文档检查,不把第38节的离线门禁冒称为真机取证通过。

## 40. 实施裁定 SKEL-RESTORE-16:身份登记与私有原文离线归档

SKEL-RESTORE-15 由本裁定处理;原现场与失败证据不改。本轮先实施离线修改和门禁,
门禁通过后等待用户重新回复“开始”,不复用上一轮授权。

### 40.1 裁定原文

一、身份登记规则修正(qb_redact.SessionPageRedactor 与 capture worker)
1. Welcome 区域的身份文本无论是单项(仅账号或仅显示名)还是“账号 (显示名)”复合形式都登记;不再以“必须是复合形式”作为完整性前提。
2. 补全:在同一页正文中,凡形如“X (Y)”且 X 或 Y 等于已登记身份的文本,把另一半也登记(仅按完整字符串、词边界匹配,只作用于文本节点与属性值,不作用于标签/属性名)。
3. 完整性判据改为:至少登记到一个非空身份,且归档前后复检所有已登记身份残留为 0。Welcome 区域不存在或为空才判失败。
4. 失败时输出封闭的阶段码(IDENTITY_REGISTER、IDENTITY_EMPTY、REDACT、PRECHECK、WRITE、POSTCHECK 之一)及计数(Welcome 区域数、已登记身份数、替换次数);不输出身份原文、异常原文、堆栈或页面内容。
5. 离线测试:单项账号、单项显示名、复合形式三种 Welcome 均能归档且残留 0;“X (Y)”补全生效;Welcome 缺失返回 IDENTITY_EMPTY;各阶段失败码各有一例;输出中扫描不到任何身份原文。

二、取证流程调整(只改取证工具,不改生产代理)
1. 三个目标页(html_report、唯一 iframe 页、zlib armv7l 日志)按原规则逐页读取;读取阶段的网络/导航/下载等安全停止条件不变。
2. 原始正文只写入仓库外私有目录 ~/.local/state/campaign-capture-private/<run>/(目录 0700、文件 0600),不写入仓库、不 git add、不推送;读取过程中不做脱敏判定,脱敏失败不再中断读取。
3. 浏览器关闭、profile 删除后,离线对私有目录中的原文做脱敏并归档到仓库 evidence;git add 前对整个 discovery-capture 目录做一次身份残留扫描,必须为 0。
4. 归档成功后删除私有目录原文并记录删除;若脱敏失败,原文保留在私有目录,写停止报告(含阶段码),等待裁定,后续离线修复后直接对该原文重做,不需要再次登录。
5. 离线测试覆盖:私有目录权限、仓库内不出现原文、残留扫描拦截、成功后删除。

三、执行
1. 第一、二条完成后跑全仓门禁(不加 -x)及 mypy、ruff、lint-imports、design 检查;计时敏感名单按既有规则。
2. 门禁通过后回报“等待用户确认开始”;用户回复“开始”后执行一次真机只读取证(三页,需用户在弹窗登录),然后按 SKEL-RESTORE-08 第三条分叉:四条件全满足则直接实施 campaign-discover 与第四批,任一不满足则停止报告。
3. 其余要求不变。推送报 Permission denied 时提交后停止,由用户本机推送。

### 40.2 实现与证据边界

- `tizen_qb_verify/qb_redact.py`:只改SessionPageRedactor及其值范围解析辅助器;
  默认PageRedactor的位置脱敏规则不改。Welcome单项也完整,配对补全使用完整身份,
  注释不作为新别名来源(已知身份仍会在注释中遮蔽),标签/属性名不参与匹配。
- `discovery-capture/capture.mjs`:读取时只调用private store;三页原有请求、正文、
  地址、下载与唯一链接检查不变。finally先关闭浏览器/确认profile删除,再finish归档。
- `discovery-capture/redact_capture.py`与新增`capture_archive.py`:固定仓外私有根,
  0700/0600、排除仓库和符号链接、保留原始字节与严格解码文本。浏览器清理后统一登记,
  双重自检、全目录身份扫描、成功删除;失败保留原文并有不联网的--replay入口。
- `tests/unit/test_restore_capture_redaction.py`:原“单项不完整”的两项worker参数用例
  由新归档测试替代;“不从其它用户推定身份”用例只将完整性断言改为true,
  仍断言没有登记其它用户。其余原字节/标签/凭据保护断言保持。
- 新增`tests/unit/test_restore_capture_archive.py`15项,覆盖三种Welcome、缺失/空值、
  六阶段失败、权限、源码不进仓库、全目录拦截后离线重做、清理前不得脱敏与路径防护。
  Node本机HTTPS增加no-welcome:服务器收到全部三页后才报IDENTITY_EMPTY;
  正文零归档、原文保留,证明脱敏失败不再中断网络读取。

门禁根:`evidence/restore/redaction-16/`。定向初查43个pytest项通过
(包含1个真实Chromium包装,内部10个Node测试);正式输出由该目录focused重新归档。
所有Chromium为本机假服/虚拟显示;没有真实QB登录、提交、Gerrit访问或真实gbs。
全目录历史身份复检:`archive-scan.json`,取RESTORE-12已经确认的历史cell只在内存登记,
扫描44个文件,已登记身份残留0,没有改写历史正文或输出身份。新真机会话将重新登记,
本结果不冒充未来会话的扫描结果。

### 40.3 最终树门禁与停点

全仓UTC 2026-11-05 06:57:01开始,完整运行1152.59秒;pytest自身1152.14秒,
不加-x。**3453通过、0失败、1既有跳过**,共3454项,相对上一轮净增18项。
唯一跳过仍为`test_case_insensitive_bypass_is_platform_specific`(case-sensitive filesystem)。
loadavg前2.43/2.57/2.29,后5.52/4.17/3.58,20核;CPU前十名称/占用见
`redaction-16/full/command.json`,没有保存进程命令行参数。

| 门禁 | 结果 | 证据 |
| --- | --- | --- |
| 定向 | 43通过,0失败/跳过;内部Node10项 | `redaction-16/focused/` |
| 全仓 | 3453通过,0失败,1既有跳过 | `redaction-16/full/pytest.xml`, `stdout.log` |
| mypy | 169源码,0错误 | `redaction-16/mypy/` |
| ruff | 完整原配置清单加本轮新增Python;取证/helper另作不忽略路径检查通过 | `redaction-16/ruff/`, `capture-ruff/` |
| import-linter | 7 kept,0 broken | `redaction-16/imports/` |
| design检查 | 0 problem | `redaction-16/design/` |
| P5Q既有回归 | 可信读取/字段、静态断言、允许拒绝矩阵、四组安全封装均通过 | 全仓JUnit对应Node包装 |
| 计时敏感/调查 | C5a六参数、C8调查、字段窗口均通过;无需豁免或三次重跑 | 全仓JUnit; `full/c5a/`, `full/c8/` |
| 完整性/清理 | 530源码门禁前后不变;12受保护文件hash不变;P5Q进程/profile=0,私有真机run=0 | `integrity-after.json`, `protected-final.json`, `cleanup.json` |

汇总:`redaction-16/summary.json`;实现与逐项测试:`redaction-16/README.md`。
本轮没有新的读取失败观测,没有任何真实QB/Gerrit/gbs操作,没有覆盖原失败证据。
代理完整hash仍为431b27137c857f5089053737b320ea35f2317d66493892b3dec5f7608db2e26c,
前缀仍为1708c9567418043345c6f8a1e875aff93e1f21ce627540583f734fc5eeafb2ed。
无与RESTORE-16不一致或做不到之处。现在停在**等待用户确认开始**:
新确认后只执行html_report→唯一iframe→zlib armv7l日志一次,不重复前六页;
四条件仍须现场事实齐备后才允许进入正式campaign-discover与第四批。
暂存后`git diff --cached --check`只报告C5a原样归档HTML的23处行尾空格,
不改写响应字节;排除这些原始夹具证据后exit0,详见`redaction-16/diff-check.json`。

## 41. RESTORE-16唯一一次剩余三页取证:live-04与停止SKEL-RESTORE-17

基线5721a32已推送;用户本次确认原话:“开始”。执行前重读第40节与工具,
核对源码/受保护文件hash与门禁一致,输出目录不存在,P5Q进程/profile/私有run均0,
DISPLAY存在。loadavg为7.57/4.44/3.68,见`discovery-capture/live-04.preflight.json`。
没有改工具或生产代码,没有注入本机测试参数,没有读取凭据或要求终端登录。

只调用capture导出入口一次,paths=`[PATHS.at(-1)]`,输出新目录`discovery-capture/live-04`。
argv、UTC起止、授权、exit见`live-04.command.json`;08:18:21.154–08:19:42.051 UTC,
80.831秒,exit4。完整stdout/stderr为同级`live-04.stdout.log`、`live-04.stderr.log`。

| 项目 | 事实 | 证据(相对discovery-capture) |
| --- | --- | --- |
| 登录 | ok=true | `live-04/run.json:110` |
| html_report | 主帧GET200,text/html;charset=utf-8,单跳,无Disposition/Download | `run.json:7`;`01.response.html` |
| iframe显式主帧 | GET `/download/1204736/html/HTML%20REPORT/index.html`,200,text/html; charset=utf-8,inline,单跳,无Download | `run.json:28`;`02.response.html` |
| 源src与wire编码 | 源码空格,实际请求%20,目录确为HTML REPORT | `01.response.html:803`;`run.json:80` |
| 日志选择 | 唯一zlib行、主架构href恰好一个,文字failed,无class属性 | `02.response.html:1596,1597`;`report-structure.json` |
| 工具首个停止 | class=failed匹配0,CAPTURE_LOG_LINK_MISMATCH;日志未请求 | `run.json:113`;`capture.mjs:120` |
| 附加安全停止 | Fetch.continueResponse/REQUEST_ID_INVALID,idle,response,generation5;FETCH_CONTINUE_FAILED | `run.json:205,214` |
| 脱敏 | Welcome1、登记身份1、替换1;两页替换次数1/0,残留均0,全目录扫描后删除原文 | `run.json:17,38,221` |
| 关闭 | PAGE_CLOSED78863ms,disconnected78988ms,profile_removed=true,私有run删除 | `run.json:100,219,227` |

日志选择失败与附加安全停止分别记录,不把后者推定为前者的原因;trace没有其独立时间戳,
不能确定continueResponse错误是否由关闭动作引起。没有扩大RESTORE-10的豁免。
`live-04/inspect_report.py`只解析已脱敏归档,不联网、不改取证工具;
结果为zlib行1、class匹配0、armv7l href1、日志请求0。
后验清理、逐文件检查、源码完整性见`live-04/validation.json`。
原文严格在仓外私有目录中暂存,归档成功后已删除;没有把原文或身份原文加入Git。

四项实施前提未齐:iframe同源/编码/响应已确认,日志href已取得但响应Content-Type、
Download与跳转仍UNKNOWN。按RESTORE-08第三.2及RESTORE-16第三.2停止,
同时记录RESTORE-10第五条要求停止的未豁免失败。没有再读任何页面、换包或重试,
没有进入campaign-discover正式实现或第四批。

[停止报告](evidence/restore/discovery-capture/stop-report-SKEL-RESTORE-17.md)
给出候选:按实测四列表头/链接文字精确定位zlib主架构链接并补正负例;
continueResponse仍按原规则停止,如需调查关闭竞争须另行裁定。
本轮仅新增证据、离线结构摘录与文档检查,不将第40节全仓结果冒称为本轮重跑。
设计检查0 problem,离线摘录脚本ruff通过;暂存diff仅两份响应HTML的476处原始空白警告,
保留CR/LF和响应字节不格式化,非HTML文件检查exit0(`live-04/diff-check.json`)。

## 42. 实施裁定 SKEL-RESTORE-18:结束取证系列,直接实施campaign-discover与第四批

以下为裁定原文:

一、已确认事实(作为实现依据)
1. iframe:属性原文 /download/<id>/html/HTML REPORT/index.html,实际请求 /download/<id>/html/HTML%20REPORT/index.html,同源 HTTPS,200,text/html,inline,单跳,无 Download。
2. iframe 页 Details 表:表头 name | standard armv7l | standard aarch64 | standard x86_64;每包一行;失败以该架构列中链接文字 failed 表示,链接无 class;href 为相对 iframe 页的 logfiles/standard/<arch>/<package>.txt。
3. 日志响应(Content-Type、Download、跳转)未实测;不再为此单独取证,改为正式实现中的运行时 fail-closed 检查(见第二.4 条)。

二、campaign-discover 实施(按 SKEL-RESTORE-01 第三.2、SKEL-RESTORE-08 第一条及以下修正)
1. 报告链:/build/<已核验子构建 id>/html_report → 唯一 iframe src(按 SKEL-RESTORE-12 第二条的空格与解析规则)→ Details 表。
2. 失败包解析:按表头定位架构列(“standard <arch>” 映射为 standard-<arch>;无法映射的列名视为非白名单 arch,交给 arch 前置门);包名按 name 列完整文本精确匹配;某包在某架构列存在唯一链接且链接文字精确为 failed,即该架构失败;同一单元格多个链接、表头缺失或重复、包名重复,均判该构建 DISCOVERY_REPORT_AMBIGUOUS 并停止该构建,不猜。不再使用 class 匹配。
3. 只为主架构日志登记一次精确读取:href 用标准 URL 解析器相对 iframe 最终 URL 解析一次,必须同源 HTTPS、无 userinfo/query/fragment、构建号一致、路径以 /download/<id>/html/<报告目录>/logfiles/standard/<主架构>/<包名>.txt 结尾。
4. 日志读取 read_text 运行时检查:单跳且最终地址等于登记地址;无 Download 事件、无 Content-Disposition attachment;Content-Type 为 text/*;UTF-8 严格解码;≤64 MiB。任一不满足 → 该包记 DISCOVERY_LOG_UNREADABLE(附固定原因码),不建档,继续处理下一个包;不重试、不换路径。
5. 其余按原设计:arch 前置门、主架构固定优先序、构建变量解析 project/branch/base_commit(解析不出 → DISCOVERY_SOURCE_UNRESOLVED)、默认只为编译阶段失败建档、--dry-run、幂等、discover.json/discover.md 报告、串行。

三、浏览器代理
1. Fetch.continueResponse 失败的停止规则不变;不扩大任何豁免。
2. 仅为 trace 中 OPERATION_FAILED、DENY_TARGET_GONE、CONTINUE_TARGET_GONE、AGENT_STOPPED、PAGE_CLOSED、BROWSER_DISCONNECTED 事件增加相对启动时间 elapsed_ms(整数毫秒),不记录 URL 查询、正文或身份;补断言。
3. 精确路径表、html_report 例外与 read_text 按 SKEL-RESTORE-08 第一条实施;补 discovery-url-shapes.md 第 5 节全部 Node 正负例,并加入本次真实结构的归档形态夹具(四列表、无 class 的 failed 链接、空格目录)。

四、第四批
按 SKEL-RESTORE-01 第四条执行(剧本与模板、离线全流程新增发现→先例复用→评审链路、design.md 第 4.6 节与收尾记录更新、progress/INDEX)。

五、验收与停止
1. 全部完成后跑全仓门禁(不加 -x)及 mypy、ruff、lint-imports、design 检查;计时敏感名单按既有规则。
2. 完成后停止并回报:各 commit、新增命令、测试数量、与原设计的偏差清单。不运行真实 campaign-discover;首次真机运行(--dry-run,针对 1204735)另行裁定,届时需用户登录。
3. 实施中遇到契约冲突或安全规则需要变动时,按既有纪律停止报告。推送报 Permission denied 时提交后停止,由用户本机推送。

### 42.1 开工核对与依赖冲突停点SKEL-RESTORE-19

基线79cbe9f;通读RESTORE-01第三/四批、RESTORE-08/12/16/18、
discovery-url-shapes、现行Agent/驱动/建档与依赖规则。停止RESTORE-17由本裁定处置;
日志的未知响应改为运行时核验,不再要求新登录或补取证。原始停止证据不覆盖。

另发现代码层契约冲突:RESTORE-01第〇.2要求包分层/import-linter不放宽,
第三.2同时指定intake入口复用qb-verify浏览器驱动;骨架冻结稿§4.3明确
同层包互不依赖,`.importlinter:31`将这两包列在同一独立层。
不能自行添加ignore、把`|`换为`:`、动态导入或复制驱动绕过合约。

离线探针`evidence/restore/batch3/r18/probe_dependencies.py`使用当前全部root_packages
及实际LayersContract.check,在内存图里分别加入单条拟议import,从未写生产源码:

| 探针 | root-layers结果 | 证据 |
| --- | --- | --- |
| 当前未修改依赖图 | kept=true | `batch3/r18/probe.json:7` |
| intake.campaign_discover → qb_verify.qb_browser | kept=false | `probe.json:16` |
| intake.campaign_discover → qb_verify.qb_config | kept=false | `probe.json:45` |
| intake.campaign_discover → qb_verify.qb_redact | kept=false | `probe.json:74` |

4项均符合探针预期;558个已跟踪Python/Node源码、冻结稿与.importlinter的hash
前后相同。这里只证明现行直接复用违反合约,不声称所有架构选择都无法实现。
新增独立子进程桥接可以作为候选,但没有现成只读入口且需要另定进程协议/依赖边界,
本轮不自行用该方式绕开同层约束。候选A为精确模块依赖例外,候选B为批准只读桥接;
具体文字diff、副作用和验收建议见
[停止报告](evidence/restore/stop-report-SKEL-RESTORE-19.md)。

按RESTORE-18第五.3停止,没有实现新命令、代理扩权、第四批剧本或新业务测试。
本轮只运行离线依赖探针、现有import-linter、设计检查及新增探针ruff/diff检查;
完整输出与命令见`batch3/r18/validation.json`。全仓pytest/mypy及四组安全测试未运行,
不以RESTORE-16的3453通过结果冒充本轮验收。没有访问QB/Gerrit、启动浏览器或gbs,
没有修改已有测试、冻结稿、生产源码、状态库及无关工作树文件。
本轮结果:依赖探针4/4符合预期(1绿/3红);现行import-linter 7 kept/0 broken;
design 0 problem;新增证据脚本ruff通过;文档diff检查通过。未增加业务测试nodeid。

## 43. 实施裁定 SKEL-RESTORE-20:两命令文件交接

SKEL-RESTORE-19已由本裁定处置;候选A/B均不采纳,原停止报告与探针保留。
以下为裁定原文:

一、裁定
1. 不采用候选 A(依赖例外)与 B(子进程桥接)。包分层与 .importlinter 合约保持逐字不变。
2. 发现拆为两个命令,通过 state-root 下的清单文件交接(同 qb-result-fetch → review-submit 的既有模式):
   a) python -m tizen_qb_verify qb-discover --config <yaml> --state-root <dir> --qb-project <key> (--build-id <id> | --since <ISO 日期>):唯一上网的一步。按 SKEL-RESTORE-18 第二.1–二.4 条与 SKEL-RESTORE-08 第一条完成登录、构建核验、报告链、Details 表解析、构建变量解析与主架构日志 read_text;写出 <state-root>/discovery/<build_id>/discover-manifest.json 与 logs/<package>.<arch>.txt。不调用 analyzer、不建档、不写状态库。
   b) python -m tizen_campaign_intake campaign-discover --manifest <path> --state-db <db> --config <yaml> [--dry-run] [--include-non-compile]:不上网。校验清单 schema、清单与日志均位于配置的 state-root 之下(resolve 后判定,拒绝符号链接越界)、每份日志 sha256 与清单一致;然后按 SKEL-RESTORE-01 第三.2.c–e 条做 analyzer、编译阶段过滤、arch 前置门、主架构优先序、intake.add_unit 建档(串行、幂等);写 discover.json/discover.md。
3. 清单 schema(clang_discover_manifest/v1)固定字段:schema_version、qb_project、build_id(父)、child_build_id、captured_at、report_dir、packages[];每个 package:spec_name、failed_arches(raw 名,规范化排序)、primary_arch、project、branch、base_commit、log_path(相对清单目录)、log_sha256、status(ok | DISCOVERY_SOURCE_UNRESOLVED | DISCOVERY_LOG_UNREADABLE | DISCOVERY_REPORT_AMBIGUOUS | ARCH_NOT_ALLOWED)、reason(固定原因码或 null)。清单与日志写入用 temp+fsync+rename,写后不再修改;同一 build 重复运行写新子目录(带时间戳),不覆盖旧清单。
4. --state-root 解析:qb-discover 使用命令行 --state-root;campaign-discover 从清单路径向上核验其属于 <state-root>/discovery/ 结构,并要求与同次运行传入的 --state-root 一致(为此 campaign-discover 也增加必填 --state-root)。

二、测试
1. qb-discover:用 P5Q 假 HTTPS 服务器与 live-04 归档形态夹具覆盖报告链、四列表解析、无 class 的 failed 链接、空格目录、ambiguous 各形态、日志 read_text 各 fail-closed 原因、清单字段与原子写;Node 安全矩阵与既有 C5a/C8/四组安全测试全过。
2. campaign-discover:清单 schema 负例、路径越界与符号链接负例、sha256 篡改拒绝、各 status 透传进报告、过滤/arch 门/幂等/dry-run;断言该命令不发起任何网络请求(禁用网络的测试夹具)。
3. 依赖合约:lint-imports 7/7 不变;新增静态断言 tizen_campaign_intake 不导入 tizen_qb_verify。

三、文档与剧本
SKILL.md 与开局模板写明两步顺序(先 qb-discover、再 campaign-discover --manifest);design.md 第 4.6 节“恢复项落地裁定”加一条说明本次拆分及理由,并撤销 SKEL-RESTORE-01 第三.2.a 中单命令入口的写法。

四、其余按 SKEL-RESTORE-18 第二至五条执行(含 trace elapsed_ms、continueResponse 规则不变、第四批、完成后全仓门禁、不运行真实发现)。遇冲突按既有纪律停止报告;推送报 Permission denied 时提交后停止,由用户本机推送。

### 43.1 首次建档网络边界探针与停止SKEL-RESTORE-21

基线0931cb4。两命令分包/file交接可避免第42节直接import冲突,不需要更改.importlinter。
开工核对新命令调用链时发现RESTORE-20第一.2.b的“不上网”与必用的既有
`intake.add_unit`首次建档行为冲突:冻结稿5.1第4步要求源码暂存克隆与身份核验;
`intake.py:155`调用`_prepare_source`,缺少canonical副本时`:57`发起ssh远端clone。
这不只是QB访问;新包/新构建的首次建档正是需要源码克隆的路径。

离线探针`evidence/restore/batch3/r20/probe_offline_intake.py`:
临时配置使用ssh://gerrit.invalid:29418,临时库/工作区,真实intake与真实gbs_analyzer;
仅在测试进程内替换SandboxGit.run,记录请求的操作并在git子进程创建前抛固定异常。
未启动git传输,未访问QB/Gerrit,未修改任何生产函数/断言或真实状态库。

| 项目 | 实测 | 证据 |
| --- | --- | --- |
| Git调用意图 | clone,remote=true,ssh://gerrit.invalid:29418/platform/upstream/example | `batch3/r20/probe.json` attempts |
| 该调用前 | evidence已发布,unit已建立,状态CI_EVIDENCE_READY | 同文件unit_exists_at_call/status_at_call |
| 禁止Git后 | exit5 INTAKE_CLONE_FAILED,canonical源码不存在,暂存残留0 | 同文件failure/canonical_source_exists/staging_remaining |
| 清理 | 仓外临时目录连同临时DB均已删除 | 同文件temporary_directory_removed=true |
| 完整性 | 生产源码、既有测试、冻结稿、.importlinter前后hash相同 | 同文件protected_hashes/protected_unchanged |

这是既有可重跑的克隆失败路径,不将其描述为新发现的状态库缺陷。
但不能据此宣称新命令既能首次完整建档又严格不上网,也不能把禁用网络测试
改成只禁Python socket而漏掉git/ssh子进程。不能自行绕过源码准备或更改身份判据。

[SKEL-RESTORE-21停止报告](evidence/restore/stop-report-SKEL-RESTORE-21.md)
列出候选A:澄清只禁止QB访问、允许既有只读克隆;候选B:保持绝对离线并另裁定
建档/源码准备分离的API、输出及后续入口。两个候选均未实施。
design第4.6节已追加RESTORE-20的文件交接裁定,明确尚未验收;剧本暂不宣称新命令可用。
本轮只做探针、依赖/设计/证据脚本/diff检查,完整日志见`batch3/r20/validation.json`;
全仓pytest、mypy、四组安全测试未运行。无新业务命令、无新业务nodeid。
按RESTORE-20第四条停止,不继续第三/四批实现,等待网络边界裁定。
检查结果:离线探针符合预期;import-linter 7 kept/0 broken;design 0 problem;
新增探针及检查脚本ruff通过;文档diff检查通过;560个已跟踪源码/冻结稿/合约hash不变。
首次证据脚本ruff发现一行103字符(E501),已仅折行修正;原输出保留为
`ruff-first.stdout.log`与`validation-first.json`,最终检查为`validation.json`。

## 44. 实施裁定 SKEL-RESTORE-22:campaign-discover与建档克隆

SKEL-RESTORE-21由本裁定处置,保留原证据。裁定原文:

一、裁定:采用候选 1。
1. SKEL-RESTORE-20 第一.2.b 条中“不上网”修订为:campaign-discover 不访问 QuickBuild(不登录、不读页面、不启动浏览器、不导入 tizen_qb_verify);允许并仅允许经 intake.add_unit 既有路径、通过 SandboxGit 对 gerrit_ssh_base + project 执行的只读克隆与 checkout,行为与手工 campaign-add-unit 完全相同。不新增任何其它网络访问。
2. 不采用候选 2(建档与源码准备分离),intake.add_unit 不改。

二、测试修订
SKEL-RESTORE-20 第二.2 条的“禁用网络”断言改为:campaign-discover 运行期间不发生任何 HTTP(S) 请求、不启动浏览器或 node 进程;唯一外部进程为经 SandboxGit 的 git(测试中走既有假 SSH + 本地裸库夹具),其目标地址必须等于 gerrit_ssh_base.rstrip('/') + '/' + 清单中的 project。补一例:清单 project 被篡改为非法名时在克隆前被拒。

三、其余按 SKEL-RESTORE-20、SKEL-RESTORE-18 执行;本条写入 design.md 第 4.6 节“恢复项落地裁定”。遇冲突按既有纪律停止报告;推送报 Permission denied 时提交后停止,由用户本机推送。

### 44.1 进程白名单核对与停止SKEL-RESTORE-23

基线b7e4272。第43节克隆冲突已处置,但本次第二条新增的“唯一外部进程为git”
与第一.2要求intake.add_unit不改不能同时满足。`intake.py:134`必经analyze;
`_campaign_io.py:79`组装`sys.executable -m gbs_analyzer analyze`,`:93`执行子进程。
这是正常建档的CI证据生成,不是浏览器、真实gbs编译或Gerrit网络访问。

离线探针`evidence/restore/batch3/r22/probe_process_boundary.py`调用现有add_unit,
临时配置/工作区/库与现有本地日志,在subprocess.run边界记录首个argv并阻断进程创建。
实测首个argv正是Python analyzer,阻断后exit5 INTAKE_ANALYZER_FAILED;
git/analyzer实际子进程均0,网络请求0,DB未创建,临时目录已删除。
原始结果`batch3/r22/probe.json`,没有修改生产代码/测试断言/.importlinter/冻结稿。

[停止报告](evidence/restore/stop-report-SKEL-RESTORE-23.md)提供最小文字diff:
将既有本地analyzer子进程加入允许集合,仍禁止HTTP、浏览器/node与额外远端操作,
对git按SandboxGit精确目标断言。该例外未实施,不把“外部进程”自行解释为“联网进程”。
design第4.6节已追加RESTORE-22;本轮只做离线探针、7条依赖合约、设计/ruff/diff检查,
输出见`batch3/r22/checks.json`。没有新增业务命令或业务测试nodeid,未跑全仓pytest、
mypy或四组安全测试,第三/四批仍未完成。未访问真实QB/Gerrit或运行真实gbs。

## 45. 实施裁定 SKEL-RESTORE-24:campaign-discover允许的本地子进程

SKEL-RESTORE-23由本裁定关闭,原探针与停止证据保留。裁定原文:

一、裁定
1. SKEL-RESTORE-22 第二条修订为:campaign-discover 运行期间允许的外部进程限于两类——(a) 经 SandboxGit 的 git,目标地址等于 gerrit_ssh_base.rstrip('/') + '/' + 清单中的 project;(b) 以当前解释器 sys.executable 运行的 python -m gbs_analyzer(intake.add_unit 与 campaign-discover 编译阶段过滤的既有/同形调用)。禁止:任何 HTTP(S) 请求、node/浏览器进程、gbs、curl/wget 及其它外部进程。intake.add_unit 不改。
2. 测试断言相应改为:记录全部子进程 argv,只允许上述两类;对 (b) 断言 argv[0] 为 sys.executable、模块为 gbs_analyzer、子命令为 analyze;任何第三类进程或 HTTP 请求即失败。

二、执行纪律补充(仅限本恢复任务剩余部分)
若冲突仅源于设计方裁定的测试/措辞要求与“复用未修改的既有代码路径”之间,且不涉及网络访问范围、QuickBuild、Gerrit 推送、浏览器代理规则、脱敏或任何安全拒绝规则,则按既有代码行为实现,在 progress 记录“措辞冲突按既有行为处理”及具体条目,继续执行,不必停止。涉及上述安全面的冲突仍按原纪律停止报告。

三、其余按 SKEL-RESTORE-18/20/22 执行;本条写入 design.md 第 4.6 节“恢复项落地裁定”。推送报 Permission denied 时提交后停止,由用户本机推送。

### 45.1 实施范围与措辞处理

基线4936377。继续第三批两命令清单交接及第四批剧本/离线链路;不运行真实发现。
intake.add_unit与.importlinter保持不变。措辞冲突按既有行为处理:
SandboxGit的本地rev-parse、origin核对与checkout不含远端地址参数,仍属既有建档路径;
测试对实际clone的目标作精确等值断言,并逐条记录全部Git/analyzer子进程。
以下为实施与最终树验收结果;历史停止与开发失败证据均保留。

### 45.2 第三批落点与边界

| 裁定条目 | 实现位置 | 本轮事实 |
| --- | --- | --- |
| RESTORE-20文件交接/24进程边界 | core/discovery_manifest.py:82、:142、:159;intake/discover.py:32 | 固定schema、resolve越界/哈希前置校验;新run目录原子发布;原add_unit不改 |
| RESTORE-08/18作用域 | qb_discovery_scope.mjs:85;qb_browser_agent.mjs:112、:675 | CLI只给已登记项目/id,不能给下游URL;父子身份与链接核验后登记精确路径;旧会话scope为空 |
| RESTORE-12/18真实报告形态 | qb_discovery_scope.mjs:17、:57 | HTML REPORT空格标准解析;四列表、无class的failed;歧义停止该构建,未知arch前置拒绝 |
| RESTORE-18文本fail-closed | qb_browser_agent.mjs:834、:882;qb_collect.py:22 | 单跳/最终地址/Content-Type/下载/UTF-8/64MiB;日志仅返回文件路径与SHA;逐包失败无重试 |
| RESTORE-18观测 | agent:26、:221、:1126、:1136 | 六类trace的elapsed_ms为非负整数;continueResponse规则不变 |
| RESTORE-20生产入口 | qb_collect.py:139;intake/discover.py:114 | qb-discover采集、不建库;campaign-discover消费、不访问QB;两步各有CLI入口 |

路径缩写:core为`tizen-campaign-core/scripts/tizen_campaign_core`,
intake为`tizen-campaign-intake/scripts/tizen_campaign_intake`,
qb文件均为`tizen-qb-verify/scripts/tizen_qb_verify`。

既有三个Node诊断测试只把新增elapsed_ms先断言为非负整数,再对剩余对象执行原deepEqual;
helper为`tests/node/elapsed_trace.mjs`,没有修改原停止次数、类别、路径或敏感值断言。
假HTTPS服务增加可选discoveryHandler,未启用时既有场景原样。
wheel的既有`*.mjs`package-data覆盖新增纯解析辅助模块,无需调整包列表或依赖合约。

开发过程保留:首轮r24定向51通过,mypy通过,ruff指出intake入口import排序,仅排序修复。
final定向期间审阅发现waitUntil被误加到旧read,已撤回到原timeout:30000,
该选项只留新增discoveryNavigate。修正时间早于完整全仓启动;
`r24/full-source-proof.json`记录mtime、启动时间与哈希,不把混合树定向结果当最终源码证明。
完整全仓、静态与安全组均在修正后启动,最终结论另记。

### 45.3 最终树门禁与保护文件

权威证据目录为`evidence/restore/batch3/r24/accepted/`,不是此前的`final/`。
每项的command.json记录完整argv、UTC起止、exit、耗时、前后loadavg、20核及CPU前十进程名/占用。

| 门禁 | 结果 | 证据(相对r24) |
| --- | --- | --- |
| 发现与恢复定向 | 53 passed,0 failed | accepted/focused/pytest.xml |
| 完整全仓,不加-x | 3501 passed,0 failed,1既有skip;1161.39秒 | accepted/full/pytest.xml |
| mypy / ruff / import-linter | 172文件无问题 / 通过 / 7 kept,0 broken | accepted/mypy、ruff、imports |
| design / Node静态及负例 | 0 problem / 183 passed,0 failed | accepted/design、static |
| P5Q四组安全 | 4/4,仅loopback,profile删除 | accepted/safety/stdout.log |
| nodeid | 旧3454全部保留,新增48,合计3502 | nodeids.json |
| 补充真实归档结构/拒绝矩阵 | 21 passed,0 failed,0网络请求 | supplementary-scope/ |
| 封版源码一致性 | 定向到全仓结束零变化 | accepted/source-proof.json、integrity-after.json |

全仓UTC 11:20:54至11:40:16;loadavg三值由2.42/2.06/3.14变为1.65/1.44/1.78。
C5a全部参数、C8调查与RESTORE-14字段窗口用例均通过,无需计时敏感重跑,无新增自然读取失败观测。
唯一skip为既有大小写不敏感文件系统用例。补充矩阵以C6b第05页归档为输入,
验证Recent Builds六列表、身份/重复ID/链接查询/>50行拒绝、各阶段文法与iframe个数;
只在about:blank隔离惰性文档中解析,没有真实QB访问。

Worker安全组走b:browser_fail_closed;shared_worker closeTarget成功,
worker closeTarget异常Error;攻击HTTP=0、WS握手=0、浏览器关闭且临时目录删除。
其它三组307/308、逐跳、凭据隔离通过;停止/拒绝断言未放宽。

`protected-final.json`证明intake.add_unit、.importlinter、sandbox-submit、qb-trigger、
qb-result-fetch、review-submit、安全核心和两冻结稿不变。代理完整SHA256:
`431b27137c857f5089053737b320ea35f2317d66493892b3dec5f7608db2e26c` →
`309e7ab8877fe652d60cb6b27733431c633ef799a05ede5403358d147f4e22bb`;
前缀SHA256:
`1708c9567418043345c6f8a1e875aff93e1f21ce627540583f734fc5eeafb2ed` →
`594107e04912b90ef803b3f2a1142b5b42afab83399829dba4e3c8e95664095c`。
变化限RESTORE-08/18授权的发现作用域、文本读取和六类elapsed_ms;
Fetch.continueResponse失败停止规则及旧read导航参数保持不变。

提交前复核:design仍0 problem,证据脚本ruff通过,保护hash/nodeid审计通过。
`git diff --cached --check`仅报告假服务原始脱敏HTML中的46处既有行尾空格,
不修剪证据正文;排除本轮证据HTML后exit0。完整输出为`r24/diff-evidence/`,
源码/文档检查为`r24/diff-source/`。无DB二进制、pyc或符号链接加入提交。

### 45.4 偏差与停点

授权偏差已逐条并入design第4.6节:两命令清单交接替代单命令;
消费端允许既有SandboxGit与Python analyzer;未实测日志响应由运行时fail-closed;
仅登记的html_report GET作永久禁止例外。唯一措辞处理见45.1,不扩展网络或拒绝规则。
无未获授权的契约偏差。未运行真实qb-discover/campaign-discover、QuickBuild登录、
真实Gerrit或gbs;第一次针对1204735的真实dry-run等待另行裁定。

## 46. 恢复第四批:剧本、模板与离线完整链路

`tizen-clang-campaign/SKILL.md`与`references/campaign-kickoff-template.md`纳入
qb-discover→campaign-discover清单交接、propose-fix、generated/suppress/t1_cherry_pick
三种来源及审核去向、sandbox后kb sync与QB PASS后kb sync;相关intake/repair/qb skill同步。
state-root统一,首次真实发现仍不自动执行。design第4.6节与INDEX/收尾记录同步,
骨架原真实第3.5/4批仍为延后,不与恢复任务第四批混淆。

新增`test_campaign_restore_e2e.py::test_discovery_precedent_review_offline_chain`
实际调用采集逻辑(假代理协议)产出清单,再经真实analyzer/假SSH建档、三架构基线、
导入T1/建议/修复、sandbox、KB追加、QB PASS、KB升级、review与释放/报告。
另有真实Python CLI→生产代理→本地假HTTPS/Chromium的采集用例,两类证据不混称。
序列为DISCOVERED → CI_EVIDENCE_READY → BASELINE_RUNNING(三条) →
BASELINE_REPRODUCED → REPAIR_ROUND_RUNNING → LOCAL_3ARCH_PASS →
SANDBOX_PUSHING → SANDBOX_PUSHED → QB_REQUESTED → QB_TRIGGERED →
SANDBOX_QB_PASS → REVIEW_PUSHING → REVIEW_PUSHED;副本释放,
先例来源t1_cherry_pick,KB从NEW到CI_VERIFIED。

证据:`r24/accepted/focused/discovery/restored-chain.json`;
采集CLI与服务器清单为同目录`cli.json`、`producer-requests.json`;
消费端全部argv与0 HTTP/浏览器为`consumer-processes.json`。
第四批与第三批使用45.3所列同一最终树完整门禁,不是只测文档。
本轮结束停在离线交付,不进入真实发现。

## 47. SKEL-RESTORE-25:首次真机发现试运行前置与停止

基线6f5e801。授权目标1204735,只读qb-discover后离线campaign-discover --dry-run,
单次、失败不重试;浏览器必须另等用户“开始”。本轮尚未请求或收到该次确认。

新建仓外`/home/linhao/Toolchain/campaign-discover-trial/r01/`,config.yaml与state-root;
state.db、kb.jsonl仅指定全新路径,没有创建/写入数据库。qb配置逐项沿用C8 preparation,
真实Gerrit SSH来源为本机~/.ssh/config的review.tizen.org条目,地址
`ssh://review.tizen.org:29418`;不猜测、不使用C8的本地镜像地址。
其它键按启动模板填写,clang_conf_path为本机已存在gbs_llvm.conf,不代表已确认
1204735实际build.conf,且本次不编译。完整配置留仓外,不归档账号身份。

一次campaign-start-check使用历史预筛确认的platform/upstream/libtirpc:
UTC12:27:13–12:27:17,exit0,五项通过,实际只读Gerrit ls-remote通过;
既有gbs检查为--version,未执行build。argv/UTC/exit/固定JSON见
`evidence/restore/live-dryrun-01/preflight-command.json`。
config SHA256为`68b4f39b1ad768629acff344fdd6e8e1812d109d74924330a9ceec3cb24dda44`。

真机前发现RESTORE-25第三.1的取证通道缺口:生产CLI不输出带elapsed_ms的runtime.trace,
read_text应答没有Content-Type/跳转/Download元数据;它们虽然参加运行时核验,
并未作为事实回传。不能推测或把测试harness输出混称生产CLI输出。
据既有契约冲突纪律写[停止报告SKEL-RESTORE-26](evidence/restore/live-dryrun-01/stop-report-SKEL-RESTORE-26.md),
附准确代码位置与候选A封闭观测补修/B明确接受NOT_COLLECTED,均未实施。
唯一一次真机机会未使用;无日志正文、无失败包清单、无安全停止事件可供判定,
不是“安全事件为0”的真机结论。自动发现真机只读保持未验证。

入仓前对本轮两个证据文件执行PageRedactor.check_bytes,凭据检查通过;
从仓外配置取已知本机账号/署名作完整词边界残留扫描,计数0,不输出原文。
未登录QB,会话身份扫描标为NOT_APPLICABLE_NO_LOGIN,不伪称已经扫描未知登录身份。
state-root为空,状态库与KB文件不存在;受检生产文件与6f5e801逐字一致。
design检查0 problem、git diff --check通过;没有运行全仓测试或任何QB命令。

## 48. 实施裁定 SKEL-RESTORE-27:试运行归档字段与开发机资源限制

2026-11-06,基线24fe825。RESTORE-26由本裁定处置,保留原停止报告和前置记录。
裁定原文:

一、归档字段裁定
1. 接受代理 trace(含 elapsed_ms)与日志逐项元数据(Content-Type 原值、跳转链、Download 事件)在本次试运行中记为 NOT_COLLECTED;不为本次试运行修改生产 CLI 或代理。
2. 等价证据:每份 status=ok 的日志,记录“已通过 read_text 运行时检查(text/*、单跳且地址一致、无 Download/attachment、UTF-8 严格解码、≤64MiB)”及 sha256、字节数;每份失败的日志记录其固定原因码。任何安全停止以 CLI 返回的错误码为准写入报告。
3. SKEL-RESTORE-25 第三.1 条相应修订,其余不变。

二、开发机资源限制(本条线后续所有任务的常设要求)
1. 全仓 pytest、mypy 等门禁及任何浏览器/真机命令,一律在 systemd-run --user --scope -p CPUQuota=400% -p MemoryMax=6G -p MemorySwapMax=0 下运行;本次 qb-discover 与 campaign-discover 用 -p CPUQuota=200% -p MemoryMax=3G -p MemorySwapMax=0。
2. 另加 nice -n 10;禁止并行跑两组门禁;不使用 pytest-xdist 或其它并行参数。
3. 每次运行前后记录 free -m 与 /proc/loadavg;若运行前可用内存 < 6G 或 1 分钟负载 > 10,等待至满足再开始(最长 30 分钟,超时停止报告)。
4. 若 systemd-run --user 不可用,停止并报告,不在无限制状态下运行。
5. 计时敏感用例在受限资源下若失败,按既有 3 次单独重跑规则处理(重跑同样受限),不放宽资源限制规则。

三、继续
按 SKEL-RESTORE-25(含本裁定修订)执行:前置已完成,回报“等待用户确认开始”;用户回复“开始”后执行唯一一次 qb-discover 与 campaign-discover --dry-run。其余要求不变;推送报 Permission denied 时提交后停止,由用户本机推送。

### 48.1 资源边界检查与待执行点

未重跑第47节campaign-start-check,没有QB/Gerrit业务访问,没有启动浏览器。
仅运行systemd scope能力探针,再在受限scope内读取自身cgroup值并断言:
cpu.max=`200000 100000`,memory.max=`3221225472`,memory.swap.max=`0`,nice=`10`;
exit0。实际资源限制可用,不是只凭systemd-run返回成功推断。
前置可用内存14353MiB,1分钟loadavg=3.45;运行后14277MiB,loadavg仍3.45;
无需等待。free -m原文、三项loadavg、UTC/argv/exit与实际限额见
`evidence/restore/live-dryrun-01/resource-preflight-27.json`。
既有swap已用4092MiB,仅记录,没有清理或结束他人进程;新scope禁止swap。

仓外r01配置SHA256仍为
`68b4f39b1ad768629acff344fdd6e8e1812d109d74924330a9ceec3cb24dda44`,
state-root为空,不复用状态库。生产CLI、代理、测试均不改。
真正执行两个命令之前还会分别重新读取free -m/loadavg,不复用本次即时资源读数;
不满足时最多等待30分钟,systemd失败不回退无限制执行。
只有收到本次“开始”后才执行qb-discover一次,成功后再执行campaign-discover --dry-run一次;
任一步失败停止,不换构建、不重试。原始日志只留仓外。

后续报告将代理trace/elapsed_ms与原始日志响应元数据明确标NOT_COLLECTED,
status=ok只记裁定允许的运行时检查通过及SHA/大小,失败只记固定原因码,
不会把缺失trace解释为“安全事件为0”。当前为**等待用户确认开始**,
尚无本次失败包/日志读取/dry-run结果,真机发现仍未验证。

## 49. RESTORE-25/27真机执行与停止SKEL-RESTORE-28

2026-11-06,基线97217e0。用户确认原话:“开始”。新运行目录仍为r01,
没有复用旧state-root或状态库。确认后初次资源查询available9284MiB、load1=12.96,
未启动浏览器;准备记录工具期间下降,正式运行前重新查询available9555MiB、
loadavg=6.86/6.95/4.09才启动。未清理资源或结束他人进程。

唯一一次qb-discover的UTC起止05:45:48.258756–05:47:25.550388,97.291秒,exit4。
外层systemd-run --user --scope CPUQuota=200%、MemoryMax=3G、MemorySwapMax=0,
内部nice10;实查scope值为2s/3221225472/0。运行后available9277MiB,
loadavg=3.65/5.81/3.96。完整argv、资源原文与CLI应答见
`evidence/restore/live-dryrun-01/producer-command.json`。

CLI返回DISCOVERY_REPORT_AMBIGUOUS,reason=REPORT_STRUCTURE,
failure.command=discovery_read,failure_category=null;
错误捕获时agent_exited=false、agent_exit_code=null。当前应答不含具体页面或首个失败项,
不据错误名猜测Details、包名或架构列有何问题。stderr未见固定AGENT_STOPPED行,
但trace/elapsed_ms未收集,不推定安全事件为0。停止依据就是CLI错误码。

state-root为空,没有清单/包日志,故campaign-discover --dry-run未运行。
zlib/libtirpc/elfutils均为NOT_COLLECTED,不是已确认“默认过滤跳过”;
没有status=ok日志可填等价运行时证据。日志元数据及完整代理trace按RESTORE-27记
NOT_COLLECTED。state.db、kb.jsonl、ws未创建,未克隆/建档/提交/推送。
执行后scope inactive/dead,本仓库代理与p5q-browser-*残留均未发现。

[停止报告SKEL-RESTORE-28](evidence/restore/live-dryrun-01/stop-report-SKEL-RESTORE-28.md)
记录上述事实及候选离线核验/封闭诊断方案,均未实施。唯一一次机会已使用,
不重跑、不换构建、不补读。收尾记录的实际结论为“已执行但未通过验证”。

结构化证据归档/扫描在CPU400%、MemoryMax6G、swap0、nice10的scope内完成;
前available9137MiB、loadavg2.01/4.76/3.75,后9030MiB、loadavg相同。
固定CLI应答键值逐项校验、PageRedactor凭据检查通过,已知本机身份残留0;
没有读取/输出本次QB身份原文,会话身份字符串本身NOT_COLLECTED。
仓内仅命令/资源事实、固定应答和报告,没有日志正文、配置或DB二进制。

最终文档/证据检查亦在CPU400%/6GiB/swap0/nice10 scope内串行完成,exit0:
design 0 problem、git diff --check通过、生产/测试与97217e0零diff;
证据目录凭据检查通过、已知本机身份残留0。前后free -m/loadavg及完整argv
见`live-dryrun-01/final-checks-command.json`。不运行全仓或任何第二次真机命令。

## 50. 实施裁定 SKEL-RESTORE-29:REPORT_STRUCTURE 离线复现与封闭诊断

基线 b7a55d8。裁定原文:

一、离线复现(不登录、不联网)
1. 用仓内已有的真实脱敏归档,按 qb-discover --build-id 1204735 的实际调用顺序,逐页送入当前生产 discoveryDOM / DiscoveryScope.consume:live-02 的 /build/1204735/overview、/variables,/build/1204736/overview、/variables,/build/1204736/html_report;live-04 的 iframe 页(HTML%20REPORT/index.html)。若当前代码的调用顺序或页面集合与此不同,以代码实际顺序为准并写明。
2. 记录第一个失败的页面类型与检查项;若失败仅由归档本身的已知缺陷(live-02/02.response.html 被误改的 </thead>)引起,单独标注,不据此修改解析规则,改用其它不受影响的归档页验证同一检查。
3. 若全部归档均通过而无法复现,写明并进入第二条,不修改解析逻辑。

二、封闭诊断字段(无论是否复现都实施)
DISCOVERY_REPORT_AMBIGUOUS 及其它发现阶段结构错误的应答增加:page_kind(parent_overview | parent_variables | child_overview | child_variables | report_entry | report | log 之一)与 first_failed_check(固定枚举,至少覆盖 identity_mismatch、child_link_count、variables_missing、iframe_count、header_missing、header_duplicate、arch_unmapped、package_duplicate、cell_multi_link、link_text、link_path),外加相关计数;不输出 URL、页面文本、身份或包名之外的内容(包名可输出)。补 Node/Python 用例逐项断言。

三、修复
1. 若复现出的失败源于解析假设与真实页面结构不符,按真实结构修正解析规则,并把对应真实归档页作为回归夹具加入测试(只用已脱敏归档,入仓前残留扫描为 0)。
2. 不得放宽:身份核对、帧归属、精确路径登记、html_report 例外范围、失败单元格“唯一链接且文字为 failed”的规则、read_text 运行时检查。若修复必须放宽其中任一项,停止报告。

四、门禁
全仓 pytest(不加 -x)、mypy、ruff、lint-imports、design 检查,全部按 SKEL-RESTORE-27 第二条资源限制运行;计时敏感名单按既有规则。

五、再次真机试运行
门禁通过后回报“等待用户确认开始”;用户回复“开始”后,用与 SKEL-RESTORE-28 相同的命令、新的仓外运行目录(r02)执行一次 qb-discover;成功则接着执行 campaign-discover --manifest ... --dry-run。失败则停止报告(应答中应已含第二条诊断字段),不重试。归档与回报要求同 SKEL-RESTORE-25/27。推送报 Permission denied 时提交后停止,由用户本机推送。

### 50.1 执行边界与修改前复现

只处理本裁定,不复用此前“开始”的真机授权。`qb_collect.collect` 的实际顺序与
裁定六页一致;使用生产 `TrustedPage.run(discoveryDOM, raw)` 在 about:blank
隔离环境解析归档,再串行调用生产 `DiscoveryScope.consume`。禁止全部网络请求,
不执行归档脚本、不登录。脚本与原始结果放在 `evidence/restore/diagnostics-29/`。
每次浏览器/门禁运行均经 `run_limited.py` 检查资源、最多等待30分钟,
再用 systemd user scope CPU400%/6GiB/swap0/nice10 串行运行,记录前后资源。
既有无关工作树改动不纳入本次提交。

### 50.2 复现结论与实现

`replay-before/stdout.txt`与`replay-checks/stdout.txt`:前五页通过,第六页
`live-04/02.response.html`(report)为首个失败页。Details四列表共259行,
零基第238行(归档第1482–1485行)是`toybox - details`,原`packageOK`包名检查失败。
该行四格无链接,紧邻的toybox行三架构均为unresolvable。并非`failed`链接无class的问题,
也不是live-02/02.response.html的已知坏标签:该父overview直接通过,原始坏标签未改。
复现没有网络请求;仅本机Chromium/about:blank+隔离DOMParser。

修复仅允许这种紧邻、包名完全对应、前行三列均无链接且unresolvable、说明行无链接
的说明行不作为包处理;不登记它的日志。不改变普通包名正则,失败单元格仍须唯一
failed链接。孤立/异名说明行、说明行有链接、前行failed、重复说明行、缺格均拒绝。
真实六页归档直接作为`test_qb_discovery_archives.mjs`夹具输入,不修改、不复制原文。
修复后`replay-after`六页通过;报告中的zlib/libtirpc/elfutils可识别,
这仅为离线结构结果,没有读取任何真实包日志,不提前推断analyzer分类。

封闭诊断:代理结构错误应答增加page_kind/first_failed_check/counts;
Python严格校验类型、枚举、计数键与0至2^53-1的非布尔整数范围,错误落入
QB_BROWSER_UNAVAILABLE协议错误。有效字段保留在QbBrowserError.discovery_facts,
沿既有failure_facts进入CLI的failure及驱动trace;既有错误码映射不变。
counts只允许actual_count、expected_count、row_index、column_index,不含文本/URL。
枚举表和用例见本轮README与tests/unit/test_qb_discovery_diagnostics.py。

配置页枚举缺口已询问用户,原话:**“批准增加 configuration”**。
因此page_kind为原七种加configuration,不把--since配置页错误混称parent_overview;
已写design.md第4.6节恢复项落地裁定第13条。无其它授权扩展。

开发定向检查原记录保留:focused为51失败/21通过(新增诊断校验在JSON解码前引用response,
本次实现错误已修);focused-2为1失败/71通过(新增测试误认为驱动不映射Build ID错误,
实际既有契约为QB_FETCH_FAILED且agent_code保留QB_READ_ID_MISMATCH,只修新测试)。
这两次均为开发定向检查,非完整门禁;未改既有断言或放宽计时阈值。

### 50.3 门禁与停止报告 SKEL-RESTORE-30

证据根目录为`evidence/restore/diagnostics-29/`。全部运行串行、CPU400%、
MemoryMax6GiB、MemorySwapMax0、nice10;资源不足先等待,没有放宽限制。

| 检查 | 实际结果 | 证据子目录 |
| --- | --- | --- |
| mypy | 172文件,exit0 | mypy |
| ruff | 完整待提交代码检查通过 | ruff |
| import-linter | 7 kept / 0 broken | imports |
| design检查 | 0 problem | design |
| 代理静态/单元 | 183 Node测试通过,pytest包装1通过 | static |
| 四组拦截安全 | 4/4,pytest包装1通过 | safety |
| collect | 3550 nodeid,既有3502全保留,新增48 | collect |
| 完整pytest,无-x | 3548通过 / 1失败 / 1既有skip,1477.96秒 | full |
| build单独重跑1 | 1通过,26.61秒 | retry-c5a-build-1 |
| build单独重跑2 | 1失败,87.93秒 | retry-c5a-build-2 |
| build单独重跑3 | 未运行:任一次失败即停 | 不适用 |

全仓唯一失败为`test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]`:
假qb-trigger子进程150秒TimeoutExpired,假服务器received为空,没有agent日志。
清单允许的独立重跑第二次又失败,未满足3次全通过,不把门禁算通过。
本轮新增用例及C8调查包装在完整门禁中通过,没有新增skip或修改旧断言。

| 运行 | 前available MiB / load1 | 后available MiB / load1 |
| --- | --- | --- |
| full | 6658 / 3.37 | 6420 / 3.29 |
| retry2 | 6403 / 2.48 | 6635 / 14.83 |

每次完整free -m、三项loadavg、CPU核数及CPU前十进程名/占用见对应command.json;
retry1及其它门禁同样留存。后负载升高不构成放宽门禁依据。

读取失败观测表新增一行(不替换此前观测):

| 采样 | 阶段与断言原文 | harness_failure | trace | 处置 |
| --- | --- | --- | --- | --- |
| RESTORE29 retry-c5a-build-2 | fill返回QB_BROWSER_UNAVAILABLE/UNKNOWN;close断言`assert 0 <= close_seconds < 5`,实际20.91734027862549 | 未提供该字段 | OPERATION_FAILED=0;AGENT_STOPPED=1,UNKNOWN | 停止,不归因为已确认的纯计时问题 |

代理close_started/close_finished差18.400秒;服务器submissions为空、builds=0,
仅本机夹具,没有真实提交。事后发现`/dev/shm/p5q-browser-3ByKn8`残留,
mtime为2026-11-06 14:35:45 +08:00;未擅自清理或结束进程。
证据检查最初因残留断言失败,原记录保留;之后改为如实记录,不是把清理算通过。

[停止报告](evidence/restore/diagnostics-29/stop-report-SKEL-RESTORE-30.md)
保留本轮未验收实现与原始失败。未启动r02、未要求登录、未运行真实QuickBuild/Gerrit/gbs,
未写任何专用状态库。下一步须设计方裁定,不复用过去的“开始”。

完整性记录见本轮`integrity-and-archive-scan.json`:代理前缀前后相同
(`594107e04912b90ef803b3f2a1142b5b42afab83399829dba4e3c8e95664095c`),
完整门禁后的生产/测试源文件无变化。六份真实归档不修改且复检身份残留0。
收集输出与完整pytest XML中与身份字符串重合的测试标识符做脱敏,不改失败正文;
前后hash记录于`test-identifier-redaction.json`,nodeid比较对两侧作同样替换。
残留profile进程引用检查未发现携带该类user-data-dir参数的进程,不推断目录可删除。

## 51. 实施裁定 SKEL-RESTORE-31:解析认可与计时敏感重新验收

基线582c65d。裁定原文:

一、解析修复与诊断:设计方已审阅 qb_discovery_scope.mjs / qb_browser_agent.mjs / qb_browser.py 改动、test_qb_discovery_diagnostics.py、replay-before/after 输出及 live-04/02.response.html 第1482行说明行,判定修复符合真实页面结构、未放宽任何安全规则,代码层面认可。“包只在部分架构 unresolvable 时说明行被拒”保持失败关闭,记入收尾文档已知限制,本轮不改。

二、C5a 失败归属:
1. 先书面列出本次 diff 中所有可能影响 fill/submit/close 路径的改动点并逐条说明(设计方判断:agent 新增字段仅在 discovery_read/read_text 生效,decode_response 新分支仅在应答含 page_kind/first_failed_check/counts 时进入),若发现任何触及该路径的改动,停止报告。
2. 计时敏感重新验收:从头执行一轮“三次单独重跑”,三次全过才算通过。每次开始前除既有条件(available≥6G、load1≤10)外,额外等待 load1≤4 且 swap 可用≥512MiB,最长等 30 分钟;超时则停止报告,不放宽、不结束他人进程、不清缓存。资源限制同 SKEL-RESTORE-27。
3. 若三次中任一失败:在仓外 git worktree 检出 b7a55d8,同样条件下单独跑同一 nodeid 三次作对照,记录结果后停止报告,不进入真机。

三、残留 /dev/shm/p5q-browser-3ByKn8:用 fuser/lsof 确认无进程引用,且名称前缀与 C5a 测试工具创建的浏览器临时目录一致,则删除并在证据中记录检查输出;任一条件不满足则保留并在报告中说明。

四、第二条三次全过后,补跑一次完整 pytest(不加 -x,资源限制同前);其中 C5a 若再次失败,按既有计时清单规则处理。全部通过则更新 progress.md 与收尾文档(含第一条已知限制),提交推送后回报“等待用户确认开始”;用户回复“开始”后按 SKEL-RESTORE-29 第五条执行 r02 真机试运行(qb-discover 成功则接 campaign-discover --dry-run),失败即停止报告,不重试。

五、推送报 Permission denied 时提交后停止,由用户本机推送。

### 51.1 路径审查与残留处理

[路径审查](evidence/restore/revalidation-31/path-audit.md)逐项覆盖582c65d的三个生产
文件和测试/文档改动。合法fill/submit/close的实现、输入输出、超时与关闭路径均未改;
共享异常对象仅新增默认None属性,合法常规应答不含新字段,不进入新诊断分支。
discoveryScope未启用的C5a不会调用新增的说明行解析。没有以此认定先前UNKNOWN的根因。
本轮不改生产代码、旧测试断言、资源限制或冻结稿。

2026-11-06 15:28:38 +08:00,fuser -v与lsof -nP +D均exit1、stdout/stderr为空;
再次检查仍无引用,且目录不是符号链接。C5a测试入口调用生产createRuntime,
其mkdtemp('/dev/shm/p5q-browser-')前缀一致。15:29:00 +08:00仅删除
`/dev/shm/p5q-browser-3ByKn8`,exit0,之后exists=false。
见`revalidation-31/profile-check.json`、`profile-removal.json`,未处理其它目录/进程。

重新验收以`revalidation-31/run_one.py`记录每10秒前置采样,满足available≥6GiB、
load1≤4、SwapFree≥512MiB才启动;最多等待1800秒。测试启动时强制
systemd user scope CPU400%/MemoryMax6GiB/MemorySwapMax0及nice10,
不使用-x或并行参数。首轮开始等待时swap余约28MiB,尚未启动测试。

### 51.2 资源等待超时:停止报告 SKEL-RESTORE-32

2026-11-06 15:28:18至15:58:18 +08:00,共181次采样,单调时钟等待1800.025秒。
SwapFree在0–28752KiB之间(最高约28.08MiB),始终低于524288KiB门槛。
MemAvailable范围6373816–7300576KiB,load1范围0.05–2.69,两者始终达标;
唯一持续阻塞项为swap余量。最后available7035MiB、swap余约1MiB、load1=0.39。
原始free -m、loadavg、CPU前十及UTC逐次写入
`evidence/restore/revalidation-31/retry-1/command.json`。

等待器exit125、stop=RESOURCE_WAIT_TIMEOUT、started=false。这是资源前置停止,
不是pytest失败:本轮测试执行0次,通过/失败/跳过均不适用;第2、3次未启动;
不满足“测试中任一次失败”的基线对照分支,未创建b7a55d8仓外worktree。
未补跑全仓、未执行r02、未弹登录窗口,没有清缓存、swap操作或结束进程。
指定废弃profile已按51.1完成删除,与swap等待条件分开记录。

[SKEL-RESTORE-32停止报告](evidence/restore/revalidation-31/stop-report-SKEL-RESTORE-32.md)
与[本轮说明](evidence/restore/revalidation-31/README.md)记录结果。
收尾文档第5节已列“部分架构unresolvable说明行仍被拒”的已知限制。
生产、测试、design.md、冻结稿均未修改;仅文档/证据提交。先前失败证据未覆盖。
资源达标后仍需从头完成三次重验及全仓门禁,当前不进入“等待用户确认开始”阶段。

## 52. 实施裁定 SKEL-RESTORE-33:SwapFree只观测与重新验收

基线dbdc8ee。裁定原文:

一、撤销 SKEL-RESTORE-31 第二.2条新增的“swap 可用≥512MiB”前置条件。理由:已换出页面在空闲后不会自动回收,SwapFree 不反映当前内存压力;且测试 scope 已设 MemorySwapMax=0。SwapFree 继续每次采样记录,仅作观测,不作门槛。

二、其余前置条件不变:每次开始前 available≥6G 且 load1≤4,最长等待 30 分钟;超时停止报告,不放宽、不结束他人进程、不清缓存、不执行 swapoff/swapon。资源限制同 SKEL-RESTORE-27。

三、从头执行 SKEL-RESTORE-31 第二.2条的三次单独重跑(同一 nodeid,三次全过才算通过);任一失败按其第二.3条在仓外 worktree 检出 b7a55d8 做三次对照后停止报告。

四、三次全过后按 SKEL-RESTORE-31 第四条执行完整 pytest、更新 progress.md 与收尾文档、提交推送,回报“等待用户确认开始”;用户回复“开始”后按 SKEL-RESTORE-29 第五条执行 r02 真机试运行,失败即停止报告,不重试。

五、推送报 Permission denied 时提交后停止,由用户本机推送。

本轮证据新建于`evidence/restore/revalidation-33/`,不修改31/32证据。
run_one.py继续记录SwapFree,不再比较其值;其余资源门槛不变,每次测试使用
systemd user scope CPU400%/MemoryMax6G/MemorySwapMax0/nice10。
run_three.py串行运行同一build参数,任一非零立即返回,不并行、不加-x、不改断言。
生产、测试、冻结稿不改;51.1的路径审查与指定残留清理结论继续有效。

### 52.1 三次独立重跑

同一nodeid的retry-1/2/3分别1 passed,pytest耗时30.78/23.13/23.27秒。
每次均重新满足资源前置,其中retry-2等待30.080秒、retry-3等待10.039秒。
每轮实际触发CLI与两次读取CLI的关闭尾段均约0.073–0.079秒,没有UNKNOWN停止。
详见`revalidation-33/README.md`、各次`c5a/build/commands.json`及代理trace。
三次全过,不触发b7a55d8仓外对照分支。随后以同样资源限制启动完整pytest,
不加-x;完整结果另记,不提前标为全仓通过。

### 52.2 完整门禁与交付边界

2026-11-06 16:19:10至16:38:51 +08:00,完整pytest exit0:
**3549 passed、0 failed、1既有skipped**,pytest耗时1180.28秒,scope包裹耗时1180.841秒。
完整运行未使用-x,无新增skip/xfail,计时清单本轮无失败、无需追加重跑。
运行前available6744872KiB/load1=0.98,运行后6766016KiB/load1=2.44;
SwapFree分别4/100KiB只观测,MemorySwapMax=0始终保持。
原始argv/UTC/exit/free/loadavg/CPU前十见`revalidation-33/full/command.json`,
stdout/stderr、JUnit与C5a/C8记录均归档。C8包装通过;竞争/故障注入场景的预期
拒绝保留在`full/c8/`,不将它们混称为新的门禁失败。

546份生产/测试/冻结稿等文件前后hash一致;代理、驱动、测试断言均无本轮改动,
所以没有新增nodeid,3550项完整保留。未复跑mypy/import-linter等无代码变化的门禁,
沿用RESTORE-29已通过的记录;本轮按RESTORE-31/33只重验三次C5a与完整pytest。
结束后未发现p5q-browser-*残留。详见`source-before.json`与`summary.json`。

证据全文扫描已登记历史身份残留0;完整JUnit的4处测试标识符与身份字符串重合,
仅这些标识符替换为[REDACTED_IDENTITY],测试结果不变,原失败正文未改(本轮无失败)。
前后hash/替换次数见`identifier-redaction.json`;未输出或保存历史身份原文。
仅本机假HTTPS与临时裸库,未创建r02目录/配置/状态库,未运行任何真机命令或登录。

RESTORE-30的UNKNOWN根因未另行确定,不因本轮通过而改写历史停止报告。
按RESTORE-33口径重新验收通过;收尾第3/5节同步结论与已知限制。
证据提交推送之后**等待用户确认开始**;收到新的“开始”才按RESTORE-29第五条
执行一次r02,成功后接dry-run,任一步失败即停,不复用以前的确认。

附加文档/证据检查在同样资源限制下串行执行。doc-checks首次仅新证据脚本的5处
import排序未过Ruff,整理后doc-checks-2 exit0:证据脚本Ruff通过、design检查0 problem、
文档diff --check通过、源码变化0、身份残留0。未改生产或测试,没有重跑/覆盖功能测试。
原始pytest输出及合成HTML证据的行尾空白保留,不清洗原始日志。
