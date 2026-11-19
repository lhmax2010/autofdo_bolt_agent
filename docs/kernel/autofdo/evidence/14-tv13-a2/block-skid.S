.syntax unified
.arch armv7-a
.arm
.global _start
.type _start,%function
_start:
    ldr r7, [sp, #8]
    mov r0, #0
.rept 9
    ldrb r1, [r7], #1
    sub r1, r1, #48
    add r2, r0, r0, lsl #2
    add r0, r1, r2, lsl #1
.endr
    mov r3, #0
block_00:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_01
    udf #0
block_01:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_02
    udf #0
block_02:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_03
    udf #0
block_03:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_04
    udf #0
block_04:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_05
    udf #0
block_05:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_06
    udf #0
block_06:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_07
    udf #0
block_07:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_08
    udf #0
block_08:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_09
    udf #0
block_09:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_10
    udf #0
block_10:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_11
    udf #0
block_11:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_12
    udf #0
block_12:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_13
    udf #0
block_13:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_14
    udf #0
block_14:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_15
    udf #0
block_15:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_16
    udf #0
block_16:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_17
    udf #0
block_17:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_18
    udf #0
block_18:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_19
    udf #0
block_19:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_20
    udf #0
block_20:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_21
    udf #0
block_21:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_22
    udf #0
block_22:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_23
    udf #0
block_23:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_24
    udf #0
block_24:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_25
    udf #0
block_25:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_26
    udf #0
block_26:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_27
    udf #0
block_27:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_28
    udf #0
block_28:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_29
    udf #0
block_29:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_30
    udf #0
block_30:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_31
    udf #0
block_31:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_32
    udf #0
block_32:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_33
    udf #0
block_33:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_34
    udf #0
block_34:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_35
    udf #0
block_35:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_36
    udf #0
block_36:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_37
    udf #0
block_37:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_38
    udf #0
block_38:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_39
    udf #0
block_39:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_40
    udf #0
block_40:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_41
    udf #0
block_41:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_42
    udf #0
block_42:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_43
    udf #0
block_43:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_44
    udf #0
block_44:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_45
    udf #0
block_45:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_46
    udf #0
block_46:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_47
    udf #0
block_47:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_48
    udf #0
block_48:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_49
    udf #0
block_49:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_50
    udf #0
block_50:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_51
    udf #0
block_51:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_52
    udf #0
block_52:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_53
    udf #0
block_53:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_54
    udf #0
block_54:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_55
    udf #0
block_55:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_56
    udf #0
block_56:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_57
    udf #0
block_57:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_58
    udf #0
block_58:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_59
    udf #0
block_59:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_60
    udf #0
block_60:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    b block_61
    udf #0
block_61:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    b block_62
    udf #0
block_62:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    b block_63
    udf #0
block_63:
    add r3, r3, #1
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    add r3, r3, #6
    add r3, r3, #7
    add r3, r3, #1
    add r3, r3, #2
    add r3, r3, #3
    add r3, r3, #4
    add r3, r3, #5
    subs r0, r0, #1
    bne block_00
end_blocks:
    mov r0, #0
    mov r7, #1
    svc #0
.size _start, .-_start
