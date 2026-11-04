; Hand-written semantic matcher fixture, not an optimization result.
define i32 @f(i64 %x, i32 %y, ptr %p) !dbg !0 {
entry:
  switch i64 %x, label %yes [ i64 1, label %no ], !dbg !2, !prof !5
yes:
  ret i32 1, !dbg !3
no:
  ret i32 2, !dbg !4
}
declare i32 @g(i32)
!0 = distinct !DISubprogram(name: "f", scope: !1, file: !1, line: 1, type: !9, scopeLine: 1, spFlags: DISPFlagDefinition, unit: !7)
!1 = !DIFile(filename: "fixture.c", directory: "/fixture")
!2 = !DILocation(line: 2, column: 3, scope: !0)
!3 = !DILocation(line: 3, column: 5, scope: !0)
!4 = !DILocation(line: 4, column: 5, scope: !0)
!5 = !{!"branch_weights", i32 80, i32 20}
!llvm.dbg.cu = !{!7}
!llvm.module.flags = !{!13}
!7 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "hand-written fixture", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug)
!9 = !DISubroutineType(types: !10)
!10 = !{!11, !11, !11, !12}
!11 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!12 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: null, size: 64)
!13 = !{i32 2, !"Debug Info Version", i32 3}
