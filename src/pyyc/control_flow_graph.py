import sys
import ast
from ast import *
#  pip install graphviz
# comment this out before uploading to github
#import graphviz

class cfg():
    def __init__(self, output_graph, github):
        # output graph to file bool
        self.output_graph = output_graph
        # dictionary of nodes based on names
        self.graph = {}
        # whether or not uploading to github
        # if we are this is true so graphviz disabled
        self.github = github
        if not self.github:
            self.dot = graphviz.Graph(comment='Control Flow Graph', strict=True)
        
    def create_graph(self, intermediate):
        # start of the program
        current_node = 'start'
        self.graph[current_node] = Node('start')
        # go through every line of intermediate representation
        for line in intermediate.split('\n'):
            # sometimes we get emptpy lines so skip those
            if len(line) == 0:
                break
            # split the line on instructions and such for easy compares
            split_line = line.replace(',','').replace('\t','').split(' ')
            # if the last symbol is : then we are in a new block
            # so make a new node, set our current node to this node
            if line[-1] == ':':
                name = line.replace(':','').replace('\t','')
                new_node = None
                if not name in self.graph.keys():
                    new_node = Node(name)
                    self.graph[name] = new_node
                    if not self.github:
                        self.dot.node(name, shape='rectangle')
                else:
                    new_node = self.graph[name]
                # python is annoying and I can't tell when it's
                # reference and when it's copy so just always edit
                # self.graph just to be sure
                if current_node:
                    self.graph[current_node].add_child(new_node)
                    self.graph[name].add_parent(self.graph[current_node])
                current_node = name
            # if it's a je then add where you're jumping to 
            # as a child of this block
            elif split_line[0] == 'je':
                name = split_line[1]
                new_node = None
                if not name in self.graph.keys():
                    new_node = Node(name)
                    self.graph[name] = new_node
                    if not self.github:
                        self.dot.node(name, shape='rectangle')
                else:
                    new_node = self.graph[name]
                self.graph[current_node].add_child(new_node)
                self.graph[name].add_parent(self.graph[current_node])
            # if it's a jmp add where you're jumping to 
            # as a child of this block but also change
            # currently active block to that block since
            # you are jmp there no matter what, you've passed control
            elif split_line[0] == 'jmp':
                name = split_line[1]
                new_node = None
                if not name in self.graph.keys():
                    new_node = Node(name)
                    self.graph[name] = new_node
                    if not self.github:
                        self.dot.node(name, shape='rectangle')
                else:
                    new_node = self.graph[name]
                self.graph[current_node].add_child(new_node)
                self.graph[name].add_parent(self.graph[current_node])
                current_node = None
            # else it's just a normal line so put that line
            # into this block
            elif split_line[0] == 'def':
                name = split_line[1].replace('\t','')
                new_node = None
                if not name in self.graph.keys():
                    new_node = Node(name)
                    self.graph[name] = new_node
                    if not self.github:
                        self.dot.node(name, shape='rectangle')
                else:
                    new_node = self.graph[name]
                current_node = name
            elif split_line[0] == 'ret':
                self.graph[current_node].add_line(line)
                current_node = 'start'
            else:
                self.graph[current_node].add_line(line)
        # make an end node so we know where to start with liveness
        # eop is just to be safe and make sure we don't find one
        # of our ends from ifs and whiles accidently
        self.graph['eop'] = Node('eop')
        self.graph['eop'].add_parent(self.graph[current_node])
        self.graph[current_node].add_child(self.graph['eop'])
        # if not github and output graph then do this
        if self.output_graph and not self.github:
            self.draw_graph()
        return self.graph
            
    # draw the graph using graph viz
    def draw_graph(self):
        for node in self.graph.values():
            # we only need to loop through children
            # because parents and children are reflections
            # so iterating on either or both is the same
            for child in node.children:
                self.dot.edge(node.name, child.name)
        self.dot.render('control_graph.gv', view=False)
        
# simple node class
class Node():
    def __init__(self, name):
        self.name = name
        self.body = []
        self.parents = set()
        self.children = set()
        # for later
        self.liveness_out = None
        self.liveness_list = None
        self.liveness_in = None
        
    # simple self explanatory helper methods
    def add_parent(self, parent):
        self.parents.add(parent)
        
    def add_child(self, child):
        self.children.add(child)
        
    def add_line(self, line):
        self.body.append(line)