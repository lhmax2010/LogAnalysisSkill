# P4.9 Skill-1 Convergence-Judge Closeout

Authority:
`docs/clang-fix-campaign/p49-skill1-convergence-judge-design-v1.3-FROZEN.md`
(v1.2 freeze, revised in place to v1.3 by commit C, then filename-aligned at
sign-off).

Implementation commits: `f4c8142`, `f7194ae`, `954bbcd`, `9bf1af0`.
Freeze commit: `d3478ab`.

## Summary

- Frozen §7 DoD: **8 DONE / 0 DEFERRED**.
- Named downstream ledger: **3 DEFERRED**, each with a closing batch.
- Combined account: **8 DONE / 3 DEFERRED**.

## DoD Account

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| 1 | “全量 == 基线(846/1),且 C21 修后干净环境 0 failed” | DONE | `f7194ae`, `9bf1af0`; `progress.md:89-100`, `progress.md:306-329` | Required alias coverage raised the suite from the 846/1 launch baseline to `847 passed, 1 skipped`. Independent Claude clean-environment acceptance changed the three C21 tests from `3 failed` to `0 failed` at `9bf1af0`; repository minimal-environment replay: `3 passed, 35 deselected`, exit 0. |
| 2 | “别名同一性断言绿;grep 全仓两函数各恰一处定义” | DONE | `f7194ae`; `tests/unit/test_convergence.py:66-68`; `tizen_convergence_judge/convergence.py:203`, `:383`, `:442-443`; `progress.md:79-87` | `test_public_fingerprint_and_error_count_aliases_are_identical: 1 passed`; both `is` assertions are true; repository definitions are exactly `_primary_fingerprint` at line 203 and `_error_count` at line 383. |
| 3 | “旧址 convergence.py 零 def/class(纯 shim)” | DONE | `f7194ae`; `ci_triage/verify/convergence.py:1-35`; `progress.md:106-111` | `rg '^(def|class) ' .../verify/convergence.py` produced no output; the file contains only re-exports and `__all__`. |
| 4 | “root-layers/forbidden 激活,负控制①②红 + 四契约正向绿,exit code 入 dev_memory” | DONE | `954bbcd`; `.importlinter:1-44`; `progress.md:155-196` | Positive: `Contracts: 5 kept, 0 broken`, exit 0 (root-layers plus the four step-0 contracts). Skill→orchestration and shared→skill probes each returned exit 1 with the named broken contract. |
| 5 | “双道审计全绿(35 行逐符号 + 计数钉定溯及 step-0 四模块),多消费方两条负 fixture 均红,step-0 42+4 判定逐项不翻转” | DONE | `954bbcd`; `progress.md:128-152`, `progress.md:198-222` | Both layered-rule fixtures returned MISMATCH and exit 1; regression lock: `42` symbols + `4` modules, `verdict_changes=0`; symbol audit: `77 SYMBOL OK + 4 MODULE-SCOPE OK`, zero mismatch/incomplete; bridge: same 77+4, all difference counts zero. Pins are `10/3/8/27`; temporary classify count `28/27` returned mismatch and exit 1. |
| 6 | “parity 掩码一致;⑧ arch 豁免证据(grep)在档” | DONE | `954bbcd`; `progress.md:224-243` | Shim and skill JSON share SHA-256 `2f881fe8935b8b652c756efac596c2d904c1e45f3b502857b75c3d071d99957b`; `cmp_exit=0`. `grep -c arch .../convergence.py` printed `0` and exited 1. |
| 7 | “SKILL.md 落盘;shim 清单更新” | DONE | `954bbcd`; `tizen-convergence-judge/SKILL.md:1-44`; `progress.md:106-111` | `SKILL.md` contains the narrow trigger, inputs, outputs, errors, and idempotency contract. The legacy convergence shim is registered for the one-shot P4.9 cleanup after all six skills are extracted. |
| 8 | “测试 diff 仅 §5.1 两类(C21 的 A commit 除外,其性质为测试基建修复,单独 commit 隔离)” | DONE | `f4c8142`, `f7194ae`, `9bf1af0`; commit stats and diffs | C21 environment work is isolated in test commits A/D. Commit B test changes are import-path flips plus the explicitly frozen §2.2 alias-identity assertion; no existing behavioral assertion or fixture data was rewritten. Commit C changes no production implementation or tests. |

## Layered Criterion Proof

The v1.3 multi-consumer criterion is a refinement, not a relaxation:

```text
skill owner + shared consumer      -> MISMATCH, exit 1
skill owner + peer-skill consumer -> MISMATCH, exit 1
step0_symbol_verdicts_compared=42
step0_module_verdicts_compared=4
verdict_changes=0
regression_lock_exit=0
```

The rule now uses the same order as the active root contract:
`ci_triage > registered skills > tizen_ci_shared`.

## C21 Acceptance

Commit A's five-root list was structurally stale after commit B introduced a
sixth package root. Commit D (`9bf1af0`) derives sorted repository `*/scripts`
roots and asserts both a non-empty result and the presence of
`tizen_convergence_judge` and `ci_triage`.

Evidence is intentionally separated:

- Independent Claude clean environment: `3 failed` before the fix, `0 failed`
  at `9bf1af0` (reported 2026-08-15).
- Repository minimal environment: the same three tests report `3 passed,
  35 deselected`, exit 0.
- Target full suite at closeout: `847 passed, 1 skipped in 18.02s`.

The local pre-fix detached probe remained green because the existing virtual
environment could still resolve the installed skill. That is evidence of the
masking condition, not a claimed reproduction of Claude's clean failure.

## Deferred Ledger

| Item | Status | Closing batch | Evidence |
|---|---|---|---|
| Activate `skill-independence` and its peer-skill negative control | DEFERRED | Second skill extraction batch | frozen skill-1 §3; `progress.md:193-196` |
| Delete the convergence and other compatibility shims | DEFERRED | Single P4.9 final cleanup after all six skills are extracted | step-0 frozen §6.2; `progress.md:106-111` |
| Resolve the seven inherited `gbs_report` fetch/parse constraints | DEFERRED | `triage-report` extraction batch | step-0 frozen §8, lines 399-427 |

Every deferred item has an owning batch. None changes the convergence-judge
runtime contract or weakens a current safety gate.

## Final Verification

Fresh closeout runs on `9bf1af0`:

```text
pytest: 847 passed, 1 skipped in 18.02s
C21 minimal environment: 3 passed, 35 deselected in 0.46s
alias identity: 1 passed, 14 deselected in 0.01s
lint-imports: 5 kept, 0 broken; exit 0
symbol_audit: 77 SYMBOL OK + 4 MODULE-SCOPE OK; 0 MISMATCH; 0 INCOMPLETE
table_audit_bridge: 77 SYMBOL OK + 4 MODULE-SCOPE OK; all difference counts zero
```

## 最终签批

| Signer | Date | Confirmation |
|---|---|---|
| Claude | 2026-08-15 | 独立核验全部门禁，并完成 C21 定义性验收：干净环境三条子进程测试由 `3 failed` 变为 `0 failed`。 |
| 评审 A | 2026-08-15 | 独立实跑评审包全部门禁命令后确认 skill-1 CLOSED。 |
| 评审 B | 2026-08-15 | 独立实跑评审包全部门禁命令后确认 skill-1 CLOSED；提出冻结文件名与正文版本不一致的 Kimi NIT。 |

状态：**skill-1 CLOSED @ `e7900bb`**（开发者放行日期：2026-08-15）。

Kimi NIT 已在本签批提交中处置：冻结正文与 history 快照由旧的 v1.2
文件名对齐为 `p49-skill1-convergence-judge-design-v1.3-FROZEN.md`，所有
tracked 引用同步更新；`table_audit_bridge.py` 仅更新解析目标路径常量，
判据、解析逻辑与输出格式均未改变，并以 bridge 全绿复验。
