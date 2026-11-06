from __future__ import annotations

import io
import json

import pytest
from tizen_qb_verify import qb_collect
from tizen_qb_verify.qb_browser import (
    DISCOVERY_CHECKS,
    DISCOVERY_PAGE_KINDS,
    QbBrowserError,
    decode_response,
)


def response(**changes):
    return dict(
        dict(
            ok=False,
            error="DISCOVERY_REPORT_AMBIGUOUS",
            reason="REPORT_STRUCTURE",
            page_kind="report",
            first_failed_check="package_name",
            counts={"row_index": 238},
        ),
        **changes,
    )


def decode(value, command="discovery_read"):
    return decode_response(json.dumps(value), submit_sent=False, command=command)


@pytest.mark.parametrize("page_kind", sorted(DISCOVERY_PAGE_KINDS))
def test_discovery_page_kind_round_trip(page_kind):
    with pytest.raises(QbBrowserError) as caught:
        decode(response(page_kind=page_kind))
    assert caught.value.code == "DISCOVERY_REPORT_AMBIGUOUS"
    assert caught.value.failure_facts()["page_kind"] == page_kind


@pytest.mark.parametrize("check", sorted(DISCOVERY_CHECKS))
def test_discovery_check_reaches_cli_and_trace(monkeypatch, check):
    def fail(_args):
        decode(response(first_failed_check=check))

    monkeypatch.setattr(qb_collect, "collect", fail)
    out = io.StringIO()
    code = qb_collect.main(
        [
            "--config",
            "unused",
            "--state-root",
            "unused",
            "--qb-project",
            "tizen_base",
            "--build-id",
            "1204735",
        ],
        stdout=out,
    )
    assert code == 4
    value = json.loads(out.getvalue())
    assert value["error_code"] == "DISCOVERY_REPORT_AMBIGUOUS"
    assert value["failure"]["first_failed_check"] == check
    assert value["failure"]["counts"] == {"row_index": 238}
    assert value["failure"]["page_kind"] == "report"


@pytest.mark.parametrize(
    "change",
    [
        {"page_kind": "private-title"},
        {"page_kind": []},
        {"first_failed_check": "private-error"},
        {"first_failed_check": None},
        {"counts": {"url": "https://secret.invalid/?token=private"}},
        {"counts": {"actual_count": True}},
        {"counts": {"actual_count": -1}},
        {"counts": {"actual_count": 1.5}},
        {"counts": {"actual_count": 2**53}},
        {"counts": None},
        {"ok": True},
        {"error": "QB_BROWSER_UNAVAILABLE"},
    ],
)
def test_malformed_discovery_diagnostics_are_protocol_error(change):
    with pytest.raises(QbBrowserError) as caught:
        decode(response(**change))
    assert caught.value.code == "QB_BROWSER_UNAVAILABLE"
    assert caught.value.discovery_facts is None
    assert "private" not in json.dumps(caught.value.failure_facts())


@pytest.mark.parametrize("missing", ["page_kind", "first_failed_check", "counts"])
def test_incomplete_diagnostics_are_protocol_error(missing):
    value = response()
    del value[missing]
    with pytest.raises(QbBrowserError, match="QB_BROWSER_UNAVAILABLE"):
        decode(value)


@pytest.mark.parametrize("command", ["read", "fill", "login", "submit"])
def test_discovery_diagnostics_cannot_change_other_command_contracts(command):
    with pytest.raises(QbBrowserError, match="QB_BROWSER_UNAVAILABLE"):
        decode(response(), command)


def test_discovery_build_identity_keeps_existing_error_mapping():
    with pytest.raises(QbBrowserError) as caught:
        decode(response(error="QB_READ_ID_MISMATCH", first_failed_check="identity_mismatch"))
    assert caught.value.code == "QB_FETCH_FAILED"
    assert caught.value.agent_code == "QB_READ_ID_MISMATCH"
    assert caught.value.failure_facts()["first_failed_check"] == "identity_mismatch"
