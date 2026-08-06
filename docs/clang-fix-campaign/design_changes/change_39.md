# change_39:checker 两规则可执行化(→ v1.5.15-FROZEN)【v3】

**触发**:Codex P0 审计停止-报告(协议 2 正常工作,零代码改动)。
**v3 修订记录(2026-08-04,评审 2 MAJOR + 2 MINOR + 1 NIT 全采)**:
①prompt P0-2 checker 口径同步至本 change v2 裁决(v2 升版时仅替换
版本引用、漏同步 P0-2 正文——"prompt 落后主裁决"的漂移形态在
修订流程自身复发);②唯一权威落点闭合:无版本旧 prompt **与
v1_5_14 prompt 均入 history/**,根目录仅留 v1_5_15,头部声明两份
归档;③fixture 文案消歧:"任意**非空**子集 → PASS"+ 新增
"空集 → FAIL" fixture;④措辞更正:"**当前权威版本绑定引用**升
v1.5.15;**历史来源引用**(如 'v1.5.14 起/立')保留原版本号——
历史 provenance 不随权威版本漂移";⑤prompt 内下一变更编号改
`change_40+`;fixture 基数按实况更正为 22,自测输出以合并实跑
`N/N` 为准。
**v2 修订记录(2026-08-04,评审 3 MAJOR + 1 MINOR 全采)**:v1 的
两条正则未按 D⑥ 对实物试跑即冻结——多行签名漏检
(`multiline_signature_matched=False`)、`IF NOT EXISTS` 未处理
(六索引全提成 `IF`),均由评审实测抓出并已按修正式对冻结版复跑
全绿(六索引精确、多行签名命中、62 处裸签名待转换);另修 prompt
版本权威冲突与移动/快照记账。**立规文档自己违反了自己刚立的⑥**,
记入 D 节。
**性质**:CK-API-01/CK-IDX-01 的冻结定义不可按原文执行;本 change
仅改**校验规则定义与文档形态**,**零契约语义变更**。应用后
design.md 版本升 **v1.5.15-FROZEN**(Frozen 协议下的 R1 修订)。

---

## A. CK-API-01:§4.2 重写为真实 Python skeleton(采 Codex 推荐项)

**问题实锤**:§4.2 为接口伪语法(`模块.函数(*, ...) -> str`),
`ast.parse` 直接 SyntaxError。**不采伪语法转换器备选项**——转换器
会掩盖签名错误(B4 的重复形参必须被裸解析抓住,这是本规则的
立规事故)。

**裁决**:
1. §4.2 全部接口块改为 ```python 围栏内的真实 skeleton:
   `def 函数名(参数表) -> 返回类型: ...`(去模块前缀,模块归属以
   紧邻注释行 `# module: campaign_state` 标注);dataclass 块本就是
   合法 Python,仅补围栏标签;既有 `#` 注释原样保留在块内。
2. **参数省略一律展开**(`(*, ...)` 形态是实现输入文档的规格缺口,
   借本次清除):P4.5 新 API 的参数表**逐字取自冻结文本**;早期
   阶段既有 API(如 `build_campaign_unit_key`)从**现行代码转录**,
   块内首行注释标注 `# 签名权威=代码(P<n> 既有);此处为快照`。
3. 规则定义(替换 §7.13 7g 对应句):**CK-API-01 = design.md 内
   每个 ```python 围栏块 `ast.parse` 必须通过**;并在**排除全部
   fence 后的裸文本**上扫描签名**起始**行:
   `^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\(`
   ——命中即 FAIL(v2:v1 的 `^\S+\.\w+\(.*\)\s*->` 要求同行
   闭合,漏掉全部多行签名;起始式不要求同行 `)->`,已对实物验证
   命中 62 处现存裸签名,转换完成后应归零)。
4. Fixture(至少三个):①重复形参块 → FAIL(复刻 B4);
   ②单行裸签名未入围栏 → FAIL;③**真实多行裸签名**(取自
   转换前的 `build_campaign_unit_key` 原文)→ FAIL(v2:锁死
   多行漏检不复发)。
5. **抄录漂移护栏**:Codex 交付**逐签名新旧对照表**(旧伪语法行 →
   新 skeleton 行)入提交报告,供人工/Claude 抽审;冻结文本已有
   参数表逐字保留;任何参数名/顺序/默认值/返回类型的改动 = 语义
   变更 = 违规,须停止报告。

## B. CK-IDX-01:方向收窄为子集 + 权威文件唯一化(偏离推荐项)

**不采"两份 prompt 各补齐六条 CREATE INDEX"**——prompt 复述 DDL
即重造双权威(change_37 丙-B1 刚冻结"主文唯一契约权威";prompt
的 DDL 章节写的是"§3.4 逐字实现"引用式,这是有意为之)。

**裁决**:
1. 旧 `p45-implementation-prompt.md` **移入
   `docs/clang-fix-campaign/history/`**(已 Git 跟踪则 `git mv`;
   当前未跟踪则普通移动后精确 `git add`——v2 修正:campaign 文档
   现未被跟踪,盲用 git mv 会失败);权威实现输入**重命名并升版**为
   `p45-implementation-prompt-v1_5_15.md`(v2,MAJOR-1:权威 prompt
   版本必须与冻结设计同步;v3 措辞更正:**当前权威版本绑定引用**
   升 v1.5.15,**历史来源引用**('v1.5.14 起/立'类)保留原号——
   provenance 不漂移;**仅版本引用与 checker 规则说明,零 P4.5
   运行时语义改动**),头部加权威声明行(修订版文件已随本 change
   交付)。**v3 唯一权威落点闭合**:`p45-implementation-prompt.md`
   与 `p45-implementation-prompt-v1_5_14.md` **两份均入 history/**
   (目标机 v1_5_14 已落盘,同样归档),根目录仅留 v1_5_15;
   CK-IDX-01 仅扫描根目录权威件。
2. 规则定义(替换 §7.13 7g 对应句):**CK-IDX-01 = 权威 prompt 中
   全部索引名形态 token(regex `\b[iu]x_[a-z0-9_]+\b`)必须 ⊆
   design.md 索引名集合,且 prompt token 集合**非空**(v2:防
   索引护栏整段被删后的空集假绿)**;design 侧提取式冻结为
   (v2:v1 未处理 `IF NOT EXISTS`,实测六索引全提成 `IF`):
   `CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)`
   (已对冻结版实测:恰得六名)。history/ 目录不扫描。立规事故
   (旧名 `ux_convergence_once` 残留)恰为子集违例;集合相等系
   过度规格。
3. Fixture(至少三个,v3 消歧):①prompt 样本含
   `ux_convergence_once` → FAIL;②prompt 样本含 design 六索引的
   任意**非空**子集 → PASS;③prompt 样本索引 token 集合为**空**
   → FAIL(护栏整段被删的假绿)。

## C. 应用与验收

1. Codex 按 A/B 修改 design.md(版本行升 v1.5.15-FROZEN、状态行
   追加 change_39 记录)、checker、prompt 升版、文件移动;
   随后生成 `history/clang-fix-campaign-design-v1.5.15-FROZEN.md`
   快照并**断言与 design.md 逐字节一致**(`cmp` 输出入报告——v2,
   MINOR:冻结记账闭环);
2. 验收:`ast.parse` 全 python 围栏通过;checker 自测(含 A4/B3
   新 fixtures)全绿;`ruff check` 干净;对 design.md 跑 checker
   `OK: 0 problem`;逐签名对照表随报告提交;
3. **本 change 不改任何运行时契约**——§3.4/§4.1 的语义、DDL、
   分支表、DoD 一字不动;若重写过程中发现签名与正文叙述矛盾,
   停止并报告(候选 change_40),禁止顺手修正。
4. 验收通过后 P0 继续(P0-1 change_31 回写、P0-3 Ruff 项与本
   change 的 checker 工作合并执行),随后进入 P1。

## D. 方法论记账

**⑥规则冻结前先对真实输入试跑**:CK-API-01/IDX-01 在 change_32
立规时只写了意图、没对 design.md 实物跑过一次——checker 规则也是
代码,同样适用"实测验证不脑补"。今后新增 checker 规则的 change
必须附对当前文档的试跑输出(预期 PASS 或列明待修清单)。
**⑥的首个违例是 change_39 v1 自己**:立规同一文档内的两条正则
未试跑即冻结,双双在评审实测中碎裂——"必须附试跑输出"自本 v2
起为 change 文档的**硬格式要求**,无试跑输出的规则类 change 一律
退回。

---

## 落盘校验附记(v3.2,2026-08-04)

**v3.2 修订(评审 1 MAJOR + 1 MINOR 全采)**:①SHA 闸门写入 prompt
P0 验证输出第⑤项(断言指令入文、SHA 值留本附记外部维护,规避
自指;⑤先于其余项执行,不符即停);②prompt 内 change_39 版本标签
统一为**不带子版本**引用(以最新修订为准,防标签随修订漂移);
SHA 已按修改后文件重算并更新下值。
(v3.1 原文如下)

本轮评审(BLOCKER-1/MAJOR-2/MINOR-3)所引行号与 **v2 期交付件**吻合,
三处在 v3 交付件中均已修复(核验输出见会话记录:P0-2 新口径全文、
change_40+ 在位、双归档头在位、旧口径 grep 计数 0)——**属落盘断层,
非内容缺口**:目标机落的是 v2 期下载件,v3 件未同步。这是本元流程
第二次落盘失同步(第一次为 change_37 丙-B1),故给 prompt 落盘补上
与设计快照同级的物理校验:

1. 目标机 `p45-implementation-prompt-v1_5_15.md` 必须以**本次交付件
   整文件替换**(含 CK-IDX 目标钉死为确切文件名的 v3.1 微修);
2. **落盘断言**:目标机文件 sha256 必须等于
   `22d217a2e5e3c73e0110a5763ae16bc85e23cfbf38cc6aa3c9384dbc2d2432c5`
   (`sha256sum` 输出入 P0 报告;不一致 = 落错版本,禁止开工);
3. C 节验收补一行:checker/设计/prompt 三件的落盘一致性断言
   (design 快照 `cmp` + prompt sha256)同为 P0 完成条件。
