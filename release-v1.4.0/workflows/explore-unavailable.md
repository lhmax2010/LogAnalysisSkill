# Explore & Repair — 源码类失败的通用探索与修复

这份文档处理两种情况:

1. `patch-suggest` 标了 `source_context_unavailable`(它没能把源码喂给你,
   **不等于**这个失败无法修复)
2. build-verify 返回 `repair_allowed == "needs_confirmation"`
   (错误确实在本包源码内,但诊断类型不在自动修白名单,修法需要现场判断)

两种情况走**同一套判断骨架**。

> **这不是一本按诊断类型查表的手册。** 下面第 2 节是通用流程,适用于任何诊断。
> 第 5 节的"已知模式"只是参考,**不穷尽** —— 遇到没见过的诊断类型,照第 2 节走,
> 不要因为"文档里没写"就停下。

## 0. 铁律

1. **不编造源码内容。** 没看到的代码不要猜。要改哪一行,先把它读出来。
2. **探索有刹车。** 每个 unit 最多 **10 次探索性工具调用**(`find`/`grep`/`ls`/
   `sed` 等;**不计** formatter/build-verify/gerrit-submit)**或 10 分钟,先到者为准**。
   仍无明确、可解释、owned-source 的 repair hypothesis → 标 `needs_human`,
   写清卡在哪,继续下一个包。
3. **产出 edit_spec 后暂停。** 把推理过程 + 完整 edit_spec + 风险评估展示给人,
   **等确认**才 formatter/build-verify。
4. **安全门不因"人确认过"而跳过。** 探索出的 patch 同样要过 formatter + build-verify。
5. **上游 bug 不硬 workaround。** 根因在工具链/生成器/依赖包时,标 `needs_human`
   报上游。局部绕过是可以的(见 3.3),但要说清它是绕过不是修复。

## 1. 起点

**先 guard**:
```
unit["evidence_packet"] 为 null 或文件不存在
  → 没有诊断可探索 → needs_human + missing_evidence
unit["src_clean"] 为 null
  → 源码没 clone 成功,无从探索 → needs_human + missing_source
```

读诊断:
```python
ev = json.load(open(unit["evidence_packet"]))
p = ev["primary_error"]
file, line, message = p["file"], p["line"], p["message"]
cascade = ev.get("cascade_summary", "")
candidates = ev.get("root_cause_candidates", [])
```

> **信息优先从 evidence 取。** analyzer 已经把 build log 压缩成结构化证据了 ——
> `primary_error` 只是诊断报告的位置,`cascade_summary` 和 `root_cause_candidates`
> 里常有触发它的编译单元、make 目标等关键线索。
> **不要为了找线索去读 raw build log**(token rule);在**源码树**里 grep 是允许的。

## 2. 通用判断骨架

### 2.1 这个错误在本包源码内吗

这是**唯一**的分流点。

```
能定位到 <unit.src_clean> 下的一个 owned source 文件
  → 在本包内 → 走 2.2 修复流程
定位不到
  → 转人工(第 4 节),说清是哪一类边界
```

`primary_error.file` 的形态**不能**直接决定答案 —— 它是诊断**报告**的位置,
不一定是**能改**的位置:

- 相对路径带 `../`(out-of-tree build)→ 剥掉前导 `../` 后文件通常就在 repo 里
- 绝对路径指向 `/usr/include/`(依赖包头文件)→ 报告位置在包外,但**触发它的
  编译单元**可能在本包内,那样就能在本包的构建配置里处理
- 路径含 `generated/`(构建时生成)→ 文件不在 repo,但**生成它的输入**
  (`.tidl`/`.proto`/spec 脚本)可能在

所以要**先查再判**,不要看一眼路径就下结论。查的手段:

```bash
# 剥掉前导 ../ 后在源码树里找
find "<unit.src_clean>" -path "*<剥掉 ../ 后的路径>" -type f | head

# evidence 的 cascade 里有没有触发它的编译单元（.o / .cpp / .c）
# → 拿到源文件名后再 grep 确认它在本 repo
grep -rln "<触发源文件名>" "<unit.src_clean>" | head

# 谁 include 了这个头文件 / 谁引用了这个符号
grep -rln "<头文件名或符号>" "<unit.src_clean>" \
     --include="*.c" --include="*.cc" --include="*.cpp" \
     --include="*.h" --include="*.hpp" | head
```

**恰好定位到一个**才算数。找不到、或多个候选无法确认 → 转人工,不猜。

### 2.2 修复流程(五步,任何诊断类型都走这个)

#### 第 1 步:读懂错误

这个诊断在说什么?涉及哪些符号、哪些文件、哪个编译单元?
消息里提到的每个标识符都要能对应到源码里的具体位置。

#### 第 2 步:看清结构(**不猜**)

把相关的定义、引用、构建配置**读出来**。要读什么由错误性质决定,例如:

- 符号冲突 → 两个同名符号各自定义在哪、是嵌套还是平级
- 类型/接口不匹配 → 双方的声明各是什么
- 编译选项相关 → 哪个 `CMakeLists.txt`/`.spec` 段控制着这个编译单元,
  它管的是 test target 还是生产库
- 行为类警告(如短路语义变化)→ 相关函数是不是纯读取、有无副作用

命令用 `grep -n` / `sed -n '<a>,<b>p'` / `cat -A`(看精确字节)。
**看到什么才能写什么。**

#### 第 3 步:拟定 edit_spec

写出完整的 edit_spec,不是"建议 XXX"。
`old` 字节级匹配,`line` 是 `old` **开始**的行号(见主 workflow A3)。

**机械替换类修改必须精确到位置**:按 build log / evidence 给出的
`file:line:column` 逐处改,**不要全局 sed 替换**。同一个标识符在文件里
可能有些地方本来就是对的、有些地方语义不同,全局替换会误伤。

#### 第 4 步:评估改动规模与风险

按下面的档位判断,**结论要写进报告**:

| 档位 | 特征 | 说明 |
|---|---|---|
| **局部** | 单文件、不改声明、机械可做(加关键字/加限定符/改格式符/加编译选项) | 风险低 |
| **跨文件** | 改多个文件,但都是引用侧,不动定义 | 中等,要列全改了哪些文件 |
| **改声明/接口** | 改函数签名、类型定义、命名、对外符号 | **高** —— 可能影响 ABI 和其它包,报告里必须显式标注 |

> ⚠️ **build-verify 只能验证"能编译",验证不了"改法对不对"。**
> 改声明/重命名这类,编译过了也可能是错的。档位越高,报告里的风险说明要越详细。

**抑制类修改的专门约束**(用 `-Wno-*` 绕过警告时,无论诊断类型):

- 只有当警告**源自第三方/系统头文件或生成代码**(本包无法控制其质量)时才正当;
  警告出在本包自己代码里 → 回去正常修,不要 `-Wno` 掩盖
- **只加单个精确的 `-Wno-<具体warning>`**
- 禁止:`-Wno-error`(一次关一大片)、全局 `-Wno-*`、全包/生产库范围的
  `CFLAGS`/`CXXFLAGS`、spec 顶层 `%build` 全局关警告
- **作用域必须限定到触发单元所在的 target**,不得扩散到生产库
- 怎么找对 target:从触发单元路径向上找最近的 `CMakeLists.txt`,
  再 `grep` 确认哪个 `add_executable`/`add_library` 真的包含该源文件;
  若同一文件也定义了生产库 target,用
  `target_compile_options(<该target> PRIVATE -Wno-xxx)` 而非改共享变量;
  **判断不出该源文件属于哪个 target → 转人工**,改错会扩散
- 报告必须三段式写清:
  ```
  根因:    <依赖包/生成器> 的 <文件> 触发的 warning
  本包动作:仅对触发该 warning 的本包编译单元/target 做局部抑制
  后续建议:根因方仍应修正 warning 源头(报 bug / 提 patch)
  ```
  **不要把局部抑制包装成"修好了"。**

#### 第 5 步:展示,暂停,等确认

按第 3 节的模板输出,然后**停下**。人确认后才走主 workflow 的
A4(formatter)→ A5(build-verify)→ A6(gerrit-submit)。

### 2.3 多轮:一个错误修完还有下一个

修好当前错误后 build-verify 可能因**另一个**错误再次 FAIL。这是正常的 ——
CI 上的诊断只是第一个撞到的墙,后面可能还有。

判断依据是 build-verify 返回的 `repair_allowed`:

| 值 | 含义 | 行为 |
|---|---|---|
| `"auto"` | 修法确定唯一(白名单内诊断) | 扩展 edit_spec,自动进下一轮 |
| `"needs_confirmation"` | 错误在本包源码内,但修法需现场判断 | **回到 2.2 走一遍**,产出新的 edit_spec,暂停等确认,确认后再进下一轮 |
| `"denied"` | 依赖/工具链/环境/源码不可达/非本包所有 | **停,转人工。不得越过。** |

轮次没有固定上限,由 `check-convergence` 决定何时停:

- `advance`(指纹或错误数变化 = 有实质进展)→ 继续
- `stalled`(指纹和错误数都没变 = 原地打转)→ 停,转人工
- `regressed`(变糟了)→ 停,转人工

> 每一轮的 `needs_confirmation` 都要人确认,人始终在环里 —— 这就是不设轮次
> 上限也安全的原因。但如果同一个包连着走了很多轮,在报告里提醒人:
> 这个包可能存在更系统性的问题,值得包 owner 看一眼。

## 3. 输出模板

```markdown
### <unit_key>

**诊断**: <message> @ <file>:<line>

**探索**: <查了什么、看到了什么>

**结论**: repairable | needs_human

--- repairable ---
**根因**: <是什么>
**改法**: <改哪些文件、怎么改、为什么这么改是对的>
**改动规模**: 局部 | 跨文件 | 改声明/接口
**风险**: <可能的副作用;若是抑制类,写三段式说明>
**edit_spec**: <完整 JSON>
→ **等人确认后才 formatter + build-verify。**

--- needs_human ---
**类别**: cross_package | upstream_bug | dependency | ambiguous_target | unknown
**原因**: <为什么本包源码内解决不了,或为什么无法确定改法>
**已查证据**: <查了什么、结论依据>
**建议**: <人该怎么做;若是上游问题,给出报 bug 需要的信息>
```

## 4. 转人工的边界

这些是**真实**的能力边界,不是"暂时不会修":

| 类别 | 特征 | 为什么不在本包修 |
|---|---|---|
| `cross_package` | 定位到的问题只能靠改依赖包解决 | 本包改不了对方的源码 |
| `upstream_bug` | 生成器/工具链本身有 bug | 正解是修生成器或它的输入,不是 patch 生成物 |
| `dependency` | `nothing provides ...` / 缺包 | 先查 gbs.conf 是否用对 |
| `ambiguous_target` | 定位到多个候选、或无法确定改哪个 target | 猜错会扩散到生产库 |
| `unknown` | 刹车用尽仍无明确 hypothesis | 写清卡在哪 |

`repair_allowed == "denied"` 时同理:那是 build-verify 已经判定的边界,
**Cline 不得单方面越过**。若怀疑误判,只能提出证据 + 暂停等人确认,
人确认 override 后从 A3 重新进入安全门(见主 workflow A5 的说明)。

## 5. 已知模式(参考,不穷尽)

以下是实测遇到过的几类。**它们不是分支,是例子** —— 说明第 2 节的骨架
在具体场景里长什么样。遇到没列出的诊断类型,照骨架走。

### 5.1 相对路径带 `../` — out-of-tree build 的假阴性

诊断 `../src/bin/server/e_comp_wl.c:814` 的 `-Wbitwise-instead-of-logical`。
patch-suggest 的 suffix 匹配被前导 `..` 破坏,标了 unavailable,但文件就在 repo 里。

骨架落地:剥前导 `../` → `find` 唯一命中 → 读第 814 行看实际代码 →
第 2 步查右操作数那几个 getter 是不是纯读取(`|`→`||` 会引入短路,有副作用就不能改)
→ 确认是 `return ec->字段` 的纯 getter → 拟定 `|`→`||` → 局部档 → PASS。

> 这个模式后来沉淀回工具了(resolver 会剥前导 `.`/`..`),现在多数
> `../` 路径会直接判 available,不再需要探索。

### 5.2 诊断报告在系统头文件 — 但触发单元在本包

诊断 `/usr/include/libscl-core-pure/sclcore.h:516` 的 `-Wunused-private-field`。
路径在包外,但错误是**编译本包某个源文件时**触发的。

骨架落地:evidence 的 `cascade_summary` 里有
`.../src/inputmethod-core/fake_sclcore.cpp.o` → grep 确认该文件在本 repo 的
`tests/src/inputmethod-core/` → 向上找到 `tests/CMakeLists.txt`,确认它管的是
tests target 而非生产库 → 正当性成立(警告源自依赖包 `libscl-core` 的头文件)
→ `EXTRA_CFLAGS` 追加 `-Wno-unused-private-field` → 报告三段式说明根因在
`libscl-core` → 人确认 → build-verify PASS,`actual_changed_paths` 只含
`tests/CMakeLists.txt`(作用域约束生效的实证)。

### 5.3 符号冲突 — 结构决定了能不能局部修

诊断 `reference to 'LWE' is ambiguous`,20 处,全在一个文件里。

骨架落地:第 2 步查两个同名符号的定义 ——
`inc/LWEWebView.h:43` 是 `namespace LWE {`,`:48` 是 `class LWE_EXPORT LWE {`,
**class 在 namespace 内部**(嵌套)。所以全局作用域只有 namespace 一个 `LWE`,
`::LWE::` 无歧义 → 在报错处按 `file:line:column` 逐处加 `::` 限定,
不碰任何定义 → 局部档 → PASS。

> **如果结构是平级的**(namespace 和 class 都在全局作用域),就只能重命名 ——
> 那是"改声明/接口"档,跨文件、可能影响 ABI,要转人工或至少在报告里
> 重点标注风险。**同一个诊断文本,结构不同修法完全不同** —— 这正是第 2 步
> 必须"看清结构"而不能凭诊断类型查表的原因。

### 5.4 构建时生成的代码 — 先判根因在哪

诊断路径含 `generated/`(如 `src/service_plugin/generated/hal_drm_stub_1.c`),
文件不在 repo。

骨架落地:确认 repo 里没有该文件 → 找谁生成的
(`grep -nE "tidlc|generat|%build|codegen" packaging/*.spec`)→ 判根因:

- **生成器 bug**(生成的代码引用了自己没生成的符号;错误类型是
  `use of undeclared identifier` 且集中在 `generated/`;检查发现数组引用和
  函数定义不成对)→ `needs_human` + `upstream_bug`,**不 workaround**
- **生成器输入有问题**(`.tidl`/`.proto` 在 repo 里)→ 改输入,走正常流程
- **确实需要生成后 post-process** → 可以改 `packaging/*.spec`,但改动范围
  必须限定,且理解生成物结构后再写
  > 上一次 build 的产物(`~/GBS-ROOT*/.../BUILD/<pkg>-*/`)只用于**理解结构**,
  > 不得作为当前验证的输入 —— 最终必须由 build-verify 在本轮 verified copy 中
  > 重新生成并编译。

## 6. 反面教材(实测踩的坑)

**hal-api-drm 的 sed patch** —— 看着完全合理,实际改坏代码:

```
诊断:generated/hal_drm_stub_1.c:3948 引用了未声明的
     __rpc_port_stub_drm_method_init_privilege_checker

看着合理的修法:在 spec 的 %build 里,tidlc 生成后 sed 替换:
  sed -i 's/__rpc_port_stub_drm_method_[a-z_]*_privilege_checker/NULL/g' <生成的 .c>

实际结果:
  ✅ 数组里的引用 → NULL（这是想要的）
  ❌ 但函数【定义】也被替换了:
     static int __rpc_port_stub_drm_method_xxx_privilege_checker(...)
     → static int NULL(...)          ← 语法错误!
  → 编译失败,build-verify FAIL,不出提交命令 ✓ 安全门兜住了

教训:
  1. 正则/sed 改代码必须【限定作用范围】—— 这就是第 3 步"机械替换要精确到
     file:line:column、不要全局 sed"的由来
  2. 改之前要【看清结构】(第 2 步),不能凭诊断猜
  3. 根因是 tidlc 的 bug → 正解是修 tidlc,不是打补丁(铁律 5)
  4. 安全门(build-verify 真编译)挡住了这个错误的推理 —— 这正是它存在的意义
```

**普适版本**:探索出来的 patch,**你的推理越"聪明",越要让 build-verify 检验它。**
而 build-verify 只能验证"能编译" —— 所以改动规模越大(第 4 步的档位越高),
越要靠报告里的风险说明让人做最后判断。
