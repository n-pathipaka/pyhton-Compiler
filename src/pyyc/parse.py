import sys
import ast
from ast import *

class Parser:
    # variables on initialize that tell us whether or not to print
    def __init__(self, print_prog, print_tree):
        self.print_prog = print_prog
        self.print_tree = print_tree
        
    # make an ast from a file
    def parse_file(self, filename):
        # convert to a string
        temp_prog = ''
        with open(filename) as f:
            temp_prog = f.read()
        # we have a string now so call parse_string
        return self.parse_string(temp_prog)
    
    def parse_string(self, string):
        # call ast.parse
        # TODO: replace with our own for ec
        tree = ast.parse(string)
        # print stuff for debugging
        if self.print_prog:
            print("----- program -----")
            print(string)
        if self.print_tree:
            print("----- ast -----")
            print(ast.dump(tree, indent=4))
        return tree
    
    def parse(self, prog):
        # TODO: replace ast.parse with self.parse for ec
        # fill in our own parsing method here
        pass