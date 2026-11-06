# SKEL-RESTORE-26:首次真机发现的归档通道缺口

日期:2026-11-05。基线6f5e801。状态:真机执行前停止,未消耗RESTORE-25的一次执行机会。
2026-11-06补记:已由SKEL-RESTORE-27采用候选B处置,本次明确接受上述字段
NOT_COLLECTED,以运行时检查通过及SHA/大小作为等价证据。原报告保留;
受限scope实测通过,等待用户本次确认“开始”,尚未执行真机发现。
这不是QuickBuild网络或安全停止事件,不是日志类型已判不符合。

## 1. 已完成的前置

- 新目录:`/home/linhao/Toolchain/campaign-discover-trial/r01/`,私有运行目录;
  config.yaml权限0600,state-root新建且未复用。state.db与kb.jsonl是新路径,尚无文件。
- qb.browser与tizen_base整个项目逐项等于stage20
  `evidence/C8/preparation/config.yaml`。本机三条可执行/模块路径存在。
- Gerrit真实值为`ssh://review.tizen.org:29418`,来源为本机`~/.ssh/config`
  的review.tizen.org条目(HostName、Port、User),不读取密钥、不改SSH配置。
  User只存仓外config,不写入本报告。Git署名取本机全局配置。
- clang_conf_path取已存在的`/home/linhao/Toolchain/gbs_llvm.conf`;
  仅供启动检查存在性校验,不宣称它与1204735实际build.conf一致,不用于本轮编译。
  max_rounds=3、max_build_invocations=12、push_retry=0等未使用配置仅填齐清单;
  本轮不建档、不编译、不推送。kb_db指向r01新文件。
- 预检项目platform/upstream/libtirpc,来源为已有1204735预筛记录
  `evidence/batch3.5/selection/candidates.md`及`source-facts.json`。
- `campaign-start-check`只执行一次,2026-11-05T12:27:13Z至12:27:17Z,
  exit0,五项通过。既有检查包含gbs --version,不是gbs build。
  Gerrit仅由SandboxGit执行ls-remote,无clone/fetch/push。
  完整argv/UTC/exit与固定JSON见[preflight-command.json](preflight-command.json)。

## 2. 无法原样完成的归档要求

RESTORE-25第三.1要求代理trace摘要含elapsed_ms,以及每份日志的Content-Type、
跳转/Download事实。当前正式CLI没有可供外部取证脚本读取的这些数据:

| 事实 | 代码位置(相对仓库) | 实际输出 |
| --- | --- | --- |
| Python命令trace不是代理runtime.trace | tizen-qb-verify/scripts/tizen_qb_verify/qb_browser.py:399–414 | 成功只追加command/ok;失败为固定failure_facts |
| CLI取的是上述trace | 同包qb_collect.py:133–135 | commands列表,没有elapsed_ms或网络元数据 |
| read_text归档应答 | 同包qb_browser_agent.mjs:912 | 只有path与sha256 |
| 元数据在读取时使用但未保留 | 同包qb_browser_agent.mjs:834–870 | Content-Type/下载/跳转用于fail-closed,函数只返回正文文本 |
| close也不返回代理trace | 同包qb_browser_agent.mjs:660 | 仅ok:true;Python.close不读取该应答 |

已验收的本地CLI证据同样显示此区别:
`evidence/restore/batch3/r24/accepted/focused/discovery/cli.json`的output.commands
没有这些字段;文件中另外的trace是测试harness直持Agent采集,不是生产CLI输出。
不能把该测试通道当成真机CLI已有通道。

日志SHA与字节数可由仓外文件计算,但不能从文件反推原HTTP Content-Type;
“运行时检查成功”也不能冒充实际记录的header或Download事件。
CLI失败路径还会抛弃collect内已累计的output,只返回最终错误。
因此先停止,不等登录后再发现证据缺口,不加调试协议或另建浏览器旁路。

## 3. 候选处置(未实施)

A. 批准一次只增加封闭观测的离线补修:发现会话逐条保留既有过滤后的trace
及elapsed_ms;read_text增加元数据的独立诊断记录(状态码、受限Content-Type形态、
redirected/downloaded布尔值、字节数);Python驱动严格校验,CLI无论成败在finally
落盘摘要。不改Policy、停止规则、清单schema、正文归档或网络访问范围;
不输出查询、其它响应头、身份、正文。先补元数据/敏感值/失败落盘测试及门禁,
再重新请求“开始”。具体应答/落盘键集合需设计方确认。

B. 明确授权本次接受缺项:代理完整trace/elapsed_ms及日志响应元数据记
NOT_COLLECTED,只保留现有命令级结果、日志SHA/大小,不得据此宣称没有任何代理
安全事件或实际Content-Type为何。其它只读/一次/dry-run要求不变。

## 4. 本轮停点

没有启动qb-discover/campaign-discover,没有浏览器或QuickBuild请求,
无清单、无包日志、无分析/跳过/将建档结果。state.db未创建。
没有修改生产代码、测试、冻结稿、既有运行目录或配置。
用户确认开始尚未请求;需先裁定上述归档缺口,不是要求提供任何凭据。
自动发现真机只读仍为未验证。

入仓检查:两个证据文件通过PageRedactor凭据自检;仓外配置中已知本机身份
完整词边界残留计数0。QB会话身份扫描为NOT_APPLICABLE_NO_LOGIN,
因为尚未登录,没有已登记的本次QB身份。日志正文/凭据/配置不入仓库。
