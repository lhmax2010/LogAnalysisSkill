# Changelog

## [1.4.0] - 2026-07-21

v1.4.0 在 v1.3.0 的四个 GBS skill 基础上,新增 CI triage 编排能力和 AI 执行剧本,用于把 QuickBuild 失败构建推进到可审阅的修复建议、编译验证和 Gerrit dry-run。

### Added

- 新增 `tizen-ci-triage`:可从 QuickBuild 发现失败 build,下载单包 buildlog,定位 Gerrit 源码,运行 analyzer/patch-suggest,生成单包报告和批量 manifest。
- 新增编译验证闭环:一次性源码 copy、edit_spec 路径边界校验、真实 `gbs build` 验证、PASS verification record、收敛判断和 Gerrit dry-run 安全门。
- 新增 `workflows/`:包含 `ci-triage-batch-full.md`、`explore-unavailable.md`、`repair-verify-submit.md`,供 AI 助手执行批量 triage、不可用源码探索和修复验证提交流程。
- 新增 `batch_manifest.json` 机器可读产物,让 AI 助手读取结构化 unit、路径、状态和错误原因,不需要解析 markdown 表格。

### Changed

- 发布包增加中立的 `workflows/` 目录,不绑定 Cline 的 `.clinerules/` 目录约定。
- QuickBuild GBS Reports 默认扫描 standard、emulator、gcov 相关 arch;workflow 对未验证的 emulator/gcov build-verify 路径保持人工确认。
- Gerrit dry-run 结果会区分 `dry_run` 与 `dry_run_unverified_remote`,并在 workflow 汇总中显式暴露远端状态和分支漂移。
- daily report 折叠无 GBS report 的重复 arch 行,同时 manifest 保持 per-unit 粒度。

### Fixed

- 支持 out-of-tree build 的 `../` 相对诊断路径,减少源码存在却被误判为 unavailable 的情况。
- `match_pkg_key` 支持 Tizen 常见 `hal-api-*` / `capi-*` 包名到 Gerrit project 的保守映射,歧义时仍转人工。
- `build-verify` 使用完整 copy 而不是 git worktree,避免 GBS 2.0.1 不识别 worktree 的 `.git` 指针文件。
- `gerrit-submit` 在无法确认远端 HEAD 时不再返回普通 `dry_run`,避免把检查失败伪装成检查通过。

### Boundaries

- 工具仍不调用 LLM、不自动 apply patch、不自动 push Gerrit。
- `gerrit-submit` 只查本地 state DB 的 duplicate,不查远端 Gerrit 已存在 change。
- emulator/gcov profile 的 build-verify 支持仍需更多真实失败样本和 gbs.conf profile 验证。
- 不确定的源码归属、系统头、generated/vendor 代码和依赖/环境问题仍会降级为人工处理。
