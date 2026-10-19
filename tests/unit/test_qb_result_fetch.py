from __future__ import annotations

import copy
import fcntl
import hashlib
import html
import io
import json
import os
from pathlib import Path

import pytest
from ci_triage import campaign_state as state
from ci_triage import cli
from ci_triage import qb_result_fetch as fetch
from ci_triage import qb_result_html as pages
from ci_triage import qb_trigger as trigger
from ci_triage._campaign_workspace import _unit_hash
from ci_triage.qb_browser import QbBrowser
from ci_triage.qb_config import ARCHITECTURES, canonical_profile_json
from ci_triage.qb_redact import PageRedactor
from test_qb_trigger import ARCHIVE, Campaign

P, C = "1193467", "1193469"
R = "a" * 32
FROZEN = "tizen-base-toolchain_20260924.094908"
CONFIG = "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"


def serialize(node):
    if isinstance(node, str):
        return html.escape(node)
    children = "".join(serialize(n) for n in node.children)
    if node.tag == "document":
        return children
    attrs = "".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in node.attrs.items())
    if node.tag == "script":
        children = node.text()
    return f"<{node.tag}{attrs}>{children}</{node.tag}>"


def mutate(text, operation):
    doc = pages.Document(text).root
    operation(doc)
    return serialize(doc)


def summary_change(doc, key, value):
    table = doc.find(cls="build-summary")[0].find("table")[0]
    headers = table.find("th")
    row = table.find("tbody")[0].find("tr")[0]
    names = [h.text().strip() for h in headers]
    if key in names:
        pages.cells(row)[names.index(key)].children = [value]
    else:
        headers[0].parent.children.append(pages.Element("th", children=[key]))
        row.children.append(pages.Element("td", children=[value]))


def variable_page(index, changes):
    rows = pages.variables((ARCHIVE / f"{index:02d}.response.html").read_text())
    rows.update(changes)
    body = "<tr><td>Name</td><td>Display Name</td><td>Value</td></tr>"
    for key, item in rows.items():
        if item is not None:
            body += (
                "<tr>"
                + "".join(
                    "<td>" + html.escape(s).replace("\n", "<br>") + "</td>" for s in (key, *item)
                )
                + "</tr>"
            )
    return "<table>" + body + "</table>"


class FetchCampaign(Campaign):
    def __init__(self, root, monkeypatch):
        super().__init__(root, monkeypatch)
        self.project["configuration_path"] = CONFIG
        self.save()
        self.profile = canonical_profile_json(self.project, frozen_snapshot=FROZEN)
        with trigger._write(self.db) as conn:
            state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=self.profile)
        self.target = "u1@" + self.units["u1"]["sha"]
        self.seq = state.create_qb_request(self.db, "u1", request_id=R, sbs_target=self.target)
        state.append_status(self.db, "u1", "QB_REQUESTED")
        self.overview = (ARCHIVE / "01.response.html").read_text()
        self.child = mutate(
            (ARCHIVE / "03.response.html").read_text(),
            lambda d: summary_change(d, "Status", "Successful"),
        )
        self.steps = (ARCHIVE / "05.response.html").read_text()
        self.parent_changes = dict(
            QB_TRIGGER_ID=("", P),
            BUILD_PKG_LIST_MODIFY=("Build Package List", self.target),
            BUILD_NOTES=("BUILD NOTES", "clang-fix-campaign request=" + R),
            BUILD_REFERENCE=("", "Ref. Snapshot"),
            BUILD_TYPE=("", "Full"),
            PROJECT_BRANCH=("", "tizen_base"),
            FAIL_FAST=("Immediate Stop With Error", "yes"),
            CHILD_CONFIGURATIONS=("", ARCHITECTURES),
            SNAPSHOT_NUM=("", "do not need select"),
        )
        self.child_changes = dict(
            TRIGGER_ID=("", P),
            QB_TRIGGER_ID=("", C),
            FAIL_FAST=("", "yes"),
            BUILD_PKG_LIST=("", "other/repo@abc\n" + self.target + "\nthird/repo@def"),
            REPO_ARCH=("", ARCHITECTURES),
            CHILD_CONFIGURATIONS=("", ARCHITECTURES),
            BUILD_REFERENCE=("", "Ref. Snapshot"),
            SNAPSHOT_NUM_URL=("", pages.SNAPSHOT_ROOT + FROZEN),
            EACH_GBS_BUILD_STATUS=("", ""),
        )
        self.reply_changes = {}
        self.last = None

    def bind(self, build=P):
        state.append_qb_event(
            self.db, request_seq=self.seq, event_type="BUILD_BOUND", qb_build_id=build
        )
        state.append_status(self.db, "u1", "QB_TRIGGERED")

    def replies(self):
        texts = [
            self.overview,
            variable_page(2, self.parent_changes),
            self.child,
            variable_page(4, self.child_changes),
            self.steps,
        ]
        replies = [
            dict(ok=True, status=200, html_redacted=t, outside_identity_count=0) for t in texts
        ]
        for index, replacement in self.reply_changes.items():
            replies[index] = replacement
        return replies

    def run(self, args=None, replies=None, login=None):
        self.script.write_text(json.dumps([login or dict(ok=True), *(replies or self.replies())]))
        stdout, stderr = io.StringIO(), io.StringIO()
        args = ["--request-id", R, "--qb-build-id", P] if args is None else args
        code = cli.main(
            [
                "qb-result-fetch",
                *args,
                "--state-db",
                str(self.db.path),
                "--state-root",
                str(self.root),
                "--config",
                str(self.config),
            ],
            stdout=stdout,
            stderr=stderr,
        )
        self.last = (code, json.loads(stdout.getvalue()), stderr.getvalue())
        return code, self.last[1][0], self.last[2]

    def events(self, kind="RESULT"):
        return self.sql("SELECT * FROM campaign_qb_events WHERE event_type=?", (kind,))

    def result_file(self, output):
        return json.loads((self.root / output["qb_result_path"]).read_bytes())

    def status(self):
        return self.sql("SELECT status FROM campaign_status_log ORDER BY log_id DESC LIMIT 1")[0][
            "status"
        ]


@pytest.fixture
def c(tmp_path, monkeypatch):
    return FetchCampaign(tmp_path, monkeypatch)


def test_pass_schema_and_parent_child_echo(c):
    code, result, err = c.run()
    assert (code, result["error_code"], err) == (0, None, "")
    assert result["status"] == "PASS" and result["terminal"]
    facts = c.result_file(result)
    assert set(facts) == fetch.RESULT_KEYS
    assert set(facts["child_params_echo"]) == {"BUILD_REFERENCE", "SNAPSHOT_NUM_URL"}
    assert facts["params_echo"]["SNAPSHOT_NUM"] == "do not need select"
    assert facts["child_params_echo"]["SNAPSHOT_NUM_URL"] == pages.SNAPSHOT_ROOT + FROZEN
    assert facts["sbs_target_echo"] == c.target
    assert facts["snapshot_used"] == FROZEN and facts["snapshot_drift_accepted"] is False
    assert facts["child_failed_step"] is facts["child_error_message"] is None
    assert len(facts["evidence"]) == 4
    raw = (c.root / result["qb_result_path"]).read_bytes()
    assert c.events()[0]["qb_result_sha256"] == hashlib.sha256(raw).hexdigest()
    assert state.latest_qb_result(c.db, "u1")["event_id"] == result["result_event_id"]
    assert c.status() == "SANDBOX_QB_PASS"
    assert [x["command"] for x in c.commands()] == [
        "login",
        "read",
        "read",
        "read",
        "read",
        "close",
    ]


@pytest.mark.parametrize("text,status", [*pages.STATES.items(), (" Successful ", "PASS")])
def test_status_table(c, text, status):
    c.child = mutate(c.child, lambda d: summary_change(d, "Status", text))
    code, output, err = c.run()
    assert (code, err) == (0, "")
    assert output["status"] == status
    if status in pages.TERMINAL:
        facts = c.result_file(output)
        if status != "PASS":
            assert facts["child_failed_step"] == "master > BUILD > Build > Build_GBS"
            assert facts["child_error_message"]
        assert len(c.events()) == 1
    else:
        assert c.events() == [] and c.status() == "SANDBOX_QB_PENDING"


@pytest.mark.parametrize("text", ["Success ful", "successful", "Success"])
def test_unrecognized_status(c, text):
    c.child = mutate(c.child, lambda d: summary_change(d, "Status", text))
    code, out, _ = c.run()
    assert (code, out["error_code"], c.events()) == (5, pages.UNRECOGNIZED, [])


@pytest.mark.parametrize(
    "side,key",
    [
        *(
            ("parent", k)
            for k in (
                "QB_TRIGGER_ID",
                "BUILD_PKG_LIST_MODIFY",
                "BUILD_NOTES",
                "BUILD_TYPE",
                "BUILD_REFERENCE",
                "PROJECT_BRANCH",
                "FAIL_FAST",
                "CHILD_CONFIGURATIONS",
            )
        ),
        *(
            ("child", k)
            for k in (
                "TRIGGER_ID",
                "QB_TRIGGER_ID",
                "BUILD_PKG_LIST",
                "FAIL_FAST",
                "REPO_ARCH",
                "CHILD_CONFIGURATIONS",
                "BUILD_REFERENCE",
                "EACH_GBS_BUILD_STATUS",
            )
        ),
    ],
)
@pytest.mark.parametrize("missing", [False, True])
def test_required_variables(c, side, key, missing):
    changes = getattr(c, side + "_changes")
    if not missing and side == "child" and key in {"BUILD_REFERENCE", "EACH_GBS_BUILD_STATUS"}:
        changes[key] = ("", "Live" if key == "BUILD_REFERENCE" else "unregistered-status")
        code, out, _ = c.run()
        assert code == (0 if key == "BUILD_REFERENCE" else 5)
        if code == 0:
            assert c.result_file(out)["child_params_echo"][key] == "Live"
        else:
            assert out["error_code"] == pages.UNRECOGNIZED
            assert "R1" in out["message"] and "--retrigger" in out["message"]
        return
    display = changes[key][0]
    changes[key] = None if missing else (display, "wrong")
    code, out, _ = c.run()
    assert (code, out["error_code"], c.events()) == (4, pages.BINDING, [])
    if side == "parent":
        assert c.events("BUILD_BOUND") == []


@pytest.mark.parametrize("key", ["BUILD_PKG_LIST_MODIFY", "BUILD_NOTES", "FAIL_FAST"])
def test_parent_display_name(c, key):
    c.parent_changes[key] = ("wrong display", c.parent_changes[key][1])
    assert c.run()[1]["error_code"] == pages.BINDING
    assert not c.events("BUILD_BOUND")


@pytest.mark.parametrize(
    "side,extra", [("parent", "duplicate"), ("child", "duplicate"), ("child", "other_commit")]
)
def test_target_uniqueness(c, side, extra):
    changes = getattr(c, side + "_changes")
    key = "BUILD_PKG_LIST_MODIFY" if side == "parent" else "BUILD_PKG_LIST"
    changes[key] = (
        changes[key][0],
        c.target + "\n" + (c.target if extra == "duplicate" else "u1@another"),
    )
    assert c.run()[1]["error_code"] == pages.BINDING
    assert not c.events()


@pytest.mark.parametrize("value", ["do not need select", "arbitrary-parent-snapshot"])
def test_parent_snapshot_only_recorded(c, value):
    c.parent_changes["SNAPSHOT_NUM"] = ("", value)
    code, out, _ = c.run()
    assert code == 0 and c.result_file(out)["params_echo"]["SNAPSHOT_NUM"] == value


BAD_SNAPSHOTS = [
    "http://example.org/snapshots/" + FROZEN,
    pages.SNAPSHOT_ROOT.replace("Tizen-Base", "Tizen-Unified") + FROZEN,
    "http://download.tizen.org/RBS/" + FROZEN,
    "file:///tmp/" + FROZEN,
    pages.SNAPSHOT_ROOT.replace("//", "//user@") + FROZEN,
    pages.SNAPSHOT_ROOT + FROZEN + "?x=1",
    pages.SNAPSHOT_ROOT + FROZEN + "#x",
    pages.SNAPSHOT_ROOT + FROZEN + "/",
    pages.SNAPSHOT_ROOT + "extra/" + FROZEN,
    pages.SNAPSHOT_ROOT + "not-a-snapshot",
    None,
]


@pytest.mark.parametrize("url", BAD_SNAPSHOTS)
@pytest.mark.parametrize("accept", [False, True])
def test_snapshot_negative_not_overridden(c, url, accept):
    c.child_changes["SNAPSHOT_NUM_URL"] = None if url is None else ("", url)
    args = ["--request-id", R, "--qb-build-id", P] + (["--accept-snapshot-drift"] if accept else [])
    code, out, _ = c.run(args)
    assert (code, out["error_code"], c.events()) == (5, pages.UNRECOGNIZED, [])
    assert FROZEN in out["message"] and "按 R1 定判据" in out["message"]
    assert "qb_evidence/" in out["message"]


def test_drift_accept_and_repeat(c):
    actual = "tizen-base-toolchain_20261014.094908"
    c.child_changes["SNAPSHOT_NUM_URL"] = ("", pages.SNAPSHOT_ROOT + actual)
    code, out, _ = c.run()
    assert code == 5 and "该 unit 的复验基准已漂移" in out["message"]
    assert FROZEN in out["message"] and actual in out["message"] and not c.events()
    code, out, _ = c.run(["--request-id", R, "--accept-snapshot-drift"])
    assert code == 0
    facts = c.result_file(out)
    assert facts["snapshot_drift_accepted"] is True and facts["snapshot_used"] == actual
    event, path = out["result_event_id"], out["qb_result_path"]
    before = c.snapshot()
    code, out, _ = c.run(["--request-id", R])
    assert code == 0 and (out["result_event_id"], out["qb_result_path"]) == (event, path)
    assert c.snapshot() == before


@pytest.mark.parametrize("args", [["--qb-build-id", P], ["--requests-file", "requests.json"], []])
def test_accept_drift_invalid_modes(c, args):
    before = c.snapshot()
    code, out, _ = c.run([*args, "--accept-snapshot-drift"])
    assert code == 2 and out["error_code"] == "INVALID_ARGS" and c.starts == 0
    assert c.snapshot() == before


@pytest.mark.parametrize("failure", ["404", "QB_READ_ID_MISMATCH", "QB_READ_REDIRECTED", "shape"])
def test_optional_steps_ordinary_failure(c, failure):
    c.child = (ARCHIVE / "03.response.html").read_text()
    c.reply_changes[4] = (
        dict(ok=False, error=failure)
        if failure.startswith("QB_")
        else dict(
            ok=True,
            status=404 if failure == "404" else 200,
            html_redacted="<html>unavailable</html>",
            outside_identity_count=0,
        )
    )
    code, out, err = c.run()
    assert (code, err, out["status"]) == (0, "", "FAIL")
    facts = c.result_file(out)
    assert facts["child_failed_step"] is facts["child_error_message"] is None


@pytest.mark.parametrize("index", [0, 1, 2, 3, 4])
@pytest.mark.parametrize(
    "failure",
    [
        "QB_READ_ID_MISMATCH",
        "QB_READ_REDIRECTED",
        "QB_TRUSTED_CONTEXT_UNAVAILABLE",
        "QB_EVIDENCE_REDACTION_FAILED",
        "EXIT",
    ],
)
def test_read_failure_categories(c, index, failure):
    c.child = (ARCHIVE / "03.response.html").read_text()
    c.reply_changes[index] = "EXIT" if failure == "EXIT" else dict(ok=False, error=failure)
    code, out, _ = c.run()
    if index == 4 and failure in {"QB_READ_ID_MISMATCH", "QB_READ_REDIRECTED"}:
        assert code == 0 and out["status"] == "FAIL"
    else:
        expected = failure if failure == "QB_EVIDENCE_REDACTION_FAILED" else "QB_FETCH_FAILED"
        assert (code, out["error_code"], c.events()) == (5, expected, [])


def child_table(doc):
    heading = next(n for n in doc.find("h3") if "Child Build" in n.text())
    siblings = [n for n in heading.parent.children if isinstance(n, pages.Element)]
    return siblings[siblings.index(heading) + 1]


def alter_config(doc, case):
    tab = doc.find("li", cls="tab-ConfigurationOverview")[0]
    link = tab.find("a")[0]
    crumb = next(n for n in doc.find() if n.attrs.get("id") == "breadcrumb")
    if case == "id":
        link.attrs["href"] = "../../overview/2"
    elif case == "duplicate":
        tab.children.append(copy.deepcopy(link))
    elif case == "external":
        link.attrs["href"] = "https://other.example/overview/1917"
    elif case in {"query", "fragment"}:
        link.attrs["href"] += "?x=1" if case == "query" else "#x"
    elif case == "pipeline":
        doc.find("li", cls="tab-PipelinePage")[0].find("a")[0].attrs["href"] = "../../pipeline/2"
    elif case == "children":
        doc.find("li", cls="tab-ChildrenPage")[0].find("a")[0].attrs["href"] = "../../children/2"
    elif case == "breadcrumb":
        crumb.find("span")[-1].children = ["wrong"]
    elif case == "current_link":
        crumb.find("span")[-1].children = [pages.Element("a", children=["TRIGGER"])]
    elif case == "copy":
        script = next(s for s in doc.find("script") if "onCopyClipboardLinkDomReady" in s.text())
        script.children = [script.text().replace("/RBS/TRIGGER", "/RBS/wrong")]
    elif case == "name":
        for span in doc.find(cls="build-header")[0].find("span"):
            if not span.find() and span.text().strip().startswith("TIZEN_"):
                span.children = ["TIZEN_wrong"]


@pytest.mark.parametrize(
    "case",
    [
        "id",
        "duplicate",
        "external",
        "query",
        "fragment",
        "pipeline",
        "children",
        "breadcrumb",
        "current_link",
        "copy",
        "name",
    ],
)
def test_parent_configuration_checks(c, case):
    c.overview = mutate(c.overview, lambda d: alter_config(d, case))
    code, out, _ = c.run()
    assert (code, out["error_code"]) == (4, pages.BINDING)
    assert c.events() == c.events("BUILD_BOUND") == []
    assert [x.get("path") for x in c.commands() if x["command"] == "read"] == [
        f"/build/{P}/overview",
        f"/build/{P}/variables",
    ]


def test_request_url_not_page_base(c):
    c.overview = '<base href="https://outside.example/build/">' + c.overview
    assert c.run()[0] == 0


@pytest.mark.parametrize("case", ["two_rows", "header", "arch", "href", "two_links"])
def test_child_table_checks(c, case):
    def change(doc):
        table = child_table(doc)
        body = table.find("tbody")[0]
        row = body.find("tr")[0]
        if case == "two_rows":
            body.children.append(copy.deepcopy(row))
        elif case == "header":
            pages.cells(table.find("thead")[0].find("tr")[0])[0].children = ["wrong"]
        elif case == "arch":
            pages.cells(row)[0].children = ["armv7l"]
        elif case == "href":
            pages.cells(row)[1].find("a")[0].attrs["href"] = "/build/" + C
        else:
            cell = pages.cells(row)[1]
            cell.children.append(copy.deepcopy(cell.find("a")[0]))

    c.overview = mutate(c.overview, change)
    expected = pages.UNRECOGNIZED if case in {"two_rows", "header"} else pages.BINDING
    assert c.run()[1]["error_code"] == expected and not c.events("BUILD_BOUND")


@pytest.mark.parametrize("bad_parent", [False, True])
@pytest.mark.parametrize("absent", [False, True])
def test_child_pending_checks_parent_then_binds_once(c, bad_parent, absent):
    def change(doc):
        table = child_table(doc)
        table.find("tbody")[0].children = []
        if absent:
            heading = next(n for n in doc.find("h3") if "Child Build" in n.text())
            heading.children = ["not Child Build"]

    c.overview = mutate(c.overview, change)
    if bad_parent:
        c.parent_changes["BUILD_NOTES"] = None
    code, out, _ = c.run()
    if bad_parent:
        assert code == 4 and out["error_code"] == pages.BINDING
        assert not c.events("BUILD_BOUND") and c.status() == "QB_REQUESTED"
    else:
        assert code == 0 and out["status"] == "QUEUED" and out["child_build_id"] is None
        assert c.status() == "SANDBOX_QB_PENDING" and len(c.events("BUILD_BOUND")) == 1
        before = c.snapshot()
        assert c.run()[0] == 0 and c.snapshot() == before
    assert not c.events()


def test_not_finished_parent_fallback(c):
    c.child = mutate(c.child, lambda d: summary_change(d, "Status", "Not started"))

    def change(doc):
        pages.cells(child_table(doc).find("tbody")[0].find("tr")[0])[2].children = [
            "Not Finished (waiting)"
        ]

    c.overview = mutate(c.overview, change)
    code, out, _ = c.run()
    assert code == 0 and out["status"] == "RUNNING" and not c.events()


@pytest.mark.parametrize("case", ["breadcrumb", "copy"])
def test_child_configuration(c, case):
    def change(doc):
        if case == "breadcrumb":
            crumb = next(n for n in doc.find() if n.attrs.get("id") == "breadcrumb")
            crumb.find("span")[-1].children = ["TRIGGER"]
        else:
            script = next(
                s for s in doc.find("script") if "onCopyClipboardLinkDomReady" in s.text()
            )
            script.children = [script.text().replace("/RBS/build", "/RBS/wrong")]

    c.child = mutate(c.child, change)
    assert c.run()[1]["error_code"] == pages.BINDING and not c.events()


@pytest.mark.parametrize(
    "accepted,expected",
    [
        ("ACCEPTED", True),
        ("ACCEPTED (2026-10-10 12:00)", True),
        ("ACCEPTED_BY_X", False),
        ("NOT_ACCEPTED", False),
        (None, None),
    ],
)
def test_accepted_is_record_only(c, accepted, expected):
    if accepted is not None:
        c.overview = mutate(c.overview, lambda d: summary_change(d, "SR_STATUS", accepted))
    code, out, _ = c.run()
    assert code == 0 and out["status"] == "PASS"
    assert c.result_file(out)["accepted"] is expected


def test_terminal_idempotent_changed_fields_and_status(c):
    code, out, _ = c.run()
    assert code == 0
    old = (c.root / out["qb_result_path"]).read_bytes()
    event = out["result_event_id"]
    before = c.snapshot()
    assert c.run()[1]["result_event_id"] == event and c.snapshot() == before
    c.overview = mutate(c.overview, lambda d: summary_change(d, "SR_STATUS", "ACCEPTED"))
    code, new, _ = c.run()
    assert code == 0 and new["result_event_id"] != event
    assert (c.root / out["qb_result_path"]).read_bytes() == old
    assert len(c.events()) == 2
    assert c.snapshot()["campaign_status_log"] == before["campaign_status_log"]
    before = c.snapshot()
    c.child = (ARCHIVE / "03.response.html").read_text()
    code, out, _ = c.run()
    assert code == 4 and out["error_code"] == "REJECTED_STATE_INCONSISTENT"
    assert c.snapshot() == before and len(list((c.root / "qb_results" / R).glob("*"))) == 2


@pytest.mark.parametrize(
    "mode",
    ["unbound", "no_request_build", "not_released", "different_bound", "superseded", "other_bound"],
)
def test_entry_refusals_no_browser(c, mode):
    args = ["--request-id", R, "--qb-build-id", P]
    if mode == "unbound":
        args = ["--request-id", R]
    elif mode == "no_request_build":
        args = ["--qb-build-id", P]
    elif mode == "not_released":
        state.append_status(c.db, "u1", "QB_SUBMIT_FAILED")
    elif mode == "different_bound":
        c.bind("999")
    elif mode == "superseded":
        state.create_qb_request(c.db, "u1", request_id="b" * 32, sbs_target=c.target)
    else:
        c.add("u2")
        seq = state.create_qb_request(c.db, "u2", request_id="b" * 32, sbs_target="u2@sha")
        state.append_qb_event(c.db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id=P)
    before = c.snapshot()
    code, out, _ = c.run(args)
    assert code == 4 and c.starts == 0 and c.snapshot() == before
    assert out["error_code"] == (
        "REJECTED_QB_SUPERSEDED" if mode == "superseded" else pages.BINDING
    )


def test_reverse_build_lookup(c):
    c.bind()
    code, out, _ = c.run(["--qb-build-id", P])
    assert code == 0 and out["request_id"] == R


def test_reverse_build_ambiguous(c):
    c.bind()
    c.add("u2")
    seq = state.create_qb_request(c.db, "u2", request_id="b" * 32, sbs_target="u2@sha")
    state.append_qb_event(c.db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id=P)
    assert c.run(["--qb-build-id", P])[1]["error_code"] == "AmbiguousQbReference"
    assert c.starts == 0


def test_batch_single_login_independent(c):
    path = c.root / "requests.json"
    path.write_text(json.dumps([dict(request_id="b" * 32), dict(request_id=R, qb_build_id=P)]))
    code, _, _ = c.run(["--requests-file", str(path)])
    assert code == 4 and c.last[1][0]["error_code"] == pages.BINDING
    assert c.last[1][1]["status"] == "PASS" and c.starts == 1


def test_lock_held_network_outside_transaction(c, monkeypatch):
    original = QbBrowser.command
    seen = []

    def command(browser, name, **fields):
        if name != "close":
            lock = c.root / "ws" / _unit_hash("u1") / ".sandbox_submit.lock"
            with lock.open("a") as stream:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            conn = state._read_connection(c.db)
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.rollback()
            finally:
                conn.close()
            seen.append(name)
        return original(browser, name, **fields)

    monkeypatch.setattr(QbBrowser, "command", command)
    assert c.run()[0] == 0 and seen == ["login", "read", "read", "read", "read"]


@pytest.mark.parametrize("point", ["binding", "pending", "result_event", "result_status"])
def test_write_point_rollback(c, monkeypatch, point):
    if point != "binding":
        c.bind()
    if point == "pending":
        c.child = mutate(c.child, lambda d: summary_change(d, "Status", "Running"))
    before = c.snapshot()
    if point == "result_event":
        original = state._append_qb_event_on_connection

        def append(conn, **fields):
            original(conn, **fields)
            raise RuntimeError("injected after event")

        monkeypatch.setattr(state, "_append_qb_event_on_connection", append)
    else:
        original = state._append_status_on_connection

        def status(conn, *args, **kwargs):
            original(conn, *args, **kwargs)
            raise RuntimeError("injected after status")

        monkeypatch.setattr(state, "_append_status_on_connection", status)
    code, out, _ = c.run()
    assert code == 5 and out["error_code"] == "INTERNAL_ERROR"
    assert c.snapshot() == before
    assert list((c.root / "qb_results").rglob("*.json")) == []


@pytest.mark.parametrize("race", ["superseded", "binding", "target"])
def test_transaction_rechecks_and_removes_file(c, monkeypatch, race):
    c.bind()
    original = fetch._publish

    def publish(*args):
        output = original(*args)
        if race == "superseded":
            state.create_qb_request(c.db, "u1", request_id="b" * 32, sbs_target=c.target)
        elif race == "binding":
            # Simulate out-of-band corruption; the public API correctly forbids rebinding.
            c.sql("UPDATE campaign_qb_events SET qb_build_id='999' WHERE event_type='BUILD_BOUND'")
        else:
            c.sql(
                "UPDATE campaign_qb_requests SET sbs_target='changed' WHERE request_seq=?", (c.seq,)
            )
        return output

    monkeypatch.setattr(fetch, "_publish", publish)
    code, out, _ = c.run()
    assert code == 4
    assert out["error_code"] == (
        "REJECTED_QB_SUPERSEDED" if race == "superseded" else "REJECTED_STATE_INCONSISTENT"
    )
    assert not c.events() and list((c.root / "qb_results").rglob("*.json")) == []


@pytest.mark.parametrize("identity", ["Successful", "Full", "root"])
def test_redacted_identity_keeps_business_fields(c, identity):
    decorated = c.overview + (
        f"<span>Welcome! <a>{identity}</a></span><table><tr><th>Requested By</th><th>Owner</th>"
        f"</tr><tr><td>{identity}</td><td>{identity}</td></tr></table>"
        '<input type="hidden" name="token" value="SYNTHETIC_SECRET_VALUE">'
        '<a href="/x;jsessionid=SYNTHETIC_SESSION">x</a>JSESSIONID_8810=SYNTHETIC_COOKIE;'
    )
    redactor = PageRedactor()
    redacted = redactor.redact(decorated)
    redactor.check_bytes(redacted.encode())
    assert f"<td>{identity}</td>" in redacted and "&lt;USER&gt;" in redacted
    c.reply_changes[0] = dict(
        ok=True,
        status=200,
        html_redacted=redacted,
        outside_identity_count=redactor.identity_outside_registered_count,
    )
    code, out, err = c.run()
    assert code == 0 and err == "" and out["status"] == "PASS"
    artifacts = [
        *c.root.glob("qb_evidence/**/*.html"),
        *c.root.glob("qb_results/**/*.json"),
        *c.root.glob("qb_traces/*.jsonl"),
    ]
    for artifact in artifacts:
        raw = artifact.read_bytes()
        redactor.check_bytes(raw)
        assert b"SYNTHETIC_" not in raw and b"JSESSIONID_8810=" not in raw
    traces = [
        json.loads(line)
        for p in c.root.glob("qb_traces/*.jsonl")
        for line in p.read_text().splitlines()
    ]
    assert traces[0]["outside_identity_count"] >= 1


def test_write_after_check_failure_removes_evidence(c, monkeypatch):
    original = Path.read_bytes

    def read(path):
        raw = original(path)
        if "qb_evidence" in path.parts:
            return raw + b"JSESSIONID_8810=INJECTED"
        return raw

    monkeypatch.setattr(Path, "read_bytes", read)
    code, out, _ = c.run()
    assert code == 5 and out["error_code"] == "QB_EVIDENCE_REDACTION_FAILED"
    assert not c.events() and not list((c.root / "qb_evidence").rglob("*.html"))


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_required_http_failure(c, index):
    c.reply_changes[index] = dict(
        ok=True, status=404, html_redacted="missing", outside_identity_count=0
    )
    assert c.run()[1]["error_code"] == "QB_FETCH_FAILED" and not c.events()


def test_result_publication_fsync_order(c, monkeypatch):
    operations = []
    fsync, replace, append = os.fsync, os.replace, state._append_qb_event_on_connection

    def sync(fd):
        operations.append(
            "fsync-directory" if os.path.isdir(f"/proc/self/fd/{fd}") else "fsync-file"
        )
        fsync(fd)

    def rename(src, dest):
        operations.append("rename")
        assert Path(src).read_bytes()
        replace(src, dest)

    def event(conn, **fields):
        if fields["event_type"] == "RESULT":
            operations.append("RESULT")
        return append(conn, **fields)

    monkeypatch.setattr(os, "fsync", sync)
    monkeypatch.setattr(os, "replace", rename)
    monkeypatch.setattr(state, "_append_qb_event_on_connection", event)
    assert c.run()[0] == 0
    assert operations == ["fsync-file", "rename", "fsync-directory", "RESULT"]


@pytest.mark.parametrize("point", ["file", "rename", "directory"])
def test_publication_failure_removes_temp_and_final(c, monkeypatch, point):
    c.bind()
    original = os.fsync

    def sync(fd):
        directory = os.path.isdir(f"/proc/self/fd/{fd}")
        if directory == (point == "directory"):
            raise OSError("injected publication failure")
        original(fd)

    def rename(*args):
        raise OSError("injected rename failure")

    monkeypatch.setattr(os, "replace", rename) if point == "rename" else monkeypatch.setattr(
        os, "fsync", sync
    )
    assert c.run()[1]["error_code"] == "INTERNAL_ERROR"
    assert not c.events() and list((c.root / "qb_results" / R).iterdir()) == []


@pytest.mark.parametrize("race", ["superseded", "not_released", "other_bound"])
def test_manual_binding_transaction_recheck(c, monkeypatch, race):
    original = fetch._manual_bind

    def bind(db, view):
        if race == "superseded":
            state.create_qb_request(c.db, "u1", request_id="b" * 32, sbs_target=c.target)
        elif race == "not_released":
            state.append_status(c.db, "u1", "QB_SUBMIT_FAILED")
        else:
            c.add("u2")
            seq = state.create_qb_request(c.db, "u2", request_id="b" * 32, sbs_target="u2@sha")
            state.append_qb_event(c.db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id=P)
        original(db, view)

    monkeypatch.setattr(fetch, "_manual_bind", bind)
    code, out, _ = c.run()
    assert code == 4 and out["error_code"] == (
        "REJECTED_QB_SUPERSEDED" if race == "superseded" else pages.BINDING
    )
    assert not c.events() and not [e for e in c.events("BUILD_BOUND") if e["request_seq"] == c.seq]


def test_each_status_blocks_retrigger(c):
    c.child_changes["EACH_GBS_BUILD_STATUS"] = ("", "armv7l=Failed")
    code, out, _ = c.run()
    assert code == 5 and "R1" in out["message"] and not c.events()
    before_starts = c.starts
    stdout = io.StringIO()
    code = cli.main(
        [
            "qb-trigger",
            "--verification-ids",
            "u1-v0,u1-v1,u1-v2",
            "--retrigger",
            "--state-db",
            str(c.db.path),
            "--state-root",
            str(c.root),
            "--config",
            str(c.config),
        ],
        stdout=stdout,
        stderr=io.StringIO(),
    )
    assert (
        code == 4
        and json.loads(stdout.getvalue())[0]["error_code"] == "REJECTED_QB_REQUEST_PENDING"
    )
    assert c.starts == before_starts


@pytest.mark.parametrize("index", [0, 4])
def test_read_diagnostic_is_archived(c, index):
    c.child = (ARCHIVE / "03.response.html").read_text()
    c.reply_changes[index] = dict(
        ok=False,
        error="QB_READ_ID_MISMATCH",
        diagnostic={
            "html_redacted": "<html>diagnostic</html>",
            "first_failed_check": "id",
            "outside_identity_count": 0,
        },
    )
    code, out, _ = c.run()
    assert code == (0 if index == 4 else 5)
    directory = Path(out["diagnostic_dir"])
    assert (directory / "page.html").read_text() == "<html>diagnostic</html>"
    assert json.loads((directory / "structure.json").read_text())["first_failed_check"] == "id"


@pytest.mark.parametrize("key", ["cookie", "set-cookie", "authorization"])
def test_agent_sensitive_keys_never_archived(c, key):
    c.reply_changes[0] = dict(ok=True, data={key: "SYNTHETIC_MUST_NOT_LEAK"})
    code, out, err = c.run()
    assert code == 5 and out["error_code"] == "QB_FETCH_FAILED"
    assert "SYNTHETIC_MUST_NOT_LEAK" not in err + json.dumps(out)
    assert not c.events() and not list(c.root.glob("qb_evidence/**/*"))


def test_registered_user_residue_rejected(c):
    c.reply_changes[0] = dict(
        ok=True,
        status=200,
        outside_identity_count=0,
        html_redacted="<table><tr><th>Requested By</th></tr><tr><td>PrivateUser</td></tr></table>",
    )
    code, out, _ = c.run()
    assert code == 5 and out["error_code"] == "QB_EVIDENCE_REDACTION_FAILED" and not c.events()


@pytest.mark.parametrize("shape", ["extra", "missing", "child_extra", "child_missing"])
def test_result_schema_closed(c, monkeypatch, shape):
    original = fetch._collect

    def collect(*args):
        facts = original(*args)
        if shape == "extra":
            facts["extra"] = "bad"
        elif shape == "missing":
            del facts["child_params_echo"]
        elif shape == "child_extra":
            facts["child_params_echo"]["extra"] = "bad"
        else:
            del facts["child_params_echo"]["BUILD_REFERENCE"]
        return facts

    monkeypatch.setattr(fetch, "_collect", collect)
    assert c.run()[1]["error_code"] == "REJECTED_STATE_INCONSISTENT" and not c.events()


@pytest.mark.parametrize("optional", [False, True])
@pytest.mark.parametrize("failure", ["io", "redaction"])
def test_diagnostic_io_preserves_original_but_redaction_stops(c, monkeypatch, optional, failure):
    c.child = (ARCHIVE / "03.response.html").read_text()
    c.reply_changes[4 if optional else 0] = dict(
        ok=False,
        error="QB_READ_ID_MISMATCH",
        diagnostic=dict(html_redacted="<html>safe</html>", first_failed_check="id"),
    )
    original_write, original_read = Path.write_bytes, Path.read_bytes

    def write(path, data):
        if "qb_diagnostics" in path.parts:
            raise OSError("injected storage failure")
        return original_write(path, data)

    def read(path):
        raw = original_read(path)
        if "qb_diagnostics" in path.parts:
            return raw + b"JSESSIONID_8810=INJECTED"
        return raw

    monkeypatch.setattr(Path, "write_bytes", write) if failure == "io" else monkeypatch.setattr(
        Path, "read_bytes", read
    )
    code, out, _ = c.run()
    if failure == "redaction":
        assert code == 5 and out["error_code"] == "QB_EVIDENCE_REDACTION_FAILED" and not c.events()
    elif optional:
        assert code == 0 and out["status"] == "FAIL"
    else:
        assert code == 5 and out["error_code"] == "QB_FETCH_FAILED" and not c.events()
    assert not list((c.root / "qb_diagnostics").glob("*"))
