# P4.9 末终止批次遗留问题

PHASE2-04～07 基线裁决(2026-10-08):逐条按固定改前树 `43a6aa6` 原样实跑的90条命令对账。
基线证据: `a0-evidence/phase2/execution/BASE43/checkers/commands.json`。
本表当前侧取 `787b804` 的 REG03b 原始实跑;本轮未改checker及生产代码。
基线不符20条:仍遗留3条,当前已通过17条(固定树尚未引入的末批工具)。
另有当前 skill5 ledger check 相对基线的新失败,不计入可放行遗留,见 progress PHASE2-08。

| 命令(在tools目录下,python执行) | 原预期exit | 43a6aa6 exit | 当前exit | 原因/状态 |
|---|---|---|---|---|
| `check_design_doc.py --self-test` | 0 | 1 | 1 | OPEN_CARRIED: 未入库的v1.5.2历史样本;self-test 37/38。PHASE2-05按既有问题关闭。 |
| `symbol_audit.py --negative-fixture duplicate-spec-root-mismatch` | 1 | 0 | 0 | OPEN_CARRIED: report旧址已是shim,无_attrs_to_map定义;两树红因相同。PHASE2-04按既有问题关闭,不改断言。 |
| `symbol_audit.py --key-fixture twin-both-binary-key` | 0 | 1 | 1 | OPEN_CARRIED: report旧址已是shim,无_attrs_to_map定义;两树红因相同。PHASE2-04按既有问题关闭,不改断言。 |
| `terminal_predicates.py p49_terminal_data/predicates.json` | 0 | 2 | 0 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_expected_diff.py check` | 0 | 2 | 0 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py normal` | 0 | 2 | 0 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py extra-change` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py missed-change` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py empty-reason` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py impossible-registration` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py missing-mode` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py unknown-mode` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py no-diff-with-differences` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py empty-diff-set` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py readers-empty` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py readers-missing` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_diff_controls.py unchanged-timeout-message` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_phase_controls.py normal` | 0 | 2 | 0 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_phase_controls.py premature-item3` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |
| `terminal_phase_controls.py missing-item4` | 1 | 2 | 1 | RESOLVED: 固定树不存在此末批工具,python exit2;当前已实现且符合预期。 |

准许继承的边界仅为逐条基线不符项,不得扩到其它命令;已修复的末批门禁仍应保留其控制。
PHASE2-04/05关闭的是本批阻塞状态,并不宣称这三条历史控制已修好。
