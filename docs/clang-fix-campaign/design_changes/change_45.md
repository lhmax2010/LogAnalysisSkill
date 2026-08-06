# change_45: R14 round-two closure and canonical publication hardening

- 状态:已采纳并冻结
- 生效版本:`v1.5.18-FROZEN`
- 日期:2026-08-06
- 来源:`review/r14-round2-change45.md`

## 程序性裁决

`change_*.md` 只记录意图,权威正文才是事实。处置表中的 `Closed` 必须
同时给出正文修改位置、修改前后片段和可复核 grep;记录与正文冲突时以
`design.md` 为准。无法由正文 grep 自证的项目仍视为 Open。

## 正文闭环

1. reconcile 的 a0 失败与未 link PASS 归属多命中只提交 arch-scoped
   `HELD(state_inconsistent)` 后立即返回,不得继续 b/b'/c/d;出口优先级
   公式只适用于 c 异常组与 clean 组并存。
2. previous evidence 的 `rebaselined` 锚点绑定到该事件之前紧邻的
   REPRODUCE;向前没有实质事件或锚点时回退最新 REPRODUCE。DoD 分别
   固定 n_a-over-PASS 与 n_a-over-rebaselined 的不可穿越反例。
3. CONVERGENCE 契约恢复 `at` 必填、result/verdict/previous_basis 枚举、
   FAIL evidence 必填和其它组合 `PayloadSchemaError` 兜底。
4. `event_type` 注释补 CONVERGENCE/SECONDARY_TARGET_ADOPTED;
   `adopted_fingerprint` 统一单数;生命周期终态释放统一经
   `release_terminal_worktrees`。
5. `orphan_pass` / `state_inconsistent` HELD 为终态,repair-step 与
   rebaseline 均无恢复旁路;仅 `previous_evidence_missing` 可经
   campaign-rebaseline 恢复。前两类只能人工带外修库并带外写状态复位。
6. `REJECTED_ORPHAN_PASS_HELD` 接入 wrapper step 7 与 §4.2 branch 映射;
   b' 零 invocation 候选明确写 `no_free_invocation_slot`,多候选写
   `ambiguous`;错误码 grep 覆盖非 `REJECTED_` 异常名。
7. 恢复 §4.1 代码块丢失的注释前缀;checker 新增 CK-FENCE-01:
   真 design 必须至少包含一个 Python fence,任何未闭合 fence 显式失败。
8. FK 约束增加 pragma-off 反向 DoD;`change_44` 的 D10 实际修改范围补记。

## FIX-1 补强

1. canonical edit spec 不再直接独占创建目标后分离写入。实现改为同目录
   唯一临时文件完整 write + flush/fsync,再用 `os.link` 原子发布;
   EEXIST 只接受目标 hash 相同。崩溃前不会留下半文件/零字节 canonical。
2. X6 的 rebaseline 测试在锚点更早处写入实质 FAIL,使穿越锚点的旧实现
   确实取错 previous;修复后必须取锚定 REPRODUCE。
3. X11 的目标 unit 建合法 link/PASS,另一 unit 注入坏 payload_json;
   全表扫描旧实现会误 HELD,unit-scoped 实现必须返回 linked_already。
4. 残留 disposable copy 检查前移到 invocation consume 之前。protected、
   PASS-bound 或清理失败时 HELD 且不计费;无保护残留仍安全清理后 build。

## 完成闸门

- `design.md` 与 v1.5.18 frozen snapshot 逐字节一致。
- checker self-test 含真文档 Python-fence 非空与未闭合 fence 反例。
- 正文 grep 自证表逐项覆盖 D/X 项,无自证不得标 Closed。
- campaign targeted、全量 pytest、ruff、mypy 全绿;第二轮 delta 包回送
  两家确认。merge 在双家确认与开发者放行前继续 blocked。
