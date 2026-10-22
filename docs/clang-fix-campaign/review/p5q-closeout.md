# P5Q QuickBuild 提交与结果读取收口

日期:2026-10-22。状态:**CLOSED**。
依据设计方裁定P5Q-C8-04,C8按已取得的自动绑定与终态PASS证据通过,三项验收残余接受且不再补测;
P1的EF-5由C6/C8证据覆盖并一并关闭。裁定全文见[stage20 progress第54节](../dev_memory/stage20_p5q_qb_trigger/progress.md#54-实施裁定-p5q-c8-04p5q-收口)。
阶段关闭不表示已接受残余已修复,也不把历史停止报告改写为全部测试通过。
自本裁定起停止一切QuickBuild真机操作,不再请求FatTank登录;下一次真机执行只在最终端到端阶段。

## 1. 权威与交付

### 1.1 冻结设计与实施记录

| 设计 | SHA256 | 状态 |
|---|---|---|
| [P5Q v1.8-FROZEN](../p5q-qb-trigger-design-v1.8-FROZEN.md) | `d0242ca8b708e9c1e3e714387bae963f8f6f16fc765179e6ed60d8be56493364` | 当前权威,结合后续已登记裁定 |
| [P5Q v1.5-FROZEN](../p5q-qb-trigger-design-v1.5-FROZEN.md) | `f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c` | 原字节保留备查 |
| [P5Q v1.2-FROZEN](../p5q-qb-trigger-design-v1.2-FROZEN.md) | `0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950` | 原字节保留备查 |

[design.md](../design.md)已由C7同步至v1.5.24-FROZEN。本次不修改它、冻结稿、生产代码或状态库。
v1.5后的裁定已并入v1.8附录I;后续P5Q-C7-03明确代理等待预算残余,
C8-01完成失败分类小修,C8-02/03处置补绑定与验收范围,C8-04给出本次收口结论。

| 阶段/锚点 | 交付结论 | 记录 |
|---|---|---|
| C0–C2c | 配置/状态原语、浏览器安全边界、可信读取与脱敏交付 | [progress第2节及第9–28节](../dev_memory/stage20_p5q_qb_trigger/progress.md) |
| C3 `3ef542a` / C4 `39e4bde` | 两个生产CLI、提交与结果契约及离线用例交付 | 同上第31/33节 |
| C5a/C5b | 本机完整链路与工具、真机原始正文比对及零提交填表演练通过 | 同上第34–36节 |
| C6及关闭修复 `9cc481f` | 一次实际提交、人工绑定PASS、样本补证与关闭缺陷修复 | 同上第43–46节 |
| C7 `0b27c49` | 两种自动查找模式、驱动上限、终止记录与预算裁定落实 | 同上第48节;[交付审计](../dev_memory/stage20_p5q_qb_trigger/evidence/C7/continuation/delivery-audit.json) |
| C8小修 `e393a1f` | 基线读取失败分类与真实结构假页面回归 | 同上第49节;[离线审计](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/audit.json) |
| C8真机证据 `9a688a0` / `a11736d` / `2c9ed30` | 提交后查找停止、读取时自动补绑定PASS、FatTank确认 | 同上第51/53节;原停止报告保留 |
| 本文与P1/P5Q状态同步 | P5Q-C8-04文档收口,本次提交SHA由Git外部锚定 | 同上第54节 |

### 1.2 模块与CLI清单

下列模块均在`tizen-ci-triage/scripts/ci_triage/`,不表示新增独立skill或打包边界。

| 模块/入口 | 用途 |
|---|---|
| [qb_config.py](../../../tizen-ci-triage/scripts/ci_triage/qb_config.py) | 校验工程/表单配置并生成按branch冻结的规范profile。 |
| [qb_redact.py](../../../tizen-ci-triage/scripts/ci_triage/qb_redact.py) | 对凭据与登记身份位置脱敏,供应答、诊断和证据写后自检。 |
| [campaign_state.py](../../../tizen-ci-triage/scripts/ci_triage/campaign_state.py)的P5Q增量 | 新增campaign_qb_profiles、按连接写入原语与qb_profile查询,保持既有API行为。 |
| [qb_browser_agent.mjs](../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs) | 在独立浏览器内执行人工登录检测、受限填表/提交和隔离环境原始正文读取,拦截越界请求。 |
| [qb_browser.py](../../../tizen-ci-triage/scripts/ci_triage/qb_browser.py) | 驱动代理的逐行JSON协议,校验应答并执行read/submit硬上限及退出诊断。 |
| [qb_trigger.py](../../../tizen-ci-triage/scripts/ci_triage/qb_trigger.py) | 锁内前置与幂等、远端ref核对、参数冻结、意图事务和一次提交,必要时自动查找。 |
| [qb_discovery.py](../../../tizen-ci-triage/scripts/ci_triage/qb_discovery.py) | 解析Recent Builds并按两种模式、候选分类与时限定位唯一匹配请求标记。 |
| [qb_binding.py](../../../tizen-ci-triage/scripts/ci_triage/qb_binding.py) | 复用自动/人工绑定的父构建核对与写事务。 |
| [qb_result_html.py](../../../tizen-ci-triage/scripts/ci_triage/qb_result_html.py) | 只从脱敏HTML解析配置、变量、父子关系、状态、快照与失败步骤。 |
| [qb_evidence.py](../../../tizen-ci-triage/scripts/ci_triage/qb_evidence.py) | 管理取证文件序号与归档边界,不落盘他人候选页面。 |
| [qb_result_fetch.py](../../../tizen-ci-triage/scripts/ci_triage/qb_result_fetch.py) | 只处理最新request,核对父子结果并原子发布结果文件、事务追加RESULT与迁移状态。 |
| [cli.py](../../../tizen-ci-triage/scripts/ci_triage/cli.py): `python -m ci_triage qb-trigger` | 生产提交入口,接收单unit或批量输入并输出固定JSON/退出码。 |
| 同一cli.py: `python -m ci_triage qb-result-fetch` | 生产读取入口,支持已绑定读取、自动/人工补绑定及单request人工接受快照漂移。 |
| [p5q_compare_raw_active.mjs](../spikes/p5q_compare_raw_active.mjs) / [p5q_fill_rehearsal.mjs](../spikes/p5q_fill_rehearsal.mjs) | 非生产取证工具,分别验证原始正文前提与不提交的十二字段演练,不作为收口后真机授权。 |

## 2. 真机验证记录

### 2.1 C6:父1201886与子1201889

目标为`platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`,
请求号为`9fe02dc3927c4b7fa55a3dffce699d03`。

| 环节 | 事实与结论 | 证据 |
|---|---|---|
| C6a live-05提交 | 一次生产提交后落点不明、QB_SUBMIT_UNCERTAIN;没有重新Run或retrigger | [trigger/stdout.json](../dev_memory/stage20_p5q_qb_trigger/evidence/C6a/live-05/trigger/stdout.json)、[原停止报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C6a/live-05/stop-report.md) |
| 人工绑定与首次读取 | FatTank提供父1201886和完整请求标记;一次fetch绑定,子1201889首次读取已PASS,RESULT=3 | [fetch/report.md](../dev_memory/stage20_p5q_qb_trigger/evidence/C6a/live-05/fetch/report.md)、[stdout](../dev_memory/stage20_p5q_qb_trigger/evidence/C6a/live-05/fetch/stdout.json) |
| 结果核对 | 子Status为Successful,父Child Build为SUCCESSFUL,EACH_GBS_BUILD_STATUS存在且为空;目标在全量列表唯一,标记逐字相等 | [fetch/analysis.json](../dev_memory/stage20_p5q_qb_trigger/evidence/C6a/live-05/fetch/analysis.json)及同目录原始脱敏四页 |
| 快照 | 冻结值、父SNAPSHOT_NUM、子快照URL末段同为tizen-base-toolchain_20261013.024319;same、未接受漂移;manifest确认目标revision未变 | [manifest核对](../dev_memory/stage20_p5q_qb_trigger/evidence/C6a/live-05/manifest-20261013/result.json)、fetch/report.md |
| C6b终态重读 | exit0,仍指向RESULT=3,DB字节不变,新增四页、无新增结果文件;关闭尾段0.213秒,代理退出码未采集 | [C6b README](../dev_memory/stage20_p5q_qb_trigger/evidence/C6b/README.md)、[重读审计](../dev_memory/stage20_p5q_qb_trigger/evidence/C6b/reread-01/post-audit.json) |
| 成功样本与BUILD_NOTES | 父/子overview及variables、配置1917共五页50项原始正文/活动文档比对一致,两侧身份计数0;非空BUILD_NOTES无额外空白/转义/截断,两个挂账CLOSED | [比对run.json](../dev_memory/stage20_p5q_qb_trigger/evidence/C6b/raw-active-01/run.json)、[progress第45.5节](../dev_memory/stage20_p5q_qb_trigger/progress.md#455-挂账关闭表) |

C6a首次读取的关闭尾段35.042秒属于当时已知缺陷,由9cc481f离线修复后,
C6b首次真机核对恢复秒级。没有由CLI退出0推断代理退出码。
五页50项是规定字段的比较,不适用项两侧均为空;不代表整页HTML逐字节相等。
配置1917两张表的菜单锚点在活动文档中多出class,正文/构建链接/状态class一致,
原差异见[configuration-tables.diff](../dev_memory/stage20_p5q_qb_trigger/evidence/C6b/configuration-tables.diff),不扩大发现的含义。

### 2.2 C8:live-01与live-02

目标仍为上述libtirpc行,请求号为`202711dfe6b34472b6b8dc23f3a74a6e`。

| 环节 | 事实与结论 | 证据 |
|---|---|---|
| live-01验证性提交 | 仅一次trigger,落点/wicket/page、unknown;随后配置页read在579ms返回QB_BROWSER_UNAVAILABLE/UNKNOWN,代理未观察到退出;保留提交意图并停止,不重提 | [live-01停止报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-01/stop-report.md) |
| live-02前置停止 | 其它浏览器进程未满足当轮前置;后按C8-03缩小P5Q进程范围,FatTank确认本轮不使用其它Chrome登录 | [前置停止报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/stop-report.md)、progress第53.3节 |
| live-02自动补绑定 | 一次生产fetch,无人工指定build_id,自动绑定父1204698/子1204699并直接写终态PASS,exit0、RESULT=3 | [stdout](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/fetch/stdout.json)、[执行记录](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/fetch/execution.json) |
| 查找事实 | 1轮10候选,候选全集与未绑定Recent Builds行相等;1匹配、7标记不同、2暂不可读;12次相关读取合计6278ms,非查找墙钟时长 | [trace](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/fetch/trace-new.jsonl)、[归档校验](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/fetch/archive-validation.json) |
| 终态与归档 | 父/子Successful,Child Build为SUCCESSFUL,逐架构状态空;标记/目标符合;快照同C6且same,accepted=null、冻结profile不要求Accept;只归档配置及匹配父子5页,他人页0、诊断0 | 同一archive-validation.json及[读取停止报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/read-stop-report.md) |
| 人工核对 | FatTank于2026-10-22回复原话“构建号与完整请求标记一致” | [human-build-confirmation.json](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/human-build-confirmation.json) |
| 状态与关闭 | QB_REQUESTED→QB_TRIGGERED→SANDBOX_QB_PASS,新增BUILD_BOUND和RESULT;整条CLI162.300秒,关闭尾段1.391秒,代理退出码NOT_COLLECTED | 同一execution.json、[状态SQL导出](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/fetch/state-after.sql) |
| 收口处置 | b的两个暂不可读候选、e3a身份计数1、e3b变量名集合按C8-04接受,不再补测;读取时模式完成真机自动绑定,不是提交后模式成功的证明 | progress第54节;第4节R11–R17 |

原定构造unit 2的零提交验证已被C8-02的真实未绑定请求恢复替代,没有构造unit 2。
原read-stop-report与archive-validation中的当时PENDING/停止状态不改写,
由后续人工确认和C8-04裁定闭合验收。未点击Accept/Ready to Accept,未做真实Gerrit推送。

## 3. 测试与门禁

下表是已有验收记录,不是本次文档收口重跑。最近一次完整全仓回归共**2892例:2891通过、0失败、1跳过**。
此后离线调查定向用例另列,不与全量或Node内部用例重复相加。

| 验收 | 结果 | 证据 |
|---|---|---|
| C8前小修全仓pytest | 2891 passed / 0 failed / 1 skipped,896.30秒,exit0 | [完整输出](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/full/output.log)、[JUnit](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/full/junit.xml)、[计数审计](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/audit.json) |
| mypy / ruff / lint-imports / design checker | 119文件无类型问题;ruff通过;6 kept/0 broken;0 problem,均exit0 | [mypy](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/mypy/output.log)、[ruff](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/ruff-final/output.log)、[imports](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/imports/output.log)、[design](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/design/output.log) |
| C7 Node与静态负例 | 362 passed / 0 failed / 0 skipped,含159静态负例;驱动预算6个负例另有定向记录 | [Node日志](../dev_memory/stage20_p5q_qb_trigger/evidence/C7/continuation/node-01/output.log)、[定向日志](../dev_memory/stage20_p5q_qb_trigger/evidence/C7/continuation/focused-01/output.log)、delivery-audit.json |
| 四组拦截安全 | C7从头重跑4/4:Worker/WebSocket、307/308、凭据隔离、逐跳拦截;C8未改代理 | [safety-01日志](../dev_memory/stage20_p5q_qb_trigger/evidence/C7/continuation/safety-01/output.log) |
| 本机完整CLI集成 | C8全量中六种提交落点/延迟/失败模式通过,协议与服务器请求分别记录 | [full/cli-artifacts](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/offline/full/cli-artifacts/) |
| C8调查补充 | navigation-02为4 passed,03为2 passed,均0失败/0跳过;navigation-01的错误假设失败原文保留,非生产回归 | [调查报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/investigation/README.md)、[最终调查审计](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/investigation/audit-final.json) |

唯一全量skip为大小写不敏感文件系统专用用例,不是浏览器/Node缺失跳过。
代理保护前缀SHA256仍为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`;
本次不改代理,不重跑会启动浏览器的任何测试。文档检查结果见progress第54.3节。

## 4. 已接受残余与待办

共**20条**。下列“待办”不授权本阶段实施或追加真机访问;C8-04已关闭本阶段。
失败签名、候选根因与实际根因明确区分,不因收口选择一个尚未证实的解释。

| 编号 | 残余/待办及处置 | 证据或裁定 |
|---|---|---|
| R01 | read可信环境的本机CDP等框架等待不设代理侧预算;统一由驱动read 60秒、submit 150秒硬上限兜底。 | P5Q-C7-03,progress第48节 |
| R02 | open_form/fill无驱动侧应答上限,挂起可能长期占锁,此时提交尚未放行。 | v1.8第3.2节、附录K第2条 |
| R03 | 变量值自由文本中的第三方名字不脱敏也不计数;他人候选页不归档,不得据计数0宣称所有身份已识别。 | v1.8第9.4节3/e3b、附录K第7条 |
| R04 | 未登记账号列若内容不等于登录显示名,不会被现有身份计数发现;结构断言不能替代身份承载位置登记。 | progress第48.5节;v1.8第9.1节与附录K第7条 |
| R05 | 批量提交/恢复不保证数分钟完成;保持输入顺序,后续批量操作先恢复未绑定request再继续提交。 | v1.8第5.5节、附录K第4条 |
| R06 | 自动查找只覆盖Recent Builds有限窗口,样本10行、规范上限50行;旧请求被挤出后不保证自动恢复。 | progress第48.5节;v1.8第5.5节、附录J第6/13条 |
| R07 | 快照漂移分支仅有离线覆盖,无真机样本;P12首次遇到时按既有人工接受规则登记,不得为补样本提前运行。 | v1.8第9.4节第3步“快照漂移分支” |
| R08 | C6/C8专用库前置验证记录为构造,远端ref核对使用本机bare镜像;不覆盖真实Gerrit检查或修复流水线前半段。 | P5Q-C6-01;progress第37/38/49节 |
| R09 | 首次真实sandbox推送是否自发触发QB仍待P12观察,本阶段没有真实Gerrit推送。 | progress第5节;v1.8第10节C8 |
| R10 | Unified配置未取证、未启用,不能以Base样本代替或猜配置ID。 | progress第5节;v1.8第0.1/2.1节 |
| R11 | C8 live-01提交后read快速失败的根因未唯一确定;读取失败细分诊断候选修复延期。 | [调查报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/investigation/README.md)、P5Q-C8-04第3条 |
| R12 | 真机成功自动绑定来自读取时模式;提交后模式未完成真机成功闭环,C8按本次裁定接受,不另行补测。 | live-01/live-02报告;P5Q-C8-04第1/2条 |
| R13 | SIGINT退出可抢在外层/dev/shm profile清理前留下目录;历史残留来源为强关联而非PID级证明,清理修复延期。 | [SIGINT证据](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/investigation/navigation-02/cleanup-SIGINT.json)、调查报告、P5Q-C8-04第3条 |
| R14 | 会话被挤掉的处理候选延期;本机302到signin可复现相似签名,不代表已证实live-01就是会话失效。 | 调查报告“configuration response 302 to signin”;P5Q-C8-04第3条 |
| R15 | 验收b:候选1204735/1204798暂不可读,实际原因未细分且页面未归档;不能以观测到唯一匹配证明它们不含另一匹配,按裁定接受、不补测。 | [读取停止报告](../dev_memory/stage20_p5q_qb_trigger/evidence/C8/live-02/read-stop-report.md)、P5Q-C8-04第1条 |
| R16 | 验收e3a:1203397变量页登记位置外登录显示名计数1,位置无法由保留证据定位;按裁定接受、不补测。 | 同一读取停止报告、P5Q-C8-04第1条 |
| R17 | 验收e3b:现有trace不含候选变量名集合,未采集也未人工浏览;后续元数据取证为待办,本阶段不补测。 | P5Q-C8-03第3条、P5Q-C8-04第1条 |
| R18 | 破坏性监听器正则按子串匹配,desktop/nonstop等组件名会被误拒并作废表单;安全方向误拒已接受,遇到按R1处理。 | P5Q-C2C-03,progress第28节;v1.8附录I |
| R19 | qb-trigger默认格式的一次性bare只做ls-remote,sha256远端可能拒绝或不匹配,归REJECTED_SANDBOX_NOT_BOUND;本机用例曾SHA_MATCHED,不保证所有环境。 | P5Q-C4-02,progress第33节及其focused.log |
| R20 | C6a live-01/live-04登录超时原因仍未确定;已补login_facts供后续定位,不能将final_path_shape为/单独解释成已到首页。 | progress第44–46节、P5Q-C6B-01第3条 |

R04、R06、R12、R18–R20为从既有进度补列的边界/覆盖限制;不增加新的验收门或设计规则。

## 5. 后续阶段移交

只复述已有冻结设计,不增加接口或新的降级路径。

| 接收阶段 | 已有约定与必须保留的边界 | 来源 |
|---|---|---|
| P5R审核提交 | 按unit的最新request取最新RESULT,核对结果文件原始字节SHA256与数据库锚点,不得使用旧request的PASS或仅相信外部JSON。 | [design.md](../design.md) review-submit;v1.8第5.4节 |
| P5R参数与schema | 按unit.branch读取campaign_qb_profiles冻结值,不以当前配置覆盖;接收固定schema及null语义,child_params_echo仅BUILD_REFERENCE/SNAPSHOT_NUM_URL,snapshot_used为实际快照名。 | v1.8第2.2/5.4节、附录A第6/11/12条及v1.5增补 |
| P5R状态与拒绝 | QB_REQUESTED/QB_TRIGGERED/SANDBOX_QB_PENDING不得降级或打印push命令;已有RESULT校验失败不得降级;accepted为null不代表已Accept,要求Accept时只有数据库1通过。 | v1.8附录A第10/11条;design.md第4.5节 |
| P5R判读 | FAIL只表示包含目标行的全量构建失败,不能直接归因到本unit修复;由人结合child_failed_step/child_error_message判读,报告标出接受过快照漂移的unit及实际快照。 | v1.8第0.5/5.3/5.4节、附录A第14条 |
| P12/最终端到端 | 按原计划覆盖真实Gerrit远端与首次sandbox推送观察,先恢复未绑定请求再继续批量提交;首次漂移按既有单request规则留痕,不重提不明提交。 | v1.8第5.5/9.4/10节;P5Q-C6-01 |
| 后续设计/维护 | Unified启用须先取证;表单/页面形态变化与调查候选修复须按R1/设计裁定,不因本次关闭自行放宽拦截或扩大隐私输出。 | v1.8第8节;P5Q-C8-04第3条 |

P1 EF-5的关闭依据与旧spike边界见[stage15第18节](../dev_memory/stage15_p1_ef_spike/progress.md#18-p1-ef-5关闭p5q-c8-042026-10-22)。
本轮不执行上述移交项;后续真机时机受P5Q-C8-04第2条约束,仅最终端到端阶段。

## 6. 最终收口

2026-10-22,按设计方P5Q-C8-04收口裁定:P5Q **CLOSED**,P1 **CLOSED**。
FatTank已核对C8父构建1204698与完整请求标记一致;本次裁定接受剩余三项验收残余。
INDEX、stage20当前状态与挂账表、stage15关闭记录已同步。
本次仅文档提交,没有新增评审签名、真机运行、代码修复或状态库写入;本提交由Git记录锚定。
