# 真实格式的小规模夹具

来源：docs/enhance/batch1/real-snippets/ 两份原始 head120。报告头、CSS、汇总标题和表头写法原样保留，仅替换汇总数量，重新补完小规模明细与结束标签。保留未闭合 p、无引号 href、font/br、多空白等真实写法。明细为合成包；arm 4=1成功+2扩展错误+1编译失败，x86 2=1成功+1编译失败。

rows.txt 和 links.txt 是人工固定的独立验收输入，运行时不从解析器生成。expected-counts.json 是小规模固定预期；只能在 verify 的 fixture 模式使用。detail.html 为合成状态页：头部 failed，后面推广链接 successful，测试不能选错状态。其它格式 conflict 消息用于人工确认与待办测试。

这些文件只证明格式兼容和离线验收脚本可运行，不能声称构建机完整报告已通过验收。导出表标题尚待真实 Export 非零页面核实。
