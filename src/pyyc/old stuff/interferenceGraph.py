import sys
import ast 
from graph import Graph




class InterferenceGraph:
    def __init__(self):
        self.graph = Graph()
        

    def create_interference_graph(self, intermediate_ir, liveness_list, tot_variables):

        ### add register as the nodes.
        self.graph.add_node('eax', 'pink')
        self.graph.add_node('ecx', 'orange')
        self.graph.add_node('edx', 'green')
        self.graph.add_node('ebx', 'yellow')
        self.graph.add_node('esi', 'red')
        self.graph.add_node('edi', 'purple')
    

        self.graph.create_nodes(tot_variables)

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



        #self.traverse_graph()
        #self.graph.draw_graph()

        ### return the graph object.
        return self.graph 
        

