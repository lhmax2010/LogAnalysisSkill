---
name: tizen-clang-campaign
description: Orchestrate an explicitly authorized GCC-to-Clang campaign from verified discovery or manual intake through precedent reuse, review and cleanup. Use the campaign commands and bound evidence, never ad hoc builds or direct Git/QuickBuild operations.
---

# Tizen Clang Campaign

## Inputs

Complete [campaign-kickoff-template.md](references/campaign-kickoff-template.md).
Missing required input means stop and ask; do not infer values. All QuickBuild
commands use the same explicit `STATE_ROOT`, provided in that template. It is
not inferred from `STATE_DB` or the workspace. Configuration freezes the clang
configuration and Git author/committer identities. Never request credentials in
chat; browser login is performed by the operator in the tool's window.

The AI's campaign decisions are limited to generating an edit specification,
deciding when to reread a nonterminal result, and proposing abandonment for human
confirmation. Respect the per-unit MAX_ROUNDS and max_build_invocations recorded
in the database. Do not bypass a refusal by changing the database or budgets.

## Deterministic Workflow

Run in this order for each package. Capture each command's JSON and exit code.
Stop on a nonzero exit; use its documented recovery rather than guessing paths.
Pass every package's project as a separate `--project` in the batch startup check.
Process packages serially, never in parallel; render the combined report after
the last package. A confirmed abandonment advances to the next package.

```bash
python -m tizen_campaign_intake campaign-start-check --config "$CONFIG" --state-root "$STATE_ROOT" --project "$PROJECT"
```

For authorized discovery, first collect an immutable manifest, then consume it.
Only qb-discover logs in to QuickBuild. campaign-discover uses local logs and the
existing read-only source-clone path, never a browser. Start with --dry-run;
remove it only after confirming the reported packages and source revisions.
The two commands share STATE_ROOT. Use an emitted manifest path, not a guessed one.

```bash
python -m tizen_qb_verify qb-discover --config "$CONFIG" --state-root "$STATE_ROOT" --qb-project "$QB_PROJECT" --build-id "$SOURCE_BUILD_ID"
```

```bash
python -m tizen_campaign_intake campaign-discover --manifest "$DISCOVERY_MANIFEST" --state-db "$STATE_DB" --state-root "$STATE_ROOT" --config "$CONFIG" --dry-run
```

Manual intake remains available for supplied CI evidence:

```bash
python -m tizen_campaign_intake campaign-add-unit --state-db "$STATE_DB" --config "$CONFIG" --ci-log "$CI_LOG" --project "$PROJECT" --branch "$BRANCH" --spec-name "$SPEC_NAME" --base-commit "$BASE_COMMIT" --source-build-id "$SOURCE_BUILD_ID" --failed-arches "$FAILED_ARCHES" --toolchain-profile "$TOOLCHAIN_PROFILE"
```

Use the returned unit key, primary architecture and src_clean; never construct a
workspace/iter path. Run the following once for the primary architecture, then
once for each of the other two architectures. `ARCH_RAW` uses the registered raw
architecture name. Do not begin repair until all three baselines exist and the
primary outcome is matched.

```bash
python -m tizen_baseline_reproduce baseline-reproduce --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY" --src-clean "$SRC_CLEAN" --base-commit "$BASE_COMMIT" --gbs-conf "$CLANG_CONF" --package "$SPEC_NAME" --arch "$ARCH_RAW" --profile "$TOOLCHAIN_PROFILE" --output-dir "$BASELINE_OUTPUT"
```

Before generating each round's edit_spec, query the existing precedent path:

```bash
python -m tizen_campaign_repair propose-fix --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY" --round-index "$ROUND_INDEX" --arch "$ARCH_RAW" --output-dir "$PROPOSAL_OUTPUT"
```

For mode=t1 and needs_generation=false use its edit_spec_path and source_kind
`t1_cherry_pick`. For mode=generate and needs_generation=true, give context_dir
and its ordered T2 suggestions to the AI, then create a `generated` or narrowly
scoped `suppress` specification. Never fabricate an edit spec from a failed T1
application. A non-suppress T1 with reproduced baselines may reach review;
suppression remains sandbox-only, and forbidden always stops. Check policy
before EVERY repair-step, including additional architectures and later rounds.
The `&&` is a control barrier: policy forbidden (exit 4) stops this command block,
so repair-step is not invoked. Sandbox/review still recompute authoritative policy.

```bash
python -m tizen_campaign_repair suppress-policy check --edit-spec "$EDIT_SPEC" --src-root "$SRC_CLEAN" --source-kind "$SOURCE_KIND" && \
python -m tizen_campaign_repair campaign-repair-step --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY" --round-index "$ROUND_INDEX" --edit-spec "$EDIT_SPEC" --arch "$ARCH_RAW"
```

The build-round, charge, compile and verification-link sequence has one entry:
campaign-repair-step. Never directly call build-verify or gbs, or construct iter_
paths. Follow convergence verdicts: nonterminal advancement may generate another
edit_spec; denied, stalled, regressed and exhausted are terminal, not retry signals.
Keep all three PASS verification IDs from the same final round.

Suppression must obey policy and remain narrowly scoped. For CMake FetchContent
third-party source under build/_deps/, the relevant target belongs to the
downloaded project; the package CMakeLists may not reach it. If the target cannot
be identified, stop as ambiguous_target and ask a human. A2 permits review only
for a code fix with reproduced baselines; a suppress fix is sandbox-only.

Batch 3.5 ends with three linked PASS records for the same final round and status
REPAIR_ROUND_RUNNING (SKEL-B3-05), NOT LOCAL_3ARCH_PASS. Do not release or abandon
these copies: batch 4 needs them. Stop before the next command until batch 4 is
authorized. sandbox-submit performs aggregation and writes LOCAL_3ARCH_PASS.

```bash
python -m tizen_sandbox_submit sandbox-submit --verification-ids "$VERIFICATION_IDS" --state-db "$STATE_DB" --config "$CONFIG" --sandbox-branch "$SANDBOX_BRANCH" --message-brief "$MESSAGE_BRIEF" --edit-source-kind "$SOURCE_KIND"
```

After successful sandbox submission, synchronize the bound fix into the KB as NEW:

```bash
python -m tizen_campaign_kb campaign-kb-sync --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY"
```

QuickBuild login happens only when the production command needs it. Never click
Accept/Ready to Accept, issue a direct Run, or submit again after an uncertain
result. Follow the request ID returned by the tool; no manual result fallback.

```bash
python -m tizen_qb_verify qb-trigger --verification-ids "$VERIFICATION_IDS" --state-db "$STATE_DB" --state-root "$STATE_ROOT" --config "$CONFIG"
```

```bash
python -m tizen_qb_verify qb-result-fetch --request-id "$REQUEST_ID" --state-db "$STATE_DB" --state-root "$STATE_ROOT" --config "$CONFIG"
```

For SANDBOX_QB_PENDING report the request/build and wait until the operator is
available for the next read; do not run an unattended polling/login loop.
Use the returned result-file reference under the shared STATE_ROOT as QB_RESULT.
An unrecognized result requires its printed instructions, not repeated fetches
or fabricated PASS. A deliberate abandonment remains possible below.

Only after a bound QB PASS, synchronize again to promote the same record:

```bash
python -m tizen_campaign_kb campaign-kb-sync --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY"
```

```bash
python -m tizen_review_submit review-submit --verification-ids "$VERIFICATION_IDS" --state-db "$STATE_DB" --config "$CONFIG" --qb-result "$QB_RESULT" --review-target "$REVIEW_TARGET"
```

```bash
python -m tizen_campaign_report campaign-finish-unit --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY"
```

```bash
python -m tizen_campaign_report campaign-report --state-db "$STATE_DB" --output "$REPORT_PATH"
```

## Abandonment Exit

Only after explicit human confirmation that the unit should be abandoned:

```bash
python -m tizen_campaign_report campaign-release-worktrees --state-db "$STATE_DB" --config "$CONFIG" --campaign-unit-key "$UNIT_KEY" --confirmed-by "$CONFIRMED_BY" --abandon
```

This releases protection and records a durable barrier; it does not cancel an
already running QuickBuild build. Do not bypass it by rerunning submit commands.
Report may still show a later build status, but its workspace column remains
abandoned. For held/failed/lost worktrees without abandonment, use the same
release command without `--abandon` only after human confirmation.

## Outputs And Recovery

Keep stdout, request/verification IDs, result references and report together.
Busy means another owner holds the locks; do not remove locks. Missing or
tampered evidence is not permission to reconstruct it by hand. Finish-unit
retains held, missing-copy and failed-QB evidence; inspect its retained flag.
Review uses cached Change-Id and bound first-party results; retry never means
creating a different identity. Exceptions to this workflow require a design ruling.

## Retained P11 Requirements

以下照录 design.md 第 7 节 P11 中本骨架仍适用的条款;启动自检以骨架
第 5.5 节五项替代旧 A0。知识库、D2E、T1按恢复项裁定恢复,人工降级仍不适用。

- 启动输入契约(campaign-launch-template:必填项缺任一 fail-closed
  停下询问不猜;敏感项 cookie 只用于 fetch 不回显)。本版登录在浏览器
  会话内完成,不向人索取 cookie。
- suppress-policy 调用的 source_kind 赋值规则:新生成 = generated,
  受约束抑制 = suppress,已验证先例转换 = t1_cherry_pick。
- 双闸与全链口径(v1.4.4):修复轮的"建 round → 计费 → 编译 → link"
  一律经 `campaign-repair-step`(唯一入口),禁止直调裸 `build-verify`,
  也禁止剧本自行拼装 workspace/iter 路径。
- 抑制约束(含新增已知模式:CMake FetchContent `build/_deps/` 下载的
  第三方源码——既非本包 repo 亦非系统头文件;抑制作用域需挂到被下载
  工程定义的 target,本包 CMakeLists 未必够得到,判不出即
  ambiguous_target 转人工;实测样本:Open3D 的 ext_benchmark
  `-Wc2y-extensions`)。
- A2 质量前置、SANDBOX_QB_PENDING 报告要求、启动输入契约与用户填空模板
  (campaign_config 键枚举含 A12 git 身份 / qb-result);输入 fail-closed
  校验(缺项停,不猜默认值;cookie 只进会话不落盘)。

无人环三态按现有收敛输出处理:continue 才能提出下一轮修法,终态失败停止并
收尾,需要人工判断的歧义/HELD 保留证据并询问。MAX_ROUNDS 与调用预算
都是数据库权威,不得通过改参数绕过。不得把 PASS 当作跳过后续 gate 的许可。
