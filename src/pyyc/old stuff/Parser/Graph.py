import sys
import ast 
import graphviz

class Node:
    ## need to add the neighbors and the color ##
    def __init__(self, name = None, color='white', dot=None, neighbors=[], npos_reg=set()):
        self.name = name
        self.color = color
        self.neighbors = neighbors
        self.npos_reg = npos_reg
        self.constrained = 0
        self.reg_alloc = None
        if name:
            dot.node(self.name, fillcolor=self.color, style='filled', shape='circle')

    def __repr__(self):
        return f"{self.name} ({self.color})"
    
    def set_color(self, name, color, nodes, dot):
        node = self.search_node(name, nodes)
        if node:
            node.color = color
            dot.node(node.name, fillcolor=color, style="filled", shape="circle")
    
    def search_node(self, name, nodes):
        for node in nodes:
            if node.name == name:
                return node
        return None
    

class Graph:
    node = Node()
    def __init__(self):
        self.dot = graphviz.Graph(comment='Interference Graph', strict=True)
        self.nodes = []
        self.edges = {}
        

    def create_nodes(self, nodes_list, color=None):
        for node in nodes_list:
            self.nodes.append(Node(node, color, self.dot, [], set()))
        
        self.edges = {}

    def add_node(self, name, color=None):
        self.nodes.append(Node(name, color, self.dot, [], set()) )
        
    def add_edge(self, node1, node2):
        ## get the node1 object and add node2 to its neighbors
        if node1 != node2:
            node1_obj = self.node.search_node(node1, self.nodes)
            node2_obj = self.node.search_node(node2, self.nodes)
            if node1_obj:
                ## I dont want to add the same node twice
                if node2_obj not in node1_obj.neighbors:
                    node1_obj.neighbors.append(node2_obj)
                    node1_obj.constrained += 1
            if node2_obj:
                if node1_obj not in node2_obj.neighbors:
                    node2_obj.neighbors.append(node1_obj)
                    node2_obj.constrained += 1
    
    def get_constrained_nodes(self, registers):
        ## get the constarined nodes in the graph in decreasing order except the registers.
        constrained_nodes = []
        for node in self.nodes:
            if node.name not in registers:
                constrained_nodes.append((node.constrained, node))
                constrained_nodes.sort(key=lambda x: x[0], reverse=True)
        return [node[1] for node in constrained_nodes]
    
    def update_grap_with_not_possible_reg(self, registers):
        for node in self.nodes:
            for neighbor in node.neighbors:
               if node.name not in registers and neighbor.name in registers:
                   node.npos_reg.add(neighbor.name)
                   #print("adding neighbor:", neighbor.name,  node.npos_reg)

    def get_possible_register(self, name, npos_reg, registers):
        ## traverse the registers 
        priority_registers = dict(sorted(registers.items(), key=lambda x: x[1], reverse=True))
        ## if npos_reg is empty then return the first register
        if not npos_reg:
            return list(priority_registers.keys())[0], self.node.search_node(list(priority_registers.keys())[0], self.nodes).color
        for reg in priority_registers:
            if reg not in npos_reg:
                return reg, self.node.search_node(reg, self.nodes).color
        return None, None
            
       
        
    def set_node_color(self, name , color):
        self.dot.node(name, fillcolor=color, style="filled", shape="circle")
        
        

    ### just using graphviz to draw the graph
    def draw_graph(self):
        for node in self.nodes:
            for neighbor in node.neighbors:
                self.dot.edge(node.name, neighbor.name)
        self.dot.render('interference_graph.gv', view=True)

    def updated_graph(self):
        self.dot.render('interference_graph.gv', view=True)
    
