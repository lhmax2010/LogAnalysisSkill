# Explore Unavailable — source_context_unavailable 的探索决策树

`patch-suggest` 标 `source_context_unavailable`,意思是**它**没能把诊断指向的源码
喂给你,**不等于这个失败无法修复**。它在 context.md 里明说了:

> "Ask the outer assistant to open that file and inspect the reported line before
> generating a patch. Do not invent source content."

你就是那个 outer assistant。这份文档告诉你怎么接这个球。

## 0. 铁律

1. **不编造源码内容。** 没看到的代码不要猜。
2. **探索有刹车。** 每个 unit 最多 **10 次探索性工具调用**(`find`/`grep`/`ls`/`sed`
   等;**不计** formatter/build-verify/gerrit-submit)**或 10 分钟,先到者为准**。
   仍无明确、可解释、owned-source 的 repair hypothesis → 标 `needs_human`,
   写清卡在哪,继续下一个包。**不要无限探索。**
3. **探索完成后暂停。** 把推理过程 + 拟定的 edit_spec 展示给人,**等确认**才 build-verify。
   探索出的改法风险高于标准 patch-suggest 路径(见第 4 节反面教材)。
4. **安全门不因"人确认过"而跳过。** 探索出的 patch 同样要过 formatter + build-verify。
5. **上游 bug 不硬 workaround。** 如果根因是工具链/生成器的 bug,标 `needs_human`,
   报给上游。硬打补丁治标不治本,而且容易改坏。

## 1. 起点:读诊断

**先 guard**:
```
若 unit["evidence_packet"] 为 null,或文件不存在
→ 没有诊断可探索
→ 标 needs_human + missing_evidence,继续下一个包。不要猜。

若 unit["src_clean"] 为 null
→ 源码没 clone 成功,无从探索
→ 标 needs_human + missing_source。
```

guard 过了再读:
```python
ev = json.load(open(unit["evidence_packet"]))
p = ev["primary_error"]
file    = p["file"]        # 诊断指向的文件路径
line    = p["line"]
message = p["message"]
reasons = ev.get("degraded_reasons")   # 常见:['source_file_unavailable', ...]
```

`file` 的形态决定走哪个分支。

## 2. 决策树

### 分支 1:相对路径带 `../` → 路径归一化(通常可推进到 edit_spec)

**特征**:`file` 形如 `../src/bin/server/e_comp_wl.c`

**原因**:out-of-tree build,诊断路径相对于构建目录,不是源码根。
文件**在** repo 里,只是 patch-suggest 的 suffix search 匹配不上。
这是**假阴性**——不是"无法修",只是路径没归一化。

**处理(必须走完,不要停在泛泛建议)**:

1. **归一化找文件**:
   ```bash
   # 剥掉前导 ../,在 src_clean 里找
   find "<unit.src_clean>" -path "*<剥掉 ../ 后的路径>" -type f | head
   ```
   - 恰好 1 个 → 记下相对 src_clean 的路径,继续第 2 步。
   - 0 个或多个 → 转 `needs_human`,写清情况。

2. **打开文件看诊断行的实际代码**(`sed -n '<line-8>,<line+8>p' <找到的文件> | cat -A`)。
   **不要凭诊断消息猜代码。**

3. **拟定 edit_spec**(不是"给建议",是写出完整 edit_spec):
   按诊断类型:
   - **简单确定的改法**(格式符 `%zu→%u`、去 `std::move`、`|→||` 且已确认无副作用)
     → 直接写出 edit_spec。
   - **需要判断语义/副作用的改法** → 先做完判断(见下),判断清楚了照样写出 edit_spec;
     判断不了才转 `needs_human`。

4. **输出**:按第 3 节格式,给出**根因 + 改法 + 风险 + 完整 edit_spec**,
   然后**暂停等人确认**。**不要只给"建议 XXX",要给可以直接 build-verify 的 edit_spec。**

> **关键**:分支 1 的目标是**产出一个具体的 edit_spec 等人点头**,不是产出一句
> "建议确认操作数类型"。如果你能归一化找到文件 + 看到代码,就应该能拟定 edit_spec。
> 停在"建议"= 没做完探索。

**`|` → `||` 的副作用判断**(bitwise-instead-of-logical 专用):
`|` 不短路,`||` 短路。改 `||` 后,若左操作数为真会跳过右操作数。
→ 必须确认右操作数**无副作用**(纯读取,不改状态/不触发回调)才能安全改。
```bash
# 看右操作数里调用的函数定义
grep -rn "^<函数名>\b\|<函数名>(E_Client" "<unit.src_clean>/src/" | head
```
- 都是纯 getter(只读字段,EFL 的 `_get` 命名约定通常如此)→ 安全,写 edit_spec。
- 有副作用 → 不能简单改 `||`,转 `needs_human`。

**实例**:enlightenment 的 `../src/bin/server/e_comp_wl.c:814`
→ find 归一化到 `<src_clean>/src/bin/server/e_comp_wl.c`
→ 诊断行:`e_client_priv_want_focus_set(ec, e_client_priv_want_focus_get(ec) | (...))`
→ 右侧 `e_client_icccm_accepts_focus_get` / `e_client_override_get` 是纯 getter → 安全
→ 拟定 edit_spec:`|` → `||`
→ (实测)build-verify PASS ✓
→ **应该产出这个 edit_spec 等确认,而不是停在"建议确认操作数类型"。**

### 分支 2:路径含 `generated/` → 构建时生成的代码

**特征**:`file` 形如 `.../src/service_plugin/generated/hal_drm_stub_1.c`

**先确认它真的不在 repo 里**:
```bash
find "<unit.src_clean>" -name "<文件名>" | head
ls "<unit.src_clean>/<generated 的父目录>/"
```
repo 里没有 → 确认是构建时生成的。

**找出谁生成的**:
```bash
grep -nE "tidlc|generat|%build|%prep|codegen|protoc" \
    "<unit.src_clean>"/packaging/*.spec
grep -iE "tidlc|generat" "<unit.package_buildlog>" | head
```

**判断根因,三选一**:

#### 2a. 生成器本身有 bug → `needs_human` + `upstream_bug`,**不 workaround**

**典型信号**:
- 生成的代码引用了**自己没生成**的符号
- 错误类型是 `use of undeclared identifier`,且集中在 `generated/`
- 检查生成的代码:数组引用和函数定义**不成对**

**实例**:hal-api-drm / hal-api-hdcp 的 `tidlc`
→ 数组引用 `__rpc_port_stub_drm_method_<x>_privilege_checker`(18+ 个 method),
  但只为其中 5 个生成了函数定义 → `use of undeclared identifier`
→ 在 spec 里 sed 打补丁**看着能修,实际会改坏代码**(见第 4 节)
→ 正解是修 tidlc 或 `.tidl`,不是 patch 生成的代码
→ **标 needs_human,报上游**

#### 2b. 生成器输入(`.tidl`/`.proto`/schema)有问题 → 改输入

输入文件**在** repo 里(`include/*.tidl` 等)→ 可以改它 → 走标准安全门。

#### 2c. 确实需要生成后 post-process → 可以改 spec,但**必须限定范围**

`edit_spec` **可以改 `packaging/*.spec`**(已验证 `actual_changed_paths` 会含它)。

但 sed/正则**必须限定作用范围**,不能无差别替换。写之前先看生成的代码实际结构:

```bash
# 上一次 build 的产物(理解结构用)
find ~/GBS-ROOT*/local/BUILD-ROOTS/*/home/abuild/rpmbuild/BUILD/<pkg>-*/ \
     -name "<生成的文件名>" | head -1
```

> ⚠️ **上一次 BUILD 产物只用于理解结构,不得作为当前验证的输入。**
> 最终必须通过 build-verify 在本轮 verified copy 中重新生成并编译。

**暂停,给人看 sed 的精确作用范围,确认后才 build-verify。**

### 分支 3:诊断路径指向系统目录(`/usr/include/`)→ 先定位触发的编译单元,再决定

**特征**:`file` 形如 `/usr/include/libscl-core-pure/sclcore.h`

**易犯的错**:看到 `/usr/include/` 就直接判"跨包→needs_human"。**这太粗。**
诊断 `file` 是警告**报告的位置**(第三方头文件里的字段/声明),但这个警告是
**编译本包某个源文件时**触发的(那个 `.cpp`/`.c` `#include` 了这个头文件)。
如果触发的编译单元在**本 repo**,通常可以在**本包的构建配置**里针对性抑制,
不必转人工。

**第 1 步:从 evidence 找触发这个诊断的本包编译单元。**
诊断的 `primary_error.file` 是系统头文件,但 evidence 的 **cascade 信息里通常已经
含触发它的本包目标文件**(`.o`),不用读 raw log:
- `cascade_summary`:如 `make cascade: .../src/inputmethod-core/fake_sclcore.cpp.o -> unlinked`
- `root_cause_candidates` 里 `kind == "make_cascade"` 的 `message`:如
  `make[2]: *** [.../fake_sclcore.cpp.o] Error 1`

从这里提取触发的源文件(如 `fake_sclcore.cpp`)。若 evidence 的 cascade 没给出具体
`.cpp`/`.c`,再退回在**本包源码树** grep 谁 `#include` 了这个系统头文件:
```bash
grep -rln "<系统头文件名，如 sclcore.h>" "<unit.src_clean>" \
     --include="*.c" --include="*.cc" --include="*.cpp" \
     --include="*.h" --include="*.hpp" | head
```
> 优先读 evidence 的 cascade(信息已被 analyzer 提取);grep **源码树**是允许的
> targeted 检查。**都不要读 raw build log**(token rule)。

**第 2 步:确认触发单元在本 repo。**
```bash
grep -rln "<触发源文件名，如 fake_sclcore>" "<unit.src_clean>" | head
```
- **恰好定位到本 repo 一个** owned 源文件(如 `tests/src/.../fake_sclcore.cpp`)
  → 走第 3 步(本包抑制)。确认它所属的构建配置(哪个 `CMakeLists.txt`/`.spec`
  段带 `-Werror`,且是哪个 target)。
- **找不到 / 多个候选 / 无法确认属于哪个 target** → `needs_human` + `cross_package`。
  不猜(保守 fallback,和只看 `primary_error.file` 的旧行为在"定位不到"时一致)。

**第 3 步:本包针对性抑制(仅当警告源自第三方/系统头文件)。**

判断这个抑制**是否正当**:
- ✅ 正当:警告是**第三方/系统头文件**自身的代码问题(如依赖包某个类的
  `-Wunused-private-field`),本包无法控制依赖包的代码质量,不该为它 block 构建。
- ❌ 不正当:警告其实是**本包自己代码**的问题 → 不要 `-Wno` 掩盖,回分支 1/正常修复。

正当时,产出 candidate edit_spec:在**触发单元所属的构建配置**(通常是那个目录的
`CMakeLists.txt`,或 `packaging/*.spec` 的对应 target/CFLAGS)里,给 `-Werror` 那行
**追加精确的单个** `-Wno-<具体warning>`:
```
# 例:tests/CMakeLists.txt 的
SET(EXTRA_CFLAGS "... -Wall -Werror")
# → 追加精确抑制（只关这一个 warning，不动其它检查）
SET(EXTRA_CFLAGS "... -Wall -Werror -Wno-unused-private-field")
```

**允许**:
```
-Wno-<具体单个 warning>    如 -Wno-unused-private-field
```
**禁止(这些会把局部抑制泛化成危险 workaround)**:
```
-Wno-error                 会一次关掉一大片
全局 -Wno-*                 无差别关警告
全包/生产库范围的 CFLAGS/CXXFLAGS 修改
在 spec 顶层 %build 全局关警告
```

**作用域铁律**:抑制必须**限定到触发单元所在的 target / test target / 那一个
`CMakeLists.txt` 的局部 compile option**,**不得扩散到生产库**。
`fake_sclcore.cpp` 在 tests target → 抑制放 tests 的构建配置,不能碰生产库的 CFLAGS。

**这不是修根因,必须在报告里写清**:
```
根因:  第三方/系统头文件(<依赖包>/<头文件>)触发的 warning
本包动作:仅对触发该 warning 的本包编译单元/target 做局部 -Wno-<warning> 抑制,
        用于避免该单元因依赖头文件 warning 被 -Werror 阻塞
后续建议:依赖包(<依赖包>)仍应修正 warning 源头(报 bug/提 patch)
```
不要把局部抑制包装成"修好了"。这与本文档"上游 bug 不硬 workaround"的原则一致:
局部抑制是**绕过依赖包 warning 对本包的阻塞**,不是修复依赖包的代码。

**必须人确认,不因 skill 曾成功就跳过安全门**:这类修法(依赖头文件根因 + 本包局部抑制)
风险高于标准源码修复。**暂停,展示完整 candidate edit_spec + 上面的根因说明,等人确认**
后才走主 workflow A4→A5→A6(formatter → build-verify → gerrit-submit)。
探索出的 patch 同样过 build-verify,不跳过安全门。

**实例**:capi-ui-inputmethod
→ 诊断:`/usr/include/libscl-core-pure/sclcore.h:516` 的 `-Wunused-private-field`
  (evidence 判 `system_or_toolchain_path`,not patch-ready — 这是【正确】的
  ownership 判定,但不等于无法处理)
→ evidence 的 `cascade_summary` / make_cascade candidate 里含
  `.../src/inputmethod-core/fake_sclcore.cpp.o` → 触发源文件是 `fake_sclcore.cpp`
→ `grep fake_sclcore <src_clean>` 确认它在本 repo 的 `tests/src/inputmethod-core/`
→ 确认构建配置:`tests/CMakeLists.txt` 的 `EXTRA_CFLAGS` 带 `-Werror`
→ 正当性:警告源自依赖包 `libscl-core` 的头文件(`m_impl` 未使用),本包不该为它 block
→ edit_spec:`tests/CMakeLists.txt` 的 `EXTRA_CFLAGS` 追加 `-Wno-unused-private-field`
→ 报告说明根因在 `libscl-core`,建议给它报 bug
→ 暂停等确认 → build-verify → 提交命令
→ **不再直接 needs_human**;信息(触发单元)就在 evidence 的 cascade 里,
  之前分支 3 只看 `primary_error.file` 才误判为纯跨包。

### 分支 4:`failure_class` 是 `dependency` / `toolchain` / `build_env`

**特征**:evidence 或 build-verify 返回 `repair_allowed: false`

**处理**:**不进修复循环。** 标转人工。

常见:
- `dependency`:`nothing provides pkgconfig(xxx)` → 依赖缺失或 **gbs.conf 用错**
- `toolchain`:编译器拒绝了某个 flag
- `build_env`:构建环境问题

**先检查 gbs.conf 是否用对**(这是最常见的假失败原因,实测踩过)。

### 分支 5:其他 / 无法归类

```bash
ls "<unit.src_clean>"
find "<unit.src_clean>" -name "<文件基名>" | head
grep -rn "<诊断消息里的关键符号>" "<unit.src_clean>/" \
     --include="*.c" --include="*.h" --include="*.cc" --include="*.cpp" | head
```

**刹车内没有明确 hypothesis → 标 `needs_human`,写清:**
- 诊断是什么
- 探索了什么、发现了什么
- 卡在哪、还需要什么信息

## 3. 探索的输出

对每个探索的 unit,产出:

```markdown
### <unit_key>

**诊断**: <message> @ <file>:<line>

**探索**: <做了什么、发现了什么>

**结论**: repairable | needs_human

--- 如果 repairable ---
**根因**: <是什么>
**改法**: <改哪个文件、怎么改、为什么这么改是对的>
**风险**: <可能有什么副作用>
**edit_spec**: <完整 JSON>
→ **等人确认后才 build-verify。**

--- 如果 needs_human ---
**类别**: upstream_bug | cross_package | dependency | unknown
**原因**: <为什么自动化处理不了>
**建议**: <人该怎么做>
```

## 4. 反面教材(实测踩的坑)

**hal-api-drm 的 sed patch**——看着完全合理,实际改坏代码:

```
诊断:generated/hal_drm_stub_1.c:3948 引用了未声明的
     __rpc_port_stub_drm_method_init_privilege_checker

看着合理的修法:在 spec 的 %build 里,tidlc 生成后 sed 替换:
  sed -i 's/__rpc_port_stub_drm_method_[a-z_]*_privilege_checker/NULL/g' <生成的 .c>

实际结果:
  ✅ 数组里的引用 → NULL(这是想要的)
  ❌ 但函数【定义】也被替换了:
     static int __rpc_port_stub_drm_method_xxx_privilege_checker(...)
     → static int NULL(...)          ← 语法错误!
  → 编译失败:expected identifier or '(' before 'void'
  → build-verify FAIL,不出提交命令 ✓ 安全门兜住了

教训:
  1. 正则/sed 改代码必须【限定作用范围】(只改数组块,不碰函数定义)
  2. 改之前要【看生成的代码实际结构】,不能凭诊断猜
  3. 根因是 tidlc 的 bug(生成了引用但没生成定义)→ 正解是修 tidlc,不是打补丁
  4. 安全门(build-verify 真编译)挡住了这个错误的推理 —— 这正是它存在的意义
```

**这条教训的普适版本**:探索出来的 patch,**你的推理越"聪明",越要让 build-verify 检验它。**
