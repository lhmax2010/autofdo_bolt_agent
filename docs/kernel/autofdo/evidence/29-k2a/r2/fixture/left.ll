; ModuleID = 'layout.c'
source_filename = "layout.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@sink = dso_local global i32 0, align 4

; Function Attrs: nofree noinline norecurse nounwind memory(readwrite, target_mem0: none, target_mem1: none) uwtable
define dso_local i32 @choose(i32 noundef %0) local_unnamed_addr #0 !dbg !47 !prof !50 {
  %2 = icmp eq i32 %0, 0, !dbg !51
  br i1 %2, label %3, label %5, !dbg !52, !prof !53

3:                                                ; preds = %1
  %4 = tail call i32 @left(i32 noundef 0), !dbg !54, !prof !55
  br label %7

5:                                                ; preds = %1
  %6 = tail call i32 @right(i32 noundef %0), !dbg !56, !prof !57
  br label %7

7:                                                ; preds = %5, %3
  %8 = phi i32 [ 5, %5 ], [ 3, %3 ]
  %9 = phi i32 [ %6, %5 ], [ %4, %3 ]
  %10 = load volatile i32, ptr @sink, align 4, !dbg !58, !tbaa !43
  %11 = mul i32 %10, %8, !dbg !58
  %12 = add i32 %11, %9, !dbg !58
  store volatile i32 %12, ptr @sink, align 4, !dbg !58, !tbaa !43
  ret i32 %9, !dbg !59
}

; Function Attrs: mustprogress nofree noinline norecurse nounwind willreturn memory(readwrite, argmem: none, target_mem0: none, target_mem1: none) uwtable
define dso_local i32 @left(i32 noundef %0) local_unnamed_addr #1 !dbg !60 !prof !61 {
  %2 = mul i32 %0, 7, !dbg !62
  %3 = load volatile i32, ptr @sink, align 4, !dbg !63, !tbaa !43
  %4 = urem i32 %3, 13, !dbg !64
  %5 = add i32 %4, %2, !dbg !65
  ret i32 %5, !dbg !66
}

; Function Attrs: mustprogress nofree noinline norecurse nounwind willreturn memory(readwrite, argmem: none, target_mem0: none, target_mem1: none) uwtable
define dso_local i32 @right(i32 noundef %0) local_unnamed_addr #1 !dbg !67 !prof !68 {
  %2 = mul i32 %0, 11, !dbg !69
  %3 = load volatile i32, ptr @sink, align 4, !dbg !70, !tbaa !43
  %4 = urem i32 %3, 19, !dbg !71
  %5 = add i32 %4, %2, !dbg !72
  ret i32 %5, !dbg !73
}

; Function Attrs: nofree norecurse nounwind memory(readwrite, target_mem0: none, target_mem1: none) uwtable
define dso_local range(i32 0, 2) i32 @main(i32 noundef %0, ptr noundef readnone captures(none) %1) local_unnamed_addr #2 !dbg !74 !prof !75 {
  %3 = icmp sgt i32 %0, 1, !dbg !76
  br label %8, !dbg !77

4:                                                ; preds = %8
  %5 = load volatile i32, ptr @sink, align 4, !dbg !79, !tbaa !43
  %6 = icmp eq i32 %5, 305419896, !dbg !80
  %7 = zext i1 %6 to i32, !dbg !81
  ret i32 %7, !dbg !82

8:                                                ; preds = %2, %8
  %9 = phi i32 [ 0, %2 ], [ %15, %8 ]
  %10 = urem i32 %9, 1000, !dbg !83
  %11 = icmp eq i32 %10, 0, !dbg !84
  %12 = xor i1 %3, %11, !dbg !85
  %13 = zext i1 %12 to i32, !dbg !86
  %14 = tail call i32 @choose(i32 noundef %13), !dbg !87, !prof !89
  %15 = add nuw nsw i32 %9, 1, !dbg !90
  %16 = icmp eq i32 %15, 100000, !dbg !92
  br i1 %16, label %4, label %8, !dbg !93, !prof !94, !llvm.loop !95
}

attributes #0 = { nofree noinline norecurse nounwind memory(readwrite, target_mem0: none, target_mem1: none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" "use-sample-profile" }
attributes #1 = { mustprogress nofree noinline norecurse nounwind willreturn memory(readwrite, argmem: none, target_mem0: none, target_mem1: none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" "use-sample-profile" }
attributes #2 = { nofree norecurse nounwind memory(readwrite, target_mem0: none, target_mem1: none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" "use-sample-profile" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6, !7, !8, !37}
!llvm.ident = !{!42}
!llvm.errno.tbaa = !{!43}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 22.1.8", isOptimized: true, runtimeVersion: 0, emissionKind: LineTablesOnly, splitDebugInlining: false, debugInfoForProfiling: true, nameTableKind: None)
!1 = !DIFile(filename: "layout.c", directory: "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k0/k2a/r2/fixture", checksumkind: CSK_MD5, checksum: "ff3a2c4d0ce65b9c0af819ee70a279c4")
!2 = !{i32 7, !"Dwarf Version", i32 5}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 1, !"wchar_size", i32 4}
!5 = !{i32 8, !"PIC Level", i32 2}
!6 = !{i32 7, !"PIE Level", i32 2}
!7 = !{i32 7, !"uwtable", i32 2}
!8 = !{i32 1, !"ProfileSummary", !9}
!9 = !{!10, !11, !12, !13, !14, !15, !16, !17, !18, !19}
!10 = !{!"ProfileFormat", !"SampleProfile"}
!11 = !{!"TotalCount", i64 1299906}
!12 = !{!"MaxCount", i64 100001}
!13 = !{!"MaxInternalCount", i64 0}
!14 = !{!"MaxFunctionCount", i64 100000}
!15 = !{!"NumCounts", i64 23}
!16 = !{!"NumFunctions", i64 4}
!17 = !{!"IsPartialProfile", i64 0}
!18 = !{!"PartialProfileRatio", double 0.000000e+00}
!19 = !{!"DetailedSummary", !20}
!20 = !{!21, !22, !23, !24, !25, !26, !27, !28, !29, !30, !31, !32, !33, !34, !35, !36}
!21 = !{i32 10000, i64 100001, i32 1}
!22 = !{i32 100000, i64 100000, i32 7}
!23 = !{i32 200000, i64 100000, i32 7}
!24 = !{i32 300000, i64 100000, i32 7}
!25 = !{i32 400000, i64 100000, i32 7}
!26 = !{i32 500000, i64 100000, i32 7}
!27 = !{i32 600000, i64 99900, i32 13}
!28 = !{i32 700000, i64 99900, i32 13}
!29 = !{i32 800000, i64 99900, i32 13}
!30 = !{i32 900000, i64 99900, i32 13}
!31 = !{i32 950000, i64 99900, i32 13}
!32 = !{i32 990000, i64 99900, i32 13}
!33 = !{i32 999000, i64 99900, i32 13}
!34 = !{i32 999900, i64 100, i32 18}
!35 = !{i32 999990, i64 100, i32 18}
!36 = !{i32 999999, i64 1, i32 23}
!37 = !{i32 5, !"CG Profile", !38}
!38 = distinct !{!39, !40, !41}
!39 = !{ptr @choose, ptr @left, i64 99900}
!40 = !{ptr @choose, ptr @right, i64 100}
!41 = !{ptr @main, ptr @choose, i64 99999}
!42 = !{!"clang version 22.1.8"}
!43 = !{!44, !44, i64 0}
!44 = !{!"int", !45, i64 0}
!45 = !{!"omnipotent char", !46, i64 0}
!46 = !{!"Simple C/C++ TBAA"}
!47 = distinct !DISubprogram(name: "choose", scope: !1, file: !1, line: 7, type: !48, scopeLine: 8, flags: DIFlagPrototyped | DIFlagAllCallsDescribed, spFlags: DISPFlagDefinition | DISPFlagOptimized, unit: !0, keyInstructions: true)
!48 = !DISubroutineType(types: !49)
!49 = !{}
!50 = !{!"function_entry_count", i64 100000}
!51 = !DILocation(line: 9, column: 11, scope: !47, atomGroup: 1, atomRank: 2)
!52 = !DILocation(line: 9, column: 11, scope: !47, atomGroup: 1, atomRank: 1)
!53 = !{!"branch_weights", i32 99900, i32 100}
!54 = !DILocation(line: 10, column: 17, scope: !47, atomGroup: 2, atomRank: 2)
!55 = !{!"branch_weights", i32 99900}
!56 = !DILocation(line: 14, column: 13, scope: !47, atomGroup: 5, atomRank: 2)
!57 = !{!"branch_weights", i32 100}
!58 = !DILocation(line: 0, scope: !47)
!59 = !DILocation(line: 17, column: 1, scope: !47, atomGroup: 8, atomRank: 1)
!60 = distinct !DISubprogram(name: "left", scope: !1, file: !1, line: 19, type: !48, scopeLine: 20, flags: DIFlagPrototyped | DIFlagAllCallsDescribed, spFlags: DISPFlagDefinition | DISPFlagOptimized, unit: !0, keyInstructions: true)
!61 = !{!"function_entry_count", i64 99900}
!62 = !DILocation(line: 21, column: 30, scope: !60)
!63 = !DILocation(line: 21, column: 37, scope: !60)
!64 = !DILocation(line: 21, column: 42, scope: !60)
!65 = !DILocation(line: 21, column: 35, scope: !60, atomGroup: 1, atomRank: 2)
!66 = !DILocation(line: 21, column: 5, scope: !60, atomGroup: 1, atomRank: 1)
!67 = distinct !DISubprogram(name: "right", scope: !1, file: !1, line: 24, type: !48, scopeLine: 25, flags: DIFlagPrototyped | DIFlagAllCallsDescribed, spFlags: DISPFlagDefinition | DISPFlagOptimized, unit: !0, keyInstructions: true)
!68 = !{!"function_entry_count", i64 100}
!69 = !DILocation(line: 26, column: 30, scope: !67)
!70 = !DILocation(line: 26, column: 38, scope: !67)
!71 = !DILocation(line: 26, column: 43, scope: !67)
!72 = !DILocation(line: 26, column: 36, scope: !67, atomGroup: 1, atomRank: 2)
!73 = !DILocation(line: 26, column: 5, scope: !67, atomGroup: 1, atomRank: 1)
!74 = distinct !DISubprogram(name: "main", scope: !1, file: !1, line: 29, type: !48, scopeLine: 30, flags: DIFlagPrototyped | DIFlagAllCallsDescribed, spFlags: DISPFlagDefinition | DISPFlagOptimized, unit: !0, keyInstructions: true)
!75 = !{!"function_entry_count", i64 1}
!76 = !DILocation(line: 32, column: 30, scope: !74, atomGroup: 1, atomRank: 3)
!77 = !DILocation(line: 33, column: 5, scope: !78, atomGroup: 12, atomRank: 1)
!78 = !DILexicalBlockFile(scope: !74, file: !1, discriminator: 2)
!79 = !DILocation(line: 37, column: 12, scope: !74)
!80 = !DILocation(line: 37, column: 17, scope: !74, atomGroup: 10, atomRank: 3)
!81 = !DILocation(line: 37, column: 17, scope: !74, atomGroup: 10, atomRank: 2)
!82 = !DILocation(line: 37, column: 5, scope: !74, atomGroup: 10, atomRank: 1)
!83 = !DILocation(line: 34, column: 28, scope: !74)
!84 = !DILocation(line: 34, column: 35, scope: !74, atomGroup: 5, atomRank: 3)
!85 = !DILocation(line: 35, column: 16, scope: !74, atomGroup: 6, atomRank: 1)
!86 = !DILocation(line: 0, scope: !74)
!87 = !DILocation(line: 35, column: 9, scope: !88)
!88 = !DILexicalBlockFile(scope: !74, file: !1, discriminator: 6)
!89 = !{!"branch_weights", i32 100000}
!90 = !DILocation(line: 33, column: 33, scope: !91, atomGroup: 7, atomRank: 2)
!91 = !DILexicalBlockFile(scope: !74, file: !1, discriminator: 4)
!92 = !DILocation(line: 33, column: 23, scope: !78, atomGroup: 3, atomRank: 1)
!93 = !DILocation(line: 33, column: 5, scope: !78, atomGroup: 4, atomRank: 1)
!94 = !{!"branch_weights", i32 1, i32 99999}
!95 = distinct !{!95, !96, !97, !98}
!96 = !DILocation(line: 33, column: 5, scope: !74)
!97 = !DILocation(line: 36, column: 5, scope: !74)
!98 = !{!"llvm.loop.mustprogress"}
