from control_flow_graph import Node
import ast

class Liveness():
    def __init__(self, display_liveness):
        self.display_liveness = display_liveness
        self.two_in_one_out = ['equal', 'get_subscript', 'add', 'not_equal']
        
    def analyze(self, control_graph):
        print('----- running liveness analysis -----')
        queue = [control_graph['eop']]
        while len(queue) != 0:
            # remove from queue
            node = queue.pop(0)
            liveness_list = self.livenessAnalysis(node.body, node.liveness_in)
            new_liveness_out = liveness_list[-1]
            node.liveness_list = liveness_list
            if new_liveness_out != node.liveness_out:
                node.liveness_out = new_liveness_out
                for parent in node.parents:
                    if parent.liveness_in:
                        parent.liveness_in = parent.liveness_in.union(node.liveness_out)
                    else:
                        parent.liveness_in = node.liveness_out
                    queue.append(parent)
        if self.display_liveness:
            self.display(control_graph)
        return control_graph
            
    def display(self, graph):
        print("----- liveness graph -----")
        for node in graph.values():
            print("----- %s -----" % (node.name))
            print(" parents: " + str([parent.name for parent in node.parents]))
            print("\t\t", node.liveness_list[len(node.liveness_list)-1])
            for i in range(len(node.body)):
                print(node.body[i])
                print('\t\t', node.liveness_list[len(node.liveness_list)-2-i])
            print(" children: " + str([child.name for child in node.children]))
        
    def livenessAnalysis(self, IR, liveness_in):
        current_liveness = set()
        if liveness_in != None:
            current_liveness = liveness_in
        liveness_list = []
        liveness_list.append(current_liveness)
        for i in reversed(range(len(IR))):
            instruction = IR[i].replace(","," ").split()
            #print("instruction:",instruction, current_liveness)
            if   instruction[0] == 'movl' or instruction[0] == 'movzbl':
                    current_liveness = (current_liveness - set([instruction[2]])).union(set() if instruction[1][0] == '$' else set([instruction[1]]))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'addl':
                    current_liveness = (current_liveness - set([instruction[2]])).union(set([instruction[2]]) if instruction[1][0] == '$' else set([instruction[1]] + [instruction[2]]))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'cmpl':
                    new_liveness = []
                    if instruction[1][0] != '$':
                        new_liveness += [instruction[1]]
                    if instruction[2][0] != '$':
                        new_liveness += [instruction[2]]
                    current_liveness = (current_liveness - set(new_liveness)).union(set(new_liveness))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'neg':
                    current_liveness = current_liveness.union(set() if instruction[1][0] == '$' else set([instruction[1]]))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'call':
                if instruction[1] == 'print':
                    current_liveness = current_liveness.union(set() if instruction[2][0] == '$' else set([instruction[2]]))
                    liveness_list.append(current_liveness)
                elif instruction[1] == 'eval_input' or instruction[1] == 'create_dict':
                    current_liveness = (current_liveness - set([instruction[2]]))
                    liveness_list.append(current_liveness)
                elif instruction[1] == 'set_subscript':
                    append = []
                    if instruction[3][0] != '$':
                        append.append(instruction[3])
                    if instruction[4][0] != '$':
                        append.append(instruction[4])
                    if instruction[2][0] != '$':
                        append.append(instruction[2])
                    append = set(append)
                    current_liveness = current_liveness.union(append)
                    liveness_list.append(current_liveness)
                elif instruction[1] in self.two_in_one_out:
                    append = []
                    if instruction[3][0] != '$':
                        append.append(instruction[3])
                    if instruction[4][0] != '$':
                        append.append(instruction[4])
                    append = set(append)
                    current_liveness = current_liveness.union(append) - set([instruction[2]])
                    liveness_list.append(current_liveness)
                else:
                    if len(instruction) == 4:
                        current_liveness = current_liveness.union(set() if instruction[2][0] == '$' else set([instruction[2]])) - set([instruction[3]])
                        liveness_list.append(current_liveness)
                    else:
                        liveness_list.append(current_liveness)
            elif instruction[0] == 'sete' or instruction[0] == 'setne':
                # remove %al
                    current_liveness = current_liveness - set([instruction[1]])
                    liveness_list.append(current_liveness)
            else:
                print('***** instruction %s not in liveness *****' % (instruction[0]))
        return liveness_list