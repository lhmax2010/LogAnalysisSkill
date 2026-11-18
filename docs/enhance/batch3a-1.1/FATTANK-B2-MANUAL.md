# FatTank 手工操作手册：Checkpoint B2

本页仅供控制终端人工使用；ClineSR 的 SKILL 不列出 once / recover / resolve。配置原件不进仓库。下面命令尚未在真实服务上执行。

## 构建机离线验收（无登录、无提交、无真实演练）

先进入本线部署目录，PATH 指向构建机已有 run/venv（Python 3.10.12、Playwright 1.64.1、import-linter 2.3）。EXPECTED_COMMIT 必须填本次最终回报的完整提交号，不用临时读取 HEAD 替代审定值。VD_CONFIG 是构建机现有配置绝对路径；VD_CHROME 是现有 Chrome 的可执行路径。不要安装浏览器或依赖。

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b2_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --chrome "$VD_CHROME"
```

验收核对提交/工作区、contract、静态扫描、完整离线套件，强制真实无头浏览器测试不能因缺依赖跳过。输出在原 data_root/verification/b3a11b2-<随机号>/，result.json 和 offline-tests.txt 均先过凭据检查；不复制真实配置，不做 A/B1 的在线检查。

## 之后由 FatTank 亲自在控制终端演练

必须先查看 B2 验收 PASS。仍保持 property_map_confirmed=false；不要为了通过演练临时启用正式提交。配置需要完整 18 项表单值、现有 browser_executable、登记的 auth_paths（主机/路径/方法）和精确 static_paths；名单默认空会拒绝。认证链路若依赖跨域 iframe，当前实现保守拒绝，不能扩大名单绕过框架拦截。

已有配置先用 `nice -n 19 python3 vd-cosmos-core/scripts/apply_property_map.py --config "$VD_CONFIG"` 写入 B2.4 对应表（同时留下原配置的私有备份）。首版要求 GITURL、Product Version (ks)、rpm Add & Delete、PACKAGE_LIST (DELETE)、PACKAGE_LIST (x86 arch) 全为空；两个复选框保持勾选，Image Skip? 使用打开表单时的预选文本。工具回读确认这些要求后才继续。演练核验编码前不要更改 `property_map_confirmed`。

```bash
nice -n 19 python3 vd-cosmos-submit/scripts/run.py once --config "$VD_CONFIG" --backend real --base-from-hub 37376237 --bm-build 19206687 --reason "FatTank B2 live rehearsal" --rehearse
```

该命令不由实现者执行。浏览器打开前先确认来源构建；Run 请求先阻断录制，终端确认 allow-run 后才允许完全相同的一次 GET；提交请求在演练中始终拒绝。回读全部属性后输入请求摘要前 12 位。首轮未登记编码只输出字段长度/摘要，verified=false 不等于编码确认。指纹/回调候选写入结果产物，由 FatTank 核对后人工更新本机配置，工具不自动登记。

## 会话恢复

```bash
nice -n 19 python3 vd-cosmos-submit/scripts/run.py recover --config "$VD_CONFIG" --session "$SESSION_ID" --holder-gone --reason "$REASON"
nice -n 19 python3 vd-cosmos-submit/scripts/run.py resolve --config "$VD_CONFIG" --session "$SESSION_ID" --no-manual-action --checked-at "$CHECKED_AT" --reason "$REASON"
```

只在确知旧持有进程已退出、并在提交端历史核对后使用。不得删除点击意图/暴露记录；uncertain 不能靠重新运行 once 消除。新请求、换输入也不能绕过。lookup --via-hub 尚未开放，仍明确拒绝；匿名 lookup/watch 不受 profile 锁阻挡。
