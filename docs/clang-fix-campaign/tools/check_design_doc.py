#!/usr/bin/env python3
"""design.md 契约一致性机械核对(§7.13 清单的可执行形态)。

用法:
    python3 tools/check_design_doc.py docs/clang-fix-campaign/design.md
    python3 tools/check_design_doc.py --self-test      # 运行内置正负 fixture

退出码: 0 = 无问题 / 1 = 发现问题 / 2 = 用法或输入错误。
变更提案落盘前必须运行,并把**实际输出**粘贴进提案(R13 精神)。
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

AUTHORITATIVE_PROMPT = "p45-implementation-prompt-v1_5_15.md"
PYTHON_FENCE_RE = re.compile(r"^```python[^\n]*\n(.*?)^```\s*$", re.M | re.S)
ANY_FENCE_RE = re.compile(r"^```[^\n]*\n.*?^```\s*$", re.M | re.S)
MERMAID_FENCE_RE = re.compile(r"^```mermaid[^\n]*\n(.*?)^```\s*$", re.M | re.S)
BARE_SIGNATURE_RE = re.compile(
    r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\(",
    re.M,
)
DESIGN_INDEX_RE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
    re.I,
)
PROMPT_INDEX_RE = re.compile(r"\b[iu]x_[a-z0-9_]+\b")
MERMAID_NODE_DECL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\[|\(|\{|>)")
MERMAID_EDGE_RE = re.compile(r"(?:-->|---|==>|-\.->)")

# 已知的非 REJECTED_ 前缀错误码/状态码(新增码请同步此处与 §4.3)
KNOWN_CODES = {
    "BASELINE_TOOLING_FAILED",
    "PREFLIGHT_FAILED",
    "QB_SUBMIT_FAILED",
    "PUSH_FAILED",
    "NOT_REPRODUCED",
    "ROUNDS_EXHAUSTED",
    "INVALID_ARGS",
    "DIFF_CONVERT_UNSUPPORTED",
    "KB_SCHEMA_INVALID",
    "INVALID_BRANCH_NAME",
    "CAMPAIGN_STATE_BUSY",
    "REVIEW_MANUAL",
}
# 改名映射(7e 格:每次改名必须在此登记)
RENAMED = {
    "adopt_secondary_target": "adopt_secondary_target_with_convergence",
    "campaign-build-verify": "campaign-repair-step",
    "campaign-check-convergence": "(已合并进 campaign-repair-step)",
    "link_verification(": "link_verification_with_convergence(",
}
# 错误码形态:全大写下划线,长度 >= 8,或以 REJECTED_ 开头
CODE_RE = r"(?:REJECTED_[A-Z][A-Z0-9_]*|[A-Z][A-Z0-9_]{7,})"


def _section(src: str, start_pat: str, end_pat: str) -> str:
    m = re.search(start_pat, src, re.M)
    n = re.search(end_pat, src, re.M)
    if not m:
        return ""
    return src[m.start() : n.start() if n else len(src)]


def _find_authoritative_prompt(design_path: Path) -> Path | None:
    for directory in (design_path.parent, *design_path.parents):
        candidate = directory / AUTHORITATIVE_PROMPT
        if candidate.is_file():
            return candidate
    return None


def _check_python_contracts(src: str) -> list[str]:
    problems: list[str] = []
    for match in PYTHON_FENCE_RE.finditer(src):
        line_no = src.count("\n", 0, match.start()) + 1
        try:
            compile(match.group(1), f"<design.md:L{line_no}>", "exec")
        except SyntaxError as exc:
            detail = exc.msg
            if exc.lineno is not None:
                detail += f" at block line {exc.lineno}"
            problems.append(f"[CK-API-01] L{line_no}: {detail}")

    bare_src = ANY_FENCE_RE.sub(
        lambda match: "\n" * match.group(0).count("\n"),
        src,
    )
    for match in BARE_SIGNATURE_RE.finditer(bare_src):
        line_no = bare_src.count("\n", 0, match.start()) + 1
        signature = match.group(0).rstrip("(")
        problems.append(f"[CK-API-01] L{line_no}: fence 外模块式裸签名 {signature}")
    return problems


def _check_index_contract(src: str, prompt_src: str | None) -> list[str]:
    if prompt_src is None:
        return [f"[CK-IDX-01] 缺少唯一权威 prompt: {AUTHORITATIVE_PROMPT}"]
    design_indexes = {name.lower() for name in DESIGN_INDEX_RE.findall(src)}
    prompt_indexes = set(PROMPT_INDEX_RE.findall(prompt_src.lower()))
    if not prompt_indexes:
        return ["[CK-IDX-01] 权威 prompt 的索引 token 集合为空"]
    unknown = sorted(prompt_indexes - design_indexes)
    if unknown:
        return ["[CK-IDX-01] prompt 索引不属于 design 集合: " + ", ".join(unknown)]
    return []


def _mermaid_edge_nodes(line: str) -> list[str]:
    if not MERMAID_EDGE_RE.search(line):
        return []
    without_labels = re.sub(r"\|[^|]*\|", "", line)
    nodes: list[str] = []
    for segment in MERMAID_EDGE_RE.split(without_labels):
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", segment)
        if match:
            nodes.append(match.group(1))
    return nodes


def _check_mermaid_contracts(src: str) -> list[str]:
    problems: list[str] = []
    for block in MERMAID_FENCE_RE.finditer(src):
        block_line = src.count("\n", 0, block.start()) + 1
        declared: set[str] = set()
        for offset, line in enumerate(block.group(1).splitlines(), 1):
            declared.update(MERMAID_NODE_DECL_RE.findall(line))
            for node in _mermaid_edge_nodes(line):
                if node not in declared:
                    problems.append(
                        f"[CK-MMD-01] L{block_line + offset}: 节点 {node} 在声明前被引用"
                    )

    return problems


def check(src: str, *, prompt_src: str | None = None) -> list[str]:
    lines = src.split("\n")
    problems: list[str] = []
    problems.extend(_check_python_contracts(src))
    problems.extend(_check_index_contract(src, prompt_src))
    problems.extend(_check_mermaid_contracts(src))
    sec43 = _section(src, r"^### 4\.3 ", r"^## 5\. ")
    if not sec43:
        problems.append("[STRUCT] 找不到 §4.3 错误码章节")

    # 0) **权威清单**:§4.3 表内"行首(可缩进)+ 全大写码"即已登记错误码。
    #    分类不再靠白名单猜测——这是 v1.5.4 三轮返工的根因(状态名与错误码
    #    形态重叠,穷举必漏)。
    # "§4.3 表内出现的码 = 已登记"(长码后可能只有单空格,亦可能跨行折断)
    registered = set(re.findall(rf"\b({CODE_RE})\b", sec43))
    registered |= {c.rstrip("_") for c in registered}
    # 状态名权威清单:§3.6 状态机表首列
    sec36 = _section(src, r"^### 3\.6 ", r"^### 3\.7 ")
    state_names = set(re.findall(rf"^\|\s*\**({CODE_RE})", sec36, re.M))
    # 事件名权威清单:§3.4 payload 契约表首列(| `REPRODUCE` | …)
    # 仅 §3.6 状态机表与 §3.4 payload 契约表的首列算权威;其余表首列不豁免
    sec34 = _section(src, r"^### 3\.4 ", r"^### 3\.5 ")
    state_names |= set(re.findall(r"^\|\s*\**`?([A-Z][A-Z0-9_]{3,})`?", sec34, re.M))
    # 1) 错误码登记(不依赖白名单:全大写码一律要求登记,豁免表仅用于排除非错误码)
    NON_CODE = {
        "BEGIN",
        "IMMEDIATE",
        "PRIMARY",
        "AUTOINCREMENT",
        "NOT",
        "NULL",
        "CREATE",
        "TABLE",
        "EXISTS",
        "FOREIGN",
        "REFERENCES",
        "UNIQUE",
        "INTEGER",
        "TEXT",
        "CHECK",
        "INDEX",
        "DEFAULT",
        "SELECT",
        "PASS",
        "FAIL",
        "JSON",
        "TODO",
        "HELD_FOR_INVESTIGATION",
        "WORKTREE_LOST",
        "SANDBOX_QB_FAILED",
        "SANDBOX_QB_PASS",
        "SANDBOX_PUSHED",
        "REVIEW_PUSHED",
        "REVIEW_INELIGIBLE",
        "LOCAL_3ARCH_PASS",
        "BASELINE_REPRODUCED",
        "CI_EVIDENCE_READY",
        "REPAIR_ROUND_RUNNING",
        "QB_REQUESTED",
        "QB_TRIGGERED",
        "SANDBOX_QB_PENDING",
        "SANDBOX_PUSHING",
        "REVIEW_PUSHING",
        "KB_APPENDED",
        "DISCOVERED",
        "BASELINE_RUNNING",
        "DENIED",
        "STALLED",
        "REGRESSED",
        "GERRIT_READY",
        "WORKSPACE_CLEANUP",
        "WORKSPACE_RELEASE",
        "BUILD_INVOCATION",
        "SECONDARY_TARGET_ADOPTED",
        "ORPHAN_PASS",
        "CONVERGENCE",
        "REPRODUCE",
        "CI_EVIDENCE",
        "BUILD_OUTCOME",
        "SUBMITTED",
        "BUILD_BOUND",
        "RESULT",
        "MAX_ROUNDS",
        "MAX_BUILD_INVOCATIONS",
        "QB_PASSWORD",
        "SANDBOX_PUSH_FAILED",
        "REVIEW_PUSH_FAILED",
        "QB_SUBMIT_FAILED",
        "NOT_REPRODUCED",
        "ROUNDS_EXHAUSTED",
        "QB_COOKIE",
        "JSESSIONID_8810",
        "SBS_TARGET",
        "EXIT_TIMEOUT",
    }
    all_codes = {
        c for c in re.findall(rf"\b({CODE_RE})\b", src) if not c.endswith("_")
    }  # 过滤跨行折断碎片
    for c in sorted(all_codes):
        if c in registered or c.rstrip("_") in registered:
            continue
        if c in NON_CODE or c in state_names:
            continue
        if c in KNOWN_CODES and c in registered:
            continue
        looks_like_code = (
            c.startswith("REJECTED_")
            or c in KNOWN_CODES
            or re.search(
                r"_(FAILED|MISMATCH|ERROR|EXHAUSTED|INVALID|MISSING|"
                r"BUSY|DENIED|SUPERSEDED|NOT_ALLOWED|NOT_BOUND|"
                r"NOT_VERIFIED|UNSUPPORTED|DRIFT|TIMEOUT|BUSY|CONFLICT)$",
                c,
            )
        )
        if looks_like_code and c not in registered:
            problems.append(f"[ERRCODE] {c} 未登记于 §4.3")

    # 2) 拼接损坏:§4.3 之外出现 "CODE + >=2 空格 + 说明"(不再要求行首特征)
    off43 = src.find(sec43) if sec43 else -1
    pos = 0
    for i, line in enumerate(lines, 1):
        in43 = off43 >= 0 and off43 <= pos < off43 + len(sec43)
        pos += len(line) + 1
        if in43:
            continue
        # 定义式排版特征:未加反引号的**错误码**(非状态名/事件名)+ 空白 + 说明
        for m in re.finditer(rf"(`?)({CODE_RE})(`?)(\s+)(\S)", line):
            code = m.group(2)
            if code in state_names:
                continue
            is_code = (
                code in registered
                or code.startswith("REJECTED_")
                or code in KNOWN_CODES
                or re.search(
                    r"_(FAILED|MISMATCH|ERROR|EXHAUSTED|INVALID|"
                    r"MISSING|BUSY|DENIED|SUPERSEDED|NOT_ALLOWED|"
                    r"NOT_BOUND|NOT_VERIFIED|UNSUPPORTED|DRIFT|TIMEOUT|CONFLICT)$",
                    code,
                )
            )
            if not is_code:
                continue
            quoted = m.group(1) == "`" or m.group(3) == "`"
            gap, nxt = m.group(4), m.group(5)
            if quoted:
                continue
            # 真实事故签名:①2+ 空格对齐(§4.3 表式)②码后紧跟 ASCII 小写
            # 英文说明(如 "REJECTED_X previous evidence 缺失")。
            # 码后跟中文/标点是正常散文(如 "→ REJECTED_X 且不计费"),不报。
            if len(gap) >= 2 or re.match(r"[a-z]", nxt):
                problems.append(f"[SPLICE] L{i}: §4.3 外出现错误码定义式排版: {line.strip()[:70]}")
                break

    # 3) 断链
    heads = set(re.findall(r"^#{2,4}\s+([0-9]+(?:\.[0-9]+)*)", src, re.M))
    for ref in sorted(set(re.findall(r"§([0-9]+(?:\.[0-9]+)*)", src))):
        if ref not in heads and not any(h.startswith(ref + ".") for h in heads):
            problems.append(f"[CK-XREF-01][DEADLINK] §{ref} 无对应章节")

    # 4) 占位符(排除 CLI 参数式占位)
    ok_ph = re.compile(r"路径|页名|副本|URL|形态|映射|<[a-z_0-9]+>|数字|可空")
    for i, line in enumerate(lines, 1):
        for ph in re.findall(r"<[^>\n]{2,40}>", line):
            if re.search(r"[\u4e00-\u9fff]", ph) and not ok_ph.search(ph):
                problems.append(f"[PLACEHOLDER] L{i}: {ph}")

    # 5) 改名旧名残留(仅 "(历史)" 标记豁免;不再按 v1.4 等版本串豁免)
    for old, new in RENAMED.items():
        pat = re.escape(old) if old.endswith("(") else rf"(?<![\w-]){re.escape(old)}(?![\w-])"
        for i, line in enumerate(lines, 1):
            if re.search(pat, line) and "(历史)" not in line:
                problems.append(f"[RENAMED] L{i}: 旧名 {old} → 应为 {new}")

    # 6) 表格中间空行
    in_tbl = False
    for i, line in enumerate(lines, 1):
        if line.startswith("| "):
            in_tbl = True
        elif in_tbl:
            if line.strip() == "" and i < len(lines) and lines[i].startswith("| "):
                problems.append(f"[TABLE] L{i}: 表格中间空行,渲染会断表")
            in_tbl = False

    # 6b) 数据锚点:campaign_units 的 NOT NULL 列须在 §3.3 数据流中出现
    ddl = _section(
        src,
        r"CREATE TABLE IF NOT EXISTS campaign_units",
        r"CREATE TABLE IF NOT EXISTS campaign_gate_events",
    )
    flow = _section(src, r"^### 3\.3 ", r"^### 3\.4 ")
    for col in re.findall(r"^\s{2}([a-z_]+)\s+\w+[^\n]*NOT NULL", ddl, re.M):
        if col in {"created_at", "schema_version"}:
            continue
        if col not in flow and col not in _section(src, r"^## 4\. ", r"^## 5\. "):
            problems.append(f"[ANCHOR] campaign_units.{col} 为 NOT NULL,但 §3.3/§4 未描述其写入方")

    # 7) 版本号头尾一致(任一缺失即报,不再静默跳过)
    #    冻结流程与草案复用同一 checker;mode 也是契约的一部分,
    #    禁止头部声称 FROZEN 而文末仍是 draft(或反之)。
    hv = re.search(r"- 版本:\*\*(v[\d.]+)-(draft|FROZEN)", src)
    tv = re.search(r"本文档为 \*\*(v[\d.]+)-(draft|FROZEN)", src)
    if not hv:
        problems.append("[VERSION] 缺少头部版本声明")
    if not tv:
        problems.append("[VERSION] 缺少文末版本声明")
    if hv and tv and hv.groups() != tv.groups():
        problems.append(
            f"[VERSION] 头 {hv.group(1)}-{hv.group(2)} ≠ 尾 {tv.group(1)}-{tv.group(2)}"
        )
    return problems


BASE_OK = """# d
- 版本:**v1.5.4-draft**
CREATE INDEX IF NOT EXISTS ix_fixture ON fixture_table (id);
## 4. 接口契约
### 4.3 错误码定义
REJECTED_FOO                       示例
## 5. 非功能性需求
本文档为 **v1.5.4-draft**。
"""
BASE_PROMPT_OK = "ix_fixture"


def self_test() -> int:
    """每条规则的正负 fixture:负例必须被抓到,正例必须放行。"""
    cases = [
        ("baseline-ok", BASE_OK, None),
        # 注:负例必须插在 §4.3 **之前**(插在 "### 4.3" 前),否则会落进
        # §4.3 区间内被合法豁免——fixture 位置本身也是被测对象。
        (
            "errcode-unregistered",
            BASE_OK.replace("### 4.3", "文中提到 SOURCE_SCAN_FAILED\n### 4.3"),
            "[ERRCODE]",
        ),
        # 复刻 v1.4.10 与 v1.5.2 两次真实事故(码后紧跟英文说明 / 表式对齐)
        (
            "splice-real-inline",
            BASE_OK.replace(
                "### 4.3",
                "  # 否则 exit 4 REJECTED_BAR previous evidence 缺失或 hash 不符\n### 4.3",
            ),
            "[SPLICE]",
        ),
        (
            "splice-real-aligned",
            BASE_OK.replace(
                "### 4.3", "REJECTED_BAZ                       说明被贴进正文\n### 4.3"
            ),
            "[SPLICE]",
        ),
        (
            "splice-prose-ok",
            BASE_OK.replace("### 4.3", "身份不符 → REJECTED_FOO 且不计费;\n### 4.3"),
            None,
        ),
        # 甲方变异测试复刻:*_FAILED 形态的未登记码 + 表式对齐,必须双报
        (
            "mutation-xyz-failed",
            BASE_OK.replace(
                "### 4.3", "REJECTED_XYZ_FAILED                说明被贴进正文\n### 4.3"
            ),
            "[SPLICE]",
        ),
        (
            "mutation-xyz-errcode",
            BASE_OK.replace(
                "### 4.3", "REJECTED_XYZ_FAILED                说明被贴进正文\n### 4.3"
            ),
            "[ERRCODE]",
        ),
        (
            "mutation-inline-failed",
            BASE_OK.replace(
                "### 4.3", "  # exit 4 SOURCE_SCAN_FAILED previous evidence 缺失\n### 4.3"
            ),
            "[SPLICE]",
        ),
        # 状态名后跟中文是正常写法,不得误报
        (
            "state-name-prose-ok",
            (
                BASE_OK.replace(
                    "## 4. 接口契约",
                    "### 3.6 状态机\n| SANDBOX_PUSH_FAILED | 说明 |\n### 3.7 x\n## 4. 接口契约",
                ).replace("### 4.3", "推送失败进入 SANDBOX_PUSH_FAILED 状态,可重入。\n### 4.3")
            ),
            None,
        ),
        (
            "splice-backticked-ok",
            BASE_OK.replace("### 4.3", "  # 否则 exit 4 `REJECTED_FOO`(见下)\n### 4.3"),
            None,
        ),
        (
            "renamed-with-version-line",
            BASE_OK.replace("### 4.3", "v1.4 起 adopt_secondary_target 用于…\n### 4.3"),
            "[RENAMED]",
        ),
        (
            "renamed-history-exempt",
            BASE_OK.replace("### 4.3", "adopt_secondary_target(历史)已废弃\n### 4.3"),
            None,
        ),
        ("version-tail-missing", BASE_OK.replace("本文档为 **v1.5.4-draft**。", ""), "[VERSION]"),
        (
            "version-mismatch",
            BASE_OK.replace("本文档为 **v1.5.4-draft**", "本文档为 **v1.5.3-draft**"),
            "[VERSION]",
        ),
        ("version-frozen-ok", BASE_OK.replace("v1.5.4-draft", "v1.5.4-FROZEN"), None),
        (
            "version-mode-mismatch",
            BASE_OK.replace("- 版本:**v1.5.4-draft**", "- 版本:**v1.5.4-FROZEN**"),
            "[VERSION]",
        ),
        # ANCHOR 正负例(乙-M8:此前无 fixture)
        (
            "anchor-missing",
            BASE_OK.replace(
                "## 4. 接口契约",
                "### 3.3 数据流\n发现层建 unit。\n### 3.4 x\n"
                "CREATE TABLE IF NOT EXISTS campaign_units (\n"
                "  ci_evidence_ref TEXT NOT NULL,\n);\n"
                "CREATE TABLE IF NOT EXISTS campaign_gate_events (\n);\n## 4. 接口契约",
            ),
            "[ANCHOR]",
        ),
        (
            "anchor-described-ok",
            BASE_OK.replace(
                "## 4. 接口契约",
                "### 3.3 数据流\n发现层写入 ci_evidence_ref 锚点。\n### 3.4 x\n"
                "CREATE TABLE IF NOT EXISTS campaign_units (\n"
                "  ci_evidence_ref TEXT NOT NULL,\n);\n"
                "CREATE TABLE IF NOT EXISTS campaign_gate_events (\n);\n## 4. 接口契约",
            ),
            None,
        ),
        # 甲-8 变异:无关表格首列的未登记错误码 / *_TIMEOUT 形态
        (
            "mutation-table-firstcol",
            BASE_OK.replace("### 4.3", "| SOME_UNREGISTERED_FAILED | 说明 |\n### 4.3"),
            "[ERRCODE]",
        ),
        (
            "mutation-fetch-timeout",
            BASE_OK.replace("### 4.3", "超时 → FETCH_TIMEOUT 处理\n### 4.3"),
            "[ERRCODE]",
        ),
        ("deadlink", BASE_OK.replace("### 4.3", "见 §9.9\n### 4.3"), "[DEADLINK]"),
        ("table-blank", BASE_OK.replace("### 4.3", "| a | b |\n\n| c | d |\n### 4.3"), "[TABLE]"),
    ]
    contract_cases = [
        (
            "ck-api-duplicate-arg",
            BASE_OK.replace(
                "### 4.3",
                "```python\ndef broken(a, a): ...\n```\n### 4.3",
            ),
            "[CK-API-01]",
            BASE_PROMPT_OK,
        ),
        (
            "ck-api-b4-duplicate-arg",
            BASE_OK.replace(
                "### 4.3",
                "```python\n"
                "def adopt(state_db, *, convergence_payload, arch_norm,\n"
                "          convergence_payload): ...\n"
                "```\n### 4.3",
            ),
            "[CK-API-01]",
            BASE_PROMPT_OK,
        ),
        (
            "ck-api-bare-single",
            BASE_OK.replace(
                "### 4.3",
                "campaign_state.latest_status(state_db, unit) -> str\n### 4.3",
            ),
            "[CK-API-01]",
            BASE_PROMPT_OK,
        ),
        (
            "ck-api-bare-multiline",
            BASE_OK.replace(
                "### 4.3",
                "campaign_state.build_campaign_unit_key(*, ci_system,\n"
                "    source_build_id, project) -> str\n### 4.3",
            ),
            "[CK-API-01]",
            BASE_PROMPT_OK,
        ),
        (
            "ck-idx-stale-name",
            BASE_OK,
            "[CK-IDX-01]",
            "ux_convergence_once",
        ),
        (
            "ck-idx-nonempty-subset",
            BASE_OK,
            None,
            BASE_PROMPT_OK,
        ),
        (
            "ck-idx-empty",
            BASE_OK,
            "[CK-IDX-01]",
            "no index token here",
        ),
        (
            "ck-mmd-forward-reference",
            BASE_OK.replace(
                "### 4.3",
                "```mermaid\nflowchart TD\nA[start]\nA --> B\nB[end]\n```\n### 4.3",
            ),
            "[CK-MMD-01]",
            BASE_PROMPT_OK,
        ),
        (
            "ck-mmd-declared-first",
            BASE_OK.replace(
                "### 4.3",
                "```mermaid\nflowchart TD\nA[start]\nB[end]\nA --> B\n```\n### 4.3",
            ),
            None,
            BASE_PROMPT_OK,
        ),
    ]
    all_cases = [
        (name, doc, expect, BASE_PROMPT_OK) for name, doc, expect in cases
    ] + contract_cases
    failed = 0
    for name, doc, expect, prompt_src in all_cases:
        got = check(doc, prompt_src=prompt_src)
        hit = any(expect in p for p in got) if expect else not got
        status = "ok" if hit else "FAIL"
        if not hit:
            failed += 1
        print(f"[self-test] {status:4} {name}: expect={expect or 'no-problem'} got={got or '[]'}")

    ruff = shutil.which("ruff")
    if ruff is None:
        repo_ruff = Path(__file__).resolve().parents[3] / ".venv" / "bin" / "ruff"
        if repo_ruff.is_file():
            ruff = str(repo_ruff)
    ruff_ok = False
    ruff_output = "ruff executable not found"
    if ruff is not None:
        result = subprocess.run(
            [ruff, "check", "--select", "E,F", str(Path(__file__).resolve())],
            check=False,
            capture_output=True,
            text=True,
        )
        ruff_ok = result.returncode == 0
        ruff_output = (result.stdout + result.stderr).strip() or "clean"
    print(f"[self-test] {'ok' if ruff_ok else 'FAIL':4} ruff-e-f: {ruff_output}")
    if not ruff_ok:
        failed += 1

    campaign_dir = Path(__file__).resolve().parent.parent
    historical_path = campaign_dir / "design_changes" / "clang-fix-campaign-design-v1.5.2-draft.md"
    authoritative_prompt = campaign_dir / AUTHORITATIVE_PROMPT
    historical_ok = False
    historical_detail = "historical sample or prompt missing"
    if historical_path.is_file() and authoritative_prompt.is_file():
        historical_problems = check(
            historical_path.read_text(encoding="utf-8"),
            prompt_src=authoritative_prompt.read_text(encoding="utf-8"),
        )
        legacy_counts: dict[str, int] = {}
        for problem in historical_problems:
            tag = problem.split("]", 1)[0] + "]"
            if tag.startswith("[CK-"):
                continue
            legacy_counts[tag] = legacy_counts.get(tag, 0) + 1
        expected_counts = {"[ERRCODE]": 5, "[SPLICE]": 1, "[RENAMED]": 6}
        historical_ok = legacy_counts == expected_counts
        historical_detail = f"legacy={legacy_counts}, expected={expected_counts}"
    print(
        f"[self-test] {'ok' if historical_ok else 'FAIL':4} historical-v1.5.2: {historical_detail}"
    )
    if not historical_ok:
        failed += 1

    total = len(all_cases) + 2
    print(f"-- self-test: {total - failed}/{total} passed --")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="design.md 契约一致性机械核对")
    ap.add_argument("path", nargs="?", help="design.md 路径")
    ap.add_argument("--self-test", action="store_true", help="运行内置正负 fixture")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.path:
        ap.error("需要 design.md 路径,或使用 --self-test")
    p = Path(args.path)
    if not p.is_file():
        print(f"[FATAL] 文件不存在: {p}", file=sys.stderr)
        return 2
    prompt_path = _find_authoritative_prompt(p)
    prompt_src = prompt_path.read_text(encoding="utf-8") if prompt_path is not None else None
    problems = check(
        p.read_text(encoding="utf-8"),
        prompt_src=prompt_src,
    )
    print(f"== check_design_doc: {p} ==")
    for x in problems:
        print(x)
    print(f"-- {len(problems)} problem(s) --" if problems else "-- OK: 0 problem --")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
