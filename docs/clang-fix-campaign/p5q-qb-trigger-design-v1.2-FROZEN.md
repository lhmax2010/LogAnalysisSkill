# P5Q QuickBuild 复验触发与结果读取设计(v1.2-FROZEN)

- 阶段:Phase 5Q(安全阶段,三家评审)
- 上位文档:`docs/clang-fix-campaign/design.md` v1.5.21-FROZEN。本文只写 P5Q 的接口、行为与验收;
  与 design.md 冲突处以本文为准,冲突点全部列在附录 A,随 P5Q 第一个提交同步进 design.md(升 v1.5.22)。
- 输入基线:`origin/clang-fix-campaign` @ `26e9e3d`(P5 已 CLOSED @ `1f0ca30`;EF-5 只读取证与表单离线解析已完成)。
- v1.1 是第一轮评审(Kimi、ChatGPT、Claude Code)后的修订,修改与采纳来源见附录 D。
- v1.2 是第二轮(最后一轮)评审后的修订,修改与采纳来源见附录 E;两轮已用满。2026-10-10 FatTank 裁定第 0.5 节两项(参照团队 quickbuild-sbs 工具的做法),本版冻结。
- 凡写着"待实测"或"以只读取证确定"的地方,实现必须按"失败即停"处理,不得猜。

---

## 0. 范围、前提与本版裁定

### 0.1 已确认的事实、裁定与取证来源

design.md 原设计是"用 SBS 的 REST 接口提交、Basic Auth 鉴权"。EF-5 取证与 FatTank 裁定推翻了这个前提。
下表"来源"一列区分三类:**裁定**(FatTank 决定)、**RBS 取证**(本阶段流水线的实测)、**SBS 取证**(另一条流水线的实测,只作 RBS 的预期,须在第 9.4 节第 1 步用 RBS 构建验证,不符即停)。

| 事项 | 结论 | 来源 |
|---|---|---|
| REST 权限 | 不申请;REST 接口在本环境实测拒绝访问 | 裁定(2026-10-10);EF 报告历史 REST 实测 |
| 复验流水线 | **RBS/TRIGGER**,不是 SBS/TRIGGER;按包所属工程选 Tizen-Base-Toolchain 或 Tizen-Unified-Toolchain | 裁定 |
| 触发方式 | 配置页"运行"按钮(▶)先进入"Specify Build Options"表单页,点 Ok 才开跑 | RBS 取证(FatTank 截图;`rbs-form-01/form.json`) |
| 由谁填表 | 工具驱动独立浏览器窗口按标签填表、核对后点 Ok;不自己拼 HTTP 请求 | 裁定(理由见 0.2) |
| 登录 | 工具弹出浏览器窗口,FatTank 只在窗口里登录;工具自动检测登录完成,不需要回终端;会话只存在于浏览器与专用代理进程的内存中(可信边界见 0.5 第二项) | 裁定 |
| 表单字段与结构 | 十三个字段标签、双列表选择器三元素结构、Ok 为整表提交、Cancel 为 `ILinkListener-form-cancel` | RBS 取证(`rbs-form-01/`) |
| 目标写在哪 | 表单字段 Build Package List,格式 `仓库路径@commit`,一行一个 | RBS 取证(表单)+ 裁定 |
| 目标的回显变量 | SBS 父构建:显示名 Build Package List 对应变量 **`BUILD_PKG_LIST_MODIFY`**,另有 `BUILD_PKG_LIST` 同值;SBS 子构建:`BUILD_PKG_LIST` | SBS 取证(`web-cookie-02/facts.json`;`03.response.txt:804`);RBS 待验证 |
| 父子关系 | SBS 子构建变量 `TRIGGER_ID` 指回父构建;父构建页 Child Build 表链接子构建 | SBS 取证(`03.response.txt:804`、`06.response.txt:1189`);RBS 截图显示 Child Build 表存在,变量待验证 |
| 架构状态 | SBS 子构建三个架构合在一个构建里,只有一个总状态;`FAIL_FAST=yes`;`EACH_GBS_BUILD_STATUS` 在成功构建上为空 | SBS 取证(`03.response.txt:804`);RBS 待验证 |
| 通过判据 | **子构建 Status 精确等于 `Successful` 即通过**,不要求 SR_STATUS=ACCEPTED;`qb_pass_requires_accept` 默认 false,每个 campaign 冻结 | 裁定;文字形态来自 SBS 取证(`01.response.txt:832`) |
| 合入 | 合入正式快照必须有人点 Accept;**工具永远不点 Accept / Ready to Accept** | 裁定 |
| 推送 sandbox 分支是否自动开跑 | 不会;构建只由工具显式提交表单发起;P12 首次真实推送后观察一次 | 裁定;团队 quickbuild-sandbox-branch 代码只有 `git push` |

### 0.2 为什么用浏览器填表,而不是拼 HTTP 请求

表单离线解析显示:字段名按位置编号(QuickBuild 加减一个字段编号就错位);每个可编辑字段改动时都回传服务器,表单状态一部分在服务器端,联动刷新哪些字段从保存页面看不出来;双列表真正提交的是页面脚本生成的隐藏"记录"字段;页面地址带每次不同的版本号。自己拼请求要把这些全部模拟对。让真实浏览器执行页面自己的脚本,工具只做"按标签找字段 → 设值 → 等联动结束 → 逐项读回核对",出错面小得多。

代价是浏览器会自己发出很多请求,所以第 3.4 节的请求拦截必须做到"每一跳都检查、只放行精确登记的地址"。

### 0.3 P5Q 范围

1. 浏览器代理 `qb_browser_agent`(Node + Playwright + 本机 Chromium + DevTools 协议拦截):登录检测、逐跳请求拦截、只读取页、填表核对与一次性提交(第 3 节)。
2. 复验参数配置与每个 campaign 的参数冻结(第 2 节)。
3. `qb-trigger` CLI(第 4 节)与 `qb-result-fetch` CLI(第 5 节)。
4. `campaign_state` 新增按连接写入的内部原语与 `qb_profile` 查询(第 6 节)。
5. 页面脱敏模块从 spike 移入正式代码(第 3.7 节)。

### 0.4 不在 P5Q

- review-submit(P5R)。P5Q 只保证 RESULT 事件与 qb_result 文件按本文契约产出、冻结参数入库,并在附录 A 中写定 P5R 必须遵守的读取规则(结果文件 schema、人工降级判据收紧)。
- 后台轮询。读取结果是按需一次性执行;一次执行只读当前状态,不等待。
- 真实 Gerrit 推送:第一次真实 sandbox push 仍按 EF-6 放在 P12。P5Q 的真实 QuickBuild 提交只用 FatTank 指定的已有提交(第 9.4 节第 2 步)。
- Tizen-Unified-Toolchain 的 RBS 表单尚未取证;该工程的配置项在取证前保持关闭。
- 除 Ok 提交外的一切 QuickBuild 操作(Accept、取消、停止、重跑、删除等)。
- 三架构以外的架构组合:本版 CHILD_CONFIGURATIONS 固定为 `standard-armv7l:aarch64:x86_64`,其它组合须走 R1 修订通过判据。

### 0.5 FatTank 裁定的两项(2026-10-10)

**第一项:复验基准快照——已裁定采用下述默认。** 表单的 BUILD_REFERENCE 有 Live / Ref. Snapshot / Snapshot Number 三种。三家评审一致支持本文默认;团队 quickbuild-sbs 工具提交时不改动 BUILD_REFERENCE 与快照字段,即沿用表单默认(RBS 表单默认正是 `Ref. Snapshot`),本文在此之上增加冻结与回显核对:

- BUILD_REFERENCE = `Ref. Snapshot`;SNAPSHOT_NUM 在该 campaign、该 QuickBuild 工程第一次触发时取表单**当时选中**的值并冻结(冻结范围是"campaign × 工程",不同工程各自冻结)。
- 同一 campaign 后续触发时,冻结值必须仍在下拉框中,否则该 unit 拒绝触发(`REJECTED_QB_SNAPSHOT_UNAVAILABLE`,报告记 `skip_reason=qb_snapshot_unavailable`);**已取得终态 RESULT 的 unit 不受影响**(RESULT 与结果文件是不可变快照);尚未触发的 unit 须在新 campaign(新 state DB)中处理。
- 每次读取结果都核对父构建回显的 SNAPSHOT_NUM 等于冻结值(第 5.3 节),这是"基准没被服务端换掉"的唯一凭据。

理由:这一步要回答的是"修复在官方构建系统里当前能不能过",复现原失败已由本地基线复现完成;`Ref. Snapshot` 是表单默认、最常用路径,同一 campaign 内所有包对同一基准、结果可比。`Live` 会使基准漂移、失败无法归因;`Snapshot Number` 固定为 CI 失败时的快照,旧快照可能已下架,且要走未取证的服务端联动路径。三者在代码上只差配置值。

**第二项:凭据可信边界——已裁定采用下述边界。** 浏览器请求拦截要用 Chromium 调试协议,而该协议把每个被拦请求的请求头(含 Cookie)与请求体(含人工登录时提交的密码)交给控制它的 Node 代理进程,无法关掉(第二轮评审实测)。所以"会话与 cookie 永远不离开浏览器进程"做不到。本文默认把可信边界定为 **Chromium 浏览器 + 专用 Node 代理进程**:这些内容只在代理进程内存中瞬时存在,协议适配层收到事件后立即丢弃请求头与请求体,只向业务代码提供方法、地址等判定所需的元数据;不得用于业务解析、独立请求、日志、文件或对 Python 的应答;禁止协议调试日志与原始事件输出(第 3.1 节)。不接受此边界的替代做法是把请求判定放进浏览器内部、只向外输出元数据,实现难度与不确定性都明显更高,本文不采用。作为对照,团队 quickbuild-sbs 工具由 Python 进程直接取得密码(终端输入、环境变量、命令行参数或配置文件明文),cookie 长期存放在 `~/.cache` 下的文件里,调试页面不脱敏落盘;本文边界严格小于它,且不采用其保存密码与 cookie 落盘的做法。

---

## 1. 术语与固定值

| 名称 | 含义 |
|---|---|
| 父构建 | RBS/TRIGGER 配置被触发产生的构建,id 记为 P。`BUILD_BOUND` 与 `RESULT` 事件里的 `qb_build_id` 一律是 P |
| 子构建 | 父构建派生的实际编译构建,id 记为 C,其 Status 是通过判据 |
| 目标行 | `<campaign_units.project>@<derived_commit_sha>`。沿用表字段名 `sbs_target`(表结构冻结,不改列名),语义改为"RBS 构建包列表中的唯一一行" |
| 请求号 | `request_id`,工具在提交前生成的 32 位小写十六进制随机串(uuid4 hex) |
| 请求标记 | 写进表单 BUILD NOTES 的固定文本:`clang-fix-campaign request=<request_id>`,父构建变量页回显它 |
| 复验参数 | 第 2.1 节配置中的全部表单取值 |
| 参数冻结 | 每个 state DB(即每个 campaign)每个 QuickBuild 工程(以 unit.branch 区分)第一次触发时写入的复验参数快照,之后只读 |
| 固定架构值 | `standard-armv7l:aarch64:x86_64` |

QuickBuild 构建状态归一:页面文字先去掉首尾空白,再按下表**精确、区分大小写**匹配:

| 页面文字 | 归一 | 类别 |
|---|---|---|
| `Successful` | PASS | 终态成功(已实测) |
| `Failed` | FAIL | 终态失败(待实测) |
| `Cancelled` | CANCELLED | 终态失败(待实测) |
| `Timeout` | TIMEOUT | 终态失败(待实测) |
| `Running` | RUNNING | 非终态(待实测) |
| `Waiting` | WAITING | 非终态(待实测) |
| `Queued` | QUEUED | 非终态(待实测) |
| 父构建 Child Build 表不存在或为空 | QUEUED | 非终态 |
| Child Build 表中 Build Result 为 `Not Finished (...)`,且子构建页 Status 不在本表 | RUNNING | 非终态(已见于 RBS 截图) |
| 其它任何文字 | 无法识别 | 读取失败,不写 RESULT(第 5.4 节) |

任何表外文字一律"无法识别",绝不当作 PASS。第一次见到新的状态文字后,按 R1 补表。

---

## 2. 复验参数配置与冻结

### 2.1 配置(campaign config 新增 `qb` 段)

```yaml
qb:
  base_url: https://quickbuild.tizen.org          # 固定值,不同则拒绝
  browser:
    node: /usr/bin/node                          # 绝对路径
    playwright_module: /abs/path/to/playwright/index.mjs
    chromium: /abs/path/to/chromium
    login_timeout_seconds: 600
  projects:                                      # 以 campaign_units.branch 为键
    tizen_base:
      enabled: true
      configuration_path: root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER
      overview_id: <由第 9.4 节第 1 步只读取证确定>
      project_name: Tizen-Base-Toolchain         # 表单只读字段 PROJECT_NAME 必须等于此值
      form:
        BUILD_TYPE: Full
        REPO_TYPE: ALL
        BUILD_REFERENCE: Ref. Snapshot
        SNAPSHOT_NUM: "@freeze"                  # 见 2.2
        PROJECT_BRANCH: tizen_base               # 必须等于键名(unit.branch)
        Immediate Stop With Error: true          # 本版只允许 true
        CHILD_CONFIGURATIONS: [standard-armv7l:aarch64:x86_64]   # 本版只允许这一个值
        TARGET_IMAGE: []
        Add Package List: ""
        Remove Package List: ""
        # Build Package List 与 BUILD NOTES 不可配置,由工具写目标行与请求标记
      qb_pass_requires_accept: false
    tizen:
      enabled: false                             # Unified-Toolchain 表单未取证前保持关闭
```

校验规则(读配置时一次完成,任一不满足 exit 2 `INVALID_ARGS`,不打开浏览器):

1. `base_url` 必须正好等于 `https://quickbuild.tizen.org`。
2. `browser` 下三个路径必须是存在的绝对路径。
3. 每个 `enabled: true` 的工程,`form` 必须**恰好**包含上面列出的十个键;`SNAPSHOT_NUM` 只能是具体值或字面量 `@freeze`。
4. `PROJECT_BRANCH` 必须等于该工程的键名。
5. `Immediate Stop With Error` 必须为 `true`;`CHILD_CONFIGURATIONS` 必须恰好是 `[standard-armv7l:aarch64:x86_64]`;`TARGET_IMAGE` 必须为空列表;Add/Remove Package List 必须为空字符串。这几项决定"子构建总状态能代表三架构",本版不开放配置。
6. `qb_pass_requires_accept` 必须是布尔值。

unit.branch 在 `projects` 中不存在,或对应工程 `enabled: false` → exit 4 `REJECTED_QB_PROJECT_NOT_READY`。

### 2.2 参数冻结(新表 `campaign_qb_profiles`)

```sql
CREATE TABLE IF NOT EXISTS campaign_qb_profiles (
  branch          TEXT NOT NULL PRIMARY KEY,   -- campaign_units.branch
  profile_json    TEXT NOT NULL,               -- 规范化 JSON(键排序、紧凑分隔符、ensure_ascii=False)
  profile_sha256  TEXT NOT NULL
                  CHECK (length(profile_sha256) = 64
                         AND profile_sha256 NOT GLOB '*[^0-9a-f]*'),
  created_at      TEXT NOT NULL
);
```

- `profile_json` 内容:`configuration_path`、`overview_id`、`project_name`、`form` 全部十个键(`SNAPSHOT_NUM` 为实际值)、`qb_pass_requires_accept`。
- 主键是 branch;"冻结范围是 campaign × 工程"成立的前提是 branch 与工程一一对应,由第 2.1 节校验规则 4 保证。将来若一个 branch 对应多个工程,须按 R1 改主键。
- **首写即定,不更新、不删除**:写入原语用 `INSERT ... ON CONFLICT(branch) DO NOTHING` 后回读,内容逐字节相同则视为成功(含并发进程先写入的情形),不同则 `StateInconsistent`。写入与提交意图在同一事务(第 4.3 节第 8 步)。
- 后续触发:用当前配置(`@freeze` 以已冻结值代入)生成同样的规范化 JSON,与冻结行逐字节比较;不等 → exit 4 `REJECTED_QB_PARAMS_CHANGED`,不打开浏览器。即改配置只对新 campaign(新 state DB)生效。
- 新增只读查询 `campaign_state.qb_profile(state_db, branch) -> dict | None`,**按 unit 的 `campaign_units.branch` 取**(一个 state DB 可能有多个 branch 的 unit,不得实现成"取唯一一行")。P5R 从这里读 `qb_pass_requires_accept`,不再读配置文件。

---

## 3. 浏览器代理 `qb_browser_agent`

### 3.1 进程模型

- 实现文件:`tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs`(Node),Python 侧驱动 `ci_triage/qb_browser.py`。
- Python 用参数列表启动 `node qb_browser_agent.mjs <playwright_module> <chromium>`,不经 shell;stdin/stdout 走逐行 JSON 命令与应答;stderr 只允许输出脚本内的固定提示文字。
- Chromium:有界面窗口,用户目录建在 `/dev/shm` 下的临时目录(不可用则 `QB_BROWSER_UNAVAILABLE`),不加载日常 profile,不允许下载,不启用 service worker,不开 HAR/trace/storage-state,不使用 `ignoreHTTPSErrors`。进程退出时(正常、异常、收到信号)关闭浏览器并删除该目录。
- **拦截先于一切页面活动**:浏览器启动后、首个页面导航前,装好第 3.4 节的全部拦截面;任何页面目标在拦截装好之前不得开始加载。
- **新目标**:浏览器级自动挂接新目标,并要求新目标启动即暂停;新窗口、弹窗、新标签页、iframe 之外的一切目标(Worker、SharedWorker、ServiceWorker 等)本版一律不支持——不恢复执行、立即关闭并计数;无法可靠阻止时关闭整个浏览器并以 `QB_BROWSER_UNAVAILABLE` 停止。不得以"收到创建通知后再关闭"代替"执行前阻断"。新窗口与弹窗同样在执行前关闭。
- **凭据可信边界是 Chromium 浏览器 + 专用 Node 代理进程**(第 0.5 节第二项):
  - 所有发往 QuickBuild 的请求都必须由浏览器页面本身发出并经过第 3.4 节的拦截;只读页面一律通过**页面导航**取得,从导航响应拿 HTTP 状态,从 DOM 拿内容;
  - **禁止**使用 `page.request`、`context.request`、`request.newContext` 或任何代理侧 HTTP 客户端访问 QuickBuild——它们共享浏览器 cookie 却不经过页面请求拦截;
  - 不调用 `context.cookies()`、`storageState()`;
  - 调试协议事件中隐式携带的请求头与请求体:由唯一的协议适配层接收,**立即丢弃** `headers`、`postData`、`postDataEntries` 及其它请求头类字段,只把方法、协议、主机、路径、查询原文、资源类型、重定向来源、响应状态码交给判定逻辑;不得用于业务解析、独立请求、日志、文件或对 Python 的应答;
  - 禁止开启协议调试日志(如 Playwright/DevTools 的 debug 环境变量),禁止输出原始协议事件;异常处理只输出固定错误类别,不带原始事件或异常文本。
- 代理单会话串行执行命令;整个 CLI 进程只启动一个代理,多个 unit / 请求共用一次登录。

### 3.2 命令

| 命令 | 允许的阶段 | 作用 |
|---|---|---|
| `login` | 启动后第一条 | 打开登录页,等待人工登录完成(第 3.3 节) |
| `read {path}` | 已登录 | 导航到只读页面,核对最终地址与页面中的构建号,返回脱敏后的 HTML 与 HTTP 状态(第 3.6 节) |
| `open_form {overview_id}` | 已登录 | 打开配置页,核对配置路径,点击"运行",等待表单(第 3.5 节) |
| `fill {fields}` | 表单已打开 | 按标签设值、等待联动、逐项读回;返回读回值与指纹 |
| `submit {fingerprint}` | `fill` 成功后 | 复核指纹,放行一次提交,点 Ok,返回落点 |
| `close` | 任意 | 关闭浏览器、删除临时目录、退出 |

代理拒绝任何不在本表中的命令,以及阶段不对的命令(应答 `{"ok": false, "error": "AGENT_PHASE"}`,不执行)。`fill` 失败或 `submit` 结束后,该表单进入"作废"状态,再次提交必须重新 `open_form`。

### 3.3 登录检测(不需要回终端)

- `login` 打开 `/signin`,之后每 2 秒检查一次当前页:**已登录**当且仅当最终地址路径不是 `/signin`、页面中没有 `type=password` 输入框、并且存在文字为 `Sign Out` 的链接。三个条件缺一即视为未登录。
- 超过 `login_timeout_seconds` 仍未登录 → `QB_LOGIN_TIMEOUT`;窗口被关闭 → `QB_LOGIN_ABORTED`;两者都关闭浏览器退出。
- 终端只打印固定提示:"已打开 QuickBuild 登录窗口,请在窗口中登录;登录后工具会自动继续。"不读取终端输入。
- 工具从不填写用户名或密码;登录表单只由人在窗口里提交。`login` 命令的实现只做导航到 `/signin` 与只读轮询(地址、密码框、Sign Out 链接三项),不做任何点击、输入、按键或页面内脚本执行。拦截层分不出请求由人还是由代理触发,所以这一条靠源码静态断言与集成测试保证(第 9.2、9.3 节)。
- 此判定是相对 spike(人工回车确认)的新行为,第 9.3、9.4 节分别做真假阳性测试与真机确认。

### 3.4 请求拦截(逐跳、精确登记)

**拦截机制**(三个拦截面,都在首个页面导航前装好):

1. **HTTP 请求**:对页面目标启用 Chromium DevTools 协议的请求拦截(Fetch 域)。每一个请求——页面脚本发起的、子资源、以及**重定向产生的每一跳**——都在**请求阶段**暂停并判定,不通过即以失败中止。获准的请求同时在**响应阶段**再暂停一次:响应状态码为 307 或 308 时在响应阶段终止,不让浏览器跟随(请求阶段拿不到状态码,只能在这里判);其它响应放行,下一跳重新接受请求阶段判定。响应阶段不再次消耗提交放行次数;提交已放行后在响应阶段被终止的,仍按落点 unknown 处理。
2. **WebSocket**:在创建任何页面之前安装上下文级拒绝(ws/wss 一律不连接服务器)。
3. **新目标**:按第 3.1 节,Worker 类目标与新窗口在执行前阻断。

Playwright 的 `page.route`/`context.route` 不满足要求(重定向只拦首跳,且不覆盖 Worker),不得作为唯一拦截面。第 9.2、9.3 节用"服务器端实际收到的请求清单"证明三个拦截面都生效,不能只测判定函数。

判定只看第 3.1 节列出的元数据。被拒请求只记"阶段 + 路径形态"到本次运行的 trace(不含查询值),并计数。

**永久禁止**(先于一切放行规则):

- 非 `https://quickbuild.tizen.org` 的任何请求(含 download.tizen.org、iframe、外站资源);WebSocket;
- 路径以 `/rest/` 开头;
- 查询中出现 Wicket 监听器且监听器组件名命中破坏性动作的请求,即匹配
  `(?i)I(Link|Behavior|FormSubmit|Resource)Listener[.0-9-]*-[A-Za-z0-9:_-]*(promote|cancel|stop|rerun|delete|abort)`;
  以及两个已取证的完整特征 `ILinkListener-content-buildHead-promote`(Ready to Accept)、`ILinkListener-form-cancel`(表单 Cancel)。放弃表单一律用 `close` 关闭浏览器;
- `/build/<id>/log`、`/build/<id>/html_report`、产物下载链接;
- 状态码 307/308 的重定向(会重放 POST),在响应阶段终止,见上文拦截机制第 1 项。

**放行规则**(只有在当前阶段、当前命令执行期间才生效;地址"精确登记"指从当前页面 DOM 中读出的完整地址原文,逐字符相等才放行,不按监听器名前缀泛化):

| 阶段 | 放行 |
|---|---|
| 所有已加载页面 | 静态资源:GET,路径前缀属于登记清单(初版来自 `rbs-form-01/form.redacted.html:24-40` 与 spike:`/styles/`、`/jquery/`、`/scripts/`、`/datetimepicker/`、`/codemirror/`、`/wicket/resource/`、`/images/`、`/favicon.ico`;第 9.4 节第 1 步记录实际被拒的静态资源后按 R1 补齐),查询为空或恰好匹配 `^v=\d+$`,且查询中不含任何 Listener |
| 登录中 | GET `/signin`(查询为空);由人在窗口中提交的 POST `/signin?<查询>`(查询只允许匹配 `^\d+-\d*\.?IFormSubmitListener-[A-Za-z0-9:_-]+$`,代理自身从不发起);登录后的跳转 GET `/`、`/overview/0`(查询为空;沿用 spike 已实测可用的落点),以及第 9.4 节第 1 步实测并登记在附录 C 的登录落点(同样要求精确路径与空查询) |
| 已登录、只读 | GET `/build/\d+`、`/build/\d+/(overview\|variables\|step_status)`、`/overview/<配置的 overview_id>`,**查询必须为空**;当前页面 DOM 中登记的定时刷新地址(`...IBehaviorListener...action=ajaxRefresh`)的精确原文 |
| `open_form` 执行中 | 只读放行全部 + 当前配置页 DOM 中 title 为 `Run the configuration` 的按钮所指地址的精确原文,**一次** + 由它产生的跳转 GET:路径 `/wicket/page`、查询恰好匹配 `^\d+$` |
| `fill` 执行中 | 只读放行全部 + **当前正在设值的那一个字段**的回调地址:每次设值**之前**从活动 DOM 重新读取该字段 onchange 回调地址原文,形态须符合第 3.5 节 `open_form` 第 6 项,登记为本次字段操作期间唯一放行的 POST 地址(一次),该字段操作结束即撤销 + 表单页重渲染 GET:路径 `/wicket/page`,查询匹配 `^\d+(-\d+)?$`。(Wicket 地址带页面版本号,设值后版本可能递增、回调地址随之改变,所以不能在 `open_form` 时一次性冻结原文。双列表的移动按钮是页面内脚本,不发请求;双列表的服务器回调挂在 `recorder` 的 onchange 上,按本行处理——见 `rbs-form-01/form.json` 中按钮 `server_callback: false`、`recorder` `server_callback: true`。) |
| `submit` 执行中 | 在指纹复核通过后从活动 DOM 读取的表单 action 精确原文(POST,路径 `/wicket/page`,查询须匹配 `^\d+-\d+\.IFormSubmitListener-form$`),**一次**;随后的跳转 GET:路径 `/build/\d+`(查询为空)或 `/wicket/page`(查询 `^\d+(-\d+)?$`) |

额外约束:

- 提交地址每个 `open_form` 至多放行一次;放行后同一表单的任何提交一律拒绝;`fill` 失败(表单作废)后不经新的 `open_form` 的提交一律拒绝。
- `dragDrop`、`loadPopup`、`unloadPopup`、`quicksearch` 及其它未登记的 Listener 一律拒绝。
- 旧版 Wicket 的 AJAX 脚本可能在回调地址末尾追加随机数参数(如 `&random=0.123`)。若第 9.3 节本机集成或第 9.4 节第 1.5 步观察到这一行为,"精确原文"规则改为"登记原文 + 末尾恰好一个 `random=` 十进制小数参数",按 R1 记入附录 C;除此之外不允许任何偏差。
- 代理记录每个表单实例的状态:`not_released`(从未放行提交)或 `released`(已放行一次)。这一状态是第 4.3 节判定"确定未提交"的唯一依据。

### 3.5 填表、核对与提交

**`open_form` 成功的条件**(任一不满足 → `QB_FORM_CHANGED`,不进入表单已打开阶段):

1. 配置页 `<title>` 以 `QuickBuild - <configuration_path>` 开头(其后只允许为空或 ` - ...`),路径逐字等于配置。
2. 页面上恰好一个 title 为 `Run the configuration` 的按钮,其所指地址含 `ILinkListener-run`。
3. 点击后 30 秒内出现标题文字 `Specify Build Options` 的表单,其 action 含 `IFormSubmitListener-form`。
4. 表单的字段标签**去重后的集合**恰好是:`PROJECT_NAME`、`BUILD_TYPE`、`REPO_TYPE`、`BUILD_REFERENCE`、`SNAPSHOT_NUM`、`PROJECT_BRANCH`、`Immediate Stop With Error`、`CHILD_CONFIGURATIONS`、`Build Package List`、`Add Package List`、`Remove Package List`、`TARGET_IMAGE`、`BUILD NOTES`;
   - PROJECT_NAME 恰好对应一个只读显示区域(`property-viewer`,见 `form.redacted.html:729-740`),不要求输入控件,其显示值按第 5 项核对;
   - 其余非双列表的可编辑字段,每个标签恰好对应一个输入控件;
   - 双列表字段(`CHILD_CONFIGURATIONS`、`TARGET_IMAGE`)每个标签恰好对应三个控件,角色恰好是 `recorder`(隐藏记录)、`choices`(待选)、`selection`(已选),依据 `rbs-form-01/form.json` 的 palette 结构识别。
5. 只读字段 PROJECT_NAME 显示值等于配置的 `project_name`。
6. 校验各业务字段 onchange 回调地址的**形态**:路径为 `/wicket/page`,查询匹配 `^\d+-\d+\.IBehaviorListener\.\d+-[A-Za-z0-9:_-]+$`。只校验形态,不冻结原文;原文在 `fill` 每一步之前重新读取(第 3.4 节)。形态不符即 `QB_FORM_CHANGED`。

**`fill` 的步骤**(一律按"标签 + 角色"定位,不按 name 中的序号定位):

1. 按固定顺序设值:BUILD_TYPE → REPO_TYPE → BUILD_REFERENCE → SNAPSHOT_NUM → PROJECT_BRANCH → Immediate Stop With Error → CHILD_CONFIGURATIONS → Build Package List → Add Package List → Remove Package List → TARGET_IMAGE → BUILD NOTES。BUILD_REFERENCE 在 SNAPSHOT_NUM 之前,因前者的联动可能刷新后者。
2. 下拉框按**选项显示文字**精确匹配选择;找不到该文字 → `QB_FORM_VALUE_UNAVAILABLE`。SNAPSHOT_NUM 为 `@freeze` 时不设值,读取**当前选中项**文字作为待冻结值;无选中项或下拉框为空 → `QB_FORM_VALUE_UNAVAILABLE`;选项多于一个时照常取选中项,并在应答中带回选项数(写入 trace)。
3. 双列表只操作 `choices`/`selection` 两个列表与页面自带的移动按钮,把 `selection` 的全部选项文字(按顺序)调整为配置值;**不直接写 `recorder`**。
4. 每设一个值之前,从活动 DOM 重新读取该字段的回调地址并登记(第 3.4 节);设值后等待该回调请求完成,且 1 秒内没有新的**非定时刷新**请求(登记的 `ajaxRefresh` 不计入静默判定);单个字段总等待超过 30 秒 → `QB_FORM_CHANGED`。
5. 全部设完后逐项读回 DOM 当前值:下拉框读选中项文字;复选框读勾选状态;文本域读原始文本;双列表读 `selection` 全部文字(按顺序),并把 `recorder` 的值与 `selection` 交叉核对(`recorder` 为各选项 value 的十六进制编码,按 `rbs-form-01/form.json` 的 `hidden_palette_value_shapes` 规则解码后必须等于 `selection` 文字;解码不了即不等)。读回值必须与要求值完全相等,其中:
   - Build Package List 恰好等于目标行(单行,无前后空白,无其它行);
   - BUILD NOTES 恰好等于请求标记;
   - Add/Remove Package List 为空字符串,TARGET_IMAGE 的 `selection` 为空;
   - CHILD_CONFIGURATIONS 的 `selection` 恰好是固定架构值一项。
6. 计算表单指纹:读回值按"标签/角色"排序后的规范化 JSON 的 sha256。返回 `{readback, fingerprint, snapshot_option_count}`。

任一步失败:应答对应错误,表单作废。

**`submit {fingerprint}`**:

1. 再读回一次全部字段,重算指纹,必须等于传入值;不等 → `QB_FORM_CHANGED`,不放行、不点击,表单状态保持 `not_released`,同时置表单为作废态,之后只接受 `close` 或新的 `open_form`。
2. 置表单状态为 `released`,放行一次表单 action,点击文字为 `Ok` 的提交按钮。
3. 等待最多 60 秒,直到导航结束或超时。
4. 返回落点,只有两种:
   - `{"landed": "build", "build_id": "<P>"}`:最终地址路径为 `/build/\d+`,且页面 Summary 表 Id 一栏等于该数字;
   - `{"landed": "unknown", "observed": "<脱敏后的最终路径形态>", "messages": [...]}`:其它一切情况,**包括停在表单页并显示错误提示**、超时、跳到别的页面。
5. 应答始终带 `released: true|false`。只有第 1 步拒绝时为 `false`。

提交请求一旦放行,**任何页面表现都不能证明服务器没有创建构建**(例如服务器已建构建、渲染响应时出错并返回带错误提示的表单),所以不存在"提交后确定失败"的落点。

**待实测**:点 Ok 后实际跳到哪里尚未观察(第 9.4 节第 2 步)。若不跳到 `/build/<id>`,落点一律 `unknown`,构建号走第 5.2 节人工绑定;不改安全判定。

代理应答到 CLI 错误码的映射(Python 侧固定表,表外应答一律 `INTERNAL_ERROR`):

| 代理应答 | CLI 错误码 |
|---|---|
| `QB_FORM_CHANGED` | `REJECTED_QB_FORM_CHANGED` |
| `QB_FORM_VALUE_UNAVAILABLE`(SNAPSHOT_NUM) | `REJECTED_QB_SNAPSHOT_UNAVAILABLE` |
| `QB_FORM_VALUE_UNAVAILABLE`(其它字段)、读回不等 | `REJECTED_QB_FORM_MISMATCH` |
| `QB_LOGIN_TIMEOUT` / `QB_LOGIN_ABORTED` | 同名 |
| `AGENT_PHASE`、代理进程退出、应答不是合法 JSON | `submit` 已发出命令后发生:按落点 unknown 处理;其余:`QB_BROWSER_UNAVAILABLE` |

### 3.6 只读取页

`read {path}`:

1. 路径必须属于第 3.4 节"已登录、只读"放行集合,否则 `AGENT_PHASE`。
2. 导航到该路径;最终地址必须与请求地址逐字相等(发生任何重定向即失败 `QB_READ_REDIRECTED`)。
3. 对 `/build/<id>` 及其子页:页面 Summary 表(子页无 Summary 时用页面标题中的构建号)中的 Id 必须等于请求的 id;不等 → `QB_READ_ID_MISMATCH`。防止从另一个构建的页面借用 `Successful`。
4. 返回 `{status, html_redacted}`。HTTP 非 200 照实返回状态,由 Python 判定。

### 3.7 页面脱敏(`ci_triage/qb_redact.py`)

从 spike 的 `PageRedactor` 与 `ef5_rbs_form.py` 规则移入正式代码并补测试:

- 登录显示名(`Welcome!` 之后)、Triggered By 等账号字段 → `<USER>`;
- 所有隐藏输入框的 value、URL 中的 `jsessionid`、形如 token/csrf/session 的参数值 → `<REDACTED>`;**例外**:双列表 `recorder` 字段不是凭据,保留原值;
- `Set-Cookie`、`Cookie`、`Authorization` 头不进入任何返回值(代理本就不读请求头)。

代理返回前脱敏一次;Python 写证据文件前按同一规则再自检一次(写后按原始字节检查不含 `JSESSIONID_8810=`、不含登录显示名)。自检失败 → 删除该证据文件,`QB_EVIDENCE_REDACTION_FAILED` exit 5,不写 RESULT。

---

## 4. `qb-trigger` CLI

### 4.1 接口

```
python3 -m ci_triage qb-trigger
    (--verification-ids <id1,id2,id3> | --units-file <path>)
    --state-db <path> --state-root <path> --config <path>
    [--retrigger]
```

- `--units-file`:JSON 数组,每项 `{"verification_ids": [id1, id2, id3]}`;一次登录,按数组顺序逐个处理,**每个 unit 独立判定、独立加锁、独立落库**,一个失败不影响后续。
- stdout:JSON 数组,每个 unit 一项:
  `{campaign_unit_key, sbs_target, request_id|null, request_seq|null, qb_build_id|null, action, status, error_code|null}`;
  `action` ∈ `submitted_bound`、`submit_uncertain`、`submit_failed`、`already_requested`、`already_passed`、`rejected`。
- 退出码:全部 unit 成功(含幂等命中)→ 0;参数/配置错误 → 2;存在校验拒绝且无提交失败或不确定 → 4;存在 `submit_failed` 或 `submit_uncertain` → 5;`CampaignStateBusy` → 4 `CAMPAIGN_STATE_BUSY`;意外异常 → 5 `INTERNAL_ERROR`(沿用 P5:该出口不写数据库)。
- 原 design.md 的命令名 `qb-sbs-trigger` 废止(附录 A)。

### 4.2 前置校验(逐 unit,在该 unit 的锁内)

整段第 4.2、4.3 节在 `.sandbox_submit.lock` 持有期间执行(与 sandbox-submit 同一把锁,路径规则沿用 P5 的 `_unit_hash`)。

1. 由三份 verification record 定位 unit,沿用 P5 的选择规则;选择错误不写 HELD,直接 `rejected`。
2. 读配置与工程(第 2.1 节);参数冻结比对(第 2.2 节)。
3. 读 gate_view(一次一致读快照):
   - 最新状态必须属于 {SANDBOX_PUSHED, KB_APPENDED, QB_REQUESTED, QB_TRIGGERED, SANDBOX_QB_PENDING, SANDBOX_QB_PASS, SANDBOX_QB_FAILED, QB_SUBMIT_FAILED};否则 `REJECTED_SANDBOX_NOT_BOUND`。
   - 必须有 DERIVE 事件(取 `derived_commit_sha`)与 PUSH 事件,PUSH 的 `result=ok`、`pushed_sha == derived_commit_sha`、`ref` 为 sandbox 白名单 ref;否则 `REJECTED_SANDBOX_NOT_BOUND`。PUSH 事件的 `url` 在 P5 中恒为 null,不读取。
4. 计算目标行 `unit.project@derived_commit_sha`;`unit.project` 必须匹配 `^[A-Za-z0-9][A-Za-z0-9._/+-]*$`(Tizen 仓库名有大写,如 Open3D)且不含 `..`、不以 `/` 结尾;否则 `REJECTED_SANDBOX_NOT_BOUND`。
5. 幂等判定(取该 unit 最新 request,即 request_seq 最大者)。按下表**自上而下第一个匹配的行**判定;各行条件已按"最新 request 的事件构成 + unit 最新状态"写成互斥:

| 最新 request 情况 | 不带 `--retrigger` | 带 `--retrigger` |
|---|---|---|
| 无 request | 提交 | 提交 |
| 只有 SUBMITTED、无 BUILD_BOUND,**且 unit 最新状态为 QB_SUBMIT_FAILED**(提交确定未放行) | 提交(新 request) | 提交(新 request) |
| 只有 SUBMITTED、无 BUILD_BOUND,**且 unit 最新状态不是 QB_SUBMIT_FAILED**(无法确定是否已提交) | `already_requested`,不提交 | 提交(新 request);旧 request 保留 |
| 已 BUILD_BOUND,无 RESULT | `already_requested` | 拒绝 `REJECTED_QB_REQUEST_PENDING` |
| 最新 RESULT 为 PASS | `already_passed` | 拒绝 `REJECTED_QB_REQUEST_PENDING` |
| 最新 RESULT 为终态失败 | `already_requested`(不自动重提) | 提交(新 request) |

  "无法确定是否已提交"时允许人工 `--retrigger`:最坏结果是 QuickBuild 上多跑一次构建,不会错绑——每个构建只凭请求标记对应唯一请求。

### 4.3 提交流程(逐 unit,通过前置校验后)

1. (整个 CLI 第一次需要浏览器时)启动代理并 `login`。登录失败 → 所有尚未处理的 unit 记 `submit_failed`、`error_code=QB_LOGIN_TIMEOUT|QB_LOGIN_ABORTED`,**不写数据库**,exit 5。
2. 生成 `request_id` 与请求标记。
3. `open_form`。失败 → `rejected`,不写数据库。
4. `fill`(十个配置字段 + 目标行 + 请求标记)。失败 → `rejected`,不写数据库。
5. 冻结比对:本 branch 无冻结行 → 用读回值生成待冻结 profile;已有冻结行 → 读回值逐项等于冻结值,否则 `REJECTED_QB_PARAMS_CHANGED`,不写数据库。
6. **远端 sandbox ref 实时核对**:远端地址按 P5 规则由配置构造(`gerrit_ssh_base.rstrip('/') + '/' + unit.project`,并按 P5 规则校验地址格式与 URL 改写),ref 取自 PUSH 事件;用 P5 的隔离传输仓库与统一 git 环境(`_sandbox_git` 及 `<ws>/<unit_hash>/.transport`)做一次 `ls-remote`,不得以主副本为 `-C`/`--git-dir`、不得另起 git 环境。结果必须等于 `derived_commit_sha`,否则 `REJECTED_SANDBOX_NOT_BOUND`,不写数据库。本步在填表之后、落库之前,缩短核对到提交的时间。
7. 写一条 trace:目标行、request_id、表单指纹、是否首次冻结、SNAPSHOT_NUM 选项数(不含页面内容)。
8. **提交意图落库**(一个写事务,使用第 6.2 节按连接写入的原语):
   - 事务内重查:最新状态与第 4.2 节第 3 步读到的相同;最新 request_seq 与第 4.2 节第 5 步读到的相同;PUSH 事件不变。任一变化 → 回滚,`REJECTED_STATE_INCONSISTENT`;
   - 冻结行重查:第 5 步判为"需冻结"而此时该 branch 已有冻结行(同一 branch 的另一个 unit 被并发进程先冻结;unit 锁不互斥不同 unit)→ 与待冻结的规范化 JSON 逐字节比较,相等则不再写,不等则回滚 `REJECTED_QB_PARAMS_CHANGED`;
   - 若需冻结且仍无冻结行,写 `campaign_qb_profiles`;
   - 写 request 与 SUBMITTED;
   - 追加状态 `QB_REQUESTED`。
9. `submit(fingerprint)`。
10. 按应答处理:
    - `released: false`(指纹复核不过,提交确定未放行):一个写事务追加状态 `QB_SUBMIT_FAILED`;`submit_failed`,`error_code=REJECTED_QB_FORM_CHANGED`。
    - `landed: build`:读 `/build/<P>/variables`,核对第 5.3 节第 2 项中"请求标记"与"目标行"两条;并查 P 未绑定到任何其它 request。全部通过 → 一个写事务(事务内重查该 request 仍是最新且无 BUILD_BOUND):`BUILD_BOUND(qb_build_id=P)` + 状态 `QB_TRIGGERED`,`submitted_bound`。任一不通过 → 不写,`submit_uncertain`,`error_code=REJECTED_QB_BINDING_MISMATCH`。
    - `landed: unknown`,或 `submit` 命令发出后代理异常:不写任何事件,状态保持 QB_REQUESTED,`submit_uncertain`,`error_code=QB_SUBMIT_UNCERTAIN`;输出脱敏后的 `observed` 与提示文字。人工到 QuickBuild 上按请求标记找到构建后用第 5.2 节绑定;确认没有构建后用 `--retrigger` 重提。

### 4.4 崩溃窗口

| 崩溃发生在 | 数据库状态 | QuickBuild 状态 | 重跑行为 |
|---|---|---|---|
| 第 8 步事务提交之前 | 无变化(事务原子回滚) | 未提交 | 正常提交 |
| 第 8 步之后、第 9 步放行之前 | 冻结行(如首次)+ SUBMITTED + QB_REQUESTED | 未提交 | `already_requested`,不自动重提;人工确认后 `--retrigger` |
| 放行之后、第 10 步写库之前 | 同上 | 可能已提交 | 同上;若构建存在,用第 5.2 节按请求标记绑定 |
| 第 10 步之后 | 完整 | 已提交或确定未提交 | 幂等命中 |

意图先于放行落库,保证"QuickBuild 上出现了构建,但数据库没有任何记录"这种情况不会发生;代价是可能留下从未真正提交的 request,由人工 `--retrigger` 处理。

---

## 5. `qb-result-fetch` CLI

### 5.1 接口

```
python3 -m ci_triage qb-result-fetch
    (--request-id <id> [--qb-build-id <P>] | --qb-build-id <P> | --requests-file <path>)
    --state-db <path> --state-root <path> --config <path>
```

- `--request-id` 单独:读取该请求已绑定的构建。未绑定 → exit 4 `REJECTED_QB_BINDING_MISMATCH`(提示同时给 `--qb-build-id` 以绑定)。
- `--request-id` + `--qb-build-id`:人工指定绑定(第 5.2 节),成功后继续读取。
- `--qb-build-id` 单独:沿用 design.md v1.4.10 规则,经 BUILD_BOUND 反查 request;查不到 → exit 4 `REJECTED_QB_BINDING_MISMATCH`,不得猜测挂到最新 request;命中多个 unit → `AmbiguousQbReference`。
- `--requests-file`:JSON 数组,每项为上面三种形式之一;一次登录,逐项独立处理。
- 只处理每个 unit 的**最新 request**:传入的 request 不是最新 → 该项 exit 4 `REJECTED_QB_SUPERSEDED`,不读取、不写库。
- 每项在该 unit 的 `.sandbox_submit.lock` 内完成从入口校验到落库的全流程(网络读取期间持锁,但不放在数据库事务内)。
- stdout:每项 `{request_id, qb_build_id, child_build_id|null, status, terminal, result_event_id|null, qb_result_path|null, error_code|null}`。
- 退出码:全部成功(含非终态)→ 0;参数错误 → 2;存在校验拒绝 → 4;存在读取失败 → 5;busy/意外异常同第 4.1 节。

### 5.2 人工指定绑定(`--request-id R --qb-build-id P`)

1. R 必须是其 unit 的最新 request,且没有 BUILD_BOUND;已有 BUILD_BOUND 且等于 P → 视为已绑定继续;已有且不等 → `REJECTED_QB_BINDING_MISMATCH`。
2. R 所在 unit 最新状态为 QB_SUBMIT_FAILED → 拒绝 `REJECTED_QB_BINDING_MISMATCH`(那次提交确定未放行,出现匹配构建说明有异常)。
3. P 不得已绑定到任何其它 request → 否则 `REJECTED_QB_BINDING_MISMATCH`。
4. 读 `/build/P` 与 `/build/P/variables`,第 5.3 节第 1、2 项的**父构建核对全部通过**(Child Build 表为空不影响绑定,但不能跳过第 2 项)。
5. 一个写事务(事务内重查 1–3):`BUILD_BOUND(qb_build_id=P)` + 状态 `QB_TRIGGERED`。父构建任一核对不通过 → 不写 BUILD_BOUND。

### 5.3 读取与逐项核对

已绑定 P 后(人工绑定时是绑定之前),依次 `read`(变量名凡标"以只读取证确定"者,由第 9.4 节第 1 步写入附录 C 后固定;取证前实现不得启用对应核对以外的任何猜测)。**第 1、2 项(父构建)总是全部执行完,才根据 Child Build 表决定是否结束本次读取**:

1. **`/build/P`(父构建)**
   - 配置路径(取自 `<title>`)等于冻结 profile 的 `configuration_path`;
   - 读父构建 Status 与 SR_STATUS(若该栏存在),只记入结果文件,不作判据;
   - Child Build 表:不存在或为空 → 记 `child_pending`,**继续执行第 2 项**;恰好一行 → 其 Repository-Architecture 按附录 C 登记的比较口径等于固定架构值,否则 `REJECTED_QB_BINDING_MISMATCH`;多于一行 → `QB_RESULT_UNRECOGNIZED`;读出子构建 id C。
2. **`/build/P/variables`**
   - 表单字段 Build Package List 的回显变量(SBS 样本中为 `BUILD_PKG_LIST_MODIFY`,RBS 以只读取证确定)的值按空白切分后**恰好一项**,等于目标行;
   - 请求标记的回显变量(以只读取证确定)恰好等于 `clang-fix-campaign request=<R>`;
   - BUILD_TYPE、BUILD_REFERENCE、SNAPSHOT_NUM、PROJECT_BRANCH 的回显变量值逐项等于冻结 profile;
   - 页面中其它值含 `@` 的变量全部原样记入结果文件 `pkg_list_echo`,不作判据。
   任一项找不到或不等 → `REJECTED_QB_BINDING_MISMATCH`,不写 BUILD_BOUND(人工绑定时)、不写 RESULT。
   第 1、2 项全部通过后:若第 1 项记了 `child_pending` → 归一 QUEUED,结束本次读取(按第 5.4 节非终态处理);否则继续第 3、4 项。
3. **`/build/C`(子构建)**
   - 配置路径存在于 `<title>`,且属于同一 QuickBuild 工程(路径前缀与父构建相同,末段以只读取证确定);
   - Summary 表 Status 一栏,按第 1 节归一。
4. **`/build/C/variables`**
   - `TRIGGER_ID`(以只读取证确认)等于 P;
   - `BUILD_PKG_LIST` 按空白切分后恰好一项,等于目标行;
   - `FAIL_FAST`(表单 Immediate Stop With Error 的回显,以只读取证确认)等于 `yes`——这是"子构建总状态代表三架构"的依据,缺失或不等即 `REJECTED_QB_BINDING_MISMATCH`;
   - `EACH_GBS_BUILD_STATUS`:为空 → `per_arch_status=null`;**非空** → 其格式尚无取证,`QB_RESULT_UNRECOGNIZED`,不写 RESULT。
     这是**有意的停止-报告**:此时该 unit 不会有 RESULT,不得人工降级(附录 A 第 10 条),`--retrigger` 亦被拒(第 4.2 节,已绑定无 RESULT)。唯一出路是用本次读到的样本按 R1 定义解析规则(解析出各架构状态,任一非 `Successful` 即整体 FAIL)、升本文版本后重跑 fetch。实现必须在 stdout 与 trace 中输出这一处置指引与证据文件路径,不得只报错误码。为避免把这一分支留到生产中第一次失败才处理,第 9.4 节第 1 步尽量一并读取一个已失败的 RBS 子构建。
   任一不符 → `REJECTED_QB_BINDING_MISMATCH`,不写 RESULT。

每个读到的页面经第 3.7 节脱敏后归档到 `<state_root>/qb_evidence/<request_id>/<序号>.<页面名>.html`,写后自检。

### 5.4 结果落库

| 子构建归一状态 | 写库 | 状态迁移 |
|---|---|---|
| 非终态(QUEUED/WAITING/RUNNING) | **不写 RESULT** | 首次见到时追加 `SANDBOX_QB_PENDING`(已是则不重复) |
| PASS | 写 qb_result 文件 + RESULT | `SANDBOX_QB_PASS` |
| 终态失败(FAIL/CANCELLED/TIMEOUT) | 写 qb_result 文件 + RESULT | `SANDBOX_QB_FAILED` |
| 无法识别 | 不写 RESULT,exit 5 `QB_RESULT_UNRECOGNIZED`;页面证据保留 | 不迁移 |
| 页面 HTTP 非 200、重定向、构建号不符、登录失效、代理异常 | 不写 RESULT,exit 5 `QB_FETCH_FAILED` | 不迁移 |

非终态不写 RESULT,配合附录 A 第 10 条(P5R 人工降级判据收紧),复验未出结果期间不构成人工降级条件。

qb_result 文件(键集合固定,多一个少一个都算 schema 错误):

```json
{
  "qb_build_id": "<P>",
  "child_build_id": "<C>",
  "status": "PASS|FAIL|CANCELLED|TIMEOUT",
  "sbs_target_echo": "<子构建 BUILD_PKG_LIST 原值>",
  "per_arch_status": null,
  "accepted": true|false|null,
  "configuration_path": "...",
  "child_configuration_path": "...",
  "parent_status_text": "...",
  "child_status_text": "...",
  "request_marker_echo": "clang-fix-campaign request=<R>",
  "params_echo": {"BUILD_TYPE": "...", "BUILD_REFERENCE": "...", "SNAPSHOT_NUM": "...", "PROJECT_BRANCH": "...", "FAIL_FAST": "yes"},
  "pkg_list_echo": {"<变量名>": "<原值>"},
  "evidence": ["qb_evidence/<R>/01.build.html", "..."],
  "fetched_at": "<UTC ISO8601>"
}
```

- `accepted`:父构建页存在 SR_STATUS 一栏时,值匹配 `^ACCEPTED(\s*\(.*\))?$` 为 true,否则 false;不存在该栏为 null。
- `per_arch_status`:本版恒为 null(见第 5.3 节第 4 项)。
- 文件写到 `<state_root>/qb_results/<R>/<UTC时间戳>.json`:临时文件 → fsync → rename → fsync 父目录(沿用 P5 的发布写法);计算原始字节 sha256。
- 一个写事务(第 6.2 节原语),事务内重查:R 仍是该 unit 最新 request;R 已有 BUILD_BOUND 且等于 P;然后 `RESULT(qb_build_id=P, status, accepted, sbs_target_echo, per_arch_status_json=NULL, qb_result_sha256, qb_result_ref=相对路径)` + 状态迁移。重查不过 → 回滚并删除刚写的结果文件,`REJECTED_QB_SUPERSEDED` 或 `REJECTED_STATE_INCONSISTENT`。
- `sbs_target_echo` 必须等于该 request 的 `sbs_target`(第 5.3 节已核对;事务内再比一次)。
- **同一 request 已有终态 RESULT 时**:
  - 读到的归一状态不同 → `REJECTED_STATE_INCONSISTENT`,不写(终态构建的状态不应改变);
  - 状态相同,且 `accepted`、`sbs_target_echo`、`per_arch_status_json` 均与最新 RESULT 相同 → 幂等,输出已有 event,不写;
  - 状态相同但 `accepted` 等判定字段有变化(例如有人在 QuickBuild 上点了 Accept)→ 写新结果文件并追加新的 RESULT,旧事件与旧文件保留;最新 RESULT 为权威(两级最新);不重复追加状态。

---

## 6. 数据、写入原语与状态

### 6.1 表与查询

- 新表 `campaign_qb_profiles`(第 2.2 节)。`campaign_qb_requests` / `campaign_qb_events` 不改结构。
- 新只读查询 `qb_profile(state_db, branch)`。
- 事件语义修订:`SUBMITTED` = "提交意图已落库,即将放行提交"(原意"REST 提交成功"废止)。

### 6.2 按连接写入的内部原语(`campaign_state.py`)

现有 `create_qb_request`、`append_qb_event`、`append_status` 各自打开连接并开启 `BEGIN IMMEDIATE`,无法被外层合成一个事务(外层持事务时调用会得到 `CampaignStateBusy`)。新增内部原语,沿用已有 `_append_event_on_connection` 的写法:

```python
def _create_qb_request_on_connection(conn, campaign_unit_key, *, request_id, sbs_target) -> int: ...
def _append_qb_event_on_connection(conn, *, request_seq, event_type, **fields) -> int: ...
def _append_status_on_connection(conn, campaign_unit_key, status, reason=None, arch_norm=None) -> None: ...
def _insert_qb_profile_on_connection(conn, branch, *, profile_json: str) -> None: ...
```

- 原语只做校验与写入,**不初始化 schema、不开启/提交/回滚事务、不关闭连接**;调用方负责一个 `BEGIN IMMEDIATE` 事务。
- `_insert_qb_profile_on_connection`:`profile_json` 必须是第 2.2 节定义的规范化 JSON 原文,原语不再二次序列化;原语内部计算 `profile_sha256 = sha256(profile_json 的 UTF-8 原始字节)`、`created_at` = 当前 UTC ISO8601,与 `profile_json` 一并写入;冲突处理见第 2.2 节。
- 现有三个公共 API 改为"开连接 → 开事务 → 调原语 → 提交",对外行为与校验不变,**包括 `create_qb_request` 对同一 `request_id`、同 unit 同 sbs_target 返回既有 `request_seq` 的幂等行为**(既有测试全部保持通过)。
- P5Q 的每个写入点都是一个事务:提交意图(冻结行 + request + SUBMITTED + 状态)、确定未放行(状态)、绑定(BUILD_BOUND + 状态)、非终态(状态)、结果(RESULT + 状态)。

### 6.3 状态迁移(在 design.md §3.6 基础上)

| 从 | 触发 | 到 |
|---|---|---|
| SANDBOX_PUSHED / KB_APPENDED / QB_SUBMIT_FAILED | qb-trigger 第 8 步 | QB_REQUESTED |
| SANDBOX_QB_FAILED、QB_REQUESTED(未绑定) | 带 `--retrigger` 的 qb-trigger 第 8 步(新 request) | QB_REQUESTED |
| QB_REQUESTED | 提交确定未放行 | QB_SUBMIT_FAILED |
| QB_REQUESTED | 落点 build 且核对通过,或人工绑定成功 | QB_TRIGGERED |
| QB_TRIGGERED | fetch 读到非终态 | SANDBOX_QB_PENDING |
| QB_TRIGGERED / SANDBOX_QB_PENDING | fetch 读到 PASS | SANDBOX_QB_PASS |
| QB_TRIGGERED / SANDBOX_QB_PENDING | fetch 读到终态失败 | SANDBOX_QB_FAILED |

QB_TRIGGERED 首次读取即终态时直接迁到 SANDBOX_QB_PASS / SANDBOX_QB_FAILED。KB_APPENDED 尚由 P8 实现;P5Q 期间从 SANDBOX_PUSHED 直接进入 QB_REQUESTED。SANDBOX_QB_FAILED 仍是修复循环意义上的终态,只能经显式 `--retrigger` 开新 request,旧 request 与其事件永不覆盖。

---

## 7. 错误码(新增或语义修订,同步登记 design.md §4.3)

```
REJECTED_QB_PROJECT_NOT_READY     unit.branch 无对应工程配置,或该工程未启用
REJECTED_QB_PARAMS_CHANGED        当前配置或表单读回值与本 campaign 已冻结的复验参数不符
REJECTED_QB_SNAPSHOT_UNAVAILABLE  SNAPSHOT_NUM 无选中项,或冻结值已不在下拉框中
REJECTED_QB_FORM_CHANGED          配置页/表单结构与已取证结构不符,或提交前读回指纹变化
REJECTED_QB_FORM_MISMATCH         填表后读回值与要求值不等,或要求的下拉选项不存在
REJECTED_QB_REQUEST_PENDING       --retrigger 被拒:最新请求的构建仍在运行或已通过;
                                  或 review-submit 人工降级时存在未出结果的复验请求
QB_SUBMIT_FAILED                  (语义修订)提交意图已落库,但提交请求确定未放行
QB_SUBMIT_UNCERTAIN               提交请求已放行,无法确定是否已产生构建;状态保持 QB_REQUESTED
QB_LOGIN_TIMEOUT                  登录窗口超时未完成登录
QB_LOGIN_ABORTED                  登录窗口被关闭
QB_BROWSER_UNAVAILABLE            Node/Playwright/Chromium 不可用,/dev/shm 不可用,或代理异常退出(提交放行前)
QB_RESULT_UNRECOGNIZED            构建状态文字或页面结构无法识别,不写 RESULT
QB_FETCH_FAILED                   读取页面失败(非 200、重定向、构建号不符、登录失效、代理异常),不写 RESULT
QB_EVIDENCE_REDACTION_FAILED      证据写后脱敏自检失败,证据删除,不写 RESULT
```

`REJECTED_SANDBOX_NOT_BOUND`、`REJECTED_QB_BINDING_MISMATCH`、`REJECTED_QB_SUPERSEDED`、`REJECTED_STATE_INCONSISTENT`、`AmbiguousQbReference`、`CAMPAIGN_STATE_BUSY`、`INTERNAL_ERROR` 沿用,适用场景按本文扩展。代理内部应答(`QB_FORM_CHANGED`、`QB_FORM_VALUE_UNAVAILABLE`、`QB_READ_REDIRECTED`、`QB_READ_ID_MISMATCH`、`AGENT_PHASE`)只在代理协议内使用,不作为 CLI 错误码输出。

---

## 8. 安全要求汇总(验收逐条对应第 9 节用例)

1. 工具只在一个地方发起构建:`submit` 放行的那一次表单 action;每个表单至多一次;多个 unit 时每个 `open_form` 各至多一次。
2. 永远不发出 Ready to Accept、取消、停止、重跑、删除、REST、日志/报告/产物下载请求,包括重定向的后续跳;不使用绕开页面拦截的 HTTP 客户端。
3. 提交一旦放行,不再有"确定失败"的结论;不确定时不自动重提,只有人工 `--retrigger`。
4. 构建与请求的对应只靠回显:请求标记 + 目标行 + 子构建 TRIGGER_ID + 配置路径 + 页面构建号;任何一项对不上都不绑定、不写 RESULT。
5. PASS 只来自子构建 Status 的精确文字 `Successful`,且子构建回显 `FAIL_FAST=yes`、架构为固定值、逐架构状态为空;无法识别一律不写 RESULT。
6. 表单每个字段显式设值、逐项读回、提交前指纹复核;表单结构变化即停。
7. 复验参数每个 campaign × 工程冻结,配置改动只影响新 campaign;架构与失败传播相关参数不开放配置。
8. 凭据:工具不接触用户名密码;会话与 cookie 只在"浏览器 + 专用代理进程"可信边界内,协议事件中的请求头与请求体在适配层立即丢弃,不进入判定以外的任何代码、日志、文件或对 Python 的应答;浏览器临时目录在内存盘并在退出时删除;所有页面落盘前脱敏、写后自检。
9. 远端 sandbox ref 核对使用 P5 的隔离传输与统一 git 环境,远端地址由配置构造。
10. 每个数据库写入点是一个事务;复验未出结果期间不构成 P5R 人工降级条件。
11. 拦截面在首个页面导航前装好,覆盖 HTTP 每一跳(含 307/308 的响应阶段终止)、WebSocket 与新目标;Worker 类目标与新窗口执行前阻断。

---

## 9. 验收用例(DoD)

### 9.1 Python 侧(假代理,CI 必跑)

用一个实现第 3.2 节协议的假代理(Python,按用例脚本应答,并记录收到的每条命令)驱动 CLI,真实 state DB 与本地裸仓库。

触发前置与幂等:
- [ ] 状态不足、无 DERIVE、无 PUSH、PUSH result≠ok、pushed_sha≠derived、ref 不在白名单,各自独立 → `REJECTED_SANDBOX_NOT_BOUND`,假代理 `submit` 0 次。
- [ ] PUSH 事件为 P5 实际形态(`url=None`)时正常通过。
- [ ] 远端 ref 在填表后被改(本地裸仓库改写)→ `REJECTED_SANDBOX_NOT_BOUND`,无新 request。
- [ ] 隔离传输:主副本 `.git/config` 加一个名字等于远端地址字符串的具名远端、以及 `url.<x>.insteadOf`/`pushInsteadOf` 指向另一个含假 sandbox ref 的裸仓库 → 核对结果取自真实远端;用 git 调用包装统计 argv,断言没有任何 git 命令以主副本为 `-C`/`--git-dir`。把 `_sandbox_git` 的任一覆盖项移除(变异)→ 本例必须变红。
- [ ] 正确 sha 存在于另一个仓库、目标仓库的 ref 指向别的 sha → `REJECTED_SANDBOX_NOT_BOUND`。
- [ ] 第 4.2 节幂等表每一格一例(含带/不带 `--retrigger`),断言 submit 次数与新增 request 数。
- [ ] `--retrigger` 追加新 request,旧 request 及其事件逐字段不变。
- [ ] 第 8 步事务内重查发现并发写入改变状态或最新 request → `REJECTED_STATE_INCONSISTENT`,事务回滚无残留,submit 0 次。
- [ ] 多 unit:三 unit 的 `--units-file`,第 2 个在 `fill` 失败 → 假代理收到 `open_form` 3 次、`submit` 2 次;恰好 2 个新 request;第 2 个 unit 无任何写入;三项 action 依次为 `submitted_bound`/`rejected`/`submitted_bound`。

填表与提交:
- [ ] `open_form` 返回表单已变 / 字段集合多一项 / 少一项 / 双列表少一个角色 / 多一个同标签控件 → `REJECTED_QB_FORM_CHANGED`,无 DB 写入。
- [ ] 读回值任一项不等(逐字段各一例,含 Build Package List 多一行、尾随空格、Add Package List 非空、CHILD_CONFIGURATIONS 多一项、recorder 与 selection 不一致)→ `REJECTED_QB_FORM_MISMATCH`。
- [ ] SNAPSHOT_NUM 冻结值不在下拉框 → `REJECTED_QB_SNAPSHOT_UNAVAILABLE`;且同 campaign 中已有终态 RESULT 的其它 unit 的事件与结果文件逐字段不变。
- [ ] `@freeze`:选项一个 → 冻结成功;选项多个、有选中项 → 冻结选中项,trace 含选项数;无选中项 → `REJECTED_QB_SNAPSHOT_UNAVAILABLE`。
- [ ] `released: false` → 状态 QB_SUBMIT_FAILED、该 request 只有 SUBMITTED;**紧接着不带 `--retrigger` 重跑 → 产生新 request,submit 恰好被调用一次**(幂等表第 2 行先于第 3 行匹配的退化守卫)。
- [ ] 落点 build 且回显一致 → SUBMITTED + BUILD_BOUND + QB_TRIGGERED。
- [ ] 落点 build 但请求标记不符 / P 已绑定到其它 request → 无 BUILD_BOUND,`submit_uncertain`,`REJECTED_QB_BINDING_MISMATCH`。
- [ ] 落点 unknown(含"停在表单页并有错误提示"的情形)→ 只有 SUBMITTED,状态 QB_REQUESTED,`error_code == QB_SUBMIT_UNCERTAIN`;不带 `--retrigger` 重跑 → `already_requested`,submit 0 次。
- [ ] 第 4.4 节每个崩溃点一例(第 8 步事务中途、事务后放行前、放行后写库前)注入异常并重跑,断言 request 条数、事件与状态。
- [ ] 登录超时 → 无 DB 写入,exit 5。

参数冻结与配置:
- [ ] 首次触发写冻结行;第二个 unit 同 branch 复用;改配置任一键 → `REJECTED_QB_PARAMS_CHANGED`,且不启动代理。
- [ ] 新 state DB 用改后的配置可正常冻结新值;两个 branch 各自冻结,`qb_profile` 按 branch 取得各自的行。
- [ ] 冻结行原语第二次写不同内容 → StateInconsistent;同内容 → no-op。
- [ ] 冻结行的 `profile_sha256` 等于 `profile_json` 原始字节的 sha256,`created_at` 为合法 UTC ISO8601;直接 INSERT 63 位 `profile_sha256` → 被 CHECK 拒。
- [ ] 并发冻结:在第 5 步之后、第 8 步之前用另一连接插入同 branch、内容相同的冻结行 → 本 unit 正常提交、不新增冻结行;内容不同 → `REJECTED_QB_PARAMS_CHANGED`,无 request。
- [ ] 配置中 CHILD_CONFIGURATIONS 为单架构 / 缺架构 / 重复 / 多组,`Immediate Stop With Error: false`,TARGET_IMAGE 非空 → `INVALID_ARGS`,不启动代理。

读取与落库:
- [ ] 第 5.3 节每一条核对各一个负例 → `REJECTED_QB_BINDING_MISMATCH`,无 RESULT;含 Child Build 表一行但架构与固定值不等、子构建 `FAIL_FAST=no`、`FAIL_FAST` 缺失。
- [ ] `EACH_GBS_BUILD_STATUS` 非空 → `QB_RESULT_UNRECOGNIZED`,无 RESULT,stdout 含处置指引文本、trace 记录证据路径;此状态下 `--retrigger` → `REJECTED_QB_REQUEST_PENDING`(把这一停止-报告行为钉成已知行为);为空 + `FAIL_FAST=yes` + `Successful` → PASS,`per_arch_status=null`。
- [ ] Child Build 表为空 → 非终态,无 RESULT,状态 SANDBOX_QB_PENDING;再次读取不重复追加状态。
- [ ] Child Build 表为空,但父构建请求标记 / 目标行 / 冻结参数任一不符 → `REJECTED_QB_BINDING_MISMATCH`,零 BUILD_BOUND(人工绑定)、零 RESULT、无 PENDING 状态;全部相符 → 可绑定并进入 PENDING。
- [ ] Child Build 表两行 → `QB_RESULT_UNRECOGNIZED`。
- [ ] 第 1 节状态表每一行一例;`" Successful "` 经去首尾空白 → PASS;`Success ful`、`successful`、`Success` → `QB_RESULT_UNRECOGNIZED`,无 RESULT。
- [ ] 代理 `read` 返回重定向 / 构建号不符 → `QB_FETCH_FAILED`,无 RESULT。
- [ ] PASS 写 RESULT:文件 sha256 = 事件 `qb_result_sha256`;`latest_qb_result` 两级最新返回该事件;文件键集合固定。
- [ ] 首次读取即 PASS、首次读取即终态失败,各一例(QB_TRIGGERED 直达)。
- [ ] 终态 RESULT 后再次读取:同状态同字段 → 不新增;同状态 accepted 由 false/null 变 true、由 true 变 false → 新 RESULT 与新文件,旧事件与文件不变,最新事件字段正确;状态不同 → `REJECTED_STATE_INCONSISTENT`。
- [ ] `accepted` 解析:`ACCEPTED`、`ACCEPTED (2026-10-10 12:00)` → true;`ACCEPTED_BY_X`、`NOT_ACCEPTED` → false;无该栏 → null。
- [ ] 非最新 request → `REJECTED_QB_SUPERSEDED`,不读取;读取期间被 retrigger(并发)→ 落库事务重查失败,回滚并删除结果文件。
- [ ] 人工指定绑定:成功;P 已绑定到其它 request → 拒;unit 状态 QB_SUBMIT_FAILED → 拒;请求标记不符 → 拒。
- [ ] `--qb-build-id` 单独且未 BUILD_BOUND → exit 4,不挂到最新 request。

事务与原语:
- [ ] 每个写入点(意图、确定未放行、绑定、非终态、结果)在事务中途注入异常 → 整组回滚,无半提交。
- [ ] 外层持 `BEGIN IMMEDIATE` 时调用四个原语成功;公共 API 行为与既有测试一致。

凭据与脱敏:
- [ ] 假代理在页面中植入登录显示名、hidden token、`jsessionid=` URL、`JSESSIONID_8810=` 文本 → 证据文件、stdout、stderr、trace、qb_result 中均不出现(扫描断言);双列表 recorder 原值保留。
- [ ] 写后自检失败(注入)→ 证据删除,`QB_EVIDENCE_REDACTION_FAILED`,无 RESULT。
- [ ] 假代理任何命令的应答中出现 `cookie`、`set-cookie`、`authorization` 键 → Python 侧拒收并 `QB_BROWSER_UNAVAILABLE`。

### 9.2 浏览器代理(Node,离线必跑)

- [ ] 判定函数自检(参照 spike `--policy-self-test` 写法):第 3.4 节每条永久禁止各一例(含产物下载、`/log`、`/html_report`、WebSocket、307/308);各阶段放行项各一例;阶段外的放行项拒绝(未 `submit` 时的表单 action、`fill` 之外的字段回调);只读路径带查询拒绝;登记地址改一个字符拒绝;查询中含 `stop` 字样但监听器名无破坏性动作的合法回调 → 放行;`ILinkListener-content-buildHead-cancel` 形态 → 拒绝。
- [ ] 命令阶段机:阶段不对的命令全部 `AGENT_PHASE`;连续两次 `open_form`,每次至多放行一次提交;`fill` 失败后不经新 `open_form` 的提交拒绝。
- [ ] 命令阶段机补充:`submit` 指纹不符后再次 `submit` → `AGENT_PHASE`。
- [ ] 字段回调逐字段登记:同一字段的旧版本回调地址在该字段操作结束后被拒;另一字段的回调地址在当前字段操作期间被拒;形态不符的回调地址 → `QB_FORM_CHANGED`。
- [ ] 307、308 在响应阶段终止(判定函数层);合法 302 继续并对下一跳重新判定。
- [ ] 协议适配层单元测试:构造含 Cookie、Authorization 请求头与含密码请求体的合成协议事件 → 交给判定逻辑的对象只含第 3.1 节列出的元数据;异常路径输出只有固定错误类别。
- [ ] 进程退出(正常、异常、SIGTERM)后 `/dev/shm` 临时目录不存在。
- [ ] 源码静态断言:代理源码不出现 `page.request`、`context.request`、`newContext(` 的请求上下文用法、`.cookies(`、`storageState`、`ignoreHTTPSErrors: true`、协议调试日志开关;`login` 命令实现中不出现 `click(`、`fill(`、`press(`、`type(`、`evaluate(` 等交互调用;除协议适配层外无代码引用 `headers`、`postData`、`postDataEntries`;`qb_browser.py` 不传任何测试专用参数(见 9.3)。

### 9.3 本机浏览器集成(FatTank 开发机执行,CI 中 skip)

假 QuickBuild 的运行方式:本地 HTTPS 服务器,用测试专用证书;Chromium 用 `--host-resolver-rules` 把 `quickbuild.tizen.org` 解析到本机,并用只信任该测试证书的启动参数。这两个参数只能由集成测试入口传给代理,代理生产路径的 origin 判定、证书校验不变;生产 CLI 静态断言不含这两个参数(9.2)。页面以 `rbs-form-01/form.redacted.html` 为模板,**保留其页面脚本依赖**(jquery、main.js、Wicket 脚本及双列表 onchange 行为),服务器记录实际收到的每一个请求。

- [ ] 正常路径:登录检测(假登录页)→ `open_form` → `fill` → `submit` → 落点 build。断言服务器只收到一次提交;收到的提交载荷中 Build Package List、BUILD NOTES、双列表 recorder 精确等于要求值;从未收到任何禁止类请求。
- [ ] 逐跳拦截:放行地址返回 302 到 `/rest/trigger`、到 `ILinkListener-content-buildHead-promote`、到外站 → 服务器未收到第二跳;307 重放 POST → 未收到。
- [ ] 读取:`/build/C` 页面重定向到 `/build/D`(D 页显示 Successful)→ `QB_FETCH_FAILED`;服务器端记录确认未据 D 判定。
- [ ] 提交后服务器先记录"已建构建"再返回带错误提示的表单 → 落点 unknown;重跑零新增提交。
- [ ] 提交后不跳转 → unknown;表单多一个字段 → `QB_FORM_CHANGED`;表单页带定时 `ajaxRefresh` → `fill` 仍能完成。
- [ ] 登录检测真假阳性:仍在 `/signin` 但页面含 Sign Out 字样、已跳离 `/signin` 但仍有密码框、无 Sign Out 链接 → 均判未登录;三条件齐备 → 已登录。
- [ ] 页面脚本尝试 `window.open`、iframe 指向外站 → 窗口被关闭、请求被拒,计数正确。
- [ ] Worker 与 WebSocket:页面创建 `SharedWorker`、`Worker` 并在其中请求 `/rest/trigger`;页面创建 ws/wss 连接;新目标在首个请求上抢跑 → 服务器均未收到;对应目标被关闭并计数。
- [ ] 307/308:放行地址分别以 307、308 跳到另一个**原本合法且已登记**的地址 → 服务器未收到第二跳;同时保留一条合法 302 路径,断言其第二跳正常到达(防止实现简单地禁掉所有重定向)。
- [ ] 页面版本递增:假服务器每次字段回调后递增页面版本并重渲染各字段回调地址 → `fill` 十二个字段全部完成,服务器收到的回调数等于设值次数;假服务器返回与 DOM 不一致的回调地址 → 被拒。
- [ ] 表单结构:以真实 HTML 中只读 PROJECT_NAME(`property-viewer`)结构为正常样本;重复只读区域、缺区域、值不等 → `QB_FORM_CHANGED`。
- [ ] 对称用例:服务器返回带错误提示的表单且**未**建构建 → 同样落点 unknown、同样不自动重提(工具侧两种情况不可区分,这一点要钉进用例)。
- [ ] 登录:人工点击登录按钮之前,服务器未收到任何 `/signin` POST;登录后跳转到未登记落点 → 被拦截,登录超时。
- [ ] 凭据隔离:浏览器真实请求携带合成 Cookie、Authorization 与合成登录密码 → Node→Python 协议、stdout、stderr、trace、证据文件中均不出现;在适配层注入异常后同样不出现原始事件。
- [ ] 执行记录(命令、输出、服务器收到的请求清单)归档到 stage 证据目录。

本节中"Worker 与 WebSocket""307/308""凭据隔离""逐跳拦截"四组属于拦截安全子集,**必须在 C2 的真实只读取证之前**在 FatTank 开发机上跑通并归档;其余在 C5 完成。

### 9.4 真实 QuickBuild(三步,均需 FatTank 在场)

1. **只读取证(随 C2 执行,C3 开工前置)**:用新代理只读模式读取 FatTank 已有的 RBS 构建 1193467(父)与 1193469(子)的 `/build`、`/variables`、`/step_status`,以及 RBS 配置页。必须确定并写入附录 C:
   - RBS 配置页的 `overview_id` 与 `<title>` 形态;
   - 父构建变量页中 Build Package List、BUILD NOTES、BUILD_TYPE、BUILD_REFERENCE、SNAPSHOT_NUM、PROJECT_BRANCH 的回显变量名、显示名与行号;
   - 子构建配置路径末段;子构建变量页 TRIGGER_ID、BUILD_PKG_LIST、FAIL_FAST、EACH_GBS_BUILD_STATUS 是否存在、行号与值形态;
   - Child Build 表结构是否与 SBS 样本一致;Repository-Architecture 列与固定架构值的比较口径(是否就是冒号连接串、是否带其它文字);
   - 登录检测三条件在真实页面上的表现;登录成功后的实际跳转落点集合;被拒的静态资源路径清单;
   - 失败样本:FatTank 提供的已失败构建 **1186372**(父)。读取其 `/build`、`/variables`、`/step_status`,由 Child Build 表找到子构建并读取同样三页;先核对其配置路径确为 RBS/TRIGGER(不是则停止报告,不作为样本);记录子构建 Status 文字、`EACH_GBS_BUILD_STATUS` 的值形态,以及 Child Build 表中失败时的 Build Result 文字(用于按 R1 定义逐架构解析规则,并坐实第 1 节 `Failed` 一行)。
   任一项缺失或与本文假设不符 → 停止并报告,按 R1 修订本文,不得用 SBS 字段代补;C3 不开工。
   本步之前,第 9.3 节的拦截安全子集必须已在本机跑通。
1.5. **表单联动取证(随第 1 步执行,不产生构建)**:在真实 RBS 表单上执行 `open_form` → 把 BUILD_TYPE 从 `Full` 改为 `Partial` 再改回 `Full`(设同一个值不会触发回调,所以要改一次再改回)→ `close`,**不调用 `submit`**。记录设值前后字段回调地址与表单 action 是否变化、页面版本号变化方式、是否有整页重渲染 GET,写入附录 C。此步只进入表单页,提交地址从未放行,代理记录保持 `not_released`,不会建构建。
2. **一次确认的真实提交(收口前最后一步)**:目标由 FatTank 指定(建议一个已在快照中的小包、用它当前已合入的 commit,构建内容与快照一致,不引入新代码)。工具先在 Codex 对话中打印全部十二个字段的拟填值与目标行,FatTank 在对话里确认后才执行 `qb-trigger`;随后执行 `qb-result-fetch` 至少一次。记录:提交后的实际落点、构建号获取方式、父子页面回显是否与只读取证结论一致、父构建回显的 SNAPSHOT_NUM 是否等于冻结值。若落点不是 `/build/<id>`,用第 5.2 节人工绑定完成闭环并记录。此步完成前 P5Q 不得 CLOSED。

### 9.5 通用门禁

- [ ] 全量测试、mypy、ruff 通过;Node 自检通过。
- [ ] `tests/unit/test_campaign_state.py::test_ensure_schema_creates_exact_campaign_tables_and_required_guards` 的期望表集合与 DDL 同一提交更新(增加 `campaign_qb_profiles`),并补该表 CHECK 负例(`profile_sha256` 非 64 位小写十六进制)。
- [ ] design.md 检查器通过(新增错误码已登记 §4.3)。
- [ ] 每个提交同步更新 stage 进度文件。

---

## 10. 提交计划

| 提交 | 内容 | 依赖 |
|---|---|---|
| C0 | design.md 同步(附录 A);stage20 进度文件建立 | 无 |
| C1 | `qb_redact.py`;配置解析与校验;`campaign_qb_profiles` 表、四个按连接写入原语与公共 API 重构、`qb_profile` 查询;既有精确表集合测试同步;第 9.1 节冻结、配置、原语、脱敏用例 | C0 |
| C2 | `qb_browser_agent.mjs`(三个拦截面与协议适配层)+ `qb_browser.py` + 假代理;第 9.2 节;第 9.3 节拦截安全子集(本机);**随后执行第 9.4 节第 1、1.5 步并填附录 C** | C1 |
| C3 | `qb-trigger` CLI 及第 9.1 节触发/填表/崩溃/多 unit/隔离传输用例 | C2 及只读取证结论 |
| C4 | `qb-result-fetch` CLI、人工绑定及第 9.1 节读取/落库用例 | C3 |
| C5 | 第 9.3 节其余本机浏览器集成及证据归档 | C4 |
| C6 | 第 9.4 节第 2 步真实提交与收口文档 | C5 + FatTank 确认 |

C2 的真机取证若发现与本文假设不一致(例如变量页没有 BUILD NOTES 回显、回调地址形态不同),停止,先按 R1 修订本文再继续 C3。

---

## 附录 A:design.md 同步(C0 照录,design.md 升 v1.5.22)

在 §4.4 之后新增 §4.5,原文如下:

> ### 4.5 v1.5.22 修订:P5Q 复验触发改为 RBS 网页表单
>
> P5Q 模块(qb_browser_agent、qb_browser、qb_redact、qb-trigger、qb-result-fetch)的权威契约见 `p5q-qb-trigger-design-v1.x-FROZEN.md`,与本文其它章节冲突时以该文件为准。
>
> 1. 不使用 QuickBuild REST 接口与 Basic Auth;QB_PASSWORD 不再使用。复验触发由工具驱动独立浏览器窗口在 RBS/TRIGGER 配置的运行表单上填表提交;登录由人在该窗口完成;凭据可信边界为浏览器与专用代理进程,协议事件中的请求头与请求体在适配层立即丢弃;所有请求经逐跳拦截,WebSocket 与 Worker 类目标一律阻断。
> 2. 复验流水线为 RBS/TRIGGER(非 SBS),按 campaign_units.branch 选择 QuickBuild 工程;命令 `qb-sbs-trigger` 更名为 `qb-trigger`。
> 3. 目标行写入表单 Build Package List,格式 `仓库路径@commit`,只写一行;表字段 `sbs_target` 保留原名,语义为该行。
> 4. 每次提交在 BUILD NOTES 写入请求标记 `clang-fix-campaign request=<request_id>`;构建与请求只凭回显的请求标记、目标行、子构建 TRIGGER_ID、配置路径与页面构建号对应。
> 5. `SUBMITTED` 事件语义改为"提交意图已落库,即将放行提交";意图先于放行写入。提交一旦放行,不存在"确定失败"结论;无法确定是否已提交时不自动重提。`QB_SUBMIT_FAILED` 只表示意图已落库但提交确定未放行。
> 6. 通过判据为子构建 Status 精确等于 `Successful`,且子构建回显 `FAIL_FAST=yes`、架构为 `standard-armv7l:aarch64:x86_64`、逐架构状态为空;`qb_pass_requires_accept` 默认 false,与其它复验参数一起在每个 state DB、每个 branch 首次触发时冻结于新表 `campaign_qb_profiles`,P5R 按 unit.branch 从该表读取。
> 7. 工具永远不点 Ready to Accept;推送 sandbox 分支不会自动触发 QuickBuild 构建,P12 首次真实推送后观察确认。
> 8. EF-5:①REST 探活不再需要;③SBS 构建只读取证与 RBS 表单结构证据已取得,RBS 构建页完整字段映射由 P5Q 设计文件第 9.4 节第 1 步确定,确定后 P5Q 的 qb-trigger 才开工;④accept 语义已由 FatTank 裁定;②真实提交的响应形态移入 P5Q 收口前的确认提交(P5Q 设计文件第 9.4 节第 2 步),不再作为 P5Q 开工门。
> 9. campaign-preflight 取消 QB REST 探针与 QB_PASSWORD/QB_COOKIE 检查,改为检查 Node、Playwright 模块、Chromium 路径与 /dev/shm 可用。
> 10. review-submit 的人工装配降级判据收紧为:最新 request 完全不存在 RESULT 行,**且**该 unit 最新状态不属于 {QB_REQUESTED, QB_TRIGGERED, SANDBOX_QB_PENDING};处于这三个状态表示存在未出结果的复验请求,一律 exit 4 `REJECTED_QB_REQUEST_PENDING`,不得降级、不得打印 push 命令。复验请求确已失效(QuickBuild 侧构建丢失或永久无法读取)时,由人用 `--retrigger` 产生新 request,或按 R2 带外处置后再降级。降级仅作为 P5R 的工具故障通道,不作为复验未完成通道。
> 11. qb_result 文件 schema 以 P5Q 设计文件第 5.4 节为准。review-submit 接受该 schema:`per_arch_status` 为 null 与数据库 NULL 表示未提供独立架构状态,不启动逐架构校验,非空映射才按架构校验;`accepted` 可空,冻结参数要求 Accept 时只有数据库 accepted=1 才通过,NULL 与 0 均不通过。"已有 RESULT 而校验失败不得降级"不变。
> 12. 同一 request 已有终态 RESULT 后,状态不变而 accepted 等判定字段变化时,追加新的 RESULT,最新 RESULT 为权威;状态改变视为状态不一致。
> 13. 新增 `campaign_state` 按连接写入的内部原语;P5Q 的每个写入点在一个事务内完成。

同时:

- §0 元信息:版本行改为 v1.5.22,加变更记录一行;§4.4 标题改为"v1.5.20–v1.5.21 修订:P2–P5 落地裁定"。
- §1.4 EF-5 条目末尾加一行:"(v1.5.22)按 §4.5 第 8 条处理。"
- §3.4 campaign schema 代码块末尾追加 `campaign_qb_profiles` 的 DDL(照录 P5Q 设计文件第 2.2 节),并在迁移说明后补"(v1.5.22:新增 `campaign_qb_profiles`)"。
- §3.6 转移表:`QB_REQUESTED` 的进入条件改为"提交意图已落库(SUBMITTED 已写),尚未确认构建";按 P5Q 设计文件第 6.3 节追加转移行(含 retrigger 回到 QB_REQUESTED、确定未放行到 QB_SUBMIT_FAILED、QB_TRIGGERED 首次读取即终态直达);`SANDBOX_QB_FAILED` 的终态标注后补"(可经显式 `--retrigger` 开新 request;旧 request 与其事件永不覆盖)"。
- §4.1 中 `qb-sbs-trigger` 与 `qb-result-fetch` 两段之前各加一行:"(v1.5.22)本命令契约以 P5Q 设计文件第 4、5 节为准。";review-submit 段校验链第 2 项之前加一行:"(v1.5.22)人工降级判据与 qb_result schema 按 §4.5 第 10、11 条。"
- §4.2 `campaign_state` 签名块追加 `def qb_profile(state_db, branch: str) -> dict | None: ...  # v1.5.22:只读,按 campaign_units.branch 取冻结的复验参数`。
- §4.3 按 P5Q 设计文件第 7 节登记新增错误码,并把 `QB_SUBMIT_FAILED` 的说明改为"提交意图已落库但提交请求确定未放行(v1.5.22)";`REJECTED_QB_BINDING_MISMATCH` 的说明补"含请求标记、目标行、TRIGGER_ID、配置路径、FAIL_FAST 回显"。
- §7 Phase 5Q 标题改为"Phase 5Q: qb-trigger + qb-result-fetch",范围行前加:"(v1.5.22)范围与 DoD 以 P5Q 设计文件第 0.3、9 节为准。";Phase 5R 范围行前加:"(v1.5.22)人工降级判据与 qb_result schema 按 §4.5 第 10、11 条。";Phase 8.5 范围行前加:"(v1.5.22)探针项按 §4.5 第 9 条调整。"
- 引用本文章节一律写作"P5Q 设计文件第 x 节",不使用 § 符号(避免检查器按 design.md 内部章节解析)。

## 附录 B:证据索引

| 事实 | 证据路径(仓库内,`E` = `docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence`) | 流水线 |
|---|---|---|
| 子构建 Status=Successful、无 SR_STATUS 栏 | `E/web-cookie-02/01.response.txt:832` | SBS |
| 子构建 TRIGGER_ID、BUILD_PKG_LIST、FAIL_FAST、EACH_GBS_BUILD_STATUS(空) | `E/web-cookie-02/03.response.txt:804` | SBS |
| 父构建显示名 Build Package List 对应 BUILD_PKG_LIST_MODIFY | `E/web-cookie-02/facts.json`(`parent_BUILD_PKG_LIST_MODIFY`) | SBS |
| HTML REPORT 只有 iframe | `E/web-cookie-02/05.response.txt:805` | SBS |
| 父构建步骤页链接子构建 | `E/web-cookie-02/06.response.txt:1189` | SBS |
| 配置页运行按钮指向 `ILinkListener-run` | `E/web-cookie-02/07.response.txt:699` | SBS |
| 表单字段、标签、双列表三元素、AJAX 回调、按钮 | `E/rbs-form-01/form.json`、`form.redacted.html:720-1110` | RBS |
| 表单页依赖的静态资源 | `E/rbs-form-01/form.redacted.html:24-40` | RBS |
| Ok 为整表提交;Cancel 为 `ILinkListener-form-cancel` | `E/rbs-form-01/form.redacted.html:1109-1110` | RBS |
| RBS 父构建 Child Build 表、Not Finished 文字 | FatTank 截图(构建 1193467),第 9.4 节第 1 步入库 | RBS |
| 登录跳转落点 `/`、`/overview/0` | `docs/clang-fix-campaign/spikes/ef5_browser_login.mjs:15` | — |
| PUSH 事件 `url=None`,远端由配置构造 | `tizen-ci-triage/scripts/ci_triage/sandbox_submit.py:709,808-819` | — |
| Ready to Accept 链接特征 | 外部参考(团队 quickbuild-sbs `create_sbs.py`),仅用于禁止名单 | — |

## 附录 C:只读取证结论(第 9.4 节第 1 步完成后由实现方照录)

(待填:RBS 配置 `overview_id` 与标题形态;父构建变量页各回显变量名、显示名与行号;子构建配置路径末段;子构建 TRIGGER_ID、BUILD_PKG_LIST、FAIL_FAST、EACH_GBS_BUILD_STATUS 的存在性、行号与值形态;Child Build 表结构与 Repository-Architecture 比较口径;登录检测在真实页面的表现与登录落点集合;被拒静态资源清单;失败样本(若有)的 EACH_GBS_BUILD_STATUS 形态;第 1.5 步记录的回调地址与表单 action 在设值前后的变化方式。)

## 附录 D:v1.0 → v1.1 修改记录(第一轮评审)

采纳原则:三家意见先回仓核对证据;同一问题多家提出时比较各家方案取最稳妥者,写明采用谁的、为什么。

### 阻断

| 编号 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|
| 1 | `page.request` 共享浏览器 cookie 却不经过页面拦截,可绕过白名单 | ChatGPT(离线复现) | 采用 ChatGPT:禁止一切代理侧 HTTP 客户端,只读改为页面导航;另加源码静态断言(吸收 Kimi 对 cookie 读取的静态断言建议) | 3.1、3.6、9.2 |
| 2 | 路由只拦重定向首跳;只读路径未要求查询为空;跳转放行过宽 | ChatGPT(离线复现) | 采用 ChatGPT 总则,并具体化:DevTools 请求阶段逐跳拦截,所有放行地址精确登记、只读路径查询为空、禁 307/308、读取核对最终地址与页面构建号;以服务器实收请求证明 | 3.4、3.6、9.2、9.3 |
| 3 | "停在表单并有错误"不能证明未建构建,会触发自动重复提交 | ChatGPT | 采用 ChatGPT:放行后一律 unknown;"确定未提交"只来自代理记录的"从未放行" | 3.4、3.5、4.2、4.3、7、附录 A 第 5 条 |

### 重要

| 编号 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|
| 4 | 架构集合可配置,但 PASS 依赖"三架构总状态"的假设 | ChatGPT | 采用 ChatGPT:固定架构值,失败传播相关参数不开放配置 | 0.4、2.1、9.1 |
| 5 | FAIL_FAST 未进回显核对,"某架构失败仍 Successful"未堵死 | Claude Code | 采用 Claude Code 的回显核对;`EACH_GBS_BUILD_STATUS` 解析部分改为"非空即无法识别",因为唯一样本是成功构建、值为空,格式无从取证,按失败即停处理 | 5.3、5.4、8、9.1 |
| 6 | 现有写 API 各自开事务,"同一事务"不可实现;fetch 无完整锁边界 | ChatGPT、Claude Code | 采用 ChatGPT 的按连接写入原语(仓内已有 `_append_event_on_connection` 先例),不采用 Claude Code 的"三个独立事务 + 固定顺序":后者需要在每个写入点做半提交分析,原子事务更简单可靠;fetch 全程持锁、落库事务内重查 | 4.3、5.1、5.4、6.2、9.1 |
| 7 | 结果文件固定含 null 的字段与上位可选字段契约不一致 | ChatGPT | 采用 ChatGPT,写入附录 A 第 11 条约束 P5R | 5.4、附录 A |
| 8 | 只比 status 的幂等会冻结人工 Accept 前的旧值 | ChatGPT | 采用 ChatGPT:判定字段变化即追加 RESULT | 5.4、附录 A 第 12 条、9.1 |
| 9 | 非终态不写 RESULT 恰好满足 P5R 人工降级条件,复验未出结果就可降级 | Claude Code | 采用 Claude Code:收紧降级判据并写入附录 A 第 10 条 | 5.4、7、附录 A |
| 10 | 白名单拦掉表单依赖的 jquery/main.js 等静态资源 | ChatGPT | 采用 ChatGPT:按证据登记静态资源前缀,查询限 `v=数字`;集成测试保留真实脚本依赖,测试环境映射不放宽生产 origin | 3.4、9.3 |
| 11 | PUSH 事件 `url=None`,无"记录的远端" | ChatGPT | 采用 ChatGPT:远端按 P5 规则由配置构造 | 4.2、4.3 |
| 12 | 双列表标签对应三个控件,"标签唯一"不可满足 | Claude Code | 采用 Claude Code:按"标签 + 角色"定位,结构纳入表单变更检测;另加 recorder 与 selection 交叉核对 | 3.5、9.1 |
| 13 | 多 unit 时放行计数没有用例 | Claude Code | 采用 | 9.1、9.2 |
| 14 | 隔离传输与统一 git 环境没有用例 | Claude Code | 采用,含变异用例 | 9.1 |
| 15 | 新表未同步 design.md §3.4,既有"精确表集合"测试会红 | Claude Code | 采用 | 9.5、10、附录 A |
| 16 | 把 SBS 取证当作 RBS 已确认事实;父构建 Build Package List 实际对应 BUILD_PKG_LIST_MODIFY | Kimi(重要)、Claude Code(次要) | 两家合并:表格加来源列;父构建核对改为"Build Package List 的回显变量,以只读取证确定";子构建仍核 BUILD_PKG_LIST | 0.1、5.3、9.4、附录 B |

### 次要与建议

| 编号 | 问题 | 提出 | 处理 |
|---|---|---|---|
| 17 | `QB_SUBMIT_UNCERTAIN` 登记了但从未赋值 | Kimi、Claude Code | 落点 unknown 输出该码,用例断言 |
| 18 | §3.6 状态机未同步(QB_REQUESTED 进入条件、四条新边) | Kimi、Claude Code | 附录 A 补 §3.6 同步;6.3 写明首次读取即终态直达 |
| 19 | 禁止词按整串子串匹配可能误伤 | Claude Code | 锚定到 Listener 组件名,保留两个完整特征;被拒写 trace |
| 20 | 自动绑定路径未查"P 未绑定到其它 request" | Claude Code | 4.3 第 10 步补齐 |
| 21 | `@freeze` 要求恰好一个选项过脆;与 0.5 表述矛盾 | Kimi、Claude Code | 改为取当前选中项,选项数入 trace |
| 22 | 定时 ajaxRefresh 使静默窗口等不到 | Claude Code | 静默判定排除登记的定时刷新 |
| 23 | `accepted` 前缀匹配过宽 | Claude Code | 改为正则,补正负例 |
| 24 | 状态测试中尾随空格与 strip 规则相反 | ChatGPT | 改用例 |
| 25 | 附录 A 提前宣称 EF-5③已确定 | ChatGPT | 改写附录 A 第 8 条 |
| 26 | §4.4 标题版本口径 | Kimi | 附录 A 顺带改标题 |
| 27 | 缺"下载被拦截"负例 | Kimi | 9.2 补 |
| 28 | 登录自动检测是新行为,未经实证 | Kimi | 9.3 真假阳性用例,9.4 真机确认 |
| 29 | 快照冻结范围与下架处置写不清;冻结文字不能证明构建实际用了该快照 | ChatGPT、Claude Code | 0.5 写明"campaign × 工程"、已有 RESULT 不受影响;9.4 第 2 步核对父构建回显 SNAPSHOT_NUM |
| 30 | `qb_profile` 须按 branch 取 | Claude Code | 2.2 写明 |

## 附录 E:v1.1 → v1.2 修改记录(第二轮评审)

第二轮三家结论:Kimi 可冻结(4 条次要/建议);Claude Code 修改后可冻结(重要 3、次要 2、建议 2);ChatGPT 修改后可冻结(阻断 2、重要 3、次要 1)。三家都逐条核对了附录 D 的 30 条,认定全部落实。下表处理第二轮新意见。

| 编号 | 级别 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|---|
| 31 | 阻断 | 只给页面目标开请求拦截,SharedWorker 内的请求与 WebSocket 握手不经过它(离线实测服务器收到) | ChatGPT | 采用:三个拦截面(HTTP 逐跳、WebSocket 上下文级拒绝、新目标启动即暂停并阻断),首个导航前装好;以服务器实收请求为断言 | 3.1、3.4、8 第 11 条、9.3 |
| 32 | 阻断 | 调试协议把请求头(含 Cookie)与请求体(含登录密码)交给 Node 代理,"cookie 不离开浏览器进程"做不到 | ChatGPT | 采用 ChatGPT 的边界改写:可信边界定为浏览器 + 专用代理进程,适配层立即丢弃请求头与请求体;因涉及安全边界,列为第 0.5 节第二项请 FatTank 确认 | 0.1、0.5、3.1、8 第 8 条、9.2、9.3、附录 A 第 1 条 |
| 33 | 重要 | 请求阶段拿不到状态码,无法按规定识别 307/308 | ChatGPT | 采用:获准请求再在响应阶段暂停,307/308 在响应阶段终止;提交放行后被终止的仍按 unknown | 3.4、9.2、9.3 |
| 34 | 重要 | 字段回调地址在 open_form 时冻结原文,与 Wicket 页面版本递增不兼容,且自写夹具测不出 | Claude Code | 采用:open_form 只校验形态,每次设值前从活动 DOM 重读并只放行这一个地址;提交 action 同样在提交时重读;假服务器递增版本;新增第 9.4 节第 1.5 步(进表单改一个字段再关,不提交)在真机坐实 | 3.4、3.5、9.2、9.3、9.4 |
| 35 | 重要 | 幂等表第 2、3 行对同一状态同时匹配、结论相反 | Claude Code | 采用:写成互斥条件并规定自上而下第一匹配;加退化守卫用例 | 4.2、9.1 |
| 36 | 重要 | `EACH_GBS_BUILD_STATUS` 非空时无 RESULT、不能降级、不能 retrigger,形成无出路状态 | Claude Code | 采用:判据不放宽,写成"有指引的停止-报告",输出处置指引与证据路径;只读取证阶段尽量取一个失败样本 | 5.3、9.1、9.4 |
| 37 | 重要 | PROJECT_NAME 是只读显示区域,"普通字段恰好一个输入控件"会拒绝真实表单 | ChatGPT | 采用 | 3.5、9.3 |
| 38 | 重要 | Child Build 表为空时提前返回,人工绑定可能跳过父构建核对而错绑 | ChatGPT | 采用:父构建两项核对总是先做完,再按 child_pending 返回非终态 | 5.2、5.3、9.1 |
| 39 | 次要 | 冻结行原语签名缺 `profile_sha256`、`created_at`,照签名实现必然违反 NOT NULL | Claude Code | 采用:原语内部计算两列 | 6.2、9.1 |
| 40 | 次要 | 同 branch 两个 unit 并发冻结会撞主键,落到 INTERNAL_ERROR | Claude Code | 采用:`ON CONFLICT DO NOTHING` 后回读比较,事务内重查冻结行 | 2.2、4.3、9.1 |
| 41 | 次要 | 冻结写入的步骤引用错号(第 9 步应为第 8 步) | ChatGPT | 改正 | 2.2 |
| 42 | 次要 | 登录落点只依据 spike 一次观察 | Kimi | 采用:真机取证登记落点并纳入放行,补"未登记落点被拦截"用例 | 3.4、9.3、9.4 |
| 43 | 建议 | 登录阶段"代理不发起 /signin POST"无断言 | Claude Code | 采用:源码静态断言 + 服务器端"人工点击前无 POST" | 3.3、9.2、9.3 |
| 44 | 建议 | submit 指纹不符后表单未作废 | Claude Code | 采用 | 3.5、9.2 |
| 45 | 建议 | 双列表移动按钮的请求可能不在放行集合内 | Kimi | 不改规则,写明依据:`rbs-form-01/form.json` 显示移动按钮为页面内脚本(`server_callback: false`),服务器回调挂在 recorder 的 onchange 上,已按逐字段登记处理;第 9.4 节第 1.5 步与 9.3 页面版本用例会在真机与夹具上再验证 | 3.4 |
| 46 | 建议 | 破坏性动作正则的破坏词未锚定尾段 | Kimi | 不改:Claude Code 已对所有观察到的合法地址逐个验算不误伤;锚定尾段反而可能漏掉破坏词不在尾段的真实动作,而正向白名单仍是主控制 | — |
| 47 | 建议 | Child Build 表 Repository-Architecture 的比较口径未取证 | Kimi | 采用:列入只读取证必填项,第 5.3 节按附录 C 登记的口径比较 | 5.3、9.4、附录 C |
| 48 | 建议 | 冻结主键是 branch 而表述是"campaign × 工程" | Claude Code | 采用:写明二者等价的前提 | 2.2 |
| 49 | 建议 | 原语重构时 `create_qb_request` 的既有幂等行为容易丢 | Claude Code | 采用:写明必须保留 | 6.2 |
| 50 | 建议 | 补"返回错误表单但未建构建"的对称用例 | Claude Code | 采用 | 9.3 |
| 51 | 建议 | 拦截安全用例应在真机只读取证之前执行 | ChatGPT | 采用:列为 C2 中真机取证的前置 | 9.3、10 |
