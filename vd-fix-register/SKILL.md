---
name: vd-fix-register
description: 在终端登记 VD Cosmos 的人工终态、shelve 输入确认、base 清单绑定和待办关闭。
---

入口为 `python3 vd-fix-register/scripts/run.py <命令> --config <配置> --backend fixture|real --round <构建号> --reason <理由>`；fixture 报告另加 `--manifest`。必须有控制终端，由人确认，非 TTY 返回 2。

- `confirm-terminal --report-digests '<按架构的 JSON 摘要映射>'`：未发布架构填“未发布”。可信来源仍运行/排队时必须加 `--override-running` 并输入构建号确认。撤回使用 `--withdraw`。
- `confirm-input --package '<包含 arch/name/path 的 JSON 包键>' --shelve-digest <摘要>`：只放行该摘要对应的输入。
- `bind-base-list --file <base 清单> [--shelve-file <原始 shelve 清单>]`：复制为不可变输入；只给 base 时不声称核验过原始 shelve 清单。
- `inbox done --todo-key <待办键>`：关闭待办，p4_unclassified 对应包恢复重做。

stdout 仅 JSON，人工回显与确认通过控制终端；不执行提交、shelve 或浏览器写操作。其余裁决命令由后续批次实现。
