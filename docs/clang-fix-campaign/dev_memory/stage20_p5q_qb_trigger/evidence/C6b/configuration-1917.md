# Configuration 1917: Offline Table Extract

来源:[05.raw-redacted.html](raw-active-01/05.raw-redacted.html),同次导航的活动文档为
[05.active-redacted.html](raw-active-01/05.active-redacted.html)。以下仅摘录归档内容,
没有点击链接、发送额外请求或推断自动绑定方案。行号均为raw-redacted源行。
完整结构化单元格、链接和两侧行号在[offline-analysis.json](offline-analysis.json)。

## Build Requests

标题:830;table:837;表头:839。
表头依次为`空选择列 / Requested By / Schedule Date / Priority / Process Status / Master Node / Build Version`。
tbody共1行,Requested By已脱敏为`<USER>`。

| 行/源行 | Process Status | Build Version | 链接 |
|---|---|---|---|
| 1 / 862 | RUNNING_BUILD (单元格:872) | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261019.071746 | /build/1202070 (:882) |

1201886不出现在本表。

## Recent Builds

标题:892;table:901;表头:903。
表头依次为`Id / Version / Master Node / Begin Date / Duration / Triggered By`。
tbody共10行,Triggered By各行均已脱敏为`<USER>`。
class列为版本名链接的class原文(保留前导空格);每行还有状态图标class,
全部在offline-analysis.json中保留。

| 行/源行 | Id | 版本名(链接源行) | 状态class | Begin Date | Duration |
|---|---|---|---|---|---|
| 1 / 924 | 1202070 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261019.071746 (:936) | ` build-status running maskable` | 2026-10-19 07:17:46 | 7 seconds |
| 2 / 971 | 1201886 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261019.052151 (:983) | ` build-status successful maskable` | 2026-10-19 05:21:52 | 18 minutes 45 seconds |
| 3 / 1002 | 1201414 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261018.084117 (:1014) | ` build-status successful maskable` | 2026-10-18 08:41:17 | 4 hours 49 minutes 47 seconds |
| 4 / 1033 | 1200964 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261016.105352 (:1045) | ` build-status failed maskable` | 2026-10-16 10:53:53 | 1 day 4 hours 57 minutes 23 seconds |
| 5 / 1064 | 1200950 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261016.100620 (:1076) | ` build-status cancelled maskable` | 2026-10-16 10:06:20 | 12 hours 16 minutes 35 seconds |
| 6 / 1095 | 1200465 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261016.031921 (:1107) | ` build-status failed maskable` | 2026-10-16 03:19:22 | 9 hours 51 minutes 43 seconds |
| 7 / 1126 | 1200120 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261015.161304 (:1138) | ` build-status failed maskable` | 2026-10-15 16:13:05 | 5 hours 48 minutes |
| 8 / 1157 | 1199036 | [Snapshot] TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261015.022255 (:1169) | ` build-status successful maskable` | 2026-10-15 02:22:56 | 18 minutes 29 seconds |
| 9 / 1188 | 1198829 | TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261014.221921 (:1200) | ` build-status timeout maskable` | 2026-10-14 22:19:22 | 2 days 0 hours 0 minutes 11 seconds |
| 10 / 1219 | 1197829 | [Snapshot] TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261014.065008 (:1231) | ` build-status successful maskable` | 2026-10-14 06:50:09 | 11 hours 11 minutes 49 seconds |

版本名链接href均为`/build/<Id>`。1201886出现在本表第2行,Id源行972,
版本链接983,Begin Date单元格995,Duration单元格997。
运行中的1202070行另外含Stop入口文字与进度1%;没有点击或请求该入口。
这些只是配置页当时显示的行,不据此推断任何新提交来源。

## 原始正文与活动文档

两表完整HTML均**不是逐字一致**。差异原文见[configuration-tables.diff](configuration-tables.diff)。

- Build Requests:active在Schedule Date的change锚点增加`class="popup-trigger close popup-target"`,源行868。
- Recent Builds:active为每行的下拉菜单图标锚点追加同样三个class,
  源行937、984、1015、1046、1077、1108、1139、1170、1201、1232。
- 全部表头与单元格文字相同;Build Version/Version构建链接的文字、href及状态class相同。
  没有把class差异全局掩码后声称原字节相等。它不在现有比对工具的十项字段中。

| 表 | raw table SHA256 | active table SHA256 |
|---|---|---|
| Build Requests | b14add862f3cb5e98115cef00b01731512a067ace02bd96cea34cb5b7c11c2e1 | 9ba9fab29084e4cba7580660e2476daf844b6f201c650fce820aafe300273844 |
| Recent Builds | b41e3a53879912df939bbf3215ca60f8828ca82c848f82d5cf443e99d5286fb0 | e392a4a7cdcd584fdb1380077db28a20291e9106872672acb316fa2d2e57cf01 |

本节仅记录事实,不作v1.6的定位/绑定规则结论。
