import sys
import ast
from ast import *
import helper


from parse import Parser
from datetime import datetime

INT = "int"
BOOL = "bool"
BIG = "big"


### class functions defined in the book for type chekcing.

class GetTag(ast.AST):
    def __init__(self, arg):
        self.arg = arg
        self.counter = 0


class InjectFrom(ast.AST):
    def __init__(self, typ, arg ):
        self.typ = typ 
        self.arg = arg

    def __repr__(self):
        return "InjectFrom(%s, %s)" % (repr(self.typ), repr(self.arg))

class ProjectTo(ast.AST):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg

    def __repr__(self):
        return "ProjectTo(%s, %s)" % (repr(self.typ), repr(self.arg))

class Let(ast.AST):
    def __init__(self, var, val, body):
        self.var = var
        self.val = val
        self.body = body

    def __repr__(self):
        return "Let(%s, %s, %s)" % (repr(self.var), repr(self.val), repr(self.body))
    
class IsInt(ast.AST):
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return  "%s(%s)" % ('IsInt', self.obj)


class IsBool(ast.AST):
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return  "%s(%s)" % ('IsBool', self.obj)



class IsBig(ast.AST):
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return  "%s(%s)" % ('IsBig', self.obj)
    

class AddBig(BinOp):
    def __repr__(self):
        return "AddBig(%s)" % (str(self.asList()))


class IsTrue(IsInt):
    def __repr__(self):
        return self.printName('IsTrue')


class TypeError(ast.AST):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "TypeError(%s)" % (repr(self.message))
    
class Modified(ast.AST):
    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return "Modified(%s)" % (repr(self.node))


## we will not use the classes defined in the book but create explicate AST from the python code as discussed in the class.
## to add bool plus int and viceversa
def add_type_check(target, left, right, tmp1, tmp2, tmp3, tmp4):
    code = r"""
t0 = left
t1 = right
if(is_big(t0) and is_big(t1)):
    target = inject_big(add(project_big(t0), project_big(t1)))
elif(is_big(t1)):
    TypeError("Type Error")
else:
    if(is_int(t0)):
        t2 = project_int(t0)
    else:
        t2 = project_bool(t0)
    if(is_int(t1)):
        t3 = project_int(t1)
    else:
        t3 = project_bool(t1)
    target = inject_int(t2 + t3)
"""

    code = code.replace('target', target).replace('left', left).replace('right', right).replace('t0', tmp1).replace('t1', tmp2).replace('t2', tmp3).replace('t3', tmp4)

    #print(code)
    #print(ast.dump(ast.parse(code), indent=4))

    return ast.parse(code).body

### just test the explicate one ###

def create_list(list , target, tmp):
    code =  r"""
    %s =  inject_big(create_list(inject_int(%d)))
    """% (tmp, len(list))
    for i in range(len(list)):
        code += r"""
        set_subsript(%s, inject_int(%d), inject_int(%d))
        """ % (target, i, list[i])
    code += r"""
    target = tmp
    """


def create_dict(dict, target, tmp):
    code = r"""
    %s = inject_big(create_dict(inject_int(%d)))
    """ % (tmp, len(dict))
    for key, value in dict.items():
        code += r"""
        set_subscript(%s, inject_int(%s), inject_int(%s))
        """ % (tmp, key, dict[key])
    code += r"""
    target = tmp
    """
    code = code.replace('target', target)

    print(code)

class Explicate:
    def __init__(self, print_explicated_ast):
        self.explicate_ast = None
        self.counter = 0
        self.print_explicated_ast = print_explicated_ast
        self.replace_ast = [BinOp]

    def tempVar(self):
        ## generate temporary variables
        self.counter += 1
        return "temp" + "_" + str(self.counter)
    
    def make_explicate(self, n):
        self.explicate(n, None)
        if self.print_explicated_ast:
            print(ast.dump(self.explicate_ast))
        return self.explicate_ast


    def explicate(self, n, var=None):
        if isinstance(n, Module):
            child = []
            for node in n.body:
                result = self.explicate(node,var)
                if isinstance(result, Modified):
                    child.extend(result.node)
                else:
                    child.append(self.explicate(node, var))
            self.explicate_ast = (Module(child))
        elif isinstance(n, Assign):
            if self.check_instances(n.value):
                return self.explicate(n.value, n.targets[0].id)
            return Assign([self.explicate(n.targets[0], var)], self.explicate(n.value, n.targets[0].id))
        elif isinstance(n, Expr):
            if isinstance(n.value, Call):
                if n.value.func.id == 'print':
                    return Expr(n.value)
        elif isinstance(n, Constant):
            return Call(Name('inject_int', Load()), [Constant(n.value)])
        elif isinstance(n, Name):
            return n
        elif isinstance(n, BinOp):
            '''
                 we need to box/unbox here as it is an operation
            '''
           ### if both ints or bools we can just add normally in compile time.

            left   = n.left
            right  = n.right

            
            if isinstance(left, Constant) and isinstance(right, Constant):
                if left.value in [True, False]:
                    left =  Constant(0) if left.value == 'False' else Constant(1)
                if right.value in [True, False]:
                    right = Constant(0) if right.value == 'False' else Constant(1)
                return  Assign([Name(var)],self.explicate( Constant(left.value + right.value)))

            ## if they are not bools or ints just do recursion by storing the left value to a temporary value and right to temp value and box/unbox.
            ## we are explicating the AST after flattening it so we can just use the temp variables to store the values.

           

            ltemp = helper.tempVar()
            rtemp = helper.tempVar()
            tmp3 = helper.tempVar()
            tmp4 = helper.tempVar()

            if isinstance(left, Name) and isinstance(right, Name):
                return Modified(add_type_check(var, left.id, right.id, ltemp, rtemp, tmp3, tmp4))
            if isinstance(left, Constant):
                return Modified(add_type_check(var, str(left.value), right.id, ltemp, rtemp, tmp3, tmp4))
            if isinstance(right, Constant):
                return Modified(add_type_check(var, left.id, str(right.value), ltemp, rtemp, tmp3 , tmp4))
                    
        ## handle unary sub , call , list dict , subscript

        elif isinstance(n, Call):
            return Call(self.explicate(n.func), [self.explicate(arg) for arg in n.args])
        
        elif isinstance(n, List):
            ## if you get a list create a list and append the elements.
            ## call the create_list function
            ## convert that ast and flatten it for the set_subscript, create_list with args as legth stored tmp value as a argument. similary for set_subsript all the params 
            l = []
            for child in n.elts:
                l.append(self.explicate(child, var))
            return List(l)
        
        elif isinstance(n, Dict):
            d = []
            keys = n.keys
            values = n.values
            for k in range(len(keys)):
                d.append(self.explicate(keys[k], var), self.explicate(values[k], var))
            return Dict(d)
        
        elif isinstance(n, Subscript):
            pass

        elif isinstance(n, If):
            return If(self.explicate(n.test, var), self.explicate(n.body[0], var), self.explicate(n.orelse[0], var))
        
        ## we will handle remaining instances later
            
    def check_instances(self, n):
        for instance in self.replace_ast:
            if isinstance(n, instance):
                return True
        return False


# parser = Parser(True , True)
# file_ast = parser.parse_file(sys.argv[1])

# e = Explicate()
# e.explicate(file_ast)

# #print(e.explicate_ast)
# print(ast.dump(e.explicate_ast, indent=4))


# for node in ast.walk(e.explicate_ast):
#     if isinstance(node, InjectFrom):
#         print(node.arg.value)