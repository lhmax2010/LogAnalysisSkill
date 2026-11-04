# GBS Build Failure Analysis
- Verdict: needs_llm
- Failed phase: %install
- Matched tier: None

## Primary Error
{
  "id": "E324",
  "kind": "rpm_phase",
  "severity": "error",
  "message": "error: Bad exit status from /var/tmp/rpm-tmp.XkCg6P (%install)",
  "line_no": 1732,
  "raw_offset": 125558,
  "phase": "%install",
  "command_id": "C058",
  "details": {
    "phase": "%install"
  }
}

## Evidence
{
  "primary_error": {
    "id": "E324",
    "kind": "rpm_phase",
    "severity": "error",
    "message": "error: Bad exit status from /var/tmp/rpm-tmp.XkCg6P (%install)",
    "line_no": 1732,
    "raw_offset": 125558,
    "phase": "%install",
    "command_id": "C058",
    "details": {
      "phase": "%install"
    }
  },
  "phase": "%install"
}

## Error Clusters
{
  "schema_version": "error_clusters/v1",
  "truncated": false,
  "truncation_signals": [],
  "full_locations_path": "error_clusters.json",
  "clusters": [
    {
      "id": "CL001",
      "kind": "source_warning_option",
      "diagnostic_kinds": [
        "compiler"
      ],
      "warning_option": "-Wdeprecated-non-prototype",
      "count": 320,
      "file_count": 48,
      "files": [
        "clnt_perror.c",
        "authunix_prot.c",
        "clnt_raw.c",
        "auth_unix.c",
        "bindresvport.c",
        "auth_none.c",
        "clnt_bcast.c",
        "clnt_vc.c",
        "clnt_dg.c",
        "getnetpath.c",
        "getnetconfig.c",
        "getrpcport.c",
        "pmap_getmaps.c",
        "pmap_getport.c",
        "pmap_prot.c",
        "pmap_prot2.c",
        "pmap_rmt.c",
        "rpc_prot.c",
        "rpc_callmsg.c",
        "rpc_soc.c"
      ],
      "locations_sample": [
        {
          "event_id": "E001",
          "file": "clnt_perror.c",
          "line": 63,
          "column": 1
        },
        {
          "event_id": "E006",
          "file": "authunix_prot.c",
          "line": 48,
          "column": 1
        },
        {
          "event_id": "E009",
          "file": "clnt_raw.c",
          "line": 80,
          "column": 1
        },
        {
          "event_id": "E010",
          "file": "auth_unix.c",
          "line": 85,
          "column": 1
        },
        {
          "event_id": "E019",
          "file": "bindresvport.c",
          "line": 60,
          "column": 1
        },
        {
          "event_id": "E023",
          "file": "auth_none.c",
          "line": 65,
          "column": 15
        },
        {
          "event_id": "E024",
          "file": "clnt_bcast.c",
          "line": 260,
          "column": 1
        },
        {
          "event_id": "E027",
          "file": "clnt_vc.c",
          "line": 178,
          "column": 1
        },
        {
          "event_id": "E037",
          "file": "clnt_dg.c",
          "line": 152,
          "column": 1
        },
        {
          "event_id": "E045",
          "file": "getnetpath.c",
          "line": 132,
          "column": 1
        }
      ],
      "locations_truncated": true,
      "advisory": "Large repeated source diagnostic cluster. Patching only the primary error is likely incomplete; consider a class-wide fix strategy.",
      "large_scale": true
    }
  ]
}

## Prompt
请根据 evidence_packet JSON 定位 GBS 构建失败根因并给出最小修复建议。
Failed phase: %install
Primary error: {"id":"E324","kind":"rpm_phase","severity":"error","message":"error: Bad exit status from /var/tmp/rpm-tmp.XkCg6P (%install)","phase":"%install"}
Top candidate: {"rank":1,"event_id":"E324","kind":"rpm_phase","semantic_class":"generic_error","confidence":0.38}
Evidence paths: []
Use packet.primary_error, packet.root_cause_candidates, and packet.evidence for details.

