# Repair-Verify-Submit Workflow (Cline 驱动的编译验证闭环)

本 workflow 驱动 tizen-ci-triage 的编译验证闭环:对一个编译失败的包,迭代地
生成/改进 patch,每轮用 GBS 实际编译验证,只有真的编译通过的 patch 才准备提交
到 Gerrit(Stage1 仅 dry-run,生成提交命令供人 review)。

## 第一性原理(必读,决定本 workflow 的一切行为)

> **所有 gate 判断以确定性工具的 JSON 返回为准,Cline 不得基于自身推理断言结果。**

Cline 是执行者,不是裁判。以下判断【只能】来自工具的 JSON 字段,【不能】来自
Cline 的主观判断:
- "编译过了吗" → 只看 `build-verify` 返回的 `result` 字段(PASS/FAIL)
- "这个失败能修吗" → 只看 `build-verify` 返回的 `repair_allowed` 字段
- "该继续下一轮吗" → 只看 `check-convergence` 返回的 `verdict` 字段
- "能提交了吗" → 只看 `gerrit-submit` 返回的 `action` 字段

⚠️ Cline 禁止的行为(这些会破坏物理安全门):
- ❌ 因为"我改的 patch 看起来对"就跳过 build-verify,直接认为 PASS
- ❌ 因为"这个错误看起来是新的"就自己断言 regressed,跳过 check-convergence
- ❌ 因为"应该收敛了"就提前停止
- ❌ 因为"可以提交了"就试图绕过 gerrit-submit 的 state DB 校验

即使 Cline 试图绕过,底层工具有物理兜底:
- `gerrit-submit` 只信任 state DB 的 verification record + verification_id 绑定,
  Cline 无法伪造 GERRIT_READY;想跳过 build-verify 直接 submit → rejected_not_ready
- `GERRIT_READY` 状态只能由 build-verify 在真实编译 PASS 时写入
但 workflow 剧本仍必须显式锚定工具返回——不依赖"Cline 自觉",而是每步写死。

### 文件依赖链(物理保证 Cline 无法跳步)

每个工具都把结果写到固定路径的 JSON 文件,下一步的输入【只能】从上一步的
输出文件读取:

```
build-verify   --output-dir → <out>/build_verify_result.json
  ├─ result / repair_allowed → 决定走 PASS/停止/继续
  ├─ verification_id         → 步骤 D 的 gerrit-submit 输入(只能从这读)
  ├─ actual_changed_paths    → iter=1 的 touched_files;iter>1 作为 delta 的 guard
  └─ evidence                → 步骤 B 的 current-evidence 输入
check-convergence --output → conv_out.json
  └─ verdict                 → 决定继续/停止
gerrit-submit  --output → submit_out.json
  └─ action                  → 成功/拒绝
```

Cline 若跳过某个工具调用,就【拿不到】下一步需要的字段(文件不存在/字段缺失),
物理上无法继续。这不是纪律要求,是数据流的硬约束:
- verification_id、verdict 必须从工具输出文件获得,Cline 无处"构造";
- touched_files 在 iter=1 来自 build-verify 的 actual_changed_paths,在 iter>1 由
  previous_edit_spec → current_edit_spec 机械计算(并用 actual_changed_paths 校验),
  不得凭空构造(详见步骤 B)。

## 确定性工具 vs Cline 决策(边界表)

| 环节 | 谁负责 | 依据 |
|------|--------|------|
| 编译验证(过没过) | build-verify 工具 | `result` 字段 |
| 失败能否修复 | build-verify 工具 | `repair_allowed` 字段 |
| 是否收敛(继续/停) | check-convergence 工具 | `verdict` 字段 |
| 提交 gate | gerrit-submit 工具 | `action` 字段 + state DB |
| **看编译错误、写/改进 edit_spec** | **Cline** | context + build log(智能决策) |

Cline 的智能决策【只有一处】:根据 patch-suggest 的 context + 编译错误,
写或改进累积 edit_spec。其余全是调工具 + 读 JSON 字段。

## 前提检查(不满足则不进入本 workflow)

1. 已有一个 triage 单 build 产出的失败包,状态为 `source_context_available`
   (patch-suggest 已产出 context)。若状态不是 source_context_available → 不进入。
2. 已有该包的干净源码(clone 的 src)、baseline evidence(原始失败的 evidence)。
3. 环境已配置:gbs.conf 路径、state DB 路径、PYTHONPATH(四个 skill + ci_triage)。
4. Python 解释器:本文命令写作 `python -m ci_triage ...`,但不同机器的解释器名
   可能是 `python` 或 `python3`。运行前先确认环境中可用的名字(如
   `command -v python || command -v python3`),用可用的那个;若 `-m ci_triage`
   报 `No module named ci_triage`,先 export PYTHONPATH(见第 3 点)。

## 循环剧本(iter = 1..MAX_ITER,MAX_ITER=3)

累积 edit_spec 从空开始;每轮 build-verify 内部会从干净源码 copy 重打累积
edit_spec(Cline 不需手动管理源码状态,只维护 edit_spec 内容)。

```
iter = 1
累积 edit_spec = 依据 patch-suggest 的 v1 context 生成的初版

LOOP:
  ── 步骤 A:编译验证(确定性工具)──
  调 build-verify:
    python -m ci_triage build-verify \
      --src-clean <src> --base-commit <commit> --edit-spec <累积 edit_spec> \
      --gbs-conf <conf> --package <pkg> --workspace-root <ws> \
      --output-dir <out> --baseline-evidence <baseline> --iter-index <iter> \
      --state-db <db> --build-id <id> --project <proj> --branch <br> --arch <arch>
  ⭐ Cline 必须读固定路径 `<out>/build_verify_result.json`(工具写的),
  从中提取以下字段(不得凭记忆/推理构造这些值):
    - `result`(PASS/FAIL)
    - `repair_allowed`(true/false)
    - `verification_id`(PASS 时用于步骤 D,只能从这里读)
    - `actual_changed_paths`(list,步骤 B 的 touched_files 只能从这里来)
    - `evidence`(路径,步骤 B 用)
    - `failure_class` / `reason`(转人工时展示)
  下面所有判断以这个文件的字段为准:

  ▸ result == "PASS":
      → 跳到 步骤 D(GERRIT_READY,准备提交)
      → ⚠️ 不是 Cline 判断"过了",是 result JSON 的 result 字段说 PASS

  ▸ result == "FAIL" 且 repair_allowed == false:
      → 停止。这个失败不是源码可修(工具链/环境/依赖/apply/污染等)。
      → 转人工。Cline 不得尝试改源码重试(工具已判定不可修)。
      → 输出 failure_class + reason,结束 workflow。

  ▸ result == "FAIL" 且 repair_allowed == true:
      → 继续 步骤 B(收敛判断)

  ── 步骤 B:收敛判断(确定性工具)──
  ⭐ touched_files 【不由 Cline 从 edit_spec 凭空提取】,口径分两档:

    - iter=1:
        touched_files = 步骤 A result 的 `actual_changed_paths`(全量)
        (首轮累积 edit_spec 就是本轮 patch,全量 == 本轮 delta)

    - iter>1(多轮,本次单轮验证不涉及):
        touched_files = 本轮累积 edit_spec 相比【上一版累积 edit_spec】新增/内容
          变化的 delta 文件
        并校验:delta 文件 ⊆ 步骤 A result 的 `actual_changed_paths`
        (actual_changed_paths 此时是累积全量,只作 guard,不直接当 touched_files)
        ⚠️ 原因:多轮时 build-verify 打的是累积 edit_spec,actual_changed_paths 是
          完整 patch 的全部改动,不是本轮 delta;若直接传全量,上轮已有文件上的
          新 cluster 会被误判成本轮 regressed。
        若无法可靠计算 delta 文件 → 停止转人工,不得降级传累积全量。

  Cline 把选定的 touched_files(list)包成 {"files": [...]} 写入
  `<out>/touched_files.json`(<out> = build-verify 的 --output-dir)。
  current-evidence / previous-evidence 用固定路径:
    - current-evidence = 步骤 A result 的 `evidence` 字段指向的文件
      (通常在 <out>/audit/analyzer_output/evidence_packet.json)
    - previous-evidence:
        iter=1 → baseline evidence 路径(原始失败 build 的 evidence)
        iter>1 → 上一轮 build-verify 的 <out>/ 中的 evidence 文件
  调 check-convergence:
    python -m ci_triage check-convergence \
      --current-evidence <本轮 evidence(来自 result.evidence)> \
      --previous-evidence <上轮 evidence;iter=1 时 baseline evidence> \
      --touched-files touched_files.json --output <conv_out>
  ⭐ Cline 必须读固定路径 <conv_out>,以其 `verdict` 字段为准
  (不得自己判断是否收敛/恶化):

  ▸ verdict == "regressed":
      → 停止。本轮 patch 在它改的文件引入了新的源级错误(修复方向有害)。
      → 转人工。输出 reason,结束 workflow。

  ▸ verdict == "stalled":
      → 停止。patch 没修动主错误,再试也是白试。
      → 转人工。输出 reason,结束 workflow。

  ▸ verdict == "advance":
      → 更新状态供下一轮(和 touched_files delta 口径配套):
          previous_evidence   = 本轮 current_evidence
          previous_edit_spec  = 当前累积 edit_spec 的快照
      → 继续 步骤 C(改进 edit_spec)

  ── 步骤 C:改进累积 edit_spec(Cline 唯一的智能决策)──
  iter += 1
  若 iter > MAX_ITER(3):
    → 停止。达到迭代上限仍未编译通过。转人工。结束 workflow。
  否则:
    1. 使用本轮 build-verify FAIL 返回的 evidence(步骤 A result.evidence)。
    2. 调 analyzer / patch-suggest 基于该 evidence 重新生成 context(显式动作,
       不是 Cline 凭印象)。
    3. 若 patch-suggest 返回 not_applicable / 无可用 context:
         → 停止转人工。Cline 不得在无 context 时凭感觉继续改源码。
    4. Cline 只基于【新 context + previous_edit_spec】改进累积 edit_spec:
        · 同一文件的错误反复 → 改进该文件的 edit(替换,不叠加)
        · 新文件的错误(牵连出的)→ 新增该文件的 edit
       结果始终是"让包编译通过所需的全部修改"的完整累积快照。
    5. 回到 步骤 A(下一轮 build-verify,内部会用干净源码重打累积 edit_spec)。
       下一轮 touched_files 用 previous_edit_spec → 新累积 edit_spec 的 delta 计算。

  ── 步骤 D:准备提交(确定性工具,dry-run)──
  ⭐ verification_id 【只能从步骤 A 读到的 build_verify_result.json 的
  `verification_id` 字段取】,不得凭记忆/构造/复用旧 id。
  (若用了错的 id,gerrit-submit 的 verification_id 绑定校验会 rejected_not_ready。)
  调 gerrit-submit(默认 dry-run):
    python -m ci_triage gerrit-submit \
      --verification-id <result JSON 的 verification_id> --state-db <db> \
      --gerrit-host <host> --gerrit-port <port> --gerrit-user <user> \
      --submit-target <ref> --submit-mode dry-run --output <submit_out>
  ⭐ Cline 必须读固定路径 <submit_out>,以其 `action` 字段为准:

  ▸ action == "dry_run":
      → 成功。展示给人:
        · command / command_argv(可执行的 git push 命令)
        · provenance(build_id / failure_key / verified_commit_sha / base_commit)
        · warnings(如目标分支偏移提示)
      → 交人 review。
      → ⚠️ Stage1 中 Cline 【禁止执行】command 或 command_argv,禁止代替人
        运行 git push;只能展示,由人手动执行。
      → 结束 workflow(成功路径)。

  ▸ action == "skipped_duplicate":
      → 停止。该 submission_key 已有提交记录(幂等)。
      → 输出 action + provenance,转人工确认,不再生成/执行命令。
      → 结束 workflow。

  ▸ action != "dry_run"(任何其他,fail-closed):
      → 停止。安全门未放行(record_not_found / rejected_not_ready /
        rejected_verification_mismatch / rejected_worktree_dirty /
        rejected_worktree_missing / rejected_submit_not_enabled 等)。
      → 输出 action + reason + warnings,转人工排查。结束 workflow。
      → ⚠️ Cline 不得绕过、不得重试提交、不得自行构造/执行 push 命令。
```

## 停止条件汇总(全部来自工具返回,非 Cline 主观判断)

| 停止原因 | 来源 | 后续 |
|---------|------|------|
| 编译通过 | build-verify `result==PASS` | → gerrit-submit dry-run(成功) |
| 失败不可修 | build-verify `repair_allowed==false` | 转人工 |
| 恶化 | check-convergence `verdict==regressed` | 转人工 |
| 不收敛 | check-convergence `verdict==stalled` | 转人工 |
| 达迭代上限 | iter > 3 | 转人工 |
| 提交未放行 | gerrit-submit `action != dry_run`(含 rejected_* / skipped_duplicate / record_not_found) | 转人工 |

## 纪律(UX 兜底;真正的安全由工具的物理机制保证)

- 编译/环境类错误(repair_allowed=false)不反复堆 patch:工具已判不可修,直接转人工。
- 同一问题最多 3 轮(MAX_ITER):即使 convergence 一直 advance,超过 3 轮也停(刹车)。
- Cline 每轮只维护 edit_spec 内容;源码状态、编译、收敛、提交 gate 全交给工具。
- ⚠️ 本节纪律是行为建议;即使 Cline 违反,底层工具的物理 gate(state DB /
  verification record / Git-object 匹配)仍会拦住不安全的提交。

## 单轮验证(本次 Stage1 验证范围)

1095003 / inference-engine-interface 已知第一轮 build-verify 即 PASS(删死字段
decodingType → gbs 编译成功)。用它验证单轮闭环(build-verify PASS → gerrit-submit
dry-run)的 Cline 驱动形态:

1. Cline 依 context 生成 edit_spec(删 decodingType 死字段)
2. 步骤 A:调 build-verify → result==PASS(工具返回,非 Cline 判断)
   步骤 A 后 `<out>/` 中应有(Cline 读固定路径,不猜):
     - `build_verify_result.json` — 主结果(result / verification_id /
       actual_changed_paths / evidence 等字段)
     - `audit/` — build log 等排障产物
3. 步骤 D:从 build_verify_result.json 读 verification_id → 调 gerrit-submit
   dry-run → 读 <submit_out> 的 action==dry_run
4. 展示 command_argv + provenance,交人 review(Cline 不执行 command_argv)

验证要点:
- Cline 全程通过读工具 JSON 字段决策,不脑补 PASS/可提交
- 即使 Cline 试图跳过 build-verify 直接 gerrit-submit,后者会 rejected_not_ready
  (state DB 无对应 GERRIT_READY record)——物理 gate 生效

多轮循环的逻辑(convergence 驱动 advance/stalled/regressed)已由 convergence 真机
验证(5 场景全对)单独覆盖;本 workflow 结构支持多轮,待有合适的多轮场景包时验证
完整循环。
