"""Bounded, read-only request-marker discovery on registered configuration pages."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tizen_ci_shared.state import StateDatabase

from ci_triage import campaign_state as state
from ci_triage import qb_binding as binding
from ci_triage import qb_result_html as pages
from ci_triage.qb_browser import QbBrowser, QbBrowserError
from ci_triage.qb_evidence import archive
from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor

IDENTITY_CHECKS = frozenset(
    {
        "configuration_title",
        "configuration_http",
        "configuration_read",
        "breadcrumb",
        "breadcrumb_path",
        "breadcrumb_current",
        "copy_path",
    }
)


def baseline_message(check: str) -> str:
    if check in IDENTITY_CHECKS:
        return (
            f"配置页身份与冻结 profile 不符({check}),该 overview_id 可能已不指向冻结的配置;"
            "停止提交,按 R1 核对第 2.2 节冻结值与附录 C 第 3 项"
        )
    return (
        f"配置页最近构建表结构与登记不符({check}),自动查找无法工作,故不提交;"
        "处置是按 R1 更新附录 C 第 18 项的登记与第 5.5 节第 1 步的解析规则,不涉及表单与放行规则"
    )


def page_reply(reply: dict[str, Any]) -> tuple[str, int, int]:
    html, status, count = (
        reply.get("html_redacted"),
        reply.get("status"),
        reply.get("outside_identity_count"),
    )
    if not isinstance(html, str) or type(status) is not int or type(count) is not int or count < 0:
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    PageRedactor().check_bytes(html.encode("utf-8"))
    return html, status, count


def baseline(browser: QbBrowser, profile: dict[str, Any]) -> int:
    html, status, _count = page_reply(
        browser.command("read", path=f"/overview/{profile['overview_id']}")
    )
    pages.require(status == 200, "configuration_http", "REJECTED_QB_FORM_CHANGED")
    return max((int(build) for build in pages.recent_builds(html, profile)), default=0)


@dataclass
class Discovery:
    category: str = "未找到"
    builds: list[str] = field(default_factory=list)
    checked: set[str] = field(default_factory=set)
    unreadable: set[str] = field(default_factory=set)
    evidence: list[str] = field(default_factory=list)
    facts: dict[str, Any] | None = None

    def retry_message(self, request_id: str, *, driver_failure: bool = False) -> str:
        counts = (
            ""
            if driver_failure
            else (
                f"({self.category},已核对 {len(self.checked)} 个候选,"
                f"{len(self.unreadable)} 个暂不可读)"
            )
        )
        return (
            f"自动查找未找到带本请求标记的构建{counts};请尽快运行 qb-result-fetch --request-id "
            f"{request_id} 再次自动查找(配置页最近构建表只保留约 10 个构建,该配置再产生约 10 个"
            "新构建后将只能人工查号),或到 QuickBuild 按请求标记找到构建后用 --qb-build-id 绑定;"
            "确认没有构建后用 --retrigger 重提"
        )


def discover(
    browser: QbBrowser,
    db: StateDatabase,
    root: Path,
    request: dict[str, Any],
    profile: dict[str, Any],
    *,
    baseline_w: int,
    submitted_at: float | None,
    trace: Callable[[dict[str, Any]], None],
) -> Discovery:
    result = Discovery()
    conn = state._read_connection(db)
    try:
        binding.automatic_allowed(conn, request)
    finally:
        conn.close()
    mode = "post_submit" if submitted_at is not None else "read"
    deadline = submitted_at + 180 if submitted_at is not None else None
    different: set[str] = set()
    last_configuration: str | None = None
    archive_attempted = False
    matched: dict[str, str] = {}
    rounds: list[dict[str, Any]] = []
    path = f"/overview/{profile['overview_id']}"

    def expired() -> bool:
        return deadline is not None and time.monotonic() > deadline

    def read(path: str, round_: dict[str, Any]) -> tuple[str, int, int]:
        started = time.monotonic()
        observation: dict[str, Any] = dict(
            path=path, elapsed_ms=0, outside_identity_count=None, failure=None
        )
        round_["reads"].append(observation)
        try:
            html, status, count = page_reply(browser.command("read", path=path))
            observation["outside_identity_count"] = count
            return html, status, count
        except QbBrowserError as exc:
            observation["failure"] = exc.failure_facts()
            raise
        finally:
            observation["elapsed_ms"] = round((time.monotonic() - started) * 1000)

    try:
        for index in range(10 if submitted_at is not None else 1):
            if expired():
                break
            matched = {}
            round_: dict[str, Any] = dict(
                started_seconds=0 if submitted_at is None else time.monotonic() - submitted_at,
                configuration_status=None,
                row_count=None,
                candidates=[],
                reads=[],
            )
            rounds.append(round_)
            ids: list[str] | None = None
            try:
                html, status, _ = read(path, round_)
                last_configuration = html
                round_["configuration_status"] = status
                if status != 200:
                    result.category = "配置页读取失败"
                else:
                    ids = pages.recent_builds(html, profile)
                    round_["row_count"] = len(ids)
            except pages.ResultCheckError:
                result.category = "配置页不可识别"
            except QbBrowserError as exc:
                if exc.code == "QB_EVIDENCE_REDACTION_FAILED":
                    raise
                if exc.agent_code in {"QB_READ_REDIRECTED", "QB_READ_ID_MISMATCH"}:
                    result.category = "配置页读取失败"
                else:
                    result.category = "读取失败"
                    break
            if ids is not None:
                result.category = "未找到"
                conn = state._read_connection(db)
                try:
                    bound = {
                        r[0]
                        for r in conn.execute(
                            "SELECT qb_build_id FROM campaign_qb_events "
                            "WHERE event_type='BUILD_BOUND'"
                        )
                    }
                finally:
                    conn.close()
                candidates = sorted(
                    (
                        i
                        for i in ids
                        if int(i) > baseline_w and i not in bound and i not in different
                    ),
                    key=int,
                )
                for build in candidates:
                    if expired():
                        result.category = "查找超时"
                        break
                    result.checked.add(build)
                    category = "暂不可读"
                    try:
                        html, status, _ = read(f"/build/{build}/variables", round_)
                        if status == 200:
                            values = pages.variables(html)
                            if "BUILD_NOTES" in values:
                                # No candidate payload, including agent diagnostics, leaves memory.
                                if (
                                    values["BUILD_NOTES"][1]
                                    == f"clang-fix-campaign request={request['request_id']}"
                                ):
                                    category = "匹配"
                                    matched[build] = html
                                else:
                                    category = "标记不同"
                                    different.add(build)
                    except pages.ResultCheckError:
                        pass
                    except QbBrowserError as exc:
                        if exc.code == "QB_EVIDENCE_REDACTION_FAILED":
                            raise
                        if exc.agent_code not in {"QB_READ_REDIRECTED", "QB_READ_ID_MISMATCH"}:
                            category = result.category = "读取失败"
                    round_["candidates"].append(dict(build_id=build, category=category))
                    if category == "暂不可读":
                        result.unreadable.add(build)
                    else:
                        result.unreadable.discard(build)
                    if category == "读取失败":
                        break
                if result.category in {"读取失败", "查找超时"}:
                    break
                if matched:
                    result.builds = list(matched)
                    result.category = "匹配" if len(matched) == 1 else "多于一个"
                    break
            if deadline is None or index == 9 or expired():
                break
            time.sleep(min(20, max(0, deadline - time.monotonic())))
        if last_configuration is not None:
            archive_attempted = True
            result.evidence.append(archive(root, request["request_id"], path, last_configuration))
        if result.category == "匹配":
            if expired():
                result.category = "查找超时"
            else:
                build = result.builds[0]
                overview, status, _ = read(f"/build/{build}/overview", rounds[-1])
                pages.require(status == 200, "binding_http")
                for page_path, html in (
                    (f"/build/{build}/variables", matched[build]),
                    (f"/build/{build}/overview", overview),
                ):
                    result.evidence.append(archive(root, request["request_id"], page_path, html))
                result.facts = binding.parent_facts(
                    overview, matched[build], build, profile, request
                )
                binding.bind(db, request, build)
                result.category = "已绑定"
    except pages.ResultCheckError:
        result.category = "核对不通过"
    except QbBrowserError as exc:
        result.category = (
            "证据脱敏自检失败" if exc.code == "QB_EVIDENCE_REDACTION_FAILED" else "读取失败"
        )
    except EvidenceRedactionError:
        result.category = "证据脱敏自检失败"
    finally:
        if last_configuration is not None and not archive_attempted:
            try:
                result.evidence.append(
                    archive(root, request["request_id"], path, last_configuration)
                )
            except EvidenceRedactionError:
                result.category = "证据脱敏自检失败"
        trace(
            dict(
                request_id=request["request_id"],
                mode=mode,
                W=baseline_w,
                rounds=rounds,
                final_category=result.category,
            )
        )
    return result
