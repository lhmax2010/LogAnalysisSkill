# 实际本地搜索范围

2026-11-04上午,仅本机读取。`rg`优先;没有网络搜索、HTTP请求、Gerrit/P4调用、
campaign命令、浏览器或编译。外部仓库只读,没有往llvm-optimize写入或推送任何东西。
未读取浏览器profile、cookie文件、凭据或进程命令行。

| 实际目录 | 方式与范围 | 结果/限制 |
|---|---|---|
| 本仓库docs/clang-fix-campaign/dev_memory | rg shelve/shelved;stage21 progress、冻结稿第7节;stage15 progress;stage20历史状态 | 找到链路取证,未找到本批所需同源shelve修法 |
| 本仓库docs/clang-fix-campaign/spikes | ef_report.md关键词读取 | SBS/RBS网页身份,非包编译首错 |
| 本仓库temp、tmp、.dev_memory、tests/fixtures | ls/rg --files,读取temp/log.txt等头部 | multi-assistant属Unified;合成日志/故障注入剔除;tmp少量受限目录Permission denied,不提升权限 |
| 本仓库tizen-gbs-log-analysis | SKILL.md、launcher、analyze/source_candidates/ctags相关调用检查 | 确认离线analyzer入口与输出语义 |
| /home/linhao/Downloads | 顶层ls,定向读取clang_shelve_cl_eval_all_20261016_zh.md、Clang_Fix_Evaluation_Table_Complete_1030.md、LLVM_Base改动说明_20261009_zh.md、Summary_Report_2_Tizen_Base_Changes_1030.md、Base manifest | shelve汇总主要为VD;OBS Base不是Tizen-Base-Toolchain同一工程 |
| /home/linhao/Downloads/files、files (3) | rg shelve/fix5/b844,仅md/txt/log | 未命中;未解压zip或tar |
| /home/linhao/Downloads/ci-triage-real-run.md | 只按shelve/QuickBuild/compile/Clang关键词检索 | 是检测环境操作说明,不是修法证据;不读取/使用其中凭据配置 |
| /home/linhao/Toolchain/LLVM_Upgrade | ls | Python/LLVM升级日志,无小包shelve链 |
| /home/linhao/Toolchain/development/rpms_all_building | ls;md/json/tsv中rg shelve;README/STATUS/INVENTORY定向读取 | VD/P4构建工具与合成testkit;不是Base修法来源 |
| /home/linhao/Toolchain/development/qb_1206511_base | summary/build_info,round2/summary | glibc GCC部分链接失败;不选 |
| /home/linhao/Toolchain/development/qb_1203397_lld | README/docs关键词、work/status.json与三包三架构原日志 | Base工程、成功耗时参照;成功不替代失败 |
| /home/linhao/Toolchain/development/qb_1204463_unified | 顶层ls | 标明Unified,未拿其日志作Base候选 |
| /home/linhao/Toolchain/development/llvm-lld/qb1215850 | analysis.md、顶层ls | 4包是Unified/lld,排除 |
| /home/linhao/qb_analysis/1204735_vs_1202044 | summary_overview、failed_packages.tsv、config目录;三包原日志、子构建主日志;整个x86_64/failed目录做位置型编译error检索 | 真实Base失败;三包失败类型与修法不对应。rg无命中不等于证明所有180包没有编译错误 |
| /home/linhao/Toolchain/development/llvm-optimize | 顶层ls;md/json中rg shelve;docs/qb_1199098_vs_1178133/FINDINGS.md;temp目录名称 | 只读。两QB属Unified,Base是关联依赖证据;没有拷贝产物或写入该仓库 |
| /home/linhao/Toolchain/codes、KnowledgeBase、libtool | 顶层ls | 没有扩展成全源码内容扫描 |
| /home/linhao/qb_fetch、work、temp、toolchain、Documents、tmp、cleanup-review-20261015 | 顶层ls;cleanup旧measurements关键词 | 不读取会话;旧磁盘数据不代替当次采样 |
| /home/linhao/Toolchain/p5q-live-validation/p5q-c6、p5q-c8 | 只列文件名 | 不打开/修改状态库、配置、凭据;不用历史成功记录充当修法 |
| /home/linhao/GBS-ROOT-TIZEN-UNIFIED-LLVM、GBS-ROOT-TOOLCHAIN-LLVM-R4-20260714 | ls目录;三个scratch只读du | Permission denied保留,未sudo;不清理 |
| /home1/chengkai/vd-tree/workspace/quickbuild | ls -d | exit2:本机不存在,未访问远端 |

目录发现还运行过一次:
`find /home/linhao/Toolchain /home/linhao/work /home/linhao/temp -maxdepth 5 -type d`
并按名字shelv/clang*fix/round/qb过滤。仅枚举目录名,不是读取所有子目录文件内容。
另对`/home/linhao`做过maxdepth2的clang目录名查询。
该发现过程正常退出,没有终止任何进程。没有扫描完整home隐藏凭据目录。

搜索有限,结论是“上述本地材料尚未证明存在合格候选”,不是“所有地方都没有”。
外部来源不整包入库,避免将无关身份/会话材料带入证据。
关键摘录/行号、源文件hash见source-facts.json、source-excerpts.json和config-hashes.json。
