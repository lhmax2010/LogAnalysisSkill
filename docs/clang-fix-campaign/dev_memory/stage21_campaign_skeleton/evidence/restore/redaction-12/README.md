# RESTORE-12 离线修复证据

基线57cac6e,2026-11-05。**门禁未通过,没有真机操作**。

- `root-cause-before.json`:纯合成正文复现splitlines/HTMLParser行号不一致,
  导致位置替换误伤标签、漏掉身份。生产LF偏移已修。
- `../discovery-capture/archive-redaction-12.json`:live-01无正文;
  live-02六份后处理,一份实际替换,残留全0。旧坏标签不猜测还原。
- `final-archive-check.json`:最终脱敏实现复检六份正文,只保存计数/hash。
- `focused/`为114项早期结果;`final-focused/`为最终115项通过。
- `capture-node/`:9项Node测试通过,真实Chromium、本机HTTPS,含唯一主帧请求;
  全仓中的`test_capture_spaces_session_redaction_and_remaining_three_pages`也通过。
- `full/`:不加-x完整运行,3433通过/1失败/1既有跳过,失败原文与JUnit原样保留。
  运行中新增稀疏边界映射及实体负例,所以最终树还须重新完整验收;
  不以本次部分新代码被运行冒充最终树门禁。非豁免失败后没有重跑放行。
- `gate-summary.json`:全仓封装用例结果,含安全4组、C5a、C8及静态负例。
- `final-mypy/`:169源码通过;`final-ruff-format/`:通过;
  `final-ruff/`保留此前一处新增代码行长失败,只换行已修。
- `imports/`:7合约通过;`design/`:0 problem。
- `final-nodeids.json`:3411既有全保留,新增25,最终3436。
- `integrity-final.json`:12个受保护文件与HEAD字节相同,代理/驱动未改。
- `cleanup.json`:无P5Q profile与自身代理/浏览器残留。
- 源码与说明文档`git diff --check`通过;全部证据检查另报29处行尾空白,
  均在原样的合成HTML、pytest输出/JUnit中,保留以免改写原始失败证据。

停止事实、未决项与候选处理见[停止报告](stop-report-SKEL-RESTORE-13.md)。
没有创建live-03,没有实施发现CLI或第四批。
