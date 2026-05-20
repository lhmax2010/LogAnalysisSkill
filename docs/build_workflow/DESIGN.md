# GbsBuildWorkflow v0.1 设计

**版本**: v0.1（首版，与 LogAnalysisSkill v0.5 集成）
**仓库**: https://github.com/lhmax2010/LogAnalysisSkill（Monorepo + 子目录）
**目标**: 让 AI 助手能一键完成"gbs 编译 → 分析失败 → 输出修复建议"流程

## 1. 设计哲学

> Workflow 是编排者，不是决策者。Workflow 只负责：触发 build / 调用 analyzer / 
> 生成 suggestion patches / 展示给用户。**修不修、怎么修、是否重试，全部由用户决定。**

## 2. 仓库结构

```
LogAnalysisSkill/                          # Monorepo
├── gbs_analyzer/                          # v0.5 MVP（不动）
├── gbs_build_skill/                       # 新增：编译 skill（v0.1）
│   ├── __init__.py
│   ├── __main__.py                        # python -m gbs_build_skill
│   ├── runner.py                          # 跱 gbs 编译
│   └── README.md
├── gbs_workflow/                          # 新增：编排器（v0.1）
│   ├── workflow.py                        # 单文件 Python 脚本
│   ├── suggesters/                        # 各类错误的 patch 生成器
│   │   ├── __init__.py
│   │   ├── base.py                        # SuggesterBase ABC
│   │   ├── depsolve.py                    # depsolve → BuildRequires patch
│   │   └── ...（v0.2 扩展）
│   └── README.md
├── tests/
│   ├── unit/
│   │   ├── test_build_runner.py
│   │   ├── test_workflow.py
│   │   └── test_suggesters/...
│   └── e2e/
│       └── test_workflow_e2e.py
└── docs/
    ├── DESIGN.md                          # v0.5 analyzer 设计（不动）
    ├── BUILD_SKILL_DESIGN.md              # 新增（v0.1）
    └── WORKFLOW_DESIGN.md                 # 新增（v0.1）
```

## 3. gbs_build_skill 设计

### 3.1 职责
只做一件事：**调用 gbs 命令，输出 buildlog 文件和 exit code**。

### 3.2 接口

```bash
python -m gbs_build_skill \
    --conf gbs.conf \
    --arch armv7l \
    --include-all \
    --output-log ./out/compiler.log \
    --timeout 1800
```

输出：
- `compiler.log` 文件（gbs stdout+stderr 合并）
- exit code（0=成功，非 0=失败）

### 3.3 不做的事
- 不解析 buildlog
- 不调用 analyzer
- 不修复代码
- 不自动 retry

## 4. gbs_workflow 设计

### 4.1 职责
编排 build_skill 和 analyzer 的调用顺序，根据 evidence_packet 生成 suggestion patches。

### 4.2 流程

```
1. 调用 gbs_build_skill 跱 gbs
2. 检查 exit code:
   - 0 (成功) → workflow 退出，打印 "Build succeeded"
   - 非 0 (失败) → 进入第 3 步
3. subprocess 调用 gbs_analyzer 分析 buildlog
4. 读 evidence_packet.json
5. 把 evidence_packet 展示给用户（markdown 友好格式）
6. 根据 packet 找匹配的 Suggester:
   - 没匹配 → "No automated suggestion available, please review evidence_packet.md"
   - 有匹配 → 生成 suggestion_patches/*.patch + 每个 patch 配一个 .md 说明文件
7. 退出，告诉用户 patch 文件位置
8. 用户自己决定 apply / reject / 修改 / 手动改
```

### 4.3 输出目录结构

```
.gbs_workflow/
├── compiler.log                           # gbs 完整 buildlog
├── analyzer_output/                       # gbs_analyzer 全套输出
│   ├── evidence_packet.json
│   ├── evidence_packet.md
│   ├── perf_report.json
│   └── trace.jsonl
└── suggestions/                           # workflow 生成的修复建议
    ├── 001_depsolve_libssl.patch          # 实际 git patch
    ├── 001_depsolve_libssl.md             # 说明：解决什么问题 + 怎么 apply
    └── ...
```

### 4.4 Suggester 接口

```python
class SuggesterBase(ABC):
    """每个 Suggester 对应一类错误，从 evidence_packet 生成 0~N 个 patch。"""
    
    @abstractmethod
    def matches(self, packet: dict) -> bool:
        """这个 packet 是否适合本 suggester 处理？"""
    
    @abstractmethod
    def generate(self, packet: dict, src_root: Path) -> list[Suggestion]:
        """返回 Suggestion 对象列表，每个含 patch 内容 + 说明。"""

@dataclass
class Suggestion:
    title: str                              # 简短说明（如 "Add BuildRequires for libssl"）
    description: str                        # 详细说明（修什么、为什么、风险）
    patch_content: str                      # git diff 格式的 patch 文本
    target_file: str                        # 该 patch 改的文件路径
    confidence: str                         # "high" / "medium" / "low"
    risks: list[str]                        # 已知风险/局限
```

### 4.5 MVP 阶段实现的 Suggester

**仅 1 个：`DepsolveSuggester`**

输入条件：
- packet.verdict == "direct_answer"
- packet.matched_tier == "tier1"
- packet.primary_error.kind == "depsolve"

输出：
- 1 个 patch：在 spec 文件的 BuildRequires 段加 `BuildRequires: pkgconfig(<lib_name>)`
- 1 个说明文档：解释这个修复的逻辑 + 如果 lib_name 不在 Tizen 仓库的备选方案

**其他错误类型的处理**：
- workflow 仍调用 analyzer，展示 evidence_packet
- 但 suggestions/ 目录为空，输出 "No automated suggestion for this error type. Please review evidence_packet.md."

### 4.6 不做的事（v0.1 边界）
- ❌ 不自动 apply patch
- ❌ 不自动 retry build
- ❌ 不修改源代码（只生成 patch 文本）
- ❌ 不处理 patch_failed / spec_script / compile_error / linker（v0.2+ 再加）
- ❌ 不做 multi-error 复合修复（只处理 primary_error）

## 5. 集成方式（Cline / Compiling Agent）

### 5.1 Cline 接入

新增 `integrations/cline/build_workflow.json`：

```json
{
  "name": "gbs_build_and_analyze",
  "description": "Build with gbs, analyze failure, generate suggestion patches",
  "command": "python",
  "args": [
    "-m", "gbs_workflow",
    "--conf", "gbs.conf",
    "--arch", "armv7l",
    "--include-all",
    "--src-root", "${workspaceFolder}",
    "--output-dir", "${workspaceFolder}/.gbs_workflow"
  ]
}
```

### 5.2 Compiling Agent 接入

新增 `integrations/compiling_agent/workflow_runner.py`：

```python
from gbs_workflow.workflow import run_workflow

result = run_workflow(
    conf="gbs.conf",
    arch="armv7l",
    src_root=Path("/path/to/source"),
    output_dir=Path("/tmp/gbs_workflow"),
    timeout=1800,
)

# result.success: bool (build 是否成功)
# result.suggestions: list[Path] (生成的 patch 文件路径)
# result.evidence_packet_path: Path
```

## 6. 实施计划（MVP）

**3 个 milestone，估计 3-5 天**：

| Milestone | 内容 | 工作量 |
|-----------|------|--------|
| BW-M1 | gbs_build_skill 实现 + UT + 真实 gbs 调用验证 | 1-1.5 day |
| BW-M2 | gbs_workflow 编排 + DepsolveSuggester + UT | 1-1.5 day |
| BW-M3 | E2E 测试（用 B depsolve fixture 跑完整 workflow）+ Cline/Agent 接入示例 + 文档 | 1-2 day |

每个 milestone 一个 PR，按 v0.5 hotfix 周期的工作模式。

## 7. 验收标准

### MVP 验收
- ✅ `python -m gbs_workflow` 能在 ffmpeg 项目跑通
- ✅ Build 成功时 workflow 正常退出，exit 0
- ✅ Depsolve 失败场景（用之前的 B 注入）：
   - workflow 检测到 depsolve 错误
   - 生成 1 个 BuildRequires patch
   - 生成对应 .md 说明文件
   - patch 内容可用 `git apply` 直接 apply
- ✅ 其他错误（A/C/D）：
   - workflow 调用 analyzer 成功
   - 展示 evidence_packet
   - suggestions/ 目录为空 + 输出说明

### 不退化 gate
- gbs_analyzer 所有 346 tests pass
- LogAnalysisSkill v0.5 / hotfix_001 / hotfix_002 功能 100% 保留

## 8. 已知边界 / v0.2 输入

- patch_failed 类的 Suggester（如重新生成 patch）：v0.2 评估，风险高
- linker missing -l 类（推断 BuildRequires）：v0.2 评估，需要 Tizen 仓库知识库
- compile_error / undefined_reference / spec_script：**永远不做** suggestion patch（语义太重）
- workflow 自动 retry：v0.2 决定（可选 --auto-retry-once）

## 9. 风险

| 风险 | 缓解 |
|------|------|
| gbs 命令在不同环境差异大 | gbs_build_skill 接受 --conf 参数，配置文件用户提供 |
| Suggester 生成的 patch 在某些 spec 上不能 apply | 每个 patch 配 .md 说明 + apply 命令，用户自己 review |
| workflow 超时 / hang | --timeout 参数（默认 30 分钟），超时返回明确 exit code |
| Cline / Compiling Agent 接入方式各异 | 各自独立的接入示例 + README |
