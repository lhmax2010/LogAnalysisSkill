# SKEL-B2-04: campaign-report 的子构建号缺少可定位的数据源

状态:STOPPED,等待设计方裁定。基线51513bd,2026-11-03。
SKEL-B2-03假SSH注入前置已通过;本停止与本地origin问题无关。

## 事实与证据

1. 冻结稿`campaign-skeleton-design-v1.3-FROZEN.md:229`规定:
   `campaign-report --state-db [--output <md>]`,列含QuickBuild父/子构建号,
   并且“只读状态库”。命令没有state-root参数。
2. `tizen_campaign_core/campaign_state.py:210`的campaign_qb_events只有
   qb_build_id、per_arch_status_json、qb_result_ref等列,没有child_build_id。
   campaign表中也没有state_root字段。
3. `tizen_qb_verify/qb_result_fetch.py:495`写父构建号,
   `:499`明确写per_arch_status_json=None,
   `:501`写`qb_result_ref=str(output.relative_to(root))`。
   子构建号在RESULT JSON中,不是这条数据库记录里的字段。
4. QB命令的state_root独立于state_db;不能假设是数据库父目录或当前工作目录。
   新离线探针在临时数据库通过现有create_unit/create_qb_request/append_qb_event
   API建合成记录,结果文件放另一根目录。父101在库内,子102只在文件中;
   相对ref从DB父目录/CWD解析都不存在,从显式state_root解析存在。
   探针只验证存储契约,合成JSON不是完整QB业务结果样本。

证据:
- `ssh-resume/probe-report-source.py.txt`与`report-source.stdout.log`:
  完整campaign列、合成RESULT行、现行写入代码行号、路径判定;
  exit 0,SPEC_GAP_CONFIRMED,临时目录已删除,网络请求0。
- `ssh-resume/commands.json`:命令、UTC起止、exit。

## 为什么停止

按现有入口无法可靠定位子构建号。猜目录、扫描磁盘、把应有值静默置空、
增加数据库列或增加CLI参数都会自行改变契约。此前未验收草稿中的相对路径读取
不能作为实现,已连同其它业务草稿撤出源码并归档为WIP,没有交付新业务命令。
不修改冻结稿、P5Q结果写入、安全核心或共享身份校验。

## 候选文字修改(仅建议,未实施)

候选A(建议设计方确认):显式输入结果根目录,扩大只读输入范围。

```diff
- campaign-report --state-db [--output <md>]
+ campaign-report --state-db --state-root <path> [--output <md>]
- 只读状态库。
+ 只读状态库及指定state_root内由最新RESULT引用的结果文件。
+ 父构建号取对应BUILD_BOUND/RESULT;子构建号取RESULT文件的child_build_id。
+ 读取前校验ref解析后仍在state_root内、文件SHA256等于事件登记值;
+ 缺少RESULT时子构建号为空;已登记RESULT但文件缺失、越界或校验不符时,
+ 报REJECTED_STATE_INCONSISTENT,不输出伪完整报告、不写库。
```

副作用:新增必需参数及文件读取边界,更新CLI/SKILL、JSON错误用例;
不改旧库/P5Q格式,但须设计方确认上述失败规则及父子来源。

候选B:保留纯数据库报告,把子构建号列改为明确的“不可从状态库取得”或删除该列。
副作用:报告能力收缩,无法满足原列要求;仍需设计方明确空值/展示契约。
不建议为报告单独改P5Q状态写入或扩展共享状态schema。

候选A需补夹具:
- state.db与state_root分离,不同CWD运行仍取得正确父/子构建号;
- 已绑定但无RESULT,明确空值;有RESULT缺文件不得静默空值;
- SHA不符、ref越界/符号链接逃逸、错误child字段均拒绝且数据库字节不变;
- 多request/多RESULT只选规定的最新记录,父子不串位;
- Markdown与JSON内容一致,并验证新入口参数与错误输出。

## 本轮保留与未完成

- 保留测试专用假SSH及7个测试:upload-pack、receive-pack、非白名单、根外、
  两种`..`路径、符号链接逃逸。真实SandboxGit路径实测7 passed/0 failed/0 skipped。
  receive-pack只写临时本地裸仓库,没有访问真实Gerrit。
- 建档草稿的5例连同上述7例曾初跑12 passed/1.19s;未完成验收,仅记录事实,
  业务代码和该测试已撤回,不将其计入交付用例。
- `ssh-resume/implementation-wip.patch`与`wip-manifest.json`仅保存未验收定位资料,
  包括错误的相对路径读取草稿,禁止直接套用当作交付。
- 第2批命令/API、SKILL、CLI去重、屏障及其全部验收仍未交付;
  sandbox-submit与qb-trigger最终生产diff均0行。全量pytest/mypy、四组安全测试
  本轮NOT_RUN,未触发计时敏感用例重跑。已跑夹具ruff、collect、import-linter、
  设计检查与完整性核对,结果见progress及ssh-resume目录。
- 第1批2922用例保留情况见`ssh-resume/nodeid-diff.json`。
  不修改任何历史证据,不执行历史探针,不开始第3批。
