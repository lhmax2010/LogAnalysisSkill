# GBS Build Failure Analysis
- Verdict: needs_llm
- Failed phase: %build
- Matched tier: None

## Primary Error
{
  "id": "E001",
  "kind": "raw_error",
  "severity": "error",
  "message": "autoreconf: error: autopoint failed with exit status: 1",
  "line_no": 391,
  "raw_offset": 24975,
  "phase": "%build",
  "command_id": "C046",
  "details": {}
}

## Evidence
{
  "fallback_context": {
    "primary_error_excerpt": "[  529s] + ref=/usr/lib/rpm\n[  529s] + mints=0\n[  529s] + case $(uname -m) in\n[  529s] ++ uname -m\n[  529s] + for s in guess sub\n[  529s] ++ find -maxdepth 8 -name config.guess\n[  529s] toybox: Unknown command find\n[  529s] + for s in guess sub\n[  529s] ++ find -maxdepth 8 -name config.sub\n[  529s] toybox: Unknown command find\n[  529s] + export AR=llvm-ar RANLIB=llvm-ranlib\n[  529s] + AR=llvm-ar\n[  529s] + RANLIB=llvm-ranlib\n[  529s] + export CC=x86_64-tizen-linux-gnu-clang CXX=x86_64-tizen-linux-gnu-clang++\n[  529s] + CC=x86_64-tizen-linux-gnu-clang\n[  529s] + CXX=x86_64-tizen-linux-gnu-clang++\n[  529s] + CFLAGS='-Os -ffunction-sections -fdata-sections -fstack-protector -Wno-unused-command-line-argument -Wno-error=unused-but-set-variable -Wno-error=unused-command-line-argument -momit-leaf-frame-pointer  -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches -fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer -g'\n[  529s] + export CFLAGS\n[  529s] + CXXFLAGS='-Os -ffunction-sections -fdata-sections -fstack-protector -Wno-unused-command-line-argument -Wno-error=unused-but-set-variable -Wno-error=unused-command-line-argument -momit-leaf-frame-pointer  -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches -fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer -g'\n[  529s] + export CXXF\n[truncated]",
    "current_phase": "%build",
    "current_command_summary": {
      "id": "C046",
      "phase": "%build",
      "argv_short": "autoreconf -v --install --force",
      "argv_full": "autoreconf -v --install --force",
      "rsp_expanded": {},
      "command_degraded": false
    },
    "cascade_summary": "",
    "token_estimate": 679
  }
}

## Prompt
请根据 evidence_packet JSON 定位 GBS 构建失败根因并给出最小修复建议。
Failed phase: %build
Primary error: {"id":"E001","kind":"raw_error","severity":"error","message":"autoreconf: error: autopoint failed with exit status: 1","phase":"%build"}
Top candidate: {"rank":1,"event_id":"E001","kind":"raw_error","semantic_class":"generic_error","confidence":0.63}
Evidence paths: []
Use packet.primary_error, packet.root_cause_candidates, and packet.evidence for details.

