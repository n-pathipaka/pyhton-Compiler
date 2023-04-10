from collections import deque
import ply.lex as lex
from myLexer import MyLexer


class IndentWrapper(MyLexer):

    def __init__(self,debug=0, optimize=0, lextab='lextab', reflags=0):
        super().__init__()
        print("From indentation")
        self.lexer = lex.lex(module=self)
        self.token_stream = None
        self.indent_stack = [0]
        self.token_queue = deque()
        self.eof_reached = False
        
        

    def input(self, data, add_endmarker=False):
        self.lexer.input(data)
        self.token_stream = self.filter(self.lexer, add_endmarker)


    def _new_token(self,type, lineno, lexpos):
        tok = lex.LexToken()
        tok.type = type
        tok.value = None
        tok.lineno = lineno
        tok.lexpos = lexpos
        return tok

    # Synthesize a DEDENT tag

    def DEDENT(self, lineno, linepos):
        return self._new_token("DEDENT", lineno, linepos)

    # Synthesize an INDENT tag

    def INDENT(self, lineno, linepos):
        return self._new_token("INDENT", lineno, linepos)
    
    def NEWLINE(self, lineno, linepos):
        return self._new_token("NEWLINE", lineno, linepos)
    
    def filter(self, lexer,  add_endmarker):
        token = None
        tokens = iter(lexer.token, None)
        for token in self.token_indentation(tokens):
            yield token

        if add_endmarker:
            lineno = 1
            lexpos = 0
            if token is not None:
                lineno = token.lineno
                lexpos = token.lexpos
            yield self._new_token("ENDMARKER", lineno, lexpos)


    def token_indentation(self, tokens):
        token = None
        for token in tokens:
            if token.type == 'NEWLINE':
                # get the indentation level of the line
                line_indent = len(token.value) - 1
                if line_indent > self.indent_stack[-1]:
                    # new level of indentation found
                    self.indent_stack.append(line_indent)
                    yield self.INDENT(token.lineno, token.lexpos)
                elif line_indent < self.indent_stack[-1]:
                    # dedent tokens are needed
                    #yield self.NEWLINE(token.lineno, token.lexpos)
                    while line_indent < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        yield self.NEWLINE(token.lineno, token.lexpos)
                        yield self.DEDENT(token.lineno, token.lexpos)
                    if line_indent != self.indent_stack[-1]:
                        raise IndentationError("Inconsistent indentation")
                else :
                    yield token
            else:
                yield token

        ## add dedent tokes for all the levels of indentation
        while len(self.indent_stack) > 1:
            assert token is not None
            self.indent_stack.pop()
            yield self.NEWLINE(token.lineno, token.lexpos)
            yield self.DEDENT(token.lineno, token.lexpos)

    def token(self):
        try:
            return self.token_stream.__next__()
        except StopIteration:
            return None