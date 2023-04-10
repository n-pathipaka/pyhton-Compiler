import ply.lex as lex
from collections import deque

class MyLexer:
    # Define the tokens to be used in the lexer
    reserved = {
    'if'   : 'IF',
    'else' : 'ELSE',
    'while' : 'WHILE',
    'and'   : 'AND',
    'or'    : 'OR',
    'not'   : 'NOT',
    'eval' : 'EVAL',
    'input' : 'INPUT',
    'print' : 'PRINT',
    'int'   : 'INT'
    }

    tokens = (
        'NUMBER',
        'PLUS',
        'LPAR',
        'RPAR',
        'EQUALS',
        'DOUBLEEQUALS',
        'NOTEQUALS',
        'MINUS',
        'COLON',
        'NEWLINE',
        'INDENT',
        'DEDENT',
        'VARNAME',
    )

    tokens = tokens + tuple(reserved.values())

    # Define the regular expressions for each token
    t_MINUS = r'-'
    t_PLUS  = r'\+'
    t_LPAR  = r'\('
    t_RPAR  = r'\)'
    t_DOUBLEEQUALS = r'\=='
    t_EQUALS = r'\='
    t_NOTEQUALS = r'\!='
    t_COLON  = r'\:'


    t_ignore_single_line_comment = r'\#.*[\s\S]*?$'
    t_ignore_multi_line_comment  = r'\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'' 

    # Define the lexer constructor
    def __init__(self):
        self.lexer = lex.lex(module=self)
        #pass

   
    def t_NUMBER(self, t):
        r'\d+'
        try:
            t.value = int(t.value)
        except ValueError:
            print("integer value too large", t.value)
            t.value = 0
        return t

    def t_VARNAME(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'  # variable names but reserved values will also come into this expression.
        t.type = self.reserved.get(t.value, 'VARNAME')    # Check for reserved words if not present assign it to varname
        return t

    t_ignore = ' \t'
    
   
    # Define a rule for NEWLINE token
    
    def t_NEWLINE(self, t):
        r'\n+[ \t]*'
        print("Newline found", t.value)
        t.lexer.lineno += len(t.value)
        t.type = 'NEWLINE'
        return t
    
    def input(self, data):
        self.lexer.input(data)
    
    # Tokenize the input string and get the tokens
    def token(self):
        return self.lexer.token()
    
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)
        

