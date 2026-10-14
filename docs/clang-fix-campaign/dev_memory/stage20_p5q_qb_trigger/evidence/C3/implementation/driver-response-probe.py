"""Repeat the former C3-01 driver probe against the C3-02 response contract."""
import json

from ci_triage.qb_browser import QbBrowserError, decode_response

cases = []
for current in ("current-snapshot-A", "current-snapshot-B"):
    response = dict(ok=False, error="QB_FORM_VALUE_UNAVAILABLE", field="SNAPSHOT_NUM",
                    released=False, snapshot_state=dict(selected=[current], option_count=1))
    try:
        decode_response(json.dumps(response), submit_sent=False, command="fill")
    except QbBrowserError as error:
        assert error.code == "REJECTED_QB_SNAPSHOT_UNAVAILABLE"
        assert error.snapshot_state == response["snapshot_state"]
        cases.append(dict(response=response, error_code=error.code,
                          snapshot_state=error.snapshot_state))
    else:
        raise AssertionError("expected unavailable snapshot")
assert cases[0]["snapshot_state"] != cases[1]["snapshot_state"]
print(json.dumps(dict(network_requests=0, cases=cases), ensure_ascii=False, indent=2))
