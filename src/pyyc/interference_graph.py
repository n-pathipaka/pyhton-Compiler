import sys
import ast 
from graph import Graph




class InterferenceGraph:
    def __init__(self, github):
        self.graph = Graph(github)
        
    def get_node_register(self, name):
        return self.graph.get_node_register(name)

    def create_interference_graph(self, liveness_graph, tot_variables):
        print('----- creating interference graph -----')
        #print('variables: ', tot_variables)
        ### add register as the nodes.
        self.graph.add_node('eax', 'pink')
        self.graph.add_node('ecx', 'orange')
        self.graph.add_node('edx', 'green')
        self.graph.add_node('ebx', 'yellow')
        self.graph.add_node('esi', 'red')
        self.graph.add_node('edi', 'purple')
    
        self.graph.create_nodes(tot_variables)
        
        for node in liveness_graph.values():
            self.new_IR(node.body, node.liveness_list)
        
        #self.graph.draw_graph()
        return self.graph

        
    def new_IR(self, intermediate_ir, liveness_list):
        '''
            Algo:
              for each instruction Ik 
                 if Ik is a move instruction:
                    Target interfers with all variables live after Ik, except the source variable
                 If Ik is an arthemetic op:
                    Target interfers with all variables live after Ik
                If Ik is a call:
                    caller save registers interfere with all variables live after Ik
        '''

        ##  converting  each set to a list.
        for i in range(len(liveness_list)):
            liveness_list[i] = list(liveness_list[i])
        liveness_list.reverse()
        for k in range(len(intermediate_ir)):
            instruction = intermediate_ir[k].replace(","," ").split()
            if instruction[0] == 'movl':
                if instruction[1][0] == '$':
                    for i in range(len(liveness_list[k+1])):
                        self.graph.add_edge(instruction[2], liveness_list[k+1][i])
                else:
                    ## interference with all variables live after Ik, except the source variable
                    #print("Liveness List:", liveness_list[k+1], "source:", instruction[1], "target:", instruction[2])
                    for i in range(len(liveness_list[k+1])):
                        if liveness_list[k+1][i] != instruction[1]:
                            self.graph.add_edge(instruction[2], liveness_list[k+1][i])
            elif instruction[0] == 'addl':
                for i in range(len(liveness_list[k+1])):
                    self.graph.add_edge(instruction[2], liveness_list[k+1][i])
            elif instruction[0] == 'call':
                ## caller save registers will behave as a target and interfere with all variables live after Ik. This
                # This is because the caller save registers are not preserved across function calls.
                for i in range(len(liveness_list[k+1])):
                    self.graph.add_edge('eax', liveness_list[k+1][i])
                    self.graph.add_edge('ecx', liveness_list[k+1][i])
                    self.graph.add_edge('edx', liveness_list[k+1][i])
                    self.graph.add_edge(instruction[2], liveness_list[k+1][i])
                    if len(instruction) >= 4:
                        self.graph.add_edge(instruction[3], liveness_list[k+1][i])
                    if len(instruction) >= 5:
                        self.graph.add_edge(instruction[4], liveness_list[k+1][i])
            elif instruction[0] == 'sete' or instruction[0] == 'setne':
                for i in range(len(liveness_list[k+1])):
                    self.graph.add_edge('eax', liveness_list[k+1][i])
            elif instruction[0] == 'cmpl':
                if instruction[1][0] != '$':
                    for i in range(len(liveness_list[k+1])):
                        self.graph.add_edge(instruction[1], liveness_list[k+1][i])
                elif instruction[2][0] != '$':
                    for i in range(len(liveness_list[k+1])):
                        self.graph.add_edge(instruction[2], liveness_list[k+1][i])
            elif instruction[0] == 'movzbl':
                for i in range(len(liveness_list[k+1])):
                    self.graph.add_edge(instruction[2], liveness_list[k+1][i])
            elif instruction[0] == 'neg':
                for i in range(len(liveness_list[k+1])):
                    self.graph.add_edge(instruction[1], liveness_list[k+1][i])
            else:
                print('***** instruction not recognized *****')
                print(instruction)
        

