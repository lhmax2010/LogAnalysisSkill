# RESTORE-24:发现文件交接与恢复剧本

基线4936377;裁定RESTORE-18/20/22/24。全部为本地假HTTPS、Chromium私有Xvfb、
假SSH/本地裸库、真实analyzer与假gbs,没有真实发现、登录、Gerrit访问或编译。
第三/四批共用同一最终树门禁,原始失败/开发记录不覆盖。

## 结果与证据

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 最终定向 | 53 passed | accepted/focused/pytest.xml |
| mypy | 172 source files,0 issues | accepted/mypy/stdout.log |
| ruff | 通过 | accepted/ruff/stdout.log |
| 依赖合约 | 7 kept,0 broken | accepted/imports/stdout.log |
| 设计检查 | 0 problem | accepted/design/stdout.log |
| Node静态断言及负例 | 183 passed,0 failed | accepted/static/stdout.log |
| 四组安全测试 | 4 passed,0 failed | accepted/safety/stdout.log |
| 完整全仓最终树 | 3501 passed,0 failed,1既有skip;1161.39秒 | accepted/full/ |
| 真实归档结构/作用域补充 | 21 passed,0 failed,0网络请求 | supplementary-scope/ |
| nodeid | 3454全部保留,新增48,合计3502 | nodeids.json |
| 保护文件与代理哈希 | 未授权保护文件不变;代理/驱动按裁定扩展 | protected-final.json |
| 最终树一致性 | 定向、全仓期间源码不改 | accepted/source-proof.json、accepted/integrity-after.json |

每条命令的argv、UTC起止、exit、耗时、前后loadavg/CPU核数/CPU前十进程名与占用,
分别见对应目录command.json。证据不含state.db二进制或真实凭据。
暂存diff检查仅有46处假服务HTML原始行尾空格,保留正文不改;排除证据HTML后通过。
分别见diff-evidence与diff-source,不是生产源码格式问题。

Worker组走b分支时,关闭浏览器并删除profile,攻击HTTP与WS握手均0;
closeTarget具体返回保留在accepted/safety/stdout.log。307/308、逐跳与凭据隔离沿用原断言。
全仓loadavg从2.42/2.06/3.14到1.65/1.44/1.78,20核;所有计时敏感用例通过,无重跑。
补充矩阵scope-matrix.mjs使用C6b真实脱敏归档,仅在about:blank惰性文档解析,
覆盖Recent Builds身份/六列表/精确ID/查询/行数,各阶段与未知帧拒绝,iframe基数。

## 用例对照

| 要求 | 位置 |
| --- | --- |
| 只接受已核验页面产生的精确路径、无全目录授权 | test_qb_discovery_scope.mjs的verified document chain、identity mismatch、scope-only grammar |
| 空格目录标准URL一次解析及拒绝文法 | 同文件canonical registration与16个路径反例 |
| 四列表、主架构、无class失败链接、歧义/未知arch | 同文件four columns、ambiguous五例、unknown arch |
| HTML入口/iframe/日志同一主帧链、零表单提交 | test_discovery_local_https_browser[ok]、test_real_qb_discover_cli_manifest |
| 日志HTTP/跳转/编码/附件/类型/64MiB | test_discovery_local_https_browser[status/redirect/encoding/attachment/binary/large] |
| 清单精确键集、路径/符号链接/哈希、原子发布 | test_campaign_discovery.py的manifest_rejected、resolve_rejects、atomic_no_overwrite |
| RESTORE-24进程白名单与非法project前置拒绝 | test_discovery_subprocess_boundary_clone_and_analyzer、manifest_rejected[project] |
| 过滤、显式override、arch前置门、幂等、dry-run | test_campaign_discovery.py对应四组 |
| 重跑新目录、since窗口、固定错误应答、不改旧read映射 | test_qb_collect.py |
| 畸形YAML固定JSON且不启动浏览器 | test_discovery_invalid_yaml_is_fixed_json两例 |
| 发现采集→文件消费→基线→导入T1→三架构修复→sandbox→KB追加→QB PASS→KB升级→审核→报告 | test_discovery_precedent_review_offline_chain |

完整命令/产物交接的真实Python+真实代理+本地浏览器证据:
`accepted/focused/discovery/cli.json`、`producer-requests.json`。
消费端全部Git/analyzer argv见`consumer-processes.json`;HTTP与浏览器进程均0。
恢复全链路使用假代理协议与原有假gbs/假SSH夹具,状态序列及先例引用见`restored-chain.json`。
原四条端到端用例与所有旧nodeid保留,不是用新路径替换旧断言。

## 开发记录与偏差

1. 初轮定向51通过;mypy通过;ruff只报新增intake入口import排序,已修正。
2. `final/`为第一轮全仓:3499 passed/1既有skip。该轮门禁runner最终hash断言为非零,
   原因是定向期间把误放在旧read的waitUntil撤回,发生于完整pytest启动前;
   `full-source-proof.json`保留时间/哈希依据。此轮不作为最终树一致性验收。
3. 封版再补两命令畸形YAML固定错误、恢复链路实际调用采集逻辑并留存进程/状态证据;
   `accepted/`从定向至全仓不再修改源码,是交付依据。
4. RESTORE-24“措辞冲突按既有行为处理”:SandboxGit本地rev-parse/origin/checkout
   不带远端URL,仍属原路径;实际clone目标逐字断言,并记录全部argv。
5. 设计偏差均由裁定覆盖:单命令改两命令清单交接;消费端允许既有Git/analyzer;
   未实测日志元数据改运行时fail-closed;只对登记html_report作永久禁令例外。
   不扩展continueResponse豁免,不修改既有提交/结果/审核规则或intake.add_unit。

日志真机响应仍未验收;第一次真实`--dry-run`另行裁定。本轮结束不运行真实发现。
