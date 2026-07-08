# Stage 1 Validation Notes — 编译验证闭环 + Gerrit 回提安全门

本文记录 tizen-ci-triage 编译验证闭环 Stage1 的验证结果与边界,防止后续工作
(Stage2 / 其他任务) 混淆已验证的范围。

## 一句话总结

Stage1 把"AI 建议的 patch"变成"只有真实 GBS 编译通过的 patch 才能 dry-run 出
Gerrit 提交命令",安全门由 triage 子命令的物理机制保证(不依赖 AI 自觉),
并已通过真机三态验证 + Cline 驱动的单轮整体闭环。

## 状态

```
Stage1 code-level gate:                DONE
Stage1 real-machine smoke gate:        DONE
Stage1 safety gate three-state:        DONE
Stage1 convergence real-evidence:      DONE (5 场景)
Stage1 Cline workflow single-round:    DONE
Full production hardening:             BACKLOG / Stage2+
```

## 已验证(Validated)

### 六块子命令(单独,代码 + 逐行 review + cross-review)
- S1-1 workspace:一次性验证目录 = 完整 copy(cp -a,保留 .git);gbs 不兼容
  git worktree(No source package found),退回 copy 方案;marker 三重校验 cleanup;
  PASS worktree 保护(.ci_triage_protected)不被 check_disk 误清。
- S1-2 state DB:append-only;GERRIT_READY 只能由 write_pass_record 写;
  verification record 绑定 verified_commit_sha / verified_tree_sha;
  submission_key = sha256(failure_key : verified_tree_sha),不暴露明文。
- S1-3 build-verify:copy → apply edit_spec → verification commit → gbs 编译 →
  build_mutated_source 检查 → PASS 写 record + GERRIT_READY。
- S1-4 check-convergence:advance / stalled / regressed;verdict 顺序 regressed
  先于 stalled;regressed 覆盖"全新 cluster"和"已有 cluster 扩展";touched_files
  缺失 fail-safe;基于 analyzer error_clusters。
- S1-5 gerrit-submit:只信 state DB record;commit/tree 匹配 + dirty check 两层;
  verification_id 绑定;默认 dry-run;submit-mode 无 push 路径。
- S1-6 failure-classify:denylist 短路(不可翻转) + 启发式 + uncertain<0.8 拒绝。

### 真机验证(测试环境:liushanshan@riscv-Alienware-Aurora-R16, Ubuntu + gbs)
用 build 1095003 / inference-engine-interface(删 OutputMetadata.h 的 decodingType
未使用私有字段,消除 -Werror,-Wunused-private-field):

- build-verify 真机 PASS:gbs 真实编译成功(Total succeeded built packages: 1),
  写出 verification record + GERRIT_READY + protected marker。verified_tree_sha
  可重现(d865c368...)。这是"删死字段能编译通过"第一次由真实 gbs 证实
  (此前均为 git apply --check 级推断)。
- 安全门三态:
  - 放行:正常 verified worktree → action=dry_run + 正确 git push 命令。
  - 拒绝(dirty):验证后改 tracked 文件不 commit(tree_sha 不变)→
    rejected_worktree_dirty。证明只比 tree_sha 会漏,dirty check 有效。
  - 拒绝(submit):--submit-mode submit → rejected_submit_not_enabled,无 push。
  - 偏移查不到:target_head_unknown 降级 warning,不崩。
- convergence 真机(真实 error_clusters evidence,5 场景):
  stalled / advance / regressed(全新 cluster) / advance(touched 缺失 fail-safe) /
  regressed(已有 cluster 扩展) 全部判对。关键:构建路径
  /home/abuild/rpmbuild/BUILD/<pkg>-<ver>/... 成功归一化对齐相对 touched files。
- Cline workflow 单轮整体闭环:Cline 读 .clinerules/workflows/repair-verify-submit.md,
  步骤 A build-verify → result=PASS + verification_id(25bbda6f...) →
  步骤 D gerrit-submit dry-run → action=dry_run。全程决策来自工具 JSON 字段,
  Cline 未脑补 PASS、未构造 verification_id、未执行 command_argv。

## 边界(Not in Stage1)

- 真实 Gerrit push(Stage1 只 dry-run 生成命令,人手动执行)
- 跨机器 Gerrit topic 去重(Stage1 submission_key 幂等仅本地 state DB)
- service-level 的 state DB 真隔离 / HMAC 签名(Stage1 是强流程约束,
  同 OS 用户不抗篡改;见 v3 §0.1)
- 多包源码分层(一个 build id 多个失败包;当前 src 扁平)
- 多轮 workflow 的真机验证(convergence 决策逻辑已单独真机验证 5 场景,
  但"FAIL → 改进 → 再 build-verify"的完整多轮循环尚未用真实多轮场景包跑通)

## 真机排掉的集成 bug(mock 单测测不出,真机才暴露)

1. runner.py 循环导入(入口 import 链)→ 修入口。
2. build-verify CLI 入口未接线(main(argv=None) 分发失效)→ argv 兜底 sys.argv[1:]
   + 补 test_ci_triage_entrypoints。
3. git apply 相对路径 exit 128(git -C worktree 后相对 patch 路径基准变)→
   output_patch.resolve()。
4. gbs 不兼容 git worktree(.git 是 gitdir 指针文件)→ 退回 cp -a 完整 copy。
5. gbs 命令缺 -A 架构(depsolve 失败)→ 对齐 gbs -c conf build -A <arch> --include-all。
6. (流程)review 后未 push 就去测试环境验证 → 验证到旧代码。纠正:开发环境
   review → push → 测试环境 pull 确认 commit → 才真机验证。

共同根因:单测 mock 了 subprocess / import / git,把真实环境的路径、进程、
git 行为也 mock 掉了。→ backlog:补真实 git repo 集成测试。

## Commit 列表(origin/main)

```
69f0323 S1-2 state DB
810d456 build-verify (S1-1 + S1-3 + S1-6)
579a9aa 入口链修复
0f6b74d apply 相对路径修复
4562259 worktree → copy + gbs 命令对齐
59eec29 S1-4 check-convergence
7d0dd95 S1-5 gerrit-submit + get_latest_status_row + protected marker
c83637e submission_key 改 sha256 hash
ea9efa9 build-verify 输出 actual_changed_paths
<workflow> .clinerules/workflows/repair-verify-submit.md
```

## Backlog

P0:
- build-verify 真实 git repo 集成测试(补 mock 盲区,防 refactor 改坏安全门)。
- 上面 6 个集成 bug 作为回归测试设计输入。

P1:
- 设计文档 v3 §3.8 回填:HEAD^{tree} 只证明 HEAD commit 的 tree,不能证明 worktree
  无未提交修改;必须额外 git diff --quiet HEAD -- 和 git diff --cached --quiet。
- failure-classify 加 depsolve → dependency 规则(现在 "nothing provides" 走
  raw_unparsed)。

P2:
- src 分层:triage clone 到 src/<package>/,支持一个 build id 多失败包。
- 设计文档 v1/v2/v3 归档进 docs。

远期(Stage2):
- 真实 Gerrit push + 写 submissions record。
- 跨机器 Gerrit topic 去重。
- state DB 真隔离 / 签名。
- 多轮 workflow 真机验证(需一个第一轮修不好、需多轮的真实场景包)。
