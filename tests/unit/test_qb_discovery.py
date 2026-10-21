from __future__ import annotations

import io
import json
from queue import Empty, Queue

import pytest
from ci_triage import campaign_state as state
from ci_triage import qb_binding as binding
from ci_triage import qb_discovery as discovery
from ci_triage import qb_result_html as pages
from ci_triage import qb_trigger as trigger
from ci_triage.qb_browser import QbBrowserError
from ci_triage.qb_redact import PageRedactor
from qb_discovery_fixtures import CONFIG_ARCHIVE, configuration, reply
from test_qb_result_fetch import FROZEN, C, FetchCampaign, P, R, variable_page
from test_qb_trigger import Campaign


@pytest.fixture
def c(tmp_path, monkeypatch):
    return FetchCampaign(tmp_path, monkeypatch)


def config_reply(c, ids=()):
    return reply(configuration(c.project, ids))


def run_find(c, replies, *, post=False, w=0, advance=None):
    class Browser:
        def __init__(self):
            self.calls = []
            self.replies = iter(replies)

        def command(self, command, **fields):
            assert command == "read"
            self.calls.append(fields["path"])
            if advance:
                advance(fields["path"], len(self.calls))
            response = next(self.replies)
            if isinstance(response, Exception):
                raise response
            return response

    browser = Browser()
    traces = []
    request = c.sql("SELECT * FROM campaign_qb_requests")[0]
    out = discovery.discover(
        browser,
        c.db,
        c.root,
        request,
        json.loads(c.profile),
        baseline_w=w,
        submitted_at=0 if post else None,
        trace=traces.append,
    )
    return out, browser.calls, traces


def test_actual_configuration_heading_with_history_rss(c):
    ids = pages.recent_builds(CONFIG_ARCHIVE.read_text(), c.project)
    assert len(ids) == 10 and "1201886" in ids
    assert pages.recent_builds(configuration(c.project), c.project) == []


def test_configuration_dropdown_and_stop_links_are_not_build_links(c):
    html = configuration(c.project, [P, C])
    assert html.count('href="javascript:void(0);"') == 2
    assert html.count("ILinkListener-stop") == 2
    assert pages.recent_builds(html, c.project) == [P, C]


BAD_CONFIG = [
    ("configuration_title", lambda s: s.replace("QuickBuild - ", "Wrong - ")),
    ("breadcrumb_path", lambda s: s.replace("<span>root</span>", "<span>other</span>")),
    ("copy_path", lambda s: s.replace("'copy', 'root/", "'copy', 'other/")),
    ("recent_builds_title", lambda s: s.replace("Recent Builds", "Other")),
    ("recent_builds_title", lambda s: s.replace('class="flex-1"', 'class="other"')),
    (
        "recent_builds_title",
        lambda s: s.replace(
            "<a>history</a>", '<div class="box-head"><div class="flex-1">Recent Builds</div></div>'
        ),
    ),
    ("recent_builds_columns", lambda s: s.replace("<th>Id</th>", "<th>Extra</th><th>Id</th>")),
    (
        "recent_builds_columns",
        lambda s: s.replace("<th>Id</th><th>Version</th>", "<th>Version</th><th>Id</th>"),
    ),
    ("recent_builds_link", lambda s: s.replace(f'href="/build/{P}"', 'href="/build/9"')),
    (
        "recent_builds_link",
        lambda s: s.replace('</a><a href="/?', f'</a><a href="/build/{P}">dup</a><a href="/?'),
    ),
    ("recent_builds_id", lambda s: s.replace(f"<td>{P}</td>", "<td>bad</td>")),
    ("recent_builds_duplicate_id", lambda s: s.replace("</tbody>", s.split("<tbody>")[1])),
]


@pytest.mark.parametrize(
    "check,change", BAD_CONFIG, ids=[p[0] + str(i) for i, p in enumerate(BAD_CONFIG)]
)
@pytest.mark.parametrize("mode", ["baseline", "post", "read"])
def test_bad_configuration_all_modes(c, check, change, mode):
    bad = change(configuration(c.project, [P]))
    if mode == "baseline":

        class Browser:
            def command(self, *args, **kwargs):
                return reply(bad)

        output = trigger.empty_result()
        with pytest.raises(trigger._Rejected, match="REJECTED_QB_FORM_CHANGED"):
            trigger._baseline(Browser(), c.project, output)
        assert f"({check})" in output["message"]
        assert ("配置页身份" in output["message"]) == (check in discovery.IDENTITY_CHECKS)
    else:
        out, calls, _ = run_find(c, [reply(bad)] * 10, post=mode == "post")
        assert out.category == "配置页不可识别"
        assert len(calls) == (10 if mode == "post" else 1)
        assert len(out.evidence) == 1 and not c.events("BUILD_BOUND")


def test_51_rows_rejected(c):
    with pytest.raises(pages.ResultCheckError, match=pages.BINDING) as caught:
        pages.recent_builds(configuration(c.project, range(1, 52)), c.project)
    assert caught.value.check == "recent_builds_limit"


@pytest.mark.parametrize("post", [False, True])
def test_unique_match_shares_manual_binding_and_archives_only_matching(c, post):
    c.parent_changes["BUILD_NOTES"] = ("BUILD NOTES", "other marker")
    other = reply(variable_page(2, c.parent_changes))
    c.parent_changes["BUILD_NOTES"] = ("BUILD NOTES", "clang-fix-campaign request=" + R)
    out, calls, traces = run_find(
        c, [config_reply(c, ["1", P]), other, c.replies()[1], c.replies()[0]], post=post
    )
    assert out.category == "已绑定" and out.builds == [P]
    assert calls == [
        "/overview/1917",
        "/build/1/variables",
        f"/build/{P}/variables",
        f"/build/{P}/overview",
    ]
    assert [e.split("/")[-1] for e in out.evidence] == [
        "01.overview-1917.html",
        f"02.{P}-variables.html",
        f"03.{P}-overview.html",
    ]
    assert "other marker" not in "".join((c.root / name).read_text() for name in out.evidence)
    assert len(c.events("BUILD_BOUND")) == 1 and out.facts["child_build_id"] == C
    assert set(traces[0]) == {"request_id", "mode", "W", "rounds", "final_category"}
    assert all("elapsed_ms" in r for r in traces[0]["rounds"][0]["reads"])


@pytest.mark.parametrize("pending", [False, True])
def test_unbound_fetch_continues_pass_or_pending_and_sequences(c, pending):
    if pending:
        c.child = c.child.replace("Successful", "Running")
    replies = [config_reply(c, [P]), c.replies()[1], c.replies()[0], *c.replies()[2:]]
    code, out, err = c.run(["--request-id", R], replies)
    assert code == 0, err
    assert out["status"] == ("RUNNING" if pending else "PASS")
    assert len(c.events("BUILD_BOUND")) == 1
    if not pending:
        assert c.result_file(out)["evidence"][0].endswith("01.overview-1917.html")
    old = {p.name: p.read_bytes() for p in (c.root / "qb_evidence" / R).glob("*.html")}
    c.child = c.child.replace("Running", "Successful")
    code, out, _ = c.run(["--request-id", R])
    assert code == 0
    for name, raw in old.items():
        assert (c.root / "qb_evidence" / R / name).read_bytes() == raw
    if pending:
        assert all(
            int(name.split("/")[-1].split(".")[0]) > 5 for name in c.result_file(out)["evidence"]
        )


@pytest.mark.parametrize("advance", [0, 5])
def test_rounds_deadline_zero_cost_ten_and_slow_fewer(c, advance):
    out, calls, traces = run_find(
        c, [config_reply(c)] * 10, post=True, advance=lambda *_: c.clock.advance(advance)
    )
    assert out.category == "未找到"
    assert len(calls) == (10 if advance == 0 else 9)
    assert all(r["started_seconds"] <= 180 for r in traces[0]["rounds"])
    if advance == 0:
        assert traces[0]["rounds"][-1]["started_seconds"] == 180


@pytest.mark.parametrize(
    "scenario", ["fifty", "incomplete_match", "overview_late", "overview_started"]
)
def test_deadline_includes_candidate_completeness_and_binding_read(c, scenario):
    replies = [config_reply(c, [P])]
    if scenario in {"fifty", "incomplete_match"}:
        replies = [config_reply(c, [str(int(P) + n) for n in range(50)])]
        replies += [
            c.replies()[1] if scenario == "incomplete_match" else reply("<html></html>")
        ] * 50

        def advance(_path, n):
            c.clock.advance(0 if n == 1 else 30)
    else:
        replies += [c.replies()[1], c.replies()[0]]

        def advance(_path, n):
            if n == 2:
                c.clock.advance(181 if scenario == "overview_late" else 179)
            if n == 3:
                c.clock.advance(30)

    out, calls, _ = run_find(c, replies, post=True, advance=advance)
    assert out.category == ("已绑定" if scenario == "overview_started" else "查找超时")
    assert bool(c.events("BUILD_BOUND")) == (scenario == "overview_started")
    assert out.evidence[0].endswith("01.overview-1917.html")
    if scenario == "overview_late":
        assert not any(path.endswith("overview") for path in calls)


@pytest.mark.parametrize("temporary", ["missing", "duplicate", "redirect", "id", "http"])
def test_temporarily_unreadable_retried_without_diagnostic(c, temporary):
    diagnostic = {"html_redacted": "<p>OTHER_PERSON_PAYLOAD</p>", "facts": {}}
    bad = {
        "missing": reply(variable_page(2, {**c.parent_changes, "BUILD_NOTES": None})),
        "duplicate": reply(
            variable_page(2, c.parent_changes).replace(
                "</table>", "<tr><td>BUILD_NOTES</td><td></td><td>x</td></tr></table>"
            )
        ),
        "redirect": QbBrowserError("QB_FETCH_FAILED", agent_code="QB_READ_REDIRECTED"),
        "id": QbBrowserError(
            "QB_FETCH_FAILED", agent_code="QB_READ_ID_MISMATCH", diagnostic=diagnostic
        ),
        "http": reply("OTHER_PERSON_PAYLOAD", 404),
    }[temporary]
    out, calls, traces = run_find(
        c,
        [config_reply(c, [P]), bad, config_reply(c, [P]), c.replies()[1], c.replies()[0]],
        post=True,
    )
    assert out.category == "已绑定" and calls.count(f"/build/{P}/variables") == 2
    assert not (c.root / "qb_diagnostics").exists()
    assert "OTHER_PERSON_PAYLOAD" not in json.dumps(traces)


@pytest.mark.parametrize("value", ["", "third-party-marker"])
def test_different_marker_is_not_reread(c, value):
    other = reply(variable_page(2, {**c.parent_changes, "BUILD_NOTES": ("BUILD NOTES", value)}))
    out, calls, _ = run_find(
        c, [config_reply(c, [P]), other] + [config_reply(c, [P])] * 9, post=True
    )
    assert out.category == "未找到" and calls.count(f"/build/{P}/variables") == 1


def test_multiple_matches_do_not_bind(c):
    out, _, _ = run_find(c, [config_reply(c, [P, "1193468"]), c.replies()[1], c.replies()[1]])
    assert out.category == "多于一个" and out.builds == [P, "1193468"]
    assert not c.events("BUILD_BOUND")


@pytest.mark.parametrize("point", ["overview", "target", "trigger_id"])
def test_matching_marker_still_requires_full_manual_checks(c, point):
    if point == "overview":
        c.overview = c.overview.replace("overview/1917", "overview/1918")
    else:
        c.parent_changes["BUILD_PKG_LIST_MODIFY" if point == "target" else "QB_TRIGGER_ID"] = (
            "Build Package List" if point == "target" else "",
            c.target + "\nother@sha" if point == "target" else "1",
        )
    out, _, _ = run_find(c, [config_reply(c, [P]), c.replies()[1], c.replies()[0]])
    assert out.category == "核对不通过" and not c.events("BUILD_BOUND")


@pytest.mark.parametrize("failure", ["exit", "trusted", "timeout"])
@pytest.mark.parametrize("post", [False, True])
def test_second_candidate_read_failure_archives_configuration(c, failure, post):
    error = QbBrowserError(
        "QB_FETCH_FAILED" if failure != "exit" else "QB_BROWSER_UNAVAILABLE",
        agent_code="QB_TRUSTED_CONTEXT_UNAVAILABLE" if failure == "trusted" else None,
    )
    out, calls, _ = run_find(
        c, [config_reply(c, ["1", "2", "3"]), reply("missing"), error], post=post
    )
    assert out.category == "读取失败" and len(calls) == 3
    assert len(out.evidence) == 1 and not c.events("BUILD_BOUND")


def test_baseline_excludes_old_build_but_read_mode_finds(c):
    out, calls, _ = run_find(c, [config_reply(c, [P])] * 10, post=True, w=int(P))
    assert out.category == "未找到" and calls == ["/overview/1917"] * 10
    out, _, _ = run_find(c, [config_reply(c, [P]), c.replies()[1], c.replies()[0]])
    assert out.category == "已绑定"


@pytest.mark.parametrize("race", ["bound", "retrigger"])
def test_binding_transaction_rechecks_after_lookup(c, monkeypatch, race):
    original = binding.bind

    def changed(db, request, build):
        if race == "bound":
            c.bind()
        else:
            state.create_qb_request(c.db, "u1", request_id="b" * 32, sbs_target=c.target)
        return original(db, request, build)

    monkeypatch.setattr(binding, "bind", changed)
    out, _, _ = run_find(c, [config_reply(c, [P]), c.replies()[1], c.replies()[0]])
    assert out.category == "核对不通过"
    assert len(c.events("BUILD_BOUND")) == (1 if race == "bound" else 0)


def trigger_setup(c):
    c.sql("DELETE FROM campaign_qb_events")
    c.sql("DELETE FROM campaign_qb_requests")
    state.append_status(c.db, "u1", "SANDBOX_PUSHED")
    c.parent_changes["BUILD_NOTES"] = (
        "BUILD NOTES",
        "clang-fix-campaign request=" + "0" * 31 + "1",
    )
    form = Campaign.replies(c, current=FROZEN)
    return form[:2]


def run_trigger(c, responses, units=None):
    c.script.write_text(json.dumps([dict(ok=True), *responses]))
    err = io.StringIO()
    path = None
    if units:
        path = c.root / "units.json"
        path.write_text(
            json.dumps([dict(verification_ids=[f"{key}-v{i}" for i in range(3)]) for key in units])
        )
    result = trigger.qb_trigger(
        trigger.QbTriggerOptions(
            c.db.path,
            c.root,
            c.config,
            verification_ids=None if units else "u1-v0,u1-v1,u1-v2",
            units_file=path,
        ),
        stderr=err,
    )
    assert not err.getvalue()
    return result


def test_trigger_unknown_finds_and_binds_without_extra_parent_reads(c):
    form = trigger_setup(c)
    code, rows = run_trigger(
        c,
        [
            config_reply(c, ["1"]),
            *form,
            dict(ok=True, released=True, landed="unknown", observed="/wicket/page", messages=[]),
            config_reply(c, ["1", P]),
            c.replies()[1],
            c.replies()[0],
        ],
    )
    assert code == 0 and rows[0]["action"] == "submitted_bound", rows
    assert rows[0]["qb_build_id"] == P and "找到并绑定" in rows[0]["message"]
    assert [v["path"] for v in c.commands() if v["command"] == "read"] == [
        "/overview/1917",
        "/overview/1917",
        f"/build/{P}/variables",
        f"/build/{P}/overview",
    ]
    assert [r["event_type"] for r in c.sql("SELECT * FROM campaign_qb_events")] == [
        "SUBMITTED",
        "BUILD_BOUND",
    ]


DRIVER_FAILURES = [
    "EXIT",
    "INVALID_JSON",
    None,
    [],
    dict(ok=1),
    dict(ok=True, cookie="SYNTHETIC"),
    dict(ok=True, released=True, landed="build", build_id="x"),
    dict(ok=True, released=True, landed="unknown", observed="/", messages=[], html_redacted="x"),
    dict(ok=False, error="QB_FORM_CHANGED"),
    dict(ok=False, released=True, error="QB_FORM_CHANGED"),
    dict(ok=False, released=False, error=1),
    dict(ok=False, released=False, error="QB_FORM_CHANGED", failure_category="bad"),
    dict(
        ok=True,
        released=True,
        landed="unknown",
        observed="/",
        messages=[],
        failure_category="UNKNOWN",
    ),
    dict(ok=True, released=True, landed="unknown", observed="/", messages=[], login_facts={}),
    dict(ok=False, released=False, error="QB_FORM_CHANGED", snapshot_state={}),
    dict(ok=False, released=False, error="QB_LOGIN_TIMEOUT", login_facts={}),
]


@pytest.mark.parametrize("response", DRIVER_FAILURES)
def test_real_driver_synthesized_unknown_never_looks_up(c, response):
    form = trigger_setup(c)
    code, rows = run_trigger(c, [config_reply(c), *form, response])
    assert (code, rows[0]["error_code"]) == (5, "QB_SUBMIT_UNCERTAIN")
    assert [v["path"] for v in c.commands() if v["command"] == "read"] == ["/overview/1917"]
    assert len(c.sql("SELECT * FROM campaign_qb_events")) == 1
    assert "DriverUnknown" not in json.dumps(rows)


@pytest.mark.parametrize("failure", ["missing", "pipe", "exited"])
def test_real_driver_transport_failure_cli_never_looks_up(c, monkeypatch, failure):
    from ci_triage.qb_browser import QbBrowser

    original = QbBrowser.command

    def command(browser, name, **fields):
        if name == "submit":
            if failure == "missing":
                browser.close()
            elif failure == "pipe":
                browser.process.stdin.close()
            else:
                browser.process.terminate()
                browser.process.wait()
        return original(browser, name, **fields)

    monkeypatch.setattr(QbBrowser, "command", command)
    form = trigger_setup(c)
    code, rows = run_trigger(c, [config_reply(c), *form])
    assert (code, rows[0]["error_code"]) == (5, "QB_SUBMIT_UNCERTAIN")
    assert c.status() == "QB_REQUESTED" and len(c.events("SUBMITTED")) == 1
    assert [r["path"] for r in c.commands() if r["command"] == "read"] == ["/overview/1917"]
    assert not c.events("BUILD_BOUND")


@pytest.mark.parametrize("check,change", BAD_CONFIG)
def test_baseline_failure_cli_has_no_form_or_writes(c, check, change):
    trigger_setup(c)
    before = c.snapshot()
    code, rows = run_trigger(c, [reply(change(configuration(c.project, [P])))])
    assert code == 4 and rows[0]["error_code"] == "REJECTED_QB_FORM_CHANGED"
    assert check in rows[0]["message"]
    assert c.snapshot() == before
    assert [r["command"] for r in c.commands()] == ["login", "read", "close"]


@pytest.mark.parametrize("failure", ["http", "redirect"])
@pytest.mark.parametrize("mode", ["baseline", "post", "read"])
def test_configuration_read_failure_modes(c, failure, mode):
    response = (
        reply("not found", 404) if failure == "http" else dict(ok=False, error="QB_READ_REDIRECTED")
    )
    if mode == "baseline":
        trigger_setup(c)
        before = c.snapshot()
        code, rows = run_trigger(c, [response])
        assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_CHANGED")
        assert rows[0]["message"].startswith("配置页身份与冻结 profile 不符")
        assert c.snapshot() == before
        if failure == "redirect":
            traces = "".join(p.read_text() for p in (c.root / "qb_traces").glob("*.jsonl"))
            assert '"agent_error_code": "QB_READ_REDIRECTED"' in traces
    elif mode == "read":
        code, out, _ = c.run(["--request-id", R], [response])
        assert (code, out["error_code"]) == (5, "QB_FETCH_FAILED")
    else:
        form = trigger_setup(c)
        code, rows = run_trigger(c, [config_reply(c), *form, unknown(), *([response] * 10)])
        assert (code, rows[0]["error_code"]) == (5, "QB_SUBMIT_UNCERTAIN")
        assert "配置页读取失败" in rows[0]["message"]
    assert not c.events("BUILD_BOUND")


@pytest.mark.parametrize("failure", [403, 404, 500, "redirect", "trusted"])
def test_baseline_identity_failure_does_not_submit(c, failure):
    trigger_setup(c)
    before = c.snapshot()
    response = (
        reply("unavailable", failure)
        if isinstance(failure, int)
        else dict(
            ok=False,
            error="QB_READ_REDIRECTED"
            if failure == "redirect"
            else "QB_TRUSTED_CONTEXT_UNAVAILABLE",
        )
    )
    code, rows = run_trigger(c, [response])
    assert (code, rows[0]["error_code"]) == (4, "REJECTED_QB_FORM_CHANGED")
    assert rows[0]["message"].startswith("配置页身份与冻结 profile 不符")
    assert c.snapshot() == before
    assert [r["command"] for r in c.commands()] == ["login", "read", "close"]


@pytest.mark.parametrize("failure", ["timeout", "unavailable", "exited", "malformed"])
def test_baseline_driver_failure_stops_batch_without_restart(c, monkeypatch, failure):
    from ci_triage import qb_browser as driver

    trigger_setup(c)
    for key in ("u2", "u3", "u4"):
        c.add(key)
    state.create_qb_request(c.db, "u4", request_id="b" * 32, sbs_target=c.target)
    state.append_status(c.db, "u4", "QB_REQUESTED")
    before = c.snapshot()
    if failure == "timeout":

        class TimeoutReplies(Queue):
            def get(self, block=True, timeout=None):
                raw = super().get(block=block, timeout=5)
                if timeout == 60:
                    raise Empty
                return raw

        monkeypatch.setattr(driver, "Queue", TimeoutReplies)
    response = {
        "timeout": config_reply(c),
        "unavailable": dict(ok=False, error="QB_BROWSER_UNAVAILABLE"),
        "exited": "EXIT",
        "malformed": "INVALID_JSON",
    }[failure]
    code, rows = run_trigger(c, [response], units=["u1", "u2", "u3", "u4"])
    assert code == 5 and c.starts == 1
    assert rows[0]["error_code"] == "QB_BROWSER_UNAVAILABLE"
    assert rows[0]["message"] is None
    for row in rows[1:3]:
        assert row["error_code"] == "QB_BROWSER_UNAVAILABLE"
        assert row["message"] == "浏览器在处理 u1 时不可用,本批剩余 unit 未处理;请排查后重跑"
    assert rows[3]["action"] == "already_requested"
    assert c.snapshot() == before
    assert [r["command"] for r in c.commands() if r["command"] != "close"] == ["login", "read"]
    if failure == "timeout":
        traces = [
            json.loads(line)
            for path in (c.root / "qb_traces").glob("*.jsonl")
            for line in path.read_text().splitlines()
        ]
        assert sum(t.get("event") == "agent_terminated" for t in traces) == 1


def unknown():
    return dict(ok=True, released=True, landed="unknown", observed="/wicket/page", messages=[])


def test_appears_second_round(c):
    out, _, traces = run_find(
        c, [config_reply(c), config_reply(c, [P]), c.replies()[1], c.replies()[0]], post=True
    )
    assert out.category == "已绑定" and len(traces[0]["rounds"]) == 2
    assert traces[0]["rounds"][1]["started_seconds"] == 20


def test_bound_to_other_request_excluded(c):
    c.add("u2")
    seq = state.create_qb_request(c.db, "u2", request_id="b" * 32, sbs_target=c.target)
    state.append_qb_event(c.db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id=P)
    out, calls, _ = run_find(c, [config_reply(c, [P])])
    assert out.category == "未找到" and calls == ["/overview/1917"]


@pytest.mark.parametrize("status", ["QB_SUBMIT_FAILED", "QB_TRIGGERED", "superseded"])
def test_unbound_inconsistent_state_does_not_start_agent(c, status):
    if status == "superseded":
        state.create_qb_request(c.db, "u1", request_id="b" * 32, sbs_target=c.target)
    else:
        state.append_status(c.db, "u1", status)
    code, out, _ = c.run(["--request-id", R])
    assert code == 4 and c.starts == 0
    assert out["error_code"] == (
        "REJECTED_QB_SUPERSEDED" if status == "superseded" else pages.BINDING
    )


@pytest.mark.parametrize("post", [False, True])
@pytest.mark.parametrize("column", ["Requested By", "Triggered By"])
def test_configuration_postwrite_identity_failure_deleted(c, monkeypatch, post, column):
    good = configuration(c.project, [P])
    identity = f"<table><tr><th>{column}</th></tr><tr><td>&lt;USER&gt;</td></tr></table>"
    good = good.replace("</html>", identity + "</html>")
    assert identity in good
    from pathlib import Path

    original = Path.write_bytes

    def corrupt(path, raw):
        if path.name.endswith("overview-1917.html"):
            raw = raw.replace(b"&lt;USER&gt;", b"SyntheticIdentity")
        return original(path, raw)

    monkeypatch.setattr(Path, "write_bytes", corrupt)
    if post:
        form = trigger_setup(c)
        code, rows = run_trigger(
            c, [config_reply(c), *form, unknown(), reply(good), c.replies()[1]]
        )
        output = rows[0]
        assert output["action"] == "submit_uncertain"
    else:
        code, output, _ = c.run(["--request-id", R], [reply(good), c.replies()[1]])
    assert (code, output["error_code"]) == (5, "QB_EVIDENCE_REDACTION_FAILED")
    assert not c.events("BUILD_BOUND")
    assert not list((c.root / "qb_evidence").rglob("*.html"))


@pytest.mark.parametrize("owner,count", [("UnrelatedPerson", 0), ("LoginPerson", 1)])
def test_unregistered_owner_counter_limit_and_never_archived(c, owner, count):
    source = (
        "<div>Welcome! <b>LoginPerson</b></div>"
        "<table><tr><th>Owner</th></tr><tr><td>" + owner + "</td></tr></table>"
    )
    redactor = PageRedactor()
    redacted = redactor.redact(source)
    # The counter finds only known login identities, not arbitrary account-bearing columns.
    assert redactor.identity_outside_registered_count == count
    response = reply(redacted)
    response["outside_identity_count"] = count
    out, _, traces = run_find(c, [config_reply(c, [P]), response])
    assert out.category == "未找到"
    assert traces[0]["rounds"][0]["reads"][1]["outside_identity_count"] == count
    assert owner not in "".join((c.root / name).read_text() for name in out.evidence)


@pytest.mark.parametrize("failed_at", ["open_form", "submit", "lookup"])
def test_batch_unavailable_no_restart_remaining_units_and_idempotent(c, failed_at):
    trigger_setup(c)
    for key in ("u2", "u3", "u4"):
        c.add(key)
    state.create_qb_request(c.db, "u4", request_id="b" * 32, sbs_target=c.target)
    state.append_status(c.db, "u4", "QB_REQUESTED")
    form = Campaign.replies(c, current=FROZEN)[:2]
    replies = {
        "open_form": ["EXIT"],
        "submit": [*form, "EXIT"],
        "lookup": [*form, unknown(), "EXIT"],
    }[failed_at]
    code, rows = run_trigger(c, [config_reply(c), *replies], units=["u1", "u2", "u3", "u4"])
    assert code == 5 and c.starts == 1
    for out in rows[1:3]:
        assert out["error_code"] == "QB_BROWSER_UNAVAILABLE"
        assert out["message"] == "浏览器在处理 u1 时不可用,本批剩余 unit 未处理;请排查后重跑"
    assert rows[3]["action"] == "already_requested"
    assert "自动查找构建号" in rows[3]["message"]
    assert (
        len(c.sql("SELECT * FROM campaign_qb_requests WHERE campaign_unit_key IN ('u2','u3')")) == 0
    )
    assert sum(r["command"] == "open_form" for r in c.commands()) == 1


def test_close_termination_trace_write_failure_does_not_override(c, monkeypatch):
    class Browser:
        termination_records = [dict(event="agent_terminated", waited_seconds=35, exit_code=-15)]

        def close(self):
            pass

    def fail(*args):
        raise OSError("synthetic")

    monkeypatch.setattr(trigger, "_trace", fail)
    trigger._close_browser(Browser(), c.root, "u1")


@pytest.mark.parametrize("evicted", [False, True])
def test_requests_file_mixed_input_order_and_slow_eviction(c, monkeypatch, evicted):
    c.bind()
    selections = [dict(request_id=R)]
    for key, rid in (("u2", "b" * 32), ("u3", "c" * 32)):
        c.add(key)
        state.create_qb_request(
            c.db, key, request_id=rid, sbs_target=key + "@" + c.units[key]["sha"]
        )
        state.append_status(c.db, key, "QB_REQUESTED")
        selections.append(dict(request_id=rid))
    first = c.replies()[:4]
    second_id = "1193470"
    c.parent_changes.update(
        QB_TRIGGER_ID=("", second_id),
        BUILD_PKG_LIST_MODIFY=("Build Package List", "u2@" + c.units["u2"]["sha"]),
        BUILD_NOTES=("BUILD NOTES", "clang-fix-campaign request=" + "b" * 32),
    )
    c.child_changes.update(
        TRIGGER_ID=("", second_id),
        BUILD_PKG_LIST=("", "u2@" + c.units["u2"]["sha"]),
    )
    second = c.replies()
    script = [
        *first,
        config_reply(c, [second_id]),
        second[1],
        second[0],
        *second[2:4],
        config_reply(c),
    ]
    from ci_triage.qb_browser import QbBrowser

    original = QbBrowser.command

    def command(browser, name, **fields):
        if name == "read" and fields["path"] == f"/build/{second_id}/variables":
            c.clock.advance(60)
        result = original(browser, name, **fields)
        if name == "read" and fields["path"] == "/overview/1917" and c.clock.now >= 60:
            assert result["html_redacted"] == configuration(c.project)
        return result

    if evicted:
        monkeypatch.setattr(QbBrowser, "command", command)
    path = c.root / "requests.json"
    path.write_text(json.dumps(selections))
    code, _, err = c.run(["--requests-file", str(path)], script)
    assert code == 4 and not err
    rows = c.last[1]
    assert [r["request_id"] for r in rows] == [R, "b" * 32, "c" * 32]
    assert [r["status"] for r in rows] == ["PASS", "PASS", None]
    assert rows[2]["error_code"] == pages.BINDING and "未找到" in rows[2]["message"]
    assert len(c.events("BUILD_BOUND")) == 2 and c.starts == 1
    assert len(c.sql("SELECT * FROM campaign_qb_requests")) == 3
    assert [x["path"] for x in c.commands() if x["command"] == "read"] == [
        f"/build/{P}/overview",
        f"/build/{P}/variables",
        f"/build/{C}/overview",
        f"/build/{C}/variables",
        "/overview/1917",
        f"/build/{second_id}/variables",
        f"/build/{second_id}/overview",
        f"/build/{C}/overview",
        f"/build/{C}/variables",
        "/overview/1917",
    ]
