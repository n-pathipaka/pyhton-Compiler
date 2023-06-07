'''
        Need to uniquify the varibles and update the variables with its scope
        How? Implement using symbol table 
        All the current scope variables in one dict 
        Determine scope ? 
'''

import ast
from ast import *
from helper import *
from unify import Unify

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
        self.lambda_converted_assign = []
        self.stack = Stack()
        self.reserved_names = ['print', 'eval', 'input', 'int', 'is_int', 'unbox_int', 
                               'box_int', 'box_bool', 'unbox_bool', 'is_bool', 'box_big', 'unbox_big',
                              'create_list', 'set_subscript', 'create_dict', 'equal', 'is_big',
                              'get_subscript', 'is_true', 'add', 'not_equal', 'TypeError']
        self.function_list = set()
    
    def get_uniqufied_ast(self, n):
        self.visit(n)
        print("all the functions;", self.function_list)
        return self.uniqufied_ast, self.function_list

    def visit(self, n, parent = None):
        if isinstance(n, Module):
            self.stack.push(set([]))  ## stack is used to push the current scope variables
            ## As per the recommendatin we need to convert lambda to func def
            ## we need to convert the lambda in return statment of function def to assign statement, so we store  that values the lambda converted list and we assign it to some global variable
            self.lambda_converted_assign.append([])
            body = []
            for node in n.body:
                body.append(self.visit(node))
            self.uniqufied_ast = Module(body, n.type_ignores)
            self.lambda_converted_assign.pop()
            self.stack.pop()
        elif isinstance(n, Assign):
             ## uniquify this target varible 
            lhs = self.visit(n.targets[0])
            ## if the value is lambda send it's parent, so should keep as it is
            if isinstance(n.value, Lambda):
                print('sending parent as assign')
                rhs = self.visit(n.value, "Assign")
            else:
                rhs = self.visit(n.value)
            return Assign([lhs], rhs)

        elif isinstance(n, Expr):
            return Expr(self.visit(n.value))

        elif isinstance(n, Constant):
            return Constant(n.value)
        
        elif isinstance(n, Name):
            var = n.id
            current_scope = self.stack.size()-1
            found = False
            for i in range(current_scope, -1, -1):
                if var in self.stack.get(i):
                    var = var + '_' + str(i)
                    found = True
                    break
            if not found:  ## if not found in the current scope then check in the function name
                for i in range(current_scope, -1, -1):
                    if var in self.func_lookup[i]:
                        var = var + '_' + str(i)
                        found = True
                        self.function_list.add(var)
                        break
            if not found: ## yet to see in the variable name
                self.stack.top().update(set([var]))
                var = var + '_' + str(current_scope)

            return Name(var, n.ctx) ## return the uniquified name ## return the uniquified name
        
        elif isinstance(n, BinOp):
            return BinOp(self.visit(n.left), Add(), self.visit(n.right))

        elif isinstance(n, UnaryOp):
            return UnaryOp(n.op, self.visit(n.operand))

        elif isinstance(n, Call):
            var = n.func.id
            if var not in self.reserved_names:
                current_scope = self.stack.size()-1
                for i in range(current_scope, -1, -1):
                    if var in self.func_lookup[i]:
                        var = var + '_' + str(i)
                        self.function_list.add(var)
                        break
            return Call(Name(var, n.func.ctx), [self.visit(arg) for arg in n.args], [])

        elif isinstance(n, Compare):
            return Compare(self.visit(n.left), n.ops, [self.visit(n.comparators[0])])

        elif isinstance(n, BoolOp):
            return BoolOp(n.op, [self.visit(node) for node in n.values])

        elif isinstance(n, If):
            return If(self.visit(n.test), [self.visit(node) for node in n.body], [self.visit(node) for node in n.orelse])
        
        elif isinstance(n , IfExp):
            return IfExp(self.visit(n.test), self.visit(n.body), self.visit(n.orelse))
           
        elif isinstance(n, While):
            return While(self.visit(n.test), [self.visit(node) for node in n.body])
           
        elif isinstance(n, List):
            return List([self.visit(node) for node in n.elts])
        
        elif isinstance(n, Dict):
            dict = []
            keys = []
            values = []
            for i in range(len(n.keys)):
                keys.append(self.visit(n.keys[i]))
                values.append(self.visit(n.values[i]))
            return Dict(keys = keys, values = values)

        elif isinstance(n, Subscript):
            return Subscript(self.visit(n.value), self.visit(n.slice))
          

        ### Handle the funciton calls

        elif isinstance(n , FunctionDef):
            ## we are going to enter into new scope
            current_scope = self.stack.size()-1
            f_id = n.name + '_' + str(current_scope)
            self.stack.top().update(set([f_id]))
            ## push empty set to the stack ## this is the scope of the function
            self.stack.push(set([]))
            self.lambda_converted_assign.append([])
            current_scope = self.stack.size()-1
            ## we need to uniquify the arguments
            args = []
            for arg in n.args.args:
                self.stack.top().update(set([arg.arg]))
                arg_name = arg.arg + '_' + str(current_scope)
                arg.arg = arg_name
                args.append(arg)
            n.args.args = args

            ## we need to uniquify the body
            body = [self.visit(node) for node in n.body]
            ## we have converted the lambda to assign just add it to the body
            body = self.lambda_converted_assign[current_scope] + body

            ## pop the function scope
            self.lambda_converted_assign.pop()
            self.stack.pop()
            return FunctionDef(f_id, n.args , body, [])

        elif isinstance(n, Lambda):
            ## we are going to enter into new scope
            ## push empty set to the stack ## this is the scope of the function
            self.stack.push(set([]))
            self.lambda_converted_assign.append([])

            current_scope = self.stack.size()-1
            
            ## we need to uniquify the arguments
            args = []
            for arg in n.args.args:
                self.stack.top().update(set([arg.arg]))
                arg_name = arg.arg + '_' + str(current_scope)
                arg.arg = arg_name
                args.append(arg)
            
            n.args.args = args
            ## we are convertign to lambda to functions so, need to return the body statment

            body = [Return(self.visit(n.body))]
            
            if len(self.lambda_converted_assign[current_scope]) > 0:
                 body = self.lambda_converted_assign[current_scope] + body

            ## we will whether the lambda is from return or assign
            ret_lambda =  Lambda(n.args , body)
            if not parent == "Assign":
                var = tempVar('unique_lambda')
                self.lambda_converted_assign[current_scope-1].append(Assign([Name(var)], ret_lambda))
                ret_lambda = Name(var)
            else:
                var = tempVar('unique_lambda')
                self.lambda_converted_assign[current_scope-1].append(ret_lambda)
            

            ## pop the function scope
            self.stack.pop()
            self.lambda_converted_assign.pop()
            return ret_lambda

        elif isinstance(n, Return):
            return Return(self.visit(n.value))

def uniquify_vars(n, print_asts):
    f = functionScope()
    func_scope_list =  f.find_func_scope(n)
    uniquify = Uniqufy(func_scope_list)
    uniquifed_ast, functions = uniquify.get_uniqufied_ast(n)
    if print_asts:
        print("UNiquifed AST:")
        print(ast.dump(uniquifed_ast, indent=4))
    unify = Unify(functions)
    unified_ast, functions = unify.get_unified_ast(uniquifed_ast)
    print("All the funcitons", functions)
    if print_asts:
        print("Unified AST:")
        print(ast.dump(unified_ast, indent=4))
    return unified_ast, functions


