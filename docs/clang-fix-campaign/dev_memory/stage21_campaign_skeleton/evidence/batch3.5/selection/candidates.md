# SKEL-B3.5-01 选包预筛

日期:2026-11-04,Asia/Shanghai 白天。代码基线`fd4c6f6`。
**合格候选0个;不启动第3.5批。** 下表是已实际解析的3个预筛对象,均未入选,
不是三个满足条件的候选。不能把“Base工程失败”“Clang前端失败”“已有shelve修法”混为一谈。
推荐执行包:暂不推荐。补证优先级:elfutils > zlib > libtirpc;这不是执行顺序。

## 路径约定与来源

- `B=/home/linhao/qb_analysis/1204735_vs_1202044`
- `F=B/llvm_1204735/packages/standard/x86_64/failed`
- `S=/home/linhao/Toolchain/development/qb_1203397_lld/work`
- `D=/home/linhao/Downloads`
- 表中`F/zlib.buildlog.txt`等均为上述绝对本地路径,不是待下载URL。
- `source-facts.json`保存输入SHA256、三个架构的状态来源、原日志行号与时间边界。
- 本地下载的`D/tizen-base-toolchain_20261020.074527_standard.xml:44,97,236`
  分别列elfutils/libtirpc/zlib,证明工程成员身份,不把它的revision当1204735的输入revision。
  1204735各包日志第8行自身也写明project `Tizen-Base-Toolchain`。

## 预筛表(全部未入选)

| 补证排序/包 | QuickBuild / CI日志 | 人工修法、shelve CL、改动行数 | build.conf与base | 真实analyzer一次离线结果 | 单架构时间依据/排序理由 |
|---|---|---|---|---|---|
| 1 elfutils | 父1204735/子1204736;`F/elfutils.buildlog.txt` | 找到另一套OBS `Tizen:10.0:Base:Dev:LLVM` r2修法,不是shelve CL。2行源码替换(+2/-2),spec另+4行,两个patch文件;不能充当本包shelve完整diff。缺CL与同源基线映射 | base确定为`20261013.024319`;构建工作目录的build.conf确切字节未确定,见下节 | exit0,`needs_llm`,phase `%build`,primary `raw_error`,L391 `autoreconf: error: autopoint failed with exit status: 1`;**不对应**OBS修法的`-Wunterminated-string-initialization` | 历史成功QB1203397:arm318s/aarch64363s/x86136s,约2.3–6.1分钟/架构;小修法最具体,优先补证,但当前缺编译首错及CL |
| 2 zlib | 父1204735/子1204736;`F/zlib.buildlog.txt` | 在实际搜索材料中未找到对应shelve CL或修法diff;行数UNKNOWN,不是0 | 同上 | exit0,`needs_llm`,phase `%install`,primary `rpm_phase`,L584 Bad exit status。原日志L582–583为toybox Unknown command find/xargs;不是已证实的Clang编译首错 | QB1203397:arm134s/aarch64239s/x86105s,约1.8–4.0分钟/架构;体量小、日志齐,但没有对应修法 |
| 3 libtirpc | 父1204735/子1204736;`F/libtirpc.buildlog.txt` | 未找到对应shelve CL或修法diff;行数UNKNOWN。C6/C8既有PASS是链路验证,不能替代修法 | 同上 | exit0,`needs_llm`,phase `%install`,primary `rpm_phase`,L1732 Bad exit status;L1730–1731 toybox Unknown command find/xargs。另有320处`-Wdeprecated-non-prototype`**warning**、48文件,不能把它们当本次致命编译错误 | QB1203397:arm234s/aarch64274s/x86107s,约1.8–4.6分钟/架构;已有工程经验,但当前首错非编译,且warning集合大 |

时间均来自`S/logs/<arch>/<package>.log`的started/finished边界:
zlib结束行arm831/aarch64836/x86817;
libtirpc结束行arm1844/aarch641849/x861827;
elfutils结束行arm2309/aarch642315/x862292。
这些是另一轮成功构建的整包wall time(含初始化/打包),不是当前机器的编译峰值或保证时长。
1204735的失败时长x86分别为elfutils530s/zlib483s/libtirpc567s,也不能用失败提前结束估计修好后的总耗时。
三者在1203397三架构均有succeeded记录;证明三架构曾构建,不证明待选修法三架构通过。
没有取得精确BuildRequires闭包,因此“不存在大型依赖链”仍未证明。

## 配置可确定程度

本地`B/llvm_1204735/children/1204736/logs/build_1204736.log:310–312`
明确解析base为:
`http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319/repos/standard`。
第326行只给`buildconf=./build.conf`,没有其字节或P4版本。

已有发布配置(本轮重新算hash,见`config-hashes.json`):

| 本地文件(B下) | SHA256 | 能证明什么 |
|---|---|---|
| llvm_1204735/config/packages/build.conf | e7fb11ccd377cfb5df044bfbedabaefbf2701758be70d65b7d887a666de77d28 | 输出仓库发布配置 |
| llvm_1204735/config/effective_base/build.conf | e5187fd758a663eec273a434090aaab9f8e32f80a036e3bca2cf0352dd286945 | 已解析base的仓库配置 |
| llvm_1204735/config/base/build.conf | 同effective_base | Profile/base发布配置 |

两个配置hash不同。缺构建时实际`./build.conf`的归档字节或等价性证明,
不能任选一份声称完全复现QB。本地`B/summary_overview.md:18–35`也明确这个限制。

## shelve材料交叉核对与排除

1. `D/Summary_Report_2_Tizen_Base_Changes_1030.md:27,125–188`:elfutils
   `baseregs[][2]`改`[][3]`,OBS r2,初入`20260929.1`。这是另一OBS工程,
   不是本任务的Tizen-Base-Toolchain QB失败+shelve证据。前端warning与所解析autopoint不对应。
2. `D/clang_shelve_cl_eval_all_20261016_zh.md:71–79,107,818`:
   libdeflate CL14337558,Clang22 evex512修复,VD b844/b776/b165。
   未找到本机对应CI日志或CL完整diff;只有报告的编号/方案,没有可核验的改动行数。
   本地Base manifest没有libdeflate项目。**不入候选,不伪造analyzer输出。**
3. `D/Clang_Fix_Evaluation_Table_Complete_1030.md:245,257,275`:
   tbb CL14319329、toybox CL14409741、zypper CL14335725均为VD产品侧记录。
   toybox虽在Base manifest,但1204735自身为unresolvable,不是本次Clang编译失败;
   不能把VD toybox的FORTIFY/flags修法自动映射到Base的Unknown command。
   tbb/zypper不在该Base manifest中。
4. VD报告中的真实日志位置指向`/home1/chengkai/vd-tree/workspace/quickbuild/1006_1/`:
   `D/LLVM_Base改动说明_20261009_zh.md:29–33`。本机`ls -d`返回exit2/不存在,
   未SSH访问另一机器,未索要凭据。
5. `/home/linhao/Toolchain/development/qb_1206511_base/round2/summary.md:35–58`:
   glibc三架构失败是GCC部分链接`--gc-sections`报错,无对应shelve,
   且不是短编译小包。不拿安装了clang证明该失败用了clang。
6. `/home/linhao/Toolchain/development/llvm-lld/qb1215850/analysis.md:1–18,81–96`:
   ell/iw/prelink/wayland是Unified工程lld链接失败;只有proposed diff,不是shelve;
   不把其Base依赖仓库等同于包属于Base。
7. 本仓库`tmp/campaign-smoke/logs/E1-zlib-broken-baseline.log`等为历史本地故障注入,
   不是QB真实首错;测试fixtures与合成PASS也一律不充当候选。

## analyzer执行与证据

执行真实本仓库模块`gbs_analyzer`,导入位置:
`tizen-gbs-log-analysis/scripts/gbs_analyzer/__init__.py`。
每包只执行一次,完整argv/UTC/exit/stdout/stderr在`analyzer/<包>/command.json`等;
原始JSON、Markdown、trace、perf和sidecar在`analyzer/<包>/output/`,没有人工改写。
未提供源码root,按analyzer契约使用日志父目录;源码未落地/无法解析也照实保留。
三个输入日志前后SHA256一致。三个exit均0,但`needs_llm`不是匹配修法成功。
本轮没有修analyzer,没有执行编译,没有进行全仓测试(只新增筛选文档与证据)。

## 下一步必须补齐

请选包裁定提供/指定本机可读的一组同源材料:
Tizen-Base-Toolchain真实Clang编译失败的QB号与原始包日志、对应shelve CL及完整diff、
失败时源码revision、实际build.conf归档、base快照。
elfutils可优先补证,但当前**不得直接用于第3.5批**;若现有shelve只属于VD,
需设计方决定换材料或改范围,本轮不自行接受OBS/Gerrit提交替代shelve。
完整搜索范围见`search.md`,资源摸底见`environment.md`。
