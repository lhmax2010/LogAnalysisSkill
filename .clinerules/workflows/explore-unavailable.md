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

### 分支 1:相对路径带 `../` → 路径归一化(可自动修)

**特征**:`file` 形如 `../src/bin/server/e_comp_wl.c`

**原因**:out-of-tree build,诊断路径相对于构建目录,不是源码根。
文件**在** repo 里,只是 patch-suggest 的 suffix search 匹配不上。

**处理**:
```bash
# 剥掉前导 ../,在 src_clean 里找
find "<unit.src_clean>" -path "*<剥掉 ../ 后的路径>" | head
```

找到 → 这就是标准的源码修复,回主 workflow 的 A3(写 edit_spec)。
`edit_spec.file` 用**相对 src_clean** 的路径。

**实例**:enlightenment 的 `../src/bin/server/e_comp_wl.c:814`
→ 实际在 `<src_clean>/src/bin/server/e_comp_wl.c`
→ `-Wbitwise-instead-of-logical`,`|` → `||`(getter 是纯函数,短路安全)
→ build-verify PASS ✓

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

### 分支 3:绝对路径指向系统目录 → 跨包错误

**特征**:`file` 形如 `/usr/include/libscl-core-pure/sclcore.h`

**原因**:错误在**依赖包**装到系统目录的头文件里,不在这个包的 repo。

**确认**:
```bash
find "<unit.src_clean>" -name "<文件名>" | head   # 应该找不到
```

**处理**:**标 `needs_human` + `cross_package`。**

报告:
- 错误在哪个包的头文件(从路径推断:`/usr/include/libscl-core-pure/` → `libscl-core`)
- 要修的是那个包,不是当前包
- 当前包也可以加编译选项绕过,但那是掩盖问题,需要人判断值不值

**实例**:capi-ui-inputmethod
→ `/usr/include/libscl-core-pure/sclcore.h:516` 的 `-Wunused-private-field`
→ 要修的是 `libscl-core` 包
→ 转人工

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
