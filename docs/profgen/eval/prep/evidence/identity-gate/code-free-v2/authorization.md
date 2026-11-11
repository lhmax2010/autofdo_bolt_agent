# code_free v2 补采裁决（用户原文）

裁决：同意补采，按以下条件执行。

1. 范围：沿用上一轮 code_free_ast 的原 C 编译命令（同样的源目录重定位、sysroot、生成头与 config 证据），只扩展独立插件的输出字段，新增：
   - Decl 节点（VarDecl、FunctionDecl、FieldDecl、TypedefDecl、LabelDecl 等，包括 DeclStmt 中的各 Decl）的源码范围与类型，以及 VarDecl 是否带初始化；
   - Stmt/Expr 的细分种类（具体类名；BinaryOperator/CompoundAssignOperator 的运算符种类；CallExpr、ReturnStmt 等）；
   - 判定 own_stmt_no_code 和 expr_continuation 所需的节点起始行信息。
   不修改、不重编 clang 本体，不执行挂载。

2. 一致性核对（必须通过，否则停止报告）：
   - 新采集中的 Stmt/Expr 节点集合（类型、spelling/expansion 起止位置）与上一轮保存的结果逐条比对，必须完全一致；差异逐条列出并停止，不得只用新结果覆盖。
   - 每条命令的源文件 SHA、完整命令、退出码与上一轮对应命令一致；FFmpeg 每侧 311 个 CU、spike 每侧 1 个 CU 全部成功，complete.errors=false。

3. 原始大 JSONL 放 temp/prep-code-free-v2/，登记路径与 SHA；仓库内只放小于 1MB 的分片与索引。

4. 其余按 code_free 分类重做任务的原文执行：分类规则、报告、测试、停止条件和约束都不变。对新规则仍无法判定的行，单列 ast_unavailable 或 other 并写明原因，不得猜测归类。
