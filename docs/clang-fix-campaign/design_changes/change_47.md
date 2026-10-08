# change_47: EF-3 关闭 —— Change-Id 改为 commit-msg hook 生成并按 submission_key 缓存复用

- 状态:两轮评审意见均已处置(见 §6、§7),待 FatTank 批准后随 `design.md` 一并入库生效;入库前 `design.md` 头部的 FROZEN 标记不生效
- 生效版本:`v1.5.19-FROZEN`
- 日期:2026-10-08
- 触发:EF-3 结论(FatTank 确认,2026-10-08):**按团队规定,不得使用非 commit-msg hook 生成的 Change-Id**,确定性 Change-Id 方案不可用,必须经 commit-msg hook 生成。
- 依据:`design.md` v1.5.18 §1.4 EF-3 已预置的应急方案("降级为 commit-msg hook 生成 Change-Id,但以 submission_key 为键缓存入 state DB 复用,保住幂等;届时走 R1 变更")与 §6 风险表同名降级方案。本 change 只把该预案落为正文,不引入预案以外的新机制。

## 1. 为什么要改

v1.5.18 的 `change_id = "I" + sha1(submission_key)` 是纯函数:同一 submission_key 永远得到同一 Change-Id,幂等不依赖存储。规定不允许使用这种 Change-Id 后,只能由 commit-msg hook 生成,而 hook 每次生成的值都不同。若不缓存,同一修复的重推会变成新的 change,Gerrit 侧幂等与 A12(derived_commit_sha 可复算)同时失效。

## 2. 正文修改(均在 `design.md` v1.5.19)

| # | 位置 | 修改 |
|---|---|---|
| 1 | §0 元信息 | 版本 v1.5.19-FROZEN;下一个变更编号改为 change_48 |
| 2 | §1.4 EF-3 | `[OPEN]` → `[RESOLVED 2026-10-08]`,写明结论(按团队规定,非实测)与采用的降级方案;§7 DAG、关键路径、Phase 1 目标/范围/DoD 与文末 EF 台账同步去掉 EF-3 |
| 3 | §3.2 模块表 submission_identity 行 | 职责改为"经 hook 生成 Change-Id(纯生成,不落库)",落库与复用归 campaign_state |
| 4 | §3.4 双层 key 末条 | 删除 `change_id = "I" + sha1(submission_key)`,改为"Change-Id 来源"六条规则:一 key 一值;**生成许可由 API 依该 unit 是否已有 DERIVE 事件自行判定**,不信调用方;生成在写事务外执行,插入前在 `BEGIN IMMEDIATE` 内重查缓存与 DERIVE;**顺序不变式**:缓存行先于该 unit 首个 DERIVE 落库;其余取用只读,未命中即 StateInconsistent;hook 字节校验后复制执行;`hook_sha256` 为审计字段、命中时不比对;`change_id` 一经写入即为 Gerrit 侧唯一身份 |
| 5 | §3.4 campaign 新增表 | 新增 `campaign_change_ids`(submission_key NOT NULL 主键且须为 64 位小写十六进制、change_id UNIQUE 且格式 CHECK、source 固定 `commit_msg_hook`、hook_sha256 须为 64 位小写十六进制、created_at);只新增表,不 ALTER 既有表 |
| 6 | §4.1 campaign-preflight / sandbox-submit | preflight:config 必填键增 `gerrit_commit_msg_hook`、`gerrit_commit_msg_hook_sha256`;检查 hook 文件存在、可读、sha256 相符,并用登记的 hook **冒烟生成一次**;注明 hook 以 `sh` 执行、与 Python 解释器检查无关。sandbox-submit:写明取 Change-Id → 组装 message → derive → 写 DERIVE → push 的固定顺序及失败 exit 4 |
| 7 | §4.2 submission_identity | `compute_change_id(submission_key)` 替换为 `generate_change_id_via_hook(*, hook_path, hook_sha256, submission_key, message)`:先拒绝已含 Change-Id 行(整键不分大小写)或 Gerrit 身份 Link 的 message;校验 hook 字节后在**业务仓库外的一次性临时 git 仓库**里执行其副本;临时仓库写死本地身份并建空初始 commit(具备 HEAD);隔离 HOME/全局/系统 git 配置;hook 输入额外带一行 `X-Campaign-Submission-Key`(不进最终 commit);新进程组、30s 超时 kill、要求退出码 0、锚定正则取恰好一行;准备失败与启动失败归入拒绝;临时目录删除失败只记 WARN |
| 8 | §4.2 campaign_state | 新增 `get_or_create_change_id(state_db, *, campaign_unit_key, submission_key, hook_sha256, generate)`:命中即返回;未命中时该 unit 已有 DERIVE 或 `generate=None` → StateInconsistent;生成后在写事务内重查;写入列含 hook_sha256 与 created_at;位置在 campaign_lifecycle 横幅之前;不提供更新/删除 API |
| 9 | §4.3 错误码 | 新增 `CHANGE_ID_HOOK_FAILED`,逐项列出与 §4.2 一致的失败形态;不写库、不 push |
| 10 | §6 风险表 | "剩余 EF"行去掉 EF-3;"确定性 Change-Id 被拒"行改为"已发生,已按降级方案落地" |
| 11 | §7 Phase 1 / Phase 2 | Phase 1 注记 EF-3 已关闭;Phase 2 范围改为 `generate_change_id_via_hook` + `get_or_create_change_id` + 新表,Phase 门删除,DoD 增缓存幂等、只读模式、hook 生成各失败形态、CHECK 约束、RD-1 边界五组用例 |
| 12 | 文末变更记录 | 登记 change_46(部分回填)与 change_47 |

## 3. 不变的部分

- `submission_identity_key`、`submission_key` 的字段与字节公式不变;Change-Id 的"身份维度"仍是 submission_key,只是取值方式由哈希派生改为"首次 hook 生成 + 缓存"。
- A12 四要素与 derived_commit_sha 复算规则不变:commit message 中的 `Change-Id:` trailer 取自缓存,首写即定,复算结果不变。
- `derive(...)` 签名不变(仍接收完整 message);sandbox-submit 在组装 message 前调用 `get_or_create_change_id`。
- 既有表零修改;P4.5 已实现的 campaign_state API 行为不变,只新增一张表和一个函数。

## 4. 顺带收口 change_46 的措辞项

| change_46 项 | 处置 |
|---|---|
| RD-1 | §4.1 的概括句与 DoD 两处,措辞由"该 arch 从未 build 过"对齐为与同段详细扫描规则(无实质事件/PASS/rebaselined 锚点)一致的"该 arch 无任何实质 build outcome";详细规则未变。Phase 2 DoD 增一条边界用例钉住此读法 |
| RD-2 | CONVERGENCE 契约行补总括句"`result=n_a` 的各类事件 evidence 一律为 null" |
| RD-5 | 出口优先级公式首项 `state_inconsistent_held` 标为"本局部公式内不可达,仅作防御性保留" |
| RD-6 | residual 副本 protected/PASS-bound/清理失败路径点名 `HELD(reason=state_inconsistent)`(与 `campaign_repair_step.py` 现行实现一致) |
| RD-4 | 属评审台账措辞,不在 `design.md`,由实现方在对应 review 记录中更正 |
| B-NIT-1 / B-NIT-2 | 不在本 change 处理,仍按 change_46 约定在 P5 推送闸前关闭 |

RD-1/2/5/6 均为措辞或显式化,不改变已实现行为。

## 5. 实施与验证要求(给实现方)

- 新表 SQL 须在内存 SQLite 中实际执行,并验证 CHECK 约束对非法值的拒绝(遵守文末"凡写入设计的 SQL 须实际执行验证"的规定)。
- `check_design_doc.py` 对新版 `design.md` 须通过(含 §4.2 的编译期检查)。
- `generate_change_id_via_hook` 的测试使用测试替身 hook,不访问真实 Gerrit;真实 hook 文件由 FatTank 从 Gerrit 下载后在 config 中登记路径与 sha256。

## 6. 第一轮评审处置(2026-10-08)

收到两家:Claude Code(完整评审)、Kimi(文末 change_47 一节;该文件主体是另一份旧文档的评审,与本 change 无关,未采用)。ChatGPT 意见未收到。

| 来源 | 问题 | 严重程度 | 处置 |
|---|---|---|---|
| Claude Code 发现 1 | `hook_sha256`/`created_at` 写入未定义,命中时是否比对未定义;严格比对会在 hook 升级后卡死 | 重要 | 采纳 Claude Code 方案:写入时落库,命中时不比对,定为审计字段(§3.4 ⑤、§4.2) |
| Claude Code 发现 2;Kimi 第 1 点 | 只有"取或建"一个 API,只读路径遇空表会静默生成第二个 Change-Id | 重要 | 采纳并收紧:`generate` 可为 None;生成时机限定为"该 unit 尚无 DERIVE 事件时的 sandbox-submit",其余一律只读,未命中即 StateInconsistent(§3.4 ②③) |
| Claude Code 发现 5 | message 已含 `Change-Id:` 时标准 hook 原样保留,错误值会被缓存并推到别人的 change | 重要 | 采纳:生成前拒绝含 `Change-Id:` 行(不分大小写)的 message(§4.2 第 1 步) |
| Claude Code 发现 6 | 在业务仓库里执行 hook 会写对象库、受索引锁影响,且"不写仓库"不成立 | 重要 | 采纳:改在一次性临时 git 仓库中执行,显式开启 `gerrit.createChangeId`,环境白名单;另加一行 `X-Campaign-Submission-Key` 作 hook 输入,保证不同 submission_key 输入必然不同(该行不进最终 commit),替代 Claude Code 方案中"钉定身份日期"的思路,避免同输入撞号 |
| Kimi 第 3 点 | preflight 的 hook 检查项与"解释器为 .venv/bin/python"连写,易误读为同一检查 | 重要 | 采纳:改写措辞,注明 hook 以 `sh` 执行、与解释器检查无关 |
| Claude Code 发现 3 | submission_key 主键可为 NULL;hook_sha256 无格式约束 | 次要 | 采纳:NOT NULL + 64 位小写十六进制 CHECK;DoD 要求先用固定向量确认 `build_submission_key` 返回形态,不符即停 |
| Claude Code 发现 4 | created_at 无格式约束 | 次要 | 不采纳:既有表均无此约束,单独加会与既有写入口径不一致;仅注明 UTC ISO8601 |
| Claude Code 发现 7;Kimi 第 3 点次要项 | 超时后清理、退出码、CRLF、临时文件清理、正则未锚定;§4.2 与 §4.3 失败形态不对齐 | 次要 | 采纳:新进程组、超时 kill、要求退出码 0、锚定正则并 strip、finally 删除临时目录;§4.3 逐项对齐 |
| Claude Code 发现 8 | sha256 校验与执行之间可被替换 | 次要 | 采纳:校验过的字节复制到临时目录后执行副本 |
| Claude Code 发现 9 | 本文 §4 对 RD-1 的描述与实际不符 | 次要 | 采纳:已更正描述,并在 DoD 增边界用例 |
| Claude Code 发现 10;Kimi 附带 | `get_or_create_change_id` 位于 campaign_lifecycle 横幅之下 | 次要 | 采纳:移到横幅之前 |
| Kimi 流程备注 | 本文标"待评审",`design.md` 却已标 FROZEN | 次要 | 采纳:本文状态行注明入库前 FROZEN 标记不生效 |

## 7. 第二轮评审处置(2026-10-08)

收到三家:Codex、Claude Code、Kimi(本轮未收到 ChatGPT,第三家为 Codex)。三家均无阻断项。

| 来源 | 问题 | 严重程度 | 处置 |
|---|---|---|---|
| Codex 重要 1;Claude Code 发现 1 | 生成时机只靠调用方纪律,API 没有 `campaign_unit_key`,无法自查 DERIVE | 重要 | 采纳 Codex 方案(比 Claude Code 方案多了"生成后在写事务内重查",覆盖 hook 执行期间别的连接写入 DERIVE 的竞态):API 增 `campaign_unit_key`,未命中且已有 DERIVE 一律拒,插入前在 `BEGIN IMMEDIATE` 内重查 |
| Claude Code 发现 2 | 未排除"已有 DERIVE、无缓存行"的中间态,另一种合乎文字的实现顺序会把合法重跑打进 HELD 终态 | 重要 | 采纳:写入顺序不变式(缓存行先于首个 DERIVE),并在 sandbox-submit 契约中写明固定顺序 |
| Claude Code 发现 3;Kimi 发现一 | 临时仓库无 HEAD 是新依赖,替身 hook 测不出,preflight 只比 sha256 | 重要 | 两项都做:临时仓库建空初始 commit 消除依赖;preflight 用登记的真实 hook 冒烟一次;DoD 增真实 hook 冒烟与"未处理无 HEAD 的变体"负例 |
| Codex 重要 3 | 环境白名单传入调用方 HOME,全局 git 配置(如 `gerrit.reviewUrl`)会让 hook 生成 Link 而非 Change-Id | 重要 | 采纳:HOME/XDG_CONFIG_HOME 指向临时空目录,`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`;DoD 增配置隔离用例。**不采纳**其"`gerrit.createChangeId always`"建议:较旧版本 hook 以 `--bool` 读取该键,`always` 会解析失败;本流程消息模板固定以 `Fix build error` 开头,不会触发 `fixup!`/`squash!` 跳过逻辑,保持 `true` |
| Codex 重要 2;Claude Code 发现 4 | 拒绝已有 Change-Id 的正则大小写覆盖不全;未拒绝 Gerrit 身份 Link | 重要 | 采纳 Codex 方案:整键不分大小写,并拒绝 `/id/I<40hex>` 形式的 Link;普通 Link 不受影响 |
| Codex 重要 4;Claude Code 发现 8;Kimi 发现三 | EF-3 在 DAG、关键路径、Phase 1 目标/范围/DoD、文末版本与 EF 台账仍按"待实测"书写;本文第 2 节第 2 项仍写"实测结论" | 重要 | 采纳:全部同步;关键路径解除 P1→P2(P1 只阻塞 P5Q) |
| Claude Code 发现 7;Kimi 发现二 | DoD 缺生成时机、X-Campaign-Submission-Key 正控制与"不进最终 commit"、真实 hook 冒烟、环境隔离、sandbox 重推删行等用例 | 重要 | 采纳,逐条补入 Phase 2 DoD |
| Claude Code 发现 5 | `author_identity`/`committer_identity` 入参来源与格式未定义且非必需 | 次要 | 采纳 Claude Code 方案 A:删除两个入参,临时仓库本地 config 写死 `campaign` / `campaign@invalid` |
| Codex 次要 1;Claude Code 发现 6 | §4.3 未覆盖临时仓库准备、子进程启动、清理失败 | 次要 | 采纳:准备失败与启动失败归入 CHANGE_ID_HOOK_FAILED。清理失败两家意见相反,采用 Claude Code 方案(只记 WARN、不改变结果):临时目录在业务仓库之外、不含状态,残留无害;若改为失败,清理环境有问题时每次生成都会失败,反而卡住流程 |
