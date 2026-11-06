# SKEL-RESTORE-29 离线复现、结构诊断与回归

基线 `b7a55d8`。本目录没有真机操作、登录或包日志正文。所有浏览器均为本机
隔离解析或假HTTPS测试,经RESTORE-27的systemd scope/nice限制串行执行。
每个运行目录的`command.json`记录argv、UTC、exit、等待与前后free/loadavg。

## 复现

`replay.mjs`按`qb_collect.collect`实际顺序,用生产TrustedPage/discoveryDOM解析
已存在的脱敏归档,不执行页面脚本,再交给生产DiscoveryScope.consume。
`replay-before/`、`replay-checks/`是修改前独立记录,未覆盖。

| 页面类型 | 原归档(相对discovery-capture) | 修改前 | 修改后(replay-after) |
| --- | --- | --- | --- |
| parent_overview | live-02/02.response.html | 通过 | 通过 |
| parent_variables | live-02/03.response.html | 通过 | 通过 |
| child_overview | live-02/04.response.html | 通过 | 通过 |
| child_variables | live-02/05.response.html | 通过 | 通过 |
| report_entry | live-02/06.response.html | 通过 | 通过 |
| report | live-04/02.response.html | 首次失败REPORT_STRUCTURE | 通过 |

首个失败检查为旧`detailsPackages`的包名正则:报告零基第238行的name为
`toybox - details`(归档1482行),不是一个包。它紧随toybox的unresolvable行,
四格均无链接;其它格为依赖错误说明。报告共259行、四个表头。
父overview的已知坏标签`</thea&lt;USER&gt;`仍保留;该页通过且不是本次根因。
三次回放均network_requests=0、browser_closed=true。

修复仅忽略上述严格相邻、同名、无链接说明行,不产生包或日志登记。
普通包名、唯一failed链接、架构优先序、来源核对、精确URL与read_text规则不变。
`tests/node/test_qb_discovery_archives.mjs`直接复用原归档作为回归夹具,
并拒绝六种变体:孤立说明行、异名、有链接、前行failed、重复说明行、缺格。
已知归档坏标签不修改,不复制原始页面到新夹具。

## 封闭字段

结构错误在代理应答顶层提供三个字段,Python校验后保存在error.discovery_facts,
由原failure_facts路径写到驱动trace及CLI stdout的failure对象。旧错误码映射保持:
例如代理QB_READ_ID_MISMATCH仍映射QB_FETCH_FAILED,agent_error_code保留原码。
非结构性的下载/编码/网络错误仍用已有错误码/reason,不伪造结构检查事实。

- page_kind:parent_overview、parent_variables、child_overview、child_variables、
  report_entry、report、log、configuration。最后一项已由用户回复
  **“批准增加 configuration”**授权,用于既有--since配置页。
- first_failed_check:identity_mismatch、child_link_count、variables_missing、
  iframe_count、header_missing、header_duplicate、arch_unmapped、package_duplicate、
  cell_multi_link、link_text、link_path、structure_invalid、table_count、cell_count、
  package_name、row_limit、variable_duplicate、package_count。
- counts:仅actual_count、expected_count、row_index、column_index;各值为
  0至2^53-1的非布尔整数。row_index/column_index为零基,未取得的计数不编造。
  无URL、页面文字、身份、异常原文、请求头或正文。

未知架构仍先作为ARCH_NOT_ALLOWED包状态,不新增整构建停止;
arch_unmapped诊断用于尝试为这种包登记日志的拒绝路径。

## 落点与测试

| 内容 | 位置 |
| --- | --- |
| 说明行/固定失败检查 | qb_discovery_scope.mjs:80(detailsPackages) |
| 诊断枚举与净化 | qb_discovery_scope.mjs:6、30 |
| 已登记页面类型与诊断上下文 | qb_discovery_scope.mjs:138、148、244 |
| 错误应答及Build ID诊断 | qb_browser_agent.mjs:715、876 |
| Python严格校验/错误事实 | qb_browser.py:120、222 |
| Node各类型/失败项/敏感值扫描 | tests/node/test_qb_discovery_diagnostics.mjs |
| 六页真实结构和六个拒绝变体 | tests/node/test_qb_discovery_archives.mjs |
| Python枚举、非法字段、CLI映射 | tests/unit/test_qb_discovery_diagnostics.py |

上表生产文件均在`tizen-qb-verify/scripts/tizen_qb_verify/`下。
首次开发定向运行`focused/`51失败/21通过,原因是新Python校验引用尚未解码的变量;
修正后`focused-2/`71通过/1失败,剩余为新测试对既有QB_FETCH_FAILED映射的错误期望,
已修新测试,未改既有断言。原始记录均保留,不计作完整门禁通过证据。
最终门禁及完整pytest以本目录独立gate目录为准;完整门禁不使用-x。

## 最终结果:停止,未验收

mypy(172文件)、ruff、import-linter(7/7)、design(0 problem)、代理静态/单元
(183 Node测试)、四组拦截安全(4/4)均通过。完整pytest为3548通过、1失败、1既有skip;
3550 nodeid中既有3502全保留,新增48。唯一失败为C5a的build参数150秒子进程超时。
单独重跑第1次通过、第2次失败(close_seconds=20.91734027862549且fill UNKNOWN),
未跑第3次。完整负载及命令记录在各目录command.json,不覆盖原失败。

详见[SKEL-RESTORE-30停止报告](stop-report-SKEL-RESTORE-30.md)。事后有一个profile残留,
未擅自清理。修复和新增诊断保留待验收;没有进行r02或任何真实登录。

归档检查:六份既有真实页面经SessionPageRedactor复检身份残留为0,原文hash记录
在`integrity-and-archive-scan.json`。新增证据另做同一身份集合的全文扫描。
`collect/stdout.txt`与`full/pytest.xml`有测试标识符与已登记身份重合,仅这些标识符
替换为`[REDACTED_IDENTITY]`;前后hash与次数见`test-identifier-redaction.json`,
原始失败断言/输出不变。nodeid集合比较对前后采用相同的标识符替换。
通用HTML凭据检查器用于测试源码/测试输出时会拒绝合成的敏感值反例,
对应文件单列为page_checker_rejected_files,不宣称这些测试输出是HTML归档检查通过;
实际历史身份全文扫描独立执行,不得有残留。archive-check系列失败过程保留。

代理完整sha256由`309e7ab8877fe652d60cb6b27733431c633ef799a05ede5403358d147f4e22bb`
变为`5583d6bec7504fb3ef595bcd5612450a8b577340581f16b3a6fd981afd239ac1`;
以`export class Agent {`为末端的前缀前后均为
`594107e04912b90ef803b3f2a1142b5b42afab83399829dba4e3c8e95664095c`。
完整门禁后生产/测试文件哈希无变化。代理+11/-1行、驱动+45/-0行,
discovery scope +98/-30行;前缀内安全逻辑零改动。

文档/证据最终检查见`final-document-checks-2/`:exit0,design 0 problem,
证据脚本ruff通过、历史身份扫描0。完整暂存diff的空白检查仍指出原始pytest
stdout/XML及夹具HTML的行尾空白,为保留原始证据不清洗;代码与进度/design文档
diff --check通过。被通用build/忽略的三个C5a证据目录单独强制纳入,不改.gitignore。

## 边界

Policy、FrameOwnership、installGuards及Agent前源码前缀不变。
exactDiscoveryURL、read_text运行时检查、失败链接判据不放宽。
没有真实QuickBuild/Gerrit/gbs操作;没有建档、克隆、写状态库或创建构建。
r02必须门禁通过并收到用户新的“开始”后才执行;此前确认不复用。
