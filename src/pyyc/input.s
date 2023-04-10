.globl main
main:
	pushl %ebp
	movl %esp, %ebp
	subl $0, %esp
	pushl %ebx
	pushl %esi
	pushl %edi
	popl %edi
	popl %esi
	popl %ebx
	movl $0, %eax
	movl %ebp, %esp
	popl %ebp
	ret
	