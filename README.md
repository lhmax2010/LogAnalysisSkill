# LogAnalysisSkill

Tizen gbs 编译日志分析 Skill。把 1~100 MB 的 buildlog 压缩成 ≤ 1800 token 的 Evidence Packet，让 LLM 准确定位构建失败根因。

---

## ⚠️ 给 AI 助手（Codex / Claude / ChatGPT / 其他）：必读

**如果你是被分配到这个项目的 AI 助手，按以下顺序操作，不要跳步**：

### 首次进入项目

1. **先读 `docs/CODEX_PROMPT.md`** —— 工作规则、强制约束、何时停下来等用户
2. **再读 `docs/DESIGN.md`** —— 设计基线（v0.5，已冻结，不允许修改）
3. **在读完上述两份文档前，不要写任何代码**

### 接手现有进度

1. `cat .dev_memory/current.yaml` —— 查看当前 milestone 状态
2. 读 `docs/CODEX_PROMPT.md` 末尾"接手现有项目"章节
3. 读最新 milestone 的 `.dev_memory/m{N}_{name}/memory.md`
4. 跑 `pytest tests/` 确认基线绿
5. 看 `git log --oneline -30`
6. **报告状态 + 下一步计划，等用户确认后再继续**

### 不允许的行为

- ❌ 跳过 milestone 顺序
- ❌ 自由发挥写"应该这样设计"的代码
- ❌ 修改 `docs/DESIGN.md`（任何设计变动必须通过用户出 patch）
- ❌ 一次实现多个 milestone
- ❌ 不写 dev_memory 就提交 PR

---

## 给人类用户

- 项目使用指南：[`docs/README_FOR_USER.md`](docs/README_FOR_USER.md)
- 设计文档：[`docs/DESIGN.md`](docs/DESIGN.md)
- Codex 开发规则：[`docs/CODEX_PROMPT.md`](docs/CODEX_PROMPT.md)
- 历史决策追溯：[`docs/archive/`](docs/archive/)

---

## 项目状态

- **阶段**：M3（rank_causes）
- **设计版本**：v0.5（已冻结）
- **MVP 工作量**：16 天，8 个 milestones
- **仓库**：https://github.com/lhmax2010/LogAnalysisSkill

---

## 快速链接

| 想做什么 | 看哪里 |
|---------|--------|
| 启动 Codex 开发 | `docs/CODEX_PROMPT.md` "启动指令" 章节 |
| 理解设计 | `docs/DESIGN.md` |
| Review 当前进度 | `.dev_memory/current.yaml` + 最新 milestone 的 dev_memory |
| 接入 Cline | `integrations/cline/README.md`（M14 后可用）|
| 接入 Compiling Agent | `integrations/compiling_agent/README.md`（M14 后可用）|
| 在真实环境测试 | `docs/test_guides/m{N}_{name}.md` |
| 提报 Bug | GitHub Issue（使用 bug_report 模板） |
| 提议新 Pattern | GitHub Issue（使用 pattern_proposal 模板） |

---

## 安装

```bash
git clone https://github.com/lhmax2010/LogAnalysisSkill.git
cd LogAnalysisSkill
pip install -e .
```

**系统依赖**：`universal-ctags`（Ubuntu: `sudo apt install universal-ctags`）

---

## 使用（M8 完成后可用）

```bash
python -m gbs_analyzer analyze /path/to/buildlog \
    --src-root /path/to/source \
    --max-tokens 1800 \
    --output-dir ./out

# 输出：
# - out/evidence_packet.json    程序消费
# - out/evidence_packet.md      LLM 直读
# - out/perf_report.json        性能评估
# - out/trace.jsonl             debugging
```

---

## License

待定
