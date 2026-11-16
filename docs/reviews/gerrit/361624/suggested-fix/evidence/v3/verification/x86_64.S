.text
.globl _start
.type _start,@function
_start:
 call answer
 mov %eax,%edi
 mov $60,%eax
 syscall
.size _start,.-_start
.globl answer
.type answer,@function
answer:
 mov $7,%eax
 ret
.size answer,.-answer
