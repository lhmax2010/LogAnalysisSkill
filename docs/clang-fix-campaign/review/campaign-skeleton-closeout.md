# Clang 修复活动骨架收尾

日期:2026-11-05。状态:**骨架阶段及恢复四批离线完成,真实端到端延后**。
依据:[stage21 progress 第25节 SKEL-CLOSE-01](../dev_memory/stage21_campaign_skeleton/progress.md)。
第3.5、4批是“延后”,不是“通过”;预筛0个合格候选(`96b5776`),实际QuickBuild
build.conf原件本地不可得,不能证明本地验证条件与QuickBuild一致,真实端到端留待COSMOS build接入后另行裁定执行。
冻结输入:[骨架设计v1.3](../campaign-skeleton-design-v1.3-FROZEN.md),正文不改;
SHA256 `1d66247c78ed4ab36a37f81149fbec6a648b10830ec15b38a2a454a93ee2fec9`。

## 1. 交付清单

下表入口写作`python -m <包名> <子命令>`;core是库,无CLI。原八包目录与归属按冻结稿第4节,
恢复第二批另增KB执行包。实际入口见各包的`scripts/<包名>/__main__.py`
(`5b9ecea`、`1a4ed25`、`a58494b`及progress第32节恢复验收)。

| 包 | 职责 | 子命令 |
|---|---|---|
| tizen_campaign_core | 状态、身份、聚合、派生提交、策略、复现、生命周期、D2E/KB与发现清单API | 无,由执行包调用 |
| tizen_campaign_intake | 建档、五项启动检查与发现清单消费 | campaign-add-unit、campaign-start-check、campaign-discover |
| tizen_baseline_reproduce | 三架构基线复现 | baseline-reproduce |
| tizen_campaign_repair | 修复轮、策略预检、修法转换与先例建议 | campaign-repair-step、suppress-policy check、diff-to-edit-spec、propose-fix |
| tizen_sandbox_submit | 聚合校验、放弃屏障与sandbox提交 | sandbox-submit |
| tizen_qb_verify | QuickBuild触发、查找绑定、结果归档与发现采集 | qb-trigger、qb-result-fetch、qb-discover |
| tizen_review_submit | 六道重校验、锁与放弃屏障后的审核提交 | review-submit |
| tizen_campaign_report | 终态释放、保留副本释放/放弃与只读报告 | campaign-finish-unit、campaign-release-worktrees、campaign-report |
| tizen_campaign_kb | 知识库导入、查询与绑定修法同步 | kb、campaign-kb-sync |

编排与开局输入已交付:[tizen-clang-campaign/SKILL.md](../../../tizen-clang-campaign/SKILL.md)、
[campaign-kickoff-template.md](../../../tizen-clang-campaign/references/campaign-kickoff-template.md)。
旧`ci_triage.X`用`sys.modules[__name__] = 新模块`保持模块对象同一,不是星号导入;
旧CLI与执行包共享解析/执行函数。搬迁18模块、别名与wheel验收见`5b9ecea`,CLI去重见`1a4ed25`。

[.importlinter](../../../.importlinter)共7合约:层次为ci_triage → 六个执行包 → sandbox → core →
既有skills → shared;另有既有skills独立、shared内部层次、shared禁止上行、L1/L0各自独立、
非repair活动包禁止直接或间接导入build_verify子模块。唯一既有例外为build_verify →
gbs_patch_suggest.formatter;不把同层关系解释为新增独立性合约。
静态import检查不覆盖子进程依赖,边界见[subprocess-boundaries.md](../dev_memory/subprocess-boundaries.md)。

## 2. 阶段裁剪

- **保留:** P6三架构基线、P5R审核提交、P11剧本与模板;P12真实端到端仍是后续验证目标,本阶段延后而非删除。依据:冻结稿第2、7节及SKEL-CLOSE-01。
- **精简:** P8.5为五项启动检查,P10为最小释放/报告加放弃屏障;P6无rebaseline,P5R无人工降级。依据:冻结稿第2、5.2至5.5节。
- **砍掉:** P9自动发现改手工建档,P7 diff-to-edit-spec、P8知识库、P11独立对抗测试组取消;相应安全保护由依赖/剧本静态检查和review六道拒绝用例承担。依据:冻结稿第2、5.1、6节;恢复条件见第8节。

**恢复裁定更新(2026-11-05):** 上述是SKEL-CLOSE-01时的裁剪记录,不是当前功能清单。
按RESTORE-01/02/04/06恢复D2E、KB与T1/T2建议;按RESTORE-18/20/22/24恢复发现,
以`python -m tizen_qb_verify qb-discover`采集清单,再以
`python -m tizen_campaign_intake campaign-discover --manifest ... --state-root ...`
调用既有analyzer与建档。消费端不访问QB,只允许既有SandboxGit和当前Python解释器的
`gbs_analyzer analyze`子进程。依赖合约与intake.add_unit不改。
编排skill和开局模板已纳入两步发现、propose-fix、三种修法来源与两次kb sync;
实现与本轮门禁以[progress第45节](../dev_memory/stage21_campaign_skeleton/progress.md)为准。
真实单包编译/推送仍延后,不因离线恢复而改为“通过”。

## 3. 离线验收

下表前四行为SKEL-CLOSE-01的既有验收记录,最后一行为恢复第三/四批最终树离线门禁。

| 批次/验收commit | 全仓原始结果(通过/失败/跳过) | 结论与证据 |
|---|---|---|
| 第1批 `5b9ecea` | 2921 / 0 / 1 | 拆分、nodeid保留、别名、静态红例、wheel入口与.mjs打包通过;[batch1](../dev_memory/stage21_campaign_skeleton/evidence/batch1/) |
| 第2批 `1a4ed25` | 3026 / 1 / 1 | late-build原始失败保留,单独3次重跑全过,按SKEL-B1-05/B3-01接受;[coverage](../dev_memory/stage21_campaign_skeleton/evidence/batch2/implementation/coverage.md)、[timing-decision](../dev_memory/stage21_campaign_skeleton/evidence/batch2/implementation/timing-decision.json)。该失败原始签名为FETCH_CONTINUE_FAILED(见timing-decision.json第3行),后经诊断确认为读取失败缺陷而非计时问题,已由读取失败修复(5b41ee9)解决并按SKEL-R-08验收。 |
| 第3批 `a58494b` | 3087 / 0 / 1 | 60个新增用例,旧3028个全保留;[coverage](../dev_memory/stage21_campaign_skeleton/evidence/batch3/implementation/coverage.md) |
| 读取失败修复 `5b41ee9`、`fb549ea`、`fd4c6f6` | 3099 / 0 / 1 | 按SKEL-R-08验收;[final.json](../dev_memory/stage21_campaign_skeleton/evidence/read-failure/fix/implementation/r08/final.json) |
| RESTORE-24恢复第三/四批 | 3501 / 0 / 1 | 旧3454 nodeid全保留、新增48;[r24门禁](../dev_memory/stage21_campaign_skeleton/evidence/restore/batch3/r24/README.md) |

骨架原各批mypy、ruff、import-linter、design检查均验收通过;当时import-linter为7通过/0失败,
mypy检查161文件,design为0 problem。读取失败修复的P5Q四组安全测试4/4;
nodeid最终3100个,唯一既有skip为大小写不敏感文件系统专用用例。
来源:[stage21各批登记](../dev_memory/stage21_campaign_skeleton/progress.md)、上述final.json。

RESTORE-24封版检查:mypy172文件、ruff通过、import-linter仍7/7、design 0 problem,
Node静态及负例183通过、P5Q安全4/4。无计时敏感重跑或新增自然失败。
新增发现→清单消费→先例复用→审核离线链路终态REVIEW_PUSHED且副本释放,
KB从NEW升级CI_VERIFIED;真实Python CLI与真实代理采集另在本地假HTTPS验证。
两者的证据及边界见[progress第45、46节](../dev_memory/stage21_campaign_skeleton/progress.md)。

离线端到端三条均通过,使用假gbs、假SSH加本地裸库、P5Q页面夹具与假代理,不是真实编译/推送:

- 成功:DISCOVERED → CI_EVIDENCE_READY → BASELINE_RUNNING(三架构各一条) → BASELINE_REPRODUCED → REPAIR_ROUND_RUNNING → LOCAL_3ARCH_PASS → SANDBOX_PUSHING → SANDBOX_PUSHED → QB_REQUESTED → QB_TRIGGERED → SANDBOX_QB_PASS → REVIEW_PUSHING → REVIEW_PUSHED;副本释放、报告正确。
- STALLED:同前缀至REPAIR_ROUND_RUNNING → STALLED;finish-unit释放,报告保留STALLED。
- 放弃:同成功前缀至QB_TRIGGERED后写WORKSPACE_RELEASE屏障(非状态迁移);晚到PASS仍可入库,review被REJECTED_UNIT_ABANDONED拒绝、零推送,报告仍显示已放弃。

三条原始状态与用例位置见[batch3 coverage / Offline Chains](../dev_memory/stage21_campaign_skeleton/evidence/batch3/implementation/coverage.md)。
修复采样:C8共20次,19通过/1历史观测失败;late-build共20次全过;两组FETCH_CONTINUE_FAILED均0,
DENY_TARGET_GONE共3次且未导致停止。逐次结果、负载及原始失败见[R08采样表](../dev_memory/stage21_campaign_skeleton/evidence/read-failure/fix/implementation/r08/sampling-results.md)。

## 4. 未经真实环境验证

下列项均不以离线通过替代真实验收,依据SKEL-CLOSE-01与冻结稿第7节:

- 自动发现真机只读:**未验证**。RESTORE-25新运行目录及只读启动预检通过,
  但CLI未提供所要求的代理trace/elapsed_ms和日志响应元数据,在弹窗前停止;
  未消耗一次执行机会,未运行dry-run消费或真实建档。
  [RESTORE-26停止报告](../dev_memory/stage21_campaign_skeleton/evidence/restore/live-dryrun-01/stop-report-SKEL-RESTORE-26.md)。
  2026-11-06 RESTORE-27已接受本次元数据NOT_COLLECTED并规定等价证据;
  资源scope检查通过,等待用户确认开始,本项仍不标真机通过。

- 真实gbs失败形态与三架构基线/修复耗时:第3.5批未执行,无真实单包全链路测量。
- 真实CI日志上的analyzer有效诊断:预筛3次均exit0但needs_llm,不能证明与人工Clang修法对应;[candidates.md](../dev_memory/stage21_campaign_skeleton/evidence/batch3.5/selection/candidates.md)。
- campaign-start-check对真实Gerrit的ls-remote:本阶段只有假SSH用例;`a58494b`。
- campaign-add-unit的真实只读克隆:本阶段只有本地裸库经假SSH用例;`1a4ed25`。
- 真实sandbox推送:第4批未执行,尚未观察推送是否自行触发构建;[P5Q收口残余](p5q-closeout.md)。
- 新浏览器代理对真实QuickBuild的登录、提交与读结果:SKEL-R-02/R-04修改后只有本机验收;历史P5Q C6/C8成功证据不能替代当前版本真机核对;[P5Q收口](p5q-closeout.md)、`5b41ee9`、`fd4c6f6`。
- review-submit真实审核推送:第4批未执行,仅验证了临时裸库的refs/for;`a58494b`。

## 5. 遗留与观测

- 恢复任务的首轮真实`qb-discover`尚未运行。报告iframe与Details四列表以
  [live-04](../dev_memory/stage21_campaign_skeleton/evidence/restore/discovery-capture/live-04/)和RESTORE-18为依据;
  日志响应类型、编码、大小、跳转、Download尚无真机样本,由read_text逐包运行时fail-closed,
  不把本地夹具测试写成真机通过。首次真实发现需另行裁定,本轮不登录。
- RESTORE-14将`test_node_c2c_trusted_reads_and_fields[test_qb_browser_fields.mjs]`
  纳入计时敏感名单,失败保留并单独重跑3次全过才接受;不调阈值或加skip。

- C8调查用例按SKEL-R-08为观测项,不按一次新形态失败阻断;窄化失效、同一非豁免形态20次内至少3次、profile/浏览器残留仍须停止。观测表在[progress第23节](../dev_memory/stage21_campaign_skeleton/progress.md)与[R08采样表](../dev_memory/stage21_campaign_skeleton/evidence/read-failure/fix/implementation/r08/sampling-results.md),第4次原始失败保留。
- timing-sensitive清单为C5a `test_real_cli_browser_submit_bind_pending_pass`全部参数及C8调查用例;C5a失败须原样留证且单独3次全过,非关闭时延失败另记观测表;C8适用R08覆盖规则。依据:SKEL-B1-05、SKEL-B3-01、SKEL-R-08,见[progress](../dev_memory/stage21_campaign_skeleton/progress.md)。
- 仅测试harness的登录记录未处理空login应答,访问`response.ok`会自身抛错,未修复;[p5q_c8_investigation.mjs的login函数](../../../tests/node/p5q_c8_investigation.mjs),`fb549ea`。
- elfutils补证缺口:同源Clang编译首错日志、shelve完整diff、源码revision、QuickBuild实际build.conf。现有其它产品线修法不能替代Base同源证据;[预筛候选表](../dev_memory/stage21_campaign_skeleton/evidence/batch3.5/selection/candidates.md),`96b5776`。

## 6. 以后补跑的进入条件

选包标准引用[冻结稿第7节第3.5批](../campaign-skeleton-design-v1.3-FROZEN.md)原文:
“真实 gbs 单包干跑:选一个已有人工修法(shelve CL)的包,由人按该修法写 edit_spec”。
SKEL-B3.5-01进一步要求Base包真实Clang失败、可对应本地CI日志与人工修法,
优先三架构均编、改动小、耗时短、无大型依赖链;当前仍无合格候选(`96b5776`)。

补跑输入必须齐备:失败构建号、同源CI日志、shelve CL及完整diff、实际build.conf原件与base快照、
源码revision,并能证明本地验证条件与QuickBuild一致。先补齐再选包,不得凭相似发布配置代替实际输入。
依据:SKEL-CLOSE-01、[selection/candidates.md](../dev_memory/stage21_campaign_skeleton/evidence/batch3.5/selection/candidates.md)。

资源下限尚无实测依据;小包、有限并行度、三架构顺序执行的**初步预留为8GiB available及40GiB新增磁盘**,
不是已验收最低需求。2026-11-04环境为available16GiB、磁盘余133G、swap已用3.9/4GiB;
执行前须重测负载/换页、按所选包依赖与并行度校准预算,不据满swap自行清理。
来源:[environment.md](../dev_memory/stage21_campaign_skeleton/evidence/batch3.5/selection/environment.md)。

COSMOS接入后的真实端到端须先出执行裁定,明确输入、资源与授权边界;本收尾不授权编译、登录或推送。
第3.5批三架构最终轮PASS且已link时仍为REPAIR_ROUND_RUNNING,不得释放或放弃副本;
LOCAL_3ARCH_PASS由后续sandbox-submit写入,按SKEL-B3-05执行,不照旧状态文字误操作。
依据:[progress实施裁定SKEL-B3-05及SKEL-CLOSE-01](../dev_memory/stage21_campaign_skeleton/progress.md)。

COSMOS接入时需复核的现有位置(仅列包/模块,不指定替换方案):
`tizen_baseline_reproduce.baseline`、`tizen_campaign_core.reproduce`、
`tizen_campaign_core._campaign_workspace`、`tizen_campaign_repair.campaign_repair_step`、
`tizen_build_verify.build_verify`、`tizen_build_verify.workspace`、`gbs_analyzer`、
`tizen_campaign_intake`、`tizen_sandbox_submit`、`tizen_qb_verify`、`tizen_review_submit`。
位置依据:冻结稿第4.2节目录映射及[子进程边界](../dev_memory/subprocess-boundaries.md);不构成实现授权。
