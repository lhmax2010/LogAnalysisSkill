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

```text
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

```text
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

遵循项目既有节奏: frozen design → Codex 复述 → 分阶段 PR → 真实验证。

- **PS-M1** 包骨架 + CLI + 读 Evidence(`--evidence`)+ 解析出第 1 个编译错误。⚠️以 analyzer 实际 JSON 为准。
- **PS-M2** fault class 判断(D6: 非 compile 类提示不适用)+ 源码上下文收集(D3,含降级)。
- **PS-M3** 输出契约: context.md / README.md / meta.json。context.md 含 D7 全部约束指令。
- **PS-M4** `--buildlog` 便利模式: 内部复用 analyzer(sibling skill 调用 + PYTHONPATH 合并)。
- **PS-M5** SKILL.md(Anthropic 规范)+ 参数缺失行为对齐
  (evidence/buildlog 缺 → 问; output-dir 缺 → 默认 ./.gbs_patch_suggest; src-root 对齐 analyzer)。
- **PS-M6** workflow 接入(D5 路 1): workflow 加可选阶段产 context.md。⚠️不在子进程调 LLM。
- **PS-M7** 真实验证: 用真实 E 场景(implicit declaration 那类)在 Cline 跑,确认:
  context.md 信息充分、外层 Claude 据此能生成合理 patch、skill 全程没碰源码、非 compile 类正确跳过。

每个 milestone 独立 PR + 停下 review,和你一贯流程一致。

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

### fault class 判断(核对确认)

无 fault_class 字段。用: primary_error.kind == "compiler" 筛 compile 类;
语义用 root_cause_candidates[0].semantic_class(undeclared_identifier/syntax_error/type_mismatch...)。
与现有 CompileErrorSuggester 一致。非 compiler kind → D6 提示不适用。

### PS-M1 必须包含降级(不许只做 happy path)

[D12] PS-M1 一开始就实现三级降级骨架,不许只做"有 source_snippet 才工作"的 happy path。
  Codex 警告: 只做 happy path 的 patch-suggest 只能在 fixture 跑,真实环境立刻撞墙。
  PS-M1 DoD 含: evidence ingest + fault class 判断 + 源码三级 resolver + 级别 B/C 的 advisory 输出。
