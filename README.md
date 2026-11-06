# Tizen Clang 修复工具集 1.5.0

面向 GCC 到 Clang 迁移的批量修复流程：失败发现、日志分析、建档、基线复现、修法规格转换、先例检索、本地三架构验证、sandbox 提交、QuickBuild 验证、审核提交与结果报告。

自动发现失败包：**离线测试通过，真机未验证**。状态库、工作副本和输出目录由同一次活动管理，不要手工修改状态或绕过验证。

## 环境与安装

- Linux，Python **3.10+**，Git 与 SSH；工作盘需支持文件锁、硬链接和原子重命名。
- 实际编译需要 Tizen `gbs`、匹配目标快照的 Clang 构建配置和足够的磁盘空间。
- QuickBuild 功能需要 Node.js（本发布语法检查使用 **24.22.1**）、Playwright 模块和对应 Chromium，以及能显示登录窗口的桌面会话。Python 安装不会自动安装浏览器。
- Python 依赖由安装命令安装：Jinja2、PyYAML、tiktoken。

在发布目录执行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m tizen_campaign_intake --help
.venv/bin/python -m tizen_qb_verify --help
```

如需 QuickBuild，在独立目录安装 Playwright 及其 Chromium，将实际绝对路径写入配置。工具目录的 `SKILL.md` 随源码发布；Python 包安装用于命令执行。

## 配置

发布目录没有完整的 campaign YAML 样例。请依据以下实际加载键准备配置，并填写 [开局模板](tizen-clang-campaign/references/campaign-kickoff-template.md)。路径请使用绝对路径，凭据不要写入配置。

| 键 | 必填范围与含义 |
|---|---|
| `campaign_workspace` | 建档、复现、修复及提交必填，活动工作副本根目录 |
| `clang_conf_path` | 启动检查、复现、修复必填，实际 Clang 构建配置文件；不得使用浮动 reference 路径 |
| `gerrit_ssh_base` | 启动检查与建档/提交必填，`ssh://` Gerrit 基址；完整项目地址由基址与项目名组成 |
| `gerrit_user` | 启动检查必填；SSH 连接身份另由实际 SSH 地址/配置决定 |
| `git_author_identity`、`git_committer_identity` | 启动检查与提交必填，`Name <email>` 格式 |
| `push_timeout_sec`、`push_retry` | 启动检查要求存在；不替代下面提交模块实际读取的超时键 |
| `target_arches` | 启动检查要求存在，填写计划验证的架构；具体架构仍由命令与校验规则约束 |
| `max_rounds`、`max_build_invocations` | 建档必填，均为正整数；后续轮数与编译预算由状态库约束 |
| `gerrit_commit_msg_hook`、`gerrit_commit_msg_hook_sha256` | sandbox/审核提交必填，批准的 commit-msg hook 路径及其 64 位小写十六进制 SHA-256 |
| `push_timeout_seconds` | 可选，提交 Git 操作超时秒数，默认 `300`；与 `push_timeout_sec` 是两个不同键 |
| `git_ssh_command` | 可选，提交传输命令，默认 `ssh` |
| `wall_timeout` | 可选，修复编译超时秒数，默认 `3600`，可由 `--wall-timeout` 覆盖 |
| `kb_db` | 先例建议与知识同步必填，知识记录 JSONL 路径 |
| `state_root` | 可选，仅发现导入校验时读取；若填写，必须与命令 `--state-root` 解析后的路径相同。推荐统一显式传参 |
| `qb` | QuickBuild 命令必填，结构见下表 |

QuickBuild 配置加载器要求：

| 键 | 值与约束 |
|---|---|
| `qb.base_url` | 固定 `https://quickbuild.tizen.org` |
| `qb.browser.node`、`playwright_module`、`chromium` | 必填，均为存在的绝对路径 |
| `qb.browser.login_timeout_seconds` | 必填，正整数 |
| `qb.projects.<branch>.enabled` | 必填布尔值；未启用项目不执行 |
| `configuration_path` | 启用项目必填，以 `root/` 开头、以 `/RBS/TRIGGER` 结尾 |
| `overview_id`、`project_name` | 启用项目必填，正整数配置 ID 与项目名 |
| `qb_pass_requires_accept` | 启用项目必填布尔值；工具不会代为点击 Accept |
| `form` | 启用项目必填，且键集合恰为下面十项 |

`form` 的十个键：`BUILD_TYPE`、`REPO_TYPE`、`BUILD_REFERENCE`、`SNAPSHOT_NUM`（非空字符串，可用 `@freeze` 冻结当时选中项）；`PROJECT_BRANCH`（等于项目键）；`Immediate Stop With Error`（`true`）；`CHILD_CONFIGURATIONS`（`[standard-armv7l:aarch64:x86_64]`）；`TARGET_IMAGE`（`[]`）；`Add Package List`、`Remove Package List`（均为空字符串）。目标包行和请求标记由命令生成，不放进这十项配置。

## 命令入口

下表命令前加 `python -m <模块>`；对具体命令追加 `--help` 查看完整参数，不会开始业务操作。

| 模块 | 命令或用途 |
|---|---|
| `tizen_campaign_intake` | `campaign-start-check`、`campaign-add-unit`、`campaign-discover` |
| `tizen_baseline_reproduce` | `baseline-reproduce` |
| `tizen_campaign_repair` | `diff-to-edit-spec`、`propose-fix`、`suppress-policy check`、`campaign-repair-step` |
| `tizen_campaign_kb` | `kb`（追加/查询/导入，详见其帮助）、`campaign-kb-sync` |
| `tizen_sandbox_submit` | `sandbox-submit` |
| `tizen_qb_verify` | `qb-discover`、`qb-trigger`、`qb-result-fetch` |
| `tizen_review_submit` | `review-submit` |
| `tizen_campaign_report` | `campaign-finish-unit`、`campaign-release-worktrees`、`campaign-report` |
| `gbs_analyzer` | 已有构建日志的 `analyze` |
| `gbs_build_skill` | 本地构建封装 |
| `gbs_workflow` | 构建、分析、建议的组合流程 |
| `gbs_patch_suggest` | 修复上下文与 patch 格式化 |
| `ci_triage` | 兼容入口，保留原有子命令和旧模块别名 |

`tizen_campaign_core`、`tizen_ci_shared`、`tizen_convergence_judge`、`tizen_qb_discover`、`tizen_gerrit_fetch`、`tizen_build_verify`、`tizen_gerrit_submit`、`tizen_triage_report` 提供共享或独立工具 API；旧发现/验证/报告流程可经 `ci_triage --help` 查看入口，不应与活动审核命令混用。

## 典型流程

1. 填写模板，统一 `CONFIG`、`STATE_DB`、`STATE_ROOT`。运行 `campaign-start-check`，此步骤含只读远端检查。
2. `qb-discover` 输出已核验构建的清单与主架构日志。`campaign-discover --dry-run` 校验清单、分析日志并报告将建档项；确认后才去掉 dry-run，建档会只读克隆源码。也可用 `campaign-add-unit` 导入本地日志。
3. 对同一源码与构建配置运行三个架构的 `baseline-reproduce`，保持原始失败锚点。
4. `propose-fix` 检索先例，或 `diff-to-edit-spec` 将人工修法转换为规格。每轮先 `suppress-policy check`，再对三个架构顺序执行 `campaign-repair-step`，使用同一轮编号和修法规格。
5. 三份 PASS 已 link 后，经明确授权运行 `sandbox-submit`。不要释放后续提交仍需使用的工作副本。用 `campaign-kb-sync` 同步先例记录。
6. 经明确授权运行 `qb-trigger`，记录请求号；用 `qb-result-fetch` 核对结果。提交不确定时不能直接重提，应按请求标记查找绑定结果。
7. `review-submit` 重查质量、来源、QuickBuild 结果与工作副本后提交审核；用 `campaign-finish-unit` 与 `campaign-report` 收尾。放弃必须显式确认并用 `campaign-release-worktrees --abandon`，不要手动删除保护标记。

完整参数序列见 [活动流程](tizen-clang-campaign/SKILL.md)，各命令的边界与退出码见对应工具的 `SKILL.md`。发现示例：

```sh
python -m tizen_qb_verify qb-discover --config "$CONFIG" --state-root "$STATE_ROOT" --qb-project tizen_base --build-id "$BUILD_ID"
python -m tizen_campaign_intake campaign-discover --manifest "$MANIFEST" --state-root "$STATE_ROOT" --state-db "$STATE_DB" --config "$CONFIG" --dry-run
```

## 安全约束

- 发现只读，不 Run、不提交构建。`--dry-run` 不建档、不克隆。
- 登录凭据只在弹出的浏览器窗口输入，不在终端、配置或报告中填写账号密码、Cookie 或会话值。
- 工具永不点击 **Accept / Ready to Accept**；审核推送与 sandbox 推送须单独授权。
- 身份不符、解析不明确、快照不可用或漂移、脱敏失败均应按错误提示停止，不能通过改库、换路径或反复提交绕过。
- 知识库建议与转换结果必须通过策略检查、复现与编译验证；禁止以抑制绕过审核质量要求。
