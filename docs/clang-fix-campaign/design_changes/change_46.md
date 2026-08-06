# change_46: R14 round-2 deferred cleanup ledger

**Status: OPEN — 待 P4.9 前收口**

**Opened:** 2026-08-06

**Scope rule:** 本记录只登记 R14 两家第二轮 delta 评审提出的 NIT/MINOR。
本 change 不修改 `design.md`、实现或测试；各项须在下列约定收口点重新核验并
通过正常设计变更流程落地。

## 待办

| ID / source | 现象 | 约定收口点 |
|---|---|---|
| RD-1 | previous 回退措辞“仅该 arch 从未 build 过”与“向前扫尽后回退最新 REPRODUCE”的一般兜底冲突。涉及当前 `design.md:1520-1521` 与 DoD `2830-2831`；拟统一为“无任何实质 build outcome”。 | P4.9 重构前 |
| RD-2 | `CONVERGENCE` 契约行(`design.md:833`)虽逐类规定字段，但缺少总括句“n_a 类事件 evidence 必为 null”。 | P4.9 重构前 |
| RD-4 | finding disposition 的 D8 文字写成“five event types”，实际应为“five ORPHAN_PASS reason values”。这是审计账措辞，不是运行时枚举变化。 | P4.9 重构前，与 disposition 同步 |
| RD-5 | 出口优先级公式(`design.md:1367-1374`)收窄到 c+clean 共存后，首项 `state_inconsistent_held` 在该局部公式内已不可达；应删除或明确标成防御性保留。 | P4.9 重构前 |
| RD-6 | `design.md:1401` 的 residual-copy HELD 路径没有点名 `reason=state_inconsistent`，恢复/审计语义需显式。 | P4.9 重构前 |
| B-NIT-1 | Canonical 临时文件已 flush/fsync 且通过 `os.link` 原子发布，但未 fsync 父目录；进程并发与部分写入风险已闭合，掉电持久性窗口仍需记录。当前异常路径 fail-closed。 | P5 推送闸前 |
| B-NIT-2 | `os.link` 原子发布依赖临时文件与 canonical 位于支持硬链接的同一文件系统；当前使用同目录临时文件，系统不支持硬链接时会 fail-closed，但环境前提尚未成为显式契约/预检。 | P5 推送闸前 |

## 非目标

- 本 change 不实现以上任何一项。
- 不改变 v1.5.18-FROZEN 权威正文、FIX-1 行为或现有测试结论。
- 不把 NIT/MINOR 升格为本轮 merge blocker；P4.9/P5 到点时必须逐项关闭或重新裁决。
