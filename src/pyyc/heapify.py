import sys
import ast
from ast import *

class Heapify:
    def __init__(self, print_heapified_ast, functions):
        self.print_ast = print_heapified_ast
        self.free_variables = []
        self.reserved_names = ['print', 'eval', 'input', 'int', 'is_int', 'unbox_int', 
                               'box_int', 'box_bool', 'unbox_bool', 'is_bool', 'box_big', 'unbox_big',
                              'create_list', 'set_subscript', 'create_dict', 'equal', 'is_big',
                              'get_subscript', 'is_true', 'add', 'not_equal', 'TypeError']
        self.functions = functions
        
    def heapify(self, uniquified_ast):
        heapified_ast = uniquified_ast
        self.make_parents(heapified_ast)
        
        for node in ast.walk(heapified_ast):
            #print(ast.dump(node))
            if hasattr(node, 'parent'):
                pass
                #print(ast.dump(node))
                #print(str(type(node)) + " parent: " + str(node.parent))
            else:
                print('Error: no parent')
                print(str(type(node)))
        
        
        for node in ast.walk(heapified_ast):
            if isinstance(node, FunctionDef):
                self.bound_variables = []
                #print(node.args.args)
                for arg in node.args.args:
                    self.bound_variables.append(arg.arg)
                #print(ast.dump(node.args, indent=4))
                for var in ast.walk(node):
                    if isinstance(var, Name):
                        if isinstance(var.ctx, Store):
                            self.bound_variables.append(var.id)
                
                for var in ast.walk(node):
                    if isinstance(var, Name):
                        if isinstance(var.ctx, Load):
                            if not var.id in self.bound_variables and not var.id in self.reserved_names  and not var.id in self.functions:
                                self.free_variables.append(var.id)
                '''
                print('----- function def node -----')
                #print(ast.dump(node, indent=4))
                print(node.name)
                '''
                print('----- bound variables -----')
                print(self.bound_variables)
                
                
        print('----- free variables -----')
        self.free_variables = set(self.free_variables)
        print(self.free_variables)
        
        #print(ast.dump(heapified_ast, indent=4))
        
        '''
        for change in ast.walk(uniquified_ast):
            if isinstance(change, Name):
                if isinstance(change.ctx, Load):
                    if change.id in self.free_variables:
                        print('----- changing -----')
                        print(ast.dump(change, indent=4))
                        change.id = change.id + '_ptr'
                        change = Subscript(change, Constant(0), Load())
                        print(ast.dump(change, indent=4))
        
        for change in ast.walk(heapified_ast):
            if isinstance(change, Name):
                if isinstance(change.ctx, Load):
                    if change.id in self.free_variables:
                        change.id = change.id + '_ptr'
                        #change = 'soahfdhafo'
                        #print(ast.dump(change, indent=4))
                        #mkSub = MakeSubscript()
                        #mkSub.visit_Name(change)
                        #change = ast.copy_location(Subscript(change, Constant(0), Load()), node)
                        #change = Subscript(change, Constant(0), Load())
                        #print(ast.dump(change, indent=4))
        '''
        heapified_ast = RewriteName(self.free_variables).visit(heapified_ast)
        
        if(self.print_ast):
            print(heapified_ast)
        return heapified_ast
        
    def make_parents(self, node, parent=None):
        node.parent = parent
        if isinstance(node, Module):
            for n in node.body:
                self.make_parents(n, node)
        elif isinstance(node, Assign):
            self.make_parents(node.targets[0], node)
            self.make_parents(node.value, node)
        elif isinstance(node, Expr):
            self.make_parents(node.value, node)
        elif isinstance(node, Name):
            self.make_parents(node.ctx, node)
        elif isinstance(node, BinOp):
            self.make_parents(node.left, node)
            self.make_parents(node.op, node)
            self.make_parents(node.right, node)
        elif isinstance(node, UnaryOp):
            self.make_parents(node.operand, node)
            self.make_parents(node.op, node)
        elif isinstance(node, Call):
            self.make_parents(node.func, node)
            for n in node.args:
                self.make_parents(n, node)
        elif isinstance(node, BoolOp):
            for n in node.values:
                self.make_parents(n, node)
            self.make_parents(node.op, node)
        elif isinstance(node, Compare):
            self.make_parents(node.left, node)
            for n in node.ops:
                self.make_parents(n, node)
            for n in node.comparators:
                self.make_parents(n, node)
        elif isinstance(node, If):
            self.make_parents(node.test, node)
            for n in node.body:
                self.make_parents(n, node)
            for n in node.orelse:
                self.make_parents(n, node)
        elif isinstance(node, IfExp):
            self.make_parents(node.test, node)
            self.make_parents(node.body, node)
            self.make_parents(node.orelse, node)
        elif isinstance(node, While):
            self.make_parents(node.test, node)
            for n in node.body:
                self.make_parents(n, node)
        elif isinstance(node, List):
            for n in node.elts:
                self.make_parents(n, node)
        elif isinstance(node, Dict):
            for n in node.keys:
                self.make_parents(n, node)
            for n in node.values:
                self.make_parents(n, node)
        elif isinstance(node, Subscript):
            self.make_parents(node.value, node)
            self.make_parents(node.slice, node)
        elif isinstance(node, FunctionDef):
            self.make_parents(node.args, node)
            for n in node.body:
                self.make_parents(n, node)
        elif isinstance(node, Return):
            if node.value:
                self.make_parents(node.value, node)
            
class RewriteName(ast.NodeTransformer):
    def __init__(self, free_vars):
        self.free_variables = free_vars
        
    def visit_Name(self, node):
        if node.id in self.free_variables:
            if isinstance(node.ctx, Load):
                node.id = node.id + '_ptr'
                return ast.copy_location(Subscript(node, Constant(0), Load()), node)
        return node
    
    def visit_Assign(self, node):
        if isinstance(node.targets[0], Name) and node.targets[0].id in self.free_variables:
            node.targets[0].id = node.targets[0].id + '_ptr'
            #print(ast.dump(node, indent=4))
            node.value = List([node.value], Load())
            return node
        elif not isinstance(node.targets[0], Name):
            print("***** visit names heapify not Name *****")
            return node
        return node