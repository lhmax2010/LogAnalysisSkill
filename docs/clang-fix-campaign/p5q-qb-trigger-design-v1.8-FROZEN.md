# P5Q QuickBuild 复验触发与结果读取设计(v1.8-FROZEN)

- 阶段:Phase 5Q(安全阶段,三家评审)
- 上位文档:`docs/clang-fix-campaign/design.md` v1.5.23-FROZEN。本文只写 P5Q 的接口、行为与验收;与 design.md 冲突处以本文为准。design.md 第 4.5 节已按 v1.2 附录 A 与 v1.4/v1.5 增补同步(v1.5.23);v1.6 需要再同步两处(附录 A 末尾"v1.6 增补",design.md 升 v1.5.24)。
- 前一版:`p5q-qb-trigger-design-v1.5-FROZEN.md`,sha256 `f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。更早的冻结稿 `p5q-qb-trigger-design-v1.2-FROZEN.md`,sha256 `0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`,修改记录见附录 D、E。
- **v1.6 是 v1.5 冻结后、实施阶段 C2c 至 C6 结束时的汇总修订**,分三部分,全部修改与依据见附录 I:
  1. 并入 v1.5 冻结后登记的实施裁定(P5Q-C2C-03、P5Q-C3-02、P5Q-C3-04、P5Q-C4-02、P5Q-C6-01、P5Q-C6A-03、P5Q-C6A-04、P5Q-C6A-05、P5Q-C6B-01)。这些裁定都已实现并验收,并入正文只改文字、不改已验收的行为;
  2. 按 R1 登记 C5b、C6 的真机事实(成功样本、`BUILD_NOTES` 回显、提交落点、配置页最近构建表、快照关系、原始字节前提),并按第 9.4 节第 2 步的要求对快照判据作出 R1 决定(第 0.5 节);
  3. **新增一项功能**:提交后落点不是构建页时,工具在配置页的最近构建表中按请求标记自动查找构建号并绑定(第 5.5 节)。FatTank 2026-10-19 裁定纳入 P5Q;实现并经一次验证性真实提交(第 9.4 节第 3 步)后 P5Q 才能 CLOSED。
- **v1.7 是 v1.6 经外部评审(ChatGPT、Claude Code)后的修订**,两家结论均为"修改后可冻结",无阻断项。修改与采纳来源见附录 J;自动查找的方案与绑定原则不变,主要收紧驱动接口、查找总时限、验收计数与原始字节来源,并补一次零提交的读取时模式真机验证。
- **v1.8 是 v1.7 经定向评审(ChatGPT、Claude Code,只审 v1.7 的改动)后的修订**,两家结论均为"修改后可冻结",无阻断项,两家都同意附录 J 第 18 条的不采纳。修改与采纳来源见附录 K:补齐查找时限与绑定读取的关系、`submit` 的驱动侧应答上限、批次中途代理不可用的处理,并把几处既有分界与限制写准。
- 证据根目录:stage20 进度文件为 `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/progress.md`(下称"进度文件"),证据目录简称 `S`(附录 B)。
- **v1.3 是按 v1.2 第 10 节"C2 真机取证与假设不一致即按 R1 修订"写出的修订稿**。依据是 C2b 在真实 QuickBuild 上的只读取证与表单联动取证(`origin/clang-fix-campaign` @ `b6bec94`,live-01 至 live-12,实施裁定 P5Q-C2B-01 至 P5Q-C2B-10,记录于 stage20 进度文件第 17–26 节)。全部修改及其证据见附录 F;取证结论见附录 C。
- 与 v1.2 相比,只改与实测不符或实测新发现的地方;其余条文逐字保留。
- **v1.4 是 v1.3 经三家评审(Kimi、ChatGPT、Claude Code)后的修订**,修改与采纳来源见附录 G。其中两处改动需要同步 design.md(附录 A 末尾"v1.4 增补")。
- **v1.5 是 v1.4 经三家第二轮评审后的修订**(三家结论均为"修改后可冻结"),修改与采纳来源见附录 H。新增一个 CLI 开关(`qb-result-fetch --accept-snapshot-drift`)与两个结果文件键;design.md 同步内容并入附录 A"v1.4 增补"(标 v1.5 的条目)。
- 凡写着"待实测"的地方,实现必须按"失败即停"处理,不得猜。

---

## 0. 范围、前提与本版裁定

### 0.1 已确认的事实、裁定与取证来源

design.md 原设计是"用 SBS 的 REST 接口提交、Basic Auth 鉴权"。EF-5 取证与 FatTank 裁定推翻了这个前提。
下表"来源"一列区分三类:**裁定**(FatTank 决定)、**RBS 取证**(本阶段流水线的实测;v1.3 起以 C2b 真机取证为主)、**SBS 取证**(另一条流水线的实测,只作参考)。

| 事项 | 结论 | 来源 |
|---|---|---|
| REST 权限 | 不申请;REST 接口在本环境实测拒绝访问 | 裁定(2026-10-10);EF 报告历史 REST 实测 |
| 复验流水线 | **RBS/TRIGGER**,不是 SBS/TRIGGER;按包所属工程选 Tizen-Base-Toolchain 或 Tizen-Unified-Toolchain | 裁定 |
| 触发方式 | 配置页"运行"按钮(▶)先进入"Specify Build Options"表单页,点 Ok 才开跑。运行按钮是带 onclick 的 `button`,不是链接 | RBS 取证(附录 C 第 3 项) |
| 由谁填表 | 工具驱动独立浏览器窗口按标签填表、核对后点 Ok;不自己拼 HTTP 请求 | 裁定(理由见 0.2) |
| 登录 | 工具弹出浏览器窗口,FatTank 只在窗口里登录(可在窗口内重试);工具自动检测登录完成,不需要回终端;成功登录后跳转到 `/dashboard` | 裁定;RBS 取证(附录 C 第 1 项) |
| 表单字段与结构 | 十三个字段标签、双列表三元素结构、Ok 为整表提交、Cancel 为 `ILinkListener-form-cancel`;字段回调运行时在地址末尾追加 `&random=<小数>` | RBS 取证(附录 C 第 4 项) |
| 目标写在哪 | 表单字段 Build Package List,格式 `仓库路径@commit`,一行一个(本版只写一行) | RBS 取证 + 裁定 |
| 目标的回显变量 | 父构建:显示名 Build Package List 对应 **`BUILD_PKG_LIST_MODIFY`**(只含表单里写的行);父构建另有 `BUILD_PKG_LIST` 为全量包列表。子构建:`BUILD_PKG_LIST` 为**全量包列表**(Full 构建,样本 245 行),目标行包含在其中 | RBS 取证(附录 C 第 5、6 项) |
| 父子关系 | 子构建变量 `TRIGGER_ID` 等于父构建号;父子构建各自的 `QB_TRIGGER_ID` 等于自身构建号;父构建 overview 页 Child Build 表链接子构建 | RBS 取证(附录 C 第 5、6、7 项) |
| 架构状态 | 子构建三个架构合在一个构建里,Child Build 表只有一行、一个结果;`FAIL_FAST=yes`;`EACH_GBS_BUILD_STATUS` 存在且为空(**失败的子构建上同样为空**) | RBS 取证(附录 C 第 6、7 项) |
| 通过判据 | **子构建 Status 精确等于 `Successful` 即通过**,不要求 SR_STATUS=ACCEPTED;`qb_pass_requires_accept` 默认 false,每个 campaign 冻结。`Failed`(1193469)与 `Successful`(1201889,v1.6)均已在 RBS 实测 | 裁定;RBS 取证(附录 C 第 7、15 项);SBS 取证(`01.response.txt:832`) |
| 合入 | 合入正式快照必须有人点 Accept;**工具永远不点 Accept / Ready to Accept** | 裁定 |
| 推送 sandbox 分支是否自动开跑 | 不会;构建只由工具显式提交表单发起;P12 首次真实推送后观察一次 | 裁定 |
| 构建子标签记忆 | QuickBuild 按会话记住上次选中的构建子标签;裸地址 `/build/<id>` 显示的内容取决于上一次浏览,**不可依赖**。凡要读 Summary、Status、Child Build 表的,一律读 `/build/<id>/overview` | RBS 取证(附录 C 第 8 项) |
| 页面脚本改写内置函数 | QuickBuild 页面脚本把 `String.prototype.trim` 换成了有缺陷的实现(只去掉一端空白);在页面主环境里执行的代码不能信任页面可改写的内置函数,也不能信任页面主环境序列化出来的内容。v1.4 起工具不在页面主环境执行任何代码(第 3.1 节) | RBS 取证(附录 C 第 9 项);评审(附录 G 第 1 条) |
| 失败样本 | **1193469**(Base 工程子构建,Status `Failed`)。原定的 1186372 属于 Tizen-Unified-Toolchain,按裁定第 9 条不作 Base 样本 | RBS 取证;裁定(P5Q-C2B-06) |
| 失败的粒度 | 子构建失败只到步骤级(样本:`Build_GBS` 步失败,23 小时),页面上没有逐包状态;Full 构建的 `Failed` 表示"含目标行的全量构建失败",**不等于目标包的修复失败** | RBS 取证(`L/live-12/05.response.html`、`03.response.html`);评审(附录 G 第 5 条) |
| (v1.6)提交落点 | 真实提交点 Ok 后最终落在 `/wicket/page`,不是 `/build/<id>`;构建已正常创建(1201886)。落点判定不改,仍为 unknown;构建号由第 5.5 节自动查找 | RBS 取证(附录 C 第 17 项) |
| (v1.6)配置页最近构建表 | 配置页 `/overview/1917` 的服务器原始字节中有 `Recent Builds` 表,列出最近 10 个构建(含运行中的),每行构建号与 `/build/<id>` 链接一致;原始字节与活动文档的单元格文字、链接一致 | RBS 取证(附录 C 第 18 项) |
| (v1.6)快照关系 | 以 Ref. Snapshot 提交时,父构建回显的 `SNAPSHOT_NUM`、冻结值、子构建 `SNAPSHOT_NUM_URL` 的最后一段三者相同;按 R1 把子构建快照地址定为判据(第 0.5 节) | RBS 取证(附录 C 第 16 项);裁定(2026-10-19) |
| (v1.6)原始字节前提 | 第 3.1 节第 2 条依赖的字段都在服务器原始字节中:C5b 固定六页 60 项、C6b 成功父子与配置页五页 50 项逐项一致 | RBS 取证(附录 C 第 19 项) |

### 0.2 为什么用浏览器填表,而不是拼 HTTP 请求

表单离线解析显示:字段名按位置编号(QuickBuild 加减一个字段编号就错位);每个可编辑字段改动时都回传服务器,表单状态一部分在服务器端,联动刷新哪些字段从保存页面看不出来;双列表真正提交的是页面脚本生成的隐藏"记录"字段;页面地址带每次不同的版本号;字段回调运行时还追加随机数参数。自己拼请求要把这些全部模拟对。让真实浏览器执行页面自己的脚本,工具只做"按标签找字段 → 设值 → 等联动结束 → 逐项读回核对",出错面小得多。

代价是浏览器会自己发出很多请求,所以第 3.4 节的请求拦截必须做到"每一跳都检查、只放行精确登记的地址";并且页面主环境本身不可信,工具在页面里执行的代码只取原始数据,判定一律在代理进程里做(第 3.1 节)。

### 0.3 P5Q 范围

1. 浏览器代理 `qb_browser_agent`(Node + Playwright + 本机 Chromium + DevTools 协议拦截):登录检测、逐跳请求拦截、只读取页、填表核对与一次性提交、结构核对失败时的诊断取证(第 3 节)。
2. 复验参数配置与每个 campaign 的参数冻结(第 2 节)。
3. `qb-trigger` CLI(第 4 节)与 `qb-result-fetch` CLI(第 5 节)。
4. `campaign_state` 新增按连接写入的内部原语与 `qb_profile` 查询(第 6 节)。
5. 页面脱敏模块从 spike 移入正式代码(第 3.7 节)。
6. (v1.6)提交后落点不是构建页时,按请求标记自动查找构建号并绑定(第 5.5 节)。

### 0.4 不在 P5Q

- review-submit(P5R)。P5Q 只保证 RESULT 事件与 qb_result 文件按本文契约产出、冻结参数入库,并在附录 A 中写定 P5R 必须遵守的读取规则(结果文件 schema、人工降级判据收紧)。
- 后台轮询。读取结果是按需一次性执行;一次执行只读当前状态,不等待。(v1.6 唯一例外:`qb-trigger` 在提交落点不明后,于同一次执行内查找构建号,截止点为提交后 180 秒、总耗时不超过约 240 秒,见第 5.5 节;结果读取仍不等待。)
- 真实 Gerrit 推送:第一次真实 sandbox push 仍按 EF-6 放在 P12。P5Q 的真实 QuickBuild 提交只用 FatTank 指定的已有提交(第 9.4 节第 2、3 步)。
- Tizen-Unified-Toolchain:其 RBS 表单尚未取证,配置项在取证前保持关闭。已知它与 Base 不同(样本 1186372:`FAIL_FAST=no`,`CHILD_CONFIGURATIONS` 以逗号分隔三项),启用前须单独取证并按 R1 修订通过判据。
- 除 Ok 提交外的一切 QuickBuild 操作(Accept、取消、停止、重跑、删除等)。
- 三架构以外的架构组合:本版 CHILD_CONFIGURATIONS 固定为 `standard-armv7l:aarch64:x86_64`,其它组合须走 R1 修订通过判据。

### 0.5 FatTank 裁定的两项(2026-10-10)与 v1.3 补充(v1.6 补快照判据的 R1 定案)

**第一项:复验基准快照——已裁定采用下述默认。** 表单的 BUILD_REFERENCE 有 Live / Ref. Snapshot / Snapshot Number 三种,实测默认选中 `Ref. Snapshot`;此时 SNAPSHOT_NUM 下拉框**只有一个选项**,即当前参考快照(实测 `tizen-base-toolchain_20260924.094908`;v1.6:参考快照会滚动,2026-10-19 C6 首次冻结时已是 `tizen-base-toolchain_20261013.024319`,附录 C 第 16 项)。本文规定:

- BUILD_REFERENCE = `Ref. Snapshot`;SNAPSHOT_NUM 在该 campaign、该 QuickBuild 工程第一次触发时取表单**当时选中**的值并冻结(冻结范围是"campaign × 工程",不同工程各自冻结)。
- 同一 campaign 后续触发时,冻结值必须仍在下拉框中,否则该 unit 拒绝触发(`REJECTED_QB_SNAPSHOT_UNAVAILABLE`,报告记 `skip_reason=qb_snapshot_unavailable`);**已取得终态 RESULT 的 unit 不受影响**(RESULT 与结果文件是不可变快照);尚未触发的 unit 须在新 campaign(新 state DB)中处理。
- **v1.3 补充(已知限制)**:因为 Ref. Snapshot 模式下只有一个选项,参考快照一旦更新,同一 campaign 里尚未触发的 unit 全部会被拒绝。这是"同一 campaign 内基准一致"的代价,本版接受;拒绝时 stdout 必须提示"参考快照已从 <冻结值> 变为 <当前值>,需在新 campaign 中处理"(v1.6:提示文字按第 4.3 节第 5 步的两个模板,实施裁定 P5Q-C3-04)。改用 Snapshot Number 模式指定历史快照,须先取证该模式的联动与选项,再按 R1 修订,本版不做。
- **v1.4 修订(构建实际用了哪个快照),v1.6 按 R1 定案**:实测父构建回显的 `BUILD_REFERENCE`/`SNAPSHOT_NUM` 是表单值本身(样本 1193467 以 `Live` 提交,回显 `Live` 与 `do not need select`);而它的子构建仍回显 `BUILD_REFERENCE=Ref. Snapshot` 与 `SNAPSHOT_NUM_URL=<下载站>/snapshots/<工程路径>/<快照名>`。v1.4/v1.5 因此只记录子构建快照、不一致时停止,并要求在第 9.4 节第 1.6 步与第 2 步实测后按 R1 决定是否升为判据。
  (v1.6)**R1 定案**:1201886/1201889 以 Ref. Snapshot 提交,父构建回显的 `SNAPSHOT_NUM`、本次冻结值、子构建 `SNAPSHOT_NUM_URL` 的最后一段三者相同(附录 C 第 16 项)。据此(FatTank 2026-10-19 裁定,实施裁定 P5Q-C6B-01):
  - **子构建快照地址按下面的三分规则正式作为判据**(第 5.3 节第 4 项)。子构建 `BUILD_REFERENCE` 与 `SNAPSHOT_NUM_URL` 必须存在,原值记入结果文件 `child_params_echo`;`SNAPSHOT_NUM_URL` 形态符合附录 C 第 6 项登记的下载站快照根、且快照名等于冻结值时,`snapshot_used` 记该快照名,照常落库;
  - (v1.5)**快照漂移**:主机与路径根相符、快照名与冻结值同形态但不相等——最可能是参考快照在构建期间滚动(含新代码的 Full 构建可能长达约 24 小时,快照名带日期),不是格式问题,重跑 fetch 也不会改变页面。默认有指引地停止、不写结论;由人确认构建内容仍可比后,对该 request 用 `qb-result-fetch --accept-snapshot-drift` 接受,结果文件记实际快照名与 `snapshot_drift_accepted=true`(第 5.3 节第 4 项)。不加这个出口,该 unit 既无 RESULT、又不能降级、又不能 `--retrigger`,无路可走;
  - 其它不符(主机、路径根、形态不对)→ **有指引的停止-报告**:不写 RESULT,`QB_RESULT_UNRECOGNIZED`,输出冻结值、读到的值、证据路径与(v1.6 改写)"子构建快照地址的主机、路径根或形态与登记不符,须人工核对后按 R1 修订附录 C 第 6 项的登记"的指引;开关对此无效(第 5.3 节第 4 项);
  - 父构建回显的 `SNAPSHOT_NUM` 继续只记录,不作判据:它是表单值的回显,"提交时选的是冻结值"已由第 4.3 节第 5 步的读回核对保证,再比一次不增加信息。
  "提交时用的是冻结参数"的凭据是:触发时冻结值必须在下拉框中、读回值等于冻结值(第 4.3 节第 5 步),以及父构建 `BUILD_REFERENCE`/`BUILD_TYPE`/`PROJECT_BRANCH` 的逐项回显核对(第 5.3 节第 2 项);子构建以哪个快照为基准,以子构建快照地址为准。下载站上实际取用了哪些包,本版不核对、不宣称。

理由:这一步要回答的是"修复在官方构建系统里当前能不能过",复现原失败已由本地基线复现完成;`Ref. Snapshot` 是表单默认、最常用路径,同一 campaign 内所有包对同一基准、结果可比。`Live` 会使基准漂移、失败无法归因;`Snapshot Number` 要走未取证的服务端联动路径。

**第二项:凭据可信边界——已裁定采用下述边界。** 浏览器请求拦截要用 Chromium 调试协议,而该协议把每个被拦请求的请求头(含 Cookie)与请求体(含人工登录时提交的密码)交给控制它的 Node 代理进程,无法关掉。本文把可信边界定为 **Chromium 浏览器 + 专用 Node 代理进程**:这些内容只在代理进程内存中瞬时存在,协议适配层收到事件后立即丢弃请求头与请求体,只向业务代码提供方法、地址等判定所需的元数据;不得用于业务解析、独立请求、日志、文件或对 Python 的应答;禁止协议调试日志与原始事件输出(第 3.1 节)。作为对照,团队 quickbuild-sbs 工具由 Python 进程直接取得密码,cookie 长期存放在 `~/.cache` 下的文件里,调试页面不脱敏落盘;本文边界严格小于它。

**v1.4 补充:页面主环境不在可信边界内。** 页面自己的脚本可以改写页面主环境里的一切内置对象与 DOM 接口(实测改写了 `String.prototype.trim`;评审本地复现了改写 `outerHTML` 读取器、把序列化结果里的 `Failed` 改成 `Successful`)。这不影响请求拦截(拦截在浏览器协议层,页面脚本改不到),但会影响在页面主环境里做的取数、脱敏与序列化。v1.4 规定:**工具不在页面主环境执行任何代码**;业务判定的数据来源是服务器返回的原始字节(读取)或隔离执行环境中读到的活动表单(填表),规则见第 3.1 节"页面主环境"一段。

**v1.3 说明:BUILD_TYPE 保持 Full。** 实测 Full 构建的子构建会构建全量包列表(样本 245 个包,构建命令超时 8 小时),而不是只构建目标包。这与 FatTank 自己提交的样本 1193467 一致,本版不改配置值;若要改为 Partial 以缩短时间,须先取证 Partial 构建的子构建回显,再按 R1 修订第 5.3 节。(v1.6 实测:构建内容与快照完全一致时,Full 构建父 18 分 45 秒、子 16 分 12 秒完成,附录 C 第 15 项;含新代码时仍可能长达约 24 小时。)

**v1.4 补充:Full 构建失败的含义。** `FAIL_FAST=yes` 的全量构建只有一个共享的 `Build_GBS` 步,页面上没有逐包结果;子构建 `Failed` 只能说明"包含目标行的这次全量构建失败",早期依赖包失败时目标包可能根本没编译。所以 `status=FAIL` 写入 RESULT 时同时记录失败步骤与错误信息(第 5.3 节第 5 项、第 5.4 节),并在附录 A 增补第 14 条约束 P5R:不得仅凭 FAIL 断言本 unit 的修复失败。PASS 不受影响:全量构建成功意味着目标行所在的构建整体通过。

---

## 1. 术语与固定值

| 名称 | 含义 |
|---|---|
| 父构建 | RBS/TRIGGER 配置被触发产生的构建,id 记为 P。`BUILD_BOUND` 与 `RESULT` 事件里的 `qb_build_id` 一律是 P |
| 子构建 | 父构建派生的实际编译构建,id 记为 C,其 Status 是通过判据 |
| 目标行 | `<campaign_units.project>@<derived_commit_sha>`。沿用表字段名 `sbs_target`(表结构冻结,不改列名),语义为"表单 Build Package List 中的唯一一行" |
| 请求号 | `request_id`,工具在提交前生成的 32 位小写十六进制随机串(uuid4 hex) |
| 请求标记 | 写进表单 BUILD NOTES 的固定文本:`clang-fix-campaign request=<request_id>`,父构建变量 `BUILD_NOTES` 原样回显它(v1.6 已实测,附录 C 第 15 项) |
| 复验参数 | 第 2.1 节配置中的全部表单取值 |
| 参数冻结 | 每个 state DB(即每个 campaign)每个 QuickBuild 工程(以 unit.branch 区分)第一次触发时写入的复验参数快照,之后只读 |
| 固定架构值 | `standard-armv7l:aarch64:x86_64` |
| 子构建配置路径 | 由父配置路径推出:把 `configuration_path` 的最后一段 `TRIGGER` 换成 `build`(实测 `root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/build`) |

**文本规整**:凡从页面读取的文字(状态、标签、单元格、选项文字),一律在代理进程或 Python 中去掉首尾空白(含不换行空格)后再比较;页面主环境中不做规整(第 3.1 节)。

QuickBuild 构建状态归一:规整后的文字按下表**精确、区分大小写**匹配:

| 页面文字 | 归一 | 类别 |
|---|---|---|
| `Successful` | PASS | 终态成功(RBS 已实测:1201889,附录 C 第 15 项) |
| `Failed` | FAIL | 终态失败(RBS 已实测,附录 C 第 7 项) |
| `Cancelled` | CANCELLED | 终态失败(待实测) |
| `Timeout` | TIMEOUT | 终态失败(待实测) |
| `Running` | RUNNING | 非终态(待实测) |
| `Waiting` | WAITING | 非终态(待实测) |
| `Queued` | QUEUED | 非终态(待实测) |
| 父构建 Child Build 表不存在或为空 | QUEUED | 非终态 |
| Child Build 表中 Build Result 为 `Not Finished (...)`,且子构建页 Status 不在本表 | RUNNING | 非终态(已见于 RBS 截图) |
| 其它任何文字 | 无法识别 | 读取失败,不写 RESULT(第 5.4 节) |

任何表外文字一律"无法识别",绝不当作 PASS。第一次见到新的状态文字后,按 R1 补表。父构建 Child Build 表的 Build Result 文字(实测失败时为 `FAILED`)只记入结果文件,不作判据。

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
      overview_id: 1917                          # 实测(附录 C 第 3 项)
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
7. (v1.3)`configuration_path` 必须以 `root/` 开头、以 `/RBS/TRIGGER` 结尾,由它推出子构建配置路径(第 1 节);`overview_id` 必须是正整数。

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

- `profile_json` 内容:`configuration_path`、`overview_id`、`project_name`、`form` 全部十个键(`SNAPSHOT_NUM` 为实际值)、`qb_pass_requires_accept`。(子构建配置路径由 `configuration_path` 推出,不另存。)
- 主键是 branch;"冻结范围是 campaign × 工程"成立的前提是 branch 与工程一一对应,由第 2.1 节校验规则 4 保证。将来若一个 branch 对应多个工程,须按 R1 改主键。
- **首写即定,不更新、不删除**:写入原语用 `INSERT ... ON CONFLICT(branch) DO NOTHING` 后回读,内容逐字节相同则视为成功(含并发进程先写入的情形),不同则 `StateInconsistent`。写入与提交意图在同一事务(第 4.3 节第 8 步)。
- 后续触发:用当前配置(`@freeze` 以已冻结值代入)生成同样的规范化 JSON,与冻结行逐字节比较;不等 → exit 4 `REJECTED_QB_PARAMS_CHANGED`,不打开浏览器。即改配置只对新 campaign(新 state DB)生效。
- 新增只读查询 `campaign_state.qb_profile(state_db, branch) -> dict | None`,**按 unit 的 `campaign_units.branch` 取**(一个 state DB 可能有多个 branch 的 unit,不得实现成"取唯一一行")。P5R 从这里读 `qb_pass_requires_accept`,不再读配置文件。

---

## 3. 浏览器代理 `qb_browser_agent`

### 3.1 进程模型

- 实现文件:`tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs`(Node),Python 侧驱动 `ci_triage/qb_browser.py`。
- Python 用参数列表启动 `node qb_browser_agent.mjs <playwright_module> <chromium>`,不经 shell;stdin/stdout 走逐行 JSON 命令与应答;stderr 只允许输出脚本内的固定提示文字。
- (v1.6,实施裁定 P5Q-C6A-04、P5Q-C6A-05)**关闭与退出**:代理收到 `close` 后关闭浏览器、删除临时目录并应答 `{"ok": true}`;主循环随即结束,清理完成后由代理自己结束对标准输入的读取(销毁 stdin),进程自行退出,退出码 0。登录超时或中止、运行时停止条件触发后同样清理并退出。Python 驱动写出 `close` 后**立即关闭 stdin**,再等待进程退出,最多 35 秒;超时才终止进程。(v1.7 写明形状)发生终止时,驱动生成一条固定形状的记录 `{"event": "agent_terminated", "waited_seconds": <整数>, "exit_code": <整数或 null>}`(不含页面内容或异常文本),CLI 在关闭之后把它写入 `<state_root>` 下的 trace;写出失败不覆盖已完成的业务结果、不改 stdout 与退出码。该记录是缺陷迹象,出现即须排查关闭协议两侧是否一致;正常退出不产生该记录。(v1.6 已要求"终止写入 trace",但实现中 `QbBrowser.close` 未写,C7 补齐。)两侧缺一都会互相等待:C6a 实测每次 CLI 结束多等约 35 秒、代理被 SIGTERM 结束;修复后真机关闭尾段 0.213 秒(附录 C 第 15 项所列 C6b 重读)。测试入口必须与生产入口的退出行为一致,不得在测试入口里单独销毁 stdin(该缺陷正是因为测试入口多做了这一步而没被测试发现)。
- Chromium:有界面窗口,用户目录建在 `/dev/shm` 下的临时目录(不可用则 `QB_BROWSER_UNAVAILABLE`),不加载日常 profile,不允许下载,不启用 service worker,不开 HAR/trace/storage-state,不使用 `ignoreHTTPSErrors`。进程退出时(正常、异常、收到信号)关闭浏览器并删除该目录。
- **拦截先于一切页面活动**:浏览器启动后、首个页面导航前,装好第 3.4 节的全部拦截面;任何页面目标在拦截装好之前不得开始加载。
- **新目标**:浏览器级自动挂接新目标,并要求新目标启动即暂停;新窗口、弹窗、新标签页、iframe 之外的一切目标(Worker、SharedWorker、ServiceWorker 等)本版一律不支持——不恢复执行、立即关闭并计数;无法可靠阻止时(包括关闭被暂停目标失败)关闭整个浏览器并以 `QB_BROWSER_UNAVAILABLE` 停止。不得以"收到创建通知后再关闭"代替"执行前阻断"。新窗口与弹窗同样在执行前关闭。
- **凭据可信边界是 Chromium 浏览器 + 专用 Node 代理进程**(第 0.5 节第二项):
  - 所有发往 QuickBuild 的请求都必须由浏览器页面本身发出并经过第 3.4 节的拦截;只读页面一律通过**页面导航**取得,从导航响应拿 HTTP 状态与正文原始字节(本节"页面主环境"第 2 条);
  - **禁止**使用 `page.request`、`context.request`、`request.newContext` 或任何代理侧 HTTP 客户端访问 QuickBuild;
  - 不调用 `context.cookies()`、`storageState()`;
  - 调试协议事件中隐式携带的请求头与请求体:由唯一的协议适配层接收,**立即丢弃** `headers`、`postData`、`postDataEntries` 及其它请求头类字段,只把方法、协议、主机、路径、查询原文、资源类型、重定向来源、响应状态码交给判定逻辑;不得用于业务解析、独立请求、日志、文件或对 Python 的应答;
  - 禁止开启协议调试日志,禁止输出原始协议事件;异常处理只输出固定错误类别,不带原始事件或异常文本。
- **页面主环境(v1.3 新增,v1.4 改写,v1.5 补边界)**:页面主环境由页面脚本控制,工具既不在其中执行代码,也不信任它序列化的内容。规则:
  1. **生产代理不使用任何在页面主环境执行代码的接口**(由第 9.2 节源码静态断言保证)。(v1.5)完整清单:`page.evaluate`、`frame.evaluate`、`locator.evaluate`、`evaluateAll`、`evaluateHandle`、`$eval`、`$$eval`、`waitForFunction`、`addScriptTag`、`exposeFunction`、`exposeBinding`、`addInitScript`(评审在本项目同版本 Playwright 上逐项实测,均在主环境执行;`addInitScript` 还先于页面脚本执行)。**唯一具名例外**:`addInitScript` 只在首个导航前调用一次,用于安装 `window.open` 守卫(新目标阻断的纵深防御,见本节"新目标");它不读取页面数据、不参与任何判定,不得再用于取数或判定。需要在页面上读取或处理 DOM 时,一律在代理自建的**隔离执行环境**中进行:通过已在使用的公开 CDP 会话(`context.newCDPSession`)调用 `Page.createIsolatedWorld` 为工作页面主帧建立隔离环境,用 `Runtime.evaluate`(指定该环境)执行代理自带的函数。隔离环境与页面共享 DOM 树,但有独立的内置对象与 DOM 包装,页面脚本对主环境原型的改写不影响它(评审实测:主环境改写 `outerHTML`、`textContent`、`DOMParser.prototype.parseFromString`、`String.prototype.trim` 后,隔离环境中四者均为原生)。
     (v1.5)**隔离环境随文档生命周期**:每次导航提交后必须为工作页面主帧**重新建立**,不得跨导航复用(复用旧环境会得到协议层"找不到执行环境"错误,评审实测)。`read` 的解析、`open_form` 两次导航(配置页、点击运行后的表单页)之后的读取,一律用该次导航之后新建的环境;建立失败即 `QB_TRUSTED_CONTEXT_UNAVAILABLE`,不退回主环境。
  2. **读取(`read`)的业务数据来源是同一次已核验导航响应的原始字节**:取页面导航响应的正文(浏览器已收到的服务器字节,不是新请求)。(v1.7 更正)**只用**同一次已核验导航在响应阶段暂停时取得的 `Fetch.getResponseBody` 原始字节;不得退回 Playwright `response.body()`/`text()`——C2c 实施期本机实测这条路在本项目的双阶段拦截下会转码:Latin-1 字节 `636166e9` 变成 UTF-8 的 `636166c3a9`,非法 UTF-8 `c328` 变成 `efbfbd28` 后反而能通过严格解码,破坏"非法字节必须停止"的契约(进度文件第 28.3 节;评审复跑结果相同);v1.5 写的"两条路均可用"作废。正文取得后,在隔离环境中用 `DOMParser` 解析成**惰性文档**(不执行脚本、不加载任何资源)后核对构建号、脱敏并序列化;不读取、不序列化活动文档。导航响应正文不可得、隔离环境建立失败 → 代理内部错误 `QB_TRUSTED_CONTEXT_UNAVAILABLE`,不退回页面主环境取数。
     (v1.5)**解码**:`DOMParser` 收到的是已解码字符串,原始字节中的 `<meta charset>` 不再起作用,所以代理按该响应 `Content-Type` 头的 charset 解码(缺省 UTF-8),使用严格解码(遇到非法字节即报错,不以替换字符代之);charset 不受支持或解码报错 → `QB_TRUSTED_CONTEXT_UNAVAILABLE`。
     (v1.5)**前提**:这条来源成立的前提是本文读取的字段(导航栏构建号标签、Summary 区块、Child Build 表、变量表、配置来源五项、失败步骤)都在服务器原始字节中。(v1.6)**已取证成立**:第 9.4 节第 1.6 步 a 的比对在 C5b 固定六页(60 项)与 C6b 成功父子及配置页五页(50 项)上逐项一致(附录 C 第 19 项);第 5.5 节读取的配置页 `Recent Builds` 表同样在原始字节中(附录 C 第 18 项)。以后若有字段只在活动文档中出现,工具的表现仍是读取停止(构建号核对失败或结构不符),不会读错(第 9.3 节有对应夹具)。
  3. **表单(`open_form`/`fill`/`submit` 的快照、读回与指纹)读取活动文档**(填表后的状态只存在于活动 DOM),但只在隔离环境中读;读到的是原始文本、属性原文、选项原文与结构计数,规整、正则匹配、比较与判定一律在代理进程(Node)中完成。
  4. 设值动作本身(选择下拉项、勾选、填文本、失焦、点击双列表移动按钮、点击运行与 Ok、派发一次 `change`)使用 Playwright 的定位器接口执行,不读取、不规整、不判定。其中取值与设值不经过页面主环境的属性访问器(评审实测:主环境把文本域 value 的 setter 劫持后,`fill` 写入的仍是真实值;`selectOption` 未触发被劫持的 setter)。(v1.5 更正)但**派发 `change` 必然进入主环境**——页面的 onchange 就在那里,该调用可以被页面挂钩或吞掉(评审实测)。后果是等不到回调、本字段 `QB_FORM_CHANGED`,方向安全;"值已相等"路径完全依赖这一次派发,在被篡改的页面上必然失败,这是已接受的残余。正确性由第 3.5 节 `fill` 第 5 步在隔离环境中的读回与提交前指纹复核保证。
  5. 隔离环境只防主环境函数劫持;页面脚本仍可以修改活动 DOM 的内容。对读取,这由第 2 条(只用服务器原始字节)解决;对表单,活动 DOM 就是将被提交的内容,读回它正是目的。
  6. Python 侧的脱敏写后自检只承担"无敏感残留"的检查,**不承担业务真实性证明**。
- **被动处理(v1.4)**:脱敏与诊断一律在惰性文档(`DOMParser` 解析结果)上进行,**不在活动文档上 `cloneNode` 或重建带资源地址的节点**(在活动文档上克隆会让浏览器再次加载图片等资源,评审本地复现了由此产生的新请求)。
- 代理单会话串行执行命令;整个 CLI 进程只启动一个代理,多个 unit / 请求共用一次登录。

### 3.2 命令

| 命令 | 允许的阶段 | 作用 |
|---|---|---|
| `login` | 启动后第一条 | 打开登录页,等待人工登录完成(第 3.3 节) |
| `read {path}` | 已登录 | 导航到只读页面,核对最终地址与页面中的构建号(配置页没有构建号,见第 3.6 节),返回脱敏后的 HTML 与 HTTP 状态(第 3.6 节) |
| `open_form {overview_id}` | 已登录 | 打开配置页,核对配置路径,点击"运行",等待表单(第 3.5 节) |
| `fill {fields}` | 表单已打开 | 按标签设值、等待联动、逐项读回;返回读回值与指纹 |
| `submit {fingerprint}` | `fill` 成功后 | 复核指纹,放行一次提交,点 Ok,返回落点 |
| `close` | 任意 | 关闭浏览器、删除临时目录、退出 |

代理拒绝任何不在本表中的命令,以及阶段不对的命令(应答 `{"ok": false, "error": "AGENT_PHASE"}`,不执行)。`fill` 失败或 `submit` 结束后,该表单进入"作废"状态,再次提交必须重新 `open_form`。(v1.6)第 5.5 节的自动查找只用 `read`,不新增命令;`read` 在 `open_form` 之前、`submit` 之后均可执行(执行 `read` 会使当前表单作废)。

**(v1.6)错误应答的附加字段**(实施裁定 P5Q-C3-02、P5Q-C6A-03、P5Q-C6A-05)。三个字段都是固定形状;Python 驱动严格校验键集合、类型与取值范围,形状不符,或 `snapshot_state`、`login_facts` 出现在下列情形以外的应答中 → 按协议错误处理(`QB_BROWSER_UNAVAILABLE`;`submit` 已发出时按落点 unknown):

- `failure_category`:代理因运行时停止条件(`runtime.failure`,第 3.1 节"新目标"、第 3.4 节拦截面的停止路径)失败时附带,取值只能是 `NEW_PAGE`、`WORKER_BLOCKED`、`WORKER_NOT_PAUSED`、`CLOSE_TARGET_FAILED`、`BROWSER_DISCONNECTED`、`PAGE_CLOSED`、`ADAPT_FAILED`、`FETCH_CONTINUE_FAILED`、`UNKNOWN` 之一,记录首个停止原因。浏览器 `disconnected` 事件与页面 `close` 事件映射到对应类别;同一次关闭伴随的页面关闭不覆盖浏览器断开;正常 `close` 不记为异常。代理异常停止时 stderr 输出一行固定格式 `QB_AGENT_STOPPED category=<类别>`。installGuards 各停止调用点只增加类别参数,不改任何判定条件。
- `snapshot_state`:只在 `fill` 于 SNAPSHOT_NUM 返回 `QB_FORM_VALUE_UNAVAILABLE` 时附带(第 3.5 节 `fill` 第 2 步)。
- `login_facts`:只在 `login` 返回 `QB_LOGIN_TIMEOUT` 或 `QB_LOGIN_ABORTED` 时附带(第 3.3 节)。

命令失败时,Python 驱动把命令名、代理错误码、`failure_category`、`login_facts`、代理进程是否已退出及退出码记到异常对象上;`qb-trigger` 与 `qb-result-fetch` 把这些固定字段写入 `<state_root>` 下的 trace(沿用现有 `_trace` 写法与脱敏自检),**stdout 结构与错误码映射不变**,数据库写入分支不变;trace 写出失败不覆盖原结果。

**(v1.7)驱动侧失败与代理应答必须可区分**:现有驱动在 `submit` 已发出后,把"代理进程不存在或已退出、管道读写失败、应答不是合法 JSON 或不符合协议"都转换成与代理合法应答相同的 `landed: unknown` 结果(`qb_browser.py` 的 `_unknown()`),调用方无法区分。v1.7 要求:驱动侧失败在 `submit` 之后仍按落点 unknown 处理(不改"提交一旦放行不存在确定失败"的原则),但必须带一个只在驱动内部使用的固定标记,CLI 据此**不做自动查找**(第 4.3 节第 10 步);代理返回的合法 `landed: unknown` 不带该标记。代理自己在 `submit` 放行后内部出错时返回的 `landed: unknown` 属于合法应答,照常查找;若此时代理已进入运行时停止状态,查找中的读取会失败,按第 5.5 节"读取失败"处理。
(v1.8 写准)**标记的要求**:字段名不规定;要求是"代理的合法应答上一定不出现、驱动合成的落点上一定出现",且不进 stdout、不进结果文件与数据库、不改错误码;驱动在 `submit` 已发出后仍以返回值(而不是抛异常)交出这一结果,不改 `command()` 现有的返回契约。**驱动侧失败的外延**就是"凡由驱动自己合成落点 unknown 的全部路径",逐类为:代理进程不存在或已退出;管道读写失败或读到 EOF;应答不是合法 JSON;应答不是对象,或 `ok` 不是布尔;应答含敏感键;`login_facts`、`failure_category`、`snapshot_state` 出现在规定情形之外或取值非法;`ok: true` 但 `released` 不为真、既不是合法的 build 落点也不是合法的 unknown 落点、或带 `html_redacted`;`ok: false` 但 `released` 不为假或 `error` 不是字符串;以及代理在下面规定的应答上限内不应答。其中"代理还活着、只是载荷不合协议"的几类,浏览器也许仍可用、查找也许能成功,本版**仍不查找**:载荷不合协议说明代理状态不可知,再让它做十轮读取不可靠,统一成一条规则也便于验收。

**(v1.7)`read` 应答等待上限**:驱动等待 `read` 命令应答最多 60 秒;超时视为代理异常:终止代理,按第 3.1 节写 `agent_terminated` 记录,`qb-result-fetch` 中为 `QB_FETCH_FAILED`,第 5.5 节查找中为"读取失败"。(v1.8)该上限由代理自有预算推出,所以代理必须**显式**把 `read` 的页面导航超时设为 30000 毫秒(不依赖框架默认值),并保证 `read` 路径上没有其它可超过该值的等待;第 9.2 节以源码静态断言钉住"驱动上限大于代理 `read` 自有预算"。

**(v1.8)`submit` 应答等待上限**:代理在 `submit` 上的自有预算约 130 秒(Ok 按钮点击最多 60 秒、放行等待 10 秒、跳转等待 60 秒,另有两次隔离环境读取),所以驱动等待 `submit` 应答最多 150 秒。超时按**驱动侧失败**处理:终止代理,按第 3.1 节写 `agent_terminated` 记录,不做自动查找(浏览器已不可用),不写任何事件,状态保持 QB_REQUESTED,`submit_uncertain`、`QB_SUBMIT_UNCERTAIN`,`message` 同第 4.3 节第 10 步末行。理由:提交可能已放行、构建可能已存在,无限等待会一直占着 unit 锁,并让第 5.5 节"批量恢复的时效"窗口白白流逝。服务器极慢时代理自己的 60 秒跳转等待会先超时并返回合法的 unknown,所以触发 150 秒上限的只有"代理不应答"这一类真缺陷。
`open_form`、`fill` 本版不设驱动侧上限:它们挂起时提交必定未放行、QuickBuild 上没有任何痕迹,风险只是本机阻塞,列为已接受残余,操作者中断即可;P12 若出现实例,按 R1 用同样办法补上限。`login` 自有登录时限,`close` 按第 3.1 节。

**结构核对失败时先取证再报错(v1.3 新增,v1.4 修订)**:`read` 返回 `QB_READ_ID_MISMATCH`、`open_form`/`fill` 返回 `QB_FORM_CHANGED` 时,代理在返回错误之前:

1. 先撤销本表单的运行、字段与提交登记(放行集合只剩只读与静态资源);
2. 只在已有数据上做被动诊断:读取失败用该次导航响应的原始字节;表单失败在隔离环境中读取活动文档的序列化文本(`outerHTML` 读取器在隔离环境中为原生),再用 `DOMParser` 解析为惰性文档;**不发起任何新请求、不点击、不输入、不在活动文档上克隆节点**;
3. 生成结构事实(标签集合与差集、各行控件个数与角色、回调地址是否符合形态、导航栏构建号标签、Summary 区块个数、首个失败的核对项名称)与脱敏后的 HTML;**结构事实中的每个字符串字段与 HTML 使用同一脱敏上下文处理**;
4. 应答带 `diagnostic: {...}`。诊断过程本身失败 → 只返回原错误与固定类别 `diagnostic_failed`,不返回任何原始快照或部分结果。

Python 侧把诊断写入 `<state_root>/qb_diagnostics/<UTC时间戳>-<unit_hash>/`,写后按第 3.7 节对每个文件做字节自检;自检失败同样删除文件并报 `QB_EVIDENCE_REDACTION_FAILED`(不改变原错误码之外的任何结果)。stdout 给出该目录。`QB_TRUSTED_CONTEXT_UNAVAILABLE` 不产生诊断。理由:C2b 中每一次"核对失败但没有现场"都多耗一次人工登录(附录 F 第 13 条)。

### 3.3 登录检测(不需要回终端)

- `login` 打开 `/signin`,之后每 2 秒检查一次当前页:**已登录**当且仅当最终地址路径不是 `/signin`、页面中没有 `type=password` 输入框、并且存在文字为 `Sign Out` 的链接。三个条件缺一即视为未登录。实测成功登录后落在 `/dashboard`,三条件均成立。
- 超过 `login_timeout_seconds` 仍未登录 → `QB_LOGIN_TIMEOUT`;窗口被关闭 → `QB_LOGIN_ABORTED`;两者都关闭浏览器退出。
- 终端只打印固定提示:"已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。"不读取终端输入。(v1.6 设计方自查:现有实现少了"若提示登录失败,可在窗口中重新输入"一句,C7 按本条补齐。)
- 工具从不填写用户名或密码;登录表单只由人在窗口里提交。`login` 命令的实现只做导航到 `/signin` 与只读轮询,不做任何点击、输入、按键。拦截层分不出请求由人还是由代理触发,所以这一条靠源码静态断言与集成测试保证(第 9.2、9.3 节)。
- **登录重试(v1.3)**:登录失败时服务器返回 200 并重新显示登录页;此后 Wicket 把登录页变成带页号的页面,再次提交发往 `/wicket/page?<页号>-<n>.IFormSubmitListener-content-form`。放行规则见第 3.4 节"登录中"一行:最多 5 次,首个 3xx 响应后关闭。用尽 5 次仍未登录时,stderr 固定提示"已达 5 次登录提交上限,请关闭窗口后重新运行工具",随后按超时处理。
- (v1.6,实施裁定 P5Q-C6A-05)**登录失败事实 `login_facts`**:`QB_LOGIN_TIMEOUT`、`QB_LOGIN_ABORTED` 应答附带一个对象,键集合固定为八个:
  - `final_path_shape`:结束时当前页路径经现有路径形态函数处理的结果,只能是 `/`、`/dashboard`、`/wicket/page`、`/signin`、`/overview/<id>`、`/build/<id>`、`/build/<id>/overview`、`/build/<id>/variables`、`/build/<id>/step_status`、`<other>` 之一(不含主机与查询);
  - `on_signin`、`password_present`、`sign_out_present`:最后一次检查时三个登录条件各自的布尔值;
  - `checks`:完成的检查次数。为 0 表示一次检查都没完成,此时三个布尔值是初值 false,**不表示观察到页面上没有这些元素**;
  - `login_posts_released`:登录 POST 的放行次数;
  - `login_channel_closed`:登录通道是否已关闭;
  - `denied`:登录阶段被拒请求的计数,按路径形态分组(键的取值范围同 `final_path_shape`)。
  不含任何查询值、请求头、请求体、账号、密码或 Cookie;只在已有检查的基础上记录,不新增网络请求、取数或判定条件。**判读注意**:登录后被跳到未登记地址时,请求被拒,浏览器停在错误页,其路径为 `/`,所以 `final_path_shape` 为 `/`;这时必须与 `denied` 中的 `<other>` 计数及 `login_channel_closed` 一起看,不得理解为"登录到了首页"(本机实测场景见第 9.2 节)。

### 3.4 请求拦截(逐跳、精确登记)

**拦截机制**(三个拦截面,都在首个页面导航前装好):

1. **HTTP 请求**:对浏览器全部页面目标启用 Chromium DevTools 协议的请求拦截(Fetch 域,浏览器级,带帧归属:只放行属于工作页面帧树的请求)。每一个请求——页面脚本发起的、子资源、以及**重定向产生的每一跳**——都在**请求阶段**暂停并判定,不通过即以失败中止。获准的请求同时在**响应阶段**再暂停一次:响应状态码为 307 或 308 时在响应阶段终止;其它响应放行,下一跳重新接受请求阶段判定。响应阶段不再次消耗任何一次性放行;提交已放行后在响应阶段被终止的,仍按落点 unknown 处理。
2. **WebSocket**:在创建任何页面之前安装上下文级拒绝(ws/wss 一律不连接服务器)。
3. **新目标**:按第 3.1 节,Worker 类目标与新窗口在执行前阻断。

Playwright 的 `page.route`/`context.route` 不满足要求,不得作为唯一拦截面。第 9.2、9.3 节用"服务器端实际收到的请求清单"证明三个拦截面都生效。

判定只看第 3.1 节列出的元数据。被拒请求只记"阶段 + 路径形态"到本次运行的 trace(不含查询值),并计数。

**永久禁止**(先于一切放行规则):

- 非 `https://quickbuild.tizen.org` 的任何请求(含 download.tizen.org、iframe、外站资源);WebSocket;
- 路径以 `/rest/` 开头;
- 查询中出现 Wicket 监听器且监听器组件名命中破坏性动作的请求,即匹配
  `(?i)I(Link|Behavior|FormSubmit|Resource)Listener[.0-9-]*-[A-Za-z0-9:_-]*(promote|cancel|stop|rerun|delete|abort)`;
  以及两个已取证的完整特征 `ILinkListener-content-buildHead-promote`(Ready to Accept)、`ILinkListener-form-cancel`(表单 Cancel)。放弃表单一律用 `close` 关闭浏览器;
  (v1.6,实施裁定 P5Q-C2C-03)该正则按子串匹配,组件名中含 `desktop`、`nonstop` 之类的词也会被拒,后果是该字段失败、表单作废(方向安全),属已接受残余,真机遇到时停止按 R1 处理。只读页面查询必须为空、字段回调文法闭合且只允许末尾一个 `random`,而 `stop` 放进组件名又会命中本条,所以不存在"含 stop 字样且合法放行"的地址;第 9.2 节相应用例按三层验收;
- `/build/<id>/log`、`/build/<id>/html_report`、产物下载链接;
- 状态码 307/308 的重定向,在响应阶段终止。

**放行规则**(只有在当前阶段、当前命令执行期间才生效;"精确登记"指从当前页面 DOM 中读出的完整地址原文,逐字符相等才放行,不按监听器名前缀泛化):

| 阶段 | 放行 |
|---|---|
| 所有已加载页面 | 静态资源:GET,路径前缀属于登记清单(`/styles/`、`/jquery/`、`/scripts/`、`/datetimepicker/`、`/codemirror/`、`/wicket/resource/`、`/images/`、`/favicon.ico`),查询为空或恰好匹配 `^v=\d+$`,且查询中不含任何 Listener。实测被拒但不影响任何功能的静态资源(`/ckeditor/ckeditor.js?v=<数字>`、`/images/fonts/bootstrap-icons.woff(2)?<哈希>`)**保持拒绝**,不登记 |
| 登录中 | GET `/signin`(查询为空);GET `/`、`/overview/0`(查询为空,沿用 spike);GET `/dashboard`(资源类型为页面,查询为空或 `^\d+$`;实测落点);**人工登录提交**:POST `/signin` 或 POST `/wicket/page`,查询都必须完整匹配 `^\d+-\d+\.IFormSubmitListener-content-form$`;登录阶段累计最多放行 5 次,任一登录提交的响应为 3xx 后两条通道立即永久关闭,离开登录阶段后亦关闭 |
| 已登录、只读 | GET `/build/\d+`、`/build/\d+/(overview\|variables\|step_status)`、`/overview/<配置的 overview_id>`,**查询必须为空**。页面定时刷新请求(`...IBehaviorListener...action=ajaxRefresh...`,无论是否带 random)**一律拒绝**:只读取证与表单操作都不需要它们(实测拒绝后读取与填表均正常)。代理**不得保留任何刷新放行集合**,不得有从页面提取刷新地址并登记的代码路径(第 9.2 节静态断言)。注意:C2b 实测的"刷新被拒"是因为实际请求追加了 random 而与当时登记的原文不等,属偶然,不能据此认为规则已生效 |
| `open_form` 执行中 | 只读放行全部 + 运行按钮地址的精确原文,**一次**(提取规则见第 3.5 节 `open_form` 第 2 项) + 由它产生的跳转 GET:路径 `/wicket/page`、查询恰好匹配 `^\d+$` |
| `fill` 执行中 | 只读放行全部 + **当前正在设值的那一个字段**的回调地址:每次设值**之前**从活动 DOM 重新读取该字段 onchange 中的回调地址原文(实测为相对地址 `page?...`),按表单页地址解析为绝对地址 U(解析规则同第 3.5 节 `open_form` 第 6 项),形态须符合该项;本次字段操作期间只放行一次 POST,其完整 URL 必须等于 U,或等于 `U + "&random=" + R`,R 完整匹配 `^0\.\d{1,20}$`(实测浏览器追加 `random`,样本 `0.3453609721766676`;科学计数法、`0` 等其它写法一律拒绝。`Math.random()` 极少数情况下会产生这类写法,后果是该字段回调被拒、本字段失败、`REJECTED_QB_FORM_CHANGED`,重跑即可;stdout 提示"字段回调随机参数形态不在登记范围,请重跑",避免被当作表单结构变化排查);该字段操作结束即撤销 + 表单页重渲染 GET:路径 `/wicket/page`,查询匹配 `^\d+(-\d+)?$`。双列表的移动按钮是页面内脚本,不发请求;服务器回调挂在 `recorder` 的 onchange 上,按本行处理 |
| `submit` 执行中 | 在指纹复核通过后从活动 DOM 读取的表单 action 精确原文(POST,路径 `/wicket/page`,查询须匹配 `^\d+-\d+\.IFormSubmitListener-form$`,**不允许** random 后缀),**一次**;随后的跳转 GET:路径 `/build/\d+`(查询为空)或 `/wicket/page`(查询 `^\d+(-\d+)?$`) |

额外约束:

- 提交地址每个 `open_form` 至多放行一次;放行后同一表单的任何提交一律拒绝;`fill` 失败(表单作废)后不经新的 `open_form` 的提交一律拒绝。
- `dragDrop`、`loadPopup`、`unloadPopup`、`quicksearch`(页面上另有一个快速搜索表单)及其它未登记的 Listener 一律拒绝。
- 第 3.5 节 `fill` 第 4 步的"静默"判定只计**获准**的请求;被拒请求(如定时刷新)不延长等待。代理的最近活动时间只在放行请求时更新。
- 代理记录每个表单实例的状态:`not_released`(从未放行提交)或 `released`(已放行一次)。这一状态是第 4.3 节判定"确定未提交"的唯一依据。

### 3.5 填表、核对与提交

**`open_form` 成功的条件**(任一不满足 → `QB_FORM_CHANGED`,不进入表单已打开阶段;失败时按第 3.2 节先取证):

1. 配置页 `<title>` 以 `QuickBuild - <configuration_path>` 开头(其后只允许为空或 ` - ...`),路径逐字等于配置(已实测通过)。
2. 页面上 title 为 `Run the configuration` 的元素恰好一个,且必须是 `button`;其 onclick 属性必须完整匹配
   `^var win = this\.ownerDocument\.defaultView \|\| this\.ownerDocument\.parentWindow; if \(win == window\) \{ window\.location\.href='((?:\.\./)*wicket/page\?\d+-\d+\.ILinkListener-run)'; \} ;return false$`
   (实测原文见附录 C 第 3 项);捕获的地址按当前页地址解析后必须同源、路径为 `/wicket/page`、查询完整匹配 `^\d+-\d+\.ILinkListener-run$`。该地址登记为本次 `open_form` 唯一放行一次的运行地址,然后点击按钮。是链接、个数不为 1、缺 onclick、写法不同,一律失败,不做兼容退回。
3. 点击后 30 秒内出现标题文字 `Specify Build Options` 的表单,其 action 含 `IFormSubmitListener-form`。页面上另有快速搜索表单(action 含 `IFormSubmitListener-quicksearch`),不计入。
4. 表单的字段标签**去重后的集合**恰好是:`PROJECT_NAME`、`BUILD_TYPE`、`REPO_TYPE`、`BUILD_REFERENCE`、`SNAPSHOT_NUM`、`PROJECT_BRANCH`、`Immediate Stop With Error`、`CHILD_CONFIGURATIONS`、`Build Package List`、`Add Package List`、`Remove Package List`、`TARGET_IMAGE`、`BUILD NOTES`(实测一致,无多无少无重复);
   - PROJECT_NAME 恰好对应一个只读显示区域(`property-viewer`),不要求输入控件;其原始文本前后带有空白与空子元素,规整在代理进程中做(第 3.1 节);
   - 其余非双列表的可编辑字段,每个标签恰好对应一个输入控件(实测 Immediate Stop With Error 为复选框,Build Package List、Add/Remove Package List、BUILD NOTES 为文本域,其余为下拉框);
   - 双列表字段(`CHILD_CONFIGURATIONS`、`TARGET_IMAGE`)每个标签恰好对应三个控件,角色恰好是 `recorder`(`type=hidden`,服务器回调挂在它的 onchange 上)、`choices`、`selection`。实测 CHILD_CONFIGURATIONS 默认 `selection` 恰为固定架构值一项、`choices` 为空,选项 value 为文字的十六进制编码;TARGET_IMAGE 两个列表均为空。
   - (v1.6,实施裁定 P5Q-C3-04)**普通下拉框**(双列表的 `choices` 与 `selection` 不在此列)中,选项显示文字在代理进程中去首尾空白后若有重复,即视为表单结构与已取证结构不符。该检查在 `open_form` 与 `fill` 每一次表单快照的结构校验中执行,覆盖全部普通下拉框(不只 SNAPSHOT_NUM),应答 `QB_FORM_CHANGED`(先按第 3.2 节取证),不带 `snapshot_state`。理由:工具按选项显示文字选值,文字重复时选哪一项有歧义;已取证的表单中选项文字都不重复;把它报成"快照不可用"会误导处置。
5. 只读字段 PROJECT_NAME 规整后的显示值等于配置的 `project_name`。
6. 校验各业务字段 onchange 回调地址的**形态**:onchange 中恰好一个 `wicketAjaxPost('<相对地址>', ...)` 调用;相对地址按表单页地址解析后路径为 `/wicket/page`,查询匹配 `^\d+-\d+\.IBehaviorListener\.\d+-[A-Za-z0-9:_-]+$`(实测形如 `10-1.IBehaviorListener.0-form-editor-content-basicProperties-1-property-editor-editor-wrapper-select`)。只校验形态,不冻结原文;原文在 `fill` 每一步之前重新读取。
7. 表单的 action 匹配第 3.4 节 `submit` 行的形态。

实测表单选项(附录 C 第 4 项):BUILD_TYPE 为 Full / Partial(默认 Full);REPO_TYPE 只有 ALL;BUILD_REFERENCE 为 Live / Ref. Snapshot / Snapshot Number(默认 Ref. Snapshot);SNAPSHOT_NUM 只有当前参考快照一项;PROJECT_BRANCH 只有 tizen_base。BUILD_TYPE 改值后:回调 HTTP 200,页面版本号、表单 action 与该字段回调地址均不变,无整页导航。(v1.7)十二个字段的联动已在 C5b 填表演练中整体实测:每个字段恰好 1 次获准回调、0 次被拒,全程只有一个页面版本与一个表单 action,均不变;其中 10 个字段走"值已相等"路径(所以"值已相等时派发一次 change"是主路径,不是边角);提交放行 0 次,登记位置外身份计数 0(附录 C 第 20 项)。

**`fill` 的步骤**(一律按"标签 + 角色"定位,不按 name 中的序号定位):

1. 按固定顺序设值:BUILD_TYPE → REPO_TYPE → BUILD_REFERENCE → SNAPSHOT_NUM → PROJECT_BRANCH → Immediate Stop With Error → CHILD_CONFIGURATIONS → Build Package List → Add Package List → Remove Package List → TARGET_IMAGE → BUILD NOTES。
2. 下拉框按**选项显示文字**(在代理进程中规整后)精确匹配选择;找不到该文字 → `QB_FORM_VALUE_UNAVAILABLE`。SNAPSHOT_NUM 为 `@freeze` 时不改变选中项,读取**当前选中项**文字作为待冻结值;无选中项或下拉框为空 → `QB_FORM_VALUE_UNAVAILABLE`;选项数写入应答与 trace。`@freeze` 只是"不改选项",**不是"跳过回调"**:该字段同样登记、触发一次 change、等待回调后撤销登记。
   (v1.6,实施裁定 P5Q-C3-02)**SNAPSHOT_NUM 不可用应答**:SNAPSHOT_NUM 返回 `QB_FORM_VALUE_UNAVAILABLE` 时(冻结值不在选项中、`@freeze` 时无选中项或有多个选中项、下拉框为空),应答附带 `snapshot_state`,键集合恰为两个:
   - `selected`:取自本字段开始时那一次隔离环境表单快照,为全部选中项文字(在代理进程中去首尾空白)组成的列表,可以是 0 项、1 项或多项;任一项长度超过 200,或不完全匹配 `^[A-Za-z0-9._:+-]+$`,则整体置为 null,不返回原文;
   - `option_count`:该下拉框的选项数,非负整数。
   不增加任何请求、不额外设值、不重开表单;该错误不产生诊断;表单照常作废,`released=false`。Python 侧校验形状(键集合、`selected` 为 null 或符合长度与字符限制的字符串列表、`option_count` 为非负整数),通过后供第 4.3 节第 5 步生成提示文字。
3. 双列表只操作 `choices`/`selection` 两个列表与页面自带的移动按钮,把 `selection` 的全部选项文字(按顺序)调整为配置值;**不修改 `recorder` 的 value**。`selection` 已等于配置值时(CHILD_CONFIGURATIONS 的默认态即如此,没有可点的移动按钮),只在 `recorder` 上派发一次 `change`,其 value 保持逐字节不变。
4. **每个设值的字段恰好产生一次获准回调、零次被拒回调**:每设一个值之前,从活动 DOM 重新读取该字段的回调地址并登记;按控件类型使该字段**总共只产生一次 change**:
   - (v1.5)下拉框、复选框:值不等时**只调用设值接口**(`selectOption`、`check`/`uncheck`),**不得补派发**——评审实测 Playwright 1.58.2 上这两个调用各自产生一次 change;
   - (v1.5)文本域:值不等时调用 `fill`,随后在本字段窗口内做一次**受控失焦**(定位器的 `blur`),由失焦产生唯一一次原生 change;**不得人工补派发**——评审实测:`fill` 后立即人工派发,下一字段获得焦点时还会多出一次原生 change,正好触发下面的"被拒回调即失败";
   - 下拉框、复选框、文本域值已相等时:不改值,只派发一次 change(复选框不得用点击,点击会把它翻成错值);
   - 双列表:按第 3 步;
   - 设值后等待该回调请求完成(响应已返回),且 1 秒内没有新的获准请求;单个字段总等待超过 30 秒 → `QB_FORM_CHANGED`;
   - (v1.5)**计数窗口**从本字段登记开始,持续到下一字段登记之前(最后一个字段持续到第 5 步读回结束),以便抓到迟到的原生 change;窗口内拦截器记录到**任何被拒的回调 POST**(例如多派发了一次 change)→ 本字段失败,`QB_FORM_CHANGED`。不能只靠"服务器收到的回调数"判断,因为多余的回调会被一次性登记拒掉而看不见。
   - (v1.5)**启动自检**:上面"设值调用各产生一次 change"是框架行为,随 Playwright 版本可能变化,而 Playwright 模块路径由 Python 在启动时传入(第 3.1 节)。代理启动后、首个 QuickBuild 导航前,在一个不触网的合成页面上(空白页 `setContent`,页面自带计数脚本;它不是 QuickBuild 页面,用后关闭)对下拉框、复选框、文本域各做一次"值不等"设值(文本域含受控失焦),在隔离环境中读取计数;任一类不是恰好 1 次 → 关闭浏览器,stderr 固定提示"浏览器框架的设值行为与设计不符,升级 Playwright 后须重新验证",退出,Python 侧按 `QB_BROWSER_UNAVAILABLE` 处理。不得按旧分支继续。Playwright 版本号写入 trace。
   字段之间的联动(例如 BUILD_REFERENCE 改变后刷新 SNAPSHOT_NUM 的选项)随该字段回调的同一响应返回,不产生第二个回调请求(附录 C 第 4 项),所以一次性登记不影响联动;若真机出现联动产生的额外请求,按 R1 处理。
5. 全部设完后逐项读回 DOM 当前值:下拉框读选中项文字;复选框读勾选状态;文本域读原始文本;双列表读 `selection` 全部文字(按顺序),并把 `recorder` 与 `selection` 交叉核对:实测 `selection` 恰一项时 `recorder` 等于该项 value(文字的十六进制编码),解码后必须等于 `selection` 文字,解码不了即不等;多于一项时的分隔符尚未取证,本版 `selection` 恒为一项,出现多于一项即 `QB_FORM_CHANGED`。读回值必须与要求值完全相等,其中:
   - Build Package List 恰好等于目标行(单行,无前后空白,无其它行);
   - BUILD NOTES 恰好等于请求标记;
   - Add/Remove Package List 为空字符串,TARGET_IMAGE 的 `selection` 为空;
   - CHILD_CONFIGURATIONS 的 `selection` 恰好是固定架构值一项。
6. 计算表单指纹:读回值按"标签/角色"排序后的规范化 JSON 的 sha256。返回 `{readback, fingerprint, snapshot_option_count}`。

任一步失败:应答对应错误,表单作废;结构类失败按第 3.2 节先取证。

**`submit {fingerprint}`**:

1. 再读回一次全部字段,重算指纹,必须等于传入值;不等 → `QB_FORM_CHANGED`,不放行、不点击,表单状态保持 `not_released`,同时置表单为作废态,之后只接受 `close` 或新的 `open_form`。
2. 置表单状态为 `released`,放行一次表单 action,点击文字为 `Ok` 的提交按钮。
3. 等待最多 60 秒,直到导航结束或超时。
4. 返回落点,只有两种:
   - `{"landed": "build", "build_id": "<P>"}`:最终地址路径恰为 `/build/\d+`,且页面导航栏恰好一个 `Build (id:<同一数字>)` 标签(在隔离环境中读取,判定在代理进程中做)。(v1.3:裸地址 `/build/<id>` 显示的子标签由会话记忆决定,不能要求 Summary 表存在,见第 0.1 节。)
   - `{"landed": "unknown", "observed": "<脱敏后的最终路径形态>", "messages": [...]}`:其它一切情况,**包括停在表单页并显示错误提示**、超时、跳到别的页面。
5. 应答始终带 `released: true|false`。只有第 1 步拒绝时为 `false`。

提交请求一旦放行,**任何页面表现都不能证明服务器没有创建构建**,所以不存在"提交后确定失败"的落点。

(v1.6 已实测)真实提交 1201886 点 Ok 后,最终路径为 `/wicket/page`,`messages` 为空,应答 `landed: unknown`,而构建已正常创建(附录 C 第 17 项)。落点判定不改:不按 `/wicket/page` 推断成功,也不读取该页取构建号(`/wicket/page` 不在只读放行集合内)。构建号由第 4.3 节第 10 步调用第 5.5 节自动查找;找不到时仍走第 5.2 节人工绑定。

代理应答到 CLI 错误码的映射(Python 侧固定表,表外应答一律 `INTERNAL_ERROR`):

| 代理应答 | CLI 错误码 |
|---|---|
| `QB_FORM_CHANGED`、`QB_TRUSTED_CONTEXT_UNAVAILABLE`(表单阶段) | `REJECTED_QB_FORM_CHANGED` |
| `QB_FORM_VALUE_UNAVAILABLE`(SNAPSHOT_NUM) | `REJECTED_QB_SNAPSHOT_UNAVAILABLE` |
| `QB_FORM_VALUE_UNAVAILABLE`(其它字段)、读回不等 | `REJECTED_QB_FORM_MISMATCH` |
| `QB_LOGIN_TIMEOUT` / `QB_LOGIN_ABORTED` | 同名 |
| `QB_READ_REDIRECTED`、`QB_READ_ID_MISMATCH`、`QB_TRUSTED_CONTEXT_UNAVAILABLE`(读取阶段) | `QB_FETCH_FAILED` |
| `AGENT_PHASE`、代理进程退出、应答不是合法 JSON | `submit` 已发出命令后发生:按落点 unknown 处理;其余:`QB_BROWSER_UNAVAILABLE` |

### 3.6 只读取页

`read {path}`:

1. 路径必须属于第 3.4 节"已登录、只读"放行集合,否则 `AGENT_PHASE`。
2. 导航到该路径;最终地址必须与请求地址逐字相等(发生任何重定向即失败 `QB_READ_REDIRECTED`)。
3. 取该次导航响应的原始字节,按第 3.1 节第 2 条解码,在该次导航之后新建的隔离环境中解析为惰性文档;以下核对都在这份文档上做,判定在代理进程中完成:
   - 所有 `/build/<id>` 及其子页:页面导航栏中文字形如 `Build (id:N)` 的标签恰好一个,且 N 等于请求的 id;
   - `/build/<id>/overview` 另外要求:恰好一个标题为 `Summary` 的 `.build-summary` 区块,其中恰好一个表格,表头 `Id` 一列唯一,首行该列等于请求的 id。
   不符 → `QB_READ_ID_MISMATCH`(先按第 3.2 节取证)。防止从另一个构建的页面借用 `Successful`。
   - (v1.6)`/overview/<id>`(配置页):页面上没有构建号标签,代理只做第 2 步的地址核对,不做页面身份核对;页面身份(title、面包屑、复制路径)与 `Recent Builds` 表结构由 Python 按第 5.5 节第 1 步核对。
4. 在同一惰性文档上脱敏并序列化,返回 `{status, html_redacted}`。HTTP 非 200 照实返回状态,由 Python 判定。Python 的业务判定全部基于这份由服务器原始字节得到的脱敏 HTML。

### 3.7 页面脱敏(`ci_triage/qb_redact.py` 与代理 `redactDOM`)

- 身份值(登录显示名等账号字段)→ `<USER>`,按下面的登记位置遮蔽;
- 所有隐藏输入框的 value、URL 中的 `jsessionid`、形如 token/csrf/session 的参数值 → `<REDACTED>`;**例外**:双列表 `recorder` 字段不是凭据,保留原值;
- `Set-Cookie`、`Cookie`、`Authorization` 头不进入任何返回值(代理本就不读请求头)。
- (v1.4)**身份值按位置遮蔽,不做全局字符串替换**:登录显示名所在的 `Welcome!` 区域、表头为 `Triggered By` 的列及其它已登记的身份承载位置(与 Python `_UserFields` 识别的位置一致),整格替换为 `<USER>`;**不依据显示名字符串去全局改写页面**——Status、变量值、配置路径、标签、选项与监听器代码中与显示名同字的内容必须原样保留(评审反例:显示名为 `Successful`、`Full`、`root` 时,全局替换会改坏判据)。显示名若在登记位置之外以自由文本出现(例如别人写的 BUILD NOTES),属已接受的残留,只记出现次数(按单词边界计)到 trace,不阻断。代理与 Python 两端用同一组位置语义与测试向量。v1.3 的单词边界方案作废(它修好了 `ILinkListener` 被改写的问题,但没解决显示名与完整业务词相同的情况)。
- (v1.5)**身份承载位置登记清单**(代理与 Python 共用;Python `_UserFields` 按此实现,不再以"与 `_UserFields` 一致"反向定义):
  a. `Welcome!` 之后的显示名区域;
  b. 表头为 `Triggered By` 的列,以及标签为 `Triggered By` 的相邻值格;
  c. 表头为 `Requested By` 的列(配置页的构建请求表,附录 C 第 14 项)。该列在 v1.4 之前靠全局替换才被遮蔽,去掉全局替换后必须显式登记,否则配置页(生产路径会读、诊断会序列化)的这一列会原样落盘。
  (v1.6)配置页 `Recent Builds` 表的 `Triggered By` 列属于 b,第 5.5 节归档配置页时据此遮蔽(C6b 归档中各行均为 `<USER>`,附录 C 第 18 项)。同一表格出现多段表头时,每段表头重新确定身份列,不沿用前一段的列号(C3 修复 C2c 评审遗留,进度文件第 29.2 节;代理与 Python 共用向量)。
  每一处都整格替换为 `<USER>`。**登记流程**:第 9.4 节第 1.6 步、第 2 步与(v1.6)第 3 步读到的每一个页面(含配置页),都检查 trace 中"登记位置之外的显示名出现次数";不为零时人工确认是否为新的身份承载列或区域,是则按 R1 补登记,并对已归档证据重新脱敏或删除。生产运行中不自动判断"新身份列",只计数。
- 凭据类值(隐藏输入框 value、`jsessionid`、token/csrf/session 参数值、`JSESSIONID_8810=`)仍执行全局脱敏与全局残留检查。
- 诊断对象的每个字符串字段与诊断 HTML 使用同一脱敏上下文(第 3.2 节)。

代理返回前脱敏一次;Python 写证据文件前按同一规则再自检一次。(v1.5 改写)写后按原始字节自检的判据是:(a) 凭据类值全局无残留(`JSESSIONID_8810=`、隐藏输入框 value、`jsessionid`、token/csrf/session 参数值);(b) 每一个已登记的身份承载位置都为 `<USER>` 或为空。**不做"全文不含登录显示名"的全局检查**——显示名可能与 `Successful`、`Full`、`root` 等业务词相同,全局检查会让每个含该词的证据文件自检失败,通过的构建一个也写不进结论(评审用仓内 `PageRedactor` 复现)。显示名在登记位置之外的出现按上文只计数。自检失败 → 删除该证据文件,`QB_EVIDENCE_REDACTION_FAILED` exit 5,不写 RESULT。实现侧:删除 `qb_redact.py` 的全局身份替换与全局身份残留检查,保留并按登记清单扩展位置检查(第 10 节 C2c)。Python 侧自检只检查敏感残留,不证明业务内容的真实性(第 3.1 节第 6 条)。

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
  `{campaign_unit_key, sbs_target, request_id|null, request_seq|null, qb_build_id|null, action, status, error_code|null, diagnostic_dir|null, message|null}`;
  `action` ∈ `submitted_bound`、`submit_uncertain`、`submit_failed`、`already_requested`、`already_passed`、`rejected`。
  (v1.6,实施裁定 P5Q-C3-02、P5Q-C3-04)`message` 只填本文规定的固定模板文字(第 4.2 节第 5 步 `already_requested`、第 4.3 节第 5 步快照模板、第 4.3 节第 10 步落点与自动查找结果),同一段文字写入 trace;其它情况为 null。
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
  (v1.6)表中"只有 SUBMITTED、无 BUILD_BOUND、不是 QB_SUBMIT_FAILED"一行的 `already_requested`,`message` 为"该 unit 已有未绑定的请求 <R>;可运行 qb-result-fetch --request-id <R> 自动查找构建号,确认没有构建后再用 --retrigger 重提"。`qb-trigger` 本身不对旧 request 做自动查找。

### 4.3 提交流程(逐 unit,通过前置校验后)

1. (整个 CLI 第一次需要浏览器时)启动代理并 `login`。登录失败 → 所有尚未处理的 unit 记 `submit_failed`、`error_code=QB_LOGIN_TIMEOUT|QB_LOGIN_ABORTED`,**不写数据库**,exit 5。
   (v1.8)**代理在批次中途不可用**:处理某个 unit 时代理被终止或判定不可用(第 3.2 节的应答上限、第 3.1 节的运行时停止条件、进程退出)之后,**不再为后续 unit 重启代理**(重启需要再次人工登录,且与"整个 CLI 只启动一个代理、多个 unit 共用一次登录"不符):当前 unit 按它所处步骤的规则处理(放行后为 `submit_uncertain`,放行前为 `rejected`);其后尚未处理、且需要浏览器的每个 unit 记 `rejected`、`error_code=QB_BROWSER_UNAVAILABLE`,`message`"浏览器在处理 <当前 unit 的 campaign_unit_key> 时不可用,本批剩余 unit 未处理;请排查后重跑",不写数据库、不提交、不再向代理发命令;不需要浏览器的幂等命中(第 4.2 节第 5 步)照常输出。退出码按第 4.1 节取最严重项。重跑是幂等的(第 4.2 节)。
2. 生成 `request_id` 与请求标记。
2.5. (v1.6)**配置页基线读取**:`read /overview/<N>`,N 为该工程的 `overview_id`(已有冻结行时与冻结值相同,由第 2.2 节的冻结比对保证),按第 5.5 节第 1 步核对页面身份与 `Recent Builds` 表结构,取表中最大构建号为本次提交的基线 W(表为空时 W=0),写入第 7 步的 trace。核对不通过、HTTP 非 200、重定向或可信读取环境不可用 → `rejected`,`REJECTED_QB_FORM_CHANGED`,不写数据库、不提交;代理不可用 → `QB_BROWSER_UNAVAILABLE`。理由:配置页不可识别时自动查找必然失败,此时提交只会产生需要人工查号的构建;先停下按 R1 修订,与"表单结构变化即停"同一原则。本页只用于取基线,不归档。
   (v1.8)错误码不变,但 `message` 与 trace 必须区分两类,并写出首个失败的核对项名(运维据此知道该改哪里):
   a. **页面身份**类(第 5.5 节第 1 步 a、b:HTTP 状态、重定向、可信读取环境、title、面包屑、复制路径)→ "配置页身份与冻结 profile 不符(<核对项>),该 overview_id 可能已不指向冻结的配置;停止提交,按 R1 核对第 2.2 节冻结值与附录 C 第 3 项";
   b. **`Recent Builds` 结构**类(第 1 步 c、d)→ "配置页最近构建表结构与登记不符(<核对项>),自动查找无法工作,故不提交;处置是按 R1 更新附录 C 第 18 项的登记与第 5.5 节第 1 步的解析规则,不涉及表单与放行规则"。
3. `open_form`。失败 → `rejected`,不写数据库;有诊断时 stdout 带 `diagnostic_dir`。
4. `fill`(十个配置字段 + 目标行 + 请求标记)。失败 → `rejected`,不写数据库;有诊断时同上。
5. 冻结比对:本 branch 无冻结行 → 用读回值生成待冻结 profile;已有冻结行 → 读回值逐项等于冻结值,否则 `REJECTED_QB_PARAMS_CHANGED`,不写数据库。SNAPSHOT_NUM 不等时按 `REJECTED_QB_SNAPSHOT_UNAVAILABLE` 报告,并按第 0.5 节输出冻结值与当前值。
   (v1.6,实施裁定 P5Q-C3-02、P5Q-C3-04)**SNAPSHOT_NUM 不可用的统一处理**:包括第 4 步 `fill` 在 SNAPSHOT_NUM 返回 `QB_FORM_VALUE_UNAVAILABLE`(带 `snapshot_state`)与本步比对不等,一律 `REJECTED_QB_SNAPSHOT_UNAVAILABLE`、`skip_reason=qb_snapshot_unavailable`、表单作废、零提交、零数据库写入。stdout `message` 与 trace 只用两个模板:
   a. 已有冻结值,且 `snapshot_state.selected` 恰好 1 项:"参考快照已从 <冻结值> 变为 <当前值>,需在新 campaign 中处理";
   b. 其它所有情况:"参考快照不可用:冻结值 <V>,当前选中项 <S>,共 <N> 个选项;<后续>"。槽位:V 有冻结值时为冻结值原文,首次冻结时为"尚无";S 在 `selected` 为 1 项时为该项原文,0 项时为"无",多项时为各项以逗号分隔,null 时为"形态不在登记范围";N 为 `option_count`;后续在有冻结值时为"需在新 campaign 中处理",首次冻结时为"请人工核对 SNAPSHOT_NUM 下拉框后重跑"。
   是否首次冻结,以数据库中该 branch 是否已有冻结行判断,不以配置是否写了具体快照判断。
6. **远端 sandbox ref 实时核对**:远端地址按 P5 规则由配置构造(`gerrit_ssh_base.rstrip('/') + '/' + unit.project`,并按 P5 规则校验地址格式与 URL 改写),ref 取自 PUSH 事件;用 P5 的隔离传输仓库与统一 git 环境(`_sandbox_git` 及 `<ws>/<unit_hash>/.transport`)做一次 `ls-remote`,不得以主副本为 `-C`/`--git-dir`、不得另起 git 环境。结果必须等于 `derived_commit_sha`,否则 `REJECTED_SANDBOX_NOT_BOUND`,不写数据库。
   (v1.6,实施裁定 P5Q-C4-02)传输仓库是每次新建、默认对象格式的一次性 bare 仓库,只做 `ls-remote`,用后删除;不查询、不对齐源仓库的对象格式(P5 对齐格式是因为推送要借源仓库的对象,这里只查 ref,用不到对象),第 9.1 节"没有任何 git 命令以主副本为 `-C`/`--git-dir`"的全称禁令不开例外。已接受残余:远端若为 sha256 仓库,`ls-remote` 可能报错或得不到匹配,结果只能是"sha 相符则通过"或 `REJECTED_SANDBOX_NOT_BOUND`,不会误判绑定;Tizen Gerrit 为 sha1。
7. 写一条 trace:目标行、request_id、表单指纹、是否首次冻结、SNAPSHOT_NUM 选项数、(v1.6)第 2.5 步的基线 W(不含页面内容)。
8. **提交意图落库**(一个写事务,使用第 6.2 节按连接写入的原语):
   - 事务内重查:最新状态与第 4.2 节第 3 步读到的相同;最新 request_seq 与第 4.2 节第 5 步读到的相同;PUSH 事件不变。任一变化 → 回滚,`REJECTED_STATE_INCONSISTENT`;
   - 冻结行重查:第 5 步判为"需冻结"而此时该 branch 已有冻结行 → 与待冻结的规范化 JSON 逐字节比较,相等则不再写,不等则回滚 `REJECTED_QB_PARAMS_CHANGED`;
   - 若需冻结且仍无冻结行,写 `campaign_qb_profiles`;
   - 写 request 与 SUBMITTED;
   - 追加状态 `QB_REQUESTED`。
9. `submit(fingerprint)`。
10. 按应答处理:
    - `released: false`(指纹复核不过,提交确定未放行):一个写事务追加状态 `QB_SUBMIT_FAILED`;`submit_failed`,`error_code=REJECTED_QB_FORM_CHANGED`。
    - `landed: build`:读 `/build/<P>/variables`,核对第 5.3 节第 2 项中"请求标记"与"目标行"两条;并查 P 未绑定到任何其它 request。全部通过 → 一个写事务(事务内重查该 request 仍是最新且无 BUILD_BOUND):`BUILD_BOUND(qb_build_id=P)` + 状态 `QB_TRIGGERED`,`submitted_bound`。任一不通过 → 不写,`submit_uncertain`,`error_code=REJECTED_QB_BINDING_MISMATCH`。
    - (v1.6 改写)`landed: unknown`:先不写任何事件,状态保持 QB_REQUESTED;随即在同一浏览器会话中按第 5.5 节自动查找(提交后模式,基线 W,时限按第 5.5 节第 4 步),结果按下表处理。各行的 `message` 都以"观察到的落点:<observed>;"开头(`observed` 为脱敏后的路径形态):

      | 查找结果 | 写库 | stdout |
      |---|---|---|
      | 恰好找到一个构建 P,且第 5.2 节第 1–5 步全部通过 | 第 5.2 节第 5 步的同一事务:`BUILD_BOUND(qb_build_id=P)` + 状态 `QB_TRIGGERED` | `submitted_bound`,`qb_build_id=P`,`status=QB_TRIGGERED`;`message`:"已按请求标记在配置页最近构建中找到并绑定构建 <P>" |
      | 找到 P 但第 5.2 节核对不通过,或同一轮找到多于一个 | 不写 | `submit_uncertain`,`error_code=REJECTED_QB_BINDING_MISMATCH`;`message`:"自动查找到的构建 <P[,P2…]> 不能绑定(<核对不通过或多于一个>),须人工核对后按第 5.2 节绑定" |
      | 证据写后自检失败(第 5.5 节第 5 步) | 不写 | `submit_uncertain`,`error_code=QB_EVIDENCE_REDACTION_FAILED`;`message` 同下一行,结果类别为"证据脱敏自检失败" |
      | 未找到、查找超时(v1.7)、配置页不可识别或读取失败 | 不写 | `submit_uncertain`,`error_code=QB_SUBMIT_UNCERTAIN`;`message`:"自动查找未找到带本请求标记的构建(<结果类别>,已核对 <n> 个候选,<m> 个暂不可读);请尽快运行 qb-result-fetch --request-id <R> 再次自动查找(配置页最近构建表只保留约 10 个构建,该配置再产生约 10 个新构建后将只能人工查号),或到 QuickBuild 按请求标记找到构建后用 --qb-build-id 绑定;确认没有构建后用 --retrigger 重提" |

    - `submit` 命令发出后的驱动侧失败(外延见第 3.2 节,含 v1.8 的 `submit` 应答超过 150 秒;由驱动标记识别,不得凭返回值形状判断):浏览器已不可用,不做自动查找;不写任何事件,状态保持 QB_REQUESTED,`submit_uncertain`,`error_code=QB_SUBMIT_UNCERTAIN`;`message` 为上表最后一行的文字,去掉括号中的查找结果与计数。
    以上 `submit_uncertain` 的后续处理:尽快(时效见第 5.5 节"已接受的限制")用 `qb-result-fetch --request-id R`(第 5.1 节,读取时模式自动查找),或人工到 QuickBuild 上按请求标记找到构建后用第 5.2 节绑定;确认没有构建后用 `--retrigger` 重提。

### 4.4 崩溃窗口

| 崩溃发生在 | 数据库状态 | QuickBuild 状态 | 重跑行为 |
|---|---|---|---|
| 第 8 步事务提交之前 | 无变化(事务原子回滚) | 未提交 | 正常提交 |
| 第 8 步之后、第 9 步放行之前 | 冻结行(如首次)+ SUBMITTED + QB_REQUESTED | 未提交 | `already_requested`,不自动重提;人工确认后 `--retrigger` |
| 放行之后、第 10 步写库之前(v1.6:含自动查找期间) | 同上 | 可能已提交 | 同上;若构建存在,用 `qb-result-fetch --request-id` 自动查找(第 5.5 节读取时模式),或第 5.2 节按请求标记人工绑定 |
| 第 10 步之后 | 完整 | 已提交或确定未提交 | 幂等命中 |

意图先于放行落库,保证"QuickBuild 上出现了构建,但数据库没有任何记录"这种情况不会发生;代价是可能留下从未真正提交的 request,由人工 `--retrigger` 处理。

---

## 5. `qb-result-fetch` CLI

### 5.1 接口

```
python3 -m ci_triage qb-result-fetch
    (--request-id <id> [--qb-build-id <P>] | --qb-build-id <P> | --requests-file <path>)
    --state-db <path> --state-root <path> --config <path>
    [--accept-snapshot-drift]
```

- `--request-id` 单独:读取该请求已绑定的构建。(v1.6 改写,v1.7 统一前置)**未绑定**时,前置以第 5.5 节"前置"一段为唯一定义;不满足按原规则拒绝(R 不是最新 → `REJECTED_QB_SUPERSEDED`;unit 状态为 QB_SUBMIT_FAILED 或其它非 QB_REQUESTED 状态 → `REJECTED_QB_BINDING_MISMATCH`),不做查找、不读配置页;满足则按第 5.5 节自动查找(读取时模式:无基线,单次),结果:
  - 恰好找到一个 P,且第 5.2 节第 1–5 步全部通过 → 绑定后按第 5.3 节继续读取,与人工绑定后的读取完全相同;
  - 找到 P 但核对不通过、多于一个,或未找到 → exit 4 `REJECTED_QB_BINDING_MISMATCH`,不写库;`message` 说明查找结果(类别、候选数、暂不可读数、构建号),并提示"可稍后重试,或人工查到构建号后同时给 --qb-build-id 绑定";
  - 配置页不可识别 → exit 5 `QB_RESULT_UNRECOGNIZED`;配置页读取失败、查找中代理异常 → exit 5 `QB_FETCH_FAILED`;证据写后自检失败 → exit 5 `QB_EVIDENCE_REDACTION_FAILED`;均不写库,配置页证据(读到时)按第 5.5 节归档。
- `--request-id` + `--qb-build-id`:人工指定绑定(第 5.2 节),成功后继续读取。
- `--qb-build-id` 单独:沿用 design.md v1.4.10 规则,经 BUILD_BOUND 反查 request;查不到 → exit 4 `REJECTED_QB_BINDING_MISMATCH`,不得猜测挂到最新 request;命中多个 unit → `AmbiguousQbReference`。
- `--requests-file`:JSON 数组,每项为上面三种形式之一;一次登录,逐项独立处理。只有 `request_id` 的项同样适用上面的自动查找。
- (v1.5)`--accept-snapshot-drift`:只能与 `--request-id` 一起使用(与 `--requests-file` 或单独的 `--qb-build-id` 同用 → exit 2 `INVALID_ARGS`),保证漂移是对单个 request 的人工裁定,不能批量放过。它只放宽第 5.3 节第 4 项的"快照漂移"一种情形,其余核对、主机与路径根校验一律不变。
- 只处理每个 unit 的**最新 request**:传入的 request 不是最新 → 该项 exit 4 `REJECTED_QB_SUPERSEDED`,不读取、不写库。
- 每项在该 unit 的 `.sandbox_submit.lock` 内完成从入口校验到落库的全流程(网络读取期间持锁,但不放在数据库事务内)。
- stdout:每项 `{request_id, qb_build_id, child_build_id|null, status, terminal, result_event_id|null, qb_result_path|null, error_code|null, diagnostic_dir|null, message|null}`。(v1.6 补列)`message` 承载本文要求输出的固定指引文字:第 5.3 节第 4 项的快照停止-报告、`EACH_GBS_BUILD_STATUS` 非空的处置指引、第 5.5 节自动查找结果;其它情况为 null。v1.5 正文已要求在 stdout 输出这些指引,但键表漏列,实现已有此键。
- 退出码:全部成功(含非终态)→ 0;参数错误 → 2;存在校验拒绝 → 4;存在读取失败 → 5;busy/意外异常同第 4.1 节。

### 5.2 人工指定绑定(`--request-id R --qb-build-id P`)

(v1.6)第 5.5 节自动查找得到的 P 走本节同一组步骤与同一个写事务,不放宽任何一步;其中第 4 步可以直接使用查找时在同一次执行内已读到的 `/build/P/variables`(不重读),只再读 `/build/P/overview`;两页都按第 5.3 节末尾的规则归档(`qb-trigger` 中同样归档)。

1. R 必须是其 unit 的最新 request,且没有 BUILD_BOUND;已有 BUILD_BOUND 且等于 P → 视为已绑定继续;已有且不等 → `REJECTED_QB_BINDING_MISMATCH`。
2. R 所在 unit 最新状态为 QB_SUBMIT_FAILED → 拒绝 `REJECTED_QB_BINDING_MISMATCH`。
3. P 不得已绑定到任何其它 request → 否则 `REJECTED_QB_BINDING_MISMATCH`。
4. 读 `/build/P/overview` 与 `/build/P/variables`,第 5.3 节第 1、2 项的**父构建核对全部通过**(Child Build 表为空不影响绑定,但不能跳过第 2 项)。
5. 一个写事务(事务内重查 1–3):`BUILD_BOUND(qb_build_id=P)` + 状态 `QB_TRIGGERED`。父构建任一核对不通过 → 不写 BUILD_BOUND。

### 5.3 读取与逐项核对

页面由 Python 侧从脱敏 HTML 解析(不在页面主环境中解析)。变量页是三列表格(Name、Display Name、Value),值中的换行以 `<br>` 表示;"按行切分"指以 `<br>` 与换行切分、各行去首尾空白、丢弃空行。凡变量"必须存在"的,该行缺失即不符。

已绑定 P 后(人工绑定时是绑定之前),依次 `read`。**第 1、2 项(父构建)总是全部执行完,才根据 Child Build 表决定是否结束本次读取**:

1. **`/build/P/overview`(父构建)**
   - 配置来源核对(同 C2b 取证所用五项规则,附录 C 第 3 项;解析基址一律是已核验的请求地址,不采用页面里的 base 元素):
     a. Configuration Overview、Pipelines、Children 三个标签链接各恰好一个,按请求地址解析后同源、无查询、无片段,路径分别恰为 `/overview/N`、`/pipeline/N`、`/children/N`,N 相同且等于冻结的 `overview_id`;
     b. 面包屑恰好一个,各段依次拼接等于冻结 profile 的 `configuration_path`,且最后一段为当前项(无链接);
     c. "复制路径"脚本参数恰好一个,路径字符串与 b 相等;
     d. 构建名以附录 C 第 3 项为该工程登记的前缀开头(Base 工程实测 `TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_`,即配置路径去掉 `root/CI_TIZEN/` 后把 `/` 换成 `_` 再加 `_`;其它工程启用前按 R1 登记);
   - 读父构建 Summary 中的 Status 与 SR_STATUS(若该栏存在),只记入结果文件,不作判据;
   - Child Build 表:定位为文字 `Child Build` 的标题(去掉前导符号 `◆`)后紧邻的表格,表头必须恰为 `Repository-Architecture`、`QB Build URL`、`Build Result`、`Build Profiling` 四列,否则 `QB_RESULT_UNRECOGNIZED`;
     - 标题不存在或表格无数据行 → 记 `child_pending`,**继续执行第 2 项**;
     - 恰好一行 → Repository-Architecture 规整后**精确等于**固定架构值(实测为冒号连接串,无其它文字),否则 `REJECTED_QB_BINDING_MISMATCH`;QB Build URL 单元格中恰好一个链接,其 href 完整匹配 `^https://quickbuild\.tizen\.org/build/(\d+)$`,读出子构建 id C;Build Result 文字记入结果文件;
     - 多于一行 → `QB_RESULT_UNRECOGNIZED`。
2. **`/build/P/variables`**
   - `QB_TRIGGER_ID` 等于 P(v1.3 新增);
   - `BUILD_PKG_LIST_MODIFY`(显示名 `Build Package List`,必须存在)按行切分后**恰好一项**,等于目标行;
   - `BUILD_NOTES`(显示名 `BUILD NOTES`,必须存在)恰好等于 `clang-fix-campaign request=<R>`(v1.6:1201886 实测原样回显,单元格无首尾空白、无 HTML 转义、无换行或截断,附录 C 第 15 项);
   - `BUILD_TYPE`、`BUILD_REFERENCE`、`PROJECT_BRANCH` 逐项等于冻结 profile;`FAIL_FAST`(显示名 `Immediate Stop With Error`)等于 `yes`;`CHILD_CONFIGURATIONS` 等于固定架构值;
   - `SNAPSHOT_NUM` 原值记入结果文件 `params_echo`,**不作判据**(第 0.5 节第一项);
   - 页面中其它值含 `@` 的变量全部原样记入结果文件 `pkg_list_echo`,不作判据。
   任一项找不到或不等 → `REJECTED_QB_BINDING_MISMATCH`,不写 BUILD_BOUND(人工绑定时)、不写 RESULT。
   第 1、2 项全部通过后:若第 1 项记了 `child_pending` → 归一 QUEUED,结束本次读取;否则继续第 3、4 项。
3. **`/build/C/overview`(子构建)**
   - 面包屑各段拼接与"复制路径"字符串都等于子构建配置路径(第 1 节,由冻结的 `configuration_path` 推出);
   - Summary 表 Status 一栏,按第 1 节归一。
4. **`/build/C/variables`**
   - `TRIGGER_ID` 等于 P;`QB_TRIGGER_ID` 等于 C;
   - `BUILD_PKG_LIST`(必须存在,Full 构建为全量包列表)按行切分后:**目标行恰好出现一次**,且除这一行外没有任何一行以 `<unit.project>@` 开头(防止同一仓库带另一个 commit 混入)。取这一行作为 `sbs_target_echo`;
   - `FAIL_FAST` 等于 `yes`——这是"子构建总状态代表三架构"的依据,缺失或不等即 `REJECTED_QB_BINDING_MISMATCH`;
   - `REPO_ARCH` 与 `CHILD_CONFIGURATIONS` 都等于固定架构值(`ARCHITECTURE` 实测为 `armv7l:aarch64:x86_64`,只记录);
   - `BUILD_REFERENCE`、`SNAPSHOT_NUM_URL` 必须存在,原值记入结果文件 `child_params_echo`。子构建 `BUILD_REFERENCE` 只记录,不与冻结值比较(实测它与父构建表单的选择无关,第 0.5 节)。`SNAPSHOT_NUM_URL` 必须是绝对 URL、无用户信息、无查询、无片段,主机与路径根符合附录 C 第 6 项登记的映射(`http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/`,协议、主机或根路径变更按 R1 登记),根之后恰好一段非空路径(即快照名,无尾斜杠)。快照名等于冻结的 SNAPSHOT_NUM → `snapshot_used` 记该快照名,`snapshot_drift_accepted=false`,照常落库。不等时分两种:
     a. (v1.5)**快照漂移**:上述主机、根与段数均符合,快照名与冻结值**同形态**(冻结值最后一个 `_` 之前的前缀相同,`_` 之后完整匹配 `^\d{8}\.\d{6}$`)但不相等。不带 `--accept-snapshot-drift` → 有指引的停止-报告:不写 RESULT,`QB_RESULT_UNRECOGNIZED`,stdout 与 trace 输出冻结值、实际快照名、证据文件路径与指引"该 unit 的复验基准已漂移(参考快照可能在构建期间滚动),须由人裁定:确认构建内容仍可比,则对该 request 加 `--accept-snapshot-drift` 重跑 fetch;否则在新 campaign 中重做"。带开关 → 继续其余核对与判定,`snapshot_used` 记实际快照名,`snapshot_drift_accepted=true`,trace 记冻结值与实际值。该 request 已有 RESULT、其最新结果文件 `snapshot_drift_accepted=true` 且 `snapshot_used` 等于本次快照名时,视同已裁定,再次读取不要求开关。
     b. **其它一切不符**(主机或根不符、带用户信息/查询/片段、根后不止一段或有尾斜杠、快照名形态不同):有指引的停止-报告,同上但指引为(v1.6 改写)"子构建快照地址的主机、路径根或形态与登记不符,须人工核对后按 R1 修订附录 C 第 6 项的登记";`--accept-snapshot-drift` 对此**无效**。
     (v1.6 按 R1 定案,第 0.5 节第一项)子构建快照地址是正式判据:一致 → 照常落库;漂移 → 默认停止、可对单个 request 人工接受;其它不符 → 停止。规则本身与 v1.5 相同,只是定性从"不一致的迹象时不写结论"改为判据。只解析字符串,不访问下载站;
   - `EACH_GBS_BUILD_STATUS`:必须存在;为空 → `per_arch_status=null`;**非空** → 其格式尚无取证,`QB_RESULT_UNRECOGNIZED`,不写 RESULT。实测失败的子构建(1193469)与成功的子构建(1201889,v1.6)上它都为空,所以它为空**不表示**各架构都成功;通过与否只看 Status(第 1 节)。
     非空时是**有意的停止-报告**:此时该 unit 不会有 RESULT,不得人工降级(附录 A 第 10 条),`--retrigger` 亦被拒。唯一出路是用本次读到的样本按 R1 定义解析规则、升本文版本后重跑 fetch。实现必须在 stdout 与 trace 中输出这一处置指引与证据文件路径,不得只报错误码。
   - (v1.4)**前提说明**:"目标行恰好出现一次"成立的前提是子构建 `BUILD_PKG_LIST` 反映表单里提交的那一行。该前提对**已合入**的 commit 已由样本证实(附录 C 第 6 项);对 sandbox 分支上尚未合入的 commit,要到第一次真实 campaign 使用(P12)时才能证实。在此之前,目标行缺失按本条判 `REJECTED_QB_BINDING_MISMATCH`,不推断原因。
   任一不符 → `REJECTED_QB_BINDING_MISMATCH`,不写 RESULT。
5. **`/build/C/step_status`(v1.4 新增,不作判据)**:当第 3 项归一为终态失败时读取,取失败步骤的层级路径(实测 `master` → `BUILD` → `Build` → `Build_GBS`)与 `/build/C/overview` 中 Error Message 原文,记入结果文件 `child_failed_step`、`child_error_message`。页面缺失、结构不符或读不出 → 两个键为 null,**不改变判定结果**,不得因此变成 `QB_RESULT_UNRECOGNIZED`。该页面已在只读放行集合内,不新增放行规则。
   (v1.5)**优先级**:本项是辅助取证。仅本页的 HTTP 非 200、重定向、构建号不符(`QB_READ_ID_MISMATCH`,诊断照常写出)或结构解析失败,都按上一句记 null,**优先于第 5.4 节"页面 HTTP 非 200……不写 RESULT"一行**,不推翻已核验的构建结论。以下仍按原规则停止,不得被辅助取证的宽泛异常处理吞掉:本页证据脱敏自检失败(第 3.7 节,`QB_EVIDENCE_REDACTION_FAILED`);代理异常或退出、`QB_TRUSTED_CONTEXT_UNAVAILABLE`(说明工具本身不可用,`QB_FETCH_FAILED`)。只有本页享有这一优先级,其它必读页面不得变成可选。

每个读到的页面经第 3.7 节脱敏后归档到 `<state_root>/qb_evidence/<request_id>/<序号>.<页面名>.html`,写后自检。(v1.7)**序号规则**:同一 `request_id` 目录内按归档的先后顺序编号,两位起;每次执行从目录中已有的最大序号加一开始,跨执行续编,不覆盖旧文件(与第 5.4 节保留旧结果文件一致;C6b 重读即续编为 05–08)。结果文件的 `evidence` 只列本次执行写入的文件。第 5.5 节的配置页在绑定之前归档,所以在读取时模式中它是本次执行的第一个文件。

### 5.4 结果落库

| 子构建归一状态 | 写库 | 状态迁移 |
|---|---|---|
| 非终态(QUEUED/WAITING/RUNNING) | **不写 RESULT** | 首次见到时追加 `SANDBOX_QB_PENDING`(已是则不重复) |
| PASS | 写 qb_result 文件 + RESULT | `SANDBOX_QB_PASS` |
| 终态失败(FAIL/CANCELLED/TIMEOUT) | 写 qb_result 文件 + RESULT | `SANDBOX_QB_FAILED` |
| 无法识别 | 不写 RESULT,exit 5 `QB_RESULT_UNRECOGNIZED`;页面证据保留 | 不迁移 |
| 页面 HTTP 非 200、重定向、构建号不符、登录失效、可信读取环境不可用、代理异常(辅助页 step_status 的例外见第 5.3 节第 5 项) | 不写 RESULT,exit 5 `QB_FETCH_FAILED` | 不迁移 |

非终态不写 RESULT,配合附录 A 第 10 条(P5R 人工降级判据收紧),复验未出结果期间不构成人工降级条件。

qb_result 文件(键集合固定,多一个少一个都算 schema 错误):

```json
{
  "qb_build_id": "<P>",
  "child_build_id": "<C>",
  "status": "PASS|FAIL|CANCELLED|TIMEOUT",
  "sbs_target_echo": "<子构建 BUILD_PKG_LIST 中等于目标行的那一行>",
  "per_arch_status": null,
  "accepted": true|false|null,
  "configuration_path": "...",
  "child_configuration_path": "...",
  "parent_status_text": "...",
  "child_status_text": "...",
  "child_build_result_text": "<父构建 Child Build 表 Build Result 原文>",
  "child_failed_step": "<失败步骤层级路径,无则 null>",
  "child_error_message": "<子构建 overview Error Message 原文,无则 null>",
  "request_marker_echo": "clang-fix-campaign request=<R>",
  "params_echo": {"BUILD_TYPE": "...", "BUILD_REFERENCE": "...", "SNAPSHOT_NUM": "...", "PROJECT_BRANCH": "...", "FAIL_FAST": "yes"},
  "child_params_echo": {"BUILD_REFERENCE": "<子构建回显原文>", "SNAPSHOT_NUM_URL": "<子构建回显原文>"},
  "snapshot_used": "<子构建 SNAPSHOT_NUM_URL 中的快照名>",
  "snapshot_drift_accepted": true|false,
  "pkg_list_echo": {"<变量名>": "<原值>"},
  "evidence": ["qb_evidence/<R>/01.build-overview.html", "..."],
  "fetched_at": "<UTC ISO8601>"
}
```

- (v1.3/v1.4)新增 `child_build_result_text`、`snapshot_used`、`child_failed_step`、`child_error_message` 四个键;`sbs_target_echo` 改为子构建全量列表中匹配的那一行;`params_echo` 中的值为父构建回显原文。
- (v1.5)新增 `child_params_echo`(子构建 `BUILD_REFERENCE`、`SNAPSHOT_NUM_URL` 回显原文,键集合固定为这两个)与 `snapshot_drift_accepted`;`snapshot_used` 改记子构建地址中的**实际**快照名(未漂移时等于冻结值,漂移被接受时为实际值),使结果文件自洽、不必回查 trace。三者都是观测记录,都不证明服务端实际消费了哪个快照(第 0.5 节)。
- (v1.4)**`status=FAIL` 的语义**是"包含本 unit 目标行的那一次全量构建失败",不等于本 unit 的修复未通过(第 0.5 节);P5R 的约束见附录 A 增补第 14 条。
- `accepted`:父构建页存在 SR_STATUS 一栏时,值匹配 `^ACCEPTED(\s*\(.*\))?$` 为 true,否则 false;不存在该栏为 null。
- `per_arch_status`:本版恒为 null(见第 5.3 节第 4 项)。
- 文件写到 `<state_root>/qb_results/<R>/<UTC时间戳>.json`:临时文件 → fsync → rename → fsync 父目录(沿用 P5 的发布写法);计算原始字节 sha256。
- 一个写事务(第 6.2 节原语),事务内重查:R 仍是该 unit 最新 request;R 已有 BUILD_BOUND 且等于 P;然后 `RESULT(qb_build_id=P, status, accepted, sbs_target_echo, per_arch_status_json=NULL, qb_result_sha256, qb_result_ref=相对路径)` + 状态迁移。重查不过 → 回滚并删除刚写的结果文件,`REJECTED_QB_SUPERSEDED` 或 `REJECTED_STATE_INCONSISTENT`。
- `sbs_target_echo` 必须等于该 request 的 `sbs_target`(第 5.3 节已核对;事务内再比一次)。
- **同一 request 已有终态 RESULT 时**:
  - 读到的归一状态不同 → `REJECTED_STATE_INCONSISTENT`,不写;
  - 状态相同,且 `accepted`、`sbs_target_echo`、`per_arch_status_json` 均与最新 RESULT 相同 → 幂等,输出已有 event,不写;
  - 状态相同但 `accepted` 等判定字段有变化 → 写新结果文件并追加新的 RESULT,旧事件与旧文件保留;最新 RESULT 为权威;不重复追加状态。
- (v1.6 实测)C6b 对已有 PASS 的 request 重读:RESULT 仍为原事件、数据库逐字节不变、未保留新结果文件,新增的 4 个页面证据照常归档(附录 C 第 15 项)。

### 5.5 (v1.6 新增)自动查找构建号

**为什么需要**:真实提交实测点 Ok 后落在 `/wicket/page`,不是构建页(附录 C 第 17 项),C6 只能由人去 QuickBuild 按请求标记查号再绑定;P12 要批量提交,不能每个构建都靠人工。已取证的事实足以让工具自己查:配置页 `Recent Builds` 表在服务器原始字节中列出该配置最近的构建(含运行中的),每行带构建号链接(附录 C 第 18 项);父构建 `BUILD_NOTES` 原样回显请求标记(附录 C 第 15 项);请求标记含 32 位随机请求号,只对应一个请求。

**原则**:
- 查找只负责给出候选构建号;**绑定一律走第 5.2 节同一组核对与同一个写事务**,不放宽任何一步。查找宽松最多造成"找不到"(回到人工绑定),不会造成错绑。
- 只用已有的 `read` 命令与已有的只读放行集合(登记的配置页、`/build/<id>/variables`、`/build/<id>/overview`),**不新增代理命令、代理代码或放行规则**。配置页上有"停止构建""取消请求"等链接,工具从不点击、从不访问;只读阶段这些地址本就被拒(第 3.4 节)。
- 他人构建的页面不落盘。

**两种模式**:

| 模式 | 调用处 | 基线 W | 轮询 |
|---|---|---|---|
| 提交后 | `qb-trigger` 第 4.3 节第 10 步,落点 unknown(且不是驱动侧失败) | 第 4.3 节第 2.5 步读到的最大构建号 | (v1.7 改写)截止点 = `submit` 应答时刻 + 180 秒(本机单调时钟);首轮立即开始;未找到则上一轮结束后等 20 秒再开始下一轮;截止点之后不再发起任何新的读取;共至多 10 轮(详见第 4 步) |
| 读取时 | `qb-result-fetch --request-id R`,R 未绑定(第 5.1 节) | 无(视为 0) | 单次 |

**前置**(两种模式相同,在该 unit 的 `.sandbox_submit.lock` 内;第 5.1 节以本段为唯一定义):R 是其 unit 的最新 request;R 没有 BUILD_BOUND;unit 最新状态为 QB_REQUESTED。(按第 4.3、6.3 节的迁移,"最新 request 未绑定"时状态只可能是 QB_REQUESTED 或 QB_SUBMIT_FAILED;写成正面条件,是为了状态集合将来增项时不至于静默放行。)

**步骤**:

1. **读配置页并核对**:`read /overview/<N>`,N 为冻结 profile 的 `overview_id`(提交后模式在首次冻结之前取配置值,两者相同由第 2.2 节保证)。在 Python 中解析脱敏 HTML,以下全部成立才算"可识别":
   a. HTTP 200;
   b. 页面身份:`<title>` 等于 `QuickBuild - <configuration_path>`,或以它加 ` - ` 开头;面包屑各段拼接、"复制路径"脚本参数都恰好一个且等于 `configuration_path`(附录 C 第 3 项"配置页两项",C2b 起已用于同一页面);
   c. (v1.7 写明标题取法)区块标题按已取证结构取:区块标题栏(`.box-head`)的直接子元素 `.flex-1` 的文字,去首尾空白后等于 `Recent Builds`;不得取整个标题栏的文字(标题栏里还有 `history`、`rss` 两个操作链接,整栏文字为 `Recent Builds history rss`,附录 C 第 18 项)。这样的区块恰好一个,区块内恰好一个表格,表头恰为 `Id`、`Version`、`Master Node`、`Begin Date`、`Duration`、`Triggered By` 六列;
   d. 每个数据行:`Id` 单元格文字(去首尾空白)完整匹配 `^\d+$`;`Version` 单元格中 href 完整匹配 `^/build/(\d+)$` 的链接恰好一个,其数字等于该行 Id;同一 Id 不得出现在两行;数据行不超过 50 行(实测 10 行;上限防止页面异常引发大量读取)。同一单元格中的其它链接(下拉菜单 `javascript:void(0);`、运行中构建的停止链接等)忽略,且不访问。
   任一不成立 → 本轮结果"配置页不可识别"。行数可以为 0。`Build Requests` 表不参与查找:排队中尚未创建的构建没有构建号;已创建的运行中构建同时出现在 `Recent Builds` 中(附录 C 第 18 项)。
2. **确定候选**:`Recent Builds` 各行的构建号中,大于 W 的;去掉已绑定到本库任何 request 的构建号(不读取);去掉本次执行中已判为"标记不同"的构建号;按构建号升序。
3. **逐个核对候选**:对每个候选 P 执行 `read /build/P/variables`,用第 5.3 节第 2 项的变量表解析规则判定:
   - `BUILD_NOTES` 行恰好一个,且值等于 `clang-fix-campaign request=<R>` → "匹配";
   - `BUILD_NOTES` 行恰好一个,值为其它(含空)→ "标记不同",本次执行内不再读取;
   - `BUILD_NOTES` 行缺失或多于一个、HTTP 非 200、重定向、构建号不符(`QB_READ_ID_MISMATCH`)→ "暂不可读",下一轮重读(运行中的构建变量可能尚未完整,不能据此排除);这类读取不写诊断目录(页面属于他人构建)。(v1.7 写明)因为不扩展代理协议,代理遇到 `QB_READ_ID_MISMATCH` 时仍会按第 3.2 节在应答中附带 `diagnostic`;Python 收到后直接丢弃,不落盘、不进 trace、不进 stdout。即他人构建页只在代理与驱动进程的内存中短暂存在,这是不扩协议的已接受代价;
   - 代理异常或退出、可信读取环境不可用、(v1.7)`read` 应答超过 60 秒 → 立即停止查找,结果"读取失败"。
   非匹配候选的页面在内存中判定后丢弃,**不归档**;trace 只记构建号与判定类别;页面的登记位置外身份计数照常累计进 trace。
4. **轮询与总时限**(只在提交后模式;v1.7 改写):整个查找共享一个截止点,即 `submit` 应答时刻加 180 秒,用本机单调时钟,不用页面上的时间(QuickBuild 服务器时钟与本机不同步,附录 C 第 17 项)。
   - 每次发起读取之前检查截止点——(v1.8 写明范围)包括配置页、候选变量页,以及转入第 5.2 节绑定所需的 `/build/P/overview`;当前时刻**严格大于**截止点时停止查找,不再发起新的读取。已在进行中的那一次读取不中断,其耗时受第 3.2 节"`read` 应答等待上限 60 秒"约束,所以查找(含绑定读取)总耗时不超过约 240 秒;
   - 本轮没有匹配 → 等 20 秒(等待到截止点为止);截止点未过则回到第 1 步开始下一轮;
   - 某一轮配置页读取失败(非代理异常)或不可识别,只记入 trace,照常进入下一轮;
   - 轮次至多 10 轮(读取零耗时时恰为 10 轮,第 10 轮恰在第 180 秒开始并照常发起;实际读取有耗时时更少)。
   到期仍无匹配,按最后一轮的情况归类为"未找到""配置页不可识别"或"配置页读取失败";截止点过时某一轮的候选尚未全部核对完,或(v1.8)已有唯一匹配但绑定所需的概览页尚未发起读取,归类为"查找超时"。浏览器关闭与清理按第 3.1 节的关闭协议另行计时,不计入本时限。
5. **结果**:
   - 同一轮的候选**全部核对完**,且恰好一个"匹配"P,且(v1.8)绑定所需的 `/build/P/overview` 在截止点之前发起读取 → 交第 5.2 节绑定(复用第 3 步读到的变量页,只再读 `/build/P/overview`;该读取若在截止点之前发起、之后返回,按其结果照常核对与绑定);(v1.7)某一轮因截止点未核对完全部候选时,即使已出现一个匹配也不绑定(无法确认是否唯一),结果"查找超时",交读取时模式补绑定;(v1.8)全部候选核对完、唯一匹配,但截止点已过、概览页未发起 → 同样不绑定,"查找超时";
   - 同一轮两个及以上"匹配" → "多于一个",不绑定;
   - 其它 → 上一步的类别。
   归档:查找结束时(交给第 5.2 节绑定之前),最后一次读到的配置页按第 3.7 节写后自检,归档为 `<state_root>/qb_evidence/<R>/<序号>.overview-<N>.html`(序号按第 5.3 节末尾的规则);"匹配"构建的两页按第 5.2 节归档。任一归档写后自检失败 → 删除该文件,不绑定;提交后模式 `submit_uncertain`、`error_code=QB_EVIDENCE_REDACTION_FAILED`,读取时模式 exit 5 `QB_EVIDENCE_REDACTION_FAILED`。
   trace(固定字段,不含页面内容):`request_id`、模式、W、每一轮的开始时间(相对 `submit` 应答的秒数;读取时模式为 0)、配置页 HTTP 状态与行数、各候选的构建号与判定类别、(v1.8)每次读取的耗时(毫秒,用于用真机数据核对 60 秒上限的余量)、最终结果类别。
   结果到 CLI 输出的映射见第 4.3 节第 10 步(提交后模式)与第 5.1 节(读取时模式)。

**已接受的限制**:
- 基线 W 的前提是构建号随创建时间递增(两份配置页样本中,构建号与 Begin Date 的顺序一致,附录 C 第 18 项)。万一不成立,提交后模式会漏找,结果为"未找到";随后读取时模式(无基线)可以补上。
- `Recent Builds` 只列最近若干个构建(实测 10 个)。构建被更新的构建挤出该表后,读取时模式也找不到,只能人工绑定;`/history/<id>` 等页面不在只读放行集合内,本版不扩。P12 批量提交时,`qb-trigger` 逐 unit 执行,每个 unit 在下一个提交之前完成查找,正常情况下不会被自己的提交挤出。
- (v1.7 新增)**批量恢复的时效**:`Recent Builds` 实测只有 10 行。P12 批量提交中出现未绑定的 request(提交后查找未命中、查找超时、`submit` 后驱动侧失败、或第 4.4 节的崩溃)时,必须在该配置再产生约 10 个构建之前运行读取时模式补绑定,否则只能人工查号;批量越大越紧迫。`qb-trigger` 的 `message` 已写明这一点(第 4.3 节第 10 步);收口文档(第 10 节 C8)须把它列为 P12 的操作要求。(v1.8 改写)`qb-result-fetch --requests-file` 保持输入顺序处理、stdout 按输入顺序输出的既有约定,不自动重排,也不承诺整批的完成时长:恢复能否赶上窗口,取决于请求在批中的位置、每个请求的候选读取耗时(每个请求至多 50 个候选)与该配置的构建速率。因此 P12 的操作要求是:出现未绑定 request 时,**先恢复未绑定的请求(可只把它们单独列进一次 `--requests-file`),再继续批量提交**;已移出窗口的转人工查号。
- 读取时模式读的是 `Recent Builds` 中未被本库绑定的全部行(样本 10 行,规范上限 50 行),多为他人构建的变量页,只在内存中判定,不落盘;第 9.4 节第 3 步在真机上验证一次。
- 构建在 180 秒之后才出现时,提交后模式报"未找到";实测构建在点 Ok 后数秒内即已开始(附录 C 第 17 项,推算值),之后用读取时模式补绑定。

---

## 6. 数据、写入原语与状态

### 6.1 表与查询

- 新表 `campaign_qb_profiles`(第 2.2 节)。`campaign_qb_requests` / `campaign_qb_events` 不改结构。(v1.6)自动查找不新增表或列;基线 W 只在同一次执行内使用,只写 trace;自动绑定写入的 `BUILD_BOUND` 与人工绑定相同,绑定途径记在 trace 中。
- 新只读查询 `qb_profile(state_db, branch)`。
- 事件语义修订:`SUBMITTED` = "提交意图已落库,即将放行提交"(原意"REST 提交成功"废止)。

### 6.2 按连接写入的内部原语(`campaign_state.py`)

现有 `create_qb_request`、`append_qb_event`、`append_status` 各自打开连接并开启 `BEGIN IMMEDIATE`,无法被外层合成一个事务。新增内部原语,沿用已有 `_append_event_on_connection` 的写法:

```python
def _create_qb_request_on_connection(conn, campaign_unit_key, *, request_id, sbs_target) -> int: ...
def _append_qb_event_on_connection(conn, *, request_seq, event_type, **fields) -> int: ...
def _append_status_on_connection(conn, campaign_unit_key, status, reason=None, arch_norm=None) -> None: ...
def _insert_qb_profile_on_connection(conn, branch, *, profile_json: str) -> None: ...
```

- 原语只做校验与写入,**不初始化 schema、不开启/提交/回滚事务、不关闭连接**;调用方负责一个 `BEGIN IMMEDIATE` 事务。
- `_insert_qb_profile_on_connection`:`profile_json` 必须是第 2.2 节定义的规范化 JSON 原文,原语不再二次序列化;原语内部计算 `profile_sha256 = sha256(profile_json 的 UTF-8 原始字节)`、`created_at` = 当前 UTC ISO8601,与 `profile_json` 一并写入;冲突处理见第 2.2 节。
- 现有三个公共 API 改为"开连接 → 开事务 → 调原语 → 提交",对外行为与校验不变,**包括 `create_qb_request` 对同一 `request_id`、同 unit 同 sbs_target 返回既有 `request_seq` 的幂等行为**。
- P5Q 的每个写入点都是一个事务:提交意图(冻结行 + request + SUBMITTED + 状态)、确定未放行(状态)、绑定(BUILD_BOUND + 状态)、非终态(状态)、结果(RESULT + 状态)。

(C1 已按本节实现,v1.3 不改。)

### 6.3 状态迁移(在 design.md §3.6 基础上)

| 从 | 触发 | 到 |
|---|---|---|
| SANDBOX_PUSHED / KB_APPENDED / QB_SUBMIT_FAILED | qb-trigger 第 8 步 | QB_REQUESTED |
| SANDBOX_QB_FAILED、QB_REQUESTED(未绑定) | 带 `--retrigger` 的 qb-trigger 第 8 步(新 request) | QB_REQUESTED |
| QB_REQUESTED | 提交确定未放行 | QB_SUBMIT_FAILED |
| QB_REQUESTED | 落点 build 且核对通过,自动查找绑定成功(v1.6,第 5.5 节),或人工绑定成功 | QB_TRIGGERED |
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
QB_FETCH_FAILED                   读取页面失败(非 200、重定向、构建号不符、登录失效、可信读取环境不可用、代理异常),不写 RESULT
QB_EVIDENCE_REDACTION_FAILED      证据写后脱敏自检失败,证据删除,不写 RESULT
```

`REJECTED_SANDBOX_NOT_BOUND`、`REJECTED_QB_BINDING_MISMATCH`、`REJECTED_QB_SUPERSEDED`、`REJECTED_STATE_INCONSISTENT`、`AmbiguousQbReference`、`CAMPAIGN_STATE_BUSY`、`INTERNAL_ERROR` 沿用,适用场景按本文扩展。代理内部应答(`QB_FORM_CHANGED`、`QB_FORM_VALUE_UNAVAILABLE`、`QB_READ_REDIRECTED`、`QB_READ_ID_MISMATCH`、`QB_TRUSTED_CONTEXT_UNAVAILABLE`、`AGENT_PHASE`)只在代理协议内使用,不作为 CLI 错误码输出。v1.3/v1.4 没有新增 CLI 错误码;`QB_FETCH_FAILED` 的说明多一种原因,随附录 A"v1.4 增补"一并同步 design.md §4.3。

(v1.6)没有新增 CLI 错误码,适用场景扩展如下(design.md §4.3 的说明文字已能覆盖,不改):
- `REJECTED_QB_FORM_CHANGED`:含提交前配置页基线读取不通过(第 4.3 节第 2.5 步,属"配置页结构与已取证结构不符");
- `REJECTED_QB_BINDING_MISMATCH`:含自动查找到的构建核对不通过或多于一个;读取时模式未找到(与 v1.5"未绑定即拒"同码);
- `QB_SUBMIT_UNCERTAIN`:含提交后模式未找到、配置页不可识别或读取失败;
- `QB_RESULT_UNRECOGNIZED`、`QB_FETCH_FAILED`:含读取时模式的配置页不可识别、配置页读取失败。

---

## 8. 安全要求汇总(验收逐条对应第 9 节用例)

1. 工具只在一个地方发起构建:`submit` 放行的那一次表单 action;每个表单至多一次;多个 unit 时每个 `open_form` 各至多一次。
2. 永远不发出 Ready to Accept、取消、停止、重跑、删除、REST、日志/报告/产物下载请求,包括重定向的后续跳;不使用绕开页面拦截的 HTTP 客户端。
3. 提交一旦放行,不再有"确定失败"的结论;不确定时不自动重提,只有人工 `--retrigger`。
4. 构建与请求的对应只靠回显:请求标记 + 目标行 + 父子构建号互指(`TRIGGER_ID`、`QB_TRIGGER_ID`)+ 配置路径 + 页面构建号;任何一项对不上都不绑定、不写 RESULT。
5. PASS 只来自子构建 Status 的精确文字 `Successful`,且子构建回显 `FAIL_FAST=yes`、架构为固定值、逐架构状态为空;子构建快照地址与冻结值不一致时不写结论(有指引的停止-报告),一致时只记录;快照漂移只能由人对单个 request 以开关接受,并在结果文件中留痕;无法识别一律不写 RESULT。FAIL 只表示含目标行的全量构建失败,附失败步骤与错误信息。
6. 表单每个字段显式设值(含"值已相等也触发一次回调")、逐项读回、提交前指纹复核;表单结构变化即停。
7. 复验参数每个 campaign × 工程冻结,配置改动只影响新 campaign;架构与失败传播相关参数不开放配置。
8. 凭据:工具不接触用户名密码;会话与 cookie 只在"浏览器 + 专用代理进程"可信边界内,协议事件中的请求头与请求体在适配层立即丢弃;浏览器临时目录在内存盘并在退出时删除;所有页面落盘前脱敏、写后自检;身份值按位置遮蔽。
9. 远端 sandbox ref 核对使用 P5 的隔离传输与统一 git 环境,远端地址由配置构造。(v1.6)传输仓库为默认格式的一次性 bare 仓库,只做 `ls-remote`。
10. 每个数据库写入点是一个事务;复验未出结果期间不构成 P5R 人工降级条件。
11. 拦截面在首个页面导航前装好,覆盖 HTTP 每一跳(含 307/308 的响应阶段终止)、WebSocket 与新目标;Worker 类目标与新窗口执行前阻断。
12. (v1.3/v1.4/v1.5)页面主环境不可信:生产代理不使用第 3.1 节列出的任何主环境执行接口,唯一例外是首个导航前安装 `window.open` 守卫的一处 `addInitScript`;读取的业务数据来自同一次导航响应的服务器原始字节,按 charset 严格解码,在每次导航后新建的隔离环境中惰性解析;表单读回在隔离环境中读活动 DOM;规整与判定在代理进程或 Python 中做;派发 `change` 进入主环境、可被页面吞掉,属已接受残余(后果为失败,不会错填);Python 脱敏自检不承担业务真实性证明。
13. (v1.3/v1.4)结构核对失败时先撤销本表单的登记,只在已有数据上被动取证(不克隆活动节点、不发新请求、不重试),结构事实与 HTML 同一脱敏上下文,诊断失败不返回原始内容。
14. (v1.3)登录提交只放行登录表单(`content-form`)、最多 5 次、首个跳转后关闭;字段回调只多允许末尾一个十进制 `random` 参数;定时刷新一律拒绝。
15. (v1.4/v1.5)身份值按登记位置遮蔽(含 `Requested By`),不全局改写页面业务内容;写后自检查凭据全局残留与登记位置,不做全局显示名检查;凭据类值全局脱敏。
16. (v1.4)代理不保留任何定时刷新放行集合;静默判定只计放行请求。
17. (v1.6)自动查找只用已有 `read` 命令与已有只读放行集合中的页面(登记的配置页、构建变量页与概览页),不新增代理命令、代码或放行规则,不点击、不访问配置页上的任何其它链接;查找只给出候选,绑定一律经第 5.2 节同一组核对与同一个写事务;找不到或多于一个时保持未绑定,交人处理;他人构建的页面不落盘;配置页不可识别时不提交。(v1.7)驱动侧失败不做查找;查找有总时限,未核对完整轮不绑定。(v1.8)总时限覆盖绑定所需的读取;`read`、`submit` 有驱动侧应答上限,超时即终止代理且不重启。
18. (v1.6)关闭协议:代理收到 `close` 后自行退出,驱动写出 `close` 后立即关闭 stdin;测试入口与生产入口的退出行为一致。
19. (v1.6)诊断附加字段(`failure_category`、`snapshot_state`、`login_facts`)键集合与取值固定,由 Python 严格校验;不含查询值、请求头、请求体、账号、密码或 Cookie;只进 trace 与提示文字,不改 stdout 结构、错误码与判定。

---

## 9. 验收用例(DoD)

### 9.1 Python 侧(假代理,CI 必跑)

用一个实现第 3.2 节协议的假代理(Python,按用例脚本应答,并记录收到的每条命令)驱动 CLI,真实 state DB 与本地裸仓库。页面样本一律以附录 C 所列真实归档页为模板改造,不手写结构。

触发前置与幂等:
- [ ] 状态不足、无 DERIVE、无 PUSH、PUSH result≠ok、pushed_sha≠derived、ref 不在白名单,各自独立 → `REJECTED_SANDBOX_NOT_BOUND`,假代理 `submit` 0 次。
- [ ] PUSH 事件为 P5 实际形态(`url=None`)时正常通过。
- [ ] 远端 ref 在填表后被改(本地裸仓库改写)→ `REJECTED_SANDBOX_NOT_BOUND`,无新 request。
- [ ] 隔离传输:主副本 `.git/config` 加一个名字等于远端地址字符串的具名远端、以及 `url.<x>.insteadOf`/`pushInsteadOf` 指向另一个含假 sandbox ref 的裸仓库 → 核对结果取自真实远端;用 git 调用包装统计 argv,断言没有任何 git 命令以主副本为 `-C`/`--git-dir`。把 `_sandbox_git` 的任一覆盖项移除(变异)→ 本例必须变红。
- [ ] 正确 sha 存在于另一个仓库、目标仓库的 ref 指向别的 sha → `REJECTED_SANDBOX_NOT_BOUND`。
- [ ] 第 4.2 节幂等表每一格一例(含带/不带 `--retrigger`),断言 submit 次数与新增 request 数。
- [ ] `--retrigger` 追加新 request,旧 request 及其事件逐字段不变。
- [ ] 第 8 步事务内重查发现并发写入改变状态或最新 request → `REJECTED_STATE_INCONSISTENT`,事务回滚无残留,submit 0 次。
- [ ] 多 unit:三 unit 的 `--units-file`,第 2 个在 `fill` 失败 → 假代理收到 `open_form` 3 次、`submit` 2 次;恰好 2 个新 request;第 2 个 unit 无任何写入;三项 action 依次为 `submitted_bound`/`rejected`/`submitted_bound`。(v1.6)每个 unit 在 `open_form` 之前各读一次配置页(第 4.3 节第 2.5 步)。
- [ ] (v1.8)批次中途代理不可用:三 unit,第 2 个的 `read` 应答挂起导致终止 → 第 1 个 `submitted_bound`;第 2 个按所处步骤处理(放行前为 `rejected` + `QB_BROWSER_UNAVAILABLE`);第 3 个 `rejected` + `QB_BROWSER_UNAVAILABLE`,`message` 为第 4.3 节第 1 步的模板,代理收到的命令为 0、`open_form` 0 次、零数据库写入;trace 中恰一条 `agent_terminated`;代理不被重启(只登录一次)。另一例:第 2 个在 `submit` 应答超过 150 秒 → 第 2 个 `submit_uncertain` + `QB_SUBMIT_UNCERTAIN`、不查找,第 3 个同上。

填表与提交:
- [ ] `open_form` 返回表单已变 / 字段集合多一项 / 少一项 / 双列表少一个角色 / 多一个同标签控件 → `REJECTED_QB_FORM_CHANGED`,无 DB 写入;应答带 `diagnostic` 时诊断目录写出、写后自检通过、stdout 带 `diagnostic_dir`;诊断写出失败时错误码不变。
- [ ] 读回值任一项不等(逐字段各一例,含 Build Package List 多一行、尾随空格、Add Package List 非空、CHILD_CONFIGURATIONS 多一项、recorder 与 selection 不一致)→ `REJECTED_QB_FORM_MISMATCH`。
- [ ] SNAPSHOT_NUM 冻结值不在下拉框 → `REJECTED_QB_SNAPSHOT_UNAVAILABLE`,stdout 含冻结值与当前值;且同 campaign 中已有终态 RESULT 的其它 unit 的事件与结果文件逐字段不变。
- [ ] (v1.6 并入,已实现)快照提示两个模板:有冻结值/首次冻结 × `selected` 为 0 项/1 项/多项/null 的全部组合各一例,外加"配置写了具体快照但库中无冻结行"一例(按首次冻结处理);stdout `message` 与 trace 文字逐字一致;`snapshot_state` 键集合多一个、少一个、`selected` 含超长或非法字符项、`option_count` 为负数 → 协议错误 `QB_BROWSER_UNAVAILABLE`;非 SNAPSHOT_NUM 错误应答带 `snapshot_state` → 协议错误。
- [ ] `@freeze`:选项一个 → 冻结成功;选项多个、有选中项 → 冻结选中项,trace 含选项数;无选中项 → `REJECTED_QB_SNAPSHOT_UNAVAILABLE`。
- [ ] `released: false` → 状态 QB_SUBMIT_FAILED、该 request 只有 SUBMITTED;紧接着不带 `--retrigger` 重跑 → 产生新 request,submit 恰好被调用一次。
- [ ] 落点 build 且回显一致 → SUBMITTED + BUILD_BOUND + QB_TRIGGERED。
- [ ] 落点 build 但请求标记不符 / P 已绑定到其它 request → 无 BUILD_BOUND,`submit_uncertain`,`REJECTED_QB_BINDING_MISMATCH`。
- [ ] 落点 unknown,且自动查找到期未找到(假配置页只有 W 及以下的构建)→ 只有 SUBMITTED,状态 QB_REQUESTED,`error_code == QB_SUBMIT_UNCERTAIN`,`message` 含观察到的落点、结果类别与候选计数;不带 `--retrigger` 重跑 → `already_requested`,`message` 为第 4.2 节第 5 步的提示,submit 0 次。
- [ ] 第 4.4 节每个崩溃点一例,断言 request 条数、事件与状态。
- [ ] 登录超时 → 无 DB 写入,exit 5。

参数冻结与配置:
- [ ] 首次触发写冻结行;第二个 unit 同 branch 复用;改配置任一键 → `REJECTED_QB_PARAMS_CHANGED`,且不启动代理。
- [ ] 新 state DB 用改后的配置可正常冻结新值;两个 branch 各自冻结,`qb_profile` 按 branch 取得各自的行。
- [ ] 冻结行原语第二次写不同内容 → StateInconsistent;同内容 → no-op。
- [ ] 冻结行的 `profile_sha256` 等于 `profile_json` 原始字节的 sha256,`created_at` 为合法 UTC ISO8601;直接 INSERT 63 位 `profile_sha256` → 被 CHECK 拒。
- [ ] 并发冻结:同 branch、内容相同 → 本 unit 正常提交、不新增冻结行;内容不同 → `REJECTED_QB_PARAMS_CHANGED`,无 request。
- [ ] 配置中 CHILD_CONFIGURATIONS 为单架构 / 缺架构 / 重复 / 多组,`Immediate Stop With Error: false`,TARGET_IMAGE 非空,`configuration_path` 不以 `/RBS/TRIGGER` 结尾,`overview_id` 非正整数 → `INVALID_ARGS`,不启动代理。

读取与落库(样本以 live-12 的 `01`–`05.response.html` 为模板):
- [ ] 第 5.3 节每一条核对各一个负例 → `REJECTED_QB_BINDING_MISMATCH`,无 RESULT。至少包括:父构建 `QB_TRIGGER_ID` 不等;`BUILD_PKG_LIST_MODIFY` 两行;`BUILD_NOTES` 缺失或不等;父构建 `FAIL_FAST=no`;父构建 `CHILD_CONFIGURATIONS` 不等;面包屑或复制路径不等;Configuration Overview 链接指向别的 id;Child Build 表一行但架构与固定值不等;Child Build 链接不是本站绝对地址;子构建 `TRIGGER_ID` 不等、`QB_TRIGGER_ID` 不等;子构建 `FAIL_FAST=no`、缺失;子构建 `REPO_ARCH` 不等;子构建 `BUILD_REFERENCE` 缺失;`EACH_GBS_BUILD_STATUS` 行缺失;子构建配置路径末段不是 `build`。(v1.5)`SNAPSHOT_NUM_URL` 的缺失与不一致统一按下方"子构建快照"项验收,不在本项。
- [ ] (v1.5)子构建 `BUILD_REFERENCE=Live`、其它条件全部满足 → 照常判定与落库,原值进入 `child_params_echo`(只记录)。
- [ ] 子构建 `BUILD_PKG_LIST`:全量列表中含目标行一次 → 通过,`sbs_target_echo` 为该行;目标行缺失、出现两次、同一仓库另一 commit 同时出现 → `REJECTED_QB_BINDING_MISMATCH`。
- [ ] 父构建 `SNAPSHOT_NUM` 为 `do not need select` 或任意值 → 不影响判定,原值进入 `params_echo`。
- [ ] (v1.4/v1.5)子构建快照:归档样本地址(根正确、快照名等于冻结值)→ `snapshot_used` 为冻结值、`snapshot_drift_accepted=false`,照常落库;外站主机、错误工程路径、`RBS` 产物根、`file:` 地址、带用户信息、带查询、带片段、带尾斜杠、根后两段、快照名形态不同、缺 `SNAPSHOT_NUM_URL` → 各自 `QB_RESULT_UNRECOGNIZED`,无 RESULT,stdout 含冻结值、读到的值、证据路径与(v1.7 同步 R1 定案的措辞)"子构建快照地址的主机、路径根或形态与登记不符,须人工核对后按 R1 修订附录 C 第 6 项的登记"指引;以上各例带 `--accept-snapshot-drift` 结果不变。
- [ ] (v1.5)快照漂移:根与形态相符、快照名为另一日期 → 不带开关:`QB_RESULT_UNRECOGNIZED`,无 RESULT,stdout 含冻结值、实际值与漂移处置指引;带开关 → 照常落库,`snapshot_used` 为实际值、`snapshot_drift_accepted=true`,trace 记两值;已接受后不带开关再读同一快照 → 视同已裁定,按第 5.4 节幂等;开关与 `--requests-file` 或单独 `--qb-build-id` 同用 → exit 2 `INVALID_ARGS`,不启动代理。
- [ ] (v1.4/v1.5)失败归因:终态失败时读 step_status,失败步骤路径与 Error Message 写入结果文件;step_status 缺失、HTTP 404、构建号不符、结构不符 → 两键为 null,判定结果仍为 FAIL,照常写 RESULT,不得变成 `QB_RESULT_UNRECOGNIZED` 或 `QB_FETCH_FAILED`;step_status 证据脱敏自检失败(注入)→ `QB_EVIDENCE_REDACTION_FAILED`,无 RESULT;读 step_status 时代理退出或 `QB_TRUSTED_CONTEXT_UNAVAILABLE` → `QB_FETCH_FAILED`,无 RESULT;PASS 时不读该页,两键为 null。
- [ ] (v1.4)五项配置来源:三标签 id 不一致、某标签重复、标签指向外站同路径、带查询或片段、面包屑与复制路径不一致、构建名前缀不符 → 各自 `REJECTED_QB_BINDING_MISMATCH`。
- [ ] `EACH_GBS_BUILD_STATUS` 非空 → `QB_RESULT_UNRECOGNIZED`,无 RESULT,stdout 含处置指引文本、trace 记录证据路径;此状态下 `--retrigger` → `REJECTED_QB_REQUEST_PENDING`;为空 + `FAIL_FAST=yes` + `Successful` → PASS;为空 + `Failed` → FAIL(按 live-12 真实样本)。
- [ ] Child Build 表为空 → 非终态,无 RESULT,状态 SANDBOX_QB_PENDING;再次读取不重复追加状态。
- [ ] Child Build 表为空,但父构建任一核对不符 → `REJECTED_QB_BINDING_MISMATCH`,零 BUILD_BOUND、零 RESULT、无 PENDING 状态;全部相符 → 可绑定并进入 PENDING。
- [ ] Child Build 表两行、表头列不同 → `QB_RESULT_UNRECOGNIZED`。
- [ ] 第 1 节状态表每一行一例;`" Successful "` 经去首尾空白 → PASS;`Success ful`、`successful`、`Success` → `QB_RESULT_UNRECOGNIZED`,无 RESULT。
- [ ] 代理 `read`(必读页面)返回重定向 / 构建号不符 / `QB_TRUSTED_CONTEXT_UNAVAILABLE` → `QB_FETCH_FAILED`,无 RESULT。(主环境内置函数被改写时可信读取结果不变,由第 9.2、9.3 节验证。)
- [ ] PASS 写 RESULT:文件 sha256 = 事件 `qb_result_sha256`;`latest_qb_result` 两级最新返回该事件;文件键集合固定(含 v1.3/v1.4/v1.5 新增键);`params_echo` 存父构建值、`child_params_echo` 存子构建值,两者原文不串位,`child_params_echo` 的键集合恰为两个。
- [ ] 首次读取即 PASS、首次读取即终态失败,各一例。
- [ ] 终态 RESULT 后再次读取:同状态同字段 → 不新增;accepted 变化 → 新 RESULT 与新文件,旧的不变;状态不同 → `REJECTED_STATE_INCONSISTENT`。
- [ ] `accepted` 解析:`ACCEPTED`、`ACCEPTED (2026-10-10 12:00)` → true;`ACCEPTED_BY_X`、`NOT_ACCEPTED` → false;无该栏 → null。
- [ ] 非最新 request → `REJECTED_QB_SUPERSEDED`,不读取;读取期间被 retrigger(并发)→ 落库事务重查失败,回滚并删除结果文件。
- [ ] 人工指定绑定:成功;P 已绑定到其它 request → 拒;unit 状态 QB_SUBMIT_FAILED → 拒;请求标记不符 → 拒。
- [ ] `--qb-build-id` 单独且未 BUILD_BOUND → exit 4,不挂到最新 request。

自动查找与绑定(v1.6,第 4.3 节第 2.5、10 步,第 5.1、5.5 节;假配置页以 `S/C6b/raw-active-01/05.raw-redacted.html` 的原始字节为模板改造,假时钟驱动轮询,不真实等待):
- [ ] 提交后模式,一轮命中:第一轮配置页含一个大于 W 的新构建,其变量页 `BUILD_NOTES` 等于请求标记 → 第 5.2 节核对通过 → SUBMITTED + BUILD_BOUND + QB_TRIGGERED,`submitted_bound`,`message` 为绑定模板;假代理收到的 `read` 依次恰为:基线配置页、配置页、候选变量页、候选概览页;W 及以下的构建一个也不读;两页构建证据与配置页按第 5.5 节归档并通过写后自检。
- [ ] 第一轮新构建尚未出现、第二轮出现 → 第二轮绑定;(v1.7 改写)始终不出现:假时钟下读取零耗时 → 恰 10 轮、配置页(不含基线)读 10 次、`QB_SUBMIT_UNCERTAIN`,`message` 含"未找到"与候选计数;读取期间假时钟推进(每轮 5 秒)→ 轮次少于 10、截止点之后零新读取。
- [ ] (v1.7)总时限:首轮 50 个慢候选(每次读取推进假时钟 30 秒)→ 截止点后不再发起读取,本轮未核对完,结果"查找超时",零 BUILD_BOUND;截止点前最后一次读取恰好命中匹配、但本轮仍有未核对的候选 → 不绑定、"查找超时";单次 `read` 应答挂起 → 驱动 60 秒后终止代理,写 `agent_terminated` 记录,结果"读取失败",零 BUILD_BOUND。
- [ ] (v1.8)截止点与绑定读取:最后一个候选在截止点前发起、截止点后返回,本轮全部核对完且唯一匹配,但概览页尚未发起 → 不再读取、零绑定、"查找超时";概览页在截止点前发起、截止点后返回且核对通过 → 照常绑定;两例都断言配置页归档、unit 状态与 stdout。边界:读取零耗时时第 10 轮恰在第 180 秒开始且照常发起(截止点比较为"严格大于")。trace 含每次读取的耗时字段。
- [ ] 候选第一轮 `BUILD_NOTES` 行缺失 → "暂不可读",第二轮出现本请求标记 → 绑定;"标记不同"(含空值)的候选在后续轮次不再读取(假代理计数);候选读取返回重定向、构建号不符、HTTP 非 200 → "暂不可读",不写诊断目录;(v1.7)候选读取返回带 `diagnostic` 的 `QB_READ_ID_MISMATCH` → `qb_diagnostics/` 零新增目录,trace 与 stdout 中不含该页任何内容。
- [ ] 同一轮两个候选都带本请求标记 → `submit_uncertain`,`REJECTED_QB_BINDING_MISMATCH`,零 BUILD_BOUND,`message` 列出两个构建号。
- [ ] 匹配候选的第 5.2 节核对不通过(各一例:三标签 id 不等于冻结 `overview_id`、`BUILD_PKG_LIST_MODIFY` 两行、`QB_TRIGGER_ID` 不等)→ `REJECTED_QB_BINDING_MISMATCH`,零 BUILD_BOUND。
- [ ] 匹配的构建号已绑定到本库其它 request → 不读取(第 5.5 节第 2 步排除),结果"未找到"。
- [ ] 配置页不可识别,各一例:title 不符、面包屑或复制路径不符、无 `Recent Builds`、两个 `Recent Builds`、(v1.7)`Recent Builds` 只出现在标题标签以外的位置、表头多一列或顺序不同、Id 与链接数字不同、`Version` 单元格两个 `/build/` 链接、同一 Id 两行、51 行 → 提交前(第 2.5 步):`rejected`、`REJECTED_QB_FORM_CHANGED`、零数据库写入、submit 0 次、`open_form` 0 次,(v1.8)`message` 按第 4.3 节第 2.5 步分"页面身份"与"`Recent Builds` 结构"两类模板、含首个失败核对项名,两类 `error_code` 相同;提交后各轮:结果"配置页不可识别"、到期 `QB_SUBMIT_UNCERTAIN`;读取时模式:exit 5 `QB_RESULT_UNRECOGNIZED`,配置页证据归档。0 行的 `Recent Builds` → 可识别,W=0。(v1.7)正例:真实结构的标题栏(`.flex-1` 为 `Recent Builds`,同栏另有 `history`、`rss` 链接)→ 可识别。
- [ ] 配置页 HTTP 非 200、重定向:提交前 → `rejected`、`REJECTED_QB_FORM_CHANGED`;读取时模式 → `QB_FETCH_FAILED`。
- [ ] 查找中代理退出、`QB_TRUSTED_CONTEXT_UNAVAILABLE`(v1.7:设在第 2 个候选读取时)→ 立即停止查找;提交后模式 `submit_uncertain`、`QB_SUBMIT_UNCERTAIN`(`message` 结果类别为"读取失败"),读取时模式 `QB_FETCH_FAILED`;两种模式下已读到的配置页仍按第 5.5 节第 5 步归档并通过写后自检;均零 BUILD_BOUND、零数据库写入。
- [ ] (v1.7 改写,v1.8 扩充)`submit` 发出后的驱动侧失败:经**真实 Python 驱动**(不是假代理直接抛异常),按第 3.2 节"驱动侧失败的外延"逐类各注入一例(进程不存在、管道断开、EOF、非法 JSON、非对象或 `ok` 非布尔、含敏感键、三个附加字段越位或取值非法、`ok: true` 但落点不合法或带 `html_redacted`、`ok: false` 但 `released` 不为假、`submit` 应答超过 150 秒)→ 驱动带内部标记返回,CLI 不做查找:提交后零条 `read`,`QB_SUBMIT_UNCERTAIN`,状态 QB_REQUESTED;其中"`ok: true` 但 build 落点的构建号形态非法"与"`ok: false` 但 `released` 不为假"两类额外断言零条 `read`(最容易被实现成继续查找);该内部标记不出现在任何 stdout 项、结果文件与数据库字段中;对照正例:代理返回合法 `landed: unknown` → 启动查找;代理在放行后内部出错返回的合法 unknown → 启动查找,其后读取失败归"读取失败"。
- [ ] 落点 build(第 4.3 节第 10 步原路径)→ 不做查找,行为与 v1.5 相同。
- [ ] 基线:一个带本请求标记、但构建号不大于 W 的构建(构造)→ 提交后模式不读取、结果"未找到";随后读取时模式(无基线)找到并绑定。
- [ ] 读取时模式:R 未绑定、配置页含匹配 → 绑定并继续第 5.3 节读取,首次读取即 PASS、非终态各一例,输出与人工绑定后的读取相同;未找到 → exit 4 `REJECTED_QB_BINDING_MISMATCH`、`message` 含候选计数、零写入;R 不是最新 → `REJECTED_QB_SUPERSEDED`,不读配置页;unit 状态为 QB_SUBMIT_FAILED → 拒绝,不读配置页;(v1.7)人为构造的不一致库(最新 request 未绑定但 unit 状态为 QB_TRIGGERED)→ 拒绝,不读配置页;`--requests-file` 三项(已绑定、未绑定可找到、未绑定找不到)各自独立;R 已绑定 → 不读配置页。
- [ ] (v1.8)`--requests-file` 顺序:假时钟下前一项候选读取很慢、后一项的构建在此期间被挤出 `Recent Builds` → 输出仍按输入顺序,后一项"未找到"、不写绑定、不自动重提。
- [ ] (v1.8)把限制钉成事实:候选变量页夹具含一个未登记的账号承载列(例如额外的 `Owner` 列,值为第三方姓名)→ "登记位置外的登录显示名计数"不变(该计数不能发现它),且该页零归档;同一夹具值改为登录显示名 → 计数加一。
- [ ] (v1.7)证据序号:同一 request 连续两次 fetch(第一次非终态、第二次终态)→ 第二次的文件序号接着第一次,旧文件不被覆盖,结果文件 `evidence` 只列本次写入的文件;读取时模式自动绑定时,配置页是本次执行的第一个文件。
- [ ] 证据与 trace:非匹配候选的页面零落盘;归档的配置页中 `Requested By`、`Triggered By` 为 `<USER>`,写后自检通过;把其中一格改回显示名 → 写后自检失败、文件删除、零 BUILD_BOUND,提交后模式 `submit_uncertain` + `QB_EVIDENCE_REDACTION_FAILED`,读取时模式 exit 5 `QB_EVIDENCE_REDACTION_FAILED`;trace 字段集合固定、不含页面内容。
- [ ] 并发:查找完成后、绑定事务之前,另一进程已为 R 写入 BUILD_BOUND 或 retrigger 出新 request → 第 5.2 节第 5 步事务内重查失败,不写,无重复 BUILD_BOUND。

事务与原语:
- [ ] 每个写入点在事务中途注入异常 → 整组回滚,无半提交。
- [ ] 外层持 `BEGIN IMMEDIATE` 时调用四个原语成功;公共 API 行为与既有测试一致。

凭据与脱敏:
- [ ] 假代理在页面中植入登录显示名、hidden token、`jsessionid=` URL、`JSESSIONID_8810=` 文本 → 证据文件、诊断目录、stdout、stderr、trace、qb_result 中均不出现(显示名指登记的身份承载位置);双列表 recorder 原值保留。
- [ ] (v1.4)身份值按位置遮蔽:与代理共用测试向量。显示名分别为 `Successful`、`Failed`、`Full`、`root`、`Lin` 时,`Welcome!` 区域与 `Triggered By` 列被遮蔽;Status 单元格、变量值、配置路径、选项文字、`ILinkListener` 等原样保留;合法 PASS/FAIL 与绑定结果不变;显示名在自由文本中出现时只计数不阻断。(v1.5)显示名为 `Successful`、`Full`、`root` 的三例还必须断言**写后自检通过**、RESULT 照常写入(本例在 v1.4 时的代码上必须变红)。
- [ ] (v1.5)身份位置登记:配置页夹具(以 live-12 `06.response.html` 为模板)含 `Requested By` 列 → 该格为 `<USER>`,写后自检通过;把该格改回显示名 → 写后自检失败;夹具含一个未登记的账号列(例如 `Owner`)→ 不阻断,trace 中"登记位置之外的显示名出现次数"加一。
- [ ] (v1.4)诊断脱敏:回调地址原文含合成 `;jsessionid=`、未知标签中植入与 hidden token 相同的合成值 → 诊断 JSON、诊断 HTML、日志与诊断目录均不残留;诊断失败时应答只有原错误与 `diagnostic_failed`,不含任何快照内容。
- [ ] 写后自检失败(注入)→ 证据删除,`QB_EVIDENCE_REDACTION_FAILED`,无 RESULT。
- [ ] 假代理任何命令的应答中出现 `cookie`、`set-cookie`、`authorization` 键 → Python 侧拒收并 `QB_BROWSER_UNAVAILABLE`。

### 9.2 浏览器代理(Node,离线必跑)

- [ ] 判定函数自检:第 3.4 节每条永久禁止各一例;各阶段放行项各一例;阶段外的放行项拒绝;只读路径带查询拒绝;登记地址改一个字符拒绝;`ILinkListener-content-buildHead-cancel` 形态 → 拒绝。
- [ ] (v1.6 改写,实施裁定 P5Q-C2C-03)含 `stop` 字样的三层验收(替代 v1.5 本条中"查询含 stop 字样的合法回调 → 放行"一句,该句与闭合的放行文法不相容):
  a. 永久禁止判定层单元测试:`stop` 只出现在监听器组件名以外的查询里(合法字段回调后接 `&value=stop`,以及 `?q=stop`)→ 不命中永久禁止;组件名含 stop(如 `form-stopper`)→ 命中永久禁止;
  b. 端到端放行判定:上面带 `&value=stop` 的地址最终仍被拒(不符合放行文法);不得为这条用例增加任何放行例外或参数例外;
  c. 旧正例"登记的刷新 GET 带 `value=stop` 放行"改为"在任何阶段都必须拒绝"的回归例。
- [ ] (v1.3)登录阶段:`/signin` 与 `/wicket/page` 的 `content-form` 提交各放行;`-form` 监听器、多余后缀、GET、其它路径拒绝;3xx 响应之后再提交拒绝;第 6 次提交拒绝;离开登录阶段后拒绝;`/dashboard` 空查询与纯数字查询放行、其它查询拒绝、非页面资源类型拒绝。
- [ ] (v1.3)字段回调:不带 random、带 `random=0.<数字>` 放行;random 出现两次、不在末尾、为空、为负数、为科学计数法、含字母、多一个其它参数、监听器名不同、同一回调第二次 POST 拒绝;`submit` 阶段 action 带 random 拒绝;定时刷新(带 random)在任何阶段拒绝。
- [ ] (v1.3)运行按钮:观察到的 button+onclick 写法通过;a[href] 写法、两个按钮、onclick 多一条语句、监听器为 `-promote` 或 `-run2`、外站绝对地址、onclick 缺失 → `QB_FORM_CHANGED`。
- [ ] (v1.3)构建号核对:子标签被记住时(裸 `/build/N` 显示 Variables)只做导航核对并通过;带 Summary 的 overview 通过;不带 Summary 的 overview → `QB_READ_ID_MISMATCH`。
- [ ] (v1.4/v1.5)页面主环境:页面先注入有缺陷的 `String.prototype.trim`、改写 `Element.prototype.outerHTML` 读取器(把 `Failed` 换成 `Successful`)、改写 `Node.prototype.textContent`、`DOMParser.prototype.parseFromString`、改写 `querySelectorAll` 为过滤实现、并伪造这些函数的 `toString` → 读取得到的 Status 仍为 `Failed`,表单核对、构建号核对、脱敏结果与正常夹具完全相同(工具不做原生判定,伪造 `toString` 不影响任何结果);隔离环境建立失败或导航响应正文不可得 → `QB_TRUSTED_CONTEXT_UNAVAILABLE`,不退回主环境取数。
- [ ] (v1.5)隔离环境前提直接断言:上例中,在隔离环境内断言 `outerHTML`、`textContent`、`parseFromString`、`trim` 均为原生(Chromium 行为变化时本例立即变红,而不是表现为结果可疑)。
- [ ] (v1.5)隔离环境生命周期:连续两次 `read`、以及 `open_form` 的两次导航之后的读取均成功(证明每次导航后重建);注入"复用旧环境"→ 必须失败;注入"建立失败"→ `QB_TRUSTED_CONTEXT_UNAVAILABLE`。
- [ ] (v1.5)解码:`Content-Type: text/html; charset=ISO-8859-1` 的响应含非 ASCII 字符 → 按该 charset 正确解码;声明 UTF-8 但含非法字节 → `QB_TRUSTED_CONTEXT_UNAVAILABLE`;无 charset → 按 UTF-8。
- [ ] 命令阶段机:阶段不对的命令全部 `AGENT_PHASE`;连续两次 `open_form`,每次至多放行一次提交;`fill` 失败后不经新 `open_form` 的提交拒绝;`submit` 指纹不符后再次 `submit` → `AGENT_PHASE`。
- [ ] 字段回调逐字段登记:同一字段的旧版本回调地址在该字段操作结束后被拒;另一字段的回调地址在当前字段操作期间被拒;形态不符的回调地址 → `QB_FORM_CHANGED`。
- [ ] (v1.4/v1.5)每字段恰好一次获准回调、零次被拒:下拉框、复选框、文本域、双列表、`SNAPSHOT_NUM=@freeze` 各一例,分"值不等"与"值已相等"两种;"值不等"路径零补派发;断言控件的 value/checked/selection/recorder 在"值已相等"路径前后逐字节不变,拦截器在该字段窗口内恰好 1 次获准、0 次拒绝;另加"设值后多派发一次 change"→ 拒绝 1 次 → 本字段 `QB_FORM_CHANGED`。
- [ ] (v1.5)文本域跨字段:"文本域改值 → 受控失焦 → 下一字段登记并获得焦点"连续执行,计数窗口覆盖到下一字段登记,旧字段无迟到回调、总计恰好 1 次获准;负例:`fill` 后人工补派发再进入下一字段 → 迟到的原生 change 被拒 → `QB_FORM_CHANGED`。
- [ ] (v1.5)启动自检:正常合成页面通过,Playwright 版本写入 trace;构造"设值不产生 change"或"产生两次 change"的合成控件 → 自检失败,浏览器关闭,stderr 为固定提示,Python 侧 `QB_BROWSER_UNAVAILABLE`;自检期间服务器零请求。
- [ ] (v1.5)页面吞掉 change:页面改写 `dispatchEvent` 使其返回而不派发,"值已相等"字段 → 30 秒超时 → `QB_FORM_CHANGED`,表单作废,提交零放行。
- [ ] (v1.4)双列表 `selection` 两项 → `QB_FORM_CHANGED`(不猜分隔符)。
- [ ] (v1.4)字段回调地址:DOM 原文为相对地址、请求为解析后的绝对地址 → 放行;原文被改成指向别的 origin 的绝对地址 → 拒绝。
- [ ] (v1.4)定时刷新:**不带** random 的刷新地址在任何阶段被拒;持续被拒的刷新流不延长 fill 的静默窗口(1 秒静默后推进,不走到 30 秒)。
- [ ] (v1.4)诊断:失败前已撤销运行、字段、提交登记;诊断期间拦截器零新增放行;页面含 `no-store` 图片时诊断前后服务器请求清单不增长(本机集成同测)。
- [ ] 307、308 在响应阶段终止(判定函数层);合法 302 继续并对下一跳重新判定。
- [ ] 协议适配层单元测试:构造含 Cookie、Authorization 请求头与含密码请求体的合成协议事件 → 交给判定逻辑的对象只含第 3.1 节列出的元数据;异常路径输出只有固定错误类别。
- [ ] 进程退出(正常、异常、SIGTERM)后 `/dev/shm` 临时目录不存在。
- [ ] (v1.6 并入,已实现;实施裁定 P5Q-C6A-04/05)关闭:用**生产入口**(不是测试入口),在 Python 侧保持 stdin 打开的情况下发送 `close` → 代理 5 秒内自行退出、退出码 0;`QbBrowser.close` 进入等待前 stdin 已关闭、不走终止分支;测试入口不含单独销毁 stdin 的代码;`qb-trigger` 与 `qb-result-fetch` 用假服务器各完整跑一次,关闭命令到 CLI 退出在 5 秒内。
- [ ] (v1.7)终止记录:代理收到 `close` 后故意不退出 → 驱动等满 35 秒后终止,CLI 的 trace 中恰有一条 `event=agent_terminated`,`waited_seconds>=35`、`exit_code` 为终止后的退出码;正常退出路径 trace 中无该记录;trace 写出失败(注入)不改变已完成的 stdout 与退出码。`read` 应答挂起超过 60 秒 → 同样终止并写该记录,`qb-result-fetch` 为 `QB_FETCH_FAILED`。
- [ ] (v1.6 并入,已实现;实施裁定 P5Q-C6A-03)停止类别:九个类别各一例(含浏览器断开优先于同次关闭伴随的页面关闭);正常 `close` 不记为异常;stderr 只有固定格式一行;Python 对表外类别按协议错误处理;CLI 失败时 trace 含命令名、代理错误码、类别、是否已退出与退出码,stdout 键集合不变。
- [ ] (v1.6 并入,已实现;实施裁定 P5Q-C6A-05)`login_facts`:四种本机场景——一直停在 `/signin` 且有密码框;登录提交 302 到未登记路径被拒;302 到 `/dashboard` 但没有 Sign Out;关闭窗口(`QB_LOGIN_ABORTED`)——逐字段断言;其中未登记路径一例 `final_path_shape` 为 `/`、`denied` 含 `<other>`、`login_channel_closed=true`;Python 侧多键、少键、类型错误、路径形态不在集合内、出现在非 login 应答中,各一例 → 协议错误;产物中不出现合成账号、密码、会话值与查询值;两个 CLI 的 trace 正确记录、stdout 不增字段。
- [ ] (v1.6 并入,已实现;实施裁定 P5Q-C3-04)普通下拉框选项文字(去首尾空白后)重复 → `QB_FORM_CHANGED`,`open_form` 与 `fill` 各一例,并覆盖一个非 SNAPSHOT_NUM 的下拉框;应答不带 `snapshot_state`;双列表 `choices`/`selection` 中同名不在此列。
- [ ] (v1.6 并入,已实现;实施裁定 P5Q-C3-02)SNAPSHOT_NUM 不可用的四种情形(冻结值不在选项中、`@freeze` 无选中项、多个选中项、下拉框为空)→ `snapshot_state` 形状正确;选中项超过 200 字符或含登记外字符 → `selected=null`;其它错误应答不带 `snapshot_state`;该错误不产生诊断、`released=false`。
- [ ] (v1.6)自动查找不改代理:代理命令表仍为六个;`read /overview/<登记 id>` 走既有只读路径(地址核对、原始字节、惰性文档、脱敏),不做构建号核对;`read /overview/<未登记 id>` → `AGENT_PHASE`。
- [ ] (v1.8)应答上限与代理自有预算:源码静态断言——`read` 路径上的页面导航带显式 `timeout`,其值为 30000 毫秒且小于驱动的 `read` 上限 60 秒;`submit` 路径上各等待的显式超时之和(Ok 点击、放行等待、跳转等待)小于驱动的 `submit` 上限 150 秒;对每条各有一个负例(去掉显式 `timeout` 或把值调到不小于驱动上限即变红)。行为用例:假代理收到 `submit` 后不应答 → 驱动 150 秒后终止,trace 中有 `agent_terminated`,CLI 为 `submit_uncertain` + `QB_SUBMIT_UNCERTAIN`、状态 QB_REQUESTED、提交后零条 `read`;对照:假代理在 149 秒时返回合法 `landed: unknown` → 正常进入查找。
- [ ] 源码静态断言:代理源码不出现 `page.request`、`context.request`、`newContext(` 的请求上下文用法、`.cookies(`、`storageState`、`ignoreHTTPSErrors: true`、协议调试日志开关;`login` 命令实现中不出现 `click(`、`fill(`、`press(`、`type(` 等交互调用;除协议适配层外无代码引用 `headers`、`postData`、`postDataEntries`;(v1.4/v1.5)生产代理源码不出现任何主环境执行接口:`page.evaluate(`、`frame.evaluate(`、`locator.evaluate(`(及任何 `.evaluate(` 调用于页面、帧、定位器、句柄)、`.evaluateAll(`、`evaluateHandle(`、`$eval(`、`$$eval(`、`waitForFunction(`、`addScriptTag(`、`exposeFunction(`、`exposeBinding(`;`addInitScript(` 出现次数恰为 1 且位于 `window.open` 守卫安装处;`setContent(` 只出现在启动自检处;对每个名字各有一条负例(故意加一行即变红);不出现从页面提取 `ajaxRefresh` 地址并登记的代码,也不存在刷新放行集合;不在活动文档上调用 `cloneNode`;`qb_browser.py` 不传任何测试专用参数。

### 9.3 本机浏览器集成(FatTank 开发机执行,CI 中 skip)

假 QuickBuild 的运行方式:本地 HTTPS 服务器,用测试专用证书;Chromium 用 `--host-resolver-rules` 把 `quickbuild.tizen.org` 解析到本机,并用只信任该测试证书的启动参数。这两个参数只能由集成测试入口传给代理,代理生产路径的 origin 判定、证书校验不变。页面以附录 C 所列真实归档页(live-12 的构建页、配置页与 `form-initial.html`)为**蓝本**构造,**保留其页面脚本依赖**。(v1.5)**响应体不得直接使用归档页**:归档页是脚本运行后的活动文档序列化结果,直接当响应体发出,会让"原始字节等于活动文档"按构造成立,永远发现不了第 3.1 节第 2 条的前提风险。假服务器并复现实测行为:有缺陷的 `trim`、回调追加 `&random=Math.random()`、构建子标签记忆、登录失败后的 `/wicket/page` 重提交、`/dashboard` 落点、定时刷新带 random。服务器记录实际收到的每一个请求。

- [ ] 正常路径:登录检测 → `open_form` → `fill` → `submit` → 落点 build。断言服务器只收到一次提交;收到的提交载荷中 Build Package List、BUILD NOTES、双列表 recorder 精确等于要求值;从未收到任何禁止类请求。
- [ ] 逐跳拦截:放行地址返回 302 到 `/rest/trigger`、到 `ILinkListener-content-buildHead-promote`、到外站 → 服务器未收到第二跳;307 重放 POST → 未收到。
- [ ] 读取:`/build/C/overview` 页面重定向到 `/build/D/overview`(D 页显示 Successful)→ `QB_FETCH_FAILED`。
- [ ] 提交后服务器先记录"已建构建"再返回带错误提示的表单 → 落点 unknown;重跑零新增提交。对称用例:返回错误表单且**未**建构建 → 同样 unknown、同样不自动重提。
- [ ] 提交后落点 `/build/P` 显示的是被记住的 Variables 子标签 → 落点 build(只按导航栏核对)。
- [ ] 提交后不跳转 → unknown;表单多一个字段 → `QB_FORM_CHANGED` 且诊断写出,诊断前后服务器收到的请求清单不变(页面含 `no-store` 图片);表单页带定时刷新 → `fill` 仍能完成(刷新被拒不延长等待)。
- [ ] (v1.4)页面脚本改写 `outerHTML` 读取器与 `trim` → 读取与填表结果不受影响(同第 9.2 节,在真实浏览器与真实页面脚本下再测一次)。
- [ ] (v1.5)前提失效时停而不错:构建页原始字节中**没有**导航栏 `Build (id:N)` 标签,由页面脚本在加载后插入 → `read` 返回 `QB_READ_ID_MISMATCH`(Python 侧 `QB_FETCH_FAILED`),不得读出结论;原始字节中 Status 为 `Failed`、页面脚本把活动文档改成 `Successful` → 读取结果为 `Failed`。
- [ ] 登录检测真假阳性:仍在 `/signin` 但页面含 Sign Out 字样、已跳离 `/signin` 但仍有密码框、无 Sign Out 链接 → 均判未登录;三条件齐备 → 已登录。登录失败一次后从 `/wicket/page` 重提交成功;连续 6 次失败,服务器只收到 5 次。
- [ ] 页面脚本尝试 `window.open`、iframe 指向外站 → 窗口被关闭、请求被拒,计数正确。
- [ ] Worker 与 WebSocket:页面创建 `SharedWorker`、`Worker` 并在其中请求 `/rest/trigger`;页面创建 ws/wss 连接 → 服务器均未收到;对应目标被关闭并计数。
- [ ] 307/308:放行地址分别以 307、308 跳到另一个**原本合法且已登记**的地址 → 服务器未收到第二跳;合法 302 第二跳正常到达。
- [ ] 页面版本递增:假服务器每次字段回调后递增页面版本并重渲染各字段回调地址 → `fill` 十二个字段全部完成,服务器收到的回调数等于字段数(含值已相等的字段);假服务器返回与 DOM 不一致的回调地址 → 被拒。
- [ ] 登录:人工点击登录按钮之前,服务器未收到任何 `/signin` POST;登录后跳转到未登记落点 → 被拦截,登录超时。
- [ ] 凭据隔离:浏览器真实请求携带合成 Cookie、Authorization 与合成登录密码 → Node→Python 协议、stdout、stderr、trace、证据与诊断文件中均不出现。
- [ ] (v1.6)自动查找本机集成:假配置页以 `S/C6b/raw-active-01/05.raw-redacted.html` 为蓝本(它是原始字节而不是活动文档,可以作为响应体蓝本;其中的 `<USER>` 改为合成显示名,以验证遮蔽),保留下拉菜单与"停止构建"链接;假服务器在提交后先让浏览器落在 `/wicket/page`,隔数秒才把新构建加入 `Recent Builds` → `qb-trigger` 自动绑定,`submitted_bound`。断言服务器实际收到的请求:(v1.7 更正计数)配置页 GET 总数等于基线读取 1 次、`open_form` 内部导航 1 次、再加查找轮次,并按阶段分别断言来源(协议层的 `read` 命令清单与服务器请求清单分开核对,不混用计数);构建变量页 GET 只针对大于 W 的构建;除 `open_form`、`fill`、`submit` 本就登记的请求外,从未收到停止、取消或其它 `/wicket/page` 监听器请求;归档配置页中合成显示名已遮蔽。另跑一次未绑定 request 的 `qb-result-fetch --request-id`,走读取时模式绑定并读出结果。
- [ ] 执行记录(命令、输出、服务器收到的请求清单)归档到 stage 证据目录。

"Worker 与 WebSocket""307/308""凭据隔离""逐跳拦截"四组属于拦截安全子集,任何改动生产放行规则的提交之后都要从头重跑并归档(C2b 期间已执行)。

### 9.4 真实 QuickBuild(均需 FatTank 在场)

1. **只读取证**:**已完成**(C2b,live-12 收齐;结论见附录 C)。
1.5. **表单联动取证**:**已完成**(live-12:BUILD_TYPE Full → Partial → Full,两次回调 HTTP 200,未提交)。
1.6. **(v1.3 新增,v1.4、v1.5 修订)完整填表演练与样本补齐,随 C5 执行**。(v1.6)**已完成**:c 填表演练于 C5b 通过(十二字段各 1 次获准、0 次被拒,提交放行 0 次;进度文件第 36 节);a 的原始字节比对于 C5b 固定六页(60 项)通过,C6b 又对成功父子与配置页五页(50 项)补做,均一致;a 的成功样本与 b 的 `BUILD_NOTES` 样本由第 2 步的构建补齐,2026-10-19 核验关闭(进度文件第 45 节;附录 C 第 15、19 项)。以下为原要求,保留备查。按以下顺序,**不调用 `submit`**:
   a. 读一个 FatTank 指定的**以 Ref. Snapshot 提交、已成功**的 Base RBS 父构建及其子构建的 overview 与 variables:坐实 `Successful` 文字、成功构建上 `EACH_GBS_BUILD_STATUS` 的形态,以及父构建选 Ref. Snapshot 时父构建 `SNAPSHOT_NUM` 与子构建 `SNAPSHOT_NUM_URL` 的关系;
      (v1.5)**原始字节与活动文档比对**(坐实第 3.1 节第 2 条的前提):对每个读到的页面,同时留存该次导航响应的原始字节与同一时刻在隔离环境中读到的活动文档序列化文本,逐项比对本文读取依赖的字段——导航栏 `Build (id:N)` 标签、`.build-summary` 区块与 Id/Status 表、Child Build 表的表头与数据行、变量页三列表格的全部行、配置来源五项(三标签、面包屑、复制路径、构建名)、step_status 的失败步骤路径与 Error Message。比对不依赖成功样本:至少覆盖附录 C 的 1193467、1193469(含 step_status)与配置页 1917,找到成功样本时一并覆盖。读取活动文档只为取证:本项由取证脚本执行(`docs/clang-fix-campaign/spikes/` 下,沿用 C2b 的方式,不是生产代码),可与 c 分属两次登录;生产代理不增加读取活动文档的入口。比对结果与两份文本(脱敏后)归档。**任一字段只在活动文档中存在、或原始字节中的值不同 → 停止,按 R1 修订第 3.1 节第 2 条与第 3.6 节**(候选退回方案:对该页改为在隔离环境读活动文档,并把"页面脚本可改活动文档内容"写成该页的已接受残余);
   b. 若能找到 BUILD NOTES 非空的 RBS 父构建,读其 variables,坐实 `BUILD_NOTES` 回显形态(空白、转义、截断);
   c. 用生产 `open_form` → `fill` 填写全部十二个字段,目标行用第 2 步拟提交的同一行,请求标记用演练专用 request_id(不落库);记录每个字段的回调地址、random 原值、回调响应、获准与被拒计数、页面版本变化、值已相等字段的回调情况、读回值与指纹;然后 `close`。代理记录必须保持 `not_released`。
   (v1.5)a、b、c 读到的每一个页面都按第 3.7 节"登记流程"检查登记位置之外的显示名出现次数。
   完成判定分开记录:c(填表演练)与 a 中的"原始字节与活动文档比对"**始终是第 2 步的前置**,未通过不得进入第 2 步;a 的成功样本部分与 b 若暂时找不到合适样本,登记为**具名挂账项**,不得计入 C5 已完成,改由第 2 步的构建补齐;挂账项核验关闭之前,P5Q 不得 CLOSED。任一项与本文不符 → 停止并按 R1 修订。
2. **一次确认的真实提交(收口前最后一步)**:目标由 FatTank 指定(建议一个已在快照中的小包、用它当前已合入的 commit,构建内容与快照一致,不引入新代码)。工具先在 Codex 对话中打印全部十二个字段的拟填值与目标行,FatTank 在对话里确认后才执行 `qb-trigger`;随后执行 `qb-result-fetch` 至少一次。记录:提交后的实际落点、构建号获取方式;父构建变量 `BUILD_NOTES`、`BUILD_REFERENCE`、`SNAPSHOT_NUM` 在 Ref. Snapshot 模式下的回显原文;子构建 `SNAPSHOT_NUM_URL` 是否以冻结值结尾;父子页面回显是否与本文一致。若落点不是 `/build/<id>`,用第 5.2 节人工绑定完成闭环并记录。依据本步与第 1.6 步 a 的结果,按 R1 决定父构建 `SNAPSHOT_NUM` 或子构建快照地址是否升为判据。若 `BUILD_NOTES` 回显与请求标记不一致导致绑定失败,按第 5.2 节人工核对并停止,先按 R1 修订再继续。此步完成前 P5Q 不得 CLOSED。
   (v1.6)**已完成**(C6,进度文件第 37–46 节):
   - 准备方式(实施裁定 P5Q-C6-01):P12 之前不允许真实推送,所以 C6 在仓库外的专用目录使用专用状态库与专用配置,不触碰任何真实 campaign 的状态库;状态库照搬 C5a 完整链路用例构造(三份 verification record、unit、DERIVE、PUSH,均为合成前提,不是真实 gbs 验证或真实推送的证明);专用配置的 `gerrit_ssh_base` 指向本机 bare 镜像,镜像中的 sandbox ref 指向目标 commit,目标对象只从 Tizen Gerrit 只读拉取,严禁 push。除远端地址外,代理、浏览器、两个 CLI 与 QuickBuild 全部走生产路径,不传任何测试专用参数。因此 C6 **不覆盖真实 Gerrit 远端核对**,该步由 C3 离线验证,首次真实 sandbox 推送仍在 P12。
   - 结果:目标 `platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`;落点 `/wicket/page`(unknown);FatTank 按请求标记查到 1201886 后人工绑定;首次读取子构建 1201889 即 PASS;父子回显与本文一致;C6b 终态重读幂等;关闭修复后真机关闭尾段 0.213 秒。依据本步与第 1.6 步 a 的结果所作的 R1 决定见第 0.5 节第一项。附录 C 第 15–19 项。
   - 期间三次执行因登录超时、本机磁盘 I/O 阻塞、登录后代理不可用而中止(进度文件第 38–42 节),促成第 3.2 节停止类别与第 3.3 节 `login_facts`;两次登录超时的原因仍未知,再出现时可凭 `login_facts` 区分。
3. **(v1.6 新增)一次验证性真实提交,验证自动查找(P5Q 收口前最后一步)**:
   - 准备:同第 2 步的方式与边界(实施裁定 P5Q-C6-01),但**新建**一个专用状态库与专用配置,不复用 C6 的库——C6 的库已冻结 `tizen-base-toolchain_20261013.024319`,参考快照若已滚动,新提交会被拒。目标由 FatTank 指定(建议仍用 C6 的 libtirpc 同一 commit:构建内容与快照一致,约 20 分钟出结果,且已知其清单 revision 一致)。
   - 执行:工具在 Codex 对话中打印十二个字段的拟填值与目标行,FatTank 逐字回复"确认提交"后,只运行一次生产 `qb-trigger`,不带 `--retrigger`;随后运行 `qb-result-fetch --request-id` 直到终态(每次运行前在对话中预告;读取不需要"确认提交")。
   - 验收:
     a. 落点为 unknown 时,`action=submitted_bound`,且 trace 显示由自动查找绑定(每轮的时间、候选与判定类别可读);人在 QuickBuild 页面核对绑定的构建号与请求标记一致;记录从 `submit` 应答到绑定的秒数与轮次;
     b. 终态结果文件与 C6 同样逐项核对,快照判据按第 0.5 节;
     c. 关闭尾段为秒级;
     d. 每个读到的页面按第 3.7 节"登记流程"检查登记位置外的显示名计数(含配置页)。
   - 例外处理:落点直接是 `/build/<id>`(QuickBuild 行为变了)→ 记录事实,自动查找未得到真机验证,由 FatTank 决定是否另行验证;自动查找未找到、查找超时或多于一个 → 按第 4.3 节第 10 步人工处理并停止,先按 R1 修订再继续;配置页基线读取不通过(第 4.3 节第 2.5 步)→ 停止,不提交。
   - (v1.7 改写)**读取时模式的零提交真机验证**:读取时模式是唯一会成批读取他人构建页面的模式,离线夹具只能验证我们自己造的页面,所以在本步做一次不提交、不产生构建的真机执行:
     - 准备:在本步的专用状态库中,按实施裁定 P5Q-C6-01 的方法另构造一个 unit,并用第 4.3 节第 8 步的同一组按连接写入原语写入一条提交意图(request + SUBMITTED + 状态 QB_REQUESTED),请求号随机生成;**不运行 `qb-trigger`、不提交**。证据中注明该 unit 与 request 是构造的,该库不参与任何真实 campaign。(v1.8)构造的 unit 只需满足第 5.5 节"前置"(最新 request、无 BUILD_BOUND、状态 QB_REQUESTED);本项预期"未找到",不会进入第 5.2 节的父构建核对,因此不要求补齐目标行所需的其它状态;若意外出现"匹配",立即停止,作为异常事实记录;
     - 执行:在验证性提交的结果读取完成之后,对该 request 运行一次 `qb-result-fetch --request-id`(运行前在对话中预告,需要 FatTank 在窗口中登录);
     - 预期:"未找到",exit 4 `REJECTED_QB_BINDING_MISMATCH`,数据库零写入;
     - 验收:e1. trace 中的候选恰为 `Recent Builds` 中未被本库绑定的全部行(验证性提交的构建已绑定,应被排除),各自的判定类别可读,无"匹配";e2. `qb_evidence/<R>/` 下只有配置页一个文件,他人构建的变量页零落盘,`qb_diagnostics/` 零新增目录;e3.(v1.8 拆成两项)e3a. trace 中每个读到的页面"登记位置外的**登录显示名**计数"均为 0(该计数只统计操作者自己的显示名,第 3.7 节),不为 0 时按第 3.7 节"登记流程"人工确认;e3b. 候选页一律是 `/build/<id>/variables`,其中没有已登记的身份承载列(`Triggered By`、`Requested By` 只在构建概览页与配置页上,C6a 归档的两份变量页中均为 0 处),所以 e3a 的计数**不能**发现他人页面上的新身份位置。本项改为:由实现对每个读到的候选页断言其为"Name / Display Name / Value"三列变量表、没有其它表格;并由人浏览一次本次读到的候选页的**变量名集合**,确认没有新的账号承载位置;发现则停止并按 R1 补登记后重跑本项。第三方姓名若出现在变量值的自由文本中(例如别人写的 BUILD NOTES),本版既不遮蔽也不统计,因这些页面不归档而不构成落盘泄漏,列为已接受残余并写入收口文档(第 10 节 C8)。
   - (v1.7)**快照漂移分支**:本步用内容与快照一致的目标,约 20 分钟出结果,不等待参考快照滚动,所以漂移分支仍只有第 9.1 节的离线覆盖。其真机样本挂账到 P12:P12 第一次遇到漂移停止-报告时,按第 5.3 节第 4 项 a 人工裁定,并把该次的冻结值、实际快照名与处置作为漂移分支的首个真机样本记录;收口文档(第 10 节 C8)列明这一挂账。
   此步完成前 P5Q 不得 CLOSED。

### 9.5 通用门禁

- [ ] 全量测试、mypy、ruff 通过;Node 自检通过。
- [ ] `tests/unit/test_campaign_state.py::test_ensure_schema_creates_exact_campaign_tables_and_required_guards` 的期望表集合与 DDL 一致,并有该表 CHECK 负例(`profile_sha256` 非 64 位小写十六进制)(C1 已实现,作为复跑清单保留)。
- [ ] design.md 检查器通过。
- [ ] 每个提交同步更新 stage 进度文件。
- [ ] (v1.6)C7 不改代理放行规则,但改动了代理的登录固定提示(第 3.3 节),并在生产路径中新增对配置页的读取:四个拦截安全组从头重跑并归档,第 9.2 节静态断言全部通过。
- [ ] (v1.7)附录 I 第 14 条与附录 J 第 7 条的两处实现偏差(登录固定提示、关闭终止不写 trace)均已补齐并有用例;C8 时第 9.4 节第 3 步 a–d 与 e1、e2、e3a、e3b 均已执行并归档。

---

## 10. 提交计划

| 提交 | 内容 | 状态/依赖 |
|---|---|---|
| C0 | design.md 同步(附录 A);stage20 进度文件建立 | 已完成 |
| C1 | `qb_redact.py`;配置解析与校验;`campaign_qb_profiles` 表、四个按连接写入原语与公共 API 重构、`qb_profile` 查询 | 已完成;v1.3 需补:配置校验规则 7(第 2.1 节) |
| C2 | `qb_browser_agent.mjs` + `qb_browser.py` + 假代理;第 9.2 节;第 9.3 节拦截安全子集;第 9.4 节第 1、1.5 步 | 已完成(C2a、C2b,截至 `b6bec94`) |
| C2c | v1.5 冻结后对代理与脱敏模块的补齐:①去掉第 3.1 节清单内的一切主环境执行(`addInitScript` 只留 `window.open` 守卫一处),改为隔离环境(每次导航后重建)+ 读取用导航响应原始字节(按 charset 严格解码)(第 3.1、3.6 节);②脱敏与诊断改为惰性文档上的被动处理;身份按登记位置遮蔽(含 `Requested By`),删除 `qb_redact.py` 的全局身份替换与全局身份残留检查,写后自检按第 3.7 节 v1.5 判据;③删除刷新登记与放行集合,最近活动时间只在放行时更新(第 3.4 节);④每字段恰好一次获准回调、零次被拒,含 `@freeze`;值不等时不补派发,文本域受控失焦,计数窗口延续到下一字段;启动自检(第 3.5 节);⑤结构失败诊断应答;⑥design.md 按附录 A"v1.4 增补"(含 v1.5 条目)同步;对应第 9.2 节用例与第 9.1 节脱敏用例;改动生产放行规则则重跑拦截安全子集 | 已完成(进度文件第 27–28 节) |
| C3 | `qb-trigger` CLI 及第 9.1 节触发/填表/崩溃/多 unit/隔离传输/诊断用例 | 已完成(第 29–31 节;裁定 P5Q-C3-02、P5Q-C3-04) |
| C4 | `qb-result-fetch` CLI、人工绑定及第 9.1 节读取/落库用例(按第 5.3、5.4 节 v1.5 判据,含 `--accept-snapshot-drift`、`child_params_echo`、`snapshot_drift_accepted` 与辅助页 step_status 的优先级) | 已完成(第 32–33 节;裁定 P5Q-C4-02) |
| C5 | 第 9.3 节其余本机浏览器集成(含 v1.5 前提失效夹具)及证据归档;**第 9.4 节第 1.6 步** | 已完成(C5a、C5b,第 34–36 节) |
| C6 | 第 9.4 节第 2 步真实提交 | 已完成(C6a、C6b 及其间的诊断与关闭修复轮,第 37–46 节;裁定 P5Q-C6-01、P5Q-C6A-03/04/05、P5Q-C6B-01);两个具名挂账项已核验关闭。原定的"收口文档"移到 C8 |
| C7 | (v1.6)本文冻结后的实现:第 5.5 节自动查找(两种模式)、第 4.3 节第 2.5 步与第 10 步、第 5.1 节未绑定 request 的读取、第 4.2 节第 5 步与第 4.3 节第 10 步的提示文字;第 5.3 节第 4 项 b 的指引措辞(第 0.5 节 R1 定案);第 3.3 节登录固定提示补齐;design.md 按附录 A"v1.6 增补"同步;第 9.1 节"自动查找与绑定"用例、第 9.2 节新增断言、第 9.3 节自动查找本机集成;第 9.5 节门禁(含四个拦截安全组回归)。(v1.7 增)驱动侧失败的内部标记与 `read` 应答等待上限(第 3.2 节);关闭超时的 `agent_terminated` 记录(第 3.1 节);查找总时限与"查找超时"类别(第 5.5 节第 4、5 步);证据序号规则(第 5.3 节末尾);附录 J 所列全部采纳项。(v1.8 增)驱动侧失败外延与标记要求、`submit` 应答上限 150 秒、代理 `read` 导航显式 30 秒超时(第 3.2 节);批次中途代理不可用的处理(第 4.3 节第 1 步);第 2.5 步失败提示分两类(第 4.3 节第 2.5 步);截止点覆盖绑定读取、比较为严格大于、trace 记每次读取耗时(第 5.5 节第 4、5 步);附录 K 所列全部采纳项。注意:代理改动(显式导航超时)涉及代理文件,四个拦截安全组照第 9.5 节从头重跑 | 本文冻结 |
| C8 | (v1.6)第 9.4 节第 3 步验证性真实提交;(v1.7)同步骤中读取时模式的零提交真机验证;P5Q 收口文档:汇总全部挂账与已接受残余、C6 不覆盖真实 Gerrit 远端核对的说明、P12 需要观察的事项——至少包括:首次真实 sandbox 推送后是否自发构建、批量恢复的时效(第 5.5 节"已接受的限制")、快照漂移分支的首个真机样本(第 9.4 节第 3 步)、Unified 配置未取证;(v1.8)已接受残余还须列出:他人构建变量值自由文本中的第三方姓名既不遮蔽也不统计(第 9.4 节第 3 步 e3b)、`open_form`/`fill` 无驱动侧应答上限(第 3.2 节) | C7 + FatTank"确认提交" |

C5、C6 或 C8 的真机结果若与本文不一致,停止,先按 R1 修订本文再继续。

---

## 附录 A:design.md 同步(C0 照录 v1.5.22,C2c 同步 v1.5.23;v1.6 增补待 C7 同步为 v1.5.24)

v1.2 附录 A 的同步已在 C0 完成(design.md 第 4.5 节 13 条、各处指引与 DDL)。v1.3 的修改都在 P5Q 设计文件内部;v1.4 因 FAIL 语义与快照记录方式影响 P5R,需要同步 design.md,内容见本附录末尾"v1.4 增补"。

以下为 v1.2 附录 A 原文的第 4.5 节引文,保留备查:

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
> 10. review-submit 的人工装配降级判据收紧为:最新 request 完全不存在 RESULT 行,**且**该 unit 最新状态不属于 {QB_REQUESTED, QB_TRIGGERED, SANDBOX_QB_PENDING};处于这三个状态表示存在未出结果的复验请求,一律 exit 4 `REJECTED_QB_REQUEST_PENDING`,不得降级、不得打印 push 命令。复验请求确已失效时,由人用 `--retrigger` 产生新 request,或按 R2 带外处置后再降级。降级仅作为 P5R 的工具故障通道,不作为复验未完成通道。
> 11. qb_result 文件 schema 以 P5Q 设计文件第 5.4 节为准。review-submit 接受该 schema:`per_arch_status` 为 null 与数据库 NULL 表示未提供独立架构状态,不启动逐架构校验,非空映射才按架构校验;`accepted` 可空,冻结参数要求 Accept 时只有数据库 accepted=1 才通过,NULL 与 0 均不通过。"已有 RESULT 而校验失败不得降级"不变。
> 12. 同一 request 已有终态 RESULT 后,状态不变而 accepted 等判定字段变化时,追加新的 RESULT,最新 RESULT 为权威;状态改变视为状态不一致。
> 13. 新增 `campaign_state` 按连接写入的内部原语;P5Q 的每个写入点在一个事务内完成。

第 11 条指向第 5.4 节,v1.3/v1.4 在 schema 中新增的键随之生效;P5R 尚未实现,不受影响。

**v1.4 增补(随 C2c 同步进 design.md,升 v1.5.23)**:

- §4.5 第 6 条末尾追加:"(v1.5.23)子构建快照地址与冻结值的关系尚未取证,只记录;不一致时有指引地停止、不写结论。其中参考快照在构建期间滚动(主机与路径根相符、快照名不同)的情形,可由人对单个 request 以 `qb-result-fetch --accept-snapshot-drift` 接受,结果文件记实际快照名 `snapshot_used` 与 `snapshot_drift_accepted=true`;P5R 报告须标出这类 unit 及其实际快照名。FAIL 只表示含目标行的全量构建失败,见第 14 条。"(本句含 P5Q 设计 v1.5 的补充)
- §4.5 新增第 14 条,原文如下:

> 14. qb_result 的 `status=FAIL` 表示"包含本 unit 目标行的那一次全量构建(`FAIL_FAST=yes`,单个 Build_GBS 步)失败",**不等于本 unit 的修复未通过**:QuickBuild 页面上没有逐包状态。P5R 不得仅凭 FAIL 断言本 unit 的修复失败,须结合结果文件中的 `child_failed_step`、`child_error_message` 由人判读;PASS 的语义不变。

- §4.3 `QB_FETCH_FAILED` 说明后补"含可信读取环境不可用(P5Q 设计文件 v1.4)"。
- (v1.5)§4.5 第 11 条无需改文字(它指向第 5.4 节);P5R 实现时注意 schema 新增 `child_params_echo`、`snapshot_drift_accepted`,`snapshot_used` 记实际快照名。
- §0 元信息版本行与文末版本声明同步改为 v1.5.23,加变更记录一行。

(以上 v1.4 增补已在 C2c 同步,design.md 现为 v1.5.23。)

**v1.6 增补(随 C7 同步进 design.md,升 v1.5.24)**:

- §4.5 第 5 条末尾追加:"(v1.5.24)提交后落点不是构建页时,工具只读该配置页的 Recent Builds 表,逐个读取候选构建的变量页,按请求标记精确匹配;恰好一个、且通过与人工绑定相同的全部核对,才自动绑定;找不到或多于一个时保持未绑定,由人处理。规则见 P5Q 设计文件 v1.6 第 5.5 节。"
- §4.5 第 6 条中"子构建快照地址与冻结值的关系尚未取证,只记录;不一致时有指引地停止、不写结论。"改为:"(v1.5.24)子构建快照地址已取证:以 Ref. Snapshot 提交时,其最后一段等于冻结值;它作为判据,一致照常落库,不一致时有指引地停止、不写结论。"该条其余文字不变。
- §4.3 不改:v1.6 没有新增错误码,扩展的适用场景已在各码现有说明的范围内(本文第 7 节)。
- §0 元信息版本行与文末版本声明同步改为 v1.5.24,加变更记录一行。

## 附录 B:证据索引

`E` = `docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence`;`L` = `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b`;(v1.6)`S` = `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence`(C5b、C6a、C6b 证据在其下的同名子目录)。

| 事实 | 证据路径 | 流水线 |
|---|---|---|
| 子构建 Status=Successful、无 SR_STATUS 栏 | `E/web-cookie-02/01.response.txt:832` | SBS |
| 子构建 TRIGGER_ID、BUILD_PKG_LIST、FAIL_FAST、EACH_GBS_BUILD_STATUS(空) | `E/web-cookie-02/03.response.txt:804` | SBS |
| 表单字段、标签、双列表三元素、AJAX 回调、按钮(早期取证) | `E/rbs-form-01/form.json`、`form.redacted.html:720-1110` | RBS |
| Ok 为整表提交;Cancel 为 `ILinkListener-form-cancel` | `E/rbs-form-01/form.redacted.html:1109-1110` | RBS |
| PUSH 事件 `url=None`,远端由配置构造 | `tizen-ci-triage/scripts/ci_triage/sandbox_submit.py:709,808-819` | — |
| Ready to Accept 链接特征 | 外部参考(团队 quickbuild-sbs `create_sbs.py`),仅用于禁止名单 | — |
| v1.3 依据的 RBS 真机取证 | 见附录 C 各项所列 `L/live-*` 路径;完整记录 `L/appendix-c.md` 与 stage20 进度文件第 17–26 节 | RBS |
| (v1.6)v1.6 依据的 RBS 真机取证 | 见附录 C 第 15–19 项所列 `S/C5b`、`S/C6a`、`S/C6b` 路径;完整记录在进度文件第 35–46 节 | RBS |

## 附录 C:只读取证结论(C2b,live-01 至 live-12)

`L` 同附录 B。行号指归档文件中的行。下列为本文所依据的事实;未列出的项见第 9.4 节第 1.6、2 步。

| 编号 | 事项 | 结论 | 证据 |
|---|---|---|---|
| 1 | 登录 | 登录 POST `/signin?0-1.IFormSubmitListener-content-form` 成功返回 302 → `GET /dashboard` 200,三条件成立。登录失败返回 200,重提交发往 `/wicket/page?1-1.IFormSubmitListener-content-form` | `L/live-12/run.json:2442`;`L/live-02c/run.json`;`L/live-02b/run.json` |
| 2 | 被拒静态资源 | `/ckeditor/ckeditor.js?v=1701391813000`、`/images/fonts/bootstrap-icons.woff(2)?<32 位十六进制>` 被拒,登录、读取、填表均不受影响;定时刷新 `...IBehaviorListener.0-=&action=ajaxRefresh&random=<小数>` 被拒,无影响 | `L/live-12/README.md`(拒绝计数);`L/live-02b/run.json` |
| 3 | RBS/TRIGGER 配置 | overview_id **1917**;来源为父构建 overview 页的 Configuration Overview 标签(与 Pipelines、Children 标签同一 id,面包屑与"复制路径"均为 `root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER`);配置页 title 以 `QuickBuild - <路径>` 开头;运行按钮为 `<button title="Run the configuration" onclick="var win = this.ownerDocument.defaultView \|\| this.ownerDocument.parentWindow; if (win == window) { window.location.href='../wicket/page?9-1.ILinkListener-run'; } ;return false">` | `L/live-12/run.json:2737,2756`;`L/live-12/06.response.html`;`L/live-06/07.response.html:722` |
| 4 | 表单 | 十三标签与 v1.2 一致;PROJECT_NAME 显示区原始文本前后带空白;BUILD_TYPE Full/Partial;REPO_TYPE ALL;BUILD_REFERENCE Live/Ref. Snapshot/Snapshot Number(默认 Ref. Snapshot);SNAPSHOT_NUM 仅 `tizen-base-toolchain_20260924.094908`;PROJECT_BRANCH tizen_base;CHILD_CONFIGURATIONS 默认已选固定架构值(value 为文字十六进制);TARGET_IMAGE 两表均空;action `/wicket/page?10-1.IFormSubmitListener-form`;回调 `/wicket/page?10-1.IBehaviorListener.0-form-editor-content-basicProperties-1-property-editor-editor-wrapper-select`,运行时追加 `&random=0.3453609721766676` 等;两次改值回调均 200,版本号、action、回调地址不变,无整页导航 | `L/live-12/run.json:2878,2898,2924,2944,2953,3076,3206`;`L/live-10/form-unverified.response.html:732-736` |
| 5 | 父构建变量(1193467) | `BUILD_PKG_LIST_MODIFY`(显示名 Build Package List,4 行);`BUILD_PKG_LIST`(245 行全量);`BUILD_NOTES`(显示名 BUILD NOTES,样本为空);`BUILD_TYPE=Full`;`BUILD_REFERENCE=Live`;`SNAPSHOT_NUM=do not need select`;`PROJECT_BRANCH=tizen_base`;`FAIL_FAST=yes`(显示名 Immediate Stop With Error);`CHILD_CONFIGURATIONS=standard-armv7l:aarch64:x86_64`;`QB_TRIGGER_ID=1193467` | `L/live-12/02.response.html:808` |
| 6 | 子构建变量(1193469) | `TRIGGER_ID=1193467`;`QB_TRIGGER_ID=1193469`;`BUILD_PKG_LIST` 245 行,含父构建 4 个目标行;`FAIL_FAST=yes`;`EACH_GBS_BUILD_STATUS` 存在且为空;`REPO_ARCH`、`CHILD_CONFIGURATIONS` 为固定架构值;`ARCHITECTURE=armv7l:aarch64:x86_64`;`BUILD_REFERENCE=Ref. Snapshot`;`SNAPSHOT_NUM_URL=http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260924.094908`(登记的快照根为 `http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/`)。注意父构建以 Live 提交,子构建这两个值与父构建表单选择的关系尚未取证(v1.6:以 Ref. Snapshot 提交时的关系见第 16 项) | `L/live-12/04.response.html:800` |
| 7 | Child Build 表与状态 | 父构建 overview 页 `◆ Child Build` 标题后表格,表头 Repository-Architecture / QB Build URL / Build Result / Build Profiling;一行:`standard-armv7l:aarch64:x86_64`、`https://quickbuild.tizen.org/build/1193469`、`FAILED`;子构建 Summary Status `Failed` | `L/live-12/01.response.html:879-892`;`L/live-12/03.response.html:828` |
| 8 | 子标签记忆与子构建配置 | 先读变量页再读裸 `/build/1193469`,页面显示 Variables 子标签、无 Summary;子构建配置为 `root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/build`(overview 1915) | `L/live-06/03.id-unverified.response.html:783-784`;`L/live-11/run.json`(configuration_sources) |
| 9 | 页面主环境 | 八次采样:`String.prototype.trim` 非原生;`replace`/`split`/`includes`、`Array.prototype.map`/`filter`/`includes`、`JSON.stringify`、`RegExp.prototype.exec` 均原生;PROJECT_NAME 经页面 `trim` 后只去掉前导空白 | `L/live-12/run.json:2453`;`L/live-10/run.json`(form_diagnostics) |
| 10 | 身份值子串替换缺陷 | 显示名为常见词片段时,`ILinkListener` 等被改写为 `I<USER>kListener`(归档中为 HTML 转义形态 `I&lt;USER&gt;kListener`) | `L/live-03/01.response.html`(多处) |
| 11 | Unified 样本 1186372 | `GBSBUILD_TAG` 属 Tizen-Unified-Toolchain/RBS/TRIGGER;`FAIL_FAST=no`;`CHILD_CONFIGURATIONS=standard-armv7l,standard-aarch64,standard-x86_64`;不作 Base 样本 | `L/live-06/06.response.html` |
| 12 | 安全(真机会话) | `form_action_releases=0`、`released=false`、`runtime_failure=null`,浏览器与临时目录已清理;未产生构建 | `L/live-12/run.json:4064`(放行)、`:3870`(清理) |
| 12b | 安全(合成环境) | Worker 类目标与新窗口阻断等拦截安全组通过——来自合成本地服务器,不是真机会话计数 | `L/live-12/node-gates.log`;`L/live-12/README.md` |
| 13 | 子构建失败步骤 | Step Status 为 `master` → `BUILD` → `Build` → `Build_GBS` 均失败(`Build_GBS` 23 小时余);overview Error Message 为 `Composite step 'BUILD' failed due to unsatisfied success condition`;无逐包状态 | `L/live-12/05.response.html`;`L/live-12/03.response.html` |
| 14 | 配置页身份列(v1.5 补) | 配置页 `/overview/1917` 有构建请求表,表头 `Requested By`、`Schedule Date`、`Priority`、`Process Status`、`Master Node`、`Build Version`;`Requested By` 列为账号,归档中已是 `<USER>`,但那是全局替换的结果,不是位置遮蔽 | `L/live-12/06.response.html:845` |

(v1.6)以下第 15–19 项来自 C5b、C6 的真机执行;`S` 见附录 B,`Q` = `S/C6a/live-05/fetch/state/qb_evidence/9fe02dc3927c4b7fa55a3dffce699d03`。

| 编号 | 事项 | 结论 | 证据 |
|---|---|---|---|
| 15 | 成功样本与 `BUILD_NOTES` 回显(1201886/1201889,Ref. Snapshot 提交,C6a) | 子构建 Summary Status `Successful`(父构建 Summary 同为 `Successful`,只记录);父构建 Child Build 表一行,Build Result `SUCCESSFUL`,链接 1201889;子构建 `EACH_GBS_BUILD_STATUS` 存在且为空;父构建 `BUILD_NOTES` 为 `clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03`,与请求标记逐字相等,单元格无首尾空白、HTML 转义、换行或截断;`BUILD_PKG_LIST_MODIFY` 恰一行等于目标行。构建内容与快照一致:父 18 分 45 秒(05:21:52 开始)、子 16 分 12 秒(05:23:31 开始)。C6b 终态重读:RESULT 仍为原事件,数据库逐字节不变,未保留新结果文件,新增 4 页证据;真机关闭尾段 0.213 秒(修复前约 35 秒) | `Q/03.1201889-overview.html:830`、`Q/01.1201886-overview.html:891`、`Q/04.1201889-variables.html:802`、`Q/02.1201886-variables.html:810`;`S/C6b/raw-active-01/01–04`(同行号);`S/C6b/reread-01/stdout.json`、`execution.json`、`post-audit.json` |
| 16 | 快照关系与滚动 | 父构建 `BUILD_REFERENCE=Ref. Snapshot`、`SNAPSHOT_NUM=tizen-base-toolchain_20261013.024319`(等于本次首次冻结值);子构建 `BUILD_REFERENCE=Ref. Snapshot`、`SNAPSHOT_NUM_URL=http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319`;三者相同,`snapshot_kind=same`。该快照清单中 libtirpc 的 revision 等于目标 commit。参考快照在 2026-10-15 至 10-19 之间由 `20260924.094908` 滚动到 `20261013.024319` | `Q/02.1201886-variables.html:810`、`Q/04.1201889-variables.html:802`;`S/C6a/live-05/manifest-20261013/result.json`;进度文件第 43.3、43.8 节 |
| 17 | 提交落点与构建出现时间 | 生产 `qb-trigger` 点 Ok 后观察到的最终路径为 `/wicket/page`,`messages` 为空,应答 `landed: unknown`;构建 1201886 已创建,版本名 `TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261019.052151`,Begin Date `2026-10-19 05:21:52`(页面时间)。本机记录的提交意图写入时间为 05:21:27.8(UTC),提交紧随其后。C6b 读配置页时,本机时间不晚于 07:17:31.9,页面上运行中的 1202070 显示开始于 07:17:46、已运行 7 秒,据此推算 QuickBuild 服务器时钟比本机快约 20–30 秒;换算后 1201886 在点 Ok 后数秒内即已开始。**这是推算,不是直接测量**,第 9.4 节第 3 步记录实际查找耗时 | `S/C6a/live-05/trigger/trace-new.jsonl`、`stdout.json`、`state-after.sql`;`S/C6b/configuration-1917.md`;`S/C6b/raw-active-execution-01/execution.json` |
| 18 | 配置页最近构建表 | `/overview/1917` 的服务器原始字节中有两张构建表:① `Build Requests`(表头:空的选择列、`Requested By`、`Schedule Date`、`Priority`、`Process Status`、`Master Node`、`Build Version`;运行中的请求 Process Status 为 `RUNNING_BUILD`,Build Version 带 `/build/<id>` 链接);② `Recent Builds`(表头 `Id`、`Version`、`Master Node`、`Begin Date`、`Duration`、`Triggered By`;10 行,含运行中的构建;`Version` 单元格中构建链接的 href 为 `/build/<Id>`,与 Id 一致,另有下拉菜单链接 `javascript:void(0);`,运行中的行另有"停止构建"链接)。1201886 在提交约 2 小时后位于 `Recent Builds` 第 2 行。`Requested By`、`Triggered By` 归档中均为 `<USER>`。原始字节与活动文档的单元格文字、构建链接与状态 class 一致;活动文档只在下拉菜单锚点上多出页面脚本添加的 class,两表 HTML 因此不逐字相同 | `S/C6b/raw-active-01/05.raw-redacted.html:830-1232`;`S/C6b/configuration-1917.md`、`configuration-tables.diff`;另一时刻样本 `S/C5b/raw-active-01/06.raw-redacted.html` |
| 19 | 原始字节与活动文档比对 | 第 3.1 节第 2 条依赖的十项字段(导航、Summary、Child Build、变量表、配置三标签、面包屑、复制路径、构建名、失败步骤、Error Message):C5b 固定六页(1193467 两页、1193469 三页含 step_status、配置页 1917)60 项一致;C6b 成功父子四页与配置页共五页 50 项一致;两侧登记位置外身份计数均为 0 | `S/C5b/raw-active-01/run.json`;`S/C6b/raw-active-01/run.json`、`NN.comparison.json` |
| 20 | (v1.7)填表演练(C5b,不提交) | 生产 `open_form` → `fill` 十二个字段:每个字段恰好 1 次获准回调、0 次被拒,回调 HTTP 200;全程只有一个页面版本(`/wicket/page?4`)与一个表单 action(`/wicket/page?4-1.IFormSubmitListener-form`),均不变;10 个字段走"值已相等"路径,只有 Build Package List 与 BUILD NOTES 两个文本域改值;读回全部相符;提交放行 0 次、表单状态 `not_released`;启动自检记录 Playwright 1.58.2、三类控件各 1 次 change;登记位置外身份计数 0 | `S/C5b/fill-rehearsal-02/acceptance.json`、`run.json`;进度文件第 36 节 |

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

## 附录 F:v1.2 → v1.3 修改记录(R1,依据 C2b 真机取证)

"裁定"列为 stage20 进度文件中的实施裁定编号;已在代码中落实的标"已实现(提交)",只在本文新增的标"待实现"。(v1.4 补:v1.3 还改动了第 2.2、4.2、6.2、7、9.5 节的文字而本表未列;其中第 4.2、6.2、9.5 节被误删的原文已在 v1.4 恢复,见附录 G 第 13 条。)

| 编号 | 级别 | 与 v1.2 的差异 / 新事实 | 处理 | 位置 | 裁定 / 实现状态 |
|---|---|---|---|---|---|
| 1 | 重要 | 登录后落点是 `/dashboard`,不是 `/`、`/overview/0` | 登录阶段登记 `/dashboard`(页面类型,查询空或纯数字) | 3.3、3.4、附录 C-1 | C2B-02/03;已实现 `3013899` |
| 2 | 重要 | 登录失败后重提交发往 `/wicket/page`,v1.2 只允许 `/signin` | 两条登录提交通道,监听器名收紧为 `content-form`,最多 5 次,首个 3xx 后关闭 | 3.3、3.4 | C2B-03;已实现 `0c06f15` |
| 3 | 次要 | 部分静态资源与定时刷新被拒 | 保持拒绝,不登记;删除"定时刷新精确登记"规则;静默判定只计获准请求 | 3.4、3.5 | C2B-02/10;**v1.4 更正**:生产代理仍有刷新登记与放行集合,C2b 的拒绝是偶然(附录 G 第 6 条),待实现(C2c) |
| 4 | 重要 | 运行按钮是 button + onclick,无 href | 按完整写法提取地址,其余不兼容 | 3.5 第 2 项 | C2B-06;已实现 `a364489` |
| 5 | 重要 | 字段回调运行时追加 `&random=<小数>`(v1.2 第 3.4 节已预见) | 按预见规则落实:登记原文或原文 + 末尾一个 `random=0.\d{1,20}` | 3.4 | C2B-10;已实现 `2ee8ab6` |
| 6 | 重要 | 构建子标签按会话记忆,裸 `/build/N` 不一定显示 Summary | 读取一律用 `/build/N/overview`;裸地址只核导航栏;提交落点同此 | 0.1、3.5、3.6、5.2、5.3 | C2B-06;读取已实现 `a364489`;落点核对待核对 |
| 7 | 重要 | 配置 ID 不在面包屑上 | 配置来源改为 overview 标签 + 兄弟标签 + 面包屑 + 复制路径 + 构建名;结果读取的配置路径核对采用同一来源 | 5.3 第 1、3 项、附录 C-3 | C2B-04/07(取证脚本);生产读取待实现 |
| 8 | 重要 | 页面脚本改写 `String.prototype.trim` | 页面内只取原始数据,规整在 Node;脱敏内不用 trim;新增内置函数原生检查;Python 自检为最终防线;不采用隔离环境并写明理由。**v1.4 已被附录 G 第 1 条取代** | 0.5、1、3.1、3.5、7、8 第 12 条、9.2 | C2B-09;规整已实现 `4a4a727`;其余见附录 G 第 1 条 |
| 9 | 重要 | 身份值子串替换改坏代码与包名 | 两端改为 ASCII 单词边界,共用测试向量。**v1.4 已被附录 G 第 3 条取代** | 3.7、9.1 | C2B-04;已实现 `6028356`,待按附录 G 第 3 条重做 |
| 10 | 重要 | 子构建 `BUILD_PKG_LIST` 是全量包列表(Full 构建),"恰好一项等于目标行"永远不成立 | 改为"目标行恰好出现一次且同仓库无其它行";`sbs_target_echo` 取该行 | 0.1、5.3 第 4 项、5.4、9.1 | 待实现(C4) |
| 11 | 重要 | 父构建回显的 BUILD_REFERENCE/SNAPSHOT_NUM 是表单值本身;子构建才给出实际快照地址 | "实际用了冻结快照"改由子构建 `SNAPSHOT_NUM_URL` 最后一段证明;父构建 SNAPSHOT_NUM 只记录,C6 后再定;结果文件新增 `snapshot_used` | 0.5、5.3 第 2、4 项、5.4、9.4 第 2 步 | 待实现(C4) |
| 12 | 次要 | 父子构建都有 `QB_TRIGGER_ID`(=自身);父构建也回显 `FAIL_FAST`、`CHILD_CONFIGURATIONS`;子构建有 `REPO_ARCH` | 加入回显核对,收紧绑定 | 5.3 第 2、4 项、8 第 4 条 | 待实现(C4) |
| 13 | 重要 | C2b 多次"核对失败但没有现场",每次多耗一次人工登录 | 生产代理在结构核对失败时先只读取证再报错,CLI 写诊断目录 | 3.2、4.1、4.3、5.1、8 第 13 条 | 取证脚本已有(C2B-05/08);生产待实现 |
| 14 | 次要 | Child Build 表结构已实测(四列,一行,URL 为本站绝对地址,失败为 `FAILED`) | 写定定位方式、表头与链接形态;Build Result 记入结果文件 `child_build_result_text` | 1、5.3 第 1 项、5.4 | 待实现(C4) |
| 15 | 次要 | 子构建配置路径末段为 `build` | 由父路径推出子路径;配置校验规则 7 | 1、2.1、5.3 第 3 项 | 待实现(C1 补、C4) |
| 16 | 次要 | `EACH_GBS_BUILD_STATUS` 在失败子构建上同样为空 | 写明"为空不代表各架构成功",通过只看 Status;规则不放宽 | 0.1、5.3 第 4 项 | 文字澄清 |
| 17 | 次要 | 1186372 属 Unified 工程,且 FAIL_FAST、架构写法与 Base 不同 | 失败样本改用 1193469;Unified 启用前单独取证 | 0.1、0.4、附录 C-11 | C2B-06 |
| 18 | 次要 | Ref. Snapshot 模式下 SNAPSHOT_NUM 只有一个选项 | 写明参考快照更新后同 campaign 未触发 unit 全部拒绝,stdout 给出新旧值 | 0.5、4.3 第 5 步、9.1 | 待实现(C3) |
| 19 | 重要 | 浏览器对"设成同一个值"不触发回调;v1.2 每字段等待回调 | 值已相等时显式触发 change,每字段恰好一次回调;本机与真机演练验证 | 3.5 `fill` 第 4 步、9.2、9.3、9.4 第 1.6 步 | 实现中已对复选框、双列表处理;下拉框、文本域待核对 |
| 20 | 重要 | 完整十二字段填表从未在真机执行,C6 是第一次 | 新增第 9.4 节第 1.6 步:完整填表演练(不提交)+ 读一个成功的 Base 子构建 | 9.4、10 | 待执行(C5) |
| 21 | 次要 | BUILD_TYPE=Full 会构建全量包列表(样本 245 包,超时 8 小时) | 写明代价;配置值不变 | 0.5 | — |
| 22 | 次要 | v1.2 第 3.6 节"子页无 Summary 时用页面标题中的构建号"与实测不符(C2A-04) | 删除,改为导航栏标签 | 3.6 | C2A-04;已实现 `09e14c5` |

## 附录 G:v1.3 → v1.4 修改记录(R1 修订稿评审)

三家结论:Kimi 可冻结(3 条建议);ChatGPT 修改后可冻结(阻断 1、重要 3、次要 2、建议 1);Claude Code 修改后可冻结(阻断 1、重要 4、次要 5、建议 3)。设计方回仓核对了两条涉及代码现状的意见:生产代理确实仍有刷新登记与放行(`qb_browser_agent.mjs` 第 105、476 行),脱敏确实在活动文档上 `cloneNode`(第 230 行)。采纳原则同附录 D:同一问题多家提出时比较方案取最稳妥者,写明采用谁的、为什么。

| 编号 | 级别 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|---|
| 1 | 阻断 | 页面主环境可劫持 `outerHTML` 等读取器,序列化结果把 `Failed` 变成 `Successful`,八项原生检查与 Python 脱敏自检都发现不了(本地复现);原生检查清单来自采样而非代码依赖 | ChatGPT(阻断)、Claude Code(重要) | 采用 ChatGPT:生产代理不在页面主环境执行任何代码;读取用同一次导航响应的服务器原始字节,在 CDP 隔离环境中惰性解析;表单读回在隔离环境中读活动 DOM;Python 自检只担脱敏。不采用 Claude Code 的"扩充原生检查清单 + 静态比对":它仍信任 `Function.prototype.toString` 与页面可改写的读取器,且清单要随代码长期维护;隔离环境从根上消除依赖,且可用已在用的公开 CDP 会话实现(v1.3"Playwright 无公开接口"的说法不成立,设计方更正)。原生检查删除 | 0.1、0.5、3.1、3.5、3.6、7、8 第 12 条、9.2、9.3、10 |
| 2 | 阻断 | 子构建快照"末段等于冻结值"被写成硬判据,但唯一样本父构建以 Live 提交、子构建仍回显 Ref. Snapshot 与快照地址,二者关系无证据;正确构建可能被误判且无出路 | Claude Code | 采用 Claude Code:不作判据,只记录;不一致时有指引地停止、不写结论;第 1.6 步要求以 Ref. Snapshot 提交的样本。同时吸收 ChatGPT 第 4 条:是否"一致"按登记的下载站快照根与完整路径判断,而不是只比最后一段 | 0.5、5.3 第 4 项、5.4、8 第 5 条、9.1、9.4 |
| 3 | 重要 | 单词边界脱敏在显示名等于完整业务词(`Successful`、`Full`、`root`)时仍会改坏判据 | ChatGPT | 采用 ChatGPT:身份值按位置遮蔽(与 Python 现有 `_UserFields` 一致),不全局改写;凭据仍全局脱敏。代价:显示名在自由文本中出现时会残留,只计数不阻断——这是用户本人的显示名,出现在本机证据里,隐私影响小于判据被改坏 | 3.7、8 第 15 条、9.1 |
| 4 | 重要 | 快照地址判断只比最后一段,外站、错误工程、file 地址都能通过 | ChatGPT | 采用,并入第 2 条:按登记的快照根与完整路径判断,带用户信息、查询、片段一律不一致 | 5.3 第 4 项、附录 C 第 6 项、9.1 |
| 5 | 重要 | Full 构建的 `Failed` 只到步骤级,不能归因到本 unit 的包,却直接写 FAIL 交给 P5R | Claude Code | 采用:FAIL 时读 step_status,记失败步骤与错误信息(不作判据,缺失不改变判定);明确 FAIL 语义并新增 design.md §4.5 第 14 条约束 P5R | 0.1、0.5、5.3 第 5 项、5.4、8 第 5 条、9.1、附录 A、附录 C 第 13 项 |
| 6 | 重要 | v1.3 称"刷新拒绝已是现状",实际生产代理仍登记并放行刷新,被拒只是因为 random 不匹配;被拒请求还会刷新活动时间 | Claude Code | 采用:不得保留刷新放行集合,静态断言;活动时间只在放行时更新;更正附录 F 第 3 条 | 3.4、8 第 16 条、9.2、10、附录 F 第 3 条 |
| 7 | 重要 | "值已相等也触发回调"与"不改 recorder""页面内只取数据"冲突;文本域可能双触发,而服务器侧计数看不出 | Claude Code | 采用其规则:每字段总共只派发一次 change,双列表只在 recorder 上派发且值不变,设值动作经 Playwright 定位器执行;字段窗口内出现被拒回调即本字段失败。不采用其"`fill()` 已派发 change"的事实断言,改为按控件类型由测试确定,因为设计方无法确认该框架行为。**(v1.5:该处理已由附录 H 第 8 条取代)** | 3.1 第 4 条、3.5 第 3、4 步、9.2 |
| 8 | 重要 | 诊断在活动文档上克隆会再次加载图片(本地复现新请求);结构 JSON 未纳入脱敏 | ChatGPT、Claude Code(次要) | 合并采用:诊断前撤销登记;惰性文档上被动处理,不克隆活动节点;结构 JSON 与 HTML 同一脱敏上下文;诊断失败不返回原始内容 | 3.1、3.2、8 第 13 条、9.1、9.2、9.3 |
| 9 | 次要 | 正文只展开五项配置来源中的三项 | ChatGPT | 采用:五项逐条写全,解析基址为已核验请求地址;构建名前缀按工程登记(设计方另外更正了前缀的推导写法) | 5.3 第 1 项、9.1 |
| 10 | 次要 | 第 1.6 步先 close 再读样本,顺序矛盾;"C6 前置"与"可后补"边界不清 | ChatGPT | 采用:先读样本再填表最后 close;填表演练始终是第 2 步前置,样本缺失登记未完成、不计入 C5 完成 | 9.4 |
| 11 | 次要 | §3.4 把相对地址原文当成完整 URL 比较 | Claude Code | 采用:原文按表单页地址解析为绝对地址再比较 | 3.4、9.2 |
| 12 | 次要 | 附录 C 第 12 项把合成环境的拦截计数写成真机会话结论,且行号指向不符 | Claude Code | 采用:拆成真机与合成两行,更正引用 | 附录 C |
| 13 | 次要 | v1.3 误删前轮评审修复所立的文字(§4.2 互斥说明与 Open3D 理由、§6.2 哈希定义、§9.5 CHECK 负例),附录 F 位置列不全 | Claude Code | 采用:恢复原文,附录 F 补注 | 4.2、6.2、9.5、附录 F |
| 14 | 次要 | recorder 的措辞"各选项 value 的十六进制"不准,多选分隔符未取证 | Claude Code | 采用:写明实测一项时的形态,多于一项即 `QB_FORM_CHANGED` | 3.5、9.2 |
| 15 | 建议 | `@freeze` 是"不改选项"还是"跳过回调"未写明 | ChatGPT | 采用:同样登记、触发一次、等待 | 3.5 第 2 步、9.2 |
| 16 | 建议 | `BUILD_NOTES` 回显第一次验证就在唯一真实提交之后 | Claude Code | 采用:第 1.6 步尽量读一个 BUILD NOTES 非空的父构建;第 2 步失配则停止按 R1 修订 | 9.4 |
| 17 | 建议 | random 极少数写法会让 unit 失败,易被误判为表单变化 | Claude Code | 采用:写明后果与提示文字 | 3.4 |
| 18 | 建议 | 登录 5 次配额用尽时无提示 | Claude Code | 采用 | 3.3 |
| 19 | 建议 | "目标行出现在子构建列表"对 sandbox commit 尚未证实 | Kimi | 采用:写明前提,P12 证实 | 5.3 第 4 项 |
| 20 | 建议 | 写清字段联动随同一响应返回、不产生第二请求 | Kimi | 采用,并写明若真机出现额外请求按 R1 处理 | 3.5 第 4 步 |
| 21 | 建议 | 附录 C 第 10 项应注明归档中是转义形态 | Kimi | 采用 | 附录 C |

## 附录 H:v1.4 → v1.5 修改记录(第二轮评审)

三家结论均为"修改后可冻结":Kimi(重要 2、建议 1);ChatGPT(重要 3、次要 2、验收建议 1);Claude Code(阻断 2、重要 5、次要 4、建议 3,并在本机同版本 Playwright 与 Chromium 上做了四组实验)。三家一致认可 v1.4 的隔离环境 + 导航响应原始字节方案,本轮没有架构改动,只修边界条文、脱敏一节的自相矛盾与一个未取证的前提。设计方回仓核对:`Requested By` 列在 `L/live-12/06.response.html:845`;`qb_browser_agent.mjs` 约第 674 行确实用 `addInitScript` 安装 `window.open` 守卫。采纳原则同前:同一问题多家提出时取最稳妥者,写明采用谁的、为什么。

| 编号 | 级别 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|---|
| 1 | 阻断 | §3.7 末段的写后自检仍是"全文不含登录显示名",与同节的位置遮蔽矛盾;显示名等于 `Successful` 等业务词时,每个含该词的证据都自检失败,通过的构建一个也写不进结论(Claude Code 用仓内 `PageRedactor` 复现,ChatGPT 本地复现) | 三家 | 采用 Claude Code 的判据写法(凭据全局无残留 + 登记位置已遮蔽,不做全局显示名检查),吸收 ChatGPT"测试必须覆盖脱敏后自检通过"的要求;写明对应删除 `qb_redact.py` 的全局身份替换与全局检查 | 3.7、8 第 15 条、9.1、10 |
| 2 | 阻断 | 读取改用导航响应原始字节,但"原始字节里有本文要读的字段"从未取证(C2b 归档的都是活动文档);且以归档页为响应体的夹具让这一前提按构造成立,任何测试都发现不了 | Claude Code | 采用:第 1.6 步 a 增加原始字节与活动文档逐项比对,作为第 2 步前置(比对不依赖成功样本);第 9.3 节假服务器不得直接用归档页,新增"导航标签由脚本插入"夹具,断言停而不错。与 Claude Code 方案的差别:比对由取证脚本执行,而不是在生产代理里为静态断言开一个"仅取证入口"的例外——生产代码保持零例外更容易审 | 3.1 第 2 条、9.3、9.4、10 |
| 3 | 重要 | 主环境执行接口清单不全:`locator.evaluate`、`evaluateAll`、`$eval`、`$$eval`、`waitForFunction`、`addInitScript`、`exposeFunction`、`exposeBinding` 都在主环境执行(Claude Code 实测),`addInitScript` 现有代码在用,静态断言会在仍有主环境代码时通过 | Kimi、Claude Code | 采用 Claude Code 的完整清单与"`addInitScript` 唯一具名例外(`window.open` 守卫)、出现次数恰为 1"的断言;每个名字一条负例 | 3.1 第 1 条、8 第 12 条、9.2 |
| 4 | 重要 | 去掉全局替换后,配置页 `Requested By` 列不再被遮蔽,写后的位置检查也不看它——v1.4 新引入的落盘泄漏 | Claude Code | 采用:写出身份承载位置登记清单(含 `Requested By`),`_UserFields` 按清单实现;新增登记流程(取证时检查登记位置外的显示名计数);附录 C 补第 14 项 | 3.7、8 第 15 条、9.1、9.4、附录 C |
| 5 | 重要 | 快照"不一致即停"在参考快照滚动这一常规场景下无出路:Full 构建约 24 小时,快照按日期滚动;此时无 RESULT、不能降级、不能 retrigger、重跑 fetch 也无用 | Claude Code | 采用 `--accept-snapshot-drift`,并收紧:只能与单个 `--request-id` 同用;"漂移"限定为主机、根、段数均符合且快照名与冻结值同形态(同前缀 + 日期时间);其它不符开关无效;新增 `snapshot_drift_accepted` 键留痕;已接受的 request 再次读取视同已裁定;design.md 同步要求 P5R 报告标出 | 0.5、5.1、5.3 第 4 项、5.4、8 第 5 条、9.1、附录 A |
| 6 | 重要 | §9.1 仍要求已撤销的判据(子构建 `BUILD_REFERENCE=Live` 即拒、快照不符报绑定不符、内置函数非原生报读取失败),与新正文无法同时满足 | ChatGPT | 采用其候选改法;另加"子构建 `BUILD_REFERENCE=Live` 只记录"的正例 | 9.1 |
| 7 | 重要 | §5.3 第 4 项要求记录的子构建两个回显值,在固定 schema 中没有键 | ChatGPT、Claude Code | 采用 Claude Code 的键名 `child_params_echo`(与 ChatGPT 的 `child_snapshot_echo` 内容相同,与父构建的 `params_echo` 对称);同时采用 Claude Code 建议:`snapshot_used` 改记实际快照名,否则成功时它恒等于冻结值、不携带信息 | 5.3、5.4、9.1、附录 A |
| 8 | 重要 | "设值调用是否产生 change"交给测试决定,生产代码却要确定分支;文本域"设值后补派发"还会与失焦产生的原生 change 叠加 | Claude Code、ChatGPT | 合并:采用 Claude Code 实测(Playwright 1.58.2 的 `selectOption`、`check` 各产生一次 change)→ 下拉框、复选框值不等时不补派发;采用 ChatGPT 实测 → 文本域 `fill` 后受控失焦、不补派发,计数窗口延续到下一字段登记;采用 Claude Code 的启动自检(版本变化时停止,不按旧分支继续)。更正附录 G 第 7 条 | 3.5 第 4 步、9.2、10、附录 G |
| 9 | 重要 | §3.1 第 4 条称设值动作"运行在 Playwright 自己的隔离环境里",但派发 `change` 必然进入主环境,可被页面挂钩或吞掉(实测) | Claude Code | 采用:更正措辞,写明取值与设值免疫、派发不免疫,后果方向安全,列为已接受残余;加"页面吞掉 change"用例 | 3.1 第 4 条、8 第 12 条、9.2 |
| 10 | 次要 | 第 9.4 节允许样本 a/b 由真实提交补齐,但第 10 节 C6 仍依赖"C5 完成" | ChatGPT | 采用:C6 依赖改为本机门禁 + 1.6 步 c 与原始字节比对通过 + FatTank 确认;a/b 为具名挂账,未关闭不得 CLOSED | 9.4、10 |
| 11 | 次要 | 辅助页 step_status 的"读不出记 null"与第 5.4 节"HTTP 非 200 不写 RESULT"优先级不明 | ChatGPT | 采用:仅本页的普通读取失败记 null,优先于通用规则;脱敏自检失败仍停止。设计方补充:代理异常与可信环境不可用说明工具本身不可用,仍为 `QB_FETCH_FAILED` | 5.3 第 5 项、5.4、9.1 |
| 12 | 次要 | 隔离环境在每次导航后失效,复用旧环境报"找不到执行环境"(实测),正文未规定创建时机 | Claude Code | 采用:每次导航后重建,失败即 `QB_TRUSTED_CONTEXT_UNAVAILABLE` | 3.1 第 1 条、3.6、9.2 |
| 13 | 次要 | §10 C4 行仍写"v1.3 判据" | Claude Code | 采用,并写明 v1.5 新增的读取规则 | 10 |
| 14 | 次要 | §9.2 用例仍"伪造 `toString` 返回原生",而原生检查已删 | Claude Code | 采用:改写为"伪造 `toString` 不影响任何结果",并补充改写 `textContent`、`parseFromString` | 9.2 |
| 15 | 次要 | §8 编号乱序(13、15、16、14) | Kimi | 采用,按序排列 | 8 |
| 16 | 建议 | 导航响应正文的解码口径未规定 | Claude Code | 采用,但改为**严格解码**(非法字节即报错),而不是"解码结果含替换字符即失败"——页面原文本身可能合法地含有替换字符 | 3.1 第 2 条、9.2 |
| 17 | 建议 | "隔离环境中内置读取器为原生"是第 3.2 节的前提,应直接断言 | Claude Code | 采用 | 9.2 |
| 18 | 次要 | §3.1 凭据边界一段仍写"从 DOM 拿内容",与第 2 条不符 | 设计方自查 | 改为"导航响应正文原始字节" | 3.1 |

## 附录 I:v1.5 → v1.6 修改记录(实施期汇总修订)

v1.5 于 2026-10-14 冻结(sha256 `f16621bb…dfedcf91c`),此后 C2c 至 C6 按冻结稿实施。实施中登记的设计方裁定、C5b/C6 真机事实与 FatTank 2026-10-19 的两项决定,在本版并入正文。设计方回仓核对了各裁定原文(进度文件第 28–45 节)、`qb_browser_agent.mjs` 与 `qb_browser.py` 中对应实现、C6a/C6b 证据原文件;核对到的实现与正文不一致之处列为第 14 条。实施期取证工具(`docs/clang-fix-campaign/spikes/` 下)的失败落盘规则(实施裁定 P5Q-C5B-02)不属于生产契约,不并入正文。

| 编号 | 类别 | 内容 | 依据 | 改动位置 |
|---|---|---|---|---|
| 1 | 新功能 | 自动查找构建号:提交后模式(提交前取基线、最长 180 秒、至多 10 轮)与读取时模式(无基线、单次);只用已有 `read` 与只读放行集合;绑定走第 5.2 节同一组核对与同一事务;非匹配页面不落盘;配置页不可识别时不提交 | FatTank 裁定(实施裁定 P5Q-C6B-01);附录 C 第 15、17、18 项 | 头部、0.1、0.3、0.4、3.2、3.5、3.6、3.7、4.1、4.2、4.3 第 2.5/7/10 步、4.4、5.1、5.2、5.5、6.1、6.3、7、8 第 17 条、9.1、9.2、9.3、9.4 第 3 步、9.5、10、附录 A |
| 2 | R1 定案 | 子构建快照地址按现行三分规则正式作为判据;父构建 `SNAPSHOT_NUM` 继续只记录;停止指引措辞改为"与登记不符,须人工核对后按 R1 修订登记" | 冻结稿第 9.4 节第 2 步的要求;FatTank 裁定(P5Q-C6B-01);附录 C 第 16 项 | 0.1、0.5、5.3 第 4 项、附录 A |
| 3 | 事实登记 | 成功样本(`Successful`、`SUCCESSFUL`、`EACH_GBS_BUILD_STATUS` 为空)、`BUILD_NOTES` 原样回显、提交落点 `/wicket/page`、配置页两张构建表、原始字节前提成立、快照滚动、快照一致时的构建时长、终态重读幂等 | C5b、C6a、C6b | 0.1、0.5、1、3.1、3.5、5.3、5.4、9.4、附录 C 第 15–19 项 |
| 4 | 并入裁定 | 含 `stop` 的放行用例按三层验收;永久禁止正则按子串匹配造成的误拒列为已接受残余 | P5Q-C2C-03 | 3.4、9.2 |
| 5 | 并入裁定 | SNAPSHOT_NUM 不可用应答 `snapshot_state` 与 Python 校验;两个 CLI 的 stdout `message` 键;快照提示收敛为两个模板 | P5Q-C3-02、P5Q-C3-04 | 0.5、3.2、3.5 `fill` 第 2 步、4.1、4.3 第 5 步、9.1、9.2 |
| 6 | 并入裁定 | 普通下拉框选项文字重复即结构变化 | P5Q-C3-04 | 3.5 `open_form` 第 4 项、9.2 |
| 7 | 并入裁定 | 远端核对的传输仓库用默认格式、只做 `ls-remote`、不对齐源格式;sha256 远端的已接受残余 | P5Q-C4-02 | 4.3 第 6 步、8 第 9 条 |
| 8 | 并入裁定 | C6 的专用状态库、专用配置与本机 bare 镜像;C6 不覆盖真实 Gerrit 远端核对 | P5Q-C6-01 | 9.4 第 2、3 步 |
| 9 | 并入裁定 | 停止类别 `failure_category`、固定 stderr 行、命令失败的 trace 字段 | P5Q-C6A-03 | 3.2、8 第 19 条、9.2 |
| 10 | 并入裁定 | 关闭协议:代理收到 `close` 后自行退出,驱动写出 `close` 后立即关闭 stdin;测试入口与生产入口一致 | P5Q-C6A-04、P5Q-C6A-05 | 3.1、8 第 18 条、9.2 |
| 11 | 并入裁定 | `login_facts` 八键定义与判读注意(最终路径为 `/` 时须结合被拒计数与通道状态) | P5Q-C6A-05、P5Q-C6B-01 | 3.2、3.3、9.2 |
| 12 | 补列 | `qb-result-fetch` stdout 的 `message` 键:v1.5 正文已要求在 stdout 输出指引,但键表漏列;实现已有此键 | 设计方回仓核对 | 5.1 |
| 13 | 补记 | 同一表格多段表头时,每段重新确定身份列 | C3 修复 C2c 评审遗留(进度文件第 29.2 节) | 3.7 |
| 14 | 实现偏差 | 登录固定提示:实现少了"若提示登录失败,可在窗口中重新输入"一句,C7 按第 3.3 节补齐 | 设计方回仓核对(`qb_browser_agent.mjs` 的 `login`) | 3.3、9.5、10 |
| 15 | 状态 | 提交计划:C2c–C6 标为已完成;原 C6 的"收口文档"移到新增的 C8;新增 C7(v1.6 实现)与 C8(验证性提交与收口) | — | 9.4、10 |

## 附录 J:v1.6 → v1.7 修改记录(外部评审)

本轮收到两家意见:ChatGPT(重要 4、次要 3)、Claude Code(重要 3、次要 4、建议 5,另有多项"已核对成立"的结论)。两家结论均为"修改后可冻结",无阻断项;两家都在仓库 `48b0aa9` 上核对了代码与证据,ChatGPT 另复跑了原始字节探针与相关单元测试(532 passed)。Kimi 的意见本轮未收到。设计方回仓核对了被引用的代码:`qb_browser.py` 中 `_command` 在进程缺失时、`decode_response` 在应答非法时确实返回与合法应答相同的 `_unknown()`;`QbBrowser.close` 超时分支确无 trace 写入;代理 `read` 的导航使用 Playwright 默认 30 秒超时,驱动 `readline()` 无独立超时;`qb_result_fetch.py` 的证据序号为"目录中最大序号加一",`evidence` 列表每次执行重新开始;C5b 填表演练的验收文件与进度文件第 28.3 节的转码反例。采纳原则同前:确属问题的一律修改;两家方案择优,都不合适时用设计方方案,并写明理由。

| 编号 | 级别 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|---|
| 1 | 重要 | 驱动把"进程缺失、管道失败、应答非法"与代理合法的 `landed: unknown` 合并成同一返回值,提交后无法区分是否应自动查找 | ChatGPT | 采用其方向,写成行为要求:驱动侧失败带只在驱动内部使用的标记,CLI 不做查找,仍按落点 unknown、保持 QB_REQUESTED;不规定具体字段名。测试经真实驱动注入四类失败,并保留合法 unknown 的正例。补一句:代理在放行后内部出错返回的 unknown 属合法应答,照常查找 | 3.2、4.3 第 10 步、5.5 模式表、8 第 17 条、9.1、10 |
| 2 | 重要 | 180 秒只限制"轮次开始",慢读取可使查找远超预算并长时间持锁;"恰好 10 轮"在读取有耗时时不成立 | ChatGPT;Claude Code(轮次部分) | 采用 ChatGPT 的共享截止点与"未核对完整轮不绑定",新增结果类别"查找超时"。与其方案的差别:不按剩余预算中断进行中的读取——逐行协议无法取消已发出的命令,中断只能杀掉代理;改为驱动对 `read` 应答设 60 秒上限、截止点之后不发起新读取,总耗时上限约 240 秒。"至多 10 轮、零耗时假时钟恰 10 轮"采用两家共同写法 | 0.4、3.2、4.3 第 10 步、5.5 第 4、5 步、9.1、9.2、10 |
| 3 | 重要 | 本机集成用例的配置页 GET 计数漏了 `open_form` 内部的那次导航 | ChatGPT | 采用,并要求协议命令清单与服务器请求清单分开计数 | 9.3 |
| 4 | 重要 | 第 3.1 节第 2 条仍允许 Playwright `response.body()` 作为原始字节来源,而实施期已实测它会转码、使非法字节通过严格解码 | ChatGPT | 采用:只用 `Fetch.getResponseBody`,不得回退;注明进度文件第 28.3 节的原始反例。实现本就如此,只是正文对齐 | 3.1 第 2 条 |
| 5 | 重要 | 读取时模式是唯一成批读取他人构建页面的模式,却在真机上一次都不跑 | Claude Code | 采用其"构造一个未绑定 request、零提交运行一次 fetch"的方案;构造方式限定为实施裁定 P5Q-C6-01 的方法加第 4.3 节第 8 步的同一组原语(不手写 SQL),时点在验证性提交的结果读取完成之后;e3 按第 3.7 节登记流程处理(该计数只针对登录显示名) | 9.4 第 3 步、9.5、10 |
| 6 | 重要 | P12 批量时,未绑定 request 的恢复窗口只有约 10 个构建 | Claude Code | 部分采用:写入"已接受的限制",并把时效提示写进 `submit_uncertain` 的 `message`,列为 C8 收口文档中的 P12 操作要求。不采用两点:① `--requests-file` 按 request_seq 重排——一次执行数分钟内即处理完全部项,顺序对时效没有实质影响,却改变 stdout 顺序的约定;② 在 stdout 末尾追加提示——stdout 是 JSON 数组,不能附加文本,已改为放进每个 unit 的 `message` | 4.3 第 10 步、5.5、10 |
| 7 | 次要 | 第 3.1 节要求"终止写入 trace",实现未写 | ChatGPT、Claude Code | 采用 Claude Code 的固定记录形状 `agent_terminated`;按 ChatGPT 的写法由 CLI 在关闭后写入,写出失败不覆盖已完成结果。作为附录 I 第 14 条之外的第二处实现偏差,由 C7 补齐 | 3.1、9.2、9.5、10 |
| 8 | 次要 | `Recent Builds` 的"标题文字"有两种读法;整个标题栏的文字是 `Recent Builds history rss` | ChatGPT | 采用:取标题栏直接子元素 `.flex-1` 的文字;补真实结构正例与"只在别处出现同名文字"的负例 | 5.5 第 1 步 c、9.1 |
| 9 | 次要 | 快照停止指引的验收仍要求旧措辞,正确实现新提示后会失败 | ChatGPT | 采用 | 9.1 |
| 10 | 次要 | 第 5.1 节与第 5.5 节把同一前置写成两种说法 | Claude Code | 采用:第 5.5 节"前置"为唯一定义;补"不一致库"用例 | 5.1、5.5、9.1 |
| 11 | 次要 | 证据文件序号没有定义,"沿用第 5.3 节末尾的连续编号"在提交后模式中没有指代对象 | Claude Code | 采用,规则与现有实现一致(目录最大序号加一、跨执行续编;C6b 重读即续编为 05–08);补用例 | 5.3、5.5、9.1 |
| 12 | 次要 | 第 3.5 节"其它字段改值后的联动尚未实测"已过期 | Claude Code | 采用:改为 C5b 填表演练的实测事实,新增附录 C 第 20 项(设计方回证据原文件核对,含"只有两个文本域改值") | 3.5、附录 C |
| 13 | 次要 | "至多约 10 个"容易被误读为读取量上限 | ChatGPT | 采用:写为"样本 10 行,规范上限 50 行" | 5.5 |
| 14 | 建议 | 候选页的诊断是"代理生成、Python 丢弃",正文未写明 | Claude Code | 采用 | 5.5 第 3 步、9.1 |
| 15 | 建议 | 缺"查找中代理异常"的用例 | Claude Code | 部分采用:v1.6 第 9.1 节已有该用例(评审漏看);补"设在第 2 个候选时"、配置页仍归档、零数据库写入三项断言 | 9.1 |
| 16 | 建议 | 快照漂移分支没有真机样本 | Claude Code | 采用:不为它制造漂移,挂账到 P12,列入 C8 收口文档 | 9.4 第 3 步、10 |
| 17 | 建议 | 本轮采纳项应记附录 J 并进入 C7 清单 | Claude Code | 采用 | 10、附录 J |
| 18 | 不采用 | 第 4.3 节第 2.5 步应分层:只有页面身份不符才不提交;`Recent Builds` 结构不符时照常提交、跳过查找、提示人工绑定 | Claude Code | **不采用**,保留 v1.6 的"配置页认不出就不提交"(ChatGPT 本轮明确认可这一做法)。理由:结构不符时照常提交,P12 批量会产生一批未绑定构建;按本表第 6 条,它们很快被挤出 10 行窗口,只能逐个人工查号,正是自动查找要消除的工作量;而表结构改版的处理只是按 R1 更新附录 C 第 18 项的登记与解析规则,代价小且一次性。代价是表改版期间无法提交,本文接受 | — |

## 附录 K:v1.7 → v1.8 修改记录(定向评审)

本轮为定向评审,只审 v1.7 的改动与附录 J 第 18 条的不采纳决定。收到两家意见:ChatGPT(重要 1、次要 1)、Claude Code(重要 2、次要 4、建议 3,并逐条核对了附录 J 的 17 条采纳项,结论为"都改对了")。两家结论均为"修改后可冻结",无阻断项;两家都同意附录 J 第 18 条的不采纳(Claude Code 撤回了自己上轮的提议,并说明了理由)。Kimi 本轮未提交意见。设计方回仓核对:代理 `submit` 的等待为 Ok 点击 60 秒、放行等待 10 秒、跳转等待 60 秒(`qb_browser_agent.mjs` 的 `submit`);`read` 与 `open_form` 的页面导航均未传显式超时;`qb_trigger.py` 中代理在某个 unit 不可用后,后续 unit 会各自以 `rejected` + `QB_BROWSER_UNAVAILABLE` 失败,但条文未规定;C6a 归档的两份变量页中 `Triggered By`、`Requested By` 均为 0 处。

| 编号 | 级别 | 问题 | 提出 | 采用方案与理由 | 改动位置 |
|---|---|---|---|---|---|
| 1 | 重要 | 截止点与绑定所需的最后一次读取没有闭合:最后一个候选跨截止点返回、唯一匹配时,概览页读不读、算不算超时,有两种实现 | ChatGPT | 采用:截止点检查覆盖绑定所需的概览页;截止点已过、概览页未发起 → 不绑定、"查找超时";截止点前已发起的照常完成并核对。同步去掉第 4.3 节第 10 步残留的"最长 180 秒" | 4.3 第 10 步、5.5 第 4、5 步、9.1 |
| 2 | 重要 | `submit` 没有驱动侧应答上限;代理挂起时 CLI 无限等待并持锁,而此时构建可能已存在、恢复窗口正在流逝 | Claude Code | 采用其 150 秒上限(代理自有预算约 130 秒,设计方回仓核对属实);超时按驱动侧失败处理、不查找。`open_form`、`fill` 不设上限并列为已接受残余,理由同其分析:挂起时提交必定未放行 | 3.2、4.3 第 10 步、9.1、9.2、10 |
| 3 | 重要 | 代理被终止后,批次中剩余 unit 的处置没有条款 | Claude Code | 采用:不重启代理,剩余需要浏览器的 unit 记 `rejected` + `QB_BROWSER_UNAVAILABLE` 与固定提示,不发命令、不写库。与现有实现的结果码一致,只是把它写成规定并避免向已终止的代理继续发命令 | 4.3 第 1 步、9.1 |
| 4 | 次要 | "一次执行数分钟内处理完、顺序对时效无实质影响"是不成立的保证 | ChatGPT | 采用:删去该保证,保持输入顺序与 stdout 顺序的约定,改写为 P12 操作要求"先恢复未绑定请求,再继续批量提交";补顺序用例 | 5.5、9.1 |
| 5 | 次要 | "驱动侧失败"的外延只点了三类,实现者容易只标这三类,对"代理活着但载荷不合协议"的几类仍去查找 | Claude Code | 采用:外延写成"凡驱动自己合成落点 unknown 的全部路径"并逐类列出,写明这几类也不查找及理由;用例改为逐类各注入一例 | 3.2、9.1 |
| 6 | 次要 | 第 3.2 节举的"以 `QbBrowserError` 表示"会改掉 `submit` 已发出后从不抛异常的现有契约,且"`released` 不为 false"容易反向理解 | Claude Code | 采用:不规定字段名与实现方式,只规定标记的出现条件与不外泄(不进 stdout、结果文件、数据库,不改错误码),并要求保持返回值契约 | 3.2、9.1 |
| 7 | 次要 | 零提交真机验证的 e3 验不到它声称要验的东西:该计数只统计操作者自己的显示名,变量页上本就没有已登记的身份列 | Claude Code | 采用:拆为 e3a(登录显示名计数)与 e3b(候选页结构断言 + 人工浏览变量名集合);第三方姓名出现在变量值自由文本中列为已接受残余并写入收口文档;补一个把这条限制钉成事实的离线用例 | 9.1、9.4 第 3 步、9.5、10 |
| 8 | 次要 | 第 2.5 步的两类失败(页面身份 / 最近构建表结构)同一错误码、同一提示,运维无法区分处置 | Claude Code | 采用:错误码不变,`message` 与 trace 分两类模板并写出首个失败核对项名 | 4.3 第 2.5 步、9.1 |
| 9 | 建议 | `read` 上限 60 秒依赖代理导航的框架默认 30 秒,未显式钉住 | Claude Code | 采用:代理显式设置 30000 毫秒;源码静态断言"驱动上限大于代理自有预算",`submit` 同样断言。这是代理文件改动,四个拦截安全组按第 9.5 节重跑 | 3.2、9.2、10 |
| 10 | 建议 | 截止点比较边界("已过"是 `>` 还是 `>=`)影响"恰 10 轮";trace 没有逐次读取耗时 | Claude Code | 采用:严格大于;trace 增加每次读取的耗时(毫秒),供第 9.4 节第 3 步用真机数据核对 60 秒上限的余量 | 5.5 第 4、5 步、9.1 |
| 11 | 建议 | 零提交验证中构造的 unit 需要多少状态没写 | Claude Code | 采用:只需满足第 5.5 节"前置";意外出现匹配即停止并记录 | 9.4 第 3 步 |
