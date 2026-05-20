# GbsBuildWorkflow v0.1 设计文档

**版本**: v0.1（首版，与 LogAnalysisSkill v0.5 集成）
**仓库**: https://github.com/lhmax2010/LogAnalysisSkill（Monorepo + 子目录）
**目标**: AI 助手能一键完成"gbs 编译 → 失败时分析 → 输出修复建议"流程
**文档状态**: 修订版（基于 BW-M1 完成 + 范围扩展）

## 0. 修订记录

| 版本 | 日期 | 修订点 |
|------|------|--------|
| v0.1 initial | 2026-05-20 | 首版（1 Suggester / 3 milestone）— 见 archive/ |
| v0.1 (current) | 2026-05-20 | BW-M1 完成；BW-M2 范围扩展到 7 个 Suggester（含 6 advisory + Fallback）；新增 BW-M4 E2E milestone |

## 1. 设计哲学

> Workflow 是编排者，不是决策者。它产出**所有错误类型的修复建议候选**（含说明 + risks），
> **不自动 apply 任何 patch**。用户 review 后自己决定 apply / reject / 修改。
> 多轮修复由用户手动驱动（修完一次重新跑 workflow），保持每一步可控。

## 2. 仓库结构

```
LogAnalysisSkill/                          # Monorepo
├── gbs_analyzer/                          # v0.5 MVP（不动）
├── gbs_build_skill/                       # ✅ BW-M1 已完成
│   ├── __init__.py
│   ├── __main__.py
│   ├── runner.py
│   └── README.md
├── gbs_workflow/                          # BW-M2 / M3 待实现
│   ├── __init__.py
│   ├── __main__.py
│   ├── workflow.py
│   ├── suggesters/
│   │   ├── __init__.py
│   │   ├── base.py                        # SuggesterBase ABC
│   │   ├── registry.py
│   │   ├── depsolve.py
│   │   ├── linker_missing.py
│   │   ├── linker_undef.py
│   │   ├── patch_failed.py
│   │   ├── spec_script.py
│   │   ├── compile_error.py
│   │   └── fallback.py
│   └── README.md
├── tests/
│   ├── unit/
│   │   ├── test_build_runner.py           # ✅ BW-M1
│   │   ├── test_workflow.py               # BW-M2
│   │   └── suggesters/                    # BW-M2 / M3
│   └── e2e/
│       └── test_workflow_e2e.py           # BW-M4
└── docs/
    ├── DESIGN.md                          # v0.5 analyzer（不动）
    ├── build_workflow/
    │   ├── DESIGN.md                      # 本文档
    │   └── archive/
    │       └── DESIGN_v0.1_initial.md     # 原版 v0.1
    └── CODEX_PROMPT.md
```

## 3. gbs_build_skill（编译 skill）✅ BW-M1 已完成

### 3.1 职责
**单一职责**：调用 gbs 命令，输出 buildlog 和 exit code。

### 3.2 接口

```bash
python -m gbs_build_skill \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --output-log ./out/compiler.log \
    --timeout 1800
```

Python API：
```python
from gbs_build_skill.runner import run_gbs_build, BuildOptions

result = run_gbs_build(BuildOptions(
    conf=Path("gbs.conf"),
    arch="armv7l",
    output_log=Path("./out/compiler.log"),
    timeout=1800,
    include_all=True,
))
# result.exit_code: int
# result.log_path: Path
# result.duration_seconds: float
# result.timed_out: bool
```

### 3.3 Exit code 约定
- 0：build 成功
- 1：build 失败（gbs 退出非 0）
- 124：超时
- 127：gbs 命令未找到

### 3.4 不做的事
- 不解析 buildlog
- 不调用 analyzer
- 不修复代码

### 3.5 BW-M1 实施记录
- 完成日期：2026-05-20
- Merge commit：`42cee36`
- 真实验证：ffmpeg `tizen` (build success) + `real_smoke/B_*` (depsolve failure)
- 详细：见 `.dev_memory/bw_m1_build_skill/`

## 4. gbs_workflow（编排器）— BW-M2 / M3 待实现

### 4.1 职责

```
1. 调用 gbs_build_skill
2. 检查 exit code:
   - 0 → 退出，打印 "Build succeeded"
   - 非 0 → 第 3 步
3. subprocess 调用 gbs_analyzer 分析 buildlog
4. 读 evidence_packet.json
5. 把 evidence_packet.md 展示给用户
6. 遍历所有 Suggester，每个匹配的 Suggester 产生 0~N 个 Suggestion
7. 写入 .gbs_workflow/suggestions/ 目录（.patch + .md）
8. 退出，输出 workflow_summary.md
```

### 4.2 接口

```bash
python -m gbs_workflow \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root . \
    --output-dir .gbs_workflow \
    --timeout 1800
```

### 4.3 输出目录结构

```
.gbs_workflow/
├── compiler.log                           # gbs_build_skill 的 buildlog
├── analyzer_output/                       # gbs_analyzer 输出（仅在 build 失败时）
│   ├── evidence_packet.json
│   ├── evidence_packet.md
│   ├── perf_report.json
│   └── trace.jsonl
├── suggestions/                           # Suggester 输出
│   ├── 001_<suggester>_<id>.patch        # 仅 patch 类型有此文件
│   ├── 001_<suggester>_<id>.md           # 所有类型都有
│   └── ...
└── workflow_summary.md                    # 编排总结
```

### 4.4 Suggester ABC

```python
@dataclass
class Suggestion:
    suggester: str                          # 哪个 suggester 生成的
    title: str                              # 简短描述
    description: str                        # 详细说明
    patch_content: str | None               # git patch 文本，None 表示无 patch（仅引导）
    target_files: list[str]                 # 这个 patch 影响哪些文件
    confidence: str                         # "medium" / "low" / "advisory"
    risks: list[str]                        # 已知风险
    manual_steps: list[str] | None          # 没法生成 patch 时，提供手动步骤


class SuggesterBase(ABC):
    """每个 Suggester 对应一类错误。"""
    
    @abstractmethod
    def matches(self, packet: dict) -> bool:
        """这个 packet 是否适合本 suggester 处理？"""
    
    @abstractmethod
    def generate(self, packet: dict, src_root: Path) -> list[Suggestion]:
        """返回 Suggestion 对象列表，可以为空。"""
```

**关键设计**：
- 所有 Suggester 都至少输出说明 .md，advisory 类不带 patch_content
- MVP 阶段 confidence 字段**仅供用户参考**，不影响 workflow 行为
- 用户看 .md 文件里的 confidence + risks 自己判断是否 apply

### 4.5 MVP 阶段 7 个 Suggester

| Suggester | 触发条件 | 输出 | confidence |
|-----------|---------|------|-----------|
| **DepsolveSuggester** | primary_error.kind == "depsolve" | spec 加 BuildRequires patch | medium |
| **LinkerMissingSuggester** | primary_error.kind == "linker_missing" | 候选 BuildRequires patch（含 -devel 候选）+ -L 路径引导 | low |
| **LinkerUndefSuggester** | primary_error.kind == "linker_undef" | 引导：检查符号声明 / .o 是否链接 / 缺哪个 -l | advisory |
| **PatchFailedSuggester** | primary_error.kind == "patch" | 引导：检查 .rej / 重新生成 patch | advisory |
| **SpecScriptSuggester** | primary_error.kind in ("spec_script", "rpm_phase") | 展示 spec 失败段 + 引导审查 | advisory |
| **CompileErrorSuggester** | primary_error.kind == "compiler" | 展示源码位置 + semantic_class + 引导 | advisory |
| **FallbackSuggester** | 上述都没匹配 | 通用引导：如何手动 review evidence_packet | advisory |

### 4.6 workflow_summary.md 输出格式

```markdown
# Workflow Summary

**Build status**: failed (exit 1)
**Failed phase**: %build
**Top-1 root cause**: linker_undef (undefined reference to <symbol>)

## Suggestions Generated

| # | Suggester | Title | Confidence | Has Patch |
|---|-----------|-------|------------|-----------|
| 001 | LinkerUndefSuggester | Resolve undefined reference in <file> | advisory | No (guidance only) |

## What to do next

1. Read `analyzer_output/evidence_packet.md` for full diagnosis
2. Read each `suggestions/*.md` for proposed fixes
3. For patch suggestions: run `git apply suggestions/<file>.patch` if you accept
4. For advisory suggestions: follow manual_steps in the .md
5. Re-run `python -m gbs_workflow` after applying changes
```

### 4.7 不做的事（v0.1 边界）
- ❌ 不自动 apply patch
- ❌ 不自动 retry build
- ❌ 不修改源代码（只写 .patch 和 .md 文件）
- ❌ 不做 multi-error 复合（只用 primary_error）
- ❌ 不做 confidence-based 行为分支（v0.2 评估）
- ❌ 不接 Compiling Agent（v0.2）

## 5. Cline 接入

`integrations/cline/build_workflow.json`：

```json
{
  "name": "gbs_build_with_analysis",
  "description": "Run gbs build, analyze failures, generate fix suggestions",
  "command": "python",
  "args": [
    "-m", "gbs_workflow",
    "--conf", "gbs.conf",
    "--arch", "armv7l",
    "--include-all",
    "--src-root", "${workspaceFolder}",
    "--output-dir", "${workspaceFolder}/.gbs_workflow"
  ],
  "post_process": {
    "read_file": ".gbs_workflow/workflow_summary.md",
    "feed_to_llm": true,
    "system_prompt": "你是 Tizen 构建专家。Workflow 已分析失败并生成修复建议。请帮用户判断哪些 suggestion 适合 apply。"
  }
}
```

## 6. 实施计划

4 个 milestone，估计 4-5 days：

| Milestone | 内容 | 工作量 | 状态 |
|-----------|------|--------|------|
| **BW-M1** | gbs_build_skill 实现 + UT + 真实 gbs smoke | 1 day | ✅ 已完成（merge `42cee36`）|
| **BW-M2** | gbs_workflow 主流程 + Suggester ABC + DepsolveSuggester | 1 day | 待启动 |
| **BW-M3** | 其余 6 个 Suggester + FallbackSuggester + workflow_summary.md | 1.5 days | 待启动 |
| **BW-M4** | E2E 测试（用 hotfix_002 的 A/B/C/D fixture）+ Cline 接入示例 + 文档 | 1 day | 待启动 |

每个 milestone：feature 分支 + dev_memory + PR + review，按 v0.5 hotfix 周期模式。

dev_memory 目录：`.dev_memory/bw_m{N}_<name>/`

## 7. 验收标准

### MVP 验收（BW-M4 完成时）
- ✅ `python -m gbs_workflow` 在 ffmpeg 项目跑通
- ✅ Build 成功时 workflow 正常退出，输出 workflow_summary.md
- ✅ 4 类已知错误（A/B/C/D fixture）全部触发对应 Suggester：
   - A linker_undef → LinkerUndefSuggester（advisory）
   - B depsolve → DepsolveSuggester（patch）
   - C patch failed → PatchFailedSuggester（advisory）
   - D rpm_phase → SpecScriptSuggester（advisory）
- ✅ 未知错误（unknown kind）→ FallbackSuggester
- ✅ DepsolveSuggester 生成的 patch 可用 `git apply` 直接 apply
- ✅ 所有 advisory 类型都有 manual_steps

### 不退化 gate
- gbs_analyzer 所有 346 tests pass
- gbs_build_skill 所有 BW-M1 tests pass
- 整体 coverage ≥ 95%

## 8. v0.2 输入（不做但记录）

1. 自动 apply patch（基于 confidence-based 决策）
2. 自动 retry build（multi-iteration loop）
3. Multi-root-cause 复合修复
4. Patch 推荐质量评估（基于 confidence 真实数据校准）
5. Tizen 仓库知识库（让 LinkerMissingSuggester 能精确推断 BuildRequires）
6. Compiling Agent 接入

## 9. 风险

| 风险 | 缓解 |
|------|------|
| gbs 命令在不同环境差异大 | --conf 参数，用户提供 gbs.conf |
| Suggester 生成的 patch 在某些 spec 上不能 apply | 每个 patch 配 .md 说明 + apply 命令，用户 review |
| workflow 超时 / hang | --timeout 参数（默认 30 分钟）|
| 用户误以为 advisory 是 patch（直接 apply 空 patch） | workflow_summary.md 明确标注 "Has Patch: No" |
| 7 个 Suggester 工作量超 1.5 天 | M3 优先做 Depsolve（带 patch），其他 6 个用模板化方式快速实现 |