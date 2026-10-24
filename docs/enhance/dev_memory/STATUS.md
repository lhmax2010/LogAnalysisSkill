# LogAnalyzer 增强版分支状态

## 1. 本线说明

本线为 LogAnalyzer 增强版第一版。

- 设计文档：`docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.3.md`（第 2 批权威设计；复制摘要符合指定值，凭据预检通过，未改写。v0.5.2 保留）。
- 分支：`vd-cosmos-loganalyzer`。
- 分支起点：`accd7f4`。

## 2. 工作约定

- 本分支只新增目录与 `docs/enhance/` 下的文件，不修改仓库已有文件。
- 已有 skill 只通过命令行调用。
- 公开仓库约束按 HLD 第 0.3 节执行：内部词表命中只告警，凭据模式命中拦截；本批代码和配置样例只用占位值。
- 新 Session 开场先读本文件核对。
- 每个任务收尾在同一个 commit 里更新本文件。
- 本批按 2026-10-24 第 2 批开发任务、HLD v0.5.3 与 B2-Q01 裁定实施；未授权的后续章节不实现。

## 3. 计划

本线按设计方分批任务推进；第 2 批只实现读取侧，不包含浏览器、P4 写入或构建提交协议。

| 批 | 内容 | 验证范围 |
|---|---|---|
| 1（已完成离线） | core；纯函数报告解析；watch/fetch；固定页面序列 Submitter 桩 | Python 3.10 离线测试、合成夹具、CLI 回放 |
| 1.1（已完成离线） | 真实格式兼容、执行状态、其它扩展错误、构建机验收脚本 | 78 项测试、真实配置加载、脚本离线回放 |
| 2（已完成离线） | HTTP 读取、状态拆分、只读 tick/loop、A～E 验收脚本 | 100 项测试、三条 import 约束、本地 HTTP 模拟、真实配置加载 |
| 后续 | 构建机按完整提交号运行第 2 批 A～E；第 3 批按新任务实施 | 第 2 批真实网络尚未验收；P4/浏览器/提交协议未实现 |

## 4. 当前进度

2026-10-24 第 2 批读取侧实现与离线验收完成，基点 `8ca13b3fd37d53af6dbc5c084e976bfc5bc78843`。新增对账失败与独立包覆盖、修正 arm-only links 验收、HTTP ReportReader 和只读 workflow、构建机 A～E 验收脚本。B2-Q01 按人工裁决实现并闭合，HLD 未改。100 项测试、三条 import 约束及三个 SKILL 校验通过；127.0.0.1 A～E 小规模回放 PASS，2 条合成失败日志只下载一次、导出 1 块。实现、证据与本 STATUS 同批提交；完整索引：`docs/enhance/batch2/DELIVERY.md`。真实服务未访问，构建机 A～E 验收待执行。

设计方本次反馈：第 1.1 批脚本已在构建机用保存页面运行，计数、报告头、执行状态、arm 2244 行输入多重集合与路径集合、270 个扩展错误组、其它格式 0 条及源文件不变均已核实。唯一 FAIL 是 links.txt 仅含 arm 的 6 个失败包而脚本比较了两架构 7 个；设计方确认 x86 的额外失败包解析正确，属于上一批验收说明口径错误，第 2 批按 arm 单架构独立基线修正。此为用户提供的验收反馈，本机未访问真实网络。

2026-10-24：第 1.1 批离线修复完成。五份输入已核对归位；v0.5/v0.5.1 未跟踪副本已删除，v0.2 保留。真实汇总与报告头格式、首个详情页 title 判读、其它格式扩展错误人工确认已实现；78 项测试与两条 import 约束通过，真实 config.json 本地加载通过，verify_b1_real.sh 小规模离线回放 PASS。实现、设计依据、两份真实片段、证据和本文件同批提交；仅普通 push。完整索引：`docs/enhance/batch1.1/DELIVERY.md`。

2026-10-24：第 1 批离线实现完成；55 项测试通过，本线两条 import 约束通过；两个 SKILL.md 校验通过。实现、测试证据与本文件同批提交。完整交付索引见 `docs/enhance/batch1/DELIVERY.md`。

未访问内网、Cosmos 或浏览器，未执行 P4 操作或真实构建提交。第 1.1 批收到的两份 head120 是格式参照，完整真实报告及 2244/43 独立基线验收仍未执行，不能用合成测试替代。

## 5. 已闭合结论（附证据路径）

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

来源：设计方 2026-10-24 对 B2-Q01 的答复。实例锁使用 flock，覆盖 loop 全生命周期（包含睡眠），第二个 loop 获取失败退出 6，退出/崩溃由内核释放，不另写锁文件清理逻辑。轮次操作锁和 SQLite 写事务仅在 tick 必要阶段持有，睡眠前释放；手工 watch/fetch/workflow tick 不获取实例锁，睡眠期间可正常执行。loop 醒来读取最新事件，避免重复下载和重复待办。新增对应并发测试。HLD 不改，以此裁定为准。

2026-10-22：

- 本线放在独立分支 `vd-cosmos-loganalyzer`，不进 main。
- 仓库公开，提交内容不含内网信息，具体值只放构建机配置。
- Demo 目标周五，至少完成能力 1 和 2。

2026-10-24 第 1.1 批：按 v0.5.2 和专门任务修复本线既有代码；原始报告片段和设计文档纳入提交，环境真实配置只作本地加载、不提交。HLD §0.3 开发期内部名称/路径可入仓库，仅告警；凭据仍拦截。

2026-10-24：按 HLD v0.5.1 继续第 1 批；B1-Q01/B1-Q02 是确定契约，无需再次等待。仅离线实现，不开展真实读取或外部写操作；Git 收尾使用普通 push，禁止 force push。

## 7. 待确认事项

B1.1-Q01 及“对账失败是否单设”均已闭合。B2-Q01 已按设计方答复闭合：实例锁全生命周期持有，轮次锁及写事务睡眠前释放。第 1.1 批真实验收已收到设计方反馈；links.txt 已修为仅 armv7l 编译失败包，x86 只核失败数量自基线。后续待确认项按 HLD v0.5.3 §14。

## 8. 挂账

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
