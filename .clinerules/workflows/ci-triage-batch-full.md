# CI Triage Batch Full — 总控 Workflow

一个 QuickBuild 失败 build → 所有失败包的、编译验证过的、可提交的 patch。

## 0. 铁律（必须先读）

1. **主输入是 `batch_manifest.json`,不是 `daily_report.md`。** 不解析 markdown 表格,
   不从文本里猜路径。所有包信息、路径、状态都从 manifest 的字段读。
2. **所有 gate 判断以工具 JSON 返回为准。** 不脑补"这个应该能过"。
   `build-verify` 返回 `result`/`failure_stage`/`failure_class`/`repair_allowed`,
   `gerrit-submit` 返回 `action`,照读。
3. **`gbs_conf` / `state_db` / `gerrit_user` 由人显式提供,不猜。** manifest 里没有这些
   (运行时参数)。用错 gbs.conf 会导致 depsolve 失败,或更糟——环境和 CI 不一致
   导致"假通过"。
4. **`source_context_available` 才能自动走完。** `source_context_unavailable`
   必须走 explore-unavailable.md,且 build-verify 前**暂停给人确认**。
5. **只汇总 `command_argv`,不执行。** Stage1 是 dry-run only,人 review 后自己 push。
6. **串行处理包。** 一个包走完再下一个(gbs build root 冲突 + state DB 写入)。
7. **`edit_spec` 的 `line` 是 `old` 文本【开始】的行号**(基于原始文件)。
   formatter --check 通过 ≠ build-verify 能 apply(两者 line 语义不同,曾踩过)。
   最终以 build-verify 为准。
8. **`edit_spec` 可以改 `packaging/*.spec`**(已验证:`actual_changed_paths` 会含它)。
9. **fail-closed。** 遇到未预期的字段值/状态/action → 停,转人工,不猜。

## 1. 输入(人提供)

```
build_id       例如 1127447
arch(es)       例如 standard-aarch64 standard-armv7l standard-x86_64
gbs_conf       例如 /home/xxx/Toolchain/gbs.conf   ← 必须是对的那个!
state_db       例如 ./tmp/bXXX/citriage.db
work_root      例如 ./tmp/bXXX
cookie         QuickBuild cookie JSON 路径
gerrit_user    例如 lhmax2025
since          覆盖该 build 的时间下限,例如 2026-07-12T00:00:00
```

环境:
```bash
export PYTHONPATH="<repo>/tizen-ci-triage/scripts:<repo>/tizen-gbs-build/scripts:\
<repo>/tizen-gbs-log-analysis/scripts:<repo>/tizen-gbs-patch-suggest/scripts:\
<repo>/tizen-gbs-build-workflow/scripts:$PYTHONPATH"
```

### 1.1 unit_dir 命名规则(Cline 的工作目录)

每个 unit 的产物(edit_spec / patch / verify_ws / verify_out / submit_out)放在:

```
unit_dir = <work_root>/units/<unit_key 安全化>

安全化:把 ":" 替换成 "__"
  1127447:standard-aarch64:united-service
  → <work_root>/units/1127447__standard-aarch64__united-service/
```

`unit_key` 含 `:`,虽然 Linux 路径能用,但对后续脚本/日志/跨平台不稳。统一安全化。

```bash
UNIT_DIR="<work_root>/units/$(echo "<unit_key>" | tr ':' '_' | sed 's/_/__/g')"
# 或直接:UNIT_DIR="<work_root>/units/${unit_key//:/__}"
mkdir -p "$UNIT_DIR"
```

**注意**:`unit_dir` 是 Cline 的工作目录,和 batch 自己的输出目录
(`<work_root>/batch_state/runs/<date>/<build>/<arch>/<pkg>/`)是**两回事**。
manifest 里的路径(`src_clean` / `evidence_packet` / `patch_context`)指向 batch 的输出,
**只读**;Cline 自己的产物写到 `unit_dir`。

## 2. 跑 batch,拿 manifest

```bash
python tizen-ci-triage/scripts/run_ci_triage_batch.py \
  --since <since> \
  --arch <arch1> [--arch <arch2> ...] \
  --state-root <work_root>/batch_state \
  --cookie <cookie> \
  --git-ssh-command "ssh"
```

**找 manifest**(`<date>` 是动态生成的,不要猜):
```bash
MANIFEST=$(ls <work_root>/batch_state/runs/*/batch_manifest.json | tail -1)
```

### 2.1 校验 manifest(防 manifest 生成 bug 把 Cline 带偏)

读进来后先校验:
```
- manifest["packages"] 存在且是 list
- 每个 unit 有全部 16 个 key:
  unit_key, build_id, arch, spec_name, state, patch_status, project,
  base_commit, branch, src_clean, evidence_packet, patch_context,
  patch_context_meta, report, package_buildlog, error
- 路径字段若非 null,必须是绝对路径
```
任一不满足 → **停,报告 manifest 异常,不继续。**

**只处理目标 build_id 的 unit**(manifest 可能含时间窗内其他 build):
```python
units = [p for p in manifest["packages"] if p["build_id"] == "<build_id>"]
```

## 3. 分流

| `patch_status` | 处理 |
|---|---|
| `source_context_available` | → 分支 A(自动) |
| `source_context_unavailable` | → 分支 B(探索 + 人确认) |
| `not_applicable` | → 分支 C(跳过,记录) |
| `null`(有 `error`) | → 分支 C(跳过,记录 error) |
| 其他值 | → **fail-closed,转人工** |

**先处理所有 A,再处理 B。** A 成功率高,先把确定的做完。

## 4. 分支 A:source_context_available(自动)

### A0. Fail-safe 检查

```
若 patch_status == source_context_available 但以下任一为 null:
  src_clean / evidence_packet / patch_context / base_commit / project / branch / arch
→ 不自动处理;记录 manifest_incomplete;转人工。
```

### A1. 读诊断和上下文

```
读 unit["patch_context"]      → context.md(诊断 + 源码上下文 + 指引)
读 unit["evidence_packet"]    → 结构化诊断(file/line/message/kind)
```

### A2. ⭐ 路径归一化(必须先做,否则 edit_spec 的 file 写不对)

evidence 里的 `file` 是**构建路径**,不是 repo 相对路径:

```
evidence.file:  /home/abuild/rpmbuild/BUILD/united-service-1.3.1/src/exception.cc
                └────────── 构建前缀 ──────────────────────┘ └── 相对路径 ──┘
edit_spec.file: src/exception.cc            ← 相对 src_clean 的路径
实际源码:       <unit.src_clean>/src/exception.cc
```

**归一化规则**(按 `file` 的形态):

| `file` 形态 | 归一化 |
|---|---|
| `/home/abuild/rpmbuild/BUILD/<pkg>-<ver>/<rel>` | 剥掉 `BUILD/<pkg>-<ver>/` 前缀 → `<rel>` |
| `../<rel>`(out-of-tree build) | 剥掉前导 `../` → `<rel>`,再在 src_clean 里 `find` 确认 |
| `/usr/include/...` 等系统路径 | **不在本 repo**;不该出现在 available 分支;若出现 → 转人工 |
| 上述都不匹配 | **suffix fallback**(见下) |

**suffix fallback**(GBS 路径有时多一层子目录,或包名版本不完全可预测):
```bash
# 用 file 的后缀在 src_clean 里唯一匹配
find "<unit.src_clean>" -path "*<file 的后几段>" -type f
```
- **恰好 1 个匹配** → 用它(取相对 src_clean 的路径)
- **0 个或 2+ 个匹配** → **转人工,不猜。** 匹配错文件 = 改错代码。

**必须验证归一化结果确实存在**:
```bash
test -f "<unit.src_clean>/<rel>" && echo OK || echo "归一化失败,转人工"
```
不存在 → 不猜,转人工。

### A3. 看源码精确字节,写 edit_spec

```bash
sed -n '<line-5>,<line+10>p' "<unit.src_clean>/<rel>" | cat -A
```
`cat -A` 显示 tab(`^I`)和行尾(`$`)。`old` 必须**字节级匹配**。

写到 `<unit_dir>/edit_spec.json`:
```json
{
  "schema_version": "gbs_patch_suggest/edit-spec/v1",
  "patch_name": "candidate_1.patch",
  "edits": [
    {
      "file": "<归一化后的相对路径>",
      "line": "<old 文本【开始】的行号>",
      "old": "<精确原文,字节级匹配>",
      "new": "<替换文本>"
    }
  ]
}
```

要点:
- `line` 是 `old` **开始**的行号。build-verify 从这行**往后**找 `old`。
- `old` 字节级匹配(tab vs 空格!)。
- `old` 保持最小(能唯一定位即可)。
- 同一 `old` 出现多次 → 每处一条 edit,用 `line` 区分。

### A4. formatter 验证(秒级)

```bash
python3 -m gbs_patch_suggest format-patch \
  --src-root "<unit.src_clean>" \
  --edit-spec "<unit_dir>/edit_spec.json" \
  --output "<unit_dir>/candidate_1.patch" \
  --check
```
失败 → 改 edit_spec 重试。**不要手写 unified diff。**
看生成的 patch,确认改法符合预期。

> formatter 通过**不保证** build-verify 能 apply(line 语义不同)。以 build-verify 为准。

### A5. build-verify(真 gbs 编译,几十分钟)

先清残留:
```bash
rm -rf "<unit_dir>/verify_ws" "<unit_dir>/verify_out"
```

```bash
python -m ci_triage build-verify \
  --src-clean "<unit.src_clean>" \
  --base-commit "<unit.base_commit>" \
  --edit-spec "<unit_dir>/edit_spec.json" \
  --gbs-conf "<gbs_conf>" \
  --package "<unit.spec_name>" \
  --workspace-root "<unit_dir>/verify_ws" \
  --output-dir "<unit_dir>/verify_out" \
  --baseline-evidence "<unit.evidence_packet>" \
  --iter-index 1 \
  --state-db "<state_db>" \
  --build-id "<unit.build_id>" \
  --project "<unit.project>" \
  --branch "<unit.branch>" \
  --arch "<unit.arch>"
```

读 `<unit_dir>/verify_out/build_verify_result.json`,**按字段判断(不按直觉)**:

| 条件 | 处理 |
|---|---|
| `result == "PASS"` | → A6(出提交命令) |
| `result == "FAIL"` 且 `failure_stage == "apply_failed"` | edit_spec 的 `old`/`line` 不对 → 修 edit_spec 重来(回 A3) |
| `result == "FAIL"` 且 `repair_allowed == false` | **停,不进修复循环。** 看 `failure_class`:`dependency` → 检查 gbs.conf 是否用对;`toolchain`/`build_env` → 环境问题。转人工。 |
| `result == "FAIL"` 且 `repair_allowed == true` | 源码类失败 → **走 `repair-verify-submit.md` 的多轮循环剧本**(iter=2..3,含 check-convergence 判 advance/stalled/regressed) |
| 其他 | fail-closed,转人工 |

### A6. gerrit-submit dry-run

```bash
VID=$(jq -r .verification_id "<unit_dir>/verify_out/build_verify_result.json")

python -m ci_triage gerrit-submit \
  --verification-id "$VID" \
  --state-db "<state_db>" \
  --gerrit-host review.tizen.org --gerrit-port 29418 \
  --gerrit-user "<gerrit_user>" \
  --submit-target "refs/for/<unit.branch>" \
  --submit-mode dry-run \
  --output "<unit_dir>/submit_out.json"
```

按 `action` 字段判断(**fail-closed**):

| `action` | 处理 |
|---|---|
| `dry_run` | 记录 `command_argv` + `worktree_path`,进汇总。**不执行。** |
| `skipped_duplicate` | 已提交过 → 记录,转人工确认,不再生成命令 |
| **其他任何值** | fail-closed:记录 `action` / `reason` / `warnings`,转人工 |

## 5. 分支 B:source_context_unavailable(探索 + 人确认)

**走 `explore-unavailable.md`。**

- 探索目标是判断"能不能安全形成 edit_spec",不是硬凑一个 patch。
- 探索完成后**暂停**,把推理 + 拟定的 edit_spec 展示给人,**等确认**才 build-verify。
- 刹车:每个 unit 最多 **10 次探索性工具调用**(不计 formatter/build-verify/gerrit-submit)
  **或 10 分钟,先到者为准**。仍无明确 hypothesis → `needs_human`,继续下一个包。

人确认后,走 A4 → A5 → A6。
**探索出来的 patch 同样要过 build-verify,不因"人确认过"跳过安全门。**

## 6. 分支 C:not_applicable / error(跳过)

记录 `unit_key` / `spec_name` / `arch` / `patch_status` / `error.code` / `error.message`。
不进修复循环。

## 7. 汇总报告

```markdown
# Build <build_id> Triage Summary

## 可提交(build-verify PASS + dry-run)
| unit_key | 诊断 | 改动文件 | verification_id | worktree_path | 提交命令 |
|---|---|---|---|---|---|

## 转人工
| unit_key | 类别 | 原因 | 证据路径 |
|---|---|---|---|

## 跳过
| unit_key | patch_status | 原因 |
|---|---|---|

## 统计
- 总 unit / 可提交 / 转人工 / 跳过
```

**提交命令只展示,不执行。** 人 review 后自己跑。

## 8. 已知陷阱(实测踩过)

| 陷阱 | 表现 | 应对 |
|---|---|---|
| gbs.conf 用错 | `depsolve` 失败,缺 dlog/glib 等基础包 | 用对的 gbs.conf。不同 arch/工具链可能要不同的 conf。 |
| `--git-ssh-command` 传错 | `ssh variant 'simple' does not support setting port` | 传 `"ssh"`(一个 ssh 命令),不是别的命令或占位符。 |
| `line` 号用错 | build-verify `apply_failed: edit old text was not found at or after the requested line` | `line` 用 `old` **开始**的行号。 |
| formatter 过但 build-verify apply 失败 | 同上 | 两者 line 语义不同。以 build-verify 为准。 |
| edit_spec 的 `file` 写成构建路径 | apply 失败 / 文件找不到 | 必须先做 A2 路径归一化。 |
| 残留 verify_ws | `WorkspaceViolation: disposable worktree already exists` | build-verify 前 `rm -rf verify_ws`。这是安全保护,不是 bug。 |
| 并发跑多个 build-verify | gbs build root 冲突 | 串行,一个一个跑。 |
