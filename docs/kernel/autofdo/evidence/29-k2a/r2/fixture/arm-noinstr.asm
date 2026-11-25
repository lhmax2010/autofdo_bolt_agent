
arm-noinstr.o:	file format elf32-littlearm

Disassembly of section .text:

00000000 <ordinary>:
       0: e59f1048     	ldr	r1, [pc, #0x48]         @ 0x50 <ordinary+0x50>
       4: e3500007     	cmp	r0, #7
       8: e08f1001     	add	r1, pc, r1
       c: ba000007     	blt	0x30 <ordinary+0x30>    @ imm = #0x1c
      10: e59f203c     	ldr	r2, [pc, #0x3c]         @ 0x54 <ordinary+0x54>
      14: e79f2002     	ldr	r2, [pc, r2]
      18: e2922001     	adds	r2, r2, #1
      1c: e5812000     	str	r2, [r1]
      20: e5912004     	ldr	r2, [r1, #0x4]
      24: e2a22000     	adc	r2, r2, #0
      28: e5812004     	str	r2, [r1, #0x4]
      2c: eafffffe     	b	0x2c <ordinary+0x2c>    @ imm = #-0x8
			0000002c:  R_ARM_JUMP24	early
      30: e5912008     	ldr	r2, [r1, #0x8]
      34: e591300c     	ldr	r3, [r1, #0xc]
      38: e2800003     	add	r0, r0, #3
      3c: e2922001     	adds	r2, r2, #1
      40: e2a33000     	adc	r3, r3, #0
      44: e5812008     	str	r2, [r1, #0x8]
      48: e581300c     	str	r3, [r1, #0xc]
      4c: e12fff1e     	bx	lr
      50: 40 00 00 00  	.word	0x00000040
			00000050:  R_ARM_REL32	__llvm_gcov_ctr
      54: 38 00 00 00  	.word	0x00000038
			00000054:  R_ARM_REL32	__llvm_gcov_ctr

00000058 <__llvm_gcov_writeout>:
      58: e92d4010     	push	{r4, lr}
      5c: e59f0048     	ldr	r0, [pc, #0x48]         @ 0xac <__llvm_gcov_writeout+0x54>
      60: e59f403c     	ldr	r4, [pc, #0x3c]         @ 0xa4 <__llvm_gcov_writeout+0x4c>
      64: e59f1034     	ldr	r1, [pc, #0x34]         @ 0xa0 <__llvm_gcov_writeout+0x48>
      68: e08f0000     	add	r0, pc, r0
      6c: e1a02004     	mov	r2, r4
      70: ebfffffe     	bl	0x70 <__llvm_gcov_writeout+0x18> @ imm = #-0x8
			00000070:  R_ARM_CALL	llvm_gcda_start_file
      74: e59f102c     	ldr	r1, [pc, #0x2c]         @ 0xa8 <__llvm_gcov_writeout+0x50>
      78: e3a00000     	mov	r0, #0
      7c: e1a02004     	mov	r2, r4
      80: ebfffffe     	bl	0x80 <__llvm_gcov_writeout+0x28> @ imm = #-0x8
			00000080:  R_ARM_CALL	llvm_gcda_emit_function
      84: e59f1024     	ldr	r1, [pc, #0x24]         @ 0xb0 <__llvm_gcov_writeout+0x58>
      88: e3a00002     	mov	r0, #2
      8c: e08f1001     	add	r1, pc, r1
      90: ebfffffe     	bl	0x90 <__llvm_gcov_writeout+0x38> @ imm = #-0x8
			00000090:  R_ARM_CALL	llvm_gcda_emit_arcs
      94: ebfffffe     	bl	0x94 <__llvm_gcov_writeout+0x3c> @ imm = #-0x8
			00000094:  R_ARM_CALL	llvm_gcda_summary_info
      98: e8bd4010     	pop	{r4, lr}
      9c: eafffffe     	b	0x9c <__llvm_gcov_writeout+0x44> @ imm = #-0x8
			0000009c:  R_ARM_JUMP24	llvm_gcda_end_file
      a0: 2a 31 31 42  	.word	0x4231312a
      a4: 5d e3 a4 fd  	.word	0xfda4e35d
      a8: cb e6 6f c6  	.word	0xc66fe6cb
      ac: 3c 00 00 00  	.word	0x0000003c
			000000ac:  R_ARM_REL32	.L__unnamed_1
      b0: 1c 00 00 00  	.word	0x0000001c
			000000b0:  R_ARM_REL32	__llvm_gcov_ctr

000000b4 <__llvm_gcov_reset>:
      b4: e59f0018     	ldr	r0, [pc, #0x18]         @ 0xd4 <__llvm_gcov_reset+0x20>
      b8: e3a01000     	mov	r1, #0
      bc: e08f0000     	add	r0, pc, r0
      c0: e5801000     	str	r1, [r0]
      c4: e5801004     	str	r1, [r0, #0x4]
      c8: e5801008     	str	r1, [r0, #0x8]
      cc: e580100c     	str	r1, [r0, #0xc]
      d0: e12fff1e     	bx	lr
      d4: 10 00 00 00  	.word	0x00000010
			000000d4:  R_ARM_REL32	__llvm_gcov_ctr

000000d8 <__llvm_gcov_init>:
      d8: e59f000c     	ldr	r0, [pc, #0xc]          @ 0xec <__llvm_gcov_init+0x14>
      dc: e59f100c     	ldr	r1, [pc, #0xc]          @ 0xf0 <__llvm_gcov_init+0x18>
      e0: e08f0000     	add	r0, pc, r0
      e4: e08f1001     	add	r1, pc, r1
      e8: eafffffe     	b	0xe8 <__llvm_gcov_init+0x10> @ imm = #-0x8
			000000e8:  R_ARM_JUMP24	llvm_gcov_init
      ec: 70 ff ff ff  	.word	0xffffff70
      f0: c8 ff ff ff  	.word	0xffffffc8

Disassembly of section .noinstr.text:

00000000 <early>:
       0: e3a01003     	mov	r1, #3
       4: e3500006     	cmp	r0, #6
       8: c3e01003     	mvngt	r1, #3
       c: e0810000     	add	r0, r1, r0
      10: e12fff1e     	bx	lr
