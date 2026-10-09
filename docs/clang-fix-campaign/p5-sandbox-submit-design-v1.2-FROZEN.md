# P5 sandbox-submit 设计(v1.2,FROZEN)

- 阶段:Phase 5(安全阶段,三家评审)
- 上位文档:`docs/clang-fix-campaign/design.md` v1.5.19-FROZEN。本文只写 P5 的接口、行为与验收;
  与 design.md 冲突处以本文为准,冲突点全部列在附录 A,随 P5 第一个提交同步进 design.md(升 v1.5.20)。
- 输入基线:`origin/clang-fix-campaign` @ `cd7f8dd`(P2/P3/P4 已 CLOSED)。
- 两轮评审的修改与采纳来源见附录 B(第一轮)与附录 C(第二轮)。两轮评审已用满,v1.2 经 FatTank 批准后即冻结。

---

## 0. 范围与一个必须先说明的缺口

### 0.1 P4.5 遗留缺口(三家评审均已回仓核实)

design.md §7 把 P5 写成"调用 P4.5 的 policy 与 gate 记录 API(自身不再实现)",但仓库现状是:

| design.md 中 P4.5 应交付 | 仓库现状 @ cd7f8dd |
|---|---|
| `ci_triage/suppress_policy.py`:`evaluate` + `suppress-policy check` CLI | **不存在** |
| `campaign_state.gate_view` | **不存在**(只有 `latest_event` 等单类型读取) |
| gate 事件写入(`append_event` + 各 payload 校验器,含 POLICY/DERIVE/PUSH) | 已存在 |
| `campaign_repair_step`(九步 wrapper) | 已存在,P4.5 close-out 只覆盖了这一部分 |

**裁定**:这两项并入 P5 实施,不另开阶段。它们的 DoD 沿用 design.md §7 Phase 4.5 中的对应条目,本文 §6 逐条列出。

### 0.2 P5 范围

1. `suppress_policy`:§3.7 判定的可执行规则(本文 §2)。
2. `gate_view` 与只读缓存查询(本文 §3)。
3. `sandbox_submit`:`toctou_recheck`、`check_push_ref` 与 `sandbox-submit` CLI 全流程(本文 §4)。
4. 移交到 P5 的加固项(本文 §5):
   - change_46 遗留两项:canonical edit_spec 发布后父目录 fsync;`os.link` 不可用时的显式失败;
   - P4 签收登记的两项:日期正则限 ASCII 并校验日期真实存在;真实 hook 测试 hash 不符改为失败;
   - P2 移交:已有 DERIVE 的 sandbox 重推,若缓存行被删,必须拒绝且不 push(端到端)。

### 0.3 不在 P5

- 真实 Gerrit 推送:P5 全部用本地裸仓库充当远端。第一次真实 sandbox push 按 EF-6 结论放在 P12。
- KB append(P8)、QB 触发(P5Q)、review-submit(P5R)、副本释放(P10)、campaign-preflight(P8.5)。
- 同一 Gerrit 仓库多个 unit 共用同一 sandbox 分支的冲突检测:沿用 design.md A5-b 假设,本期不做。
  后推者覆盖;先推者在 P5Q 的远端 ref 实时校验处 fail-closed。

---

## 1. 术语与固定值

- **三份记录**:调用方传入的三个 verification_id 对应的 `verification_records` 行。
- **unit / round**:`campaign_units` 行 / `campaign_rounds` 行。
- **unit_hash**:`hashlib.sha256(campaign_unit_key.encode("utf-8")).hexdigest()[:12]`。
  实现**直接复用** `campaign_repair_step._unit_hash`,把它提为两处共用的私有函数,行为不变。
  锁路径与 src_clean 路径一律由它派生。
- **主副本**:`unit.primary_arch` 那份记录的 `worktree_path`,derive 与 push 都在它的对象库上执行。
- **src_clean**:`<campaign_ws>/<unit_hash>/src`,发现阶段 checkout 到 `unit.base_commit` 的干净源码树(design.md §4.1 第 5 步)。
- **sandbox ref**:`refs/heads/<--sandbox-branch>`。
- **subject 前缀**:`Fix build error for clang compiler: `(含末尾空格)。
- **时间格式**:`YYYY-MM-DDTHH:MM:SS+00:00`,UTC,秒级,由 `datetime.now(timezone.utc).replace(microsecond=0).isoformat()` 生成。
- **ARCH_ORDER**:`("aarch64", "armv7l", "x86_64")`。凡需要在多个 arch 中选一个时,按此顺序取第一个。
- **WHOLESALE_NAMES**:`{"everything", "all", "extra", "pedantic"}`,§2 三处共用这一份。
- **POLICY_RULES_VERSION**:`"p5-policy/v1"`。规则有任何改动都必须升这个版本号。

---

## 2. suppress_policy(`ci_triage/suppress_policy.py`)

### 2.1 接口

```python
SourceKind = Literal["t1_cherry_pick", "generated", "suppress"]

@dataclass(frozen=True)
class PolicyHit:
    edit_index: int     # 触及该处的 edit 下标;判不出时为 -1(见 2.7)
    file: str           # edit_spec 中的原样路径
    kind: str           # 2.4 的 kind 枚举,或移除类规则名 werror_removed / pragma_pop_removed / target_removed / pure_deletion(字段取值见 progress P5-C2-02)
    token: str | None   # 命中的选项、pragma flag 或 "命令名 名称"
    scope: str          # 2.5 的 scope 枚举;非作用域类为 "n/a"
    rule: str           # "forbidden" | "suppress"
    count: int          # 该键编辑后比编辑前多出(或少掉)的实例数,≥1

@dataclass(frozen=True)
class PolicyVerdict:
    verdict: Literal["allowed", "forbidden"]
    fix_strategy_final: Literal["code", "cherry_pick", "suppress"] | None  # forbidden 时为 None
    hits: tuple[PolicyHit, ...]
    rules_version: str  # 恒为 POLICY_RULES_VERSION

class PolicyInputError(ValueError): ...

def evaluate(edit_spec: Mapping[str, object], src_root: Path,
             source_kind: SourceKind) -> PolicyVerdict: ...
```

- `evaluate` 是纯函数:不写文件,不访问 state DB,不联网。同一输入多次调用结果逐字段相等,且与 `edits[]` 的排列无关(`edit_index` 除外)。
- 输入校验:先调用既有 `tizen_build_verify.edit_spec_guard.validate_edit_spec(edit_spec, str(src_root))`,
  它抛 `EditSpecViolation` 时转抛 `PolicyInputError`。`source_kind` 不在三值内同样抛 `PolicyInputError`。
- `hits` 排序键:`(rule, kind, file, token or "", scope, edit_index)`。

### 2.2 编辑前后的整文件内容

判定只比较**编辑前、编辑后的完整文件**,不看单个 edit 的 old/new 片段。
(v1.0 按片段计数,会被拼接、等数迁移、注释转活动文本绕过,见附录 B。)

1. 对每个被编辑的文件,从 `src_root` 读原文,作为"编辑前内容"(`utf-8`,`errors="surrogateescape"`)。
2. 用与 `edit_spec_guard` 相同的定位规则求出每个 edit 的 `[start, end)`,按 start 从大到小依次替换为 new,得到"编辑后内容"。
   同时记录每个 edit 在编辑前内容中的区间,以及其 new 在编辑后内容中的区间。
3. 未被任何 edit 触及的文件不参与判定。

### 2.3 词法:哪些文本算"活动文本"

只有活动文本里的内容参与识别。各文件类别见 2.3.1,规则如下:

| 类别 | 不算活动文本 | 其余说明 |
|---|---|---|
| `cmake` | 行注释与块注释 | 见下方三条 |
| `automake` `build_other` `spec` | `#` 注释 | 先做续行拼接 |
| `source` | 注释、字符串字面量、字符字面量 | 先做续行拼接 |
| `doc` | 全部(不识别任何选项与 pragma) | 文档不参与编译 |
| `other` | — | 全部算活动文本 |

**cmake 的三条规则:**
- **行注释**:位于参数起始位置的 `#` 开始一行注释,到行尾结束。
  参数起始位置指前一字符为空白、`(` 或 `)`,或位于行首,且不在引号参数或括号参数内。
- **块注释**:`#[` 加若干 `=` 加 `[` 开始,对应的 `]` 加同样数量的 `=` 加 `]` 结束。
- **引号参数与括号参数**:引号参数 `"…"`(支持 `\` 转义)与括号参数 `[=*[ … ]=*]` 都是活动文本。
  其中的括号和 `#` 不参与括号配对,也不开始注释,但其中的选项照常识别。
  每个参数还要求出它的**值**:引号参数去掉两端引号并处理 CMake 转义;括号参数去掉定界符;未加引号的参数取原文。

**automake、build_other、spec:**
- 先做续行拼接:行尾 `\` 与紧随的换行一起删除。删除前后的位置要能对应回原文。
- 然后,位于行首或前一字符为空白的 `#` 开始注释。引号内的内容仍算活动文本。

**source:**
- 先做续行拼接,规则同上。
- `//` 与 `/* */` 注释不算活动文本。
- 字符串字面量与字符字面量不算活动文本,唯一例外是 `_Pragma(...)` 的参数,见 2.4。

#### 2.3.1 文件分类

按路径匹配,扩展名大小写不敏感,自上而下取第一个命中的类别。

| 类别 | 规则 |
|---|---|
| `spec` | 扩展名 `.spec`,或路径含 `packaging/` 目录段 |
| `cmake` | 文件名 `CMakeLists.txt`,或扩展名 `.cmake` |
| `automake` | 文件名 `Makefile.am` |
| `build_other` | 文件名以 `Makefile` 开头(`Makefile.am` 除外)、扩展名 `.mk` `.in` `.ac` `.m4`,或文件名 `meson.build` `configure` |
| `source` | 扩展名 `.c` `.cc` `.cpp` `.cxx` `.c++` `.h` `.hh` `.hpp` `.hxx` `.inl` `.ipp` `.m` `.mm` |
| `doc` | 扩展名 `.md` `.rst` `.adoc`;文件名以 `README` `ChangeLog` `NEWS` `AUTHORS` 开头;路径含 `doc/` 或 `docs/` 目录段 |
| `other` | 其余(包括 `.txt`,因为它可能被 `file(READ)` 读成编译选项) |

#### 2.3.2 选项 token 的定义

在活动文本上用下面的正则做匹配,得到选项 token:

```
(?<![A-Za-z0-9_\-])-(?:W[A-Za-z0-9_+.=#\-]*|w)(?![A-Za-z0-9_+.=#\-])
```

- 以 `-W` 或 `-w` 开头;前一字符不是字母、数字、`_` 或 `-`;向后取最长的名字字符;后一字符不再是名字字符。
- 其它字符都是边界,包括空白、引号、`\` `{` `}` `(` `)` `,` `;` `:` `>` `|` `&`。
- 据此,`$<…:-Wno-foo>`、`${FLAGS}-Wno-foo`、`"-Wno-foo"`、`-Wno-foo,-Wno-bar` 都能识别出 token,`XX-Wno-foo` 不算 token。

### 2.4 识别的形态(kind)

| kind | 识别 | 规则 |
|---|---|---|
| `wno_flag` | token 为 `-Wno-<name>`;name 不是 `error`,不以 `error=` 开头,且不在 WHOLESALE_NAMES 中 | 抑制,需做作用域判定 |
| `wno_error_flag` | token 为 `-Wno-error=<name>`,name 不在 WHOLESALE_NAMES 中 | 抑制,需做作用域判定 |
| `wno_error_all` | token 恰为 `-Wno-error` | **forbidden** |
| `wno_wholesale` | token 为 `-Wno-<n>` 或 `-Wno-error=<n>`,n ∈ WHOLESALE_NAMES | **forbidden** |
| `w_all_off` | token 恰为 `-w` | **forbidden** |
| `werror` | token 为 `-Werror` 或 `-Werror=<name>` | 只参与"移除"判定(2.6) |
| `pragma_suppress` | pragma 语法第 1 条,flag 的 name 不在 WHOLESALE_NAMES 中 | 抑制,scope=`source_local` |
| `pragma_wholesale` | pragma 语法第 1 条且 flag 的 name ∈ WHOLESALE_NAMES;或 pragma 语法第 2 条 | **forbidden** |
| `pragma_unparsed` | 见下方 | **forbidden** |
| `pragma_pop` | pragma 语法第 3 条中的 `pop` | 只参与"移除"判定(2.6) |
| `target_decl` | cmake 中 `add_executable` / `add_library` / `add_test` 命令 | 只参与"移除"判定(2.6) |

**pragma 文本的来源**(只在 `source` 文件的活动文本中识别):

- **指令形式**:以 `#` 开头(前面只允许空白)、续行拼接后的整行。去掉 `#` 与 `pragma` 关键字后,剩余部分即 pragma 文本。
- **运算符形式**:`_Pragma ( <参数> )`。参数必须是单个普通字符串字面量。
  按 C 标准"去字符串化"得到 pragma 文本:去掉两端引号,把 `\"` 换成 `"`、`\\` 换成 `\`。
  去字符串化后若仍含其它反斜杠转义(如 `\42`),整条视为无法解析。

**pragma 语法**(两种来源统一套用,`(clang|GCC)` 大小写按原样匹配,各段之间允许任意空白):

1. `(clang|GCC) diagnostic (ignored|warning) "<flag>"`,flag 形如 `-W<name>`。
   `warning` 与 `ignored` 同样算抑制,因为在 `-Werror` 下 `warning` 会把该诊断从错误降为警告。
2. `(clang|GCC) system_header`:让编译器把文件其余部分当作系统头,屏蔽全部警告。
3. `(clang|GCC) diagnostic (push|pop|error|…)` 等其它 diagnostic 子命令:不产生抑制 hit。`pop` 计为 `pragma_pop` 实例。
4. 其余 pragma(`once`、`pack` 等):不产生 hit。

**pragma_unparsed** 指以下任一情况:
- 活动文本中出现 `__pragma` 标识符;
- 出现 `_Pragma`,但参数不是单个普通字符串字面量(例如经宏包装),或去字符串化后含其它转义;
- pragma 文本中含 `diagnostic` 或 `system_header` 字样,但不符合语法第 1–3 条中的任何一条(例如 flag 没有引号)。

### 2.5 作用域判定(`wno_flag` / `wno_error_flag` / `werror`)

每个选项实例都要求出 scope,规则按文件类别区分。

**cmake**:把活动文本切成顶层命令 `name( … )`,括号按深度配对,参数按 2.3 的规则划分。

| 实例所在位置(命令名不分大小写) | scope | 对抑制的结论 |
|---|---|---|
| `target_compile_options` 中 `PRIVATE` 段 | `target_private` | 允许 |
| `set_source_files_properties` / `set_target_properties` / `set_property` 中,实例之前最近的"属性参数"为 `COMPILE_OPTIONS` 或 `COMPILE_FLAGS`;`set_property` 的第 1 个参数的值还须为 `TARGET` 或 `SOURCE` | `target_property` | 允许 |
| `target_compile_options` 的 `PUBLIC` / `INTERFACE` 段,不在任何段内,或段归属无法确定 | `global_or_ambiguous` | **forbidden** |
| `add_compile_options`、`add_definitions`、`set`、`string`、`list`、其它任何命令,或不在任何命令内 | `global_or_ambiguous` | **forbidden** |

- **段的划分**:在 `target_compile_options` 的参数中,**值**(2.3)恰为 `PRIVATE`、`PUBLIC`、`INTERFACE` 的参数是段关键字。
  未加引号、引号、括号三种写法一律按值识别,因为 CMake 本身按值识别。
  实例属于它之前最近的那个段关键字;之前没有段关键字时视为"不在任何段内"。
- **段归属无法确定**:从第 2 个参数起,到实例所在的参数为止(含该参数),只要有任一参数含变量引用(`${`、`$ENV{`、`$CACHE{`),
  该实例就算段归属无法确定。原因是变量展开后可能成为段关键字。生成器表达式 `$<…>` 不算,它在配置阶段之后才求值,不可能成为段关键字。
  第 1 个参数(目标名)的形态不限,`${PROJECT_NAME}` 之类也可以。
- **属性参数**:按值判断,指 `PROPERTY`、`PROPERTIES`、`COMPILE_OPTIONS`、`COMPILE_FLAGS` 这四个之一。
- **已知限制**(写进收口文档):同一命令中若在 `COMPILE_OPTIONS` 之后又设置了别的属性,该属性值里的 `-Wno-*` 会被视为 `target_property`。
  这种写法没有编译效果,不构成全局抑制。
  `target_compile_options(t PRIVATE ${MY_FLAGS} -Wno-x)` 会因段归属无法确定而被拒,属保守误杀,须人工处理。

**automake**:取实例所在的逻辑行(已做续行拼接)。
- 行首形如 `<prefix>_(CFLAGS|CXXFLAGS|CPPFLAGS)\s*[:+?]?=`,且 prefix 非空、不是 `AM`:scope=`target_variable`,允许;
- 其余:`global_or_ambiguous`,forbidden。

**spec、build_other、other**:一律 `global_or_ambiguous`,forbidden。spec 中没有按 target 限定的写法(§3.7)。

**source**:选项 token 不在 source 中识别,因为源码中的 `-W` 文本只可能出现在字符串或注释里,已被 2.3 排除。pragma 的 scope 为 `source_local`。

### 2.6 判定:比较编辑前后的实例计数

对每个被编辑的文件,在编辑前、编辑后内容上分别枚举全部实例,每个实例得到一个键:
- 选项与 pragma 类实例:键为 `(kind, token, scope)`。pragma 的 token 为 flag 或 `system_header`;`pragma_unparsed` 的 token 为该段原文。
- `target_decl`:键为 `(命令名小写, 第一个名称参数的值)`。`add_test(NAME x …)` 形式取 `NAME` 之后的参数。名称含 `${…}` 时按原文字面比较。

**所有规则都逐文件比较**,不允许用一个文件里的新增抵消另一个文件里的移除。

| 规则 | 判定(在同一文件内) | hit 的 rule |
|---|---|---|
| 抑制(`wno_flag` `wno_error_flag` `pragma_suppress`) | 某键编辑后次数多于编辑前 | scope 允许时为 `suppress`,否则 `forbidden` |
| 整类形态(`wno_error_all` `wno_wholesale` `w_all_off` `pragma_wholesale` `pragma_unparsed`) | 某键编辑后次数多于编辑前 | `forbidden` |
| `werror_removed` | 对每个 werror token(`-Werror` 或某个 `-Werror=<name>`):`global_or_ambiguous` 键减少;或其它 scope 的减少总数大于 `global_or_ambiguous` 键的增加数 | `forbidden` |
| `pragma_pop_removed` | `pragma_pop` 的减少数大于全部 `pragma_suppress` 键减少数之和 | `forbidden` |
| `target_removed` | 某个 `target_decl` 键编辑后次数少于编辑前 | `forbidden` |
| `pure_deletion` | 逐 edit:新文本去掉空白后为空 | `forbidden` |

按键比较的效果:

| 改动 | 结果 |
|---|---|
| 等数迁移:`target_compile_options(t PRIVATE -Wno-foo)` 改成 `add_compile_options(-Wno-foo)` | `global_or_ambiguous` 键加 1,`target_private` 键减 1,命中前者,forbidden |
| 拼接:把 `-Werror` 中的 `error` 改为 `no-error` | 编辑后整文件中出现 `-Wno-error`,同时 `-Werror` 减少,两条都命中 |
| 注释转活动文本 | 原来在注释里的 token 不计数,移出注释后计数加 1,命中 |
| 同一文件内同作用域重排已有抑制或 `-Werror` | 不产生 hit |
| 把 `-Werror` 从单个 target 放大到同一文件的全局 | 全局增加抵消非全局减少,不产生 hit |
| 把 `-Werror` 从全局收窄到单个 target | 命中 `werror_removed`(有意从严) |
| 跨文件搬动 `-Werror` 或 target 声明 | 移出的那个文件命中(有意从严,合法搬动须人工处理) |
| 只删 `#pragma … pop`,让已有抑制扩大到文件末尾 | 命中 `pragma_pop_removed` |
| 把 push、ignored、pop 整段一起删除(撤销一处抑制) | pop 与 suppress 同时减少,不命中 |

### 2.7 hit 的定位

- **选项与 pragma 类 hit**:取编辑后内容中,该键各实例所在区间与各 edit 新区间相交的最小 edit 下标。
  对 cmake 实例,"所在区间"取其所属命令的整个括号范围,这样只改 `PRIVATE`→`PUBLIC` 时也能定位到那个 edit。
  都不相交时为 -1。
- **移除类 hit**(`werror_removed`、`pragma_pop_removed`、`target_removed`):按编辑前内容与各 edit 旧区间做同样的计算。
- **`pure_deletion`**:`edit_index` 就是该 edit 的下标。

### 2.8 判定顺序(§3.7 四步序的落地)

1. 有任何 `rule="forbidden"` 的 hit:`verdict="forbidden"`,`fix_strategy_final=None`。
2. 否则,有任何 `rule="suppress"` 的 hit:`final="suppress"`。
3. 否则 `source_kind == "suppress"`:`final="suppress"`(只收紧,不放宽)。
4. 否则 `source_kind == "t1_cherry_pick"`:`final="cherry_pick"`。
5. 否则 `final="code"`。

`fix_strategy_initial`(写入 POLICY 事件时用)按来源固定映射:`t1_cherry_pick → cherry_pick`,`generated → code`,`suppress → suppress`。

**已知限制**(写进收口文档,不实现):
- edit_spec 只能替换已有文件的内容,"删除源文件"在结构上无法表达;
- 从 CMake 源文件列表中移除单个 `.c` 不在检测范围;
- 纯删行的修复(包括删掉未使用变量的整行)会被 `pure_deletion` 拦下,须走人工;
- 新增调用一个在本次 edit 之外定义的抑制宏(如 `SUPPRESS_WARNING("-Wfoo")`)不会被识别,只有宏定义处的 `_Pragma` 会被识别;
- 跨文件搬动 `-Werror` 或 target 声明会被拦下,须走人工;
- `doc` 类文件不做识别。若某仓库把编译选项放进 `.md`/`.rst` 再读入,不会被检出。

### 2.9 独立 CLI

```
python -m ci_triage suppress-policy check --edit-spec <json> --src-root <path>
    [--source-kind {t1_cherry_pick|generated|suppress}]   # argparse choices;默认 generated
stdout JSON: { verdict, fix_strategy_final, rules_version,
               hits: [ {edit_index,file,kind,token,scope,rule,count} ] }
exit: 0 allowed;4 forbidden(error_code=REJECTED_SUPPRESS_POLICY);2 参数错或 PolicyInputError(INVALID_ARGS)
```

- 输出 JSON 等于 `dataclasses.asdict(evaluate(...))`,hits 输出为列表;有一致性测试。
- 此 CLI 只做预检,不写 state DB。

---

## 3. gate_view 与只读查询(`ci_triage/campaign_state.py` 新增)

```python
@dataclass(frozen=True)
class GateView:
    reproduced: bool
    reproduce_by_arch: Mapping[str, Mapping[str, object]]  # {arch_norm: {outcome, evidence_local, evidence_sha256}}
    policy: Mapping[str, object] | None        # 最新 POLICY payload
    derive: Mapping[str, object] | None        # 最新 DERIVE payload
    sandbox_push: Mapping[str, object] | None  # ref_class=sandbox 的最新 PUSH
    review_push: Mapping[str, object] | None   # ref_class=review 的最新 PUSH
    kb: Mapping[str, object] | None
    review: Mapping[str, object] | None
    qb_result: Mapping[str, object] | None     # 两级最新 RESULT

def gate_view(state_db: StateDatabase, campaign_unit_key: str) -> GateView: ...
def latest_policy_for_round(state_db, campaign_unit_key: str, round_index: int) -> Mapping[str, object] | None: ...
def lookup_change_id(state_db, submission_key: str) -> str | None: ...   # 只读,不生成
```

- **一致快照**:`gate_view` 在同一连接上显式开启读事务(`BEGIN`),在该事务内完成全部 unit、gate 事件与 QB 查询,然后结束事务。
  不得调用会另开连接的公共读取函数(如 `latest_event`、`latest_qb_result`),改用连接级的内部查询原语。
  读事务内不做文件检查、git 或 hook 调用。
- "最新"一律按 `event_id` 最大,不看时间戳。
- **reproduced**:三个目标 arch 各自至少有一条 REPRODUCE,且 primary arch 最新一条的 outcome 为 `matched`。
  secondary 的 outcome 不限(与 design.md §3.6 BASELINE_REPRODUCED 一致)。
  primary 不是 matched 时,无论 secondary 后写什么都为 False。
- **qb_result**:取该 unit 最大 request_seq 的请求;再取该请求内 event_id 最大的 RESULT。
  最新请求还没有 RESULT 时为 None,不回退到旧请求。
- **DERIVE 冲突扫描**:扫描该 unit 全部 DERIVE 行。若 `message_brief`、`author_identity`、`committer_identity`、`author_date`、`committer_date`
  任一字段在不同行之间不一致,抛 `StateInconsistent`。
  这一检查**新增了 committer_identity**:写入侧 `_validate_immutable_derive_fields` 的字段列表漏了它,P5 一并补齐,写入侧与读取侧使用同一字段集。
- unit 不存在:`StateInconsistent`。unit 存在但没有事件:各字段为 None,`reproduced=False`。
- `latest_policy_for_round`:取 `round_index` 等于参数的 POLICY 事件中 event_id 最大的一条。
- `lookup_change_id`:只读查询 `campaign_change_ids`,不调用 generate,不写库。

---

## 4. sandbox_submit(`ci_triage/sandbox_submit.py` + CLI)

### 4.1 CLI(对 design.md §4.1 的修订见附录 A)

```
python -m ci_triage sandbox-submit
    --verification-ids <id1,id2,id3> --state-db <path> --config <path>
    --sandbox-branch <sandbox/<seg>(/<seg>)*>
    [--message-brief "<text>"]                                  # 该 unit 无 DERIVE 时必填
    [--edit-source-kind {t1_cherry_pick|generated|suppress}]    # argparse choices;该 round 无 POLICY 时必填
stdout JSON:{ action, status, aggregate{ok,verified_tree_sha,base_commit,reasons[]},
              policy_verdict, fix_strategy_final, change_id, derived_commit_sha,
              push{ref,result,url}, reused{message_brief,edit_source_kind},
              held{reason,arch_norm,scope}, surviving_worktrees[], error_code|null, reason|null }
exit:0 成功;2 参数错;4 校验拒绝 / HELD / 忙;5 推送失败
```

- `action` ∈ `pushed` | `already_pushed` | `rejected` | `held` | `worktree_lost` | `push_failed` | `invalid_args` | `busy`。
- 不适用的字段输出 null,数组输出 `[]`;字段集合固定,每个 action 都有快照测试。
- `held.scope` ∈ `copy` | `unit` | null:表示 HELD 是由某份副本的问题引起,还是 unit 级问题。
- `push.url` 回显实际使用的远端地址。
- 已有存量时,`--message-brief` / `--edit-source-kind` 的新传入值被忽略,一律复用存量,并在 `reused` 中标 true。

**config 键**(YAML,读取方式同 repair-step):

| 键 | 要求 |
|---|---|
| `campaign_workspace` | 必填,已有键 |
| `gerrit_ssh_base` | 必填。`ssh://` 开头,或绝对路径(仅供测试用本地裸仓库)。远端地址 = 去掉末尾 `/` 后接 `/` + `unit.project`。非 `ssh://` 时由 campaign-preflight(P8.5)报 `PREFLIGHT_FAILED`,本约束经附录 A 写入 design.md |
| `git_author_identity` / `git_committer_identity` | 必填,`Name <email>`,按 `derive_commit._identity` 的规则校验 |
| `gerrit_commit_msg_hook` / `gerrit_commit_msg_hook_sha256` | 必填,已有键 |
| `git_ssh_command` | 可选;作为 `GIT_SSH_COMMAND` 传给所有 git 调用,未配置时取 `ssh`(见 4.4) |
| `push_timeout_seconds` | 可选,正整数,默认 300;ls-remote 与 push 各自适用 |

缺键或格式错:exit 2,`INVALID_ARGS`,零写入。

### 4.2 记号

- **零写入**:不写 state DB、不写缓存行、不调用 hook、不 push。
- **HELD(x)**:调用 `append_status(state_db, unit, HELD_FOR_INVESTIGATION, reason=x, arch_norm=a)`,然后 exit 4,action=`held`。
  `a` 按下表确定,`held` 字段同时回显 reason、arch_norm 与 scope。

| 条件来源 | scope | arch_norm |
|---|---|---|
| 某份副本的问题:保护标记缺失、HEAD 树不等、不干净、记录字段被改 | `copy` | 该副本的 arch_norm;多份同时不符时按 ARCH_ORDER 取第一个,其余写入 stdout `reason` |
| unit 级问题,且 reason ∈ `_ARCH_SCOPED_HELD_REASONS`(P5 只会用到其中的 `state_inconsistent` 与 `verification_mismatch`;该常量的完整成员见 `campaign_state`) | `unit` | `unit.primary_arch` 对应的 arch_norm |
| unit 级问题,且 reason 为 `aggregate_mismatch`、`edit_spec_rebind_mismatch`、`suppress_policy_recheck` | `unit` | None |

  HELD 的 reason 全部取自现有 `_HELD_REASONS`,不新增枚举值,也不改 `append_status`。

- **已在挂起**:写 HELD 前若最新状态已是 `HELD_FOR_INVESTIGATION`,不再追加,直接 exit 4。

### 4.3 执行流程

每一步失败即停。

**第 0 步 参数(零写入,exit 2)**
- `--verification-ids`:逗号分隔,恰好 3 个,去空白后非空且互不相同。
- `--sandbox-branch`:匹配 `^sandbox/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$`,且 `git check-ref-format refs/heads/<branch>` 返回 0;否则 `INVALID_BRANCH_NAME`。
- `--message-brief`(若给出):`strip` 后长度 1–100,不含 `unicodedata.category` 为 `Cc` 的字符。
- `--edit-source-kind`:由 argparse `choices` 限定三值,非法值为 exit 2。
- config 按 4.1 校验。

**第 1 步 加锁(零写入)**
1. 加锁前,只读查 `campaign_verifications`,取三个 id 链接的 unit_key。不是同一个 unit 时按第 2 步规则直接拒绝,不加锁。
2. 按固定顺序非阻塞获取四把锁:
   `<ws>/<unit_hash>/.sandbox_submit.lock`,以及按 ARCH_ORDER 的三个 `<ws>/<unit_hash>/<arch>/.repair_step.lock`。
   后三把与 repair-step 使用的是同一组文件,路径都由 §1 的 unit_hash 派生。
3. 任一把锁拿不到:exit 4,`CAMPAIGN_STATE_BUSY`,action=`busy`。
4. 加锁后,第 2 步的全部检查在锁内**重新完整执行**,不复用加锁前读到的任何结果。
   锁内查得的 unit_key 与加锁时所用的不同,同样 exit 4 `CAMPAIGN_STATE_BUSY`,零写入。

**第 2 步 选定(零写入,exit 4)**

调用方选错记录不能冻结单元,所以这一步的拒绝都不写 HELD。

| 检查 | 不符时的错误码 |
|---|---|
| 三个 id 都在 `campaign_verifications` 中有链接行 | `REJECTED_ARCH_AGGREGATE_MISMATCH` |
| 三行的 `campaign_unit_key` 相同、`round_index` 相同,`arch_norm` 集合等于 `ARCH_NORMS` | `REJECTED_ARCH_AGGREGATE_MISMATCH` |
| 该 round 就是 `latest_round(unit)` | `REJECTED_ROUND_SUPERSEDED`(新增错误码),stdout `reason` 写出两个 round_index |
| `latest_status(unit)` ∈ {`REPAIR_ROUND_RUNNING`, `LOCAL_3ARCH_PASS`, `SANDBOX_PUSHING`, `SANDBOX_PUSH_FAILED`, `SANDBOX_PUSHED`} | `REJECTED_STATE_INCONSISTENT`(与 repair-step 对不可执行状态的处理一致) |

- 首次必填项:`latest_event(unit, "DERIVE") is None` 且未给 `--message-brief`,
  或 `latest_policy_for_round(unit, round) is None` 且未给 `--edit-source-kind`:exit 2,`INVALID_ARGS`。
- 这一步只判断"有没有",不做 DERIVE 历史行的冲突扫描。冲突扫描在第 8 步经 `gate_view` 执行,冲突即 HELD。
- 这一步的结果连同 unit 行一起记为**选定快照**,供第 12 步比对。

**第 3 步 聚合与副本存在性**
- `aggregate_verifications(ids, state_db)`:`ok=False` → HELD(`aggregate_mismatch`),stdout 带 reasons。
- 聚合结果的 `base_commit`、`project`、`spec_name`、`branch` 必须分别等于 unit 的同名字段;不等 → HELD(`aggregate_mismatch`)。
- 三份记录的 `worktree_path` 必须都是存在的目录。缺任何一份时:
  - 写状态 `WORKTREE_LOST`,reason 为缺失的 arch_norm 按 ARCH_ORDER 逗号连接;
  - exit 4,`REJECTED_WORKTREE_MISSING`,action=`worktree_lost`;
  - `surviving_worktrees` 列出仍存在的路径。
- 三份副本都必须带保护标记(`tizen_ci_shared.workspace.is_protected`);任一缺失 → HELD(`verification_mismatch`),scope=copy。
- 通过后,仅当最新状态是 `REPAIR_ROUND_RUNNING` 时写 `LOCAL_3ARCH_PASS`;重跑时不再写。
- 聚合结果记为**聚合快照**。

**第 4 步 edit_spec 重绑定**
- 读取 `round.edit_spec_ref` 文件的原始字节,计算 sha256。它必须同时等于:
  `round.edit_spec_sha256`、三条链接行的 `edit_spec_sha256`、聚合结果的 `edit_spec_sha256`。
  任一不等 → HELD(`edit_spec_rebind_mismatch`)。
- 后续 policy **只用这份已绑定的字节**(`json.loads` 一次,不再读文件)。

**第 5 步 src_clean 校验(不写 HELD)**
- 与 repair-step 相同的三重校验:HEAD 等于 `unit.base_commit`;origin 归一化后等于 `unit.project`;`.campaign_clone` 标记内容与 unit 一致。
- 另加两层干净检查:`git diff --quiet HEAD --` 与 `git diff --cached --quiet`。
- 任一不符:exit 4,`REJECTED_IDENTITY_MISMATCH`。src_clean 可以重建,不是现场证据,所以不冻结单元。
- src_clean 还要通过 4.4 的配置安全检查;不通过时 exit 4,`REJECTED_UNSAFE_GIT_CONFIG`,不写 HELD。
- 本步及以后的所有 git 调用都使用 4.4 的统一环境与覆盖。
- 实现上把 repair-step 现有的校验函数提为两处共用的私有模块,行为不变。

**第 6 步 policy**
- source_kind:该 round 已有 POLICY 时取其 `edit_source_kind`;否则取 `--edit-source-kind`。
- `evaluate(第 4 步的 edit_spec, src_clean, source_kind)`。抛 `PolicyInputError` → HELD(`edit_spec_rebind_mismatch`)。
  这份内容已通过构建验证,此时不合法,说明它被改过或 src_clean 不对应。
- 该 round **无** POLICY 时,追加一条 POLICY 事件:
  `{round_index, verdict, hits(asdict 列表), fix_strategy_initial(按 2.8 映射), fix_strategy_final, edit_source_kind, rules_version}`。
- 该 round **已有** POLICY 时,比较 `verdict`、`fix_strategy_final`、`edit_source_kind` 三项:
  - 不同 → HELD(`state_inconsistent`),stdout `reason` 同时写出存量与当前的 `rules_version`;
  - 相同则不追加。`hits` 不参与比较。
  - 规则升级导致结论变化时,已有的未推送单元会因此挂起,须人工重置;这一点写入收口文档。
- `verdict == "forbidden"` → HELD(`suppress_policy_recheck`),`error_code=REJECTED_SUPPRESS_POLICY`。
  forbidden 时 POLICY 事件照写(用于审计),但流程到此为止:不派生、不调用 hook、不 push。

**第 7 步 副本现场校验(不写状态)**

对三份副本逐一检查:
- 通过 4.4 的配置安全检查;不通过时 exit 4,`REJECTED_UNSAFE_GIT_CONFIG`,不写 HELD。
  配置不安全来自源仓库或环境,不是对已验证内容的篡改,修正配置后可重跑。
- `git rev-parse HEAD^{tree}` 必须等于 `verified_tree_sha`;不等 → HELD(`verification_mismatch`),scope=copy。
- 两层干净检查同第 5 步;不干净 → HELD(`worktree_dirty`),scope=copy。

**第 8 步 四要素**
- 调用 `gate_view(unit)`。抛 `StateInconsistent`(DERIVE 历史行冲突)→ HELD(`state_inconsistent`)。
- `gate_view.derive` 存在(重跑):其 `verified_tree_sha` 必须等于聚合值,否则 HELD(`state_inconsistent`)。brief、两个身份、两个日期一律取存量。
- 不存在(首次):brief 取参数;身份取 config;`author_date = committer_date = 当前时间`(§1 格式)。

**第 9 步 Change-Id**
- `submission_key = compute_submission_key(unit.submission_identity_key, verified_tree_sha)`。
- 调用 `get_or_create_change_id(state_db, campaign_unit_key=unit, submission_key=…, hook_sha256=config 值, generate=…)`:
  - 无 DERIVE 时,`generate` 为调用 `generate_change_id_via_hook(hook_path, hook_sha256, submission_key, message=subject + "\n")` 的闭包;
  - 有 DERIVE 时,`generate=None`。
- `ChangeIdHookError` → exit 4,`CHANGE_ID_HOOK_FAILED`,action=`rejected`,不写 HELD。可重试:不写 DERIVE、不 push。
- `StateInconsistent` → HELD(`state_inconsistent`)。P2 移交的"缓存行被删"走这里。

**第 10 步 组装消息与派生**
- `message = f"{SUBJECT_PREFIX}{brief}\n\nChange-Id: {change_id}\n"`。这是唯一格式,不加其它 trailer(附录 A 修订 A5)。
- `derived = derive(主副本, verified_tree_sha, base_commit, message, author_identity, committer_identity, author_date, committer_date)`。
- 无 DERIVE:追加 DERIVE 事件
  `{message_brief, author_identity, committer_identity, author_date, committer_date, derived_commit_sha, verified_tree_sha}`。
  顺序不变式保持:缓存行(第 9 步)先于首个 DERIVE。
- 有 DERIVE:`derived` 必须等于存量 `derived_commit_sha`,否则 HELD(`state_inconsistent`)。不追加。
- `derive` 抛 `ValueError` 或 `CalledProcessError` → HELD(`state_inconsistent`)。输入全部来自已校验的存量,派生失败说明对象库或存量异常。

**第 11 步 推送目标校验(不写 HELD,exit 4)**

```python
class RefClass(Enum): SANDBOX = "sandbox"; REVIEW = "review"; FORBIDDEN = "forbidden"
def check_push_ref(ref: str) -> RefClass: ...
```

- `SANDBOX`:`^refs/heads/sandbox/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$`,且 `git check-ref-format` 通过。
- `REVIEW`:`^refs/for/<branch>$`,branch 通过 `git check-ref-format --branch`,且不含 `%`(P5R 如需推送选项另行修订)。
- 其余:`FORBIDDEN`。
- 本步要求结果为 `SANDBOX`,否则 `REJECTED_REF_NOT_ALLOWED`。第 0 步已校验过分支名,这里是纵深防御。
- **远端地址不得被改写**,以下三项任一不符 → `REJECTED_REF_NOT_ALLOWED`,stdout `reason` 注明命中项:
  1. 主副本通过 4.4 的配置安全检查。该检查拒绝任何 `url.*.insteadOf` 与 `url.*.pushInsteadOf`:
     后者只在 push 时生效,`ls-remote --get-url` 看不到它,所以必须直接查配置键;
  2. `git -C <主副本> remote` 列出的远端名中没有与 `<remote>` 逐字相同的,防止 `<remote>` 被当作具名远端解析;
  3. `git -C <主副本> ls-remote --get-url <remote>` 的输出与 `<remote>` 逐字相等。

**第 12 步 TOCTOU 重校验(写入与推送紧前)**

```python
@dataclass(frozen=True)
class SubmitSnapshot:
    unit: Unit                     # 选定快照中的 unit 行
    round_: Round
    links: tuple[...]              # 三条 campaign_verifications 行
    expected_status: str           # 本次运行最后一次读到或写入的最新状态
    aggregate: AggregateResult     # 聚合快照
    policy: Mapping[str, object]   # 本次写入或比对过的 POLICY
    derive_payload: Mapping[str, object]
    change_id: str
    submission_key: str
    derive_inputs: DeriveInputs    # derive 的八个输入,worktree 为主副本
    derived: str
    remote: str

@dataclass(frozen=True)
class TocTouResult:
    ok: bool
    error_code: str | None
    held_reason: str | None        # None 表示不写 HELD(src_clean 不符、副本缺失、配置不安全、远端被改写)
    held_arch: str | None
    detail: str | None

def toctou_recheck(state_db, snapshot: SubmitSnapshot, *, src_clean: Path) -> TocTouResult: ...
```

按顺序逐项核对,第一个不符即返回。数据库读取全部在同一读事务内完成。

| 项 | 核对内容 | 不符时 |
|---|---|---|
| 1 | 三条链接行、同 unit 同 round、arch 集合;`latest_round` 仍为快照 round;最新状态等于 `expected_status`;unit 行全部字段等于快照 | `state_inconsistent`(unit 级) |
| 2 | 重新调用 `aggregate_verifications`,`ok=True`,且全部七个绑定字段与聚合快照逐项相等 | `aggregate_mismatch` |
| 3 | 三份记录的 `worktree_path`、`arch` 与快照相等 | `verification_mismatch`(copy) |
| 4 | 每份副本:目录存在;带保护标记;通过配置安全检查;`HEAD^{tree}` 等于 `verified_tree_sha`;两层干净 | 目录缺失:按第 3 步写 `WORKTREE_LOST`;配置不安全:exit 4 `REJECTED_UNSAFE_GIT_CONFIG`,不写 HELD;保护标记或树不符:`verification_mismatch`(copy);不干净:`worktree_dirty`(copy) |
| 5 | round 文件 sha256 等于 `round.edit_spec_sha256` | `edit_spec_rebind_mismatch` |
| 6 | `gate_view`:最新 DERIVE 等于 `derive_payload`;`latest_policy_for_round` 的三项等于 `policy`;`lookup_change_id(submission_key)` 等于 `change_id` | `state_inconsistent`(unit 级) |
| 7 | src_clean 三重校验、配置安全检查与两层干净 | exit 4 `REJECTED_IDENTITY_MISMATCH` 或 `REJECTED_UNSAFE_GIT_CONFIG`,不写 HELD |
| 8 | 用已绑定字节与 src_clean 重算 `evaluate`,`verdict` 与 `fix_strategy_final` 等于 `policy` | `state_inconsistent`(unit 级) |
| 9 | 用 `derive_inputs` 再调一次 `derive`,结果等于 `derived` | `state_inconsistent`(unit 级) |
| 10 | 第 11 步的三项远端地址检查 | exit 4 `REJECTED_REF_NOT_ALLOWED`,不写 HELD |

`ok=False` 时,调用方按 `held_reason` 写 HELD(或写 `WORKTREE_LOST`、或直接拒绝),不写其它任何东西,不 push。

**第 13 步 远端读取、记账与推送**

0. **远端读取**:用 4.4 的环境执行 `git ls-remote --exit-code <remote> <sandbox ref>`:
   - 返回 0:记 `R` 为远端 sha;
   - 返回 2:记 `R = None`;
   - 其余返回码或超时:按本步第 4 项处理。
1. **已推送**:`R == derived`,且 `gate_view.sandbox_push` 为 `{ref 相同, pushed_sha == derived, result="ok"}`,且最新状态为 `SANDBOX_PUSHED`:
   不写任何东西,exit 0,action=`already_pushed`。
2. **补账**:`R == derived`,但上一项条件不完全满足:
   - `sandbox_push` 不是上述 ok 记录 → 追加 PUSH(ok);
   - 最新状态不是 `SANDBOX_PUSHED` → 追加 `SANDBOX_PUSHED`;
   - exit 0,action=`pushed`。
3. **推送**:`R != derived`:
   - 若最新状态不是 `SANDBOX_PUSHING`,先写 `SANDBOX_PUSHING`;
   - 紧接着对主副本再做一次配置安全检查(防止在第 12 步之后被改),不通过则 exit 4 `REJECTED_UNSAFE_GIT_CONFIG`,不 push;
   - 执行 4.4 的推送命令;
   - 成功后再执行一次第 0 项的 ls-remote,远端 sha 必须等于 `derived`。
4. **推送失败**:以下任一情况:第 0 项读取失败;推送命令失败或超时;推后 ls-remote 失败;推后 sha 不等。处理:
   - 追加 PUSH(`result="failed"`,`pushed_sha=derived`);
   - 写 `SANDBOX_PUSH_FAILED`;
   - exit 5,`PUSH_FAILED`,action=`push_failed`。可直接重跑。
5. **成功**:追加 PUSH `{ref, ref_class:"sandbox", pushed_sha:derived, result:"ok", url:null, at}`;写 `SANDBOX_PUSHED`;exit 0,action=`pushed`。

### 4.4 所有 git 调用的统一环境与配置安全检查

P5 中的每一次 git 调用都使用下面的环境与覆盖,包括 src_clean 与副本上的本地检查(`rev-parse`、`diff`、`remote`、`config`)和远端操作(`ls-remote`、`push`)。
`derive` 沿用 P4 已冻结的环境,不在此列。

**环境变量:**
- 从当前环境中去掉全部 `GIT_*` 变量;
- 设 `GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_TERMINAL_PROMPT=0`;
- 设 `GIT_ALLOW_PROTOCOL=file:ssh`,只允许本地路径与 ssh 两种传输;
- **无条件**设 `GIT_SSH_COMMAND`:取 config 的 `git_ssh_command`,未配置时为 `ssh`。环境变量优先于仓库配置的 `core.sshCommand`;
- 远端操作的超时取 `push_timeout_seconds`;本地检查命令的超时固定为 60 秒。

**每条命令都带的 `-c` 覆盖:**
- `core.hooksPath=/dev/null`
- `core.fsmonitor=false`
- `core.askPass=`
- `credential.helper=`
- `push.followTags=false`
- `push.recurseSubmodules=no`
- `push.gpgSign=false`
- `push.pushOption=`(清空配置中的推送选项)

**`diff` 类命令**一律加 `--no-ext-diff --no-textconv`。

**配置安全检查**:对被检查的仓库执行 `git config --get-regexp <键模式>`(带上述环境),只要出现下列任一键就不通过,
错误码 `REJECTED_UNSAFE_GIT_CONFIG`(新增),exit 4,不写 HELD,stdout `reason` 列出命中的键名(不回显值)。
`--get-regexp` 无命中时返回 1 且无输出,这种情况视为通过。键名大小写不敏感。

- `url.*.insteadof`、`url.*.pushinsteadof`
- `core.sshcommand`、`core.fsmonitor`、`core.gitproxy`、`core.askpass`
- `credential.*`
- `filter.*.clean`、`filter.*.smudge`、`filter.*.process`
- `diff.external`、`diff.*.command`、`diff.*.textconv`
- `protocol.*.allow`

这份名单是纵深防御。即使名单不全,上面的环境变量与 `-c` 覆盖仍然生效。
该检查分别在三处执行:第 5 步对 src_clean,第 7 步对三份副本,第 11 步对主副本;第 12、13 步再各复查一次。

**推送命令:**

```
git -C <主副本> <上述 -c 覆盖> push --porcelain --no-verify --no-follow-tags --recurse-submodules=no \
    <remote> +<derived>:<sandbox ref>
```

- 除这一条 refspec 外,不得推送任何 ref。
- 上述环境、覆盖与检查都是硬要求,不依赖仓库配置。
- 强制推送(`+`)只用于 sandbox ref。

### 4.5 崩溃窗口与重跑

| 崩溃发生在 | 重跑时的状态 | 重跑行为 |
|---|---|---|
| 写 POLICY 后、写 DERIVE 前的任何时点 | 该 round 已有 POLICY | 三项比较相同,不追加,继续 |
| hook 返回后、缓存行提交前 | 无缓存行、无 DERIVE | `generate` 照传,**会再调用一次 hook,得到不同的 Change-Id**;只有提交进缓存行的那个会被使用。前一次的值从未落库、从未推送,Gerrit 侧仍只有一个 change |
| 缓存行提交后、DERIVE 前 | 有缓存行、无 DERIVE | 缓存命中,返回同一 Change-Id(不调用 hook);写 DERIVE |
| DERIVE 后、写 `SANDBOX_PUSHING` 前 | 有 DERIVE,状态为 `LOCAL_3ARCH_PASS` 或更早的允许值 | 复用四要素,派生结果与存量相等,继续推送 |
| `SANDBOX_PUSHING` 后、push 完成前 | 远端不是 derived | 重新推送 |
| push 成功后、PUSH 事件前 | 远端已是 derived | 第 13 步第 2 项补账 |
| push 失败后、PUSH(failed) 前 | 远端不是 derived,状态 `SANDBOX_PUSHING` | 重新推送 |
| PUSH(failed) 后、`SANDBOX_PUSH_FAILED` 前 | 同上 | 重新推送 |
| PUSH(ok) 后、`SANDBOX_PUSHED` 前 | 远端相同,PUSH ok 已有 | 只补 `SANDBOX_PUSHED` |

全程只会有一条 DERIVE、一行缓存、一个被推送的 Change-Id。

### 4.6 保护标记

P5 不调用任何释放 API。成功后三份副本的保护标记全部保持(DoD 断言)。

---

## 5. 移交加固项

1. **日期校验**(`derive_commit` 与 `campaign_state._validate_derive` 共用同一个函数):
   - `COMMIT_DATE_RE` 加 `re.ASCII`;
   - 正则通过后,把末尾 `Z` 替换为 `+00:00`,再交给 `datetime.fromisoformat` 解析。项目要求 Python ≥3.10,而 3.10 的 `fromisoformat` 不接受 `Z`,所以这一步不能省;
   - 解析失败(如 13 月、2 月 30 日)即拒绝。
2. **真实 hook 测试**:配置或 hook 文件不存在时 skip;sha256 不符时 `pytest.fail`。
3. **edit_spec 发布的持久性**(`campaign_repair_step._materialize_canonical_edit_spec`)。
   该函数有两个调用点:canonical 路径在 `create_round` 之前,`out/round_N/edit_spec.json` 在 `create_round` 之后、计费之前。
   加固规则:
   - 三条成功路径(新建并 link、目标已存在、link 时遇 `FileExistsError`)都必须在 hash 校验通过后,
     用 `os.open(parent, O_RDONLY | O_DIRECTORY)` 对父目录 fsync,完成后才返回;
   - `os.link` 抛出 `FileExistsError` 以外的 `OSError`(如 EPERM、EXDEV、ENOTSUP),或父目录 fsync 失败,都转为 `WORKSPACE_FS_UNSUPPORTED`,exit 5;
   - canonical 发布失败:不建 round、不计费。build 副本发布失败:round 行已存在但不计费,重跑安全(已存在的文件走 hash 比对后再 fsync,round 行按既有幂等语义比对)。
4. **DERIVE 不可变字段补 `committer_identity`**:写入侧 `_validate_immutable_derive_fields` 与读取侧 gate_view 用同一字段集(见 §3)。

---

## 6. 验收用例(DoD)

**总纲**:
- 第 2–5 节的每条规则至少有一条用例,在该规则被删除或放宽后会转红;
- 收口文档给出"规则条目 ↔ 用例编号"的双向映射表。

**测试环境**:临时目录内建真实 git 仓库作为 src_clean 与三份副本,用本地裸仓库作远端(`gerrit_ssh_base` 设为其父目录的绝对路径),使用真实 state DB。只有标注"桩"的用例使用替身。

### 6.1 suppress_policy

1. **token 边界表**:断言识别出的 token 文本。
   - 应识别:`-Wno-x\`、`'-Wno-x'`、`"-Wno-x"`、`${FLAGS}-Wno-x`、`-Wno-x,-Wno-y`、`$<$<BOOL:1>:-Wno-x>`、`-Wno-#pragma-messages`;
   - 不应识别:`XX-Wno-x`。
2. **2.4 每个 kind 的正例与反例**,其中必须包括:
   - `-Wno-error=foo` 判 `wno_error_flag`,不是 `wno_error_all`;
   - `-Wno-error=all`、`-Wno-error=extra` 判 `wno_wholesale`(forbidden);
   - `target_compile_options(t PRIVATE -Wno-error=unused-variable)` 判 suppress;
   - `#pragma GCC diagnostic warning "-Wunused"` 判 `pragma_suppress`;
   - `_Pragma("GCC diagnostic ignored \"-Wunused-variable\"")` 判 `pragma_suppress`;
   - 续行的 `#pragma clang diagnostic ignored \` 加换行加 `"-Wx"` 判 `pragma_suppress`;
   - `#pragma GCC diagnostic ignored "-Wall"`、`#pragma GCC system_header`、`_Pragma("GCC system_header")` 判 `pragma_wholesale`;
   - 经宏包装的 `_Pragma(STR(...))`、出现 `__pragma(...)`、无引号的 diagnostic pragma、参数含八进制转义的 `_Pragma("clang diagnostic ignored \42-Wunused\42")`,判 `pragma_unparsed`;
   - `_Pragma("once")` 等无关 pragma 不产生 hit;
   - 字符串字面量与注释中的 `#pragma`、`-Wno-x` 都不计;
   - `#pragma GCC diagnostic push/pop/error` 不产生 hit。
3. **2.5 每行至少一例**,其中必须包括:
   - `target_compile_options(t PRIVATE -Wno-x)` 与 `target_compile_options(${T} PRIVATE -Wno-x)` 允许;
   - `PUBLIC`、`INTERFACE` 禁止;
   - 混合段:`PRIVATE -O2 PUBLIC -Wno-x` 禁止,`PUBLIC -O2 PRIVATE -Wno-x` 允许,`PRIVATE -O2 INTERFACE -Wno-x` 禁止;
   - 带定界符的段关键字按值识别:`PRIVATE -O2 "PUBLIC" -Wno-x` 禁止,`PRIVATE -O2 [=[INTERFACE]=] -Wno-x` 禁止,`"PRIVATE" -Wno-x` 允许;
   - 段归属无法确定:`PRIVATE ${MY_FLAGS} -Wno-x` 与 `PRIVATE ${P}-Wno-x` 禁止;`PRIVATE $<$<C_COMPILER_ID:Clang>:-Wno-x>` 允许;
   - 生成器表达式内的 token;
   - 引号参数:`target_compile_options(t PRIVATE "-Wno-x")` 允许,`add_compile_options("-Wno-x")` 禁止;
   - 括号参数内的 token;
   - 行注释、块注释(含 `#[==[ … ]==]`)中的 token 不计;
   - 命令跨多行且 edit 只改其中一行;
   - automake 中 `foo_CFLAGS =`、`foo_CFLAGS +=`、`foo_CFLAGS :=` 允许,`AM_CFLAGS` 禁止,续行;
   - `doc` 类:同一 edit_spec 改一个 `.c`(无抑制)与一个 `README.md`(新增一句含 `-Wno-unused` 的说明)→ allowed、无 hit;同样文本写进 `foo.mk` → forbidden;写进 `notes.txt` → forbidden(`.txt` 不属于 doc);
   - spec 一律禁止。
4. **2.6 比较规则的退化守卫**:规则退化回按片段计数时,以下六例都必须变红:前五例会漏检,第六例会误杀。
   - 等数迁移:`target_compile_options(t PRIVATE -Wno-foo)` → `add_compile_options(-Wno-foo)`,forbidden;
   - 只把 `PRIVATE` 改为 `PUBLIC`,forbidden,`edit_index` 指向该 edit;
   - 拼接:原文 `add_compile_options(-Werror)`,edit 只把 `error` 改为 `no-error`,产生 `wno_error_all` 与 `werror_removed`;
   - 两个相邻 edit 合成 `-Wno-foo`,产生 hit;
   - 注释转活动:`# -Wno-foo` → `add_compile_options(-Wno-foo)`,forbidden;
   - 同文件内重排 `-Werror`(同作用域),allowed。
5. **2.6 其余规则**:
   - 跨文件抵消:`strict/CMakeLists.txt` 去掉 `add_compile_options(-Werror)`,同时 `other/CMakeLists.txt` 新增同样一行 → forbidden(规则退化回合计比较时必须变红);
   - 测试声明从一个 CMakeLists 搬到另一个 → forbidden;
   - `-Werror` 从全局移入单 target,forbidden;
   - `-Werror` 从单 target 移到同文件的全局,allowed;从 target A 移到全局、同时删掉 target B 的,forbidden(非全局减少 2 大于全局增加 1);
   - 只删 `#pragma GCC diagnostic pop` → forbidden(`pragma_pop_removed`);把 push、ignored、pop 整段一起删除 → allowed;
   - `add_test(real COMMAND real)` 改为 `add_test(dummy COMMAND true)`,forbidden;
   - 只重命名 target,forbidden;
   - 注释中的伪 `add_executable` 不计;
   - `pure_deletion` 正例与反例。
6. **原样保留**:已有的全局 `-Wno-x` 原样保留,同一 edit 改了它旁边的代码,不产生 hit。
7. **四步序 × source_kind**:
   - 无抑制的 T1 → `cherry_pick`;无抑制的 generated → `code`;
   - 有允许抑制的 T1 → `suppress`;
   - source_kind=suppress 但内容无抑制 → `suppress`;
   - forbidden 的 T1 → forbidden,final 为 None。
8. **`PolicyInputError`**:old 找不到、路径逃逸、非法 source_kind。
9. **CLI 端到端**:allowed 与 forbidden 各一例,stdout 与 `asdict(evaluate(...))` 逐字段相等;exit 码 0、4、2 各一例。
10. **确定性**:同一输入调用两次结果相等;打乱 `edits[]` 顺序后,除 `edit_index` 外结果相等;edit 改变长度导致后续位置偏移时,判定不变。
11. **P5-C2-02 hit 输出形状**:`pure_deletion`、`werror_removed`、`pragma_pop_removed`、`target_removed` 的 kind、token、scope、count 逐字段符合该裁定;`werror_removed` 的 count 至少覆盖 `g<0` 与 `n>g≥0` 两种情形。

### 6.2 gate_view 与只读查询

1. **REPRODUCE 聚合**:
   - primary=matched、secondary 后写 baseline_pass → True;
   - primary 不是 matched、secondary 后写 matched → False;
   - 缺一个 arch → False;
   - `reproduce_by_arch` 内容正确。
2. **PUSH** 按 ref_class 分别取最新。**POLICY、DERIVE、KB、REVIEW** 各取最新:构造时间戳顺序与 event_id 顺序相反的数据,断言按 event_id 取。
3. **qb_result**:旧请求有 RESULT、最新请求无 RESULT 时为 None;同一请求内多条 RESULT 取 event_id 最大的。
4. **DERIVE 不可变字段跨行冲突**:五个字段各一例(含 `committer_identity`),均抛 `StateInconsistent`。写入侧:第二条 DERIVE 只改 `committer_identity` 时 `append_event` 拒绝。
5. **一致快照**:在 gate_view 的两次查询之间用另一连接追加事件(桩:在内部查询原语之间插入回调),返回结果仍来自同一快照。
6. **边界**:无事件的 unit 各字段为 None;unit 不存在抛 `StateInconsistent`。
7. **`latest_policy_for_round`** 只取对应 round 的记录;`lookup_change_id` 命中与未命中各一例,且不写库。

### 6.3 sandbox-submit 端到端

**每例都断言**:exit 码、stdout 快照、state DB 增量(逐条列出状态行与事件行,HELD 行含 `arch_norm`)、远端 ref 的前后值、push 与 hook 子进程的调用次数(用调用计数包装,不改变行为)。

1. **正常路径**:
   - exit 0,action=`pushed`;远端 sandbox ref 等于 derived,`derived^{tree}` 等于 verified_tree_sha;
   - commit message 与 `subject + "\n\nChange-Id: I…\n"` 逐字节相等;
   - 状态依次为 REPAIR_ROUND_RUNNING → LOCAL_3ARCH_PASS → SANDBOX_PUSHING → SANDBOX_PUSHED;
   - 事件依次为 POLICY、DERIVE、PUSH;
   - 追加 DERIVE 时缓存行已存在(包装 `append_event` 检查);
   - 三份副本的保护标记仍在;远端除 sandbox ref 外无任何 ref 变化。
2. **幂等重跑**:exit 0,action=`already_pushed`,state DB 零增量,push 与 hook 调用 0 次。
3. **补账两例**:
   - 远端已是 derived 但缺 PUSH 事件,补 PUSH 与状态;
   - 有 PUSH(ok) 但缺 `SANDBOX_PUSHED`,只补状态。
4. **远端被改后重跑**:把远端 ref 改为别的 commit,重跑后强制推回;新增一条 `SANDBOX_PUSHING`、一条 PUSH(ok)、一条 `SANDBOX_PUSHED`;Change-Id 与 derived 不变。
5. **P2 移交项**:首次成功后删掉 `campaign_change_ids` 中该行,再重跑 → exit 4,HELD(`state_inconsistent`, primary arch),hook 调用 0 次,push 调用 0 次,远端 ref 不变。
6. **参数**(exit 2,零写入):
   - 首次缺 `--message-brief`、缺 `--edit-source-kind`;
   - brief 含换行、含制表符、超过 100;
   - 非法 `--edit-source-kind`;
   - 只给 2 个 id、id 重复。
7. **分支名反例**(exit 2,`INVALID_BRANCH_NAME`):`master`、`refs/heads/sandbox/a`、`sandbox/`、`sandbox//a`、`sandbox/a/../b`、`sandbox/a b`、`sandbox/a.lock`、`sandbox/a@{1}`。
8. **选定错误**(exit 4,零写入):
   - 某 id 无链接;三个 id 分属两个 unit;分属两个 round;
   - 不是最新 round,错误码为 `REJECTED_ROUND_SUPERSEDED`;
   - 状态为 HELD、`KB_APPENDED`、`DENIED`。
9. **加锁**:
   - 用 repair-step 的路径派生函数算出四条锁路径,逐一占用 → exit 4 `CAMPAIGN_STATE_BUSY`,零写入;
   - 持有某 arch 的 `.repair_step.lock` 时运行 sandbox-submit 得 busy;反之 sandbox-submit 持锁期间运行 repair-step 得 busy;
   - 加锁前后链接被改(桩:在加锁后、重查前插入回调),锁内重查以新数据为准。
10. **聚合不符**:改一条记录的 `base_commit`;使记录 branch 与 unit 不一致 → HELD(`aggregate_mismatch`, None),无 POLICY、无 DERIVE、无 push。
11. **重绑定**:验证后改写 round 的 edit_spec 文件 → HELD(`edit_spec_rebind_mismatch`),`evaluate` 调用 0 次。
12. **forbidden 重查**:用一份能过构建但含 `add_compile_options(-Wno-foo)` 的 round → 写入 POLICY(forbidden)与 HELD(`suppress_policy_recheck`),hook、derive、push 调用均为 0。
13. **POLICY 不一致**:存量 POLICY 的 `fix_strategy_final` 被改 → HELD(`state_inconsistent`, primary arch),stdout 带两个 rules_version。
14. **副本现场**(第 3、7 步):
    - 非主 arch 副本有已跟踪改动、有暂存改动 → HELD(`worktree_dirty`),arch 为该副本;
    - 非主 arch 副本 HEAD 树不等、保护标记被删 → HELD(`verification_mismatch`),arch 为该副本;
    - 两份副本同时不符,arch 取 ARCH_ORDER 中的第一个,另一个出现在 `reason` 中。
15. **副本缺失**:删掉一份非主 arch 副本 → `WORKTREE_LOST`,exit 4,`surviving_worktrees` 列出另外两份,无 HELD、无 push。
16. **src_clean 不符**:HEAD 不对、origin 不对、标记不对、有改动 → exit 4 `REJECTED_IDENTITY_MISMATCH`,无 HELD。
17. **TOCTOU**(桩:在第 11 步之后、第 12 步之前插入回调,依次改动下列一项):
    - 某记录的 `branch`、`gbs_conf_sha256` → HELD(`aggregate_mismatch`);
    - 链接归属、`latest_round`(插入新 round)、unit 行字段、最新状态、缓存行 → HELD(`state_inconsistent`);
    - 主副本已跟踪文件 → HELD(`worktree_dirty`);
    - round 文件 → HELD(`edit_spec_rebind_mismatch`);
    - src_clean HEAD → exit 4 `REJECTED_IDENTITY_MISMATCH`;
    - 主副本新增 `url.<x>.pushInsteadOf` → exit 4 `REJECTED_UNSAFE_GIT_CONFIG`;
    - 每例 push 调用都为 0。
    另一例:在第 12 步之后、第 13 步第 0 项之前把远端 ref 改成别的 commit(桩)→ 最终远端等于 derived(强制推回),state DB 不出现"已推送但远端不符"的记录。
18. **A12 篡改**:用原始 SQL 插入一条 DERIVE,`derived_commit_sha` 不同而不可变字段相同 → 重跑 HELD(`state_inconsistent`),无 push。
19. **hook 失败**:配置的 sha256 不对 → exit 4 `CHANGE_ID_HOOK_FAILED`,无 HELD、无缓存行、无 DERIVE、无 push;改正后重跑成功。
20. **推送失败与远端读取**:
    - 远端路径不可写 → PUSH(failed) 与 `SANDBOX_PUSH_FAILED`,exit 5;恢复后重跑成功,Change-Id 不变;
    - 远端路径不存在(ls-remote 失败)→ exit 5,push 调用 0 次;
    - ls-remote 超时、push 超时(桩)→ exit 5;
    - 推送成功但推后 ls-remote 失败(桩)→ exit 5,重跑走补账。
21. **隐式推送路径**,每例断言远端只有 sandbox ref 改变:
    - 主副本 `.git/config` 设 `push.followTags=true`,并给 derived 打注解标签 → 远端无任何 `refs/tags/*`;
    - 带子模块的夹具,设 `push.recurseSubmodules=on-demand` → 子模块远端零变化;
    - 主副本装一个会写标记文件的 `pre-push` hook → 标记文件不存在;
    - 主副本配置 `url.<x>.insteadOf` 或 `url.<x>.pushInsteadOf` 改写远端 → exit 4 `REJECTED_UNSAFE_GIT_CONFIG`,push 调用 0 次,**两个裸仓库的 ref 都不变**;
    - 主副本配置一个名字与 `<remote>` 逐字相同的具名远端 → exit 4 `REJECTED_REF_NOT_ALLOWED`;
    - 主副本配置 `core.sshCommand`、`core.fsmonitor` 为写标记文件的脚本 → 流程被 `REJECTED_UNSAFE_GIT_CONFIG` 拒绝,标记文件不存在;
    - 把上述配置检查用包装跳过后再跑(退化守卫):标记文件仍不存在,证明 4.4 的环境变量与 `-c` 覆盖本身有效;
    - src_clean 配置 `filter.x.clean` 并用 `.gitattributes` 绑定 → `REJECTED_UNSAFE_GIT_CONFIG`。
22. **崩溃窗口**:4.5 表中九个时点各注入一次异常(桩),重跑后收敛到 `SANDBOX_PUSHED`,全程一条 DERIVE、一行缓存、一个被推送的 Change-Id。
    对"hook 返回后、缓存行提交前"一例另断言:hook 调用 2 次,缓存行恰一行,commit message 中的 Change-Id 等于缓存行的值。
23. **环境隔离**:环境中设置 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_OBJECT_DIRECTORY` 为敌对值,结果与干净环境相同。
24. **重跑传入不同 brief 与 source kind**:采用存量值,`reused` 两项为 true,derived 不变。
25. **HELD 退化守卫**:用包装把 `arch_norm` 强制置 None 后调用 `append_status` 写 `state_inconsistent`,断言抛 `PayloadSchemaError`。
    同时断言 sandbox-submit 的 HELD 路径不会走到这个分支,即第 5、13、14、17 例的 HELD 行都已真正提交。
26. **stdout 快照**:8 种 action 各一份。

### 6.4 移交加固

1. **日期**(`derive` 与 `_validate_derive` 两处都要覆盖):
   - 全角数字、阿拉伯-印度数字被拒;
   - `2026-13-01T00:00:00Z`、`2026-02-30T00:00:00+00:00` 被拒;
   - `…Z` 与 `…+08:00` 被接受。
2. **真实 hook 测试**:hash 不符为 failed;配置缺失、文件缺失为 skipped。本机实跑须有 passed 原文。
3. **edit_spec 发布**:
   - 包装 `os.fsync`,对三条成功路径分别断言父目录 fd 被 fsync 过;
   - 在 canonical 调用点注入 `os.link` 抛 EPERM、EXDEV、ENOTSUP,以及父目录 fsync 抛错(桩)→ exit 5 `WORKSPACE_FS_UNSUPPORTED`,无 round 行、无 BUILD_INVOCATION;
   - 在 build 副本调用点做同样注入 → exit 5,round 行存在、无 BUILD_INVOCATION;
   - 第一次父目录 fsync 失败、重跑时仍失败 → 继续拒绝;
   - 恢复后重跑,两处都成功。
4. **DERIVE 写入侧**对 `committer_identity` 的不可变检查,与 6.2 第 4 条共用。

### 6.5 通用门禁

全仓回归、mypy、ruff、lint-imports,以及相对 `cd7f8dd` 无新增失败的全部既有设计门禁,远端 CI 通过。
`carried-over-issues.md` 的三项保持原状,不计为新增失败。

---

## 7. 提交计划

| 提交 | 内容 |
|---|---|
| C0 | 附录 A 同步进 design.md(升 v1.5.20);本文入库为 `docs/clang-fix-campaign/p5-sandbox-submit-design-v1.x-FROZEN.md`;若签名审计覆盖这些函数,更新受影响的设计门禁夹具 |
| C1 | 第 5 节四项加固 + 6.4 |
| C2 | suppress_policy + CLI + 6.1 |
| C3 | gate_view、`latest_policy_for_round`、`lookup_change_id` + 6.2 |
| C4 | `_unit_hash` 与 src_clean 校验的共用化(行为不变)、4.4 的 git 统一环境与配置安全检查、sandbox_submit + CLI + 6.3 |
| C5 | 收口文档 `review/p5-sandbox-submit-closeout.md`(READY_FOR_REVIEW,含规则 ↔ 用例映射表与已知限制)、stage19 progress、INDEX |

- 每个提交单独跑通 6.5 的门禁后再推送。
- 实现中发现会改变行为或安全边界的缺口,停下报告;不改变两者的缺口,记入 progress 后继续。

---

## 附录 A:design.md 同步(C0 照录)

### A.1 新增 §4.4(追加在 §4.3 之后,原文照录)

> ### 4.4 v1.5.20 修订:P2–P5 落地裁定
>
> 本节汇总 P2、P3、P4 收口时的裁定,以及 P5 设计引入的契约变化。
> P5 模块(suppress_policy、gate_view、sandbox_submit)的权威契约见 `p5-sandbox-submit-design-v1.x-FROZEN.md`,
> 与本文其它章节冲突时以该文件为准。
>
> **submission_identity(P2)**
> 1. `generate_change_id_via_hook` 与 `get_or_create_change_id` 入口先校验 submission_key 为 64 位小写十六进制,
>    分别抛 `ChangeIdHookError` / `StateInconsistent`;在创建临时目录或调用 generate 之前拒绝。
> 2. 缓存未命中后先确认 campaign_unit_key 存在,不存在即 `StateInconsistent`,不得调用 generate;生成后事务内复查沿用此规则。
> 3. 首行匹配 `^[a-z]+! ` 的消息在调用 hook 前拒绝(Gerrit hook 对 fixup!/squash! 类提交不生成 Change-Id);首行大写不在拒绝范围。
>    `gerrit.createChangeId` 保持 `true`,不改为 `always`。
> 4. 已知边界:DERIVE 检查只针对传入的 unit;跨 unit 带外删除共享缓存行不在保护范围。
>
> **aggregate(P3)**
> 5. 绑定字段增加 `branch`,`AggregateResult` 同步增加该字段;任一不符时全部绑定字段为 None。
> 6. 七个绑定字段在每条记录上 strip 后必须非空,空值逐条进入 reasons;相等性比较原值,不做 hex 格式校验。
>
> **derive_commit(P4)**
> 7. author_date / committer_date 必须匹配 `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$`(`re.ASCII`),
>    且能解析为真实日期(`Z` 换成 `+00:00` 后用 `fromisoformat` 解析);不符即拒,不运行 git。DERIVE 事件写入使用同一校验。git 环境固定 `TZ=UTC`。
> 8. 仓库查找上界为 `worktree.resolve().parent`,传入目录不是仓库根时报错,不得写入上层仓库。
> 9. DERIVE 首写不可变字段为 message_brief、author_identity、committer_identity、author_date、committer_date(补入 committer_identity)。
>
> **sandbox-submit(P5)**
> 10. 新增可选参数 `--edit-source-kind`,该 round 无 POLICY 时必填;已有存量时复用存量。
> 11. commit message 固定为 `Fix build error for clang compiler: <brief>`、一个空行、`Change-Id: <id>` 三部分,不加其它 trailer;
>     溯源信息只保存在 state DB 与 KB 记录中。
> 12. `fix_strategy_initial` 由 edit_source_kind 固定映射:t1_cherry_pick→cherry_pick,generated→code,suppress→suppress。
>     POLICY 事件增加 `rules_version` 字段,规则升级后已有未推送单元若结论变化即挂起,须人工重置。
> 13. 调用方选错记录(未链接、跨 unit、跨 round、非最新 round、状态不允许)只拒绝,不写 HELD;选定之后的绑定异常按 §4.2 拒绝矩阵进入 HELD。
>     HELD 行的 arch_norm 按 P5 设计文件第 4.2 节 的规则填写。
> 14. 推送只更新显式给出的那一条 sandbox ref。P5 的所有 git 调用:禁用系统与全局配置,无条件设 `GIT_SSH_COMMAND`,限定传输协议为 file 与 ssh,
>     用 `-c` 覆盖 hooksPath、fsmonitor、askPass、credential.helper、followTags、recurseSubmodules、gpgSign、pushOption;推送加 `--no-verify`。
>     仓库本地配置中出现 URL 改写或可执行命令类键时拒绝(名单见 P5 设计文件第 4.4 节)。
> 15. `toctou_recheck`、`check_push_ref` 的签名与返回结构、`gate_view` 的字段集与一致快照要求,以 P5 设计文件为准。
> 16. 新增错误码 `WORKSPACE_FS_UNSUPPORTED`:edit_spec 发布时 `os.link` 或父目录 fsync 不可用,exit 5。
>     canonical 发布失败不建 round、不计费;build 副本发布失败不计费。各成功路径都在返回前对父目录 fsync。
> 17. 新增错误码 `REJECTED_ROUND_SUPERSEDED`:sandbox-submit 传入的记录不属于该 unit 的最新 round。
> 18. `gerrit_ssh_base` 非 `ssh://` 时,campaign-preflight 必须报 `PREFLIGHT_FAILED`(本地路径只供测试)。
> 19. 新增错误码 `REJECTED_UNSAFE_GIT_CONFIG`:被检查仓库的本地配置含 URL 改写或可执行命令类键,exit 4,不写 HELD。
> 20. suppress policy 的全部计数规则逐文件比较,不允许跨文件抵消;合法的跨文件搬动须走人工。

### A.2 指引行(C0 在原位置插入一行,不改原文)

| 位置 | 插入内容 |
|---|---|
| §1.4 A5 末尾 | `(v1.5.20:commit message 格式以 §4.4 第 11 条为准。)` |
| §3.4 聚合绑定段末尾 | `(v1.5.20:绑定字段与非空要求以 §4.4 第 5–6 条为准。)` |
| §3.7 末尾 | `(v1.5.20:检测规则的可执行定义见 P5 设计文件第 2 节;计数逐文件比较,见 §4.4 第 20 条。)` |
| §4.1 sandbox-submit 块末尾 | `# v1.5.20:参数、流程、输出与退出码以 P5 设计文件第 4 节 为准(§4.4 第 10–14、17、19 条)` |
| §4.1 campaign-repair-step 第 2 步末尾 | `# v1.5.20:发布后父目录 fsync;link 不可用 → WORKSPACE_FS_UNSUPPORTED(§4.4 第 16 条)` |
| §4.1 campaign-preflight 检查项末尾 | `# v1.5.20:gerrit_ssh_base 须为 ssh://(§4.4 第 18 条)` |
| §4.2 submission_identity、aggregate、derive_commit、sandbox_submit、suppress_policy、campaign_state.gate_view 各签名块末尾 | `# v1.5.20:见 §4.4` |
| §4.3 错误码表 | 增加三行:`WORKSPACE_FS_UNSUPPORTED  edit_spec 发布所需的硬链接或目录 fsync 不可用(v1.5.20)`;`REJECTED_ROUND_SUPERSEDED  传入记录不属于最新 round(v1.5.20)`;`REJECTED_UNSAFE_GIT_CONFIG  仓库本地配置含 URL 改写或可执行命令类键(v1.5.20)` |
| §7 Phase 4.5 范围末尾 | `(v1.5.20:suppress_policy 与 gate_view 两项未在本阶段交付,已移交 P5 实施,DoD 条目随之移交,见 §4.4 与 P5 设计文件第 0.1 节。)` |
| §7 Phase 5 范围末尾 | `(v1.5.20:并入 P4.5 未交付的 suppress_policy 与 gate_view,见 P5 设计文件第 0.1 节。)` |
| §0 元信息版本行 | 版本号改为 v1.5.20-FROZEN,变更记录追加一行指向 §4.4 |

C0 完成后运行既有设计文档检查器,零问题方可继续。

---

## 附录 B:v1.0 → v1.1 修改记录(第一轮评审;表中步骤编号为 v1.1 编号)

按严重程度排列。"来源"中:GPT = ChatGPT,CC = Claude Code,K = Kimi。

| 级别 | 修改 | 来源 | 采纳说明 |
|---|---|---|---|
| 阻断 | 抑制判定从"按 edit 片段计数"改为"整文件按 (kind, token, scope) 键比较",堵住拼接、等数迁移、注释转活动、PRIVATE→PUBLIC 四种绕过,并消除同作用域重排 `-Werror` 的误杀(§2.2、2.6、2.7) | GPT、CC、K | 采用 CC 的按键整文件比较框架;`werror_removed` 改为全部被编辑文件合计并带 scope,兼顾 CC 指出的跨文件搬动与 GPT 的收窄问题;hit 定位用命令范围相交,解决只改关键字时的定位 |
| 阻断 | `target_compile_options` 按 PRIVATE/PUBLIC/INTERFACE 关键字分段,实例归属最近的段(§2.5) | GPT | 采用 GPT 方案 |
| 阻断 | `_Pragma`、`warning` 级别、续行、宏包装与 `__pragma` 纳入 pragma 判定;无法解析即 forbidden(§2.3、2.4) | GPT、CC | 合并两家方案;另加 `#pragma … system_header` 为整类抑制(自补) |
| 阻断 | 推送禁用系统与全局配置,`-c` 覆盖 followTags、recurseSubmodules、hooksPath、gpgSign、pushOption,加 `--no-verify --no-follow-tags --recurse-submodules=no`,并校验远端地址未被 insteadOf 改写(§4.4、第 11 步) | GPT、CC | 两家方案合并;`pre-push` hook 与 insteadOf 两条为自补;不采用 CC 的 `--atomic`(只有一条 refspec,无收益且 P12 的 Gerrit 版本兼容性未知) |
| 阻断 | HELD 行按条件来源填写 arch_norm,stdout 增加 `held` 字段(§4.2) | CC(阻断)、GPT(重要) | 采用 CC 的分类;多份副本同时不符按 ARCH_ORDER 取第一个(两家一致) |
| 重要 | 删去第 7 步写 `SANDBOX_PUSHING`,改为只在真正推送前写;已推送路径零写入可达;补账规则拆成两项(§4.3 第 14 步) | GPT | 采用 GPT 方案;崩溃窗口表同步 |
| 重要 | TOCTOU 改为九项全量重校验:选定、unit 行、完整聚合、记录、副本、round 文件、DERIVE/POLICY/缓存、src_clean 与 policy 重算、派生重算(§4.3 第 13 步) | GPT、CC、K | 合并三家;src_clean 不符维持"不冻结"以与第 5 步一致;新增只读 `lookup_change_id` |
| 重要 | unit_hash 固定为复用 repair-step 的 `_unit_hash`;锁内 unit_key 变化按 busy 退出(§1、第 1 步) | CC | 采用 CC 方案 |
| 重要 | `-Wno-error=` 加整类名归 forbidden,WHOLESALE_NAMES 三处共用(§1、2.4) | CC、K | 采用 |
| 重要 | `${VAR}` 目标名不再判 forbidden(§2.5) | CC | 采用;scope 仍为 `target_private`,不另设枚举值(作用域判据与目标是谁无关) |
| 重要 | `target_removed` 改为按 (命令, 名称) 比较,名称原文字面比较(§2.6) | GPT | 采用;名称含变量时按原文比较,未改动的声明自然相等,无需"无法确定即拒绝" |
| 重要 | gate_view 在同一读事务内完成,不调用另开连接的公共函数(§3) | GPT | 采用 |
| 重要 | edit_spec 发布:三条成功路径都要父目录 fsync;如实区分两个调用点的失败语义(§5 第 3 条、A.1 第 16 条) | GPT、CC | 采用 CC 的"不改调用顺序、如实表述",加上 GPT 的"已存在与 EEXIST 路径也 fsync" |
| 重要 | 验收用例按上述修改全面补齐,增加总纲与规则 ↔ 用例映射表要求;反转 v1.0 中"warning 不算抑制"的错误反例(§6) | CC、GPT、K | 采用 |
| 次要 | token 边界改为正则定义(§2.3.2) | CC | 采用其思路,但改写了正则:CC 原方案把 `:` 放进名字字符集,会使 `$<…:-Wno-x>` 识别失败 |
| 次要 | 明确引号参数与括号参数内的 token 照常识别,注释内不计;一般化块注释的 `=` 层级(§2.3) | CC、GPT、K | 采用 |
| 次要 | 崩溃窗口表补齐为九行,写明"hook 返回后、缓存提交前"重跑会产生第二个未使用的值(§4.5) | CC、GPT | 采用 |
| 次要 | 非法 `--edit-source-kind` 在参数阶段拒绝(第 0 步) | K | 采用 |
| 次要 | 附录 A 补 §7 Phase 4.5 指引行、preflight 指引行 | CC | 采用 |
| 建议 | "不是最新 round"单列错误码 `REJECTED_ROUND_SUPERSEDED` | CC | 采用 |
| 建议 | POLICY 事件记录 `rules_version`;规则升级导致的结论变化仍挂起,收口文档写明须人工重置 | K | 采用"记录版本 + 写明"的做法;不放宽比较 |
| 建议 | `gerrit_ssh_base` 本地路径的机械约束:stdout 回显、preflight 拒绝 | CC | 采用 |
| 建议 | 纯删行修复须走人工,写入已知限制 | K | 采用 |
| 不采纳 | `reproduced` 要求 secondary 不为 baseline_pass | K | 与 design.md §3.6 冻结口径冲突:secondary 为 baseline_pass 是合法状态。改为在 §3 写明 secondary outcome 不限,并补用例 |
| 不采纳 | 保护标记校验需从 `_rebuild_pass_convergence` 提取 | K | 共用 API 已存在:`tizen_ci_shared.workspace.is_protected`(`workspace/__init__.py:144`) |
| 不采纳 | 未配对的 `#pragma … diagnostic push` 判 forbidden | CC | push 本身不抑制;其后的 `ignored`/`warning` 已按 `pragma_suppress` 计入,作用域限于当前翻译单元,不构成全局抑制 |

## 附录 C:v1.1 → v1.2 修改记录(第二轮评审)

三家第二轮结论均为"修改后可冻结";第一轮问题三家确认全部修复,对附录 B 中三条"不采纳"均表示同意。
按严重程度排列。"来源"中:GPT = ChatGPT,CC = Claude Code,K = Kimi。

| 级别 | 修改 | 来源 | 采纳说明 |
|---|---|---|---|
| 阻断 | `pushInsteadOf` 只在 push 时生效,`ls-remote --get-url` 查不出来,commit 会被推进另一个仓库(GPT、CC 均已实测)。改为直接检查配置键:任何 `url.*.insteadOf` / `url.*.pushInsteadOf` 一律拒绝;另查同名具名远端;在 TOCTOU 和推送前各复查一次(第 11–13 步、4.4) | GPT(阻断)、CC、K(重要) | 合并三家:采用 CC 的"直接查配置键",加上 GPT 的"具名远端"与"推送前复查" |
| 阻断 | 带引号或括号的 `"PUBLIC"` / `[=[INTERFACE]=]` 被当成普通参数,抑制被错判为 PRIVATE。段关键字改为按参数值识别;从第 2 个参数到实例所在参数之间含变量引用的,判为段归属无法确定(2.3、2.5) | GPT | 采用;"变量引用"的范围由我限定为 `${`、`$ENV{`、`$CACHE{`。生成器表达式不可能成为段关键字,不计入 |
| 阻断 | `_Pragma("GCC system_header")` 漏检(GPT 已用 GCC 实测)。两种 pragma 来源先统一得到 pragma 文本,再套用同一套语法;`_Pragma` 先按 C 标准去字符串化,含其它转义的视为无法解析(2.4) | GPT(阻断)、CC N6(建议) | 合并:统一语法入口(GPT),转义变体归 `pragma_unparsed`(CC) |
| 重要 | 仓库本地的 `core.sshCommand`、`core.fsmonitor` 能在 git 调用中执行任意命令(CC 已实测)。改为:4.4 的统一环境用于 P5 中所有 git 调用;无条件设 `GIT_SSH_COMMAND`;`-c` 覆盖增加 fsmonitor、askPass、credential.helper;`diff` 加 `--no-ext-diff --no-textconv`;限定传输协议;新增配置安全检查名单与错误码 `REJECTED_UNSAFE_GIT_CONFIG`,不写 HELD | CC | 采用 CC 的覆盖方案;filter、diff 驱动、protocol 三类名单项与 `GIT_ALLOW_PROTOCOL` 为自补(同一类本地配置执行面) |
| 重要 | 跨文件合计会让一个文件里的删除被另一文件里的新增抵消。`werror_removed`、`target_removed` 改为逐文件比较(2.6) | GPT(重要)、K(建议) | 采用 GPT 的逐文件方案;代价是合法的跨文件搬动须走人工,已写入已知限制 |
| 次要 | 远端读取原本排在 TOCTOU 之前,补账可能依据过期读数。改为先 TOCTOU、再读远端、再记账与推送(第 12、13 步) | CC | 采用 |
| 次要 | 把 `-Werror` 从单 target 放大到同文件全局被误杀。同一文件内,全局增加量可以抵消非全局减少量(2.6) | CC | 采用,并按上一条改为逐文件生效 |
| 次要 | 文档文件中提到 `-Wno-…` 会被判 forbidden。新增 `doc` 类,不做识别(2.3) | CC | 采用,但 `.txt` 不归入 doc:`.txt` 可能被 `file(READ)` 读成编译选项,保守处理 |
| 建议 | 只删 `#pragma … pop` 会把已有抑制扩大到文件末尾。新增 `pragma_pop_removed`;push、ignored、pop 整段一起删除不命中(2.4、2.6) | CC | 采用 |
| 建议 | automake 赋值运算符补 `:=`、`?=`(2.5) | CC | 采用 |
| 建议 | §4.2 对 `_ARCH_SCOPED_HELD_REASONS` 的描述改为"P5 只用到其中两个",避免误解为常量全部成员 | CC | 采用 |
| 建议 | 新增调用在 edit 之外定义的抑制宏,不会被识别。写入已知限制 | K | 采用 |
| 建议 | 用例同步:第二轮各发现均有对应用例,包括退化守卫(跳过配置检查后标记文件仍不存在,证明环境覆盖本身有效) | 三家 | 采用 |

v1.1 → v1.2 之后不再安排第三轮评审:两轮已用满轻量流程的上限,第二轮各发现都局限在已重写的段落内,不涉及流程骨架。
