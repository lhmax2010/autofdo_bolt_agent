"""Pure descriptive rules. No changes to C/U, weights or identity rules."""
CATEGORIES=("asm_interior","structural_line","expr_continuation","own_stmt_no_code","other","ast_unavailable")
CONTROL={"IfStmt","ForStmt","WhileStmt","SwitchStmt","DoStmt","CXXForRangeStmt"}
STRUCTURAL={"l_brace","r_brace","semi","else","do"}
def structural(tokens,labels):
    covered=set()
    for label in labels:
        for i,t in enumerate(tokens):
            if label["begin_offset"]<=t["offset"] and t["end_offset"]<=label["end_offset"]:
                covered.add(i)
    if any(t["kind"] not in STRUCTURAL and i not in covered for i,t in enumerate(tokens)):return None
    kinds=sorted({t["kind"] for i,t in enumerate(tokens) if i not in covered})
    if covered:kinds.append("label")
    return "+".join(kinds) if kinds else "blank_or_comment_only"
def classify(line,newc,nodes,tokens,labels,available=True):
    if not available or tokens is None:return dict(category="ast_unavailable",reason="missing_AST_or_raw_lex",witness=None)
    nodes=[n for n in nodes if n["begin_line"]<=line<=n["end_line"]]
    inner=lambda n:(n["end_offset"]-n["begin_offset"],-n["begin_offset"],n["kind"],n.get("tu",""))
    asm=[n for n in nodes if n["kind"]=="GCCAsmStmt"]
    if asm:return dict(category="asm_interior",reason="GCCAsmStmt_range_no_code_line",witness=min(asm,key=inner))
    st=structural(tokens,labels)
    if st is not None:return dict(category="structural_line",reason=st,witness=None)
    starts=[n for n in nodes if n["kind"]!="CompoundStmt" and n["begin_line"]==line]
    if not starts:
        cont=[n for n in nodes if n["kind"] not in CONTROL|{"CompoundStmt"} and n["begin_line"]<line and n["begin_line"] in newc]
        if cont:
            w=min(cont,key=inner)
            if w["kind"]=="FunctionDecl":
                return dict(category="other",reason="only_FunctionDecl_range_declarator_vs_body_eligibility_unavailable",witness=w)
            return dict(category="expr_continuation",reason="no_node_starts_here_inner_eligible_range",witness=w)
    if starts:
        def outer(n):
            return (n["begin_offset"],-n["end_offset"],n.get("depth",0),n["kind"],n.get("tu",""))
        w=min(starts,key=outer)
        kind=w.get("semantic_kind",w["kind"])
        return dict(category="own_stmt_no_code",reason="non_compound_node_starts_here",witness=w,statement_kind=kind,
                    start_kinds=sorted({n["kind"] for n in starts}))
    return dict(category="other",reason="no_node_start_and_no_eligible_range_starting_in_C",witness=min(nodes,key=inner) if nodes else None)
