# v0.5 交付物使用指南

本目录包含 v0.5 完整交付物。本文件帮你理解每份文档的用途和正确使用方式。

---

## 交付物清单

| 文件 | 大小 | 用途 |
|-----|------|------|
| `docs/DESIGN.md` | ~1500 行 | **设计基线**，Codex 实施唯一来源 |
| `CODEX_PROMPT.md` | ~400 行 | **Codex 启动 prompt**，开发规约 |
| `README_FOR_USER.md` | 本文 | 给你（用户）的使用指南 |

---

## 给 Codex 的启动流程

### Step 1：把 v0.5 文档放进 GitHub 仓库

```bash
# 假设你已经在本机 clone 了 https://github.com/lhmax2010/LogAnalysisSkill
cd /path/to/LogAnalysisSkill

# 创建文档目录
mkdir -p docs/archive
cp /path/to/docs/DESIGN.md ./docs/DESIGN.md
cp /path/to/CODEX_PROMPT.md ./docs/CODEX_PROMPT.md

# 把之前的演进文档归档（可选但推荐，方便决策追溯）
cp /path/to/tizen-gbs-design-v0.3.md docs/archive/
cp /path/to/tizen-gbs-design-v0.3.1-patch.md docs/archive/
cp /path/to/tizen-gbs-design-v0.4.md docs/archive/
cp /path/to/tizen-gbs-design-v0.4.1-patch.md docs/archive/
cp /path/to/tizen-gbs-changelog-v0.2-to-v0.3.md docs/archive/
cp /path/to/tizen-gbs-changelog-v0.3-to-v0.4.md docs/archive/

# 提交
git add .
git commit -m "docs: bootstrap v0.5 design baseline + Codex prompt"
git push origin main
```

### Step 2：给 Codex 第一次启动指令

把以下消息发给 Codex（或任何接手的 AI）：

```
你将开始一个 Tizen gbs 日志分析 skill 的开发项目。

仓库：https://github.com/lhmax2010/LogAnalysisSkill

请按以下步骤启动：

1. clone 仓库
2. 完整阅读 docs/DESIGN.md
3. 完整阅读 docs/CODEX_PROMPT.md
4. 严格按 CODEX_PROMPT.md 的工作规则执行
5. 你的第一个任务是 M0 初始化（见 CODEX_PROMPT.md "第一步"章节）
6. M0 完成后开 PR，停下来等我 review

注意：你不被授权修改 v0.5 设计文档。如遇到设计问题必须停下来问我。
```

---

## 给你（用户）的工作流程

### 阶段 1：M0 启动验收

Codex 完成 M0 后会开 PR `[M0] Initialize project structure`。你做：

1. 检查仓库结构是否符合 v0.5 §12
2. 检查 `.dev_memory/current.yaml` 是否正确
3. 跑一次 `pytest tests/` 看 CI 基线
4. 检查 `.github/workflows/ci.yml` 是否合理
5. Merge PR

### 阶段 2：每个 milestone 的 review

Codex 完成每个 milestone 后开 PR。你做：

#### 必查项（5 分钟）

```bash
# 1. checkout PR 分支
gh pr checkout {PR_number}

# 2. 跑测试
pytest tests/ -v --cov

# 3. 跑代表性 fixture
python -m gbs_analyzer analyze tests/fixtures/{some_fixture}/buildlog --trace

# 4. 看性能报告
cat /tmp/gbs_analysis_out/perf_report.json
```

#### 必读项（10 分钟）

- `.dev_memory/m{N}_{name}/memory.md` — 这次做了什么
- `.dev_memory/m{N}_{name}/decisions.md` — 重要决策
- `.dev_memory/m{N}_{name}/test_report.md` — 测试结果
- `docs/test_guides/m{N}_{name}.md` — 真实环境测试方法

#### 真实环境测试（按需）

如果你有真实的 gbs buildlog 想验证：

```bash
# 按 docs/test_guides/m{N}_{name}.md 的步骤
python -m gbs_analyzer analyze /your/real/buildlog \
    --src-root /your/source \
    --max-tokens 1800 \
    --trace
```

### 阶段 3：跨 AI Review

如果你想让其他 AI（Claude / ChatGPT / Kimi）review 某个 milestone：

```
我有一个 Tizen gbs 日志分析 skill 的开发项目，目前完成到 M{N}。
请帮我 review 这个 PR 的实施质量。

仓库：https://github.com/lhmax2010/LogAnalysisSkill
PR：https://github.com/lhmax2010/LogAnalysisSkill/pull/{N}
设计基线：docs/DESIGN.md（在仓库根目录）
开发规则：docs/CODEX_PROMPT.md

请检查：
1. 是否符合 v0.5 设计
2. dev_memory 是否完整
3. 测试覆盖是否足够
4. 性能基线是否达标
5. 是否有 review 时容易遗漏的盲点

不需要质疑设计本身（已经经过三轮 review 冻结）。
```

### 阶段 4：换 AI 接手

如果 Codex session 崩溃或你想换 AI（比如改用 Claude Code）：

```
我之前用 Codex 在开发这个项目，现在切换到你。

仓库：https://github.com/lhmax2010/LogAnalysisSkill

请按 docs/CODEX_PROMPT.md 末尾"如果你是接手现有项目"的指令操作。

具体来说：
1. cat .dev_memory/current.yaml
2. 读 docs/DESIGN.md
3. 读 docs/CODEX_PROMPT.md
4. 读最新 milestone 的 dev_memory
5. 跑 pytest 验证基线
6. 看最近 30 个 commit
7. 报告你了解的状态 + 下一步计划
8. 等我确认后再继续
```

---

## 常见问题

### Q1：Codex 不按规则做，自由发挥怎么办？

CODEX_PROMPT.md 已经明确禁止自由发挥。如果发生：
1. 直接拒绝 PR
2. 在 PR 评论指出违反了哪条规则
3. 让 Codex 重新看 CODEX_PROMPT.md 后修改

### Q2：某个 milestone 工作量超出估算很多怎么办？

按 CODEX_PROMPT.md "强制停下点" 的规则，Codex 应该主动停下问你。

如果它没停下：你强制让它停下，分析原因：
- 设计问题 → 出 v0.5.1 patch 修正
- 实施能力不足 → 拆分 milestone
- 估算本身偏乐观 → 调整后续 milestone

### Q3：测试一直跑不通怎么办？

如果是单元测试一两次失败 → 让 Codex 自己修
如果是反复失败超 2 次 → 介入分析（fixture 数据问题？设计盲点？）
如果是性能基线达不到 → 决策：继续优化 vs 接受 + 记录

### Q4：发现设计有问题怎么办？

**不要让 Codex 自己改设计**。

正确做法：
1. 你出 v0.5.1 patch 文档（描述修正）
2. 让其他 AI（Claude/ChatGPT/Kimi）review patch
3. 确认后更新仓库的设计基线
4. 让 Codex 按新设计调整代码

### Q5：Cline / Compiling Agent 接入什么时候做？

按 v0.5 §13 实施计划，接入示例放在 M14（full 阶段）。

但**接口契约从 M1 起就要遵守**（CODEX_PROMPT.md "与 Cline / Compiling Agent 的接入" 章节）：
- 不允许 stdout 干扰
- 日志走 tracing logger
- 错误有清晰 exit code

### Q6：怎么评估方案是否成功？

MVP 验收 gate（v0.5 §13）：
- 20 fixtures 全通过
- Fast-Path 命中率 ≥ 25%
- Top-1 准确率 ≥ 80%
- 完整流程端到端 < 15s
- BudgetPool 守恒率 100%
- 各 milestone 的 dev_memory 完整

如果 MVP 验收通过，说明方案可行，可以进入 full 阶段或部署到 Cline / Compiling Agent。

---

## 文档版本管理

```
当前版本：v0.5 (frozen)

历史：
v0.1 → v0.2 (Evidence Packet 定位)
v0.2 → v0.3 (Fast-Path + 单趟扫描)
v0.3 → v0.3.1 patch (兜底完备性，部分被 v0.4 否决)
v0.3.1 → v0.4 (做减法 + 弹性预算池)
v0.4 → v0.4.1 patch (实施层细节)
v0.4.1 → v0.5 (工程化 + dev_memory + 接入方案，本版本)

未来路线图：
v0.5 → v0.6 (基于 MVP 实测数据)
v0.6 → v0.7 (扩展 collector 类型)
```

---

## 关键链接（贴这给 Codex 或其他 AI）

```
仓库：https://github.com/lhmax2010/LogAnalysisSkill
设计基线：docs/DESIGN.md
开发规则：docs/CODEX_PROMPT.md
```

---

**祝开发顺利。如果 MVP 实施过程中发现 v0.5 设计有问题，记得用 v0.5.1 patch 流程，不要让 Codex 自己改。**
