# P4.9 末终止批次设计(v1.31-FROZEN)

> **状态:FROZEN(2026-09-27,FatTank 批准)。** 交 Codex 按本稿实现。冻结后任何改动只走下面第 3 条的勘误流程。
> **已生效勘误:附录 C 勘误 1(2026-09-29,FatTank 批准)。** 勘误只追加在附录 C,不改动正文任何一行。
> **已生效勘误:附录 C 勘误 2(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 3(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 4(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 5(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 6(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 7(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 8(2026-10-07,FatTank 批准)。**
> **已生效勘误:附录 C 勘误 9(2026-10-07,FatTank 批准)。**
> 冻结前的放行规则(v1.27 起,留作记录):
> 1. **落地核对**:三家只核对最新修订段所列改动是否按所写落地、有无改到别处;**不开新的审查面**;
> 2. **放行标准只看"朝开"**:仅当发现**会导致删错真实依赖或删掉行为型测试**的问题才阻止冻结;
>    **"朝闭"问题**(某断言恒红、seal 不可达、实现方无法执行)**不阻止冻结** —— 它们在实现期会以红灯或
>    无法执行的形式立即暴露,本身不会造成错误删除;
>    **反例落在 §1.1"静态发现的残余边界"内的朝开问题也不阻止冻结** —— 该边界由删除后验证兜底,登记为实现期观察项;
> 3. **冻结后的问题走实现期停止-报告**:Codex 遇到规范自相矛盾、不可达或无法执行,**停下并报告**,
>    由设计方出勘误、FatTank 批准后写入冻结稿(与前七批的例外处理同一流程),**不回到整轮评审**。
>
> **分工**:设计方(Claude)出设计、审 Codex 的代码与证据;Codex 实现并运行全部代码;
> 三家外部评审审设计;FatTank 裁决冻结与放行。本稿不含实现代码
> (规范性伪代码、文法与 schema 示例不属于实现),不含设计方自跑的实测值。

- 阶段:**P4.9 的最后一批**;抽取阶段已 CLOSED(总账 `p49-extraction-phase-summary.md`)
- 权威并行:step-0 `v2.1`、skill-1 `v1.4`、skill-2 `v1.3`、skill-3 `v1.3.1`、
  skill-4 `v1.12.1`、skill-5 `v1.3.2`、skill-6 `v1.8`(均 FROZEN)
- **基线**:由 A₀ 脚本产出并登记于**附录 B-0**
- **性质:本批与前七批根本不同**——前七批铁律是"**零行为变更**",
  **本批是 P4.9 唯一允许行为变更的批次**,且受**终止条款**约束:
  5 项必须在本批关闭,**未完成即阻塞 P4.9 收口,不得转交**。


> **修订摘要**:v1.1 两表改脚本产出;v1.4 **admission→seal 两阶段**;v1.5 分母切 **`effective_inventory`** +
> **SEAL 清单**;v1.6 状态机 + 实测值禁令;v1.7 表示能力缺口 + 闭合调用图;v1.8 扫描完整性协议 + 可信叶子白名单 +
> 五分类 + OBS + 自我适用条款;v1.9 输入面外锚;v1.10 减法上界(元规则(五));v1.11 claim 两型分治 +
> 每 detector 正控制(元规则(六))+ `INDETERMINATE`;v1.12 claim 型别闸门 + `ledger_membership` 维度(元规则(七));
> v1.13 12 格全函数导出表 + 型别默认反转(元规则(八));v1.14 状态对象统一(§1.1c-0);
> v1.15–v1.17 台账粒度归一、召回默认反转、SEAL 阶段分层、`covers`/`primary_owner` 两关系分开;
> v1.18 七格全函数分类器、阶段列落地、事故 (54) 的 `SEAL-1` fixture 真改;
> v1.20 构造不变式提为标准化期独立断言;v1.14–v1.23 另为本稿自身建了一套文档自检机制(见下)。
>
> **v1.24 修订(FatTank 裁决)**:**整体移除本稿自身的文档自检机制** —— 元规则(九)、删文检查与冲突对账两个工具、
> hash 对象、断言③ 族、断言冻结、发版包与发版顺序、解冻谓词、工具规格(`p49-doccheck-spec-*` 作废)。
> 它只管"这份设计文档自己有没有写错",不是本批交付物,却成了冻结前置条件,最近六轮评审几乎全部耗在它上面。
> 本稿回到**人工修订纪律 + 三家评审**(§1.0a 末);§7 机制清单只保留五条 P4.9 本身的机制;
> DoD 删去全部文档自检条目;附录 B-13/B-14 撤销;事故台账保留作历史记录(新增 (119))。
> **五个事项(§1–§5)、§6 预期差异门禁与 A₀ 交付物的规范内容本版未改。**
>
> **v1.25 修订(第二十二轮:甲 3 BLOCKER + 4 MAJOR + 3 MINOR / 丙 3 BLOCKER + 5 MAJOR + 1 MINOR;
> 两家均判"补完即可冻结",问题全部落在五个事项与机制本身)**:
> **阻断**:①五类处置不互斥 —— ①②③ 的谓词补 `A=否` 前提(丙);②§5 作出裁决:**选 (B) 维持现状**,
> 写明两个中断时点的失败态,并在 §6 登记零差异(丙;甲同向);③§6 封闭场景清单与结果字段
> (丙);④`SEAL-16b` 五方覆盖补对账键与各方投影方式(甲);⑤被后代覆盖的祖先 key 补记账形式,
> 并明确不进 `SEAL-11` 的五元组核验(甲);⑥三条机制补 near-miss(两家)。
> **较重**:`SEAL-11` 与 DoD 的台账侧覆盖义务统一到七格分类器(两家);`SEAL-12b` 汇总门移到终局(丙);
> ④/⑤ 的代码动作写死(丙);A₀ 补 `private_consumption` 枚举器,commit A 补逐调用面验收(丙);
> `SEAL-16b` 与 `12b-12` 的分工写明(甲);附录 B-8 补分类器与监控量的记录字段(甲);
> §1.3 清零清单补三个阻塞态(甲)。**措辞**:删去对已撤销机制的规范性指向(两家);DoD 硬门条目去掉旧统计(甲);
> B-11 的 `SEAL-6` 违例改为三条(丙)。
>
> **v1.26 修订(第二十三轮 delta 核对:丙 4 BLOCKER + 1 MAJOR;甲本轮回传的是上一轮的旧文件,未计入)**:
> ①**消费者形态拆为十九个原子形态,每个形态一个 capability branch(一一对应)**,`SEAL-16b` 的对账键由此确定
> (上一版的"九形态表登记的分支"在 §1.1 并不存在,且第 5、6、7、8 类各含多种机制);
> ②**祖先 key 的覆盖须由有效后代承担**:覆盖它的 candidate 至少一个在 `preseal_effective_inventory` 内、
> admission 为 `NOT_REQUIRED`/`ADMITTED`;否则转第 4–6 格,生成普通台账侧 item;item 构造语义同步统一;
> ③**④ 私有化前须先处理外部消费者**:消费者集合须为 `CLOSED`,外部消费者按 ②/③ 同款动作处理完才删公开绑定;
> ④**`expected_diff.json` 按场景分两种模式**(`NO_DIFF` / `DIFF_SET`),§5 的零差异由此可表达;
> ⑤**protected marker 的观测补内容 hash 与读取方结果**,不完整 marker 进入封闭结果面。
>
> **v1.27 修订(第二十四轮:甲 4 BLOCKER + 1 MAJOR + 3 MINOR / 丙 4 BLOCKER + 1 MAJOR,两家均判"补完即可冻结")**。
> **更正**:v1.26 修订段称"甲本轮回传的是上一轮的旧文件,未计入",**这是设计方的误判** —— 甲当轮审的就是 v1.25,
> 其中 3 条(下面的 ①⑦⑧)因此漏了一轮,本版补上。两家本轮有两处同题(②③),合并处理。
> **阻断**:
> ①**维度 A 收归 §1.2 一处定义,改为全函数**:`#MODULE`/`#PROXY` → A=否,`#REEXPORT`/`#INLINE` 看有无 `Load`;
> fail-closed 只对 B(甲;v1.25 遗留 —— 原写法下整模块候选全部卡住,项 1 无法关闭);
> ②**capability branch 分命名空间**:消费者形态分支改名 `consumer.<形态 ID>`;`SEAL-16b` 只对账 `consumer.*`,
> `12b-12` 只对账其余命名空间(甲、丙同题;采用甲的命名空间写法 —— 与丙的 domain 字段等价,但不改 registry schema);
> ③**祖先 key 的有效覆盖改在 `SEAL-3` 之前完成**:admission 期分 A/B/C 三个固定子步骤,fallback item 在 `SEAL-3` 前取得终态;
> 分类器暂定用原始 `covers`、终态用 `effective_covers`(甲、丙同题;采用丙的写法 —— 甲的"追加一轮 admission 再重算
> `SEAL-3`"也可行,但会让已通过的断言回退,丙的写法不产生回退);
> ④**十九个原子形态改为互斥全分区**:谓词按 AST 字段、被调函数限定名、文件类别切分,函数名集合封闭、删去"等",
> 封闭集合外的调用 → `UNKNOWN_CAPABILITY`;加四条边界 near-miss(丙);
> ⑤**④ 处理外部测试消费者时先按 §2 三分**:行为型测试迁移保留,不再一律按 ② 删除(丙)。
> **较重**:⑥`expected_diff.json` 两种模式写死结构,禁止空 `DIFF_SET`,准入证伪由四条增至七条(丙);
> ⑦④ 的私有化动作按 `#REEXPORT` / `#INLINE` 分述(甲;v1.25 遗留);
> ⑧`SEAL-11` 不再在 disposition 期求值暂态清零,该项移入 §1.3 断言二(终局)(甲;v1.25 遗留)。
> **措辞**:§3 预期差异改用标记值写法并声明两个场景各取的模式(甲);`SEAL-8b` ① 与 §2 枚举器的"九形态"改指原子形态表(甲)。
> **未采纳**:无。
>
> **v1.28 修订(v1.27 落地核对:丙"可冻结";甲 2 条朝开,均出在 v1.27 ④ 新写的原子形态表)**:
> ①**进程启动族补全并纳入受监控集合**:`os.popen`/`os.exec*`/`os.spawn*`/`os.posix_spawn*`/`pty.spawn`/`asyncio` 子进程等补进 `C8a`/`C8b`
> 的封闭集合;`C8b` 改为"进程启动族中不匹配 `python -m` 的一切调用",无模块名时不产生消费边(甲 朝开-1;采用甲的补集合方案,
> 并按其副作用分析只监控 `os` 的进程启动类名字,不监控整个 `os`);
> ②**零命中改为阻塞**:参与点收窄为可机械枚举的候选参与点,每个须恰命中一个形态,零命中与多命中均 `UNKNOWN_CAPABILITY`;
> 另立**名字命中兜底**:按候选的模块名/路径在全部受版本控制文本文件中搜索,每处命中须有去处(某形态、第 9 类排除、或阻塞),
> `Makefile`/`Dockerfile` 等未登记文件中的命中一律阻塞(甲 朝开-2;甲的方案只按 `python`/`-m` 字面量兜底,
> 本版改按候选自身的名字兜底 —— 不依赖调用写法,覆盖面更全,且命中与具体候选直接关联)。
> 同步:`SEAL-16b` 投影⑤、`12b-10`、DoD、B-8 记录字段、B-11 正控制与 near-miss。
>
> **v1.29 修订(v1.28 落地核对:甲 2 条朝开 / 丙 2 条朝开;两家均确认 v1.28 两项已落地、无未申报改动)**。
> **先说判断**:v1.26 起连续四轮,每轮都有人找到一种新的"引用模块的写法"绕过静态发现。这不是谓词写错,
> 是静态枚举本身不可能对任意文本证明完整。本版因此做两件事:**把本轮四条全部修掉**,并**新增一道不依赖静态完整性的删除后验证**,
> 同时写明静态层承诺覆盖的范围;落在承诺范围以外(残余边界)的新反例由删除后验证兜底,不再阻止冻结。
> ①**解释器行兜底**(甲 朝开-1 反例 A):非 Python 文件中含解释器 token 的行都是参与点;模块位是变量或宏 → `DYNAMIC_UNRESOLVED`
> (按既有证据链销账、由 `SEAL-5` 计数);新增 `C7d` 承接 `Makefile`/`*.spec`/`Dockerfile` 等构建与打包文件。
> 采用甲的"与名字兜底并存"思路;甲把展开失败定为 `UNKNOWN_CAPABILITY`,本版改为 `DYNAMIC_UNRESOLVED` —— 后者有销账路径
> (变量在同一文件的定义点即闭合值域),前者只能扩表,而扩表解决不了宏展开;
> ②**受监控名字集合扩充**(甲 朝开-1 反例 B、C):补 `pkgutil`/`imp`/`zipimport`/`exec`/`eval`/`compile`;对受监控名字的裸读取
> (`f = importlib.import_module`)与 `sys.modules` 的任何访问都成为参与点,零命中即阻塞 —— 修复 v1.28 相对 v1.27 的覆盖面回退(采用甲的方案);
> ③**doctest 与 `-c` 载荷按 Python 源处理**(甲 朝开-2、丙 朝开-2):docstring 与 `*.md`/`*.rst` 中的 doctest 行、解释器行的 `-c` 载荷
> 解析为 Python 后套用全部规则,排除规则对它们不适用。甲建议"含 `>>>` 即阻塞",本版改为解析后按正常规则处理 ——
> 同样朝闭,但不会把合法 doctest 一律拦死;
> ④**名字形态补拆分导入 `from a.b import c`**(丙 朝开-2;采用丙的方案);
> ⑤**进程启动族按签名族提取命令载荷**(丙 朝开-1;采用丙的方案):`os.execve` 等不再统一取首参,位置不定即 `DYNAMIC_UNRESOLVED`;
> ⑥**新增"静态发现的残余边界与删除后验证"**(§1.1 末):删除按 shim 模块分组提交;删除后跑全量测试、运行时锚、import-all、
> 名字残留复扫、打包构建五项,任一失败即回退该组并走勘误;新增机制 `MECH_POST_DELETE` 及其控制;冻结规则第 2 条相应补一句。
> ⑦**受监控名字集合改为按用途列举**(设计方自查):v1.28 写"`unittest.mock`、`subprocess` 下的全部可调用对象",
> 会把测试中的 `MagicMock()`、`except subprocess.CalledProcessError` 一律拉成零命中而阻塞 —— 朝闭,但会让 seal 在真实仓库上不可达;
> 改为只收导入机制、打桩、进程启动三类名字;另明写 `monkeypatch` 按 fixture 形参名识别。
> 同步:原子形态计数(十九 → 二十)、`SEAL-8b` ①、§2 枚举器、§7 commit C 与 D、DoD、机制清单、B-8、B-11。
>
> **v1.30 修订(v1.29 落地核对:1 条朝开 —— 解释器从标准输入读取的代码没人看;①–⑦ 已确认落地、无未申报改动)**:
> ①**解释器的代码来源改为封闭四类**(`-m` 模块、`-c` 载荷、脚本文件、标准输入),每类要么静态解析为 Python 源,要么落 `DYNAMIC_UNRESOLVED`,
> 不存在第三种出路;stdin 中 heredoc 正文、here-string 字面量、`echo`/`printf`/`cat <受版本控制文件>` 管道上游按 Python 源解析,其余 stdin 来源一律未决。
> 采用评审方的方向;评审方的候选 diff 只补了 stdin,本版把四类写成封闭集合,并补上两处同型缺口:
> `python < 文件` 输入重定向、以非 `.py` 文件为脚本的情形;
> ②**Python 源里的进程启动调用同样适用**(设计方自查,同型):命令是解释器且读 stdin 时,只有 `input=` 为字符串常量才解析,
> `stdin=`、`communicate()`、`.stdin.write()` 等一律 `DYNAMIC_UNRESOLVED`。
> 同步:嵌入式片段定义、名字兜底去处、承诺覆盖范围、正控制(五条)、B-8 记录字段。
>
> **v1.31 修订 = 冻结版(v1.30 落地核对:丙 1 条 / 甲 2 条,均为承诺覆盖范围内的朝开;两家均确认 v1.30 ①② 已落地、无未申报改动)**。
> **记账更正**:v1.30 修订段写"1 条朝开",是因为上一轮转来的两段评审文本逐字相同(同一家贴了两次),甲对 v1.29 的两条从未送达设计方,
> 并非收到后漏记;甲本轮已重新提交,下面逐条记账。
> **逐家逐条**:
> - **丙 朝开-1(解释器选项参数被误认成脚本)· 采纳,方案扩写**:丙的候选只点名 `-W`/`-X`/`--check-hash-based-pycs`;
>   本版写成完整的封闭选项文法(无参字符集、带参字符、`-c`/`-m` 结束选项、短选项簇与紧贴写法、长选项),未知选项一律未决 ——
>   同时覆盖甲 朝开-2 反例 b 的 `-mpkg.mod` 紧贴写法;Python 侧进程启动 argv 适用同一文法。
> - **甲 朝开-1(`docs/` 按路径整体豁免)· 采纳甲的方案**:文档豁免改按类别判定 —— 只豁免 `*.md`/`*.rst`,
>   以及 `docs/` 下不属 `C7a`–`C7d` 任何类别、无可执行位、无 shebang 的文件;`docs/Makefile` 等按类别处理。
> - **甲 朝开-2(一行多命令只取一个;名字命中只记形态不产生消费边)· 采纳甲的方案**:引号外按 `&&`/`||`/`;`/`|`/换行切分命令,
>   每个解释器 token 各是一个参与点;名字命中在解释器命令内却未得到消费边 → `UNKNOWN_CAPABILITY`。
> 同步:`C8a` 谓词、代码来源(一)(二)(三)、正控制与 near-miss(八条)、B-8 记录字段。
> **冻结判断**:三条修改都落在解释器命令的解析规则内,不涉及其它小节;修改后解释器命令的每一种写法都有确定去处
> (消费边 / 第 9 类排除 / `DYNAMIC_UNRESOLVED` / `UNKNOWN_CAPABILITY`),且删除后验证在其后兜底。FatTank 批准以本版冻结。

---

## §0 ⑰ 跨批次复核(**结论为 claim,引 `OBS-1.*`**)

| 项 | 登记依据 | 复核结论(claim key) |
|---|---|---|
| 1 shim 删除 | step-0 §6.2 清单 | `OBS-1.item1-basis`;清单与计数由 `shim_inventory.py` 产出 |
| 2 测试私有件收窄 | skill-4 私有件 | `OBS-1.item2-scope`;清单由 `private_consumption.json` 产出 |
| 3 悬空 symlink | `tizen_gerrit_fetch/gerrit.py` 的源目录安全检查 | `OBS-1.item3-predicate`(锚点见 §3,SEAL-14 核验) |
| 4 timeout 统一 | skill-5 `v1.3.2` §3.2 映射表 | `OBS-1.item4-anchors`(锚点见 §4) |
| 5 marker 顺序 | `tizen_ci_shared/workspace` 的写入序 | `OBS-1.item5-order`(锚点见 §5) |

> *(早期版本曾在项 1/项 2 直接写出结论词并声称那是规范判断;**不成立**——
> 它们是"登记依据"与"当前树"的**比较型观测**,属 §8-2 类一,**禁止手填**。
> **按 §8-2 否定豁免,本版不复述那两个结论词本身。**)*

**复核纪律**:上表每项均须由实跑产出;**两项"依据/范围"类结论不得沿用登记时
的数字**(*历史记录,已否定*;**不得被任何条款引用为依据**,本版不复述其值)。

## §1 项 1:兼容位置分类(**表由脚本产出,本节只写生成规则**)

### 1.0 为何不在文档里维护该表
早期版本的表由人写 grep 产出,存在**三类盲区**(下列即其定义):①**目录范围**;
②**前缀撞名**;③**非 import 形态**(CLI 字符串字面量误判为消费者;
动态导入完全不可见)。
**故与 `expected_diff.json` 同一治法**:表由 `shim_inventory.py` 产出并存入
`shim_inventory.json`,**本设计稿不书写任何位置清单与计数**。

### 1.0a 八条元规则,与它们被绕过的十次

| 轮次 | 谁当权威 / 出了什么 | 漏了什么 |
|---|---|---|
| v1.1→v1.2 | **结构扫描**当权威 | **多**:A 类候选混入包根/入口 |
| v1.4 | **状态跃迁**当第三段权威 | **少**:"少"表现为"**该删的没删**" |
| v1.5 | **SEAL 清单**当完整性权威 | **少**:只断言"来源非零贡献" |
| v1.6 | **权威源声明**当发现面权威 | **少**:只证"声明集 = 解析集" |
| v1.7 | **扫描**当发现面权威 | **少**:只证"发现的都进了比对" |
| v1.8 | **`scan_manifest`** 当输入面权威 | **少**:manifest 锚回了文档清单 |
| v1.9 | 锚已外部化,**但减法仍是声明的** | **少**:三处收缩都能把发现面压回去 |
| v1.10 | **全部断言都在验"记账"** | **少**:**没有一条验"检出"** |
| v1.11 | **`type` 登记与排除标记效力成了新声明面** | **少**:承重 claim 登记为纯观测即零核验 |
| v1.12 | **写出了新规则,没让新规则与旧规则对账** | **矛盾**:新维度没和旧可达表对账(导出规则非全函数)、新 `12b-8` 没和旧 `12b-3b` 对账(相邻两行互斥)、新两型分治没和旧三条禁止对账(空 predicate 真空绿) |


> **元规则(一)**:任何"**以 X 为权威**"的设计,都必须再问一句——
> "**X 是怎么生成的?它的生成规则漏什么?**"
> 旧权威的毛病是"**多**",新权威的毛病是"**少**";"少"因为**分母是它自己**
> 而天然不可见。
>
> **自我适用条款**:
> > **(前半)** 凡在某一版中被提拔为权威的机制,**必须在同一版内为它配一条
> > "生成规则完整性"断言**,否则该提拔**不得进入 DoD**。
> > **(后半)** 而那条断言**必须锚到一个不需要任何声明的外部事实**。
> > **凡是锚到另一份文档的,都只是把回归往后推一格。**
> > **(第三段,v1.14 新增)** 凡在某一版中新立的**检查器/对账器**,
> > **必须在同一版内自带构造式正控制**(注入一个已知应被捕获的实例),
> > 否则它的"已跑过"只是叙述——**元规则(六)对检查器自身同样适用**。
>
> **元规则(二)**:**基于单一维度变化的枚举,看不见其他维度上的变化。**
> **推论**:**凡以"变化"为判据者,必须显式声明它观测的是哪个维度**
> (维度全表见 §1.1b),并列出**该维度恒定而其他维度变化**的情形由谁承担。
>
> **元规则(三)**:"**文档零手填**"不能只堵实现方——**评审方口头给出的结论
> 同样只有信任兜底、没有 hash 兜底**。
> **v1.13 的第二次实证**:v1.12 的 `12b-8` 中那句 *(引号内为**已否决措辞**,
> 不再是本稿声明)* "唯一效力 = 例外凭证",**源自评审方答问时自补的推论而非
> 被审原文,且方向反了**;汇总方直接采纳,与未改动的 `12b-3b` 撞成矛盾。
> **教训**:**评审方的结论与实现方的产出同样须回到被审原文核对**,
> 否则"异构交叉评审"本身会成为新的单点信任。条款见 **§8-2**;
> **对账手段见元规则(八)**。
>
> **元规则(四)**:
> > **台账是"候选权威";扫描是"独立发现源"。两者互不裁剪——
> > 输出侧不得过滤,输入侧不得派生,candidacy 侧不得被任何标记抑制。**
> *(v1.14 措辞同步:原文写"不得被排除规则抑制";自 v1.13 起该标记
> **不产生任何豁免**,本版更名为 `NON_SHIM_PREDICTION`,措辞相应泛化为
> "任何标记",**义务不变、覆盖面更宽**。)*
>
> **元规则(五)**:
> > **凡从外部锚上做减法者,每条减法规则必须自带一个机械上界
> > ("它不可能减掉什么"),否则减法就是新的声明面。**
> **适用边界**:**不做减法者不受本条约束**——
> `NON_SHIM_PREDICTION` 自 v1.13 起**不产生任何豁免**,故**不是减法,
> 无需上界**(见 12b-8)。
> **v1.14 新增适用对象**:**`MEASUREMENT` 豁免清单是默认反转之后唯一的收窄面,
> 受本条约束**,其机械上界见 §8-2(清单基数 = 逐字点名数)。
>
> **元规则(六)**:
> > **记账断言只能证明"该看的都看了",不能证明"看了就能看出来"。
> > 凡新增任何探测器或判据,必须为它的【每一个 capability branch】各配一条
> > "应当发现的已知实例"正控制——方法论 ⑱ 必须下沉到分支级。**
>
> **元规则(七)**:
> > **同源重算不能自证。** 凡"重算结果与记录一致"型断言,
> > **若其判据实现与被验对象同源**,则判据本身写错时**产出与重算会一致地错、
> > 双绿**。此类断言**必须另配"外部已知答案"控制**,其期望结论为**规则常量**,
> > **不得由判据实现产出**,且**须以外部可观察的终态表达,不得复述判据的
> > 内部中间变量**(否则异源性被打折)。
>
> **元规则(八)**:
> > **规则之间的一致性本身是新的声明面。**
> > **凡改写一条规范行,必须机械列出全文中【引用同一对象】的其它规范行,
> > 逐条标注"一致 / 已同步改 / 本轮不改及理由";未对账即文本事故。**
> **对账方式(v1.24 改为人工)**:"引用同一对象"以**共享同一个编号或具名对象**(`SEAL-*`、`12b-*`、
> `E*`/`R*`、状态取值名、字段名等)为准;**只对【本轮被改写的】规范行生效**;
> 由设计方在变更块中逐条列出并标注,评审方复核。
>
> **修订纪律(v1.24 起为人工纪律)**:
> - **删文方向**:每次版本递进,变更块须申报删去或改写了哪些规范句、改到了哪里;
>   **无申报的删除即文本事故**;评审方对照上一版复核。
> - **冲突方向**:改写一条规范行时,按元规则(八) 列出引用同一对象的其他规范行并逐条对账。
> - **变更块 → 正文**:变更块里每条"已修 / 已改 / 已立",须在正文有对应的规范句;只写在变更块里的义务无效。
>
> *(v1.24 注:v1.14–v1.23 为本稿自身建了一整套机械自检 —— 元规则(九)、删文检查与冲突对账两个工具、
> hash 对象、断言③ 族、断言冻结、发版包与工具规格。**它们只管"这份设计文档自己有没有写错",
> 不是本批的交付物**,却成了冻结的前置条件,使最近六轮评审几乎全部花在它上面。
> **v1.24 按 FatTank 裁决整体移除**,本稿回到"人工修订纪律 + 三家评审"。相关事故保留在 §8-1 台账作历史记录。)*

### 1.1 枚举器规格(台账为候选权威,扫描为独立发现源)

1. **初始候选集 = 冻结台账,三段构成**:
   - **第一段**:step-0 §6.2 shim account,**逐条标注时效**(依据见
     `OBS-2.seg1-staleness`);**冻结不得固化过期否定项**;
   - **第二段**:各批 closeout 的 shim 相关条目——**贡献形态与可用性由
     `OBS-2.seg2-form` 产出**,**其结论决定本段是否可作覆盖面依据**;
   - **第三段**:各批**实际抽取提交**所创建的旧址整模块 shim,规格见 §1.1b;
   **provenance**:每条须记录**贡献文档 + 版本/hash + 批次 + 导出方式**;
   缺任一字段即阻塞 seal(SEAL-2)。
   **贡献者全集断言**:三段并集须覆盖 **step-0 + skill-1…6 共七个来源**;
   **完整性由 SEAL-1、SEAL-12、SEAL-12b 三者共同保证**,缺一即有死角。
   **台账 key 的粒度(v1.15 改写;甲 BLOCKER-2、丙 MAJOR)**:
   **台账 key 保持【来源自身声明的粒度】**,使用 §1.1c 的四种 ID 格式书写
   ——**整模块义务只能映射 `#MODULE`,不得被强制伪展开为若干 binding**。
   > **v1.14 曾要求"三段均须展开到 binding 级",【无法成立】**:三段的可用锚
   > 不对称——第三段有"实际抽取提交 SHA",**第一、二段的 provenance 只有文档
   > 版本/hash,没有代码快照**;于是**用当前树展开 → 台账 key 派生自扫描面 →
   > 撞元规则(四)"输入侧不得派生";不展开 → 第一、二段全量
   > `SOURCE_OBLIGATION_UNENUMERABLE` → seal 不可达**;剩下的只有
   > "实现者自选展开基准"。**粒度归一(见 §1.1c-0 的 π)使展开不再必要。**
   **`SOURCE_OBLIGATION_UNENUMERABLE` 的适用面随之收窄**:仅用于
   **来源连【它自己声明的粒度】都无法机械枚举**的情形;
   **且须先走时序出口**(见 §1.1c-0 末)。
2. **扫描 = 独立发现源**(元规则(四)):输入面锚定版本控制的**完整 tree**、
   **不做减法**(12b-1);**其每一项都必须进入 reconciliation**(SEAL-12,
   **`NON_SHIM_PREDICTION` 条目一视同仁**);**扫描自身须先证明完整**(SEAL-12b)
   **且须先证明有检出能力与判定正确性**(12b-10 / 12b-11);
   **reconciliation 逐项产出**(§1.1c)。
   **扫描须按四级粒度全部产出候选,不只模块级**——类别 (e) **无 admission
   兜底**,全靠这条总义务;**降格为脚本职责列举即等于取消该义务**
   (v1.15 恢复理由句:**降格之后,实现者按模块级扫描【不违反任何明文规范】**
   ——这正是"义务"与"职责描述"的区别)。
3. **消费者扫描面**:**全部 manifest 条目**——含 `tests/**`、打包配置、
   CI 配置、脚本入口、shell/argv 承载物。

**结构特征**:
- **A 纯兼容模块**:零 `def`/`class` 且存在跨模块兼容 import,**且不是包入口**
  (§1.2a);**满足 A 仍不足以判为 shim——须同时在台账内或经 admission 裁决**;
  **A 是模块级判据**,结构上**看不见**已 shim 模块内新增的绑定与代理 callable;
- **B 内联兼容引用**:含 `P4.9 shim` 注释,或 `import X as X` 同名别名;
  **满足结构特征仍须在台账内或经 admission 裁决**;
- **D 代理委托**:见 §1.1c 粒度④。

**消费者判定(九种形态,缺一即盲区;v1.26 起以下方"原子形态表"为权威)**:
1. `from X import ...` / `import X`(**须词边界匹配**,消除前缀撞名);
2. **`importlib.import_module("X")`**,含 **f-string / 变量拼接**
   ——**不可静态解析者一律落 `DYNAMIC_UNRESOLVED`,不得静默略过**
   (该分流义务丢失后,detector 解析不了时可静默跳过,
   **消费者漏检 → 误判为"零消费者可直接删" → 删错方向且无断言会红**);
3. `monkeypatch.setattr("X.attr", ...)` 等**字符串目标**;
4. **包 + 子模块 alias**;
5. **相对 import**、`__import__`、`runpy.run_module`、`importlib.util`、
   `sys.modules[...]`;
6. **对象式 patch / 属性操作**:**`monkeypatch.setattr(module_obj, "_name", …)`**、
   `patch.object`、`setattr`/`delattr`、**`getattr(module, name_var)` 变量驱动**;
7. **打包与入口**:`[project.scripts]`、CI 配置、shell 命令中的模块入口;
8. **`-m` 与 subprocess argv**;
9. **排除**:CLI 提示语、docstring、注释中的模块名字面量
   ——**判据:该字符串是否出现在 import/patch/argv 语义位置**。

**原子形态表(v1.26 立;v1.27 改为互斥全分区)** —— 上面第 1–8 类拆成原子形态(v1.26 十九个,v1.29 增 `C7d` 为二十个);第 9 类是排除规则,不是消费者形态。
**每个原子形态恰对应一个 capability branch,branch 名 = `consumer.<形态 ID>`(一一对应,capability registry 不得合并或拆分)**;
**`consumer.*` 是消费者形态分支的专用命名空间**,registry 中其余分支(`ledger.*` / `scan.*` / `resolve.*` / `provider.*`,
见 §1.1b 九类表与 `12b-10`)**不属于本表**;registry 中每个分支**恰属这五个命名空间之一**,前缀不在其中即红。
新增形态须先入本表再入 registry。`SEAL-16b` 五方对账、`12b-10` 逐形态正控制均以本表为准。

**互斥全分区(v1.27;丙 BLOCKER-1)**:**先按文件类别分流**(Python 源 → C1–C6d、C8a、C8b;非 Python 文件 → C7a–C7d),
**再按下表谓词判定;谓词按构造两两不相交**。
**参与点(v1.28 收窄为可机械枚举的候选参与点;甲 朝开-2)**:
> **Python 源**:①`Import`/`ImportFrom` 的每个 alias 项;②被调函数解析到**受监控名字集合**的每个 `Call`;
> ②′**对受监控名字集合中任一名字的每个非调用读取**(如 `f = importlib.import_module`;v1.29 补,甲 朝开-1 反例 C)
> —— 没有形态承接裸读取,故按下条零命中 → `UNKNOWN_CAPABILITY`;
> ③以 `sys.modules` 为对象的**任何**下标访问、属性访问(含方法调用,如 `sys.modules.update`)与 `in`/`not in` 比较
> (v1.29 由"下标与比较"扩为"任何访问";`C5e` 封闭集合外的访问即零命中);
> ④调用内建 `setattr`/`delattr`/`getattr`/`hasattr` 且首参解析为模块对象 binding 者。
> **嵌入式 Python 片段按 Python 源处理(v1.29;丙 朝开-2、甲 朝开-2)**:docstring 与 `*.md`/`*.rst` 中的 **doctest 行**
> (以 `>>> ` 或 `... ` 开头的行,去掉提示符后拼成代码块)、任何文件中**解释器行**按"代码来源四类"(见下"解释器行兜底")解析出的
> `-c` 载荷、脚本文件与 stdin 载荷(v1.30 补后两者)、以及 Python 源中进程启动调用经 `input=` 传入的字符串常量载荷(见 `C8a` 下的载荷提取),
> 均按 Python 源解析并套用本节全部规则(含 ①–④ 与名字命中兜底);**解析失败 → `UNKNOWN_CAPABILITY`**。
> **非 Python 文件**:①**解释器行**(见下"解释器行兜底")每行一个参与点;②**名字命中兜底**(见下)产出的每一处命中。
> **受监控名字集合**(v1.29 重写为按用途列举;甲 朝开-1 反例 B)=
> **(导入机制)**`importlib`(含其全部子模块)、`runpy`、`pkgutil`、`imp`、`zipimport` 下的全部可调用对象,内建 {`__import__`, `exec`, `eval`, `compile`};
> **(打桩)**`unittest.mock` 下的 {`patch`, `patch.object`, `patch.dict`, `patch.multiple`},以及 `monkeypatch.setattr`/`monkeypatch.delattr`;
> **(进程启动)**进程启动族全体(见 `C8a`),以及 `os` 下名字以 `system`、`popen`、`exec`、`spawn`、`posix_spawn` 开头的可调用对象。
> **不在集合内**的同模块名字(如 `unittest.mock.MagicMock`、`subprocess.CalledProcessError`、`subprocess.PIPE`)不是参与点
> —— v1.28 写"`unittest.mock`、`subprocess` 下的全部可调用对象",会把测试里的 `MagicMock()` 与 `except subprocess.CalledProcessError` 全部拉成零命中而阻塞。
> **每个参与点须恰命中一个形态:命中 0 个或多于 1 个 → `UNKNOWN_CAPABILITY` 阻塞(fail-closed)**,
> 不得按"未命中即无消费"处理,也不得归入最近的形态。
**下表中的函数名集合都是封闭集合**(属类三·规则常量),**不含"等"**;受监控名字集合中不在任何形态封闭集合内的调用与读取,
按上一条即为零命中 → `UNKNOWN_CAPABILITY`。函数名按 import binding 解析为限定名后比较,不按字面文本比较;例外:`monkeypatch.*` 按 pytest fixture 形参名 `monkeypatch` 及 `pytest.MonkeyPatch` 实例识别(v1.29 明写)。
**解除 `UNKNOWN_CAPABILITY` 的唯一途径是扩表**:按冻结稿勘误流程新增原子形态及其 `consumer.*` 分支与正控制,不得逐条人工放行。

**名字命中兜底(v1.28;甲 朝开-1/朝开-2)** —— 谓词覆盖不到的写法不能等价于"不存在":
> 对每个 candidate 生成**名字形态**:①点分模块名(`a.b.c`;binding 级候选另加 `a.b.c.<name>`);②源文件路径(`a/b/c.py`);
> ③包目录路径(`a/b/c/`);④**拆分导入形态**(v1.29;丙 朝开-2):`from a.b import c`(binding 级候选为 `from a.b.c import <name>`),
> 匹配允许任意空白、括号、逗号列表与 `as` 别名。
> 在 `scan_manifest` 的**全部受版本控制文本文件**中搜索(①–③ 按词边界:前一字符不属 `[A-Za-z0-9_.]`,后一字符不属 `[A-Za-z0-9_]`,
> 后跟 `.` 的子模块写法同样计为命中)。二进制文件跳过并逐个记入 B-8。每一处命中必须恰有一个去处:
> - **已被某个参与点分类的** → 按该形态计;
> - **位于 doctest 行、`-c` 载荷、stdin 载荷或脚本文件内的** → 已按上文"嵌入式 Python 片段"作为 Python 源处理,**不适用下面任何排除**(v1.29;v1.30 补后两者);
> - **Python 源中未被分类的字符串常量命中**:位于**排除位置封闭集合**{docstring 中的非 doctest 行;`print`、`logging` 记录方法、`warnings.warn` 的实参;
>   `argparse` 的 `help`/`description`/`epilog` 关键字实参;`raise` 语句所构造异常的实参}→ 按第 9 类排除并记入 B-8;否则 → `UNKNOWN_CAPABILITY`;
>   注释不是 AST 节点,按构造属第 9 类;
> - **非 Python 文件中的命中**:位于某条解释器命令内、**且该命令的代码来源判定已对该名字产生消费边**的 → 按该命令的形态计;
>   **位于解释器命令内、但代码来源判定未对该名字产生消费边的 → `UNKNOWN_CAPABILITY`**(v1.31;甲 朝开-2,不得只记形态);
>   位于**文档文件**的非 doctest 行 → 按第 9 类排除并记入 B-8;**其余一律 `UNKNOWN_CAPABILITY`**。
>   **文档文件(v1.31 按类别而非路径判定;甲 朝开-1)** = 扩展名为 `*.md`、`*.rst` 的文件,以及 `docs/` 下**既不属 `C7a`–`C7d` 任何文件类别、
>   又无可执行位且无 shebang** 的文件;`docs/Makefile`、`docs/*.mk`、`docs/*.sh`、`docs/*.spec` 等一律按其类别处理,**不因路径豁免**。
> 兜底命中清单(文件、位置、名字形态、去处)逐条落 B-8,**空记录即红**(无命中须显式记零)。

**解释器行兜底(v1.29;甲 朝开-1 反例 A)** —— 名字兜底只抓"名字是字面量"的引用;"调用写法是字面量、名字是拼出来的"须另有一路,两路并存:
> **解释器 token**(封闭):去掉路径前缀后完全匹配 `python[0-9.]*` 的 token;或完全匹配
> `^(\$\(|\$\{|%\{)[A-Za-z0-9_]*python[A-Za-z0-9_]*[)}]$`(不区分大小写,覆盖 `$(PYTHON)`、`${PYTHON3}`、`%{__python3}` 等)的 token;或 `$PYTHON`。
> `scan_manifest` 中**全部非 Python 文本文件**(文档文件的非 doctest 行除外,按第 9 类记入 B-8;文档文件的定义见名字命中兜底)先做**命令切分**:
> 按续行(行尾 `\`)合并后,在**引号外**按 `&&`、`||`、`;`、`|`、换行切成单条命令(引号内的这些符号不切分,属类三·规则常量);
> **每条命令中的每个解释器 token 各是一个参与点**(v1.31;甲 朝开-2:一行多条命令不再只取一个)。
> **解释器选项文法(v1.31;丙 朝开-1、甲 朝开-2 反例 b)** —— 先按下列封闭文法消费解释器选项,**再**确定代码来源,不得凭"第一个非选项 token"猜测:
> > 从解释器 token 之后逐个读取:`--` 结束选项;单独的 `-` 表示 stdin;以 `-` 开头的短选项簇逐字符处理 ——
> > 无参字符 {`b`, `B`, `d`, `E`, `h`, `i`, `I`, `O`, `P`, `q`, `R`, `s`, `S`, `u`, `v`, `V`, `x`, `?`} 不消费参数;
> > `W`、`X` 取簇内剩余字符为参数,簇内无剩余则取下一个 token;
> > `c`、`m` 同样取簇内剩余字符或下一个 token 为参数(故 `-mpkg.mod` 等价于 `-m pkg.mod`、`-Bm pkg.mod` 亦然),**并结束选项解析**;
> > 长选项 `--check-hash-based-pycs` 取 `=` 后的值或下一个 token;`--help`、`--version` 不消费参数;
> > 选项结束后的第一个 token 即脚本位(为 `-` 则是 stdin),其后均为脚本参数。
> > **未知的短选项字符或长选项、选项缺参数、选项或其参数含未展开的变量/宏 → `DYNAMIC_UNRESOLVED`,不得猜测脚本位。**
> > 本文法同样适用于 Python 源中以解释器为命令的进程启动调用的 argv。
> **代码来源(v1.30 改为封闭四类;丙 朝开 stdin)** —— 解释器执行的代码只可能来自下列四类之一,**每类要么静态解析为 Python 源,
> 要么落 `DYNAMIC_UNRESOLVED`,不存在第三种出路**(按构造不会再有"解释器行存在、但其执行的代码没人看"的情形):
> > **(一)`-m` 模块**:按上述文法取得的 `-m` 参数 → 与各 candidate 名字形态比对,命中即消费边;
> > **(二)`-c` 载荷**:按上述文法取得的 `-c` 参数,按 Python 源解析(见上文嵌入式片段);
> > **(三)脚本文件**:按上述文法取得的脚本位(不为 `-`),或 `< <路径>` 输入重定向 → 该文件按 Python 源解析
> > (受版本控制的 `.py` 文件本已作为 Python 源扫描,此处只记关联;其它扩展名的受版本控制文本文件在此按 Python 源解析;不在版本控制内 → `DYNAMIC_UNRESOLVED`);
> > **(四)标准输入**:脚本位为 `-` 或缺省(无 `-m`、无 `-c`、无脚本文件)时,代码来自 stdin。
> > **静态可界定**的 stdin 载荷按 Python 源解析:heredoc(`<<X`、`<<-X`、`<<'X'`、`<<"X"`)的正文;here-string(`<<<`)的字面量;
> > 管道上游为 `echo`/`printf` 字面量或 `cat <受版本控制文件>` 者。
> > **不带引号定界符的 heredoc 正文含 `$`、反引号或 `%{` 时,按展开规则处理,含未展开部分 → `DYNAMIC_UNRESOLVED`**;
> > 其余任何 stdin 来源(上游为其它命令、变量、命令替换、文件不在版本控制内)→ `DYNAMIC_UNRESOLVED`。
> 上述任一类的 token 或载荷**含未展开的变量、宏或命令替换(`$`、`%{`、反引号)→ `DYNAMIC_UNRESOLVED`**,按既有六字段证据链销账
> (非 Python 文件的"闭合值域证明"= 该变量/宏在同一文件或其显式 include 中的全部定义点;不可得即保持未决),**由 `SEAL-5` 与 §1.3 断言二计数**;
> (一)(三)中静态展开后不属任何 candidate 名字形态者不产生消费边并记 B-8。
> 解释器行所在文件不属 `C7a`–`C7d` 任一类 → `UNKNOWN_CAPABILITY`。

| 形态 ID | 所属类 | 识别谓词(互斥) |
|---|---|---|
| `C1` | 1 | `Import` 的 alias 项且**无** `asname`;或 `ImportFrom` 且 `level == 0` |
| `C4` | 4 | `Import` 的 alias 项且**有** `asname`(含 `import pkg.sub as alias`) |
| `C5a` | 5 | `ImportFrom` 且 `level > 0` |
| `C2a` | 2 | 调用 `importlib.import_module`,首参为字符串常量 |
| `C2b` | 2 | 调用 `importlib.import_module`,首参不是字符串常量 → 一律 `DYNAMIC_UNRESOLVED` |
| `C3` | 3 | 调用 {`monkeypatch.setattr`, `monkeypatch.delattr`, `unittest.mock.patch`, `unittest.mock.patch.dict`, `unittest.mock.patch.multiple`},**首参为字符串常量**;`unittest.mock.patch` / `.dict` / `.multiple` 首参不是字符串常量 → 落 `DYNAMIC_UNRESOLVED`,形态仍记 `C3` |
| `C6a` | 6 | 调用 {`monkeypatch.setattr`, `monkeypatch.delattr`},**首参不是字符串常量** |
| `C6b` | 6 | 调用 `unittest.mock.patch.object` |
| `C5b` | 5 | 调用内建 `__import__` |
| `C5c` | 5 | 调用 `runpy.run_module` |
| `C5d` | 5 | 调用 {`importlib.util.find_spec`, `importlib.util.spec_from_file_location`, `importlib.util.spec_from_loader`, `importlib.util.module_from_spec`, `importlib.util.resolve_name`} |
| `C5e` | 5 | 对 `sys.modules` 的下标访问(读/写/删)、调用 {`sys.modules.get`, `sys.modules.pop`, `sys.modules.setdefault`}、或 `in` / `not in` 比较右侧为 `sys.modules` |
| `C6c` | 6 | 调用内建 {`setattr`, `delattr`},首参解析为模块对象 binding |
| `C6d` | 6 | 调用内建 {`getattr`, `hasattr`},首参解析为模块对象 binding;第二参为字符串常量 → 按静态属性访问解析,否则 → `DYNAMIC_UNRESOLVED` |
| `C8a` | 8 | 调用**进程启动族**,argv(或命令串)按解释器选项文法(见解释器行兜底)规范化后**匹配 `<python> -m X`**(含 `-mX`、`-Bm X` 等紧贴与组合写法;v1.31)。**进程启动族**(v1.28 补全;甲 朝开-1)= {`subprocess.run`, `subprocess.call`, `subprocess.check_call`, `subprocess.check_output`, `subprocess.getoutput`, `subprocess.getstatusoutput`, `subprocess.Popen`, `os.system`, `os.popen`, `os.execl`, `os.execle`, `os.execlp`, `os.execlpe`, `os.execv`, `os.execve`, `os.execvp`, `os.execvpe`, `os.spawnl`, `os.spawnle`, `os.spawnlp`, `os.spawnlpe`, `os.spawnv`, `os.spawnve`, `os.spawnvp`, `os.spawnvpe`, `os.posix_spawn`, `os.posix_spawnp`, `pty.spawn`, `asyncio.create_subprocess_exec`, `asyncio.create_subprocess_shell`} |
| `C8b` | 8 | 调用进程启动族,**不匹配 `<python> -m X`**(含一切其它命令);消费边从 argv 中的模块名或 `.py` 路径提取(如 `python path/X.py`、`python -c "import X"`),**argv 中无模块名或路径 → 该参与点不产生消费边,但照常记入 B-8**;argv 无法静态规范化 → `DYNAMIC_UNRESOLVED`,形态仍记 `C8b` |
| `C7a` | 7 | 非 Python 文件:`pyproject.toml` 的 `[project.scripts]` / `[project.gui-scripts]` / `[project.entry-points.*]`,`setup.cfg` 的 `[options.entry_points]` |
| `C7b` | 7 | 非 Python 文件:CI 配置文件(文件集合 = `scan_manifest` 中 kind 为 CI 配置的条目)中的模块入口 |
| `C7c` | 7 | 非 Python 文件:shell 脚本(`*.sh`,或 shebang 为 sh/bash 的无扩展名文件)中的模块入口;**不含 Python 源中的 subprocess 调用**(那归 `C8a`/`C8b`) |
| `C7d` | 7 | 非 Python 文件:构建与打包文件 {`Makefile`, `GNUmakefile`, `*.mk`, `*.spec`, `Dockerfile`, `*.service`, `tox.ini`} 中的解释器行(v1.29 新增;甲 朝开-1、丙 朝开-2 的 `Makefile`/`.spec` 反例) |

**进程启动族的命令载荷提取位置(v1.29;丙 朝开-1)** —— 按签名族取,**不得统一取首参**:
> `subprocess.run`/`call`/`check_call`/`check_output`/`Popen`:`args`;`subprocess.getoutput`/`getstatusoutput`、`os.system`、`os.popen`、
> `asyncio.create_subprocess_shell`:`cmd`/`command`(命令串,按 shell 规则切分);`os.execl*`:`path`/`file` 之后、环境映射之前的剩余位置参数;
> `os.execv*`:`args`;`os.spawnl*`:`mode`、`path`/`file` 之后、环境映射之前的剩余位置参数;`os.spawnv*`:`args`;
> `os.posix_spawn`/`os.posix_spawnp`:`argv`;`pty.spawn`:`argv`;`asyncio.create_subprocess_exec`:`[program, *args]`。
> `subprocess` 族带 `shell=True` 时 `args` 按命令串处理。**参数位置、关键字绑定或展开结果无法静态确定 → `DYNAMIC_UNRESOLVED`,
> 不得落 `C8b` 的"无消费边"分支**;载荷中的 `-c` 代码按 Python 源处理(见上文嵌入式片段)。
> **命令是解释器时,其执行的代码同样按"代码来源四类"判定**(v1.30,与解释器行兜底同一规则):`-m`、`-c`、脚本文件照上;
> 脚本位为 `-` 或缺省(读 stdin)时,**只有 `input=` 关键字实参为字符串常量(含相邻字面量拼接)才按 Python 源解析**;
> `input=` 为非常量、经 `stdin=` 传入、经 `Popen(...).communicate(...)` 或 `.stdin.write(...)` 写入、或无法确定者 → 一律 `DYNAMIC_UNRESOLVED`。

**互斥性的构造依据**:`C1`/`C4`/`C5a` 按 AST 节点类型与 `asname`/`level` 两个字段分割;调用类形态按**被调函数的限定名**分割,
同名函数(`monkeypatch.setattr`)再按首参是否字符串常量分割到 `C3`/`C6a`,进程启动族再按是否匹配 `<python> -m X` 分割到 `C8a`/`C8b`;
`C7*` 只取非 Python 文件,四者按文件类别分割。**边界 near-miss 并入 B-11 `MECH_FIVE_WAY` 组**:
`import pkg.sub as a`(只落 `C4`)、`from . import X`(只落 `C5a`)、`subprocess.run([sys.executable, "-m", "X"])`(只落 `C8a`)、
`monkeypatch.setattr(mod, "x", v)`(只落 `C6a`)、`subprocess.run(["gbs", "build"])`(只落 `C8b`、不产生消费边)、
`README.md` 中提到模块名(非 doctest 行,按第 9 类排除)、`*.spec` 中 `BuildRequires: python3-devel`(无解释器 token,不成参与点)
—— **各须恰命中一个去处且不红**。
**正控制(v1.28 立、v1.29 补)**:`os.popen("python -m <sentinel>")` → 须落 `C8a` 并产生消费边;
`os.execve(sys.executable, [sys.executable, "-m", "<sentinel>"], env)` → 须从第二参提取并落 `C8a`;
`Makefile` 中 `python -m <sentinel>` → 须落 `C7d` 并产生消费边;`*.spec` 中 `%{__python3} -m pkg.%{suffix}` → 须 `DYNAMIC_UNRESOLVED`;
`Makefile` 中 `python -c 'from a.b import <sentinel>'` → 须产生消费边;docstring 中 `>>> from <sentinel> import f` → 须产生消费边、不得被排除;
`f = importlib.import_module`(裸读取)→ 须 `UNKNOWN_CAPABILITY`;`sys.modules.update({...})` → 须 `UNKNOWN_CAPABILITY`;
`pkgutil.resolve_name(...)`、`importlib.reload(<sentinel>)`(受监控集合内、不在任何形态)→ 须 `UNKNOWN_CAPABILITY`;
未登记文件类别(如 `*.bat`)中的解释器行 → 须 `UNKNOWN_CAPABILITY`;**(v1.30)**`Makefile` 中 `python - <<'PY'` heredoc 正文含 `importlib.import_module("<前半>." "<后半>")` → 须解析载荷并产生消费边;here-string `python - <<< "import <sentinel>"` → 须产生消费边;`some_cmd | python -` → 须 `DYNAMIC_UNRESOLVED`;`subprocess.run([sys.executable, "-"], input="import <sentinel>")` → 须产生消费边;`subprocess.run([sys.executable], stdin=f)` → 须 `DYNAMIC_UNRESOLVED`;**(v1.31)**`python -W ignore scripts/check`(`scripts/check` 为无扩展名受版本控制文件,内含 `importlib.import_module("<前半>." "<后半>")`)与 `subprocess.run([sys.executable, "-W", "ignore", "scripts/check"])` → 须以 `scripts/check` 为脚本位并产生消费边,不得把 `ignore` 当脚本;`python -m<sentinel>` → 须落 `-m` 并产生消费边;`Makefile` 同一行 `python -m <a> && python -m <b>` → 须两个参与点、两条消费边;引号内的 `"x && y"` 不切分(near-miss);`docs/Makefile` 中 `python -m <sentinel>` → 须落 `C7d` 并产生消费边,不得按文档排除;`python --unknown-opt x.py` → 须 `DYNAMIC_UNRESOLVED`;`echo "python -m <sentinel>"` → 名字命中未得消费边,须 `UNKNOWN_CAPABILITY`。

**静态发现的残余边界与删除后验证(v1.29 新增)**
> **为什么要写这一节**:v1.26 起连续四轮,每轮都能找到一种新的"引用模块的写法"绕过静态发现 —— 这不是某条谓词写错,
> 而是静态枚举本身不可能对任意文本证明完整(§1.1a 已写明运行时锚"不能证明静态枚举完整",对静态层同样成立)。
> 继续逐写法补表不会收敛,故本节**明确静态层承诺覆盖什么、不承诺什么,并给不承诺的部分配一道不依赖静态完整性的验证**。
> **静态层承诺覆盖**:原子形态表全部形态;受监控名字集合内的全部调用与读取;名字形态 ①–④ 的字面出现;
> 解释器 token 封闭集合所标记的解释器行及其全部四类代码来源(`-m`、`-c`、脚本文件、stdin;v1.30);进程启动调用中以解释器为命令者的同四类来源;doctest 行。以上任一处漏检即为本稿缺陷。
> **静态层不承诺覆盖(残余边界)**:模块名**完全由非字面片段在运行时拼出**,**且**经由受监控名字集合以外的调用、
> 或解释器 token 封闭集合以外的命令写法到达(例:经项目自定义包装函数、经运行时读取的配置文件、经名字不含 `python` 的 make 变量充当解释器)。
> **残余边界由删除后验证兜底**(不依赖静态完整性):
> > **(一)分组可回退**:commit C 中 ① 与 ② 的删除**按 shim 模块分组,每组一个独立 commit**,commit message 列出该组删除的全部条目;
> > **(二)删除后验证**(C 的全部删除完成后、D 收口之前执行;`SEAL-9` 冻结的是删除前的判定,本验证检的是删除后的真实结果,两者不互相替代):
> > ①全量测试与前七批全部门禁;②运行时锚与冒烟入口全量(§1.1a);③**import-all**:在新解释器中逐个导入仓库内每个受版本控制的
> > Python 模块;④**名字残留复扫**:以已删条目的名字形态对全树重跑名字命中兜底与解释器行兜底,除第 9 类排除外命中数须为 0;
> > ⑤仓库含打包描述(`pyproject.toml`/`setup.cfg`/`*.spec`)时,按其构建一次、装入干净环境,并对 `C7a` 登记的每个入口执行 `--help`。
> > **任一项失败 → 回退失败所涉的删除组(`git revert` 该组 commit),停止并报告**;失败说明静态层漏了一种引用,
> > 须先按冻结稿勘误流程把该引用写法补进承诺覆盖范围(新增形态或扩充封闭集合)并配正控制,再从 A₀ 起重跑判定,**不得就地修补后重试同一删除**;
> > 被回退的组未重新通过之前,项 1 不算关闭(受终止条款约束)。
> > 删除后验证的输入、命令、输出与回退记录落 B-8。
> **对冻结规则的含义**:评审发现的"朝开"问题,若其反例落在残余边界内(即须同时满足上面两个条件),**不阻止冻结**,
> 登记为实现期观察项;落在承诺覆盖范围内的,仍按缺陷处理。

### 1.1a 元要求、外部锚与解析层扫描

**元要求**:形态清单须由"**该模块可能被引用的全部机制**"**反向导出**。

**外部锚(必做)**:以一次**运行时 import 记录**校验静态枚举;断言:
> **静态枚举判为"零消费者"的模块,不得出现在运行时加载集合中**;出现即红。

**三者定位**:**冻结台账 = 候选权威**;**独立扫描 = 发现源**;
**运行时 trace = 独立反证锚**——**不得升为权威全集**;
**它只能证伪"静态判零消费者"这一结论,不能证明静态枚举完整**。
**锚须在新解释器中、导入前安装钩子,并覆盖子进程。**
**冒烟覆盖面**:须覆盖**全部已文档化入口**——包入口的 subprocess 消费关系与
覆盖面见 `OBS-5.entry-consumers`;**本节不陈述其内容**。
**规范判断**:若该 claim 显示覆盖面依赖少数测试,则本批删测试会同时失效该锚,
**故冒烟入口清单须独立于被删测试集**。

**解析层扫描**:下列形态的导出面或导入解析**运行时决定、静态不可穷举**,
**单列一层扫描并一律 fail-closed**:

| 形态 | 处置 | 是否遮蔽台账条目存在性 |
|---|---|---|
| 模块级 `__getattr__` / `__dir__` | `DYNAMIC_UNRESOLVED`;**若同时满足粒度④ 判据则另产出 `PROXY_CALLABLE` 候选** | **是** → 相关台账 key 的 `ledger_membership = UNKNOWN` |
| 动态 `__all__` | `DYNAMIC_UNRESOLVED` | **是** → 同上 |
| `sys.modules[...]` 别名注入 | `DYNAMIC_UNRESOLVED` | **是** → 同上 |
| import hook / `meta_path` / `path_hooks` | `DYNAMIC_UNRESOLVED` | 否 |
| 打包入口与文件系统层重定向(符号链接、`.pth`、命名空间包 portion、gitlink) | `DYNAMIC_UNRESOLVED` | 否 |

> **"遮蔽存在性"这一列的口径(v1.14 明写,随 `PRESENT` 取读法(i) 同步)**:
> 该列问的是"**该台账 key 所指实体在当前树中是否存在**"这一**存在性**问题
> 能否被静态确定,**不问它是否仍是 shim**;**前三行遮蔽存在性 → `UNKNOWN`**,
> **后两行不遮蔽存在性**(条目本身可见),**只遮蔽解析去向 →
> 仅落 `DYNAMIC_UNRESOLVED`**。

> **原则**:对看不见的东西,**承认看不见,而不是假装能看见**;
> **不得**以"当前仓库没有"为由略过扫描;命中为零时**显式记零**(SEAL-13)。

**`DYNAMIC_UNRESOLVED` 的销账证据链(六字段)**:
**①表达式与 span、②候选值域、③裁决、④运行时 import trace 或闭合值域证明、
⑤命令、⑥快照 SHA**。**只写理由就改 resolved 不够。**

**RC-1 构造式控制**:以**子进程** + **变量拼接的动态导入**加载一个静态判
"零消费者"的 **sentinel 模块**,断言运行时锚**必红**。
- **RC-1-a**:失败原因**精确指向唯一 sentinel 模块**的 child trace;
- **RC-1-b**:记录 `child_pid != parent_pid`;
- **RC-1-c**:断言**父进程侧无该 sentinel 模块的加载事件**。

**结论边界(正向刻画)**:
> **RC-1 仅证明:经 `subprocess` 以 Python 解释器启动、且继承了钩子安装
> 机制的子进程被覆盖。此范围之外的任何子进程形态均未被证明。**

**正向刻画自动排除同 PID 替换形态**——对它 RC-1-b 天然不适用;
举例列表则要靠记得列上。
**钩子安装方式**:`sitecustomize` 或注入环境变量;
**`PYTHONSTARTUP` 不适用于非交互解释器,不得作为安装方式**。
**RC-1 的记录字段规格见 B-12(v1.14 恢复;v1.13 压缩为标题,记录义务消失)。**

**计数纪律**:**§6 七条准入证伪、RC-1(a/b/c)、12b-10 的 detector 正控制、12b-11 的判定层 golden**
—— **四处证伪对象各不相同,各自独立计数,不得合写**;
合并计数会让其中一方的失败被另一方的绿灯稀释。
*(v1.24:原另含本稿两个文档自检工具的正控制,随该机制一并移除。)*

### 1.1b 第三段导出规格、观测维度与不覆盖清单

**(一)不得依赖提交次序。**
**立规依据**:该批(具名见证:skill-3 批次;见证文档:该批 closeout)的
**测试提交与登记抽取提交的次序关系**,以及**"使旧址模块变为 shim 的是哪一个
提交"**,**均由 `OBS-3.commit-order` 产出**;**本节不陈述其结论**。
**规范判断**:既然该次序关系**不可由提交序位推定**,则"按提交次序取首个"这一
规格**不得使用**。

> **修正规格**:第三段从**各批冻结 closeout / lifecycle 记录中登记的
> "实际抽取提交 SHA"**读取,**不得由字母序位或提交次序推断**;
> 对该 commit 的 diff 应用判据:**旧址文件由"有顶层 `def`/`class`"变为
> "零 `def`/`class`"** 者,即该批创建的**整模块 shim**。
> **SHA 须逐批落入 provenance。**
> 该判据在现存旧址 shim 上的逐模块溯源结果见 `OBS-3.transition-map`
> ——**它同时是"不覆盖九类"中各类归属的实测依据**。

**(二)观测维度全表(七维度)**
**按元规则(二)的推论**:本判据观测的是 **D1(定义计数)**;
**该维度恒定而其他维度变化的情形,逐类承担方见下**。

| # | 维度 | 承载的 shim 化形态 | 由谁观测 |
|---|---|---|---|
| D1 | **定义计数** | 有实现 → 纯转发模块 | 第三段跃迁判据 |
| D2 | **导出目标** | 计数恒为 0,导出面翻转 | 第一段 + 粒度② |
| D3 | **定义内容 / 调用委托** | 计数不变,函数体变为转发 | **粒度④** |
| D4 | **绑定级** | 模块级不变,绑定增删 | 粒度②③ |
| D5 | **动态属性** | 导出面运行时决定 | 解析层 → fail-closed |
| D6 | **导入解析** | 模块身份被重定向 | 解析层 → fail-closed |
| D7 | **实现载体与运行时变异** | **D1–D4 全是 AST 判据,对无源可读的模块结构上失明** | **`UNSUPPORTED` 分流**;**封闭 artifact universe** |

> **封闭 artifact universe**:**显式列出本批支持的 provider 类型**——
> 纯 `.py` 源文件、包目录(含 `__init__.py`)、命名空间包 portion。
> **其余一律 `UNSUPPORTED`,阻塞 seal**。清单属类三·规则常量,
> **扩充走变更流程**;**注册表键须覆盖本清单全部 kind**(12b-3c)。

**(三)不覆盖清单(九类,逐类声明承担方与 capability branch)**

| # | 类别 | 维度 | 由谁承担 | capability branch(v1.14 补,供 12b-12 机械比较) |
|---|---|---|---|---|
| (a) | **step-0 自建 shim** | D1 | **第一段** | `ledger.seg1` |
| (b) | **零定义→零定义,导出目标翻转** | D2 | **第一段** + **粒度②** | `ledger.seg1` + `scan.reexport` |
| (b′) | **代理 shim:有定义→仍有定义** | D3 | **粒度④** | `scan.proxy_callable` |
| (c) | **re-export binding 与内联 binding** | D4 | **第一段** + **粒度②③** | `ledger.seg1` + `scan.reexport` + `scan.inline` |
| (d) | **登记抽取提交之外的后续提交所创建的 shim** | D1 | **`UNREGISTERED_CANDIDATE` + admission** | `scan.module` |
| (e) | **已是 shim 的模块上、后续批次追加的 binding** | D4 | **粒度②**(**无 admission 兜底**) | `scan.reexport` |
| (f) | **动态属性导出面** | D5 | 解析层 → `DYNAMIC_UNRESOLVED` | `resolve.dynamic_attr` |
| (g) | **导入解析层重定向** | D6 | 解析层 → `DYNAMIC_UNRESOLVED` | `resolve.import_redirect` |
| (h) | **无源可读的 provider 与运行时变异** | D7 | **`UNSUPPORTED` 分流** | `provider.unsupported` |

> **本表兼作 12b-10 正控制的取材来源**:每个 detector 的正控制实例
> **须取自"该 detector 被指定为承担方"的类别**,**实现方不得自选**。
> **唯一合法的扩充次序**:**新形态须先进本表 / registry →
> 双向覆盖立即转红 → 再补正控制;实例目录不得先于本表扩充。**
> **`capability branch` 列属类三·就地列举**,是 **12b-12 四方对账**的键之一;
> **该列与 registry 的分支名不一致即红**。
> **命名空间(v1.27;甲 BLOCKER-3、丙 BLOCKER-2)**:本表分支全部在 `ledger.*` / `scan.*` / `resolve.*` / `provider.*` 内,
> **不含 `consumer.*`**;消费者形态分支(`consumer.*`)只由 §1.1 原子形态表登记、只进 `SEAL-16b` 对账。

**兜底完整性**:兜底链"扫描 → `UNREGISTERED_CANDIDATE` → SEAL-3"
**只在七件事同时成立时有效**:①扫描**看得见**该形态(SEAL-13);
②扫描**本身完整**(SEAL-12b);③**输入面不被权威源裁剪**(12b-1);
④**输入面之上的减法有机械上界**(**§8-2 豁免清单四条上界**;
`NON_SHIM_PREDICTION` **不做减法故不适用**);⑤**行级下界成立**(12b-3b);
⑥**扫描确实具备检出能力**(12b-10);⑦**判定层确实判得对**(12b-11)。
**七者缺一,这条链就是断的。**

### 1.1c-0 标准化阶段(v1.14 新增;三家 BLOCKER 的直接修法)

**问题**:v1.13 的两个维度分别写"对象 = finding"与"对象 = 台账 key",
而后者的取值里有 `NO_LEDGER_KEY`(= 没有台账 key)——**对象域自相矛盾**;
且 **`raw finding → candidate → 台账 key` 的归并与配对关系全文未定义**,
而 12 格导出表**完全建立在它之上**。**故先定义对象,再谈状态。**

**三级对象与两级归并**

```
raw finding            扫描器在某个 span 上的一次命中
   │  归并规则 N1(多 producer 归并,见 §1.1c"多 producer 归并与落未决规则")
   ▼
candidate (candidate_id)   §1.1c 四级粒度,ID 全局唯一(SEAL-7)
   │  配对函数 π(见下)
   ▼
ledger_key            保持来源自身粒度(§1.1 第 1 条);由 π 粒度归一配对
```

- **N1 的定型**:同一 `candidate_id` 下的多个 raw finding **按 guard 互斥性
  归并为多个 producer span**;**归并不计入 SEAL-7b 的"重复"**;
  归并失败(guard 非互斥或不可判定)→ `UNRESOLVED_DISPOSITION`。
- **配对函数 π(v1.15 改为【粒度归一】;甲 BLOCKER-2)**:
  `π(candidate_id) → ledger_key | ⊥`,**判定规则(v1.16 改为【最细粒度优先】;
  甲 MAJOR-1、丙 BLOCKER-1)**:**先按 ID 逐字相等匹配;无匹配则逐级放粗,
  取【包含该 candidate 的最细台账 key】**。
  > **为何 v1.15 的"最粗优先"是方向性错误**:台账保持来源自身粒度之后,
  > 第二段 closeout 条目完全可能是 binding 级。台账同时登记 `#MODULE` 与其内部
  > binding key 时,"同粒度逐字相等"与"归一到最粗"**各给一个值、文中无优先级**
  > → `|π(c)| = 2` → `LEDGER_KEY_AMBIGUOUS` **阻塞一个由"保持来源粒度"直接
  > 导致的正常配置**;台账只登记 binding 级时,candidate 全部上卷至无对应 key 的
  > `#MODULE`,该 binding key 落 `LEDGER_PRESENT_NO_FINDING`——而该状态的语义是
  > "扫描在它身上找不到任何候选特征",**事实恰恰相反(候选找到了,被上卷走了)**,
  > 一个状态被赋了与事实相反的语义。最细优先后:binding 级 key 正常 `MATCHED`,
  > 模块级 key 由 `covers` 关系覆盖,**歧义只留给真歧义**。
  > **两个关系分开(丙 BLOCKER-1)**:**`π`(= `primary_owner`)至多一个,
  > 用于 item 归属**;**`covers(candidate, ledger_key)` 允许同时覆盖包含链上的
  > 多个 key,用于台账侧完整性**——**不得再用 `π⁻¹` 同时承担两者**。**π 必须是全函数**(与 12b-3c③ 同款):
  **对每个 candidate 都必须给出一个 key 或 `⊥`,不得留空**。
- **基数断言(v1.15 只保留一侧)**:**`|π(c)| ≤ 1`**——一个 candidate
  至多归属一个台账 key;**多于一个 → `LEDGER_KEY_AMBIGUOUS` 阻塞 seal**,
  **不得静默归并、不得任选其一**。
  > **`|π⁻¹(k)| ≤ 1` 已撤销**:**一个模块级台账 key 被它内部的多个 binding 级
  > candidate 覆盖,是正常情形,不是歧义**;保留该断言会逼出"台账必须展开到
  > binding 级"这条无基准的义务(见 §1.1)。
- **台账侧的覆盖义务 —— 由【全函数分类器】给出(v1.18 重写;甲 BLOCKER-2、丙 BLOCKER-5)**:
  **输入 = (是否处于 `SOURCE_OBLIGATION_UNENUMERABLE` 未落定暂态, `covers⁻¹(k)` 是否为空
  (暂定求值用原始 `covers⁻¹`,终态求值用 `effective_covers⁻¹`,见下文"祖先 key 须由有效后代覆盖";v1.27),
  `primary_owner⁻¹(k)` 是否为空, 独立存在性检查结果)**;**输出恰一个出口**;
  **判定按下表逐格给出,表外组合 → `UNKNOWN_LEDGER_EXIT` 阻塞,不得回落默认**
  (与 12b-3c③ 同款,与 §1.1c 的 12 格导出表同手法,**不引入新锚**)。

  | # | 暂态 | `covers⁻¹` | `primary_owner⁻¹` | 存在性 | 出口 |
  |---|---|---|---|---|---|
  | 1 | **是** | 任意 | 任意 | 任意 | **暂态豁免**(优先级最高;不计入 `SEAL-1` 的红,亦不计入本义务的红) |
  | 2 | 否 | ≠∅ | ≠∅ | 任意 | **被 candidate 覆盖(有 primary owner)** |
  | 3 | 否 | ≠∅ | =∅ | 任意 | **`LEDGER_COVERED_BY_DESCENDANT`** |
  | 4 | 否 | =∅ | =∅ | `PRESENT` | **`LEDGER_PRESENT_NO_FINDING`** |
  | 5 | 否 | =∅ | =∅ | `ABSENT` | **`LEDGER_ONLY`** |
  | 6 | 否 | =∅ | =∅ | `UNKNOWN` | **`INDETERMINATE`** |
  | 7 | 否 | =∅ | ≠∅ | 任意 | **非法** —— 有 primary 而无 covers,`covers ⊇ primary_owner` 不成立;登记入 §1.1c 显式非法表 |

  **互斥性由分类器的全函数性保证,不再另立事后 XOR 要求。**
  **不变式须独立于分类器求值(v1.20;甲 MAJOR-1、丙 BLOCKER-7)**:
  **`covers ⊇ primary_owner` 是构造不变式,在【标准化期】由一条独立断言核验,
  不由分类器第 7 行承载**;违反即红,**暂态不豁免**。
  第 7 行保留为分类器的全函数补格(理论上不可达),
  **其实际命中数须恒为 0 并随产物给出**;非零即说明不变式断言漏跑。
  **另补一个具名监控量作为 `SEAL-9` 前置(丙)**:
  | 量 | 定义 | 门 |
  |---|---|---|
  | `SOURCE_OBLIGATION_UNENUMERABLE_PENDING` | 处于 `UNENUMERABLE` 未落定暂态的台账 key 计数 | **须为 0;由 §1.3 断言二在终局求值(v1.27;甲 BLOCKER-2),经"以上全部"成为 `SEAL-9` 前置;`SEAL-11` 在 disposition 期不求值它** |
  **理由**:第 1 行优先级最高会掩盖第 7 行,而**第 7 行检的是构造 bug、不是状态**,
  不会因暂态消解而消失,却被推迟到暂态清零之后才可能被看见
  ——而暂态清零的前提之一正是枚举重跑成功。
  **被覆盖的祖先 key(第 3 行)不生成普通 reconciliation item。**
  **祖先 key 的记账(v1.25 补;甲 BLOCKER-3)**:落第 3 行的台账 key,在 B-8 的台账 key 记录中登记
  `ledger_exit = LEDGER_COVERED_BY_DESCENDANT` 及覆盖它的 candidate 清单;
  **它不进入 `SEAL-11` 的五元组核验,也不需要 admission**。
  **祖先 key 须由有效后代覆盖 —— admission 期内的三个有界子步骤(v1.26 立;v1.27 改为在 `SEAL-3` 之前完成;
  丙 BLOCKER-3、甲 BLOCKER-4)**:分类器分两次求值,**第一次(标准化期,暂定)用原始 `covers⁻¹(k)`**,
  **第二次(admission 期,终态)用 `effective_covers⁻¹(k)`**,两次的输入与出口都记入 B-8。admission 期按下列顺序执行:
  > **A. 终态化现有 candidate item 的 admission**;
  > **B. 计算 `effective_covers⁻¹(k) = {c ∈ covers⁻¹(k) | admission(c) ∈ {NOT_REQUIRED, ADMITTED}}`**
  > (这正是 `preseal_effective_inventory` 的成员条件,只依赖 A 的终态值,不依赖后续任何步骤);
  > 以 `effective_covers⁻¹` 替代 `covers⁻¹` **对暂定第 3 格的 key 重新求值分类器**:仍落第 3 格者保持;
  > 转入第 4–6 格者**生成一个只有台账侧的 fallback item**(**每个台账 key 至多一个**);
  > **C. 终态化 fallback item 的 admission**。
  > **A–C 全部完成后才求值 `SEAL-3`、`SEAL-4`、`SEAL-11`,并计算 `preseal_effective_inventory`。**
  > **有界且无循环**:fallback item 只有台账侧,不是 candidate,**不进入任何 `covers` 关系**,
  > 故 C 的结果不会改变 B 中任何 key 的 `effective_covers⁻¹`;B 对每个 key 只执行一次,子步骤总数固定为三。
  > 本过程在 admission 期**内部**按固定顺序执行,**不属于 §1.1d"同期内依赖闭包出现循环即红"所指的循环**。
  **违例 fixture**:祖先 key 的全部覆盖 candidate 都被 `REJECTED_NOT_SHIM` → **须转入第 4–6 格、生成 fallback item,
  且该 item 在 C 中取得终态 admission**;仍留第 3 格,或 fallback item 带 `PENDING_ADMISSION` 进入 `SEAL-3` → 红。
  *(v1.25 只要求"至少一个覆盖 candidate 的五元组在 R1–R7 内",而合法 candidate 本来都在 R1–R7 内,
  覆盖它的 candidate 即使被 `REJECTED_NOT_SHIM`,祖先 key 也照样免检 —— 条件近乎恒真。
  v1.26 改为 `SEAL-3` 之后复核,但转格生成的新 item 会推翻已通过的 `SEAL-3`,且全文没有授权这一轮追加 admission。)*
  **相同逻辑 key 来自多个来源时,先按 key 归并 provenance,不得让 π 面对多个物理记录。**
  > **v1.17 的写法不成立,必须记下(甲 BLOCKER-2、丙 BLOCKER-5)**:
  > v1.17 把第一个出口写成 `covers⁻¹(k) ≠ ∅`,又把新状态钉成
  > `LEDGER_COVERED_BY_DESCENDANT ⟺ covers⁻¹(k) ≠ ∅ ∧ primary_owner⁻¹(k) = ∅`
  > ——**后者蕴含前者**,于是每一个落该状态的祖先 key **必然同时落两个出口**,
  > 按"落入两个以上即红"→ **本版为闭合上一轮阻断而新增的状态,恒红、永不可达**。
  > 暂态出口与第一个出口**同样不互斥**(`covers` 由扫描侧产生,与台账枚举是否完成无关)。
  > **净效果是 XOR 那一句把它前面两轮刚补上的两个出口双双废掉,且方向是活性的**
  > ——正常配置转红、seal 不可达、撞终止条款。
  > **教训**:"包含式或 + 事后互斥要求"这种写法,**互斥性是一条需要另行证明的命题**;
  > 改为全函数分类器之后,互斥性是构造出来的,不需要证明。
  **构造式正控制(三条,不得合并;v1.18 新增)**:
  > **(i)** 一个被后代覆盖、`primary_owner` 落在后代的祖先 key → **须恰落第 3 行且不红**;
  > **(ii)** 一个处于暂态、同时被某 candidate 覆盖的 key → **须恰落第 1 行且不红**;
  > **(iii)** 一个 `covers⁻¹ = ∅ ∧ primary_owner⁻¹ ≠ ∅` 的 key → **须落第 7 行且红**。
  > **near-miss**:一个 `PRESENT ∧ covers⁻¹ = ∅` 的 key → 第 4 行,不得被误判为第 3 行。
  > **(i)(ii) 正是 v1.17 写法会误红的两个构造**:**须先在 v1.17 上跑出红、
  > 再在本版修法后跑出绿**,与变更⑫ 的"区间式控制"同款写法。
  这样台账 key 一个都不会无声消失,
  而台账**不需要展开、不需要基准、不派生**。

**reconciliation 的对象 = item**,定义为:
> **item = (candidate_id?, ledger_key?) 且至少一侧非空**;
> **candidate 一侧的 item,其台账侧只由 `primary_owner` 构造;`covers` 只用于七格分类与祖先覆盖记录;
> 七格第 3 格不生成 item,第 4–6 格生成只有台账侧的 item**(v1.26 统一;丙 BLOCKER-2。
> 此前写"由 `primary_owner` 与 `covers` 构造",与"第 3 格不生成 item"可两读)。
> **两个维度都以 item 为对象**:
> 维度一看 item 的 **finding 侧**,维度二看 item 的 **台账侧**。
> 这样 `NO_LEDGER_KEY` 是"**该 item 的台账侧为空**",**不再自相矛盾**。

**`scan_resolution` 的计算基准(丙问)**:**按 candidate 计算,不按 raw
finding**——raw finding 已由 N1 归并;**无 candidate 侧的 item(纯台账 key)
取 `NOT_APPLICABLE`**。

**`SOURCE_OBLIGATION_UNENUMERABLE` 的时序出口(v1.15 新增;乙 MAJOR-4)**

> **问题**:动态导出面的台账来源(模块级 `__getattr__` / 动态 `__all__`)
> 会**同时**触发 `DYNAMIC_UNRESOLVED` 与 `SOURCE_OBLIGATION_UNENUMERABLE`,
> 而**该来源的销账证据(闭合值域证明)正是枚举它所需的输入**
> ——若无时序规则,该情形**永久红**,与变更⑤ 修掉的那个同型、只换了位置。
> **规则**:**`UNENUMERABLE` 先落【暂态】**;
> **`DYNAMIC_UNRESOLVED` 按六字段证据链销账后,须以销账证据为输入
> 【重跑枚举与 π 映射】**(v1.17 删去"一次"——丙 MAJOR-1 指出本段先写"重跑一次"、
> 随后的有界性又写多轮并以首轮计数作上界,**两处互斥**:若重跑能揭示新的动态构造,
> 首轮计数就不是闭合上界;若不能揭示,多轮的理由又不成立);**仅当闭合值域证明本身不可得时,才落定 `UNENUMERABLE`
> 并 fail-closed 阻塞**。**暂态不得计入 SEAL-1 的红,亦不计入台账侧覆盖义务的红
> (v1.16:两处豁免须同时挂,见 §1.1c-0 覆盖义务第四出口)。**
>
> **有界性(v1.16 新增;甲 MAJOR-2、丙 MAJOR、乙 MINOR-2)**:v1.15 只写"重跑
> 一次",而重跑可能揭示**新的**动态构造(销账所需的 trace 本身引入第二层动态
> 导出面)——此时该项既不满足"闭合值域证明不可得",又已用掉唯一一次重跑机会,
> **第二轮无归宿 → 实现者裁量,而这条路径闸的是 SEAL-1**。补三条,**不引入新锚**:
> > **(i) 单调性**:每轮销账须使 `DYNAMIC_UNRESOLVED` 计数**严格下降**;
> > **(ii) 上界(v1.17 改由【冻结 universe】承担;丙 MAJOR-1)**:
> > **扫描期一次性冻结【动态表达式 span universe】**(类二快照,带 hash),
> > **该 universe 由【独立的 raw-syntax / config 枚举器】产出,detector 只能消费、
> > 不得生成**(v1.18 补;丙 BLOCKER-7:**若同一个扫描器最初就漏掉某个动态 site,
> > universe 与 worklist 会一致地漏**);
> > **构造式控制:scanner 漏一个动态 site,必须红**;
> > **worklist 在该 universe 上单调减少**,上界 = universe 基数;
> > **重跑中出现的、不在冻结 universe 内的动态 site → 立即 `UNSUPPORTED`,
> > 要求扩 registry 后【整轮重启】,不得就地续跑**
> > ——首轮计数不是闭合上界,universe 才是。原写法的上界
> > (六字段证据链逐条对应一个表达式 span,故该计数是有限的);
> > **(iii) 达上界或单调性不成立即落定 `UNENUMERABLE` 并 fail-closed**。

### 1.1c 状态模型与候选粒度

**五个正交维度**(对象均为 §1.1c-0 定义的 **item**)

**维度一 · `scan_resolution`(看 item 的 finding 侧)**

| 值 | 含义 |
|---|---|
| `RESOLVED` | 该 item 有 candidate,且其定性条件可机械判定 |
| `SCAN_UNRESOLVED` | **已有 candidate,但定性未决**(非白名单装饰器包装 / 宿主含副作用或可变状态 / 多委托目标或目标不可静态确定) |
| `NOT_APPLICABLE` | **该 item 无 candidate 侧**(纯台账 key)——**不得让纯台账 key 伪装成 `RESOLVED`** |

**维度二 · `ledger_membership`(看 item 的台账侧)**

> **`PRESENT` 的语义(v1.14 二选一并明写;取读法(i))**:
> > **`PRESENT` = 该台账 key 所指的模块/绑定【在当前树中仍存在】,
> > 【不含】"它是否仍满足任何 shim 判据"。**
> **取读法(i) 的理由**:读法(ii)("仍是 shim")会使 `PRESENT ⟺ 有 finding`,
> **维度一与维度二退化为一维**,v1.12 拆对象域(事故 (26))的全部理由消失。
> **代价已随动处理**:E9 由"非法"改为合法值(见导出表),
> 解析层表"是否遮蔽存在性"一列的口径已在 §1.1a 明写。

| 值 | 含义 |
|---|---|
| `PRESENT` | **独立存在性检查确定**该台账 key 所指实体在当前树仍存在 |
| `ABSENT` | **独立存在性检查确定**该台账 key 所指实体已不存在 |
| *(口径)* | **独立存在性检查取 `lstat` 语义,【不跟随符号链接】**(v1.15;甲 MINOR):**符号链接自身存在即 `PRESENT`,其目标是否存在【不参与】该判定**——否则悬空 symlink 上 `PRESENT`/`ABSENT` 二义,**而本批项 3 恰是悬空 symlink 归一化**;目标侧的可达性属 §3 的处置对象,不属存在性维度 |
| `UNKNOWN` | **存在性未能确定**(解析层三类遮蔽形态) |
| `NO_LEDGER_KEY` | **该 item 的台账侧为空**——`UNREGISTERED_CANDIDATE` 的产生前提 |

> **`ABSENT` 的判据限定(v1.14;堵乙指出的侧门)**:
> > **"扫描没有产出 finding"【不得】作为 `ABSENT` 的判据。**
> > **`ABSENT` 必须由【独立存在性检查】正面产出**(按 key 的粒度解析到
> > 文件/绑定并断言其不存在);**存在性检查本身不可判定者一律 `UNKNOWN`**。
> **否则**:一个"**仍在树中但已不再是 shim**"的台账 key(被填回真实实现、
> 注释被删)会因无 finding 而被判 `ABSENT` → `LEDGER_ONLY` →
> 合法取 `ALREADY_REMOVED` ——**"没看清"被判成"已删除"从侧门回来**。

**维度三 · `reconciliation`(观察事实;由前两维【全函数】导出;逐项产出)**

> **为何必须【逐项】产出(v1.15 恢复理由句)**:早期版本写"**全部**解决后一次性
> 产出",按全局读法,**一个已 `RESOLVED` 的条目会陪着其他未决条目一起卡在
> `NOT_YET_COMPUTED`**,而非法表又禁止 `RESOLVED × NOT_YET_COMPUTED`
> ——**合法中间态被误红**。改逐项后:**该条目的不确定性解决即产出该项**。

**导出表(3 × 4 = 12 格全列;本表即"导出规则须全函数"的落地)**

| # | scan_resolution | ledger_membership | reconciliation |
|---|---|---|---|
| E1 | `SCAN_UNRESOLVED` | `PRESENT` | `NOT_YET_COMPUTED` |
| E2 | `SCAN_UNRESOLVED` | `ABSENT` | `NOT_YET_COMPUTED` |
| E3 | `SCAN_UNRESOLVED` | `UNKNOWN` | `NOT_YET_COMPUTED` |
| E4 | `SCAN_UNRESOLVED` | `NO_LEDGER_KEY` | `NOT_YET_COMPUTED` |
| E5 | `RESOLVED` | `PRESENT` | `MATCHED` |
| E6 | `RESOLVED` | `ABSENT` | **`EXISTENCE_CONFLICT`——具名且阻塞**(v1.15:阻塞行为不变,但与 E12 **并列为"非法"的代价有三**:SEAL-11 的反向验证只要一条 fixture、B-8 不记录哪一侧错、而 §1.2b 与 B-15 存在的全部理由就是区分"判据写错"与"执行错"——**E6 恰是最需要证据的一格,却在阻塞时什么都不留**)。**与 12b-3 的 `FAILED`/`UNSUPPORTED` 同档:阻塞但逐格记录**;**须逐条落 B-8 并附两侧证据**,配**独立违例 fixture** 与**一条 12b-11 golden**。**E12 性质不同——它是定义上不可能,不具名** |
| E7 | `RESOLVED` | `UNKNOWN` | `INDETERMINATE` ※※ |
| E8 | `RESOLVED` | `NO_LEDGER_KEY` | `UNREGISTERED_CANDIDATE` |
| E9 | `NOT_APPLICABLE` | `PRESENT` | **`LEDGER_PRESENT_NO_FINDING`**(**v1.14 由"非法"改为合法值**:台账项**仍在树中但已不再满足任何 shim 判据**是**可达且合法**的情形——v1.13 判它非法会使 SEAL-11 转红、**seal 不可达**) |
| E10 | `NOT_APPLICABLE` | `ABSENT` | `LEDGER_ONLY` |
| E11 | `NOT_APPLICABLE` | `UNKNOWN` | `INDETERMINATE` |
| E12 | `NOT_APPLICABLE` | `NO_LEDGER_KEY` | **非法**——既无 candidate 又无台账 key,**该 item 依 §1.1c-0 的定义不存在** |

> ※※ **E7 不是边角格**:**它是模块级 `__getattr__` 的默认产物**——解析层表
> 规定该形态使台账 key 的 membership 为 `UNKNOWN`,而粒度④ 的发现判据
> **明文把模块级 `__getattr__` 列为 callable 形态**,**必然同时产出一个
> candidate**;定性解决后即落 E7。**v1.12 无此行致 seal 不可达**(事故 (26))。

> **全函数断言(与 12b-3c③ 同款)**:**导出器对 12 格中的每一格都必须给出
> 上表所列的值或非法判定**;**遇未覆盖组合 → `UNKNOWN_RECONCILIATION`
> 阻塞 seal,不得回落默认**。

> **`LEDGER_PRESENT_NO_FINDING` 的处置语义(v1.14 新增)**:
> > 它表示"**台账登记的实体还在,但扫描在它身上找不到任何 shim 候选特征**"。
> > **强制进入 admission**(不得自动出册);**可取 `ADMITTED`(补录为候选)
> > 或 `REJECTED_NOT_SHIM`(附逐项结构化证据)**;
> > **`ALREADY_REMOVED` 永禁**——**它存在,不可能"已删除"**
> > (与 `INDETERMINATE` 的同款禁令同理)。

**`INDETERMINATE` 的时序前提与消化语义**:它**仅在该 item 的 `scan_resolution`
已解决之后产生**(E7/E11),与 `SCAN_UNRESOLVED` **不可共存**;
它是**扫描能力的永久记录**;**消化 = 人工补全存在性判定所缺的【事实输入】
(结构化证据),裁决仍由 admission 判据机械产出**;**`ALREADY_REMOVED` 永禁**。

**维度四 · `admission verdict`(全函数)**

| 值 | 适用 | 入册? |
|---|---|---|
| `NOT_REQUIRED` | 仅 `MATCHED` | 是 |
| `PENDING_ADMISSION` | 非 `MATCHED` | 未定 |
| `ADMITTED` | 非 `MATCHED` | 是 |
| `REJECTED_NOT_SHIM` | 非 `MATCHED`,**须附证据** | 否(留档) |
| `ALREADY_REMOVED` | **仅 `LEDGER_ONLY`**(**`INDETERMINATE` 与 `LEDGER_PRESENT_NO_FINDING` 禁用**) | 否(留档) |

> **裁决纪律**:证据须**逐项、结构化**(`(claim, 判据, 命令, 输出)`),
> **不得批量裁决**。

**维度五 · `disposition`**

| 值 | 叙述编号 | 含义 |
|---|---|---|
| `DELETE_DIRECT` | ① | 零消费者 → 删 |
| `DELETE_AFTER_TEST_REMOVAL` | ② | 消费者仅为纯接线测试 |
| `DELETE_AFTER_CONSUMER_MIGRATION` | ③ | 有真实消费者 |
| `KEEP_PRIVATIZED` | ④ | A=是 ∧ B=无 |
| `NOT_SHIM_REAL_DEPENDENCY` | ⑤ | A=是 ∧ B=有 |
| `NOT_APPLICABLE` | — | 非入册项专用 |
| `PENDING_TRIAGE` | — | 过渡态:入册条目初值 |
| `UNRESOLVED_DISPOSITION` | — | 过渡态:入册后判据仍无法机械判定 |

> **④/⑤ 的代码动作(v1.25 写死;丙 MAJOR-3)**:
> **④ `KEEP_PRIVATIZED`**:**前提:该条目的消费者集合为 `CLOSED`(`SEAL-16b`),否则落 `UNRESOLVED_DISPOSITION`**;
> **先处理本模块之外的全部消费者,再私有化**(v1.26 补;丙 BLOCKER-3:A=是 时条目只能落 ④/⑤,
> 若不先处理外部消费者,删公开名会直接打断它们)。**外部消费者的处理(v1.27 改;丙 BLOCKER-4)**:
> > **每个测试消费者先按 §2 三分规则分类**:(a) 纯接线测试 → 按 ② 的动作删除,并登记替代覆盖或理由;
> > **(b) 行为型测试(含 `BEHAVIOR` 叶子)→ 按 ③ 的动作迁移到新址并保留**;(c) 不可判定 → 该条目落 `UNRESOLVED_DISPOSITION`。
> > **非测试消费者**一律按 ③ 迁移。**全部处理完并复扫确认旧公开绑定的模块外消费者为零之后**,才执行下面的私有化;
> > 复扫非零 → 该条目落 `UNRESOLVED_DISPOSITION`。
> > *(v1.26 写"测试消费者按 ② 的动作",会把 §2(b) 规定必须保留的行为型测试一并删掉。)*
> **私有化动作按粒度分述(v1.27;甲 MAJOR-1)** —— 按 §1.2 维度 A 的定义,A=是 只出现在 `#REEXPORT` 与 `#INLINE`:
> > **`#REEXPORT`**:保留该依赖;删除其公开绑定名(含 `__all__` 中的条目);
> > import 绑定改为私有别名 `_<name>`,并在同一 commit 内原子更新本模块对它的全部 `Load`;
> > **`#INLINE`**(函数体内的 import binding):它没有公开绑定名、不在 `__all__` 中、**按构造没有模块外消费者**
> > (上面的"先处理外部消费者"对它为空操作,须在 B-8 记录"外部消费者 = ∅");
> > **动作 = 把该内联 import 的绑定名改为 `_<name>`,并原子更新其所在词法作用域内的全部 `Load`;`__all__` 与模块级导出面不动**;
> > 该场景在 `expected_diff.json` 中按 `NO_DIFF` 登记。**它与 ⑤ 的区别是绑定名被改写**(⑤ 不改任何绑定)。
> **`_<name>` 与既有名字冲突 → 该条目落 `UNRESOLVED_DISPOSITION`**,不得临时另取名或改用模块限定访问;
> 冲突检查的作用域:`#REEXPORT` 为模块级;`#INLINE` 为该词法作用域 ∪ 模块级。
> **⑤ `NOT_SHIM_REAL_DEPENDENCY`**:import、绑定与消费者全部保留;只删除把它标为 shim 的注释/标记,
> 并在台账中登记"非 shim";不迁移消费者、不删除导出。

> **`UNRESOLVED_DISPOSITION` 的消化语义(v1.14 重写;三家 MAJOR)**:
> 它是五个"须清零"状态中此前唯一无出口者(五条产生路径、零条出口),
> 而谓词收紧与 §2 (c) 类**扩大了它的灌入面** → 阻塞 seal → **撞终止条款**。
> **v1.13 给了出口但没限制输出域,于是它成了后门。本版两条一起钉**:
> > **(一)消化 = 人工补全【判据所缺的事实输入】,以逐项结构化证据
> > `(claim, 判据, 命令, 输出)` 提交;【裁决仍由判据机械产出】,
> > 人工不得直接写结论。** 故 **SEAL-8b 对消化项照常重算、不开人工洞**
> > ——这正是"判据只负责发现、不负责定性"与"人工可以补事实"的分界。
> > **(二)输出域由【未决原因】的机械矩阵约束(v1.15 重写;三家 MAJOR)。**
> > **`uncertainty_kinds` 为【机械导出的多值集合】,人工不得填写**
> > (v1.16;甲 BLOCKER-2、乙 BLOCKER、丙 BLOCKER-3 三家同向)。
> > **产出规则**:**`uncertainty_kinds` = 判据本轮【失败子句】按登记映射的像集**
> > ——**每条 disposition 判据子句分配结构化 `clause_id`**,
> > 在 §1.1e 登记它对应的 kind(类三·就地列举),
> > **并断言 `predicate_clause_ids == uncertainty_mapping.keys()`
> > (双向精确覆盖,差集非空即红)**;
> > **`clause_id` 须由结构化 predicate AST 的 leaf 路径机械生成,禁止人工登记 leaf 集**
> > (v1.18 补;丙 BLOCKER-7:**若一个 predicate leaf 同时未进入两个集合,仍全绿**
> > ——两侧可以一致地漏,键集相等证明不了完整性);
> > **构造式控制:mapping 与 clause 集一致删除一个 leaf,必须红**
> > ——否则实现者漏登记一个失败子句即可让该子句"不产生任何 kind",
> > 随后机械地得到较宽输出域;
> > **判据判不出时,哪些子句失败是机械事实,不是标注**。
> > **A₀ 断言**:**记录的 `uncertainty_kinds` == 按失败子句重算的像集,不等即红**。
> > **v1.15 为何不成立**:它是**单值人工必填字段**,而把
> > `CONSUMER_SET_COMPLETENESS` 标成 `LEAF_SEMANTIC_CLASS` 即把输出域从"禁 ②"
> > 放宽到"许 ②",**全文没有任何机械断言核验 kind 与"判据为什么判不出"之间的
> > 对应**——门只是从输出侧挪到了输入侧。这是同一形状的**第三次**
> > (v1.12 的 claim `type` 登记、v1.14 的豁免上界 (iii) 的 `use` 标注、本处),
> > 而 **`use` 标注的机械化修法在 v1.15 刚刚做过**,手法已在手上,没有用在这一个上。
> > **多类同现取交集(v1.16;三家同向)**:**合法输出域 = 全部命中 kind 的输出域
> > 【交集】;任一 kind 禁 ② 则禁 ②;交集为空即继续阻塞**。
> > 矩阵如下(**八类**,v1.16 由六类补至八类):
> >
> > | `uncertainty_kinds` 的成员 | 该项未决的原因 | 该成员的输出域 |
> > |---|---|---|
> > | `CONSUMER_SET_COMPLETENESS` | 消费者集合是否枚举完整 | **{③④⑤} ∪ 保留侧;①② 均禁** |
> > | `CALLGRAPH_CLOSURE` | 闭合调用图是否穷尽 | **{③④⑤} ∪ 保留侧;①② 均禁** |
> > | `NEGATIVE_EXISTENCE` | 任何"某空间中无反例"型前提 | **{③④⑤} ∪ 保留侧;①② 均禁** |
> > | `LEAF_SEMANTIC_CLASS` | 已枚举叶子的 `semantic_class` 待定 | **{②③④⑤} ∪ 保留侧;① 永禁** |
> > | `GUARD_MUTEX` | 已枚举 producer 的 guard 互斥性待定 | 同上 |
> > | `AB_DIMENSION` | A 或 B 维度取值待定 | 同上 |
> > | `PRODUCER_DISPOSITION_CONFLICT` | 各 producer 的 disposition 冲突 | **{③④⑤} ∪ 保留侧;①② 均禁** |
> > | `DELETION_ORDER_UNREGISTERED` | 跨 candidate re-export 链的删除依赖顺序未登记(SEAL-10) | **{③④⑤} ∪ 保留侧;①② 均禁** |
> >
> > **补后两类的实证(v1.16;甲 BLOCKER-2(a)、乙 BLOCKER)**:把
> > `UNRESOLVED_DISPOSITION` 的**全部产生路径**拉出来对表,
> > **§1.1c 多 producer 归并的"disposition 冲突"**与 **SEAL-10 的"删除顺序
> > 未登记"**两条路径,**在 v1.15 的六类中无任何合法取值**——而该字段是必填:
> > 落在这两条路径上的条目要么由实现者挑一个最近的(**裁量**),要么留空(**红**)。
> > 两者的 existential core **都不可逐元素核验**,故**归上半、①② 均禁**。
> >
> > **上半三类禁 ②的理由(甲,比"② 也是全称句"更硬一层)**:② 为真的前提是
> > **"枚举完整"**,而**"枚举之外没有消费者"本身就是一个 ¬∃,与 ① 落在
> > 同一个不可枚举空间上**;而消化路径的形式恰好绕开限制——**人工不写结论,
> > 人工补入"消费者集合 = {t1, t2}"这一"事实输入",判据据此机械产出 ②,
> > SEAL-8b 重算得同一结果(输入相同)→ 三道闸门全绿,测试被删**。
> > **下半三类可产出 ② 的理由**:此时**消费者集合已由 `SEAL-16b`
> > 【消费者集合完整性门禁】封闭**,人工补的只是**已枚举条目的正面分类证据**,
> > 其 existential core **可逐元素核验**。
> > **v1.16 必须补的一步(甲 BLOCKER-2(c))**:v1.15 的上/下半划分**全部理由**
> > 就压在这个门禁上,而全文搜"完整性门禁"**只有两处叙述性出现
> > (变更块一处、本段一处)——没有编号、没有断言、没有 B-8 记录字段、
> > 没有违例 fixture**。**一个不存在的门禁承担了"哪一类删除可被人为抵达"
> > 的全部分界。** 本版立为具名断言 `SEAL-16b`(见 §1.1d),
> > **上/下半归属由该门禁的记录状态机械产出,不得人工指定**。
> > **① 在六类下一律永禁**——它的核心是**空集本身**,证据只是"没找到",
> > 什么可审的正产物都不留。
> > **④⑤ 明确放行**:其 B 维度依赖的是**冻结台账**,**有限可枚举**,
> > 属类一"具名见证"的适用范围。
> > **(三)若补入事实输入后判据判出的终态【落在 `uncertainty_kinds` 各成员
> > 输出域的交集之外】,该项不得凭消化清零**,须走"**扩充判据能力
> > (新增 capability branch + golden + 正控制)后重跑**"。
> > **禁 ② 不会再堵 seal**:**判据在完整输入下自行判出 ② 的条目根本不落
> > `UNRESOLVED_DISPOSITION`,不受本出口约束**;受约束的只有"判据判不出、
> > 靠人给集合"的那一类——**而那正是该卡住的一类**。
> 消化记录落 **B-14a**;**未经消化不得计为清零**。

**合法组合(五元组;逐一列出,表外一律非法,SEAL-11 拦截)**

| # | scan_resolution | ledger_membership | reconciliation | admission | disposition |
|---|---|---|---|---|---|
| R1 | `SCAN_UNRESOLVED` | 任一 ※ | `NOT_YET_COMPUTED` | `PENDING_ADMISSION` | `NOT_APPLICABLE` |
| R2 | `RESOLVED` | `PRESENT` | `MATCHED` | **仅** `NOT_REQUIRED` | `PENDING_TRIAGE` → 五终态 / `UNRESOLVED_DISPOSITION` |
| R3 | `NOT_APPLICABLE` | `ABSENT` | `LEDGER_ONLY` | `PENDING_ADMISSION` → (`ADMITTED` \| `ALREADY_REMOVED` \| `REJECTED_NOT_SHIM`) | `ADMITTED` 同 R2;其余 `NOT_APPLICABLE` |
| R4 | `NOT_APPLICABLE` | `UNKNOWN` | `INDETERMINATE` | `PENDING_ADMISSION` → (`ADMITTED` \| `REJECTED_NOT_SHIM`) | 同 R3 |
| R5 | `RESOLVED` | `UNKNOWN` | `INDETERMINATE` | 同 R4 | 同 R3 |
| R6 | `RESOLVED` | `NO_LEDGER_KEY` | `UNREGISTERED_CANDIDATE` | `PENDING_ADMISSION` → (`ADMITTED` \| `REJECTED_NOT_SHIM`) | 同 R3 |
| **R7** | **`NOT_APPLICABLE`** | **`PRESENT`** | **`LEDGER_PRESENT_NO_FINDING`** | `PENDING_ADMISSION` → (`ADMITTED` \| `REJECTED_NOT_SHIM`) | 同 R3 |

> ※ **R1 的"任一"是 E1–E4 四格【同值】(均 `NOT_YET_COMPUTED`)的无损压缩**
> (v1.14 补脚注,乙):**它不是"任取一值都合法"的省略,而是四格取值相同故
> 可合并书写**;与 v1.11 禁掉的那种**冲突型"任一"**(不同格取不同值却写成
> "任一")**不同构**。**展开后仍是四行,SEAL-11 按展开式核验。**

**显式非法组合(SEAL-11 逐条拦截)**

| 组合 | 为何非法 |
|---|---|
| E6(`EXISTENCE_CONFLICT`)/ E12 两格 | 见导出表;**两者性质不同:E6 是两个独立源的【经验性冲突】(具名、逐格记录、附两侧证据),E12 是【定义上不可能】(不具名)**——**不得以同一条 fixture 同时充当两者的反向验证** |
| `SCAN_UNRESOLVED` × 非 `NOT_YET_COMPUTED` | 该项 reconciliation 尚未产出 |
| `RESOLVED`/`NOT_APPLICABLE` × `NOT_YET_COMPUTED` | 该项已可产出 |
| `INDETERMINATE` × `ALREADY_REMOVED` | **"没看清"不得被判为"已删除"**(漏删路径) |
| **`LEDGER_PRESENT_NO_FINDING` × `ALREADY_REMOVED`** | **"还在树里"不得被判为"已删除"**(v1.14) |
| `INDETERMINATE` × `SCAN_UNRESOLVED` | 时序前提 |
| 未入册项 × 非 `NOT_APPLICABLE` 的 disposition | SEAL-11b |
| **`LEDGER_KEY_AMBIGUOUS` 出现** | **`|π(c)| > 1`**(同一 candidate 配到两个台账 key,§1.1c-0),**须阻塞而非归并**;**π⁻¹ 侧不再受基数约束**(v1.15 随动改:`|π⁻¹(k)| ≤ 1` 已撤销) |

> **`effective_inventory` = {R2 全部} ∪ {admission = `ADMITTED`}**;
> **入册成员资格与 disposition 的充要关系——见 SEAL-11b**(v1.15:同上,
> 原为整句重述,**定义唯一留在 §1.1d**)。

**候选粒度(四级;台账 key 与之同粒度同格式)**

| 级 | 定义 | 承担维度 |
|---|---|---|
| ① | **整模块** | D1 |
| ② | **任一模块内的单个 re-export binding**(含 `__all__` 条目同步) | D2 / D4 |
| ③ | **内联 import binding** | D4 |
| ④ | **`PROXY_CALLABLE`**:**callable 级** | D3 |

**粒度④ 规格**

> **发现判据**:**存在任一 callable——含顶层函数、`async` 函数、类方法、
> `property`/descriptor、模块级 `__getattr__`——其函数体为对单一外部模块的
> 纯委托** → 产出候选。**无其他必要条件。**
> **不得设"跨顶层包"必要条件**:同顶层包内兼容壳的存在性见
> `OBS-6.intra-package-shim`,**本节不陈述其结论**。
> **规范判断**:发现面**不得使用会结构性排除该形态的必要条件**;
> **裁决预算只能影响排期或增加资源,不得收窄发现面的正确性**。
> "跨顶层包 ∨ 宿主 ∈ 台账已登记 shim 宿主"**降为分级优先级与 admission 证据**。
> **判据只负责发现,不负责定性。**
> **三种不确定性 → `scan_resolution = SCAN_UNRESOLVED`**:非白名单装饰器包装 /
> 宿主含副作用或可变状态 / 多委托目标或目标不可静态确定。
> **开工前排期检查**:`OBS-6.proxy-count` 与 `OBS-7.class-c-projection`
> 与裁决预算对比;**超阈值时调整排期或增加资源,不得回头收窄判据**。
> **已冻结的四种假阴形态**(部分转发 / 类方法级 / 装饰器生成 / 宿主副作用)
> 属类三·规则常量,**是 12b-10 正控制的取材清单**。

**candidate ID 规格**——全局唯一,**不含行号**:

```
粒度①  <仓库相对路径>#MODULE
粒度②  <仓库相对路径>#REEXPORT#<public bound name>
粒度③  <仓库相对路径>#INLINE#<public bound name>@<lexical qualname>
粒度④  <仓库相对路径>#PROXY#<callable 的 lexical qualname>
```

**ID 锚点 = public bound name**;**原始 qualified name 必须保留为 metadata**;
**粒度③④ 用 lexical qualname**。
**同一模块内 public bound name 重复即红——见 SEAL-7b**(v1.15:此处原为整句
重述,与 §1.1d 的定义构成同一标识符的两处定义式书写(当时由文档自检对账查出;该机制已于 v1.24 移除,此处仅作历史说明);
**改为引用,定义唯一留在 §1.1d**)。
**台账 key 使用同一四种格式**(§1.1 第 1 条);
**π 的配对按【粒度归一】判定**(§1.1c-0)——**不是两侧 ID 逐字相等**;逐字相等只是"同粒度且同名"这一特例(v1.16 随动:甲 BLOCKER-1、丙、乙)。

**多 producer 归并与落未决规则**:
- span 增 **`guard` 字段 = 完整 path-condition 指纹**;
- **互斥 guard 的多 producer 归并为同一逻辑 binding 的多个 producer span**,
  **不落未决**;**该归并不计入 SEAL-7b 的"重复"**
  (v1.15 恢复理由句:**若无此例外,合法的条件式同名绑定会被误红并阻塞 seal
  ——那是活性 bug,直接撞终止条款**);
- **仅当以下之一成立才落 `UNRESOLVED_DISPOSITION`**:①各 producer 的
  **disposition 冲突**;②**guard 非互斥或互斥性不可判定**。

**互斥性判定规则(五条)**

| # | 形态 | 判定 |
|---|---|---|
| 规则一 | **`if`/`elif`/`else` 同一结构节点的不同分支** | **结构上互斥,可机械判定** |
| 规则二 | **嵌套条件** | 由**完整 path-condition 的布尔结构**判定 |
| 规则三 | **封闭表达式域**:`sys.platform`、`sys.version_info`、`__debug__` | **仅对受支持的封闭表达式域求解** |
| 规则四 | **`try`/`except`** | **默认不可证明互斥**;**仅八条 AST 谓词全部满足时放行** |
| 规则五 | **两个独立 `if` 语句**、运行时 feature flag、**`contextlib.suppress`** | **不可判定 → 卡死**(fail-safe 误伤,**接受**;其消化出口见 `UNRESOLVED_DISPOSITION`) |

**规则四的八条 AST 谓词**

```
放行条件(须全部满足,任一不满足 → 卡死):
  P1. try.body 恰为一条语句,且为 Import/ImportFrom,并原子地绑定目标名;
      排除 `from x import *`;区分 `import a.b`(只绑顶层 a)
      与 `import a.b as m`(绑 m),目标名须按实际绑定名取。
  P2. handlers 恰一项;捕获类型 ⊆ {ImportError, ModuleNotFoundError},
      且该异常名须解析到 builtins(防局部遮蔽)。
  P3. handler.body 恰为一条语句,且是对同一目标名的另一 Import/ImportFrom。
  P4. orelse == [] 且 finalbody == []。
  P5. 每个 import 语句恰一个 alias。
  P6. `except ... as e` 的异常绑定名不得与目标名相同。
  P7. try.body 与 handler.body 之外无其他语句参与该名字的绑定;
      作用域定义为模块顶层数据流,含 global 声明、嵌套作用域写入、del、
      以及任何动态名称写入(后者一律卡死)。
  P8. 两条 import 的目标名逐字相同。
```

> **任何额外语句、调用、赋值或未知异常路径均判不可证明互斥。**
> **默认设在安全侧、只对可证的窄形态开口。**

**多 span 契约**:`spans: [ (file, line_start, line_end, kind, guard) ]`。
- **`kind`**:`import_stmt`、`all_entry`、`inline_import`、`alias_assignment`、
  `dynamic_all`、`proxy_def`、`module_getattr`;后两类中的
  `dynamic_all`/`module_getattr` 一律落 `DYNAMIC_UNRESOLVED`;
- **允许 `len(spans) ≥ 1`**;**"同删同留"**:现有 span 全集同进退,
  **部分处置即红**;**span 不得跨 candidate 重复**(SEAL-7);
- **不变式**:**`__all__` 与其约束的 import 永远同文件**。

**跨 candidate re-export 链耦合**:凡存在 re-export 链者,**须在 disposition 中
显式登记删除依赖顺序**;未登记即 `UNRESOLVED_DISPOSITION`(SEAL-10)。

### 1.1d seal 前提

| # | 断言 | 阶段 |
|---|---|---|
| **SEAL-1** | **每个权威源的 obligation 与解析产物精确相等,【按该来源自身声明的粒度】比较**(v1.15:v1.14 要求统一展开到 binding 级,无展开基准故不成立,见 §1.1);无法机械枚举其自身粒度 → `SOURCE_OBLIGATION_UNENUMERABLE`,**fail-closed**;**不得以当前树为基准反向展开台账**(元规则(四):输入侧不得派生) | **admission 期** |
| **SEAL-2** | 每条 provenance **四字段齐全**;第三段另须带**实际抽取提交 SHA** | **标准化期** |
| **SEAL-3** | **无 `SCAN_UNRESOLVED`**、**无 `NOT_YET_COMPUTED`**、**无 `PENDING_ADMISSION`**;`REJECTED_NOT_SHIM` 必带逐项结构化证据 | **admission 期** |
| **SEAL-4** | 每个 `LEDGER_ONLY` / `INDETERMINATE` / **`LEDGER_PRESENT_NO_FINDING`** 项已获终态 admission 值(**后两者均不得取 `ALREADY_REMOVED`**) | **admission 期** |
| **SEAL-5** | `DYNAMIC_UNRESOLVED` **为 0**;**每条销账附六字段证据链** | **admission 期** |
| **SEAL-6** | `PENDING_TRIAGE` **为 0** 且 `UNRESOLVED_DISPOSITION` **为 0**——**后者须经 §1.1c 的消化出口清零**(**补事实输入 + 判据重判 + 输出域限定**),**不得以"无出口"为由带病 seal,亦不得以人工直接裁定终态的方式清零** | **disposition 期** |
| **SEAL-7** | **candidate ID 全局唯一**;**span 不跨 ID 重复** | **标准化期** |
| **SEAL-7b** | **同一模块内 public bound name 重复即红**;**互斥 guard 的归并不计入"重复"** | **标准化期** |
| **SEAL-8** | `effective_inventory` **每个条目恰有一个 disposition 终态值** | **disposition 期** |
| **SEAL-8b** | **disposition ⟺ 其判据**;**其"机械重算"与判据实现同源,故须由 12b-11 的 golden cases 外部兜底**(元规则(七));**对经消化的条目照常重算,【不开人工洞】**(v1.14) | **disposition 期** |
| **SEAL-10** | 跨 candidate re-export 链的**删除依赖顺序已显式登记** | **disposition 期** |
| **SEAL-11** | 全部条目的**五元组**落在可达组合表(**R1–R7**,R1 按四格展开)内;**显式非法表逐条拦截**;**导出表 12 格全函数**;**`\|π(c)\| ≤ 1`**,否则 `LEDGER_KEY_AMBIGUOUS` 阻塞;**台账侧覆盖义务成立**(每个台账 key 由 §1.1c-0 七格分类器**终态求值**恰落一格:第 7 格计数须为 0,第 1 格与第 2–6 格均为本阶段的合法出口;**第 1 格(暂态)的清零是终局条件,由 §1.3 断言二承担,本断言在 disposition 期不求值它**(v1.27;甲 BLOCKER-2);**落第 3 格的祖先 key 不在本断言"全部条目"的五元组核验之内**,其记账见 §1.1c-0);**`EXISTENCE_CONFLICT` 计数 = 0** | **disposition 期** |
| **SEAL-11b** | disposition ∈ 五终态或入册后过渡态 **⟺** 条目 ∈ `effective_inventory` | **disposition 期** |
| **SEAL-12** | **独立发现集全部进入 reconciliation**——**`NON_SHIM_PREDICTION` 条目一视同仁,不得被抑制** | **扫描期** |
| **SEAL-12b** | **扫描完整性、检出能力与判定正确性协议**——见 §1.1e,**十三条**全过方可(**汇总门**:十三条各按自身阶段求值,本条只在终局汇总;v1.25 由扫描期改为终局,丙 MAJOR-2) | **终局** |
| **SEAL-13** | **解析层扫描已执行且命中已分流**;命中为零须**显式记零** | **扫描期** |
| **SEAL-14** | **规格锚点核验**——`ANCHOR-3/4/5` 的**机械 selector(非行号)仍命中所述代码** | **扫描期** |
| **SEAL-15** | **观测一致性**——按 claim 型分治(§8-2);**含型别默认反转、三条禁止、豁免清单四条上界、`ASSERTION` 无 predicate 块或块为空即红** | **终局** |
| **SEAL-16b** | **消费者集合完整性门禁(v1.16 新立;v1.17 补结构化派生式与分支级正控制,丙 BLOCKER-4)**。**`CLOSED` 的派生式(类三,不得由自然语言判定)**:`CLOSED` ⟺ **该条目的全部消费者 capability branch 均已执行** ∧ **无 `FAILED` / `UNSUPPORTED` / `DYNAMIC_UNRESOLVED`** ∧ **每条调用边均带 provenance**;四项缺一即 `NOT_CLOSED`。**另立 `consumer_closure_registry`**,与 capability registry / §1.1 原子形态表 / 正控制目录、**以及由完整 tree / callsite 枚举器产出的【实际参与点集合】**做**五方双向精确覆盖**(v1.18 补第五方;丙 BLOCKER-7:**四者都是声明表,可以一致地漏掉同一种消费者形态**——互证不是外锚),差集非空即红;**对账键 = `(原子形态 ID, capability_branch)`**(v1.25 补;甲 BLOCKER-2。v1.26 按 §1.1 原子形态表确定:两者一一对应),五方的投影方式:①`consumer_closure_registry` —— 每条闭合记录覆盖的 (形态, 分支) 对;②capability registry —— **`consumer.*` 命名空间内的每个分支**声明支持的形态(须恰为去前缀后的同名形态;其余命名空间的分支不进入本条对账,v1.27);③§1.1 原子形态表 —— 逐行 (形态 ID, `consumer.<形态 ID>`);④正控制目录 —— 每条分支级正控制所属的 (形态, 分支);⑤实际参与点集合 —— 每个参与点经独立参与点分类器判定的 (形态, 分支);**参与点命中未登记形态、命中多个形态、或命中零个形态 → 阻塞;名字命中兜底中未得去处的命中同样阻塞**(v1.28);**投影须逐条可追溯到原记录**,不得只给投影后的集合;**与 `12b-12` 的分工**:本条管**消费者形态面**(§1.1 原子形态表),`12b-12` 管**不覆盖九类面**(§1.1b 九类表,键 `(capability_branch, detector_owner)`);两条共用 capability registry 与正控制目录,**按命名空间分投影(本条只取 `consumer.*`,`12b-12` 只取其余;v1.27),互不替代、不合并计数**;**每种消费者形态各配一条分支级正控制**;**另补构造式控制:删除一条注册边后必须红**。对每个进入 disposition 判据的条目,**其消费者集合须由 `scan_manifest` 全集 + 闭合调用图机械封闭**,封闭结果逐条落 B-8 的 `consumer_set_closure` 字段(**空记录即红**);**该字段的取值(`CLOSED` / `NOT_CLOSED`)是 `uncertainty_kinds` 上/下半归属的【唯一】依据,不得人工指定**;违例 fixture:**构造一个消费者集合未封闭的条目,其 `uncertainty_kinds` 必须落上半、② 必须被禁** | **admission 期** |
| **SEAL-16** | **观测定义/引用精确覆盖**;差集非空即红;**本断言的引用集即 §8-2「型别默认反转」的锚**(**v1.14 修正悬挂引用**:v1.13 写"即闸门 2 的锚",而闸门编号体系已在同版被"默认反转 + 三条禁止"取代,**`闸门 2` 在规范正文中零处定义**) | **标准化期** |
| **SEAL-9** | **终局闸门:以上全部通过后**(**"以上全部"【含 §1.3 的四条断言】,且全部在冻结前求值**,v1.15 明写),才冻结 `effective_inventory` 的 hash,**并先断言【冻结集合与 `preseal_effective_inventory` 逐项相等】**,**并一并冻结 per-candidate 的 disposition evidence bundle**(否则删除后无法判断当初是"判据写错"还是"执行错",而两者修法完全不同) | **终局** |

**SEAL-8b 的谓词展开**

```
① DELETE_DIRECT                  ⟺ A=否 ∧ 消费者集合 = ∅  (§1.1 原子形态表全部形态 + 解析层全查后)
④ KEEP_PRIVATIZED                ⟺ A=是 ∧ B=无
⑤ NOT_SHIM_REAL_DEPENDENCY       ⟺ A=是 ∧ B=有
② DELETE_AFTER_TEST_REMOVAL      ⟺ A=否 ∧ 消费者集合 ≠ ∅
                                  ∧ 全部消费者 ⊆ tests/**
                                  ∧ 闭合调用图的 assertion leaves 全部
                                    ∈ 可信叶子白名单
                                  ∧ 这些叶子在【其实际调用形态】下的
                                    semantic_class 全部 ∈ {IDENTITY, EXISTENCE}
③ DELETE_AFTER_CONSUMER_MIGRATION ⟺ A=否 ∧ 消费者集合 ≠ ∅
                                  ∧ ( 存在非 tests/** 消费者
                                      ∨ 存在 semantic_class = BEHAVIOR 的
                                        测试消费者 )
```

> **五类互斥(v1.25 补;丙 BLOCKER-1)**:先按 **§1.2 维度 A 的权威定义**(全函数;v1.27 收归 §1.2 一处,甲 BLOCKER-1)计算 A。
> A=是 时只落 ④/⑤(由 B 决定);A=否 时只在 ①②③ 中选取,三者谓词互斥;
> **A=否 且 ①②③ 均不成立 → `UNRESOLVED_DISPOSITION`**(即 §2 的 (c) 类)。
> v1.24 及以前 ①②③ 的谓词没有 `A=否` 前提,A=是 且有生产消费者的条目会同时满足 ③ 与 ④/⑤,
> 与 `SEAL-8`"恰一个终态"矛盾。

> **① 的特殊地位(v1.14 明写)**:**① 以 ¬∃ 为谓词**(**v1.16 更正**:v1.14 写"五终态中唯一",而 v1.15 变更⑥ 已判定 ② 的前提"枚举完整"同样落在不可枚举空间上,"唯一"不成立;乙),
> 故 **`UNRESOLVED_DISPOSITION` 的消化出口永禁产出 ①**(§1.1c),
> 且 **§8-2 类一对 ∀/¬∃ 的手填禁令对它优先适用**。

**闭合调用图与可信叶子白名单**

"全部断言"**必须递归穿透** helper、fixture、参数化回调与自定义 assertion
wrapper。**但"调用图不闭合即卡死"若无白名单,会变成活性问题**——凡用库断言的
测试全部落 (c) → **seal 永远无法完成**,**直接撞上终止条款**。

> **可信断言叶子白名单(类三·规则常量;登记于 A₀)**
> **键 = `(qualified callable, 调用形态/实参谓词)`**。
> **形态枚举的范围限定**:**只需穷尽本仓实际出现的等价类**
> (位置参数数 / 关键字参数名集合 / 是否作 context manager / 是否嵌在比较
> 表达式中)。新形态 → 无标注 → 卡死 → 走变更流程,**每次只卡一条**。
> **精确分区断言**:**实际 leaf call site 集合 = 各形态谓词匹配集的
> 【不交并】**;**零匹配 / 多匹配 / 动态实参 → `SEMANTICS_AMBIGUOUS` → 落 (c)**。
>
> **种子成员(类三·就地列举)**:
>
> | 键(callable × 形态) | `semantic_class` | hash 对象 |
> |---|---|---|
> | `assert` 语句 × 比较表达式 | 依表达式结构判定 | 语言构造,无 hash |
> | `pytest.raises` × 作 context manager | **`BEHAVIOR`** | 分发版本 + 安装 artifact / 环境锁 hash |
> | `pytest.raises` × 作可调用参数形式 | **`BEHAVIOR`** | 同上 |
> | `pytest.warns` × 作 context manager | **`BEHAVIOR`** | 同上 |
> | `pytest.approx` × 嵌于比较表达式 | **`BEHAVIOR`** | 同上 |
> | 本仓登记的 assertion helper × 各实际形态 | 逐形态标注 | **源码 AST hash** |
>
> - **无法以有限形态覆盖者标 `SEMANTICS_AMBIGUOUS` → 落 (c)**;
>   **无法区分时保守标 `BEHAVIOR`**(只影响可删性、不影响闭合,**seal 仍可达**);
> - **hash 只检测漂移,构造式语义测试才证明标签,二者不可互相替代**;
>   **每个登记形态分别证伪**(**v1.14 恢复**;v1.13 未申报删除,
>   丢失后"逐形态语义测试"退化为"抽一个形态测一次");
> - **白名单只表示"调用图可在此闭合",不表示"可删测试"**;
> - **扩充走变更流程,不由实现者临时判断。**

**求值阶段分层(v1.16 新增;甲 MAJOR-3)**:v1.15 只为 12b-8 与 §1.3 四条断言
补了求值时点,而**依赖后阶段事实的断言至少还有五条**——`SEAL-4`(依赖 admission
终态)、`SEAL-8` / `SEAL-8b`(依赖 disposition 终态)、`SEAL-11b`(依赖 admission +
disposition)、**§1.1c-0 台账侧覆盖义务**(依赖 π 完成 + `LEDGER_*` 全部赋值)。
其中 `SEAL-8`、`SEAL-11b` **正是当时为 12b-8 那一行列出的"该对账的四行"**(历史说明):
它们被列进了对账、标了"已同步改",而**同步的是集合口径,不是求值时点**。
**逐条补偏序会让对账面成倍增长**,故改为分层:

> **五个求值阶段(类三·就地列举)**:**扫描期 → 标准化期 → admission 期 →
> disposition 期 → 终局**。**每条 SEAL / 12b 断言就地标注其求值阶段**;
> **每条断言只在其阶段【及之后】求值;跨阶段提前求值即红。**
> **阶段列就地标注于 §1.1d 的 SEAL 表与 §1.1e 的 12b 表**(v1.17:v1.16 把归属
> 写成了表外一段散文,于是"某条没标注"在表上不可见 —— 甲 MINOR-1;
> **"就地标注"须字面落实为【表的一列】**)。
> **可机械核验(v1.18 落实)**:**每行【阶段列】非空 ∧ 取值 ∈ 六阶段就地列举
> (扫描期 / 标准化期 / admission 期 / disposition 期 / 终局 / A₀ 期);未标注即红**;
> **且表内阶段列与下方分组表【双向精确覆盖】,差集非空即红。**
> **同期内按依赖闭包求值,循环依赖即红。**
> **v1.18 的两处更正(甲 MAJOR-1、丙 BLOCKER-4)**:
> **(a)** v1.17 承诺"把就地标注字面落实为表的一列",而两张权威表表头**仍是两列**,
> 阶段归属**又一次写成表外的分组表** —— **"阶段列非空"这条核验指向一个不存在的列**,
> "某条没标注"在表上仍不可见,**这正是 v1.16 漏掉 `SEAL-14`/`SEAL-15` 的机制**。
> 本版已给 §1.1d 的 SEAL 表与 §1.1e 的 12b 表**各加一列,34 行逐行填满**。
> **(b)** v1.17 写"取值 ∈ **五**阶段"而分组表实列**六行**(含 A₀ 期),
> 按字面 `12b-9`…`12b-12` 四条会被核验红掉。已改为六阶段。
> **分组表自本版起降为【核验用的期望值】**,与表内阶段列双向覆盖,任一侧漏写即红。
> **正控制**:清空某行阶段列 → 必红;表内写"终局"而分组表列在"disposition 期"
> → 双向覆盖差集非空 → 必红。**near-miss**:两侧一致 → 不红。
>
> | 阶段 | 断言 |
> |---|---|
> | **扫描期** | `SEAL-12`、`SEAL-13`、`SEAL-14`、`12b-1`…`12b-7` |
> | **标准化期** | `SEAL-2`、`SEAL-7`、`SEAL-7b`、`SEAL-16` |
> | **admission 期** | `SEAL-1`、`SEAL-3`、`SEAL-4`、`SEAL-5`、`SEAL-16b` |
> | **disposition 期** | `SEAL-6`、`SEAL-8`、`SEAL-8b`、`SEAL-10`、`SEAL-11`、`SEAL-11b`、`12b-8` |
> | **终局** | `SEAL-9`、`SEAL-12b`(汇总门)、`SEAL-15`、§1.3 四条断言 |
> | **A₀ 期(先于扫描期;检查器投产前置)** | `12b-9`、`12b-10`、`12b-11`、`12b-12` |
>
> **v1.17 的四处更正(甲 MAJOR-1、丙 BLOCKER-3)**:
> **(a) 补两条漏标**——v1.16 的 SEAL 表实列 21 条而散文只覆盖 19 条,
> **`SEAL-14`、`SEAL-15` 完全未分配阶段**;12b 十三条**只标了 `12b-8` 一条**。
> 未标注 → "只在其阶段及之后求值"无从判定 → 实现者自定,**朝开**。
> **(b) `SEAL-11` 由标准化期改判 disposition 期**——它断言"全部条目的**五元组**
> 落在可达组合表内",而五元组含 `admission` 与 `disposition` 两维,
> 在标准化期**尚不存在**;提前求值要么真空绿、要么误红。
> **(c) `SEAL-1` 由标准化期改判 admission 期**——§1.1c-0 时序出口写着
> "`UNENUMERABLE` 先落暂态 → `DYNAMIC_UNRESOLVED` 销账后重跑枚举",
> 而**销账归 `SEAL-5` = admission 期**:`SEAL-1` 的终判依赖一个 admission 期的产物。
> **(d) `SEAL-16b` 由标准化期改判 admission 期**——其消费者闭合结果决定
> disposition 的删除能力,须在 admission 终态化之后求值(丙)。
> **这比逐条打补丁少一个数量级的对账面,而阶段名本身是类三常量。**

**反向验证(每条 SEAL 断言各配至少一个违例 fixture;清单以附录 B-11 为准)**:
- **SEAL-1**:从一个仍非空的来源中删除一个条目;**以及一个连【自身声明的粒度】
  都无法机械枚举的来源**(须落 `SOURCE_OBLIGATION_UNENUMERABLE`);
  **near-miss:一个自身声明粒度为整模块的来源**(须正常映射 `#MODULE`,
  **不得落 `UNENUMERABLE`**)
  ——**v1.18 真改**(甲 BLOCKER-1):v1.15/v1.16/v1.17 三版此处逐字相同,
  而事故 (54) 的状态格**连续两版写"已修"并写明了改后措辞**;
  旧写法要求"只能展开到模块级的来源必须落 `UNENUMERABLE`",而现行 `SEAL-1` 是
  "按来源自身声明的粒度比较"、§1.1 是"整模块义务只能映射 `#MODULE`"
  ——**模块级是合法且常见的正常输入,旧 fixture 断言它必红 → 合法输入必红
  → seal 不可达 → 撞终止条款**;
- **SEAL-11**:构造落在**显式非法表**内的组合;**一个导出表未覆盖组合**
  (须落 `UNKNOWN_RECONCILIATION` 而非默认值);**一个 `|π(c)| = 2` 的
  candidate**(须落 `LEDGER_KEY_AMBIGUOUS`);**一个 E6 组合**(须落
  `EXISTENCE_CONFLICT`、逐格记录并附两侧证据——**与 E12 的 fixture 不得合并**);
  **以及一个七格分类器表外组合的台账 key**(须落 `UNKNOWN_LEDGER_EXIT` 阻塞);
  **一个暂落第 3 格、而覆盖它的 candidate 全部被 `REJECTED_NOT_SHIM` 的祖先 key**
  (admission 终态化后须转入第 4–6 格并生成台账侧 item;仍留第 3 格即红);
- **SEAL-4**:构造一个 `LEDGER_PRESENT_NO_FINDING` 项并尝试裁为
  `ALREADY_REMOVED`(**须红**);
- **SEAL-6**:构造一个经消化但由人工直接写结论的条目(**须红**);
  **一个 `uncertainty_kind = CONSUMER_SET_COMPLETENESS` 却由人工补入消费者
  全集、判据据此产出 `DELETE_AFTER_TEST_REMOVAL` 的条目**(**须红**——
  这是 v1.14 的后门形态);**以及一个消化后终态落在 `uncertainty_kinds` 交集输出域之外
  合法输出域之外的条目**(**不得凭消化清零**);
- **SEAL-12**:扫描发现了一项但未进入比对;**以及一个 `NON_SHIM_PREDICTION`
  条目的 finding 被抑制**;
- **SEAL-12b**:见 §1.1e 的**十条**违例;
- **SEAL-8b**:含"断言藏在 helper 里的行为型测试";
- **SEAL-15**:`ASSERTION` 四条 + `MEASUREMENT` 一条 + **型别三条**
  (**空 predicate** / **解析失败** / **被引用却列入豁免清单而无理由**)
  + **豁免清单四条**(**通配形式** / **被决策条款引用** / **带 `GATE` 引用** /
  **带 predicate 块**);
- **SEAL-16**:定义一个从未被引用的 claim / 引用一个未定义的 claim key。

**只会亮绿灯的闸门比没有闸门更危险。**

### 1.1e SEAL-12b:扫描完整性、检出能力与判定正确性协议(十三条)

> *(脚注:**`12b-7` 是既有编号空洞**,自设立起即未使用,**非任何版本的删除**;
> 条数以实列为准。)*

| # | 断言 | 阶段 |
|---|---|---|
| **12b-1** | **`scan_manifest` = 固定 tree hash 下的完整 git tree 全集**——**无"受控目录"概念**;全部 tracked entry、gitlink、symlink mode **先全部进入**,**不做任何减法**;**不得由任何文档清单派生** | **扫描期** |
| **12b-2** | **输入面相等**:已处理条目集 **==** `scan_manifest`(**精确划分**) | **扫描期** |
| **12b-3** | **适用性由外部冻结注册表计算**;**detector 不得自报 `NOT_APPLICABLE`**;每格取 `SCANNED`/`FAILED`/`UNSUPPORTED`/`NOT_APPLICABLE`;**`FAILED` 与 `UNSUPPORTED` 阻塞**;**格级:缺记录即红** | **扫描期** |
| **12b-3b** | **行级下界(无豁免)**——每个 entry **∃ detector 判 `SCANNED`**;**`NON_SHIM_PREDICTION` 不豁免本义务** | **扫描期** |
| **12b-3c** | **注册表完备性四条**:①键 ⊇ 封闭 universe 全部 kind;②**查找未命中 = `UNSUPPORTED`(红)**,**永不得按空量词处理**;③**分类器须全函数**,未知 → `UNKNOWN_PROVIDER_KIND` 阻塞,**不得回落默认**;④**与 detector capability 双向精确覆盖** | **扫描期** |
| **12b-4** | **零解析错误 fail-closed**;**无法 AST 解析的模块单元 → `DYNAMIC_UNRESOLVED`** | **扫描期** |
| **12b-5** | **完成标记与原子落盘**;**无 completion marker 的输出视为不存在** | **扫描期** |
| **12b-6** | **三阶段同 tree hash 与 run ID 绑定** | **扫描期** |
| **12b-8** | **`NON_SHIM_PREDICTION`(v1.14 由 `EXCLUDED` 更名)不产生任何豁免**——不影响 candidacy、不抑制 finding、**不免 12b-3b 的行级下界**、仍进 reconciliation。**既然它不做任何减法,元规则(五)对它不适用,不需要上界。** 它是**一条已登记的、可证伪的预测**("此条目不是 shim"),其**证伪钩以【销账/消化后的终态】判定**:**该条目最终进入 `preseal_effective_inventory` 即预测被证伪 → 红**。**求值点具名(v1.15;甲 MAJOR-2、丙 MAJOR)**:**在 SEAL-3 通过(admission 终态化)之后、SEAL-9 之前求值**——本条属 SEAL-12b(扫描完整性协议),而其判据是一个 **admission 之后才存在的事实**,而全文**只有 SEAL-9 被排序**,SEAL-1…SEAL-16 相互之间无序;**若按所在协议的语义在扫描阶段求值,此时集合尚未计算 → 计数为 0 → 稳定恒绿**,排除规则唯一的证伪钩就此失效。**不再以"是否产生过 finding"判定**——旧口径与 12b-1 的 manifest 全集 + 解析层全分流叠加后,**任何被覆盖的 symlink/gitlink/打包入口在分流产生的那一刻即永久红且无销账路径**(撞终止条款)。**"未决分流"不再被称作 finding**;**`ledger_membership = UNKNOWN` 是 item 的 membership 状态,不是扫描产物,更不是 finding**。**中间不得静默**:该条目产生的 finding 与未决分流**须逐条落 B-8**,**空记录即红**(不设零门)。**它不承担、也无法承担结构性盲区——盲区由 12b-10 + 12b-12 承担**。**每条排除规则须精确登记匹配集、彼此互斥、带边界负控制、附【为何该条目结构上一律无 shim 候选】的理由字段(空理由即红)**,**且由独立全函数分类器计算,未知类型必红** | **disposition 期** |
| **12b-9** | **违例 fixture 十条**:①删掉一个输入条目;②注入语法错误文件;③扫描中途终止;④manifest 漏收一个仍在版本控制中的条目;⑤**把一条排除规则改宽,使其覆盖一个植入的已知 shim 实例——其候选资格不得消失、且该条目最终进入 `preseal_effective_inventory` 必须触发证伪转红**;**该 fixture 须跑完整条 admission 流水线至 SEAL-3 终态化**(v1.15:否则 fixture 自身在求值点之前完成,**它也恒绿**);⑥注册表把某 kind 错标为不需要任何 detector;⑦**逐条删除一条 required edge**;⑧**恒报 `SCANNED`、findings 恒空的 detector**;⑨**恒报大量假阳的 detector**;⑩**(v1.14 新增)把九类表某行的 `capability branch` 改成 registry 中不存在的名字**——**须被 12b-12 的四方对账捕获**;**十者都必须阻塞 seal** | **A₀ 期** |
| **12b-10** | **detector 检出能力正控制**——粒度 = **`(detector, capability branch)`**,由 capability registry **机械导出**(消费者**原子形态逐形态**(§1.1 原子形态表,分支名 `consumer.<形态 ID>`)、粒度④ 各 callable 形态**逐形态**、解析层五类**逐类**、结构特征 A/B/D **逐类**);**实例目录由 §1.1b 九类承担方映射与粒度④ 四种冻结假阴形态【机械导出】,导出结果落 B-8**;**实现方不得自选**;断言**精确 finding 集**(非"至少命中一次");配 **near-miss 负控制**;**正控制 × detector 与九类承担方映射双向精确覆盖**。**独立参与点分类器**:**枚举实际语法/配置参与点并精确分区到 capability branch**,**未知分支或零命中 → `UNKNOWN_CAPABILITY` 阻塞**(v1.28 补零命中)——registry 双向覆盖只能发现"已登记能力缺测试",**发现不了"整个新能力分支压根没登记"** | **A₀ 期** |
| **12b-11** | **判定层 golden cases**(元规则(七))——落成 **`能力分支 → fixture ID → 输入 → 精确 finding/结论`** 映射:每个 disposition 终态至少一个已知正例、每条互斥规则正/反例各一、A ∧ B 真值表四格各一、入口类分流正/反各一;**期望结论为类三·规则常量,不得由判据实现产出**;**须以外部可观察的终态 disposition 表达,不得复述判据的内部中间变量**;**每条附理由字段,空理由即红** | **A₀ 期** |
| **12b-12** | **(v1.14 新增;三家 MAJOR)四方对账**——**以 `(capability_branch, detector_owner)` 为键**,下列四个来源**两两双向精确覆盖,差集非空即红**:①**独立参与点分类器的输出域**;②**capability registry 的分支集**;③**§1.1b 九类表的 `capability branch` 列与承担方列**;④**正控制/golden 实例目录的分支集**。**投影范围(v1.27;甲 BLOCKER-3、丙 BLOCKER-2)**:四方**只投影 `consumer.*` 以外的命名空间**;`consumer.*` 分支只进 `SEAL-16b`,两条断言从此不对同一分支集提相反要求。**缺的正是"九类承担方(detector 名)↔ registry `required_detectors`(kind)"这一边**——某 kind 被要求由 detector X 扫,而 X 在九类表中不承担任何类(或反之),**此前三处各自绿**。**本条是元规则(八) 在 P4.9 机制内的具名适用对象**;**与 `SEAL-16b` 五方覆盖的键不同,两条不互相替代**(见 `SEAL-16b`) | **A₀ 期** |

### 1.2 五类处置的判别(A ∧ B 两个正交维度)

- **维度 A「本模块引用」(全函数;本条为权威定义,§1.1d 五类互斥块引用本条;v1.27 统一,甲 BLOCKER-1)**:
  **(a) 候选粒度为 `#MODULE` 或 `#PROXY`(非 binding 粒度)→ A=否**;
  **(b) 候选粒度为 `#REEXPORT` 或 `#INLINE`**:该 binding 在本模块(`#INLINE` 为其所在词法作用域)有 AST `Load` → A=是,无 → A=否;
  **A 对每个候选都有取值,不存在"无法机械判定"**;
  *(v1.26 及以前本条只写"该 binding 在本模块有 AST `Load`",对 `#MODULE` 无定义,按下面的 fail-closed 会把整模块候选全部落
  `UNRESOLVED_DISPOSITION`,① 永不可达;对 `#PROXY` 又与 §1.1d 的写法相反。)*
- **维度 B「前批保护裁决」**:台账中有具名保留裁决(结构化查表键)。

**判定规则 = A ∧ B(真值表为准);补充证据不参与判定**:
- **补充证据(一)**:该 import 是否为**消费者侧的签名依赖**——被导入符号的
  canonical owner 是否在本模块之外。**该归属关系由 `OBS-4.owner-attribution`
  产出,本节不陈述其结论**;**规范判断**:若该 claim 显示 owner 在别处,
  则本条证据成立,**且"本模块是 owner"不得作为 ⑤ 类的判据**;
- **补充证据(二)**:依赖方向符合冻结 ownership/layer;
- **fail-closed**:**A 为全函数,不会无法判定**;**B 无法机械判定** → 不得归 ④/⑤,落
  `UNRESOLVED_DISPOSITION`(其消化出口见 §1.1c);
- **pytest/mypy 仅作补充证伪**,不作定义。

**真值表**:A=是 ∧ B=无 → ④;A=是 ∧ B=有 → ⑤;A=否 → ①②③。
**四格各须一条 golden case**(12b-11),**以终态 disposition 表达**;
**A=否 那一格须同时覆盖 `#MODULE` 与 `#PROXY` 两种来源,A=是 ∧ B=无 那一格须 `#REEXPORT` 与 `#INLINE` 各一例**(v1.27)。

> **④与⑤的本质区别**:④ = "**旧兼容宿主中需要私有化的真实依赖**";
> ⑤ = "**canonical owner 的正常下层依赖**"。
> **⑤ 类的存在意义**:**若无此类,"含 shim 注释即删"会删掉真实依赖。**

### 1.2a 入口类
**具有语言级/打包级特殊语义的文件**——**`__main__.py`、`__init__.py`、
entry-point 目标**——**一律排除出 A 类**,单独归入口类:
- **处置:保留**(除非其全部入口形态均已无消费者,且须经**运行时外部锚**验证);
- **依据**:包的 `__main__.py` 是 `python -m <pkg>` 的 CLI 入口,
  其 subprocess 消费关系见 `OBS-5.entry-consumers`;**按 A 类判据会被判
  "直接删"**,故本类必须存在;
- **其分流须配正/反各一条 golden case**(12b-11)。

### 1.2b 红线
**须区分"兼容 shim"与"真实依赖";误将真实依赖当 shim 删除 → 回滚。**
本红线为**独立条款**,**不得以 DoD 的销账条目替代**。
**回滚触发**:任一被删位置在删除后导致 ①测试红 ②mypy 红 ③运行时加载集合
出现缺失 —— 立即回滚该删除并重新分类。
**重新分类所依赖的判据输入在代码删除后不可原地复算**,
故 **SEAL-9 须一并冻结 per-candidate 的 disposition evidence bundle**。

> **三层兜底**:
> (1)**admission 的 `UNREGISTERED_CANDIDATE`**——扫描发现而台账没有的
> **不得自动删,强制人工裁决**(**最实在的一层**)。
> **其有效性(七项因子的乘积;v1.15 由六项拆为七项)**:
> > **表示能力(SEAL-13) × 自身完整性(SEAL-12b) × 输入面不被裁剪(12b-1) ×
> > 减法有机械上界(§8-2 豁免清单四条上界) × 行级下界(12b-3b) ×
> > 检出能力(12b-10) × 判定正确性(12b-11)**
> > **七项任一为零,这一层就是纸面的。**
> **为何拆(丙 MAJOR;元规则(八) 该抓而未抓到的一处)**:v1.14 的因子④
> 写"**减法有机械上界(12b-3b)**",**引用对象错位**——**`12b-3b` 是行级
> 扫描下界,不是减法上界**;默认反转之后,**唯一的收窄面是豁免清单**,
> 其上界在 §8-2;行级下界是另一回事,**两者合写会让其中一方的缺失被另一方
> 的在册掩盖**。
>
> **作用域声明**:**这七项只描述第一层兜底(发现面)的有效性**;
> "判得对"在 disposition 层由 SEAL-8b + 12b-11 承担,"删得对"由本红线与三条
> 回滚触发承担——**三层各有各的因子,不得读成"这七项管全局"**;
> (2)**本红线的回滚触发第 ③ 条**——把运行时锚接到**删除之后**;
> (3)运行时锚本身的**单向证伪**。

### 1.3 末次收敛判据

> **分母 = `preseal_effective_inventory`**(v1.16 更正:v1.15 此处仍写"seal 后冻结的
> `effective_inventory`",与同节"求值时点"段自相矛盾;丙)。
> **SEAL-9 另断言冻结集合与它逐项相等,冻结后连同 hash 一并登记。**
>
> **断言一(分区)**:每个条目**恰归一个 disposition 终态值**,**空类显式记零**;
>
> **断言二(清零)**:`SCAN_UNRESOLVED` / `NOT_YET_COMPUTED` /
> `PENDING_ADMISSION` / `PENDING_TRIAGE` / `UNRESOLVED_DISPOSITION` /
> `DYNAMIC_UNRESOLVED` **全为 0**(**后二者须经各自消化出口清零**);
> **落在显式非法表内的组合数 = 0**;**导出表未覆盖组合数 = 0**;
> **`LEDGER_KEY_AMBIGUOUS` 计数 = 0**;
> **`SOURCE_OBLIGATION_UNENUMERABLE_PENDING` 计数 = 0**(即七格分类器第 1 格命中数;v1.27 列入,甲 BLOCKER-2);
> **`UNKNOWN_LEDGER_EXIT` / `UNKNOWN_CAPABILITY` / `UNKNOWN_PROVIDER_KIND` 计数 = 0**(v1.25 显式列入;甲 MAJOR-4);
> **发现集与 reconciliation 输入集之差 = 0**;**`scan_manifest` 与已处理条目集
> 之差 = 0**;**`FAILED` 与 `UNSUPPORTED` 计数 = 0**;
> **`NON_SHIM_PREDICTION` 条目【最终进入 `preseal_effective_inventory`】的数量 = 0**
> (v1.17 随动:变更⑬ 已把该证伪钩口径改指 pre-seal 集合,此处 v1.16 漏改;丙)
> (**v1.14 改口径**:v1.13 写的是"产生的 finding 数 = 0",与 manifest 全集 +
> 解析层全分流叠加后会制造**不可销账的永久红**;改以销账后终态计数,
> **中间产生的 finding 与未决分流仍须逐条落 B-8,空记录即红**);
> 并**须断言**:**每个 manifest entry 至少有一个 `SCANNED`**
> (**`NON_SHIM_PREDICTION` 不豁免**)(**此为断言要求,非对当前树的观测**);
> **不得**要求 `UNREGISTERED_CANDIDATE` / `LEDGER_ONLY` / `INDETERMINATE` /
> `LEDGER_PRESENT_NO_FINDING` 本身数量为零;
>
> **断言三(一致性)**:disposition **与其判据的机械重算结果一致**(SEAL-8b,
> **含经消化的条目**);**disposition 存在性与入册成员资格互为充要**(SEAL-11b);
> **每个 claim 按其型通过 SEAL-15**;
>
> **`preseal_effective_inventory`**:**admission 终态化(SEAL-3 通过)之后即可
> 计算的集合,= `{R2 全部} ∪ {admission = ADMITTED}`**;**它是 12b-8 证伪钩与
> §1.3 四条断言的分母**,**SEAL-9 另断言冻结集合与它逐项相等**。
> *(v1.16 补:乙 MAJOR-4、丙。v1.15 中该集合的**唯一"定义为…"书写落在变更块内**,
> 而变更块是非规范区、且下版即被整体替换 —— 规范正文实际上没有 canonical 定义,
> 五处使用全是引用。v1.16 已在规范正文补上 canonical 定义。)*
>
> **求值时点(v1.15;乙 MINOR-2)**:**以上四条断言【在 SEAL-9 冻结前求值】,
> 并纳入 SEAL-9 的"以上全部"**;**分母取 `preseal_effective_inventory`,
> SEAL-9 另断言冻结集合与它逐项相等**。
>
> **断言四(检出与判定)**:**每个 `(detector, capability branch)` 的正控制
> 精确命中、near-miss 负控制不命中**(12b-10);
> **全部判定层 golden cases 通过**(12b-11);
> **四方对账差集为空**(12b-12)。

**为何不能用"复跑后计数为 0"**:⑤ 类**删注释后结构特征即消失**,
候选会"自动"从扫描结果里蒸发,**使收敛判据自我满足**——必须以 seal 冻结的
集合为分母。
**为何分母完整性不能只靠权威源、不能只靠扫描、不能靠"扫描锚到权威源"、
不能靠"锚了但减法随意"、也不能靠"记账闭合"**:
见元规则(一)(四)(五)(六)(七)(八)。

## §2 项 2:测试私有件消费(**表由脚本产出,本节只写生成规则**)

**枚举器规格**:与 §1 消费者识别**共用同一解析引擎(§1.1 原子形态表全部形态)**;额外补对象式
`monkeypatch.setattr(module_obj, …)`、`patch.object`、`setattr`/`delattr`、
**变量驱动 `getattr(module, name_var)`**。

**准入证伪(必做)**:证伪素材**取自台账登记的现存漏检样本集**——
**成员、数量与形态由 `OBS-7.falsification-samples` 产出,本节不书写**。
**引擎须对每一个样本命中;任一抓不到即不得投产;样本集为空即视为未完成,
阻塞 A₀。**
> **与 12b-10 的分工**:准入证伪证明"引擎抓得到**已知漏检样本**",
> 12b-10 证明"**每个 detector 的每个 capability branch** 抓得到它应当发现的
> 实例"——**对象不同,不得互相替代,亦不合并计数**。

**三分规则(实现期逐组判定,不得整批处置)**:
- **(a) 纯接线类**:闭合调用图的 assertion leaves 全部 ∈ 白名单,**且其在实际
  调用形态下的 `semantic_class` 全部 ∈ {IDENTITY, EXISTENCE}** → 随 shim 删;
  **只要有一条 `BEHAVIOR` 叶子即归 (b)**;
- **(b) 仍有行为价值类**:→ 保留测试,改为经公开面或同包内测试;
- **(c) 不可判定**:调用图到达白名单外的外部调用而无法闭合、或叶子标
  `SEMANTICS_AMBIGUOUS`(含零匹配/多匹配/动态实参)、或动态调用无法静态解析
  → **`UNRESOLVED_DISPOSITION`**(其**消化出口**见 §1.1c;
  **该出口永禁产出 `DELETE_DIRECT`**)。
  **(c) 类投影计数须在 A₀ 产出**(`OBS-7.class-c-projection`)
  ——**它会吞掉多少测试应在开工前可见,而不是 seal 时才发现**。

**判定纪律**:逐组判定并附理由,**不得整批放过**;各类**计数由脚本产出**。

## §3 项 3:悬空 symlink 归一化(行为变更)

**规格锚点(类四;SEAL-14 核验)**:`ANCHOR-3` =
`tizen_gerrit_fetch/gerrit.py` 中的**源目录安全检查**;
**机械 selector(非行号)**:该函数内**对目标路径同时调用存在性
判定与符号链接判定的那个布尔合取式**。

- **现状行为**:**由 `OBS-1.item3-predicate` 产出**;**本节不陈述其判定式与
  异常路径的具体内容**;
- **目标**:使源目录安全检查**覆盖悬空符号链接**,即该输入下进入
  `SOURCE_DIR_UNSAFE` 分支而非落到目录创建路径;
- **预期差异**(§6 登记,字段值按 §6 标记值写法;v1.27 统一):**悬空 symlink 场景按 `DIFF_SET` 登记**:
  `GerritError.code` 由 `{"state":"ABSENT"}` → `{"state":"VALUE","value":"SOURCE_DIR_UNSAFE"}`;
  异常类型由现状异常(值见 `OBS-1.item3-predicate`)→ `GerritError`;
  **相邻的非悬空对照场景按 `NO_DIFF` 登记**;**其余输入的全部输出不变**;
  **具体旧值由 `OBS-1.item3-predicate` 与 `expected_diff.json` 提供**;
- 须更新 skill-3 冻结稿中相应的现状描述(**属冻结稿的行为变更记录,非漂移**)。

## §4 项 4:timeout / cancellation 统一(行为变更)

**输入 = skill-5 `v1.3.2` §3.2 的映射表**(条目与顺序见 `OBS-1.item4-anchors`);
**本批只实施 + parity + 评审,不得改动其裁决**。

**规格锚点(`ANCHOR-4`)**:①skill-3 query 阶段 ②skill-3 git 阶段
③submit `_run_git` ④submit `ls-remote` ⑤shared `_run_git`
⑥shared `_exclude_private_files`。

**参数**:各调用面统一 `timeout: float | None`,**默认 `None`**、不强制;
**SIGINT/SIGTERM 不捕获、原样传播**;**残留不自动回滚**;
`GerritSubmitError` 新类型**与 `GerritError` 同形 `(code, message)`**;
`WorkspaceViolation` **不改签名**,以 message 的 `GIT_TIMEOUT:` 前缀承载码。

**验收口径(v1.25 补;丙 MAJOR-4)**:六个调用面**逐面**验收三类场景 ——
**①默认 `timeout=None`**:与变更前 parity;调用轨迹中**唯一允许的差异是新增的 `timeout=None` 关键字实参**;
**②设置 timeout 且超时**:该面的结果与残留状态逐项登记进 `expected_diff.json`(旧值为"不存在",
新值按 skill-5 §3.2 映射表);**③外部中断(SIGINT/SIGTERM)**:原样传播,与变更前 parity。

> **澄清**:本节"**残留不自动回滚**"与 §1.2b 红线的"**误分类后回滚该删除**"
> **不冲突**——前者是超时中断留下的**磁盘残留**,后者是**误删代码的版本回滚**,
> 对象不同。

## §5 项 5:protected marker 写入顺序(**须作出裁决**)

**规格锚点(`ANCHOR-5`)**:`tizen_ci_shared/workspace` 的写入序
——`_verify_cleanup_handle` → `_exclude_private_files` → 写 protected marker。

- **隐患**:exclude 超时/中断时,**worktree 已通过验证但 marker 未写入**;
- **裁决(v1.25;丙 BLOCKER-2):选 (B),维持 `_verify_cleanup_handle` → `_exclude_private_files` → 写 protected marker。**
- **理由**:(1) §4 规定不得改动 skill-5 `v1.3.2` §3.2 映射表的裁决,而该表对 ⑥ `_exclude_private_files`
  超时登记的残留状态是"protected marker 尚未写入"(丙核对);选 (A) 先写 marker 会改变这一残留,违反 §4。
  (2) 若先写 marker,中断时会留下"已带保护标记、私有文件却尚未排除完"的 worktree,
  比现状的"未带保护标记"更难被后续清理识别。**A₀ 须经 `OBS-1.item4-anchors` 核对该残留格,
  与本裁决不一致即阻塞、退回设计方**。
- **两个中断时点的失败态(不自动回滚,沿用 §4)**:
  **(i) exclude 执行中中断**:cleanup handle 已验证;私有文件可能部分排除;protected marker 不存在;
  **(ii) marker 写入中中断**:exclude 已完成;protected marker 不存在或不完整;
  读取方对不完整 marker 的处理维持现状(由 `OBS-1.item5-order` 产出),本批不改。
- **§6 登记**:本项为**零行为差异**,两个中断场景在 `expected_diff.json` 中登记为 `NO_DIFF`;
  上述两个中断时点各一个场景进入 §6 的场景清单(parity)。

## §6 [本批核心机制] 预期差异门禁

**为何需要新机制**:前七批的 parity 是"**变更前后逐字段相等**";
本批**必须产生差异**,故判据变为"**差异恰为预期集**"。若沿用旧 parity,
本批必然全红;若无门禁,又无法证明"只改了该改的"。

**形态(三段,禁止 Markdown 手抄两份)**:
1. **脚本产出前后 inventory**(固定 fixture 双跑),产出**结构化结果对象**;
2. **机器可读决策表登记允许差异**:`expected_diff.json` 中**每个场景恰取一种模式**(v1.26;丙 BLOCKER-4):
   **`NO_DIFF`**(附理由;要求该场景实际差异集为空)或 **`DIFF_SET`**(按
   **`(字段路径) → (旧值, 新值, 理由)`** 登记**每一条允许的差异**);**场景清单中的每个场景都须登记一种模式,缺项即红**;**本设计稿不书写任何具体值**——元规则出处:
   **skill-6 FROZEN v1.8 §11-3**
   *(引用**只写章节不写行号**——两家给出的行号彼此不一致,正是 §8-2 的实例)*;
3. **断言实际差异 == 登记差异**(**精确相等,非"⊆"**):`NO_DIFF` 场景出现任何差异 → 红;
   `DIFF_SET` 场景中未登记的差异 → 红、登记的差异未出现 → 红;**每条登记与每个 `NO_DIFF` 须带理由**,空理由即红。
   **两种模式的结构(v1.27;丙 MAJOR-1)**:`NO_DIFF` = `{"mode":"NO_DIFF","reason":非空字符串}`,**禁止出现 `differences` 字段**;
   `DIFF_SET` = `{"mode":"DIFF_SET","differences":非空对象}`,每项理由非空;
   **`mode` 缺失、取值未知、`NO_DIFF` 携带 `differences`、`DIFF_SET` 的 `differences` 为空 —— 均判红**
   (否则零差异场景可登记成空 `DIFF_SET`,精确相等照样通过,绕过 `NO_DIFF` 的理由义务)。

**场景与结果字段须封闭(v1.25 补;丙 BLOCKER-3)**——否则"精确相等"只在实现者自己选择输出的字段上成立:
- **`scenario_manifest`(A₀ 冻结)** 至少覆盖:§3 悬空 symlink 输入及相邻的非悬空对照输入;
  §4 六个调用面各自的默认 `None`、超时、外部中断三类场景;§5 的两个中断时点。
- **`result_schema`(A₀ 冻结,封闭)**:每个场景逐项规定必填字段,至少含返回值、异常类型/code/message、
  警告与动作、调用参数、destination/worktree/workdir marker 的存在状态、exclude 完成状态;
  **protected marker 须记三项**(v1.26;丙 MAJOR-1):存在状态;存在时的原始字节 sha256;
  **既有读取方读取它的结果**(返回值,或异常类型/code/message)—— 否则"不完整 marker"与完整 marker 都只记为"存在",读取语义变了也看不见。
- **字段路径**统一用 JSON Pointer;**"不存在"用标记值 `{"state":"ABSENT"}`**,存在用
  `{"state":"VALUE","value":…}`,不得用 `null` 兼作不存在。
- **场景缺失、必填字段缺失、出现未声明字段,均判红。**

**准入证伪(⑱):七条**——①额外改一个不该改的字段;②漏改一个已登记差异;
③理由字段留空;④登记一条不可能发生的差异;**⑤`mode` 缺失或取值未知;⑥`NO_DIFF` 携带 `differences`;
⑦`DIFF_SET` 的 `differences` 为空**(⑤–⑦ v1.27 补;丙 MAJOR-1)—— **七者必红**。
**未经该证伪的门禁不得进入 DoD**。

> **计数纪律**:本节为**七条**;**RC-1(a/b/c)**、**12b-10 正控制**、
> **12b-11 golden** 各自独立计数,**四处不得合写**。

## §7 commit 划分与 DoD

**A₀**:预期差异门禁 + **§6 七条准入证伪** + **§6 的 `scenario_manifest` 与 `result_schema`(冻结)**;
**§2 的 `private_consumption` 枚举器与 `private_consumption.json`、§2 准入证伪与 (c) 类投影**(v1.25 明写;丙 MAJOR-4);
**`scan_manifest` 生成器** +
**排除规则登记与全函数分类器** + **冻结注册表(含完备性四条)** +
**标准化阶段(N1 归并 + 全函数配对 π + 基数断言)** +
**`shim_inventory.py`**(三段台账**保持来源自身声明的粒度**(v1.16 随动:binding 级展开义务已于 v1.15 撤销;甲 BLOCKER-1 第 2 处、丙、乙) + **四级粒度候选扫描** +
解析层扫描 + **独立存在性检查** + **SEAL 全清单断言** + **十条违例 fixture** +
**每 `(detector, capability branch)` 正控制与 near-miss** +
**独立参与点分类器** + **四方对账(12b-12)** + **判定层 golden**);
**可信叶子白名单与装饰器白名单**;**claim 型别闸门(默认反转)+ 豁免清单
四条上界核验 + predicate 登记/冻结 + canonical renderer(带 `renderer_version`)
+ 通用 verifier**;
**运行时锚 + RC-1**;**锚点核验脚本**;**开工前排期检查**;
继承三批 ledger 与 branch_inventory,**前七批全部门禁回归不退化**。
**A**:项 4(六个调用面逐面实施;按 §4 验收口径逐面跑三类场景,超时场景逐面登记预期差异);
**B**:项 3 + 项 5(项 5 按裁决 (B) 不改代码,只落两个中断时点的失败态测试与零差异登记);**C**:项 1(**⑤ → ④ → ③ → ② → ①**,
并遵守 SEAL-10 登记的跨 candidate 顺序)+ 项 2;**① 与 ② 的删除按 shim 模块分组、每组一个独立 commit,C 完成后执行
§1.1"静态发现的残余边界与删除后验证"的五项删除后验证**(v1.29);**D**:收口 + P4.9 关闭(删除后验证全部通过是 D 的前置)。

**【机制清单】(v1.24 精简)** —— 本批新立、须配构造式正控制的 P4.9 机制;
**每条须在附录 B-11 有至少一条构造式正控制 + 一条 near-miss**(DoD 硬门)。

> | 机制 key | 机制 |
> |---|---|
> | `MECH_CLASSIFIER7` | 台账 key 出口七格全函数分类器(§1.1c-0) |
> | `MECH_FIVE_WAY` | `consumer_closure_registry` 五方覆盖(`SEAL-16b`) |
> | `MECH_AST_CLAUSE_ID` | `clause_id` 由 predicate AST 叶子路径机械生成(`SEAL-16b`) |
> | `MECH_UNIVERSE_ENUM` | 动态 span universe 由独立 raw-syntax / config 枚举器产出(§1.1c-0 时序出口) |
> | `MECH_INVARIANT` | `covers ⊇ primary_owner` 构造不变式,标准化期独立断言,暂态不豁免(§1.1c-0) |
> | `MECH_POST_DELETE` | 删除后验证与分组回退(§1.1"静态发现的残余边界与删除后验证";v1.29) |
>
> *(v1.24:v1.20–v1.23 的机制清单另含九条"文档自检"机制(断言③d/③e/③f/③g/②b、`consumed` 键集、
> 归约式、行粒度排除、replacement graph),随该机制整体移除。)*

**DoD**(节选):
- [ ] **删除后验证(v1.29)**:① 与 ② 按 shim 模块分组提交;全量测试与门禁、运行时锚与冒烟、import-all、名字残留复扫、
      打包构建与入口 `--help` 五项全部通过;失败组已回退并按勘误流程处理;输入/命令/输出/回退记录落 B-8;
- [ ] **状态对象统一**:**§1.1c-0 标准化阶段在册**——`raw finding → candidate
      → ledger_key` 两级归并、**全函数配对 π(粒度归一)**、**`|π(c)| ≤ 1`**;
      **`|π⁻¹(k)| ≤ 1` 已撤销**;**台账保持来源自身粒度、不展开、不派生**;
      **台账侧覆盖义务由 §1.1c-0 七格分类器给出**(每个 key 恰落一格;表外组合 → `UNKNOWN_LEDGER_EXIT` 阻塞;
      v1.25 统一:此处原沿用四出口的旧写法,与下文"七格分类器"一条互斥);
      **`SOURCE_OBLIGATION_UNENUMERABLE` 有时序出口**(销账 → 重跑枚举与映射);
- [ ] **`PRESENT` 语义已二选一并明写**(= 存在性,不含"是否仍是 shim");
      **`ABSENT` 须由独立存在性检查正面产出**,**"无 finding"不得作判据**;
      **E9 改判合法并产出 `LEDGER_PRESENT_NO_FINDING`**,
      **其 `ALREADY_REMOVED` 永禁**;**可达表 R1–R7**;
- [ ] **`NON_SHIM_PREDICTION` 零豁免**:不影响 candidacy、不抑制 finding、
      **不免行级下界**、仍进 reconciliation;其**证伪钩以销账后终态判定**
      (**最终进入 `preseal_effective_inventory` 即红**(v1.16 随动:求值点已具名;丙)),**不得以"产生过 finding"判定**;
      **中间 finding 与未决分流逐条落 B-8,空记录即红**;
      **排除规则由独立全函数分类器计算,未知类型必红,每条附理由字段**;
- [ ] **reconciliation 导出表 12 格全函数**:每格给值或显式非法
      (**非法两格:E6 / E12**);**未覆盖组合 → `UNKNOWN_RECONCILIATION` 阻塞**;
- [ ] **claim 型别默认反转 + 豁免清单四条上界**:**被引用者默认 `ASSERTION`**;
      **仅豁免清单内可为 `MEASUREMENT`**;**清单仅限字面 claim key、禁通配**;
      **清单 ∩ 决策条款引用集 = ∅**;**豁免 claim 的 `GATE` 引用数 = 0**;
      **豁免 claim 不得带 predicate 块**;**本版清单 = ∅,冻结于 A₀ 首跑前**;
      **锚为 SEAL-16 的引用集**;**规范判断句须显式引键,无键即红**;
- [ ] **禁止事项三条在册**:禁止自由文本推断 / **禁止实现方补写** /
      **解析失败或空 predicate 一律红**;**`ASSERTION` 无块或块为空即红**;
      **事实纪律扫描按 claim 归属逐句核**;
- [ ] **`UNRESOLVED_DISPOSITION` 消化四条**:**补事实输入、裁决由判据产出**;
      **`uncertainty_kinds` 由判据失败子句机械导出,人工不得填写**;
      **输出域 = 各成员输出域的【交集】;交集为空即继续阻塞**——
      **完整性/闭合性/否定存在三类下 ①② 均禁**,其余三类下 ① 永禁;
      **终态落在合法输出域之外者不得凭消化清零**;**SEAL-8b 对消化项不开洞**;
      **SEAL-6 不得以"无出口"为由带病 seal**;
- [ ] **12b-10**:实例目录**机械导出、落 B-8**;**独立参与点分类器**且
      **未知分支或零命中 → `UNKNOWN_CAPABILITY` 阻塞**;**精确 finding 集 + near-miss**;
      **扩充次序:先进九类表/registry,再补正控制**;
- [ ] **12b-11**:golden 落成**四元映射**;**以终态 disposition 表达**;
      **每条附理由,空理由即红**;
- [ ] **12b-12 四方对账**:分类器输出域 / registry 分支 / 九类表 branch 列 /
      正控制目录**两两双向精确覆盖,差集非空即红**;
- [ ] **12b-8 证伪钩求值点**:**SEAL-3 之后、SEAL-9 之前**对
      `preseal_effective_inventory` 求值;**SEAL-9 另断言冻结集合与它逐项相等**;
      **§1.3 四条断言在冻结前求值并纳入 SEAL-9 的"以上全部"**;
      **12b-9⑤ 的 fixture 须跑完整条 admission 流水线**;
- [ ] **E6 具名 `EXISTENCE_CONFLICT`**:阻塞不变,**逐格记录 + 两侧证据 +
      独立 fixture + 一条 golden**;**与 E12 的 fixture 不得合并**;
- [ ] **独立存在性检查取 `lstat` 语义**(不跟随符号链接),口径已明写;
- [ ] **七项因子**(减法上界指向 §8-2 豁免清单,行级下界单列 12b-3b);
- [ ] **renderer 隔离**:generated block 带 `renderer_version`;
      **同版本同 predicate 重生成逐字不变**;**版本变更提交不得含 predicate 变更**;
      **不兼容升级须先走 predicate 迁移提交(版本不变)**;
- [ ] **阶段分层**:阶段列就地落实为表的一列;**SEAL 21 条与 12b 13 条全部标注**;
      **每行阶段列非空 ∧ 取值 ∈ 六阶段就地列举**(扫描期 / 标准化期 /
      admission 期 / disposition 期 / 终局 / A₀ 期);**表内阶段列与分组表双向精确覆盖**;
      同期内按依赖闭包求值,循环即红;
- [ ] **`SEAL-16b`**:`CLOSED` 四项合取派生式 + `predicate_clause_ids ==
      uncertainty_mapping.keys()` + `consumer_closure_registry` **五方覆盖**(含由完整 tree / callsite 枚举器产出的
      实际参与点集合)+ 分支级正控制;
- [ ] **台账 key 出口由【七格全函数分类器】给出**,含 `LEDGER_COVERED_BY_DESCENDANT`
      与暂态优先格;**表外组合 → `UNKNOWN_LEDGER_EXIT` 阻塞**;
      **`covers ⊇ primary_owner` 由标准化期的独立不变式断言承担,暂态不豁免**;
- [ ] **动态 span universe 扫描期冻结**;worklist 单调减少;universe 外新 site
      → `UNSUPPORTED` + 整轮重启;
- [ ] **【机制清单】见本节上文【机制清单】表**:每条须在 B-11 有至少一条构造式正控制 + 一条 near-miss;
- [ ] **【硬门】新机制不配构造式正控制,不得进 DoD**(v1.18;甲 方向 6):
      自我适用条款第三段对**本稿自己新立的每一个机制**同样适用;
      本条把它变成硬门:**§7 机制清单与附录 B-11(乙)按机制 key 双向一一对应**;
      **此后每新立一条机制,须同轮入列并同轮在 B-11 配控制**;
- [ ] **`uncertainty_kinds` 为机械导出的多值集合**:由判据失败子句按登记映射产出,
      **人工不得填**;**多类命中取输出域交集**;**八类**;
      **上/下半归属由 `SEAL-16b` 的记录状态机械产出**;
- [ ] **`SEAL-16b` 消费者集合完整性门禁**:编号 + B-8 `consumer_set_closure` 字段
      + 违例 fixture **三者齐备,缺一即红**;
- [ ] **SEAL 求值阶段分层**:**六阶段**就地标注(权威定义见下条"阶段分层";
      v1.21 修:此处自 v1.18 起一直写"五阶段");**跨阶段提前求值即红**;
- [ ] **π 最细粒度优先** + **`primary_owner` / `covers` 两关系分开**;
      **台账 key 出口由【全函数分类器】给出**(七格表,含 `UNENUMERABLE` 暂态优先);
- [ ] **时序出口有界**:扫描期冻结动态 span universe;worklist 单调减少;
      **上界 = universe 基数**;universe 外新 site → `UNSUPPORTED` + 整轮重启;
- [ ] **SEAL-9 一并冻结 per-candidate disposition evidence bundle**;
- [ ] **删除的每个测试须有替代或理由,且与 §2 三分表闭合**
      (**此前曾仅以"恢复条款在册"的元条目形式出现——那是清单不是义务**;
      **丢掉"闭合"意味着一个被删测试可以不出现在三分表里**);
- [ ] 全量测试:**允许数量变化**(本批删测试),但须**逐项说明增减**;
- [ ] **恢复条款在册**(逐条可 grep):动态导入分流义务、对象式 patch 子形态、
      形态 9 语义位置判据、运行时锚单向边界、入口类具名例子、
      `ANCHOR-3` 机械 selector、`expected_diff.json` schema、
      §2 行为型叶子归 (b)、解析层"另产出候选"、§1.3 两段"为何"、
      §1.2 ④⑤ 本质区别与存在意义、§6"未经证伪不得进 DoD"、
      结构特征 A/B 台账限定语、"每个 entry 至少一个 `SCANNED`"、
      "删除的每个测试须有替代或理由且与 §2 表闭合"、
      **白名单"每个登记形态分别证伪"**、**B-12 的 RC-1 记录 schema**、
      **B-9 的零命中十二项枚举**、**B-10/B-11 的记录字段规格**、
      **"有块却登记为 `MEASUREMENT` 即红"(以豁免清单上界(iv) 承接)**、
      **"事实纪律扫描按 claim 归属逐句核"**;
- [ ] 其余承前:manifest 不做减法、格级缺记录即红、注册表完备性四条、
      解析层逐类扫描与显式记零、封闭 artifact universe、不覆盖九类各有承担方、
      台账三段与 SEAL-1、SEAL 全清单 + 违例、§1.3 四条断言、ID 与 span 契约、
      运行时锚与 RC-1、入口类、§2 三分、§3/§5 预期差异与裁决、§4 parity、
      §6 门禁与七条证伪、SEAL-14、§8-2 纪律、七项因子及作用域声明、
      前七批门禁不退化、全量测试增减说明、冻结稿现状描述更新。

## §8 文本事故与三条纪律

### 8-1 文本事故台账

| # | 事故 | 首报 | 状态 |
|---|---|---|---|
| (1)–(19) | *(承前台账,逐条状态不变)* | v1.4–v1.10 | ✓ 已修 |
| (20) | 元规则标题基数与实列不符 | v1.11 | ✓ v1.12 修 |
| (21) | 六处未申报规范性删文 | v1.11 | ✓ v1.12 恢复并申报 |
| (22) | 排除标记被从处置面前移到候选面 | v1.11 | ✓ v1.12 修 |
| (23) | reconciliation 产出时序与非法表冲突 | v1.11 | ✓ v1.12 修 |
| (24) | §1.1a 残留半句事实陈述 | v1.11 | ✓ v1.12 修 |
| (25) | **`12b-3b` 与 `12b-8` 相邻两行互斥**;且该表述**源自评审方答问时自补的推论而非被审原文** | v1.12 | ✓ v1.13 修(**以 12b-3b 为准;12b-8 重写为零豁免 + 证伪钩**) |
| (26) | **reconciliation 导出规则非全函数**(9 格给 5 条),**`RESOLVED × UNKNOWN` 与 `UNREGISTERED_CANDIDATE` 无落点** → **seal 不可达** | v1.12 | ✓ v1.13 修 |
| (27) | **"解析失败或空 predicate 一律红"被未申报删除**(**含"禁止事项三条"整块**)→ **空 predicate 被任何产出满足,全部型别判据同时绿而内容零核验** | v1.12 | ✓ v1.13 恢复 |
| (28) | **十六处未申报的规范性删文**(清单见 v1.13 变更⑥;**其中"禁止事项三条"已由 (27) 单独记账,故 DoD 的恢复清单列 15 条**——v1.14 统一口径,甲 MINOR) | v1.12 | ✓ v1.13 逐条恢复并申报 |
| (29) | **`UNRESOLVED_DISPOSITION` 无消化语义**(五进零出) | v1.12 | ✓ v1.13 补出口 |
| (30) | `claim consumer` 导出器无完整性断言且**失效朝开** | v1.12 | ✓ v1.13 反转默认 |
| **(31)** | **状态两维的对象未统一**:`PRESENT` 语义二义(E9 的对错随读法翻转)、维度二"对象 = 台账 key"却有值 `NO_LEDGER_KEY`、**配对函数与台账 key 粒度全文未定义** | v1.13 | ✓ **v1.14 修**(§1.1c-0 + 取读法(i) + E9 改判合法 + `ABSENT` 须正面证据) |
| **(32)** | **`SEAL-16` 指向已不存在的"闸门 2"**——同版把三闸门体系改写为"默认反转 + 三条禁止",**`闸门 2` 在规范正文零处定义** | v1.13 | ✓ **v1.14 修**(改指 §8-2 型别默认反转;并立标识符两条 fail-closed,**该悬挂引用在新规则下第一次运行即被捕获**) |
| **(33)** | **B-14 立规同版未实跑**,B-13 的"已实跑"仅为自然语言自述;**两器均无正控制**,自述漏掉六处删文 | v1.13 | ✓ **v1.14 修**(元规则(九)+ 两器正控制 + 三元组 hash + 逐条产物落 B-13/B-14) |
| **(34)** | **六处未申报/未三态登记的删改**:白名单"每个登记形态分别证伪"、B-12 的 RC-1 记录 schema、B-9 的零命中十二项枚举、闸门 1 的"有块却登记为 `MEASUREMENT` 即红"、闸门 3 的"按 claim 归属逐句核"、B-10/B-11 的记录字段规格 | v1.13 | ✓ **v1.14 逐条恢复并三态登记**(见 B-13) |
| **(35)** | **扩宽的 "finding" 定义与 manifest 全集 + 解析层全分流未对账** → 被排除的 symlink/gitlink/打包入口**产生即永久红、无销账路径** | v1.13 | ✓ **v1.14 修**(证伪钩改以销账后终态判定;§1.3 计数口径同步) |
| **(36)** | **豁免清单无机械上界**,承重 claim 可被合法豁免而全程绿;清单未实例化 | v1.13 | ✓ **v1.14 修**(四条上界 + 清单 = ∅ 显式声明) |
| **(37)** | **`UNRESOLVED_DISPOSITION` 出口无输出域限制**,可人工裁出 ¬∃ 型终态 `DELETE_DIRECT` | v1.13 | ✓ **v1.14 修**(补事实输入 + 输出域限定 + ① 永禁) |
| **(38)** | **标识符提取规则 ≠ B-14 实跑所用**:冻结词法模式提不出 `A₀`/`π`/`RC-1`/`N1`/全部 lowercase_snake/`§编号`/圈数字/`闸门 n`,**而 B-14 的产出恰以其中四个为据**;遗漏方向朝开 | v1.14 | ✓ **v1.15 修**(模式表补六类 + 定义位改登记表 + 重跑 B-14) |
| **(39)** | **台账"展开到 binding 级"无基准**:第一、二段只有文档 hash、无代码快照;用当前树展开撞元规则(四),不展开则 seal 不可达 | v1.14 | ✓ **v1.15 修**(撤 `\|π⁻¹(k)\| ≤ 1`,π 改粒度归一,台账保持来源粒度 + 覆盖义务) |
| **(40)** | **B-13 判定规则升级后未回溯适用**:旧规则对"长表格行内子句"与"不变式句"零召回,而 v1.12→v1.13 的三态登记全部出自旧规则 | v1.14 | ✓ **v1.15 已回溯重跑**(见 B-13;**抓出六处存活两版的理由句删文,逐条恢复**) |
| **(41)** | **B-13 召回规则含"∪ 正文中被加粗者"**,把判定规则交回书写者——本纪律自己禁止的形态;且阈值被写了两个值(0.72 / 0.80) | v1.14 | ✓ **v1.15 修**(反转默认:全部子句 − 冻结排除集;阈值 0.80 唯一,类三) |
| **(42)** | **元规则(九) 在首个应用上不成立**:B-13 给的是"两个输入 + 时刻"、**无输出 hash**,B-14 无三元组;而 hash 对象排除记录区 → **证据本身不在覆盖面内**;锚依赖书写顺序且"区间缩短"自洽故不可检出 | v1.14 | ✓ **v1.15 修**(三元组补输出 hash + 规则文本 hash;hash 对象改内容枚举 + 覆盖双向核验;声明类三) |
| **(43)** | **消化出口的 ¬∃ 判别法不自洽**:② 与 ① 依赖同一不可枚举空间上的同一否定存在,可由"人工补入消费者集合"抵达而三闸门全绿 | v1.14 | ✓ **v1.15 修**(`uncertainty_kind` 机械矩阵;完整性类未决下 ①② 均禁) |
| **(44)** | **12b-8 证伪钩求值点未定**:SEAL-12b 与 admission 终态间无偏序,过早求值则集合为空、**稳定恒绿**;且 B-14 对该改写行漏对四行 | v1.14 | ✓ **v1.15 修**(具名 `preseal_effective_inventory` + 偏序断言 + fixture 跑全流水线 + 补对账) |
| **(45)** | **六项因子的因子④ 引用对象错位**:`12b-3b` 是行级下界,不是减法上界 | v1.14 | ✓ **v1.15 修**(拆为七项因子) |
| **(46)** | **稿 §8-1 的十六类词法表 ≠ `ident_check2.py` 实跑的十六类**:脚本整类丢掉稿的第 15 类 `circled`,又把稿里合为一行的 `meta / retired` 拆成两条凑回十六;**两边都是"十六",数字撞上把差异盖住**(与 (48) 同型) | v1.15 | ✓ **v1.16 修**(如实分十七行 + 补 `circled` + 规则区块逐字嵌入) |
| **(47)** | **稿给 `enum`/`snake`/`greek`/`circled` 登记了归属节,脚本这几类 `home` 全是 `'*'`(不核验,直接计入通过)**:240 个标识符中 **124 个(51%)从未被核验**,而 B-14 记录写的是"240 通过、零定义 0"——**聚合计数把覆盖面盖住** | v1.15 | ◐ **v1.16 修规则**(Tier A/B/C 分层 + 强制分层覆盖计数);**Tier C 收口【未闭合】,67 条清单见 B-14,未闭合即红** |
| **(48)** | **排除集"七条 vs 七条"**:稿的第⑦条是"变更块与生成记录区",脚本的 X7 是稿内从未登记的"版本修订摘要块首";稿的⑦ 在脚本里是两个结构性判断。**一条无登记、无机械上界的减法**(元规则(五)),当前冗余不生效 | v1.15 | ✓ **v1.16 修**(改八条:六行级 + 两结构性;删 X7) |
| **(49)** | **`norm_diff4.py` 的生成记录区排除仍是【区间式】**,而同版变更⑤(c) 已为 `hashobj` 写明"区间缩短是自洽的,故不可检出";**失效方向朝开**(旧版侧区间提前 → 候选差集变小 → 漏报) | v1.15 | ✓ **v1.16 修**(内容枚举;**附构造式正控制**,见 B-13 控制表第四条) |
| **(50)** | **四个 hash 出自三种对象口径**(v1.12 未减任何节、v1.13 未减 B-14、v1.14/v1.15 统一),**而授权偏离的事实陈述("v1.12 尚无 B-13/B-14、v1.13 无 B-14")经枚举为假**;**两行记录携带的规则文本 hash 相同**,断言③ 首次应用即未检出口径差异 | v1.15 | ✓ **v1.19 闭合**:两个原件已入出版环境,按版本可移植口径重算(v1.12 = `d832619a…5289f7`、v1.13 = `5f81b32d…bf5d81`,与甲、乙三方一致);**记录值对应的排除集经十六子集穷举机械坐实**({} / {B-13, B-14a, B-15});**成因见 (91)(92)** |
| **(51)** | **B-14 对账条目的共享行枚举仍是人工的**,本轮漏四处(`SEAL-1` 违例 fixture、A₀ binding 展开、B-8 两条),**其中两处被标成"已同步改"** | v1.15 | ✓ **v1.16 修**(待对账集由索引机械生成 + "已同步改"须附 diff 证据) |
| **(52)** | **`uncertainty_kind` 是人工单值必填字段,直接开闭"删测试资产"的门**;其上/下半划分依赖的"消费者集合完整性门禁"**全文仅两处叙述性出现,无编号/无断言/无记录/无 fixture**;六类不穷尽(producer 冲突、SEAL-10 两条路径无合法取值) | v1.15 | ✓ **v1.16 修**(改机械导出多值集合 + 立 `SEAL-16b` + 补两类 + 多类取交集) |
| **(53)** | **π 归一到"最粗粒度"方向错误**:使 binding 级台账 key 系统性无法 `MATCHED`、被推入语义相反的 `LEDGER_PRESENT_NO_FINDING`;两条判定规则对互相包含的 key 各给一值、无优先级 → 阻塞合法配置。**覆盖义务另漏 `UNENUMERABLE` 暂态这一合法情形** | v1.15 | ✓ **v1.16 修**(最细粒度优先 + 拆 `primary_owner`/`covers` + 覆盖义务补第四出口) |
| **(54)** | **`SEAL-1` 违例 fixture 断言与新 `SEAL-1` 相反**:fixture 要求"只能展开到模块级的来源须落 `UNENUMERABLE`",而新规则下模块级来源**合法且常见**——**合法输入上必红 → seal 不可达 → 撞终止条款** | v1.15 | ✓ **v1.16 修**(fixture 改为"连自身声明粒度都无法枚举的来源") |
| **(55)** | **元规则(九) 的断言②③ 挂在 A₀,晚于它们要守的"发版前跑完"**;本稿发出时只有断言① 可求值,②③ 一次都没被求值过——**与 12b-8"求值点未定"完全同型,只是落在元规则(九) 自己的断言上** | v1.15 | ✓ **v1.16 修**(②③ 改发版前自证,A₀ 保留为二次核验) |
| **(56)** | **排除集第⑦条把变更块整块排除于提取面**,结构上开着"只写变更块、不落正文"的逃逸路径(本版抽样九条新义务全部落地,**未被走过**) | v1.15 | ✓ **v1.16 修**(差集侧保留排除,覆盖侧新增变更块→正文单向覆盖断言) |
| **(57)** | **时序出口只授权"重跑一次",第二轮无归宿**:重跑若揭示新的动态构造,该项既不满足"证明不可得"又已用掉唯一机会 → 实现者裁量,而这条路径闸的是 SEAL-1 | v1.15 | ✓ **v1.16 修**(单调性 + 上界 = 首轮计数 + 达上界即落定) |
| **(58)** | **SEAL 之间还有五条依赖后阶段事实的断言未排序**(`SEAL-4`/`SEAL-8`/`SEAL-8b`/`SEAL-11b`/台账侧覆盖义务);其中 `SEAL-8`、`SEAL-11b` 正是 B-14 为 12b-8 列出的对账行,**同步了集合口径,没同步求值时点** | v1.15 | ✓ **v1.16 修**(五个求值阶段分层 + "跨阶段提前求值即红") |
| **(59)** | **反向索引按【新名】查表,重命名类改写结构性漏对**:`uncertainty_kind` → `uncertainty_kinds` 之后旧名在规范正文残留四处,**DoD 的"必填"与 §1.1c 的"人工不得填写"构成一对互斥规范行** —— 正是事故 (25) 的形态,而断言(ii) 恰因重命名看不见它 | v1.16 | ✓ **v1.17 修**(`renames` 由 B-13 差集机械导出;待对账集 = 索引[新] ∪ 索引[旧];收口条件 = 索引[旧] 在 v(n) 输入面内为空) |
| **(60)** | **陈旧行把陈旧名字"喂饱"**:矩阵表头那行的行首单元格正好以旧名开头,被判为【定义式书写】,于是检查器认为旧名有定义、一切正常 | v1.16 | ✓ **v1.17 修**(随 (59) 的收口条件消解) |
| **(61)** | **"已同步改须附 diff 证据"在它的第一次应用上就没挡住**:所附证据(候选差集三条)与它声称改了的四处**没有交集** | v1.16 | ✓ **v1.17 修**(diff 证据须逐处对应,不得以整批候选号代替) |
| **(62)** | **B-14a / B-15 两节【规范性记录规格】被排除在三器视野外**:不在 hash 对象内、不在 B-13 子句集内、不在 B-14 索引内,**方向全部朝开**;B-14a 已携带与同版 §1.1c 相抵的陈旧条款而三器无一可见 | v1.16 | ✓ **v1.17 修**(排除面判别法:只覆盖检查器自身本次运行的产物) |
| **(63)** | **规则区块注释写"十六类"而 `CLASSES` 实列 17 条**;**断言③ 是字节相等,对"两边一致地写错"结构上不可检出** —— "数字撞上把差异盖住"的第三次,且发生在专为消灭该形状而引入的机制内部 | v1.16 | ✓ **v1.17 修**(断言③b:区块内基数词 == 紧邻列举数 == 稿内表行数) |
| **(64)** | **`CN` 在规则区块【外】定义而区块【内】引用**:改掉区块外的 `CN`,四条断言全绿而 `元规则(九)` 静默脱离断言(i)(ii) 的覆盖 | v1.16 | ✓ **v1.17 修**(断言③c 区块自足 + `CN` 移入区块) |
| **(65)** | **输入面清单只给【排序摘要】**:不指名哪一项缺失、对归一化折叠不可检出;更要紧的是它只证"产物声称看了哪些输入",**不证"输出实际消费了这些输入"** | v1.16 | ✓ **v1.17 修**(`declared` / `consumed` 双清单逐项相等 + 保留 occurrence + 分层计数) |
| **(66)** | **阶段分层不全且有倒置**:SEAL 21 条只标 19(缺 `SEAL-14`/`SEAL-15`)、12b 十三条只标 1 条;`SEAL-11`(依赖五元组)、`SEAL-1`(依赖销账产物)、`SEAL-16b`(依赖 admission 终态)三处阶段倒置 | v1.16 | ✓ **v1.17 修**(阶段列就地落实为表的一列 + 补全 + 三处改判 + "阶段列非空 ∧ ∈ 五阶段"可机械核验) |
| **(67)** | **非标识符排除清单是【全局 token 减法】**:`LEDGER_` 是前缀形状(按前缀读法吞掉三个状态取值);`IDENTITY`/`EXISTENCE` 被误归为"ID 语法片段"而同枚举第三值 `BEHAVIOR` 判零定义 —— 一条建立在错误理由上的减法 | v1.16 | ✓ **v1.17 修**(改【上下文限定】+ 字面全等 + 枚举成员整体处理) |
| **(68)** | **§1.0a 标题"被绕过的十二次"而表实列 13 行** —— **事故 (20) 的原样再现**(元规则标题基数与实列不符);类三判别法写了十七轮,**从来没有任何检查器在跑它** | v1.16 | ✓ **v1.17 修**(断言(iii):正文基数词与紧邻列举机械核验) |
| **(69)** | **时序出口同时规定"重跑一次"与多轮**:若重跑能揭示新的动态构造,首轮计数就不是闭合上界;若不能,多轮的理由又不成立 | v1.16 | ✓ **v1.17 修**(删"一次";上界改由扫描期冻结的动态 span universe 承担;universe 外新 site → `UNSUPPORTED` 并整轮重启) |
| **(70)** | **变更块落点只验"有没有",不验"覆盖完不完整"**:填一个正文早已存在、与本次义务无关的标识符即可过零命中检查;含全称量词的声明可半落地而检查为绿(本轮实证:变更⑨ 写"每条 SEAL / 12b 就地标注",14 条未标注而零命中绿) | v1.16 | ✓ **v1.17 修**(落点记 `(identifier, 子句指纹)` 须一对一命中 + 全称量词须带覆盖计数) |
| **(71)** | **`SEAL-16b` 仍是新声明面**:`CLOSED` 无结构化派生式、判据子句 ID 全集与 kind 映射键集无覆盖断言、无分支级正控制 —— 实现者仍可把未闭合的消费者集合标为 `CLOSED` 而机械地得到较宽输出域 | v1.16 | ✓ **v1.17 修**(四项合取的 `CLOSED` 派生式 + `predicate_clause_ids == mapping.keys()` + `consumer_closure_registry` 四方覆盖 + 分支级正控制) |
| **(72)** | **`covers` 拆分后祖先 key 没有事实一致的状态**:被后代覆盖的祖先 key 与 `LEDGER_PRESENT_NO_FINDING` 可同时成立;覆盖义务写成包含式"或",**未要求互斥** | v1.16 | ✓ **v1.17 修**(新增 `LEDGER_COVERED_BY_DESCENDANT` + 两条判别式 + 五出口 XOR 分区) |
| **(73)** | **§1.3 的 `NON_SHIM_PREDICTION` 计数口径仍用最终 `effective_inventory`**,而变更⑬ 已把该证伪钩改指 pre-seal 集合 | v1.16 | ✓ **v1.17 修** |
| **(74)** | **item 的定义仍写"由 π 与 π⁻¹ 配对产生"**,而 π⁻¹ 基数断言已于 v1.15 撤销、两关系已于 v1.16 拆开 | v1.16 | ✓ **v1.17 修**(改为"由 `primary_owner` 与 `covers` 构造") |
| **(75)** | **新增 `sectext` 类后,区块注释与稿内表的基数词仍写"十七类"/17 行而 `CLASSES` 实列 18** —— **"基数不符"的第四次**(前三次:(20) 元规则标题、(46) 词法表、(48) 排除集),**且发生在写下断言③b 的同一版内**,由发版前人工清点抓出 | v1.17(自查) | ◐ **v1.17 已改为十八**;**根因未闭合**:③b 与 (iii) 均未实现,**四次全部靠人眼**;收口条件 = ③b 与 (iii) 交付 |
| **(76)** | **事故 (54) 连续两版声称"已修"并在状态格写明了改后措辞,而 §1.1d 的 `SEAL-1` 违例 fixture 原文【三版逐字未改】** —— v1.16 变更块写"逐条已改"、B-14 对账行写"已同步改",**而那两行在 v1.15/v1.16/v1.17 完全相同**;实现即合法输入必红 → seal 不可达 | v1.16 | ✓ **v1.18 真改**(fixture 改为"连自身声明粒度都无法枚举的来源" + 补 near-miss);**并把"已修"格纳入机械核验** |
| **(77)** | **五出口"XOR 分区"自相矛盾**:`LEDGER_COVERED_BY_DESCENDANT` 的判别式 `covers⁻¹≠∅ ∧ primary_owner⁻¹=∅` **蕴含**第一出口 `covers⁻¹≠∅`,**恒落两个出口 → 恒红、永不可达**;暂态出口与第一出口同样不互斥 —— **为闭合上一轮阻断而新增的东西把自己废了** | v1.17 | ✓ **v1.18 修**(改为七格全函数分类器,互斥由全函数性构造保证 + 三条正控制) |
| **(78)** | **断言③c 只查自由【名字】,而区块里剩下的是【数据】** —— 把 `'### 1.1d'` 等位置常量解析成稿内范围的代码仍在区块外;改区块外的 `home` 解析器即可让 Tier A 的 117 条核验**整类真空绿**,而七条断言全绿、分层计数照显"117/117 通过" | v1.17 | ✓ **v1.18 修**(断言③d:位置常量须在【稿内】恰定位一次 + 交叉控制;**锚落在稿,不在代码**) |
| **(79)** | **双清单仍是自证**:`declared` 与 `consumed` **同由一个实现自报**,把前者原样复制进后者、计算时忽略最后一项即全绿 —— 比丙原构造**更省力** | v1.17 | ✓ **v1.18 修**(`consumed` 改为【按输入项分组的输出】的键集,每项须携带判定结果,缺结果即视为未消费) |
| **(80)** | **"阶段列"未落地**:v1.17 承诺把就地标注字面落实为表的一列,而两张权威表表头**仍是两列**、阶段归属又写成表外分组表 —— **"阶段列非空"这条核验指向一个不存在的列**;另"取值 ∈ 五阶段"而分组表实列六行,按字面会把 `12b-9`…`12b-12` 红掉 | v1.17 | ✓ **v1.18 修**(两表各加一列,34 行逐行填满;六阶段;分组表降为核验期望值并双向覆盖) |
| **(81)** | **DoD 与正文成组陈旧**:"B-14 按十七类"(实为十八)、"覆盖义务四出口"(已改分类器)、"上界 = 首轮计数"(已改冻结 universe)、"hash 对象 = 全文 − {B-13, B-14, B-14a, B-15}"(B-14a/B-15 已移出) | v1.17 | ✓ **v1.18 逐条改** |
| **(82)** | **元规则(九) 第三句写"行号全集 / 行号索引全集"**,而第四句 (b) 是 occurrence key、§8-2 类四明写锚不得是行号 —— **事故 (25) 的形态,发生在同一条元规则的相邻两句之间** | v1.16 | ✓ **v1.18 修** |
| **(83)** | **稿内词法表第五列 Tier A 各行仍写"归属节 §1.1d"(位置)**,而区块与 §8-1(二bis) 已收紧为"定义式书写";**断言③ 比字节(必然相等)、③b 比行数,"逐行对应"此前只被核验了行数** —— 照表实现即回到"出现即定义" | v1.17 | ✓ **v1.18 修**(判据列补"定义式书写" + 立断言③e 表—区块逐行对应) |
| **(84)** | **`sectext` 正则不含版本段**,而稿内实际写法是 `skill-5 v1.3.2 §3.2` / `skill-6 FROZEN v1.8 §11-3` —— **该类存在却对其真实目标失明,方向朝开** | v1.17 | ✓ **v1.18 修**(统一外部锚语法,捕获 (稿名, 版本, 小节) 三元组;自证物核验二元组在权威并行表内) |
| **(85)** | **`renames` 一对一机械导出有三种漏法**:改名 + 改义使相似度跌破阈值、旧名仍有历史引用使配对条件不成立、一对多拆分只产出一对 | v1.17 | ✓ **v1.18 修**(改多对多 replacement graph + 与零定义新增项求交 + 历史引用须带明示标记且有可数上界) |
| **(86)** | **排除面按【小节】判定**:B-13 小节开头的规范句("差集非空即红,未经三态登记不得发版")**落在排除面内**,在其中新增义务则三器全不可见;**B-8 是第三类灰区小节**(既是规格又是产物落点),按小节判定会整节离开视野 —— **与 B-14a/B-15 同坑,只是还没踩到** | v1.17 | ✓ **v1.18 修**(判别降到【行】粒度,仅排除带 `<!-- generated -->` 标记的产物行) |
| **(87)** | **三处新机制仍由同源声明互证,缺独立外锚**:`consumer_closure_registry` 的四张声明表可一致漏掉同一形态;`clause_id` 键集两侧可一致漏同一 leaf;动态 span universe 由同一扫描器冻结、会一致地漏 | v1.17 | ✓ **v1.18 修**(补第五方实际参与点集合;`clause_id` 由 predicate AST 机械生成;universe 由独立枚举器产出;三者各补"删一条即红"的构造式控制) |
| **(88)** | **影子模式"最多保留一版"没有机械物**,失效方向朝开 | v1.17 | ✓ **v1.18 修**(产物携带 `shadow_until`,发版前自检断言当前版本 ≤ 该值) |
| **(89)** | **子句指纹落点只写"零命中即红",未写多命中** —— 一条义务句在正文出现两次时落点"命中"而映射不唯一 | v1.17 | ✓ **v1.18 修**(改为"恰一次") |
| **(90)** | **跨节引用的基数词不受任何断言约束**:③b 管区块内、(iii) 管紧邻列举,**跨节引用两头不靠**;v1.17 当场两处(元规则(九) 第四句、DoD)均写"十七类"而实为十八 | v1.17 | ✓ **v1.18 修**(立断言(iii-b):跨节基数一律改为指名该列举,不得复述数字) |
| **(91)** | **排除清单用【固定全标题正则】,不具版本可移植性** —— v1.12 的 B-13 标题多"机械"与版本后缀 → **命中 0 节**;v1.13 的 B-14 标题多";v1.13 新增" → **命中 3 节**,而 v1.13 的记录值**恰好就是排除那三节的结果**。**这是"四个 hash 三种口径"(事故 (50)) 的机械成因 —— 不是有人选错口径,是正则静默失配** | v1.12(首次发生)/ v1.19(查明) | ✓ **v1.19 修**(改为行首 `**B-<n>` 标题行枚举,版本可移植) |
| **(92)** | **"锚串未命中即红"只打印、不阻断** —— `hashobj` 在 `bad` 非空时打印一行提示后**照常返回对象**,于是失配的那一节**静默地没被排除**,而调用方拿到的是一个看起来正常的 hash。**"即红"写在规范里十七轮,实现里从来只是一条 print** | v1.14(首次写入)/ v1.19(查明) | ✓ **v1.19 修**(锚失配或标题重复 → 阻断,不得继续);**并入 DoD** |
| **(93)** | **发版前自检器自 v1.16 之后一次都没成功跑过** —— 它把"v1.15 → v1.16"这一行标签与两个产物文件名**写死在源码里**,在 v1.17/v1.18/v1.19 上直接 `AttributeError` 崩溃;**它稿内出现 0 次、无规则区块标记、不在断言③ 的模块循环内**,于是**没有任何断言会因此转红**;而三版都写着"发版前自检",实跑的是临时内联脚本 —— **那正是元规则(九) 第一句禁止的自述,只不过套了一层工具输出的壳** | v1.16 | ✓ **v1.20 修**(元规则(九) 第六句:求值器同受约束;补第四个规则区块;版本无关定位;退出码为门) |
| **(94)** | **v1.18 新立的 DoD 硬门,其两侧集合全文不存在**:`\| 机制 \|` 零命中、无正控制目录;同版声称"九条新机制均已配上构造式正控制"而**实测只有三条** —— **在立下硬门的同一条里违反了硬门**,且正是 v1.17 变更⑪ 要抓的"全称量词半落地、落点检查为绿" | v1.18 | ✓ **v1.20 修**(机制清单十二条就地列举 + B-11 扩为唯一权威目录 + 双向覆盖 + 覆盖计数) |
| **(95)** | **断言③e 不比对【模式列】,而模式列在稿表是自然语言、在区块是正则** —— 两种语言无法逐行比对;两侧一致地把 `{4,}` 收窄为 `{9,}` 可使**十条断言全绿**而 `MATCHED`/`SCANNED`/`CLOSED`/`FAILED` 等一批取值**静默脱离断言(i)**;**分层计数只报分子,没有任何断言核验分母** | v1.18 | ✓ **v1.20 修**(模式列改写正则本身 + ③e 含模式列 + 立③f 棘轮与③g 对稿覆盖) |
| **(96)** | **`<!-- generated -->` 标记"由谁写"未定义**:检查器写则自指(可把标记打在规范文字外围,那段同时离开三器视野)、人写则是**无上界的逐行手工减法**(元规则(五))—— **排除面形状的第三次**(区间式 (49) → 小节 (86) → 行标记) | v1.18 | ✓ **v1.20 修**(标记由检查器写 + 断言②b 渲染一致性 + 区块数量与起止的双向覆盖上界) |
| **(97)** | **`consumed` 键集只钉"每项被求值过",不钉"每项进入了汇总"** —— 逐项算出结果、汇总时少算一项的伪实现,四断言全绿而输出不是完整输入面的函数 | v1.18 | ✓ **v1.20 修**(聚合量须声明归约式,由自检在产物 JSON 上重算);*(当前实现 `n_cand = len(miss)` 恰好可推导,**规格缺口真、实现凑巧对**)* |
| **(98)** | **DoD 与权威定义成组陈旧,连续第五版**:本版又修四处("十六类"、"五阶段"、"四方覆盖"、"五出口 XOR")—— **断言(ii) 本该抓它,而断言(ii) 至今没有实现** | v1.15–v1.19 | ✓ **v1.20 逐条改**;**根因由【断言冻结】条款承担** |
| **(99)** | **暂态优先格掩盖构造非法**:分类器第 1 行优先级最高,会吞掉第 7 行的 `covers ⊇ primary_owner` 破坏 —— **第 7 行检的是构造 bug、不是状态,不会因暂态消解而消失** | v1.18 | ✓ **v1.20 修**(不变式提为标准化期独立断言,暂态不豁免;第 7 行降为补格 + 监控量,命中数须恒 0) |
| **(100)** | **零定义那一半的产出形态让它等于没抓到**:一个新引入的对象**必然**零定义,所以它对新增同样敏感,**而 79 条历史欠账把它淹没了** —— v1.18 写"零定义那一半不活",**结论对、归因错** | v1.16 | ✓ **v1.20 修**(零定义分两栏:历史欠账 / 本版新增;乙栏非空即红,不得与历史欠账一并延后) |
| **(101)** | **外部锚只验二元组** —— 捕获 `(稿名, 版本, 小节)` 却只核验前两项,**不存在的小节只要稿名与版本对就能通过** | v1.19 | ✓ **v1.20 修**(三元组精确核验 + 为七份冻结稿建小节标题索引) |
| **(102)** | **`shadow_until` 无上界** —— 只写"当前版本 ≤ 该值",实现者写一个远期版本即可长期留在影子模式 | v1.18 | ✓ **v1.20 修**(语义版本元组比较 + 须等于引入版或其唯一下一版 + 修改须单独审计) |
| **(103)** | **`HISTORICAL_REFERENCE` 例外无可数上界** —— v1.19 写了"须带明示标记"而没写上界 | v1.19 | ✓ **v1.20 修**(occurrence 数随产物给出,逐处可数) |
| **(104)** | **第四类灰区:论证性散文** —— 行粒度排除只区分"规格句"与"产物行",而记录区里的论证/结论叙述两者都不是;按"标记之外一律进视野"它会整段进 B-13 子句集、每版重写一次,**候选差集被噪声淹没** | v1.18 | ✓ **v1.20 修**(归入已有的 X4 括注型,须以 `*(` 起写;**不新增第九条排除模式**) |
| **(105)** | **随稿产物不是由随稿的稿产出的**:`b13_v120.json` 写 `n_new = 2425`,而用随稿的同一份脚本在随稿的同一份 v1.20 上重跑得 **2431**(甲、丙各自实跑同值,三方一致)。成因 —— **跑完两器之后又改了规范正文,只重跑了 `ident_check3`,没重跑 `norm_diff5`**,于是 `b14_v120.json` 与稿逐字节相符而 `b13_v120.json` 对的是一个更早的稿。**一次发布里的两个产物对应两个不同的稿状态**;**这正是断言① 的活体实例,而它没有转红,因为没有东西在跑** | v1.20(本方) | ✓ **v1.21 修**(§7【发版包与发版顺序】:五步固定顺序 + 跑后改动须重跑两器 + 断言① 的 `v(n)` 侧输入钉为"将要发布的那个字节串") |
| **(106)** | **发版包缺件**:上一轮实发四件,**`v1.19` 没发**,而 prompt 的清单里列着它 —— **两家都无法复算 B-13**(B-13 是 `v(n-1)` 与 `v(n)` 之间的差)。**清单与实发不符**,是"复核包送不到"的第三种形态(前两种:清单来了文件没来 ×2) | v1.20(本方) | ✓ **v1.21 修**(六件套缺一不得发布 + 发版说明列六件 sha256 并与实发逐件比对) |
| **(107)** | **X8 在稿内有三种互斥写法**:§1.0a 修订纪律⑧ 写"B-13/B-14/B-14a/B-15 四节的内容"(小节粒度,且含已移出排除清单的两节)、嵌入的 `norm_diff5` 区块写"本次运行产物所在小节的内容"(小节粒度)、§8-1 写"按【行】判定" —— **三句都是规范句,事故 (25) 的形态,而这一次落在决定三器视野的那条规则上** | v1.18 | ✓ **v1.21 修**(三处统一到行粒度;**§8-1 的判别法为唯一权威表述,另两处改为引用**) |
| **(108)** | **②b 的渲染器站在圈外**:v1.20 写"渲染器置于规则区块内",**而全稿只有四个规则区块,没有一个装着渲染器** —— 与同版抓出的"求值器站在圈外"同形,**只隔了一版**。活体实例:**附录 B-14 快照表的 v1.20 列把 Tier C 两格填成了 v1.19 的值**(表内 `3 + 77 = 80`,而同表合计写 88),**而随稿的 `b14_v120.json` 是对的** —— 那张表本就该由产物渲染,它是手写的 | v1.20(本方) | ✓ **v1.21 修**(渲染器并入第四个规则区块的 `RENDERERS` 声明表;该表登记为生成区块并按产物改正) |
| **(109)** | **机制清单写"十二条"而就地列举十四项,且覆盖计数的 `N` 无来源** —— **而这两者都是【解冻条件】的一侧,于是【断言冻结】在字面上无法被解除**;另:**零定义分栏可被"提前一版提名"洗白且已经发生**(`UNKNOWN_LEDGER_EXIT`、`HISTORICAL_REFERENCE`、`shadow_until` 三个 v1.18 新机制的标识符,到 v1.20 全在(甲)历史欠账栏里;`v1.18 → v1.20` 消解数 = 0、新增 9) | v1.20 | ✓ **v1.21 修**(基数改十四条 + 每条登记机制 key + `N`/`M` 各自指向可枚举集合;(乙)栏判据改"不在 v(n-1) 规范正文中出现" + 机制 key 一律落(乙)栏) |
| **(110)** | **`NONIDENT` 注释写"十七条"而实列 27 条** —— **【基数不符】的第五次**(前四次:(20) 元规则标题、(46) 词法表、(48) 排除集、(75) `sectext`),**由 v1.20 自己新加 (d)(e) 两类引入,发生在写着断言③b 的同一版内**,仍由发版前人工清点抓出;另 `EXCLUDED_ENUM` 把 `B-1[345]` 写死,不可前向扩展 | v1.20(本方) | ◐ **v1.21 已改为三十条**、记录小节改 `RECORD_SECTIONS` 标签集合;**根因未闭合**:③b 与 (iii) 仍未实现,**五次全部靠人眼**;收口条件 = ③b 与 (iii) 交付 |
| **(111)** | **自检项登记表漏登**:v1.20 立的登记表只登了十六项,而本稿写着"即红"的自检规则还有十三条从未入表(记录小节锚唯一、生成标记合法、覆盖双向、删文三态登记完备、变更块落点、"已修"格核验、影子期上界、阶段列、机制清单 × B-11、发版包一致、定义节上界、枚举成员整体、归约式重算)。**v1.21 把解冻谓词改成"登记表每项通过"之后,这十三条在一条都没实现的情况下解冻照样成立** —— 与丙 BLOCKER-5(v1.21 轮)同形,只是漏在登记表的分母上 | v1.20 | ✓ **v1.22 修**(全部登入工具规格 C7,每项指回本稿原条款,不新立) |
| **(112)** | **断言 (iii-b) 没有规范定义**:它出现在登记表、事故 (90) 与 v1.18 变更摘要,而全文找不到"怎么判";要实现它的人无从下手 | v1.18 | ✓ **v1.22 修**(工具规格 §7.4 给出识别口径) |
| **(113)** | **非标识符排除清单自称"四个上下文标签均已登记",实际漏了 `RULEBLOCK`** —— 那句自称写在清单的注释里,与"基数不符"同一家族:**关于清单的陈述没有被清单本身核验** | v1.21(本方) | ✓ **v1.22 修**(工具规格 C4 补上;上下文区域首次在 C4a 给出机械定义) |
| **(114)** | **角色越界:v1.14–v1.21 的检查脚本由设计方编写并运行,脚本常量以代码形式嵌入本稿,各版实测值由设计方自跑填入** —— **写规则的人与证明规则被执行的人是同一方**;(105)(106) 两个交付事故都发生在"设计方自己跑工具"的环节;元规则(九) 第一句禁止"自然语言的『本版已实跑』自述",而由规则作者自跑自填的数字,**在证据地位上与自述无异** | v1.14–v1.21(本方;FatTank 指出) | ✓ **v1.22 修**(本稿去代码;旧实测值全部作废并移除;工具规格独立成文交 Codex 实现与运行;发版流程每步写明执行方,设计方不执行运行工具的步骤;被绕过表补第十七行) |
| **(115)** | **v1.22 的评审包缺 `v1.21`**:两家都报告未收到,"迁移有没有丢东西"这一项 —— 工具未交付期里唯一替代机械删文检查的人工核对 —— 因此没能完成(甲改用 v1.20 代基线,丙判无法确认)。**连续第三轮交付缺陷**(v1.19 漏发、v1.20 产物与正文不同源、v1.21 漏发),且发生在刚为此立了发版包条款之后 | v1.22(本方) | ✓ **v1.23 修**(未交付期发版清单 + 发版清单在 prompt 正文复述 + 收件方先核对、缺件即记该项未完成、不得自选代基线;本轮重附 v1.21) |
| **(116)** | **迁移丢失与迁移映射表指错**:v1.22 把 §8-1 细则移入工具规格时丢了五处 —— C4 只许字面全等、影子期语义与修改审计、多定义的 canonical 消解(**迁移映射表点名说它在工具规格 §6.2–§6.4,实际没有**)、重命名候选与零定义新增项求交、全称量词覆盖计数由工具计算(v1.0 改成由人填,变弱);另一处语义变化未申报 | v1.22(本方) | ✓ **v1.23 修**(全部补回工具规格 v1.1;迁移映射表逐行更正并标注) |
| **(117)** | **规范正文里残留设计方自跑脚本的结论**(元规则(九) 第四句 (a) 的"B-14 实跑当场报出多定义"、(a-bis) 的"当前实现恰好可推导"、修订纪律中"该条仅命中一行、完全冗余"等),与 v1.22"旧实测值全部移除"不一致 | v1.22(本方) | ✓ **v1.23 修**(逐处改为"出自自跑脚本,不作证据"或改指事故编号;评审方的运行与抽样保留署名) |
| **(118)** | **本方的文本输出会把部分全角标点写成半角**:工具规格 v1.0 中本应是全角的分号、逗号、括号、冒号被写成半角重复(`;;`、`,,`、`()()`、`::`),中文分号因此不会被切分;**本稿全文的全角分号、逗号、冒号出现数都是零**,可见这不是个别笔误。**凡依赖全角字符的规格常量,单靠"看起来对"无法核验** | v1.0(本方;丙指出) | ✓ **v1.23 修**(工具规格 v1.1 中依赖全角字符的常量一律附码点说明,并由解析金标 C18 逐项核验) |
| **(119)** | **文档自检机制喧宾夺主**:v1.14–v1.23 为本稿自身建了一整套机械自检(元规则(九)、删文检查与冲突对账工具、hash 对象、断言③ 族、断言冻结、发版包、工具规格),**它只管"这份设计文档自己有没有写错",却成了冻结前置条件**,最近六轮评审几乎全部花在它上面,而五个事项的设计本身少有人审 | v1.14–v1.23(本方) | ✓ **v1.24 修**(按 FatTank 裁决整体移除,回到人工修订纪律 + 三家评审;本台账 (33)–(118) 中与该机制相关的行保留为历史记录,不再构成任何义务) |

> *(v1.22 注:本台账各行为描述事故而引用的数字(子句数、标识符数、候选数、hash 值等),
> 多数出自设计方自写自跑的旧脚本,**保留为历史叙述,不作为证据引用**;
> 需要数值的结论,一律以 Codex 交付后的回溯重跑为准。)*

> *(B-13 自查记录:上一段的 (24) 行在本版初稿中被误删,**并被错误地注为
> "编号空洞"**——该行是 v1.11 首报、v1.12 已修的真实事故。**由本版 B-13
> 的删文检查当场抓回并恢复**,此处保留说明以备追溯。)*

**"已修"纪律**:每写一条"**已修**",须在同一轮给出**可复核的证据**(改后原文或位置)。
**修订纪律**:见 §1.0a 末(v1.24 起为人工纪律:变更块申报删改 + 同对象规范行逐条对账 + 评审方复核)。

**已退役编号的一次性登记(v1.14;由本版 B-14 自查抓出)**

> **`闸门 1` / `闸门 2` / `闸门 3`**:v1.12 曾以此三编号指称 claim 型别的三条
> 闸门;**v1.13 起整体由「型别默认反转 + 三条禁止」取代,编号退役**。
> **本稿仅在事故台账 (27)(34) 与恢复登记中作历史引用,不再作为规范条款编号**;
> 三者的规范内容分别由:**闸门 1** → §8-2 豁免上界 (iv)「豁免 claim 不得带
> predicate 块」;**闸门 2** → §8-2「型别默认反转」(锚 = SEAL-16 的引用集);
> **闸门 3** → §8-2「事实纪律扫描按 claim 归属逐句核」**承接**。
> *(本条即"零定义标识符"的合法消解方式:**要么删掉引用,要么给它恰一处定义**;
> v1.13 对"闸门 2"两者都没做,故为悬挂引用。)*

### 8-2 实测值纪律

> **总判据**:**一句话是否为实测值,取决于它是否由一次对快照的观测产生、
> 是否需要一条命令才能复算——与它是不是数字无关。**

**分类对象**:**每个事实性 claim**。**类零推理若依赖当前树事实,
必须把事实前提拆成 claim。**

**五分类(优先级:类四 > 类一;∃ 与比较同现按比较处理)**

| 类 | 定义 | 处置 |
|---|---|---|
| **零 · 规范规则与解释性推理** | 规定、原则、推理、设计意图 | **不受禁令约束**(事实前提须另拆为类一) |
| **一 · 实测值** | 由观测产生、须命令复算 | ∀/¬∃/比较/序数**禁止手填**;∃ 须**具名见证** + claim key |
| **二 · 快照标识** | commit SHA、tree hash、版本号、批次名 | **保留** |
| **三 · 规则常量** | 规范自身定义的基数与编号、枚举值名、**白名单成员、排除规则、正控制取材规则、golden 期望、豁免清单、标识符提取规则**、**就地列举的分类** | **保留**。**判别法**:数字与紧邻列举项数不符即**文本事故**;**"就地列举"与"由规则导出"是两回事,不得混称** |
| **四 · 规格锚点** | 定义"本批要改什么"的源码坐标 | **保留**——**类一的受控例外**;**须带 anchor ID + 机械 selector(非行号)+ 验证结果引用** |

**`OBS` claim 记录:两型分治 + 默认反转 + 三条禁止 + 豁免清单四条上界**

> | 型 | `expected` | SEAL-15 判据 |
> |---|---|---|
> | **`MEASUREMENT`** | **无**(字段必须缺省,**不得填空值冒充**) | **产出非空 + schema 合规 + `snapshot` 匹配** |
> | **`ASSERTION`** | **结构化 predicate 块**,**A₀ 首跑前登记、冻结带 hash** | **产出满足 predicate** + **round-trip 逐字一致** |
>
> **型别默认反转**:
> > **正文中被引用的每个 claim 默认为 `ASSERTION`**;
> > **唯有列入冻结的"报告/人工输入"豁免清单者才可为 `MEASUREMENT`**。
> **理由**:v1.12 的判据是"**被**承重条款引用 ⟹ 必须 `ASSERTION`",
> **导出器漏判一条引用即让该 claim 悄悄退回纯观测、不验内容,漏判代价为零**;
> 反转后,漏判 → 被**多**要求成 `ASSERTION`(**过严、无害**)。
> **锚**:**SEAL-16 已有的引用集**(纯文本扫描),
> **不需要"什么算承重条款"这层分类——而正是这层分类构成了此前的新声明面**。
> **另补**:**凡规范判断句依赖某 claim 内容者,必须显式引键,无键即红。**
>
> **豁免清单的四条机械上界(v1.14;三家 MAJOR——反转之后它是唯一收窄面,
> 按元规则(五)必须有"它不可能减掉什么")**:
> > **(i) 逐字点名**:每个条目必须是一个**字面 claim key**,且该 key
> > **须在附录 B 有定义**;**不得使用模式、前缀、类别或任何通配形式**。
> > **上界 = 清单基数 = 逐字点名数**,机械可验。
> > **(ii) 与决策面不相交**:**豁免清单 ∩【§0–§7 的全部规范条款】的引用集 = ∅**;
> > **非空即红**(v1.15 按乙 MINOR-3 扩面:原枚举"规范判断句 ∪ SEAL ∪
> > admission ∪ disposition ∪ DoD"**漏掉 §3/§4/§5 的规格锚点节与 §6 门禁**)。
> > **(iii) 引用用途标注**:每处引用须标 `use = GATE | REPORT | HUMAN`;
> > **豁免 claim 的 `GATE` 引用数必须为 0**。
> > **该标注【必须由 (ii) 的机械分类产出,不得人工指定】**(v1.15;甲 MINOR)
> > ——否则没有任何东西阻止把一处 `GATE` 引用标成 `REPORT`,
> > **等于把 (ii) 已机械覆盖的事情,换成一个可由标注者调整的声明**;
> > 加上这一句,(iii) 退化为 (ii) 的展示层,**不再是独立的收窄面**。
> > **(iv) 不得带块**:**豁免清单内的 claim 不得带 predicate 块,带块即红**
> > ——*(此条即 v1.12"闸门 1"的另一半:反转只管"谁可以是 `MEASUREMENT`",
> > 不管"豁免项能否带块";带块而豁免则该块**永不核验**。"闸门 1"的这一半由本条承接。)*
> **本版实例化**:**豁免清单 = ∅**(显式声明,履行"就地列举"义务);
> **冻结时点 = A₀ 首跑前**,**由 A₀ 随 predicate 一并带 hash 冻结**;
> **扩充走变更流程**。
>
> **三条禁止**:
> 1. **禁止从自由文本推断 predicate**——必须以**结构化块**书写;
> 2. **禁止实现方补写 `expected`**——否则手填 oracle 原样回归;
> 3. **解析失败或空 predicate 一律红**;**`ASSERTION` 无 predicate 块或块为空
>    即红**——否则空块被**任何**产出满足,**全部判据同时绿而内容零核验**。
>
> **事实纪律扫描的粒度(v1.14 恢复;v1.15 补回其理由)**:
> > **该扫描【本就是】型别误标的拦截器**——"正文无断言 ⟹ `MEASUREMENT`
> > 标注正确";**此前只做全文级,而"全文级通过"不等于"每个 `MEASUREMENT`
> > 的那一句都通过"**。
> > **按 claim 归属【逐句】核**——每个 claim 的正文引用句须**单独**通过扫描;
> > **全文级通过不等于"每一句都通过"**。
>
> **predicate 的"真值来源"边界**:
> > **predicate 是"要求",不是"陈述"。** 陈述的真值由**当前树**决定(归类一);
> > **predicate 的真值由比对结果决定**(归类零)。
> **该归类仅在两条成立时有效**:①**首跑前冻结带 hash**;
> ②**producer 不输出 pass/fail**。
> **另**:**块内不得内嵌任何需命令复算的当前树值**,块内容只允许类二/类三。
>
> **round-trip 与 renderer 隔离**:
> > **predicate 的 canonical serialization 为权威;正文旁注必须由唯一
> > renderer 生成并置于 generated block;逐字比较 renderer 输出;
> > 禁止手写同义表达。**
> **为何必须钉死为渲染产物(v1.15 恢复两段理由)**:
> > **若旁注允许人手撰写,自然语言有无数合法表述,比对【几乎恒红】,
> > 实现期必被当作"过严"而放宽——那时"保真"这一重就没了。
> > 钉死为渲染产物之后,它【恒绿且有意义】:绿说明旁注确由 predicate 生成,
> > 红说明真的漂了。**
> > **generated block 带 `renderer_version`**;
> > **同 `renderer_version` 同 predicate 的重生成输出必须逐字不变,变即红**;
> > **`renderer_version` 变更的提交不得同时包含任何 predicate 变更。**
> **这三条的作用**:批量重生成**只能出现在纯 renderer 升级提交里**,
> **真实的语义漂移永远落在 `renderer_version` 未变的提交里,一条都跑不掉**。
> **不得把 `renderer_version` 塞进 predicate 的 hash 对象**——那会让升级使
> 全部 predicate hash 失效,比问题本身更糟。
> **不兼容升级的逃生口(v1.14 补,甲 MINOR)**:
> > **renderer 升级须向后兼容全部在册 predicate。**
> > **确需不兼容升级者,必须先走一次【predicate 迁移提交】
> > (`renderer_version` 不变,把 predicate 改为新旧 renderer 都能渲染的
> > 等价形式,等价性由该次提交的 round-trip 逐字比对自证),再升版本。**
> 不补此条时,"某条在册 predicate 在新 renderer 下渲染失败"会与
> "版本变更提交不得含 predicate 变更"**互锁**。
>
> **构造式证伪**:`ASSERTION` 四条(翻转 predicate / 交换 `subject` /
> 使用旧 `snapshot` / round-trip 不一致);`MEASUREMENT` 一条(产出为空);
> **型别三条**(空 predicate / 解析失败 / 被引用却列入豁免清单而无理由);
> **豁免清单四条**(通配形式 / 被决策条款引用 / 带 `GATE` 引用 / 带 predicate 块)。

**claim 记录 schema**

```
claim_id   : OBS-<n>.<slug>
type       : MEASUREMENT | ASSERTION   ← 默认 ASSERTION;MEASUREMENT 须在豁免清单内
subject    : 被断言/被观测的对象
predicate  : ASSERTION 必填(结构化块,非空,可解析);MEASUREMENT 必须缺省
quantifier : ∃ | ∀ | ¬∃ | 比较 | 计数
snapshot   : tree hash
producer   : 产出命令(只输出原始事实)
verifier   : 通用比较器(不由 producer 兼任)
renderer_version : 生成正文旁注的 renderer 版本
references : [ (引用位置, use = GATE | REPORT | HUMAN) ]   ← v1.14,供豁免上界(iii)
```

**本稿的 SEAL-15 适用范围(v1.14 明写;丙 MAJOR 1 尾)**:
> **本稿【不声称】自身已通过 SEAL-15。** 附录 B 的各 claim 目前登记的是
> **键、型别、producer 与义务**;**其 predicate 块是 A₀ 的交付物**,
> 在 A₀ 首跑前登记并冻结带 hash。**SEAL-15 的适用对象是 A₀ 之后的实现产物**,
> 不是本设计稿。**在 predicate 块落地之前,任何"本稿已通过型别闸门"的说法
> 都不成立。**

**两条否定豁免**:被明确否定的历史错值须带"*历史记录,已否定*"标注、
**不得被引用为依据**且**不复述其值**;本节对类别的举例属**类三**。

**未闭合项**:无。

---

## 附录 A:与前七批的差异声明
- **允许行为变更**(唯一批次),parity 形态改为"差异恰为预期集";
- **允许测试数量变化**,基线口径改为"逐项说明增减";
- **零新抽取**;**终止条款生效**:5 项不得再延期、不得转交。

> **交付附注(非规范)**:本稿的**八条元规则 + 自我适用条款(三段)+
> 修订纪律**覆盖"权威从哪来、看哪个维度、锚在哪、
> 减法有没有界、看了算不算数、重算能不能自证、规则之间对没对账、删文有没有申报",
> **比本批任何一条具体断言都更耐用**,建议整体抬进 campaign 级方法论模板。

## 附录 B:实测快照(**由脚本产出;本附录是唯一可出现实测值的位置**)

**总则**:各节均为 **claim 记录 + 产出命令**。**任何一方的口头值均不得直接
填入。** **正文中的每个 claim key 在此有且仅有一条定义**(SEAL-16);
**必须以正文引用时的完整形式书写**;**每条须标注 `type`**
(**默认 `ASSERTION`;`MEASUREMENT` 须在豁免清单内并附理由**);
**predicate 块为 A₀ 交付物**(见 §8-2 末)。

**B-0 基线** — 全量测试/mypy/ruff 基线;开工前与收口时各跑一次。

**B-1 §0 跨批次复核与规格锚点核验** — claim:`OBS-1.item1-basis`、
`OBS-1.item2-scope`、`OBS-1.item3-predicate`(**含 §3 现状判定式与异常路径**)、
`OBS-1.item4-anchors`、`OBS-1.item5-order`;命令:`verify_anchors.py`。

**B-2 台账三段的来源形态** — claim:`OBS-2.seg1-staleness`、`OBS-2.seg2-form`。

**B-3 第三段跃迁溯源与提交次序** — claim:`OBS-3.commit-order`、
`OBS-3.transition-map`;命令:`shim_inventory.py --audit-transitions --emit-snapshot`。

**B-4 符号归属** — claim:`OBS-4.owner-attribution`。

**B-5 入口消费关系** — claim:`OBS-5.entry-consumers`。

**B-6 粒度④ 候选** — claim:`OBS-6.proxy-count`、`OBS-6.intra-package-shim`。

**B-7 §2 样本与投影** — claim:`OBS-7.falsification-samples`、
`OBS-7.class-c-projection`。

**B-8 扫描完整性、检出能力与判定正确性记录**
- `scan_manifest`(完整 git tree 枚举 + `lstat`);
- **标准化阶段记录**:raw finding 数 / N1 归并后 candidate 数 / π 配对结果 /
  **`|π(c)| ≤ 1` 核验 + 台账侧覆盖义务核验**(v1.16 随动:`|π⁻¹(k)| ≤ 1` 已于 v1.15 撤销;甲 BLOCKER-1 第 4 处、乙) / `LEDGER_KEY_AMBIGUOUS` 计数(须为 0) /
  **(v1.25 补;甲 MAJOR-3)七格分类器逐格命中数(第 7 格须为 0)、每个台账 key 的 `ledger_exit` 及其依据
  (第 3 格附覆盖它的 candidate 清单)、`SOURCE_OBLIGATION_UNENUMERABLE_PENDING` 计数(须为 0,由 §1.3 断言二终局求值)、
  `covers ⊇ primary_owner` 不变式断言结果**;
  **(v1.27 补)暂定第 3 格的每个 key:原始 `covers⁻¹`、`effective_covers⁻¹`、暂定出口与终态出口、
  是否生成 fallback item 及其终态 admission**;**`#INLINE` 走 ④ 的条目记录"外部消费者 = ∅"**;**(v1.28)名字命中兜底清单:文件、位置、名字形态、去处(形态 / 第 9 类排除 / `UNKNOWN_CAPABILITY`),跳过的二进制文件逐个列出;无命中显式记零**;**(v1.29)解释器行清单:文件、行号、所属 `C7` 类别、模块位原文、展开结果或 `DYNAMIC_UNRESOLVED`;doctest 与 `-c` 片段的来源位置与解析结果;(v1.30)每条解释器命令(v1.31:含所在行内的命令序号与选项文法解析结果)与每个以解释器为命令的进程启动调用的代码来源类别(`-m` / `-c` / 脚本文件 / stdin)、stdin 载荷的界定方式(heredoc / here-string / 管道上游 / `input=`)与解析结果或 `DYNAMIC_UNRESOLVED`;删除后验证五项的输入、命令、输出与回退记录**;
- **`SEAL-16b` 五方覆盖记录**(v1.25 补;甲 MAJOR-2):五方各自的原记录、投影到 `(消费者形态, capability_branch)` 的键集与两两差集
  (与 `12b-12` 四方对账的记录分开登记);
- **台账 key 粒度记录**:逐来源自身声明的粒度、π 归一结果、
  `SOURCE_OBLIGATION_UNENUMERABLE` 计数与原因;
- **独立存在性检查记录**:逐 key 的 `PRESENT`/`ABSENT`/`UNKNOWN` 与判定依据
  (**`ABSENT` 须附正面不存在证据,不得以"无 finding"为据**);
- **排除规则登记**:规则 ID / 匹配集 / 互斥性证明 / 边界负控制 /
  **理由字段(为何该条目结构上一律无 shim 候选;空理由即红)** /
  **分类器全函数核验** / **该规则覆盖条目最终进入 `preseal_effective_inventory` 的
  计数(须为 0)** / **该规则覆盖条目产生的 finding 与未决分流逐条记录
  (空记录即红,不设零门)**;
- **注册表**:映射、hash、**完备性四条核验**、**与 capability 双向覆盖**;
- **覆盖矩阵**:四状态;**格级"缺记录"核验**;
  **行级下界核验(含 `NON_SHIM_PREDICTION`)**;
- tree/manifest/detector-set hash、run ID、**completion marker**;
- **十条违例 fixture 的红/绿结果**;
- **12b-10 的实例目录机械导出结果**、**每 `(detector, capability branch)` 的
  正控制与 near-miss 结果**、**独立参与点分类器的分区结果与未知分支计数**;
- **12b-12 四方对账的四个来源清单与两两差集(须全空)**;
- **12b-11 golden 的四元映射与结果(含理由字段)**。

**B-9 四级粒度与解析层扫描的命中分布**
- 列:粒度/形态 / 命中数 / 命中清单 / 分流去向(候选 / `SCAN_UNRESOLVED` /
  `DYNAMIC_UNRESOLVED` / `ledger_membership = UNKNOWN`)。
- **必含零命中记录(十二项,v1.14 恢复;v1.13 压缩为"必要的零命中记录"
  一句,SEAL-13「显式记零」的对象清单随之消失)**:
  ①粒度④ 各 callable 形态、②模块级 `__getattr__`、③`__dir__`、
  ④动态 `__all__`、⑤`sys.modules` 别名注入、⑥import hook / `meta_path`、
  ⑦打包入口、⑧文件系统层别名(符号链接/`.pth`)、⑨命名空间包 portion、
  ⑩gitlink、⑪非 Python provider、⑫条件式导入
  ——**命中为零须显式记零**(SEAL-13);
  与 12b-10 的 capability branch 枚举**逐项对齐**。

**B-10 白名单登记(v1.14 恢复字段规格)**
- **可信断言叶子**:**键 =(qualified callable, 调用形态/实参谓词)** /
  `semantic_class` / **hash 对象与算法** / hash 值 /
  **逐形态构造式语义测试结果(每个登记形态分别证伪)** /
  **实际调用点分区核验(不交并)** / 登记轮次;
- **装饰器白名单**:成员 / 来源 / hash / 登记轮次。

**B-11 构造式控制的【唯一权威目录】与红/绿结果(v1.20 扩;§1.1d、§7 DoD、
§1.0a 机制清单与本节同源;变更⑭ 所称"正控制目录"即本节,不另立第二份清单)** —
**(甲)SEAL / 12b 违例 fixture**(承前);
**(乙)机制正控制(以 §7 机制清单的机制 key 登记;v1.24 精简为五条,v1.29 增为六条)**:
`MECH_CLASSIFIER7` 三条 + near-miss(其中两条是 v1.17 五出口写法会误红的构造,须在旧写法上红、新写法上绿)、
`MECH_FIVE_WAY` 一条 + near-miss(正:从任一方删一条注册边 → 必红;near-miss:新增一种消费者形态并在五方同步登记 → 不红,
且 `12b-12` 不因该 `consumer.*` 分支转红);**另加边界 near-miss 与正控制**(v1.27 立、v1.28 补;以 §1.1 原子形态表末段为准,含进程启动族、零命中与名字命中兜底各例;以下为 v1.27 的四条:
`import pkg.sub as a`、`from . import X`、`subprocess.run([sys.executable, "-m", "X"])`、`monkeypatch.setattr(mod, "x", v)` 各恰落一个形态且不红)、
`MECH_AST_CLAUSE_ID` 一条 + near-miss(正:删 predicate AST 的一个 leaf 而映射不动 → 必红;near-miss:AST 与映射同步增删一个 leaf → 不红)、
`MECH_UNIVERSE_ENUM` 一条 + near-miss(正:独立枚举器产出的 universe 少一个 span,detector 遇到该 site → `UNSUPPORTED` + 整轮重启,必红;
near-miss:注入一个非动态表达式 span → 不进入动态 universe,不红)、`MECH_INVARIANT` 两条(构造 `covers ⊉ primary_owner`,
暂态期同样必红;near-miss:暂态合法组合不红)、`MECH_POST_DELETE` 一条 + near-miss(正:fixture 中某 shim 仅被一个经运行时读取配置文件得到模块名的自定义包装函数引用 —— 静态层判零消费者并删除,删除后验证须转红并回退该组;near-miss:该 shim 确无任何引用 → 删除后验证全绿、不回退);
**与 §7 机制清单逐条对应,缺控制的机制不得进 DoD。**
**B-11 旧自述(承前)**
— 含 SEAL-12b 的**十条**、SEAL-15 的 **`ASSERTION` 四条 + `MEASUREMENT` 一条
+ 型别误标三条 + 豁免清单四条**、SEAL-11 的非法组合与 `LEDGER_KEY_AMBIGUOUS`、
SEAL-12 的 `NON_SHIM_PREDICTION` 抑制例、SEAL-4 的
`LEDGER_PRESENT_NO_FINDING × ALREADY_REMOVED`、SEAL-6 的三条消化违例(人工直接写结论;完整性未决却产出 ②;终态越出 `uncertainty_kinds` 交集输出域)。

**B-12 RC-1 运行记录(v1.14 恢复字段规格)** — sentinel 模块名 /
`parent_pid` / `child_pid` / **父进程该模块事件数(须为 0)** / 失败原因 /
钩子安装方式(**不得为 `PYTHONSTARTUP`**)/ **正向刻画的结论边界**。

**B-13 / B-14(已撤销,v1.24)** —— 原为本稿自身的删文检查与冲突对账记录,
随文档自检机制整体移除(事故 (119))。编号保留不复用;此前各版的记录均出自设计方自跑的脚本,已于 v1.22 作废。

**B-14a `UNRESOLVED_DISPOSITION` 与 `INDETERMINATE` 的消化记录** —
逐项结构化证据 `(claim, 判据, 命令, 输出)`、**`uncertainty_kinds`(机械导出的多值集合,人工不得填写;
取值见 §1.1c 八类矩阵)**、**人工补入的事实输入清单**、
**判据重跑产出的终态**(**非人工直接书写的结论**)、
**输出域核验(须落在 `uncertainty_kinds` 各成员输出域的【交集】内;
越界出现即红,`DELETE_DIRECT` 在【八类】下一律永禁)**。

**B-15 per-candidate disposition evidence bundle(SEAL-9 一并冻结)** —
每个条目的判据输入(消费者集合、闭合调用图、叶子 `semantic_class` 标注、
A/B 取值、**存在性检查证据(`lstat` 语义)**、**π 归一结果**、
**`EXISTENCE_CONFLICT` 命中时的两侧证据**)与结论,
**供删除后追溯"判据写错"与"执行错"的区分**。

---

## 附录 C:冻结后勘误

> 本附录按冻结规则第 3 条追加:实现期停止-报告 → 设计方出勘误 → FatTank 批准。**勘误不改动正文任何一行**;
> 正文与勘误冲突处以勘误为准。每条勘误写明触发的停止报告、所补的空位与生效范围。

### 勘误 1(2026-09-29,FatTank 批准)—— §6 预期差异登记的取值来源与超时消息的生成规则

**触发**:A₀ 第 2 段停止报告 DIFF-01、DIFF-02(stage14 `progress.md` §13)。

**E1-1 · §6 登记新值的来源范围**(DIFF-01)
> `expected_diff.json` 中每条 `DIFF_SET` 登记的**新值**,只能引用下列来源之一,并在登记中写明来源位置:
> (i) skill-5 v1.3.2-FROZEN §3.2 结果映射表的具体单元格;
> (ii) skill-5 v1.3.2-FROZEN §3.2 映射表下方关于"末批 parity 须预先把 `timeout=None` 这个透传 kwarg 声明为掩码/白名单项"的段落;
> (iii) 本稿 §3 的"预期差异"条目、§4 的"验收口径"条目(含"默认 `timeout=None` 时调用轨迹中唯一允许的差异是新增的 `timeout=None` 关键字实参")、§5 的"§6 登记"条目;
> (iv) 本附录的勘误条目。
> **旧值**只能来自 OBS producer 的产出字段,或 §4 规定的"不存在"(`{"state":"ABSENT"}`)。
> **`timeout=None` 的登记方式**:六个调用面在"默认 `timeout=None`"场景下,调用轨迹中对应那一次调用的关键字实参集合**逐面登记**一条
> `DIFF_SET` 差异(旧:该关键字 `ABSENT`;新:`timeout` 值为 `None`);**不得**用全局掩码或"忽略 `timeout` 关键字"的方式处理。
> 除这一项外,该场景的其余字段一律精确相等。

**E1-2 · 超时时异常消息与告警码的确定性生成规则**(DIFF-02)
> 映射表中的 `<message>` 与 `GIT_TIMEOUT:`/`GIT_TIMEOUT: …` 按下列规则取精确值;`exc` 指该调用面捕获到的 `subprocess.TimeoutExpired` 实例:
> | 调用面 | 超时时的结果(精确) |
> |---|---|
> | skill-3 query 阶段、git 阶段 | `GerritError(code="FETCH_TIMEOUT", message=str(exc))` |
> | 本 skill(gerrit-submit)`_run_git` | `GerritSubmitError(code="GIT_TIMEOUT", message=str(exc))` |
> | 本 skill `ls-remote` | 返回的告警列表中该项为字符串 `"target_head_unknown:timeout"`,**不附原异常文本** |
> | shared/workspace `_run_git`、`_exclude_private_files` | `WorkspaceViolation` 的消息为 `"GIT_TIMEOUT: " + str(exc)`(冒号后一个半角空格) |
> **理由**:`str(exc)` 由触发超时的命令与超时值唯一决定,固定 fixture 下可复现,不需要另造文案;
> ls-remote 的告警码按映射表"码值统一、不含原始异常文本"的本意取固定串。
> **登记方式**:`expected_diff.json` 中这些消息的新值写成"由规则派生"的形式:登记规则名(`TIMEOUT_MESSAGE_FROM_EXC` 或
> `GIT_TIMEOUT_PREFIX_PLUS_EXC`)与本勘误编号,门禁在固定 fixture 上按规则算出精确期望值后**逐字比较**;
> **不得**只比前缀、忽略消息或写占位串。
> `GerritError`/`GerritSubmitError` 以 `code` 与 `message` 两个字段进入 §6 结果对象;`WorkspaceViolation` 以消息全文进入。

**生效范围**:仅 §6 登记与项 4(§4)的实现;不改变任何 SEAL、判定条件或其它事项。

### 勘误 2(2026-10-07,FatTank 批准)—— 改走既有分支的输出值,以及 `timeout=None` 登记的场景范围

**触发**:A₀ 第 2 段停止报告 DIFF-03(stage14 `progress.md` §15.3);E2-2 为设计方同时补上的同型空位,避免下一处再停。

**E2-1 · 被改道进入"改前已存在、本批未改"的分支时,该分支产生的输出字段取何值**(DIFF-03)
> 某场景因本批改动而进入一个改前就存在、且本批不改其文本的代码分支时,该分支产生的每个输出字段,其新值 =
> **该分支对本场景输入的产出**,按下列方式确定(规则名 `EXISTING_BRANCH_OUTPUT`):
> (i) 分支以 OBS producer 已锚定的源码位置为准(机械 selector,非行号);
> (ii) 同一分支在改前已有至少一个相邻场景的观测实例(OBS 产出中的原始字段),用以证明该分支产出的形式;
> (iii) 门禁按分支的产出规则代入本场景的 fixture 输入,算出精确期望值后**逐字比较**。
> 登记写成"由规则派生":规则名 `EXISTING_BRANCH_OUTPUT` + 本勘误编号 + (i) 的锚点 + (ii) 的观测实例路径。
> **本批唯一的适用实例 —— §3 悬空 symlink 场景**:分支 = ANCHOR-3 所在函数中抛出 `SOURCE_DIR_UNSAFE` 的分支;
> 相邻观测 = `OBS-1.item3-predicate` 的 `LIVE_SYMLINK_TO_DIR` 场景;
> 消息新值 = `"source directory is a symlink: " + str(<悬空场景的 destination 路径>)`(与该分支对 live symlink 的产出同一形式,只代入本场景路径);
> `code` 新值 = `SOURCE_DIR_UNSAFE`、异常类型新值 = `GerritError`(§3 已规定);**旧消息**取 OBS 产出的原始字段。
> 若门禁发现该分支在相邻场景的实际产出与上述形式不符,说明锚定或观测有误 → 停止报告,不得改用其它文案。

**E2-2 · `timeout=None` 关键字的登记覆盖所有经过新签名的场景**
> E1-1 中"逐面登记 `timeout` 关键字差异"不限于"默认 `timeout=None`"场景:**凡在改后会经过该调用面新签名的场景**
> (默认、外部中断;以及 §3、§5 中途经这些调用面的场景),调用轨迹中对应调用的关键字集合都逐面逐场景登记这一条差异
> (旧:`ABSENT`;新:该场景实际传入的值 —— 默认与中断场景为 `None`,超时场景为 fixture 设定的超时值)。
> 超时场景中,结果字段的旧值按 §4 一律为"不存在"(改前无法表达该场景),新值按映射表单元格与 E1-2。
> 除本条与 E1-1、E1-2 所列项外,其余字段一律精确相等;**仍有字段找不到来源时,停止报告,不得自行补来源**。

**生效范围**:仅 §6 登记;不改变任何 SEAL、判定条件、实现目标或其它事项。

### 勘误 3(2026-10-07,FatTank 批准)—— 超时场景的"改前"一侧如何运行、旧值从哪来

**触发**:设计方核对 A₀ 第 2 段门禁登记(commit `8e1437d`)时发现的空位,未等实现期停下:
§4 验收口径写"超时场景旧值为'不存在'",而 `OBS-1.item4-anchors` 已在改前代码上以"测试替身在同一调用处抛出
`subprocess.TimeoutExpired`"的方式观测到了超时场景的实际结果(异常类型 `TimeoutExpired`、消息为该异常文本、ls-remote
告警为 `target_head_unknown:<异常文本>`)。门禁按"实际差异恰为登记差异"逐字比较,若改前一侧照此运行而登记写"不存在",必然判红;
若改前一侧不运行,则残留状态等字段无从比较,超时场景的残留 parity 落空。

**E3-1 · 超时场景的改前运行方式**
> 改前一侧以**同一 fixture、同一调用处注入 `subprocess.TimeoutExpired`** 的方式运行;因改前签名没有 `timeout` 参数,
> 调用时不传该参数(这一项差异按 E2-2 登记)。改后一侧传入 fixture 设定的超时值,由测试替身在同一调用处抛出同一异常。
> 其余输入一律相同。

**E3-2 · 超时场景的旧值来源**
> 超时场景各结果字段的旧值取**改前一侧的实际运行结果**,与 `OBS-1.item4-anchors` 对同一场景的观测须逐字一致(不一致即停止报告);
> **§4 验收口径中"旧值为'不存在'"一语,对超时场景改按本条执行**;勘误 1 E1-1 中"旧值……或 §4 规定的'不存在'"的后半句随之不再适用于超时场景。
> 由此,超时场景只登记**确实变化**的字段:异常类型(`TimeoutExpired` → 映射表规定的具名类型)、错误码(无 → 映射表规定的码,
> `WorkspaceViolation` 无错误码字段,不登记)、消息(仅当 E1-2 的规则使其改变时登记 —— shared 两面加 `GIT_TIMEOUT: ` 前缀;
> fetch 两面与 submit `_run_git` 的消息按 E1-2 仍为 `str(exc)`,与改前相同,**不登记、须逐字相等**)、
> ls-remote 的告警与返回值(`target_head_unknown:<异常文本>` → `target_head_unknown:timeout`),以及 E2-2 的 `timeout` 关键字。
> 残留状态、marker、调用轨迹等其余字段改前改后须完全相等(对应 §4"残留不自动回滚")。

**生效范围**:仅 §6 中超时场景的运行方式与登记;不改变映射表裁决、实现目标、SEAL 与判定条件。

### 勘误 4(2026-10-07,FatTank 批准)—— 扫描清单条目的分类:条目类别与 provider 类别分为两层

**触发**:A₀ 第 3 段停止报告 SCAN-01(stage14 `progress.md` §19.2)。§1.1b 的封闭 artifact universe 只列了三种 Python provider,
而 12b-1/12b-3b/12b-3c 要求完整 git tree 的每一个条目都有类别、都有 detector 判 `SCANNED`;配置、CI、文档、二进制等条目在正文中没有类别。

**E4-1 · 两层分类**
> **第一层:条目类别(entry kind)** —— `scan_manifest` 的每个条目都有且仅有一个,由下表**按顺序**机械判定(先命中者为准);
> **第二层:provider 类别** —— 只对第一层判为 `PY_SOURCE` 或 `IMPORTABLE_BINARY` 的条目求值,仍是 §1.1b 的封闭 universe
> (纯 `.py` 源文件、包目录、命名空间包 portion;其余 → `UNSUPPORTED` 阻塞)。
> §1.1b"其余一律 `UNSUPPORTED`"只约束第二层;**非 provider 条目不是"其余",它们由第一层承接**。
> 12b-3c 的"注册表键 ⊇ 封闭 universe 全部 kind"按两层分别适用:第一层的键 = 下表全部类别,第二层的键 = §1.1b 三种 provider。

**E4-2 · 条目类别(封闭,按序判定;第一条不命中再看下一条)**
> | # | 条目类别 | 机械判据 | required detectors |
> |---|---|---|---|
> | 1 | `GITLINK` | git mode `160000` | 解析层(按"打包入口与文件系统层重定向"落 `DYNAMIC_UNRESOLVED`) |
> | 2 | `SYMLINK` | git mode `120000` | 解析层(同上) |
> | 3 | `IMPORTABLE_BINARY` | 扩展名 ∈ {`.so`, `.pyd`, `.pyc`, `.pyo`} | provider 分类器(按 §1.1b 落 `UNSUPPORTED` 阻塞) |
> | 4 | `PTH` | 扩展名 `.pth` | 解析层(`DYNAMIC_UNRESOLVED`)、名字命中兜底 |
> | 5 | `BINARY` | 内容含 NUL 字节或不能按 UTF-8 解码 | 二进制记录器(逐个记入 B-8,§1.1 名字命中兜底的"二进制文件跳过并逐个记入") |
> | 6 | `PY_SOURCE` | 扩展名 `.py`,或首行 shebang 指向 python 解释器 | provider 分类器、四级粒度候选扫描、消费者参与点识别(C1–C6d、C8a、C8b)、解析层、名字命中兜底 |
> | 7 | `PACKAGING` | 文件名 ∈ {`pyproject.toml`, `setup.cfg`} | C7a 识别、解释器行兜底、名字命中兜底 |
> | 8 | `CI_CONFIG` | 路径匹配 `.github/workflows/*.yml`、`.github/workflows/*.yaml`、`.gitlab-ci.yml`、`Jenkinsfile`、`.travis.yml` | C7b 识别、解释器行兜底、名字命中兜底 |
> | 9 | `SHELL` | 扩展名 `.sh`,或首行 shebang 指向 sh/bash | C7c 识别、解释器行兜底、名字命中兜底 |
> | 10 | `BUILD` | 文件名或模式 ∈ C7d 所列 {`Makefile`, `GNUmakefile`, `*.mk`, `*.spec`, `Dockerfile`, `*.service`, `tox.ini`} | C7d 识别、解释器行兜底、名字命中兜底 |
> | 11 | `DOC` | 按 §1.1 名字命中兜底中"文档文件"的定义(`*.md`、`*.rst`,以及 `docs/` 下不属第 7–10 类、无可执行位且无 shebang 的文件) | doctest 提取器、名字命中兜底(非 doctest 行按第 9 类排除并记账) |
> | 12 | `OTHER_TEXT` | 以上都不是的文本文件(如 `.json`、非 CI 的 `.yml`、`.txt`、`.ini`、`.importlinter`、无扩展名的文本文件) | 解释器行兜底、名字命中兜底(按 §1.1:未登记类别中的解释器行 → `UNKNOWN_CAPABILITY`) |
> 第 12 类是**有内容规则的封闭类别**,不是"默认豁免":它的条目同样逐条扫描、逐条记账,名字命中或解释器行一律按 §1.1 处理。
> **分类器必须全函数**:git mode 不属 {`100644`, `100755`, `120000`, `160000`} 的条目 → `UNKNOWN_PROVIDER_KIND` 阻塞(沿用 12b-3c③)。
> 12b-3b"每个条目 ∃ detector 判 `SCANNED`":上表每类的 required detectors 至少一个对该条目判 `SCANNED`;
> 二进制记录器对 `BINARY` 条目完成记录即为 `SCANNED`。

**E4-3 · 与其它条款的关系**
> 本勘误不新增消费者形态(`consumer.*` 仍为原子形态表二十个)、不减少任何条目、不改变 §1.1 的去处规则;
> 它只给每个条目一个机械可判的类别和对应的 detector 集合。条目类别与 provider 类别的判定结果逐条落 B-8。

**生效范围**:12b-1、12b-3、12b-3b、12b-3c 的实现与 §1.1b 封闭 universe 的适用面;不改变判定条件与其它事项。

### 勘误 5(2026-10-07,FatTank 批准)—— 模块身份按打包上下文区分:同一点分名在 live 与 release 快照中各有一份

**触发**:A₀ 第 3 段停止报告 SCAN-02(stage14 `progress.md` §20.2):全树中有两份打包描述(根 `pyproject.toml`、
`release-v1.4.0/pyproject.toml`),按各自声明的源码根导出的点分名有 85 个重名(例:`ci_triage.quickbuild` 在 live 是 shim,
在快照是独立实现),而快照内的绝对 import 只写了点分名。正文的消费者识别与名字命中兜底只按点分名对应,无法确定指向哪一份。

**E5-1 · 打包上下文与模块身份**
> **打包上下文**:受版本控制的每一份 `pyproject.toml` 或 `setup.cfg` 定义一个上下文,其范围是该文件所在目录及其子目录,
> 但不含更深一层另有打包描述的子目录(本树据此有两个:`release-v1.4.0/` 为 release 上下文,其余全部为 live 上下文)。
> 每个条目恰属一个上下文(按路径机械判定)。
> **模块身份 = (上下文, 点分名)**:点分名只按**该上下文自己的打包描述**(`[tool.setuptools.packages.find]` 的 `where`/`include`/`exclude`)
> 从文件路径导出;不在其声明源码根下的文件没有点分名,只有路径形态。
> 同一上下文内同一点分名对应多个文件 → `MODULE_IDENTITY_AMBIGUOUS` 阻塞(逐例记入 B-8)。

**E5-2 · 引用按"本上下文"解析**
> 一个条目中的点分名引用(原子形态表的各种 import/patch/argv 形态,以及名字命中兜底的点分名、拆分导入两种名字形态),
> **优先解析到该条目所属上下文中的同名模块**;本上下文没有该名字时,**朝闭回退**:恰有一个其它上下文定义该名字 → 指向该模块,
> 记为"跨上下文回退边"并产生消费边;有多个其它上下文定义该名字 → `MODULE_IDENTITY_AMBIGUOUS` 阻塞;没有任何上下文定义 → 非候选名字,不产生消费边。
> 每条回退边与非候选名字逐条记入 B-8。(回退产生消费边只会让候选更难被删,不会让被引用的模块被误删。)
> **路径形态**(源文件路径、包目录路径)由路径本身唯一确定所指文件,可跨上下文产生消费边。
> 由此,release 快照内 `from ci_triage.quickbuild import …` 指向 release 上下文自己的 `ci_triage/quickbuild.py`,
> 不是 live shim 的消费者;live 上下文中对同一点分名的引用则指向 live shim。

**E5-3 · release 上下文中的候选**
> 本批的兼容位置清理只针对 live 上下文。扫描在 release 上下文中发现的候选照常进入 reconciliation 与 admission,
> admission 以"该模块身份属于 release 上下文(冻结的历史发布快照,不是本批的兼容位置)"为证据裁为 `REJECTED_NOT_SHIM`,
> 证据含上下文判定依据(所属打包描述的路径与 hash)。**release 上下文的条目不做任何删除或修改**,也不从 manifest 与扫描中排除。

**E5-4 · 控制**
> 至少五条,登记进 `control_catalog.json`:①release 内对重名点分名的绝对 import → 指向 release 自己的文件,不成为 live 候选的消费边;①′release 内对只有 live 才有的点分名的引用 → 跨上下文回退边,成为 live 模块的消费边;
> ②live 内对同一点分名的 import → 指向 live 文件;③live 文件中以**路径形态**引用 release 文件 → 产生跨上下文消费边;
> ④同一上下文内构造两个文件导出同一点分名 → `MODULE_IDENTITY_AMBIGUOUS` 阻塞。

**生效范围**:§1.1 消费者识别与名字命中兜底的引用解析、候选的模块身份、§1.1c admission 证据;不改变判定条件与其它事项。

### 勘误 6(2026-10-07,FatTank 批准)—— 勘误 4 引入的条目级检查在 capability 注册表中的位置与对账

**触发**:A₀ 第 3 段停止报告 SCAN-03(stage14 `progress.md` §21.3)。勘误 4 的 required detectors 中,二进制记录器、名字命中兜底、
解释器行兜底、doctest 提取器四项既不是 §1.1 原子形态(不属 `consumer.*`),也不在 §1.1b 九类表中(不属 `ledger/scan/resolve/provider`);
12b-3c④ 要求注册表与 detector capability 双向精确覆盖,12b-12 要求非 consumer 分支四方精确相等 —— 这四项无处登记。

**E6-1 · 新增命名空间 `entry.*`(封闭)**
> capability registry 的命名空间由五个扩为六个:`consumer.*`、`ledger.*`、`scan.*`、`resolve.*`、`provider.*`、**`entry.*`**;
> 前缀不在其中即红(替代 §1.1 原子形态表说明中"恰属这五个命名空间之一"的表述)。
> `entry.*` 的分支封闭为四个,**扩充走勘误流程**:
> | 分支 | 承担方 detector | 作用 |
> |---|---|---|
> | `entry.binary_record` | 二进制记录器 | 对 `BINARY` 条目逐个记录(路径、mode、blob hash)并判 `SCANNED` |
> | `entry.name_backstop` | 名字命中兜底 | §1.1 名字命中兜底 |
> | `entry.interpreter_line` | 解释器行兜底 | §1.1 解释器行兜底(含命令切分、选项文法、代码来源四类) |
> | `entry.doctest_extract` | doctest 提取器 | 从 docstring 与文档文件提取 doctest 行,交给 Python 源规则 |

**E6-2 · 勘误 4 表中 required detectors 与分支的对应**
> 勘误 4 E4-2 表的 required detectors 一律按下列方式落到分支,不得另立:
> "解析层" → `resolve.*`;"provider 分类器" → `provider.unsupported`(其承担方即 provider 分类器,判支持或不支持);
> "四级粒度候选扫描" → `scan.module`/`scan.reexport`/`scan.inline`/`scan.proxy_callable`;
> "消费者参与点识别"与"C7a–C7d 识别" → 对应的 `consumer.*` 原子形态分支;
> "二进制记录器""名字命中兜底""解释器行兜底""doctest 提取器" → E6-1 的四个 `entry.*` 分支。

**E6-3 · 对账分工**
> - `consumer.*`:仍由 `SEAL-16b` 五方覆盖对账(不变);
> - `ledger.*`/`scan.*`/`resolve.*`/`provider.*`:仍由 12b-12 四方对账(不变;投影不含 `consumer.*` 与 `entry.*`);
> - **`entry.*`:新增三方双向精确覆盖** —— ①勘误 4 E4-2 表经 E6-2 落出的 `entry.*` 分支集合;②capability registry 中 `entry.*` 分支及其承担方;
>   ③正控制目录中 `entry.*` 分支的控制 —— 两两差集为空,否则红;
> - 12b-3c④"注册表与 detector capability 双向精确覆盖"按上述三组对账的并集判定,三组任一不空即红。
> 由此 `BINARY` 条目的行级下界(12b-3b)由 `entry.binary_record` 承担,不被豁免。

**E6-4 · 控制**(登记进 `control_catalog.json`,与其它控制分开计数)
> 每个 `entry.*` 分支至少一条正控制与一条 near-miss:
> `entry.binary_record` 正:一个 `.gz` 文件被记录并判 `SCANNED`;near-miss:一个纯文本文件不被路由到二进制记录器;
> `entry.name_backstop`、`entry.interpreter_line`、`entry.doctest_extract`:取 §1.1 原子形态表末段已列的对应正控制与 near-miss,改登记到相应 `entry.*` 分支下;
> 另加一条对账控制:从 registry 删去 `entry.binary_record` → 三方对账必红。

**生效范围**:capability registry 的命名空间、12b-3c④、12b-12 投影与新增的 `entry.*` 三方对账;不新增消费者形态,不改变判定条件与其它事项。

### 勘误 7(2026-10-07,FatTank 批准)—— 内建 `exec`/`eval`/`compile` 的承接

**触发**:A₀ 第 3 段停止报告 SCAN-04(stage14 `progress.md` §22.2):固定树 `check_design_doc.py` 中调用内建 `compile(...)`,
它在 §1.1"受监控名字集合"(导入机制一类的内建 {`__import__`, `exec`, `eval`, `compile`})中,却没有任何原子形态承接,按规则只能阻塞并扩表。
同一集合中的 `exec`、`eval` 同样没有形态承接。

**E7-1 · `compile` 移出受监控名字集合**
> `compile` 只把源码编译成代码对象,本身不加载任何模块;代码对象只有经 `exec`/`eval` 执行才产生导入效果,而后两者仍受监控。
> 故 §1.1 受监控名字集合中的内建集合改为 {`__import__`, `exec`, `eval`};对 `compile` 的调用与读取不是参与点。

**E7-2 · 新增原子形态 `C9`(分支 `consumer.C9`,所属类 5)**
> | 形态 ID | 所属类 | 识别谓词(互斥) |
> |---|---|---|
> | `C9` | 5 | 调用内建 {`exec`, `eval`}。首参为字符串常量(含相邻字面量拼接)→ 按 §1.1"嵌入式 Python 片段"作为 Python 源解析并套用全部规则;首参不是字符串常量(含代码对象、变量、表达式)→ `DYNAMIC_UNRESOLVED`,形态仍记 `C9` |
> 原子形态由二十个增为二十一个;`SEAL-16b` 五方对账、`12b-10` 逐形态正控制按新表执行。
> **正控制**:`exec("import <sentinel>")` → 产生消费边;`exec(code_var)` → `DYNAMIC_UNRESOLVED`;
> **near-miss**:`compile(src, "<x>", "exec")` 单独出现 → 不是参与点、不阻塞;`compile` 的结果再传给 `exec` → 由 `exec` 处落 `C9` 的 `DYNAMIC_UNRESOLVED`。
> **已冻结判定条件的影响**:`OBS-7.falsification-samples` 第 3 条的形态取值清单按冻结时的二十个形态书写;若真实样本中出现 `C9`,该 claim 将判红并停止报告,
> 届时按判定条件的勘误流程处理,本勘误不预改已冻结的判定条件。

**E7-3 · 批量处理要求**
> 为避免同类阻塞逐个出现,实现方在全树范围完成一次受监控名字预检:**收集全部零命中与多命中参与点后一次性停止报告**,
> 逐条列出(文件、位置、被调限定名、为何零命中或多命中),不得发现第一处即停。

**生效范围**:§1.1 受监控名字集合与原子形态表;不改变判定条件与其它事项。

### 勘误 8(2026-10-07,FatTank 批准)—— 进程启动函数被当作值传递、以及加载器执行模块的承接

**触发**:A₀ 第 3 段按勘误 7 E7-3 完成全树预检后停止报告 SCAN-05(stage14 `a0-evidence/part3/erratum7/blockers.md`),零命中 27 处、多命中 0 处,分两类:
①25 处对 `subprocess.run`/`subprocess.Popen` 的**非调用读取**(参数默认值 `subprocess_runner: SubprocessRunner = subprocess.run`、
调用实参 `subprocess_runner=subprocess.run`、赋值 `real_run = subprocess.run`、类型标注 `subprocess.Popen[str]`);正文 ②′ 只规定裸读取是参与点,没有形态承接。
②2 处 `spec.loader.exec_module(module)`(被调者解析为 `importlib.machinery.SourceFileLoader.exec_module`),在受监控集合内、不在任何形态的被调者封闭集合中。
第①类不能简单放行:这些读取把真实的进程启动函数注入下游函数(如 `analyzer_runner.py` 经 `subprocess_runner(command, ...)` 启动 Python 分析器),
下游经别名发起的调用此前不是参与点,若不承接即为朝开漏洞。

**E8-1 · 类型标注中的读取不是参与点**
> 出现在类型标注位置(函数形参标注、返回值标注、`AnnAssign` 的标注)中的受监控名字读取(`Name`/`Attribute`/`Subscript` 的取值部分)不是参与点;
> 标注位置中的**调用**仍按正文 ② 处理。本条对受监控名字集合全体适用。

**E8-2 · 新增原子形态 `C8c`(分支 `consumer.C8c`,所属类 8):进程启动函数的别名**
> | 形态 ID | 所属类 | 识别谓词(互斥) |
> |---|---|---|
> | `C8c` | 8 | 对**进程启动族**(见 `C8a`)中任一名字的非调用读取(标注位置除外,见 E8-1)。本身不产生消费边;按下述"别名绑定"规则处理其去向 |
> **别名绑定**(封闭四种去向,其余一律 `DYNAMIC_UNRESOLVED`,形态仍记 `C8c`):
> > (a)作为赋值右侧整体绑定到一个**普通名字** `n`(`n = subprocess.run`)→ 绑定 (所在作用域, `n`);
> > (b)作为函数 `F` 某个**具名形参** `p` 的默认值 → 绑定 (`F`, `p`);
> > (c)作为调用实参(位置或关键字),且被调者经 import binding **静态解析到扫描集合内的某个 `def`**,实参按签名绑定到其**具名形参** `p` → 绑定 (该 `def`, `p`);
> > (d)其它一切去向 —— 存入属性或容器、作为返回值、绑定到 `*args`/`**kwargs`、被调者不能静态解析、经 `lambda` 默认值或解包传递等 → `DYNAMIC_UNRESOLVED`。
> **经别名的调用(正文参与点新增 ②″)**:对每个绑定 (作用域 `S`, 名字 `n`),`S` 内(含未重新绑定 `n` 的嵌套函数与 `lambda`)
> **每个以裸名 `n` 为被调者的调用**都是一个参与点,按被别名的函数的签名族取命令载荷,再按 `C8a`/`C8b` 的既有谓词落形态(并记录来源 `C8c` 点);
> 一个绑定若经不同读取别名了**载荷位置不同**的函数(如同时收到 `subprocess.run` 与 `os.system`)→ 经该绑定的调用一律 `DYNAMIC_UNRESOLVED`。
> **不按控制流区分**:`S` 内 `n` 即使在某些路径上被重新赋值、或调用方传入的是测试替身,同名调用仍一律按启动调用处理(宁多勿漏,朝闭)。
> **向下传递**:`S` 内对 `n` 的非调用读取按上面 (a)–(d) 继续绑定;对 `n` 的其它使用(属性访问 `n.x`、存入属性或容器、作为返回值)→ `DYNAMIC_UNRESOLVED`。
> 绑定集合按不动点求出,有限必收敛;不动点结果写入证据,逐条列出 (绑定、来源读取、经该绑定的调用点)。
> **范围**:本形态**只**承接进程启动族的读取;导入机制与打桩类名字的裸读取(如 `f = importlib.import_module`)仍按正文为零命中 → `UNKNOWN_CAPABILITY`,
> 正文该条正控制不变。

**E8-3 · 新增原子形态 `C5f`(分支 `consumer.C5f`,所属类 5):加载器执行模块**
> | 形态 ID | 所属类 | 识别谓词(互斥) |
> |---|---|---|
> | `C5f` | 5 | 调用解析为 `importlib` 下任一加载器类的 {`exec_module`, `load_module`} 方法。接收者为 `<s>.loader`,且 `s` 在同一词法作用域内**唯一一次**由某个 `C5d` 调用(`spec_from_file_location`/`spec_from_loader`/`find_spec`)赋值 → 关联到该 `C5d` 参与点,本身不另产生消费边(加载目标的消费边由该 `C5d` 点按既有规则产生);接收者其它来源(形参、属性、多次赋值、无法确定)→ `DYNAMIC_UNRESOLVED`,形态仍记 `C5f` |
> 被调者封闭集合为上表两个方法名,扩充走勘误流程;加载器类的构造调用(如 `importlib.machinery.SourceFileLoader(...)`)不在本形态内,出现时仍按正文为零命中。

**E8-4 · 计数与对账**
> 原子形态由二十一个增为二十三个(新增 `C8c`、`C5f`);`SEAL-16b` 五方对账、`12b-10` 逐形态正控制、B-11 `MECH_FIVE_WAY` 按新表执行。
> 勘误 4 E4-2 表中 `PY_SOURCE` 的"消费者参与点识别"按 E6-2 落到全部 Python 源 `consumer.*` 分支,即含 `C9`、`C8c`、`C5f`。

**E8-5 · 控制**(登记进 `control_catalog.json`)
> **`C8c` 正控制**:`def f(*, runner=subprocess.run): runner([sys.executable, "-m", "<sentinel>"])` → 读取落 `C8c`,调用落 `C8a` 并产生消费边;
> 下传:`def g(r): r([sys.executable, "-m", "<sentinel>"])` 且 `def f(runner=subprocess.run): g(runner)` → 须产生消费边;
> 跨模块关键字实参:测试文件中 `mod.f(runner=subprocess.run)`,`mod.f` 的形参 `runner` 被调用启动 `<sentinel>` → 须产生消费边;
> 嵌套函数:`real_run = subprocess.run` 后在内层函数中 `real_run(["python", "-m", "<sentinel>"])` → 须产生消费边;
> 逃逸:`self._run = subprocess.run`、`return subprocess.run`、`h(*[subprocess.run])` → 各须 `DYNAMIC_UNRESOLVED`。
> **`C8c` near-miss**:`def f(p: subprocess.Popen[str]): ...` → 不是参与点、不阻塞;`f = importlib.import_module` → 仍须 `UNKNOWN_CAPABILITY`。
> **`C5f` 正控制**:`spec = importlib.util.spec_from_file_location("n", "<sentinel>.py")`、`m = importlib.util.module_from_spec(spec)`、`spec.loader.exec_module(m)`
> → `C5f` 关联到该 `C5d` 点,消费边经 `C5d` 产生;`def load(loader, m): loader.exec_module(m)` → 须 `DYNAMIC_UNRESOLVED`。
> **`C5f` near-miss**:`importlib.machinery.SourceFileLoader("n", p)` 构造调用 → 仍须 `UNKNOWN_CAPABILITY`(不被 `C5f` 吞掉)。

**已冻结判定条件的影响**:与勘误 7 相同 —— `OBS-7.falsification-samples` 第 3 条的形态取值清单按冻结时书写;若真实样本中出现 `C8c` 或 `C5f`,
该 claim 判红并停止报告,届时按判定条件的勘误流程处理,本勘误不预改已冻结的判定条件。

**E8-6 · 批量处理要求**:沿用 E7-3 —— 按本勘误重跑全树预检(含 ②″ 新增的经别名调用点),收集全部零命中与多命中后一次性停止报告;
另报告本勘误新增的 `DYNAMIC_UNRESOLVED` 条数(按 `C8c` 逃逸、经别名调用的载荷不可规范化、`C5f` 三类分列),供后续销账排期。

**生效范围**:§1.1 参与点(新增 ②″、标注位置除外)与原子形态表;不改变判定条件与其它事项。

### 勘误 9(2026-10-07,FatTank 批准)—— import-linter 配置 `.importlinter` 的承接,以及非 Python 条目的一次性全量预检

**触发**:A₀ 第 3 段停止报告 SCAN-06(stage14 `progress.md` §24.3,`a0-evidence/part3/erratum8/blockers.md`):
包 `tizen_convergence_judge` 的 re-export binding `check_convergence` 是粒度②候选,其模块名在 `.importlinter` 第 8/22/32/57 行命中;
`.importlinter` 按勘误 4 属 `OTHER_TEXT`,命中处不是解释器命令、不是文档,按 §1.1 只能 `UNKNOWN_CAPABILITY`。
该文件由 CI(`.github/workflows/ci.yml` 的 `lint-imports`)经 import-linter 读取:其中列出的模块被删除,或 `ignore_imports` 所列的导入消失
(本文件设 `unmatched_ignore_imports_alerting = error`),CI 门禁即失败。故它是**真实消费者**,不能排除,须补形态。
另:SCAN-06 是单见证停止,非 Python 条目的名字兜底尚未全量跑过 —— E9-5 要求一次性跑完。

**E9-1 · 新增条目类别 `IMPORT_LINTER`(勘误 4 E4-2 表第 10a 类)**
> | # | 条目类别 | 机械判据 | required detectors |
> |---|---|---|---|
> | 10a | `IMPORT_LINTER` | 文件名为 `.importlinter` | C7e 识别、解释器行兜底、名字命中兜底 |
> 判定顺序位于第 10 类 `BUILD` 之后、第 11 类 `DOC` 之前(故 `docs/` 下的 `.importlinter` 也归本类,不按文档排除)。条目类别由十二个增为十三个;
> 12b-3c 第一层的键集合按新表执行。`setup.cfg` 的 `[importlinter*]` 节与 `pyproject.toml` 的 `[tool.importlinter*]` 表**不在本勘误范围**,
> 出现时其中的名字命中仍按 §1.1 为 `UNKNOWN_CAPABILITY`。

**E9-2 · 新增原子形态 `C7e`(分支 `consumer.C7e`,所属类 7)**
> | 形态 ID | 所属类 | 识别谓词(互斥) |
> |---|---|---|
> | `C7e` | 7 | 非 Python 文件:`IMPORT_LINTER` 条目中,下述"模块位"上的每个模块名 token |
> **解析**:按 INI 语法(import-linter 读取该文件的方式)解析;只认节 `[importlinter]` 与 `[importlinter:contract:<id>]`。
> **模块位(封闭键集合)**:`[importlinter]` 节的 `root_package`、`root_packages`;contract 节的 `layers`、`containers`、`modules`、
> `source_modules`、`forbidden_modules`、`ignore_imports`。多行值逐行取;`layers` 每行按 `|` 与 `:` 切分为同层兄弟,去掉可选层的外层括号;
> `ignore_imports` 每行按 `->` 切分为两侧,两侧各是一个 token。**每个 token 一个参与点**。
> **名字解析**:模块名在 `.importlinter` 所在目录所属的打包上下文中解析(勘误 5;仓库根下即 live 上下文);
> contract 节带 `containers` 时,其 `layers` 中的 token 相对于每个 container 解析(`<container>.<token>`,每个 container 各一条边)。
> token 含通配符 `*` 或 `**` → `DYNAMIC_UNRESOLVED`,形态仍记 `C7e`。
> **消费边含义**:指向所解析的**模块本身**(删除它会使 `lint-imports` 失败);`ignore_imports` 两侧各产生一条。
> 这条边**不消费该模块内的任何 binding**:对 binding 级候选,模块名命中在此处按 `C7e` 计(已被参与点分类),不产生 binding 边。
> **非模块位的命中**:
> > 整行注释(首个非空白字符为 `#` 或 `;`)→ 不是参与点;其中的名字命中按第 9 类排除并记入 B-8;其中出现的解释器 token **不构成解释器行**;
> > `name` 键的值(contract 的显示名)中的命中 → 按第 9 类排除并记入 B-8;
> > 其它键、其它节、以及无法按 INI 解析的行中的命中 → `UNKNOWN_CAPABILITY`。
> 互斥性:`C7e` 只取 `IMPORT_LINTER` 条目,与 `C7a`–`C7d` 按条目类别分割。

**E9-3 · 计数与对账**
> 原子形态由二十三个增为二十四个(新增 `C7e`);`SEAL-16b` 五方对账、`12b-10` 逐形态正控制、B-11 `MECH_FIVE_WAY` 按新表执行。
> 勘误 6 E6-2:"C7e 识别"落到 `consumer.C7e`。`entry.*` 不变。

**E9-4 · 控制**(登记进 `control_catalog.json`)
> **正控制**:`.importlinter` 中 `root_packages = <sentinel>` → 产生到 `<sentinel>` 的消费边;`layers` 行 `a | <sentinel>` → 产生到 `<sentinel>` 的边;
> `containers = pkg` 且 `layers` 行 `<leaf>` → 产生到 `pkg.<leaf>` 的边;`ignore_imports = x.y -> <sentinel>.z` → 产生到 `x.y` 与 `<sentinel>.z` 两条边;
> `modules` 行 `<sentinel>.*` → `DYNAMIC_UNRESOLVED`;条目类别:根目录 `.importlinter` 与 `docs/.importlinter` 均判 `IMPORT_LINTER`。
> **near-miss**:注释行 `# python -m <sentinel>` → 不是参与点、不是解释器行,按第 9 类记账;`name = ... <sentinel> ...` → 按第 9 类记账;
> 未知键 `foo = <sentinel>` → 须 `UNKNOWN_CAPABILITY`;某 binding 级候选所在模块名在 `modules` 中命中 → 只产生模块边,该 binding 候选不因此被判为已消费。

**已冻结判定条件的影响**:与勘误 7、8 相同 —— 若 `OBS-7.falsification-samples` 真实样本中出现 `C7e`,该 claim 判红并停止报告,本勘误不预改已冻结的判定条件。

**E9-5 · 非 Python 条目一次性全量预检**(同 E7-3 的做法,扩到非 Python 条目)
> 以 §1.1c 四级粒度产出的**全部** candidate 生成名字形态,对 `scan_manifest` 中全部非 `PY_SOURCE` 文本条目
> (`PTH`、`PACKAGING`、`CI_CONFIG`、`SHELL`、`BUILD`、`IMPORT_LINTER`、`DOC`、`OTHER_TEXT`)跑名字命中兜底与解释器行兜底,
> **收集全部 `UNKNOWN_CAPABILITY` 与多去处命中后一次性停止报告**,不得发现第一处即停。
> 报告按条目类别分组,逐文件列出命中数、名字形态、所涉 candidate 与代表行;另报本勘误新增的 `DYNAMIC_UNRESOLVED` 条数。
> 若 candidate 全集在此时尚不能完整产出,如实写明缺什么,不得以部分 candidate 的结果声称全量。

**生效范围**:勘误 4 条目类别表、§1.1 原子形态表与非 Python 文件的名字兜底去处;不改变判定条件与其它事项。
