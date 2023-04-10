import ast
from ast import *
import ply.yacc as yacc
from myLexer import MyLexer
from indentWrapper import IndentWrapper
import sys

class MyParser:
    tokens = MyLexer.tokens


    ## declaring the precedence of the operators
    precedence = (
        ('nonassoc', 'PRINT'),
        ('left', 'PLUS'),
        ('right', 'UMINUS')
    )

    ## convert to AST

    def p_module(self, t):
        'module : statements'
        t[0] = Module(t[1],[])
        print("module", t[1])

    ## statements can be empty or a list of statements
    def p_statements(self, t):
        'statements : empty'
        t[0] = []

    def p_statements_list(self, t):
        'statements : statements statement'
        t[0] = t[1] + [t[2]]
        print("statements list")

    def p_suite(self, t):
        'suite : INDENT statements DEDENT'
        t[0] = t[2]

    def p_if_statement(self, t):
        'statement : IF expression COLON suite'
        t[0] = If(t[2], t[4], [])

    def p_if_else_statement(self, t):
        'statement : IF expression COLON suite ELSE COLON suite'
        t[0] = If(t[2], t[4], t[7])
        
    def p_print_statement(self, t):
        'statement : PRINT LPAR expression RPAR'
        t[0] = Expr(Call(Name("print",Load()),[t[3]], []))
        
    def p_assign_statement(self, t):
        'statement : VARNAME EQUALS expression'
        t[0] = Assign([Name(t[1],Store())],t[3])

    def p_assign_double_equals(self,t):
        'expression : expression DOUBLEEQUALS expression'
        t[0] = Compare(t[1], [Eq()], [t[3]])  
    
    def p_assign_not_equals(self,t):
        'expression : expression NOTEQUALS expression'
        t[0] = Compare(t[1], [NotEq()], [t[3]])

    def p_and_expression(self,t):
        'expression : expression AND expression'
        t[0] = BoolOp(And(), [t[1], t[3]])
        
    def p_expression_statement(self, t):
        'statement : expression'
        t[0] = Expr(t[1])
        
    def p_plus_expression(self, t):
        'expression : expression PLUS expression'
        t[0] = BinOp(t[1], Add(), t[3])
        
    def p_int_expression(self, t):
        'expression : INT'
        t[0] = Constant(t[1])
        
    def p_varname_expression(self, t):
        'expression : VARNAME'
        t[0] = Name(t[1], Load())
        
    def p_negate_expression(self, t):
        'expression : MINUS expression %prec UMINUS'
        t[0] = UnaryOp(USub(),t[2])

    def p_parenthesis_expression(self, t):
        'expression : LPAR expression RPAR'
        t[0] = t[2]

    def p_eval_input_expression(self, t):
        'expression : EVAL LPAR INPUT LPAR RPAR RPAR'
        t[0] = Call(Name("eval",Load()),[Call(Name("input",Load()), [], [])], [])
        
    def p_empty(self, t):
        'empty :'
        t[0] = None
        
    def p_error(self, t):
        print("Syntax error at '%s'" % t.value)


    def parseInput(self, program):
        #self.lexer = MyLexer()
        #self.lexer.input(program)
        self.lexer = IndentWrapper()
        self.lexer.input(program)
        while True:
            tok = self.lexer.token()
            if not tok: break
            print(tok)
        #self.parser = yacc.yacc(module=self)
        # #tree = yacc.parse(program)
        # tree = self.parser.parse(lexer=self.lexer)
        # #print(" Parsed from yacc parse")
        # print(ast.dump(tree, indent = 4))
        # #print(" Parsed from ast parse")
        # #print(ast.dump(ast.parse(program), indent = 4))
        # return tree
    
    def parse_file(self, temp_file, t):
        # load the file into a string
        temp_prog = ''
        with open(temp_file) as f:
            temp_prog = f.read()
            print(temp_prog)
        # use ast.parse to make string file
        if(t=='2'):
            print(ast.dump(ast.parse(temp_prog), indent = 4))
        else:
            return self.parseInput(temp_prog)

parser = MyParser()
parser.parse_file(sys.argv[1], sys.argv[2])

