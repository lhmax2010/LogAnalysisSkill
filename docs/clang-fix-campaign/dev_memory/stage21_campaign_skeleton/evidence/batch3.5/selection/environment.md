# 环境只读摸底

采样:2026-11-04约11:29 Asia/Shanghai(03:29 UTC),20核。白天执行。
完整argv、UTC起止、exit和stdout/stderr在`environment-raw/`与`environment-commands.json`。
没有结束进程、清缓存、清swap或GBS-ROOT;没有开启编译、浏览器或压力进程。

## 当次实测

| 项目 | 结果 |
|---|---|
| free -h | 内存total30Gi,used13Gi,free8.6Gi,buff/cache9.6Gi,available16Gi |
| swapon --show | /swap.img,file,4G,used3.9G,prio -2;free -h中swap剩109Mi |
| /proc/loadavg | 1.09 / 1.30 / 0.82 |
| nproc | 20 |
| 仓库盘 | /dev/sda1挂载/home,1.8T总、1.6T已用、133G可用、93% |
| 两个已有GBS-ROOT与仓库tmp/GBS-ROOT | 同一/home盘,不能把各行133G相加 |
| vmstat 1 3 | 后两个1秒区间si/so为4/0、0/0 KiB/s;b=0,CPU idle91%/97%,wa1%/0% |

vmstat第一行是开机以来平均值,不拿它的si14/so25当当前持续换页。
两个短区间没有持续换出证据,但不足以证明之后编译无内存压力。
swap接近满可能含历史冷页;不能据此要求立即swapoff,更不能由工具自行清空。

RSS前15(单位KiB,只保留进程名与RSS;同名行是不同进程,没有PID/命令行参数):

| 进程名 | RSS KiB |
|---|---:|
| epp-client-daem | 2288856 |
| code-insiders | 680544 |
| code-insiders | 640160 |
| code-insiders | 617460 |
| code-insiders | 609624 |
| chrome | 588632 |
| chrome | 580708 |
| code-insiders | 502840 |
| chrome | 488940 |
| code-insiders | 478080 |
| code-insiders | 400248 |
| code-insiders | 377380 |
| code-insiders | 363496 |
| xdg-desktop-por | 348332 |
| codex | 326040 |

原始输出:`environment-raw/top-rss.txt`。只列名称不建议自动终止其中任何进程。

## 三架构顺序执行的预留估算

**尚未选到合格包,因此无法给“所选包”的实测峰值。** 以下只是对zlib/libtirpc级小包、
有限编译并行度、三架构顺序执行的规划量级,不是本轮执行参数或已验收的门槛。
不能外推到LLVM、glibc或大型C++依赖链。

- 内存:建议预留8GiB available作为小包的初步规划预算,给构建进程/模拟器/缓存和宿主余量;
  顺序执行不把三架构RSS相加。当前16GiB available比该预算多约8GiB。
  本地日志没有Maximum RSS,本轮也未编译,因此这个数不是测得的最低需求或峰值承诺。
  选包后仍需依赖闭包、编译并行度及首次基线实测才能校准。
- 磁盘:初步预留40GiB新增空间,覆盖三架构保留的构建根、共享下载缓存、源码副本及产物。
  顺序编译只降低并发内存,**不意味着能删除前一架构受保护的副本**。
  当前133G空闲比规划预算多约93G,不需要为了本轮筛选清盘。
- 只读du量级参照(不是候选包的专用root):现有scratch.armv7l.0可读部分8,994,963,456B,
  scratch.aarch64.0为1,707,192,320B,scratch.x86_64.0为5,097,152,512B,
  合计约14.7GiB;历史campaign-smoke/src为9,699,328B。
  40GiB规划是对这个量级留额外缓存/源码/产物空间,不是从du推导的严格上界。
- du返回exit1:受保护的root/cache等目录Permission denied,原始stderr完整保留在
  `environment-raw/sizes/`;上述root大小只是可读下界。未sudo、未绕过权限、未改文件。
  因此不能说已经精确测得三个完整root大小。

## 是否需要用户先清理

**本轮不需要清理,也没有清理任何内容。** 就小包的初步预算而言,当前内存/磁盘余量尚可;
不建议仅因swap已用3.9/4GiB而主动清空交换区。需要注意的是swap余量很小、/home已用93%,
本次快照不能当作第3.5批启动许可。

选包和执行裁定下来后,请在无其它重编译任务的时段重新检查available/load/换页与磁盘;
若available低于规划预算或持续换出,先由用户自行保存工作、释放不需要的负载再评估。
若新增依赖/构建root估算超过40GiB,再调整磁盘预算,不要擅自清GBS-ROOT。
当前真正阻塞选包的是同源CI失败+shelve修法证据缺失,不是已证实的资源不足。
