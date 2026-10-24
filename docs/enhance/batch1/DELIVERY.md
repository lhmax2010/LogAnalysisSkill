# 第 1 批交付与证据索引

日期：2026-10-24。分支：`vd-cosmos-loganalyzer`。依据：FatTank 的第 1 批任务、B1-Q01/B1-Q02 裁定及随后提供的 HLD v0.5.1。本批只实施离线读取与公共库基础；没有访问内网、Cosmos、P4 或浏览器。

## 核验入口

- 完整文件清单：`docs/enhance/batch1/changed-files.txt`。
- 全量测试命令：`vd-cosmos-core/scripts/run_tests.sh`。
- 完整输出：`docs/enhance/batch1/evidence/test-output.txt`。
- 输出 SHA-256：`aae750cf794adbfa482283b2b82aa74817197b4c8650472d198a6b5422754a76`，另存 `evidence/test-output.sha256`。
- 结果：Python 3.10.12；55 项 unittest 通过；2 条 import-linter 契约通过；Python 3.10 语法与标准库导入白名单检查通过。
- 六次实际 CLI 离线回放的命令、退出码、stdout 和产物位置：`evidence/cli-transcript.json`。对应详细结果为 `01-watch-observe.json` 至 `06-watch-observe.json`。
- 两个 SKILL.md 的系统校验输出：`evidence/skill-validation.txt`。
- 实现与夹具的内容摘要：`evidence/source-sha256.json`。
- 提交内容的两级检查：`evidence/prepush.json`；显式标注的凭据测试样例按 HLD 豁免，导出路径仍拒绝这些样例。
- 根目录原有文件与其他会话修改的前后摘要：`evidence/protected-files.json`；10 个受保护文件均未变化。

## 逐项交付

下表路径相对仓库根目录；公共库模块位于 `vd-cosmos-core/src/vd_cosmos_core/`。

| 任务项 | 实现与范围 | 可核验位置 |
|---|---|---|
| A 配置与路径 | 必填项/类型/重复 JSON 键校验；相对路径解析；输出真实路径限制；stat -f + statvfs；NFS/CIFS/SMB 与检查失败退出 6 | `config.py`、`files.py`；配置逐项说明在 `vd-cosmos-core/README.md`；`test_foundation.py` 的 config/filesystem/path 测试 |
| A SQLite 事件库 | 只追加；UPDATE/DELETE 拒绝；BEGIN IMMEDIATE；expected_previous；活动准备、click、bind 的数据库约束 | `state.py`；`test_foundation.py` 的 optimistic/session/bind/journal 测试 |
| A flock | profile 和 round 两种非阻塞锁；冲突退出 6，进程结束释放；不删除锁 inode | `locks.py`；跨进程竞争测试 |
| A 命令分类 | 五类能力表及事件白名单；接收结果只能写 received/rejected；人工/外部写类无 TTY 退出 2 | `commands.py`；foundation 与 CLI 正反例。仅门和声明，没有具体写命令 |
| A 数据模型 | build_ref 含 backend/instance/run/execution_kind；包键含架构/名称/路径，保留版本、CL、shelve、类别、URL、依赖与行号 | `models.py`、`report.py`；`02-fetch-packages.json` |
| A 后端接口 | ReportReader/Submitter ABC 与 capability 声明；SavedReportReader 只解析本地已保存页面；FixtureReportReader 可复制夹具日志 | `backends.py`；CLI 的 real 模式证据是合成页面解析，不是真实网络验证 |
| A 导出 | UTF-8 字节上限分块、超长行切分、清单/大小/完整摘要；词表告警，凭据命中不生成 bundle；禁止敏感目录和认证页 | `export.py`；foundation 的 UTF-8、末尾凭据、认证页和类型拒绝测试 |
| A P4 桩 | 只生成 argv/env/cwd；P4CONFIG 受限于数据根；继承 P4 环境清理；持久配置/登录/client 修改/提交拒绝 | `p4.py`；计划与拒绝测试。真实执行明确不支持 |
| B observe | 汇总/逐类数量、唯一包键、分类不交叉、独立期望集合、双输入摘要与时间间隔；结构未知不猜类别 | `report.py`、`backends.py`；duplicate/category/export/status/expected-set/stability 测试 |
| B 三状态裁定 | 每架构完整才算结果；任何非成功包算失败；部分仅用于刻意缩小架构集合；未知执行状态不影响完整报告结果 | `test_reports.py` 的 result/reduced/missing-architecture 测试；`01-watch-observe.json` |
| B header_consistency | 独立字段，不扩展 report_state；不一致时结果未知、写待办、不满足读取侧终态前提 | report 与 CLI 的 header mismatch 测试 |
| B packages/inputs | 归一化前缀匹配标题，保留原始标题和行号；报告头与全部可解析输入行 | `02-fetch-packages.json`、`03-fetch-inputs.json`；title/raw-line/input 测试 |
| C watch/fetch | 免安装入口；单 JSON stdout；文件产物；状态库记录开始/结果；失败三次待办、停滞提示；两个 SKILL.md 只列观察命令 | 三个 scripts/run.py；`test_cli.py`；六次 CLI 回放 |
| C 扩展错误分组 | 单缺失项签名、保留版本约束；多缺失项须全覆盖；摘要已验证的 Provides 精确匹配为确定阻塞；名字近似仅疑似；下游计数去重 | `groups.py`、`backends.py` 的 provides；`test_reports.py` 的 GroupTests；`04-fetch-groups.json` |
| C 日志 | fixture 日志复制与 sha256；真实下载返回不支持 | `05-fetch-logs.json`；saved-parser/downloader 与 CLI 测试 |
| D 假浏览器 | 固定序列的 prepare/release/discover/verify；成功、拒绝、登录、未知、崩溃回放；无真实浏览器 | `fake_browser.py`；BrowserFixtureTests。尚非完整提交协议 |

## 真实报告验收与留桩

`docs/enhance/` 当前没有提供真实 HTML/HTM 报告或归档夹具，见 `evidence/real-fixture-inventory.json`。因此真实 armv7l 2244/1479/0/759/6、x86_64 43/42/0/0/1 的验收**未运行**。测试中的对应规模是合成数据，仅验证计数/集合算法，不能声称真实报告已通过。

本批没有网络抓取、真实日志下载、P4 执行、真实浏览器、完整提交协议、分析者或 workflow loop。未提供版本信息时 version 为 null。时长告警目前根据本地已记录观察窗口，不声称已核实服务器构建耗时。

下一批先补两架构真实报告、独立期望包集合、双观测时间及可信详情页；然后核实真实结构、标题/版本提取与原型逐行对账。其余工作按新任务授权实施。两个状态契约问题均已闭合，无需重新裁定。

## 提交边界

仅新增三个顶层目录与本批文档/证据，更新既有 STATUS.md。用户提供的未跟踪 HLD 和原有其他文件修改不纳入本批。运行时临时文件与开发工具仅存放于被忽略的 `.runtime/`、`.devtools/`。沿用仓库已声明的 import-linter==2.3 开发工具；核心运行时没有新增第三方依赖，也没有修改根 pyproject.toml、.importlinter 或 CI。

Git 使用普通推送，无 force push、PR 或 tag；STATUS.md 与实现、证据在同一提交中。提交号以本文件所属提交及最终回报为准。
