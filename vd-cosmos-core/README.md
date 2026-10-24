# VD Cosmos 读取侧（第 2.1 批）

依据 HLD v0.5.4 和第 2.1 批任务。运行代码只用 Python 3.10 标准库，适用于带 flock、GNU stat 的 Linux。测试只访问 127.0.0.1，不证明内网部署已通过。

## 命令

在仓库根目录运行；stdout 仅一个 JSON，详细内容由 artifact.path 指向文件。

```bash
python3 vd-cosmos-watch/scripts/run.py observe --config CONFIG --backend real --build-id N --expected-rows ROWS
python3 vd-cosmos-fetch/scripts/run.py packages --config CONFIG --backend real --build-id N --arch armv7l
python3 vd-cosmos-fetch/scripts/run.py inputs --config CONFIG --backend real --build-id N
python3 vd-cosmos-fetch/scripts/run.py groups --config CONFIG --backend real --build-id N
python3 vd-cosmos-fetch/scripts/run.py logs --config CONFIG --backend real --build-id N
python3 vd-cosmos-workflow/scripts/run.py tick --config CONFIG --build-id N
python3 vd-cosmos-workflow/scripts/run.py loop --config CONFIG --build-id N --max-ticks 10
python3 vd-cosmos-workflow/scripts/run.py status --config CONFIG --build-id N
python3 vd-cosmos-workflow/scripts/run.py inbox --config CONFIG
```

离线夹具使用 `--backend fixture --manifest FILE`；保存页面兼容 `--backend real --manifest FILE`（无 HTTP，下载不支持）。样例：`--config vd-cosmos-core/fixtures/minimal/config.json --backend fixture --manifest manifest.json`。HTTP 不需要 manifest，构建号只能是数字。watch/fetch 手工命令与 workflow 共用轮次锁及乐观并发。显式 `--expected-event N` 不重试。

退出码：0 成功；2 参数错误/人工命令没有终端；3 需人工处理；4 规则拒绝；5 抓取/后端失败；6 前置、锁或状态库冲突。watch observe 遇停止推进条件为 3；loop 保持低频观察，到结果已拉取、达到 max-ticks 或收到信号时退出。

## 配置

真实配置不进仓库。相对 data_root 以配置文件目录解析；P4 配置以 data_root 解析；只读输入、CA、词表以配置文件目录解析。输出经过符号链接解析后必须仍在 data_root 内。启动用 stat -f/statvfs 向上找到已有目录检查；NFS/CIFS/未知类型或检查失败退出 6，不为通过检查而创建构建机路径。

| 字段 | 含义 / 默认值 |
|---|---|
| data_root | 必填；本线专用本地数据目录 |
| cosmos.archs / regular_archs | 必填；本轮与常规架构集合，不从现有文件反推 |
| cosmos.report_markers | 必填；report/summary/expansion/export 的报告与表标题标记 |
| cosmos.detail_table_title_prefix | 必填；编译明细标题前缀，归一化匹配，保留原文 |
| cosmos.header_must_match | 必填；至少 profile/build_conf/base/product |
| cosmos.report_root / report_path_template | HTTP 必需；模板仅接受 last3/build_id/arch |
| cosmos.bucket_path_template / index_link_regex | 默认 b{last3}/、`^[0-9]+/$`；目录还须无 form/密码框 |
| cosmos.status_source | 可为 null；非空含 kind=detail_page、url_template、status_title_regex、terminal_words/running_words/queued_words，词表不交叉；旧 complete_markers 不支持 |
| status_source.identity_regex | 默认 `(?<![0-9]){build_id}(?![0-9])`，只允许 build_id 占位符；详情可见文字身份核对 |
| poll.interval_s | 必填；连续相同记录达到该时长才稳定 |
| poll.settle_s / stopped_interval_s | 默认 1800 / 600 秒；无可信终态的定型时长、停止推进后观察间隔 |
| poll.stall_polls / expected_hours | 默认 6 / 24；停滞次数、观察窗口预期小时数，超过 1.5 倍告警 |
| fetch.timeout_s / deadline_s | 默认 60 / 300 秒；单次读取空闲时限、覆盖连接/重定向/正文的总时限 |
| fetch.max_page_bytes / max_log_bytes | 默认 20 MiB / 200 MiB；页面超限拒绝，日志主动截断并标记 |
| fetch.log_concurrency / user_agent | 默认 4 / VD-Cosmos-LogAnalyzer/0.5.3；日志并发上限与固定 User-Agent |
| network.proxy / no_proxy_hosts | 显式代理、域名后缀或字面 IP 网段直连；忽略环境代理 |
| network.ca_file | 可选，叠加系统信任库；始终校验证书与主机名，HTTPS 代理走 CONNECT |
| export.allow_types / chunk_bytes | 必填；材料白名单与 UTF-8 分块字节上限（至少 4），超长单行也分块 |
| prepush.words_file / credential_patterns | 词表可选且只告警；凭据正则必填，命中阻断导出。仅 prepush 接受已批准的行内样例豁免 |
| p4.config_file / env | 配置文件必须在 data_root 内；连接环境只允许 P4PORT/P4USER/P4CLIENT/P4CHARSET。本批仍只生成调用计划 |
| budget.disk_warning_bytes | 默认 0；每次实时 statvfs，低于阈值写待办 |

新增配置都有默认值；构建机原配置可直接加载，见本批 real-config-load.json。

## 抓取、定型与覆盖

报告、目录、详情一律不跟随 3xx。日志逐跳检查同协议、主机、有效端口与解码规范化后的构建/架构目录，最多 3 跳，越界不发请求。每个请求带 no-cache、Pragma、User-Agent，不保存或回传 cookie；留状态、日期/修改时间/ETag、长度、实际字节数、摘要及起止时间。失败只记录固定类别和 HTTP 状态。

Content-Length 必须相等，chunked 必须正常结束。不完整传输不落盘或更新缓存；主动超限截断明确标 truncated=true、transfer_complete=false。日志缓存同时绑定报告摘要和截断上限，变更后重新下载；内容摘要损坏也重新下载。凭据命中日志仍留本地，标“禁止导出”。

instance_id 是报告根的协议、主机、有效端口和规范路径。页面、连续相同记录、日志及 workflow 统一存 `rounds/<build_ref 摘要>/`。旧 `rounds/<构建号>/` 不读、不迁移、不删除。

每架构维护连续相同记录：摘要、first_seen_at、last_seen_at、count、解析配置版本。内容变化、404、失败、解析配置变化或时间倒退均重置。审计历史保留 50 条；页面按完整 sha256 去重。稳定且有可信“已结束”，或持续达到 settle_s，才定型。未定型一律部分；定型后依次判断结构未知、缺头/汇总的对账失败、内部对账失败、完整。只有全部架构定型才核对 header。

包覆盖与结果独立。比对单元是路径/CL/shelve 三元组多重集合，只在定型后计算；缺少/多出排序各最多 20 条。coverage_basis 本批为 manual_file 或 none，数据结构预留 request/previous_report 和“人工接受”。手工文件不一致停止推进，但报告结果仍按成功/失败推导；manual_file 一致不满足起轮闸门。accept-coverage 留第 3 批实现。

详情在内存判读，不保存原文。验证可见构建号后选首个 Build is 状态元素，保留最多 20 个候选和所选元素属性、身份结果、规则版本、响应证据；命中凭据的字段记“未保留”。详情失败使执行状态未知，报告照常判定；连续三次写独立待办，恢复清零，不复用旧终态。报告失败时仍保留本次成功详情证据。

## 状态库与恢复

SQLite 只追加 events，WAL、busy_timeout=2000。追加用 BEGIN IMMEDIATE 和期望上一事件编号，错误分 stale_head/state_busy/constraint/corrupt。events 可按构建 SQL 过滤；投影只加载最新观察和日志产物，缺失/摘要错误视为没有、写待办后重新观察。

tick：意图→一个动作→原子产物→唯一结果。下一 tick 只清理有意图无结果的本线 attempt 目录。日志阶段先重观测，报告指纹改变则保存观察结果、不下载。完成事件绑定报告摘要、基线摘要、解析配置摘要及解析器版本；任何评估标识变化都会使旧完成状态失效。

仅 loop 驱动的追加可重试 stale_head/state_busy，最多三次；新事件必须属于其它构建且不是人工/外部写类。仅重试追加，不重做动作。显式 expected-event、同构建新事件、constraint/corrupt 不重试。

实例 flock 跨整个 loop 生命周期；轮次锁与写事务不跨睡眠。轮次忙则内存计数跳过，成功清零；连续三次退出 6 并写 loop_contention，库不可写时返回结构化错误。SIGTERM/SIGINT 让当前 tick 完成后退出，内核释放锁，不删除锁文件。

停止条件为定型后的结构/对账错误、header 不一致、request/manual_file 覆盖不一致。停止推进后只低频观察，报告变化写“依据已变化”待办并重判。正常 404 等待不算停滞；超时以本地观察窗口衡量，不宣称服务器构建耗时。待办按构建/架构/原因/依据版本去重，样本与磁盘字节数只入正文。

## 夹具、测试与验收

manifest 保存两次以上报告的路径、观测时间、HTTP 状态和可选来源地址。expected_packages 的每项须包含 path/cl/shelve（三元组基线），可附 arch/name；不是从待核对的报告推导。fixture 日志和 Provides 元数据需要对应文件及摘要。其它格式扩展错误仍要求人工确认；未知 Export Error 表不猜测。

```bash
vd-cosmos-core/scripts/run_tests.sh
```

脚本使用本线 .importlinter，检查 Python 3.10/标准库、workflow→watch/fetch→core 依赖、watch/fetch 独立及 workflow 不依赖写后端。开发工具 import-linter 2.3 位于本线忽略的 .devtools；不改根 CI 或依赖。TLS 测试用 openssl 在临时目录生成证书，缺 openssl 则明确跳过，私钥不提交。

B1 保存页面脚本仍复用独立 rows/arm-only links 核对。B2 脚本首先核对完整提交和四个本线目录干净；Python 入口也检查，real 模式拒绝 loopback/localhost/.invalid。每次在原 data_root/verification/run_id/data 建立全新运行目录，原配置不变。A 页面摘要不同即失败；B 必须新下载、传输完整、不截断、非 HTML 登录/代理页且摘要重算相符；C 保存页核对；D 可选 live 构建只记录；E 本次必须完成 observe/logs/notify 三步且复用 B 日志；F 只记录目录指纹、详情身份、3xx 状态和去查询串的跳转目的地。失败段不能被总结果掩盖。

```bash
bash --noprofile --norc vd-cosmos-core/scripts/verify_b2_real.sh EXPECTED_COMMIT \
  --config CONFIG --build-id N --saved-dir SAVED_DIRECTORY \
  --rows ROWS --links LINKS --live-build-id M
```

EXPECTED_COMMIT 必须由设计方审核，不能动态拿当前 HEAD 代填。保存目录含 report_armv7l.html、report_x86_64.html、probe_3bed7e8c.html。离线模拟增加 `--mode fixture --fixture-counts FILE`，在干净的临时源码快照验证；来源记录明确标注 http-fixture，不能冒充实机验收。所有结果均在数据根目录，导出前仍执行凭据检查。完整分组成员只留本地，外传摘要目标不超过两块。
