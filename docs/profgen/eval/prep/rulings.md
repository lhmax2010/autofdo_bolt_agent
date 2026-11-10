# 登记前准备人工裁决

## 裁决 1：system_header_no_reference

- 背景：被采样 ELF 中有来自系统头的函数（例如 /usr/include/bits/string_fortified.h 的 memcpy），CU 的 producer 为评估所用的 clang 22.1.8，有代码与 DWARF，但 C 覆盖参考没有候选。原因是 clang 生成覆盖映射时默认跳过系统头，参考侧不存在这些行的计数；这与"未插桩"不同，属于评价域外，处理方式同宏展开区域。
- 新增对应表结论状态 system_header_no_reference，须同时满足以下正面证据，任一缺失仍保留为没有结论：
  ① 该函数的规范化 decl_file 位于该 CU 编译时的系统头目录之下。系统头目录取自 C 构建与 S 构建的实际编译命令（-isystem、--sysroot 与该 clang 的默认系统头目录，用同一 clang 的 -v 输出核对），两侧须一致。
  ② C 构建的编译命令没有打开系统头覆盖（没有 -mllvm -system-headers-coverage 或等价选项），并在 LLVM 22.1.8 源码中给出跳过系统头的代码位置（clang/lib/CodeGen/CoverageMappingGen.cpp 中 SystemHeadersCoverage 相关判断，写出文件与行号）。
  ③ 覆盖导出的文件表中没有位于这些系统头目录之下的文件（全局核对，一旦出现则本规则不适用，停止并报告）。
  ④ 该函数没有任何参考候选（有候选的一律走原来的对应规则）。
- 处理语义：键照常进入映射表，值记为 system_header_no_reference；条目计入"已对齐但不在 U 内"，单列原因"系统头"，不算未对齐，不进入 U，也不进入 ③ 的分母 C。顶层组的内联树中只含 system_header_no_reference、not_instrumented 与参考侧未执行函数时，归为 known_out_of_scope；内联树中含已执行参考函数的组仍在映射范围内。
- 局限：内联进用户函数的系统头代码不参与行级指标，登记文本写明。
- 本裁决在 N.5 全部完成后与其他发现一起合入设计文档的登记版；在此之前以本文件为准。
