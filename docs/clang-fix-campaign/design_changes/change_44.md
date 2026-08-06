# change_44: R14 closure and FIX-1 contract

- 状态:已采纳并冻结
- 生效版本:`v1.5.17-FROZEN`
- 日期:2026-08-06
- 来源:`review/r14-closure-change44-fixpass.md`

## 裁决

R14 三方评审确认 P4.5 尚不能合并。设计先关闭以下契约缺口,随后
FIX-1 必须逐项实现并由 delta 评审包复核。

1. `campaign_rounds.edit_spec_ref` 改为 unit 级 canonical 路径
   `ws/<unit_hash>/rounds/round_<N>/edit_spec.json`;arch 副本仅作 build
   输入。双 arch 同轮、同字节必须共用一个 round 身份并各自 build。
2. previous evidence 回溯以 PASS 和 rebaselined 为不可穿越锚点:PASS
   返回 synthetic zero;rebaselined 只绑定其后的首个 REPRODUCE。
3. reconcile 的 a0 与 attribution 多命中仅写 HELD 后立即返回;只有 clean
   分支可继续执行其余写集。已 link PASS 必须带非空整数 invocation id。
4. wrapper 捕获 round/budget 耗尽后写 `ROUNDS_EXHAUSTED`,reason 分别为
   `rounds`/`budget`;最新 unit status 不在可执行白名单时 fail closed。
5. FK 物理保证以每个 SQLite 连接启用 `foreign_keys=ON` 为前提;WAL 与
   busy timeout 同为冻结连接属性,并由反向测试证明约束不是纸面声明。
6. §4.1 外层使用四反引号以容纳内嵌三反引号 JSON。checker 的 CK-API、
   CK-MMD 与 fence masking 共用 CommonMark 可变长度 fence 扫描器。
7. build 前残留 `iter_N` 只能经 marker 校验后的 workspace 清理 API 恢复;
   protected 或已有匹配 PASS 时不得删除,转 state-inconsistent HELD。
8. 新增 `REJECTED_ORPHAN_PASS_HELD`;登记 `ReleaseNotAllowed` 与
   `AmbiguousQbReference`;ORPHAN_PASS reason 增 `no_free_invocation_slot`。
9. n_a CONVERGENCE 的 changed paths、previous basis、verification id
   逐字段冻结;rebaselined 不得携带 invocation。
10. 普通 `append_event` 禁止写 PASS CONVERGENCE;PASS 只能由 link 原子 API
    产生。HELD reason 必须属于完整白名单,空白 edit spec ref 在 realpath
    前拒绝,SQLite integrity failures 映射为 `StateInconsistent`。

## FIX-1 验收

- BLOCKER:双架构同轮测试必须真实进入两次 build,不得只验证 create_round。
- MAJOR:顶层异常及 argparse 均输出单个固定 schema JSON;进程失败只用
  exit 4/5。previous anchors、round/budget 状态、a0/link 原子性、调用顺序、
  residual copy 恢复均须有正反测试。
- MINOR:unit 作用域查询、truncated 顶层字段、QB ambiguity、双 UNIQUE、
  link_failed 与专用 orphan 错误码同批收口。

完成标准:旧 70 个 campaign 异构测试、全量回归、checker self-test 与
design check、ruff、mypy 全绿;生成 change_44 diff、FIX-1 diff、逐 finding
处置表组成的 delta 评审包。任何未完成项不得以单架构 E2E 全绿抵消。
