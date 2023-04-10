'''
        Need to uniquify the varibles and update the variables with its scope
        How? Implement using symbol table 
        All the current scope variables in one dict 
        Determine scope ? 
'''

import ast
from ast import *


## lets walk ast and record the scope for the function names, so that we can have it's scope for each function


class functionScope():
    def __init__(self):
        self.scope = -1
        self.func_scope = [] ## store the function variables in its current scope.
    
    ## we will do same old recursion or backtarck traversal 

    def find_func_scope(self, n):
        self.visit(n)
        return self.func_scope


    def visit(self, n, parent = None):
        if isinstance(n, Module):
            self.scope += 1
            self.func_scope.append(set([]))
            for node in n.body:
                self.visit(node)
            self.scope -= 1
        elif isinstance(n, Assign):
            lhs = self.visit(n.targets[0])
            ## target can be subscript
            if isinstance(n.value, Lambda):
                self.visit(n.value, lhs)

        elif isinstance(n, Expr):
            self.visit(n.value)

        elif isinstance(n, Constant):
            return 
        
        elif isinstance(n, Name):
            return n.id
        
        elif isinstance(n, BinOp):
            self.visit(n.left)
            self.visit(n.right)

        elif isinstance(n, UnaryOp):
            self.visit(n.operand)

        elif isinstance(n, Call):
            for arg in n.args:
                self.visit(arg)

        elif isinstance(n, Compare):
            self.visit(n.left)
            self.visit(n.comparators[0])

        elif isinstance(n, BoolOp):
            for node in n.values:
                self.visit(node)

        elif isinstance(n, If):
            self.visit(n.test)
            for node in n.body:
                self.visit(node)
            self.visit(n.orelse)
        elif isinstance(n , IfExp):
            self.visit(n.test)
            self.visit(n.body)
        elif isinstance(n, While):
            self.visit(n.test)
            for node in n.body:
                self.visit(node)
        elif isinstance(n, List):
            for node in n.elts:
                self.visit(node)
        elif isinstance(n, Dict):
            for i in range(len(n.keys)):
                self.visit(n.keys[i])
                self.visit(n.values[i])

        elif isinstance(n, Subscript):
            self.visit(n.value)
            self.visit(n.slice)


        ### Handle the funciton calls

        elif isinstance(n , FunctionDef):
            ## we are going to enter into new scope
            self.func_scope[self.scope].update(set([n.name]))
            
            self.scope += 1

            if self.scope <= len(self.func_scope): ## entering into new scope otherwise we would have process this scope don't create new 
                self.func_scope.append(set([]))

            for node in n.body:
                self.visit(node)

            self.scope -= 1

        elif isinstance(n, Lambda):
            if parent is not None:
                self.func_scope[self.scope].update(set([parent]))
            
            self.scope += 1
            if self.scope <= len(self.func_scope):
                self.func_scope.append(set([]))
            
           
            self.visit(n.body)

            self.scope -= 1

        elif isinstance(n, Return):
            self.visit(n.value)

## we need to  kind implement lookup table 
## we will store all the current scope variables in a list
## if the varible doesn't found in current look back in the previous scope lists
## To store scope list, stack would be a good data structure as we need to check in reverse
class Stack():
    def __init__(self):
        self.list = []

    def push(self, val):
        self.list.append(val)

    def pop(self):
        return self.list.pop()

    def get(self, index):
        return self.list[index]

    def top(self):
        return self.list[len(self.list)-1]

    def size(self):
        return len(self.list)
    
    def is_empty(self):
        return self.list == []


class Uniqufy():
    def __init__(self, func_lookup):
        self.uniqufied_ast = None
        self.func_lookup = func_lookup
        self.stack = Stack()


    def visit(self, n, parent = None):
        if isinstance(n, Module):
            self.stack.push(set([]))
            body = []
            for node in n.body:
                body.append(self.visit(node))
            self.uniqufied_ast = Module(body)
            self.stack.pop()
        elif isinstance(n, Assign):
            ### we need to check if the variable is already defined in the current scope ##
            ## if not then we need to add it to the current scope

        elif isinstance(n, Expr):
            return Expr(self.visit(n.value))

        elif isinstance(n, Constant):
            return Constant(n.value)
        
        elif isinstance(n, Name):
            return n.id
        
        elif isinstance(n, BinOp):
            return BinOp(self.visit(n.left), Add(), self.visit(n.right))

        elif isinstance(n, UnaryOp):
            return UnaryOp(n.op, self.visit(n.operand))

        elif isinstance(n, Call):
            return Call(Name(n.func), [self.visit(arg) for arg in n.args], [])

        elif isinstance(n, Compare):
            return Compare(self.visit(n.left), n.ops, self.visit(n.comparators[0]))

        elif isinstance(n, BoolOp):
            return BoolOp(n.op, [self.visit(node) for node in n.values])

        elif isinstance(n, If):
            return If(self.visit(n.test), [self.visit(node) for node in n.body], self.visit(n.orelse))
        
        elif isinstance(n , IfExp):
            return IfExp(self.visit(n.test), self.visit(n.body), self.visit(n.orelse))
           
        elif isinstance(n, While):
            return While(self.visit(n.test), [self.visit(node) for node in n.body])
           
        elif isinstance(n, List):
            return List([self.visit(node) for node in n.elts])
        
        elif isinstance(n, Dict):
            dict = []
            for i in range(len(n.keys)):
                dict.append((self.visit(n.keys[i]), self.visit(n.values[i])))
            return Dict(dict)

        elif isinstance(n, Subscript):
            return Subscript(self.visit(n.value), self.visit(n.slice))
          

        ### Handle the funciton calls

        elif isinstance(n , FunctionDef):
            ## we are going to enter into new scope
            pass

        elif isinstance(n, Lambda):
            pass

        elif isinstance(n, Return):
            return Return(self.visit(n.value))

def uniquify_vars(self, n):
    f = functionScope()
    func_scope_list =  f.find_func_scope(n)
    uniquify = Uniqufy(func_scope_list)
    uniquifed_ast = uniquify.visit(n)

