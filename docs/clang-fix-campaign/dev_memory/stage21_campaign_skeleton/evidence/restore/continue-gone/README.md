# RESTORE-10:continueRequest失效的离线复现与窄化

基线c68b800;当前仅离线,真机重取证须待完整门禁通过、修复单独提交后进行。

## 复现与差异

| 记录 | 次数 | 确认取消/真实continue失效 | read结果 | 清理 |
| --- | --- | --- | --- | --- |
| reproduce-01 | 3 | 每次3资源,共9/9 REQUEST_ID_INVALID | 3/3失败,无正文,原规则FETCH_CONTINUE_FAILED | 3/3 profile_removed |
| fixed-01静态资源 | 3 | 每次3资源,共9/9 REQUEST_ID_INVALID | 3/3当前read及下一read成功 | 3/3 profile_removed |
| fixed-01主文档 | 1 | Network确认取消,真实continue REQUEST_ID_INVALID | QB_BROWSER_UNAVAILABLE,无正文;服务器实收0 | profile_removed |

复现使用现有假HTTPS服务器,测试入口增加默认关闭的CSS/JS/图片资源,
另一路图片在服务器延迟3000ms。只有测试入口延后continue的发送,等待
Network.loadingFailed(canceled=true)后使用原send。没有伪造拒绝,不调用
Fetch.failRequest来制造这三份资源的取消。每次序列/资源类型/匿名序号/代次/时间
见各`result.json`;argv、UTC、loadavg与退出码见`command.json`。

生产diff仅installGuards +3/-3行。新增CONTINUE_TARGET_GONE字段与DENY_TARGET_GONE
相同:action、phase、stage、path(形态)、generation;每次都记,不占第一条失败。
continueResponse的全部失败与continueRequest的非失效类别仍停止。
静态资源暂停时phase为login,generation2,实际continue发生在下一导航generation3;
真机原样本phase=read,所以这里只确认同一失效机制,不伪称精确还原那条未知资源。

主文档取消用例的UNKNOWN是原命令映射诊断,其错误来自page.goto/NAVIGATION_INTERRUPTED;
没有读取正文,不算本次修复之外的自然回归。

## 验收索引

- `integrity.json`:前后代理完整/前缀hash,installGuards之外逐字节相同,保护文件未改。
- `nodeids.json`:原3410个全部保留,新增真实Chromium pytest入口1个。
- `node-matrix/`:388项通过;新增重复continue失效/首因保留/trace异常用例,
  旧矩阵只更新continueRequest失效参数对应期望,其它类别断言不变。
- `mypy/`、`ruff/`、`imports/`、`design/`:静态门禁均exit0。
- `full/`:完整全仓(不加-x)3410 passed/0 failed/1 skipped,1211.96秒;
  旧文件系统条件skip保留,无新增skip。负载前15.78/14.25/10.71,后8.29/6.28/7.38,20核。
- `safety/`:原脚本四组全部通过,服务器请求与握手清单原样归档,临时目录删除。
- `observations.json`:C5a六种落点均通过、无OPERATION_FAILED/AGENT_STOPPED;
  C8十一场景完成,无harness_failure,profile_removed均true。
  C8独立SIGINT清理探针仍有已知短暂残留,已由探针删除(own_residue_removed=true)。
- `validation.json`:68份HTML通过生产脱敏自检,最终profile及P5Q进程无残留。
- `diff-check.json`:代码/文档检查通过;23份原始HTML的行尾空白留证不改。

尚未访问真实QuickBuild,未推送Gerrit,未运行真实gbs。
