# PHASE2-03 全套门禁实测

取证 HEAD: `787b8040245907c3c849d80478e30961d26a4ed2`; 独立工作树 `/tmp/p49-terminal-REG03b`。
下表由 `checkers/commands.json` 机械生成;负控制的预期 exit=1,不等于执行失败可充作证伪。
完整 argv、环境、日志 hash 与执行器源码见该 JSON;原始输出逐项链接。

| 命令 | 预期 exit | 实际 exit | 对账 | 原文 |
|---|---|---|---|---|
| `python symbol_audit.py` | 0 | 0 | PASS | [symbol](checkers/symbol.log) |
| `python table_audit_bridge.py` | 0 | 0 | PASS | [bridge](checkers/bridge.log) |
| `python check_design_doc.py docs/clang-fix-campaign/design.md` | 0 | 0 | PASS | [design-doc](checkers/design-doc.log) |
| `python check_design_doc.py --self-test` | 0 | 1 | FAIL | [design-doc-controls](checkers/design-doc-controls.log) |
| `python symbol_audit.py --negative-fixture skill-owner-shared-consumer` | 1 | 1 | PASS | [symbol-negative-skill-owner-shared-consumer](checkers/symbol-negative-skill-owner-shared-consumer.log) |
| `python symbol_audit.py --negative-fixture skill-owner-peer-skill-consumer` | 1 | 1 | PASS | [symbol-negative-skill-owner-peer-skill-consumer](checkers/symbol-negative-skill-owner-peer-skill-consumer.log) |
| `python symbol_audit.py --negative-fixture duplicate-spec-root-mismatch` | 1 | 0 | FAIL | [symbol-negative-duplicate-spec-root-mismatch](checkers/symbol-negative-duplicate-spec-root-mismatch.log) |
| `python symbol_audit.py --negative-fixture twin-both-name-only` | 1 | 1 | PASS | [symbol-negative-twin-both-name-only](checkers/symbol-negative-twin-both-name-only.log) |
| `python symbol_audit.py --negative-fixture import-binding-legacy-alias` | 1 | 1 | PASS | [symbol-negative-import-binding-legacy-alias](checkers/symbol-negative-import-binding-legacy-alias.log) |
| `python symbol_audit.py --key-fixture source-twin-only` | 0 | 0 | PASS | [symbol-key-source-twin-only](checkers/symbol-key-source-twin-only.log) |
| `python symbol_audit.py --key-fixture twin-both-binary-key` | 0 | 1 | FAIL | [symbol-key-twin-both-binary-key](checkers/symbol-key-twin-both-binary-key.log) |
| `python symbol_audit.py --binding-fixture regression-lock` | 0 | 0 | PASS | [symbol-binding-regression-lock](checkers/symbol-binding-regression-lock.log) |
| `python symbol_audit.py --binding-fixture aliased-import` | 0 | 0 | PASS | [symbol-binding-aliased-import](checkers/symbol-binding-aliased-import.log) |
| `python symbol_audit.py --binding-fixture same-name-import` | 0 | 0 | PASS | [symbol-binding-same-name-import](checkers/symbol-binding-same-name-import.log) |
| `python symbol_audit.py --binding-fixture planned-run-git` | 0 | 0 | PASS | [symbol-binding-planned-run-git](checkers/symbol-binding-planned-run-git.log) |
| `python symbol_audit.py --surface-fixture mixed-case-alias` | 1 | 1 | PASS | [symbol-surface](checkers/symbol-surface.log) |
| `python table_audit_bridge.py --key-fixture twin-both-binary-key` | 0 | 0 | PASS | [bridge-binary](checkers/bridge-binary.log) |
| `python table_audit_bridge.py --negative-fixture twin-both-name-only` | 1 | 1 | PASS | [bridge-name-only](checkers/bridge-name-only.log) |
| `python table_audit_bridge.py --relocation-negative missing-destination` | 1 | 1 | PASS | [relocation-missing-destination](checkers/relocation-missing-destination.log) |
| `python table_audit_bridge.py --relocation-negative wrong-definition` | 1 | 1 | PASS | [relocation-wrong-definition](checkers/relocation-wrong-definition.log) |
| `python table_audit_bridge.py --relocation-negative wrong-owner` | 1 | 1 | PASS | [relocation-wrong-owner](checkers/relocation-wrong-owner.log) |
| `python table_audit_bridge.py --relocation-negative source-remains` | 1 | 1 | PASS | [relocation-source-remains](checkers/relocation-source-remains.log) |
| `python table_audit_bridge.py --relocation-negative mapping-contract` | 1 | 1 | PASS | [relocation-mapping-contract](checkers/relocation-mapping-contract.log) |
| `python table_audit_bridge.py --relocation-negative source-table-mismatch` | 1 | 1 | PASS | [relocation-source-table-mismatch](checkers/relocation-source-table-mismatch.log) |
| `python table_audit_bridge.py --relocation-synthetic one` | 0 | 0 | PASS | [synthetic-one](checkers/synthetic-one.log) |
| `python table_audit_bridge.py --relocation-synthetic two` | 0 | 0 | PASS | [synthetic-two](checkers/synthetic-two.log) |
| `python table_audit_bridge.py --relocation-synthetic three` | 0 | 0 | PASS | [synthetic-three](checkers/synthetic-three.log) |
| `python design_drift_ledger.py check --data design_drift_ledger.json` | 0 | 0 | PASS | [ledger4-check](checkers/ledger4-check.log) |
| `python design_drift_ledger.py admission-v19 --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-admission](checkers/ledger4-admission.log) |
| `python design_drift_ledger.py negative-fixture out-of-scope-misuse --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-out-of-scope](checkers/ledger4-out-of-scope.log) |
| `python design_drift_ledger.py negative-binding B-MIGRATION-MODES --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-MIGRATION-MODES](checkers/ledger4-B-MIGRATION-MODES.log) |
| `python design_drift_ledger.py negative-binding B-PYTHONPATH-PARITY --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-PYTHONPATH-PARITY](checkers/ledger4-B-PYTHONPATH-PARITY.log) |
| `python design_drift_ledger.py negative-binding B-SYMBOL-TOTAL --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-SYMBOL-TOTAL](checkers/ledger4-B-SYMBOL-TOTAL.log) |
| `python design_drift_ledger.py negative-binding B-INCOMPLETE-GUARDS --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-INCOMPLETE-GUARDS](checkers/ledger4-B-INCOMPLETE-GUARDS.log) |
| `python design_drift_ledger.py negative-binding B-EXCEPTION-NEGATIVES --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-EXCEPTION-NEGATIVES](checkers/ledger4-B-EXCEPTION-NEGATIVES.log) |
| `python design_drift_ledger.py negative-binding B-EXCEPTION-CONFIG --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-EXCEPTION-CONFIG](checkers/ledger4-B-EXCEPTION-CONFIG.log) |
| `python design_drift_ledger.py negative-binding B-TWIN-COUNT --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-TWIN-COUNT](checkers/ledger4-B-TWIN-COUNT.log) |
| `python design_drift_ledger.py negative-binding B-BRANCH-ARCH --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-BRANCH-ARCH](checkers/ledger4-B-BRANCH-ARCH.log) |
| `python design_drift_ledger.py negative-binding B-PRE-SHIM --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-PRE-SHIM](checkers/ledger4-B-PRE-SHIM.log) |
| `python design_drift_ledger.py negative-binding B-POST-SHIM --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-POST-SHIM](checkers/ledger4-B-POST-SHIM.log) |
| `python design_drift_ledger.py negative-binding B-DELIVERY --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-DELIVERY](checkers/ledger4-B-DELIVERY.log) |
| `python design_drift_ledger.py negative-binding B-SUBPROCESS-BLIND-SPOT --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-SUBPROCESS-BLIND-SPOT](checkers/ledger4-B-SUBPROCESS-BLIND-SPOT.log) |
| `python design_drift_ledger.py negative-binding B-MECHANICAL-SYNC --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-MECHANICAL-SYNC](checkers/ledger4-B-MECHANICAL-SYNC.log) |
| `python design_drift_ledger.py negative-binding B-RELOCATION-NEGATIVES --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-RELOCATION-NEGATIVES](checkers/ledger4-B-RELOCATION-NEGATIVES.log) |
| `python design_drift_ledger.py negative-binding B-SPECS-SEMANTICS --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-SPECS-SEMANTICS](checkers/ledger4-B-SPECS-SEMANTICS.log) |
| `python design_drift_ledger.py negative-binding B-GUARD-EQUALITY --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-GUARD-EQUALITY](checkers/ledger4-B-GUARD-EQUALITY.log) |
| `python design_drift_ledger.py negative-binding B-PARITY-FREEZE --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-PARITY-FREEZE](checkers/ledger4-B-PARITY-FREEZE.log) |
| `python design_drift_ledger.py negative-binding B-LEDGER-EXECUTION --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-LEDGER-EXECUTION](checkers/ledger4-B-LEDGER-EXECUTION.log) |
| `python design_drift_ledger.py negative-binding B-RAW-DIFF --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-RAW-DIFF](checkers/ledger4-B-RAW-DIFF.log) |
| `python design_drift_ledger.py negative-binding B-EXPECTED-MATCHES --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-EXPECTED-MATCHES](checkers/ledger4-B-EXPECTED-MATCHES.log) |
| `python design_drift_ledger.py negative-binding B-X-PRESERVE --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-X-PRESERVE](checkers/ledger4-B-X-PRESERVE.log) |
| `python design_drift_ledger.py negative-binding B-CORPUS-REFERENCE --data design_drift_ledger.json` | 1 | 1 | PASS | [ledger4-B-CORPUS-REFERENCE](checkers/ledger4-B-CORPUS-REFERENCE.log) |
| `python design_drift_ledger.py check --data design_drift_ledger.skill5.json` | 0 | 2 | FAIL | [ledger5-check](checkers/ledger5-check.log) |
| `python design_drift_ledger.py admission --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-admission](checkers/ledger5-admission.log) |
| `python design_drift_ledger.py negative-fixture out-of-scope-misuse --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-out-of-scope](checkers/ledger5-out-of-scope.log) |
| `python design_drift_ledger.py negative-binding B-BRANCH-DOD --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-BRANCH-DOD](checkers/ledger5-B-BRANCH-DOD.log) |
| `python design_drift_ledger.py negative-binding B-BRANCH-FABRICATION --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-BRANCH-FABRICATION](checkers/ledger5-B-BRANCH-FABRICATION.log) |
| `python design_drift_ledger.py negative-binding B-TIMEOUT-BRANCH-LOCK --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-TIMEOUT-BRANCH-LOCK](checkers/ledger5-B-TIMEOUT-BRANCH-LOCK.log) |
| `python design_drift_ledger.py negative-binding B-TIMEOUT-TWO-PATHS --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-TIMEOUT-TWO-PATHS](checkers/ledger5-B-TIMEOUT-TWO-PATHS.log) |
| `python design_drift_ledger.py negative-binding B-RESULT-MAPPING --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-RESULT-MAPPING](checkers/ledger5-B-RESULT-MAPPING.log) |
| `python design_drift_ledger.py negative-binding B-PRIVATE-COUNT --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-PRIVATE-COUNT](checkers/ledger5-B-PRIVATE-COUNT.log) |
| `python design_drift_ledger.py negative-binding B-GATE-MEMBERS --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-GATE-MEMBERS](checkers/ledger5-B-GATE-MEMBERS.log) |
| `python design_drift_ledger.py negative-binding B-GATE-CONTROLS --data design_drift_ledger.skill5.json` | 1 | 1 | PASS | [ledger5-B-GATE-CONTROLS](checkers/ledger5-B-GATE-CONTROLS.log) |
| `python design_drift_ledger.py check --data design_drift_ledger.skill6.json` | 0 | 0 | PASS | [ledger6-check](checkers/ledger6-check.log) |
| `python design_drift_ledger.py negative-fixture out-of-scope-misuse --data design_drift_ledger.skill6.json` | 1 | 1 | PASS | [ledger6-out-of-scope](checkers/ledger6-out-of-scope.log) |
| `python design_drift_ledger.py negative-binding B-SYMBOL-PARSER --data design_drift_ledger.skill6.json` | 1 | 1 | PASS | [ledger6-B-SYMBOL-PARSER](checkers/ledger6-B-SYMBOL-PARSER.log) |
| `python design_drift_ledger.py negative-binding B-CONSTRAINT-CLOSE --data design_drift_ledger.skill6.json` | 1 | 1 | PASS | [ledger6-B-CONSTRAINT-CLOSE](checkers/ledger6-B-CONSTRAINT-CLOSE.log) |
| `python design_drift_ledger.py negative-binding B-TWIN-CLOSE --data design_drift_ledger.skill6.json` | 1 | 1 | PASS | [ledger6-B-TWIN-CLOSE](checkers/ledger6-B-TWIN-CLOSE.log) |
| `python design_drift_ledger.py negative-binding B-TEST-PARITY --data design_drift_ledger.skill6.json` | 1 | 1 | PASS | [ledger6-B-TEST-PARITY](checkers/ledger6-B-TEST-PARITY.log) |
| `python design_drift_ledger.py negative-binding B-BRANCH-INVENTORY --data design_drift_ledger.skill6.json` | 1 | 1 | PASS | [ledger6-B-BRANCH-INVENTORY](checkers/ledger6-B-BRANCH-INVENTORY.log) |
| `python branch_inventory.py check` | 0 | 0 | PASS | [branch-check](checkers/branch-check.log) |
| `python branch_inventory.py parser-only` | 0 | 0 | PASS | [branch-parser-only](checkers/branch-parser-only.log) |
| `python branch_inventory.py admission-v17` | 1 | 1 | PASS | [branch-admission-v17](checkers/branch-admission-v17.log) |
| `python terminal_predicates.py p49_terminal_data/predicates.json` | 0 | 0 | PASS | [terminal-predicates](checkers/terminal-predicates.log) |
| `python terminal_expected_diff.py check` | 0 | 0 | PASS | [terminal-expected-diff](checkers/terminal-expected-diff.log) |
| `python terminal_diff_controls.py normal` | 0 | 0 | PASS | [terminal-diff-normal](checkers/terminal-diff-normal.log) |
| `python terminal_diff_controls.py extra-change` | 1 | 1 | PASS | [terminal-diff-extra-change](checkers/terminal-diff-extra-change.log) |
| `python terminal_diff_controls.py missed-change` | 1 | 1 | PASS | [terminal-diff-missed-change](checkers/terminal-diff-missed-change.log) |
| `python terminal_diff_controls.py empty-reason` | 1 | 1 | PASS | [terminal-diff-empty-reason](checkers/terminal-diff-empty-reason.log) |
| `python terminal_diff_controls.py impossible-registration` | 1 | 1 | PASS | [terminal-diff-impossible-registration](checkers/terminal-diff-impossible-registration.log) |
| `python terminal_diff_controls.py missing-mode` | 1 | 1 | PASS | [terminal-diff-missing-mode](checkers/terminal-diff-missing-mode.log) |
| `python terminal_diff_controls.py unknown-mode` | 1 | 1 | PASS | [terminal-diff-unknown-mode](checkers/terminal-diff-unknown-mode.log) |
| `python terminal_diff_controls.py no-diff-with-differences` | 1 | 1 | PASS | [terminal-diff-no-diff-with-differences](checkers/terminal-diff-no-diff-with-differences.log) |
| `python terminal_diff_controls.py empty-diff-set` | 1 | 1 | PASS | [terminal-diff-empty-diff-set](checkers/terminal-diff-empty-diff-set.log) |
| `python terminal_diff_controls.py readers-empty` | 1 | 1 | PASS | [terminal-diff-readers-empty](checkers/terminal-diff-readers-empty.log) |
| `python terminal_diff_controls.py readers-missing` | 1 | 1 | PASS | [terminal-diff-readers-missing](checkers/terminal-diff-readers-missing.log) |
| `python terminal_diff_controls.py unchanged-timeout-message` | 1 | 1 | PASS | [terminal-diff-unchanged-timeout-message](checkers/terminal-diff-unchanged-timeout-message.log) |
| `python terminal_phase_controls.py normal` | 0 | 0 | PASS | [terminal-phase-normal](checkers/terminal-phase-normal.log) |
| `python terminal_phase_controls.py premature-item3` | 1 | 1 | PASS | [terminal-phase-premature-item3](checkers/terminal-phase-premature-item3.log) |
| `python terminal_phase_controls.py missing-item4` | 1 | 1 | PASS | [terminal-phase-missing-item4](checkers/terminal-phase-missing-item4.log) |

合计: 90 条;符合预期 86;不符合预期 4。

## 全仓与 CI

| 命令 | exit | 结果 |
|---|---|---|
| `python -m pytest tests/ -v -p pytest_cov --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | 0 | [原文](pytest-ci.log); [命令与环境](pytest-ci.command.json) |
| `python -m mypy tizen-ci-shared/scripts/tizen_ci_shared tizen-convergence-judge/scripts/tizen_convergence_judge tizen-qb-discover/scripts/tizen_qb_discover tizen-gerrit-fetch/scripts/tizen_gerrit_fetch tizen-build-verify/scripts/tizen_build_verify tizen-gerrit-submit/scripts/tizen_gerrit_submit tizen-triage-report/scripts/tizen_triage_report tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-build-workflow/scripts/gbs_workflow tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` | 0 | [原文](mypy-ci.log); [命令与环境](mypy-ci.command.json) |
| `/tmp/p49-a0-regression-43a6aa6/bin/ruff check .` | 0 | [原文](ruff.log); [命令与环境](ruff.command.json) |
| `/tmp/p49-a0-regression-43a6aa6/bin/lint-imports --no-cache` | 0 | [原文](lint-imports.log); [命令与环境](lint-imports.command.json) |

本地 pytest: **1343 passed / 1 skipped**,coverage **94.62%**。
完整 nodeid 集合与批准包逐项对比:1344 个全保留,状态变化0;4个拟删测试尚未删除。见 [nodeid-proof.json](nodeid-proof.json)。

远端 GitHub Actions [37612769455](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37612769455) 执行原样 ci.yml:
checkout/setup-python/系统依赖/Python依赖/Lint/Type check 均 success;Tests exit **1**, **106 failed / 1237 passed / 1 skipped**。
原文明确 checkout 使用 `--depth=1`,历史blob读取失败(`AUTHORITY_GIT_BLOB`);无权以本地绿代替远端失败。
状态 API 未提供成功步骤的数字 exit,此处仅如实记 success;远端 Tests 的数字 exit1来自原始日志。
`gh run view --log` 自身 exit0仅表示取日志成功,不表示CI通过。
见 [CI步骤状态](ci-status.log)、[完整CI日志](ci-log.log)、[读取命令](ci-log.command.json)。

## 停点

新停止项及候选处置见 progress.md §37.3。C01-C13 未重启,未运行删除后入口/残留/打包证明,不生成 D DONE 收口。
REG03/ 是首次补登记后的诊断日志,含命令选择纠正前的输出;本表仅采用 REG03b 的复跑结果。
E11-5 已停用的静态发现管线没有重新充作现行设计门禁;其原有单测仍包含在全仓pytest中。
