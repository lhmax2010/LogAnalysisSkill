# P5Q C0 Documentation Validation

Baseline: `26e9e3d`, branch `clang-fix-campaign`.
Scope: frozen document registration, appendix A transcription and P5Q-C0-01.
No production source, tests, checker, or frozen P5Q content changed.

The final command/exit summary is recorded in stage20 progress section 9.
No QuickBuild or real Gerrit operation is part of this validation.

| Command/check | Exit | Output |
|---|---|---|
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | 0 | design-check.log: 0 problem |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py --self-test` | 0 | checker-self-test.log: 38/38 |
| `.venv/bin/python -m pytest -q` | 0 | pytest.log: 1937 passed, 1 skipped |
| `.venv/bin/mypy` | 0 | mypy.log: 110 source files |
| `.venv/bin/ruff check .` (absolute executable, clean worktree below) | 0 | ruff.log: All checks passed |
| In-memory transcription/schema check (procedure below) | 0 | transcription-ddl-final.log |

Ruff ran in `/tmp/p5q-c0-26e9e3d` at `26e9e3d` using the main repository's
`.venv/bin/ruff`. C0 changes only docs, so the code set is identical; unrelated
untracked drafts in the main worktree were not included.

## Transcription Procedure

The one-off Python check did not create or modify any implementation/test file.
It read the frozen file, checked its approved SHA256, then:

1. Extracted the appendix A blockquote before `同时:`, removed only `>`/one
   following space, and compared it to design section 4.5. All 13 clauses match.
2. Compared the complete `CREATE TABLE IF NOT EXISTS campaign_qb_profiles`
   statement and the seven-row section 6.3 transition table with design.md.
3. Checked the literal appendix guidance, signature, and C0-01 version/EF lines.
4. Checked each section 7 code has exactly one definition within design section
   4.3 (bounded by 4.4). There are 14, including 13 new codes relative to baseline.
5. Called the unchanged checker with its resolved authoritative prompt; deleted
   QB_LOGIN_TIMEOUT's definition only in memory and added an out-of-section
   reference. It reported `[ERRCODE] QB_LOGIN_TIMEOUT 未登记于 §4.3` as expected.
6. Executed the full design SQL fence using `sqlite3.connect(':memory:')` and
   `executescript`, with foreign keys enabled. Inserted one valid profile with
   hash `a1` repeated 32 times. Six invalid hashes (empty, 63/65 characters,
   uppercase, nonhex, fullwidth digits) each raised CHECK constraint errors.

`transcription-ddl.log` retains the first attempt's stdout; that attempt exited
1 because its direct call to `check()` omitted `prompt_src`. Diagnosis:
`[CK-IDX-01] 缺少唯一权威 prompt: p45-implementation-prompt-v1_5_15.md`.
The retry used `_find_authoritative_prompt` exactly as the CLI does. No checker,
design assertion, or frozen text was changed to obtain the passing result.
