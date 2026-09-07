# P4.9 skill-5 gerrit-submit progress

## A0 inherited design drift ledger

Status: COMPLETE, awaiting independent review before extraction commit A.

Authority under test:
`docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3-FROZEN.md`
at freeze commit `f2bc050`.

### Parameterization

`design_drift_ledger.py` no longer embeds a skill-4 corpus directory, version
sequence, draft-name pattern, frozen target, admission snapshot, or required
binding IDs. Each data file now supplies:

- `corpus_dir`, `version_sequence`, and the exact `version_files` mapping;
- `target_design`, `target_version`, and generated target SHA-256;
- `excluded_sections` and `dod_section`;
- `admission.snapshot_version`, `minimum_drift_count`, and `required`;
- existing wrong-section targets used by each `REF_ONLY` negative fixture.

The skill-4 data remains
`docs/clang-fix-campaign/tools/design_drift_ledger.json`. Skill-5 has the
independent data file
`docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json`; bootstrap does
not overwrite the skill-4 file.

### Skill-4 non-regression

The shared execution path was checked against every inherited positive and
negative gate.

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=130 | retained=83 | ignored=47 | bindings=22 | binding_candidates=1410
exit=0

$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py admission-v19 \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
ADMISSION_V19 | snapshot=v1.9 | BINDING_DRIFT=3 | required_known=2 | RED_AS_EXPECTED
exit=1

$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py \
    negative-fixture out-of-scope-misuse \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.json
OUT_OF_SCOPE_SUMMARY | items=47 | RED_AS_EXPECTED
exit=1

$ for each of 22 binding IDs: ... negative-binding <id> --data <skill4-data>
NEGATIVE_BINDING_SUMMARY | bindings=22 | unexpected=0
each exit=1
```

Full outputs and every exit code:

- [skill4-check.txt](a0-evidence/skill4-check.txt)
- [skill4-admission-v19.txt](a0-evidence/skill4-admission-v19.txt)
- [skill4-out-of-scope-negative.txt](a0-evidence/skill4-out-of-scope-negative.txt)
- [skill4-binding-negatives.txt](a0-evidence/skill4-binding-negatives.txt)

The generic `REF_ONLY` negative fixture selects an existing wrong section from
the data file rather than a skill-4 section hardcode. All 22 inherited fixtures
still fail for their intended reasons.

### Skill-5 corpus and gates

The Git-anchored corpus contains the continuous sequence v1.0, v1.1, v1.2,
and v1.3-FROZEN under `history/skill5/`.

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py bootstrap \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
BOOTSTRAP | candidates=34 retained=30 ignored=4 binding_candidates=348 bindings=8
exit=0

$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py check \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
SUMMARY | RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported=34 | retained=30 | ignored=4 | bindings=8 | binding_candidates=348
exit=0
```

The eight forward bindings cover the branch-table contract, fabricated branch
removal, timeout's two observed paths in both section 4 and the DoD, the
section 3.2 result mapping, the private-member count, gate-member expansion,
and the three negative controls. Every DoD is either bound or explicitly
registered as `PROCESS_ONLY`.

Full outputs:

- [skill5-bootstrap.txt](a0-evidence/skill5-bootstrap.txt)
- [skill5-check.txt](a0-evidence/skill5-check.txt)

Bootstrap is deterministic:

```text
before=da1db91465d58031a1ade170d9d9f9aeb5c7c152f31f07ebb0952252bb9cf7c8
after=da1db91465d58031a1ade170d9d9f9aeb5c7c152f31f07ebb0952252bb9cf7c8
deterministic=yes
```

### v1.2 admission falsification

The selected snapshot is v1.2. Its required set contains exactly the two
defects proved to exist in that snapshot:

```text
246:  推送成功 / 推送失败 / 目标 HEAD 未知警告(:185)/ verification 不匹配
251:  skill-3 N2 教训);②`TimeoutExpired` **原样传播**(不归一化);
```

The admission run returns expected exit 1 and includes both required binding
IDs, `B-BRANCH-FABRICATION` and `B-TIMEOUT-TWO-PATHS`:

```text
$ python3 docs/clang-fix-campaign/tools/design_drift_ledger.py admission \
    --data docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
BINDING_DRIFT | B-BRANCH-FABRICATION | missing_definition=['本 skill 不执行 push', '推送成功/失败'], leaked_snippets=[], parsed_targets=[], expected=§4
BINDING_DRIFT | B-TIMEOUT-TWO-PATHS | missing_definition=[], missing_reference=['_run_git', 'ls-remote']
ADMISSION | snapshot=v1.2 | BINDING_DRIFT=7 | required_known=2 | RED_AS_EXPECTED
exit=1
```

The five additional drifts are valid but are not part of the required set.
Full evidence:

- [admission-v12-required-presence.txt](a0-evidence/admission-v12-required-presence.txt)
- [skill5-admission-v12.txt](a0-evidence/skill5-admission-v12.txt)

### Member-count reverse ledger

The v1.1 `6 -> 7` member-count error is deliberately not an admission required
item because it does not exist in the selected v1.2 snapshot. The reverse
ledger independently retains the v1.1-to-v1.2 deletion:

```text
matching_retained_candidates=1
candidate_id=v1.1|old:145-145,new:167-167|e8557589352edbd8e91510a8a5a4014525249827d095586b77fc7c7bb9a3369c
recorded_replay_count=1
v1.1_matches=1 sections={'§2': 1}
v1.2_matches=0 sections={}
v1.3_matches=0 sections={}
```

Full evidence:
[member-count-reverse-ledger.txt](a0-evidence/member-count-reverse-ledger.txt).

### Per-item falsification

```text
$ ... negative-fixture out-of-scope-misuse --data <skill5-data>
OUT_OF_SCOPE_SUMMARY | items=4 | RED_AS_EXPECTED
exit=1

$ for each of 8 binding IDs: ... negative-binding <id> --data <skill5-data>
NEGATIVE_BINDING_SUMMARY | bindings=8 | unexpected=0
each exit=1
```

Full mutation output and exit codes:

- [skill5-out-of-scope-negative.txt](a0-evidence/skill5-out-of-scope-negative.txt)
- [skill5-binding-negatives.txt](a0-evidence/skill5-binding-negatives.txt)

### Cross-batch rule

The skill batch template now states that every admission required item must be
proved present in the selected snapshot. Defects that exist only in another
version belong to the reverse ledger, not to admission.

### Regression and tool quality

```text
$ .venv/bin/pytest -q
897 passed, 1 skipped in 18.41s

$ .venv/bin/mypy
Success: no issues found in 109 source files

$ python3 -m py_compile \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
exit=0

$ .venv/bin/ruff check \
    docs/clang-fix-campaign/tools/design_drift_ledger.py
All checks passed!
```

The first Ruff pass found one 102-character generic error message introduced
by parameterization. It was split across lines without changing behavior; the
recorded final command above is green.
