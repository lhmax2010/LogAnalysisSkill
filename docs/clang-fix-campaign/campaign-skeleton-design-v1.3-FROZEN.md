# Clang 修复活动:骨架收尾与 skill 拆分设计 v1.3-FROZEN

日期:2026-11-02。作者:Claude(设计)。批准:FatTank。实施:Codex。
仓库:github.com/lhmax2010/LogAnalysisSkill,分支 clang-fix-campaign,代码基线 2c9ed30(当前 HEAD accd7f4 只增加 P5Q 收口文档,不含代码改动)。
2026-11-02 由 FatTank 批准冻结,内容与 v1.3 草稿相同。
v1.3 是 v1.2 经第三轮定向核对(ChatGPT、Claude Code)后的修订。修改与采纳来源见附录 A(v1.0→v1.1)、附录 B(v1.1→v1.2)与附录 C(v1.2→v1.3)。

## 0. 本文件的作用与权威关系

0.1 目的:用最短路径把 Clang 修复活动做成能从头跑到尾的完整链路,并把活动代码按"一个动作一个 skill"拆分。不追求一次做全,砍掉的部分登记恢复条件,以后按需补。

0.2 权威关系:
- `design.md`(v1.5.x)与各阶段冻结设计中,凡本文件**保留**的命令,其参数、流程、输出、退出码、错误码、表结构与内部 API 契约继续有效,实施时以原文为准。
- 本文件只改变三类内容:阶段范围(第 2 节)、目录与模块归属(第 4 节)、本文第 5 节逐条写明的简化与新增(含对既有命令 sandbox-submit、qb-trigger 增加放弃屏障检查;为新命令 review-submit、baseline-reproduce、campaign-add-unit 规定冻结稿未规定的文件锁,见 5.1–5.4)。与冻结稿冲突时,仅在这三类内容上以本文件为准;本文没有写到的,一律按冻结稿。
- 冻结稿正文不修改。唯一的改动是按以往做法在 `design.md` 末尾的修订序列中追加一节(第 4.4、4.5 节即此先例):版本号加一,该节只写五件事——本文件是剩余阶段范围、目录归属与第 5 节新增行为的权威;新增错误码 `INTAKE_ANALYZER_FAILED`、`INTAKE_CLONE_FAILED`、`REJECTED_UNIT_NOT_TERMINAL`、`REJECTED_UNIT_ABANDONED`;sandbox-submit、qb-trigger 增加放弃屏障检查;`campaign_lifecycle` 新增第四个释放 API `release_abandoned_worktrees`;模块路径以本文第 4.2 节映射表解释。不改动任何已有条目。
- 本文件冻结的前置条件:P5Q 收口文档(`review/p5q-closeout.md`)已提交。该条件已满足(提交 accd7f4)。

0.3 不变的硬约束(本文件任何简化都不放宽):
1. Change-Id 只由 Gerrit commit-msg hook 生成。
2. 工具永不点击 Accept / Ready to Accept。
3. 账号密码不落盘、不进对话;需要网站登录时由工具弹出浏览器窗口,FatTank 只在窗口里登录。
4. 第 7 节第 4 批之前,不对真实 Gerrit 做任何推送(sandbox 与 refs/for 都不推),不运行任何 QuickBuild 真机命令。对真实 Gerrit 的只读访问(克隆、`git ls-remote`)不受此限。
5. 提交署名用 Hao Lin <hao.lin@samsung.com> 或 liushanshan <ss0217.liu@samsung.com>。
6. 安全核心文件(tizen-ci-shared 的 `state/db.py`、`state/keys.py`、`state/records.py` 与 tizen-build-verify 的 `build_verify.py`)不改、不移动;浏览器代理 `qb_browser_agent.mjs` 内容不改,只移动位置。
7. 状态库只追加、不更新;现有表结构、事件类型、状态名不改名,不新增状态名与事件类型。

## 1. 现状

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0–P4.9 | 状态层、修复轮、旧代码拆成 6 个 skill | 已关闭 |
| P2 / P3 / P4 / P5 | 提交身份、三架构聚合、派生提交、沙箱提交 | 已关闭 |
| P5Q | QuickBuild 提交、自动认领、读结果 | 真机已通(1204698/1204699 PASS);收口文档提交后关闭 |
| P1 | 环境事实 spike | 随 P5Q 收口一并关闭 |
| P5R–P12 | 见第 2 节 | 未开始 |

需要特别说明的事实:到目前为止,真机验证用的是合成的三架构 PASS 记录;"建档 → 基线复现 → 本地修复 → 沙箱推送"这一段从未在真实包上连起来跑过。第 7 节为此把真实 gbs 单独提前为第 3.5 批。

## 2. 剩余阶段取舍

原设计剩余约 3,600 行。取舍后新增约 1,500 行(估算,不作验收标准)。

| 原阶段 | 内容 | 处置 | 理由 | 砍掉/简化的后果 |
|---|---|---|---|---|
| P9 自动发现 | 从 Clang QuickBuild 总览页自动找失败包并建档 | **砍,改为手工建档命令**(5.1),建档同时准备源码主副本 | 失败包现在由人逐个分析,自动发现不是瓶颈;自动发现要登录 QuickBuild | 每个包由人(或剧本)给出包名、构建号和本地 CI 日志 |
| P6 基线复现 | 三架构本地复现 CI 失败 | **保留,去掉 rebaseline** | 修复轮的首轮输入与 `BASELINE_REPRODUCED` 状态依赖它 | `previous_evidence_missing` 导致的 HELD 只能人工处理(HELD 仍可经 5.4 释放副本,不形成死结) |
| P7 diff 转修改规格 | 把已有 CL 的 diff 转成 edit_spec | **砍** | 只服务知识库复用路径 | 修法只有"新生成"和"受约束抑制"两种来源 |
| P8 知识库 | 修复经验写入与复用 | **砍** | 800 行,独立,不在主链上;冻结稿已允许 `SANDBOX_PUSHED` 直接进入 `QB_REQUESTED` | 不积累经验 |
| P8.5 启动前自检 | 独立 CLI | **缩成一条小命令**(5.5) | 剧本开头需要一个可测试、确定的检查 | 检查项从冻结稿的全量缩为五项 |
| P5R 审核提交 | QuickBuild PASS 后推 refs/for | **保留,去掉人工降级路径**(5.3) | 活动的最终产出 | 读不到结果的 unit 只能重读、按 P5Q 指引处置,或放弃(5.4) |
| P10 生命周期与报告 | 释放副本、状态报告 | **保留最小版**(5.4),新增"放弃"出口与放弃屏障 | 不释放副本会占满磁盘;放弃后必须挡住对外动作 | 部分 PASS 副本在 unit 结束或放弃时整体释放;报告只出一张状态表 |
| P11 剧本与对抗测试 | 剧本、启动模板、对抗测试组 | **保留剧本与模板,砍对抗测试组**。"不得直调 build-verify"改由依赖合约与剧本静态检查保护(4.3、6);"push 路径不得被绕过"改由 review-submit 六道重校验逐项拒绝用例保护(6) | 剧本就是总编排 | 跨命令的篡改/竞态组合场景不单独成组 |
| P12 真机端到端 | 一个包全链路真跑 | **保留**,拆为第 3.5 批(只用真 gbs)与第 4 批(推送与 QuickBuild) | 唯一一次真机 | — |

被砍项的恢复条件见第 8 节。

## 3. 骨架版端到端流程

剧本按以下顺序调用各 skill 的命令。括号内为进入的状态。

1. 启动检查 `campaign-start-check`(5.5)。任一项不满足即停,不猜默认值。
2. 建档 `campaign-add-unit`(`DISCOVERED` → `CI_EVIDENCE_READY`):输入包与本地 CI 日志,产出 CI 证据、建 unit、准备源码主副本。
3. 基线复现 `baseline-reproduce`:先主架构,再其余两个架构(`BASELINE_RUNNING` → `BASELINE_REPRODUCED` 或终态 `NOT_REPRODUCED`)。
4. 修复轮 `campaign-repair-step`(已有):AI 按剧本生成 edit_spec,每轮经该命令编译、记账、判收敛;三架构全过进入 `LOCAL_3ARCH_PASS`,失败终态为 `DENIED` / `STALLED` / `REGRESSED` / `ROUNDS_EXHAUSTED`。
5. 沙箱推送 `sandbox-submit`(已有):`SANDBOX_PUSHED`。
6. 验证构建 `qb-trigger`(已有):`QB_REQUESTED` → `QB_TRIGGERED`。
7. 读结果 `qb-result-fetch`(已有),非终态时由人隔一段时间再读:`SANDBOX_QB_PASS` / `SANDBOX_QB_FAILED`。
8. 审核提交 `review-submit`(新):`REVIEW_PUSHED`,或 `REVIEW_INELIGIBLE`。
9. 收尾 `campaign-finish-unit`(新):按终态释放或保留副本。
10. 报告 `campaign-report`(新):输出全部 unit 的状态表。

任一步停住且人决定不再做这个包时,用 `campaign-release-worktrees --abandon`(5.4)放弃,剧本转下一个包。

批量:剧本对每个包串行执行 2–9,第 10 步在最后统一执行。不做多包并行。

## 4. skill 拆分(轻量做法)

### 4.1 原则

1. 整个文件原样移动,不改函数体;只允许改 import 行(改为新包名)。
2. 旧模块名用**模块别名**转发:旧文件只做 `sys.modules[__name__] = <新模块>`(或等价写法),让旧名和新名指向同一个模块对象。旧路径的字符串补丁与模块对象补丁都作用在真实模块上。不得用 `from x import *` 形式转发。新包中的代码不得 import 任何 `ci_triage` 名字(含别名)。
3. `python -m ci_triage <子命令>` 保留并转发到新位置;每个执行包另有自己的入口 `python -m <包名> <子命令>`。剧本只用新入口;旧入口供历史证据脚本使用。
4. 不做逐符号审计、不做逐字节对照。验收标准是第 4.4 节列出的检查。
5. 先搬一个后批量:第 1 批先只搬 `derive_commit`(依赖面小、被多处补丁覆盖)并跑全量 pytest,0 失败后再搬其余。

### 4.2 目录与文件归属

新 Python 包共八个:一个公共库 `tizen_campaign_core`(无 CLI)和七个执行包。

| 目录(新) | 类型 | 包名 | 文件 |
|---|---|---|---|
| tizen-campaign-core | 公共库(无 SKILL.md、无 CLI) | tizen_campaign_core | campaign_state、_campaign_workspace、previous_evidence、suppress_policy、aggregate、derive_commit、submission_identity、_sandbox_git;新增 campaign_lifecycle、reproduce |
| tizen-campaign-repair | skill | tizen_campaign_repair | campaign_repair_step |
| tizen-sandbox-submit | skill | tizen_sandbox_submit | sandbox_submit |
| tizen-qb-verify | skill | tizen_qb_verify | qb_trigger、qb_result_fetch、qb_discovery、qb_binding、qb_evidence、qb_result_html、qb_browser、qb_browser_agent.mjs、qb_config、qb_redact |
| tizen-campaign-intake | skill(新) | tizen_campaign_intake | campaign-start-check、campaign-add-unit |
| tizen-baseline-reproduce | skill(新) | tizen_baseline_reproduce | baseline-reproduce |
| tizen-review-submit | skill(新) | tizen_review_submit | review-submit |
| tizen-campaign-report | skill(新) | tizen_campaign_report | campaign-finish-unit、campaign-release-worktrees、campaign-report |
| tizen-clang-campaign | 编排 skill(新) | 无代码 | SKILL.md(剧本)、campaign-kickoff-template.md |
| tizen-ci-triage | 保留 | ci_triage | 旧分诊主流程(orchestrator、runner、batch_cli、quickbuild_log)、`__init__.py`、`__main__.py`、cli.py 入口与上述转发 |

补充:
- `ci_triage/verify/` 子包(仅 `__init__.py`)原样保留,不移动、不删除。
- 八个新包各自新增 `__init__.py`;七个执行包另新增 `__main__.py`。这些文件是新代码,不受"原样移动"约束。
- **必须改的三行 import**:`qb_trigger.py`、`qb_result_fetch.py`、`qb_binding.py` 现各有 `from ci_triage import sandbox_submit as sandbox`,改为 `from tizen_sandbox_submit import sandbox_submit as sandbox`。不改也能运行(别名使旧名指向同一模块),但静态依赖图上成了"执行层 → ci_triage"的向上依赖,第 4.3 节层次合约会红。改后以 `submit.` 为前缀的现有补丁仍作用在同一模块对象上。
- 每个新 skill 的 SKILL.md 按现有 `tizen-qb-discover/SKILL.md` 的格式写:用途、何时用/何时不用、输入、输出、错误码、命令示例。

### 4.3 依赖方向与 import-linter 合约

依赖方向(上层可依赖下层,反之不可):

```
ci_triage
tizen_campaign_intake | tizen_baseline_reproduce | tizen_campaign_repair | tizen_qb_verify | tizen_review_submit | tizen_campaign_report
tizen_sandbox_submit
tizen_campaign_core
既有 skill 层(tizen_convergence_judge | tizen_qb_discover | tizen_gerrit_fetch | tizen_build_verify | tizen_gerrit_submit | tizen_triage_report | gbs_patch_suggest)
tizen_ci_shared
```

说明:core 现有代码已依赖既有 skill(campaign_state → tizen_convergence_judge;suppress_policy → tizen_build_verify.edit_spec_guard),所以 core 放在既有 skill 层之上。sandbox-submit 单独一层,使 qb-verify 与 review-submit 对它的依赖成为合法的下层依赖;同层各包之间互不依赖。

build-verify 单列:只有 tizen_campaign_repair 可以依赖 `tizen_build_verify.build_verify`。core 与其它执行包只能 import `tizen_build_verify.edit_spec_guard` 与 `tizen_build_verify.workspace` 这两个子模块本身,写法必须是 `from tizen_build_verify.edit_spec_guard import …` / `from tizen_build_verify.workspace import …`。**不得写 `from tizen_build_verify import …`**(即使取的是 `create_worktree`、`validate_edit_spec` 这类在 `__init__` 中重导出的名字):包的 `__init__.py` 导入了 `build_verify`,根导入会形成"消费者 → tizen_build_verify → tizen_build_verify.build_verify"的间接链,被合约 e 判违约。合约只写一条,禁止目标是 `tizen_build_verify.build_verify`;不要把包根 `tizen_build_verify` 也写进 forbidden——import-linter 把导入任何子模块都算作导入包根,那样写会让 `suppress_policy → edit_spec_guard` 立即违约,而为此加 `ignore_imports` 会把合约对 core 的约束整体豁免。这条合约是"剧本与其它命令不得绕过 campaign-repair-step 直接编译"的静态保护。

`.importlinter` 具体改动(现有六条合约:root-layers、skill-independence、shared-layers、shared-no-uplink、shared-l1-independence、shared-l0-independence,全部保留):
a. `root_packages` 增加第 4.2 节的八个新包(含 `tizen_campaign_core`)。不加则新合约不分析任何模块、静默通过。
b. `root-layers` 改为上面的层次;保留原有 `ignore_imports` 与 `unmatched_ignore_imports_alerting = error`。
c. `skill-independence` 不变(只管既有 skill)。
d. `shared-no-uplink` 的 `forbidden_modules` 增加八个新包。
e. 新增 forbidden 合约 `campaign-no-direct-build`:source_modules 为 core 与除 tizen_campaign_repair 外的全部执行包,forbidden_modules 只有 `tizen_build_verify.build_verify`,不允许间接依赖。
新增其它跨包依赖须经设计方书面裁定。

### 4.4 拆分验收

1. 全量 pytest 通过,且拆分前的用例 id 集合是拆分后的子集:拆分前后各用 `pytest --collect-only -q` 导出一次 nodeid 列表,差集必须为空;零 collect 错误、零新增 skip。两份列表与差集归档。
2. 测试文件只允许机械地更新**物理路径**:源码取证路径(如 `test_qb_browser.py` 读取 `qb_browser.py` 做 AST 检查)、Node 测试对 `.mjs` 的导入路径、启动路径,一律改指新的权威文件。不得改断言、参数化集合或 nodeid;运行时补丁目标(旧模块名)不改。改动清单逐条记入 progress。另需证明源码静态检查扫的是新文件:在新权威源码中临时植入一个被禁止的调用,确认对应既有静态检查变红,然后删除(证据归档)。
3. 新增别名测试:对每个旧模块名断言 `sys.modules['ci_triage.X'] is sys.modules['<新包>.X']`。
4. import-linter 全部合约通过;并对第 4.3 节 a、b、d、e 各构造违规 import,证明 import-linter 会变红,记录输出后删除违规代码(一次性证明,证据归档)。合约 e 的红例指定两个:`tizen_review_submit` 中 `from tizen_build_verify.build_verify import build_verify`(直接);`tizen_baseline_reproduce` 中 `from tizen_build_verify import create_worktree`(经包根的间接链)。
5. `qb_browser_agent.mjs` 字节不变(sha256 前后一致);代理前缀 hash 不变;P5Q 冻结稿规定的四组安全测试在新位置重跑通过。`qb_browser.py` 中 `Path(__file__).with_name("qb_browser_agent.mjs")` 不需改动。
6. `pyproject.toml`:`packages.find.where` 增加八个新 `scripts` 目录,`include` 增加八个包;`package-data` 的 `ci_triage = ["*.mjs"]` 改为 `tizen_qb_verify = ["*.mjs"]`;其它显式列包或路径的配置(如 mypy)同步核对。在不含源码路径的干净虚拟环境中安装 wheel 后:能 import `tizen_campaign_core`;八个入口(七个执行包与 ci_triage)各子命令 `--help` 都成功;wheel 中 `tizen_qb_verify/qb_browser_agent.mjs` 存在且 sha256 与源文件一致。
7. 历史证据目录下的脚本不改、不重跑。

## 5. 新增与简化组件

### 5.1 campaign-add-unit(取代自动发现)

```
python -m tizen_campaign_intake campaign-add-unit
    --state-db <path> --config <campaign_config>
    --project <gerrit project> --branch <branch> --spec-name <spec>
    --base-commit <sha> --source-build-id <QuickBuild 构建号>
    --failed-arches <逗号分隔,页名形态> --ci-log <primary 架构的本地 CI 日志>
    [--toolchain-profile clang]
```

步骤(顺序固定):
0. **建档锁**:先非阻塞取得 `<campaign_workspace>/<unit_hash>/.intake.lock`(目录不存在则创建),持有到命令结束;取不到 → exit 4 `CAMPAIGN_STATE_BUSY`,不做任何写入。同一 unit 的两个建档进程因此不会并发发布证据或源码。
1. 规范化 failed_arches → 按冻结优先序定 primary_arch;失败架构不在白名单:调 `create_arch_rejected_unit`,exit 4 `REJECTED_ARCH_NOT_ALLOWED`(这类 unit 不进入基线与修复,没有副本,也不准备源码)。
2. **CI 证据发布(不可覆盖)**:analyzer 输出写到临时目录并算原始字节 sha256。发布沿用 repair-step 现有的 edit_spec 发布方式(`campaign_repair_step.py` 中 canonical edit_spec 的写法):在 canonical 同目录写临时文件并 fsync → `os.link(临时文件, canonical)` 首次发布 → 遇 `FileExistsError` 逐字节比较目标,相同则复用,不同则 exit 4 `REJECTED_STATE_INCONSISTENT` 并保留旧文件 → 删除临时文件 → fsync 父目录。`os.link` 因其它原因失败 → exit 5 `WORKSPACE_FS_UNSUPPORTED`(已有错误码),不得退回覆盖式写入。不得用"先检查不存在再 rename"。canonical 路径为 `<campaign_workspace>/<unit_hash>/ci_evidence.json`。analyzer 失败或不产证据 → exit 5 `INTAKE_ANALYZER_FAILED`,不建 unit,已有 canonical 文件不变。
3. 一次 `create_unit` 写入全部列(`ci_system` 固定 `quickbuild`;unit key 用现有 `build_campaign_unit_key`;`max_rounds` / `max_build_invocations` 取自配置)。同参数重跑为 no-op;同 key 不同参数 exit 4 `REJECTED_STATE_INCONSISTENT`。
4. **源码主副本准备**(冻结稿原属发现阶段,见其第 4.1 节 repair-step 参数说明中 `--src-clean` 一项):canonical 路径 `<campaign_workspace>/<unit_hash>/src`,远端为 `gerrit_ssh_base.rstrip('/') + '/' + project`。
   - canonical 已存在 → 只用现有 `_validate_source_identity` 校验,不覆盖、不修补;校验不过 exit 4 `REJECTED_IDENTITY_MISMATCH`。
   - canonical 不存在 → 在同一父目录下的暂存目录 `.src.staging-<随机后缀>` 中完成全部工作:只读克隆 → checkout 到 `base_commit` → 核验 HEAD 与归一化 origin → 写 marker `.campaign_clone` 并 fsync → 最后 `os.rename(暂存目录, canonical)` 发布。canonical 因此永远不会处于"已存在但没有 marker"的中间态,进程任何时刻被杀都只留下暂存目录。rename 在建档锁内执行,且执行前再确认 canonical 不存在。
   - marker 为 JSON 对象,键**恰好**是 `unit_key`、`project`、`base_commit` 三个,不得增删(现有 `_validate_source_identity` 做整体字典相等比较,多一个键即判 `REJECTED_IDENTITY_MISMATCH`);值分别为 campaign_unit_key、`--project`、`--base-commit`。
   - 克隆、checkout、核验或 rename 失败 → exit 5 `INTAKE_CLONE_FAILED`,删除本次暂存目录。本步开始时(已持建档锁)先删除该父目录下所有 `.src.staging-*` 遗留目录:它们只可能由本命令产生,且建档锁保证没有其它进程正在使用。
- 任一步之后崩溃:同参数重跑依次核验已有产物并继续,不重复覆盖。
- 本命令对 Gerrit 只有只读克隆;不访问 QuickBuild。CI 日志由人按现有流程下载到本地。本命令沿用现有配置校验,`gerrit_ssh_base` 允许绝对本地路径(只供测试);离线测试从本地裸仓库克隆。`ssh://` 的强制只在 `campaign-start-check` 中(5.5)。
- stdout JSON:`{campaign_unit_key, primary_arch, failed_arches, ci_evidence_ref, ci_evidence_sha256, src_clean, created: bool, error_code|null}`。

### 5.2 baseline-reproduce

- 按冻结稿第 4.1 节 baseline-reproduce 契约与第 3.3 节第 2 步实施(三态、主架构先行、synthetic 空基线、失败分支与退出码全部照原文)。`--src-clean` 使用 5.1 准备的主副本,本命令只校验、不创建。建副本用 `from tizen_build_verify.workspace import create_worktree`(子模块写法,理由见 4.3)。reproduce 判据按冻结稿第 4.2 节 `reproduce.check` 签名,放在 tizen-campaign-core。
- **取锁**:冻结稿未给 baseline-reproduce 规定文件锁。本文规定它非阻塞取得该 unit、该架构的标准锁 `<campaign_workspace>/<unit_hash>/<arch>/.repair_step.lock`(与 repair-step 同一把;不因基线副本使用独立 workspace_root 而另建锁),持有到副本清理与 REPRODUCE 记账结束;取不到 → exit 4 `CAMPAIGN_STATE_BUSY`。它因此与同架构的修复轮、与放弃命令互斥。
- 取锁后、建副本前,用新读取的状态库检查放弃屏障(5.4),存在则 exit 4 `REJECTED_UNIT_ABANDONED`。本命令没有对外动作,其基线副本按冻结稿在 `finally` 中清理、不受保护,所以这里的检查主要是避免白跑。
- 简化:不做 `campaign-rebaseline`。
- 测试用假 gbs(返回预置日志与退出码)与真实 gbs_analyzer;真实 gbs 只在第 3.5 批。

### 5.3 review-submit

- 按冻结稿第 4.1 节 review-submit 契约与第 4.5 节第 10、11 条实施:聚合重校验、最新 QB 记录绑定与结果文件 hash 重算、edit_spec 内容重绑定、suppress 现场重推、A2 质量门、TOCTOU 重校验(复用 tizen_sandbox_submit 的 `toctou_recheck`)、Change-Id 幂等 push。
- **取锁**:冻结稿的 review-submit 契约没有规定文件锁,复用的 `toctou_recheck` 是纯校验、不取锁。本文规定 review-submit 复用 tizen_sandbox_submit 的 `_locks`(`.sandbox_submit.lock` 加三个架构的 `.repair_step.lock`,同一顺序、非阻塞,取不到 → exit 4 `CAMPAIGN_STATE_BUSY`),锁路径按同一 campaign_workspace 与 unit_hash 派生;在第一道重校验之前取得,持有到 push 结束且 REVIEW 事件落库之后才释放,不得在屏障检查后提前释放。这是放弃屏障成立的前提:放弃只解除保护标记、不删目录,副本内容不变,TOCTOU 会照常通过;若不互斥,"检查屏障后、推送前被放弃"的窗口里仍会推出 refs/for。
- 取锁后、任何重校验之前,用新读取的状态库检查放弃屏障(5.4),存在则 exit 4 `REJECTED_UNIT_ABANDONED`,零 push,不进入 TOCTOU(因而不会落到 `WORKTREE_LOST`)。
- 简化一:不实施人工降级路径。不提供 `--print-manual-command`,不产生 `REVIEW_MANUAL`。最新 request 没有 RESULT 时 exit 4 `REJECTED_QB_REQUEST_PENDING`,`message` 固定为:"该 unit 最新的验证请求还没有结果。若 qb-result-fetch 曾报告结果无法识别(QB_RESULT_UNRECOGNIZED,例如各架构状态非空或快照漂移;可在 <state_root> 下该 request 的 trace 中确认),重读不会改变结果,请按其输出的指引处置,或用 campaign-release-worktrees --abandon 放弃该 unit;否则稍后重跑 qb-result-fetch。"其中 `<state_root>` 填实际路径。本命令不读 trace、不判断属于哪一种。
- 简化二:修法来源只有 `generated` 与 `suppress`,不出现 `t1_cherry_pick`;A2 门判据不变。
- REVIEW 事件 payload 按现有校验器写入 `review_url`(推送输出中 Gerrit 返回的 change URL;取不到记 null,trace 说明原因)。
- 测试:refs/for 推送目标用本地裸仓库模拟 Gerrit(与 sandbox-submit 现有测试同法),断言推送使用的 Change-Id 来自 hook 缓存而非新生成;离线时 `review_url` 为 null 属正常。六道重校验各自的拒绝用例见第 6 节。

### 5.4 生命周期最小版与放弃屏障(tizen-campaign-report)

**释放 API**:`campaign_lifecycle` 实现冻结稿第 4.2 节的 `release_terminal_worktrees` 与 `release_held_worktrees`,语义照原文(逐份解除保护并写 `WORKSPACE_RELEASE` 事件、两步崩溃后重跑幂等)。另新增第四个 API:

`release_abandoned_worktrees(state_db, campaign_unit_key, *, confirmed_by) -> list[str]`,只供 `--abandon` 调用:
- 副本清单复用 `release_held_worktrees` 的同一枚举实现与同样两个来源:① campaign link 关联的 verification record 的 `worktree_path`;② `ORPHAN_PASS` 事件记录的 `worktree_path`。逐个探测存在性,不信调用方传入路径。
- 对账:"待确认集合" = 上述登记副本 − 该 unit 既有 `abandoned_release` 事件中已列出的路径。对其中仍受保护的逐份解除保护;已无保护标记或目录已不存在的也算释放完成。待确认集合非空时写一条 `WORKSPACE_RELEASE{paths: [待确认集合], reason: "abandoned_release", confirmed_by}`;为空时不写。这样"解除保护之后、写事件之前崩溃"的情形,重跑时会把这些路径补记进事件,不会永久漏记。
- 状态白名单为非终态;`confirmed_by` 必须非空。冻结稿"另两个 API 不得增加 `confirmed_by` 入参"的约束只针对那两个,不影响本 API。

不实现 `release_superseded_partial_round`,不改 `campaign-repair-step`;被新一轮取代的部分 PASS 副本,在 unit 结束或放弃时一并释放。代价:单个 unit 修复期间最多同时保留 `max_build_invocations` 份副本。

`WORKSPACE_RELEASE` 事件 payload 一律为 `{paths: [...], reason: <str>, confirmed_by?: <str>}`;`paths` 与 `reason` 是现有校验器的必填键,`paths` 可为空列表。

**campaign-finish-unit** `--state-db --config --campaign-unit-key`:
- 最新状态 ∈ {`REVIEW_PUSHED`, `REVIEW_INELIGIBLE`, `DENIED`, `STALLED`, `REGRESSED`, `ROUNDS_EXHAUSTED`}:调 `release_terminal_worktrees`(冻结稿白名单恰为这六个),exit 0。
- ∈ {`NOT_REPRODUCED`, `REJECTED_ARCH_NOT_ALLOWED`}:这两类 unit 从未进入修复轮,没有受保护副本(基线副本按冻结稿用后即清),不调用释放 API,输出 `released: []`,exit 0。
- ∈ {`HELD_FOR_INVESTIGATION`, `WORKTREE_LOST`, `SANDBOX_QB_FAILED`}:不释放,exit 0,输出 `retained: true` 与原因。
- 其它(非终态):exit 4 `REJECTED_UNIT_NOT_TERMINAL`,`message` 提示"如决定放弃该 unit,用 campaign-release-worktrees --abandon"。

**campaign-release-worktrees** `--state-db --config --campaign-unit-key --confirmed-by <who> [--abandon]`:
- 不带 `--abandon`:按冻结稿原契约,只适用 `HELD_FOR_INVESTIGATION` / `SANDBOX_QB_FAILED` / `WORKTREE_LOST`(去掉 `REVIEW_MANUAL`);其余 exit 4 `ReleaseNotAllowed`。
- 带 `--abandon`:只适用非终态 unit;终态 unit 带 `--abandon` → exit 4 `ReleaseNotAllowed`(应走 finish-unit)。流程固定为:
  1. 按 `--config` 定位该 unit 的 `.sandbox_submit.lock` 与三个架构的 `.repair_step.lock`,按 sandbox-submit 现有的顺序非阻塞取得全部锁;任一取不到 → exit 4 `CAMPAIGN_STATE_BUSY`,不写任何事件。
  2. 若尚无放弃屏障,写**屏障事件**:`WORKSPACE_RELEASE{paths: [], reason: "abandoned", confirmed_by: <who>}`。
  3. 调 `release_abandoned_worktrees`(枚举来源含 `ORPHAN_PASS` 孤儿副本,对账规则见上)。
  4. 释放锁,exit 0。
  - 第 2 步后崩溃:重跑跳过第 2 步、继续第 3 步;第 3 步内崩溃:重跑按对账补齐。屏障已存在时重跑 `--abandon` 始终允许(用于补释放之后新出现的副本)。
  - 屏障之后状态不变、不新增状态名;已在 QuickBuild 上启动的构建不会被取消。
- 若该 unit 是第 7 节第 3.5 / 4 批的在途包且处于 `LOCAL_3ARCH_PASS`,放弃前须确认不再做第 4 批。

**放弃屏障**:状态库中该 unit 存在 `reason` **精确等于**字符串 `"abandoned"` 的 `WORKSPACE_RELEASE` 事件即为已放弃。判定一律用精确相等,不得用前缀或包含匹配:释放事件的 reason 是 `"abandoned_release"`,前缀匹配会让"屏障写失败而释放事件写成功"的情形永远补不上屏障。

以下命令在取得各自的锁之后、产生任何外部动作或写业务事件之前,用取锁后新读取的状态库检查屏障,存在则 exit 4 `REJECTED_UNIT_ABANDONED`(新错误码),对本 unit 零推送、零代理命令、零新 request。各命令的锁都与放弃命令的四把锁冲突,所以检查与外部动作之间不会插入放弃:
- `sandbox-submit`(既有命令,新增检查;锁为现有 `_locks`);
- `qb-trigger`(既有命令,新增检查;锁为现有 `.sandbox_submit.lock`;检查在本 unit 的任何浏览器命令之前);
- `review-submit`(新命令;锁见 5.3);
- `baseline-reproduce`(新命令;锁见 5.2)。

不加检查的命令及理由:`campaign-repair-step`(本版不改;它只在本地编译,不对外;放弃后若仍被运行,新产生的副本由重跑 `--abandon` 释放,其结果到 sandbox-submit 即被挡住);`qb-result-fetch`(对 QuickBuild 只读、不触发构建,但会写状态库:RESULT 事件、状态迁移、结果文件与证据,读取时模式还会自动认领并写 BUILD_BOUND。不挡它的理由是它没有对外写动作,它写出的结果到 review-submit 处被屏障挡住;代价是被放弃 unit 的状态仍可能继续前进,报告按下文优先显示"已放弃");`campaign-add-unit`(同参数重跑是 no-op)。

**campaign-report** `--state-db [--output <md>]`:每个 unit 一行,列为包名、项目、最新状态、终止原因、修复轮数、已用编译次数、QuickBuild 父/子构建号、review URL(取自 REVIEW 事件 payload,缺失为空)、副本状态(在用 / 已释放 / 保留待查 / 已放弃)。存在放弃屏障时副本状态优先显示"已放弃",终止原因列写"abandoned(状态列为放弃时及之后的状态)";同时输出同内容 JSON。只读状态库。

### 5.5 启动检查与编排 skill

`campaign-start-check --config <campaign_config> --state-root <dir> --project <gerrit project> [--project …]`(tizen-campaign-intake):
1. 配置必填键齐全(键清单取冻结稿 campaign_config 模板中骨架保留部分,不含知识库与 QuickBuild 键)。
2. `clang_conf_path` 存在且路径不含 `/reference/`。
3. `gbs --version` 成功。
4. `gerrit_ssh_base` 以 `ssh://` 开头(冻结稿第 4.4 节第 18 条:本地路径只供测试);每个 `--project` 先按现有项目名规则校验,再对完整地址 `gerrit_ssh_base.rstrip('/') + '/' + project` 用统一 Git 环境执行一次只读 `git ls-remote`,成功即可达。不对地址前缀本身执行,不使用 `gerrit version`。`ssh://` 的要求只在本命令中强制;其它命令沿用现有配置校验、允许本地路径(只供测试),所以离线端到端不含本命令,本命令的首次真实执行在第 3.5 批。
5. state 目录可写。
剧本传入本批全部包的 project。输出脱敏 JSON(每项 pass/fail 与原因,可达性失败与配置失败分开写明);任一项失败 exit 4 `PREFLIGHT_FAILED`。QuickBuild 不在这里检查,只在第 3 节第 6 步需要时由工具弹出登录窗口。测试中 `gbs` 与 `git` 子进程用假件替代。

编排 skill tizen-clang-campaign:
- SKILL.md 即剧本,按第 3 节顺序写成确定的命令序列,可执行命令只用第 3 节列出的命令名。冻结稿第 7 节 P11 中仍适用的条款照录:修复轮只经 `campaign-repair-step`、禁止直接调用 build-verify 或 gbs、禁止自行拼装 workspace/iter 路径、抑制约束(含 CMake FetchContent 第三方源码判不出即转人工)、启动输入缺项即停。与被砍项相关的条款(知识库、D2E、T1)删除。
- `campaign-kickoff-template.md`:用户填写的启动模板,列出全部必填项(包清单及各包 project、CI 日志路径与构建号、配置文件、state 目录、署名身份)。
- 剧本中 AI 只负责三件事:生成 edit_spec、在非终态时决定何时重读结果、建议是否放弃一个包(放弃须人确认后执行 `--abandon`)。

## 6. 测试策略

1. 每个新命令:主路径一条、各退出码与新错误码各至少一条拒绝用例。另外必须包含:
   - **review-submit 六道重校验各自一条拒绝用例**,逐项构造被篡改的输入:① 聚合重校验(三份记录之一不属于最终 round);② 最新 QB 记录绑定(结果文件改一个字节,hash 重算不符);③ edit_spec 内容重绑定(发布后 edit_spec 文件被改);④ suppress 现场重推(抑制内容与存量判定不一致);⑤ A2 质量门(不过门的修法);⑥ TOCTOU(聚合通过后、推送前改 worktree)。每条断言:本地裸仓库收到 0 个 ref 更新、无 REVIEW 事件、退出码与冻结稿一致。夹具复用 sandbox-submit 现有的裸仓库与 worktree 篡改工具,另新增"被改字节的结果文件"与"不过 A2 门的 edit_spec"两个。
   - **放弃屏障**:
     - 在 `SANDBOX_PUSHED` 放弃后,`qb-trigger` → `REJECTED_UNIT_ABANDONED`、零新 request;单 unit 运行时断言零浏览器启动;`--units-file` 批量(三个 unit,中间一个已放弃,前一个已启动浏览器)时断言对该 unit 零 `open_form` / `fill` / `submit` / `read`。
     - 零受保护副本时放弃,屏障照样生效(`baseline-reproduce` 被拒)。
     - 并发:review-submit 持锁期间跑 `--abandon` → `CAMPAIGN_STATE_BUSY` 且不写屏障;`--abandon` 持锁期间跑 review-submit → `CAMPAIGN_STATE_BUSY` 且零推送;在 review-submit"屏障检查通过之后、TOCTOU 之前"注入一次 `--abandon`,断言注入拿不到锁、推送照常只由 review-submit 决定;baseline-reproduce 在"屏障检查后、建副本前"同样注入,断言 `--abandon` busy;放弃与 sandbox-submit / repair-step 并发 → `CAMPAIGN_STATE_BUSY` 且不写屏障。
     - 崩溃:屏障写入后崩溃、最后一个保护标记解除后写释放事件前崩溃 → 重跑补齐释放事件,再次重跑零新增事件。
     - 枚举:unit 有一个 link 副本和一个 `ORPHAN_PASS` 孤儿副本 → `--abandon` 后 `paths` 含两个路径、两处保护都已解除;不属于该 unit 的路径不会被释放。
     - 精确匹配:库中只有 `abandoned_release`、没有 `abandoned` 事件 → `qb-trigger` 不被挡,重跑 `--abandon` 补写屏障。
     - 放弃 → `qb-result-fetch` 取到 PASS → `review-submit` 被拒、零推送、状态不进 `WORKTREE_LOST`,报告显示"已放弃"。
   - 停在 `QB_TRIGGERED` 且读不到结果的 unit:`campaign-finish-unit` → `REJECTED_UNIT_NOT_TERMINAL`;终态 unit 带 `--abandon`、非终态 unit 不带 `--abandon` → `ReleaseNotAllowed`。
   - `review-submit` 在无 RESULT 时的固定 `message`(含实际 state_root 路径)。
   - **campaign-add-unit**:
     - 证据:同 key 换日志 → 拒绝且旧证据原始字节不变;analyzer 失败 → 旧证据不变、无 unit;两个进程同时到达发布点(绕过建档锁直接测发布函数)→ 内容相同时都成功,内容不同时只有一个成功,已发布字节不变。
     - 建档锁:两个建档进程并发 → 后者 `CAMPAIGN_STATE_BUSY`,不删对方暂存目录。
     - 源码:空目录首次克隆(本地裸仓库)→ marker 恰为三个键;分别在克隆中、checkout 后、marker 写入后 rename 前终止 → canonical 不存在,重跑成功;遗留 `.src.staging-*` 目录 → 重跑时被清理;已有 canonical 的 HEAD / origin / marker 任一不符 → `REJECTED_IDENTITY_MISMATCH` 且不删除、不覆盖;marker 多一个键 → `campaign-repair-step` 与 `sandbox-submit` 各自 `REJECTED_IDENTITY_MISMATCH`。
     - 其它崩溃点:证据发布后建 unit 前、unit 建好后克隆前 → 重跑完成。
     - 同一份本地路径配置下,`campaign-add-unit` 的克隆成功而 `campaign-start-check` 失败(固定两条命令对同一配置键的不同要求)。
   - **campaign-start-check**:五项各一条失败用例;`gerrit_ssh_base` 为本地路径 → 失败;`ssh://` 正确但 `ls-remote` 失败(假 git 返回非零)→ 失败且输出标明是可达性问题;断言传给 git 的是完整项目地址;缺 `--project` 或项目名非法 → 子进程启动前拒绝。
2. 一条离线端到端测试,从 `campaign-add-unit` 跑到 `campaign-report`(启动检查由第 1 条单测覆盖,真实执行在第 3.5 批):假 gbs、假 QuickBuild 页面(复用 P5Q 现有页面夹具)、本地裸仓库代替 Gerrit;断言状态序列依次经过第 3 节各状态,最终 `REVIEW_PUSHED`,副本已释放,报告行内容正确。另加一条失败路径(修复轮 `STALLED` → 收尾释放)和一条放弃路径(`QB_TRIGGERED` 放弃 → 报告"已放弃")。
3. 剧本静态检查:解析 `tizen-clang-campaign/SKILL.md` 中的可执行命令块,断言每条命令只属于第 3 节列出的集合,且命令块中不出现 `build-verify`、`gbs build` 或自行拼装的 `iter_` 路径。说明文字中出现这些名称(如"禁止直接调用 build-verify")不算违规。另以三个反例(命令块中分别写入上述三种)证明检查会失败。
4. 全量 pytest 与 import-linter 每批都跑;第 4.4 节第 4 条的违规反例只在第 1 批做一次;P5Q 四组安全测试在第 1 批、第 2 批(qb-trigger 增加屏障检查)与第 4 批跑。
5. 不再为单个命令做真机验证。

## 7. 实施批次与流程

每批:Codex 实施并推送 → 设计方审代码与证据 → FatTank 点头进入下一批。批内不做外部评审。进度记录在 `dev_memory/stage21_campaign_skeleton/progress.md`。

| 批 | 内容 | 真机 |
|---|---|---|
| 1 | 第 4 节拆分(只搬家):先搬一个模块验证,再批量 | 无 |
| 2 | 5.1 建档(含建档锁、证据无覆盖发布、源码暂存发布)、5.2 基线复现(含取锁)、5.4 生命周期最小版与放弃屏障(含第四个释放 API、sandbox-submit 与 qb-trigger 的屏障检查) | 无 |
| 3 | 5.3 审核提交(含取锁)、5.5 启动检查与编排 skill、第 6 节离线端到端 | 无 |
| 3.5 | 真实 gbs 单包干跑:选一个已有人工修法(shelve CL)的包,由人按该修法写 edit_spec;运行 `campaign-start-check`(含对真实 Gerrit 的只读 `ls-remote`)→ `campaign-add-unit`(含只读克隆)→ `baseline-reproduce` 三架构 → `campaign-repair-step` 直到 `LOCAL_3ARCH_PASS` 或终态。**不执行 sandbox-submit,不运行任何 QuickBuild 命令,不推送 Gerrit**。产出:真实 CI 日志的 analyzer 证据、三架构基线与修复耗时、真实 gbs 失败形态;任一项与冻结稿不符即停,先修再进第 4 批。证据归档 `dev_memory/stage21_campaign_skeleton/evidence/batch3.5/`,含三份副本路径与保护标记 | 真 gbs,不推送、不登录 |
| 4 | 在第 3.5 批同一个包上续跑:开始前核对三份副本仍在且受保护;第一次真实 sandbox 推送、一次 QuickBuild 登录与提交、读结果、review-submit;refs/for 是否实推由 FatTank 现场决定 | 有 |

- 第 3.5 批结束后,不得对该 unit 执行 `campaign-finish-unit` 或 `campaign-release-worktrees`(含 `--abandon`):`LOCAL_3ARCH_PASS` 的三份受保护副本是第 4 批 sandbox-submit 的必需输入,释放后只能重跑第 3.5 批。该约束写入第 3.5 批执行裁定与 progress。
- 第 3.5 批止于终态(未达 `LOCAL_3ARCH_PASS`)时:该包不进第 4 批;按证据判断是工具缺陷还是修法/环境问题——工具缺陷先修再重跑第 3.5 批,修法或环境问题则另选一个包重跑第 3.5 批。第 4 批不得在未达 `LOCAL_3ARCH_PASS` 的包上开始。
- 第 3.5 批与第 4 批开始前各出一份短的执行裁定(选包及选包标准、build.conf 与仓库基线须与对应 QuickBuild 配置一致、前置检查、停止条件、预计耗时),不在本文件中预先固定。

## 8. 被砍项与已接受残余

| 项 | 恢复条件 |
|---|---|
| 知识库与 diff 转修改规格 | 第 4 批跑通且有一批成功修复记录后,再评估是否值得;现有人工 shelve CL 可作为种子 |
| 自动发现 | 手工建档成为瓶颈时 |
| 冻结稿全量启动自检(含 QuickBuild 探活等) | 五项检查不够用时 |
| 对抗测试组 | 第 4 批后视需要补;"不得直调 build-verify"由 4.3 合约与第 6 节第 3 条覆盖,"push 路径不得被绕过"由第 6 节第 1 条六道重校验用例覆盖 |
| rebaseline、部分 PASS 提前释放、人工降级路径 | 出现实际需要时 |
| 放弃后的状态标记与 repair-step 屏障 | 本版放弃以屏障事件挡住对外动作、状态不变;repair-step 与 qb-result-fetch 不检查屏障(前者只在本地编译,后者只读 QuickBuild 但会写状态库),被放弃 unit 的状态可能继续前进。若放弃的包多到影响报告阅读或浪费编译资源,再评估新增状态名或给 repair-step 加检查 |
| P5Q 遗留 | 以 P5Q 收口文档为准;冻结时已知:读取失败细分诊断、SIGINT 时 /dev/shm 残留清理、会话被挤处理、两个暂不可读候选与一处身份计数、变量名集合未采集。第 4 批若复现相同问题再处理 |
| COSMOS 构建 | 以后新增独立 skill,写入同一组验证构建表与事件;其它 skill 只读状态库、不直接调用 QuickBuild 代码,届时上层不需改动 |

新发现的遗留由第 4 批后的收口文档 `review/campaign-skeleton-closeout.md` 汇总。

## 9. 交付物清单

1. 第 4.2 节全部目录、SKILL.md、转发、三行必改 import、pyproject 与 `.importlinter` 更新(含 4.3 的 a–e)。
2. 第 5 节新增命令与第四个释放 API、新命令的文件锁、sandbox-submit 与 qb-trigger 的屏障检查,及第 6 节全部用例(含 review-submit 六道重校验、放弃屏障的并发/崩溃/枚举用例、建档的崩溃恢复用例)。
3. `design.md` 末尾追加的修订节(第 0.2 节所述五件事),含四个新错误码。
4. 进度文件 `dev_memory/stage21_campaign_skeleton/progress.md`,每批收尾同 commit 更新;`dev_memory/INDEX.md` 同步。
5. 第 4 批后的收口文档 `review/campaign-skeleton-closeout.md`。

## 附录 A:v1.0 → v1.1 修改记录

第一轮评审:Claude Code 给出完整意见(结论"修改后可冻结");ChatGPT 的回复文件只有评审题目本身,未纳入。设计方已回仓核对 Claude Code 引用的代码与冻结稿行号。

| # | 严重度 | 问题 | 处置 | 采用谁的方案及理由 | 位置 |
|---|---|---|---|---|---|
| 1 | 重要 | 去掉人工降级与 `REVIEW_MANUAL` 后,读不到结果的 unit 既不能收尾也不能释放副本 | 新增 `--abandon` 出口 | 设计方方案。按"是否已有停止-报告"分支所需的信息不在状态库中;改为人工放弃,同时解决第 3 条 | 2、3、5.4、6 |
| 2 | 重要 | 砍对抗测试组后"不得直调 build-verify"只剩散文 | 新增 forbidden 合约与剧本静态检查 | 采用 Claude Code 思路,改禁 `build_verify` 子模块而非整包,避免误伤 `edit_spec_guard` 与 `workspace` | 4.3、6 |
| 3 | 次要 | 人为放弃一个包没有出口 | 并入第 1 条 | 设计方方案 | 3、5.4、8 |
| 4 | 重要 | import-linter 合约是六条;新包不登记则静默通过 | 写明改动与一次性红例 | 采用 Claude Code 方案,层次改为 core 在既有 skill 之上、sandbox-submit 单列 | 4.3、4.4 |
| 5 | 重要 | `gerrit version` 在离线测试无法执行 | 改为 `git ls-remote`,做成可测小命令 | 采用 ls-remote;保留冻结稿"本地路径只供测试",离线端到端不含启动检查 | 2、3、5.5、6 |
| 6 | 重要 | 第 4 批四个"第一次"过于集中 | 新增第 3.5 批只跑真实 gbs | 采用 Claude Code 方案,补"选已有人工修法的包" | 0.3、7 |
| 7 | 次要 | 无 RESULT 时报"pending"会误导 | 固定 `message` 覆盖两种情况 | 设计方方案 | 5.3 |
| 8 | 次要 | 文件清单遗漏 | 补充说明 | 采用 Claude Code 方案 | 4.2 |
| 9 | 次要 | `.mjs` 的 package-data 键需改名 | 写明改名与 wheel 断言 | 采用 Claude Code 方案 | 4.4 |
| 10 | 次要 | 新错误码登记位置 | 在 `design.md` 末尾追加修订节 | 设计方方案,沿用第 4.4、4.5 节先例 | 0.2、9 |
| 11 | 次要 | 用例数口径可被凑过去 | 改为 nodeid 子集比较 | 采用 Claude Code 方案 | 4.4 |
| 12 | 次要 | 对 P5Q 收口文档的引用悬空 | 收口文档提交作为冻结前置 | 采用 Claude Code 方案 | 0.2、8 |
| 13 | 次要 | 报告的 review URL 来源未写 | 写明取自 REVIEW 事件 payload | 部分采用:现有校验器已有该键 | 5.3、5.4 |
| 14 | 次要 | 先搬一个模块验证别名机制 | 写入第 1 批 | 采用 Claude Code 方案 | 4.1、7 |

## 附录 B:v1.1 → v1.2 修改记录

第二轮评审:ChatGPT 与 Claude Code 结论均为"修改后可冻结"。ChatGPT 提出 1 条阻断、5 条重要、1 条次要;Claude Code 提出 2 条重要、5 条次要,并逐条确认附录 A 中未照搬其改法的六条理由成立(其中三条承认原提法有误)。设计方已回仓核对:`release_worktree_protection` 只删除保护标记、不删目录;qb-trigger 入口不检查副本保护;`.campaign_clone` 按冻结稿由发现阶段写入、现有代码只校验不创建;qb-trigger 以 `gerrit_ssh_base` 加项目名拼接远端;`test_qb_browser.py` 与 Node 测试按物理路径读取源码;sandbox-submit 已有"一把 sandbox 锁加三把 repair 锁、固定顺序、非阻塞"的取锁方式。

| # | 严重度 | 来源 | 问题 | 处置 | 采用谁的方案及理由 | 位置 |
|---|---|---|---|---|---|---|
| 1 | 阻断 | ChatGPT | 放弃只解除保护标记、目录仍在,qb-trigger 不检查保护,已放弃的 unit 仍可触发真实构建 | 新增持久化放弃屏障:先写屏障事件再释放;sandbox-submit、qb-trigger、review-submit、baseline-reproduce 持锁后检查,存在即 `REJECTED_UNIT_ABANDONED` | 采用 ChatGPT 的屏障思路,收窄检查范围:只给有对外动作的命令和新命令加检查,不改 repair-step(只在本地编译,其结果在 sandbox-submit 被挡)、不挡 qb-result-fetch(只读);新增专用错误码,不复用 pending;屏障事件与释放事件分开写,屏障事件 `paths` 为空,语义清楚;取锁复用 sandbox-submit 现有方式 | 0.2、5.2–5.4、6、8 |
| 2 | 重要 | Claude Code | 放弃后取到结果,review-submit 落到 `WORKTREE_LOST`,报告误导 | 并入第 1 条:review-submit 先查屏障;报告优先显示"已放弃" | 采用 Claude Code 的报告显示方式;拒绝码用第 1 条的新错误码 | 5.3、5.4 |
| 3 | 重要 | ChatGPT | 砍掉发现阶段后,源码主副本与 clone marker 没有生产者 | 由 campaign-add-unit 第 4 步只读克隆并写 marker | 设计方方案:ChatGPT 建议放在首次主架构基线复现,但冻结稿中 baseline-reproduce 以 `--src-clean` 为已校验的输入,放在建档里不改它的契约,也避免一个跑三次的命令带"首次准备"分支 | 3、5.1、5.2、6 |
| 4 | 重要 | ChatGPT | 新 Python 包是八个,文字写成七个,公共库可能漏登 | 统一为八个新包、七个执行包 | 采用 ChatGPT 方案 | 4.2–4.4 |
| 5 | 重要 | ChatGPT | 别名转发不能转发测试中的物理路径(AST 读源码、Node 导入) | 允许机械更新测试的物理路径,并植入反例证明静态检查扫的是新文件 | 采用 ChatGPT 方案 | 4.4 |
| 6 | 重要 | ChatGPT | `ls-remote` 对地址前缀执行必然失败 | 增加 `--project`,对完整项目地址执行 | 采用 ChatGPT 方案;允许多个 `--project`,剧本传本批全部包 | 5.5、6 |
| 7 | 重要 | ChatGPT | 建档重跑可能先覆盖旧证据再被数据库拒绝 | 证据先写临时文件,canonical 只首次发布、已存在则逐字节比较 | 采用 ChatGPT 方案 | 5.1、6 |
| 8 | 重要 | Claude Code | 砍对抗测试组后,"push 路径不得被绕过"只剩"每个退出码一条用例" | review-submit 六道重校验各一条拒绝用例 | 采用 Claude Code 方案 | 2、6、8 |
| 9 | 重要 | Claude Code | build-verify 合约散文易被写成"禁包根",会立即变红并诱导豁免 core | 改写为对合约 e 的解释,点明短写法也违约,指定两个红例 | 采用 Claude Code 方案(有实测) | 4.3、4.4、5.2 |
| 10 | 次要 | ChatGPT | 剧本静态检查会拒绝必须写入的禁止说明 | 只检查可执行命令块 | 采用 ChatGPT 方案 | 6 |
| 11 | 次要 | Claude Code | 三行 `from ci_triage import sandbox_submit` 不改也能跑,只有合约能发现 | 在 4.2 点名必改 | 采用 Claude Code 方案 | 4.2、9 |
| 12 | 次要 | Claude Code | `WORKSPACE_RELEASE` 的 `paths` 是必填键 | 写明 payload 格式 | 采用 Claude Code 方案 | 5.4 |
| 13 | 次要 | Claude Code | 第 3.5 批的副本是第 4 批必需输入,可能被误释放 | 写明禁止释放并在第 4 批前核对 | 采用 Claude Code 方案 | 5.4、7 |
| 14 | 次要 | Claude Code | 第 3.5 批止于终态时第 4 批前提消失 | 写明应对 | 采用 Claude Code 方案 | 7 |
| 15 | 次要 | Claude Code | 启动检查缺"可达性失败"用例 | 补用例 | 采用 Claude Code 方案 | 6 |
| 16 | 次要 | Claude Code | 无 RESULT 提示要求人回忆上条输出 | message 中写明 trace 所在位置 | 采用 Claude Code 方案 | 5.3 |

## 附录 C:v1.2 → v1.3 修改记录

第三轮定向核对:ChatGPT 与 Claude Code 结论均为"修改后可冻结",各提 1 条阻断(同一问题)。ChatGPT 另提 2 条重要、1 条次要;Claude Code 另提 2 条重要、6 条次要或建议。设计方已回仓核对:sandbox_submit 的 `_locks` 为一把 sandbox 锁加三把 repair 锁、非阻塞;qb-result-fetch 不取锁;repair-step 的 canonical edit_spec 以 `os.link` 首次发布并在 `FileExistsError` 时比较;冻结稿 `release_held_worktrees` 的两个枚举来源;冻结稿基线副本在 `finally` 中清理;冻结稿 `release_terminal_worktrees` 的状态白名单。核对时仓库 HEAD 为 accd7f4,相对 2c9ed30 只新增 P5Q 收口文档,冻结前置条件已满足。

| # | 严重度 | 来源 | 问题 | 处置 | 采用谁的方案及理由 | 位置 |
|---|---|---|---|---|---|---|
| 1 | 阻断 | 两家 | review-submit 在冻结稿中没有锁,"持锁后检查屏障"无从成立;放弃只删保护标记,副本内容不变,并发时仍会推出 refs/for | review-submit 复用 sandbox-submit 的 `_locks`,持有到 push 与 REVIEW 事件落库之后 | 两家方案一致,采用;补三条并发用例,含 Claude Code 提出的"检查后注入放弃"回归锚点 | 0.2、5.3、5.4、6 |
| 2 | 重要 | ChatGPT;Claude Code(次要) | baseline-reproduce 没有锁 | 取该架构的标准 `.repair_step.lock` | 采用 ChatGPT 方案:成本低,并与同架构修复轮互斥。Claude Code 建议只写"尽力检查",理由中"白跑后留下新副本"不准确——冻结稿基线副本在 `finally` 中清理、不受保护;但其"本命令无对外动作"的判断成立,已写入 5.2 | 5.2、5.4、6 |
| 3 | 重要 | Claude Code | `--abandon` 枚举副本未写来源,`ORPHAN_PASS` 孤儿副本会永远无人释放 | 新增 `release_abandoned_worktrees`,枚举复用 `release_held_worktrees` 的两个来源 | 采用 Claude Code 方案 | 0.2、5.4、6 |
| 4 | 次要 | ChatGPT | 解除保护后、写事件前崩溃,重跑时无受保护副本,释放记录永久缺失 | 第四个 API 按"登记副本 − 已记录路径"对账,补记已解除或已不存在的路径 | 采用 ChatGPT 方案,并入第 3 条的同一 API | 5.4、6 |
| 5 | 重要 | 两家 | 源码直接克隆到最终路径,"目录已在、marker 未写"时被杀,重跑永远被自己的校验拒绝 | 暂存目录内完成克隆、校验与 marker,再 rename 发布;新增建档锁 | 两家方案一致;采用 ChatGPT 的建档锁(防两个建档进程互删暂存目录)与 Claude Code 的三个终止点用例 | 5.1、6 |
| 6 | 重要 | ChatGPT | "rename,不覆盖"不是真正的无覆盖发布,并发时旧证据仍会被覆盖 | 改用 `os.link` 首次发布,`FileExistsError` 时逐字节比较 | 采用 ChatGPT 方案,沿用 repair-step 现有写法与已有错误码 `WORKSPACE_FS_UNSUPPORTED`;建档锁另行串行化,但不替代无覆盖发布 | 5.1、6 |
| 7 | 次要 | Claude Code | 屏障判定若用前缀匹配,`abandoned_release` 会被误当屏障 | 写明精确相等 | 采用 Claude Code 方案 | 5.4、6 |
| 8 | 次要 | Claude Code | 称 qb-result-fetch"只读"低估了它会写状态库 | 改写理由 | 采用 Claude Code 方案 | 5.4、8 |
| 9 | 次要 | Claude Code | marker 是整体字典相等比较,必须写明恰好三个键 | 写明,并加多一个键的反例 | 采用 Claude Code 方案 | 5.1、6 |
| 10 | 次要 | Claude Code | `ssh://` 强制与"离线用本地路径"易被读成矛盾 | 写明 `ssh://` 只在启动检查中强制,并加反向断言用例 | 采用 Claude Code 方案 | 5.1、5.5、6 |
| 11 | 建议 | Claude Code | 批量 qb-trigger 下"零浏览器启动"不成立 | 单 unit 断言零启动,批量断言对该 unit 零代理命令 | 采用 Claude Code 方案 | 6 |
| 12 | 次要 | 设计方自查 | v1.2 的 finish-unit 把 `NOT_REPRODUCED`、`REJECTED_ARCH_NOT_ALLOWED` 交给自动释放,但冻结稿 `release_terminal_worktrees` 白名单不含这两个,照写会被拒 | 这两类不调用释放 API,直接输出空释放清单 | 设计方方案:两类 unit 从未进入修复轮,没有受保护副本 | 5.4 |

未采纳:Claude Code 1-1 副作用分析中称"review-submit 会因 qb-result-fetch 正在运行而拿不到锁"——核对代码,qb-result-fetch 不取锁,该副作用不存在;不影响第 1 条结论。
