# 第 2.1 批 + HLD v0.6 外部评审输入

本目录是第 2.1 批 + HLD v0.6 的三家外部评审输入材料。

评审对象：HLD v0.5.4 的改动（附录 G）、HLD v0.6 的改动（版本记录中的本次 v0.6 更新条目），以及提交 `3fd647043b0648dae039dd34b250148d4356ef9a`（3fd6470）相对 `3ff18e4c86c578e19622d37fb96b306b40a23bf6`（3ff18e4）的代码改动。

| 材料 | 仓库内路径 | SHA256 |
|---|---|---|
| HLD v0.5.4（保留原件，重点为附录 G） | `docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.4.md` | `8fdcb3c9b8c26e592bad0695db59736709b02790adeae9ba87386cfd1b26f2f8` |
| HLD v0.6（原样复制，重点为本次版本记录） | `docs/enhance/vd-cosmos-loganalyzer-hld-v0.6.md` | `c5e8467a2644aa5d194bd3b3b8e948f2c63075e33e36c33947926e3e8cc7fd2d` |
| 第 2.1 批代码 diff | `docs/enhance/batch2.1/review/batch21-code-3fd6470.diff` | `ed8b5a4b49ea87a6b0c589821983fd4792c09e4c3f63bed8835688e4b22ac573` |

diff 共 **3157 行**，在仓库根目录按以下命令生成，不包含工作区未提交的改动：

```bash
mkdir -p docs/enhance/batch2.1/review && git diff 3ff18e4c86c578e19622d37fb96b306b40a23bf6 3fd647043b0648dae039dd34b250148d4356ef9a -- vd-cosmos-core/src vd-cosmos-core/scripts vd-cosmos-core/tests vd-cosmos-core/config.sample.json vd-cosmos-core/fixtures vd-cosmos-workflow vd-cosmos-watch vd-cosmos-fetch > docs/enhance/batch2.1/review/batch21-code-3fd6470.diff
```

HLD v0.6 复制后的摘要与设计方指定值一致；使用本线 `config.sample.json` 的凭据模式和现有行内样例豁免预检，无未豁免命中。原件的豁免在本版本第 80、643 行，未新增、修改或移动；文档内容保持原样。HLD v0.5.4 保留不删。

评审方只读、不改仓库。评审意见由设计方处理；第 3 批等评审意见处理后再下发，期间不开工。

构建机真实验收与第 3 批开工前侦察的设计方反馈已登记在 `docs/enhance/dev_memory/STATUS.md`。本次只准备材料、更新状态，不修改代码，不代替或重跑构建机验收。
