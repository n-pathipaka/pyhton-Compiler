import sys
import ast
from ast import *

from parse import Parser

class Flatten:
    def __init__(self, print_ast, print_prog):
        self.tmp_number = 0
        self.flattened_program = []
        self.print_ast = print_ast
        self.print_prog = print_prog
        self.variables = set()
        self.indent = ''
        # Name nodes that are reserved
        self.reserved_names = ['print', 'eval', 'input', 'int', 'is_int', 'unbox_int', 
                               'box_int', 'box_bool', 'unbox_bool', 'is_bool', 'box_big', 'unbox_big',
                              'create_list', 'set_subscript', 'create_dict', 'equal', 'is_big',
                              'get_subscript', 'is_true', 'add', 'not_equal', 'TypeError']
        # classes that need to be reduced
        # ie if you're one of these classes make a tmp variable and return that instead
        self.flatten_instances = [BinOp, UnaryOp, Call, BoolOp, Compare, Subscript, List, Dict]
        # some functions you don't actually want to flatten their arguments
        # TODO: I think you can add eval and input and it'll just work
        self.dont_flatten_args = []
        # consider adding a does something expr, add print
        
    def flatten(self, tree):
        print("----- flattening -----")
        self.replace_variables(tree)
        #print(ast.dump(tree, indent=4))
        self.make_flattened_prog(tree)
        # convert list to string
        program = ''
        for line in self.flattened_program:
            program += str(line) + '\n'
        # make ast
        # TODO undid for testing
        parser = Parser(self.print_prog, self.print_ast)
        tree = parser.parse_string(program)
        # store variables
        #for node in ast.walk(tree):
        #    if isinstance(node, Name):
        #        if not node.id in self.reserved_names:
        #            variables.add(node.id)
        return tree
    
    def make_flattened_prog(self, n, assign=None):
        if isinstance(n, Module):
            for node in n.body:
                self.make_flattened_prog(node)
        # p0
        # target = value
        elif isinstance(n, Assign):
            if isinstance(n.value, IfExp):
                self.make_flattened_prog(n.value, n)
            elif isinstance(n.targets[0], Subscript):
                line = self.make_flattened_prog(n.targets[0])
                line += ' = '
                if self.check_instances(n.value):
                    line += self.make_temp(n.value)
                else:
                    line += self.make_flattened_prog(n.value)
                self.flattened_program.append(self.indent + line)
            else:
                line = self.make_flattened_prog(n.targets[0])
                line += ' = '
                line += self.make_flattened_prog(n.value)
                self.flattened_program.append(self.indent + line)
        elif isinstance(n, Expr):
            # print is the only thing that does anything
            # TODO: if add other things redo this
            if isinstance(n.value, Call):
                if n.value.func.id == 'print' or n.value.func.id == 'set_subscript' or n.value.func.id == 'TypeError':
                    self.flattened_program.append(self.indent + self.make_flattened_prog(n.value))
        # return the constant
        elif isinstance(n, Constant):
            return str(n.value)
        # return the variable name
        # also add all our variables to a list for later use
        elif isinstance(n, Name):
            self.variables.add(n.id)
            return n.id
        # do a bin op, but if any of your children are the flatten
        # instances than go flatten them
        elif isinstance(n, BinOp):
            line = ''
            if self.check_instances(n.left):
                line += self.make_temp(n.left)
            else:
                line += self.make_flattened_prog(n.left)
            line += self.make_flattened_prog(n.op)
            if self.check_instances(n.right):
                line += self.make_temp(n.right)
            else:
                line += self.make_flattened_prog(n.right)
            return line
        # same as binop but only one
        elif isinstance(n, UnaryOp):
            line = self.make_flattened_prog(n.op)
            if self.check_instances(n.operand):
                line += self.make_temp(n.operand)
            else:
                line += self.make_flattened_prog(n.operand)
            return line
        # this one you just kinda gotta go through and check everything
        elif isinstance(n, Call):
            #print(ast.dump(n, indent=4))
            line = ''
            # TODO: eval is always eval(input()) redo if this changes
            if n.func.id == 'eval':
                return 'eval(input())'
            if n.func.id == 'TypeError':
                return self.make_flattened_prog(Call(Name('error_pyobj', Load()), [Constant("0")])) 
            if n.func.id in self.dont_flatten_args:
                for arg in n.args:
                    line += self.make_flattened_prog(arg)
                return str(n.func.id) + "(" + line + ")"
            for arg in n.args:
                if self.check_instances(arg):
                    line += self.make_temp(arg) + ', '
                else:
                    line += self.make_flattened_prog(arg) + ', '
            if line[-2:] == ', ':
                line = line[:-2]
            return str(n.func.id) + "(" + line + ")"
        elif isinstance(n, Add):
            return ' + '
        elif isinstance(n, USub):
            return '-'
        elif isinstance(n, Load):
            return
        elif isinstance(n, Store):
            return
        # end of p0
        # p0a
        # this is actually kind of the same as binop, except it can for some reason
        # be any number of operations, so if it's more than 2, remove the first value
        # from your list of operations, then call yourself again accept make flat
        elif isinstance(n, BoolOp):
            line = ''
            if len(n.values) > 2:
                if self.check_instances(n.values[0]):
                    line += self.make_temp(n.values[0])
                else:
                    line += self.make_flattened_prog(n.values[0])
                line += self.make_flattened_prog(n.op)
                n.values = n.values[1:]
                line += self.make_temp(n)
            else:
                if self.check_instances(n.values[0]):
                    line += self.make_temp(n.values[0])
                else:
                    line += self.make_flattened_prog(n.values[0])
                line += self.make_flattened_prog(n.op)
                if self.check_instances(n.values[1]):
                    line += self.make_temp(n.values[1])
                else:
                    line += self.make_flattened_prog(n.values[1])
            return line
        elif isinstance(n, And):
            return ' and '
        elif isinstance(n, Or):
            return ' or '
        # same as binop really just called different stuff
        elif isinstance(n, Compare):
            line = ''
            if self.check_instances(n.left):
                line += self.make_temp(n.left)
            else:
                line += self.make_flattened_prog(n.left)
            line += self.make_flattened_prog(n.ops[0])
            if self.check_instances(n.comparators[0]):
                line += self.make_temp(n.comparators[0])
            else:
                line += self.make_flattened_prog(n.comparators[0])
            return line
        elif isinstance(n, Eq):
            return ' == '
        elif isinstance(n, NotEq):
            return ' != '
        elif isinstance(n, Not):
            return 'not '
        # crazy nonsense
        elif isinstance(n, If):
            line = ''
            if self.check_instances(n.test):
                line += self.make_temp(n.test)
            else:
                line += self.make_flattened_prog(n.test)
            self.flattened_program.append(self.indent + "if " + line + ':')
            old_indent = self.indent
            self.indent += '\t'
            for node in n.body:
                self.make_flattened_prog(node)
            if len(n.orelse) != 0:
                self.flattened_program.append(old_indent + 'else:')
                for node in n.orelse:
                    self.make_flattened_prog(node)
            self.indent = old_indent
        elif isinstance(n, IfExp):
            #print(ast.dump(n, indent=4))
            line = ''
            if self.check_instances(n.test):
                line += self.make_temp(n.test)
            else:
                line += self.make_flattened_prog(n.test)
            self.flattened_program.append(self.indent + 'if ' + line + ':')
            old_indent = self.indent
            self.indent += '\t'
            line = self.make_flattened_prog(assign.targets[0])
            line += ' = '
            line += self.make_flattened_prog(n.body)
            self.flattened_program.append(self.indent + line)
            self.flattened_program.append(old_indent + 'else:')
            
            line = self.make_flattened_prog(assign.targets[0])
            line += ' = '
            line += self.make_flattened_prog(n.orelse)
            self.flattened_program.append(self.indent + line)
            
            self.indent = old_indent
        elif isinstance(n, While):
            line = ''
            start_test = len(self.flattened_program)
            if self.check_instances(n.test):
                line += self.make_temp(n.test)
            else:
                line += self.make_flattened_prog(n.test)
            end_test = len(self.flattened_program)
            self.flattened_program.append(self.indent + "while " + line + ':')
            old_indent = self.indent
            self.indent += '\t'
            for node in n.body:
                self.make_flattened_prog(node)
            self.indent = old_indent
            for boy in self.flattened_program[start_test:end_test]:
                self.flattened_program.append(self.indent + '\t' + boy.replace('\t',''))
        elif isinstance(n, List):
            line = ''
            for element in n.elts:
                if self.check_instances(element):
                    line += self.make_temp(element) + ', '
                else:
                    line += self.make_flattened_prog(element) + ', '
            return '[' + line[:-2] + ']'
        elif isinstance(n, Dict):
            line = ''
            for i in range(len(n.keys)):
                if self.check_instances(n.keys[i]):
                    line += self.make_temp(n.keys[i])
                else:
                    line += self.make_flattened_prog(n.keys[i])
                line += ': '
                if self.check_instances(n.values[i]):
                    line += self.make_temp(n.values[i])
                else:
                    line += self.make_flattened_prog(n.values[i])
                line += ', '
            return '{' + line[:-2] + '}'
        elif isinstance(n, Subscript):
            line = ''
            if self.check_instances(n.value):
                line += self.make_temp(n.value)
            else:
                line += self.make_flattened_prog(n.value)
            line += '['
            if self.check_instances(n.slice):
                line += self.make_temp(n.slice)
            else:
                line += self.make_flattened_prog(n.slice)
            line += ']'
            return line
        # end of p0a
        elif isinstance(n, Is):
            return ' is '
        else:
            print(ast.dump(n, indent=4))
            raise Exception('***** Error: unrecognized AST node *****')
            
    # figure out how to make make_temp not just 99% copy of make_flattened_prog
    # because 99% of the lines do the same thing as make_flattened_prog, accept now instead
    # of appending to the file we just make a tmp variable and return that....so it's the same thing
    def make_temp(self, n):
        # p0
        if isinstance(n, BinOp):
            line = ''
            if self.check_instances(n.left):
                line += self.make_temp(n.left)
            else:
                line += self.make_flattened_prog(n.left)
            line += self.make_flattened_prog(n.op)
            if self.check_instances(n.right):
                line += self.make_temp(n.right)
            else:
                line += self.make_flattened_prog(n.right)
            self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return "tmp" + str(self.tmp_number-1)
        elif isinstance(n, UnaryOp):
            line = self.make_flattened_prog(n.op)
            if self.check_instances(n.operand):
                line += self.make_temp(n.operand)
            else:
                line += self.make_flattened_prog(n.operand)
            self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return "tmp" + str(self.tmp_number - 1)
        elif isinstance(n, Call):
            if n.func.id == 'eval':
                self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = eval(input())')
                self.tmp_number += 1
                self.variables.add('tmp' + str(self.tmp_number-1))
                return "tmp" + str(self.tmp_number - 1)
            if n.func.id in self.dont_flatten_args:
                for arg in n.args:
                    line += self.make_flattened_prog(arg)
                self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = ' + str(n.func.id) + "(" + line + ")")
                self.tmp_number += 1
                self.variables.add('tmp' + str(self.tmp_number-1))
                return "tmp" + str(self.tmp_number - 1)
            line = ''
            for arg in n.args:
                if self.check_instances(arg):
                    line += self.make_temp(arg) + ', '
                else:
                    line += self.make_flattened_prog(arg) + ', '
            if line[-2:] == ', ':
                line = line[:-2]
            self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = ' + str(n.func.id) + "(" + line + ")")
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return "tmp" + str(self.tmp_number - 1)
        # end of p0
        # p0a
        elif isinstance(n, BoolOp):
            line = ''
            if len(n.values) > 2:
                if self.check_instances(n.values[0]):
                    line += self.make_temp(n.values[0])
                else:
                    line += self.make_flattened_prog(n.values[0])
                line += self.make_flattened_prog(n.op)
                n.values = n.values[1:]
                line += self.make_temp(n)
            else:
                if self.check_instances(n.values[0]):
                    line += self.make_temp(n.values[0])
                else:
                    line += self.make_flattened_prog(n.values[0])
                line += self.make_flattened_prog(n.op)
                if self.check_instances(n.values[1]):
                    line += self.make_temp(n.values[1])
                else:
                    line += self.make_flattened_prog(n.values[1])
            self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return "tmp" + str(self.tmp_number - 1)
        elif isinstance(n, Compare):
            line = ''
            if self.check_instances(n.left):
                line += self.make_temp(n.left)
            else:
                line += self.make_flattened_prog(n.left)
            line += self.make_flattened_prog(n.ops[0])
            if self.check_instances(n.comparators[0]):
                line += self.make_temp(n.comparators[0])
            else:
                line += self.make_flattened_prog(n.comparators[0])
            self.flattened_program.append(self.indent + "tmp" + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return "tmp" + str(self.tmp_number - 1)
        elif isinstance(n, Subscript):
            line = ''
            if self.check_instances(n.value):
                line += self.make_temp(n.value)
            else:
                line += self.make_flattened_prog(n.value)
            line += '['
            if self.check_instances(n.slice):
                line += self.make_temp(n.slice)
            else:
                line += self.make_flattened_prog(n.slice)
            line += ']'
            self.flattened_program.append(self.indent + 'tmp' + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return 'tmp' + str(self.tmp_number-1)
        elif isinstance(n, List):
            line = ''
            for element in n.elts:
                if self.check_instances(element):
                    line += self.make_temp(element) + ', '
                else:
                    line += self.make_flattened_prog(element) + ', '
            line = '[' + line[:-2] + ']'
            self.flattened_program.append(self.indent + 'tmp' + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return 'tmp' + str(self.tmp_number-1)
        elif isinstance(n, Dict):
            line = ''
            for i in range(len(n.keys)):
                if self.check_instances(n.keys[i]):
                    line += self.make_temp(n.keys[i])
                else:
                    line += self.make_flattened_prog(n.keys[i])
                line += ': '
                if self.check_instances(n.values[i]):
                    line += self.make_temp(n.values[i])
                else:
                    line += self.make_flattened_prog(n.values[i])
                line += ', '
            line = '{' + line[:-2] + '}'
            self.flattened_program.append(self.indent + 'tmp' + str(self.tmp_number) + ' = ' + line)
            self.tmp_number += 1
            self.variables.add('tmp' + str(self.tmp_number-1))
            return 'tmp' + str(self.tmp_number-1)
        # end of p0a
        else:
            print(ast.dump(n, indent=4))
            raise Exception("***** unrecognized AST node make_temp *****")
            
    def get_variables(self):
        return self.variables
    
    def replace_variables(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, Name) and node.id not in self.reserved_names:
                node.id = "_" + node.id
            if isinstance(node, Constant) and node.value in [True, False]:
                node.value = 0 if node.value == False else 1
    
    def check_instances(self, n):
        for instance in self.flatten_instances:
            if isinstance(n, instance):
                return True
        return False