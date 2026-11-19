.syntax unified
.arch armv7-a
.arm
.global _start
.type _start,%function
_start:
    mov r0, #0x4000000
loop:
.if EXTRA
    cmp r0, r0
    bne loop
.endif
    subs r0, r0, #1
    bne loop
    mov r0, #0
    mov r7, #1
    svc #0
.size _start, .-_start
