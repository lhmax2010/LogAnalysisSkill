# VD Cosmos 第 2 批：公共库与读取侧

运行代码只依赖 Python 3.10 标准库，适用于带 `flock`、GNU `stat` 的 Linux。无需安装本项目。watch/fetch 的入口把自己的包和本线 core 加入模块路径；不 import 已有 skill 的内部模块。

依据 HLD v0.5.3，以及 2026-10-24 的 B1-Q01、B1-Q02、B2-Q01 裁定。执行、报告、结果状态与报告头/包集合一致性分别记录；结果成功/失败不要求执行终态已证实。

## 离线运行

在仓库根目录：

```bash
python3 vd-cosmos-watch/scripts/run.py observe --config vd-cosmos-core/fixtures/minimal/config.json --backend fixture --manifest manifest.json
python3 vd-cosmos-fetch/scripts/run.py packages --config vd-cosmos-core/fixtures/minimal/config.json --backend fixture --manifest manifest.json --arch armv7l
python3 vd-cosmos-fetch/scripts/run.py inputs --config vd-cosmos-core/fixtures/minimal/config.json --backend fixture --manifest manifest.json
python3 vd-cosmos-fetch/scripts/run.py groups --config vd-cosmos-core/fixtures/minimal/config.json --backend fixture --manifest manifest.json
python3 vd-cosmos-fetch/scripts/run.py logs --config vd-cosmos-core/fixtures/minimal/config.json --backend fixture --manifest manifest.json
python3 vd-cosmos-core/scripts/run.py status --config vd-cosmos-core/config.sample.json
```

示例输入是合成数据。minimal 输出写到 `vd-cosmos-core/.runtime/minimal-data/`，配置样例默认写到 `.runtime/demo-data/`。stdout 始终只有一个 JSON 对象，详细内容由 `artifact.path` 引用。`--help` 也返回 JSON。每次读取有独立 attempt 目录；先追加开始事件，产物原子写入后再追加结果事件。`--expected-event N` 可显式传入期望的库末尾事件编号。

`--backend real --build-id N [--expected-rows FILE]` 使用标准库 HTTPReportReader，不需要 manifest；expected-rows 只用于 armv7l。兼容原来的 `--backend real --manifest FILE` 保存页面解析，其日志下载仍明确返回“不支持”。本批测试只访问 127.0.0.1 上的 HTTP 夹具，不代表内网验收。

## 配置项

`config.sample.json` 不含真实连接值。相对的 `data_root` 以 config 所在目录解析；P4 配置路径以 data_root 解析；manifest、词表等只读来源以 config 所在目录解析。全部输出路径解析符号链接后必须仍位于 data_root 内。

| 字段 | 必填与含义 |
|---|---|
| `data_root` | 必填；专用数据根。启动前用 `stat -f -c %T` 验证文件系统，用 `statvfs` 读取余量。NFS/CIFS/SMB、未知类型或检查失败均退出 6，检查前不创建输出。 |
| `cosmos.archs` | 必填；本轮期望架构，非空且无重复，不从已下载文件反推。 |
| `cosmos.regular_archs` | 必填；常规架构集合，必须包含 archs。用于判断本轮是否刻意只运行常规集合的真子集。 |
| `cosmos.report_markers.report` | 必填；报告识别文字，匹配忽略大小写和多余空白。 |
| `cosmos.report_markers.summary` | 必填；汇总标题前缀，真实值为 Build Status Summary。列名归一化后去掉末尾 Packages，再匹配 Total/succeeded/Export Error/Expansion Error/Build Error；旧的无后缀列名仍可解析。 |
| `cosmos.report_markers.expansion` | 必填；扩展错误明细标题前缀。 |
| `cosmos.report_markers.export` | 必填；暂用 Export error details；真实 Export 表首次出现时须核实标题和列结构。非零 Export 无可识别明细时结构未知。 |
| `cosmos.detail_table_title_prefix` | 必填；编译明细标题前缀，默认兼容报告中的 Statis 拼法。匹配时归一化，产物保留原文。 |
| `cosmos.header_must_match` | 必填；至少含 profile、build_conf、base、product，可附加字段。 |
| `cosmos.status_source` | 必填，可为 null；非空时必须包含 kind=detail_page、url_template、status_title_regex（恰有一个捕获组）、terminal_words、running_words、queued_words。三个非空词表归一化后不得重复或交叉；url_template 为无内嵌凭据的 HTTP(S) 地址，只允许 build_id 占位符。旧 complete_markers 结构拒绝。 |
| `cosmos.report_root` / `report_path_template` | HTTP 后端必需；根地址与相对模板拼接，模板只接受 last3/build_id/arch，占位符带花括号；构建号只能是数字。 |
| `cosmos.bucket_path_template` | 可选，默认 b{last3}/；只接受 last3/build_id，用于报告 404 后验证目录索引。 |
| `network.proxy` / `no_proxy_hosts` | 可选；只采用配置，忽略环境代理。主机匹配域名后缀或字面 IP 网段时直连，其余走 proxy；未配置 proxy 时直连。 |
| `network.ca_file` | 可选，按配置目录解析；额外加载 CA，保留系统默认信任库和主机名/证书校验。 |
| `fetch.timeout_s` | 可选，默认 60 秒，请求超时。fetch 整段可省略。 |
| `fetch.max_page_bytes` / `max_log_bytes` | 可选，默认 20 MiB / 200 MiB。页面超过上限失败；日志只保留上限内字节并标记截断。 |
| `fetch.log_concurrency` / `user_agent` | 可选，默认 4 / VD-Cosmos-LogAnalyzer/0.5.3。并发日志下载上限和每次请求的 User-Agent。 |
| `poll.interval_s` | 必填，正数；两份报告观测时间至少间隔这么多秒，且原始字节 sha256 相等才稳定。 |
| `poll.stall_polls` | 可选，默认 6，至少 2；不同观测时刻连续内容不变且仍未完整时写待办，不改变构建状态。 |
| `poll.expected_hours` | 可选，默认 24；本地已记录观察窗口超过此值的 1.5 倍时提醒。未实现可信服务器开始时间换算，不能据此宣称构建已超时。 |
| `export.allow_types` | 必填；report/log/results/summary/verification 的非空子集。 |
| `export.chunk_bytes` | 必填，至少 4；每块 UTF-8 字节上限，优先换行切分，超长行在字符边界切分。 |
| `prepush.words_file` | 可选；本地逐行词表，命中仅告警；不把命中内容复制到诊断输出。 |
| `prepush.credential_patterns` | 必填，非空正则列表；配置样例包含 HLD 指定的凭据模式。命中只报告模式编号和行号，不回显内容。 |
| `p4.config_file` | 必填；必须解析到 data_root 内，给子进程的 P4CONFIG 使用。当前不读取文件内容，也不运行 P4。 |
| `p4.env` | 可选；仅允许 P4PORT/P4USER/P4CLIENT/P4CHARSET，以子进程环境传入。样例为空。继承的 P4 变量先清除。 |
| `budget.disk_warning_bytes` | 可选，默认 0；低于阈值写待办，报告事实而不跳过步骤。其余资源调度留后续批次。 |

## 保存页面的 manifest

见 `fixtures/minimal/manifest.json`。`schema_version=1`；build_ref 由 backend_id、instance_id、run_id、execution_kind 组成，最后一项只接受 cosmos/local_simulation。

- `reports` 按架构列出时间有序的抓取记录：path、带时区的 observed_at、status_code，以及可选的 source_url、error。最近两条成功记录用于稳定性判断，示例使用两份独立文件。明确 404 还需 host_ok=true；网络错误/代理页/登录页/不可解析响应记观察失败，不能变成“未发布”或终态。失败观察退出 5，连续三次才记相应待办。
- `expected_packages` 每架构列出 `{arch,name,path}`。必须由冻结请求或上一轮完整报告提供，不能从本轮待检查明细生成。缺基线时 package_coverage=未核，不影响报告完整性或结果；格式错误退出 2。
- `detail_page` 可选，保存的详情页路径。没有配置可信来源时不使用其中的终态字样。
- `previous_table_titles` 可选，上一轮原始表标题，变化保留漂移 issue；正常变化不另写人工待办。
- `logs` 为 `{key:{arch,name,path},path,sha256?}` 列表；仅 fixture 后端复制这些文件。摘要不符拒绝。
- `provides_evidence` 可选，每项为 `{key,source_kind,path,sha256}`。source_kind 为 spec 时只读取明确的 `Provides:` 行（不展开宏）；rpm_metadata 时文件内容为 `{"provides":["name >= version"]}`。必须先核对源文件完整摘要；没有来源证据或含未展开宏，不能作为确定阻塞。元数据应由上一轮成功构建的 rpm 提取，实际内网提取工具留后续批次。

manifest 引用的文件必须在其所在目录内，禁止通过 `..` 或符号链接越界。保存页面也先过凭据模式检查。解析器保留源行号与输入行；重复行不会在对账前去重。Export Error 的未知表不会按 fail 链接自行猜测为已支持结构。

## 状态契约

- 每架构报告完整才计算结果：全成功为成功；任意 Build/Expansion/Export Error 为失败。非完整为未知。
- report_state 按结构未知、部分（未稳定/缺头/缺汇总）、对账失败、完整判定。稳定后的计数不符、重复包键、分类交叉和架构不符是对账失败；未稳定时仍为部分。
- package_coverage 独立表示一致/不一致/未核，汇总优先级为不一致、未核、一致。不一致使结果未知并写缺少/多出各最多 20 条待办；未核不影响结果。
- 本轮任一期望架构未完整或 header 不一致，结果未知。全完整且 header 一致时，常规集合按任一失败/全成功汇总。本轮架构是常规集合的真子集时，汇总标部分，各架构结果仍完整保留。
- `header_consistency` 取一致/不一致/未核；不一致不会改写 report_state，但结果变未知并写待办。缺架构或报告头没读齐时未核。
- `terminal_prerequisite_met` 仅表示读取侧的终态前提：完整、header 和 package_coverage 一致、可信已结束、execution_kind=cosmos；它不是提交授权，也不检查下一批的处置/清单闸门。

详情页仅选文档顺序上首个 `title="Build is …"` 元素，然后按配置正则捕获状态词。successful/failed/cancelled/timed out/timeout 为已结束，running 为运行，queued/waiting 为排队；同时保存 subresult、title、行号、元素顺序、源文件摘要。首个元素未知或不匹配时不会向后寻找推广构建状态；可见文字和样式本身不作为证据。没有可信终态时，报告完整也只是终态推定。

扩展错误除标准 nothing provides 消息外，原文仅归一化空白后保留在 missing_dependencies 和 other_expansion_messages；对应分组标“其它格式”、requires_manual_confirmation=true，写待办且不影响结构完整性。这类签名即使与 Provides 精确相等也不能自动覆盖；须显式人工确认。未知格式与标准格式出现相同签名时，整个组保守地要求人工确认。

## 事件库、锁与权限门

`state/state.db` 只有追加的 events 表。SQLite 触发器拒绝 UPDATE/DELETE；每次写都用 BEGIN IMMEDIATE，并以 expected_previous 校验全库最后事件号。冲突、数据库占用和唯一约束冲突均退出 6。

click_intent 按 request_id 唯一，bind 按完整 build_ref 唯一。进行中的 submit_session_started 用 SQL 触发器约束：没有匹配的 submit_session_finished 就不能再开准备；结束事件必须引用真实的活动 operation_id。失败准备结束后可开新操作；有 click_intent 后不能重开。同一数据库事务保证并发写者不能绕过约束。浏览器 profile/轮次另用 flock，非阻塞；锁文件不删，进程退出由内核释放锁。

`commands.py` 登记五类命令和事件白名单。接收结果只允许 analysis_received/analysis_rejected；授权事件被拒绝（4）。人工/外部写类须打开 /dev/tty 并输入 yes；没有终端退出 2，未确认退出 3。本批只有门和声明，没有这些操作的实现；有终端确认后仍返回不支持。它们不列入两个 SKILL.md。

这些门防误用，不隔离同一操作系统账号内的恶意代码。没有实现浏览器进程、后续写操作协议或人工确认流程。

## 导出与 P4 桩

```bash
python3 vd-cosmos-core/scripts/run.py export --config vd-cosmos-core/config.sample.json --source reports/example.txt --type report --name example
python3 vd-cosmos-core/scripts/run.py prepush --config vd-cosmos-core/config.sample.json --files /absolute/path/to/file
```

导出先检查完整内容，再创建 bundle；任一凭据命中则不创建任何导出物。输出清单记录顺序、块数、每块大小/完整 sha256，以及原文大小/摘要。认证输入页、浏览器和运行敏感目录、配置文件不能借 report 标签导出。仅 prepush 允许 HLD 的行内 `# credential-test-sample` 测试示例豁免；导出不接受该豁免。

P4Adapter 只生成 subprocess 的 argv/env/cwd 计划，不执行。连接信息只能通过环境传入，禁用持久配置、登录、提交和 client 修改；只读命令也只有计划功能。FixtureSubmitter/ScriptedDriver 仅回放固定页面序列，支持成功、拒绝、登录、未知和可注入崩溃，不启动浏览器，不替代完整提交协议。

## 测试

```bash
vd-cosmos-core/scripts/run_tests.sh
```

测试使用 unittest，临时文件限定在 `.runtime/`。脚本运行 Python 3.10 语法/标准库导入检查及本线 `.importlinter`；不读取根目录 import 配置，不改根 CI。

import-linter 是仓库 pyproject.toml 已有的开发工具（固定 2.3），不是运行时依赖。若当前环境没有，可放到本线忽略目录中，既不安装本项目也不更改全局环境：

```bash
mkdir -p vd-cosmos-core/.runtime
TMPDIR="$PWD/vd-cosmos-core/.runtime" PIP_CACHE_DIR="$PWD/vd-cosmos-core/.runtime/pip-cache" python3 -m pip install --target "$PWD/vd-cosmos-core/.devtools" 'import-linter==2.3'
```

已有该工具后测试本身不联网。测试覆盖 CLI 退出码、并发/唯一性、导出拒绝、对账反例、三状态裁定、分组及假浏览器回放。合成的 2244/43 包规模测试只验证算法规模与给定计数，不能代替真实报告验收。

## 第 1.1 批保存文件验收

`fixtures/real_format/` 保留两份真实片段的报告头与汇总表布局（仅缩小计数），补完小规模明细。它是合成夹具，不能替代构建机完整报告的真实验收。原始 head120 片段保持不变，不视为完整报告。minimal 夹具仍使用其新增的独立配置（summary=Summary）。

脚本首先输出本地完整 HEAD，和第一个参数逐字比较；不相等以 6 退出，不加载配置或写结果。后续输出文件都在 data_root/verification/ 新建目录，stdout 最后一个 JSON 给出结果文件及 export 分块清单。成功为 0，比对失败为 6，参数/基线格式错误为 2，凭据拦截为 4，读文件失败为 5。失败结果也保留并经过相同导出检查。

构建机示例（先把 EXPECTED_COMMIT 替换为设计方审核的完整提交号，CONFIG 替换为配置文件路径；不能用当前 HEAD 动态代替审核值）：

```bash
bash --noprofile --norc vd-cosmos-core/scripts/verify_b1_real.sh EXPECTED_COMMIT \
  --config CONFIG --run-id 19091860 \
  --arm-report /home1/chengkai/vd-cosmos/recon2/pages/report_armv7l.html \
  --x86-report /home1/chengkai/vd-cosmos/recon2/pages/report_x86_64.html \
  --detail-page /home1/chengkai/vd-cosmos/recon2/pages/probe_3bed7e8c.html \
  --rows /home1/chengkai/vd-tree/workspace/quickbuild/b860_19091860/rows.txt \
  --links /home1/chengkai/vd-tree/workspace/quickbuild/b860_19091860/links.txt
```

源路径全部参数化；没有网络访问或对源树的写操作。复制前检查凭据模式，复制后核对源文件和副本摘要。两次副本的时间差为 poll.interval_s+1，输出明确标注稳定性是模拟，不能证明源站两次实际抓取稳定。真实模式固定检查 armv7l 2244/1479/0/759/6、x86_64 43/42/0/0/1，不允许覆盖计数。

rows.txt 的独立解析器与 HTML 解析器分开：对 (路径,CL,shelve) 做多重集合比对，不去重；arm 包名来自报告，包覆盖必须一致。links.txt 只对 arm 编译失败包的 (包名,包名-版本-发布号,路径,CL,shelve) 做多重集合比对。x86 包集合未核，失败包数仅与汇总 Build Error + Export Error 比较并标“自基线”。差异最多展示前 20 条，同时给出完整差异数量。

离线模拟将上面五个源路径改为 `vd-cosmos-core/fixtures/real_format/` 对应文件（report_armv7l.html、report_x86_64.html、detail.html、rows.txt、links.txt），run-id 改为 fixture-run，并增加：

```text
--mode fixture --fixture-counts vd-cosmos-core/fixtures/real_format/expected-counts.json
```

模拟仍需完整预期提交号和有效配置；可用 config.sample.json。输出固定标记“离线小规模夹具，不是真实验收”，build_ref.execution_kind=local_simulation。结果文件含全部核对、状态、依据、待办、签名前 15 组、其它格式消息数量与前 10 条；完整 observe/packages/inputs/groups 另存同目录。结果经已有 export_file 流程分块，逐块大小和完整 SHA256 在清单中。

## 第 2 批 HTTP 与只读 workflow

HTTP 请求显式带 no-cache、Pragma、User-Agent；忽略环境代理，不保存/回传 cookie，跨主机重定向拒绝，同主机最多 3 次。报告页先过凭据检查，再原子存到 `rounds/<build_id>/pages/<arch>/`；稳定性使用本线记录的时间和摘要，不使用 mtime。详情页原文不落盘，只留状态元素 title 原文、行号、元素序号、页面摘要、时间、HTTP 状态与保留说明。

日志仅接受与报告同源、在该报告目录下的地址，存入 `rounds/<build_id>/logs/<arch>/<nvr>/log.txt`。同时记录大小、完整 SHA256、截断与导出资格；已有文件及元数据摘要相符时不重新下载。命中凭据的日志只存本地，导出流程仍会阻断它。

```bash
python3 vd-cosmos-watch/scripts/run.py observe --config CONFIG --backend real --build-id N --expected-rows ROWS
python3 vd-cosmos-fetch/scripts/run.py logs --config CONFIG --backend real --build-id N
python3 vd-cosmos-workflow/scripts/run.py tick --config CONFIG --build-id N --expected-rows ROWS
python3 vd-cosmos-workflow/scripts/run.py loop --config CONFIG --build-id N --max-ticks 4 --expected-rows ROWS
python3 vd-cosmos-workflow/scripts/run.py status --config CONFIG --build-id N
python3 vd-cosmos-workflow/scripts/run.py inbox --config CONFIG
```

workflow 仅通过 watch/fetch 公开函数读取；每个 tick 执行观察、下载日志、写分析待办三个阶段之一，先落意图、动作后落唯一结果。完整报告、header 一致、包覆盖非不一致时下载，不要求执行已结束。对账失败/结构未知/header 不一致/覆盖不一致退出 3；观察失败退出 5，loop 下一 tick 重试，三次连续失败写待办。正常等待不写待办。完成后阶段为“结果已拉取”，同一轮重复 tick 不重复通知。

B2-Q01：实例 flock 覆盖 loop 全生命周期，含睡眠；第二个 loop 退出 6。轮次 flock 和 SQLite 写事务在 tick 必要阶段持有，睡眠前释放。手工 observe/logs/tick 只拿轮次锁，可在 loop 睡眠时执行；醒来重读事件。锁冲突和乐观并发冲突仍退出 6。信号只请求停止，当前 tick 完成后退出，内核释放文件锁；没有锁文件清理逻辑。status/inbox 不追加事件。

验收脚本先核对完整提交号，所有产物只写 data_root：

```bash
bash --noprofile --norc vd-cosmos-core/scripts/verify_b2_real.sh EXPECTED_COMMIT \
  --config CONFIG --build-id N --saved-dir SAVED_DIRECTORY \
  --rows ROWS --links LINKS --live-build-id M
```

保存目录应含 `report_armv7l.html`、`report_x86_64.html`、`probe_3bed7e8c.html`。A：两次 HTTP 读取、与保存页摘要比较及独立基线核对；B：失败日志；C：复用 B1 保存页面验收；D：可选进行中构建，只观察不下载；E：loop 最多 4 次 tick、核验日志复用与唯一分析待办。D 仅如实记录，不影响 PASS。真实模式预期固定为两架构 2244/43 包、6/1 失败日志。

结果摘要仅保留扩展错误前 15 组的签名与成员数量，不包含成员清单；完整明细在 verification 目录。stdout 最后 JSON 给出结果文件、导出清单和是否达到两块目标。离线 HTTP 模拟额外带 `--mode fixture --fixture-counts FILE`，必须明确标注合成规模；不会据此声明真实网络验收通过。
