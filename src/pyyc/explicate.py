import sys
import ast
from ast import *
from parse import Parser
from helper import tempVar

class Explicate:
    def __init__(self, print_explicate):
        self.print_explicate = print_explicate
        self.tmp = -1
        self.exp_ast = Module([], [])
        self.needs_exp = [BinOp, Constant, UnaryOp, BoolOp, Compare, List, Dict, Subscript]
        self.func_exp = ['int']
        self.has_body = [If, While, FunctionDef]
        
    def explicate(self, flattened_ast):
        print('----- explicate -----')
        self.exp(flattened_ast)
        if self.print_explicate:
            #pass
            print(ast.dump(self.exp_ast, indent=4))
        print('----- out of explicate -----')
        return self.exp_ast
    
    def exp(self, n, var=None, parent=None, weird=False):
        if isinstance(n, Module):
            for node in n.body:
                self.exp(node)
        elif self.check_instances(n, self.has_body):
            #print(ast.dump(n, indent=4))
            save_ast = self.exp_ast
            body = n.body
            n.body = []
            ##print(ast.dump(n, indent=4))
            if(hasattr(n, 'test')):
                n.test = Call(Name('is_true', Load()), [ Name(id=n.test.id, ctx=Load())])
            self.exp_ast = n
            for node in body:
                self.exp(node)
            if isinstance(n, If):
                body_ast = self.exp_ast
                self.exp_ast = Module([], [])
                for node in n.orelse:
                    self.exp(node)
                body_ast.orelse = self.exp_ast.body
                self.exp_ast = body_ast
            save_ast.body.append(self.exp_ast)
            self.exp_ast = save_ast
        elif isinstance(n, Assign):
            if self.check_instances(n.value, self.needs_exp):
                self.exp(n.value, n.targets[0].id, n)
            elif isinstance(n.value, Call):# and n.value.func.id in self.func_exp:
                self.exp(n.value, n.targets[0].id, n)
            elif isinstance(n.targets[0], Subscript):
                self.exp(n.targets[0], parent=n, weird=True)
            else:
                self.exp_ast.body.append(n)
        elif isinstance(n, Expr):
            self.exp(n.value, parent=n)
        elif isinstance(n, BinOp):
            if isinstance(n.left, Constant) and isinstance(n.right, Constant):
                #self.exp_ast.body.append(assign)
                self.binop_constants(var, str(n.left.value), str(n.right.value))
            elif isinstance(n.left, Name) and isinstance(n.right, Name):
                self.binop_type_check(var, n.left.id, n.right.id, tempVar('exp_tmp'), tempVar('exp_tmp'))
            elif isinstance(n.left, Name) and isinstance(n.right, Constant):
                self.binop_type_check(var, n.left.id, 'box_int(' + str(n.right.value) + ')', tempVar('exp_tmp'), tempVar('exp_tmp'))
            elif isinstance(n.left, Constant) and isinstance(n.right, Name):
                self.binop_type_check(var, 'box_int(' + str(n.left.value) + ')', n.right.id, tempVar('exp_tmp'), tempVar('exp_tmp'))
            else:
                print('***** binop no more else *****')
        elif isinstance(n, UnaryOp):
            op = ''
            if isinstance(n.op, USub):
                op = '-'
            elif isinstance(n.op, Not):
                op = 'not '
            if isinstance(n.operand, Constant):
                self.box_constant(var, op + str(n.operand.value))
            elif isinstance(n.operand, Name):
                self.unary_type_check(var, n.operand.id, op)
            else:
                print('***** unaryop no more else *****')
        elif isinstance(n, Constant):
            self.box_constant(var, n.value)
        elif isinstance(n, Call):
            if n.func.id in self.func_exp and isinstance(n.args[0], Name):
                self.unbox_func(var, n.func.id, n.args[0].id)
                return
            '''
            if n.func.id == 'print' and isinstance(n.args[0], Constant):
                target = self.make_tmp()
                self.box_constant(target, n.args[0].value)
                n.args[0] = Name(target, Load())
                parent.value = n
            '''
                
            for i in range(len(n.args)):
                if isinstance(n.args[i], Constant):
                    target = self.make_tmp()
                    self.box_constant(target, n.args[i].value)
                    n.args[i] = Name(target, Load())
                    parent.value = n
            self.exp_ast.body.append(parent)
        elif isinstance(n, BoolOp):
            if isinstance(n.values[0], Constant) and isinstance(n.values[1], Constant):
                if isinstance(n.op, And):
                    self.bool_constants(var, str(n.values[0].value), str(n.values[1].value), 'and')
                elif isinstance(n.op, Or):
                    self.bool_constants(var, str(n.values[0].value), str(n.values[1].value), 'or')
            elif isinstance(n.values[0], Name) and isinstance(n.values[1], Name):
                if isinstance(n.op, And):
                    self.bool_type_check(var, n.values[0].id, n.values[1].id, 'and')
                elif isinstance(n.op, Or):
                    self.bool_type_check(var, n.values[0].id, n.values[1].id, 'or')
            elif isinstance(n.values[0], Name) and isinstance(n.values[1], Constant):
                op = ''
                if isinstance(n.op, And):
                    op = 'and'
                if isinstance(n.op, Or):
                    op = 'or'
                self.bool_type_check(var, n.values[0].id, 'box_int(' + str(n.values[1].value) + ')', op)
            elif isinstance(n.values[0], Constant) and isinstance(n.values[1], Name):
                op = ''
                if isinstance(n.op, And):
                    op = 'and'
                if isinstance(n.op, Or):
                    op = 'or'
                self.bool_type_check(var, 'box_int(' + str(n.values[0].value) + ')', n.values[1].id, op)
            else:
                print('***** boolop no more else *****')
        elif isinstance(n, Compare):
            op = ''
            if isinstance(n.ops[0], Eq):
                op = '=='
            elif isinstance(n.ops[0], NotEq):
                op = '!='
            elif isinstance(n.ops[0], Is):
                if isinstance(n.left, Name) and isinstance(n.comparators[0], Name):
                    self.cmp_is(var, n.left.id, n.comparators[0].id)
                else:
                    self.cmp_is_false(var)
                return
                
            if isinstance(n.left, Constant) and isinstance(n.comparators[0], Constant):
                self.cmp_constants(var, str(n.left.value), str(n.comparators[0].value), op)
            elif isinstance(n.left, Name) and isinstance(n.comparators[0], Name):
                self.cmp_type_check(var, n.left.id, n.comparators[0].id, op)
            elif isinstance(n.left, Name) and isinstance(n.comparators[0], Constant):
                self.cmp_type_check(var, n.left.id, 'box_int(' + str(n.comparators[0].value) +')', op)
            elif isinstance(n.left, Constant) and isinstance(n.comparators[0], Name):
                self.cmp_type_check(var, 'box_int(' + str(n.left.value) + ')', n.comparators[0].id, op)
            else:
                print('***** compare no more else *****')
        elif isinstance(n, List):
            self.create_list(len(n.elts), var, n.elts)
        elif isinstance(n, Dict):
            self.create_dict(var, n.keys, n.values)
        elif isinstance(n, Subscript):
            if weird:
                self.set_subscript(n.value, n.slice, parent.value)
            else:
                self.get_subscript(var, n.value, n.slice)
        elif isinstance(n, Return):
            if isinstance(n.value, Constant):
                self.append_code('return box_int(' + str(n.value.value) + ')')
            else:
                self.exp_ast.body.append(n)
        else:
            print('***** da f*** is this *****')
            print(ast.dump(n, indent=4))
            self.exp_ast.body.append(n)
            
    def set_subscript(self, target, key, value):
        code = r"""
set_subscript(target, key, value)     
"""
        #print(target)
        #print(key)
        #print(value)
        if isinstance(key, Constant):
            code = code.replace('key', 'box_int(' + str(key.value) + ')')
        else:
            code = code.replace('key', key.id)
        if isinstance(value, Constant):
            code = code.replace('value', 'box_int(' + str(value.value) + ')')
        else:
            code = code.replace('value', value.id)
        code = code.replace('target', target.id)
        self.append_code(code)
        
        
    def get_subscript(self, target, obj, index):
        if isinstance(index, Name):
            index = index.id
        code = r"""
target = get_subscript(obj, index)
"""
        if isinstance(index, Constant):
            index = 'box_int(' + str(index.value) + ')'
        code = code.replace('target', target).replace('obj', obj.id).replace('index', index)
        self.append_code(code)
            
    def create_dict(self, target, keys, values):
        code = r"""
target = box_big(create_dict())     
"""
        for i in range(len(keys)):
            key = keys[i]
            val = values[i]
            code += '\nset_subscript(target, key, val)'
            #print(key)
            #print(val)
            if isinstance(key, Constant):
                code = code.replace('key', 'box_int(' + str(key.value) + ')')
            else:
                code = code.replace('key', key.id)
            if isinstance(val, Constant):
                code = code.replace('val', 'box_int(' + str(val.value) + ')')
            else:
                code = code.replace('val', val.id)
            #if isinstance(key, Constant) and isinstance(val, Constant):
            #    code = code.replace('key', 'box_int(' + str(key.value) + ')').replace('val', 'box_int(' + str(val.value) + ')')
            #elif isinstance(key, Name) and isinstance(val, Name):
            #    code = code.replace('key', key.id).replace('val', val.id)
            
        
        code = code.replace('target', target)
        self.append_code(code)
            
            
    def create_list(self, length, target, nodes):
        code =  r"""
target = box_big(create_list(box_int(length)))
"""
        #print('++++++')
        #print(code)
        
        #print('++++++')
        #print(code)
        for i in range(len(nodes)):
            node = nodes[i]
            code += '\nset_subscript(target, key, val)'
            if isinstance(node, Constant):
                code = code.replace('key', 'box_int(' + str(i) + ')').replace('val', 'box_int(' + str(node.value) + ')')
            elif isinstance(node, Name):
                code = code.replace('key', 'box_int(' + str(i) + ')').replace('val', node.id)
            #print('++++++')
            #print(code)
        code = code.replace('target', target).replace('length', str(length))
        self.append_code(code)
        
    def cmp_is_false(self, target):
        code = r"""
target = box_bool(0)     
"""
        code = code.replace('target', target)
        self.append_code(code)
        
    def cmp_is(self, target, left, right):
        code = r"""
if(is_big(left)):
    if(is_big(right)):
        target = box_bool(equal(unbox_big(left), unbox_big(right)))
    else:
        target = box_bool(0)
else:
    target = box_bool(0)
"""
        code = code.replace('target', target).replace('left', left).replace('right', right)
        self.append_code(code)
    
    def cmp_type_check(self, target, v1, v2, op):
        print("checking the variables:", target, v1, v2)
        code = r"""
if(is_int(v1)):
    if(is_int(v2)):
        target = box_bool(unbox_int(v1) op unbox_int(v2))
    elif(is_bool(v2)):
        target = box_bool(unbox_int(v1) op unbox_bool(v2))
    else:
        if(1 op 1):
            target = box_bool(0)
        else:
            target = box_bool(1)
elif(is_bool(v1)):
    if(is_int(v2)):
        target = box_bool(unbox_bool(v1) op unbox_int(v2))
    elif(is_bool(v2)):
        target = box_bool(unbox_bool(v1) op unbox_bool(v2))
    else:
        if(1 op 1):
            target = box_bool(0)
        else:
            target = box_bool(1)
else:
    if(is_int(v2)):
        target = box_bool(is_true(v1) op unbox_int(v2))
    elif(is_bool(v2)):
        target = box_bool(is_true(v1) op unbox_bool(v2))
    else:
        if(1 op 1):
            target = box_bool(equal(unbox_big(v1), unbox_big(v2)))
        else:
            target = box_bool(not_equal(unbox_big(v1), unbox_big(v2)))   
"""
        code = code.replace('target', target).replace('v2', v2).replace('op', op).replace('v1', v1)
   
        self.append_code(code)
            
    def unbox_func(self, target, function, value):
        code = r"""
if(is_int(value)):
    target = function(unbox_int(value))
elif(is_bool(value)):
    target = function(unbox_bool(value))
else:
    target = function(unbox_big(value))
"""
        code = code.replace('target', target).replace('function', function).replace('value', value)
        self.append_code(code)
    
    def cmp_constants(self, target, v1, v2, op):
        code = r"""
target = box_bool(v1 op v2)
"""
        
        code = code.replace('target', target).replace('v1', v1).replace('v2', v2).replace('op', op)
        self.append_code(code)
        
    def bool_constants(self, target, v1, v2, op):
        code = r"""
target = box_int(v1 op v2)
"""
                                    
        code = code.replace('target', target).replace('v1', v1).replace('v2', v2).replace('op', op)
        self.append_code(code)
        
    def bool_type_check(self, target, v1, v2, op):
        code = r"""
if(is_int(v1)):
    if(is_int(v2)):
        target = box_int(unbox_int(v1) op unbox_int(v2))
    elif(is_bool(v2)):
        target = box_int(unbox_int(v1) op unbox_int(v2))
    else:
        exp1 = unbox_int(v1)
        exp2 = is_true(v2)
        if(exp1 op exp2):
            if(exp2):
                target = v2
            else:
                target = v1
        else:
            if(exp2):
                target = v1
            else:
                target = v2
elif(is_bool(v1)):
    if(is_int(v2)):
        target = box_int(unbox_bool(v1) op unbox_int(v2))
    elif(is_bool(v2)):
        target = box_int(unbox_bool(v1) op unbox_bool(v2))
    else:
        exp1 = unbox_bool(v1)
        exp2 = is_true(v2)
        if(exp1 op exp2):
            if(exp2):
                target = v2
            else:
                target = v1
        else:
            if(exp2):
                target = v1
            else:
                target = v2
else:
    if(is_int(v2)):
        exp1 = is_true(v1)
        exp2 = unbox_int(v2)
        if(exp1 op exp2):
            if(exp2):
                target = v2
            else:
                target = v1
        else:
            if(exp2):
                target = v1
            else:
                target = v2
    elif(is_bool(v2)):
        exp1 = is_true(v1)
        exp2 = unbox_bool(v2)
        if(exp1 op exp2):
            if(exp2):
                target = v2
            else:
                target = v1
        else:
            if(exp2):
                target = v1
            else:
                target = v2
    else:
        exp1 = is_true(v1)
        exp2 = is_true(v2)
        if(exp1 op exp2):
            if(exp2):
                target = v2
            else:
                target = v1
        else:
            if(exp2):
                target = v1
            else:
                target = v2
"""
        
        #target = box_int(is_true(v1) op unbox_int(v2))
        code = code.replace('target', target).replace('v1', v1).replace('v2', v2).replace('op', op)
        self.append_code(code)
        
        
    def binop_type_check(self, target, left, right, tmp1, tmp2):
        code = r"""
if(is_int(left)):
    if(is_int(right)):
        target = box_int(unbox_int(left) + unbox_int(right))
    elif(is_bool(right)):
        target = box_int(unbox_int(left) + unbox_bool(right))
    else:
        TypeError("Type Error")
elif(is_bool(left)):
    if(is_int(right)):
        target = box_int(unbox_bool(left) + unbox_int(right))
    elif(is_bool(left)):
        target = box_int(unbox_bool(left) + unbox_bool(right))
    else:
        TypeError("Type Error")
else:
    if(is_big(right)):
        target = box_big(add(unbox_big(left), unbox_big(right)))
    else:
        TypeError("Type Error")
"""

        #print(target, left, right, tmp1, tmp2)
        code = code.replace('target', target).replace('left', left).replace('right', right)
        self.append_code(code)
            
    def append_code(self, code):
        for node in ast.parse(code).body:
            self.exp_ast.body.append(node)
        
    def make_tmp(self):
        self.tmp += 1
        return 'exp' + str(self.tmp)
    
    def check_instances(self, n, instances):
        for inst in instances:
            if isinstance(n, inst):
                return True
        return False
    
    def unary_type_check(self, target, val, op):
        code = r"""
if(is_int(val)):
    target = box_int(op unbox_int(val))
elif(is_bool(val)):
    target = box_int(op unbox_bool(val))
else:
    target = box_int(op is_true(val))
"""
        code = code.replace('target', target).replace('op', op).replace('val', val)
        self.append_code(code)
    
    def box_constant(self, target, const):
        code = r"""
target = box_int(const)
"""
        code = code.replace('target', target).replace('const', str(const))
        self.append_code(code)
            
    def binop_constants(self, target, left, right):
        code = r"""
target = box_int(left + right)     
"""
        code = code.replace('target', target).replace('left', left).replace('right', right)
        self.append_code(code)