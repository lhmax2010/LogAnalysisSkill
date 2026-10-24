# VD Cosmos 第 1 批：离线公共库与读取侧

运行代码只依赖 Python 3.10 标准库，适用于带 `flock`、GNU `stat` 的 Linux。无需安装本项目。watch/fetch 的入口把自己的包和本线 core 加入模块路径；不 import 已有 skill 的内部模块。

依据 HLD v0.5.1，以及 2026-10-24 的 B1-Q01、B1-Q02 裁定。三个状态和跨架构一致性分开；结果成功/失败不要求执行终态已证实。

## 离线运行

在仓库根目录：

```bash
python3 vd-cosmos-watch/scripts/run.py observe --config vd-cosmos-core/config.sample.json --backend fixture --manifest fixtures/minimal/manifest.json
python3 vd-cosmos-fetch/scripts/run.py packages --config vd-cosmos-core/config.sample.json --backend fixture --manifest fixtures/minimal/manifest.json --arch armv7l
python3 vd-cosmos-fetch/scripts/run.py inputs --config vd-cosmos-core/config.sample.json --backend fixture --manifest fixtures/minimal/manifest.json
python3 vd-cosmos-fetch/scripts/run.py groups --config vd-cosmos-core/config.sample.json --backend fixture --manifest fixtures/minimal/manifest.json
python3 vd-cosmos-fetch/scripts/run.py logs --config vd-cosmos-core/config.sample.json --backend fixture --manifest fixtures/minimal/manifest.json
python3 vd-cosmos-core/scripts/run.py status --config vd-cosmos-core/config.sample.json
```

示例输入是合成数据。输出写到 `vd-cosmos-core/.runtime/demo-data/`。stdout 始终只有一个 JSON 对象，详细内容由 `artifact.path` 引用。`--help` 也返回 JSON。每次读取有独立 attempt 目录；先追加开始事件，产物原子写入后再追加结果事件。`--expected-event N` 可显式传入期望的库末尾事件编号。

`--backend real` 目前是 `SavedReportReader`：按真实报告格式解析已保存 HTML，无 HTTP 访问。网络抓取和真实日志下载未实现，后者明确返回“不支持”（退出码 6）。因此所有本批运行都是离线解析/回放，不代表内网验收。

## 配置项

`config.sample.json` 不含真实连接值。相对的 `data_root` 以 config 所在目录解析；P4 配置路径以 data_root 解析；manifest、词表等只读来源以 config 所在目录解析。全部输出路径解析符号链接后必须仍位于 data_root 内。

| 字段 | 必填与含义 |
|---|---|
| `data_root` | 必填；专用数据根。启动前用 `stat -f -c %T` 验证文件系统，用 `statvfs` 读取余量。NFS/CIFS/SMB、未知类型或检查失败均退出 6，检查前不创建输出。 |
| `cosmos.archs` | 必填；本轮期望架构，非空且无重复，不从已下载文件反推。 |
| `cosmos.regular_archs` | 必填；常规架构集合，必须包含 archs。用于判断本轮是否刻意只运行常规集合的真子集。 |
| `cosmos.report_markers.report` | 必填；报告识别文字，匹配忽略大小写和多余空白。 |
| `cosmos.report_markers.summary` | 必填；汇总表配置标记。计数读取还要求 Total/succeeded/Export Error/Expansion Error/Build Error 的完整字段结构。 |
| `cosmos.report_markers.expansion` | 必填；扩展错误明细标题前缀。 |
| `cosmos.report_markers.export` | 必填；已知 Export 明细标题前缀；非零 Export 无可识别明细时结构未知。 |
| `cosmos.detail_table_title_prefix` | 必填；编译明细标题前缀，默认兼容报告中的 Statis 拼法。匹配时归一化，产物保留原文。 |
| `cosmos.header_must_match` | 必填；至少含 profile、build_conf、base、product，可附加字段。 |
| `cosmos.status_source` | 必填，可为 null；启用时为 `{"kind":"detail_page","complete_markers":["BUILD_COMPLETE"]}`。所有标记都出现在保存详情页的可见文字时才记可信终态；不从报告汇总反推。 |
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
- `expected_packages` 每架构列出 `{arch,name,path}`。必须由冻结请求或上一轮完整报告提供，不能从本轮待检查明细生成。缺基线时只能记部分。本批没有请求生成器；调用者提供这个独立基线。
- `detail_page` 可选，保存的详情页路径。没有配置可信来源时不使用其中的终态字样。
- `previous_table_titles` 可选，上一轮原始表标题，变化写漂移待办。
- `logs` 为 `{key:{arch,name,path},path,sha256?}` 列表；仅 fixture 后端复制这些文件。摘要不符拒绝。
- `provides_evidence` 可选，每项为 `{key,source_kind,path,sha256}`。source_kind 为 spec 时只读取明确的 `Provides:` 行（不展开宏）；rpm_metadata 时文件内容为 `{"provides":["name >= version"]}`。必须先核对源文件完整摘要；没有来源证据或含未展开宏，不能作为确定阻塞。元数据应由上一轮成功构建的 rpm 提取，实际内网提取工具留后续批次。

manifest 引用的文件必须在其所在目录内，禁止通过 `..` 或符号链接越界。保存页面也先过凭据模式检查。解析器保留源行号与输入行；重复行不会在对账前去重。Export Error 的未知表不会按 fail 链接自行猜测为已支持结构。

## 状态契约

- 每架构报告完整才计算结果：全成功为成功；任意 Build/Expansion/Export Error 为失败。非完整为未知。
- 本轮任一期望架构未完整或 header 不一致，结果未知。全完整且 header 一致时，常规集合按任一失败/全成功汇总。本轮架构是常规集合的真子集时，汇总标部分，各架构结果仍完整保留。
- `header_consistency` 取一致/不一致/未核；不一致不会改写 report_state，但结果变未知并写待办。缺架构或报告头没读齐时未核。
- `terminal_prerequisite_met` 仅表示读取侧的终态前提：完整、一致、可信已结束、execution_kind=cosmos；它不是提交授权，也不检查下一批的处置/清单闸门。

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
