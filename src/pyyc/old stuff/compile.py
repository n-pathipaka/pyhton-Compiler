import sys
import ast
from flatten import Flatten 
from convertToIR import ConvertToIR
from livenessAnalysis import LivenessAnalysis
from interferenceGraph import InterferenceGraph
from graphColoring import GraphColoring

class Compile:
    def __init__(self):
        self.spilled_lines = []
        self.stack = set()
        self.registers = set()
        self.graph = None
        self.convert = ConvertToIR()
        self.esp = 0
    
    def compile(self, filename):

        ## flatten the file
        new_tree, tot_variables = self.flatten_file(filename)

        intermediate_ir = self.convert_to_ir(new_tree)

        self.stack, self.registers = self.first_process(intermediate_ir, tot_variables)
        # TODO: don't check spill code from here, go through ir and check if stack variables add or neg
        # then if they do spill them
        # also, have a prioritize spilled ie: don't let those go on the stack put in registers first
        # need a list of stack variables, go change all instructions with target stack
        # repeat
        self.spilled_lines = self.convert.checkSpill(intermediate_ir, self.stack)
        #print("spilled:" + str(self.spilled_lines))
        
        #print("starting variables: " + str(tot_variables))
        ### we have to do the process untill there is no spill.
        spilledvars = 0
        while len(self.spilled_lines) != 0:
            intermediate_ir, new_vars = self.convert.modify_IR(intermediate_ir, self.spilled_lines, spilledvars)
            spilledvars += len(new_vars)
            #print("----- old variables -----")
            #print(tot_variables)
            tot_variables = tot_variables + new_vars
            #print("----- spill variables -----")
            #print(tot_variables)
            self.stack, self.registers = self.repeat_process(intermediate_ir, tot_variables, new_vars)
            self.spilled_lines = self.convert.checkSpill(intermediate_ir, self.stack)
            #print("spilled:" + str(self.spilled_lines))

        #print("ending vairables: " + str(tot_variables))
        #for line in range(len(intermediate_ir)):
        #    print(str(line) + ": " + intermediate_ir[line])
        x86 = self.assign_homes(intermediate_ir, tot_variables)
        self.x86_to_file(x86, filename)
    
    def repeat_process(self, intermediate_ir, tot_variables, spill_variables):
        liveness_list = self.do_liveness_analysis(intermediate_ir)
        
        interference_graph = InterferenceGraph()
        graph = interference_graph.create_interference_graph(intermediate_ir, liveness_list, tot_variables)
        
        graphColor = GraphColoring()
        stack, registers = graphColor.color_spill_graph(graph, spill_variables)
        self.graph = graphColor
        
        #print("stack:", stack)
        #print("registers:", registers)
        
        return stack, registers

    def first_process(self, intermediate_ir, tot_variables):
        liveness_list = self.do_liveness_analysis(intermediate_ir)

        ## ccreate the interference graph.
        interference_graph = InterferenceGraph()
        graph = interference_graph.create_interference_graph(intermediate_ir, liveness_list, tot_variables)

        ## color the graph.
        graphColor = GraphColoring()
        stack, registers = graphColor.color_graph(graph)
        self.graph = graphColor

        #print("stack:", stack)
        #print("registers:", registers)

        return stack, registers
    
    def x86_to_file(self, x86, filename):
        print("----- writing file -----")
        final_prog = ''
        final_prog += '.globl main\n'
        final_prog += 'main:\n\t'
        for line in x86:
            final_prog += line + '\n\t'
        with open(filename.replace('.py', '.s'), 'w') as f:
            f.write(final_prog)
        print(final_prog)
    
    def assign_homes(self, x86IR, variables):
        variable_dict = {}
        for variable in variables:
            register = self.graph.graph.get_node_register(variable)
            print(str(variable) + ':' + str(register))
            if isinstance(register, int):
                self.esp -= 4
                variable_dict[variable] = str(register) + "(%ebp)"
            else:
                variable_dict[variable] = "%" + register
        print("----- homes -----")
        #print(variable_dict)
        prog = []
        prog.append('pushl %ebp')
        prog.append('movl %esp, %ebp')
        prog.append('subl $' + str(-self.esp) + ', %esp')
        prog.append('pushl %ebx')
        prog.append('pushl %esi')
        prog.append('pushl %edi')
        for line in x86IR:
            split = line.replace(",","").split(" ")
            if split[0] == 'movl' or split[0] == 'addl':
                if split[1] in variable_dict.keys():
                    split[1] = variable_dict[split[1]]
                if split[2] in variable_dict.keys():
                    split[2] = variable_dict[split[2]]
                if split[1] != split[2]:
                    prog.append(split[0] + ' ' + split[1] + ', ' + split[2])
            elif split[0] == 'call':
                if split[1] == 'print':
                    if split[2] in variable_dict.keys():
                        split[2] = variable_dict[split[2]]
                    prog.append('movl ' + split[2] + ', %eax')
                    prog.append('pushl %eax')
                    prog.append('call print_int_nl')
                    prog.append('addl $4, %esp')
                else:
                    if split[2] in variable_dict.keys():
                        split[2] = variable_dict[split[2]]
                    prog.append('call eval_input_int')
                    prog.append('movl %eax, ' + split[2])
            elif split[0] == 'neg':
                if split[1] in variable_dict.keys():
                    split[1] = variable_dict[split[1]]
                prog.append('neg ' + split[1])
            else:
                print("$$$$$ not in xIR %s $$$$$" % (split[0]))
                
            
        prog.append('popl %edi')
        prog.append('popl %esi')
        prog.append('popl %ebx')
        prog.append('movl $0, %eax')
        prog.append('movl %ebp, %esp')
        prog.append('popl %ebp')
        prog.append('ret')
        return prog
    
    def flatten_file(self, filename):
        flatten = Flatten()
        new_tree = flatten.flatten_file(filename)
        variable_list = flatten.get_variables_list(new_tree)
        return new_tree, variable_list
    
    def convert_to_ir(self, tree):
        intermediate_ir = self.convert.convert(tree)
        return intermediate_ir
    
    def do_liveness_analysis(self, intermediate_ir):
        liv = LivenessAnalysis()
        liveness_list = liv.livnessAnalysis(intermediate_ir)
        return list(reversed(liveness_list))
    
    
        



compiler = Compile()
compiler.compile(sys.argv[1])
