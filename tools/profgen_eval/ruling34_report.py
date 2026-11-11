"""Write final evidence comparison and report tables; no sample profiles."""
import json,collections,hashlib
from pathlib import Path
from ruling34_inputs import OUT,dump
from static_gate_data import OBJECTS,OUT as OLD
from apply_header_ruling import rows
def table(head,data):
    return "\n".join(["|"+"|".join(head)+"|","|"+"|".join("---" for _ in head)+"|"]+["|"+"|".join(str(x) for x in r)+"|" for r in data])
def pct(x):return "null" if x is None else f"{100*x:.6f}%"
resources=[json.loads(f.read_text()) for f in OUT.rglob("resources.json")]
resource=dict(scopes=len(resources),minimum_MemAvailable_bytes=min(r["min_memavailable"] for r in resources if r["min_memavailable"]),
 maximum_cgroup_memory_peak_bytes=max(r["memory_peak_bytes"] for r in resources),
 resource_terminated=any(r["resource_terminated"] for r in resources),
 failures=[dict(scope=r["scope"],exit_code=r["exit_code"]) for r in resources if r["exit_code"]])
dump(OUT/"resources-summary.json",resource)
comparison=[];ct=[];mt=[];gt=[];lt=[];st=[];et=[];real=[];ae=[]
for obj in OBJECTS:
 old=json.loads((OLD/(obj+"-static/summary.json")).read_text())
 new=json.loads((OUT/(obj+"-static/summary.json")).read_text())
 dom=json.loads((OUT/(obj+"-C-domain/index.json")).read_text())
 ident=json.loads((OUT/(obj+"-rev1-identity/summary.json")).read_text())
 proof=json.loads((OUT/(obj+"-rev2-proof/summary.json")).read_text())
 assert new["loss_equation"]["difference"]==new["old_C_to_new_U_loss"]["difference"]==0
 comparison.append(dict(object=obj,old=old,new=new,C_domain={k:v for k,v in dom.items() if k!="parts"}))
 ct.append([obj,dom["old_C_lines"],dom["new_C_lines"],dom["old_R_C"],dom["new_R_C"],dom["code_free_lines"],dom["code_free_DA"]])
 for label,r in (("旧",old),("裁决3+4修订2",new)):
  mt.append([obj,label,r["U_lines"],r["R_U"],pct(r["coverage_1"]),pct(r["coverage_2"]),pct(r["coverage_3"]),pct(r["coverage_3_prime"]),
    "null" if r["n_eff"] is None else f'{r["n_eff"]:.6f}',r["K"],r["registration_status"]])
 for reason,g in new["gates"].items():gt.append([obj,reason,g["DA"],g["denominator"],pct(g["ratio"]),g["exceeds_one_percent"]])
 for b in new["loss_buckets"]:lt.append([obj," + ".join(b["reasons"]),b["lines"],b["DA"]])
 x=new["S_key_lines_outside_new_C"];st.append([obj,x["lines"],x["known_DA"],x["without_reference_DA"],x["formerly_in_C"],x["formerly_in_C_DA"]])
 e=proof["original_e_subset"];et.append([obj,e["instances"],e["groups"],e["reference_DA"],proof["original_e_verdicts"]])
 for x in proof["a_e_classes"]:
  if x["instances"] and x["instance_class"][0] in "abcde" and x["instance_class"][1:2]=="_":
   ae.append([obj,x["instance_class"],x["verdict"],x["instances"],x["groups"],x["reference_DA"]])
 for r in rows(OUT/(obj+"-audit"),"real-examples-*.csv"):
  x=json.loads(r["example"]);name=x["requested"]
  # Exact named function, allowing its C++-style internal LLVM linkage suffix.
  if (name+"P") in x["name"] or x["name"]==name:
   real.append([obj,x["name"],x["instances"],x["old_reasons"],x["new"],x["new_reasons"],x["new_statuses"]])
 dump(OUT/(obj+"-static/ACCEPTANCE.json"),dict(status="validated_ruling3_and_ruling4_revision2",registration_gate_status=new["registration_status"],
       actual_registration_deferred_until_v1_6_review=True,no_amendment3=True,formal_sample_profiles_opened=False))
dump(OUT/"comparison-final.json",comparison)
root=Path("docs/profgen/eval/prep/05_identity_gate_and_coverage.md")
s="""
## 10. 裁决3、裁决4修订1/2与新旧对照（2026-11-11）

基于a8aae984c31fa89cca5eefad46b60ace75539087。裁决及两次修订原文见[rulings.md](rulings.md)，待折入v1.6并经三家评审后才可登记。本轮已完成静态计算并停止；修正案3未登记，未打开正式sample profile，未计算RUN受控量，未连接板子。旧规则代码与旧结果不变。

### 10.1 实际编译参数、来源与实现

[compile-options.json](evidence/identity-gate/ruling3-4/compile-options.json)与各对象S/C的commands分片记录完整命令、实际构建日志路径/行号、日志SHA、编译器SHA。spike各1条，FFmpeg各311条libavcodec C源文件命令；不是依据spec推测。

|对象（S/C相同）|优化选项（末项生效）|调试选项|ISA选项（末项生效）|
|---|---|---|---|
|spike Thumb|-Os|-g2 -gdwarf-4 -g|-mthumb -mthumb|
|spike A32|-Os|-g2 -gdwarf-4 -g|-mthumb -marm|
|FFmpeg Thumb|-Os -O3|-g2 -gdwarf-4 -g -g|-mthumb -mthumb -mthumb|
|FFmpeg A32|-Os -O3|-g2 -gdwarf-4 -g -g|-mthumb -marm -marm|

所有S/C均有-fdebug-info-for-profiling、-funique-internal-linkage-names；C另有-fprofile-instr-generate、-fcoverage-mapping。首次摘要将dv_profile.c等文件名误识为选项，已修为只看以减号开头的参数；首轮输出保存在temp/prep-ruling3-4/compile-option-first-pass，最终为compile-options-v2-run。

新增Python入口为ruling34_inputs、ruling34_dwarf、ruling3_domain、ruling34_rules、ruling4_dwarf、ruling4_apply、ruling4_keys、ruling4_callsite、ruling4_rev2_evidence、ruling34_static、ruling34_audit；都在tools/profgen_eval。只编译取证helper并链接GBS LLVM公开API，没有修改或重编clang本体、LLVM/profgen源码或补丁。原有static_coverage_gate等入口不变。

### 10.2 裁决3：C构建自己决定C

C参考函数匹配来自C调试ELF的名字/声明与覆盖记录；候选须唯一且FNDA>0。C自身行表非零、非end_sequence记录的地址DIE链须落在已执行参考函数代码内。没有用S行表或S映射决定C。原macro-only排除保留。

"""
s+=table(["对象","旧C行","新C行","旧ΣR(C)","新ΣR(C)","code_free行","code_free DA"],ct)
s+="""

每对象*-C-domain/index.json登记输入及输出SHA、生成命令；code-lines分片逐行保存C的CU/row/地址/DIE/参考ID。移出行的逐行与文件汇总分别在code-free-lines、code-free-files分片。四对象断言旧ΣR(C)−新ΣR(C)=code_free DA全部通过。
原始大行表在temp/prep-ruling3-4/*-C-dwarf.jsonl，精确路径和SHA见*-C-dwarf-command.json。

### 10.3 实例清单、声明路径与完整上下文键

实例范围严格为原有有地址区间DIE：spike各17，FFmpeg Thumb28149、A3228190；普通候选分别15/15/26841/26876。无代码定义仅作为abstract_origin来源，没有加入组判定。

逐属性的声明查找路径在*-rev1-identity/declaration-paths分片（目录名保留，内容为最终修订2）。每个inline实例的decl_file、decl_line均经abstract_origin：spike各8、FFmpeg23519/23557；查找与公开API结果断言一致。源码及SHA见declaration-source.txt：DWARFDie.cpp:340–370、557–568。

修订1初算将“后代有非零叶子行”等同“产生键”；额外交叉核对发现Thumb47/A3252个实例全部因非叶子line0无键，已暂停并取得修订2，未自行放宽。暂停证据保留在descendant-key-crosscheck.json及*-nonleaf-zero-key-cases.json；初算表保留temp/prep-ruling3-4/revision1-provisional，comparison-PROVISIONAL.json明确不是最终表。

最终无键判定直接使用正式ProfiledBinary.cpp构造调用栈键的原文代码块，包含叶子/非叶子line0拒绝与非法名字截断；没有另写近似规则。独立helper仅设置IPMode=true、UseCanonicalFnName=false、UseProbeDiscriminator=false，与这批DWARF IP构建一致。逐字节摘取区间、SHA、完整块与编译命令见rev2-key-tool-build.json、formal-key-block.txt。枚举全部原清单顶层函数，不把未选择的函数当作“没找到键”；all-key-proofs保存每个DIE的指令覆盖数和被接受键数。原映射内358/359/413090/401052条指令的接受状态和栈深与正式代码结果逐条一致，差异0。

无键豁免仍同时要求：定义身份通过；自身声明文件非零叶子行与直接子调用行均不越界；不存在其他文件非零叶子行。任一不满足仍失败。

#### a–e分类与判定

下表按原完整普通候选清单统计，DA是每类别涉及参考行的并集，组可跨类，类别DA不可直接相加。不存在的类别/结果显式0见各对象*-rev2-proof/a-e-verdicts；自身正常非零叶子行的普通实例另列，未强塞进a–e。

"""
s+=table(["对象","类别","结果","实例","组","参考DA"],ae)
s+="""

用户指出的e子集独立核对如下（不是用FNDA或DA筛选豁免）：

"""
s+=table(["对象","e实例","组","参考DA","判定"],et)
s+="""

每个e实例所有静态地址的完整上下文、被拒绝frame、其来源子DIE及原始DW_AT_call_line（含属性是否存在）、豁免证据与结果在*-rev2-proof/e-addresses、e-instances分片。至少三例可直接按DIE定位：
Thumb 0x39b3e/0x3aea1（put_bits），0x193419（get_bits_long）；A32 0x3ca92/0x3d720（put_bits），0x16c808（decode_cabac_residual_nondc）。其中0xf0582的get_bits叶子行340、get_bits_long调用行0，最终按修订2豁免。
一次取证脚本断言发现lexical block下的inline DIE未被父函数“直接子列表”收录；新增直接读取每个inline DIE原始call属性的helper补齐来源，未改变身份/键规则。失败原文在ffmpeg-thumb-rev2-proof-run，修复后两侧proof-v2-run退出0。

纯空叶子原因组仍是Thumb69、A3277；另有同时含空集合与越界的19/18组，分列。每类原始行、DIE区间、直接子调用及至多三个完整实例见*-audit/pure-empty-example分片；真实d类若为0如实记0，失败语义由synthetic夹具覆盖。

### 10.4 指定真实例与cabac逐行对照

逐DIE完整检查见*-rev1-identity/example-*；以下保留指定函数的精确链接名，包含同源多个.__uniq.实例时逐组列出：

"""
s+=table(["对象","链接名","实例","旧原因","新结论","新原因","新实例状态"],real)
s+="""

arm/cabac.h第36–105行共70行的C原始行表、C域成员、S键和地址见*-audit/cabac-36-105分片。两侧在此区间有C行表记录/有S键的行均为36、104；其余行逐行列出否，不用S结果替代C证据。

### 10.5 四对象旧/新登记表

“可登记”仅指本表门槛；裁决3/4仍须折入v1.6并经三家评审，本轮不实际登记。①②③③′按各自原定义；引用C的使用新C。④body比例不计算。

"""
s+=table(["对象","规则","U行","ΣR(U)","①","②","③","③′","n_eff","K","表内状态"],mt)
s+="""

n_eff为null有显式分支，未作数值比较；本数据均非null。spike K=19/10<50，仍为仅描述。FFmpeg K=457/455。权重/U/排除分片及SHA见各*-static/index.json。③均≥80%；没有对象触发<50%停止门槛。完整旧/新字段在comparison-final.json；③′宏展开DA占比沿用旧参考导出统计（C筛选不改变该分母）。

三个1%门槛：

"""
s+=table(["对象","原因","分子DA","分母ΣR(C)","比例","超过1%"],gt)
s+="""

新歧义包见*-audit/ambiguity-groups、ambiguity-top20、ambiguity-top20-instances。按失败原因与partial/all统计，不按DA修复身份；每对象即使没有歧义也输出空表及0汇总。

### 10.6 互斥损失账本与S键在C外

新C到U的完整原因集合：

"""
s+=table(["对象","完整原因集合","行数","DA"],lt)
s+="""

每对象均断言ΣR(C)−ΣR(U)−Σ桶DA=0；同时另有“旧C到新U”账本，增加code_free_line并保留每行其他原因，差值也为0。移出C的code_free_line不进入新C分母或1%门槛。账本在summary.json、old-C-exclusions、exclusions；不是将互相重叠的单原因DA相加。

S有键却不在新C的行全部排除，逐行保存在S-key-outside-C分片：

"""
s+=table(["对象","C外S键行","有参考的DA合计","无覆盖DA行","原在旧C行","原在旧C的DA"],st)
s+="""

没有覆盖参考的行DA写空值，不用0伪造；其中“原在旧C”子集直接证明U⊆新C筛选没有偷用S键反向扩张C。静态系统头/宏代码规模沿用全指令枚举统计，按新身份重核，见summary的static_special_code。

### 10.7 验收、资源、SHA与停止

原113项全部保留；本轮21项synthetic夹具，共134项通过（tests-rev2，真实退出0）。包括用户要求的9项、修订1其他文件叶子行、修订2非叶子0豁免/越界失败，以及混合文件叶子行不豁免等补充负例。

"""
s+=f"全部scope串行nice19/ionice-c3，MemoryMax=3G、CPUQuota=200%，启动门槛MemAvailable≥4GiB。最低MemAvailable={resource['minimum_MemAvailable_bytes']}B，最高实读cgroup memory.peak={resource['maximum_cgroup_memory_peak_bytes']}B；资源终止={resource['resource_terminated']}。一次取证来源断言失败原文保留并已修复，不是OOM。资源原文与每次带时间结束状态、生成命令见各*-run及resources-summary.json。\n"
s+="""
所有新增文件<1MB；manifest登记SHA及路径，大原始取证数据在temp并由命令记录登记SHA。旧v1.5正文、旧代码/证据、用户配置未改，无板上操作、无挂载、无认证变更、无正式sample profile读取，边界例外：无。

本任务到此停止。不登记修正案3，不进入仿真或其他N.5项目。待折入v1.6并经评审后再由用户决定后续。
"""
assert "## 10. 裁决3" not in root.read_text()
root.write_text(root.read_text()+s)
status=Path("docs/STATUS.md");text=status.read_text()
update="""
## 裁决3、裁决4修订1/2已完成（2026-11-11；按要求停止）

- [05报告§10](profgen/eval/prep/05_identity_gate_and_coverage.md)：C行域只用C构建行表；实例清单未扩大，所有inline声明来源经abstract_origin。修订2使用正式工具原文键代码；Thumb47/A3252个指定e实例全部通过三项豁免条件，逐地址证据保留。
- 新C行数：spike Thumb75/A3274，FFmpeg Thumb7504/A327523。新③分别99.991434%、99.991339%、85.108247%、84.896746%；三个1%门槛均未超限，四对象本表门槛可登记，但须待裁决折入v1.6并经三家评审，不代表实际允许登记。
- FFmpeg identity_ambiguous分子两侧15555，unmatched_in_elf分子26367，boundary_unavailable为0；分母分别6789285726/6780632541。旧/新表与所有损失、S键域外明细及SHA均保留；两套损失账本各四个差值为0。
- 原113+新增21=134项测试通过。旧实例/结果未覆盖；修订1停止发现及初算草稿保留，最终结果以comparison-final.json为准。
- 修正案3未登记；④body比例与正式sample profile受控量未计算；未碰板子。完成后停止，不进入仿真或其他N.5。
"""
status.write_text(text.replace("## 静态身份门禁与U完成",update+"\n## 静态身份门禁与U完成",1))
print("report written",len(s.encode()),"resources",resource)
