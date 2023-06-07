import compiler
from compiler.ast import Const
from compiler.ast import Name
from compiler.ast import Discard
from compiler.ast import AssName
from compiler.ast import Assign
from compiler.ast import Module
from compiler.ast import Add
from compiler.ast import Stmt
from compiler.ast import CallFunc
from compiler.ast import UnarySub
from compiler.ast import Printnl
from compiler.ast import List
from compiler.ast import Dict
from compiler.ast import Compare
from compiler.ast import IfExp
from compiler.ast import And
from compiler.ast import Or
from compiler.ast import Not
from compiler.ast import Subscript
import ply.yacc as yacc
import ply.lex as lex


reserved = {
    'print': 'print',
    'if': 'if',
    'else': 'else',
    'and': 'and',
    'or': 'or',
    'not': 'not',
    'is': 'is',
}

tokens = ['int', 'identifier', 'lparen',
          'rparen', 'colon', 'comma',
          'plus', 'minus', 'eq', 'eqeq',
          'noteq', 'lbrace', 'rbrace',
          'lsqbracket', 'rsqbracket'] + list(reserved.values())

##############################################
#  LEXER LOGIC STARTS
#############################################


digit = r'([0-9])'

t_plus = r'\+'

t_minus = r'-'

t_eq = r'\='

t_eqeq = r'\=\='

t_noteq = r'!\='

t_colon = r':'

t_comma = r','

t_lbrace = r'\{'

t_rbrace = r'\}'

t_lsqbracket = r'\['

t_rsqbracket = r'\]'

t_lparen = r'\('

t_rparen = r'\)'


def t_identifier(t):
    r'[_A-Za-z][_0-9A-Za-z]*'
    t.type = reserved.get(t.value, 'identifier')
    return t


def t_int(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "integer value too large", t.value
        t.value = 0
    return t


t_ignore = ' \t'


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_comment(t):
    r'\#.*'
    pass


def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

 ##############################################
 #  PARSER LOGIC STARTS
 #############################################


precedence = (
    ('nonassoc', 'print'),
    ('left', 'or'),
    ('left', 'and'),
    ('right', 'not'),
    ('left', 'is'),
    ('left', 'eqeq', 'noteq'),
    ('left', 'plus', 'minus'),
    ('right', 'uminus'),
    ('left', 'lparen', 'rparen'),
)


def p_program(t):
    'program : module'
    t[0] = t[1]


def p_module(t):
    '''module : stmt
              | stmt module'''
    t[0] = [t[1]]
    if len(t) == 3:
        t[0].extend(t[2])
    t[0] = Module(None, t[0][0])


def p_stmt(t):
    '''stmt : epsilon
            | simple_stmt
            | simple_stmt stmt'''
    if len(t) == 2:
        if t[1] == None:
            t[0] = []
        else:
            t[0] = [t[1]]
    if len(t) == 3:
        t[0] = [t[1]]
        t[0].extend(t[2])
    t[0] = Stmt(t[0])


def p_print_stmt(t):
    'simple_stmt : print expression'
    t[0] = Printnl([t[2]], None)


def p_assign_stmt(t):
    'simple_stmt : target eq expression'
    if isinstance(t[1], Subscript):
        t[0] = Assign([Subscript(t[1].expr, 'OP_ASSIGN', t[1].subs)], t[3])
    else:
        t[0] = Assign([AssName(t[1], 'OP_ASSIGN')], t[3])


def p_not_expression(t):
    'expression : not expression'
    t[0] = Not(t[2])


def p_and_expression(t):
    'expression : expression and expression'
    if isinstance(t[1], And):
        t[1].nodes.append(t[3])
        t[0] = t[1]
    else:
        t[0] = And([t[1], t[3]])


def p_or_expression(t):
    'expression : expression or expression'
    if isinstance(t[1], Or):
        t[1].nodes.append(t[3])
        t[0] = t[1]
    else:
        t[0] = Or([t[1], t[3]])


def p_compare_expression(t):
    '''expression : expression eqeq expression 
                | expression noteq expression
                | expression is expression'''
    if (isinstance(t[1], Compare)):
        ops = t[1].ops
        ops.append((t[2], t[3]))
        t[0] = Compare(t[1].expr, ops)
    else:
        t[0] = Compare(t[1], [(t[2], t[3])])


def p_if_expression(t):
    'expression : expression if expression else expression'
    t[0] = IfExp(t[1], t[3], t[5])


def p_list_expression(t):
    'expression ': 'list_expression'


def p_expr_list_expression(t):
    'expression : lsqbracket expr_list rsqbracket'
    t[0] = List(t[2])


def p_expr_list(t):
    '''expr_list : epsilon
                | expression
                | expression comma expr_list'''
    if len(t) == 2:
        if t[1] == None:
            t[0] = ()
        else:
            t[0] = [t[1]]
    else:
        t[0] = [t[1]] + t[3]


def p_key_datum_list_expression(t):
    'expression : lbrace key_datum_list rbrace'
    t[0] = Dict(t[2])


def p_key_datum_list(t):
    '''key_datum_list : epsilon
                    | key_datum
                    | key_datum comma key_datum_list'''
    if len(t) == 2:
        if t[1] == None:
            t[0] = ()
        else:
            t[0] = t[1]
    else:
        t[0] = t[1] + t[3]


def p_key_datum(t):
    'key_datum : expression colon expression'
    t[0] = [(t[1], t[3])]


def p_subscription_expression(t):
    'expression : subscription'
    t[0] = t[1]


def p_subscription(t):
    'subscription : expression lsqbracket expression rsqbracket'
    t[0] = Subscript(t[1], 'OP_APPLY', [t[3]])


def p_discard_stmt(t):
    'simple_stmt : expression'
    t[0] = Discard(t[1])


def p_int_expression(t):
    'expression : int'
    t[0] = Const(t[1])


def p_paren_expression(t):
    'expression : lparen expression rparen'
    t[0] = t[2]


def p_unarySub(t):
    'expression : minus expression %prec uminus'
    t[0] = UnarySub(t[2])


def p_identifier_expression(t):
    'expression : identifier'
    t[0] = Name(t[1])


def p_function_expression(t):
    'expression : identifier lparen rparen'
    t[0] = CallFunc(Name(t[1]), [])


def p_plus_expression(t):
    'expression : expression plus expression'
    t[0] = Add((t[1], t[3]))


def p_target(t):
    '''target : identifier
              | subscription'''
    t[0] = t[1]


def p_epsilon(t):
    'epsilon :'
    pass


def p_error(t):
    print "Syntax error at '%s'" % t.value


def transform_list_to_str(seq):
    s = ""
    for ele in seq:
        s += ele
    return s


def parseText(prog):
    lexer = lex.lex()
    parser = yacc.yacc()
    return parser.parse(prog, lexer=lexer)


def parseFile(filename):
    with open(filename) as f:
        program = f.readlines()
    if program:
        program = transform_list_to_str(program)
        lexer = lex.lex()
        parser = yacc.yacc()
        return parser.parse(program, lexer=lexer)
    # parseText(program)


prog = '''
print [1,2,3][2]
'''

print compiler.parse(prog)
print parseText(prog)
