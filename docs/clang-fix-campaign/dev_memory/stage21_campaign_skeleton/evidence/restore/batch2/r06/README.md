# 恢复第2批验收证据

基线 `f5f748e`;按SKEL-RESTORE-01/02/04/06交付。

## 索引

- `coverage.md`:逐条需求与测试对应;新增246个用例。
- `nodeids-final.json`、`nodeids-*-final.txt`:3164个既有nodeid全部保留,最终3410个。
- `integrity-before.json`、`integrity-final.json`:13个受保护路径与基线逐字节相同;
  既有测试未改;审核代码仅获准的两个表达式(+4/-2)。
- `full/`:首轮3407 passed、0 failed、1既有平台skip;不加-x,UTC/负载/完整argv在command.json。
  此轮启动后完成了`promote(to_status=...)`关键字契约及YAML固定错误提示补修,
  因而不把这一轮当作最终树的唯一门禁。
- `full-final/`:最终树完整重跑3409 passed/0 failed/1既有平台skip,
  pytest 1171.56秒;结果以command.json和stdout.log为准。
- `c8-observations.json`:两轮共22个场景,无harness_failure,profile全部删除;
  本轮不需要C8观测豁免或timing-sensitive重跑。
- `mypy-complete/`、`ruff-complete/`、`imports-complete/`、`design-complete/`:
  最终代码树的静态门禁,exit均0;169源文件、7合约、设计0 problem。
- `package-check-final.json`:离线构建wheel,新包4个Python文件逐字节核对;
  6个新旧入口help成功,临时目录删除。
- `cli-first/`、`targeted-first/`、`targeted-final/`:开发中局部结果,不替代最终门禁。
  其它`*-first`/`*-final`静态记录保留其原始结果,最终以`*-complete`为准。

## 运行边界

全部业务测试只用临时DB、JSONL、假SSH和本地裸库;浏览器回归由既有虚拟显示
入口访问本机假HTTPS服务。没有真实QuickBuild登录、Gerrit推送或真实gbs编译。
仓内没有提交实际知识库数据或状态库二进制。`full*/c5a`和`full*/c8`均为合成
服务器产生的测试记录,不是新真机证据。未改变代理、放行文法、身份判据或安全核心。

新执行包的SKILL说明可用命令与退出码;编排剧本与开局模板按原计划留恢复第4批。
恢复第3批只能先生成本地URL形态证据并停止,不能在本轮修改浏览器白名单。
