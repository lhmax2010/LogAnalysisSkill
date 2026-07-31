# Tizen GBS Build Failure Toolkit v1.4.0

这是一套用于 Tizen GBS 构建失败分析与修复建议的工具集:可本地跑 build、分析日志、生成可 review 的 patch 上下文,也可从 QuickBuild 批量发现失败构建并编排到编译验证与 Gerrit dry-run。

## 环境要求

- Python 3.12+
- Python 运行依赖很少,`pip install -e .` 会按 `pyproject.toml` 安装 PyYAML
- 本地可用的 `gbs` 命令和有效 `gbs.conf`
- `tizen-ci-triage` 额外需要 QuickBuild 访问 cookie 和 Gerrit SSH 只读/提交权限

## 安装使用

```bash
python3 -m pip install -e .
```

安装后可直接使用模块入口,例如:

```bash
python -m gbs_workflow \
    --conf /path/to/gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root /path/to/source \
    --output-dir .gbs_workflow \
    --timeout 1800
```

如果不安装,也可以把各目录并列放置后直接运行脚本:

```bash
python /path/to/tizen-gbs-build-workflow/scripts/run_workflow.py \
    --conf /path/to/gbs.conf \
    --arch armv7l \
    --include-all \
    --src-root /path/to/source \
    --output-dir .gbs_workflow \
    --timeout 1800
```

免安装模式不会自动安装依赖;请先手动运行 `python3 -m pip install "PyYAML>=6.0.1"`,否则 analyzer 会因缺少 `yaml` 模块失败。

若 skill 目录不是并列放置,按需设置:

```bash
export TIZEN_GBS_BUILD_SKILL_DIR=/path/to/tizen-gbs-build
export TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR=/path/to/tizen-gbs-log-analysis
export TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR=/path/to/tizen-gbs-patch-suggest
```

## 最小输出

一次 workflow 运行会写出 `.gbs_workflow/`,优先读取:

```text
.gbs_workflow/
├── compiler.log
├── analyzer_output/
│   ├── evidence_packet.json
│   └── evidence_packet.md
├── patch_context/
│   ├── context.md
│   └── meta.json
├── suggestions/
└── workflow_summary.md
```

先读 `workflow_summary.md`。如果存在 `patch_context/context.md`,它通常比通用 advisory 更具体。

## 组件

| 组件 | 职责 |
|---|---|
| `tizen-gbs-build` | 跑 `gbs build`,抓日志 |
| `tizen-gbs-log-analysis` | 分析构建日志,产出 Evidence Packet |
| `tizen-gbs-patch-suggest` | 基于 Evidence Packet 生成修复 patch 的上下文 |
| `tizen-gbs-build-workflow` | 串联 build→分析→建议 |
| `tizen-ci-triage` | 从 QuickBuild 批量发现失败构建,编排到编译验证和 Gerrit dry-run |
| `workflows/` | 给 AI 助手的执行剧本,配合 `tizen-ci-triage` 使用 |

## AI 助手集成

- `SKILL.md`:Claude Code / Cline 可按 frontmatter 的 name/description 自动发现。其它助手可把 `SKILL.md` 内容贴进 prompt 使用。
- `workflows/*.md`:AI 执行剧本,内容不含工具特有语法。Cline 用户可复制或软链到项目根的 `.clinerules/workflows/`;其它助手可先读对应文件或把内容贴进 prompt。
- Python 脚本:纯 CLI,与 AI 工具无关,可独立运行或在任何环境调用。

## 重要提示

这些工具只生成分析结果、建议和 patch 文件,不会自动应用到源码。`tizen-ci-triage` 的 `gerrit-submit` 只做 dry-run,只输出命令,不会执行推送。

`build-verify` 失败时的 `repair_allowed` 是三态字符串:`"auto"` 表示可自动进入下一轮,`"needs_confirmation"` 表示错误在本包源码内但修法必须经人确认,`"denied"` 表示不得越过安全边界。多轮修复没有固定轮次上限,是否停止由 `repair_allowed` 和 `check-convergence` 的确定性结果决定。
