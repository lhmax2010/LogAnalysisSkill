# GBS Build Failure Analysis
- Verdict: needs_llm
- Failed phase: %install
- Matched tier: None

## Primary Error
{
  "id": "E001",
  "kind": "rpm_phase",
  "severity": "error",
  "message": "error: Bad exit status from /var/tmp/rpm-tmp.ymL9YA (%install)",
  "line_no": 584,
  "raw_offset": 71912,
  "phase": "%install",
  "command_id": "C068",
  "details": {
    "phase": "%install"
  }
}

## Evidence
{
  "primary_error": {
    "id": "E001",
    "kind": "rpm_phase",
    "severity": "error",
    "message": "error: Bad exit status from /var/tmp/rpm-tmp.ymL9YA (%install)",
    "line_no": 584,
    "raw_offset": 71912,
    "phase": "%install",
    "command_id": "C068",
    "details": {
      "phase": "%install"
    }
  },
  "phase": "%install"
}

## Prompt
请根据 evidence_packet JSON 定位 GBS 构建失败根因并给出最小修复建议。
Failed phase: %install
Primary error: {"id":"E001","kind":"rpm_phase","severity":"error","message":"error: Bad exit status from /var/tmp/rpm-tmp.ymL9YA (%install)","phase":"%install"}
Top candidate: {"rank":1,"event_id":"E001","kind":"rpm_phase","semantic_class":"generic_error","confidence":0.38}
Evidence paths: []
Use packet.primary_error, packet.root_cause_candidates, and packet.evidence for details.

