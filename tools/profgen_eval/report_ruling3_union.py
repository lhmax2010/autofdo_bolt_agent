"""Generate the static-only comparison report from saved evidence."""
import collections,json
from pathlib import Path
from ruling3_union import OUT,OLD,dump
from run_scoped import WORK,sha
from apply_header_ruling import rows
OBJECTS=("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32")
def main():
    comp={o:json.loads((OUT/(o+"-static/comparison.json")).read_text()) for o in OBJECTS}
    cls={o:json.loads((OUT/(o+"-code-free-classification/summary.json")).read_text()) for o in OBJECTS}
    resources=[]
    for p in sorted(OUT.rglob("resources.json")):
        r=json.loads(p.read_text());r["path"]=str(p);resources.append(r)
    rs=dict(min_memavailable=min(r["min_memavailable"] for r in resources),
       peak_memory=max(r["memory_peak_bytes"] for r in resources),resource_terminated=any(r["resource_terminated"] for r in resources),
       scopes=resources)
    dump(OUT/"resources-summary.json",rs)
    provenance=[]
    for mode in ("thumb","a32"):
        p=WORK/"docs/profgen/eval/prep/evidence/ruling2"/(mode+"-config-components.json")
        d=json.loads(p.read_text())
        assert sha(Path(d["components_path"]))==d["sha256"]
        assert sha(Path(d["actual_build_mak"]))==d["mak_sha256"]
        ps=[Path(d["components_path"]),Path(d["actual_build_mak"]),
            WORK/"temp/eval-prep11/build"/("ffmpeg-"+mode+"-C")/"config.h",
            WORK/"temp/prep-ruling2"/("headers4-"+mode)/"usr/include/libavutil/avconfig.h"]
        provenance.append(dict(mode=mode,prior_compiler_config_proof=str(p),proof_sha256=sha(p),checks=len(d["checks"]),
            files=[dict(path=str(q),sha256=sha(q)) for q in ps]))
    dump(OUT/"AST-config-provenance.json",provenance)
    md=["\n## 11. 裁决3修订1：两构建行表并集与 code_free 描述（2026-11-11）\n",
        "本节基于 cb2da1b；裁决原文已登记到 rulings.md，仍待折入 v1.6 并经三家评审。未读取正式 sample profile（含 CALIBRATION），未登记修正案3，未接板、未进入仿真或其他 N.5。\n",
        "### 11.1 数据流、实现与可复核范围\n",
        "三套表固定裁决4修订2的身份与键事实，只改变C域。“旧规则”在本节指v1.5原C域＋裁决4修订2，并非§10历史旧身份表；因此FFmpeg旧C的U与§10历史行不同，这是有意控制身份变量。C-only表的C/U/质量比、n_eff、K、损失桶、三个门槛均与cb2da1b逐字段相等（断言）。\n",
        "ruling3_union.py只读覆盖参考、独立C/S DWARF行表与既有映射范围的顶层函数名清单。S证据要求非end_sequence、已解析文件、非零行号、地址属于选定函数区间（原始DIE链）；使用行表叶子文件/行，不读地址→键映射表或身份结论，不要求完整上下文接受。每个C成员保存C/S见证；域先独立封存，ruling3_union_static.py随后才复用cb2已验收的裁决4修订2静态键数据库和逐行原因。数据库只读，路径/SHA入索引，未打开任何RUN数据。\n",
        "每个对象的domain/index.json保留输入SHA、实际生成命令、选择范围SHA与行表原文位置；static/{v15,ruling3,ruling3-rev1}/index.json登记U、排除、权重及摘要SHA。证据根目录：[ruling3-rev1](evidence/identity-gate/ruling3-rev1/)。旧代码/旧结果均未覆盖。\n",
        "code_free_ast.py仅构建独立插件，使用GBS Clang公开API；clang本体不改不重编。用实际C构建命令保留优化、覆盖、预处理参数，仅去掉对象/依赖输出并加-fsyntax-only、插件参数。按已验证方法重定位源目录、sysroot与生成头；AST-config-provenance.json记录实际config.h/config.mak、avconfig.h及2270项config_components对应证据与SHA。spike每侧1个CU、FFmpeg每侧311个CU全部退出0，complete.errors=false。原始大JSONL仅在temp/prep-ruling3-rev1/*-AST，每条命令单独记录源SHA、原日志行、完整命令、原始输出SHA。\n",
        "分类只按编译器SourceManager的spelling/expansion源码范围：先GCCAsmStmt，再含其他新C行的跨行Stmt/Expr，再other；无成功AST为ast_unavailable。范围冲突取最短范围，再按类型/TU排序，确定性输出。依条文字面，CompoundStmt也是Stmt，没有自行排除；故stmt_continuation不能一概解释为“实参续行”，下面单列CompoundStmt规模。无法形成同文件范围的跨文件端点不拼接、不猜测；它们的原始AST仍留存。\n",
        "### 11.2 三套对象表\n",
        "表内“可登记”只表示本表门槛通过，不代表裁决已评审或其余登记条件已完成。④body比例仍未计算。①②③③′的分子分母定义保持原实现；n_eff=null有显式分支，本数据无null；spike K<50仍仅描述。\n"]
    def table(headers,records):
        md.append("\n|"+"|".join(headers)+"|\n|"+"|".join("---" for _ in headers)+"|\n")
        for r in records:md.append("|"+"|".join(str(x).replace("|","/").replace("\n"," ") for x in r)+"|\n")
        md.append("\n")
    names={"v15":"旧C（身份固定）","ruling3":"裁决3原文","ruling3-rev1":"裁决3修订1"}
    pct=lambda v:"null" if v is None else f"{v*100:.6f}%"
    table(["对象","C规则","C行","ΣR(C)","U行","ΣR(U)","①","②","③","③′","n_eff","K","状态"],
      ([o,names[n],s["C_lines"],s["R_C"],s["U_lines"],s["R_U"],*[pct(s[k]) for k in ("coverage_1","coverage_2","coverage_3","coverage_3_prime")],
        f'{s["n_eff"]:.6f}' if s["n_eff"] is not None else "null",s["K"],s["registration_status"]+("："+",".join(s["registration_reasons"]) if s["registration_reasons"] else "")]
       for o in OBJECTS for n,s in comp[o].items()))
    md.append("三个1%门槛，分子/分母原值（同对象分母随C规则变化）：\n")
    table(["对象","C规则","原因","分子DA","分母ΣR(C)","比例","超1%"],
      ([o,names[n],reason,g["DA"],g["denominator"],pct(g["ratio"]),g["exceeds_one_percent"]]
       for o in OBJECTS for n,s in comp[o].items() for reason,g in s["gates"].items()))
    md.append("### 11.3 代码承载比例、S新增行与域外键\n")
    table(["对象","新ΣR(C)","原ΣR(C)","代码承载比例","因(b)新增行/DA","进入U行/DA","仍损失行/DA"],
      ([o,comp[o]["ruling3-rev1"]["R_C"],comp[o]["v15"]["R_C"],pct(comp[o]["ruling3-rev1"]["code_bearing_ratio"]["ratio"]),
        f'{a["lines"]}/{a["DA"]}',f'{a["U_lines"]}/{a["U_DA"]}',f'{a["loss_lines"]}/{a["loss_DA"]}']
       for o in OBJECTS for a in [comp[o]["ruling3-rev1"]["added_by_S"]]))
    md.append("新增行逐行见*-static/added-by-S-*.csv，保留in_U与完整loss_reasons。Thumb两行、A32三行仍为损失，DA均8366453，不能因S行表存在便记入U：\n")
    table(["对象","文件","行","DA","原因"],
      ([o,r["file"].split("/ffmpeg-8.0.1/")[-1],r["line"],r["DA"],r["loss_reasons"]]
       for o in OBJECTS for r in rows(OUT/(o+"-static"),"added-by-S-*.csv") if r["in_U"]=="False"))
    table(["对象","所有S键域外行","已知DA","原C内域外行","原C内域外DA","无参考DA行"],
      ([o,s["lines"],s["known_DA"],s["originally_in_C_lines"],s["originally_in_C_DA"],s["unavailable_DA_lines"]]
       for o in OBJECTS for s in [comp[o]["ruling3-rev1"]["S_keys_outside_C"]]))
    md.append("修订针对的“满足原C条件但被行表筛走”子集四侧均DA=0，已断言。若字面统计全部S键，FFmpeg两侧仍各有10 DA在原C之外：bytestream.h:94=1、96=1、99=8。逐行参考owner查询均为空（无任何参考函数主文件行范围覆盖），不是因两边行表缺失被筛走；不符合v1.5原C条件，不能为使总量为0而扩大C。全量逐行明细及原因见S-keys-outside-C分片；无覆盖DA的行写空值，不伪造0。\n")
    md.append("### 11.4 code_free结构描述（不用于门槛）\n")
    table(["对象","类别","行数","DA","占原ΣR(C)"],
       ([o,c,v["lines"],v["DA"],pct(v["fraction_of_original_R_C"])] for o in OBJECTS for c,v in cls[o]["categories"].items()))
    md.append("所有code_free行逐行归入且只归入一个类别；分类行数/DA之和等于原C减并集C，断言通过。CompoundStmt见证的stmt_continuation规模：\n")
    table(["对象","行数","DA"],
      ([o,v["lines"],v["DA"]] for o in OBJECTS for v in cls[o]["by_kind"] if v["category"]=="stmt_continuation" and v["kind"]=="CompoundStmt"))
    md.append("各类DA最高10行（不足10行全列；0行类别无条目）。完整raw AST行号/命令/SHA在*-code-free-classification/summary.json与lines分片中；下面为可读摘要。\n")
    for o in OBJECTS:
        md.append("**"+o+"**\n\n")
        table(["类别","文件","行","DA","Stmt类型","范围","view"],
          ([c,r["file"].split("/BUILD/")[-1],r["line"],r["DA"],
            r["witness"]["kind"] if r["witness"] else "无",
            f'{r["witness"]["begin_line"]}–{r["witness"]["end_line"]}' if r["witness"] else "无",
            r["witness"]["view"] if r["witness"] else "无"]
           for c,rs0 in cls[o]["top10"].items() for r in rs0))
    md.append("### 11.5 完整互斥损失账本\n")
    md.append("下表为三套C→U完整原因集合。另一个原C→该套U账本在每套summary.old_C_to_new_U_loss及old-C-exclusions分片中：被移出域的行增加code_free_line并保留其余完整原因，不重复计数。共12个C→U与12个原C→U差值均断言为0。\n")
    table(["对象","C规则","完整原因集合","行数","DA"],
      ([o,names[n]," + ".join(b["reasons"]),b["lines"],b["DA"]] for o in OBJECTS for n,s in comp[o].items() for b in s["loss_buckets"]))
    md.append("新并集C的原C→新U账本（包括code_free）：\n")
    table(["对象","完整原因集合","行数","DA"],
      ([o," + ".join(b["reasons"]),b["lines"],b["DA"]] for o in OBJECTS for b in comp[o]["ruling3-rev1"]["old_C_to_new_U_loss"]["buckets"]))
    md.append("### 11.6 测试、失败记录、资源与停止\n")
    md.append("原134项测试文件未修改、全部保留；新增10项synthetic，共144项通过。前7项逐项覆盖用户要求；另加AST不可得不归other、macro-only原域外不准入、范围内没有其他C行不归continuation。真实AST624条编译命令均成功；C-only重现及所有账本/域外DA断言通过。\n")
    md.append("保留3次开发失败：AST-plugin-build-run的显式JSON构造编译错误；spike-thumb-AST-run在插件未成功时缺少so；spike-thumb-AST-v2-run把collect当对象名的CLI错误。修正后独立插件构建成功、调用前检查so存在，真实取证均通过。它们不是OOM，未采纳失败输出。\n")
    md.append(f'串行nice19/ionice-c3、systemd scope MemoryMax=3G/CPUQuota=200%；每次分析启动前检查≥4GiB。最低实测MemAvailable={rs["min_memavailable"]}B；最高实读cgroup memory.peak={rs["peak_memory"]}B；资源终止={rs["resource_terminated"]}。原始meminfo、scope、真实退出码、ALL-END和resources-summary.json保留。未提高限额、未并行运行分析。系统scope自身记账属系统服务行为；未观察到项目在WORKDIR外产生文件。\n')
    md.append("四对象新表③均≥80%，三个1%门槛均未超限；仅本表门槛可登记。裁决待折入v1.6并经三家评审。按要求完成后停止：不登记修正案3，不进入仿真/其他N.5，不计算④body比例或任何正式sample profile受控量。\n")
    report=WORK/"docs/profgen/eval/prep/05_identity_gate_and_coverage.md"
    text=report.read_text().split("\n## 11.",1)[0]
    body="".join(md)
    body=body.replace("\n### ","\n\n### ")
    body="\n".join(line+"\n" if line.startswith("### ") else line for line in body.split("\n"))
    report.write_text(text+body)
    status=WORK/"docs/STATUS.md";text=status.read_text()
    marker="## 裁决3、裁决4修订1/2已完成"
    addition="""## 裁决3修订1已完成（2026-11-11；按要求停止）

- [05报告§11](profgen/eval/prep/05_identity_gate_and_coverage.md)：三套C规则并列、裁决4修订2固定。C域只取C/S合格行表并集，封存后才读取静态键/身份事实；旧结果不覆盖。新表spike Thumb/A32的③为99.991434%/99.991339%，FFmpeg Thumb/A32为85.204920%/85.013804%。
- FFmpeg两侧各恢复133行，DA分别100910671/108791562；进入U分别131/130行，余下损失DA均8366453。原C范围内S有键却在新C外的DA为0；全S键仍各有bytestream.h三行DA=10在v1.5原C外，逐行保留原因，不扩域。
- 三个1%门槛均未超限，新表四对象仅本表门槛可登记，仍待裁决折入v1.6并经三家评审。代码承载比例与code_free的AST类别、每类top10、两套互斥账本见[证据](profgen/eval/prep/evidence/identity-gate/ruling3-rev1/)。CompoundStmt按字面属于Stmt，描述分类单列其规模，不用于门槛。
- 原134＋新增10=144项测试通过；624条C编译命令AST取证成功。12个C→U和12个原C→U账本差值均为0。资源与开发失败原文留存；未OOM/未资源终止。
- 修正案3未登记；未读取正式sample profile/CALIBRATION，④body比例与正式受控量未计算。已停止，不接板、不进入仿真或其他N.5。

"""
    start="## 裁决3修订1已完成"
    if start in text:
        a,tail=text.split(start,1);text=a+marker+tail.split(marker,1)[1]
    assert marker in text;status.write_text(text.replace(marker,addition+marker,1))
    print(json.dumps({k:rs[k] for k in ("min_memavailable","peak_memory","resource_terminated")}))
if __name__=="__main__":main()
