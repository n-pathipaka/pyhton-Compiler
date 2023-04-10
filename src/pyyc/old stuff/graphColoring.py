import sys
import ast 

class GraphColoring:
    def __init__(self, github, output):
        self.priority = {
            'eax' : 6,
            'ecx' : 5,
            'edx' : 4,
            'ebx' : 3,
            'esi' : 2,
            'edi' : 1
        }
        self.stack_pos = -4
        self.registers = ['eax', 'ecx', 'edx', 'ebx', 'esi', 'edi']
        self.stack = []
        self.reg_vars = []
        self.github = github
        self.output = output
        
    def color_spill_graph(self, graph, spilled):
        self.graph = graph
        
        self.graph.update_grap_with_not_possible_reg(self.registers)
        
        cons_nodes_list = self.graph.get_constrained_nodes(self.registers)
        visited_nodes = set()
        
        #print(self.registers)
        
        # first pass with only spill variables so they get registers
        for node in cons_nodes_list:
            if node.name not in visited_nodes and node.name in spilled:
                visited_nodes.add(node.name)
                ## get the possible registers for the node
                possible_reg, color = self.graph.get_possible_register(node.name, node.npos_reg, self.priority)
                if possible_reg and possible_reg in self.registers:
                    node.color = color
                    node.reg_alloc = possible_reg 
                    self.graph.set_node_color(node.name, color)
                    self.reg_vars.append(node.name)
                    ## update the neighbors which it cannot be used
                    for  neighbor in node.neighbors:
                        if neighbor.name not in self.registers:
                            neighbor.npos_reg.add(possible_reg)
                else:
                    print("***** ERROR: spill variable on stack (%s) *****" % (node.name))
                    #print(spilled)
                    self.priority[node.name] = self.stack_pos
                    node.reg_alloc = self.stack_pos
                    self.stack_pos -= 4
                    self.stack.append(node.name)
        
        for node in cons_nodes_list:
            if node.name not in visited_nodes:
                visited_nodes.add(node.name)
                ## get the possible registers for the node
                possible_reg, color = self.graph.get_possible_register(node.name, node.npos_reg, self.priority)
                if possible_reg and possible_reg in self.registers:
                    node.color = color
                    node.reg_alloc = possible_reg 
                    self.graph.set_node_color(node.name, color)
                    self.reg_vars.append(node.name)
                    ## update the neighbors which it cannot be used
                    for  neighbor in node.neighbors:
                        if neighbor.name not in self.registers:
                            neighbor.npos_reg.add(possible_reg)
                
                else:  ## if we didn't find the possible register then we will spill it
                    ## add the varibale to the stack.
                    self.priority[node.name] = self.stack_pos
                    node.reg_alloc = self.stack_pos
                    self.stack_pos -= 4
                    self.stack.append(node.name)
                    
        self.graph.draw_graph()

        return self.stack, self.reg_vars

    def color_graph(self, graph):
        self.graph = graph
        '''
            Algo:
                for each node in the graph we will allocate registers which it cannot be used.
                Get the most constrained node and allocate the register which it can be used and update the neighbor which it cannot be used.
                Repeat the process until all the nodes are colored. if we did not get the color for a node then we will spill it.
        '''

        self.graph.update_grap_with_not_possible_reg(self.registers)


        cons_nodes_list = self.graph.get_constrained_nodes(self.registers)
        visited_nodes = set()


        for node in cons_nodes_list:
            if node.name not in visited_nodes:
                visited_nodes.add(node.name)
                ## get the possible registers for the node
                possible_reg, color = self.graph.get_possible_register(node.name, node.npos_reg, self.priority)
                if possible_reg and possible_reg in self.registers:
                    node.color = color
                    node.reg_alloc = possible_reg 
                    self.graph.set_node_color(node.name, color)
                    self.reg_vars.append(node.name)
                    ## update the neighbors which it cannot be used
                    for  neighbor in node.neighbors:
                        if neighbor.name not in self.registers:
                            neighbor.npos_reg.add(possible_reg)
                else:  ## if we didn't find the possible register then we will spill it
                    ## add the varibale to the stack.
                    self.priority[node.name] = self.stack_pos
                    node.reg_alloc = self.stack_pos
                    self.stack_pos -= 4
                    self.stack.append(node.name)
                
        ## print the colored graph
        #self.graph.updated_graph()
        self.graph.draw_graph()

        return self.stack, self.reg_vars
        
