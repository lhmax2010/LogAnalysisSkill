# 恢复第3批首步:发现所需URL形态

日期:2026-11-04。实现基线`7484f58`(恢复第2批已提交推送)。
本记录只执行SKEL-RESTORE-01第三.1,完成即停止等待设计方裁定。
没有访问任何URL、启动浏览器、读取Cookie文件或修改代理/测试。
下文的URL都是本地材料中的文字,不是本轮请求记录。

## 1. 搜索范围与证据等级

实际搜索了stage20的`evidence/`(重点C6b/raw-active-01、C2b/live-12、C8/live-02)、
`tests/fixtures/`、`tests/unit/`、`tizen-ci-triage/scripts/ci_triage/`、
`tizen-triage-report/scripts/tizen_triage_report/`、`tizen-qb-discover/scripts/tizen_qb_discover/`、
`tizen-ci-shared/scripts/tizen_ci_shared/`及现行`tizen-qb-verify`源码。
另在仓内`dev_memory/`检索GBS路径,找到stage21预筛的`source-facts.json`;
stage14的callable-id-scan只是代码快照,不是页面取证,不作为真机URL证据。
没有重新读取预筛记录指向的仓外日志,没有运行历史证据脚本。

为缩短下文引用,定义仓内路径前缀:

- **C6b** = `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6b/raw-active-01/`
- **Selection** = `docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/batch3.5/selection/`
- **Agent** = `tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs`

等级A为真机脱敏页面正文,等级B为既有本地采集记录,等级C为现有代码/合成夹具。
代码能够拼出某URL不等于该形态已在当前Base配置实测。

## 2. 路径事实表

所有同源例子的origin为`https://quickbuild.tizen.org`,以下只列path。

| 用途 | 本地可证形态/例子 | 来源文件:行号 | 等级与限制 |
| --- | --- | --- | --- |
| 构建列表 | `/overview/1917`,Recent Builds六列,行链接`/build/1202070` | C6b `05.raw-redacted.html:4,48,892,907,909,911,913,915,917,936` | A;配置路径是Base/RBS/TRIGGER,不推断其它项目ID |
| 列表中的非读取链接 | `javascript:void(0);`菜单,带`ILinkListener-...-stop`的Wicket链接 | 同文件`:937,939` | A;二者不登记、不点击,破坏性监听器继续永久拒绝 |
| 旧发现入口 | `/overview/<overview_config_id>`;默认1930;仅过滤当前Recent Builds窗口 | `tizen-qb-discover/scripts/tizen_qb_discover/sources.py:22,67,86` | C;不能把默认1930套用到Base,历史分页URL为UNKNOWN |
| 父构建变量 | `/build/1201886/variables`;`BUILD_PKG_LIST_MODIFY`和`PROJECT_BRANCH` | C6b `02.raw-redacted.html:48,810` | A;本例目标行在MODIFY,不能混同子构建全量列表 |
| 子构建变量 | `/build/1201889/variables`;`BUILD_PKG_LIST`为多行`project@commit` | C6b `04.raw-redacted.html:4,48,691,802` | A;标题/复制路径为Base/RBS/build,行802同时含PROJECT_NAME等变量 |
| GBS入口的真实导航标签 | 相对`html_report`,从上述子页解析为`/build/1201889/html_report` | C6b `04.raw-redacted.html:791` | A;只证实标签,没有该目标页的响应正文 |
| 旧GBS入口 | `/build/<N>/gbs_reports/<arch>`,例`/build/111/gbs_reports/standard-armv7l` | `tizen-triage-report/scripts/tizen_triage_report/gbs_report.py:68`;`tests/unit/test_tizen_triage_report.py:163,183` | C;当前Base多架构构建是否使用此入口为UNKNOWN |
| iframe目标夹具 | `/download/111/html/GBS%20Reports@%5E@standard-armv7l/index.html` | `tests/unit/test_tizen_triage_report.py:168,186`;解析基址逻辑见`gbs_report.py:72,79` | C;不得将111或该单架构形态当作真机Base事实 |
| 单包日志夹具 | iframe下`logs/fail/lightweight-web-engine-1.3.31-1/log.txt` | `tests/unit/test_tizen_triage_report.py:57,150`;`gbs_report.py:325` | C;由报告行href解析,不是由包名猜地址 |
| 多架构日志采集记录 | `/download/1204735/html/GBS Reports@^@standard-armv7l:aarch64:x86_64/logfiles/standard/armv7l/zlib.txt`及aarch64/x86_64 | Selection `source-facts.json:39,46,53` | B;原记录含空格/裸分隔符,不能直接当作CDP wire URL |
| 编码后的多架构日志记录 | `/download/1203397/html/GBS%20Reports%40%5E%40standard-armv7l%3Aaarch64%3Ax86_64/logfiles/standard/armv7l/zlib.txt`及另两架构 | Selection `source-facts.json:61,67,73` | B;libtirpc和elfutils同类例子见`:229,397`;不证明任意包/构建都适用 |
| 完整构建日志旧路线 | `/build/<N>/log`再取`ILinkListener-content-buildTab-panel-download`链接 | `tizen-ci-shared/scripts/tizen_ci_shared/quickbuild_http.py:17,117,129,143` | C;本轮不建议启用,变量页优先,不放开Wicket下载监听器 |
| 公网日志旧路线 | `http://download.tizen.org/RBS/.../tizen-unified-toolchain_<stamp>/builddata/buildlogs/...` | `quickbuild_http.py:18,150`;`tests/unit/test_ci_triage.py:1268,1276` | C;仅Unified派生规则,非同源且HTTP,本轮候选明确排除 |

`ci_triage/quickbuild_log.py:18,50,117`只解析完整日志里的`build_pkg_list_dic`、
fail_pkg/spec_name和包映射,不提供变量页URL、iframe地址或branch权威来源。
不能把它当成缺失变量的推断器。现有变量核对代码可参照
`tizen_qb_verify/qb_result_html.py:293,298,353`,但本轮不执行业务CLI。

**明确UNKNOWN:**当前Base GBS报告入口的完整响应、真实iframe的src、其内容类型/
charset/Content-Disposition、日志是否触发浏览器Download而非主帧导航、实际重定向链、
iframe到包日志的原始链接字节、多架构编码在浏览器/CDP中的精确表示、超出Recent Builds
窗口的历史分页。不能从`logfiles/...`反推出`index.html`,也不能把旧夹具当这些事实的补证。

### 2.1 RESTORE-08一次真机补证结果(2026-11-04)

授权脚本、离线7项验证及唯一一次现场执行见[discovery-capture/README.md](discovery-capture/README.md)。
登录成功后首个`/overview/1917`主帧GET观察到HTTP 200、
`Content-Type: text/html;charset=utf-8`,未观察到Content-Disposition或Download。
随后Fetch.continueRequest/REQUEST_ID_INVALID触发FETCH_CONTINUE_FAILED,
导航未完成,正文未归档。完整重定向链未取得,不能用空数组证明无重定向。

| 原UNKNOWN | 本次补证状态 |
| --- | --- |
| Base GBS报告入口正文 | NOT_COLLECTED;未到达html_report |
| 真实iframe src、内容类型/charset/Content-Disposition | NOT_COLLECTED;保持UNKNOWN |
| 日志是否为文本或触发Download | NOT_COLLECTED;保持UNKNOWN |
| 实际重定向链 | 首页请求/响应事件redirect=false,导航未完成;后续链UNKNOWN |
| iframe到日志原始href、多架构CDP编码 | NOT_COLLECTED;保持UNKNOWN |
| 历史分页 | 本轮裁定明确不实现;outside_recent_window边界保留 |

第4节原候选原则已由RESTORE-08裁定,但其第三.1自动实施的四项事实前提没有取齐。
按[SKEL-RESTORE-09停止报告](discovery-capture/stop-report-SKEL-RESTORE-09.md)停止,
不实施任何代理扩展,不重试。

### 2.2 RESTORE-10重取证结果:live-02(2026-11-04)

修复b29d6f3与完整离线门禁先行,用户回复“开始”后一次执行,没有重试。
六个固定页面均200且已脱敏归档;详见`discovery-capture/live-02/run.json`。
父/子overview配置身份与1204735→1204736关系核验通过。

| 原UNKNOWN | 本次取得的事实与来源 |
| --- | --- |
| Base GBS入口完整正文 | `/build/1204736/html_report`,`live-02/06.response.html`;200,text/html;charset=utf-8,无Content-Disposition/Download |
| 唯一iframe src | `06.response.html:803`原文`/download/1204736/html/HTML REPORT/index.html`;目录名为HTML REPORT |
| iframe实际wire path与响应元数据 | 未取得。标准URL离线计算为`/download/1204736/html/HTML%20REPORT/index.html`,不是观测到的网络响应;`live-02/path-probe.json` |
| 日志href、文本/Download、编码与重定向 | 全部NOT_COLLECTED,保持UNKNOWN;未到报告内容页 |
| 实际重定向链 | 六个固定主帧导航均单跳;iframe与日志仍UNKNOWN |
| 历史分页 | 仍不实施,outside_recent_window边界不变 |

取证工具在标准URL解析前拒绝原始src的ASCII空格,CAPTURE_PATH_UNSUPPORTED,
exit4。未出现OPERATION_FAILED/AGENT_STOPPED,profile已删除。
父overview登记位置外身份计数2,其余五页0,需要人工确认新身份位置。
四条件尚未齐备,不能进入实现;见
[SKEL-RESTORE-11](discovery-capture/stop-report-SKEL-RESTORE-11.md)。

### 2.3 RESTORE-14补读结果:live-03(2026-11-05)

41ce708离线门禁完成,用户确认“开始”后只执行一次剩余三页入口。
登录ok=true,首个`/build/1204736/html_report`主帧单跳GET为200、
text/html;charset=utf-8,无Content-Disposition/Download,
但正文worker返回QB_EVIDENCE_REDACTION_FAILED,未归档正文,立即停止。
见`discovery-capture/live-03/run.json:7`、`:61`、`:64`。

| 原UNKNOWN | 本次结果 |
| --- | --- |
| iframe实际wire path及响应元数据 | 仍UNKNOWN;未进行显式主帧读取 |
| 日志href、编码、Content-Type、Download与跳转 | 仍UNKNOWN;未到iframe内容页 |
| html_report响应元数据 | 再次确认主帧HTTP200、单跳,但本次没有正文可复核src |
| 会话身份全页遮蔽与复检 | 本次失败,替换次数/残留均NOT_COLLECTED,不能写0 |

RESTORE-12已确认live-02旧身份计数2实际涉及漏遮蔽并完成后处理;
第2.2节历史计数不作为身份安全通过依据。坏标签保留,见capture README。
新取证没有重读前六页、没有请求其它包、没有重试;
四条件未齐备,不进入第三/四批实现。
[SKEL-RESTORE-15报告](discovery-capture/stop-report-SKEL-RESTORE-15.md)给出事实与候选诊断,
不把统一错误码推断为已证实的具体根因。

### 2.4 RESTORE-16补读结果:live-04(2026-11-05)

5721a32最终树门禁通过并收到新的“开始”后只执行一次。登录成功,
html_report与其唯一iframe均主帧GET200、单跳、无Download,已脱敏归档。

| 原UNKNOWN | 本次取得事实 |
| --- | --- |
| iframe实际wire path | `/download/1204736/html/HTML%20REPORT/index.html`;`discovery-capture/live-04/run.json:28,80` |
| iframe响应 | text/html; charset=utf-8,`inline;filename*=UTF-8''index.html`,200;`run.json:30` |
| 报告表结构 | name / standard armv7l / standard aarch64 / standard x86_64;`02.response.html:47` |
| zlib日志原始href | `logfiles/standard/armv7l/zlib.txt`,唯一zlib行中主架构唯一链接,链接文字failed,没有class属性;`02.response.html:1596,1597` |
| 日志响应/编码/Download/跳转 | NOT_COLLECTED;工具class=failed选择器未匹配,日志未读取 |
| 脱敏/私有原文 | 两页替换次数1/0,身份残留0,归档后私有原文已删除;`run.json:221` |

CAPTURE_LOG_LINK_MISMATCH为工具首个停止原因。退出过程中trace另记
Fetch.continueResponse/REQUEST_ID_INVALID(idle,response,generation5)与
FETCH_CONTINUE_FAILED;此操作没有豁免。没有重试/读其它包,
四项事实未齐备,不进入第三/四批实现。见
[SKEL-RESTORE-17报告](discovery-capture/stop-report-SKEL-RESTORE-17.md)。

## 3. 当前拦截与读取边界

- Agent`:88`的readonly仅含build裸页/overview/variables/step_status和登记overview。
- Agent`:114`开始的永久禁止含异源/HTTP、WebSocket、REST、破坏性监听器、
  `/build/N/(log|html_report|artifacts)`及307/308;`/download/`当前也没有放行分支。
- Agent`:243`先检查帧归属,`:255`至`:275`只捕获当前主帧Document导航的原始正文。
  现有read不读iframe活动文档;即使允许iframe网络也不会自动返回其正文。
- Agent`:759`的read只认readonly路径,最终地址逐字比较,对build路径还核对Build标签。
  `TrustedPage`在`:411`以DOMParser解析HTML;`:430`严格解码原始字节。
  单纯加路径不能证明纯文本编译日志会被无损返回。含`<...>`的日志不能未经文本转义
  就当HTML解析;日志如何脱敏并供真实analyzer读取,尚需应答契约裁定。

## 4. 白名单最小扩展候选(仅文字diff,待审批)

不建议开放目录前缀、任意构建号、任意`/download/`或Wicket监听器。候选方案使用
**发现会话专用的精确路径表**;未启用发现作用域时P5Q现有行为完全不变。
登记只能由代理校验过的项目配置身份、构建归属和惰性文档链接产生,不能由CLI直接
把任意URL塞进表。登记协议名字、字段和新的响应格式待设计方明确,下列为策略层示意,
不是可直接应用的完整patch。

```diff
 class Policy {
   constructor(overviewIds = []) {
+    this.discoveryScope = null; // 未启用时保持现行P5Q路径
+    this.discoveryReads = new Map(); // 精确path -> {kind, project, buildId, arch}
   }
   readonly(path) {
+    if (this.discoveryScope !== null) return this.discoveryReads.has(path);
     return /* 原有P5Q只读集合 */;
   }
   allow(m, requestId = '') {
+    const entry = this.discoveryReads.get(m.path);
+    const discoveryGET = this.discoveryScope !== null && this.phase === 'read'
+      && m.method === 'GET' && !m.query && entry !== undefined;
+    const exactReportEntry = discoveryGET && entry.kind === 'report-entry'
+      && m.path === `/build/${entry.buildId}/html_report`;
     if (/* 原有异源/HTTP/WS/REST/破坏性检查 */
-      || /^\/build\/\d+\/(log|html_report|artifacts)(?:\/|$)/.test(m.path)
+      || (/^\/build\/\d+\/(log|html_report|artifacts)(?:\/|$)/.test(m.path)
+          && !exactReportEntry)
       || [307, 308].includes(m.response_status)) return false;
     if (m.response_status !== null) return this.active.has(requestId);
     /* 原有静态资源与登录分支不变 */
+    if (this.discoveryScope !== null && this.phase === 'read') return discoveryGET;
     /* 其余原有阶段分支不变 */
   }
 }
```

精确表的拟议来源/约束:

1. 列表仅登记选定`qb.projects`项目的overview;先核对配置身份。构建号只能来自该列表
   的普通链接及已核验父页Child Build关系;显式`--build-id`的首个身份核验如何引导登记
   必须由设计方明确,不可用“先读任意构建再说”绕过作用域。
2. build overview/variables继续现有原始正文、地址、Build标签核对,并验证配置路径。
   不同项目、未证实子关系的id不得登记。branch/source commit不能从构建名猜测。
3. 报告入口仅精确登记经证据确认的链接;当前真机只知html_report导航,
   gbs_reports属于旧夹具候选,不能静默双路径试错。
4. iframe目标与日志href必须来自已核验的上一层惰性文档,解析基址用最终核验请求URL;
   同源HTTPS、无查询/片段/用户信息、路径中的N等于已核验构建,架构受白名单与失败包
   前置门控制。只登记实际选中主架构所需的日志,不得批量开放所有产物。
5. URL只由标准URL解析器产生一次与CDP一致的表示,不自作多次decode/encode;
   字节等价规则待真实编码证据/设计确认。禁止路径穿越、编码的路径分隔符与跨构建跳转。
6. 读取iframe采用显式下一次主帧导航还是新增受控读取应答,以及纯文本日志的取得/
   脱敏/无损返回,需裁定。**不修改installGuards来直接放行任意子帧或Fetch请求。**

pathShape候选只增固定类别,沿用phase+shape trace,不记包名或查询:

```diff
 export function pathShape(path) {
+  if (/* 已批准报告入口文法 */) return '/build/<id>/<report>';
+  if (/* 已批准iframe文法 */) return '/download/<id>/html/<report>';
+  if (/* 已批准单包日志文法 */) return '/download/<id>/html/<report>/<package-log>';
   /* 原有规则与<other>兜底不变 */
 }
```

这里有且仅有一项拟议永久禁止例外:已登记项目/构建的精确html_report GET。
它尚未获准,不能以本文件代替裁定。`/log`、`/artifacts`、REST、外站、所有破坏性动作
和307/308仍拒绝;只记录其它缺失文法,不凭UNKNOWN补正则。

## 5. 批准后所需Node正负例

| 组 | 正例 | 负例/服务器判据 |
| --- | --- | --- |
| 作用域 | 已核验项目overview、已证实父子构建的overview/variables | 未登记项目/id、伪造配置、构建号多/缺/错,拒绝或核对失败;不登记下游 |
| 精确报告GET | 单个已登记html_report或经后续证据批准的GBS入口 | POST/HEAD、query/fragment、改一字符、额外路径段、其它阶段,服务器0请求 |
| iframe | 上层唯一已核验src的同源精确URL,显式受控取页 | 外站/HTTP、其它build id、多个歧义src、blob/data、未知帧,服务器0请求 |
| 包日志 | 已核验失败行、已批准主架构、原始href解析的精确URL | 其它包/架构/id、任意产物、目录穿越、双重编码、修改编码形式,服务器0请求 |
| 内容与保密 | 原始字节严格解码、日志中尖括号/换行保真、登记身份脱敏 | 无正文、非法字节、Download行为未支持、身份自检失败,不回退主环境/请求上下文 |
| 逐跳 | 同一已登记路径的响应按active请求核验 | 307/308、异源/未登记302落点、跳到写监听器仍逐跳拒绝 |
| 不扩权 | 旧P5Q允许/拒绝矩阵原断言全过 | stop/cancel/Accept/Ready to Accept、run/submit、WS、Worker/新页面继续阻断 |
| trace | 固定pathShape,登记/拒绝可审计 | 查询值、账号、请求体/头、日志正文不进trace |

另需C5a假HTTPS集成:服务器实收清单、命令清单分别核对;模拟多架构报告,
arch前置门先于日志读取,只读失败不自动试另一条路径。新scope不影响原P5Q提交/结果
测试;重跑既有C5a/C8(按已生效观测规则)与四组安全测试,代理静态断言全保留。
本轮没有新增或运行这些未来用例。

## 6. 停点

按RESTORE-01第三.1.c在此停止。请求设计方确认精确登记来源/引导、html_report例外、
真实iframe与多架构编码补证方式、纯文本下载读取与脱敏应答契约及历史列表覆盖边界。
UNKNOWN不当作不存在,也不当作可放行。第二批的完整离线门禁见
`batch2/r06/README.md`;第三批本次仅文档,不宣称campaign-discover已实现,
不进入恢复第4批。
