# tizen-ci-triage 编译验证闭环 + Gerrit 回提安全门 — 设计文档 v3.1

状态：**Stage 1 已实现并真机验证**（六块子命令 + Cline workflow 单轮闭环全绿）
基线代码：`af4b75e`（main）
前置：patch-suggest / gbs-build / build-workflow 不变；analyzer 阶段2 增加 fingerprint 输出

> **v3.1 修订说明（真机验证后校正，使文档与实现一致）**
> - §3.3 failure_key 去 repo 段；submission_key 改 sha256 哈希
> - §3.4 / §3.6 / §3.8 污染 & dirty check：tree_sha 匹配【不足以】检出"改 tracked
>   未 commit"，必须叠加 `git diff --quiet HEAD --` + `--cached`
> - §5.1 disposable backend 由 git worktree 改为 `cp -a` 完整 copy（gbs 不兼容
>   git worktree 的 .git 指针，报 No source package found）；参数名 / gbs 命令对齐实现
> - build-verify 输出增加 `actual_changed_paths`（供 workflow touched_files）
> - §13 新增真机验证结论与集成 bug 清单
>
> 术语约定："verified worktree""worktree_path""mark_worktree_protected"沿用为
> 【一次性验证目录】的概念名 / 字段名 / 函数名（代码同名）；凡涉及【如何创建该目录】
> 的实现描述，一律为 `cp -a` disposable copy。

## 变更摘要（v2 → v3）
v2 安全架构方向被三家 review 确认正确（从"信任外部 PASS JSON"→"内部 hash 绑定记录"）。
v3 补齐两家收敛指出的落地缺口：
- **verified commit/tree 生命周期**（ChatGPT B1 + Kimi M4）：build 前创建 verification
  commit，record 绑定 commit_sha + tree_sha，不只 patch 文本 hash。
- **state DB 可信模型诚实降级**（ChatGPT B2 + Kimi 2.2，两家都标最关键）：不再声称
  "物理不可伪造"，明确 Stage1 为"强流程约束"，同 OS 用户不抗篡改；真隔离留 Stage2。
- build_mutated_source 检查、failure_class 三层防御、symlink nofollow、build_log
  规范化、apply_failed 独立小循环、回滚语义、Stage1 wall time、偏移硬拒绝等。

---

## 0. 设计原则（第一性原理）

> **"验证过的那个 patch" 与 "要提交的那个 patch" 必须是同一个，在同一个基础上，
> 且这一等价关系由 triage 内部记录（Git object 层 + 状态机）保证。**

两个维度的绑定：
- **内容维度**：验证的 tree/commit == 提交的 tree/commit（§3 hash 绑定）
- **基础维度**：验证的基线 == 提交时的目标分支基线（§8 偏移硬拒绝）

## 0.1 安全边界的诚实声明（v3 关键修订，回应 ChatGPT B2 / Kimi 2.2）
本设计的"约束"分两级，文档不夸大：
```
Stage 1 = 强流程约束（非物理隔离）：
  - verification record / GERRIT_READY 只由官方 triage 子命令写入；
  - gerrit-submit 不信任任何外部传入的 PASS 结果，只认 state DB 内的 record；
  - 官方 Cline workflow 路径上不可绕过。
  ⚠️ 但若 Cline 与 state DB 同 OS 用户运行，Cline 理论上可直接改 DB 文件。
     Stage 1 不声称能抵抗同用户恶意/失控篡改，依赖代码审查 + 测试覆盖防绕过。
  目标：防止 agent 工作流"误绕过"，非防恶意用户。

Stage 2 = 真隔离（若需要）：
  - state DB 由独立 daemon / service account 持有，Cline 无文件级写权限（IPC 请求写）；
  - 或 verification record 带 HMAC 签名，gerrit-submit 校验签名。
```

---

## 1. 目标与非目标
目标：patch 必须 GBS 实际编译通过（且提交内容 == 验证内容、基线一致）才够格上 Gerrit；
失败则按 repairability 分类，可修的才分析→改进→重编译，循环至通过或终止。
非目标：无人值守全自动提交；依赖 CodingSystem；给 patch-suggest 加迭代能力（走 1+3）。

---

## 2. 角色分工
```
确定性 —— triage 子命令（Cline 不可经官方路径绕过）
  build-verify        disposable copy(cp -a) + apply + commit + gbs build + 污染检查 + 写 record
  check-convergence   baseline/上轮 vs 本轮（fingerprint）
  gerrit-submit       只收 verification_id，重算并 Git-object 层匹配，偏移硬拒绝，默认 dry-run
  failure-classify    （build-verify 内部）三层防御判 failure_class + repair_allowed
智能 —— Cline：改 edit_spec；不能写 status/record
编排 —— .clinerules/workflows/repair-verify-submit.md
不变 —— gbs-build / gbs-patch-suggest / build-workflow / formatter
       analyzer：Stage2 增加 diagnostic_fingerprint
```

---

## 3. 物理/流程安全门核心（v3）

### 3.1 verification record（回应 ChatGPT B1 + Kimi M4：绑定 Git object 层）
build-verify 编译 **PASS** 时写入 state DB（append-only，Cline 无官方写权限）：
```json
{
  "verification_id": "<uuid>",
  "result": "PASS",
  "timestamp": "<iso8601>",
  "failure_key": "<§3.3>",
  "base_commit": "<src_clean_ref, 验证基线>",
  "verified_commit_sha": "<build-verify 创建的验证 commit, §3.6>",
  "verified_tree_sha": "<git write-tree 的 tree hash>",
  "canonical_diff_sha256": "<规范化 diff hash>",
  "patch_sha256": "<累积 patch 文本 hash, 仅报告用>",
  "edit_spec_sha256": "...",
  "project": "platform/...", "branch": "tizen",
  "spec_name": "...", "arch": "standard-aarch64",
  "gbs_conf_sha256": "...",
  "build_log_sha256": "<规范化后 hash, §3.7>",
  "worktree_path": "<绝对路径, 仅审计, 不参与跨机校验>",
  "command_line": "..."
}
```
安全校验绑定 **verified_commit_sha / verified_tree_sha / canonical_diff_sha256**
（Git object 层，稳定），而非仅 patch 文本 hash（patch_sha256 受 diff 格式影响，仅报告）。

### 3.2 只有 build-verify 能写 GERRIT_READY（回应 B2，见 0.1 边界声明）
```
status=GERRIT_READY + verification record 只由 build-verify 在 PASS 时写。
Cline 只能写 edit_spec（受 §4.3 校验）。
gerrit-submit 只接受 status==GERRIT_READY 且携 verification_id 的单元。
（此约束在 Stage1 为强流程约束，非物理隔离，见 0.1）
```

### 3.3 双层 key（回应 M4，真机后修正）
failure_key = ci_system/build_id/project/branch/arch/spec_name/base_commit
  （已去掉 repo 段，project 已含 repo 信息，避免冗余）
submission_key = sha256(failure_key + ":" + verified_tree_sha)
  （真机后修正：原明文拼接 → sha256 哈希，防止 key 过长 + 隐含校验）

### 3.4 gerrit-submit 硬校验（回应 B1/B2/M5 + ChatGPT B3 偏移）
```
gerrit-submit --verification-id <id>：
  1. 从 state DB 读该 id 的 PASS record（不信任外部传入结果）
     不存在 → record_not_found
  1a. verification_id 绑定校验：
      row = get_latest_status_row(record.failure_key)
      必须 row.status == GERRIT_READY 且 row.verification_id == 输入 id
      否则 → rejected_not_ready（reason 区分 not_gerrit_ready /
             verification_id_superseded；防提交同 failure_key 的旧 record）
  2. 定位 verified worktree / verified_commit_sha
     不存在 → rejected_worktree_missing（不 fallback patch 文件）
  3. 重算当前提交内容的 tree_sha / canonical_diff_sha256
  4. Git-object 层严格匹配：verified_tree_sha / verified_commit_sha /
     base_commit / project / branch / spec / arch / gbs_conf_sha256
     任一不符 → rejected_verification_mismatch
  5. 偏移校验（§8）：目标分支 HEAD == base_commit ?
       dry-run：偏移 → 告警，仍输出命令
       submit ：偏移 → rejected_stale_verification（硬拒绝，要求 rebase+重验，§8）
  6. 幂等（submission_key + Stage2 Gerrit topic 查重）
  7. 从 verified worktree 的 verified_commit_sha 提交，提交前 dirty check：
     git diff --quiet HEAD --  （无 tracked 未提交改动）
     git diff --cached --quiet （无 staged 改动）
     任一脏 → rejected_worktree_dirty
     （而非拿 patch 文件重 apply；tree_sha 匹配 + dirty check 双层，
      见 §3.8 的检查方式修正）
  8. 默认 dry-run；仅 submit_mode=submit 才真提（Stage2）
```

### 3.6 verification commit 生命周期（v3 新增，回应 ChatGPT B1 方案A + Kimi E2）
build-verify 在 **gbs build 之前**创建验证 commit（解决"验证的是 diff、提交的是 commit"缝隙）：
```
1. disposable copy（§5.1，cp -a）checkout --detach base_commit
   + reset --hard base_commit + clean -ffdx -e .ci_triage_workdir
2. formatter apply 累积 edit_spec；git diff --check
3. git add -A
4. git commit -m "CI triage repair: <failure_key_short>"  → verified_commit_sha
5. git write-tree（或 rev-parse HEAD^{tree}）→ verified_tree_sha
   （用于 Git-object 匹配；build 后污染判定用 dirty check，非 pre/post tree 对比）
6. gbs build
7. build 后：检查 verified 目录是否被污染（见 §3.8 修正的检查方式）
   git diff --quiet HEAD -- + git diff --cached --quiet
   任一脏 → FAIL(build_mutated_source)，repair_allowed=false
8. PASS → 先 mark_worktree_protected（防 check_disk 误清），再写 verification
   record 绑定 verified_commit_sha / verified_tree_sha + GERRIT_READY
gerrit-submit 直接 push verified_commit_sha（内容即验证内容）。
```

### 3.7 build_log 规范化后 hash（v3 新增，回应 Kimi 2.1）
```
build log 含时间戳 / 绝对路径(/home/abuild/rpmbuild/BUILD/...) / 临时文件名 / 进度条，
裸 hash 跨机不稳。hash 前规范化：strip 时间戳、统一路径前缀、去进度条/随机名。
worktree_path（绝对路径）只作审计，不参与跨机校验。
```

### 3.8 build_mutated_source 检查（v3 新增，回应 ChatGPT M1；真机验证后修正检查方式）
gbs build 可能修改 tracked 源文件（生成代码、就地改写等）。
build 后检查 verified worktree 是否被污染。

⚠️ 检查方式（cross-review + 真机验证的关键修正）：
  ❌ 不能只比 post_build_tree_sha != pre_build_tree_sha。
     tree_sha（HEAD^{tree}）只反映【已 commit】的树；若 gbs 改了 tracked 文件
     但未 commit，HEAD^{tree} 不变、tree_sha 相同，污染会漏检。
  ✅ 必须用 git diff 检测工作区/暂存区的未提交改动：
       git diff --quiet HEAD --   （tracked 工作区无改动）
       git diff --cached --quiet  （无 staged 改动）
     任一非 0（脏）→ FAIL(build_mutated_source)，repair_allowed=false，转人工。

理由：否则"提交的 patch ≠ 实际编译时的源码状态"，破坏第一性原理。
tree_sha 匹配证明"HEAD 是验证过的 commit"；git diff 证明"verified worktree
在 build 后没有被污染"。两者缺一不可。

同一发现也应用于 gerrit-submit 的 dirty check（§3.4 第 7 步）：真机已验证，
改 tracked 文件不 commit → tree_sha 不变，仅 dirty check 能抓。

---

## 4. 编译验证闭环数据流（v3）
```
[baseline]
  original_evidence = analyzer(原始失败 build)   ← 第一轮 previous（B4）
  base_commit = CI 失败 commit（clone 原始状态）
  patch-suggest(v1 context) → Cline 写 edit_spec_v1 → formatter → patch

[VERIFY LOOP — Cline 驱动，iter 从 1，受 wall time 限制 §7.4]
  loop:
    (1) build-verify（§5.1 + §3.6 commit 生命周期 + §3.8 污染检查）
          → PASS: 写 record + GERRIT_READY → 跳出 → [Gerrit 回提]
          → FAIL: failure-classify（§4.2 三层防御）
    (2) FAIL 且 repair_allowed==false → REPAIR_EXHAUSTED(对应子类) → 回滚(§4.4) → 停
    (3) FAIL 且 failure_stage==apply_failed → apply_failed 小循环（§4.5，独立计数）
    (4) FAIL 且 repair_allowed==true（source_repairable）:
          analyzer → new_evidence
          check-convergence(iter=1 用 baseline_evidence; 其后上轮;
            touched_files: iter=1 用 build-verify actual_changed_paths；
              iter>1 用"当前累积 edit_spec 相比上一版的 delta files"，并校验
              delta ⊆ actual_changed_paths（actual_changed_paths 是累积全量，
              多轮直接传全量会把上轮已有文件的新错误误判 regressed）; §7)
            判定顺序 regressed → stalled → advance:
            regressed → REPAIR_EXHAUSTED(regressed) → 回滚 → 停
            stalled   → REPAIR_EXHAUSTED(stalled)   → 停
            advance   → 继续（更新 previous_evidence/edit_spec）
          iter++; iter>MAX_ITER(=3) 或超 wall time/build 数 → 停
          patch-suggest(new_evidence) 重新备 context（不改 skill）
          Cline 改进累积 edit_spec（§6）→ formatter → 回 (1)

[Gerrit 回提 — 仅 GERRIT_READY]
  gerrit-submit --verification-id（§3.4，Stage1 dry-run only）
```

### 4.2 failure_class 三层防御（v3，回应 Kimi C1 + ChatGPT M2）
```
第一层 确定性 denylist（不可覆盖，命中即 repair_allowed=false）：
  -enable-ml-inliner=release 等 toolchain flag、cannot find -lxxx（库缺失）、
  No space left on device（环境）、depsolve/dependency 类、raw_unparsed 等
第二层 启发式分类（analyzer kind + diagnostic_code + message regex → 置信度）
第三层 保守 fallback：
  置信度 < 0.8 → uncertain → repair_allowed=false → 转人工
判 source_repairable 需同时满足：
  analyzer 定位到 source file / source_reachable / source_owned /
  probably_fixable / 非 denylist / 非 uncertain
原则：宁可漏救（转人工），不可错救（Cline 在 toolchain/env 上乱改源码）。
failure_class 取值：source_repairable / source_unreachable / not_applicable /
  build_env / toolchain / dependency / raw_unparsed / build_mutated_source / uncertain
```

### 4.3 edit_spec 边界校验（v3，回应 Kimi C4 + 补充2）
```
apply 前强制（任一不过 → 拒绝，不 apply）：
  - schema 校验（gbs_patch_suggest/edit-spec/v1）
  - 路径安全（关键：先 nofollow 规范化，回应 Kimi C4）：
      · os.path.normpath 规范化（不跟随 symlink）→ 前缀必须在 verified copy 目录内
      · 禁止绝对路径、禁止 ../ 逃逸
      · 逐段检查：路径任一中间段是 symlink 且指向树外 → 拒绝
      · NFC Unicode 归一化；大小写不敏感 FS 上做大小写规范化
  - 路径属于该 package 源码（非构建产物、非 .git 内部）
  - no overlapping edits
  - apply 后 git diff --check
  - Stage2 可选：容器内 apply，源码树 mount 受限
```

### 4.4 回滚语义（v3 新增，回应 Kimi E1）
```
regressed          : 回滚 edit_spec 到上一轮（移除本轮新增），保留 verified copy 供 diff 审查
stalled            : 保留当前 edit_spec 与 verified copy，人可基于当前状态手动调整
unsupported_or_env : 完全停，保留所有 iter_N + evidence 供人查
（所有终止均产出 repair report：各轮 primary/fingerprint、edit_spec 演进、终止原因）
```

### 4.5 apply_failed 独立小循环（v3 新增，回应 ChatGPT M3）
```
apply_failed（edit_spec 格式/行漂移等）：
  - 不跑 GBS，不进 check-convergence
  - 允许 Cline 修 edit_spec，最多 MAX_APPLY_FIX（=2）次
  - 不计入源码 repair iteration（iter）
  - 超 MAX_APPLY_FIX → REPAIR_EXHAUSTED(edit_spec_invalid)
```

---

## 5. 子命令接口契约（v3）

## 5.1 `ci_triage build-verify`
```
输入（参数名以真机验证过的实现为准）：
  --src-clean <只读 baseline 源码>       --base-commit <commit>
  --edit-spec <累积 edit_spec.json>      --gbs-conf <path>
  --package <spec_name>                  --workspace-root <triage-managed 工作区根>
  --baseline-evidence <original_evidence.json>  --output-dir <本轮输出>
  --iter-index <N>                       --state-db <path>
  --build-id <id>  --project <path>  --branch <br>  --arch <arch>
  --wall-timeout <单轮超时, §7.4>
动作：
  1. 在 <workspace-root> 下创建 disposable copy：
     cp -a <src-clean> <workspace-root>/iter_N
     （copy 内含 .ci_triage_workdir marker，防误删用户目录）
     ⚠️ 原设计用 git worktree add，因 gbs 不兼容 git worktree 的 .git 指针文件
        （报 No source package found），真机验证后退回 cp -a copy backend，
        保留 disposable 语义。
  2. git -C iter_N checkout --detach <base_commit>
     && git -C iter_N reset --hard <base_commit>
     && git -C iter_N clean -ffdx -e .ci_triage_workdir
  3. 校验 edit_spec 边界（§4.3）；不过 → FAIL(apply_failed)
  4. formatter apply（output_patch 用绝对路径，避免 git -C 后相对路径 exit 128）
     → git diff --check
  5. git add -A && git commit → verified_commit_sha
     rev-parse HEAD^{tree} → verified_tree_sha
     （verified_tree_sha 用于 Git-object 匹配；build 后污染判定用 dirty check，
      不用 pre/post tree_sha 对比，见 §3.8）
  6. gbs build（受 wall-timeout）：
     gbs -c <gbs-conf> build -A <arch去standard-前缀> --include-all
     （cwd = iter_N copy 根定位包；不用 --package。arch 如 standard-aarch64 → aarch64）
  7. build 后污染检查（§3.8 修正的方式）：
     git diff --quiet HEAD -- + git diff --cached --quiet
     任一脏 → FAIL(build_mutated_source)，repair_allowed=false
  8. PASS：规范化 build_log 后算 hash（§3.7）；先 mark_worktree_protected（防
           check_disk 误清），再写 verification record（§3.1）+ GERRIT_READY
     FAIL：failure-classify 三层防御（§4.2）→ failure_class + repair_allowed
           （repair_allowed 时 analyzer 产 new_evidence）
输出（JSON）：
  PASS: { result:PASS, verification_id, verified_commit_sha, verified_tree_sha,
          actual_changed_paths, ... }
  FAIL: { result:FAIL, failure_stage, failure_class, repair_allowed, evidence,
          actual_changed_paths }
硬约束：只在 disposable copy 内操作；src_clean 只读；每轮 checkout+reset+clean；
       record/GERRIT_READY 只本命令写；build 后源码污染即 FAIL；
       PASS worktree 受 .ci_triage_protected 保护，check_disk 不清。
```

### 5.2 `ci_triage check-convergence`
```
输入：--current-evidence  --previous-evidence（iter=1 用 baseline_evidence, B4）
      --touched-files（本轮改动文件；缺失则永不判 regressed，fail-safe）
      --output
输出：{ verdict: advance|stalled|regressed, confidence, reason,
        current_fingerprint, previous_fingerprint, error_count, ... }
判据 §7（fingerprint；Stage1 用近似 fingerprint，偏向 advance, C5）
  regressed：基于 error_clusters 差集，覆盖"新 source cluster"和"已有 cluster
             扩展到 touched file"；touched_files 缺失 → 永不 regressed；
             不靠 error_count/severity 单独判
iter=1：previous=baseline_evidence；仅 baseline 缺失才允许 previous=null 且只进一轮
```

### 5.3 `ci_triage gerrit-submit`
```
输入：--verification-id <id>（只收 id）  --config：
      gerrit_host/port/user/git_ssh_command、submit_target（可配置：
      refs/for/<b> | %wip | refs/drafts/<b> | refs/heads/sandbox/<user>/<x>）、
      submit_mode（dry-run 默认 | submit）
动作：§3.4（读 record → verification_id 绑定 → 定位 copy → Git-object 匹配 +
       dirty check 两层 → 偏移校验 → 幂等 → 默认 dry-run）
输出：{ action, verification_id, submission_key, submit_target, submit_mode,
        command, command_argv, warnings, provenance }
  action ∈ { dry_run, skipped_duplicate, record_not_found, rejected_not_ready,
    rejected_verification_mismatch, rejected_worktree_dirty,
    rejected_worktree_missing, rejected_submit_not_enabled }
  （Stage2 submit 模式将新增 rejected_stale_verification / submitted）
物理底线（不可配置）：
  A. 只提验证过内容（verified_commit_sha/tree_sha 匹配 + dirty check）
  B. 默认 dry-run；Stage1 submit 模式无 push 代码路径 → rejected_submit_not_enabled
  C. 幂等（submission_key，dry-run 只查不写）
  D. 偏移硬拒绝（submit 模式，§8，无 --allow-stale 逃生门）
  E. verification_id 绑定：latest GERRIT_READY 的 verification_id == 输入 id
  F. worktree 缺失不 fallback patch 文件
  G. dry-run 后 verified copy 保留 .ci_triage_protected，显式 release-worktree 才解除
```

---

## 6. 累积 edit_spec 管理（同 v2）
每轮从 base_commit 建干净 disposable copy（cp -a）、checkout+reset+clean、一次性
apply 累积 edit_spec。同文件错误反复 → 替换该文件 edit（改进版）；新文件 → 新增。
始终是完整快照，可重现可审查。

---

## 7. 收敛判断（v3）
### 7.1 diagnostic_fingerprint
```
Stage2（analyzer 原生）：hash(normalized_path, normalized_message, diagnostic_code,
  kind, symbol/function, source_anchor/line_window)
Stage1（近似，不改 analyzer）：
  identity   = normalized_file + diagnostic_code + anchor
  attributes = kind + message
  —— 用锚点非裸行号（patch 后行号变）；kind 不进 identity，避免
     werror→compile_error 包装变化导致同一诊断被误判（与 §7.3 一致）
```
### 7.2 repairability 分类（非 severity 序，M2/B5）
不用 raw>link>compile>werror 排序。werror→compile/link 不必然 regression。
### 7.3 verdict（真机后修正：与 §5.2 实现一致）
```
判定顺序（regressed 先于 stalled，防 primary+error_count 巧合相同掩盖换血）：
  previous_missing → regressed → stalled → advance

fingerprint（primary_error，用于 stalled/advance）：
  identity   = normalized_file + diagnostic_code + anchor（§7.1）
  attributes = kind + message（kind 不进 identity，防 werror→compile_error 误判）

error_clusters（用于 regressed）：
  cluster_type_key       = (kind, sorted(diagnostic_kinds), diagnostic_code?)
  cluster_occurrence_key = cluster_type_key + sorted(normalized_files)

error_count：diagnostic_kinds 含 "error"/"werror" 的 cluster.count 求和
  （werror 的 kind 是 source_warning_option，但 -Werror 阻塞编译，计入）

stalled  : primary fingerprint identity 相同 且 error_count 相同
           Stage1 近似 fp 偏向 advance（C5）：仅 identity 完全相同 + error_count
           不变才判 stalled；模糊相似 → advance（多给一轮）
regressed: 遍历 current source-level cluster：
             previous 无同 type → added = current_files（全新 cluster）
             previous 有同 type → added = current_files - previous_files（扩展）
             added ∩ touched_files 且 source-level → regressed
           touched_files 缺失 → 永不 regressed（fail-safe）
           不靠 error_count / kind severity 单独判；error_count 暴涨仅标
           regression_suspected（进 reason，不改 verdict）
advance  : fingerprint 变化（含 werror→compile_error）且非 regressed
iter=1   : previous=baseline_evidence（B4）
```
### 7.4 wall time（v3 新增 Stage1，回应 Kimi E3）
```
单轮 build 超时（默认 45min）→ FAIL(build_timeout)，repair_allowed=false
总流程超时（默认 2h）→ REPAIR_EXHAUSTED(wall_time)
（Stage2 再加 max_total_builds 等更细的资源上限）
```

---

## 8. Gerrit 回提安全门 + 偏移策略（v3）
```
可配置：gerrit_host/port/user/git_ssh_command、submit_target、submit_mode
物理底线（不可配置）：
  A. 只提验证过内容（verified_commit_sha/tree_sha 匹配）
  B. 默认 dry-run
  C. 幂等（submission_key 本地 + Stage2 Gerrit topic 查重）
  D. 偏移硬拒绝（submit 模式）

偏移策略（Tizen 分支前进不频繁 → 硬拒绝代价可接受，采纳 ChatGPT B3）：
  检测目标分支 HEAD 是否 == base_commit：
    dry-run：偏移 → 告警（"验证基线已偏移，rebase 后重跑 build-verify"）
    submit ：偏移 → rejected_stale_verification（硬拒绝）
             → 要求 rebase 到当前 HEAD → 重新 build-verify（验证新基线+patch）→ 才提
    未偏移 → 正常
  ⚠️ 不提供 --allow-stale-submit 逃生门（Tizen 偏移偶发，硬拒绝干净，
     少一个可被误用绕过安全门的开关）。

Gerrit 元数据（Stage2，M4/M5）：
  Topic: ci-triage/<failure_key_sha12>   （短 hash，非完整 key）
  Trailer: CI-Triage-Failure-Key / CI-Triage-Verification / CI-Triage-Tree-SHA
  submit 前查同 topic open/merged change（跨机器幂等）
  网络查询失败 → fail-safe：不提，转人工（宁可不提不可重复提，Kimi C6）
追溯/撤回：record 存 failure_key+target+时间+源 build+build_log；
  build log 与 record 一并归档到 output-dir/audit/，留到 change merged/abandoned（E2）。
  dry-run 天然可撤；submit 后经 Gerrit abandon（人工）。
```

---

## 9. 状态机扩展 + disposable copy / DB 管理（v3）
```
新增状态：BUILD_VERIFYING / GERRIT_READY / REPAIR_EXHAUSTED（子类：max_iter/
  stalled/regressed/unsupported_or_env/edit_spec_invalid/wall_time/build_mutated_source）
  / GERRIT_SUBMITTED / GERRIT_DRY_RUN
state DB（Kimi C2）：Stage1 SQLite + WAL + append-only（只 insert 不 update，
  audit trail 完整）。写入仅经 triage 子命令（强流程约束，见 0.1）。
disposable copy 清理（Kimi C3）：
  - PASS 轮：保留至 gerrit-submit 完成（.ci_triage_protected 保护，check_disk 不清）
  - 最近 3 轮 FAIL：保留供审查
  - 更旧的 unprotected copy：build-verify 前检查磁盘，低于阈值按年龄清最旧 iter
  - 磁盘不足且只剩 protected：不清 protected，warning:disk_low_protected_worktrees_skipped
    （宁可 build-verify 磁盘不足失败，也不清 GERRIT_READY 的 verified copy）
  - clean 前把 build log/evidence 拷到 output-dir（避免排障无迹，Kimi 2.3）
protected 标记 .ci_triage_protected：内容含 verification_id / failure_key /
  protected_reason / protected_at；对 git status / dirty check 透明（private exclude）；
  build-verify PASS 时先 mark 再写 record；release-worktree 显式解除。
安全校验（S1-1）：create（cp -a → checkout/reset/clean → 写 .ci_triage_workdir marker）；
  cleanup 三重校验（marker 存在 / workspace_root 匹配 / 路径在内）后 shutil.rmtree，
  任一不过 raise WorkspaceViolation（防误删用户目录）。
```

---

## 10. Cline workflow 剧本（.clinerules/workflows/repair-verify-submit.md）
```
1. 前提：triage 已产 v1 context(source_context_available) + 干净源码。否则不进本 workflow。
2. 依 v1 context 写累积 edit_spec；formatter 出 patch。
3. 循环(iter≤3, 受 wall time)：
   a. 调 build-verify → 读结果（Cline 不能自行断言 PASS，以子命令返回为准）
   b. PASS → 步骤 5
   c. FAIL & repair_allowed==false → 停，报告，转人工（不改源码）
   d. FAIL & apply_failed → 修 edit_spec（≤MAX_APPLY_FIX），不计 iter
   e. FAIL & repair_allowed==true → check-convergence
        regressed/stalled → 停转人工；advance → 改进 edit_spec → formatter → 回 a
   f. iter>3 或超时 → 停转人工
4. GERRIT_READY → gerrit-submit --verification-id（默认 dry-run）
   → 展示提交命令 + patch 摘要 + 溯源 + 验证基线 commit → 人 review
   → 人确认 + submit_mode=submit（Stage2）才真提
5. 纪律为 UX 兜底；真正安全由 §3/§8 机制保证（0.1 声明的边界内）。
```

---

## 11. 分两阶段实现（Stage1 已实现并真机验证）

### Stage 1 — 已实现并真机验证的 dry-run 安全门（本文档范围）
```
P0（全部已实现 + 真机验证，见 §13）：
  - state DB（SQLite+WAL+append-only）+ verification record + Git-object 层 hash 绑定
  - verification commit 生命周期（build 前 commit，绑 commit_sha/tree_sha）（B1）
  - 只有 build-verify 写 GERRIT_READY；安全边界诚实声明（0.1）（B2）
  - disposable copy（cp -a，gbs 不兼容 git worktree）+ checkout --detach +
    reset --hard + clean -ffdx + marker（B3；真机后由 worktree 退回 copy）
  - build_mutated_source 检查：git diff --quiet HEAD -- + --cached（M1；真机后修正，
    非 tree_sha 对比）
  - build-verify 输出 actual_changed_paths（供 workflow touched_files）
  - failure_class 三层防御 + uncertain 默认 repair_allowed=false（C1/B5）
  - edit_spec 边界校验（symlink nofollow + NFC + 大小写）（C4/补充2）
  - baseline evidence 做第一轮 previous（B4）
  - apply_failed 独立小循环（M3）
  - 回滚语义（E1）
  - build_log 规范化后 hash（Kimi 2.1）
  - Stage1 wall time（单轮 45min / 总 2h）（E3）
  - gerrit-submit：verification_id 绑定 + Git-object 匹配 + dirty check 两层 +
    dry-run only；Stage1 submit 模式【无 push 代码路径】→ rejected_submit_not_enabled
    （Stage2 需新增真 push 路径，不是只改默认值）
  - 收敛：近似 fingerprint（偏向 advance，C5）；verdict 顺序 regressed 先于 stalled；
    regressed 覆盖"新 cluster"+"已有 cluster 扩展到 touched"；基于 error_clusters
  - disposable copy 清理 + 磁盘预警 + protected 保护（C3）
```

### Stage 2 — 真提交 + 跨机器 + 质量增强
```
  - submit_mode=submit 真提交
  - 偏移硬拒绝在 submit 模式生效（§8；dry-run 阶段已有告警）
  - Gerrit topic/trailer 跨机器查重 + fail-safe（M4/M5/C6）
  - state DB 真隔离（daemon/service account）或 record HMAC 签名（0.1）
  - analyzer 原生 diagnostic_fingerprint（M1/C5）
  - 时效校验完整化；max_total_builds 等资源上限
  - 可选：容器内 apply（路径逃逸终极防护，C4）
```

---

## 12. Stage 1 归档判断
三模型（ChatGPT 两轮 + Kimi 一轮）收敛的安全架构已实现并真机验证。
两家最强共识的三条已全部落地：
1. verified commit/tree 生命周期（§3.6）—— 实现 + 真机 PASS
2. state DB 可信模型诚实降级（§0.1）—— 实现（Stage2 真隔离）
3. 偏移硬拒绝（§8，submit 模式）—— dry-run 阶段告警已验证；submit 硬拒绝待 Stage2

**本文档 Stage 1 部分可作为已实现归档版冻结。**
Stage 2（真提交）在 Stage 1 dry-run 观察稳定后另行设计/实现（真 push 需新增
代码路径，非只改默认值）。

状态：
```
Stage1 design doc: freeze / archive OK
Stage2: future design
```

---

## 13. 真机验证结论（Stage 1，v3.1 新增）

### 13.1 已验证（测试环境 Ubuntu + gbs，build 1095003 / inference-engine-interface）
- build-verify 真机 PASS：删 OutputMetadata.h 的 decodingType 未使用私有字段 →
  gbs 真实编译成功（Total succeeded built packages: 1），写 record + GERRIT_READY +
  protected marker；verified_tree_sha 可重现。这是"删死字段能编译通过"第一次由
  真实 gbs 证实（此前均为 git apply --check 级推断）。
- 安全门三态：放行（dry_run + push 命令）/ 拒绝 dirty（改 tracked 不 commit，
  tree_sha 不变但 dirty check 抓住）/ 拒绝 submit（rejected_submit_not_enabled，无 push）。
- convergence 真机 5 场景（真实 error_clusters evidence）：stalled / advance /
  regressed(全新 cluster) / advance(touched 缺失 fail-safe) / regressed(扩展) 全对；
  构建路径 /home/abuild/rpmbuild/BUILD/<pkg>-<ver>/... 成功归一化对齐相对 touched。
- Cline workflow 单轮整体闭环：build-verify PASS → gerrit-submit dry-run，全程读
  工具 JSON 字段决策，未脑补 PASS / 未构造 verification_id / 未执行 command_argv。
- 真实 git repo 集成测试（tests/integration/，只 mock gbs）：copy / apply 绝对路径 /
  actual_changed / 污染检测（改 tracked 触发）/ gbs 命令形态 / protected 透明 /
  dirty / mismatch。

### 13.2 真机排掉的集成 bug（mock 单测测不出）
1. runner 循环导入（入口 import 链）
2. build-verify CLI 入口未接线（main(argv=None) 分发失效）→ argv 兜底 sys.argv[1:]
3. git apply 相对路径 exit 128（git -C 后路径基准）→ output_patch.resolve()
4. gbs 不兼容 git worktree（.git 指针，No source package found）→ 退回 cp -a copy
5. gbs 命令缺 -A 架构（depsolve 失败）→ gbs -c conf build -A <arch> --include-all
6. （流程）review 后未 push 就去测试环境验证到旧代码 → 固化 push→pull→确认 commit 纪律
共同根因：单测 mock 了 subprocess/git，把真实环境行为也 mock 掉。
→ 已补真实 git repo 集成测试（只 mock gbs），转为秒级回归防线。

### 13.3 Commit 序列（origin/main）
```
69f0323 S1-2 state DB            810d456 build-verify(S1-1+S1-3+S1-6)
579a9aa 入口链修复               0f6b74d apply 相对路径修复
4562259 worktree→copy + gbs 命令  59eec29 S1-4 check-convergence
7d0dd95 S1-5 gerrit-submit+回改   c83637e submission_key hash
ea9efa9 actual_changed_paths      c1bec89 Cline workflow
4795f26 真实 git 集成测试         a955980 Stage1 validation notes
```

### 13.4 Backlog
- P1：failure-classify 加 depsolve → dependency 规则（现走 raw_unparsed）
- P2：src 分层——triage clone 到 src/<package>/，支持一个 build id 多失败包
- P2：设计文档归档进 docs
- Stage2：真提交 + 跨机器 topic 去重 + state DB 隔离 + 多轮 workflow 真机验证

---

## 附：v2 → v3 修订对照
```
ChatGPT-B1 commit 生命周期        → §3.6 build 前 verification commit + tree/commit 绑定
ChatGPT-B2 state DB 不可伪造模糊  → §0.1 诚实降级（Stage1 强流程约束 / Stage2 真隔离）
ChatGPT-B3 偏移 submit 硬拒绝     → §8 硬拒绝(submit)/告警(dry-run)，无逃生门（Tizen 特性）
ChatGPT-M1 build 污染 tracked 源  → §3.8 build_mutated_source 检查
ChatGPT-M3 apply_failed 分歧      → §4.5 独立小循环 MAX_APPLY_FIX=2
ChatGPT-M4 patch hash 脆          → §3.1 绑 verified_tree_sha/commit_sha
ChatGPT-M5 topic 用完整 key       → §8 failure_key_sha12 短 hash + trailer
Kimi-2.1  build_log hash 噪声      → §3.7 规范化后 hash
Kimi-C1   failure_class 分类       → §4.2 三层防御 + uncertain 默认拒绝
Kimi-C2   state DB 并发            → §9 SQLite+WAL+append-only
Kimi-C3   worktree 清理            → §9 保留/清理策略 + 磁盘预警
Kimi-C4   symlink 逃逸             → §4.3 nofollow 规范化 + NFC + 大小写
Kimi-C5   近似 fingerprint 误判    → §7.3 偏向 advance，仅 100% 判 stalled
Kimi-C6   topic 查重网络失败       → §8 fail-safe 不提转人工
Kimi-C7   偏移策略                 → §8 已按 Tizen 定硬拒绝（与 ChatGPT-B3 一致）
Kimi-E1   回滚语义                 → §4.4 分类回滚
Kimi-E2   审计链                   → §8 build log + record 归档 audit/
Kimi-E3   Stage1 wall time         → §7.4 单轮/总流程超时
```
