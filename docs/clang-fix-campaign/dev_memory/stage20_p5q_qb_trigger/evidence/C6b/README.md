# C6b Read-Only Live Evidence

执行基线9cc481f,2026-10-19;裁定P5Q-C6B-01见progress §45.1。
状态:C6完成,等待v1.6自动绑定。P5Q不标CLOSED。
本目录只存脱敏页面、结构事实、执行记录及只读SQL文本;没有state.db二进制。
没有修改生产代码、取证工具或冻结稿;没有触发构建、点击Accept或推送Gerrit。

## 两次执行

| 操作 | UTC开始/结束 | exit | DB前后 | 新增state文件 | 关闭观察尾段 |
|---|---|---|---|---|---|
| 生产qb-result-fetch,仅request-id | 07:16:07.430044 / 07:16:32.790632 | 0 | 相同,见下方完整hash | qb_evidence+4;qb_results+0 | 0.212571秒 |
| 既有五页比对工具 | 07:16:49.567295 / 07:17:31.919075 | 0 | 相同 | 0;工具证据独立存raw-active-01 | 0.318026秒 |

两轮DB SHA256均为
`08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30`。
三表campaign_qb_requests/profiles/events均1/1/3,最新unit状态SANDBOX_QB_PASS。
冻结稿SHA256仍为`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
两次均在启动前重新preflight,无P5Q代理/Playwright Chromium/profile/.transport残留。

- [reread-01/command.json](reread-01/command.json):完整生产argv,没有qb-build-id或额外开关。
- [reread-01/execution.json](reread-01/execution.json):UTC/exit/计时。
- [reread-01/stdout.json](reread-01/stdout.json):PASS,terminal=true,event_id=3,仍指向旧RESULT文件。
- [reread-01/post-audit.json](reread-01/post-audit.json):前后DB、完整文件hash清单及增量。
- [reread-01/trace-new.jsonl](reread-01/trace-new.jsonl):四页身份计数0,无失败trace。
- [raw-active-execution-01/](raw-active-execution-01):第二次前置与完整命令/退出/计时;stdout为空。
- [raw-active-01/run.json](raw-active-01/run.json):PASSED,login/五次read/close均ok。

新增生产证据为05.1201886-overview.html、06.1201886-variables.html、
07.1201889-overview.html、08.1201889-variables.html,原字节归档于
reread-01/state/qb_evidence/9fe02dc3927c4b7fa55a3dffce699d03/。
旧RESULT复用条件位于qb_result_fetch.py:500;本轮accepted仍null,没有触发追加RESULT。
每0.1秒观察进程,尾段指最后观察到Chromium至CLI/工具结束,不是直接close耗时。
代理退出码两轮均NOT_COLLECTED。与旧live-05/fetch尾段35.042秒分开记录。
两轮stderr都仅为一行固定登录提示,不是空文件,没有停止/异常类别输出。
登录两轮均成功,没有login_facts失败应答;不得称为真机验证了失败诊断的各分支。

## 逐页逐字段

列序号与raw-active-01/NN.comparison.json一致。所有导航核对VERIFIED,
原始正文/活动文档登记位置外身份计数每页均0/0。
“一致”包括不适用字段两侧都为空,不是声称每页都存在全部字段。

| 字段 | 01父overview | 02父variables | 03子overview | 04子variables | 05配置1917 |
|---|---|---|---|---|---|
| navigation | 一致 | 一致 | 一致 | 一致 | 一致 |
| summary | 一致 | 一致 | 一致 | 一致 | 一致 |
| child_build | 一致 | 一致 | 一致 | 一致 | 一致 |
| variables | 一致 | 一致 | 一致 | 一致 | 一致 |
| configuration_tabs | 一致 | 一致 | 一致 | 一致 | 一致 |
| breadcrumb | 一致 | 一致 | 一致 | 一致 | 一致 |
| copy_path | 一致 | 一致 | 一致 | 一致 | 一致 |
| build_name | 一致 | 一致 | 一致 | 一致 | 一致 |
| failed_steps | 一致 | 一致 | 一致 | 一致 | 一致 |
| error_message | 一致 | 一致 | 一致 | 一致 | 一致 |

工具没有重跑,没有替代路径。Build Requests/Recent Builds不属于工具的这十个
比较字段,另作离线全表字节与逐列检查,不能把50/50扩大成整个页面逐字节相同。
两张配置表的HTML不逐字一致,详细事实见[configuration-1917.md](configuration-1917.md)
及[configuration-tables.diff](configuration-tables.diff),仅为v1.6设计留样。

## 挂账关闭

下面旧文件路径均相对于`../C6a/live-05/fetch/state/qb_evidence/9fe02dc3927c4b7fa55a3dffce699d03/`,
新文件均相对于`raw-active-01/`;行号为HTML源行号。

| 核对 | 事实 | 旧文件:行 | 新文件:行 |
|---|---|---|---|
| 子Summary Status | Successful,归一PASS | 03.1201889-overview.html:830 | 03.raw-redacted.html:830 |
| 父Child Build Build Result | SUCCESSFUL | 01.1201886-overview.html:891 | 01.raw-redacted.html:891 |
| EACH_GBS_BUILD_STATUS | 存在且值为空 | 04.1201889-variables.html:802 | 04.raw-redacted.html:802 |
| 父SNAPSHOT_NUM | tizen-base-toolchain_20261013.024319 | 02.1201886-variables.html:810 | 02.raw-redacted.html:810 |
| 子SNAPSHOT_NUM_URL | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319 | 04.1201889-variables.html:802 | 04.raw-redacted.html:802 |
| BUILD_NOTES | clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03 | 02.1201886-variables.html:810 | 02.raw-redacted.html:810 |

成功样本=CLOSED,BUILD_NOTES样本=CLOSED。相应四页规定字段全部一致。
父快照=冻结值=子URL末段,生产snapshot_kind=same;父值仍只记录不作判据。
BUILD_NOTES单元格未经strip的文本与内部HTML均逐字等于标记,
无首尾空白、HTML转义、换行或截断。全部结构化事实及source字段见
[offline-analysis.json](offline-analysis.json)。生产解析只运行在已归档的脱敏HTML上。

## 验收与边界

[validation.json](validation.json)记录设计检查、逐文件原字节脱敏自检、JSON/JSONL
字符串递归自检、冻结文件/既有工具不变核对及diff检查。原始HTML和差异摘录的
行尾空白照原字节保留,完整diff检查与排除原始证据的检查分开报告。
本轮不运行全量pytest;§44的2709 passed/1 skipped是历史离线修复结果。

仍开放:v1.6自动查找绑定(三方评审冻结+实现)、验证性真实提交、
live-01/live-04登录超时原因。P12真实sandbox推送观察与Unified配置原样挂账。
本轮没有新的冻结稿/裁定不一致或做不到之处,没有新增停止报告。
