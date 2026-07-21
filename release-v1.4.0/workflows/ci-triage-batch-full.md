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
时间范围(二选一,决定处理哪些 build):
  hours        回看小时数,例如 48    ← 时间窗模式(处理窗内【所有】失败 build)
  since        绝对时间下限,例如 2026-07-12T00:00:00(与 hours 二选一)

build_id     可选。只想处理某一个 build 时给它;不给则处理时间窗内所有 build。
overview_id  可选,默认 1930。QuickBuild overview(configuration)id,决定从哪个
             overview 页面发现失败 build(如 166 是另一组构建)。**必须是纯数字**,
             不要传完整 URL。不同 overview 请用不同的 `--state-root` 隔离 state。
arch(es)     例如 standard-aarch64 standard-armv7l standard-x86_64
gbs_conf     例如 /home/xxx/Toolchain/gbs.conf   ← 必须是对的那个!
state_db     例如 ./tmp/bXXX/citriage.db
work_root    例如 ./tmp/bXXX
cookie_id    QuickBuild 登录后的 session cookie 值(见 1.2 生成 cookie 文件)
gerrit_user  例如 lhmax2025
```

**两种模式**:
| 模式 | 输入 | 处理范围 |
|---|---|---|
| **单 build** | `build_id` + `hours`/`since`(要覆盖到该 build) | 只处理这一个 build 的 unit |
| **时间窗** | 只给 `hours`/`since`,不给 `build_id` | 处理窗内**所有**失败 build 的 unit |

> batch 从 QuickBuild 的 `overview/1930` 发现时间窗内的失败 build。
> ⚠️ 该 overview 只列最近约 10 条:若 stderr 出现
> `history may contain more builds` 警告,说明窗内 build 数超出页面能列出的范围,
> **更早的 build 会被漏掉**。此时缩小时间窗分批跑,并在报告里注明覆盖不完整。

> ⚠️ `cookie_id` 是**认证凭据**(登录态),敏感。**不进 git、不进 manifest、不进日志、
> 不进汇总报告。** 只在运行时用于生成 cookie 文件,处理完可删。

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
UNIT_SAFE="${unit_key//:/__}"
UNIT_DIR="<work_root>/units/${UNIT_SAFE}"
mkdir -p "$UNIT_DIR"
```

**注意**:`unit_dir` 是 Cline 的工作目录,和 batch 自己的输出目录
(`<work_root>/batch_state/runs/<date>/<build>/<arch>/<pkg>/`)是**两回事**。
manifest 里的路径(`src_clean` / `evidence_packet` / `patch_context`)指向 batch 的输出,
**只读**;Cline 自己的产物写到 `unit_dir`。

### 1.2 从 cookie_id 生成 cookie 文件

QuickBuild 抓取要一个浏览器导出格式的 cookie JSON。人只提供 `cookie_id`(session 值),
Cline 生成文件:

```bash
mkdir -p "<work_root>"
cat > "<work_root>/quickbuild_cookies.json" << EOF
[{"name": "JSESSIONID_8810", "value": "<cookie_id>", "domain": "quickbuild.tizen.org"}]
EOF
chmod 600 "<work_root>/quickbuild_cookies.json"
```

后续 batch 命令用 `--cookie <work_root>/quickbuild_cookies.json`。

要点:
- `name` 固定为 `JSESSIONID_8810`(QuickBuild 实例的 session cookie 名,不变)。
- `domain` 必须含 `quickbuild.tizen.org`(加载器按此过滤)。
- **不要把 cookie 文件或 `cookie_id` 写进 git / manifest / 日志 / 汇总报告。**
  它是登录凭据。生成文件放 `<work_root>`(临时区),`chmod 600`。
- 如果抓取报 `COOKIE_EXPIRED` / `COOKIE_MISSING` → cookie 过期,让人重新登录 QuickBuild
  导出新的 `cookie_id`,重新生成文件。

## 2. 跑 batch,拿 manifest

```bash
# 时间参数二选一：--since 优先；省略 --since 时用 --hours 回看（默认 24）
python tizen-ci-triage/scripts/run_ci_triage_batch.py \
  <time_arg> \
  [--overview-id <overview_id>] \
  --arch <arch1> [--arch <arch2> ...] \
  --state-root <work_root>/batch_state \
  --cookie <work_root>/quickbuild_cookies.json \
  --git-ssh-command "ssh"

# time_arg 取其一：
#   --hours 48                      回看 48 小时
#   --since 2026-07-18T00:00:00     绝对时间下限
# 人给了 since 就用 --since，给了 hours 就用 --hours，不要两个都套。
# --overview-id 只在人明确指定了非默认 overview 时才加（默认 1930）。
```

**读 stderr 的发现结果**:
```
ci_triage_batch: discovered N failed builds
ci_triage_batch: package units M
```
- 记下 N(发现的失败 build 数)和 M(包单元数),写进汇总。
- ⚠️ 若出现 `history may contain more builds` 警告 → **窗内 build 超出 overview
  页面能列出的范围,更早的被漏了**。缩小时间窗分批跑,并在报告里注明"覆盖不完整"。

**找 manifest**(取本次最新的 run;同一天可能跑多次,按修改时间取最新):
```bash
MANIFEST=$(ls -t <work_root>/batch_state/runs/*/batch_manifest.json | head -1)
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

**选出要处理的 unit**:
```python
pkgs = manifest["packages"]
if build_id_given:          # 单 build 模式
    units = [p for p in pkgs if p["build_id"] == "<build_id>"]
else:                       # 时间窗模式:处理窗内所有 build
    units = pkgs
```

**时间窗模式的默认处理策略**(按此执行,不要自行发挥):
```
1. 按 build_id 分组,【新 build 优先】(新的更可能是当前要修的回归)。
   "新"的定义:**按 `build_id` 数值降序**;若 manifest 里有更可靠的时间字段
   (完成时间/创建时间),按该时间降序。
2. 每个 build 组内:先处理完该组的分支 A,再处理该组的分支 B。
3. 开跑前先把 N(build 数)/M(unit 数)和预估耗时报告给人,
   若 unit 总数很大(>10),请人选择:
     - 只处理最新 build
     - 只处理分支 A(available,自动闭环)
     - 全量跑
   等人选定后再开始。
```

> ⚠️ 每个 available unit 的 build-verify 要几十分钟,时间窗模式 unit 数可能几十个。
> 串行处理,中途每完成一个 build 组输出小结,便于人叫停。

## 3. 分流

| `patch_status` | 处理 |
|---|---|
| `source_context_available` | → 分支 A(自动,先过 A0 的 arch 白名单) |
| `source_context_unavailable` | → 分支 B(探索 + 人确认) |
| `not_applicable` | → 分支 C(跳过,记录) |
| `null`(有 `error`) | → 分支 C(跳过,记录 error) |
| 其他值 | → **fail-closed,转人工** |

**两种"非包失败"状态的区别**(实测遇到,归类都正确,含义不同):

| state | 含义 | 处理 |
|---|---|---|
| `REPORTED_NO_REPORT`(spec_name `__NO_GBS_REPORT__`) | 该 build 压根没有 GBS Reports 页(RBS/trigger/snapshot 类) | 分支 C 跳过,报告里列出 build_url 供人工查看 |
| `NEEDS_INPUT` + `GBS Reports contained no failed package rows` | **有** GBS Reports 页,但扫描的 arch 里全是成功包 —— 即该 build 失败在包构建之外的步骤 | 分支 C 跳过,注明"失败不在包构建阶段,需人工看 QuickBuild 页面" |

> 这两种都**不是工具故障**,是诚实的边界标注。不要因为看到 `unknown-arch` /
> `<unknown>` 就以为解析出错。

**先处理所有 A,再处理 B。** A 成功率高,先把确定的做完。

## 4. 分支 A:source_context_available(自动)

### A0. Fail-safe 检查

```
若 patch_status == source_context_available 但以下任一为 null:
  src_clean / evidence_packet / patch_context / base_commit / project / branch / arch
→ 不自动处理;记录 manifest_incomplete;转人工。
```

**arch 白名单检查(安全门缺口,必须挡)**:
```
build-verify 的 arch → gbs -A 映射目前只在这三个 arch 上验证过:
  standard-aarch64 / standard-armv7l / standard-x86_64

若 unit.arch 不在上述三个之内(例如 emulator-x86_64、standard_gcov-armv7l)
→ 【不自动 build-verify】,标 needs_human + arch_not_verified,记录到汇总。
```
> 原因:这些 arch 能被 GBS report 发现(所以会出现在 manifest 里),但它们到
> `gbs build -A` 的映射尚未确认。贸然传给 build-verify 有两种坏结果:
> 报错白等几十分钟,或**用错误的 arch 构建却 PASS**,产出一个"验证过"
> 但实际验证的是别的架构的提交命令 —— 后者会绕过安全门,危害更大。
> 待映射确认后再放开这个白名单。

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

> **build root 疑似损坏时不要自动删。** 若上一次 build-verify 被中断/超时,
> build root 可能残留 `not-ready` 标记,导致下一次 gbs 弹交互提示 `(y/N/c)`
> 并在非交互模式挂起。此时 Cline **只做**:
> 1. 列出疑似路径(`ls ~/GBS-ROOT*/local/BUILD-ROOTS/scratch.<arch>.0/`)和证据;
> 2. **暂停,要求人确认**;
> 3. **不得自动执行 `sudo rm -rf` 或删除 build root**;
> 4. 人确认清理后再重跑 build-verify。
>
> `<unit_dir>/verify_ws` 是 disposable copy,可以自动 `rm -rf`;
> 但 `GBS-ROOT*/BUILD-ROOTS` 是共享的 gbs 构建根,删它影响面大,必须人确认。

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
  --arch "<unit.arch>" \
  --wall-timeout 7200
```

> **`--wall-timeout`**:默认 3600s 对大包(enlightenment、chromium 等)会超时。
> 大包用 `7200` 或更大。**超时不代表 patch 错**,是编译时间不够 → 调大重试。
>
> **别把 build-verify 当卡住**:真 gbs 编译几十分钟很正常,耐心等到它写出
> `build_verify_result.json`。可另开终端 `tail -f <unit_dir>/verify_out/audit/gbs_build.log`
> 看进度。

读 `<unit_dir>/verify_out/build_verify_result.json`,**按字段判断(不按直觉)**:

| 条件 | 处理 |
|---|---|
| `result == "PASS"` | → A6(出提交命令) |
| `result == "FAIL"` 且 `failure_stage == "apply_failed"` | edit_spec 的 `old`/`line` 不对 → 修 edit_spec 重来(回 A3) |
| `result == "FAIL"` 且 `failure_stage == "build_timeout"` | 编译超时,非 patch 错 → 加大 `--wall-timeout` 重跑(回 A5) |
| `result == "FAIL"` 且 `repair_allowed == false` 且 `failure_class == "dependency"` | 看 build log 区分真依赖 vs 误分类。**Cline 不得自己越过 `repair_allowed=false`**,只能提证据+暂停等人确认。见下方⚠️。 |
| `result == "FAIL"` 且 `repair_allowed == false` 且 `failure_class ∈ {toolchain, build_env}` | **停,转人工。** 环境/工具链问题,不进修复循环。 |
| `result == "FAIL"` 且 `repair_allowed == true` | 源码类失败 → **走 `repair-verify-submit.md` 的多轮循环剧本**(iter=2..3,含 check-convergence 判 advance/stalled/regressed) |
| 其他 | fail-closed,转人工 |

> ⚠️ **`failure_class == "dependency"` 的核查(实测踩过误判)**:
> 分类器有时把源码类错误(如修完一个警告后**暴露出的另一批** `-Wunused-private-field`)
> 误判成 `dependency`。但 **Cline 不得单方面越过 `repair_allowed == false` 去改源码**——
> 这是 Stage1 的硬边界。只能**提出证据 + 暂停等人确认**:
>
> 看 build log 的实际错误:
> ```bash
> grep -iE "nothing provides|cannot install|error:" "<unit_dir>/verify_out/audit/gbs_build.log" | head
> ```
> - 是 `nothing provides` / `cannot install` → **真依赖问题**。
>   若缺的是 dlog/glib/capi-base-common 等基础包 → 疑似 **gbs.conf 用错**。
>   → 转人工(换 conf 或补依赖也由人定)。
> - 是 `error: ... [-Werror,-Wxxx]` 之类**源码诊断** →
>   标记 `classifier_misclassified_dependency`;**暂停,向人展示证据**
>   (build log 里的实际源码错误)。
>   **人确认 override 后**,按下面的方式**显式重入**,不要把
>   `repair_allowed=false` 的结果当普通源码失败继续跑循环:
>   ```
>   1. 把这次人工 override 记录进汇总(unit_key / 原 failure_class / 证据 / 谁确认);
>   2. 把新暴露的源码诊断纳入 edit_spec(扩展 A3 的 edit_spec);
>   3. 从 A3 → A4 → A5 【重新进入安全门】(formatter + 新一轮 build-verify);
>   4. 不把 repair_allowed=false 的那次结果直接交给
>      repair-verify-submit 的多轮循环继续。
>   ```
> - **判断不了 → 转人工。**
>
> 关键:`repair_allowed == false` 是安全边界,Cline 只能提"疑似误判 + 证据",
> **不能自己决定继续改源码**。是否越过,由人确认。

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
| `dry_run_unverified_remote` | 命令**可用**(和 `dry_run` 的 command_argv 一致),但**远端状态完全没确认过**(`ls-remote` 没成功)。记录进汇总,并**必须显式标注**:见下方⚠️。 |
| `skipped_duplicate` | 本地 state DB 里已有同 `submission_key` → 记录,转人工确认,不再生成命令 |
| **其他任何值** | fail-closed:记录 `action` / `reason` / `warnings`,转人工 |

> ⚠️ **`dry_run_unverified_remote` 的含义**:`ls-remote` 失败,工具**对远端一无所知** ——
> 既不知道目标分支是否已漂移,也无从判断 Gerrit 上是否已有相同 change。
> command_argv 本身是对的(它只依赖本地已验证的 commit),但少了一层保证。
>
> 汇总里这类 unit **必须标注**:
> ```
> ⚠️ 远端状态未确认(ls-remote 失败)。执行前请人工核对:
>    1. Gerrit 上是否已存在相同 change(避免重复提交)
>    2. 目标分支 HEAD 是否仍是 base_commit(验证基础是否已过时)
> ```
> **不要**把它和普通 `dry_run` 混在同一行里不加区分 —— 那样人看不出差别,
> 会当成已检查过而直接执行。

> ⚠️ **`skipped_duplicate` 只查本地 state DB**,不查远端 Gerrit。
> 换机器、换 `--state-db`、或之前由人手工推送过的 change,工具**发现不了**。
> 首次在某个 state DB 上跑必然是 `dry_run` —— 这不代表远端没有相同 change。
> 执行 push 前,人仍应自行确认。

**分支漂移要单独列出,不要埋在 warnings 数组里**:
若 `warnings` 中有 `target_branch_drifted:<sha>`,说明目标分支 HEAD 已经不是
`base_commit` 了(验证基础相对当前远端已旧)。这是**已知事实**、信息完整,
所以 action 仍是 `dry_run`;但汇总表里要给它**单独一列**(填新的 HEAD sha),
让人一眼看出哪些 patch 的验证基础已经过时。埋在 warnings 里人扫不到。

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
# CI Triage Summary — <时间窗 或 build_id>

## 覆盖范围
- 模式:时间窗(--hours N) | 单 build(<build_id>)
- 发现失败 build:N 个 —— <build_id 列表>
- 包单元:M 个
- ⚠️ 覆盖完整性:若出现 `history may contain more builds` 警告,
  写明"overview 页面只列最近约 10 条,更早的 build 未纳入,本次覆盖不完整"

## 可提交(build-verify PASS + dry-run)
| build_id | unit_key | 诊断 | 改动文件 | verification_id | worktree_path | 远端状态 | 分支漂移 | 提交命令 |
|---|---|---|---|---|---|---|---|---|

> **远端状态**列填 `已确认` 或 `⚠️ 未确认(ls-remote 失败)`
> (对应 action `dry_run` / `dry_run_unverified_remote`)。
> **分支漂移**列:无漂移填 `-`;有 `target_branch_drifted:<sha>` 就填那个 sha,
> 表示验证基础相对当前远端已旧。

## 转人工
| build_id | unit_key | 类别 | 原因 | 证据路径 |
|---|---|---|---|---|

## 跳过
| build_id | unit_key | patch_status | 原因 |
|---|---|---|---|

## 统计
- 总 unit / 可提交 / 转人工 / 跳过
- 按 build 分组的小计(时间窗模式)
```

**提交命令只展示,不执行。** 人 review 后自己跑。

## 8. 已知陷阱(实测踩过)

| 陷阱 | 表现 | 应对 |
|---|---|---|
| gbs.conf 用错 | `depsolve` 失败,缺 dlog/glib 等基础包 | 用对的 gbs.conf。**不同 arch/工具链可能需要不同的 conf**;多 arch 跑之前先确认这份 conf 对所有目标 arch 都有效(尚未做过 armv7l 对照实验 → 若某 arch 大面积 `dependency` 失败,先怀疑 conf 而不是 patch)。 |
| `--git-ssh-command` 传错 | `ssh variant 'simple' does not support setting port` | 传 `"ssh"`(一个 ssh 命令),不是别的命令或占位符。 |
| `line` 号用错 | build-verify `apply_failed: edit old text was not found at or after the requested line` | `line` 用 `old` **开始**的行号。 |
| formatter 过但 build-verify apply 失败 | 同上 | 两者 line 语义不同。以 build-verify 为准。 |
| edit_spec 的 `file` 写成构建路径 | apply 失败 / 文件找不到 | 必须先做 A2 路径归一化。 |
| 残留 verify_ws | `WorkspaceViolation: disposable worktree already exists` | build-verify 前 `rm -rf verify_ws`。这是安全保护,不是 bug。 |
| GBS build root 损坏 | gbs 弹 `y/N/c` 交互提示,非交互模式挂起超时;`not-ready` 文件残留 | Cline 只列出疑似路径 + 证据,**暂停等人确认**,不自动 `sudo rm -rf` build root。人确认清理后重跑。 |
| build-verify 超时 | `result: FAIL`,`failure_stage: build_timeout`(默认 3600s) | 大包加 `--wall-timeout 7200`。超时 ≠ patch 错。 |
| 磁盘 result 被重跑覆盖 | `build_verify_result.json` 显示 FAIL,但 state DB / gerrit_submit 的 verification_id 显示 PASS | 多轮/重跑用不同 `--output-dir`,或**以 state DB / gerrit-submit 的 verification_id 为准**,不信被覆盖的磁盘 JSON。 |
| 并发跑多个 build-verify | gbs build root 冲突 | 串行,一个一个跑。 |
| 推了重复的 change | Gerrit 上出现内容相同的两个 change | `skipped_duplicate` 只查**本地 state DB**,不查远端。首次在某个 state DB 上跑必然返回 `dry_run`。执行 push 前人工核对 Gerrit(`git ls-remote <remote> \| grep <base_commit>` 能看到该 commit 是否已在某个 `refs/changes/*` 下)。实测撞过。 |
| 时间窗内 build 过多被漏 | stderr `history may contain more builds` | `overview/1930` 只列最近约 10 条。缩小时间窗分批跑,报告注明覆盖不完整。 |
