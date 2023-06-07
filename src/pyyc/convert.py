import sys
import ast
from ast import *
import pickle


class CallFunction():
    def __init__(self, args = [], returnList = []):
        self.args = args
        self.returnList = returnList

class ToIRConverter():
    def __init__(self, print_x86_IR):
        # print x86 IR when we are done
        self.print_IR = print_x86_IR
        # stores our intermediate code
        self.intermediate = []
        # for control flow we need indents
        # this is the current level of indents we have
        self.indent = ''
        # this is a number so we can label our control flows
        self.control_num = 0
        # functions that do the same thing
        self.functions_one_arg = ['print', 'error_pyobj']
        self.functions_two_arg = ['is_int', 'box_int', 'unbox_int', 'box_bool', 'unbox_bool', 'int', 
                                  'is_bool', 'box_big', 'unbox_big', 'create_list', 'is_big', 'is_true']
        self.functions_two_in_one_out = ['equal', 'get_subscript', 'add', 'not_equal']
        self.functions_one_out = ['eval', 'create_dict']
        self.functions_three_arg = ['set_subscript']


    ## it is hard to create all the objects, so instead we will just do it for call functions. 
    def create_call_func(self, indent, func_id, args, rv):
        argsList = []
        for arg in args:
            argsList.append(self.convert(arg))

        if len(argsList) > 0:
            argsList[0] = ', ' + argsList[0]
        #f = CallFunction(argsList, rl)
        ## for now just do how it was processing 
        rl = ''
        if rv:
            rl = ', ' + rv
        self.intermediate.append(
            indent +
            'call ' + func_id + ', '.join(argsList) + rl
        )
        
    def python_to_IR(self, python_ast):
        print('----- making intermediate -----')
        self.convert(python_ast)
        # convert our list to a single string
        intermediate_prog = ''
        for line in self.intermediate:
            intermediate_prog += line + '\n'
        if self.print_IR:
            print('----- intermediate code -----')
            print(intermediate_prog)
        return intermediate_prog   
        
    def convert(self, n, var=None):
        # p0
        # if it's a module go do IR for all your nodes
        if isinstance(n, Module):
            for node in n.body:
                self.convert(node)
        # if it's a simple assign just move value into target
        # if it's not put targets as var so later things can use it
        # and then go do whatever your child says to do
        elif isinstance(n, Assign):
            if isinstance(n.value, Name) or isinstance(n.value, Constant):
                self.intermediate.append(
                    self.indent +
                    'movl ' + self.convert(n.value) + ', ' + self.convert(n.targets[0])
                )
            else:
                self.convert(n.value, n.targets[0].id)
        # expr just convert your child
        elif isinstance(n, Expr):
            self.convert(n.value)
        # constant return value
        elif isinstance(n, Constant):
            return '$' + str(n.value)
        # return variable name
        elif isinstance(n, Name):
            return n.id
        # call has 3 instances, print eval int
        # print, call print and convert your argument
        # eval, call eval_input and use var passed from assign
        # int, just convert your children it's stupid
        elif isinstance(n, Call):
            # has int in it also
            if n.func.id in self.functions_one_arg:
                self.intermediate.append(
                    self.indent +
                    'call ' + n.func.id + ', ' + self.convert(n.args[0])
                )
            elif n.func.id in self.functions_two_arg:
                self.intermediate.append(
                    self.indent + 
                    'call ' + n.func.id + ', ' + self.convert(n.args[0]) + ', ' + var
                )
            elif n.func.id in self.functions_three_arg:
                self.intermediate.append(
                    self.indent +
                    'call ' + n.func.id + 
                    ', ' + self.convert(n.args[0]) + 
                    ', ' + self.convert(n.args[1]) + 
                    ', ' + self.convert(n.args[2])
                )
            elif n.func.id in self.functions_one_out:
                if n.func.id == 'eval':
                    n.func.id = 'eval_input'
                self.intermediate.append(
                    self.indent +
                    'call ' + n.func.id + ', ' + var
                )
            elif n.func.id in self.functions_two_in_one_out:
                self.intermediate.append(
                    self.indent +
                    'call ' + n.func.id +
                    ', ' + var +
                    ', ' + self.convert(n.args[0]) +
                    ', ' + self.convert(n.args[1])
                )
            elif n.func.id == 'int':
                return self.convert(n.args[0], var)
            else:
                self.create_call_func(self.indent, n.func.id, n.args, var)
                #print(ast.dump(n, indent=4))
                #raise Exception('***** Error: unrecognized function id convert *****')
        # uhg, was is not a unary op
        # just, if it's not do dumb nonsense, else be normal
        elif isinstance(n, UnaryOp):
            if isinstance(n.op, Not):
                self.intermediate.append(
                    self.indent +
                    'cmpl $0, ' + self.convert(n.operand)
                )
                self.intermediate.append(
                    self.indent +
                    'sete %al'
                )
                self.intermediate.append(
                    self.indent +
                    'movzbl %al, ' + var
                )
            else:
                self.intermediate.append(
                    self.indent +
                    'movl ' + self.convert(n.operand) + ', ' + var
                )
                self.intermediate.append(
                    self.indent +
                    self.convert(n.op) + var
                )
        # binop is weird because we have to be careful about overwriting stuff
        # so if the left op is the same as what we are moving into, just add
        # if the right op is same as what we are moving into, just add
        # else, move left into our var then add the right
        # have to do it this way since x = 3 + x
        # if you moved 3 into x then added x that's wrong
        elif isinstance(n, BinOp):
            left = self.convert(n.left)
            right = self.convert(n.right)
            if left == var:
                self.intermediate.append(
                    self.indent +
                    self.convert(n.op) + right + ', ' + var
                )
            elif right == var:
                self.intermediate.append(
                    self.indent +
                    self.convert(n.op) + left + ', ' + var
                )
            else:
                self.intermediate.append(
                    self.indent +
                    'movl ' + left + ', ' + var
                )
                self.intermediate.append(
                    self.indent +
                    self.convert(n.op) + right + ', ' + var
                )
        elif isinstance(n, Add):
            return 'addl '
        elif isinstance(n, USub):
            return 'neg '
        elif isinstance(n, Load):
            return
        elif isinstance(n, Store):
            return
        # end of p0
        # p0a
        # vaguely annoying
        # if it's an and, if the first value is 0 set it to that and leave
        # if not then whatever the second value is
        # for or just the opposite
        elif isinstance(n, BoolOp):
            if isinstance(n.op, And):
                self.intermediate.append(
                    self.indent +
                    'cmpl $0, ' + self.convert(n.values[0])
                )
                self.intermediate.append(
                    self.indent +
                    'je or' + str(self.control_num)
                )
                self.intermediate.append(
                    self.indent +
                    'movl ' + self.convert(n.values[1]) + ', ' + var
                )
                self.intermediate.append(
                    self.indent +
                    'jmp end' + str(self.control_num)
                )
                self.intermediate.append(
                    self.indent +
                    'or' + str(self.control_num) + ':'
                )
                self.intermediate.append(
                    self.indent +
                    'movl ' + self.convert(n.values[0]) + ', ' + var
                )
                self.intermediate.append(
                    self.indent +
                    'end' + str(self.control_num) + ':'
                )
                self.control_num += 1
            elif isinstance(n.op, Or):
                self.intermediate.append(
                    self.indent +
                    'cmpl $0, ' + self.convert(n.values[0])
                )
                self.intermediate.append(
                    self.indent +
                    'je or' + str(self.control_num)
                )
                self.intermediate.append(
                    self.indent +
                    'movl ' + self.convert(n.values[0]) + ', ' + var
                )
                self.intermediate.append(
                    self.indent +
                    'jmp end' + str(self.control_num)
                )
                self.intermediate.append(
                    self.indent +
                    'or' + str(self.control_num) + ':'
                )
                self.intermediate.append(
                    self.indent +
                    'movl ' + self.convert(n.values[1]) + ', ' + var
                )
                self.intermediate.append(
                    self.indent +
                    'end' + str(self.control_num) + ':'
                )
                self.control_num += 1
            else:
                print(n)
                raise Exception('***** Error: unrecognized BoolOp *****')
        elif isinstance(n, And):
            return
        elif isinstance(n, Or):
            return
        elif isinstance(n, Not):
            return
        # this one is actually easy and straightforward
        # just uh, do it ig
        elif isinstance(n, Compare):
            self.intermediate.append(
                self.indent +
                'cmpl ' + self.convert(n.left) + ', ' + self.convert(n.comparators[0])
            )
            self.intermediate.append(
                self.indent +
                self.convert(n.ops[0]) + '%al'
            )
            self.intermediate.append(
                self.indent + 
                'movzbl %al, ' + var
            )
        elif isinstance(n, Eq):
            return 'sete '
        elif isinstance(n, NotEq):
            return 'setne '
        # if is cmp, then based on cmp jump to if or else
        # then change the self.indent so that everything in 
        # the body is indented, then go through and add everything
        # in the body
        elif isinstance(n, If):
            self.intermediate.append(
                self.indent +
                'cmpl $0, ' + self.convert(n.test)
            )
            self.intermediate.append(
                self.indent +
                'je else' + str(self.control_num)
            )
            self.intermediate.append(
                self.indent +
                'then' + str(self.control_num) + ':'
            )
            old_num = self.control_num
            old_indent = self.indent
            self.indent += '\t'
            self.control_num += 1
            for node in n.body:
                self.convert(node)
            self.intermediate.append(
                old_indent +
                'jmp end' + str(old_num)
            )
            self.intermediate.append(
                old_indent +
                'else' + str(old_num) + ':'
            )
            for node in n.orelse:
                self.convert(node)
            self.intermediate.append(
                old_indent + 
                'end' + str(old_num) + ':'
            )
            self.indent = old_indent
        # if it's false jump to the end, indent everything in body
        elif isinstance(n, While):
            self.intermediate.append(
                self.indent +
                'while' + str(self.control_num) + ':'
            )
            self.intermediate.append(
                self.indent +
                'cmpl $0, ' + self.convert(n.test)
            )
            self.intermediate.append(
                self.indent +
                'loop' + str(self.control_num) + ':'
            )
            old_num = self.control_num
            old_indent = self.indent
            self.indent += '\t'
            self.control_num += 1
            self.intermediate.append(
                self.indent +
                'je end' + str(old_num)
            )
            for node in n.body:
                self.convert(node)
            self.intermediate.append(
                self.indent +
                'jmp while' + str(old_num)
            )
            self.intermediate.append(
                old_indent +
                'end' + str(old_num) + ':'
            )
            self.indent = old_indent
        elif isinstance(n, FunctionDef):
            self.intermediate.append(
                self.indent + 'def ' + n.name)
            old_indent = self.indent
            self.indent += '\t'
            for i in range(len(n.args.args)):
                self.intermediate.append(
                    self.indent +
                    'movl +' + str((i+1)*4+4) +
                    '(%ebp), ' + n.args.args[i].arg
                )
            for node in n.body:
                self.convert(node)
            self.indent = old_indent
        elif isinstance(n, Return):
            self.intermediate.append(self.indent + 'ret ' + self.convert(n.value))
        # end of p0a
        else:
            print(n)
            raise Exception('***** Error: unrecognized AST node in IR *****')