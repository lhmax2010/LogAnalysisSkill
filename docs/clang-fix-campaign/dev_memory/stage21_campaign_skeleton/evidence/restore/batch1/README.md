# 恢复第1批:离线验收

基线56e74f0;新增diff-to-edit-spec转换器与共享CLI,不改已有业务拒绝规则。
权威及逐项测试对照见[coverage.md](coverage.md),SKEL-RESTORE-02登记见progress第27节。

| 检查 | 最终结果 | 证据 |
|---|---|---|
| 新增转换器用例 | 64 passed | focused-final/stdout.log、pytest.xml |
| 完整pytest(无-x) | 3163 passed / 0 failed / 1既有skip | full-final/stdout.log、pytest.xml、command.json |
| mypy | success,163 source files | mypy-final/stdout.log |
| ruff完整待提交Python树 | all checks passed | ruff-final/command.json、stdout.log |
| import-linter | 7 kept / 0 broken | imports-final/stdout.log |
| design检查器 | 0 problem | design-final/stdout.log |
| 模块CLI入口help | exit0 | entry-help/stdout.log |
| nodeid | 3100 -> 3164,新增64,删除0 | integrity-final.json、nodeids-*-final.txt |
| 受保护字节 | 全部与56e74f0一致 | integrity-final.json |

唯一skip是`test_tizen_build_verify::test_case_insensitive_bypass_is_platform_specific`,
原因case-sensitive filesystem,不是新增skip。C5a与C8调查用例通过,未使用失败豁免。
最终负载(20核)前`1.98 4.83 6.87`,后`2.90 2.65 3.91`;包装耗时1079.27秒。
每个gate保留完整argv、UTC、exit、前后loadavg与CPU前10进程名/占用,不记其命令行。

`full/`是最初61个新增用例时的完整运行:3160 passed/1 skip,耗时1129.84秒;
P4边界补3例后重新跑`full-final/`,不覆盖前次证据。无旧测试断言、参数集或nodeid改动。
`collect/`、`integrity.json`等无final后缀材料仅记录中间61例阶段。

两轮独立SIGINT观察均有profile_exists=true,原测试查无进程引用后已回收
(own_residue_removed=true),见各自c8/cleanup-SIGINT.json。normal/SIGTERM正常;
调查场景profile_removed=true,无harness_failure。最终/dev/shm无p5q-browser-*残留。
不把这个已知瞬时残留写成“已修复”。

全部浏览器样本来自既有离线假服务器,无真实登录或提交;未运行真实gbs或Gerrit命令。
归档仅文本(JSON/HTML/log/XML/nodeid);不含state.db、浏览器profile或凭据文件。
暂存差异检查仅报采集HTML第10行原有空白,为保持原始证据字节不清洗;
排除HTML的源码/测试/文档差异检查通过,原输出见whitespace-check.json。
