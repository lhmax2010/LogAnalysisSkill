# SKEL-RESTORE-23:仅git进程限制遗漏既有analyzer子进程

2026-11-05,基线b7e4272。RESTORE-21已由RESTORE-22处置,本报告只针对其新增测试边界。

## 事实与证据

- RESTORE-22第一.2要求`intake.add_unit`不改;第二条同时规定“唯一外部进程为经SandboxGit的git”。
- `tizen-campaign-intake/scripts/tizen_campaign_intake/intake.py:134`在发布证据和建档前调用analyze。
- `tizen-campaign-core/scripts/tizen_campaign_core/_campaign_io.py:79`的argv为
  `sys.executable -m gbs_analyzer analyze <log> --output-dir <dir> --output-format both`,
  `:93`通过subprocess.run执行。这是本地日志分析,不是实际gbs编译。
- [离线探针](batch3/r22/probe_process_boundary.py)在subprocess.run处阻断后记录上述首个argv,
  add_unit返回`INTAKE_ANALYZER_FAILED`,exit5;未创建DB,未启动任何被探测子进程,
  未联网。临时目录已删除。[原始结果](batch3/r22/probe.json)。

只调用进程内analyzer过滤不能消除后续add_unit内部这次子进程;
修改共享analyze或临时替换它会改变已有路径,不以此绕过本次约束。

## 建议最小裁定(未实施)

```diff
- 唯一外部进程为经SandboxGit的git。
+ 允许的直接子进程仅为:
+ (1) 既有analyze路径的sys.executable -m gbs_analyzer analyze,仅分析本地日志;
+ (2) 既有SandboxGit路径的git,保留本地身份检查与只读clone/checkout。
+ git为SSH克隆启动的既有ssh传输链包含在(2)内;测试用假SSH及本地裸库。
+ clone目标逐字等于gerrit_ssh_base.rstrip('/') + '/' + 清单project;
+ 禁止任何HTTP(S)访问、浏览器/node、额外网络操作或任意可执行程序。
+ intake.add_unit、analyze和SandboxGit的现有实现不改。
```

副作用:纠正进程集合,不扩大网络目的地或授权新增业务操作。
新增测试应捕获整个命令的子进程argv:analyzer固定模块/动作和本地输入输出;
Git只能由SandboxGit调用,区分无远端的本地校验与唯一clone目标;
非法project在任何克隆前拒绝;额外HTTP/browser/node进程均判失败。
不能对rev-parse、remote get-url等本地Git调用要求一个不存在的远端参数。

若坚持绝对只允许Git进程,则需另行授权改变既有analyzer调用方式,与“add_unit不改且行为相同”
的要求一并重新定义;不建议为这条测试措辞重构已验收的证据生成路径。

## 停点

裁定已照录progress,design§4.6同步;生产源码、既有测试、冻结稿、依赖合约不改。
没有实现发现命令、没有新业务测试,未执行全仓门禁或真机操作。
检查输出见[checks.json](batch3/r22/checks.json)。等待进程白名单裁定,不自行继续。
