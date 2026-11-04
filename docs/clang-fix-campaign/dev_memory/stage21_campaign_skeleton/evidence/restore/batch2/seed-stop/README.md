# SKEL-RESTORE-05 停止证据

基线aecf55a。本目录不是恢复第2批验收交付。

| 记录 | 含义 |
| --- | --- |
| `../probe-seed-dedupe.py` | 独立的七元null编码试算,不导入草稿实现 |
| `../seed-contract-probe/` | 首次探针命令与输出,exit0 |
| `../seed-contract-probe-final/` | 为zip补strict后最终探针,exit0,结论不变 |
| `implementation-wip.patch` | 9个既有文件和12个新文件的未验收草稿,仅作定位资料 |
| `tracked-wip.patch` | 上述9个既有文件的子集,用于逐字节撤回本轮改动 |
| `wip-manifest.json` | 草稿各文件hash、基线hash、完整patch hash |
| `rollback-integrity.json` | 恢复后的21路径核验、9个受保护文件hash、nodeid集合对照 |
| `collect/` | 3164 collected,与基线集合相同,不是执行全仓测试 |
| `design/` | 0 problem |
| `ruff/` | 初次探针两处B905,保留失败记录 |
| `ruff-final/` | 仅改zip strict后通过 |
| `whitespace-check.json` | 两份生成patch的空白上下文行保留;其余暂存文件检查通过 |

局部功能测试的观察与未完成项列于
[停止报告](../../stop-report-SKEL-RESTORE-05.md)。没有全仓门禁或第二批完成结论。
不把草稿中临时拒绝seed的实现当成可接受降级,不直接套用本patch作为交付。
