
import ast
from ast import *
from helper import *

class Unify():
    def __init__(self, functions):
       self.unified_ast = None
       self.lambda_converted_function = []
       self.functions = functions
       self.replace_vars = {}

    def get_unified_ast(self, n):
        self.visit(n)
        return self.unified_ast, self.functions
    

    def visit(self, n):
        ## Traversing the AST AND remove the redundant nodes and convert the lambdas to funcion
        ## that's the intution of this function
        ## for now converting assigned lambda to function, Do we need to more ? check with kelly

        if isinstance(n, Module):
            body = []
            for node in n.body:
                if self.visit(node):
                    body.append(self.visit(node))
            self.unified_ast = Module(body, n.type_ignores)
            ## jUST ADD ALL THE LAMBDA CONVERTED FUNCTION TO THE START OF THE AST
            self.unified_ast.body = self.lambda_converted_function + self.unified_ast.body
            
        if isinstance(n, Assign):
            print("Assign statement")
            if isinstance(n.value, Lambda):
                if 'unique_lambda' in n.targets[0].id:
                    self.lambda_converted_function.append(FunctionDef(n.targets[0].id, n.value.args, n.value.body, [], None))
                    return None
                else:
                    
                    var = tempVar("unique_lambda")
                    print("chekcing", var, n.targets[0].id)
                    self.functions.add(var)
                    self.lambda_converted_function.append(FunctionDef(var, n.value.args, n.value.body, [], None))	
                    self.replace_vars[n.targets[0].id]=var
                    return None
                    # body.append(Assign(node.targets,  Call(Name(var, Load()), [Name(self.visit(arg.arg), Load()) for arg in node.value.args.args], [])))
            else:
                return n

        if isinstance(n, FunctionDef):
            body = []
            for node in n.body:
                print("checking ast node", ast.dump(node, indent = 4))
                if isinstance(node, Assign):
                    if isinstance(node.value, Lambda):
                        if 'unique_lambda' in node.targets[0].id:
                            self.lambda_converted_function.append(FunctionDef(node.targets[0].id, node.value.args, node.value.body, [], None))
                        else:
                            var = tempVar("unique_lambda")
                            self.functions.add(var)
                            self.lambda_converted_function.append(FunctionDef(var, node.value.args, node.value.body, [], None))	
                            body.append(Assign(node.targets,  Call(Name(var, Load()), [Name(self.visit(arg.arg), Load()) for arg in node.value.args.args], [])))
                    else:
                        body.append(self.visit(node))
                else:
                    body.append(self.visit(node))
            return FunctionDef(n.name, n.args, body, n.decorator_list, n.returns)
        ## for remaining all instances just return the node
        elif isinstance(n, Expr):
            return Expr(self.visit(n.value))
        elif isinstance(n, Call):
            if n.func.id in self.replace_vars.keys():
                return Call(Name(self.replace_vars[n.func.id], Load()), [self.visit(arg) for arg in n.args])
            else:
                return Call(Name(n.func.id, Load()), [self.visit(arg) for arg in n.args])
        
        else:
            return n

        
