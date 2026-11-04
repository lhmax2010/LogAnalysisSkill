# GBS Build Failure Analysis
- Verdict: needs_llm
- Failed phase: %build
- Matched tier: None

## Primary Error
{
  "id": "E001",
  "kind": "compiler",
  "severity": "error",
  "message": "use of undeclared identifier 'clang_missing'",
  "line_no": 3,
  "raw_offset": 37,
  "phase": "%build",
  "command_id": "C001",
  "details": {
    "is_assembler": false,
    "tool": "clang"
  },
  "file": "src/clang_case.c",
  "line": 4,
  "column": 10
}

## Evidence
{
  "primary_error": {
    "id": "E001",
    "kind": "compiler",
    "severity": "error",
    "message": "use of undeclared identifier 'clang_missing'",
    "line_no": 3,
    "raw_offset": 37,
    "phase": "%build",
    "command_id": "C001",
    "details": {
      "is_assembler": false,
      "tool": "clang"
    },
    "file": "src/clang_case.c",
    "line": 4,
    "column": 10
  },
  "command_summary": {
    "id": "C001",
    "phase": "%build",
    "argv_short": "clang -c src/clang_case.c",
    "argv_full": "clang -c src/clang_case.c",
    "rsp_expanded": {},
    "command_degraded": false
  }
}

## Source Candidates
{
  "schema_version": "source_candidates/v1",
  "full_candidates_path": "source_candidates.json",
  "candidate_count": 1,
  "structured_source_candidate_count": 1,
  "type_probably_fixable_count": 0,
  "type_unknown_count": 1,
  "type_not_fixable_count": 0,
  "source_reachable_count": 1,
  "source_owned_count": 1,
  "patch_ready_count": 0,
  "excluded_summary": {
    "missing_file_count": 0,
    "missing_line_count": 0,
    "explicit_parent_count": 0
  }
}

## Prompt
请根据 evidence_packet JSON 定位 GBS 构建失败根因并给出最小修复建议。
Failed phase: %build
Primary error: {"id":"E001","kind":"compiler","severity":"error","message":"use of undeclared identifier 'clang_missing'","phase":"%build","file":"src/clang_case.c","line":4}
Top candidate: {"rank":1,"event_id":"E001","kind":"compiler","semantic_class":"undeclared_identifier","confidence":0.76}
Evidence paths: ["src/clang_case.c"]
Use packet.primary_error, packet.root_cause_candidates, and packet.evidence for details.

