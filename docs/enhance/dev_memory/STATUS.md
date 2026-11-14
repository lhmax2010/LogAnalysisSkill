# LogAnalyzer 增强版分支状态

## 1. 本线说明

本线为 LogAnalyzer 增强版第一版。

- 当前设计文档：v0.9.18（`docs/enhance/vd-cosmos-loganalyzer-hld-v0.9.18.md`；v0.9.17 两家评审处置，附录 Z）；第 3a-1.1 批 Checkpoint A/B1 按冻结 v0.9.18 与 B3a11-Q01 实施。第 3a-1 批按 v0.9.5 正文及 B3a1-Q01 裁定实现。第 2.1 批依据 v0.5.4；历次设计与评审原件保留。
- 分支：`vd-cosmos-loganalyzer`。
- 分支起点：`accd7f4`。

## 2. 工作约定

- 本分支只新增目录与 `docs/enhance/` 下的文件，不修改本线以外的仓库已有文件；第 3a-1 批只动 vd-cosmos-*、vd-fix-analyze、vd-fix-register 与 docs/enhance/；已有文档仅更新本文件。
- 已有 skill 只通过命令行调用。
- 公开仓库约束按 HLD 第 0.3 节执行：内部词表命中只告警，凭据模式命中拦截；本批代码和配置样例只用占位值。
- 新 Session 开场先读本文件核对。
- 每个任务收尾在同一个 commit 里更新本文件。
- 第 2.1 批按 v0.5.4 与 B2-Q01 交付；第 3a-1 批已正式下发，只做指定读取与源码快照范围。3a-2、3a-3 等设计方后续任务，不提前实现。核心只用标准库；离线验证不访问真实服务、不执行真实 P4。提交作者/提交者 Hao Lin，普通 push，禁止强推。

## 3. 计划

本线按设计方分批任务推进；第 2 批只实现读取侧，不包含浏览器、P4 写入或构建提交协议。

| 批 | 内容 | 验证范围 |
|---|---|---|
| 1（已完成离线） | core；纯函数报告解析；watch/fetch；固定页面序列 Submitter 桩 | Python 3.10 离线测试、合成夹具、CLI 回放 |
| 1.1（已完成离线） | 真实格式兼容、执行状态、其它扩展错误、构建机验收脚本 | 78 项测试、真实配置加载、脚本离线回放 |
| 2（已完成离线） | HTTP 读取、状态拆分、只读 tick/loop、A～E 验收脚本 | 100 项测试、三条 import 约束、本地 HTTP 模拟、真实配置加载 |
| 2.1（构建机真实验收已通过，外部评审进行中） | 三家评审处置与原六条：传输、定型、覆盖、详情、并发恢复、独立验收 | 125 项离线测试；设计方反馈 2026-10-26 构建机 A/B/C/E 全 PASS，F 指纹/身份/跳转检查已核实 |
| 3a-1（已完成离线） | 读取加固、本轮输入、P4 只读访问、源码快照、四类人工命令 | 153 项测试、三条 import 约束、两个新 SKILL 校验、真实配置本地加载 PASS |
| 3a-1.1 Checkpoint A（已完成离线） | 附录 O 修复、Python 3.10 兼容、只读构建机验收脚本 | 3.10.12 / 3.12.3 各 172 项 PASS、各三条 import 约束、配置加载；真实 A3 待构建机执行 |
| 3a-1.1 Checkpoint B1（已完成离线） | 无浏览器查号、请求/认领/重跑观察、doctor、构建机 B1 脚本 | 3.10.12 / 3.12.3 各 216 项 PASS、三条 import 约束；真实 B1 验收待构建机；B2 未实施 |
| 3a-1.1 Checkpoint B1.1（离线完成） | 共享变量表解析、首读不可变、重跑链、映射提案 | 追补后两解释器各 236 项 PASS；B3a11-Q02 已闭合；真实 A+B1 待构建机 |
| 3a-2（未开工） | 任务包、已有分析器适配、ClineSR 隔离、结果接收、诊断族与位置模型 | 接本段 snapshot manifest、任务输入摘要与通知接口，等设计方任务 |
| 3a-3（未开工） | 其余人工裁决、处置账本、准确性验收 | 等 3a-2 产物及设计方任务；真实验收另在构建机执行 |
| 后续 | request/previous_report 来源留第 4 批；按后续任务实施 | P4/浏览器写操作与提交协议仍未实现 |

## 4. 当前进度

- 2026-11-14 B1.1 追补：已核验 recon25/recon26 输出及 recon24/25/26 原脚本归档；变量页历史变化判断撤回，首读冻结仅为防御；三列表空 Display Name 夹具，已登记属性启用 cmp-v1、未登记仍未核验；同 Hub 重跑链由 recon26 补证，EMAIL_CC 提案改“变量页不列出”。第 38 行归档豁免按 B3a11-Q02 精确登记。Python 3.10.12 / 3.12.3 各 236 项 PASS、import/静态检查通过。详见 DELIVERY 的追补节与 evidence-b11-followup/；B2 未开工。

- 2026-11-14 B1.1：按设计方裁定修复变量页三列表头、首次值不可变存储、同 Hub 重跑链；18 项映射仅提出待确认，文本比较继续未核验；构建机同一会话依次验收 A/B1。Python 3.10.12 / 3.12.3 各 232 项 PASS，import/静态检查通过；B3a11-Q02 已按设计方裁定闭合：独立脚本归档与精确摘要/行/文本/规则登记仅供仓库 prepush，运行时检查不变。详见本批 DELIVERY 的 Checkpoint B1.1。

- 2026-11-14：第 3a-1.1 批 Checkpoint B1 已实现无浏览器查号、候选/人工认领、请求保护、resolve、持续观察与独立构建机验收脚本，Python 3.10.12 / 3.12.3 全套各 216 项 PASS、三条 import 约束及静态检查通过。基线 `bf5acb49ee6947faa66de474a5d0af365341a6fc`；交付表、测试与限制见 `docs/enhance/batch3a-1.1/DELIVERY.md` 的 Checkpoint B1 节。未打开浏览器、未登录、未提交构建、未执行真实 P4/Cosmos；B2 未开工。

- 2026-11-14：HLD v0.9.18 已冻结；第 3a-1.1 批 Checkpoint A（A1–A3）已完成离线实施。Python 3.10.12 / 3.12.3 完整运行各 172 项 PASS、import-linter==2.3 三条约束全部通过。附录 O 对照、API 审计、源码摘要、完整输出 SHA256 和构建机命令见 `docs/enhance/batch3a-1.1/DELIVERY.md`。B3a11-Q01 已闭合；实际构建机 A3 待执行，Checkpoint B 未开工。

- HLD v0.9.18 已归位（sha256 `2d489e8227b1bfdc113247b21b57de74a4cb0f1bec1359f721accb613a9734a4`）。设计要点：请求级锁只保护状态库读改写、网络读取在锁外、核对版本号；第二十三次侦察加原样取值形状与四项精确核对，确认前请求与变量页的文本比较记“未核验”；`H_pre` 未知时记“未核验”并要求 `claim-unverified`；无点击时刻用“补充观察起点”；观察中断改按心跳，新配置 `poll.watch_interval_s`（默认 300 秒）。下一步：两家最小范围核对（只报阻断与重要）→ 第二十三次只读侦察 → 第 3a-1.1 批开工。

- HLD v0.9.17 已归位（sha256 `181e5e47273c4e712ac023bf750f663b5b9d3161b896f34ae7b39c607f42a6ab`）。设计要点：观察运行锁 + 细粒度请求级锁（`poll.lock_wait_s`）；`attest` 硬检查，`claim-outside-candidates` 只越过“不在候选集合”；`resolve --build-id` / `--manual-submit` 也建观察任务；第二十三次侦察用固定词表打印明文，比较规则 `cmp-v1`；§11 真实提交 A 加“发送前拦截”。下一步：两家最小范围核对 → 第二十三次只读侦察 → 第 3a-1.1 批开工。

- HLD v0.9.16 已归位（sha256 `c18f5f2dc4a49fb86fe9dd0446216fe50b0677dbf78f2c97aff8bd71312f4db9`）。设计要点：认领确认增加 `H_pre`、确认词 `claim-unverified` 和请求级锁；新增只读 `watch --request`；覆盖结论限定为“当前保留记录中”；第二十三次侦察改为记值摘要与枚举明文；`doctor` 默认不联网，`--online` 自检。下一步：两家最小范围核对 → 第二十三次只读侦察 → 第 3a-1.1 批开工。

- HLD v0.9.13 已归位（sha256 f3f91f4039d1e950a720bf388b38a81f2da23cbd1c9bced4c7cb8a9c6f61d5be；附录 U 为 v0.9.11 三家最小范围核对处置：闸门逐跳拦截、录制期间全部拦下、提交前内容核验、提交后跳转只放行只读结果页；结果落库后成功页崩溃也记待核实；人工重跑挂起；待核对构建取得结论才移出；同内容旁证；快照受限判断改为全部诊断文件的第 N 行、无行号栏一律未核对）；第 3a-1.1 批 = 附录 O 的 3a-1 修复 + §8.8 + §8.9，待用户确认冻结后开工。
- HLD v0.9.12 已归位（sha256 d55f7cf408a19b356f34bd51fe058bad1affb1673c1e6c1dfc24fbaded4c039d；= v0.9.11（附录 T 为 v0.9.10 三家最小范围核对处置）+ §3 第 12 条'不使用 PHP'硬约束：不安装不使用 PHP、不运行 playwright install 系列命令、apt 安装只由用户执行且先模拟安装、doctor 报告 php 包数、仓库静态检查）；第 3a-1.1 批 = 附录 O 的 3a-1 修复 + §8.8 + §8.9，待用户确认冻结后开工。
- HLD v0.9.10 已归位（sha256 cdcade7ae033b70947c28ec0b3095a3db6a72d4da38c9634ed65442052ddf0e5；附录 S 为 v0.9.9 三家小范围核对处置：查号要求窗口覆盖本轮、登记后继续发现重跑；认证结束后装请求闸门、演练不留查看窗口；打开提交页前写表单暴露记录，崩溃后记手工提交待核实；快照歧义改为受限比较、制表符按 Clang 22 实际规则；读取器保密规则；条件比对改为显式变量名单）；第 3a-1.1 批 = 附录 O 的 3a-1 修复 + §8.8 + §8.9，待用户确认冻结后开工。
- HLD v0.9.9 已归位（sha256 4af375518a64a2afc9f85f7de1dafa04549976685caff171f3327cb137f102fe；附录 R 为 v0.9.8 三家小范围核对处置：快照核对改为先认三行、排除归属歧义、先比内容、列号只作旁证；查号不缓存不带编号对的结果、自动登记前做新鲜扫描；--base-from-hub 只读报告头、认定记为 base 来源认定、不进任何队列；结果不确定时一律立即关闭浏览器）；第 3a-1.1 批 = 附录 O 的 3a-1 修复 + §8.8 单次提交（只允许不带 shelve，含 --base-from-hub）+ §8.9，待用户确认冻结后开工。
- HLD v0.9.8 已归位（sha256 4d8262bb88a46132a99f78c3e44cbbc16d2e86f485bb1e7ed1d960063f98fbd0；附录 Q 为 v0.9.7 三家小范围核对处置）；第 3a-1.1 批 = 附录 O 的 3a-1 修复 + §8.8 单次提交（只允许不带 shelve，含 --base-from-hub）+ §8.9 提交端编号与构建号的对应，待用户确认冻结后开工；37376237 的构建管理端构建号改由 once --base-from-hub 在登录会话里自动取得，不再需要用户提供。
- HLD v0.9.7 已归位（sha256 ae78f655845ef5ee740b7c34a908b6bafa60bd41bca8cae57a2b5aa64ba9188e；附录 P 为 v0.9.6 三家定向核对处置）；第 3a-1.1 批 = 附录 O 的 3a-1 修复 + §8.8 单次提交（只允许不带 shelve）+ §8.9 提交端编号与构建号的对应，待用户决定是否再评审后开工；37376237 的构建管理端构建号（v0.9.8 起改为工具自动取得）。
- HLD v0.9.6 已归位（sha256 d316bbe3a7ab038928ee584814ce6d728101afaea6621aad5c1c548cb5b80e29）；第 3a-1.1 批（附录 O 的 3a-1 修复 + §8.8 单次提交命令）待评审后开工；37376237 的构建管理端构建号待用户提供。
- 本线工作目录：/home/toolchain/development/LogAnalysisSkill-vdcosmos（git worktree，分离 HEAD，推送用 git push origin HEAD:vd-cosmos-loganalyzer）；/home/toolchain/development/LogAnalysisSkill 有其它 Session 的未提交改动，本线不在那里操作。

2026-11-03：第 3a-1 批离线实现完成。A：可信/人工/时长定型窗口、身份三档、三类停滞、生产日志完整性与版本保存、完成状态重验、争用分类、真实验收地址/F 结论；B：五变量白名单、不可变 base/shelve 清单与逐项核对；C：隔离的 P4 -G 只读访问、结构化分类与持久化重试；D：路径/来源/合并/精确源码行核对与快照报告；E：confirm-terminal、confirm-input、bind-base-list、inbox done。B3a1-Q01 已按设计方答复闭合并测试。

本段实现、各项 HLD 与测试名、附录 H/J～N 的分段映射和 3a-2/3a-3 接口详见 `docs/enhance/batch3a-1/DELIVERY.md`。完整测试输出 `docs/enhance/batch3a-1/evidence/test-output.txt`，SHA256 `0a2ca96e198a85e2779c55739893c1e4017f6c97f7f2b8c013b94f8d430ffdbe`：153 项通过，三条 import 约束通过，54 个实现/入口文件通过 Python 3.10 语法与标准库导入检查；本机实际 Python 3.12.3。两个新 SKILL 校验通过。`evidence/validation.json` 列出逐测试路径/行号和实现摘要，`evidence/config-load-check.json` 证明 Downloads 真实配置只加载且通过，未移动、未改动、未创建构建机 data_root。未执行真实 P4、真实服务访问或浏览器。

HLD v0.9.5 已按 mv 单独提交并普通推送，提交 `3616628442cd037e7c519eb2efa4c9128d521a17`，SHA256 `5989620912fcb86cab5b399e3a66d868616092570916a6e38433ece659f17f63`；Downloads 无此原件。初次开工暂停和 125 项基线证据保留于 `evidence/preflight.json` 与 `evidence/baseline-test-output.txt`，其等待状态是历史记录，已由本次裁定及交付替代。

2026-10-27：第 2.1 批 + HLD v0.6 三家外部评审进行中。材料说明：`docs/enhance/batch2.1/review/README.md`；代码 diff：`docs/enhance/batch2.1/review/batch21-code-3fd6470.diff`（3157 行）；设计输入为 HLD v0.5.4 附录 G 与 HLD v0.6 本次版本记录。评审方只读、不改仓库，评审意见由设计方处理；第 3 批等处理后再下发，期间不开工。本次只新增评审材料和更新状态，不改代码。

据设计方本次反馈，第 2.1 批构建机真实验收已于 2026-10-26 通过，run_id 为 `b21-d45b98d33c5d4fbe9fe8829fa85901d4`：A/B/C/E 全部 PASS；F 的目录页指纹匹配 10 个链接、详情页身份核对通过、无跳转。结果位于构建机 `/home1/chengkai/vd-cosmos/run/verification/` 下。本次按反馈登记，未从本机访问构建机或重新运行验收。

第 3 批开工前侦察结论（设计方反馈）：P4 可用，默认 client 为 VD 树所用；已有日志分析器需要 PyYAML，已在构建机专用 venv 实测可用；ClineSR skill 目录在工作区下。具体设计以 HLD v0.6 的评审结果及后续下发任务为准。

2026-10-24：第 2.1 批已按设计方统一下发任务完成离线加固。125 项测试、三条 import 约束、三个 SKILL 校验通过；A/B/C/E 本地模拟 PASS，D 未提供 live 构建而跳过，F 已记录目录指纹和详情身份。原配置加载通过；HLD 原件未修改。实现与证据、本 STATUS 同批提交，普通 push。详见 `docs/enhance/batch2.1/DELIVERY.md`；下表逐条映射附录 G。真实服务未访问，实际构建机验收待运行本批脚本。

历史：第 2 批外部评审材料位于 `docs/enhance/batch2/review/README.md` 与 `batch2-code-678024c.diff`，对象为 HLD v0.5.3 + `678024c` 相对 `8ca13b3` 的代码改动。评审结论已由设计方处理并合入 HLD v0.5.4 附录 G 和本次任务；原等待期开工限制已解除。

2026-10-24 第 2 批读取侧实现与离线验收完成，基点 `8ca13b3fd37d53af6dbc5c084e976bfc5bc78843`。新增对账失败与独立包覆盖、修正 arm-only links 验收、HTTP ReportReader 和只读 workflow、构建机 A～E 验收脚本。B2-Q01 按人工裁决实现并闭合，HLD 未改。100 项测试、三条 import 约束及三个 SKILL 校验通过；127.0.0.1 A～E 小规模回放 PASS，2 条合成失败日志只下载一次、导出 1 块。实现、证据与本 STATUS 同批提交；完整索引：`docs/enhance/batch2/DELIVERY.md`。真实服务未访问，构建机 A～E 验收待执行。

设计方本次反馈：第 1.1 批脚本已在构建机用保存页面运行，计数、报告头、执行状态、arm 2244 行输入多重集合与路径集合、270 个扩展错误组、其它格式 0 条及源文件不变均已核实。唯一 FAIL 是 links.txt 仅含 arm 的 6 个失败包而脚本比较了两架构 7 个；设计方确认 x86 的额外失败包解析正确，属于上一批验收说明口径错误，第 2 批按 arm 单架构独立基线修正。此为用户提供的验收反馈，本机未访问真实网络。

2026-10-24：第 1.1 批离线修复完成。五份输入已核对归位；v0.5/v0.5.1 未跟踪副本已删除，v0.2 保留。真实汇总与报告头格式、首个详情页 title 判读、其它格式扩展错误人工确认已实现；78 项测试与两条 import 约束通过，真实 config.json 本地加载通过，verify_b1_real.sh 小规模离线回放 PASS。实现、设计依据、两份真实片段、证据和本文件同批提交；仅普通 push。完整索引：`docs/enhance/batch1.1/DELIVERY.md`。

2026-10-24：第 1 批离线实现完成；55 项测试通过，本线两条 import 约束通过；两个 SKILL.md 校验通过。实现、测试证据与本文件同批提交。完整交付索引见 `docs/enhance/batch1/DELIVERY.md`。

实现者本机未访问内网、Cosmos 或浏览器，未执行 P4 操作或真实构建提交。既有 head120 和合成测试只作格式/离线证据；构建机真实验收以设计方反馈的上述记录为准。

## 5. 已闭合结论（附证据路径）

### 2026-11-14 B1.1 已核实侦察追补

- 设计方确认并交付摘要核验的 docs/enhance/evidence/recon25.txt、recon26.txt：D3 三构建历史清单相同，撤回变化判断；四构建三列表且显示名空；cmp-v1 已确认，已登记属性可比较（替代初次 C3），未登记仍未核验；recon26 完整窗口确认 37432138 的两次构建链，不自动选择；EMAIL_CC 不列出。脚本 docs/enhance/evidence/scripts/recon24.py、recon25.py、recon26.py 原字节归档，仅后两份第 38 行有获批登记。证据摘要、代码与测试名见 DELIVERY 追补节。原首读冻结为防御设计；旧待 recon25 的记录为历史状态，已由本条替代。

### 2026-11-14 B1.1 设计方裁定

- 来源：设计方本次答复。真实变量页为 Name / Display Name / Value；两处调用共用按表头选 Value 的解析器；变量首次使用即冻结值/摘要，变化保留原值并写“变量页已变化”；同 Hub 的多个一致构建为重跑链而非证据冲突，不自动选。文本比较仍未核验，18 项配对提案须 FatTank 确认，配置保持未登记。recon23 输出无效，等待 recon25 已核实结果。实现/测试与映射提案见 DELIVERY B1.1 节。

### 2026-11-14 第 3a-1.1 批 Checkpoint B1

- §8.9 1–4：Hub Link 主证据与两种旁证独立；历史分页匿名会话仅在内存、同主机同历史路径跳转，首屏锚点/逐页衔接/补扫与三遍快照详情读取；结论只限“当前保留记录中”，未定位不能证明未提交。实现 `bm_pages.py`、`bm_transport.py`、`bm_reader.py`；证据见本批 DELIVERY 对照表与 `evidence-b1/`。
- §8.8 2、7–8 / §8.9 5–6：请求摘要按 base 解析结果、所有表单业务值计算；不确定不重提、最近一次请求才可显式另起；resolve 与 accepted 同事务建立观察任务；H_pre/两个确认词/硬检查；绑定使用既有读取器的 build_ref，workflow 对报告输入做核对、呈现重跑谨慎标记，不能把候选绑定当起轮授权。
- 两把锁与版本：观察锁覆盖生命周期，请求锁只保护读改写；网络读取在锁外，状态变化丢弃旧扫描。独立心跳不改变请求候选版本；中断按三倍间隔判定。保留补充观察起点、已见/待核对集合，404 与历史清理不清除未决记录。
- `submit.property_map` 提供全部 18 项，未登记保留空；cmp-v1 不抹缩进/内部空行，文本形状未确认时记未核验，PACKAGE_LIST 按解析结果核对。样例不含真实连接值。真实 config.json 本地加载 PASS，证据 `docs/enhance/batch3a-1.1/evidence-b1/config-load-check.json`，未改动原件、未联网。
- 人工命令仅写 FatTank 手册：`docs/enhance/batch3a-1.1/FATTANK-B1-MANUAL.md`。ClineSR 的 SKILL 只列读取调用，watch 固定加 --read-only。默认 doctor 不联网/不启动浏览器；在线自检只访问构建管理端；php 包数检查不安装/卸载。


### 2026-11-14 第 3a-1.1 批 Checkpoint A

- B3a11-Q01 已闭合（设计方答复 2026-11-14）：打印展开的 `p4 -p <p4.port> -u <p4.user> login`，只有非默认票据路径才加 `P4TICKETS=<路径>`；不采用间接读配置命令。内部名字/路径可显示，口令、票据内容、Cookie、会话令牌、SSO/SAML、浏览器资料和凭据模式命中值仍禁止。本批其余提示与 HLD 差异按 HLD 执行并记 DELIVERY；真实阻塞才停下提问。历史提问与答复留在第 8 节。
- 附录 O #1–5、#7–13 已在 Checkpoint A 处理；#6 原已结清。本轮落实真实 shelve 写法/时间线、GBS 与源码三行核对、相对路径、一次有上限包根列举、P4 返回路径不再转义、冲突数、最终内容预算、无时间窗口的进程锁测试、人工窗口重验、base 清单来源依据。逐项文件和测试名见 `docs/enhance/batch3a-1.1/DELIVERY.md`；旧 `batch3a-1/DELIVERY.md` 只追加 plusplayer 时间线与历史 Python 版本更正。
- journal 紧凑时区在 Python 3.10 显式规范化；解析失败写 `report_start_time_invalid` 待办。全线 API/源码摘要审计见 `docs/enhance/batch3a-1.1/evidence/python-api-audit.json`、`owned-source-manifest.json`。实际解释器测试结果见同目录两份 `test-output-python*.txt`，不以语法检查代替运行。
- A3 只读构建机验收器已提供：`vd-cosmos-core/scripts/verify_b3a11_real.sh` 与 `.py`；要求审核的完整 HEAD、同解释器完整离线测试、新建独立数据根、A–F、变量页清单和 7 包 P4 快照；未登录只提示登录命令。入口、隔离、停止边界与中途票据失效经离线测试；真实 Cosmos/P4 验收仍待构建机执行。准确调用和前置资料见本批 DELIVERY。
- 构建机真实配置仅在本机 Python 3.10.12 加载 PASS，证据 `docs/enhance/batch3a-1.1/evidence/config-load-check.json`；原件未移动/改动/提交，未联网。加载 PASS 不证明示例连接参数已经换成真实值。


- Hub Link 一一对应、历史列表完整可匿名翻页、提交端认证链路与表单/回调/整表提交实测、结果页不显示提交端编号。证据：`docs/enhance/evidence/`，见 HLD v0.9.14 附录 V。

- **B3a1-Q01 已闭合（来源：设计方本次答复，2026-11-02）**：报告以 `elapsed_window` 定型、有效执行状态未知、无人工终态时，定型之后重新下载且完整性校验通过的日志属于最终日志，可进入“结果已拉取”；回执记录 `settled_basis=elapsed_window`、终态依据“无”，起轮闸门仍不通过。临时日志条件是报告未定型，或可信来源明确说运行/排队且无有效人工终态；不把未知当作运行。之后首次取得可信终态或身份为强的运行/排队时，当前完成状态失效、产物保留、通知不重发；重新满足定型及最终日志条件后验证或重取。日志摘要不变则原分析结果有效，变化则标“输入已过期”。HLD 措辞由设计方下一版修正，本次不改 HLD。对应测试已通过：`test_elapsed_final_gate_closed_terminal_invalidates_revalidation_result_identity`、`test_elapsed_then_running_rejects_old_snapshot_and_changed_log_expires_result`；完整证据 `docs/enhance/batch3a-1/evidence/test-output.txt`。

- 第 2.1 批构建机真实验收已闭合（来源：设计方 2026-10-27 反馈）：验收日期 2026-10-26，run_id `b21-d45b98d33c5d4fbe9fe8829fa85901d4`；A/B/C/E 全部 PASS；F 目录页指纹匹配 10 个链接、详情页身份核对通过、无跳转。证据在构建机 `/home1/chengkai/vd-cosmos/run/verification/` 下，本机未复制结果文件。
- 第 3 批开工前侦察已取得结论（同一反馈）：P4 可用且默认 client 为 VD 树所用；日志分析器所需 PyYAML 在构建机专用 venv 实测可用；ClineSR skill 目录在工作区下。设计记录：`docs/enhance/vd-cosmos-loganalyzer-hld-v0.6.md` 本次版本记录；不等同于第 3 批开工授权。
- 本次评审输入原样归位、摘要核对与凭据预检通过，三份材料的路径、SHA256 和 diff 生成命令见 `docs/enhance/batch2.1/review/README.md`。

- 第 2.1 批 A～G 离线交付通过：`docs/enhance/batch2.1/evidence/test-output.txt`，125 tests / OK，SHA256 `da09291c175dfaaa9afd85925141c89d436b655c349a72afd50dd4a17e64cb31`；三条 import 约束、TLS（未跳过）与三项 SKILL 校验通过。
- A～F 模拟及来源：`docs/enhance/batch2.1/evidence/offline-A-F-output.txt`、`offline-verify/result.json`、`offline-run.json`、`offline-export/manifest.json`。临时干净源码快照与待交付本线文件逐一一致；backend=http-fixture，两个合成日志只下载一次，一条两包分析待办，一块导出，非真实验收。
- 原运行配置直接接受、源文件摘要未变、不复制、不访问网络：`docs/enhance/batch2.1/evidence/real-config-load.json`。受保护文件与凭据检查：同目录 `protected-files-check.json`、`prepush-check.json`。
- 本批脚本 `vd-cosmos-core/scripts/verify_b2_real.sh` SHA256：`b59d5bbceba8921087726722b3ab552197bf9003bf8d2f9724ee6e2f216022d6`。HLD v0.5.4 SHA256：`8fdcb3c9b8c26e592bad0695db59736709b02790adeae9ba87386cfd1b26f2f8`。

### 第 3a-1 批已闭合实现结论

- §5.4 / §9.2 / §9.3：窗口和计数落盘；人工窗口不因详情恢复而改用另一依据；日志回执和完成状态按当前观察重验，历史日志按版本保留。测试：`test_terminal_epoch_unknown_since_restart_and_running_never_elapsed`、`test_manual_window_survives_running_failure_and_expires_on_digest_or_withdraw`、`test_three_stall_conditions_without_old_poll_count_false_alarm`、`test_loop_uncounted_and_counted_segments_starvation_and_fatal_errors`。
- §6.1.1a：2245/545 行合成变量页逐项核对、禁止页外变量落盘、清单不可变、人工两种退路已测试；真实页面未读取。测试：`test_appendix_i_2245_base_545_shelve_and_credential_variable_never_written`、`test_pairing_exact_segments_duplicate_cross_branch_and_shelve_tuple_mismatch`。
- §3.6 / 附录 I：假 p4 marshal 夹具覆盖默认 code0、退出码一致性、信号/残缺输出、已提交 CL 带文件行；未知错误三次后停止，inbox done 恢复。测试：`test_fake_p4_context_protocol_real_error_shapes_signal_partial_unknown_and_forbidden`、`test_confirm_input_checks_current_describe_and_unknown_retry_gate_recovers`。
- §6.1.1/1a：来源与行核对分开；所有合并动作、跨分支/跨包、大小/路径/关键字/时间、主错误仅诊断条件有正反路径；附录 I 的 2/1/32 个 edit 形状均原样叠加。测试：`test_shelve_overlay_merge_conflict_advanced_add_delete_move_and_cross_branch`、`test_move_pair_other_actions_cross_package_and_mid_snapshot_mutation`、`test_appendix_i_three_shelve_samples_2_1_32_edits_overlay_without_archive` 等。
- §0.5 / §8.1.1：四个人工命令登记入能力表，非 TTY 拒绝；真实 PTY 覆盖 override-running 回显/输入构建号/撤回。测试：`test_confirm_terminal_pty_override_echoes_build_and_records_withdraw`、`test_manual_entrypoints_non_tty_and_closed_database_are_classified`。
- 上述统一证据路径：`docs/enhance/batch3a-1/DELIVERY.md`、`docs/enhance/batch3a-1/evidence/validation.json`、`docs/enhance/batch3a-1/evidence/test-output.txt`。本段只验证离线行为，不结清 §14 的真实同步方式待确认项。

### 第 2.1 批附录 G 落实表

下列测试默认位于 `vd-cosmos-core/tests/test_batch21.py`，其它模块单独注明；完整输出见上，A～G 实现路径和更多正反例见 `docs/enhance/batch2.1/DELIVERY.md`。

| G# | 本批落实情况 | 对应测试名 / 依据 |
|---|---|---|
| 1 | 先定型；未定型结构问题仅 issues | `test_unsettled_malformed_running_then_terminal_or_settle_deadline` |
| 2 | 稳定 + 终态或 settle_s；永久缺头/汇总有出口 | `test_truncated_structure_to_full_and_missing_summary_settled`、`test_unsettled_malformed_running_then_terminal_or_settle_deadline` |
| 3 | 停止后低频观察、内容变化重判并记待办 | `test_stopped_loop_reobserves_changed_report_and_detail_failure_does_not_block` |
| 4 | 覆盖不再改变报告 result_state | `test_header_only_after_both_settled_and_coverage_projection_pure` |
| 5 | 按设计留第 3 批 accept-coverage；本批预留人工接受模型，不实现人工命令 | HLD G#5；`test_http_workflow.py::test_missing_expected_package_is_coverage_only_invalid_baseline_is_argument_error` 验证 manual_file 不满足闸门 |
| 6 | coverage_basis 与闸门来源限制；request/previous_report 实际来源留第 4 批 | 同上；`test_header_only_after_both_settled_and_coverage_projection_pure` |
| 7 | 路径/CL/shelve 多重集合，差异排序限 20 条 | `test_real_format.py::test_verify_rows_cl_shelve_and_duplicate_replacements_rejected`、`test_difference_list_is_limited_and_retains_total_count` |
| 8 | 结果已拉取不等于执行终态/起轮授权 | `test_stopped_loop_reobserves_changed_report_and_detail_failure_does_not_block`；README/SKILL 说明 |
| 9 | 全部架构定型才核对 header | `test_header_only_after_both_settled_and_coverage_projection_pure` |
| 10 | 身份、全部候选、所选属性/理由/规则/摘要；凭据字段整项净化 | `test_detail_failure_counts_identity_all_candidates_recovery_and_report_failure`；`test_http_workflow.py::test_detail_session_parameters_never_persist_raw` |
| 11 | 全部文档拒绝跳转、日志逐跳先检查，越界目标 0 请求 | `test_all_document_redirects_refused_before_target_request_and_index_fingerprint`、`test_log_redirect_port_host_and_path_refused_with_zero_target_requests`、TLS 测试 |
| 12 | 404 需无跳转的 200 目录指纹，无 form/密码框 | `test_all_document_redirects_refused_before_target_request_and_index_fingerprint` |
| 13 | CL/chunked 完整性，中断正文不落盘不缓存 | `test_content_length_chunked_interruptions_no_cache_and_true_timeouts`、`test_response_evidence_log_active_truncation_differs_from_incomplete` |
| 14 | 总 deadline 覆盖底层等待，独立 idle timeout | `test_content_length_chunked_interruptions_no_cache_and_true_timeouts` |
| 15 | 系统 CA + 指定 CA、CONNECT、固定失败类别、逐请求响应证据 | `test_tls_self_signed_extra_ca_hostname_and_downgrade_refused`、`test_response_evidence_log_active_truncation_differs_from_incomplete` |
| 16 | HTTP 使用前提遵照 HLD §5.4；文档说明无 cookie/凭据，只读配置实例 | `test_http_workflow.py::test_same_host_redirect_limit_and_no_cookie_storage_or_return`；本线 README |
| 17 | 404 正常等待不记停滞，仅检查预期时长 | `test_monitor_404_timeout_live_disk_and_versioned_todo_identity` |
| 18 | 新配置默认值、模板/正则校验与 README 补齐 | `test_http_workflow.py::test_fetch_defaults_template_validation_and_real_cli`；`real-config-load.json` |
| 19 | 按完整 SHA256 存页，历史最多 50 条 | `test_continuous_reset_failure_404_change_config_clock_and_history_bound` |
| 20 | 按构建 SQL 过滤、仅最新两份产物；损坏缺失可恢复 | `test_wal_reader_error_wrapping_and_other_build_history_not_loaded`、`test_completed_baseline_change_invalidates_and_missing_artifact_recovers` |
| 21 | 日志连续三次失败一待办 | `test_three_log_failures_have_one_todo` |
| 22 | 日志步骤重新观察，报告变化先记观察、不下载 | `test_logs_refresh_report_and_cache_bound_to_report_and_limit` |
| 23 | 缓存绑定报告/上限；完成评估绑定报告/基线/配置/解析器 | 同上；`test_completed_baseline_change_invalidates_and_missing_artifact_recovers` |
| 24 | 实例含协议/主机/端口/路径，目录统一 build_ref 摘要 | `test_rule_errors_are_not_swallowed_and_instance_scopes_do_not_mix` |
| 25 | WAL、busy_timeout=2000、SQL 错误结构化 | `test_wal_reader_error_wrapping_and_other_build_history_not_loaded` |
| 26 | A 页面不同 FAIL；B 必须新鲜完整、非 HTML、重算摘要 | `test_saved_page_difference_fails_A`、`test_truncated_incomplete_and_html_logs_fail_B` |
| 27 | 完整 HEAD、仅本线干净、real 主机限制、来源记录 | `test_direct_commit_dirty_source_and_real_loopback_rejected_before_output`、`test_clean_snapshots_repeated_independent_A_to_F_and_unrelated_changes` |
| 28 | 每次独立 data_root，只认本次缓存/状态/事件 | `test_clean_snapshots_repeated_independent_A_to_F_and_unrelated_changes` |
| 29 | 每次实时 statvfs，身份不含字节数 | `test_monitor_404_timeout_live_disk_and_versioned_todo_identity` |
| 30 | watch 停止条件返回 3 | `test_http_workflow.py::test_changing_then_stable_inconsistent_report`、`test_missing_expected_package_is_coverage_only_invalid_baseline_is_argument_error` |
| 31 | observe 仅吞 FlowError(5)，4/6 继续抛出 | `test_rule_errors_are_not_swallowed_and_instance_scopes_do_not_mix` |
| 32 | 真实超时/TLS/进程崩溃/并发/监控测试 | `test_tls_self_signed_extra_ca_hostname_and_downgrade_refused`、`test_actual_child_crash_after_observe_logs_notify_result_unique_and_cleanup`、`test_round_contention_three_skips_one_todo_and_real_two_process_ticks`、超时/监控测试 |
| 33 | 仅 loop 限定追加重试，不重做动作；同构建/人工/外部写/显式编号不重试；3 次锁跳过退出 | `test_append_retry_other_build_only_constraint_same_build_and_explicit_no_retry`、`test_tick_concurrent_other_build_append_retries_without_repeating_action`、`test_round_contention_three_skips_one_todo_and_real_two_process_ticks` |
| 34 | 连续记录不受历史裁剪影响，失败/404/配置/倒时重置 | `test_continuous_reset_failure_404_change_config_clock_and_history_bound` |
| 35 | 详情两种未知分开、独立计数/清零、不补旧终态 | `test_detail_failure_counts_identity_all_candidates_recovery_and_report_failure`、`test_stopped_loop_reobserves_changed_report_and_detail_failure_does_not_block` |
| 36 | 待办身份按构建/架构/原因/依据版本，正文排序 | `test_monitor_404_timeout_live_disk_and_versioned_todo_identity`；日志失败/详情失败/重复投影测试 |

### 先前批次已闭合结论

- 第 2 批任务 1～6 离线交付已通过：完整输出 `docs/enhance/batch2/evidence/test-output.txt`，SHA256 `60be2e43bcf43c22e6889835222b30b5af237d73c412d7deeea67e2fc971b57b`。逐条实现、测试名及文件索引：`docs/enhance/batch2/DELIVERY.md`。
- A～E 本地 HTTP 回放：`docs/enhance/batch2/evidence/offline-A-E-output.txt`、`offline-verify/result.json`、`offline-export/manifest.json`；A/B/C/E PASS，D 如实记录、不设通过条件；这是合成规模，不能替代构建机验收。
- 缺 fetch 段的真实配置原样加载通过，源文件未变、未复制、未联网：`docs/enhance/batch2/evidence/real-config-load.json`。
- 8567 个受保护文件摘要未变：`docs/enhance/batch2/evidence/protected-files-check.json`。HLD v0.5.3 原始 SHA256 保持 `279a96f2e0b50fc91ff983cc37bc2fc588df18307ea07958463f5cf565237b65`。

- B2-Q01 已闭合：实例锁与轮次操作锁分层，依据本文件人工裁决中的设计方 2026-10-24 答复；实例锁覆盖睡眠，轮次锁和写事务睡眠前释放；手工 tick 成功，loop 读取新事件，不重复下载/通知。证据：`vd-cosmos-core/tests/test_http_workflow.py::WorkflowTests.test_sleep_allows_manual_tick_instance_lock_still_excludes_second_loop`、`docs/enhance/batch2/evidence/test-output.txt`。

- “对账失败是否单设”已按 HLD v0.5.3 §5.3/§5.4 裁定闭合：新增 report_state=对账失败，包集合覆盖移至 package_coverage；本批实现及正反例测试通过；完整输出：`docs/enhance/batch2/evidence/test-output.txt`。依据：`docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.3.md`；归位证据：`docs/enhance/batch2/evidence/preflight.json`。

- 第 1.1 批任务 1～6 的离线部分已完成；测试证据：`docs/enhance/batch1.1/evidence/test-output.txt`，SHA256 `cc0d8ee5349068635e8c44a8f8153d58d7891f1e9885911f2d8c4d7c27eabacd`。逐项测试名与实现文件见 `docs/enhance/batch1.1/DELIVERY.md`。
- 真实配置被新加载器接受、源文件不变且不落库：`docs/enhance/batch1.1/evidence/real-config-load.json`。
- 验收脚本离线 PASS、独立基线相等及导出清单：`docs/enhance/batch1.1/evidence/offline-verify/result.json`、`docs/enhance/batch1.1/evidence/offline-verify/export/manifest.json`。

- B1.1-Q01 已闭合：仅在 HLD v0.5.2 第 571 行末尾追加 ` <!-- # credential-test-sample -->`，新 SHA256 `255746d16ac88b9c7c4f429575f1b493b6da85295c9307ae9b5b14d91509f830` 与设计方指定值相同。证据：`docs/enhance/batch1.1/evidence/hld-comment-exemption.json`。

- B1-Q01 已闭合：result_state 为成功/失败/部分/未知，按每架构完整报告汇总；三类错误都算失败，结果与执行终态独立。依据：HLD v0.5.1 §5.3/§5.4 及 FatTank 本次裁定。证据：`vd-cosmos-core/tests/test_reports.py`、`docs/enhance/batch1/evidence/test-output.txt`。
- B1-Q02 已闭合：header_consistency 独立取一致/不一致/未核；不一致保持报告覆盖状态、结果未知、写待办，不能通过读取侧终态前提。证据：同上及 `vd-cosmos-core/tests/test_cli.py`。
- 数据库追加纪律、乐观并发、活动准备/click/bind 约束、flock、权限门、导出拒绝和 P4 禁用门的正反例通过。证据：`vd-cosmos-core/tests/test_foundation.py`、完整测试输出。
- CLI 单 JSON 输出、退出码、文件产物与假浏览器序列通过。证据：`docs/enhance/batch1/evidence/cli-transcript.json`、`vd-cosmos-core/tests/test_cli.py`、`vd-cosmos-core/tests/test_reports.py`。
- 完整测试输出 SHA-256：`aae750cf794adbfa482283b2b82aa74817197b4c8650472d198a6b5422754a76`；路径：`docs/enhance/batch1/evidence/test-output.txt`。

- 后续设计方文档若仅说明文字的规则名称触发凭据检查，只允许在命中行行尾加 `<!-- # credential-test-sample -->`；修改后必须停下报告新 SHA256，等待设计方确认。其它修改须先询问。本次 B1.1-Q01 已明确授权并提供期望摘要，无需重复确认。

## 6. 人工裁决

- 不带 shelve 的测试构建为构建管理端 19270912（提交端 37491096，11-09 由用户手工起）；19270877（提交端 37491058）为误提交、不得使用。

来源：设计方 2026-10-24 对 B2-Q01 的答复。实例锁使用 flock，覆盖 loop 全生命周期（包含睡眠），第二个 loop 获取失败退出 6，退出/崩溃由内核释放，不另写锁文件清理逻辑。轮次操作锁和 SQLite 写事务仅在 tick 必要阶段持有，睡眠前释放；手工 watch/fetch/workflow tick 不获取实例锁，睡眠期间可正常执行。loop 醒来读取最新事件，避免重复下载和重复待办。新增对应并发测试。HLD 不改，以此裁定为准。

2026-10-22：

- 本线放在独立分支 `vd-cosmos-loganalyzer`，不进 main。
- 仓库公开，提交内容不含内网信息，具体值只放构建机配置。
- Demo 目标周五，至少完成能力 1 和 2。

2026-10-24 第 1.1 批：按 v0.5.2 和专门任务修复本线既有代码；原始报告片段和设计文档纳入提交，环境真实配置只作本地加载、不提交。HLD §0.3 开发期内部名称/路径可入仓库，仅告警；凭据仍拦截。

2026-10-24：按 HLD v0.5.1 继续第 1 批；B1-Q01/B1-Q02 是确定契约，无需再次等待。仅离线实现，不开展真实读取或外部写操作；Git 收尾使用普通 push，禁止 force push。

## 7. 待确认事项

第 2.1 批构建机真实验收已由设计方反馈通过；后续评审处置进入冻结 HLD v0.9.5，本次第 3a-1 批已完成离线实现。B1/B1.1/B2 与 B3a1-Q01 均已闭合。

保留 HLD §14 第 14 条有关 shelve 包真实同步与合并内容的待确认条件；本段按正文允许“请求 base（待确认）”及“已合并”作为分析输入，不自行升级为实际编译版本。§14 第 15～16 条的侦察事实以附录 I 为依据，本机没有重做内网侦察。3a-2 的诊断族/分析隔离与 3a-3 的准确性验收等后续任务，不在本段提前实现。

## 8. 挂账

### 2026-11-14 Checkpoint B1 收尾与 B2 前提

- 本机 ext4 上旧 batch2.1 验收子进程超过既有 20 秒时限；保留独立失败诊断，同源在 tmpfs 通过，最终两种解释器全套亦在 tmpfs 运行（不改超时/断言）。详情与复现环境见 DELIVERY 的 B1 测试环境节及 evidence-b1/test-environment.json；不冒充构建机磁盘/真实网络验收。
- 本批无新增待裁定 B3a11-Q 问题；继续执行 B3a11-Q01。用户称 watch“只读”，HLD 允许控制终端人工确认：采用 HLD 并记录于 DELIVERY，后台/--read-only 路径不绑定。
- 构建机 B1 实测待用户执行 `verify_b3a11b1_real.sh`：完整提交号与源码洁净检查、完整离线套件、doctor --online、37491096→19270912 与 37491058→19270877 两次无登录查号。19270877 只作误提交只读查号，禁止绑定、分析和输入使用。开发机没有运行在线段。
- 页面夹具按 recon15–22 的记录结构重建，不冒称原始生产 HTML；真实页面布局仍由构建机脚本验证。历史清理、换账号又换编号的重试、观察期后的重跑是已知漏观测边界。
- B2 尚未实施：浏览器启动/认证/残留清理、once、请求闸门、控件回调、点击、--rehearse、--via-hub。状态层请求/结果/观察任务与 H_pre 采样接口已就位，不由本批调用任何提交动作。属性映射与文本形状仍待第二十三次侦察、控件编码待 B2 演练登记。


### 2026-11-14 Checkpoint A 收尾与后续接口

- 没有新增待设计方裁定的问题；B3a11-Q01 已闭合。构建机尚需执行本批 DELIVERY 中的完整提交号验收命令，回传 A–F 和 7 包表格；本地不访问真实服务。未提供进行中构建时 D 段如实 SKIP。
- 本机没有 Clang 22；源码显示夹具依冻结 HLD/已记录真实形状构造，未冒称重新生成 Clang 22 金样。真实构建机日志核对结果待回传。
- 保留给后续分析/接收的接口：snapshot manifest 的 `basis` / `basis_scope` / `basis_review` / `edits_eligible`、`basis_review_interface`；范围变化或不符保持仅诊断与待复核，不自动清除争议。完整人工复核、同步流程变化登记和结果接收留后续批次。
- Checkpoint B（§8.8 / §8.9）未开始；3a-2 / 3a-3 未提前实施。下一步先评审 Checkpoint A 并完成构建机只读验收，再由设计方下发后续任务。



### 2026-11-14 第 3a-1.1 批 Checkpoint A：B3a11-Q01（已闭合；设计方答复 2026-11-14）

- 本次任务由 Claude 接任设计、FatTank 批准；设计冻结为 HLD v0.9.18，仅实施 Checkpoint A，不启动 §8.8 / §8.9。开工核对：独立工作树 HEAD 与 origin/vd-cosmos-loganalyzer 均为 `1b090b17b4029f3cccf3e2c1447b253b4a12c11d`，工作区干净。
- 问题：A3 要求未登录时打印给 FatTank 原样执行的登录命令，同时要求输出不含任何配置值、可安全回传。HLD §3 第 6 条要求该命令包含 `p4.port`、`p4.user`，非默认票据路径时还包含 `p4.tickets_file`；直接输出该命令会输出配置值。
- 建议裁定：允许输出仅引用配置文件、由 FatTank 明确手工执行后在本机读取连接参数并启动登录的命令，不在验收输出或证据中展开连接参数；验收脚本本身仍只做登录状态检查，绝不执行登录。请设计方确认是否接受此形式替代 HLD 的直接 P4 登录命令，或明确可输出配置值的例外范围。
- 裁定（设计方 2026-11-14）：不用间接读取配置的登录命令，按 HLD §3.6 输出展开的 `p4 -p <p4.port> -u <p4.user> login`；票据路径非默认时才前置 `P4TICKETS=<路径>`。允许输出连接地址、用户名、票据路径（只限路径）、数据根、主机名、构建号、CL 与 depot 路径；密码、票据内容、cookie、会话令牌、SSO/SAML、浏览器 profile 和命中 §0.3 凭据模式的名字或值永不输出。验收脚本自身不登录。
- 本批后续口径：任务与 HLD 有差异时按 HLD 执行并记录 DELIVERY.md，涉及凭据或真正阻塞才停下询问；继续 Checkpoint A，包含真实 Python 3.10 / 3.12 运行。

- HLD §14 第 23 条：第二十三次只读侦察（表单属性与构建管理端变量名对应表；记值摘要，用固定词表打印明文，比较规则 `cmp-v1`；加原样取值形状与四项精确核对，确认前请求与变量页的文本比较记“未核验”）未做；第 1 条：本线提交改为候选 + 人工确认。

- HLD v0.9.14 §14 第 20、21、22 条待定。

### 2026-11-03 第 3a-1 批收尾与下一段前提

- 当前没有新增待裁定阻塞项；B3a1-Q01 已闭合。真实环境验收尚未执行，真实配置本地加载 PASS 不表示真实连接参数或构建机验收通过。
- 3a-2 接 snapshot manifest（逐文件来源、行核对、可编辑条件和仅诊断模式）、task_notice_interface、包键+任务输入摘要；补任务包、接收器、ClineSR/已有工具适配与诊断清单。3a-3 再接其它裁决、账本和准确性脚本。
- 附录 H/J～N 的各项已落实/分段保留清单见 `docs/enhance/batch3a-1/DELIVERY.md`。正式绑定流程未来应在绑定事件提供 previous_build，使旧 loop 停止；本段未实现提交或伪造绑定。
- 本段开发只使用合成页面与假 p4。保留 §14.14 的来源待确认标签；3a-2/3a-3 开工仍需设计方任务。


### 2026-11-02 第 3a-1 批 B3a1-Q01（已闭合；保留开工挂账）

- 场景：全部期望架构报告按 `elapsed_window` 定型且完整，执行状态为“未知”，没有人工终态确认；此后新下载的日志已通过完整性校验。
- HLD v0.9.5 §5.4 第 3 条（第 408～409 行）明确讨论“此前已按时长完成读取”和三种定型依据完成后的观察；§8.1 第 1 条（第 729 行）允许没有有效终态依据时下载、分析、准备请求。
- 同时，§5.4 第 3 条要求定型、最终日志和闸门共用“有效终态依据”口径；§9.2（第 892 行）要求按有效终态依据判断“执行仍在运行”，但没有明确上述“未知 + 按时长定型”场景中日志回执是最终还是临时。两种解释会改变读取完成条件，以及 §9.2 任务输入摘要能否使用该日志，不能由实现者自行选择。
- 初次提问（历史）：此时能否把新取得的完整日志记为最终日志并进入“结果已拉取”？建议允许读取完成、保持终态闸门关闭；以后首次取得可信终态时仍按 §5.4 使当前完成状态失效，终态窗口完成后重验日志，通知不重复。当时尚未实现；现已按 B3a1-Q01 裁定实现，见第 5 节。
- 初次暂停现场（历史）：仅 HLD 单文件提交已推送，当时三个准备性源码改动已撤回，代码仍为开工基线；挂账与开工证据留在工作区，未作实现提交。基线测试完整输出及 SHA256 见 `docs/enhance/batch3a-1/evidence/preflight.json`。
- 3a-2（任务包、结果接收、诊断定性）与 3a-3（其余人工命令、账本、准确性验收）均未开始；本段接口现已交付，见本批 DELIVERY。恢复前提已由设计方 B3a1-Q01 裁定满足，本段离线实现已完成。

### 2026-10-27 第 2.1 批 + HLD v0.6 外部评审

- 第 2.1 批真实验收待执行事项已由 2026-10-26 的 PASS 反馈闭合；结果位置与 run_id 见上。以下 2026-10-24 的待验收说明保留为历史记录。
- 第 3 批开工前侦察结论已登记；当前仅评审材料准备，不实施 HLD v0.6 新设计。待设计方处理三家评审意见后正式下发第 3 批。
- HLD v0.6 原件和代码 diff 未改写；v0.5.4 原件保留。工作区已有范围外改动不纳入本次提交。

### 2026-10-24 第 2.1 批收尾与下一批前提

- 无新增待裁决设计问题。G#5 accept-coverage 按设计留第 3 批；G#6 request/previous_report 来源留第 4 批，当前 manual_file 永不满足起轮闸门。
- 构建机第 2 批留下的 `rounds/19091860/` 等旧数字目录不读、不迁移、不删除；本批统一按 build_ref 摘要存储，首次使用重新建立稳定记录和缓存。
- 下一步由设计方审核完整提交号并在构建机运行新版 verify_b2_real.sh，核验真实 7 个失败日志、独立基线与 F 段；本批离线输出不可冒充真实验收。
- 本批测试、A～F 证据、配置仅加载及受保护范围校验均有文件索引；原范围外的已有改动和未跟踪 v0.3 仍保留，不纳入提交。原任务只允许本线修改，根 CI、现有其它 skill 和依赖文件未动。
- Export Error 未知表头、分析者、人工处置、浏览器/P4 写入与构建提交协议仍按后续批次提供任务；不基于未知格式猜测。

### 2026-10-24 第 2 批收尾与下一批前提

- 无待裁决的本批设计问题；B2-Q01 和“对账失败是否单设”均已闭合。
- 待构建机用经审核的完整本批提交号运行 `vd-cosmos-core/scripts/verify_b2_real.sh`，验收真实 HTTP、6/1 个日志、独立 rows/arm-only links、loop 与可选进行中构建观察。只能由该结果确认真实部署适配；本机只做 127.0.0.1 模拟，不访问真实网络。
- Export Error 的真实表头仍缺样本：非零且结构不可识别时按设计拒绝推进。已支持可识别 export_error 包的日志分派，但不猜测真实未知表格。
- 第 3 批分析者、人工处置、来源闸门，以及后续浏览器/P4/新构建提交不在本批范围；当前“结果已拉取”不等于终态确认或起轮授权。其它架构独立包集合仍待后续来源提供。
- 本地观察时长告警沿用观察窗口，未声称等同服务器构建耗时。原有范围外修改和未跟踪 v0.3 文档未纳入本批。

### 2026-10-24 第 2 批 B2-Q01（已闭合；以下保留开工挂账）

- 第 2 批任务 4 同时要求“loop：单实例（文件锁，拿不到退出码 6）”和“两次 tick 之间睡 poll.interval_s，睡眠期间不持有锁和 SQLite 事务”。HLD v0.5.3 §9.3 要求 loop 单实例，并分别规定轮次文件锁和 SQLite 立即写事务。
- 若所有文件锁在睡眠时都释放，另一个 loop 进程可在此窗口取得实例锁并启动，无法保证原 loop 仍存活时第二个 loop 退出 6。若实例锁全程持有，则与“睡眠期间不持有锁”的字面范围不一致。实现者未自行选择解释或引入额外租约协议。
- 建议设计方明确：实例锁覆盖 loop 整个生命周期（包含睡眠），轮次操作锁及 SQLite 事务只在 tick 必要阶段持有，睡眠前释放；第二个 loop 即使在第一个 loop 睡眠时启动也退出 6。请确认该范围，或规定替代的单实例机制。
- 初次暂停时只完成 HLD 复制与只读预检、STATUS 挂账和开工证据；代码、配置、测试、SKILL.md、验收脚本均未改动，未提交、未推送。证据：`docs/enhance/batch2/evidence/preflight.json`。


### 2026-10-24 第 1.1 批 B1.1-Q01（已闭合；以下保留初次挂账背景）

- 原样复制的 HLD v0.5.2 的 SHA256 为 `7a054e9a7e0bbcec77177c31e58df5ddefb3b177d6aace41e25a474b2a897916`。现有两级推送检查以 config.sample.json 的凭据模式、启用文档允许的行内样例豁免进行预检，仍在第 571 行命中 pattern_index=3 两次；命中的是说明文字里的规则名称，不是发现了真实凭据。该行没有豁免标记。
- 本批要求把该 HLD 纳入提交，同时要求凭据模式命中拦截。若为说明文字添加 `# credential-test-sample`，文件将不再保持用户指定 SHA256；实现者未自行改写权威设计或放宽检查。请设计方裁定：允许仅在该行补充既有规则支持的豁免标记并记录新 SHA256，或另行提供核对通过的修订文件及 SHA256。
- 证据：`docs/enhance/batch1.1/evidence/file-placement.json`、`docs/enhance/batch1.1/evidence/prepush-input-check.json`。两份真实片段的预检通过；片段仅作格式参照，不能作为完整真实报告验收证据。
- 暂停时状态（历史记录）：已有未测试修改：`vd-cosmos-core/src/vd_cosmos_core/` 下 report.py、models.py、config.py、backends.py、groups.py。配置样例、测试适配、真实格式夹具、verify_b1_real.sh 以及真实运行配置加载检查均未完成，不声明这些修改已可用。全部保留在工作区，无新提交。
- 初次暂停时仅核对真实 config.json 摘要；恢复后已完成一次本地加载且通过，见 real-config-load.json。真实配置和任务说明一直保留在 Downloads，不纳入提交。
- 第 1.1 批原次要挂账（已由 v0.5.3 裁定闭合，第 2 批已实现）：计数不符、包键重复、分类交叉等稳定后的对账失败从“部分”分离；新增 package_coverage。

2026-10-22 含内网信息的提交 `2bdee6c` 曾被推送到远端，已用本提交覆盖。

### 2026-10-24 第 1 批开工检查（历史记录，现已闭合）

本批以 `docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.md` 和本次任务指令为准。已阅读设计与本文件；按“任何不确定、或发现设计文档自相矛盾时停止并挂账”的要求，尚未开始实现、运行测试或执行本批 Git 提交与推送。

1. **B1-Q01：`result_state` 的取值与推导规则未定义。** HLD §5.3 的 `observe` 接口列出了 `execution_state` 和 `report_state` 的取值，但只列出 `result_state` 字段，未定义枚举及从报告分类计数、完整性和跨架构结果推导它的规则。证据：`docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.md:268`；§5.4（同文件第 284～299 行）也未补充该字段。请设计方明确取值，以及报告尚不完整、只有扩展错误或 Export Error、跨架构结果不同时的输出，作为 watch 的三状态契约与测试断言依据。
2. **B1-Q02：跨架构“不一致”应写入哪个状态字段未明确。** HLD §5.3 将 `report_state` 列为“未发布 / 部分 / 完整 / 结构未知 / 未知”，§5.4 第 4 条要求报告头不同时记“不一致”并写待办，但未说明“不一致”是新增的 `report_state` 值还是独立的一致性字段。证据：`docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.md:268`、`:295`。请设计方明确字段归属，以及各架构分别完整但报告头不同的情况下，本轮 `report_state` 的值；实现者不自行扩展或映射枚举。

上述恢复前提已由 FatTank 的消息及随后放入的 HLD v0.5.1 满足；本批已按裁定完成离线实现。开工现场已有本批范围外的文件修改，均未触碰。

### 第 1 批原收尾挂账（历史）与第 1.1 批更新

- 第 1.1 批更新：两份真实格式片段、兼容修复、独立基线验收脚本与离线证据已交付。下一步在构建机使用经审核的本批完整提交号运行 verify_b1_real.sh；正式验收尚未发生。Export 表真实标题待核实；对账失败仍与未发布完整共用“部分”，第 2 批前裁定。
- 以下记录保留第 1 批结束时的状态，后续进展以上述第 1.1 批记录为准。

- 真实报告验收未运行：`docs/enhance/` 未提供 HTML/HTM 报告或归档夹具；证据为 `docs/enhance/batch1/evidence/real-fixture-inventory.json`。合成规模测试覆盖 armv7l 2244/1479/0/759/6、x86_64 43/42/0/0/1，但不证明真实页面格式兼容。
- 下一批需提供两架构报告、两次观测时间、独立期望包集合及可信详情页；再核实真实标题、包版本来源、表头和原型逐行比对。版本在日志路径中不可得时记录 null，不猜测。
- 真实抓取/日志下载、P4 执行、真实浏览器和完整提交协议均按范围留桩；假浏览器只回放页面序列。未实现 workflow loop、分析者、处置/清单闸门或授权命令。
- 当前时长告警依据本地已记录观察窗口，不声明真实服务器构建耗时；下一批接入可信服务器时间后补充。
- 根目录原有改动和用户提供的未跟踪设计文档不纳入本批提交。范围核验见 `docs/enhance/batch1/evidence/protected-files.json`。

### B3a11-Q02（已闭合；设计方答复 2026-11-14）

设计方批准原样归档到 docs/enhance/evidence/scripts/recon23.py（SHA256 b8781bd49d91512f0d2c0b6b8a4e92a0900658aa04487f54b1bca7152232ff81），recon_scripts.txt 不变；archive-exemptions.json 登记第 45 行的精确命中文本、规则、原因、日期及批准人。只有脚本目录内的原路径、全文件摘要、行号、文本及规则完全匹配才豁免；任何字节变化使豁免失效。仅仓库 prepush/archive 检查读取登记，运行时 check_content/export/verifiers、配置与其它预检不变。原件通过、字节变化、未登记文件、真实会话值及运行时隔离测试均通过。证据：docs/enhance/batch3a-1.1/evidence-b11/recon23-archive.json、DELIVERY.md 的 B1.1 节、vd-cosmos-core/tests/test_archive_precheck.py。
