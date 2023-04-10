import sys
import ast
from ast import *
import ply.lex as lex
import ply.yacc as yacc

reserved = {
    'print' : 'PRINT',
    'eval' : 'EVAL',
    'input' : 'INPUT'
}

tokens = ['INT','PLUS','LPAR','RPAR', 'EQUALS', 'MINUS', 'VARNAME'] + list(reserved.values())

t_PLUS = r'\+'
t_LPAR = r'\('
t_RPAR = r'\)'
t_EQUALS = r'='
t_MINUS = r'-'

t_ignore = ' \t'

def t_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("integer value too large", t.value)
        t.value = 0
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)
    
def t_VARNAME(t):
    r'[a-zA-z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'VARNAME')
    return t
    
precedence = (
    ('nonassoc', 'PRINT'),
    ('left', 'PLUS'),
    ('right', 'UMINUS')
)

def p_module(t):
    'module : statements'
    t[0] = Module(t[1],[])
    
def p_statement_empty(t):
    'statements : empty'
    t[0] = []
    
def p_statement_empties(t):
    'statements : statements empty'
    t[0] = t[1]

def p_statement_one(t):
    'statements : statement'
    t[0] = [t[1]]
    
def p_statement_plus(t):
    'statements : statements statement'
    t[0] = t[1] + [t[2]]
    
def p_print_statement(t):
    'statement : PRINT LPAR expression RPAR'
    t[0] = Expr(Call(Name("print",Load()),[t[3]], []))
    
def p_assign_statement(t):
    'statement : VARNAME EQUALS expression'
    t[0] = Assign([Name(t[1],Store())],t[3])
    
def p_expression_statement(t):
    'statement : expression'
    t[0] = Expr(t[1])
    
def p_plus_expression(t):
    'expression : expression PLUS expression'
    t[0] = BinOp(t[1], Add(), t[3])
    
def p_int_expression(t):
    'expression : INT'
    t[0] = Constant(t[1])
    
def p_varname_expression(t):
    'expression : VARNAME'
    t[0] = Name(t[1], Load())
    
def p_negate_expression(t):
    'expression : MINUS expression %prec UMINUS'
    t[0] = UnaryOp(USub(),t[2])

def p_parenthesis_expression(t):
    'expression : LPAR expression RPAR'
    t[0] = t[2]

def p_eval_input_expression(t):
    'expression : EVAL LPAR INPUT LPAR RPAR RPAR'
    t[0] = Call(Name("eval",Load()),[Call(Name("input",Load()), [], [])], [])
    
def p_empty(t):
    'empty :'
    t[0] = None
    
def p_error(t):
    print("Syntax error at '%s'" % t.value)

def ourparse(program):
    print("program to parse")
    print(program)
    lexer = lex.lex()
    lexer.input(program)
    for token in lexer:
        print(token)
    parser = yacc.yacc()
    p_tree = yacc.parse(program)
    print(ast.dump(p_tree, indent=4))
    print(ast.dump(ast.parse(program), indent=4))
    return p_tree
    

# this function makes an AST from a file name
def make_tree_from_file(temp_file):
    # load the file into a string
    temp_prog = ''
    with open(temp_file) as f:
        temp_prog = f.read()
    # use ast.parse to make string file
    ourparse(temp_prog)
    #temp_tree = ast.parse(temp_prog)
    temp_tree = ourparse(temp_prog)
    # pring the python program
    #print(temp_prog)
    # return the ast
    return temp_tree

# flatten stuff from exercise 1.6
# global variable for what tmp currently is
global tmp
tmp = 0
# function you call to flatten stuff
# takes in a tree and a string list and makes that string list
# a flattened program
# does so through recursion
def flatten(n, prog):
    # define tmp again so it doesn't mess up
    global tmp
    # if module, loop through all children and flatten them
    if isinstance(n, Module):
        tmp = 0
        for node in n.body:
            flatten(node, prog)
    # if we are assign, don't do much just flatten left and right side
    # assigns are a line so also append that to our program
    elif isinstance(n, Assign):
        line = ''
        line += flatten(n.targets[0], prog)
        line += ' = '
        line += flatten(n.value, prog)
        prog.append(line)
    # expr is simple, just flatten it and append our expression to our list of strings
    elif isinstance(n, Expr):
        prog.append(flatten(n.value, prog))
    # return the constant value
    elif isinstance(n, Constant):
        return str(n.value)
    # return a name + underscore so program variables don't mess with us
    elif isinstance(n, Name):
        return "_" + n.id
    # if BinOp we need to check if left or right are something we
    # need to flatten, if so call our helper that does that for us
    elif isinstance(n, BinOp):
        # if left or right is op do a thing
        line = ''
        if isinstance(n.left, BinOp) or isinstance(n.left, UnaryOp) or isinstance(n.left, Call):
            line += flatten_helper(n.left, prog)
        else:
            line += flatten(n.left, prog)
        line += flatten(n.op, prog)
        if isinstance(n.right, BinOp) or isinstance(n.right, UnaryOp) or isinstance(n.right, Call):
            line += flatten_helper(n.right, prog)
        else:
            line += flatten(n.right, prog)
        return line
    # same as BinOp
    elif isinstance(n, UnaryOp):
        # if op do a thing
        line = ''
        line += flatten(n.op, prog)
        if isinstance(n.operand, UnaryOp) or isinstance(n.operand, BinOp) or isinstance(n.operand, Call):
            line += flatten_helper(n.operand, prog)
        else:
            line += flatten(n.operand, prog)
        return line
    # call is weird, flatten all of our arguments and call the boy
    elif isinstance(n, Call):
        # if arg[0] is op do a thing
        line = ''
        for arg in n.args:
            if isinstance(arg, BinOp) or isinstance(arg, UnaryOp):
                line += flatten_helper(arg, prog)
            else:
                line += flatten(arg, prog)
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
def flatten_helper(node, prog):
    # make sure we reference tmp
    global tmp
    # if a binOp then flatten your left and right also
    if isinstance(node, BinOp):
        line = ''
        if isinstance(node.left, BinOp) or isinstance(node.left, UnaryOp) or isinstance(node.left, Call):
            line += flatten_helper(node.left, prog)
        else:
            line += flatten(node.left, prog)
        line += flatten(node.op, prog)
        if isinstance(node.right, BinOp) or isinstance(node.right, UnaryOp) or isinstance(node.right, Call):
            line += flatten_helper(node.right, prog)
        else:
            line += flatten(node.right, prog)
        prog.append("tmp" + str(tmp) + " = " + line)
        tmp += 1
        return "tmp" + str(tmp-1)
    # do same as BinOP
    elif isinstance(node, UnaryOp):
        line = ''
        line += flatten(node.op, prog)
        if isinstance(node.operand, BinOp) or isinstance(node.operand, UnaryOp) or isinstance(node.operand, Call):
            line += flatten_helper(node.operand, prog)
        else:
            line += flatten(node.operand, prog)
        prog.append("tmp" + str(tmp) + " = " + line)
        tmp += 1
        return "tmp" + str(tmp-1)
    # call also needs to be flattened if it was called in the middle of something
    elif isinstance(node, Call):
        line = ''
        for arg in node.args:
            if isinstance(arg, BinOp) or isinstance(arg, UnaryOp):
                line += flatten_helper(arg, prog)
            else:
                line += flatten(arg, prog)
        #prog.append("#flattening Call")
        prog.append("tmp" + str(tmp) + " = " + str(node.func.id) + "(" + line + ")")
        tmp += 1
        return "tmp" + str(tmp-1)
    else:
        raise Exception('Error: operation not passed')

# this makes all our local variables
# put all our local variables into the dict
def make_variables(tree, variables):
    register = -4
    for node in ast.walk(tree):
        if isinstance(node, Name):
            if not node.id == "print" and not node.id == "eval" and not node.id == "input" and not node.id in variables:
                variables[node.id] = register
                register -= 4
    return register + 4
            
def assembly_baby(n, esp, variables, prog):
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
            assembly_baby(node, esp, variables, prog)
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
            prog.append('movl ' + assembly_baby(n.value, esp, variables, prog) + ', %eax')
            prog.append('movl %eax, ' + assembly_baby(n.targets[0], esp, variables, prog))
        else:
            line = ''
            line += 'movl ' + assembly_baby(n.value, esp, variables, prog) + ', '
            line += assembly_baby(n.targets[0], esp, variables, prog)
            prog.append(line)
    elif isinstance(n, Expr):
        assembly_baby(n.value, esp, variables, prog)
    elif isinstance(n, Constant):
        return '$' + str(n.value)
    elif isinstance(n, Name):
        return str(variables[n.id]) + '(%ebp)'
    elif isinstance(n, BinOp):
        prog.append('movl ' + assembly_baby(n.left, esp, variables, prog) + ', %eax')
        line = assembly_baby(n.op, esp, variables, prog)
        line += assembly_baby(n.right, esp, variables, prog)
        line += ', %eax'
        prog.append(line)
        return '%eax'
    elif isinstance(n, UnaryOp):
        prog.append('movl ' + assembly_baby(n.operand, esp, variables, prog) + ', %eax')
        prog.append(assembly_baby(n.op, esp, variables, prog) + '%eax')
        return '%eax'
    elif isinstance(n, Call):
        if n.func.id == 'eval':
            prog.append('call eval_input_int')
            return '%eax'
        elif n.func.id == 'print':
            prog.append('movl ' + assembly_baby(n.args[0], esp, variables, prog) + ', %eax')
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
        
# now actually take in our arguments and flatten everything
#print('FILE: ' + sys.argv[1])
old_tree = make_tree_from_file(sys.argv[1])
flattened_prog = []
flatten(old_tree, flattened_prog)
tree_prog = ''
# make into usable string for ast
for line in flattened_prog:
    tree_prog += line + "\n"
# sanity check
with open(sys.argv[1].replace('.py', '.flatpy'), 'w') as f:
    f.write(tree_prog)

print('Flattened Program:')
print(tree_prog)
# now get ast from flattened code
# and we'll use this tree to write assembly
#new_tree = ast.parse(tree_prog)
new_tree = ourparse(tree_prog)
#print('Flattened Tree:')
#print(ast.dump(new_tree, indent=4))
        
# store all our local variable locations in a dict
local_variables = {}
esp = make_variables(new_tree, local_variables)
print('Variables:')
print(local_variables)
#print(esp)
#print(ast.dump(new_tree, indent=4))
    
new_prog = []
assembly_baby(new_tree, esp, local_variables, new_prog)
final_prog = ''
final_prog += '.globl main\n'
final_prog += 'main:\n\t'
for line in new_prog:
    final_prog += line + '\n\t'
print('Assembly:')
print(final_prog)
with open(sys.argv[1].replace('.py', '.s'), 'w') as f:
    f.write(final_prog)
