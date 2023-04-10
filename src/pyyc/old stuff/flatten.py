import sys
import ast
from ast import *
from myParser import MyParser


class Flatten:

    # flatten stuff from exercise 1.6
    # global variable for what tmp currently is
    global tmp
    tmp = 0 
    # this function makes an AST from a file name
    def make_tree_from_file(self, parser, temp_file):
        # load the file into a string
        temp_prog = ''
        with open(temp_file) as f:
            temp_prog = f.read()
        # use ast.parse to make string file
        parser.parseInput(temp_prog)
        #temp_tree = ast.parse(temp_prog)
        temp_tree = parser.parseInput(temp_prog)
        # pring the python program
        #print(temp_prog)
        # return the ast
        return temp_tree

    def get_variables_list(self, n):
        # Name nodes by walk
        variables = set()
        for node in ast.walk(n):
            if isinstance(node, Name):
                if node.id == 'print' or node.id == 'input' or node.id == 'eval':
                    continue
                variables.add(node.id)
        return list(variables)

        

    # function you call to flatten stuff
    # takes in a tree and a string list and makes that string list
    # a flattened program
    # does so through recursion
    def flatten(self, n, prog):
        # define tmp again so it doesn't mess up
        global tmp
        # if module, loop through all children and flatten them
        if isinstance(n, Module):
            tmp = 0
            for node in n.body:
                self.flatten(node, prog)
        # if we are assign, don't do much just flatten left and right side
        # assigns are a line so also append that to our program
        elif isinstance(n, Assign):
            line = ''
            line += self.flatten(n.targets[0], prog)
            line += ' = '
            line += self.flatten(n.value, prog)
            prog.append(line)
        # expr is simple, just flatten it and append our expression to our list of strings
        elif isinstance(n, Expr):
            prog.append(self.flatten(n.value, prog))
        # return the constant value
        elif isinstance(n, Constant):
            return str(n.value)
        # return a name + underscore so program variables don't mess with us
        elif isinstance(n, Name):
            return n.id
        # if BinOp we need to check if left or right are something we
        # need to flatten, if so call our helper that does that for us
        elif isinstance(n, BinOp):
            # if left or right is op do a thing
            line = ''
            if isinstance(n.left, BinOp) or isinstance(n.left, UnaryOp) or isinstance(n.left, Call):
                line += self.flatten_helper(n.left, prog)
            else:
                line += self.flatten(n.left, prog)
            line += self.flatten(n.op, prog)
            if isinstance(n.right, BinOp) or isinstance(n.right, UnaryOp) or isinstance(n.right, Call):
                line += self.flatten_helper(n.right, prog)
            else:
                line += self.flatten(n.right, prog)
            return line
        # same as BinOp
        elif isinstance(n, UnaryOp):
            # if op do a thing
            line = ''
            line += self.flatten(n.op, prog)
            if isinstance(n.operand, UnaryOp) or isinstance(n.operand, BinOp) or isinstance(n.operand, Call):
                line += self.flatten_helper(n.operand, prog)
            else:
                line += self.flatten(n.operand, prog)
            return line
        # call is weird, flatten all of our arguments and call the boy
        elif isinstance(n, Call):
            # if arg[0] is op do a thing
            line = ''
            if n.func.id == 'eval':
                return "eval(input())"
            for arg in n.args:
                if isinstance(arg, BinOp) or isinstance(arg, UnaryOp) or isinstance(arg, Call):
                    line += self.flatten_helper(arg, prog)
                else:
                    line += self.flatten(arg, prog)
            return str(n.func.id) + "(" + line + ")"
        # these are just add some correct symbols
        elif isinstance(n, Add):
            return ' + '
        elif isinstance(n, USub):
            return '-'
        elif isinstance(n, Load):
            return
        elif isinstance(n, Store):
            return
        else:
            raise Exception('Error: unrecognized AST node')

    # this is a helper, when called we've decided that this node
    # needs to be simpler, so make a simpler version of yourself
    def flatten_helper(self, node, prog):
        # make sure we reference tmp
        global tmp
        # if a binOp then flatten your left and right also
        if isinstance(node, BinOp):
            line = ''
            if isinstance(node.left, BinOp) or isinstance(node.left, UnaryOp) or isinstance(node.left, Call):
                line += self.flatten_helper(node.left, prog)
            else:
                line += self.flatten(node.left, prog)
            line += self.flatten(node.op, prog)
            if isinstance(node.right, BinOp) or isinstance(node.right, UnaryOp) or isinstance(node.right, Call):
                line += self.flatten_helper(node.right, prog)
            else:
                line += self.flatten(node.right, prog)
            prog.append("tmp" + str(tmp) + " = " + line)
            tmp += 1
            return "tmp" + str(tmp-1)
        # do same as BinOP
        elif isinstance(node, UnaryOp):
            line = ''
            line += self.flatten(node.op, prog)
            if isinstance(node.operand, BinOp) or isinstance(node.operand, UnaryOp) or isinstance(node.operand, Call):
                line += self.flatten_helper(node.operand, prog)
            else:
                line += self.flatten(node.operand, prog)
            prog.append("tmp" + str(tmp) + " = " + line)
            tmp += 1
            return "tmp" + str(tmp-1)
        # call also needs to be flattened if it was called in the middle of something
        elif isinstance(node, Call):
            line = ''
            if node.func.id == 'eval':
                prog.append("tmp" + str(tmp) + " = eval(input())")
                tmp += 1
                return "tmp" + str(tmp-1)
            for arg in node.args:
                if isinstance(arg, BinOp) or isinstance(arg, UnaryOp):
                    line += self.flatten_helper(arg, prog)
                else:
                    line += self.flatten(arg, prog)
            prog.append("tmp" + str(tmp) + " = " + str(node.func.id) + "(" + line + ")")
            tmp += 1
            return "tmp" + str(tmp-1)
        else:
            raise Exception('Error: operation not passed')
        
    # this is the function that is called to flatten a file
    # takes in a file name and returns a list of strings
    def flatten_file(self, file_name):
        parser = MyParser()
        old_tree = self.make_tree_from_file(parser, file_name)
        #print(ast.dump(old_tree, indent = 4))
        flattened_prog = []
        self.flatten(old_tree, flattened_prog)
        tree_prog = ''
        for line in flattened_prog:
            if(line == 'eval(input())'):
                break;
            tree_prog += line + "\n"

        ### write the flattened program to a file.
        with open(file_name.replace('.py', '.flatpy'), 'w') as f:
            f.write(tree_prog)

        print('Flattened Program:')
        print(tree_prog)

        ## parse the flattend program to new AST

        new_tree = parser.parseInput(tree_prog)

        #print("Flattened AST:")
        #print(ast.dump(new_tree, indent = 4))

        return new_tree
