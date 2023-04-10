import sys
import ast
from ast import *
from flatten import Flatten

class Assembly:
    # this makes all our local variables
    # put all our local variables into the dict
    def make_variables(self, tree, variables):
        register = -4
        for node in ast.walk(tree):
            if isinstance(node, Name):
                if not node.id == "print" and not node.id == "eval" and not node.id == "input" and not node.id in variables:
                    variables[node.id] = register
                    register -= 4
        return register + 4
                
    def assembly_baby(self, n, esp, variables, prog):
        if isinstance(n, Module):
            # ok, gotta do everything
            prog.append('pushl %ebp')
            prog.append('movl %esp, %ebp')
            prog.append('subl $' + str(-esp) + ', %esp')
            prog.append('pushl %ebx')
            prog.append('pushl %esi')
            prog.append('pushl %edi')
            for node in n.body:
                # do stuff
                self.assembly_baby(node, esp, variables, prog)
            # we're done lets leave
            prog.append('popl %edi')
            prog.append('popl %esi')
            prog.append('popl %ebx')
            prog.append('movl $0, %eax')
            prog.append('movl %ebp, %esp')
            prog.append('popl %ebp')
            prog.append('ret')
        elif isinstance(n, Assign):
            if isinstance(n.value, Name) and isinstance(n.targets[0], Name):
                prog.append('movl ' + self.assembly_baby(n.value, esp, variables, prog) + ', %eax')
                prog.append('movl %eax, ' + self.assembly_baby(n.targets[0], esp, variables, prog))
            else:
                line = ''
                line += 'movl ' + self.assembly_baby(n.value, esp, variables, prog) + ', '
                line += self.assembly_baby(n.targets[0], esp, variables, prog)
                prog.append(line)
        elif isinstance(n, Expr):
            self.assembly_baby(n.value, esp, variables, prog)
        elif isinstance(n, Constant):
            return '$' + str(n.value)
        elif isinstance(n, Name):
            return str(variables[n.id]) + '(%ebp)'
        elif isinstance(n, BinOp):
            prog.append('movl ' + self.assembly_baby(n.left, esp, variables, prog) + ', %eax')
            line = self.assembly_baby(n.op, esp, variables, prog)
            line += self.assembly_baby(n.right, esp, variables, prog)
            line += ', %eax'
            prog.append(line)
            return '%eax'
        elif isinstance(n, UnaryOp):
            prog.append('movl ' + self.assembly_baby(n.operand, esp, variables, prog) + ', %eax')
            prog.append(self.assembly_baby(n.op, esp, variables, prog) + '%eax')
            return '%eax'
        elif isinstance(n, Call):
            if n.func.id == 'eval':
                prog.append('call eval_input_int')
                return '%eax'
            elif n.func.id == 'print':
                prog.append('movl ' + self.assembly_baby(n.args[0], esp, variables, prog) + ', %eax')
                prog.append('pushl %eax')
                prog.append('call print_int_nl')
                prog.append('addl $4, %esp')
            return
        elif isinstance(n, Add):
            return 'addl '
        elif isinstance(n, USub):
            return 'neg '
        elif isinstance(n, Load):
            return
        elif isinstance(n, Store):
            return
        else:
            raise Exception('Error: unrecognized AST node')
        
    
    def create_assembly(self, file_name):
        flatten = Flatten()
        new_tree = flatten.flatten_file(file_name)
        local_variables = {}
        esp = self.make_variables(new_tree, local_variables)
        print('Variables:')
        print(local_variables)

        new_prog = []
        self.assembly_baby(new_tree, esp, local_variables, new_prog)
        final_prog = ''
        final_prog += '.globl main\n'
        final_prog += 'main:\n\t'
        for line in new_prog:
            final_prog += line + '\n\t'
        print('Assembly:')
        print(final_prog)
        with open(file_name.replace('.py', '.s'), 'w') as f:
            f.write(final_prog)


if __name__ == '__main__':
    print("calling the assembly class")
    assembly = Assembly()
    assembly.create_assembly(sys.argv[1])