import sys
import ast
from ast import *

from parse import Parser
from uniqufy import functionScope
from flatten import Flatten
from explicate import Explicate
from convert import ToIRConverter
from control_flow_graph import cfg
from liveness_analysis import Liveness
from interference_graph import InterferenceGraph
from graph_coloring import GraphColoring
from spill import Spill
from assign_homes import AssignHomes
from print_x86 import x86_File

# uploading to github (so you don't have to comment stuff)
github = True
# print the original file contents
print_original_file = False
# print the original ast from file
print_original_ast = False
# print the flattened ast
print_flattened_ast = False
# print the flattened program
print_flattened_prog = False
# print explicate
print_explicate_stuff = False
# print the IR
print_x86_IR = False
# output control flow graph to pdf
output_cfg = False
# display liveness analysis
display_liveness = False
# output interference graph
output_interference = False
# out spill stuff
print_spill_info = False
# print variable definitions
print_var_homes = False
# output final interference
print_final_IR = False
# show the assembly in console
print_assembly = False

class Compile:
    def compile(self, filename):
        print("----- compiling file -----")
        print(filename)
        # parse file to ast
        parser = Parser(print_original_file, print_original_ast)
        file_ast = parser.parse_file(filename)

        uniqfy = functionScope()
        uniqfy.find_func_scope(file_ast)
        # flatten ast to new ast
        flatten = Flatten(print_flattened_ast, print_flattened_prog)
        flattened_ast = flatten.flatten(file_ast)
        # explicate
        explicator = Explicate(print_explicate_stuff)
        explicate_ast = explicator.explicate(flattened_ast)
        # reflatten
        flatten = Flatten(print_flattened_ast, print_flattened_prog)
        flattened_ast = flatten.flatten(explicate_ast)
        variables = flatten.get_variables()
        # convert flattened ast to x86 IR
        converter = ToIRConverter(print_x86_IR)
        x86_IR = converter.python_to_IR(flattened_ast)
        do = True
        spilled_vars = 0
        new_vars = None
        while do:
            # create control flow graph
            control_graph_obj = cfg(output_cfg, github)
            control_graph = control_graph_obj.create_graph(x86_IR)
            # liveness analysis
            liveness_analyzer = Liveness(display_liveness)
            liveness_graph = liveness_analyzer.analyze(control_graph)
            # interference graph
            interference_graph = InterferenceGraph(github)
            inter_graph = interference_graph.create_interference_graph(liveness_graph, variables) 
            # color interference graph
            graph_colorer = GraphColoring(github, output_interference)
            stack, reg = graph_colorer.color_graph(inter_graph, new_vars)
            # find spill code
            spiller = Spill(print_spill_info)
            spilled_lines = spiller.check_spill(x86_IR, stack)
            if len(spilled_lines) != 0:
                x86_IR, new_vars = spiller.modify_IR(x86_IR, spilled_lines, spilled_vars)
                spilled_vars += len(new_vars)
                variables = variables.union(set(new_vars))
            else:
                do = False
                # assign homes
                assign = AssignHomes(print_var_homes, print_final_IR)
                program = assign.assign_homes(x86_IR, variables, interference_graph)
                # print x86
                x86er = x86_File(print_assembly)
                x86er.print_file(program, filename)
        
compiler = Compile()
compiler.compile(sys.argv[1])