---
name: vd-fix-analyze
description: 为 VD Cosmos 失败包取得只读 P4 源码快照并记录来源依据、合并通知和源码行核对结果。
---

本段只提供 `snapshot`，任务包与分析结果接收尚未接入。

运行 `python3 vd-fix-analyze/scripts/run.py snapshot --config <配置> --backend fixture|real --build-id <号> --package <包名> --arch <架构> --log <数据根目录内日志>`；fixture 报告另加 `--manifest`，该模式强制使用仓库假 p4，输入是数据根目录的 `fake-p4.json`，也可由 manifest 的 `p4_fixture` 指向夹具提供。real 模式使用配置中的可执行文件。

stdout 是单个 JSON 回执，文件内容看回执中的 manifest。stderr 的 shelve 通知也记录在 manifest 的 `notices`、`round_report_rows` 和 `task_notice_interface`，最后一项供 3a-2 接入。

“仅诊断”不能当作可靠修改依据；源码行一致不提升来源依据。票据失效由人处理，不运行登录命令。遇到 `p4_unclassified_retry_exhausted`，核对待办后通过 `vd-fix-register inbox done` 恢复重试。
