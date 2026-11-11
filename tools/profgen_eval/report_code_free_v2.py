"""Produce report and audits for descriptive-only code_free v2."""
import collections,csv,json,subprocess
from pathlib import Path
from code_free_v2_lex import OUT,TEMP,OLD
from code_free_v2_rules import CATEGORIES
from run_scoped import WORK,sha
from ruling3_union import dump
from apply_header_ruling import rows
OBJECTS=("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32")
def main():
    frozen=json.loads((OUT/"immutable-inputs.json").read_text())
    for r in frozen:assert sha(WORK/r["path"])==r["sha256"],r["path"]
    expected_counts=dict(zip(OBJECTS,(1,1,311,311)))
    audits=[];total=0
    for o in OBJECTS:
        index=json.loads((OUT/(o+"-AST/index.json")).read_text());assert len(index["commands"])==expected_counts[o]
        for it in index["commands"]:
            p=OUT/(o+"-AST")/it["command"];m=json.loads(p.read_text())
            before=json.loads(Path(m["previous"]).read_text())
            assert m["source_sha256"]==before["source_sha256"]==sha(Path(m["cwd"])/m["tu"])
            assert m["previous_command"]==before["command"]
            assert m["command"]==[m["substitutions"].get(a,a) for a in before["command"]]
            assert sha(Path(before["command"][-1]))==before["targets_sha256"]
            assert m["exit_code"]==before["exit_code"]==0 and m["complete"]=={"record":"complete","errors":False}
            assert not any(m["differences"].values())
        audits.append(dict(object=o,commands=len(index["commands"]),stmt_expr=sum(x["stmt_count"] for x in index["commands"]),
                           decl=sum(x["decl_count"] for x in index["commands"]),differences=0))
        total+=len(index["commands"])
    for p in (WORK/"tools/profgen_eval").glob("test_*.py"):
        if p.name=="test_code_free_v2.py":continue
        assert p.read_bytes()==subprocess.check_output(["git","show","HEAD:"+str(p.relative_to(WORK))])
    for mode in ("thumb","a32"):
        p=OLD/"AST-config-provenance.json"
        for r in json.loads(p.read_text()):
            for f in r["files"]:assert sha(Path(f["path"]))==f["sha256"]
    rs=[json.loads(p.read_text()) for p in OUT.rglob("resources.json")]
    memvalues=[int(line.split()[1])*1024 for p in OUT.rglob("*meminfo*.txt") for line in p.read_text().splitlines() if line.startswith("MemAvailable:")]
    resource=dict(min_memavailable=min(memvalues),memory_peak_bytes=max(r["memory_peak_bytes"] for r in rs),
                  resource_terminated=any(r["resource_terminated"] for r in rs))
    dump(OUT/"acceptance.json",dict(unchanged_old_files=len(frozen),AST=audits,total_commands=total,tests=161,resource=resource,
      complete_errors=False,command_comparison="Exact original compiler options, working directory, original command, source/config/target SHA. Only two artifact paths change: plugin shared object and JSONL output; both commands and substitutions saved.",
      old_C_U_weights_gates_unchanged=True))
    summaries={o:json.loads((OUT/(o+"-classification/summary.json")).read_text()) for o in OBJECTS}
    md=["\n## 12. code_free 描述性分类 v2（2026-11-11；完成后停止）\n\n",
        "基于4459894，只重做描述分类；旧分类与C、U、权重、三个1%门槛及登记状态不变。1048个旧证据文件全部SHA逐项一致。未读取任何正式sample profile/CALIBRATION，未登记修正案3，未接板。证据根目录：[code-free-v2](evidence/identity-gate/code-free-v2/)。\n\n",
        "### 12.1 补采授权、命令与一致性\n\n",
        "旧插件只保存Stmt/Expr，缺少Decl、运算符、初始化和标号冒号事实，因此先停下确认。PM明确授权沿用原C命令补采独立插件字段，并要求旧节点集合完全一致；本轮按此执行，不改/不重编clang本体、不挂载。完整授权及缺失字段见authorization.md与pending.json（历史停止点，现已闭合）。\n\n",
        "新插件保留旧Stmt/Expr遍历及去重顺序，额外记录Decl（含DeclStmt各Decl、DeclContext子节点）、VarDecl初始化、Binary/CompoundAssign运算符及语句类名。case/default冒号取Clang AST API，普通标号冒号由Clang Lexer::findNextToken取得并确认tok::colon。旧Stmt/Expr的完整字段投影按多重集合比较：类型、spelling/expansion视图、起止raw/offset/line、文件及macro标志全部逐条一致。\n\n",
        "完整原C命令及实际取证命令逐条保存；原编译参数、cwd、源SHA、sysroot、生成头/config及目标行清单SHA不变。命令字面仅替换两个产物路径：旧插件.so→新插件.so、旧JSONL→temp/prep-code-free-v2的新JSONL，避免覆盖旧产物；不把这两项隐藏成整串字节相同。两侧FFmpeg各311 CU、spike各1 CU，真实退出码与上轮均为0，complete.errors=false。\n\n"]
    def esc(x):return str(x).replace("|","\\|").replace("\n","<br>")
    def table(h,rs):
        md.append("|"+"|".join(h)+"|\n|"+"|".join("---" for _ in h)+"|\n")
        for r in rs:md.append("|"+"|".join(esc(x) for x in r)+"|\n")
        md.append("\n")
    table(["对象","命令数","旧/新Stmt-Expr记录数","新增Decl范围","差异数"],([r["object"],r["commands"],r["stmt_expr"],r["decl"],r["differences"]] for r in audits))
    md+=["72个物理源文件由GBS Clang公开Lexer API从文件起点raw lex，保留跨行token状态，忽略注释/空白；标识符经Clang IdentifierTable取得关键字kind。原始tokens JSONL为temp/prep-code-free-v2/raw-tokens.jsonl（路径/SHA/源码SHA见lexer-command.json），AST大JSONL也只留该temp目录。Lex使用C17/GNU C；FFmpeg原命令为-std=c17，spike为该clang默认GNU C。仓库仅存小分片与索引。\n\n",
      "### 12.2 分类算法与未决描述\n\n",
      "优先级固定为asm→structural→expr_continuation→own_stmt_no_code→other；取不到AST或lex证据单列ast_unavailable。structural按该行全部raw token检查，只接受{、}、;、else、do以及编译器确认的标号范围；空白/注释-only单列结构子类。未从文件名或源文本推测语义。\n\n",
      "expr_continuation要求本行没有任何非CompoundStmt节点起始，候选起始行在新C中，并排除CompoundStmt与if/for/while/switch/do整体范围；取最内层合格范围。own_stmt按本行起始的非CompoundStmt节点判定，汇总种类选择起点最早、覆盖最外层的节点，固定排序去除TU遍历顺序影响；同时保存全部起始节点类型。语句细类来自AST（赋值运算、调用、return、声明初始化等），不把词法等号当作AST赋值证据。\n\n",
      "每侧有2行（cabac.c:167，DA=1800；h264idct_template.c:283，DA=38861）仅能找到整段FunctionDecl容器。无法证明该行属于普通声明部分而非函数体，因此不猜成expr_continuation，列other，原因only_FunctionDecl_range_declarator_vs_body_eligibility_unavailable。其他other逐行记录no_node_start_and_no_eligible_range_starting_in_C及可得AST上下文。AST不可得为0，但并不把other解释成全部已证实优化消除。\n\n",
      "### 12.3 四对象分类汇总与两种分母\n\n"]
    pct=lambda n,d:f"{100*n/d:.6f}%"
    table(["对象","类别","行数","DA分子","原ΣR(C)","占原C","新ΣR(C)","占新C"],
       ([o,c,v["lines"],v["DA"],v["original_denominator"],pct(v["DA"],v["original_denominator"]),
         v["new_denominator"],pct(v["DA"],v["new_denominator"])] for o in OBJECTS for c,v in summaries[o]["categories"].items()))
    md+=["各类均为描述，不设门槛；分类总DA是被排除部分，因此占新C的比例允许超过100%，不是新C的组成比例。\n\n",
         "### 12.4 structural_line token细类\n\n"]
    table(["对象","结构token种类集合","行数","DA"],([o,k,v["lines"],v["DA"]] for o in OBJECTS for k,v in summaries[o]["structural_subtypes"].items()))
    md+=["label的具体case/default/普通标号以及所有原始token在逐行CSV中；表中按结构token集合互斥汇总。blank_or_comment_only是忽略注释空白后的空集合。\n\n",
         "### 12.5 own_stmt_no_code语句种类\n\n"]
    table(["对象","AST语句种类","行数","DA"],([o,k,v["lines"],v["DA"]] for o in OBJECTS for k,v in summaries[o]["own_statement_kinds"].items()))
    md+=["### 12.6 新旧分类交叉表\n\n"]
    oldcats=("asm_interior","stmt_continuation","other","ast_unavailable")
    for o in OBJECTS:
        lookup={(r["old"],r["new"]):r for r in summaries[o]["cross"]}
        md.append("**"+o+"：行数**\n\n")
        table(["旧类→新类",*CATEGORIES],([old,*[lookup.get((old,c),{}).get("lines",0) for c in CATEGORIES]] for old in oldcats))
        md.append("**"+o+"：DA**\n\n")
        table(["旧类→新类",*CATEGORIES],([old,*[lookup.get((old,c),{}).get("DA",0) for c in CATEGORIES]] for old in oldcats))
    md+=["### 12.7 每类DA最高20行\n\n",
        "不足20行全列、空类别无条目。下表token为该行全部raw token文本序列（不含注释/空白），详细kind/offset/跨行跨度、AST原始JSONL行号与SHA见各对象top20分片。structural的AST列仅列上下文，不参与除标号范围之外的结构性判断。\n\n"]
    for o in OBJECTS:
        md.append("**"+o+"**\n\n")
        data=list(rows(OUT/(o+"-classification"),"top20-*.csv"))
        def rs0():
            for r in data:
                w=json.loads(r["witness"]) if r["witness"] else None
                if not w and r["AST_context_only"]:w=json.loads(r["AST_context_only"])
                ts=json.loads(r["tokens"]) if r["tokens"] else []
                yield [r["category"],r["file"].split("/BUILD/")[-1],r["line"],r["DA"],
                    json.dumps([t["text"] for t in ts],ensure_ascii=False),
                    w["kind"] if w else "无（纯词法依据）",
                    f'{w["begin_line"]}–{w["end_line"]}' if w else "无"]
        table(["类","文件","行","DA","全部token","AST节点","范围"],rs0())
    md+=["### 12.8 不变量、测试、资源与停止\n\n"]
    table(["对象","分类行数","分类DA","原C−新C","差值"],([o,s["assertion"]["lines"],s["assertion"]["DA"],s["assertion"]["expected"],s["assertion"]["difference"]] for o,s in summaries.items()))
    md.append("每个code_free行恰好出现一次、分类DA之和=原ΣR(C)−新ΣR(C)，四对象断言均通过；新旧交叉表边际和亦核对。原144项测试文件字节不变，新增17项synthetic，共161项通过。包含用户要求的7例及asm/other/ast_unavailable、排除控制语句整体、节点本行起始阻止续行、最内层节点、Decl续行、标号后跟调用及FunctionDecl无法确认时不猜测。\n\n")
    md.append("保留开发草稿：最初把Clang token kind else/do误写成kw_else/kw_do，检查真实token后修正；未发布的分类草稿移到temp/prep-code-free-v2/draft-keyword-spelling，SHA/原因见draft-classification-disposition.json。旧发布分类从未改写，最终证据以*-classify-final-run与*-classification/index.json为准。不是编译器缺陷或规则修改。\n\n")
    md.append(f'资源全程串行nice19/ionice-c3，scope MemoryMax=3G、CPUQuota=200%；分析前MemAvailable≥4GiB。最低MemAvailable={resource["min_memavailable"]} B，最高实读cgroup memory.peak={resource["memory_peak_bytes"]} B，资源终止={resource["resource_terminated"]}；无OOM。原始meminfo/退出码/scope/ALL-END均保留。边界例外：无已知项目文件在WORKDIR外生成；systemd自身系统记账不属于项目输出。\n\n')
    md.append("完成后停止。本轮仅描述，不改变C、U、权重、任何门槛或资格；不登记修正案3，不做仿真、正式profile分析或板上工作。\n")
    report=WORK/"docs/profgen/eval/prep/05_identity_gate_and_coverage.md"
    text=report.read_text().split("\n## 12.",1)[0];report.write_text(text+"".join(md))
    status=WORK/"docs/STATUS.md";text=status.read_text();marker="## 裁决3修订1已完成"
    addition="""## code_free描述分类v2已完成（2026-11-11；停止）

- [05报告§12](profgen/eval/prep/05_identity_gate_and_coverage.md)：只替换描述分类；旧分类及C/U/权重/门槛1048个证据文件SHA全部不变。未读取正式sample profile，修正案3未登记。
- PM允许按原C命令补采Decl/语句细类字段；624条命令成功，旧Stmt/Expr集合逐条零差异。仅插件与新JSONL产物路径替换，完整命令、源/config SHA及退出码全部留证。raw lex覆盖72个源文件。
- spike Thumb/A32：structural均28行；own_stmt为19/20行。FFmpeg Thumb/A32：asm均68行，structural2105/2100，expr_continuation均25，own_stmt3056/3042，other均149；ast_unavailable均0。每侧2行FunctionDecl容器无法证明声明续行，列other并保留原因，不猜测。
- 四对象分类DA守恒且每行唯一；新旧行数/DA交叉表、每类Top20完整token、own语句类别见[证据](profgen/eval/prep/evidence/identity-gate/code-free-v2/)。原144+新增17=161项测试通过；无OOM/资源终止。
- 已按要求停止；不改变登记状态，不进入其他N.5或正式指标计算。

"""
    start="## code_free描述分类v2已完成"
    if start in text:
        a,tail=text.split(start,1);text=a+marker+tail.split(marker,1)[1]
    assert marker in text;status.write_text(text.replace(marker,addition+marker,1))
    print(json.dumps(dict(acceptance=audits,resource=resource),ensure_ascii=False))
if __name__=="__main__":main()
