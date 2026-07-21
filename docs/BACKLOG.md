# tizen-ci-triage Backlog

> 术语:skill = 有可执行实现的能力包(python),AI 按 SKILL.md 调用;
> workflow = 给 Cline 的纯文本剧本,零代码,内容是需要 AI 判断的步骤。
> `tizen-gbs-build-workflow` 名字里的 "workflow" 指它编排的业务流程,
> 不是 Cline 的 workflow 机制 —— 它有 1641 行 python,是 skill。

## 阻塞(缺输入,不是优先级问题)

### emulator-x86_64 / standard_gcov-armv7l 的 build-verify 支持

已确认(build 1130862 的五个 GBS Reports 页):

| arch 页名 | Profile | -A |
|---|---|---|
| emulator-x86_64 | tizen_unified_emulator | x86_64 |
| standard-aarch64 | tizen_unified_standard | aarch64 |
| standard-armv7l | tizen_unified_standard | armv7l |
| standard-x86_64 | tizen_unified_standard | x86_64 |
| standard_gcov-armv7l | tizen_unified_standard_gcov | armv7l |

- arch 页名结构:`<profile后缀>-<arch>`,profile = `tizen_unified_<前缀>`
- 三个 standard 共用一个 profile(这是它们一直能 PASS 的原因,不是运气)
- emulator/gcov 各有独立 profile,连包集合都不同(1020/1051/1034 个包,
  Package Path 前缀分别是 `tizen_unified_emulator/`、`tizen_unified_standard/`、
  `tizen_unified_standard_gcov/`)

**为什么不能只加 `-A` 映射**:用 standard profile + `-A armv7l` 跑 gcov 的包,
仓库源和编译参数都不同,跑出的 PASS 验证的不是 CI 上失败的那个构建 —— 假 PASS,
绕过安全门。这正是 workflow A0 白名单挡的东西。

当前 gbs.conf 只有 `tizen_unified_standard` 一个 profile,repo URL 写死
`.../repos/standard/packages/`。

三段推进:
1. **[环境]** conf 里补两个 profile。需先查 download.tizen.org 上 emulator/gcov
   对应的 repo 路径,以及 gcov 是否需要额外 build_conf/define。不写代码。
2. **[验证]** 拿一个在这两个 arch 上**真实失败**的包,手动用新 profile 复现,
   确认错误和 CI 一致。**没有真实失败案例就无法验证配置对不对** —— 这是当前的阻塞点。
3. **[代码]** 确认可行后 build-verify 支持按 arch 选 profile,解开 A0 白名单。

现状:三个 standard 能正常验证;另两个白名单挡着是正确行为。1、2 完成前不动代码。

## 高

### gerrit-submit 不查远端重复

`skipped_duplicate` 只查本地 state DB 的 `submission_key`,不查 Gerrit。
换机器 / 换 `--state-db` / 人工推过的 change 都发现不了;首次在某个 DB 上跑
必然返回 `dry_run`。

实测:capi-ui-inputmethod 的 change 已在 Gerrit(`refs/changes/62/344962/1`
就是同一 base_commit `31dfee6b`),工具照常给出 push 命令。

已缓解(6560ddc + workflow):ls-remote 失败时 action 改为
`dry_run_unverified_remote`,workflow 要求汇总标注"远端未确认"。
但**首次跑 + ls-remote 成功**的情况仍不查重复。

真正的修法需要 Change-Id(Gerrit 标准做法),涉及 commit message 生成 ——
现在的 edit_spec 流程不生成 Change-Id。范围不小,单独立项。

## 中

### manifest 对 SKIPPED_PROCESSED 的路径字段填 None

但 `report` 字段指向历史 run。跨天用同一 `--state-root` 重跑时,已处理 unit 的
`src_clean`/`evidence_packet` 都是 None,workflow 会误判 missing_source 转人工 ——
而产物其实还在 `runs/<旧日期>/` 下。今天撞上过。

### QuickBuildSource 翻页

overview 页只列最近约 10 条。活跃日时间窗内 build 超过 10 个会静默漏。
代码有 warning(`history may contain more builds`)但不翻页。
触发条件:看到该 warning。

### SKILL.md 是否补"系统头文件警告→查本包触发单元→本包抑制"指引

已讨论,**倾向暂不做**:SKILL.md 是 skill 的说明书,把 `-Wno` 抑制写进去等于把
workaround 提升成推荐做法,AI 容易从"最后手段"滑向"第一反应";而且样本量只有 1
(capi-ui-inputmethod)。等再遇到两三个同类案例、看清边界(触发单元在生产库
怎么办?多个触发单元怎么办?)再决定。

## 低

- `NEEDS_INPUT` 的 `unknown-arch`/`<unknown>` 显示(reason 已带 scanned arches,
  但 arch 字段本身仍是占位;改它会动 unit_key 影响幂等)
- build-verify not-ready 自动检测(现靠 workflow 人确认兜底)
- build-verify result 磁盘被多轮覆盖(workflow 已写以 state DB 为准)
- gerrit-submit 内部 ls-remote 失败原因(命令行两种方式都通;
  `_subprocess_env` 在未传 `--git-ssh-command` 时返回 None 继承环境,
  可能缺交互 shell 的 SSH 上下文)

## 搁置

### failure_classify 误判 -Wunused-private-field 为 dependency

数据未证实。真机重跑时 iter1 FAIL → iter2 修复流程顺畅,没有出现
`repair_allowed=false` 卡住的情况。遇到再看。

## 已解答(留档)

- **gbs.conf arch 感知**:三个 standard arch 共用 `tizen_unified_standard`,
  只需换 `-A`,实测均能 build-verify PASS。跨 profile 才需不同配置(见阻塞项)。
  另已实证:传错 conf 会在 depsolve 阶段硬失败(大面积 nothing provides
  基础包),不会假通过。

## 未落地的结论

- capi-ui-inputmethod 的 patch 已验证 PASS(`9db7c8f9`)但**不要提交**
  —— change 已存在于 Gerrit
- 1127447 另外三个 unit(united-service / sessiond / enlightenment)的
  edit_spec 就绪,未重跑
- hal-api-hdcp/drm 是 tidlc 生成器 bug(数组引用了没生成的
  `__rpc_port_stub_*_privilege_checker`),该报上游而非 workaround。
  曾试过 spec 里 sed 替换 → 把函数定义也改成 `static int NULL(...)`,
  build-verify 挡住了 —— 安全门有效的实例。
