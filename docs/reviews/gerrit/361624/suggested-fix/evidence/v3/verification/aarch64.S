.text
.globl _start
.type _start,%function
_start:
 bl answer
 mov x8,#93
 svc #0
.size _start,.-_start
.globl answer
.type answer,%function
answer:
 mov x0,#7
 ret
.size answer,.-answer
