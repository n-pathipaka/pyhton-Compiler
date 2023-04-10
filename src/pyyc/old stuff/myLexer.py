import ply.lex as lex

class MyLexer:
    # Define the tokens to be used in the lexer
    reserved = {
    'eval' : 'EVAL',
    'input' : 'INPUT',
    'print' : 'PRINT'
    }

    tokens = (
        'INT',
        'PLUS',
        'LPAR',
        'RPAR',
        'EQUALS',
        'MINUS',
        'VARNAME',
        'COMMENT'
    )

    tokens = tokens + tuple(reserved.values())

    # Define the regular expressions for each token
    t_MINUS = r'-'
    t_PLUS  = r'\+'
    t_LPAR  = r'\('
    t_RPAR  = r'\)'
    t_EQUALS = r'='


    t_ignore_single_line_comment = r'\#.*$'
    t_ignore_multi_line_comment  = r'\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'' 

    # Define the lexer constructor
    def __init__(self):
        self.lexer = lex.lex(module=self)

   
    def t_INT(self, t):
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

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

        

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)


    def input(self, data):
        self.lexer.input(data)
        
    
     # Tokenize the input string and get the tokens
    def token(self):
        return self.lexer.token()
        

