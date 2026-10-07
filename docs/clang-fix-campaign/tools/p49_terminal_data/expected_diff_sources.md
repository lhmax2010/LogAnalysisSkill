# Section 6 Registration Sources

Generated from the registration JSON, not a second authority. Before-run: PENDING_SEG3.
Every listed path changes; every unlisted field must compare exactly equal.

| Scenario | Field | Old Source | New Source |
|---|---|---|---|
| DANGLING_SYMLINK | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/0/trace/0/kwargs | 附录C/E2-2: timeout=null |
| DANGLING_SYMLINK | `/exception_type` | `OBS_VALUE`: e1-item3/raw.json#/observations/0/outcome/exception/value/type | §3 预期差异: GerritError |
| DANGLING_SYMLINK | `/exception_code` | `OBS_STATE`: e1-item3/raw.json#/observations/0/outcome/exception/value/code | §3 预期差异: SOURCE_DIR_UNSAFE |
| DANGLING_SYMLINK | `/exception_message` | `OBS_VALUE`: e1-item3/raw.json#/observations/0/outcome/exception/value/message | 附录C/E2-1: EXISTING_BRANCH_OUTPUT |
| LIVE_SYMLINK_TO_DIR | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/1/trace/0/kwargs | 附录C/E2-2: timeout=null |
| REAL_DIR | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/2/trace/0/kwargs | 附录C/E2-2: timeout=null |
| REAL_DIR | `/calls/1/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/2/trace/1/kwargs | 附录C/E2-2: timeout=null |
| REAL_DIR | `/calls/2/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/2/trace/2/kwargs | 附录C/E2-2: timeout=null |
| REAL_DIR | `/calls/3/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/2/trace/3/kwargs | 附录C/E2-2: timeout=null |
| REAL_DIR | `/calls/4/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/2/trace/4/kwargs | 附录C/E2-2: timeout=null |
| ABSENT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/3/trace/0/kwargs | 附录C/E2-2: timeout=null |
| ABSENT | `/calls/1/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/3/trace/1/kwargs | 附录C/E2-2: timeout=null |
| ABSENT | `/calls/2/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/3/trace/2/kwargs | 附录C/E2-2: timeout=null |
| ABSENT | `/calls/3/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/3/trace/3/kwargs | 附录C/E2-2: timeout=null |
| ABSENT | `/calls/4/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item3/raw.json#/observations/3/trace/4/kwargs | 附录C/E2-2: timeout=null |
| surface1-none | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/0/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface1-timeout | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/1/trace/0/kwargs | 附录C/E2-2: timeout=0.125 |
| surface1-timeout | `/exception_type` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: GerritError |
| surface1-timeout | `/exception_code` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: FETCH_TIMEOUT |
| surface1-timeout | `/exception_message` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: TIMEOUT_MESSAGE_FROM_EXC |
| surface1-SIGINT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/2/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface1-SIGTERM | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/3/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface2-none | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/4/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface2-timeout | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/5/trace/0/kwargs | 附录C/E2-2: timeout=0.125 |
| surface2-timeout | `/exception_type` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: GerritError |
| surface2-timeout | `/exception_code` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: FETCH_TIMEOUT |
| surface2-timeout | `/exception_message` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: TIMEOUT_MESSAGE_FROM_EXC |
| surface2-SIGINT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/6/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface2-SIGTERM | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/7/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface3-none | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/8/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface3-timeout | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/9/trace/0/kwargs | 附录C/E2-2: timeout=0.125 |
| surface3-timeout | `/exception_type` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: GerritSubmitError |
| surface3-timeout | `/exception_code` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: GIT_TIMEOUT |
| surface3-timeout | `/exception_message` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: TIMEOUT_MESSAGE_FROM_EXC |
| surface3-SIGINT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/10/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface3-SIGTERM | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/11/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface4-none | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/12/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface4-timeout | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/13/trace/0/kwargs | 附录C/E2-2: timeout=0.125 |
| surface4-timeout | `/warnings` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: target_head_unknown:timeout |
| surface4-timeout | `/return_value` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: target_head_unknown:timeout |
| surface4-SIGINT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/14/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface4-SIGTERM | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/15/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface5-none | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/16/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface5-timeout | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/17/trace/0/kwargs | 附录C/E2-2: timeout=0.125 |
| surface5-timeout | `/exception_type` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: WorkspaceViolation |
| surface5-timeout | `/exception_message` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: GIT_TIMEOUT_PREFIX_PLUS_EXC |
| surface5-SIGINT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/18/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface5-SIGTERM | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/19/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface6-none | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/20/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface6-timeout | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/21/trace/0/kwargs | 附录C/E2-2: timeout=0.125 |
| surface6-timeout | `/exception_type` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | §3.2⑥ timeout 单元格: WorkspaceViolation |
| surface6-timeout | `/exception_message` | `ABSENT_SECTION4`: terminal §4: ABSENT (not representable before optional timeout) | 附录C/E1-2: GIT_TIMEOUT_PREFIX_PLUS_EXC |
| surface6-SIGINT | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/22/trace/0/kwargs | 附录C/E2-2: timeout=null |
| surface6-SIGTERM | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/23/trace/0/kwargs | 附录C/E2-2: timeout=null |
| EXCLUDE_INTERRUPTED | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/22/trace/0/kwargs | 附录C/E2-2: timeout=null |
| MARKER_WRITE_INTERRUPTED | `/calls/0/kwargs/timeout` | `OBS_ABSENT_TIMEOUT`: e1-item4/raw.json#/observations/20/trace/0/kwargs | 附录C/E2-2: timeout=null |
