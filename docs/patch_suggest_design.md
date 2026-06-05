# tizen-gbs-patch-suggest — 设计文档 (DESIGN v0.1, FROZEN)

> 状态: **冻结**。决策已定。Codex 须先复述 + 核对现有代码接口(凡 ⚠️待核对 处),
> 再进入分阶段实施。实施遵循项目既有节奏: frozen design → Codex 复述 → 分阶段 PR → 真实验证。

---

## 0. 一句话定位

一个**独立新 skill**: 消费 analyzer 的编译错误证据(Evidence Packet),收集出错位置的
源码上下文,组织成**最优的、LLM-ready 的 patch 生成上下文(context.md)**,写成文件。

**核心定位: 这是"patch 生成上下文准备器",不是"patch 生成器"。**
patch 永远由**外层 Claude/Cline** 生成 —— skill 内部**绝不调 LLM、绝不 apply**。

- skill 名(kebab-case): `tizen-gbs-patch-suggest`
- Python 包名(underscore): `gbs_patch_suggest`

---

## 1. 冻结决策清单

[D1] **独立 skill**,不增强 CompileErrorSuggester。
  CompileErrorSuggester 维持 advisory(纯规则)不动,保护 workflow 确定性契约。
  现有三 skill / workflow / 所有 Suggester / pattern 零改动。

[D2] **skill 内部不调 LLM(方式 B)**。
  skill 产出"组织好的 patch 生成上下文(context.md)",由外层正在运行的 Claude 生成 patch。
  理由: skill 给 Cline/Claude Code 用,外层已有最强 LLM(Claude);skill 自己调 API 要管
  key/网络/成本/弱模型,无谓。skill 做它擅长的 —— 收集错误+源码,组织成最优 prompt。
  实现强制: skill 代码不 import 任何 LLM SDK,不发任何网络 LLM 请求。

[D3] **绝不自动 apply**。
  skill 不执行 patch / git apply / 任何写源码动作。只写输出目录。
  实现强制: 不 import subprocess 调 patch/git apply,不写源码树任何文件。

[D4] **先 1 个错误**(先窄后宽)。
  本期只处理 evidence 里**最前面的 1 个编译错误**。验证有效后再扩展到多个。

[D5] **接入 workflow,但形态 = 路 1**。
  workflow 跑到 patch-suggest 阶段时,只产出 context.md(进 workflow 输出),workflow 结束。
  外层 Claude 读 workflow 输出里的 context.md,自己生成 patch。
  → workflow 子进程内**不**调 LLM(子进程联系不到外层 Claude,这是关键约束)。
  → 独立使用与 workflow 接入两个场景,skill 都只产 context,patch 都由外层 Claude 生成。一致。

[D6] **只处理 compile error 类**。
  非 compile 类(linker/depsolve/patch/spec-script)→ skill 明确提示"不适用,
  请用 workflow 的对应 suggester",不产 context。

[D7] **LLM-ready 上下文不臆造事实**。
  context.md 里的指令明确要求外层 Claude: 只基于提供的错误信息 + 源码片段,
  不确定就说不确定,不编造不存在的函数/头文件;鼓励给多个候选 + 标注假设与置信度;
  patch 是建议草稿,需人 review,绝不直接 apply。

---

## 2. 输入(消费 analyzer 产出)

skill 不重新分析日志 —— 消费 analyzer 已产出的结构化证据(像 workflow 消费 analyzer)。

两种输入,都支持:
1. `--evidence path/to/evidence_packet.json` —— 直接消费 analyzer 产出(优先)
2. `--buildlog path/to/compiler.log` —— 内部复用 analyzer 拿 evidence(便利封装,
   复用 workflow 已验证的 sibling skill 调用 + PYTHONPATH 合并机制)

⚠️待核对(Codex 复述时用实际代码确认,不得凭本文档假设):
- analyzer Evidence Packet JSON 的实际字段结构 —— 编译错误的"文件路径/行号/错误文本"
  到底怎么表示? 字段名是什么?
- evidence 是否标注 fault class(用于 D6 的"只处理 compile error 类"判断)?
- 编译错误证据里是否已含出错源码文件路径 + 行号(决定能否定位源码片段)?
- analyzer 的 src-root 语义(与本 skill `--src-root` 对齐,避免重复 workflow 那次的偏差)

---

## 3. 源码上下文收集

[实现] 按 evidence 里的 (文件路径, 行号),从 `--src-root` 读出错位置的上下文窗口
(默认前后各约 30 行,够理解不爆 token)。
- 读不到源码文件 → 降级"仅错误信息"模式,context.md 明确标注"无源码上下文,可靠性降低"。
- src-root 缺省语义 ⚠️待核对,与 analyzer 对齐(workflow 那次的教训: 别想当然用 cwd)。

---

## 4. 输出契约

输出到 `--output-dir`(默认 `./.gbs_patch_suggest`):

```
.gbs_patch_suggest/
├── README.md      # 处理了哪个错误、context 在哪、给外层 Claude 的明确指引
├── context.md     # 核心产物: 错误信息 + 源码上下文 + 给 Claude 的 patch 生成指令
│                  #   (含 D7 的全部约束: 多候选/标假设/标置信度/不臆造/不自动 apply)
└── meta.json      # 机器可读: 处理的错误(文件/行号/错误文本)、是否有源码上下文、fault class
```

context.md 是喂给外层 Claude 的"提示包"。它里面包含:
- 编译错误原文
- 出错位置的源码上下文窗口
- 给 Claude 的明确指令: "基于以上信息,生成 1~N 个候选修复 patch(unified diff),
  每个标注思路/假设/置信度;不确定就说不确定,不编造;这是供人 review 的草稿,不要自动 apply。"

[D5 workflow 接入] workflow 输出目录里也放这份 context.md(在 .gbs_workflow/ 下),
workflow_summary.md 指向它,提示"如需 patch 建议,见 patch_context/context.md"。

---

## 5. 与现有架构的关系

```
现有(全不动):
  tizen-gbs-build        → compiler.log + B 日志
  tizen-gbs-log-analysis → Evidence Packet
  tizen-gbs-build-workflow → build→analyze→suggest(advisory)

新增:
  tizen-gbs-patch-suggest → 消费 Evidence(或 buildlog)
                           → 收集源码上下文
                           → 产 context.md(LLM-ready)
                           → 外层 Claude 据此生成 patch

workflow 接入(D5 路 1):
  workflow 末尾增加可选阶段 → 调 patch-suggest 产 context.md 进 workflow 输出
  → workflow 结束 → 外层 Claude 读 context.md 自己生成 patch
```

---

## 6. 分阶段实施(草案,每阶段独立 PR + 停下 review)

- **PS-M1** 包骨架 + CLI + 读 Evidence(`--evidence`)+ 解析出第 1 个编译错误。⚠️以 analyzer 实际 JSON 为准。
- **PS-M2** fault class 判断(D6: 非 compile 类提示不适用)+ 源码上下文收集(D3,含降级)。
- **PS-M3** 输出契约: context.md / README.md / meta.json。context.md 含 D7 全部约束指令。
- **PS-M4** `--buildlog` 便利模式: 内部复用 analyzer(sibling skill 调用 + PYTHONPATH 合并)。
- **PS-M5** SKILL.md(Anthropic 规范)+ 参数缺失行为对齐
  (evidence/buildlog 缺 → 问; output-dir 缺 → 默认 ./.gbs_patch_suggest; src-root 对齐 analyzer)。
- **PS-M6** workflow 接入(D5 路 1): workflow 加可选阶段产 context.md。⚠️不在子进程调 LLM。
- **PS-M7** 真实验证: 用真实 E 场景(implicit declaration 那类)在 Cline 跑,确认:
  context.md 信息充分、外层 Claude 据此能生成合理 patch、skill 全程没碰源码、非 compile 类正确跳过。

---

## 7. 风险与边界

| 风险 | 应对 |
|------|------|
| 外层 Claude 生成错 patch | context.md 强制多候选+置信度+假设标注; 绝不自动 apply; 人 review gate |
| 臆造不存在的函数/头文件 | context.md 指令强制"不确定就说不确定,不编造" |
| 源码读不到 | 降级"仅错误信息"+ 明确标注可靠性降低 |
| token 爆炸 | 本期只处理 1 个错误 + 上下文窗口可配 |
| 非编译错误误用 | D6: 检测 fault class,非 compile 明确提示不适用 |
| workflow 子进程调不到外层 LLM | D5 路 1: 子进程只产 context,不调 LLM,patch 交外层 Claude |
| 与现有架构耦合 | 独立 skill; workflow 仅末尾加可选阶段,不改现有 build/analyze/suggest |

---

## 8. 核心不变量(实现必须守住)

1. skill 内部**绝不调 LLM**(不 import LLM SDK,不发 LLM 网络请求)—— D2
2. skill **绝不 apply / 不写源码树** —— D3
3. workflow 子进程内**绝不调 LLM** —— D5
4. 现有三 skill / workflow build·analyze·suggest / Suggester / pattern **零改动** —— D1
5. 本期**只处理 1 个编译错误**,只处理 **compile error 类** —— D4/D6
6. patch 永远由**外层 Claude** 生成,skill 只产 **context.md** —— 全局定位

---

## 9bis. 设计修正(基于 Codex 实际代码核对 + 真实实验)

> 触发: Codex 核对发现 analyzer 读源码常失败(source_file_unavailable),且真实实验
> (Level 2 降级, source_snippets 仅 116 token)证实这是高频常态,非边缘异常。
> 同时 token 实验发现 Claude 自己读源码仅 ~300 token,极便宜。

### [D9] 源码三级降级 —— 无源码是一等路径,不是异常

skill 按"能拿到多少源码"分三级,每级都正常成功产出 context(绝不因没源码而失败退出):

- **级别 A(有源码上下文)**: evidence.source_snippet 存在,或 patch-suggest 用 src-root 读到。
  → context.md 含源码窗口,Claude 能生成具体候选 patch。
- **级别 B(有 file:line,读不到源码)**: 
  → context.md 标明"错误在 file:line,源码不可用",指引外层 Claude 自己打开该文件读上下文。
  → 不在 context 里硬塞猜测的源码; status=source_context_unavailable。
- **级别 C(连 file:line 都没有)**: 
  → 只产 diagnostic context(错误信息 + 语义分类),不涉及源码定位。

[D10] **源码读取的责任重心 —— 待真实 A/B 分布验证后定,PS-M1 不焊死**。
  已知事实: (a) analyzer 的 src-root 直接拼接经常失败(出错文件常在 GBS-ROOT/BUILD/临时导出目录);
  (b) Claude 在 Cline 有完整文件访问,不受 src-root 限制; (c) Claude 自己读源码仅 ~300 token,便宜。
  → 倾向: skill 尽力提供源码(级别 A),拿不到就指引 Claude 自己读(级别 B)。
  → 但"主要走 A 还是 B"由 PS-M1 做完后真实跑的 A/B 分布决定,不在设计阶段拍死:
    - 真实多落级别 A(skill 读源码常成功) → 强化 skill 出 patch 能力
    - 真实多落级别 B(常失败) → 坐实"交 Claude 读"的定位
  PS-M1 三级降级都实现,正是为了让真实数据来回答这个重心问题。

[D11] **绝不基于缺失/错误上下文硬编 patch**。
  无源码时(级别 B/C)产 advisory/context,不产 .patch。
  宁可"让 Claude 自己读了再生成",不可"猜个源码编个 patch"。

### fault class 判断(核对确认 + 真实 werror 修正)

无 fault_class 字段。用: primary_error.kind in {"compiler", "werror"} 筛源码级编译诊断;
语义用 root_cause_candidates[0].semantic_class(undeclared_identifier/syntax_error/type_mismatch...)。
这与 analyzer evidence router 一致: analyzer 已经把 compiler/werror 都交给 CompileEvidenceCollector。
非 compiler/werror kind → D6 提示不适用。

### PS-M1 必须包含降级(不许只做 happy path)

[D12] PS-M1 一开始就实现三级降级骨架,不许只做"有 source_snippet 才工作"的 happy path。
  Codex 警告: 只做 happy path 的 patch-suggest 只能在 fixture 跑,真实环境立刻撞墙。
  PS-M1 DoD 含: evidence ingest + fault class 判断 + 源码三级 resolver + 级别 B/C 的 advisory 输出。

---

## 9ter. context.md 对 LLM 的强制指令(用户明确要求)

> 用户要求: context.md 必须显著提醒外层 Claude (1) 按 context.md 的规则生成最终 patch;
> (2) 生成的 patch 绝不合进文件(不 apply)。这是 D7/D11 的强化,确保 Claude 不忽略。

[D13] **每个级别的 context.md 末尾都带一个固定的、醒目的"Instructions for the assistant"块**,
包含两条强制指令(措辞要显眼,放在 Claude 最后读到的位置):

```
## ⚠️ Instructions — MUST follow

1. Generate the patch strictly according to the rules in this document:
   provide candidate(s) as unified diff, each with its approach, explicit
   assumption, and confidence; do NOT fabricate functions/headers; if uncertain,
   say so rather than guessing.

2. This patch is a SUGGESTION DRAFT ONLY. Do NOT apply it to any file.
   Do NOT run `git apply` / `patch`. Do NOT modify the source tree.
   Present the patch to the user for review; the user decides whether to apply.
```

适用所有级别(A/B/C):
- 级别 A/B: 两条都给(要生成 patch + 不准 apply)
- 级别 C: 第 2 条仍给(即使信息不足不生成 patch,也强调任何后续修复不准自动 apply)

[D14] **这两条是 context.md 的固定尾部,不可省略**。PS-M3(输出契约)实现 context.md 时,
此"Instructions — MUST follow"块作为模板的强制组成部分,任何级别都附上。

---

## 9quater. PS-M2 源码上下文收集(后缀搜索 + 消歧 + 降级)

> 触发: 真实路径摸底发现 analyzer evidence 里的 `file` 常是子模块相对路径
> (如 `libavcodec/utils.c`),而用户项目根下真实路径可能是
> `gst-libs/ext/ffmpeg/libavcodec/utils.c`。直接 `src_root / file` 必然 miss。

[D15] **PS-M2 重新引入显式 `--src-root`,但不做 auto 默认**。
  `--evidence` 模式没有 buildlog path,不能复用 analyzer 的 `auto -> buildlog parent`。
  用户未提供 `--src-root` 时,skill 不搜索源码,继续走 Level B advisory。

[D16] **源码搜索使用 src-root 内的路径段后缀精确匹配**。
  先用 basename 预筛,再比较路径段:

```
candidate.relative_to(src_root).parts[-len(evidence_parts):] == evidence_parts
```

  不用纯字符串 `endswith`,避免把 `mylibavcodec/utils.c` 误认为
  `libavcodec/utils.c`。

[D17] **搜索范围严格限制在 src-root 内,并跳过重型/无关目录**。
  跳过 `.git`, `GBS-ROOT*`, `build`, `.gbs_workflow`,
  `.gbs_patch_suggest`, `node_modules`。不跨出 src-root。

[D18] **唯一命中才升级 Level A;零匹配/多匹配都保持 Level B**。
  - 唯一命中: 读取该文件窗口(默认 ±30 行),`origin="src_root_suffix_search"`。
  - 零匹配: Level B advisory,提示源码未定位。
  - 多匹配: Level B advisory,列出候选,不硬猜。

[D19] **绝对路径也不跨 src-root**。
  - evidence.file 是绝对路径,且存在并位于 src-root 内 → 可直接读,升级 Level A。
  - 存在但位于 src-root 外 → 不读,保持 Level B。
  - 不存在 → 保持 Level B。

PS-M2 仍不做 `--buildlog`(PS-M4)、不写正式 `SKILL.md`(PS-M5)、不接 workflow(PS-M6)。

---

## 9quinquies. PS-M8 deterministic patch formatter(git 后端)

> 触发: 真实 Cline 验证发现,即使 context.md 明确要求保持 tab/space,
> 外层 Claude 手写 unified diff 仍容易把 tab 改成 space 或写错 hunk 头,
> 导致 `git apply --check` 反复失败并消耗大量 token。
> 结论: 继续加软提示有天花板,patch 格式必须交给程序确定性生成。

[D20] **允许 deterministic patch formatter,但语义决策仍由外层 Claude 做**。
  formatter 只把外层 Claude 明确给出的 edit spec 格式化成 `.patch` 文件。
  它不决定修什么、不推断修复语义、不调 LLM、不 apply、不改源码树。
  这扩展了 D2 的形式,但不破坏 D2 精神:skill 仍不做语义 patch 生成。

[D21] **formatter 使用 `git diff --no-index` 作为 patch 后端,不手拼 unified diff**。
  实现流程:
  1. 读取真实源文件,复制到临时目录 `orig/` 和 `mod/`。
  2. 只在 `mod/` 副本上应用 Claude 提供的 edit spec。
  3. 运行 `git diff --no-index -- <tmp>/orig <tmp>/mod` 生成标准 git diff。
  4. `git diff --no-index` 在有差异时通常返回 exit code 1,这不是失败;
     真正失败是命令不可用、运行错误或未产出可用 diff。
  5. 删除临时目录。

  这样 hunk 头、上下文行、tab/space 都由 git 从文件副本生成,
  Claude 不再手写 diff 格式。

[D22] **路径头必须用 edit_spec.file 重建为项目相对路径(含中间目录)**。
  `git diff --no-index` 对 `mkdtemp` 临时文件会输出随机绝对路径,例如:

```
diff --git a/tmp/tmp_xxxxx/orig/src/tdm_meson_hwc.c b/tmp/tmp_xxxxx/mod/src/tdm_meson_hwc.c
--- a/tmp/tmp_xxxxx/orig/src/tdm_meson_hwc.c
+++ b/tmp/tmp_xxxxx/mod/src/tdm_meson_hwc.c
```

  formatter 不解析这些随机临时路径,也不按字面剥 `tmp/orig` / `tmp/mod` 前缀。
  它已知 `edit_spec.edits[*].file` 是项目根相对路径,例如 `src/tdm_meson_hwc.c`,
  因此必须直接用该相对路径重建三类路径头:

```
diff --git a/src/tdm_meson_hwc.c b/src/tdm_meson_hwc.c
--- a/src/tdm_meson_hwc.c
+++ b/src/tdm_meson_hwc.c
```

  其中 `diff --git` 的 a/b 两侧都使用同一个 `edit_spec.file` 项目相对路径;
  `---` 侧使用 `a/<file>`,`+++` 侧使用 `b/<file>`。对涉及多个文件的 patch,
  每个 file diff block 都按对应 edit 的 `file` 单独重建。
  这样用户可在项目根运行 `git apply candidate_N.patch`。

[D23] **edit spec 文件路径必须限制在 src-root 内,复用 PS-M2 路径安全边界**。
  `edit_spec.edits[*].file` 可以是项目相对路径;若未来支持绝对路径,
  也必须满足“存在且位于 src-root 内”。
  禁止 `../` 或 symlink/resolve 后逃逸到 src-root 外的路径。
  这与 PS-M2 的 absolute-path-inside-src-root 边界一致。

[D24] **formatter 失败时绝不退回手写 diff**。
  如果 old 不匹配、多匹配、上下文不匹配、路径不安全、`git apply --check`
  失败,外层 Claude 必须修正 `edit_spec.json` 后重跑 formatter。
  不允许回退到手写 unified diff,否则会回到 tab/hunk/context 软约束天花板。

### edit_spec.json schema(v1)

```json
{
  "schema_version": "gbs_patch_suggest/edit-spec/v1",
  "patch_name": "candidate_1.patch",
  "description": "Fix invalid Werror condition",
  "edits": [
    {
      "file": "src/tdm_meson_hwc.c",
      "line": 515,
      "old": "exact text to replace",
      "new": "replacement text",
      "before": "optional exact context before old",
      "after": "optional exact context after old"
    }
  ]
}
```

- `file`: 必填,项目根相对路径,必须位于 `--src-root` 内。
- `line`: 推荐,用于多匹配消歧;不是单独真相,仍要验证 old/context。
- `old`: 必填,要替换/删除的真实文本片段。
- `new`: 必填,替换文本;删除可用空字符串。
- `before` / `after`: 可选但推荐,用于 old 多处重复时消歧。

Claude 不必提供完整 hunk 或含 tab 的整行上下文。`old` 只用于定位替换点;
最终 patch 上下文由 git 从临时文件副本生成。

### old 定位与多处相同 old

真实场景可能存在两处完全相同的 old 文本(如同一表达式在 515/525 两行各出现一次)。
formatter 不做 replace-all 默认行为,避免误伤。

匹配规则:
1. 若提供 `before` / `after`,优先用 `before + old + after` 做锚点匹配。
   唯一匹配才通过;零匹配/多匹配都失败并要求修正 edit spec。
2. 若无 `before` / `after`,用 `old` 全文件匹配。
   - 唯一匹配: 通过。
   - 多匹配且提供 `line`: 选择覆盖该 line 或最靠近该 line 的匹配;
     若仍无法唯一确定,失败。
   - 多匹配且无 `line`: 失败,列出候选行号,要求补 `line` 或上下文。
3. 若多处相同 old 都要改,必须写多个 edit,每个 edit 带自己的 `line`
   或 `before`/`after`。

### CLI 形态

新增 `format-patch` 子命令,与现有 context 生成路径分离:

```bash
python3 -m gbs_patch_suggest format-patch \
  --src-root /path/to/source \
  --edit-spec .gbs_patch_suggest/edit_spec.json \
  --output .gbs_patch_suggest/candidate_1.patch \
  --check
```

- `--check`: 运行 `git apply --check` 验证 patch 可应用,但绝不 apply。
- 依赖系统 `git` 命令;不要求项目本身是 git 仓库。
- 若 `git` 不存在,formatter 失败并提示安装/提供 git,不回退手写 diff。

### 与三级降级的关系

- Level A: context.md 有源码窗口。Claude 决定修复语义,写 edit_spec,
  调 formatter 生成 patch。
- Level B: 有 file:line 但无源码窗口。Claude 先按 context 指引打开 file:line
  读取源码,再写 edit_spec,仍调 formatter。
- Level C: 无 file:line。默认不运行 formatter,先补定位信息。
- not_applicable: 不运行 formatter。

### context.md / SKILL.md 更新方向

PS-M8 实施时,`How to generate the patch` 从“手写 unified diff”改为:
1. 外层 Claude 做语义判断。
2. 外层 Claude 写 `edit_spec.json`。
3. 调 `format-patch` 生成 `candidate_N.patch`。
4. formatter 失败则修 edit spec 后重试,**不手写 diff**。
5. 告诉用户 patch 路径;用户 review 后自行 `git apply`。

SKILL.md 同步改为三段式:
1. run patch-suggest 产 context.md;
2. Claude 读 context.md 并写 edit spec;
3. Claude 调 formatter 生成 `.patch`,但不 apply。

PS-M8 不改 analyzer/workflow/resolver 三级降级/werror/别读 log/list_files/python3 入口引导。

---

## 9sexies. Large-scale error cluster patch context

> 触发: 真实 `capi-network-bluetooth` buildlog 中有 55+ 个
> `-Wimplicit-enum-enum-cast` / `-Werror` 源码级诊断,横跨 11 个文件,
> analyzer 已通过 `error_clusters` + `error_clusters.json` 暴露全量聚类位置。
> 现有 patch-suggest 只消费 `primary_error`,导致外层 Claude 只修 1 处,
> 形成“修 primary 就够了”的错误信号。

[D25] **large-scale cluster mode 的触发条件必须全部满足**。

触发 cluster mode 需要:

1. Evidence Packet 中存在 `error_clusters`。
2. 至少一个 cluster 满足 `large_scale == true`。
3. `error_clusters.full_locations_path` 指向的 sidecar 可读。
4. cluster 是 source diagnostic 类: `kind == "source_warning_option"`,
   且 `diagnostic_kinds` 仅包含或主要包含 `compiler` / `werror`。

如果存在多个 large-scale source diagnostic cluster,patch-suggest 处理**全部**满足条件的 cluster,
按 Evidence Packet 中 `clusters[]` 的顺序输出独立 cluster 子目录。每个 cluster 独立生成
per-file context,不把不同 warning option 的修复混成一个 patch 计划。

如果 sidecar 不可读或 schema 不匹配,不让整个 skill 失败;回退到既有 single diagnostic
流程,并在 meta/README 中记录 `cluster_sidecar_unavailable` advisory。

[D26] **cluster mode 只处理 analyzer evidence 暴露的位置,绝不读 raw log**。

patch-suggest 的输入边界保持不变:

- 可处理位置 = `error_clusters.json` sidecar 中列出的 locations。
- 不打开、不扫描、不 grep 原始 buildlog。
- 不尝试发现 sidecar 之外的零散非 cluster 错误。

因此“该文件所有 error”在 cluster mode 中精确定义为:

> 该 file 在当前 analyzer cluster sidecar 中列出的所有 locations。

如果 raw log 里还有其它未被 analyzer 聚类暴露的错误,它们对 patch-suggest 是
`not visible in evidence`,本阶段不处理。context.md 必须把这个边界说清楚,
避免外层 Claude 以为工具已经覆盖 raw log 中所有可能错误。

[D27] **源码窗口按文件、按 location 生成,默认 ±8 行,重叠窗口合并**。

对每个 cluster location,在对应源码文件中取窗口:

```
start = max(1, line - 8)
end   = min(file_line_count, line + 8)
```

选择 ±8 行的理由:

- 比单点错误的 ±30 行更克制,适合一个文件内多个重复诊断。
- 对 enum-cast / Werror 这类局部表达式错误通常足够看清语句和相邻上下文。
- 降低一文件 20+ 个 location 时的 token 爆炸风险。

同一文件内窗口按起始行排序,若两个窗口重叠或相邻间隔不超过 2 行,合并成一个连续窗口。
合并后仍列出该文件所有 locations,并在窗口标题中标出覆盖了哪些 diagnostic line。

若某个 per-file context 的源码窗口合计超过 400 行,仍列出该文件全部 locations,
但源码窗口只渲染到 400 行上限,并标记 `source_windows_truncated=true`。
context.md 必须提示外层 Claude 对未渲染窗口按 file:line 精确打开源码,而不是读 raw log。

[D28] **输出组织固定为 top-level overview + cluster 子目录 + per-file context**。

cluster mode 输出仍使用同一个 `--output-dir`,在既有 `README.md` / `context.md`
/ `meta.json` 旁边新增 `cluster_context/`:

```
.gbs_patch_suggest/
├── README.md
├── context.md
├── meta.json
└── cluster_context/
    └── CL001_-Wimplicit-enum-enum-cast/
        ├── index.md
        └── files/
            ├── 001_device_common_foo_c.md
            ├── 002_adapter_bar_c.md
            └── ...
```

命名规则:

- cluster 目录: `{cluster_id}_{warning_option_slug}`。
- per-file context: `{NNN}_{file_slug}.md`,其中 NNN 按该文件在 sidecar 首次出现顺序编号。
- `file_slug` 从项目相对路径生成: `/` 和非 `[A-Za-z0-9._-]` 字符替换为 `_`,
  必要时截断,但 meta/index 中保留完整原始 file 路径。

top-level `context.md` 在 cluster mode 中变成“cluster overview”,只列 cluster 总览、
每个文件 context 路径、逐文件处理顺序和不读 raw log/不 apply 的规则。
具体源码窗口放在 `cluster_context/.../files/*.md` 中。

[D29] **默认 patch 策略是一文件一 patch,不是一个巨型多文件 patch**。

对于一个 cluster 中的 N 个文件,默认输出 N 个 per-file patch 计划:

- 每个 per-file context 引导外层 Claude 为该文件写一个 edit spec。
- 该 edit spec 包含该文件中 sidecar 暴露的所有需要修复 locations。
- 调 PS-M8 `format-patch` 生成一个该文件对应的 patch。

推荐命名:

```
edit_spec_CL001_001_device_common_foo_c.json
candidate_CL001_001_device_common_foo_c.patch
```

一文件一 patch 的理由:

- review 粒度清晰,用户可以逐个检查和 apply。
- 失败时只影响一个文件,便于修正 edit spec。
- 复用 formatter 已支持的“同文件多 edits → multi-hunk patch”能力。

formatter 技术上可以生成多文件 patch,但 cluster mode 不默认引导这么做。
多文件 patch 只能作为用户明确要求时的高级用法,不作为本阶段默认流程。

[D30] **token 策略:Claude 逐文件处理,不要一次加载全部 11 个 per-file context**。

cluster mode 的 Claude-facing token 模型是:

1. 先读 top-level `context.md` / cluster `index.md` 了解规模和文件清单。
2. 一次只打开一个 `files/{NNN}_{file_slug}.md`。
3. 为该文件生成 edit spec + patch。
4. 再处理下一个文件。

context 必须明确写:

- Do not load every per-file context at once.
- Process one file at a time.
- Do not read the raw buildlog.

per-file context 是 Claude-facing 输出,需要控制体积;sidecar `error_clusters.json`
是机器输入,不要求 Claude 直接阅读,也不纳入 per-file context token 预算。

未来若 workflow/downstream token 统计扩展到 cluster mode,应按用户实际推荐阅读路径计:
overview + 当前 per-file context,而不是 overview + 所有 per-file contexts 一次性求和。

[D31] **无 large-scale cluster 时退回原 single diagnostic 流程**。

以下情况保持现有 patch-suggest 行为不变:

- packet 没有 `error_clusters`。
- 没有任何 cluster `large_scale == true`。
- cluster 没有 source diagnostic locations。
- cluster sidecar 不可读或无可用 locations。

此时仍按 PS-M1~PS-M8 的 single diagnostic 流程:
`primary_error` → 三级 resolver → `context.md` → 外层 Claude 写 edit spec → formatter。

小规模重复错误仍可由 single diagnostic + root-cause guidance 覆盖;
本阶段不为小规模 cluster 额外生成 per-file context,避免改变既有少数错误 case 的交互成本。

[D32] **源码定位失败时 per-file context 降级为 advisory,不硬猜,不生成 patch**。

cluster mode 对每个 sidecar file 复用 PS-M2 的 src-root suffix search 和安全边界:

- 唯一命中:读取该文件窗口,生成 per-file Level A context。
- 零匹配:生成 per-file advisory,列出该 file 的所有 cluster locations,
  指引外层 Claude 按 file:line 自己打开源码。
- 多匹配:生成 per-file ambiguous advisory,列候选路径,要求外层 Claude 先选择正确文件。
- 绝对路径仍必须位于 src-root 内,否则不读。

零匹配/多匹配时不生成 patch,不硬猜源码,不把缺失源码上下文伪装成可直接修复。

[D33] **cluster mode 是纯叠加新模块,不改 single diagnostic resolver/render/formatter 语义**。

实现时新增模块优先:

- `cluster_ingest.py`: 从 packet + sidecar 读取 large-scale source clusters。
- `cluster_resolver.py`: 按文件分组、源码定位、窗口合并。
- `cluster_render.py`: 渲染 overview/index/per-file context/meta 扩展。

既有 single diagnostic 路径保持稳定:

- 不改 `extract_first_diagnostic` 的语义。
- 不改 `resolve_context` 的三级降级逻辑。
- 不改 PS-M8 formatter 的 edit spec / git backend / no-apply 不变量。
- 不改 werror 接纳范围、别读 log、python3/list_files 引导。

如果实现需要抽共享 helper,只能做无行为变化的提取,并用测试证明 single diagnostic
输出不退化。

[D34] **workflow 调用方式不变;patch-suggest 内部多产 cluster_context**。

PS-M6 workflow 仍只调用 patch-suggest 一次,传 `--evidence` 和 `--src-root`。
workflow 不需要知道 cluster mode 的内部细节:

- patch-suggest 若检测到 large-scale cluster,在同一 output-dir 下多写 `cluster_context/`。
- workflow 现有 `patch_context/context.md` 路径仍存在,作为 overview。
- workflow exit code/verdict/suggestions/token 主流程不变。

workflow_summary 是否展示 cluster_context 的文件清单可作为后续增强;
本阶段不要求修改 workflow。若后续修改 workflow,也必须是 summary-only additive,
不改变 build/analyze/suggest/verdict/exit code。

[D35] **实现 PR 范围锁定为 cluster context 生成,不做 raw-log 分析或自动修复**。

Implementation PR 允许:

- 新增 cluster ingest/resolver/render 模块。
- CLI 在 `run_patch_suggest` 中检测并触发 cluster mode。
- meta/README/context 增加 cluster mode 字段和输出路径。
- 测试 large-scale cluster sidecar、按文件分组、窗口合并、源码 miss/ambiguous、
  小规模退化、single diagnostic 非回归。

Implementation PR 禁止:

- 读取 raw buildlog 来补充 locations。
- 自动生成 edit spec 或 patch。
- 自动调用 formatter。
- 自动 apply patch 或写源码树。
- 修改 analyzer/build/workflow/Suggester/pattern。
- 改变 single diagnostic 的输出语义。

---

## 9septies. Cluster mode Level A edit-spec skeletons

> 触发: 真实 cluster mode 验证发现,外层 Claude 面对 11 个文件逐个写
> edit spec + 调 formatter 的流程时,可能为了省事直接修改源码,违反“不 apply / 不写源码”铁律。
> 继续加强软约束不足以根治;需要把合规路径做得比越权路径更省事。

[D36] **Level A per-file context 必须预生成 edit_spec skeleton**。

当 cluster mode 的某个 file context 达到 Level A(`source_context_available`)时,
patch-suggest 为该文件生成一个 edit spec skeleton:

```json
{
  "schema_version": "gbs_patch_suggest/edit-spec/v1",
  "patch_name": "candidate_CL001_001_device_common_c.patch",
  "description": "Fill new values for all listed source diagnostics in this file.",
  "edits": [
    {
      "file": "src/device_common.c",
      "line": 119,
      "old": "\t... exact original source line ...",
      "new": "<FILL_REPLACEMENT_LINE>"
    }
  ]
}
```

预填字段:

- `file`: sidecar location 的项目相对路径。
- `line`: sidecar location 的行号。
- `old`: 真实源码的整行文本,从 `lines[line - 1]` 提取。
- `new`: 固定占位符 `"<FILL_REPLACEMENT_LINE>"`。

`old` 必须保留源码原始 tab/space,不 `strip`,不转换缩进;JSON 写出时由
`json.dumps` 正常转义。整行 old + line 的目标是最大化 formatter 一次匹配成功率,
避免外层 Claude 自己构造 old 时产生格式/缩进错误。

[D37] **同一 file 的同一 line 只生成一个 edit,但不丢 location 信息**。

同一个文件中若多个 cluster locations 指向同一行,edit spec skeleton 只生成一条 edit:

```
dedupe key = (file, line)
```

理由:

- formatter 不允许 overlapping edits。
- 同一行多诊断通常应由同一个 replacement line 处理。

但 context/meta 仍必须列出该行的所有 locations/messages/event_id,不得因为 edit 去重而丢失诊断事实。
per-file context 应把“该 edit 覆盖哪些 diagnostic messages”讲清楚,让外层 Claude 填写
`new` 时能同时考虑同一行的多个问题。

[D38] **每个 skeleton edit 必须带诊断 message 辅助 Claude 填写 new**。

edit spec schema 本身不扩展 message 字段,避免破坏 formatter schema。
诊断 message 放在 per-file context 的 location 列表和 skeleton 指引中:

- context.md 列出 line/column/message/event_id。
- 若同一 edit 覆盖多个 location,context.md 标注这些 messages 都对应同一个 skeleton edit。

Claude 根据 message 和源码窗口填写 `new`,但不需要自己重新抄 `file`/`line`/`old`。

[D39] **Level B / ambiguous / C 不生成 skeleton**。

以下状态不预生成 edit spec skeleton:

- `source_context_unavailable`
- `source_context_ambiguous`
- `diagnostic_only`
- `not_applicable`

理由:没有唯一源码文件或无法取得真实行文本时,预填 `old` 会误导外层 Claude,
并可能让 formatter 失败。此时保持 advisory:先打开/确认源码,再由 Claude 自行写 edit spec。

[D40] **before/after 初版不默认生成**。

skeleton 默认只填 `file` / `line` / `old` / `new`。

不默认填 `before` / `after` 的理由:

- 整行 old + line 已经是稳定定位组合。
- before/after 会增大 skeleton 体积。
- before/after 也可能引入额外文本匹配失败面。

若 formatter 后续报 `old_not_unique` 或 `context_not_unique`,外层 Claude 再按 formatter
错误码补 `before` / `after` 并重跑 formatter。不要因为少数失败场景让所有 skeleton 变重。

[D41] **越界 line 不生成 edit,并标记 missing_line_text**。

如果 sidecar location 的 line 不在源码文件范围内:

- 不为该 location 生成 edit。
- per-file context 仍列出该 location。
- meta/context 标记 `missing_line_text`。
- 指引外层 Claude 按 file:line 重新检查源码或确认 analyzer location 是否过期。

越界 line 不能用猜测 old,也不能退回手写 diff。

[D42] **skeleton 输出到独立 edit_specs/ 目录**。

cluster mode 输出结构扩展为:

```
.gbs_patch_suggest/
└── cluster_context/
    └── CL001_-Wimplicit-enum-enum-cast/
        ├── index.md
        ├── files/
        │   └── 001_device_common_c.md
        └── edit_specs/
            └── edit_spec_CL001_001_device_common_c.json
```

`files/` 只放 per-file markdown context;`edit_specs/` 只放 skeleton JSON。
per-file context 必须指向对应 skeleton 路径,避免 Claude 探目录。

[D43] **token 策略:per-file context 指向 skeleton,不重复展开 skeleton 内容**。

skeleton 是 Claude-facing 操作文件,但不应在 per-file context 中全文重复。
推荐阅读路径:

1. 读 overview / index。
2. 一次打开一个 per-file context。
3. 打开该 per-file context 指向的 skeleton JSON。
4. 填写 skeleton 的 `new` 字段。
5. 调 formatter。

per-file context 应说明 skeleton 的关键字段和路径,但不要把完整 JSON 再复制一遍。
这样避免“源码窗口 + skeleton old”双重展开导致 token 翻倍。

[D44] **per-file How-to 必须把“填 skeleton”放在第一位**。

Level A per-file context 的 patch 流程改为:

1. 打开本文件对应的 generated edit spec skeleton。
2. 保留 `file` / `line` / `old` 不变,除非 formatter 报具体 mismatch。
3. 只填写每个 edit 的 `new`。
4. 运行 `format-patch --check`。
5. 若 formatter 失败,修正 skeleton 后重跑 formatter。
6. 不直接改源码文件,不手写 unified diff,不 apply patch。

目标是让“走 skeleton + formatter”成为最省事路径,降低外层 Claude 越权直接写源码的动机。

[D45] **实现影响面限制在 cluster mode**。

Implementation 允许改:

- `cluster_resolver.py`: 提取 line text / missing_line_text 信息。
- `cluster_render.py`: 写 `edit_specs/*.json`,更新 per-file context 指引和 meta。
- cluster mode 相关测试。

Implementation 禁止改:

- single diagnostic `extract_first_diagnostic` / `resolve_context` / `render_context` 语义。
- formatter schema 和 formatter matching 行为。
- analyzer/build/workflow/Suggester/pattern。
- werror 接纳范围、别读 log/list_files/python3 引导。

[D46] **实现 PR 范围:只预生成 skeleton,不自动填 new、不自动运行 formatter**。

Implementation PR 只生成 skeleton JSON 和更新 context 指引。
它不做语义修复,不填 `new`,不调用 `format-patch`,不生成 `.patch`,
不运行 `git apply --check`,不 apply,不写源码树。

外层 Claude 仍负责语义判断和填写 `new`;用户仍负责 review 和最终 apply。
