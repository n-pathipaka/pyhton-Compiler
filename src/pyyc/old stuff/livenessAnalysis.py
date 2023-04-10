import ast

class LivenessAnalysis:
    def __init__(self):
        pass

    def display(self, liveness_list, n):
        print("-------- intermediate code --------")
        print("           ",liveness_list[len(liveness_list)-1])
        for i in (range(len(n))):
           print(n[i])
           print("           ",liveness_list[len(liveness_list)-2-i])
        
        print("-------- end of intermediate code --------")
        
    def livnessAnalysis(self, n):
       ## traverse a list in reverse order
       ''' 
            Algorithm for livness analysis
            Traverse backwards through the list of instructions
            Lbefore(k) = (Lafter(k) – W(k)) U R(k)
       '''

       #print("-------- start of livness analysis --------")
       current_liveness = set()
       liveness_list = []
       liveness_list.append(current_liveness)
       for i in reversed(range(len(n))):
            instruction = n[i].replace(","," ").split()
            #print("instruction:",instruction, current_liveness)
            if   instruction[0] == 'movl':
                    current_liveness = (current_liveness - set([instruction[2]])).union(set() if instruction[1][0] == '$' else set([instruction[1]]))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'addl':
                    current_liveness = (current_liveness - set([instruction[2]])).union(set([instruction[2]]) if instruction[1][0] == '$' else set([instruction[1]] + [instruction[2]]))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'neg':
                    current_liveness = current_liveness.union(set() if instruction[1][0] == '$' else set([instruction[1]]))
                    liveness_list.append(current_liveness)
            elif instruction[0] == 'call':
                if instruction[1] == 'print':
                    current_liveness = current_liveness.union(set() if instruction[2][0] == '$' else set([instruction[2]]))
                    liveness_list.append(current_liveness)
                elif instruction[1] == 'eval_input':
                    current_liveness = (current_liveness - set([instruction[2]]))
                    liveness_list.append(current_liveness)
                else:
                    liveness_list.append(current_liveness)
       #print("-------- end of livness analysis --------")

       #self.display(liveness_list, n)

       return liveness_list
 