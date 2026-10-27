结论：**建议修改后冻结。** 第 2.1 批已明显改善，已有真实验收结论可以保留；但完成状态、日志缓存和部分异常抓取仍有缺口。第 3 批设计最需要补强的是源码还原的证据，以及分析准确性的验收标准。

已核对三份材料哈希，确认目标代码与 `3fd6470` 一致。全程未修改仓库文件。测试及补充实验均使用仓库外临时目录：

- `test_batch21`、`test_http_workflow` 共 **47 项通过**，TLS 握手和 CONNECT 测试未跳过。
- 补充实验复现了旧完成状态覆盖新观察、旧短日志复用、残缺 chunked 消息被接受、回环地址别名通过预检等问题。
- 未访问内网 Cosmos、Perforce 或 ClineSR；相关设计结论依据文档、代码及官方接口说明。

以下 diff 均为候选修改，含接口伪代码，未应用。

---

**第一部分：HLD 两轮改动**

**H1｜一般｜“定型”仍被写成不可变事实，超过 settle_s 只是经验判据**

位置：§5.4 第 3、10 条，§9.2。

触发条件：发布过程暂停超过 1800 秒，或者构建已经结束、报告仍在异步发布。当前文字“只有定型才说明它不会再变”过强；停止条件仅覆盖坏报告，自洽但不完整的快照可能进入“结果已拉取”后不再观察。

候选修改：

```diff
- 只有定型才说明它不会再变。
+ “定型”是本次快照的判定条件，不保证服务端永不重新发布。
+ 保存 settled_basis=trusted_terminal|elapsed_window。
+ 仅依靠 elapsed_window 完成读取时，保留低频观察；
+ 内容变化即使旧完成评估失效，重新判定和下载。
+ elapsed_window 不赋予终态可信级别，也不证明日志不可变。
```

副作用：详情页长期不可用时会继续产生少量只读请求，需要人工停止或 abandon。

测试夹具：运行中自洽页面静止超过 settle_s，之后增加包；终态先出现、报告稍后更新；旧完成评估必须失效。

**H2｜重要｜详情页身份核对没有把构建号与状态元素关联起来**

位置：§5.4 第 11 条；[observation.py:14](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/observation.py:14)。

触发条件：页面主体是构建 9999，但推广链接或历史记录提到目标构建号。全文出现目标编号即可通过身份核对，随后取第一个状态元素。

已复现：

```html
<h1>Build 9999</h1>
<span title="Build is successful"></span>
<p>Upstream build 19091860</p>
```

查询 19091860 得到 `identity_match=true`、可信“已结束”。这会同时影响定型和后续终态闸门。

候选修改：

```diff
- 可见文字里出现本构建号即通过身份核对。
- 选择全文第一个 Build is 状态元素。
+ 按录制页面验证过的头部定位规则提取当前构建身份；
+ 构建号和总体状态必须属于同一个已识别的构建头部。
+ 全文、推广区或历史区出现目标编号不算身份匹配。
+ 头部缺失、身份冲突或状态候选歧义时记 identity_mismatch/未知。
```

副作用：布局漂移时可能需要人工确认终态；不需要恢复保存详情页原文。

测试夹具：上述反例；目标编号只在下游区域；错误构建头部；多个状态候选；正常真实头部。记录净化后的定位依据。

**H3｜重要｜路径存在、文件名唯一，不足以证明拿到了本轮编译源码**

位置：§6.1 第 1、1a 条。

触发条件与后果：

- `%prep` 打补丁、解包或生成文件后，编译路径不再直接对应 depot 文件。
- `...<文件名>` 是后缀匹配，寻找 `foo.c` 可能唯一命中 `notfoo.c`。
- 历史构建使用的 shelf 后来被更新；现在读取 `@=CL` 得到的是当前 shelf。
- 主错误文件定位成功但超过大小限制，实际未取内容，却没有明确规定必须降级。

现有“无法可靠还原则仅诊断”方向正确，但缺少可执行的可靠性判据，容易被“命中一个文件”替代。

候选补充：

```diff
+ 路径换算先产生候选，不直接标为源码定位事实。
+ 候选必须满足：属于本包 depot 根、basename 精确相等、
+ 版本和文件动作已核实，且有打包映射或诊断上下文支持。
+ 禁止把日志中的 ..、通配符、@/# 修订语法直接拼进 filespec。
+ 明确记录 base 来源及每个文件的 depotFile/#rev、类型、摘要；
+ shelf 取前取后核对动作与摘要，变化则作废本次快照。
+ 无历史 shelf 摘要时不得声称已还原历史构建输入。
+ 主错误文件未取到内容、生成过程未知或映射仍不确定：
+ diagnostic_only；不得以同名文件或 head 替代。
+ symlink 类型不得在 inputs/ 中创建可指向外部的真实符号链接。
```

副作用：部分样本会降为仅诊断；这是保留证据不足，而不是强行产出可编辑方案。

测试夹具：`foo.c/notfoo.c`；重复 basename；打包补丁改变行内容；生成源码；shelf 新增/删除/移动及抓取中变化；超过上限的主文件；指向任务外的 symlink。

**H4｜重要｜P4CLIENT 置空不能单独证明连接上下文已隔离；登录待办也缺少同一上下文约束**

位置：§3 第 6 条、附录 B。

触发条件：P4CONFIG、P4ENVIRO 或默认 client 仍提供有效配置；FatTank 在另一个目录执行裸 `p4 login`，登录的是另一服务器、用户或票据文件。

官方文档明确配置文件可以覆盖环境变量，未指定 P4CLIENT 还有主机名默认值；`p4 print` 也有处理 ChangeView 限制的选项。因此不能由空字符串推出“完全不受 client 配置影响”。这些只读命令本身不会执行 sync/edit，但仍可能读错版本或一直无法恢复。[配置优先级](https://help.perforce.com/helix-core/server-apps/cmdref/current/Content/CmdRef/p4_set.html)、[P4CLIENT 默认值](https://help.perforce.com/helix-core/server-apps/cmdref/current/Content/CmdRef/P4CLIENT.html)、[p4 print](https://help.perforce.com/helix-core/server-apps/cmdref/current/Content/CmdRef/p4_print.html)。

候选修改：

```diff
+ P4 子进程使用白名单环境和本线固定 cwd；
+ 隔离 P4CONFIG/P4ENVIRO，拒绝从共享配置继承 client、服务器或用户。
+ 只接受绝对 depot filespec，核验返回的 depotFile、revision；
+ 按构建机 P4 版本验证 ChangeView 不会改变指定版本的读取结果。
+ login -s、files、describe、print 使用同一连接和票据路径配置。
+ 登录待办给出同一服务器、用户、票据路径下的人工登录方式；
+ 工具不读取或打印票据内容，不执行 login -p。
+ 网络失败、权限不足、未登录、有效期不足分别处理。
```

副作用：需增加一次有效配置探针；不能靠清空环境后碰巧继承默认票据来恢复。

测试夹具：共享 P4CONFIG 指向别的 client；P4ENVIRO 覆盖服务器；默认 client 带 ChangeView；登录到错误服务器；无限期票据；网络失败；取源码期间票据失效。检查共享工作区和配置前后未变。

**H5｜重要｜让 ClineSR 自述可用 skill，不能证明工作区隔离成立**

位置：§6.4、§12 第 3 批第③项。

触发条件：扩展仍加载全局 skill、规则或 MCP 工具，但模型回答时遗漏。现在“隔离不成立可人工兜底”与验收“只看到分析 skill”也存在口径冲突。

候选修改：

```diff
- 验收实测：让它列出可用 skill。
+ 隔离验收依据扩展加载清单、有效配置与文件摘要；
+ 模型列举仅作辅助观察。
+ 用无敏感内容的全局/父工作区哨兵 skill、规则和工具验证加载边界；
+ 同时核验命令、文件编辑、工作区外读取及外部工具的自动批准状态。
+ 无法排除额外来源时，标“隔离未通过，人工监督模式”；
+ 人工监督模式可以按负责人裁定使用，但不能计为隔离验收通过。
```

副作用：可能需要单独 VS Code profile 或额外人工检查。这里不要求把已声明的同账号信任边界改成操作系统沙箱。

测试夹具：仅任务 skill；全局哨兵；父工作区规则；额外工具自动批准；skill 文件在 prepare 后改变。不得使用真实凭据作探针。

**H6｜重要｜两档清单需要明确匹配语义，并补上明显危险诊断**

位置：§6.3、附录 B。

触发条件：

- 只匹配 `-Wformat` 或字符串前缀，漏掉实际输出的子诊断。
- “tautological-compare 一族”没有可执行的成员规则。
- 当前明确排除 `-Wformat-security`，但这类诊断可能对应格式串漏洞；`-Wreturn-stack-address` 等也未覆盖。
- “需看一眼”没有对应确认记录，选项修法可以把提醒直接带过去。

Clang 将 `-Wformat-security` 列为潜在不安全格式串诊断，且 warning group 与实际诊断名称并不总相同。[Clang 诊断参考](https://clang.llvm.org/docs/DiagnosticsReference.html#wformat-security)。

候选修改：

```diff
+ “确定档”改名“强制人工定性档”，不表示工具已确认真 bug。
+ 使用编译器版本化的精确诊断映射，规范化 -Werror=xxx；
+ 不从命令行参数、建议文本或未知选项名称推断诊断命中。
+ 补入 -Wformat-security、-Wreturn-stack-address、
+ -Wnull-dereference 等候选，由 FatTank 审定。
+ 需看一眼档采用选项方案时，人工确认事件必须记录该提醒已检查。
+ 判断依据绑定诊断位置与上下文，不能只按 warning 名称跨条目沿用。
```

副作用：人工定性量会增加；应允许有依据的“非真 bug”确认，避免宽泛 warning group 造成长期误伤。

测试夹具：真实危险用法与合法近似用法成对；子诊断、`-Werror=`、选项只出现在命令行；同标志多个根因；被压缩掉的非主错误仍可触发检查。

**H7｜重要｜第 3 批验收目前能证明流程跑通，不能充分证明分析准确**

位置：§11“分析（真实）”、§12 第 3 批。

触发条件：结果符合 schema，但根因错误；或推荐方案与 fix5 不同、实际却同样正确。简单的“一致/不一致/说不清”既可能误判，也可能把历史修法当成唯一正确答案。若参考 CL 或案例提前进入任务包，还会变成答案复述测试。

候选修改：

```diff
+ 验收前冻结样本、日志、源码、编译条件和参考修法摘要；
+ 参考修法及其派生案例在首次分析时不提供给分析者。
+ 分别评估：证据提取、源码定位、根因解释、方案可行性、
+ 真 bug 处理与规则符合性，记录判定依据。
+ 与历史修法不同不直接判错；由人工核对等价性或更优理由。
+ 只通过 schema 不算准确；“说不清”记未验证，不计正确。
+ 已知真 bug 的选项规避检出率要求 100%，越包/错版本编辑为 0。
+ 至少选取可执行验证的代表方案复现原诊断并验证修复；
+ 未编译的样本明确标“人工认可，编译未验证”。
```

副作用：第 3 批验收比接收 JSON 更费时；无需提前实现整套自动 fix-apply，可以使用隔离的人工验证。

测试夹具：schema 合法但根因错；不同但等价修法；照抄泄露参考答案；源码不完整；修复首个错误后暴露下一层错误；已知真 bug 被抑制。

**本部分未发现问题的范围：** package_coverage 与 result_state 分离、manual_file 不满足起轮闸门、停止推进后低频观察、日志分析器定位为证据提取、专用 venv 和 `--no-tiktoken`、Obsidian 作为单向快照导出、LLM Wiki 延后处理，方向均合理。检查了附录 G、§3、§5.4、§6.1—6.4、§7.6—7.7、§9.2—9.3、§11—12、§14、附录 B，并对照了已有分析器与 patch-suggest 接口。

---

**第二部分：第 2.1 批代码**

**C1｜重要｜完成状态仍可能覆盖更新的观察，也没有验证实际日志产物**

位置：[workflow/api.py:82](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-workflow/src/vd_cosmos_workflow/api.py:82)、[versions.py:19](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/versions.py:19)。

触发条件及已复现结果：

- 完成后删除实际 `log.txt`，日志清单 JSON 仍在：tick 返回 `action=none`。
- 连续记录重置，新观察为“部分/运行”，但 HTML 摘要与旧完成相同：仍返回“结果已拉取”。
- 增大日志截断上限：评估标识不包含该参数，完成流程不重新取得更多内容。

候选修改：

```diff
- if completed_evaluation == evaluation(reader, previous):
+ if (ready(previous)
+     and completion_covers_latest_observation(state)
+     and completed_evaluation == evaluation(reader, previous)
+     and validate_log_files_and_bindings(state['logs'])):
      return completed

+ evaluation 增加影响读取结果的配置版本，如 max_log_bytes。
+ 观察重新进入未定型/失败状态时撤销旧完成有效性；
+ 恢复后重新关联有效日志和通知。
```

`validate_log_files_and_bindings` 必须检查实际文件存在、摘要、大小及当前绑定，不能只校验日志清单 JSON。

副作用：恢复/状态变化时多做检查；大日志摘要计算应只在必要边界执行，避免每次 status 全量读取。

测试夹具：上述三个复现；日志内容损坏；新观察失败后恢复同字节；无变化时仍不重复下载和通知。

**C2｜重要｜日志缓存绑定报告摘要，仍不能识别“报告没变、日志增长”**

位置：[http_reader.py:224](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/http_reader.py:224)、`read_ops.py:20`。

触发条件：运行中通过手工 fetch 提前取得短日志，报告 HTML 随后不变，但日志继续追加。终态后仍命中旧缓存。

已复现：先保存 `early log`，服务器随后改成最终日志；报告完整后调用 fetch 得到 `skipped=true`，内容仍是旧短日志。

候选修改：

```diff
+ 日志回执记录取得时的报告成熟状态、执行状态和来源验证器。
+ 未定型/运行中取得的日志只作为 provisional 缓存。
+ provisional 日志在最终读取阶段必须重新获取或验证服务器版本；
+ 不能仅凭 report_sha256 相同升级为最终日志。
+ 无法确认服务端不可变性时，采用明确的重新验证策略。
```

副作用：提前手工下载可能在终态后再下载一次；正常已结束构建仍可保留本轮缓存复用。

测试夹具：报告字节不变、日志增长；执行未知转终态；无 ETag；验证器变化；最终日志不变时避免无谓重复传输。

**C3｜重要｜chunked 尾部不完整仍被标为传输完整**

位置：[transport.py:237](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/transport.py:237)。

当前用 `response.isclosed()` 判断正常结束，但底层读取器关闭并不证明 chunked 终止结构完整。

已复现以下两种残缺消息均返回 `transfer_complete=true`：

```text
3\r\nabc\r\n0\r\n
3\r\nabc\r\n0\r\nX-Trailer: unfinished
```

chunked 消息需要最后的空行终止，不能把提前 EOF 等同于正常结束。[RFC 9112 §7.1](https://www.rfc-editor.org/rfc/rfc9112.html#section-7.1)。

候选修改：

```diff
- if not response.isclosed():
-     raise incomplete_body
+ 使用严格的 chunked framing 校验：
+ 必须看到合法零长度块、完整 trailer 行以及最终空行；
+ EOF 早于上述结束点则 incomplete_body。
```

可在专用 HTTPResponse 子类中严格处理 trailer 读取，保留现有 deadline 和头部大小限制。

副作用：会拒绝过去被宽松接受的畸形服务器响应；主动截断仍可按原策略保存前段。

测试夹具：缺最终空行、半截 trailer、缺零块、合法空 trailer、合法非空 trailer、尾部慢速滴流。现有测试只覆盖数据块内部截断。

**C4｜重要｜HTML 认证页检查只在验收脚本中，生产下载路径仍接受并缓存**

位置：[http_reader.py:231](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/http_reader.py:231)、[verify_b2.py:74](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/verify_b2.py:74)。

触发条件：日志 URL 返回 200 登录页或代理页。运行路径只检查 HTTP 状态和凭据模式，仍保存为日志并可推进 workflow。

已复现带密码输入框的 HTML 被保存，`transfer_complete=true`、`export_allowed=true`。最终导出函数还有额外拦截，因此这里不能直接等同于已发生外传，但下载回执和流程结论已经错误。

候选修改：

```diff
+ 在公共下载路径执行 validate_log_content(headers, bounded_prefix)；
+ 识别出的认证页、代理页返回 FlowError(5, 'not_a_log')，
+ 不写成功日志缓存，不进入完成状态。
+ 验收复用同一校验器，并保留独立负向断言。
```

副作用：不能简单把日志中出现 `<html>` 字样都判错；需结合响应类型、正文开头和认证结构，避免误伤编译器输出的源码片段。

测试夹具：200 登录页、200 代理错误页、纯文本日志、包含 HTML 字面量的正常编译日志。测试实际 workflow，不只测试验收 B。

**C5｜重要｜状态库读取错误仍统一包装为 state_busy，与重试契约不符**

位置：[state.py:89](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/state.py:89)、同文件 105 行；`test_batch21.py:380`。

触发条件：连接已关闭、数据库结构异常或 payload JSON 损坏。`head()`、`events()` 均返回 `state_busy`。现有测试甚至要求关闭连接后报 busy。

这会使第三部分计划的“busy 按跳过处理”把永久损坏误判为争用，延迟定位并生成错误待办。

候选修改：

```diff
- except sqlite3.Error:
-     raise FlowError(6, 'state_busy')
+ except sqlite3.Error as error:
+     raise FlowError(6, classify(error)) from None

- except (sqlite3.Error, ValueError):
-     raise FlowError(6, 'state_busy')
+ except sqlite3.Error as error:
+     raise FlowError(6, classify(error)) from None
+ except ValueError:
+     raise FlowError(6, 'corrupt') from None
```

副作用：部分原先被当成可恢复竞争的错误会立即停止，这是契约要求的行为。

测试夹具：真实 SQLITE_BUSY/LOCKED；关闭连接；缺表；损坏数据库；非法事件 JSON。只有前一类允许争用跳过。

**C6｜重要｜real 模式的回环检查只检查字符串，地址别名可以绕过**

位置：[verify_b2.py:56](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/verify_b2.py:56)。

触发条件：配置使用 `127.1`、整数形式 IPv4，或解析到回环地址的主机名。

已复现 `127.1` 通过 real 预检，而本机解析结果是 `127.0.0.1`。具有真实规模页面的本地回放仍可冒充真实来源；固定计数并不能区分。

候选修改：

```diff
+ real 模式校验规范化后的地址及实际解析结果；
+ IPv4-mapped IPv6 按其 IPv4 地址判断。
+ 拒绝回环、未指定地址及本机接口地址作为源服务。
+ 连接阶段复核实际选择的目标，避免检查与连接使用不同解析结果。
+ fixture 模式明确允许本地服务。
```

此项不要求恢复上轮已否决的“批准运行清单”。

副作用：开发机本地测试必须使用 fixture；DNS 检查也要受总时限约束。代理场景需明确校验源实例，不能把代理地址误作源地址。

测试夹具：`127.1`、整数地址、`::ffff:127.0.0.1`、DNS 回环别名、合法内网实例、代理路径。

**C7｜一般｜F 段失败不会影响总 PASS，需明确它是验收还是人工侦察**

位置：[verify_b2.py:178](/home/toolchain/development/LogAnalysisSkill/vd-cosmos-core/src/vd_cosmos_core/verify_b2.py:178)；§11“每一段的判定都必须进入结论”。

已复现目录索引返回 500、指纹失败，但 A/B/C/E 和总结果仍 PASS。现有真实运行的 F 已人工核实，所以不推翻该次结果；问题在下一次自动验收的表达。

候选修改：

```diff
+ F.verdict = PASS 当且仅当目录响应、指纹和要求的身份检查通过。
- overall = all(A, B, C, E)
+ overall = all(A, B, C, E, F)
```

若 F 保持人工侦察，则采用另一明确口径：输出 `read_path_verdict=PASS`、`deployment_verdict=未验证/FAIL`，不要单独输出无范围的总 PASS。

副作用：报告读取正常但目录服务异常时，整体部署验收不通过或待人工确认。

测试夹具：F 的索引 500、指纹不符、跳转；验证顶层结论准确反映 F 状态。

**本部分未发现问题的范围：**

- 报告、目录、详情拒绝跳转；日志逐跳检查 origin 和路径；现有越界目标零请求测试有效。
- 常规 Content-Length 提前断流、总时限滴流、额外 CA、证书主机名校验及 CONNECT 路径，本次测试未发现问题。
- 连续记录独立于 50 条历史、失败/404/配置变化重置、覆盖投影纯函数化、实例目录隔离，基本符合 v0.5.4。
- 独立验收 data_root、旧状态隔离、页面比对进入 A 判定、B 要求新下载，上一轮相应缺陷已修复。
- 动作后真实进程崩溃、通知去重和跨构建追加重试已有实质测试，不再只是模拟异常返回。

检查了用户列出的全部重点文件，并对照 `config.py`、`cli.py`、`read_ops.py`、`backends.py`、验收入口及测试辅助服务器。

---

**第三部分：三项计划修复**

**P1｜重要｜按跳过处理方向正确，但必须区分争用、永久错误和显式 expected_event**

位置：§9.3；workflow `api.py:149`；`state.py`。

残余风险：统一捕获退出码 6 会吞掉损坏和约束失败；显式 `--expected-event` 已过期时，连续重试不会使其恢复，不能自动换成新 head。tick 也可能已提交结果、仅在写待办时发生竞争，不能直接重复已完成动作。

候选修改：

```diff
+ loop 仅将 operation_locked、可恢复 stale_head、state_busy 视为争用。
+ 显式 expected_event 不自动更新或重置；其前提失效时明确返回冲突。
+ constraint、corrupt、规则拒绝立即终止，不计入争用跳过。
+ 下一次 tick 重读投影：已提交结果不重做，未提交动作按恢复协议处理。
+ 告警写库失败时返回包含原争用原因的结构化错误。
```

同时先修 C5，才能可靠区分 busy 与损坏。

副作用：错误分类和 loop 返回结构会更细；不改变只重试追加、不重做动作的原则。

测试夹具：本构建新事件、其他构建事件、人工裁决、真实 busy、约束错误、显式旧 expected_event、结果已提交但通知失败。验证动作次数和退出原因。

**P2｜一般｜按每段争用首次时间区分是正确方向，但首次时间不宜作为唯一身份**

位置：§9.3；workflow `api.py:157/175`。

残余风险：时间精度不足或时钟回拨可能让不同争用段重复；每次失败重新取时间又会把同一段拆成多条。不同原因交替发生时也需要明确是否为同一段。

候选修改：

```diff
+ 首次跳过时生成 contention_id，并记录 first_seen_at；
+ 同一连续争用段复用该 id，不因原因变化而更换。
+ 成功完成 tick 后清零；新的争用段生成新 id。
+ basis_version=contention_id，首次时间作为审计字段。
```

副作用：增加一个内存字段；进程重启视为新一段争用，符合当前计数不持久化的约定。

测试夹具：跳过→成功→再跳过；锁忙和 state_busy 交替；冻结时间；时钟回拨；连续三次只产生一条待办。

**P3｜一般｜更新请求头版本号正确，建议消除多个版本源**

位置：`config.py:13`、`config.sample.json`、`versions.py:4`。

残余风险：只修改样例会使缺少 fetch 段的旧配置继续使用旧默认；把产品版本、解析器版本一起无条件升级，又可能无谓作废缓存。

候选修改：

```diff
+ TOOL_VERSION = '<本次交付版本>'
+ DEFAULT_USER_AGENT = f'VD-Cosmos-LogAnalyzer/{TOOL_VERSION}'
- 默认值和样例分别手写版本字符串
+ 默认值与样例由同一版本源校验
+ PARSER_VERSION 独立维护，仅解析语义变化时递增。
```

副作用：显式配置的自定义 User-Agent 应继续保留；仅改请求头不应重新建立全部稳定记录。

测试夹具：缺 fetch 段使用新默认；样例与默认一致；自定义 UA 保留；仅工具版本变化不使解析缓存失效。

---

建议在第 3 批下发前先补齐 **H3、H4、H6、H7 的设计契约**，并把 **C1—C6 与 P1** 纳入修复及负向验收。现有主路径真实通过仍然有效；新增验收应证明的是：**拿到的是正确版本的源码、消费的是有效日志、更新的事实能够推翻旧完成状态，分析结果也经过内容准确性评估。**

上面是Codex的review意见

三部分评审如下。本机分支读取，材料与 SHA 见 batch2.1/review/README.md。已读：HLD v0.6 全文（1167 行）、STATUS.md、第 2.1 批全部重点文件（transport.py、http_reader.py、stability.py、versions.py、observation.py、baselines.py、report.py、state.py、journal.py、verify_b2.py、workflow/api.py、test_batch21.py）及辅助文件（config.py、cli.py、locks.py、files.py、verify.py、config.sample.json、diff 文件清单）。

---

# 第一部分：HLD 的两轮改动

## ① 读取侧的"定型"判定与停止规则（§5.4)

**[重要] H1 settle_s 兜底会盖过"可信来源说还在跑"**
位置：§5.4 第 3 条；代码落点 `stability.py:16-19`（`maturity` 只收 `terminal` 布尔）、`http_reader.py:178`。
触发：构建仍在运行（详情页判"运行/排队")，报告页面碰巧自洽且连续相同 ≥ settle_s（默认 1800 秒）——例如按小时批写报告的构建。后果：被判"定型"→ 可能判"完整"→ loop 下载日志、记"结果已拉取"、发"待分析"待办；或误判"对账失败"停机。虽然 §5.4 第 10 条的低频重观察 + §9.2 评估标识绑定能自愈，但"结果已拉取"在窗口期第 3 批起会触发分析）。设计上自相矛盾：settle_s 的本意（附录 G#2）是"没有可信终态来源时的兜底"，而这里是可信来源明确说了"没结束"。
候选改法（§5.4 第 3 条"定型"款）:
```diff
-定型:稳定,并且满足其一:执行状态已由可信来源判为"已结束"(第 11 条);或连续相同记录持续 ≥ poll.settle_s(默认 1800 秒)。
+定型:稳定,并且满足其一:执行状态已由可信来源判为"已结束"(第 11 条);或连续相同记录持续 ≥ poll.settle_s(默认 1800 秒)且执行状态不是"运行/排队"(可信来源明确说没结束时,不听 settle_s 兜底;只有执行状态为"未知"——无来源或详情不可用——settle_s 才生效)。
```
代码：`maturity(record, poll, terminal)` 改收执行状态三态；`http_reader._arch` 传 `execution['state']` 而非布尔。
副作用：详情页长期不可用（执行=未知）时 settle_s 照旧生效，不增加等待——正是 G#2 想要的行为；只有"明确在跑"时才更保守。夹具：执行=运行 + 长稳定自洽页面 → 必须保持"部分"；执行=未知 + 长稳定 → 定型；执行=已结束 + 刚稳定 → 立即定型。

**[一般] H2 停止后"依据已变化"待办会随内容反复变化逐条开新单**
位置：§5.4 第 10 条；代码 `workflow/api.py:125-127` + `journal.py` 待办身份（basis_version=新内容指纹）。
触发：停止推进后低频观察期间，慢发布的报告内容每次观察都不同。后果：每变一次写一条 `report_basis_changed`（身份含新指纹，不重复但累计），加上按新报告 sha 重开的 reconciliation 待办，inbox 膨胀。
候选5.4 第 10 条第二句）:
```diff
-内容一变就重新判定,并写一条"此前待办所依据的报告已变化,已重新判定"的待办。
+内容一变就重新判定;"依据已变化"待办只在新内容定型后再写(未定型期间的变化不单独开单,体现在下一次判定的依据版本里)。
```
副作用：中间态变化不再即时可见，但低频观察记录本身留痕，信息不丢。夹具：停止后连续两次内容变化（第二次定型）→ 只产生一条 basis_changed。

**核对通过、未发现问题**:"未定型一律部分、结构/对账问题只记 issues"(report.py:311 与测试 test_unsettled_malformed…、test_truncated_structure_to_full…)、停止后不退出而低频重观察、404/失败/配置变化/倒时重置连续记录、历史 50 条与审计分离、停滞只对"已出现页面仍为部分"计数（404 正常等待不误报）——均与附录 G 的裁定一致。

## ② P4 取源码与路径换算（§3 第 6 条、§6.1 第 1a 条）

**结论：不碰别人工作区这一点站得住**——`p4 print/files/describe -S` 都是 depot 级只读操作，不需要 client;P4 写操作协议（§10.1）另行约束。两条问题：

**[一般] H3 "P4CLIENT 的语义要写成"删除"，且要管住 P4CONFIG 文件内容**
位置：§3 第 6 条末（v0.6 新增段）。触发：`P4CLIENT=""`（空串）在 p4 里可能被当作"名为空的 client"而报错，而非"无 client"；另外 `P4CONFIG` 指向的文件若含 `P4CLIENT=…`，会重新引入 client。后果：取源码命令失败或意外关联到别人的 client。候选改法：
```diff
-子进程环境里 P4CLIENT 一律置空——构建机当前默认 client 是 VD 树那条线在用的
+子进程环境里删除 P4CLIENT();P4CONFIG 指向的本线文件不得含 P4CLIENT 行,加载配置时校验这一点。
```
副作用：无。夹具/测试：快照生成的子进程环境断言不含 P4CLIENT 键；P4CONFIG 含 P4CLIENT 行 → 配置拒绝（退出码 2)。

**[一般] H4 路径换算结果缺"必须仍在包根内"的校验**
位置：§6.1 第 1a 条。触发：日志里的路径含 `../`、绝对路径，或包名-版本目录名与预期不符（`%setup -n` 自定义）。现有兜底（按文件名找、唯一匹配才采用）覆盖了"目录名不符"，但没挡住换算结果跳出包根。后果：取到别的包的同名文件进快照（分析基于错误源码）。候选改法：
```diff
-去掉到 <包名-版本>/ 为止的前缀,得到相对路径,接到本轮输入行的包根…后面,就是 depot 路径。
+去掉到 <包名-版本>/ 为止的前缀,得到相对路径;相对 或以 / 开头时直接记"无法定位"。接到包根后,结果必须以包根为前缀,否则记"无法定位"。
```
副作用：无（错误方向更安全）。夹具：含 `../../other/` 的诊断路径、绝对路径、多套一层目录（应走唯一匹配兜底）。

## ③ 分析工作区与 skill 隔离（§6.4)

**结论：站得住。** 独立工作区 + 单 skill（逐字节一致并登记摘要）+ 不注册整个 clone + 关闭自动批准 + 逐条人工批准 + 写入命令祖先检查 + 接收器校验，纵深是够的；"是否仍加载全局 skill"列为第 3 批实测项（§14 第 11 条）是诚实的留白[一般]，非缺陷）：验收③若实测发现全局 skill 仍可见，当前处置是"如实写进残余风险，靠人工批准兜底"——其中"凭据类 skill 可被任务包里的注入文字触发读凭据文件"这一支，靠人盯批准不够稳。建议 §6.4 该句后补："若仍可见，先查 ClineSR 是否支持按工作区禁用全局 skill（配置或 .cline 内覆盖），支持则禁用；不支持再降级为残余风险 + 人工批准。"夹具：验收③的实测记录里加一条"任务包内含诱导读取凭据文件的注入文字"的负向样本。

## ④ 疑似真 bug 两档清单（§6.3)

**[一般] H5 清单整体合理，建议补四个标志、留意一个定性负担**
- 建议补确定档：`-Wunsequenced`（未定义求值顺序，真 bug 率极高）、`-Wbool-conversion`（指针/容器转 bool 恒真）、C++ 的 `-Wvexing-parse`（几乎总是真 bug);`-WdeprecatedK&R 原型，Clang 16 起为错误，ABI 相关，Clang 迁移高频）。
- 建议补"需看一眼档":`-Wlogical-op-parentheses`、`-Wpointer-sign`。
- 误伤检查：确定档现有成员误报率都低；`-Wparentheses-equality`(`x==x` 是合法 NaN 检查）放在"需看一眼"是对的。唯一要提醒 FatTank 确认的（§14 第 8 条）:`-Wimplicit-function-declaration` 在老 C 代码库里可能量大且多为历史债，全走"疑似→人工定性"会产生定性负担——可考虑首批观察其命中率。
候选改法：§6.3 清单按上增补，标注"待 FatTank 确认"。副作用：标志越多待定性条目越多，已由两档机制控制。夹具：每个新增标志一条最小诊断样本（命中/不误伤各一）。

## ⑤ 第 3 批验收设计能否证明"分析得准不准"(§12 第 3 批）

**[重要] H6 方向对（有客观锚点），但样本单一性和判定线两点不立**
验收①用 7 个真实失败包 + 与 FatTank 当时实际修法逐个对照，这是能拿到的最好锚点，且诚实保留"说不清"档。两个缺口：
(i) 7 个样本全部来自同一轮，失败类别很可能单一（同轮 Clang 迁移错误常是同类警告），覆盖不了 `diagnostic_only / disposition_proposal / cross_package_handoff` 这些 outcome 类型——"分析准不准"会只在一种类别上被证明。
(ii) 没有判定线：多少"不一致"算 FAIL？"不一致"可以是分析错，也可以是"当年修法后来被证明不是最优"——不区分就无法下结论。
候选改法（§12 第 3 批验收①替换判定）:
```diff
-把推荐方案与 FatTank 当时的实际修法(fix5 系列清单里的 CL)逐个对照,列出一致 / 不一致 / 说不清,不一致的写原因
+把推荐方案与 FatTank 当时的实际修法(fix5 系列清单里的 CL)逐个对照:逐包标 一致/不一致/说不清;不一致逐条归因(分析错误 / 修法选择不同 / 当年修法已被后来推翻),归因含"分析错误"的条目 >0 即该批验收不通过;7 个样本的 outcome 类型分布列入结果,若全部是 repair_candidate,从 VD 线补充样本里补足"仅诊断/转至少各一例,补不齐则如实标"类型未覆盖"
```
副作用：验收标准变严，可能需要 FatTank 多提供 1～2 个非编译类样本。夹具：无需新页面夹具；需要补充样本的失败日志与当时修法记录。

**[一般] H7 §7.6 Obsidian 导出目录可能违反"只写数据根目录"**
位置：§7.6(v0.6）与 §3 第 2 条。`kb.obsidian_dir` 位置待确认（§14 第 9 条）；若答"组里共享位置"，就与 §3 第 2 条"全部输出写在数据根目录下"冲突。候选改法：§7.6 补一句"导出目录必须在数据根目录内；如需放到共享位置，作为 §3 第 2 条的显式例外由 FatTank 裁定后记入 STATUS"。副作用：无。夹具：配置校验——obsidian_dir 解析后不在数据根目录内 → 退出码 2（除非例外开关）。

---

# 第二部分：第 2.1 批代码

## ① 抓取的跳转、完整性、总时限是否有绕过路径

逐项核查：**未发现问题。** 具体看过：
- 跳转：`NoRedirect` 使报告/索引/详情任何 3xx 直接 `（不发出目标请求，测试断言零目标请求）;meta refresh 不会被跟随，且页面缺 marker 会 `not_a_report` 兜底；日志逐跳在发请求前过 `log_allowed`（协议/主机/端口/解码规范化路径前缀），含 https→http 降级、跨端口、跨架构目录逃逸（测试覆盖）。
- 完整性：Content-Length 不符、chunked 未正常结束（`IncompleteRead` → `incomplete_body`)、读取中断均不落盘不进缓存（测试断言无continuous 重置）；"主动截断"与"传输中断"在落盘记录里分两个字段区分。
- 总时限：`Deadline` 覆盖 DNS（独立线程 + 有界等待）、逐地址 connect、TLS 握手、逐次 socket 读（`TimedRaw` 每次 readinto 前重设剩余时限）、多跳重定向共享同一 deadline；滴流测试实测 0.6s 内按 deadline 失败。
- TLS：系统 CA 之上叠加 ca_file、CONNECT 隧道校验目标主机证书、自签/主机名不符拒绝——真实本地 TLS 握手测试，非 mock。
- 凭据：无 cookie 处理器；响应留证只含元数据，正文永不进证据；`sanitized` 逐字段过凭据检查。

## ② 定型与停止推进的判定

**[重要] C1 = H1 的代码落点**
`stability.py:16-19` + `http_reader.py:178`：`maturity(record, poll, execution['state']=='已结束')` 把执行状态压成布尔，"运行/排队""无区别，settle_s 对两者同样生效。改法、副作用、夹具见 H1；代码 diff 要点：
```diff
-def maturity(record, poll, terminal):
+def maturity(record, poll, execution_state):
     elapsed = seconds(record['last_seen_at']) - seconds(record['first_seen_at'])
     stable = elapsed >= poll['interval_s']
-    return stable, stable and (terminal or elapsed >= poll['settle_s'])
+    return stable, stable and (execution_state == '已结束' or
+        (elapsed >= poll['settle_s'] and execution_state not in {'运行', '排队'}))
```
其余（未定型不停止、停止后低频重观察、变化重判、单码 3）与 HLD §5.4 一致，测试覆盖真实。

## ③ 状态库重试、锁与崩溃恢复

实现与 §9.3 一致：WAL + busy_timeout=2000、错误四分类、重试仅限 stale_head/state_busy 且新事件均为他构建/非人工非外部写、constraint/corrupt/显式 expected 不重试、不重做动作（测试 test_append_retry… 与 test_tick_concurrent_other_build… 逐条覆盖）；按构建 SQL 过滤 + 表达式索引（EXPLAIN QUERY PLAN 断言）;1 万条他构建事件下投影 <0.1s；崩溃恢复用真实子进程 `os._exit` 在 observe/logs/notify 三处注入，残留 attempt 目录清理、结果唯一（SQL 唯一索引）均有断言。**除下条外未发现问题：**

**[一般] C2 锁争用待办的依据版本是常量，不是"该段争用首次时间"**
位置：`workflow/api.py:175`（`basis_version: 'active_contention'`)。这正是第三部分第 修的，确认属实；其修复评估见下。

## ④ 验收脚本能否被旧数据、回放或缓存冒充

**未发现冒充路径。** 机制逐项成立：每次验收全新数据根目录（旧状态/旧缓存/旧稳定记录在结构上不可见）；HEAD 与 `--verified-commit` 双处校验（.sh 和 .py 各一）、本线四目录脏树拒绝（含未跟踪文件）、real 模式拒绝回环/localhost/.invalid；A 段页面"不同"直接 FAIL；B 段要求本次新下载（not skipped)+ 传输完整 + 未截断 + 非 HTML  + 摘要回算；E 段要求三类动作齐全、日志与 B 同源同摘要、恰好一条分析待办；provenance 记录提交号、源码树摘要、脚本摘要、配置摘要、基线摘要、实例端点、产物清单。测试用两次独立运行 + 保存页篡改 + 三类坏日志分别验证。
[一般] 一条小缺口：`verify_b2.py:154` 的 E 段时间预算公式假定 `poll.settle_s` 已被夹具调小——用真实配置（settle_s=1800）跑 fixture 模式会超时失败。建议在脚本里对 fixture 模式显式断言 `settle_s <= 预算` 或把预算公式加上 settle_s 项。副作用：无。夹具：fixture 计数 + 默认 settle_s 的配置应快速报"预算不足"而非挂到超时。

## ⑤ 测试是否真的覆盖了声称的情形

抽查了附录 G 落实表与测试的对应：G#1/2/3/4/9/10/11/12/13/14/19/20/22/23/25/26/27/28/33/34/35/36 均有名字相符、断言到位的测试，且是真实子进程崩溃、真实 TLS 握手、真实双进程争锁、真实超时/滴流，不是 mock 摆设。两条缺口：
- [一般] C3 无"执行=运行 + 长稳定"不定型的用例——若采纳 H1/C1，需新增：running + 稳定 ≥settle_s → "部分"；未知 + 同条件 → 定型。
- [一般] C4 connect 阶段的 deadline（对端 accept 前挂起）无测试——可用"监听但不 accept 的 socket具补；不补也可接受，风险低。

## ⑥ 代码与 HLD 不一致

- [一般] C5 `report.py:199-200`：`settled = stable if settled is None else settled` 插在 docstring 之前，函数 `__doc__` 丢失（文档字符串变成了无效表达式）。把赋值挪到 docstring 之后即可，无行为变化。夹具：无。
- [一般] C6 版本号双源：`versions.py` PARSER_VERSION='0.5.4' 而 `config.py:15` 的 UA 仍是 '0.5.3'——即第三部分第 ③ 条，确认属实；建议借修复把 UA 默认值改为由同一常量拼出，防再犯。夹具：断言 `FETCH_DEFAULTS['user_agent'].endswith(PARSER_VERSION)`。

---

# 第三部分：设计方计划的三处修复

**第 ① 条（tick 放弃 → 跳过计数）：方向正确，但按现在的写法有一个真实副作用，需要改一处。**
现状确认：`api.py:166-168` 只对 `operation_locked` 做跳过，其余 FlowError(stale_head 重试用尽、state_busy 重试用尽）原样抛出，loop 异常退出——问题属实。修复要点之外必须补三条：
(a) **进入"跳过"的原因必须枚举**：只含 `operation_locked`、`stale_head`、`state_busy`;`constraint`/`其它 FlowError 必须照常退出——把唯一约束冲突当争用跳过会把真 bug 埋成无限循环。
(b) **"本构建/人工裁决类新事件导致的放弃"不应计入同一个 3 次退出计数**。这是该方案最大的坑：FatTank 连续做三次 confirm（每次 append 都让 loop 的 tick 放弃）→ 计数到 3 → loop 退出 + 误报 `loop_contention`。人工操作是正常输入，不是争用。建议分开：锁 计入争用计数、按 interval 睡眠；本构建新事件 → 不计数、缩短或跳过本次睡眠立即重 tick（新事件大概率改变了投影，等一个整间隔是纯损失）。
(c) 修复后补并发基线测试（上次评审已指出 tick 级争锁只有双进程一胜一退的用例）。
候选文字（§9.3 第 4 条改写）:
```diff
-tick 因"期望编号之后出现了本构建或人工裁决类的新事件"或"状态库忙且重试用尽"而放弃时,loop 同样按"跳过"处理(计入上面的连续计数),不整体退出。
+tick 因"状态库忙/轮次锁忙且重试用尽"而放弃时,按"跳过"处理并计入连续计数;因"本构建或人工裁决/外部写类新事件"而放弃时,不计入争用计数,立即(或短睡眠后)重 tick。constraint、corrupt 及其它错误不视为跳过,照常退出。
```
夹具：连续 3 次人工裁决事件注入 → loop 不退出、无争用待办；持锁线程 3 个 → 退出 6 + 一条待办；constraint 注入 → 立即退出。

**第 ② 条（争用待办按每段争用首次时间）：正确，补一个边界。**
现码用常量 `'active_contention'`，后续争用段被去重吞掉，属实。改为"该段首次跳过的 UTC 时间"即可；注意实现上是"每段"语义——loop 因 3 次跳过退出后被重启、再次争用，属于新段会再报一条，这是期望行为（每次退出最多一条，人有感知具：两段争用（中间有成功 tick)→ 两条待办；同段内 → 一条。

**第 ③ 条（UA 版本号）：正确，建议顺手单一版本源。**
`config.py:15` → '0.5.3' 改为由 `versions` 的常量拼出（见 C6)；注意 `parsing_digest` 不含 UA,UA 变化不会重置连续记录，无副作用。夹具：见 C6 的断言测试。

**三条都没覆盖到的遗漏（按严重度）:**
1. [重要] H1/C1：运行/排队状态下 settle_s 仍会定型——三条修复均不涉及，建议进第 3 批；
2. [重要] H6：第 3 批验收①的样本类型分布与判定线——直接影响"第 3 批能否证明分析得准";
3. [一般] H2(basis_changed 待办膨胀）、H3(P4CLIENT 语义）、H4（包根前缀校验）、C3/C4（测试缺口）、C5(docstring)。

**总体结论**：附录 G 的 36 条落实在代码里逐条可考、测试真实（真实 TLS/真实崩溃/真实双进程），本的防冒充三板斧（全新数据根目录、脏树拒绝、逐段严格判定）成立；第 2.1 批代码无阻断、无重要级新问题（C1 是 HLD 层设计缺口 H1 的代码映射）。HLD v0.6 的第 3 批设计（P4 取源码、工作区隔离、两档清单）可下发，建议先把 H1、H6 两条重要项和第三部分第 ① 条的副作用修正并入任务。

上面是Kimi Code的review意见

写给：设计方（Claude）、实现方（Codex）和 FatTank。

# 第 2.1 批 + HLD v0.6 外部评审意见

**总体结论**：三部分都**没有阻断项**。

- **第 2.1 批代码**：基本按 HLD v0.5.4 落实了。跳转、完整性、总时限、TLS、投影和崩溃恢复这几块，我逐项核对过，没有发现绕过路径。
- **重要问题集中在两处**：
  - v0.6 新写的第 3 批设计：路径换算会取错文件；shelve 的 base 版本来源没定义；分析工作区的隔离靠 AI 自己报告来验证；验收证明不了“分析得准不准”。
  - 验收脚本的“非回环”检查只比较字符串，可以绕过。

**这次怎么核对的**

- **材料**：三份材料的 sha256 与 README 一致；`vd-cosmos-*` 目录在 3fd6470 和 HEAD 之间没有差异。工作区里另一条线的未提交改动没有动。
- **看过的文件**：
  - HLD v0.6 的版本记录、§3、§4.5、§5.4、§6、§7.6～7.7、§9.2～9.6、§11、§12、§14、附录 B、附录 G；
  - STATUS.md、README；
  - 代码：transport、http_reader、stability、versions、observation、baselines、report（diff）、state、journal、cli、read_ops、backends（diff）、config（diff）、verify_b2、verify_b2_real.sh，workflow 的 api.py；
  - 测试 test_batch21.py 全部 27 个用例；
  - 已有 LogAnalyzer 的参数定义（确认 `--no-tiktoken` 存在）。
- **实测**：在会话临时目录里跑了两项，用 `python3 -B`，没有写仓库。下文标〔实测〕的结论来自这两项。

---

## 第一部分：HLD 的两轮改动

### (a) v0.5.4 的改动

#### H-1【重要】“可信终态 + 稳定”就算定型，这个捷径的前提没有验证过

- **位置**：§5.4 第 3 条（第 330 行）；代码 [http_reader.py:178](vd-cosmos-core/src/vd_cosmos_core/http_reader.py#L178)、[stability.py:16-19](vd-cosmos-core/src/vd_cosmos_core/stability.py#L16-L19)。
- **隐含前提**：构建被详情页判为“已结束”时，报告已经写完。
- **为什么不一定成立**：§5.4 第 11 条和附录 D 都提到了“被推广的下游构建”和 `BUILD_COMPLETE` 推广链接。如果报告是由推广出去的下游任务在主构建结束之后才发布或补写的，那么在“已结束”之后连续两次抓到同一份半成品，相隔 ≥ 一个间隔，就会被判为定型。§14 第 3 条（进行中构建的报告与详情页时序）至今还没结清。
- **后果**：半成品被判成对账失败或结构未知，然后写待办、停止推进。后面靠低频重判可以恢复，但会多出一组误报待办。更麻烦的情况是：截断位置正好在行边界、而且汇总和明细自洽的半成品，会被判成“完整”。附录 G#2 用“定型”去堵的正是这个口子，终态捷径又把它打开了。

```diff
-   - **定型**：稳定，并且满足其一：执行状态已由可信来源判为"已结束"（第 11 条）；或连续相同记录持续 ≥ `poll.settle_s`（默认 1800 秒）。
+   - **定型**：稳定，并且满足其一：
+     - 执行状态已由可信来源判为"已结束"，并且该架构报告响应的 `Last-Modified` 早于"首次观察到已结束"的时间至少 `poll.interval_s`
+       （证明报告不是在终态之后才写完的）；没有 Last-Modified 就不走这一条；
+     - 连续相同记录持续 ≥ `poll.settle_s`。
+   - §14 第 3 条实测结清之前，loop 的自动推进只用 settle_s 这一条；终态捷径只用于验收和人工观察。
```

- **副作用**：在没有 Last-Modified 或者没结清之前，每轮最多慢 `settle_s`（30 分钟）。另外 detail.json 要新增一个字段“首次观察到已结束的时间”。
- **夹具**：`status_seq/publish_after_terminal/`：详情页在 t0 变成 failed；报告在 t0 和 t0+1 个间隔是同一份半成品，在 t0+2 个间隔才写完整。期望前两次是“部分”，第三次之后才“完整”，全程不写对账待办。

#### H-2【一般】停滞规则和新的定型模型矛盾：等待定型期间必然误报〔实测〕

- **位置**：§5.4 第 12 条（第 368 行）；代码 [journal.py:72-80](vd-cosmos-core/src/vd_cosmos_core/journal.py#L72-L80)。
- **原因**：按 v0.5.4 的模型，“内容不变”只要持续到 `settle_s` 就会定型。所以“部分且连续 N 次不变”只可能出现在等待定型的那段窗口里。只要 `stall_polls × interval_s < settle_s`（默认 6×60 秒远小于 1800 秒），这条规则在每一轮都会误报；反过来只要大于 settle_s，它就永远不会触发。
- **〔实测〕**：报告完整、详情页 500 或返回 running，`settle_s` 为间隔的 30 倍，都写出了 `report_stalled`。
- **后果**：凡是详情页拿不到终态的轮次，都会多一条假待办。

```diff
-12. **停滞与超时**：只对"至少一个架构已出现页面、但本轮仍为部分"的状态计数，连续 N 次（默认 6）观察内容不变，写待办……
+12. **停滞与超时**：v0.5.4 起"内容不变"就是定型的依据，不再代表停滞。停滞改为两种情形：
+   - 至少一个期望架构已定型，另一个期望架构持续"未发布"超过 `poll.arch_lag_s`（默认 4 小时；上一轮实测两架构相差约 2 小时）；
+   - 某架构的连续相同记录在"预期时长 × 1.5"内不断被重置（内容一直在变，始终不定型）。
```

代码对应删除 [journal.py:72-80](vd-cosmos-core/src/vd_cosmos_core/journal.py#L72-L80) 的 `waiting` 分支，换成上面两条。

- **副作用**：附录 B 新增 `poll.arch_lag_s`；`stall_polls` 不再使用。
- **夹具**：
  - 等待定型窗口内不写 `report_stalled`（我实测的场景，期望结果正好相反）；
  - x86 已定型、armv7l 一直 404 超过 `arch_lag_s` → 写一条待办；
  - 内容每次都变，超过预期时长 → 写一条待办。

#### H-3【重要】§11 的“非本机回环”检查只比较字符串，可以绕过；附录 G#15 不记录对端 IP 的理由也已经不成立〔实测〕

- **位置**：§11（第 836 行）；代码 [verify_b2.py:55-64](vd-cosmos-core/src/vd_cosmos_core/verify_b2.py#L55-L64)；附录 G#15。
- **〔实测〕**：`127.1`、`2130706433`、`::ffff:127.0.0.1` 都能通过 `ipaddress(...).is_loopback` 这一关，实际都解析到 127.0.0.1；`0.0.0.0` 也能通过，在 Linux 上连的就是本机。本机的局域网 IP 当然也能通过。
- **后果**：本机起一个回放保存页面的服务，配置里换成上面任何一种写法，real 模式的 A～E 都能 PASS，A 的“与保存页逐字节相同”也恰好成立。
- **附录 G#15 的理由已失效**：当时拒绝记录对端 IP 的理由是“urllib 拿不到可靠值”。第 2.1 批的 [transport.py:103-136](vd-cosmos-core/src/vd_cosmos_core/transport.py#L103-L136) 已经自己完成 DNS 解析和连接，`sock.getpeername()` 和 `sock.getsockname()` 都能直接拿到。

```diff
 §11 验收脚本运行前核对
-  real 模式下报告根不能是本机回环地址、localhost 或 .invalid。
+  real 模式下：报告根与详情页主机先解析；任一地址（含 IPv4 映射的 IPv6）是回环、未指定（0.0.0.0、::）、链路本地地址就拒绝；
+  每个请求在连接后比较 getpeername() 与 getsockname() 的 IP，二者相同（连的是本机自己）即 FAIL。
+  解析结果和每次请求的对端 IP 写进来源记录和响应留证。
 附录 G#15
-  **不采用**记录对端 IP：urllib 拿不到可靠值
+  （v0.6 起采用）第 2.1 批自建连接后可以可靠取得对端 IP，记入响应留证。
```

`check_source` 对应改成：

```python
for url in urls:
    host = urlsplit(url).hostname.lower().rstrip('.')
    if host == 'localhost' or host.endswith(('.localhost', '.invalid')):
        raise FlowError(2, 'real_backend_requires_non_loopback_instance')
    for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM):
        ip = ipaddress.ip_address(info[4][0].split('%')[0]); ip = getattr(ip, 'ipv4_mapped', None) or ip
        if ip.is_loopback or ip.is_unspecified or ip.is_link_local:
            raise FlowError(2, 'real_backend_requires_non_loopback_instance')
```

`connection()` 连上以后记录 `peer`，在 real 模式下检查 `peer == local` 就拒绝。

- **副作用**：预检阶段多做一次 DNS 解析。如果 Cosmos 恰好和构建机是同一台机器，会被误拒，但这种部署不会出现。
- **夹具**：`test_real_mode_rejects_numeric_loopback_forms`，参数化覆盖 `127.1`、`2130706433`、`::ffff:127.0.0.1`、`0.0.0.0`；`test_real_mode_rejects_self_connection`，用本机非回环地址起一个服务，期望 FAIL。

#### H-4【一般】F 段（目录指纹、身份核对、是否跳转）不进入结论

- **位置**：§5.4 第 2 条“目录指纹在第 2.1 批构建机验收里对真实桶页面核实”；§11“每一段的判定都必须进入结论”；代码 [verify_b2.py:183-186](vd-cosmos-core/src/vd_cosmos_core/verify_b2.py#L183-L186) 写死了 `evaluated_for_pass: False`。
- **后果**：在真实桶页面上指纹不匹配，或者发生了跳转，总结论照样 PASS。这次的“F 已核实”是设计方人工看出来的，脚本本身没有判。

```diff
-    result['F'] = sanitized({'evaluated_for_pass': False, 'index': index_result, ...
+    f_pass = (index_result.get('fingerprint', {}).get('verified') is True
+              and second['execution_evidence'].get('identity_match') is True and not redirect_responses)
+    result['F'] = sanitized(verdict(f_pass, index=index_result, ...), config)
-    result.update(verdict(all(result[part]['verdict'] == 'PASS' for part in ['A', 'B', 'C', 'E'])))
+    result.update(verdict(all(result[part]['verdict'] == 'PASS' for part in ['A', 'B', 'C', 'E', 'F'])))
```

- **夹具**：目录页没有数字链接 → F FAIL，总结论 FAIL；详情页身份核对不通过 → F FAIL。

#### H-5【一般】“期望架构来自冻结请求”与表单字段 `ARCH armv7l` 冲突

- **位置**：§5.4 第 5 条（第 339 行）对比 §14 已结清项（第 878 行）。
- **问题**：表单的 ARCH 字段是 armv7l，但真实一轮同时发布了 x86_64 报告，里面还有一个失败包（libdeflate）。第 4 批起如果按请求取期望架构，x86_64 会被排除在外，它的失败就没人管了。
- **改法**：

```diff
-5. **多架构汇总**：期望架构集合来自冻结的请求（表单有架构项时）或配置 `cosmos.archs`……
+5. **多架构汇总**：期望架构集合取配置 `cosmos.archs`（Cosmos 实际按架构发布报告的集合）；表单的 ARCH 字段只记入请求，不用来缩小期望集合。
+   要改成"按请求取"，需要第 4 批实测证明表单 ARCH 与发布的报告架构一一对应。
```

### (b) v0.6 的改动

#### H-6【一般】“P4CLIENT 置空”不一定能让 p4 不用 VD 的 client，而且没有任何核验

- **位置**：§3 第 6 条（第 180 行）、附录 B `p4.*`。
- **问题**：p4 的取值优先级是：命令行 `-c` 高于 P4CONFIG 文件，高于环境变量，高于 `~/.p4enviro`（也就是 `p4 set` 写入的地方）。环境变量 P4CLIENT 设成空串，可能被当成“未设置”，于是回退到 `~/.p4enviro` 里 VD 那条线的 client。批 3 只做 `print`、`files`、`describe` 这些只读命令，用的又是 depot 语法，所以不会碰到别人的工作区。但这条设计声称达到的效果没有被核验；到第 6 批有写操作时，这就会变成真实的风险。
- **改法**：

```diff
-   子进程环境里 **P4CLIENT 一律置空**……
+   取源码的每条 p4 命令都显式带 `-c <p4.no_client_name>`（一个保证不存在的名字，例如 `vd-cosmos-noclient`），
+   P4CONFIG 指向的文件里不得出现 P4CLIENT（配置加载时检查）。每次取快照前用 `p4 -c <名> -ztag info` 核对 clientName 为该名字、且显示 client 不存在，否则停止并写待办。
+   所有路径参数必须以 `//` 开头（depot 语法），出现本地路径即拒绝。
```

- **夹具**：假的 p4 可执行文件。info 返回 VD 的 client 名 → 拒绝；返回非 depot 路径的参数 → 拒绝。

#### H-7【重要】P4 在取快照过程中失效，会被当成“文件无法定位”，悄悄降级为“仅诊断”

- **位置**：§3 第 6 条（只在取源码前查一次 `p4 login -s`）、§6.1 第 1a 条“否则这个文件记‘无法定位’”“主错误所在文件定位不到时，结果类型只能是‘仅诊断’”。
- **触发条件**：取 20 个文件的过程中票据刚好过期、网络抖动、服务器忙。
- **后果**：`p4 files` 返回非零，被当成“不存在”。主错误所在的文件因此被记成“无法定位”，这个包只能产出“仅诊断”结论。一次临时故障变成了分析结论，而且看起来像是“正常走完了流程”。

```diff
 1a.
+   - p4 错误分两类：只有"no such file(s)""file(s) not on client"之类的明确不存在才算"无法定位"；
+     认证（session expired、password invalid）、连接、超时、服务器错误一律算"快照失败"：
+     本次 attempt 作废，写待办（认证类按 §3 第 6 条提示登录），不产出任何任务包，下次 tick 重做。
+   - 快照完成时再执行一次 `p4 login -s`；剩余时间少于本次快照实际耗时的两倍，也写提醒。
```

- **夹具**：假的 p4 在取第 5 个文件时返回 `Your session has expired`。期望快照失败、没有任务包、不出现“仅诊断”。

#### H-8【重要】路径换算会取错文件：外部头文件、生成文件、BUILD 目录名与“包名-版本”不一致

- **位置**：§6.1 第 1a 条（第 394-396 行）。
- **问题一：BUILD 下的目录名不一定是“包名-版本”**。`%setup -n` 改名、tarball 里的目录名和包名不同、版本里带 `+git` 后缀，这些都很常见。这时前缀根本匹配不上。
- **问题二：外部头文件被按文件名“找回”成本包的文件**。错误位置在 `/usr/include/...` 或 BUILDROOT 下（其它包的头文件，正是 R11 的典型情形）时，按文件名回退 `p4 files <包根>/...<文件名>@CL` 可能在本包里找到一个同名的内置副本，而且是唯一匹配，于是被采用。分析者随后就会在受害包里改一个错误的文件，这和 §6.2 的 `cross_package_handoff`、R11 正好相反。
- **问题三：生成文件被换成别的同名文件**。`config.h`、`*.pb.h`、moc 文件不在 depot 里，按文件名回退可能找到一个第三方子目录里的同名文件。
- **后果**：任务包里放的是错误的源码。接收器的“原文逐字一致”检查只能证明修改和快照一致，证明不了快照取对了文件。

```diff
-   - 日志里的源码路径形如 `…/rpmbuild/BUILD/<包名-版本>/<相对路径>`。去掉到 `<包名-版本>/` 为止的前缀……
+   - 路径先分类，只有第 ① 类做换算：
+     ① `…/rpmbuild/BUILD/<源码目录>/<相对路径>`：<源码目录> 取 BUILD 下的第一级目录（不假定等于"包名-版本"），相对路径接到包根；
+     ② `/usr/include/…`、`…/BUILDROOT/…`、sysroot 或其它包的安装路径：记"外部文件（属于其它包）"，不在本包里按文件名查找，
+        作为 cross_package_handoff 的证据交给分析者；
+     ③ 换算后不存在、且位于构建输出目录（build/、obj-*/、_build/）或文件名是生成物（config.h、*.pb.h、moc_*、*.tab.[ch]）：
+        记"生成文件"，可以取模板（如 config.h.in）作参考，但不能作为修改对象。
-   - ……不存在时……在包根下按文件名找（`p4 files <包根>/...<文件名>@CL`），**唯一匹配**才采用
+   - 按文件名回退只用于第 ① 类，并且候选文件与原路径至少最后两级一致（`foo/bar.c` 对 `…/foo/bar.c`），同时唯一，才采用；只有文件名相同不算。
```

- **副作用**：能定位到的文件会少一些，“仅诊断”的比例会上升。但这样的结论是诚实的。
- **夹具**：用 7 个真实日志里的路径原样做成换算夹具，另外合成三个反例：
  - `%setup -n` 改名后的目录；
  - `/usr/include/dlog/dlog.h` 报错，而包里正好有一个同名的 `include/dlog.h` → 必须记“外部文件”，不能采用；
  - `build/config.h` → 记“生成文件”。

#### H-9【重要】shelve 行的 base 版本来源没有定义

- **位置**：§6.1 第 1 条和第 1a 条第 3 点（第 397 行）。
- **问题**：报告里 shelve 包那一行是 `路径/...@SCL(shelve)`，只给出了 shelve 的变更号。“先取 base”取的是哪个版本，没有写。如果直接用 `@SCL` 读未修改的文件，那是“库在 SCL 编号那一刻的状态”，不是 Cosmos 这一轮实际用的 base（base CL 清单里的那个版本）。两者之间该包有别的提交时，快照就和 Cosmos 实际编译的源码不一样。
- **另一个问题**：shelve 可能跨包（§8.3 已经提到跨包 CL），叠加时可能把别的包的文件混进来。

```diff
-   - shelve 行（`@CL(shelve)`）先取 base，再用 `@=CL` 叠加 shelve 里的文件动作（增、删、改）。
+   - shelve 行（`@SCL(shelve)`）的 base 版本按以下顺序确定：本轮 base CL 清单里同一包根的那一行（`路径/...@BCL`）；
+     没有这一行时，用 `p4 describe -S SCL` 列出的各文件 shelve 基础版本（`#rev`）；不用 `@SCL` 当 base。
+     两者都拿不到 → 快照记"base 不确定"，结果只能是"仅诊断"。
+   - 叠加前核对 shelve 里的文件全部落在本包根下；跨包 shelve 只叠加本包部分，并在任务包里注明。
+   - 第 3 批开工前侦察：在一个已知的 shelve 包上，比较这样构造的快照与 Cosmos 日志里的源码行（错误行号附近的代码）是否一致。
```

- **夹具**：
  - 假 p4：base 清单里有 BCL，shelve 的 SCL 之前该包在 BCL 之后另有提交 → 未修改的文件必须取 BCL 版本；
  - 跨两个包的 shelve → 只叠加本包的文件。

#### H-10【一般】P4 路径里的特殊字符没有转义

- **位置**：§6.1 第 1a 条。
- **问题**：日志里的文件名如果含 `@ # % *`，或者含 `...`，直接拼进 `p4 files <路径>@CL` 后，`@` 会被当成版本说明符，`...` 和 `*` 会被当成通配符，查询结果就变成另一个文件集合。
- **改法**：按 P4 规则转义（`@`→`%40`、`#`→`%23`、`%`→`%25`、`*`→`%2A`）；路径里含 `...` 直接拒绝；参数始终以列表方式传给子进程。
- **夹具**：文件名为 `a@b.c`、`x%y.h` 的换算用例。

#### H-11【重要】分析工作区的隔离，用“让 AI 列出可用 skill”来验证不可靠；而且只考虑了 skill，没考虑全局生效的配置

- **位置**：§6.4（第 453 行）、§12 第 3 批验收 ③（第 849 行）、§14 第 11 条。
- **问题一：验证方法依赖 AI 自述**。§3 第 9 条自己就写了“内网 AI 会遗忘、会编造”。让它报告自己能看到哪些 skill，它可能漏报，也可能编造，这种结果不能作为隔离成立的证据。
- **问题二：范围漏了全局配置**。Cline 系扩展的 MCP 服务器、全局规则、工作流、自动批准设置通常是全局生效的，不跟着工作区走。用户平时的环境里装了凭据类 skill，很可能也配了凭据类 MCP，另开一个工作区并不能把它们隔开。

```diff
- ClineSR 是否只加载工作区自己的 skill、是否还会加载全局 skill，第 3 批验收实测（让它列出可用 skill）；
+ 隔离核验不依赖 AI 自述：
+   - 金丝雀：在用户平时的工作区 `.cline/skills` 和全局 skill 目录各放一个只含唯一随机标记、不含任何操作的 skill；
+     打开分析工作区后，由 FatTank 在 ClineSR 设置界面或日志里核对已加载的 skill 列表，截图存证；同时检查发给模型的上下文（若可查看）里没有该标记。
+   - 范围包括所有全局生效的配置：MCP 服务器、全局规则 / 工作流、自动批准设置。`analyze prepare` 记录这些配置文件的摘要；
+     有凭据类 MCP 时，在分析会话里禁用它，做不到就写进残余风险。
+   - 验收结束后删除金丝雀 skill。
```

- **夹具**：人工核验清单，写进 verify 的第 3 批段落。另加单测：`analyze prepare` 只生成一个 skill，并登记 skill 和全局配置的摘要。

#### H-12【一般】分析工作区里的 SKILL.md 可以被分析者自己改写

- **位置**：§6.4。`.cline/skills/vd-fix-analyze/` 放在分析者可写的工作区里。
- **问题**：会话过程中，指令本身可能被改。
- **改法**：`analyze prepare` 生成 skill 目录后把它设为只读（目录 0555、文件 0444）；接收器每次接收结果前都核对 skill 摘要与登记值一致，不一致就作废这个 attempt。
- **夹具**：改动 SKILL.md 后提交结果 → 拒收。

#### H-13【重要】疑似真 bug 两档清单：有明显遗漏，也有误伤；匹配规则没写

- **位置**：§6.3（第 434 行）、附录 B `rules.suspect_bug_flags` / `rules.review_flags`。

**确定档建议补充**（都是 Clang 的诊断，命中时几乎都是真缺陷）：

| 类别 | 标志 |
|---|---|
| 生命周期 | `-Wreturn-stack-address`（以及 `-Wdangling` 一族） |
| 求值顺序 | `-Wunsequenced` |
| 内存 | `-Wmismatched-new-delete`、`-Wdynamic-class-memaccess`、`-Wsizeof-pointer-div`、`-Wmemset-transposed-args`、`-Wfortify-source` |
| C++ | `-Wdelete-non-abstract-non-virtual-dtor`、`-Wdelete-non-virtual-dtor`、`-Winfinite-recursion` |
| 移位与除零 | `-Wshift-count-overflow`、`-Wshift-count-negative`、`-Wdivision-by-zero` |
| 常量与位域 | `-Wsingle-bit-bitfield-constant-conversion`（Clang 16 起：`int x:1 = 1` 得 -1）、`-Wbitfield-constant-conversion`、`-Wconstant-conversion` |
| 函数指针 | `-Wincompatible-function-pointer-types`（Clang 16 起默认是错误） |
| 空指针 | `-Wnull-dereference` |

**需看一眼档建议补充**：`-Wformat-security`（非字面量格式串可能是格式串漏洞，不该整个排除在外）、`-Wmisleading-indentation`、`-Wempty-body`、`-Wimplicit-fallthrough`、`-Wswitch`、`-Wself-assign`、`-Wlogical-not-parentheses`、`-Wstring-plus-int`、`-Wpointer-bool-conversion`、`-Wunused-value`、`-Wconditional-uninitialized`、`-Wreorder-ctor`。

**误伤，建议从确定档移到看一眼档**：
- `-Wtautological-unsigned-zero-compare`：无符号数与 0 比较，大多是无害的防御性写法，经常出现在宏里；
- `-Wenum-conversion`：多数无害；
- `-Wtautological-compare` 一族里，只有 `-overlap-compare`、`-pointer-compare`、`-constant-out-of-range-compare` 留在确定档；
- `-Warray-bounds`：命中 `arr[1]` 这种结构体尾部数组的老写法时，标“看一眼”。

**匹配规则需要写清楚**：
- 只按精确的标志名匹配，“一族”逐个列出来，不用前缀匹配；
- 标志要先归一化：`[-Werror,-Wfoo]`、`-Werror=foo`、`-Wfoo` 视为同一个；
- 定性的粒度是“一个包的同一个标志”，不是每一处命中。否则一个包几百处 `-Wformat` 会变成几百条人工定性。

- **副作用**：疑似真 bug 的命中会变多，人工定性的工作量也会增加，但按包加标志合并以后可以控制。
- **夹具**：
  - 每个标志一行真实格式的诊断，覆盖三种写法变体；
  - 一个包 300 处 `-Wformat` → 只产生 1 条待定性；
  - `-Wtautological-unsigned-zero-compare` → 只标“看一眼”。

#### H-14【重要】第 3 批的验收设计证明不了“分析得准不准”

- **位置**：§12 第 3 批验收 ①（第 849 行）、§11“分析（真实）”。

**问题**：
1. **判定口径没有冻结**。“一致 / 不一致 / 说不清”是事后判断。“说不清”没有上限，可以吸收任何不好判定的结果。
2. **参照答案不是唯一正解**。FatTank 当时的修法只是众多可接受方案中的一个：R27 要求逐个找最优解，R21 也说明别人的修法未必最优。不能用“和它一致”来衡量准确。
3. **样本可能不独立**。7 个包很可能集中在少数几类警告上，而且都是编译类，覆盖不到转交其他包（R11）、真 bug（R28）、链接 / 扩展错误这几类。
4. **有答案泄漏的风险**。§7.7 第 6 条的“VD 修复线经验案例种子”如果包含这 7 个包的修法，或者某个地方取了 head 版本（head 里已经有后来的修复），对比就失去意义。
5. **只跑一次**。LLM 每次输出不同，跑一次说明不了稳定性。
6. **没有编译验证**。第 3 批不做本地编译，结论里应该写明“未经编译验证”。

```diff
 | 3 | ……| ① 样本：……把推荐方案与 FatTank 当时的实际修法……逐个对照，列出一致 / 不一致 / 说不清，不一致的写原因……
+| | | 准确性验收单独定规则，开跑前冻结并入库：
+| | | - 参照：FatTank 在开跑前逐包写下"可接受的修法类别"（改代码 / 选项 / 删参数 / 转交其他包 / 旁支），可以多选；实际 CL 只作为其中一个例子；
+| | | - 每包四个判定：①根因与修法类别是否在可接受集合内 ②修改的文件是否正确 ③FatTank 判"可直接用 / 改后可用 / 不可用" ④真 bug 有无误标或漏标。
+| | |   "说不清"只能作为③的理由，不能作为结论；
+| | | - 防泄漏：任务包、知识库种子、分析工作区里都不得含这些包的实际修法或 CL 描述；快照严格按 19091860 的输入取，禁止读取 head；
+| | | - 覆盖：样本按诊断类别去重后少于 4 类时，补充样本必须补齐：至少 1 个外部头文件或转交（R11）、1 个疑似真 bug（R28）、1 个非编译类；
+| | | - 每包分析 2 次，两次推荐不一致的计入结论；
+| | | - 结论给出"可直接用 + 改后可用"的比例和误标数，并注明"未经编译验证"。
```

- **副作用**：FatTank 在开跑前要多花一些时间写参照集。
- **夹具**：参照集文件（入库，与样本日志摘要绑定），以及评分脚本：输入参照集和接收器产出，算出四项判定，不允许输出“说不清”作为最终结论。

#### H-15【一般】Obsidian 导出目录可能在数据根目录之外，绕过了 §5.6 的导出检查

- **位置**：§7.6（第 530 行）、§14 第 9 条（“是否同步到组里的共享位置”）。
- **问题**：导出的页面里会有日志片段和 diff。直接写到共享位置，就绕过了 §3 第 2 条（只在自己的目录里写）和 §5.6 的凭据检查。
- **改法**：

```diff
- 另导出为 Obsidian 可直接打开的 Markdown 库（`kb export --format obsidian --out <目录>`，导出目录在配置 `kb.obsidian_dir`）
+ 另导出为 Obsidian 可直接打开的 Markdown 库，导出目录固定在 `<数据根目录>/export/kb-obsidian/<时间戳>/`，每一页都过 §5.6 的凭据检查；
+ 同步到共享位置是单独的人工步骤，不由工具执行。页面文件名对包名做净化，并加上架构，避免同名包的页面互相覆盖。
```

- **夹具**：页面内容命中凭据模式 → 不产出导出物；包名含 `/` → 文件名被净化。

#### H-16【一般】venv 依赖没有锁定哈希

- **位置**：§3 第 10 条，`PyYAML==6.0.2` 经公司代理安装。
- **改法**：使用 `pip install --require-hashes -r <本线 requirements 文件>`，哈希写进仓库，每次运行前核对 venv 里 PyYAML 的版本和 RECORD 摘要。

### 第一部分里未发现问题的地方

- §5.4 第 1、2、4、6～11 条的新写法：跳转、完整性、目录指纹、按架构定型后再核对报告头、包集合来源、低频重判、详情页身份核对与两种“未知”。
- §9.2 投影和完成状态绑定评估标识；§9.3 的 WAL 和错误分类。
- §6.1 第 2 条“LogAnalyzer 只做证据提取、`--no-tiktoken`、用 JSON 不用 Markdown”。我核实过 `--no-tiktoken` 在 [analyze.py:382](tizen-gbs-log-analysis/scripts/gbs_analyzer/analyze.py#L382) 存在。
- §6.3 的其余条款；附录 B 的其余新配置项。

---

## 第二部分：第 2.1 批代码（3fd6470）

### C-1【重要】验收脚本的非回环检查可以绕过

代码侧的问题和改法见 H-3〔实测〕。这里只补一处代码细节：[transport.py:127](vd-cosmos-core/src/vd_cosmos_core/transport.py#L127) 在 `return TimedSocket(sock, deadline)` 之前，就可以取到 `sock.getpeername()` 和 `sock.getsockname()`，记进 `evidence['peer']`，不需要另外找办法。

### C-2【一般】等待定型期间必然写出 `report_stalled`〔实测〕

代码位置 [journal.py:72-80](vd-cosmos-core/src/vd_cosmos_core/journal.py#L72-L80)。代码和 HLD 第 12 条是一致的，问题出在设计本身，改法见 H-2。现有的 `test_monitor_404_...` 只覆盖了 404 的情形，所以没有暴露。

### C-3【一般】既没有 Content-Length、也不是 chunked 的响应，无法判断是否完整，结果仍被当作完整

- **位置**：[transport.py:233-241](vd-cosmos-core/src/vd_cosmos_core/transport.py#L233-L241)。
- **触发条件**：HTTP/1.0 或 `Connection: close` 的按连接关闭定界的响应（经过某些代理时会出现），中途断开。
- **后果**：半截日志被标成 `transfer_complete=True`，验收 B 照样 PASS。
- **改法**：

```diff
-                return {..., 'transfer_complete': not oversized, ...
+                verifiable = evidence['Content-Length'] is not None or getattr(response, 'chunked', False)
+                return {..., 'transfer_complete': (not oversized) and verifiable, 'transfer_verifiable': verifiable, ...
```

报告页面不可验证时按 incomplete_body 处理，或者至少记进 issues；日志照常保存，但验收 B 要求 `transfer_verifiable`。HLD §5.4 第 1 条补一句“无长度、非 chunked 的响应不可验证完整性”。

- **夹具**：`wire` 发送 HTTP/1.0 响应、不带 Content-Length、中途关闭 → 报告页面观察失败、日志 `transfer_complete=False`、B FAIL。

### C-4【一般】状态库只读错误一律归为 `state_busy`；build_key 列里混着两种格式

- **错误归类**：[state.py:89-93](vd-cosmos-core/src/vd_cosmos_core/state.py#L89-L93) 和 [state.py:104-107](vd-cosmos-core/src/vd_cosmos_core/state.py#L104-L107) 把所有 `sqlite3.Error`，连同 payload 的 JSON 解码错误，都记成 `state_busy`。数据库损坏会被当成“忙”。按第三部分 ① 的新规则，这种情况会先跳过 3 次，再以争用的名义退出，原因写错了。改法：只读路径也调用 `classify(error)`，JSON 解码失败记 `corrupt`。
- **键格式不一致**：[state.py:114](vd-cosmos-core/src/vd_cosmos_core/state.py#L114) 里，带 build_ref 的事件写入的 build_key 是 `json.dumps(build_ref)`，不带的写入 payload 里的摘要。现在只有 workflow 和 watch 的事件，相安无事。第 4 批的 `bind` 事件会走 build_ref 分支，`events(key)` 按摘要过滤时就看不到它们；`one_bind` 唯一索引也会因为两种格式并存而失效。改法：统一写成 `build_key(reader)` 那种摘要格式；需要可读形式时，另放在 payload 里。
- **夹具**：payload 损坏 → `corrupt`；用 build_ref 追加的事件能被 `events(digest)` 查到。

### C-5【一般】评估标识里的解析器版本是手工维护的常量

- **位置**：[versions.py:23](vd-cosmos-core/src/vd_cosmos_core/versions.py#L23) 的 `PARSER_VERSION = '0.5.4'`。
- **触发条件**：以后修了 report.py 或 observation.py，却忘了改这个版本号。
- **后果**：旧的“结果已拉取”仍然判为有效，§9.2“完成状态绑定解析器版本”实际上失效。这和第三部分 ③ 的 User-Agent 写成 0.5.3 是同一类问题。
- **改法**：评估标识里加上解析相关源文件的摘要，例如 `digest(report.py + observation.py + stability.py + baselines.py 的字节)`；PARSER_VERSION 只作为给人看的名字。
- **夹具**：解析器源文件改动一个字节 → 评估标识变化 → 已完成状态作废，重新观察。

### C-6【一般】详情页失败有两套计数，basis_version 可能随 head 不断变化

- **位置**：[http_reader.py:157-167](vd-cosmos-core/src/vd_cosmos_core/http_reader.py#L157-L167)（detail.json 的计数，每次调用 `detail()` 都加 1，包括 logs 步骤里的重新观察、`fetch logs` 命令）；[journal.py:66-69](vd-cosmos-core/src/vd_cosmos_core/journal.py#L66-L69)（按 observe 事件数连续失败次数）。
- **触发条件**：detail.json 的计数已经 ≥ 3，但 observe 事件的连续失败还不到 3。
- **后果**：`basis_version` 取的是 `store.head()`，每次 tick 都不一样，于是每次都开一条新待办。这一条是我读代码推出来的，没有实测。
- **改法**：只保留一套计数，以 detail.json 为准（它包含所有观察），basis_version 取它的 `failure_started_at`。去掉 journal 里的事件计数，或者只用它做核对。
- **夹具**：详情页一直 500，`fetch logs` 连跑 3 次之后再 tick 3 次 → `detail_page_unavailable` 只出现 1 条。

### C-7【一般】测试缺口：声称覆盖、实际没有覆盖的情形

| 声称 / HLD 条款 | 实际情况 | 需要补的夹具 |
|---|---|---|
| §9.3“新事件是人工裁决类时不重试” | `test_append_retry_...` 只测了同一构建的新事件 | 中间插入一条 HUMAN 类事件 → 不重试 |
| §11“real 模式拒绝本机” | 只测了 `127.0.0.1` | H-3 列出的四种写法，以及本机自连 |
| §5.4 第 12 条停滞规则 | 只测了 404 | H-2 的三个夹具 |
| §5.4 第 1 条完整性 | 只测了 Content-Length 和 chunked | C-3 的按连接关闭定界的响应 |
| §5.4 第 3 条终态定型 | `test_unsettled_..._then_terminal` 断言的是终态之后**立即**判对账失败，正好把 H-1 的风险当成了预期行为 | 改为 H-1 的 `publish_after_terminal` 夹具 |
| ca_file“叠加”系统证书 | TLS 测试只验证了额外 CA 能用，没有验证系统 CA 仍然生效 | 同时配置 `ca_file` 时，用系统根证书签发的测试证书仍然被接受（或者断言 `context.get_ca_certs()` 包含系统证书） |

### 第二部分里未发现问题的地方（附看过的位置）

- **跳转**：报告、目录、详情一律拒绝跳转；日志每一跳在发出请求之前检查协议、主机、端口和本架构目录，越界目标收到 0 个请求。看了 [transport.py:139-221](vd-cosmos-core/src/vd_cosmos_core/transport.py#L139-L221)，以及对应的两个测试。跳转响应的留证只记主机和路径，不记查询串，没问题。
- **完整性**：Content-Length 不符、chunked 未正常结束都会报 incomplete_body，产物不落盘，连续相同记录被重置；主动截断和传输中断区分开了。
- **总时限**：DNS（用线程加队列）、连接、TLS 握手、发送、每一次底层读取都受 deadline 约束；慢速滴流的测试用例是真实的。
- **TLS 与代理**：系统 CA 加额外 CA、经 CONNECT 隧道时校验目标主机、主机名不匹配和降级都会被拒绝；忽略环境变量里的代理设置。
- **定型与停止**：report.py 先判定型再判对错（[report.py diff](docs/enhance/batch2.1/review/batch21-code-3fd6470.diff)）；报告头一致性要求全部架构定型；`stopped()` 的四个条件；停止后 loop 改为低频观察，报告变化后重新判定。
- **包集合**：`apply_rows_coverage` 不修改输入、可以重复调用，带来源字段；闸门只认 request 来源的一致或人工接受。
- **状态库、锁与恢复**：
  - 投影按构建过滤，只读最新两份产物，产物损坏可以恢复；
  - `clean_unfinished` 只删“有意图、无结果”的 attempt 目录，并跳过符号链接；
  - `after_action` 的真实子进程崩溃测试覆盖 observe、logs、notify 三步；
  - WAL 加 busy_timeout；`append_retry` 只重试 stale_head 和 state_busy，排除同构建、人工、外部写类事件，不重做动作，显式给了期望编号时不重试；
  - 轮次锁忙计为跳过，连续 3 次才退出。
- **验收防冒充**：
  - 每次运行用独立的数据根目录；
  - B 要求本次新下载、传输完整、未截断、不是 HTML、摘要重算一致；
  - 在 Python 里重复核对提交号，只看本线目录是否干净，这两点都有测试；
  - 两次连续运行互不影响，有测试。
- **其余**：跳出 `except` 的异常分类、凭据净化（`sanitized`）、日志失败留证不含正文、loop 的信号处理。

---

## 第三部分：设计方计划在第 3 批修的三处

### ① tick 因新事件或状态库忙而放弃时，按“跳过”处理：方向对，有 4 处要补

位置在 [api.py:161-170](vd-cosmos-workflow/src/vd_cosmos_workflow/api.py#L161-L170)，现在只接住 `operation_locked`。

1. **人工活动引起的跳过不应计入“连续 3 次退出”**。FatTank 连着执行一串 confirm 或 confirm-group，每条都是本构建的新事件，loop 会因此连续跳过三次然后退出，还写一条 `loop_contention`。这正是不希望看到的结果。建议：
   - 锁忙、状态库忙：计入连续计数；
   - 本构建或人工裁决类新事件：不计数，并且隔一个较短的间隔（例如 5 秒）就重试，不等完整的 `interval_s`。
2. **只接住可以跳过的原因**。只有 `stale_head`（来自 `append_retry` 的放弃）和 `state_busy` 按跳过处理。`constraint`、`corrupt`、`workflow_artifact_digest_mismatch` 以及显式期望编号产生的 `stale_head`（[api.py:77-78](vd-cosmos-workflow/src/vd_cosmos_workflow/api.py#L77-L78)）仍然要退出。这条依赖 C-4 先把错误归类修好，否则数据库损坏也会被当成“忙”而跳过。
3. **动作之后才放弃的情形**：结果追加失败时动作已经执行了。现在的三个步骤（observe、logs、notify）都可以安全重做：日志有缓存，待办会去重。但要写明这条规则只适用于可重做的步骤。第 3 批的 analyze prepare、accept 这类步骤如果不可重做，放弃后就应该停止，不能跳过。
4. **新事件是 `round abandon` 时**：下一次 tick 的投影要能识别“已作废”并结束 loop，不能一直跳过下去。

- **夹具**：
  - 结果追加之前插入一条 HUMAN 类事件 → loop 继续运行，最终状态正确，notify 待办只有 1 条；
  - 连续插入 5 条人工事件 → loop 不退出；
  - 锁忙 3 次 → 退出，并写一条待办；
  - `corrupt` → 立即退出。

### ② 争用待办按每一段争用的首次时间区分版本：改法正确，补两个细节

位置在 [api.py:175](vd-cosmos-workflow/src/vd_cosmos_workflow/api.py#L175)，现在写死了 `'active_contention'`。

- 版本取这一段第一次跳过时的 UTC 时间，精确到秒，跳过计数清零时一起清掉。loop 重启以后自然开始新的一段，这是合理的。
- 和 ① 合并之后，跳过的原因（锁 / 忙 / 新事件）写进待办正文，不参与待办身份；否则同一段争用里原因一变，就会多开一条待办。
- **夹具**：两段争用之间有一次成功的 tick → 写两条待办；同一段争用里原因不同 → 只写一条。

### ③ 请求头里的版本号仍是 0.5.3：改法正确，建议一并统一来源

位置在 [config.py:15](vd-cosmos-core/src/vd_cosmos_core/config.py#L15)。

- 改成从同一个常量生成，例如 `f'VD-Cosmos-LogAnalyzer/{versions.PARSER_VERSION}'`，并加一条测试，断言 User-Agent 里包含当前版本号。
- 根本问题和 C-5 一样：手工维护的版本号会忘改。建议 C-5 一起改，让评估标识也绑定源文件摘要，以后版本号漏改只影响显示，不影响判定。

---

## 总结

- **阻断**：无。
- **第 3 批开工前必须改进 HLD 的重要项**：
  - H-8：路径分类，外部头文件和生成文件不按文件名找回；
  - H-9：shelve 的 base 来源；
  - H-7：P4 中途失效不能降级成“仅诊断”；
  - H-11：隔离核验用金丝雀，范围包括全局配置；
  - H-13：疑似真 bug 清单与匹配规则；
  - H-14：准确性验收的判定规则开跑前冻结，并防止答案泄漏。
- **随第 3 批一起修的代码和 HLD 项**：
  - H-1：终态捷径的前提，或者在 §14 第 3 条结清之前先停用；
  - H-3 / C-1：验收的非回环检查改为解析地址，并记录对端 IP；
  - 第三部分的 ①～③，按上面补充的条件实施；
  - C-4、C-5。
- **一般项，可以挂账**：H-2、H-4、H-5、H-6、H-10、H-12、H-15、H-16，C-2、C-3、C-6、C-7。其中 H-2 / C-2 已实测复现，修改很小，建议和 ① 一起做掉。
- **对已有真实验收结论的影响**：第 2.1 批构建机验收（A/B/C/E 全 PASS）的结论不受影响。真实运行连的是真实主机，日志也是本次新下载的。H-3 和 H-4 只是说明，脚本本身还不能自动挡住这两类冒充，F 段也没有进入结论。

上面是Claude Code的review意见
