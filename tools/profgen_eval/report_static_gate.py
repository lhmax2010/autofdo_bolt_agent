"""Assemble static-only evidence; no profile input."""
from static_gate_data import *
def pct(x):return "未定义" if x is None else f"{100*x:.6f}%"
def table(headers,rs):
    return "\n".join(["| "+" | ".join(headers)+" |","|"+"|".join("---" for _ in headers)+"|"]+
                    ["| "+" | ".join(str(v) for v in r)+" |" for r in rs])+"\n"
def main():
    ss={o:json.loads((OUT/(o+"-static/summary.json")).read_text()) for o in OBJECTS}
    aa={o:json.loads((OUT/(o+"-ambiguity/summary.json")).read_text()) for o in OBJECTS}
    resources=[];failures=[]
    for p in sorted(OUT.rglob("resources.json")):
        r=json.loads(p.read_text());r["path"]=str(p.relative_to(WORK));resources.append(r)
    for p in sorted(OUT.rglob("result.json")):
        r=json.loads(p.read_text())
        if r.get("exit_code",0):failures.append(dict(path=str(p.relative_to(WORK)),exit_code=r["exit_code"]))
    resource=dict(tasks=len(resources),memory_peak_bytes=max(r["memory_peak_bytes"] for r in resources),
        min_memavailable=min(r["min_memavailable"] for r in resources if r["min_memavailable"] is not None),
        resource_terminated=sum(r["resource_terminated"] for r in resources),failures=failures,
        tasks_with_resources=resources,scope="3G/200%; serial nice19/ionice-c3")
    dump(OUT/"resource-summary.json",resource)
    report=WORK/"docs/profgen/eval/prep/05_identity_gate_and_coverage.md"
    old=report.read_text();hist=old[old.index("## 6. "):];prefix=old[:old.index("## 6. ")]
    prefix=prefix.replace("# N.5 阶段1身份门禁与覆盖：历史停止与修订1验收",
        "# N.5 阶段1：普通候选、歧义证据包与静态 U/③")
    prefix=prefix.replace("## 1. 门禁状态","## 1. 历史门禁状态（补充3修订1之前）")
    prefix+="""
### 5.2 已推送的普通候选完整结果

普通结果提交 d9814714502baa2a0d446f98efb9b6c8fe75bf65；
继续静态计算裁决提交 838c88699d3c1faab2297ff4682956a35a990a2c。
集中索引：[ordinary-index.json](evidence/identity-gate/ordinary-index.json)。
四个完整清单的SHA在索引内；静态API再次枚举的DIE集合、名字、声明位置与清单逐项相等。
每个映射范围内函数都是完整清单的子集，未决0。真实多候选数量0，
多候选建立对应与多候选歧义均为0。单候选失败参考DA按候选行并集：
spike两侧0，FFmpeg Thumb1605399811、A321626239322，不按DIE重复累加。

## 6. identity_ambiguous 证据包（四个对象）

每组为规范化（decl_file、去后缀名字）及其全部S实例、参考候选。
本次歧义全部由单候选行范围检查失败触发；“来自不同TU”是覆盖副本的属性，
不是说出现了多个合并后的源函数候选。

机械分类在 ambiguity_package.py 的 mechanical 函数：a=不同PGO前缀；
b=有条件编译/重复include的编译器正面证据；
c=同TU同变体的不同C定义声明位置；否则d，保留失败原因。
没有b证据就不按模板文件名猜测。本数据b/c均为0。
每组恰好一类；类内DA按文件行去重，本数据不同类没有重叠行。
分类不是消歧裁决，identity_ambiguous全部保留。

"""
    prefix+=table(["对象","组数","涉及C行","DA分子","ΣR(C)分母","比例"],
                  ([o,aa[o]["groups"],aa[o]["involved_reference_lines"],aa[o]["DA"],aa[o]["denominator"],pct(aa[o]["fraction"])] for o in OBJECTS))
    prefix+="\n"+table(["对象","类别","组数","DA","占ΣR(C)"],
                  ([o,c["category"],c["groups"],c["DA"],pct(c["fraction"])] for o in OBJECTS for c in aa[o]["categories"]))
    prefix+="""
### 6.1 明细与前90%清单

每对象 evidence/identity-gate/<object>-ambiguity/index.json 记录CSV分片SHA；
top.md按DA降序列至少20组并达到90%累计唯一DA。
Thumb/A32前20组分别覆盖1605399764/1605399811与1626239275/1626239322；
spike无歧义组，清单为空，不虚构20条。

- [Thumb前20](evidence/identity-gate/ffmpeg-thumb-ambiguity/top.md)；
  [A32前20](evidence/identity-gate/ffmpeg-a32-ambiguity/top.md)；
  [spike Thumb](evidence/identity-gate/spike-thumb-ambiguity/top.md)；
  [spike A32](evidence/identity-gate/spike-a32-ambiguity/top.md)。
- S-instances分片：每个S实例的CU、完整名字、decl_file/line、全部low/high区间、
  subprogram/inlined_subroutine标签、abstract_origin偏移、失败检查及叶子行集合。
- candidates分片：合并参考身份、行范围、FNDA、候选行DA及C声明位置；
  candidate-copies分片：完整PGO名字、TU前缀、完整linkage、FNDA、
  命令编号及同linkage的C侧有代码DIE。此字段为空不证明C中没有抽象或优化掉的定义，
  不用于改变原身份判断。
- commands分片：完整实际命令、构建日志与行号、源文件完整相对路径。
  每个PGO副本都有命令索引；有多个命令时保留全部，不凭basename作新消歧。
- 按group/reference_id连接表，避免每行重复大对象；CU/TU/linkage事实供后续裁决，
  FNDA与DA不参与身份闭合。原有单候选C定义证明仍在共享definitions索引中。

### 6.2 三个独立1%门槛

unmatched_in_elf为已执行参考源函数没有已建立唯一对应的S实例；
仅在identity_ambiguous候选集合中不算建立对应。两种原因可重叠，
账本保留完整原因集合而不重复计数。边界按完整同名顶层组处理，本次无失败组。

"""
    prefix+=table(["对象","原因","行数","DA分子","分母","比例",">1%"],
        ([o,k,v["lines"],v["DA"],v["denominator"],pct(v["ratio"]),v["exceeds_one_percent"]]
         for o in OBJECTS for k,v in ss[o]["gates"].items()))
    prefix+="""
## 7. 静态 U、损失账本与登记状态

### 7.1 实现与输入边界

static_map_bridge.py在temp生成独立辅助程序，链接GBS LLVM 22.1.8公开DWARF/
symbolizer API；复制未修改的IPBoundary.cpp/.h并核对SHA，复用已有边界规则。
没有重编或修改GBS clang、官方llvm-profgen或LLVM源码，没有运行profile转换器。
边界实现与工具共享，本次不是独立objdump复测，也不替代此前边界验收。

先验证全部有代码DIE清单，再由父链导出顶层组并按原始名字取完整闭包。
范围由已执行参考对应或含已执行候选的identity_ambiguous导出；
只含系统头、not_instrumented、未执行参考及FNDA=0宏函数的组不纳入。
各对象groups索引保存完整角色与选择清单SHA；四对象均无“去后缀名字等于已执行参考、
却在映射范围外”的待逐个裁决组。

字节取运行ELF，映射符号取调试ELF；叶子/非叶子line0不产生键，
偏移为(Line−StartLine)&65535，discriminator按工具规则，名字不demangle并保留后缀。
GNU AS奇数下界与别名一致性校验沿用现有规则；本轮line_before_start为0。
值通过确切叶子DIE结论取得，未执行源函数的键不能替已执行源函数填行。
没有RUN、采集资格或样本量参与。

static_coverage_gate.py用SQLite控制内存，输出mapping、U、exclusions、weights分片；
audit_static_gate.py从CSV独立复算并集、权重与损失。
宏只按FileID/region类型识别；C与macro-only行交集为空的断言通过。
不按宏文件名整文件删除。n_eff=null及K无定义分支有夹具。
这不是N.5的合成profile全地址验收；本任务没有执行后者。

"""
    prefix+=table(["对象","U/C行","①","②","③","③′","n_eff","K","③档","登记状态（本表门槛）"],
        ([o,str(ss[o]["U_lines"])+"/"+str(ss[o]["C_lines"]),*[pct(ss[o][k]) for k in ["coverage_1","coverage_2","coverage_3","coverage_3_prime"]],
          str(ss[o]["n_eff"]),ss[o]["K"],ss[o]["coverage_3_tier"],ss[o]["registration_status"]] for o in OBJECTS))
    prefix+="""
②分母为整个覆盖导出的已覆盖行；①、③分母分别为C行数、C行DA。
spike两侧K<50，仅描述。“可登记”只表示本表门槛不禁止，不表示其余N.5已完成，
不授权现在登记修正案3。FFmpeg两侧身份歧义、unmatched均>1%，且③<50%，不可登记。
按裁决完成全部静态表后停止。

④的条目分类比例统一为：**未计算（需要 RUN 的 body 分母，修正案3登记后按 RUN 计算）**。
下列仅为静态部分，不充当body比例：

"""
    prefix+=table(["对象","歧义键","受影响行","涉及C行","identity歧义组/行","系统头地址/字节","宏函数地址/字节"],
        ([o,ss[o]["static_4"]["ambiguous_keys"],ss[o]["static_4"]["affected_lines"],ss[o]["static_4"]["affected_C_lines"],
          str(aa[o]["groups"])+"/"+str(aa[o]["involved_reference_lines"]),
          str(ss[o]["static_special_code"]["by_kind"]["system_header_no_reference"]["addresses"])+"/"+str(ss[o]["static_special_code"]["by_kind"]["system_header_no_reference"]["code_bytes"]),
          str(ss[o]["static_special_code"]["by_kind"]["macro_generated_function"]["addresses"])+"/"+str(ss[o]["static_special_code"]["by_kind"]["macro_generated_function"]["code_bytes"])] for o in OBJECTS))
    prefix+="\n系统头统计为映射范围内叶子DIE属于裁决1的唯一已证明指令起点及其指令长度和，包含line0地址。逐文件/函数见special-code分片。宏函数全部FNDA0且不在映射范围内，规模0。\n\n"
    prefix+=table(["对象","宏region行DA","macro-only DA","覆盖总DA","macro-only占比","宏展开文件全部DA（描述）"],
        ([o,ss[o]["macro_reference"]["macro_region_DA"],ss[o]["macro_reference"]["macro_only_DA"],ss[o]["all_DA"],pct(ss[o]["macro_reference"]["macro_only_fraction"]),ss[o]["macro_reference"]["macro_expansion_files_all_DA"]] for o in OBJECTS))
    prefix+="\n### 7.2 完整互斥损失分桶\n\n保留完整原因集合，不用一个原因覆盖其他原因；四对象独立复算差值均为0。\n\n"
    for o in OBJECTS:
        s=ss[o];prefix+="**"+o+"**\n\n"
        prefix+=table(["完整原因集合","行数","DA"],([", ".join(x["reasons"]),x["lines"],x["DA"]] for x in s["loss_buckets"]))
        e=s["loss_equation"]
        prefix+="\n{} − {} − {} = **0**（assertion通过）。\n\n".format(e["R_C"],e["R_U"],e["sum_loss"])
    prefix+="""
无键损失示例：spike.c:69、70各DA=4063610861；
FFmpeg的libavcodec/arm/cabac.h多行各DA=255523038。
这是参考行有计数、静态映射没有对应唯一键的事实；没有把“同函数其他行有键”
扩大成这些行也可评价。完整参考身份与并存原因都在exclusions分片。
改变行域需要裁决，不能挑选DA大的条目修补。

### 7.3 产物、复现与执行失败

各对象static/index.json列出所有分片及SHA；summary.json为对象表，
audit.json为独立CSV复算。上层inventory-command/map-command记录运行/调试ELF SHA、
辅助程序SHA、完整原始输出路径与SHA。大JSONL、SQLite、辅助程序只留
temp/prep-static-gate/。各命令逐个经run_scoped.py执行：

    python3 tools/profgen_eval/static_map_bridge.py build
    python3 tools/profgen_eval/static_map_bridge.py inventory <object>
    python3 tools/profgen_eval/static_gate_data.py <object>
    python3 tools/profgen_eval/static_map_bridge.py map <object>
    python3 tools/profgen_eval/static_coverage_gate.py <object>
    python3 tools/profgen_eval/ambiguity_package.py <object>
    python3 tools/profgen_eval/audit_static_gate.py <object>

保留的实现失败：GNU外部CU无decl_line文本，首次完整性比较空串转整数失败，
改为与API的0核对，身份不变；歧义包首次误把CU header偏移当CU DIE偏移查表，
改用完整清单的CU DIE键。原始失败scope保留，均非身份规则未决。
C定义明细补充内联有代码DIE；首版仅取out-of-line的派生产物保留temp。
spike Thumb初版n_eff分支标签阈值误写5，审计改为冻结阈值3，数值与U未变。

"""
    prefix+="原88项保留、新增25项synthetic，共**113通过、0失败**，见static-tests/。包含完整内联键、零行、偏移取模、后缀、四类机械分类、重叠损失、空/常量权重、n_eff null、K并列/零值/仅描述。\n\n"
    prefix+="本轮memory.peak最高{}B，最低MemAvailable {}B，资源阈值终止{}次、无OOM。resource-summary.json保留各scope原文索引。前一阶段普通候选OOM仍见5.1，不混为本轮峰值。\n\n".format(resource["memory_peak_bytes"],resource["min_memavailable"],resource["resource_terminated"])
    prefix+="""
### 7.4 停止与边界

身份未决仍为0，未扩大任何裁决。③<50%及1%门槛均保留。
现在停止等待歧义类别和低保留率裁决；不登记修正案3、不做仿真或其他N.5。
没有读取正式sample profile、RUN body比例或受控量；不碰板子，
不改LLVM、设计、认证及三个用户配置。项目输入产出均在WORKDIR；
GBS clang包装器固定TMPDIR到WORKDIR/temp/tmp，clang本体未重编。未发现项目文件越界写入。

## 8. 本轮人工裁决

不可登记不等于停止静态计算，全部对象静态表照常完成；不放宽门槛。
④body比例依v1.5第538/540行属登记后RUN级量，登记前不计算。
完成证据后停止，不进入其他准备阶段。

## 9. 保留的此前上界计算与停止记录（历史）

"""
    hist=hist.replace("## 6. ","### 历史6. ").replace("### 6.1","#### 历史6.1").replace("## 7. ","### 历史7. ").replace("### 7.1","#### 历史7.1").replace("## 8. ","### 历史8. ")
    backup=TEMP/"report05-before-static.md";assert not backup.exists()
    backup.write_text(old);report.write_text(prefix+hist)
    status=WORK/"docs/STATUS.md";s=status.read_text()
    entry="""## 静态身份门禁与U完成（2026-11-11；停止等裁决）

- 普通候选推送d981471，继续静态计算裁决838c886。四对象完整身份未决0；未新增或扩大裁决。
- [05报告§6–7](profgen/eval/prep/05_identity_gate_and_coverage.md)：spike Thumb/A32的③=54.643726%/54.044553%，K=19/10、n_eff=1.328515/1.299623，仅描述。本表门槛可登记不表示其余N.5已完成。
- FFmpeg Thumb/A32的③=19.269762%/19.172781%，均<50%；identity_ambiguous=5.580146%/5.652581%，unmatched_in_elf两侧2.284188%，均>1%；boundary_unavailable=0。当前不可登记。
- U/排除清单/权重、①②③③′/n_eff/K与互斥损失账本已生成，四个差值为0断言通过。④body比例未计算；静态歧义键0，身份歧义组1795/1802，前20组覆盖>99.99999%歧义DA。SHA索引见[evidence/identity-gate](profgen/eval/prep/evidence/identity-gate/ordinary-index.json)及各对象index。
- 映射范围系统头地址/字节：FFmpeg Thumb3067/10036、A323375/13500；spike两侧0；宏函数0（FNDA0、范围外）。原88+新增25=113项测试通过。本轮峰值{peak}B，最低MemAvailable {minimum}B，无OOM/资源阈值终止。
- 已停止，等待歧义类别及低保留率裁决。修正案3未登记；不做仿真/其他N.5，不打开正式sample profile，不计算正式受控量，不碰板子。

""".format(peak=resource["memory_peak_bytes"],minimum=resource["min_memavailable"])
    s=s.replace("## 裁决2补充3修订1执行状态",entry+"## 裁决2补充3修订1执行状态",1);status.write_text(s)
    print(json.dumps({k:v for k,v in resource.items() if k!="tasks_with_resources"}))
if __name__=="__main__":main()
