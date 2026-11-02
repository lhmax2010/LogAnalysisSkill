# Stage21 Clang Campaign Skeleton

日期:2026-11-02。状态:**STOPPED_BASELINE_FAILED**。
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
| 1 | 第4节拆分,先derive_commit全仓验证再批量;第9节第3项修订登记;第4.4节验收 | STOPPED,未拆分基线失败,尚未试搬derive_commit |
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
| 拆分前后nodeid比较/collect/skip | NOT_RUN_STOPPED;仅拆分前2903个nodeid,无拆分后列表,未计算差集 |
| 每个旧模块名与新模块对象同一性 | NOT_RUN_STOPPED;尚未建立新包/别名 |
| 新权威源码植入禁止调用,既有静态检查红例 | NOT_RUN_STOPPED;尚无新权威源码 |
| import-linter全绿与a/b/d/e红例(e直接/间接两例) | NOT_RUN_STOPPED;仅既有6条基线合约通过 |
| .mjs完整hash/前缀hash、四组安全测试 | NOT_RUN_STOPPED;原位置hash不变,未迁移/未在新位置重跑 |
| 干净wheel安装、八入口全部子命令help、资源hash | NOT_RUN_STOPPED;尚未拆包 |
| 全仓pytest对照 | STOPPED;拆分前2901 passed / 1 failed / 1 skipped,拆分后未运行 |

测试物理路径改动清单:0条,未修改任何测试。停止报告见第6节。

## 6. 停止报告 SKEL-B1-02:未拆分基线失败

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
