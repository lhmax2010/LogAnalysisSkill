# 第 2 批外部评审输入

本目录是第 2 批三家外部评审的输入材料。

评审对象为 HLD v0.5.3，以及提交 `678024cf0799f609941caddb576a9489d5c0af7e`（678024c）相对 `8ca13b3` 的代码改动。

| 材料 | 仓库内路径 | SHA256 |
|---|---|---|
| HLD v0.5.3（已有原件，只读） | `docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.3.md` | `279a96f2e0b50fc91ff983cc37bc2fc588df18307ea07958463f5cf565237b65` |
| 第 2 批代码 diff | `docs/enhance/batch2/review/batch2-code-678024c.diff` | `585a3d832ca3160ca39e0664651057e38dd6b9a34012f20f58bac0279d6f3151` |

代码 diff 按以下命令在仓库根目录生成，不包含工作区的未提交改动：

```bash
git diff 8ca13b3 678024cf0799f609941caddb576a9489d5c0af7e -- vd-cosmos-core/src vd-cosmos-core/scripts vd-cosmos-core/tests vd-cosmos-core/config.sample.json vd-cosmos-core/.importlinter vd-cosmos-core/fixtures vd-cosmos-workflow vd-cosmos-watch vd-cosmos-fetch > docs/enhance/batch2/review/batch2-code-678024c.diff
```

评审结论回来后由设计方处理。评审方只读、不改仓库。

第 2.1 批等评审意见回来后，与设计方已发现的 6 条一并下发；期间不开工。
