choose:                                 # @choose
.Lfunc_begin0:
	.file	0 "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k0/k2a/r2/fixture" "layout.c" md5 0xff3a2c4d0ce65b9c0af819ee70a279c4
	.loc	0 8 0                           # layout.c:8:0
	.cfi_startproc
# %bb.0:
	pushq	%rax
	.cfi_def_cfa_offset 16
.Ltmp0:
	.loc	0 9 11 prologue_end             # layout.c:9:11
	testl	%edi, %edi
	je	.LBB0_1
# %bb.2:
	.loc	0 14 13                         # layout.c:14:13
	callq	right
.Ltmp1:
	.loc	0 0 13 is_stmt 0                # layout.c:0:13
	movl	$5, %ecx
.LBB0_3:
	imull	sink(%rip), %ecx
	addl	%eax, %ecx
	movl	%ecx, sink(%rip)
	.loc	0 17 1 epilogue_begin is_stmt 1 # layout.c:17:1
	popq	%rcx
	.cfi_def_cfa_offset 8
	retq
.LBB0_1:
	.cfi_def_cfa_offset 16
	.loc	0 10 17                         # layout.c:10:17
	xorl	%edi, %edi
	callq	left
.Ltmp2:
	.loc	0 0 17 is_stmt 0                # layout.c:0:17
	movl	$3, %ecx
	jmp	.LBB0_3
.Ltmp3:
.Lfunc_end0:
