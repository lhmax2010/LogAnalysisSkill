# Tizen gbs 编译日志分析 Skill 设计文档 v0.5

**版本**：v0.5（实施冻结版，整合 v0.1~v0.4.1 全部 review 意见 + 工程化要求）
**Hotfix 003（2026-05-20）**：运行时 pattern 数据移入 `tizen-gbs-log-analysis/scripts/gbs_analyzer/patterns/`，通过 package data 分发；pattern schema 和内容不变。
**目标读者**：实施者（Codex）、Review 协作 AI（ChatGPT / Kimi / Claude）、最终用户
**仓库**：https://github.com/lhmax2010/LogAnalysisSkill

> **本文档是 Codex 实施的唯一基线**。v0.1~v0.4.1 的演进文档归档在 `docs/archive/`，仅供决策追溯。

---

## 目录

**第一部分：核心设计**
- §1 设计哲学与原则
- §2 整体架构
- §3 各层详细设计
- §4 Pattern 库与 Fast-Path
- §5 BudgetPool 与 Token 控制
- §6 Tizen 专项最小集

**第二部分：工程化（v0.5 新增）**
- §7 开发产物管理（dev_memory）
- §8 GitHub 工作流
- §9 测试体系
- §10 可观测性（Tracing + Token + 性能报告）
- §11 Skill 接入方案（Cline + Compiling Agent）

**第三部分：实施**
- §12 文件目录结构
- §13 实施计划（按 milestone）
- §14 风险与未决问题
- §15 附录

---

# 第一部分：核心设计

## §1 设计哲学与原则

### 1.1 一句话设计哲学

> 不要让 LLM 找信息。让 skill 找信息、压缩信息、排序信息、按错误类型定向收集证据。LLM 只负责基于 Evidence Packet 做最后判断。**简单 / 可预测 / 可观测优先于完备。**

### 1.2 设计原则

1. **结构化优先于裁剪**：抽取结构化事件，不仅切片文本
2. **Fast-Path 优先**：高 confidence 已知错误零证据收集成本直答
3. **证据按类型定向收集**：compile / link / spec / patch / depsolve 各取所需
4. **Top-K 候选优于单一首错**：让 LLM 看到根因排序
5. **预算全局守恒**：BudgetPool 统一分配，硬/软预留分级
6. **每层降级显式可观测**：不静默吞错，degraded_reasons 必须可追溯
7. **可成长的知识库**：pattern 库支持 LLM 提案 → 测试 → 人工合并
8. **简单优先于完备**：能用三级退化解决的不引入新依赖
9. **可观测、可追溯**（v0.5 新增）：每次运行产生 trace 和性能报告
10. **可接入**（v0.5 新增）：明确支持 Cline 和 Compiling Agent 调用契约

### 1.3 非目标

- 不替代人类对疑难问题的判断
- 不修复编译错误（只给建议）
- 不处理 gbs 之外的构建系统
- 不内嵌 LLM API 调用
- 不能阻止调用方 LLM 绕过 wrapper（agent 框架问题，免责）

---

## §2 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│            调用方（Cline / Compiling Agent / Claude / Codex）    │
│            只读取 Evidence Packet                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │  analyze.py         │
              │  (单入口 wrapper)    │
              │  + tracing + perf   │
              └──────────┬──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Layer 0+1: 单趟扫描    │
              │ scan_and_extract.py  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Layer 4a: Quick      │
              │ quick_filter.py      │  ← Fast-Path 入口
              └──────────┬───────────┘
                         │
            ┌────────────┴────────────┐
   命中 tier1（白名单内）           未命中
            │                         │
            ▼                         ▼
      ┌─────────────┐         ┌──────────────┐
      │  Minimal    │         │   Layer 2    │
      │  Packet     │         │ rank_causes  │
      └─────────────┘         └──────┬───────┘
                                     │
                              [BudgetPool 初始化]
                                     │
                                     ▼
                              ┌──────────────┐
                              │   Layer 3    │
                              │ evidence/    │
                              │ (按类型分发) │
                              │ (申请-协商)  │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  Layer 4b    │
                              │ full_match   │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │   Layer 5    │
                              │ packet_      │
                              │ assembler    │
                              │ + reclaim    │
                              │ + redact     │
                              └──────────────┘
```

### 2.1 BudgetPool 跨层时序（v0.5 明确化）

```
wrapper 层
  ├─> Layer 0+1 scan_and_extract（无预算约束）
  ├─> Layer 4a quick_filter（命中 tier1 时短路返回 minimal packet）
  ├─> Layer 2 rank_causes（产出 candidates 含文本摘要）
  ├─> [BudgetPool 初始化]：扣除 HardReserve + SoftReserve 占位
  ├─> Layer 3 evidence/（collectors 通过 pool.request() 申请预算）
  ├─> Layer 4b full_match（无新预算消耗）
  └─> Layer 5 packet_assembler（reclaim SoftReserve → 再分配 → 序列化 → 脱敏）
```

---

## §3 各层详细设计

### §3.1 Layer 0+1：单趟扫描 + 事件抽取（scan_and_extract.py）

**职责**：流式扫描 buildlog 一次，状态机驱动同时建立索引并抽取结构化事件。

**关键能力**：
- 支持 gzip + 纯文本输入
- 流式 mmap 扫描，绝不一次性 read
- 识别 phase markers（`+ %prep` / `+ %build` / ...）
- 识别 command 边界（`+ ` 开头行）
- 识别 11 类 diagnostic（compiler / linker_undef / linker_missing / patch / spec_script / depsolve / install_missing / werror / make_cascade / rpm_phase / raw_error）
- Cascade 文件名关联（简单后缀匹配）

**Cascade 文件名映射规则**：

```python
def candidates_for_source(src_path: str) -> set[str]:
    base = basename(src_path)              # "bar.cc"
    stem = strip_ext(base)                  # "bar"
    return {f"{stem}.o", f"{base}.o"}       # "bar.o" + "bar.cc.o"

def match_make_target(target_in_log: str, src_to_event: dict) -> str | None:
    """简单后缀匹配，多个 candidate 都匹配时不关联"""
    matches = [eid for suffix, eid in src_to_event.items() if target_in_log.endswith(suffix)]
    return matches[0] if len(matches) == 1 else None
```

支持源文件类型：`.c` / `.cc` / `.cpp` / `.cxx` / `.S` / `.cu`。

**Command parser（v0.4.1 P0-4 + Kimi 修正）**：

```python
RSP_PATTERN = re.compile(r'(?:^|\s)(?:-Wl,)?@([^\s]+\.rsp)(?:\s|$)')

def parse_command(argv_line: str, cwd: str, max_rsp_tokens: int = 200) -> dict:
    argv_line = join_backslash_continuations(argv_line)
    rsp_files = RSP_PATTERN.findall(argv_line)
    rsp_content = {}
    for rsp_path in rsp_files:
        # Kimi 修正：处理绝对路径 rsp
        full_path = rsp_path if os.path.isabs(rsp_path) else os.path.join(cwd, rsp_path)
        if os.path.exists(full_path):
            rsp_content[rsp_path] = extract_relevant_flags(read_rsp(full_path, max_rsp_tokens))
        else:
            rsp_content[rsp_path] = None  # 标记不可用

    return {
        "argv_short": shorten_argv(argv_line),
        "argv_full": argv_line if len(argv_line) < 500 else None,
        "rsp_expanded": rsp_content,
        "command_degraded": any(v is None for v in rsp_content.values()),
    }

def extract_relevant_flags(rsp_content: str) -> dict:
    """优先级：-l/-L/-Werror 必保，-I/-D 可截断（Kimi 修正）"""
    flags = rsp_content.split()
    return {
        "libraries": [f for f in flags if f.startswith('-l')],          # 必保全量
        "library_paths": [f for f in flags if f.startswith('-L')],      # 必保全量
        "other_significant": [f for f in flags if f in ('-Werror', '-fPIC', '-shared')],  # 必保
        "include_paths": [f for f in flags if f.startswith('-I')][:10], # 可截断
        "defines": [f for f in flags if f.startswith('-D')][:20],       # 可截断
        "objects": [f for f in flags if f.endswith(('.o', '.a'))][:30], # 可截断
    }
```

**输出 schema**：见 `docs/schemas/scan_result_v1.json`（实施时编写）。

---

### §3.2 Layer 4a：Quick Pattern Filter（quick_filter.py）

**职责**：在 Layer 3 之前做轻量 pattern 匹配，命中 tier1 时立即输出 minimal packet。

**tier1 白名单（中央约束）**：

```yaml
schema_version: 2

tier1_allowed_categories:
  - depsolve_failure       # nothing provides xxx
  - patch_failed           # Patch #N failed
  - linker_missing_lib     # cannot find -lxxx
  - install_file_missing   # %files 文件不存在

tier1_forbidden_categories:
  - undefined_reference
  - compile_error
  - werror_triggered
  - rpm_phase_failure
  - spec_script_error
```

**tier1 编写规范**：
- fix_template **长度 ≤ 300 字符**（patch_failed 类 **≤ 150 字符**，Kimi 修正）
- 必须使用"可能 / 通常 / 建议检查"等不确定措辞
- 禁止断言式表达
- 末尾必须提示 expand 子命令

**MVP 必含的 Patch_failed 多 pattern（v0.4.1 P1-6）**：

```yaml
- id: patch_failed_standard
  match:
    regex: ["Patch\\s*#?(?P<num>\\d+)\\s*(?:\\(.*\\))?\\s*failed"]
- id: patch_failed_hunk
  match:
    regex: ["Hunk\\s*#?(?P<num>\\d+)\\s*FAILED"]
- id: patch_failed_at_line
  match:
    regex:
      - "patch:?\\s*\\*\\*\\*\\*\\s*malformed patch at line (?P<line>\\d+)"
      - "patch failed:\\s*(?P<file>[^\\s]+):(?P<line>\\d+)"
- id: patch_failed_rpm
  match:
    regex:
      - "error: patch failed"
      - "error:\\s*Patch[\\d:]+\\s*failed"
```

**required_context 多维约束**：

```yaml
match:
  regex: [...]
  required_context:
    phase: ["%build"]
    severity: ["error", "fatal"]
    tool_in: ["ld", "lld", "gold", "clang", "clang++", "gcc", "g++"]
    not_in_warning_block: true
  negative_patterns: ["warning:", "info:"]
```

**not_in_warning_block 启发式**（MVP 简单版）：

```python
def is_in_warning_block(event, all_events):
    """错误行前后 3 行内有 warning: 且没有 error:，视为 warning block"""
    nearby = events_within_lines(event, all_events, lines=3)
    has_warning = any('warning:' in e.get('message', '').lower() for e in nearby)
    has_error = any('error:' in e.get('message', '').lower() for e in nearby if e.id != event.id)
    return has_warning and not has_error
```

---

### §3.3 Layer 2：根因排序（rank_causes.py）

**8 类语义置信度**（`tizen-gbs-log-analysis/scripts/gbs_analyzer/patterns/error_semantics.yaml`）：

| semantic_class | base_confidence | cascade_probability | 默认申请 Level |
|---------------|-----------------|--------------------|----------------|
| syntax_error | 0.90 | 0.05 | 1 |
| undeclared_identifier | 0.75 | 0.30 | 2 + grep header |
| no_member | 0.80 | 0.20 | 3 (struct/class) |
| type_mismatch | 0.85 | 0.15 | 2 + typedef |
| template_instantiation | 0.60 | 0.50 | 3 (template) |
| undefined_reference | 0.85 | 0.20 | N/A (link 类) |
| missing_lib | 0.95 | 0.05 | N/A (link 类) |
| generic_error | 0.45 / 0.70 (gating) | 0.40 | 2 |

**generic_error gating（v0.4.1 P1-5）**：

```python
def classify_generic(event, scan_result):
    if all([
        event.get('command_id'),
        event.get('raw_offset') is not None,
        event.get('phase') == scan_result.failed_phase,
        not (event.get('kind') in ('make_cascade', 'rpm_phase_failure')),
    ]):
        return GenericError(base_confidence=0.70, context_satisfied=True)
    return GenericError(base_confidence=0.45, context_satisfied=False)
```

**排序公式**：

```python
def rank_score(event, all_events):
    if event['kind'] == 'make_cascade' and event.get('parent'):
        return 0.1

    sem = classify_semantic(event['message'])
    base = sem.base_confidence
    score = base - sem.cascade_probability * 0.3

    if event.get('command_id'): score += 0.05
    if event.get('file') and event.get('line'): score += 0.05
    if is_in_warning_block(event, all_events): score -= 0.3
    if event.get('parent'): score -= 0.4
    return clamp(score, 0.0, 1.0)
```

**Top-K 输出（v0.4 决策：仅 Top-1 进入 Layer 3，Top-2/3 仅文本摘要）**：

```json
{
  "root_cause_candidates": [
    {
      "rank": 1,
      "event_id": "E001",
      "kind": "compiler_diagnostic",
      "semantic_class": "no_member",
      "confidence": 0.83,
      "confidence_band": "medium_high",
      "confidence_reason": [
        {"factor": "semantic_class", "value": "no_member", "base": 0.80},
        {"factor": "has_location", "delta": "+0.05"},
        {"factor": "cascade_penalty", "delta": "-0.06"}
      ],
      "is_terminal": true,
      "summary": "clang++ no_member error at src/foo.cc:128 — no member named 'xxx'"
    },
    {
      "rank": 2,
      "event_id": "E005",
      "summary": "include/bar.h:45 template instantiation failure",
      "confidence": 0.45,
      "confidence_band": "low"
    }
  ]
}
```

---

### §3.4 Layer 3：证据收集（按错误类型 + 弹性预算池）

**收集器路由表**：

| 错误类型 | 收集器 | MVP 包含 |
|---------|--------|---------|
| `compiler_diagnostic` / `werror_triggered` | `evidence/compile.py` | ✅ |
| `linker_undefined_ref` / `linker_missing_lib` | `evidence/link.py` | ✅ |
| `spec_script_error` | `evidence/spec.py` | ✅ |
| `depsolve_failure` | `evidence/deps.py` | ✅ |
| `patch_failed` | `evidence/patch.py` | full 阶段 |
| `install_file_missing` | `evidence/install.py` | full 阶段 |
| `unknown` | `fallback_raw_context`（assembler 内置） | ✅ |

**Collector ABC 接口**：

```python
class EvidenceCollector(ABC):
    @abstractmethod
    def estimate(self, candidate) -> dict:
        """返回 {'preferred': 900, 'minimum': 300, 'levels': {1: 300, 2: 600, 3: 900}}"""

    @abstractmethod
    def collect(self, candidate, granted_budget: int) -> Evidence:
        """根据 granted_budget 选对应 level 提取"""
```

**ctags 三级降级**：

```
Level 2/3 提取：
  1. ctags --output-format=json -f -      首选
  2. 正则匹配函数签名 + 大括号配对          ctags 失败时
  3. 行窗口 ±30                             兜底

每个降级路径都标记 extraction_method
```

**fallback_raw_context（assembler 内置，MVP 必含）**：

```python
def fallback_raw_context(top1_event, scan_result, budget=600) -> dict:
    """
    MVP 必含的最小兜底，用于 unknown / collector 失败 / 预算耗尽。
    输出预算 ≤ 600 token。
    """
    return {
        "primary_error_excerpt": read_log_window(top1_event, before=30, after=20),
        "current_phase": top1_event.get('phase'),
        "current_command_summary": scan_result.command_summaries.get(top1_event.get('command_id')),
        "cascade_summary": format_cascade(scan_result),
        "extra_log_window": read_log_window(top1_event, before=50, after=50),
    }
```

裁剪顺序（超 600 token 时）：`extra_log_window 50→30→0` → `primary_error_excerpt 50→30` → `current_command_summary` 始终保留。

---

### §3.5 Layer 4b：Full Pattern Match（full_match.py）

**直答判定（v0.4 简化版，无 degraded direct_answer）**：

```python
def determine_verdict(matched_rule, event, evidence):
    if (matched_rule.direct_answer_tier1.enabled
        and matched_rule.confidence >= 0.95
        and matched_rule.terminal
        and event.is_terminal
        and not evidence.degraded
        and passes_required_context):
        return Verdict.DIRECT_TIER1

    if (matched_rule.direct_answer_tier2.enabled
        and matched_rule.confidence >= 0.85
        and matched_rule.terminal
        and event.is_terminal
        and evidence.contains_all(matched_rule.direct_answer_tier2.evidence_required)
        and not evidence.degraded):
        return Verdict.DIRECT_TIER2

    return Verdict.NEEDS_LLM
```

**Pattern Schema 完整版**：见 `tizen-gbs-log-analysis/scripts/gbs_analyzer/patterns/schema.json`。

---

### §3.6 Layer 5：Packet Assembler

**职责**：组装最终 packet，含 token 预算、SoftReserve reclaim、脱敏（双层）、tracing 输出。

**双层脱敏（Kimi 修正）**：

```python
class MinimalRedactor:
    def redact_for_llm(self, text: str) -> str:
        """用于 prompt 字段和 evidence_packet.md（人类可读版）"""
        # /home/<user>/ → /home/<USER>/
        # hostname → <HOST>
        # workspace_root → <WORKSPACE>
        ...

    def redact_for_storage(self, obj: dict) -> dict:
        """JSON packet 内部保留真实路径，供 expand 子命令使用"""
        return obj  # 不脱敏，原样返回
```

**调用规则**：
- `evidence_packet.json`：使用 `redact_for_storage`（保留真实路径）
- `evidence_packet.md`：使用 `redact_for_llm`
- `packet.prompt` 字段：使用 `redact_for_llm`

---

## §4 Pattern 库与 Fast-Path

详细 schema 见 `tizen-gbs-log-analysis/scripts/gbs_analyzer/patterns/schema.json`。Pattern 编写指南见 `docs/pattern_authoring.md`。

**MVP 必含 pattern 数量**：≥ 15 条（覆盖 4 类 tier1 + 5 类 tier2 + 至少 6 个变体）。

---

## §5 BudgetPool 与 Token 控制

### 5.1 总预算分配

| 项 | 预算 |
|----|------|
| 总预算 | 1800 |
| Prompt 模板（指令 + 格式 + 固定上下文） | 400 |
| Evidence 净预算 | 1400 |

### 5.2 BudgetPool HardReserve / SoftReserve

```python
@dataclass
class HardReserve:
    """硬预留：未用完不返还"""
    amount: int

@dataclass
class SoftReserve:
    """软预留：未用完返还到 evidence_pool"""
    amount: int

class BudgetPool:
    def __init__(self, total: int = 1400):
        self.reserved = {
            'primary_error':         HardReserve(200),
            'command_summary':       HardReserve(120),
            'metadata':              HardReserve(80),
            'cascade_summary':       SoftReserve(50),
            'top_k_text_summaries':  SoftReserve(200),
            'raw_excerpt':           SoftReserve(100),
        }
        # Initial: 1400 - 400 (hard) - 350 (soft) = 650
        self.evidence_pool = 650
        self.reclaimable = 350
        self.reclaimed = 0

    def report_reserve_used(self, name, actual_used):
        """SoftReserve 上报实际用量，未用完返还"""
        ...

    def request(self, collector_name, requested) -> int:
        """Collector 申请，pool 返回实际允许的额度"""
        granted = min(requested, self.evidence_pool)
        self.evidence_pool -= granted
        return granted
```

### 5.3 Token 估算

主路径：tiktoken `cl100k_base`（无网络调用）。
降级路径：混合估算 `代码字符/3 + 中文字符/1.5 + 英文 word/0.75`。

**tiktoken 进 `requirements.txt` 主依赖。**

---

## §6 Tizen 专项最小集

### 6.1 spec_minimal.py（MVP 必含）

```python
class SpecMinimalParser:
    def find_spec_file(self, package, src_root) -> Path: ...
    def extract_buildrequires(self) -> list[str]: ...
    def extract_patches(self) -> list[dict]: ...
    def extract_sources(self) -> list[dict]: ...
    def extract_section(self, name: str) -> str: ...
    def extract_section_failure_context(self, phase: str) -> dict:
        """通过 '+ ' 命令标记定位失败前最后一条命令 + 输出"""
        return {
            "last_command": "...",
            "last_command_output": "...",
            "spec_section_text": "...",
        }

    def get_parse_status(self) -> dict:
        """v0.4.1 P0-3：不确定性标记"""
        return {
            "macro_expanded": False,
            "condition_evaluated": False,
            "subpackage_resolved": False,
            "confidence": "partial",
            "warnings": self._collect_warnings(),
        }
```

**v0.5 不做（推迟到 v0.6）**：宏展开 / 条件块求值 / 多包归属 / 版本约束语义比较。

### 6.2 toolchain_detector.py / werror_analyzer.py（full 阶段）

---

# 第二部分：工程化（v0.5 新增）

## §7 开发产物管理（dev_memory）

### 7.1 目的

每个 milestone 完成后写 `dev_memory`，记录：
- 当前阶段状态
- 已完成的 patch 列表 + commit hash
- 关键设计决策与改动理由
- 已知问题 / TODO
- 测试状态
- 下一阶段入口

**用途**：
1. session 崩溃后续接（任何 AI 读取后能继续）
2. 替换其他 AI 时无缝切换
3. 决策追溯

### 7.2 目录结构

```
.dev_memory/
├── README.md                    # dev_memory 读取指南
├── current.yaml                 # 当前活跃 milestone（指针）
├── m1_scan_and_extract/
│   ├── memory.md                # 主 memory
│   ├── decisions.md             # 设计决策日志
│   ├── patches.yaml             # patch 记录
│   ├── test_report.md           # UT + 功能测试报告
│   └── known_issues.md          # 已知问题
├── m2_quick_filter/
│   └── ...
└── ...
```

### 7.3 memory.md 模板

````markdown
# Milestone M{N}：{name}

**状态**：completed / in-progress / blocked
**起始 commit**：abc123def
**最新 commit**：xyz789abc
**起始日期**：2026-MM-DD
**完成日期**：2026-MM-DD（in-progress 时为空）
**预计工作量**：3 天 | **实际工作量**：3.5 天

## 已完成内容

- [x] 实现 `tizen-gbs-log-analysis/scripts/gbs_analyzer/scan_and_extract.py`
- [x] 状态机识别 phase 切换
- [x] 命令边界识别（含 multiline + rsp）
- [x] Cascade 文件名映射（.c/.cc/.cpp/.cxx/.S/.cu）
- [x] 写入 11 类 diagnostic event
- [ ] [TODO]：异常 phase marker 退化（暂用 raw_error_block 兜底）

## 关键改动详情

### 改动 1：rsp 文件路径 isabs 处理
- **改动文件**：`tizen-gbs-log-analysis/scripts/gbs_analyzer/_utils/command_parser.py:42-48`
- **改动原因**：CMake 某些版本生成绝对路径 rsp，原 `os.path.join(cwd, rsp_path)` 会错误拼接
- **改动来源**：v0.4.1 patch P0-4（Kimi 修正）
- **测试**：`tests/test_command_parser.py::test_absolute_path_rsp` 验证

### 改动 2：cascade 文件名映射
- **改动文件**：`tizen-gbs-log-analysis/scripts/gbs_analyzer/_utils/source_to_object.py`
- **改动原因**：v0.4 决策——简单后缀匹配，多 candidate 不关联
- **改动来源**：v0.5 §3.1
- **歧义率监控**：当前 fixture 0% 歧义

## 测试状态

| 测试类型 | 通过 | 失败 | 跳过 |
|---------|------|------|------|
| UT | 28 | 0 | 0 |
| 功能测试（fixture） | 5/5 | 0 | 0 |
| 集成测试 | 1/1 | 0 | 0 |

UT 覆盖率：87%（要求 ≥ 80%）

## 下一阶段入口

- 入口模块：`tizen-gbs-log-analysis/scripts/gbs_analyzer/quick_filter.py`
- 依赖本阶段：scan_result 输出 schema 已稳定
- 预期工作量：2 天

## Token 性能基线（本阶段）

- 100MB 日志单趟扫描耗时：6.2s（目标 < 8s）
- 内存峰值：48MB（目标 < 100MB）

## 给下一个开发者（AI/人类）

如果你接手这个 session：
1. 先读 `current.yaml` 确认本 milestone 状态
2. 读 `decisions.md` 了解所有设计决策
3. 读最新的 commit log（git log --oneline | head -20）
4. 跑 `pytest tests/` 确认基线绿
5. 然后开始 m2_quick_filter
````

### 7.4 patches.yaml 格式

```yaml
patches:
  - id: p001
    title: "Implement BuildLogScanner state machine"
    commit: "abc123de"
    files_changed: ["tizen-gbs-log-analysis/scripts/gbs_analyzer/scan_and_extract.py"]
    lines_added: 234
    lines_removed: 0
    rationale: "v0.5 §3.1 — 状态机驱动单趟扫描"
    test_commit: "def456gh"  # 对应的测试 commit

  - id: p002
    title: "Handle absolute path rsp files"
    commit: "ijk789lm"
    files_changed: ["tizen-gbs-log-analysis/scripts/gbs_analyzer/_utils/command_parser.py"]
    lines_added: 8
    lines_removed: 2
    rationale: "Kimi v0.4.1 review 修正：CMake 某些版本生成绝对路径"
    test_commit: "nop234qr"
```

### 7.5 current.yaml 格式

```yaml
current_milestone: m2_quick_filter
last_completed: m1_scan_and_extract
last_completed_commit: xyz789abc
session_count: 3
next_steps:
  - "实现 quick_filter.py 主流程"
  - "加载 tizen-gbs-log-analysis/scripts/gbs_analyzer/patterns/gbs_errors.yaml"
  - "实现 tier1 白名单校验"
blocked_on: null
notes: |
  上一个 session 用 Codex 跑完了 m1，已通过 5/5 fixture。
  m2 计划周内完成。
```

---

## §8 GitHub 工作流

**仓库**：https://github.com/lhmax2010/LogAnalysisSkill

### 8.1 分支策略

```
main                            # 稳定分支，每个 milestone PR 合并
└── feature/m1-scan-and-extract # M1 开发分支
└── feature/m2-quick-filter
└── feature/m3-rank-causes
└── ...
```

**规则**：
- main 分支只通过 PR 合并，不允许直接 push
- 每个 milestone 一个 feature 分支
- milestone 完成后开 PR，标题 `[M{N}] {milestone_name}`
- PR 必须含 dev_memory 链接 + 测试报告 + 性能数据

### 8.2 PR 模板

`.github/pull_request_template.md`：

```markdown
## Milestone M{N}：{name}

### Dev Memory
- 主文件：`.dev_memory/m{N}_{name}/memory.md`
- 决策日志：`.dev_memory/m{N}_{name}/decisions.md`
- 测试报告：`.dev_memory/m{N}_{name}/test_report.md`

### 关键改动
- [ ] 改动 1：{描述}
- [ ] 改动 2：{描述}

### 测试结果
- UT 通过：__/__
- 功能测试通过：__/__ fixtures
- 覆盖率：__%

### 性能数据
- 100MB 日志耗时：__s
- Token 估算精度：__%
- BudgetPool 守恒率：__%

### Review checklist
- [ ] 跑 `pytest tests/ -v` 全绿
- [ ] 跑 `python -m gbs_analyzer analyze tests/fixtures/{representative}` 验证端到端
- [ ] dev_memory 已更新
- [ ] 性能数据已记录
- [ ] 已知问题已写入 known_issues.md

### 下一阶段
依赖本阶段产出：{是 / 否}
下一阶段入口：{文件 / 函数}
```

### 8.3 Commit 规范

```
<type>(<scope>): <subject>

[optional body]

[optional footer with Refs]
```

类型：`feat` / `fix` / `test` / `docs` / `refactor` / `perf` / `chore`

scope：`scan` / `quick_filter` / `rank` / `evidence` / `assembler` / `pattern` / `tracing` / `infra`

示例：
```
feat(scan): implement BuildLogScanner state machine

- 状态机识别 phase 切换
- 11 类 diagnostic 边界识别
- Cascade 文件名映射

Refs: v0.5 §3.1, dev_memory m1_scan_and_extract
```

### 8.4 GitHub Actions CI

`.github/workflows/ci.yml`：

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          sudo apt-get install -y universal-ctags
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Lint
        run: |
          ruff check tizen-gbs-log-analysis/scripts/gbs_analyzer/
          mypy tizen-gbs-log-analysis/scripts/gbs_analyzer/
      - name: Unit tests
        run: pytest tests/unit/ -v --cov=gbs_analyzer --cov-report=xml
      - name: Pattern tests
        run: pytest tests/test_pattern_library.py -v
      - name: Fixture regression
        run: pytest tests/test_e2e.py -v
      - name: Coverage check
        run: |
          coverage report --fail-under=80
```

---

## §9 测试体系

### 9.1 测试金字塔

```
        ┌───────────────────┐
        │   E2E (5)         │  ← 完整 buildlog → packet
        ├───────────────────┤
        │ Integration (15)  │  ← 跨模块（如 scan + rank）
        ├───────────────────┤
        │  Functional (20)  │  ← Fixture 级
        ├───────────────────┤
        │     UT (100+)     │  ← 单模块 + 单函数
        └───────────────────┘
```

### 9.2 单元测试要求

每个模块必须有独立 UT，覆盖：
- Happy path
- 至少 2 个 edge case
- 至少 1 个 degraded path
- 异常输入

**覆盖率要求**：≥ 80%（CI gate）

**测试位置**：`tests/unit/test_{module_name}.py`

### 9.3 功能测试（Fixture 级）

每个 fixture 包含：
```
tests/fixtures/{fixture_name}/
├── buildlog              # 真实 buildlog（已脱敏）
├── expected_packet.json  # 期望输出
├── README.md             # 人工标注的根因
└── notes.md              # 该 fixture 的特殊注意事项
```

### 9.4 每个 milestone 的"Definition of Done"

| Milestone | UT 要求 | 功能测试要求 | 性能要求 |
|-----------|--------|-------------|---------|
| M1 scan_and_extract | 30+ tests, 85% cov | 5 fixtures 通过 scan | 100MB < 8s |
| M2 quick_filter | 20+ tests, 85% cov | 4 Fast-Path fixtures 命中 | < 100ms |
| M3 rank_causes | 15+ tests, 85% cov | Top-1 准确率 ≥ 80% | < 50ms |
| M4 spec_minimal | 15+ tests, 80% cov | 5 spec 抽取成功 | < 200ms |
| M5 4 collectors | 30+ tests, 80% cov | 各 ≥ 2 fixtures | 单次 < 500ms |
| M6 full_match | 10+ tests, 85% cov | tier2 命中至少 3 fixtures | - |
| M7 assembler | 20+ tests, 85% cov | BudgetPool 守恒 100% | - |
| M8 wrapper + redaction | 10+ tests, 80% cov | 20 fixtures 全通过 | E2E < 15s |

### 9.5 测试 guide（每 milestone 一份）

`docs/test_guides/m{N}_{name}.md`：

```markdown
# M{N} Test Guide：在真实环境上测试

## 环境要求
- OS：Ubuntu 22.04+ / Tizen build container
- Python 3.10+
- 依赖：universal-ctags / git
- （可选）真实 gbs build 失败的 buildlog

## 快速开始
\`\`\`bash
git clone https://github.com/lhmax2010/LogAnalysisSkill.git
cd LogAnalysisSkill
git checkout feature/m{N}-{name}
pip install -r requirements.txt
pytest tests/unit/test_{module}.py -v
\`\`\`

## 在真实 buildlog 上测试

\`\`\`bash
# 假设你有一份真实失败的 buildlog
python -m gbs_analyzer analyze /path/to/your/buildlog \\
    --src-root /path/to/source \\
    --max-tokens 1800 \\
    --output-dir /tmp/gbs_out \\
    --trace
\`\`\`

## 验收标准
- [ ] 命令成功退出（exit 0）
- [ ] 输出 `evidence_packet.json` 和 `evidence_packet.md`
- [ ] `verdict` 字段非空
- [ ] `token_budget.used <= 1800`
- [ ] 性能报告 `perf_report.json` 已生成

## 故障排查
- **现象 A**：xxx → **原因**：yyy → **解决**：zzz
- ...

## 反馈
如发现问题，请在 GitHub Issue 提报告，附：
- buildlog（脱敏后）
- evidence_packet.json
- trace.log
- perf_report.json
```

---

## §10 可观测性（Tracing + Token + 性能报告）

### 10.1 Tracing 日志

**层级**：DEBUG / INFO / WARNING / ERROR

**触发**：`--trace` 参数 启用 DEBUG 级；默认 INFO 级

**输出文件**：`<output_dir>/trace.log`（人类可读）+ `trace.jsonl`（结构化）

**结构化 trace 字段**：

```json
{"ts": "2026-05-10T14:30:00", "level": "INFO", "layer": "L0_scan", "event": "phase_marker_detected", "phase": "%build", "offset": 18000}
{"ts": "...", "level": "DEBUG", "layer": "L4a_quick", "event": "pattern_evaluated", "pattern": "missing_link_library", "matched": true, "tier": "tier1"}
{"ts": "...", "level": "INFO", "layer": "L3_evidence", "event": "collector_request", "collector": "compile", "requested": 900, "granted": 720}
{"ts": "...", "level": "INFO", "layer": "L5_assembler", "event": "soft_reserve_reclaimed", "reserve": "top_k_text_summaries", "reclaimed": 120}
```

**关键事件**：
- L0：phase 切换、command 边界、diagnostic 识别、cascade 关联
- L4a：pattern 匹配尝试、tier1 命中
- L2：candidate ranking、cascade folding
- L3：collector 申请-协商、ctags 三级降级、extraction_method
- L4b：tier 判定、direct_answer 决议
- L5：reclaim、redaction、token estimate

### 10.2 Token 消耗追踪

**每次 analyze 输出**（`<output_dir>/perf_report.json`）：

```json
{
  "schema_version": "perf_report/v1",
  "analyzed_at": "2026-05-10T14:30:00",
  "buildlog_size_bytes": 12345678,
  "buildlog_token_estimate": 8200000,

  "execution": {
    "total_ms": 8420,
    "by_layer": {
      "L0_scan": 6200,
      "L4a_quick": 50,
      "L2_rank": 80,
      "L3_evidence": 1800,
      "L4b_full": 30,
      "L5_assembler": 260
    },
    "fast_path_hit": false,
    "exit_status": "success"
  },

  "tokens": {
    "estimate_method": "tiktoken",
    "input_log_tokens": 8200000,
    "packet_tokens": 1320,
    "compression_ratio": 6212.0,
    "budget": {
      "limit": 1800,
      "evidence_pool_initial": 650,
      "reclaimed": 270,
      "evidence_pool_final": 920,
      "used": 1320
    },
    "by_section": {
      "primary_error": 180,
      "source_snippets": 480,
      "command_summary": 100,
      "header_declarations": 60,
      "top_k_summaries": 80,
      "structure_overhead": 100,
      "prompt_template": 400
    }
  },

  "decisions": {
    "verdict": "needs_llm",
    "via": "full_path",
    "matched_tier": null,
    "candidates_ranked": 3,
    "candidates_kept": 2,
    "evidence_collector": "compile",
    "level_preferred": 3,
    "level_achieved": 2,
    "downgraded": true,
    "downgrade_reason": "budget_pool_partial"
  },

  "degradations": [],

  "warnings": [
    "Top-2 confidence (0.45) within 0.4 of Top-1 (0.83), evidence may benefit from expand"
  ]
}
```

### 10.3 性能基线（贯穿所有 milestone）

| 指标 | 目标 | MVP 验收 |
|------|------|---------|
| 100MB 日志单趟扫描 | < 8s | 必须达标 |
| Fast-Path 命中端到端 | < 1s | 必须达标 |
| 完整流程端到端 | < 15s | 必须达标 |
| Fast-Path 命中率（fixture） | ≥ 25% | 必须达标 |
| direct_answer 命中率（tier1+tier2） | ≥ 35% | 必须达标 |
| Top-1 准确率 | ≥ 85% | ≥ 80% (MVP) |
| BudgetPool 守恒率 | 100% | 必须达标 |
| Evidence packet 平均 token | ≤ 1400 净 / 1800 含 prompt | 必须达标 |

---

## §11 Skill 接入方案

### 11.1 Cline 接入

**Cline** 是 VSCode 的 AI coding assistant 扩展，支持自定义 commands 和 MCP servers。

**接入方式**：通过 Cline 的 custom command 调用 wrapper。

**配置文件**：`.cline/commands/analyze_gbs.json`：

```json
{
  "name": "analyze_gbs_buildlog",
  "description": "分析 Tizen gbs 构建失败日志，生成 Evidence Packet",
  "command": "python",
  "args": [
    "-m", "gbs_analyzer", "analyze",
    "${input:buildlog_path}",
    "--src-root", "${workspaceFolder}",
    "--max-tokens", "1800",
    "--output-format", "both",
    "--output-dir", "${workspaceFolder}/.gbs_analysis"
  ],
  "input_handlers": {
    "buildlog_path": {
      "prompt": "Path to gbs buildlog",
      "default_from_clipboard": true
    }
  },
  "post_process": {
    "read_file": ".gbs_analysis/evidence_packet.md",
    "feed_to_llm": true,
    "system_prompt": "你是 Tizen 构建专家。基于 Evidence Packet 分析根因并给出修复建议。"
  }
}
```

**SKILL.md 兼容性**：`tizen-gbs-log-analysis/SKILL.md` 遵循 Anthropic skill 格式，Cline 可直接读取（如果 Cline 未来支持 skill 生态，无需改造）。

### 11.2 Compiling Agent 接入

**Compiling Agent** 是用户自研的构建监控 agent，需要无人值守接入。

**接入方式**：subprocess 调用 + JSON 通信。

**接入接口**：

```python
# compiling_agent/integrations/log_analysis.py
import subprocess
import json
from pathlib import Path

class GbsLogAnalysisIntegration:
    """Compiling Agent → gbs_analyzer 接入封装"""

    def __init__(self, analyzer_path: str = "python -m gbs_analyzer"):
        self.analyzer_path = analyzer_path

    def analyze(self, buildlog_path: str, src_root: str = "auto",
                max_tokens: int = 1800, timeout: int = 30) -> dict:
        """
        无人值守分析，返回 evidence packet dict。
        timeout 防止异常 buildlog 导致 hang。
        """
        cmd = [
            *self.analyzer_path.split(),
            "analyze", buildlog_path,
            "--src-root", src_root,
            "--max-tokens", str(max_tokens),
            "--output-format", "json",
            "--output-dir", "/tmp/gbs_analysis_agent",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout, check=True)
            packet_path = Path("/tmp/gbs_analysis_agent/evidence_packet.json")
            return json.loads(packet_path.read_text())
        except subprocess.TimeoutExpired:
            return {"verdict": "needs_llm", "degraded": True, "degraded_reasons": ["analyzer_timeout"]}
        except subprocess.CalledProcessError as e:
            return {"verdict": "needs_llm", "degraded": True, "degraded_reasons": [f"analyzer_exit_{e.returncode}"]}

    def feed_to_llm(self, packet: dict, llm_client) -> str:
        """packet → LLM 调用 → 修复建议"""
        if packet.get("verdict") == "direct_answer":
            return packet["direct_answer"]

        prompt = packet.get("prompt")
        if not prompt:
            return "Analysis failed; please check raw buildlog."

        return llm_client.complete(prompt)
```

**Exit code 约定**：
- 0：成功（含 degraded 但有 packet 输出）
- 1：致命错误（无 packet）
- 2：参数错误
- 3：buildlog 文件不可读
- 124：超时（沿用 GNU timeout 约定）

### 11.3 统一调用契约

无论 Cline 还是 Compiling Agent，都通过以下契约调用：

```
INPUT:
  - buildlog_path: str (必需)
  - src_root: str (可选，默认 auto)
  - max_tokens: int (可选，默认 1800)
  - extra args: --extended-evidence / --no-tiktoken / etc.

OUTPUT:
  - evidence_packet.json (机器读)
  - evidence_packet.md (LLM/人类读)
  - perf_report.json (评估)
  - trace.jsonl (debugging)

EXIT CODES:
  - 0 / 1 / 2 / 3 / 124 (见上)
```

---

# 第三部分：实施

## §12 文件目录结构

```
LogAnalysisSkill/                              # GitHub repo root
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt                            # tiktoken, pyyaml, jinja2
├── requirements-dev.txt                        # pytest, ruff, mypy
├── .github/
│   ├── workflows/ci.yml
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
├── .dev_memory/                                # §7 dev_memory
│   ├── README.md
│   ├── current.yaml
│   └── m{N}_{name}/...
├── docs/
│   ├── architecture.md                         # 架构总览
│   ├── pattern_authoring.md                    # pattern 编写指南
│   ├── test_guides/                            # §9.5 每 milestone 一份
│   │   ├── m1_scan_and_extract.md
│   │   ├── m2_quick_filter.md
│   │   └── ...
│   ├── integration_guide.md                    # §11 接入方案
│   └── archive/                                # v0.1~v0.4.1 历史文档
│       ├── v0.1.md
│       ├── ...
│       └── v0.4.1-patch.md
├── tizen-gbs-log-analysis/
│   ├── SKILL.md                                # Anthropic skill 格式
│   └── scripts/
│       ├── run_analyzer.py                     # direct folder launcher
│       └── gbs_analyzer/                       # 核心代码
│           ├── __init__.py
│           ├── __main__.py
│           ├── analyze.py                      # 主入口
│           ├── scan_and_extract.py             # Layer 0+1
│           ├── quick_filter.py                 # Layer 4a
│           ├── rank_causes.py                  # Layer 2
│           ├── full_match.py                   # Layer 4b
│           ├── packet_assembler.py             # Layer 5
│           ├── budget_pool.py                  # §5.2
│           ├── evidence/
│           ├── tizen/
│           ├── tracing/                        # §10 v0.5 新增
│           ├── _utils/
│           └── patterns/                       # runtime package data
│               ├── gbs_errors.yaml             # 主库
│               ├── error_semantics.yaml        # 8 类语义
│               ├── README.md
│               └── schema.json                 # JSON Schema 校验
├── templates/
│   ├── evidence_packet.md.j2
│   └── llm_prompt.md.j2
├── tools/
│   ├── pattern_skeleton.py                     # CLI：从样本生成骨架
│   └── benchmark.py                            # 性能 benchmark
├── tests/
│   ├── unit/
│   │   ├── test_scan_and_extract.py
│   │   ├── test_quick_filter.py
│   │   ├── test_rank_causes.py
│   │   ├── test_evidence_compile.py
│   │   ├── test_evidence_link.py
│   │   ├── test_budget_pool.py
│   │   ├── test_command_parser.py
│   │   └── ...
│   ├── functional/
│   │   ├── test_pattern_library.py             # 跑所有 pattern 的 tests
│   │   └── test_collectors_with_fixtures.py
│   ├── integration/
│   │   ├── test_scan_to_rank.py
│   │   ├── test_rank_to_evidence.py
│   │   └── test_full_flow.py
│   ├── e2e/
│   │   └── test_e2e.py                         # 端到端
│   └── fixtures/
│       ├── fast_path_missing_lib/
│       ├── fast_path_patch_failed/
│       ├── fast_path_depsolve/
│       ├── compile_undef_member/
│       ├── compile_template_error/
│       ├── link_undef_ref/
│       ├── parallel_make_cascade/
│       ├── spec_script_error/
│       ├── unknown_error/                      # 验证 fallback_raw_context
│       └── ...                                 # MVP 20 个
├── integrations/                               # §11
│   ├── cline/
│   │   ├── README.md
│   │   └── analyze_gbs.json
│   └── compiling_agent/
│       ├── README.md
│       └── log_analysis.py
└── tizen-gbs-log-analysis/
    └── SKILL.md                               # Anthropic skill 格式
```

---

## §13 实施计划（按 milestone）

### MVP 阶段（16 天）

| M | 内容 | 工作量 | DoD（Definition of Done） |
|---|------|--------|--------------------------|
| M1 | scan_and_extract（含 rsp/multiline/cascade）+ tracing 基础 | 3 天 | 30+ UT, 5 fixtures pass scan, 100MB < 8s |
| M2 | quick_filter + tier1 白名单 + 6 条 patterns（含 patch_failed 多变体） | 2 天 | 20+ UT, 4 Fast-Path fixtures hit, < 100ms |
| M3 | rank_causes + 8 类语义 + generic_error gating + confidence_reason | 1.5 天 | 15+ UT, Top-1 准确率 ≥ 80% |
| M4 | spec_minimal + parse_status 不确定性标记 | 1.5 天 | 15+ UT, 5 spec 抽取成功 |
| M5 | evidence/ 4 类 collector + ctags 三级降级 + ABC 接口 | 3 天 | 30+ UT, 各 ≥ 2 fixtures, ctags 降级触发 ≥ 1 次 |
| M6 | full_match + tier2 + Pattern schema 完整版 | 1 天 | 10+ UT, tier2 命中至少 3 fixtures |
| M7 | packet_assembler + BudgetPool + fallback_raw_context + 双层脱敏 + tiktoken | 2 天 | 20+ UT, BudgetPool 守恒 100% |
| M8 | wrapper + SKILL.md + perf_report + 20 fixture E2E | 2 天 | 20 fixtures 全通过, E2E < 15s |

**MVP 验收 gate**：
- 所有 milestones DoD 达成
- Fast-Path 命中率 ≥ 25%
- 各 milestone 的 dev_memory 完整
- GitHub 主分支 CI 全绿

### Full 阶段（再 6-8 天）

| M | 内容 |
|---|------|
| M9 | patch / install / generic collector |
| M10 | toolchain_detector + werror_analyzer |
| M11 | tools/pattern_skeleton.py CLI |
| M12 | warning_block 边界增强 |
| M13 | fixture 加到 35 + pattern tests 全绿 |
| M14 | 性能调优 + 完整文档 + Cline / Compiling Agent 接入示例 |

### 扩展路线图（v0.6+）

| 版本 | 内容 |
|------|------|
| v0.6 | tree-sitter 集成（基于 v0.5 实测准确率决定） |
| v0.6 | CMake/Ninja 精确反向映射 |
| v0.6 | 错误语义置信度细粒度调优（fixture 校准） |
| v0.7 | spec 宏展开 + 条件块求值 |
| v0.7 | 错误指纹缓存 |
| v0.7 | LLM 二段式调用 |
| v0.8 | OBS 日志格式支持 |
| v0.8 | 多包并发分析 |

---

## §14 风险与未决问题

### 14.1 风险表

| 风险 | 影响 | 缓解 |
|------|------|------|
| gbs 输出格式版本变更 | Layer 0+1 失效 | phase/command marker 抽配置；fixture 回归 |
| ctags 未安装 | Layer 3 退化 | 三级降级链；degraded 报告；CI 验证 |
| 8 类语义分类误判 | Top-K 排序失真 | 粗粒度 + fixture 校准；v0.6 细化 |
| Fast-Path tier1 建议太泛 | LLM 用户体验下降 | 白名单 + 长度限制 + 保守措辞 |
| 并行构建 cascade 关联失败 | Top-1 是 cascade | 简单后缀映射 + Top-K 文本摘要兜底 |
| LLM 不遵守 SKILL.md | token 爆炸 | 契约约束 + 免责声明 |
| BudgetPool 余额不足 | Evidence 被截断 | 优先级分配 + degraded 标记 + reclaim |
| Codex 一把梭做 full | MVP 收敛失败 | dev_memory + milestone 强制 PR + 人工 review gate |

### 14.2 未决问题（v0.6 解决）

1. BudgetPool 余额不足时的 partial vs skip 策略
2. 8 类语义分类的 generic_error 兜底 confidence 是否合适（需 fixture 校准）
3. 简单后缀映射的歧义率监控阈值
4. ctags 对 namespace / template 的边界识别（决定 v0.6 是否引入 tree-sitter）
5. prompt 模板的版本演进与已存 packet 的兼容
6. 多包并发分析的线程/进程安全（v0.8）
7. expand 子命令的精确 schema（v0.6）
8. LLM 输出反馈环（修复成功/失败回流）
9. 错误消息国际化（非英文 locale）
10. gbs 之外的构建系统（OBS / bitbake）

---

## §15 附录

### 附录 A：术语表

- **gbs**：Git Build System，Tizen 本地构建工具
- **buildlog**：单次构建产生的完整日志
- **phase marker**：RPM 构建阶段分界标志，如 `+ %build`
- **terminal error**：根因错误（非 cascade）
- **cascade error**：由根因引发的派生错误
- **Evidence Packet**：本 skill 的核心产物
- **Fast-Path**：Layer 4a 命中后跳过证据收集的高速路径
- **direct_answer tier1/tier2**：tier1 无 evidence；tier2 需 evidence 完整
- **BudgetPool**：弹性预算池，HardReserve + SoftReserve
- **semantic_class**：错误语义分级，8 类
- **dev_memory**：milestone 开发产物记录
- **fallback_raw_context**：unknown error 时的最小兜底

### 附录 B：Evidence Packet schema 简表

| 顶层字段 | 类型 | 必含 | 说明 |
|---------|------|------|------|
| schema_version | string | ✓ | "evidence_packet/v1" |
| verdict | enum | ✓ | direct_answer \| needs_llm |
| via | enum | ✓ | fast_path \| full_path |
| package / arch / profile | string | ✓ | |
| failed_phase | string | ✓ | |
| root_cause_candidates | array | ✓ | Top-K 含文本摘要 |
| cascade_summary | string | ✓ | |
| primary_error | object | ✓ | |
| evidence | object | ✓ | 含 fallback_context（unknown 时） |
| matched_patterns | array | ✓ | |
| direct_answer | string\|null | ✓ | |
| matched_tier | enum\|null | | tier1 \| tier2 |
| prompt | string\|null | needs_llm 必含 | |
| token_budget | object | ✓ | 含 reclaim 详情 |
| degraded | bool | ✓ | |
| degraded_reasons | array | ✓ | |
| allowed_next_actions | array | ✓ | |

### 附录 C：演进历程归档

完整的 v0.1 → v0.5 演进文档（含三轮 ChatGPT review + 二轮 Kimi review）归档在 `docs/archive/`，按版本号组织。

---

**v0.5 文档完结。Codex 实施基线已冻结，进入实施阶段。**

参见 `docs/CODEX_PROMPT.md` 获取 Codex 启动 prompt。
