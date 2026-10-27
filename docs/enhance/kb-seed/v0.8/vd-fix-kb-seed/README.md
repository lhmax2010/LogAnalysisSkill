# VD Clang 修复知识库种子（v0.8，草稿，待审定）

用 Obsidian 打开本目录即可浏览。所有页面状态都是"参考（未审定）"：内容来自以往对话记录的摘要，原始 CL、diff、验证记录还没逐条核对；FatTank 审定并补齐这些信息后，才能作为"先例"导入知识库（HLD §7.3）。

## 告警标志两档（HLD v0.7 §6.3 候选，待 FatTank 确认）
- **强制人工定性档**（命中只表示必须由人定性，不表示已确认是真 bug）：[[Wsizeof-pointer-memaccess]] [[Wsizeof-array-argument]] [[Wsizeof-pointer-div]] [[Wsometimes-uninitialized]] [[Wuninitialized]] [[Wreturn-type]] [[Wreturn-stack-address]] [[Wdangling]] [[Warray-bounds]] [[Wformat]] [[Wabsolute-value]] [[Wimplicit-function-declaration]] [[Wint-conversion]] [[Wincompatible-pointer-types]] [[Wincompatible-function-pointer-types]] [[Wtautological-overlap-compare]] [[Wtautological-pointer-compare]] [[Wtautological-constant-out-of-range-compare]] [[Wunsequenced]] [[Wmismatched-new-delete]] [[Wdynamic-class-memaccess]] [[Wmemset-transposed-args]] [[Wfortify-source]] [[Wdelete-non-abstract-non-virtual-dtor]] [[Wdelete-non-virtual-dtor]] [[Winfinite-recursion]] [[Wshift-count-overflow]] [[Wshift-count-negative]] [[Wdivision-by-zero]] [[Wsingle-bit-bitfield-constant-conversion]] [[Wbitfield-constant-conversion]] [[Wconstant-conversion]] [[Wnull-dereference]] [[Wbool-conversion]] [[Wvexing-parse]] [[Wdeprecated-non-prototype]]
- **需看一眼档**：[[Woverloaded-virtual]] [[Wparentheses-equality]] [[Wunused-result]] [[Wformat-security]] [[Wenum-conversion]] [[Wtautological-unsigned-zero-compare]] [[Wmisleading-indentation]] [[Wempty-body]] [[Wimplicit-fallthrough]] [[Wswitch]] [[Wself-assign]] [[Wlogical-not-parentheses]] [[Wlogical-op-parentheses]] [[Wstring-plus-int]] [[Wpointer-bool-conversion]] [[Wpointer-sign]] [[Wunused-value]] [[Wconditional-uninitialized]] [[Wreorder-ctor]]
- **未分档（出现过的其它标志）**：[[Wc2y-extensions]] [[Wunused-private-field]] [[Wvla-cxx-extension]] [[always_inline--requires-target-feature]] [[unknown-argument]]

## 每个案例页怎么读（v0.7 起，组内意见）
1. **报错原文**：日志里的主错误行长什么样。标"日志原文"的是真实日志摘出来的；标"典型形式"的只是 Clang 的诊断格式，补到真实日志后替换；标"原文待补"的还没有。
2. **解决方案**：先标类型——"通用做法"（以往记录摘要，具体 CL 和文件待补）、"待补"、"处置"（不是本组修法，例如需 owner 提交、反馈开发者）三者分开；再写做法，以及备选方案为什么没用。
3. **需联动看的模块**：头文件 / 接口的提供者、依赖这个包的下游、同一根因的其它包。下游部分在第 3b 批生成 VD 包依赖图后自动补齐（HLD §7.8）。
4. `packages/` 下是包页（目前只有构建 19091860 的 7 个失败包），页内用 `[[…]]` 双链连到案例和标志；Obsidian 右上角的"关系图"就是这些页面之间的关系图。依赖图生成后，包页之间会按依赖关系互相链接。

## 案例
| 编号 | 问题 | 包 | 是否真 bug |
|---|---|---|---|
| [[C001]] | 把 __attribute__((const)) 用在会写指针参数的函数上 | openal-soft | 真 bug |
| [[C002]] | constexpr 常量类型与实际 API 参数类型不一致 | （Tizen 平台组件，见来源） | 需看一眼 |
| [[C003]] | Cynara 凭据接口的枚举强转可能掩盖取错值 | cynara 相关调用方 | 需核实根因 |
| [[C004]] | 对字符数组成员做 NULL 判断 | tdm_meson_hwc | 非 bug（核实后） |
| [[C005]] | 整数用了 fabs | （Tizen 平台组件，见来源） | 真 bug（轻） |
| [[C006]] | 子类同名函数藏住父类虚函数（app-core ExitContext） | app-core | 需看一眼 |
| [[C007]] | 子类同名函数藏住父类虚函数（widget-viewer-dali） | widget-viewer-dali | 需看一眼 |
| [[C008]] | 未使用的私有成员：加 unused 属性还是删掉 | united-service；19091860 中的 [[com.samsung.tv.aria-engine]]、[[org.tizen.picture-test]] 同类 | 非 bug |
| [[C009]] | 引用有歧义（reference to X is ambiguous） | （见来源） | 需看一眼 |
| [[C010]] | C++ 里的变长数组改 std::vector | ELF 解析代码；19091860 中的 [[plusplayer]] 同类 | 非 bug（注意长度单位） |
| [[C011]] | 第三方源码在构建时才下载（CMake FetchContent） | Open3D（ext_benchmark） | 非 bug |
| [[C012]] | GCC 专有编译选项被 Clang 拒绝 | （见来源） | 非 bug |
| [[C013]] | x86_64 包的 Clang 失败：AVX-512 内联函数缺目标特性 | [[libdeflate]]（x86_64） | 非 bug |
| [[C014]] | spec 用了 Windows 换行符 | screend | 非 Clang 问题 |
| [[C015]] | shelve 基线、文件缺失一类的非编译问题 | power-defs、securestorage-credential、vd-kernel-dtb | 非 Clang 问题 |
| [[C016]] | 依赖库被编成共享库，连带一大片失败 | trustzone-common | 非 Clang 问题 |
| [[C017]] | C99 语义下裸 inline 函数的符号悬空 | 9 个包共 14 处（见来源） | 真 bug |
| [[C018]] | 条件里多余的括号 | 19091860 中的 [[AT-HUB]]、[[ug-captionUG-efl]] | 需看一眼 |
| [[C019]] | 子类藏住父类虚函数（tvs-ext） | 19091860 中的 [[tvs-ext]] | 需看一眼 |

## 待补
- 构建 19091860 的 7 个失败包（AT-HUB、aria-engine、picture-test、plusplayer、tvs-ext、ug-captionUG-efl、libdeflate）是第 3a 批的验收样本：它们的实际修法在验收结束前只写进验收参照集文件，不补进本库；相关页面（7 个包页和 C013、C018、C019）页首标了 `acceptance_sample: true`，验收期间不进检索。
- b844、b776 两轮共 40 多个失败的修法（中英文评估总表里有），按本格式逐条补。
- 团队修法规则（HLD 附录 A）在发布前更新后，作为 rules/ 目录导入。
- 报错原文：除标"日志原文"的页面外，其余案例的原文要从当时的日志补录。
- 需联动看的模块：标"待补"的，第 3b 批依赖图生成后补下游；提供者和同根因由审定时补。
- 三栏齐全（有日志原文、有具体修法或明确处置、联动模块已核实）的页面才计入第 3b 批的案例页验收；标"原文待补""典型形式"的页面保留作参考。
