# FatTank 手工操作手册：Checkpoint B2

本页仅供控制终端人工使用；ClineSR 的 SKILL 不列出 once / recover / resolve。配置原件不进仓库。下面命令尚未在真实服务上执行。

## 构建机验收（离线套件与匿名源读取；无登录、无提交）

先进入本线部署目录，PATH 指向构建机已有 run/venv（Python 3.10.12、Playwright 1.64.1、import-linter 2.3）。EXPECTED_COMMIT 必须填本次最终回报的完整提交号，不用临时读取 HEAD 替代审定值。VD_CONFIG 是构建机现有配置绝对路径；VD_CHROME 是现有 Chrome 的可执行路径。不要安装浏览器或依赖。

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b2_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --chrome "$VD_CHROME"
```

验收核对提交/工作区、contract、静态扫描、完整离线套件，强制真实无头浏览器测试不能因缺依赖跳过。B2.6 新增匿名源读取：以 37376237 / 19206687 读取详情、变量和各架构报告头，使用与 once 相同的确认前校验，读取失败则验收 FAIL。只写验收产物，不写业务状态、不提示确认、不打开真实浏览器。输出在原 data_root/verification/b3a11b2-<随机号>/；result.json 的 source_preflight 只记录找到的字段名，不记录值。result.json 和 offline-tests.txt 均先过凭据检查。

## 之后由 FatTank 亲自在控制终端演练

必须先查看 B2 验收 PASS。仍保持 property_map_confirmed=false；不要为了通过演练临时启用正式提交。配置需要完整 18 项表单值、现有 browser_executable、登记的 auth_paths（主机/路径/方法）和精确 static_paths；名单默认空会拒绝。认证链路若依赖跨域 iframe，当前实现保守拒绝，不能扩大名单绕过框架拦截。

已有配置先用 `nice -n 19 python3 vd-cosmos-core/scripts/apply_property_map.py --config "$VD_CONFIG"` 写入 B2.4 对应表（同时留下原配置的私有备份）。首版要求 GITURL、Product Version (ks)、rpm Add & Delete、PACKAGE_LIST (DELETE)、PACKAGE_LIST (x86 arch) 全为空；两个复选框保持勾选，Image Skip? 使用打开表单时的预选文本。工具回读确认这些要求后才继续。演练核验编码前不要更改 `property_map_confirmed`。

登录后，dashboard 必须恰有一个可见的 `Sign Out` 链接或按钮（此标签不区分大小写）。从该控件向上最多三层找最近的欢迎区，`submit.account` 必须在可见文字中独立出现且大小写一致，例如 `Welcome! <account> Sign Out`。通过后才打开目标。各操作人在自己的配置中填写账号；若收到 `hub_account_mismatch`，请核对当前登录及 `account_check` 结果。结果保存控件和欢迎区的 tag/id/class；只有匹配且欢迎区文字不超过 80 字符才记录文字。目标表单的面包屑逐段核对 `submit.target_config`；不符时检查结果文件中的段列表。查号和绑定以候选变量页的 `HUB_CONFIG_ID`、`HUB_CONFIG_PATH` 和已列出的 `FROM_HUB_ID` 核对目标；前两项未核验时不能绑定。

B2.5 从 Hub 根地址开始 SSO。若遇到 Hub 自己的密码登录页，工具拒绝继续；请关闭并重新走 SSO。真实允许列表及账号放在私有 JSON 中，再导入以下五个可选字段：`auth_paths`、`static_paths`、`target_config`、`target_config_id`、`account`。认证条目严格匹配 host/path/method；带显式端口的主机须作为独立条目登记。输出只列变更键，原配置备份权限为 0600。任一确认标志为 true 时不更新。

```bash
nice -n 19 python3 vd-cosmos-core/scripts/apply_property_map.py --config "$VD_CONFIG" --browser-input "$VD_BROWSER_INPUT"
```

工具只以样式隐藏已识别的公告，不调用网页关闭函数。Run 按钮中心仍被遮挡，或隐藏公告期间有请求，演练会停止；不要绕过拦截。

```bash
nice -n 19 python3 vd-cosmos-submit/scripts/run.py once --config "$VD_CONFIG" --backend real --base-from-hub 37376237 --bm-build 19206687 --reason "FatTank B2 live rehearsal" --rehearse
```

该命令不由实现者执行。浏览器打开前先确认来源构建；Run 请求先阻断录制，终端确认 allow-run 后才允许完全相同的一次 GET；提交请求在演练中始终拒绝。回读全部属性后输入请求摘要前 12 位。首轮未登记编码只输出字段长度/摘要，verified=false 不等于编码确认。指纹/回调候选写入结果产物，由 FatTank 核对后人工更新本机配置，工具不自动登记。

命令入口通用确认仍输入 `yes`。之后按每次提示末行输入显示的精确值：

| 确认 | 终端提示示例 | 输入 |
|---|---|---|
| 来源构建 | 输入构建号 19206687 以确认 / type 19206687 to confirm | `19206687`；其他构建输入当次提示的构建号 |
| 放行 Run | type allow-run to confirm | `allow-run` |
| 请求摘要 | type the 12-character digest prefix 012345abcdef to confirm | 当次显示的 12 位摘要前缀；示例为 `012345abcdef` |
| 重提（仅指定 `--resubmit-of`） | type resubmit to confirm | `resubmit` |

终端仅显示摘要和 `Full JSON:` 路径。完整源清单、回读及历史见配置的 `data_root/submit/confirmations/` 下对应的 JSON 文件。路径以 `data_root/` 开头时相对于配置的数据根目录。答错时本次操作停止，错误的 `todo` 会重复应输入的值。输入“确认”不能代替构建号或确认词。

## 会话恢复

```bash
nice -n 19 python3 vd-cosmos-submit/scripts/run.py recover --config "$VD_CONFIG" --session "$SESSION_ID" --holder-gone --reason "$REASON"
nice -n 19 python3 vd-cosmos-submit/scripts/run.py resolve --config "$VD_CONFIG" --session "$SESSION_ID" --no-manual-action --checked-at "$CHECKED_AT" --reason "$REASON"
```

只在确知旧持有进程已退出、并在提交端历史核对后使用。不得删除点击意图/暴露记录；uncertain 不能靠重新运行 once 消除。新请求、换输入也不能绕过。lookup --via-hub 尚未开放，仍明确拒绝；匿名 lookup/watch 不受 profile 锁阻挡。
