class Spill():
    def __init__(self, print_info):
        self.print_info = True
        self.stack = None
    
    def check_spill(self, intermediate, stack):
        self.stack = stack
        intermediate = intermediate.replace('\t','').split('\n')
        spilled = []
        print('----- checking for spill -----')
        for i in range(len(intermediate)):
            instruction = intermediate[i].replace(',','').split(' ')
            if instruction[0] == 'movl':
                if instruction[1] in stack and instruction[2] in stack:
                    spilled.append(i)
            elif instruction[0] == 'addl':
                if instruction[1] in stack or instruction[2] in stack:
                    spilled.append(i)
            elif instruction[0] == 'neg':
                if instruction[1] in stack:
                    spilled.append(i)
            elif instruction[0] == 'cmpl':
                if instruction[2][0] == '$' or instruction[2] in stack:
                    spilled.append(i)
            elif instruction[0] == 'movzbl':
                if instruction[2] in stack:
                    spilled.append(i)
        return spilled
    
    def modify_IR(self, intermediate, spilled, spilledvars):
        intermediate = intermediate.replace('\t','').split('\n')
        print("----- removing spill -----")
                
        #print(intermediate)
        line_offset = 0
        oj = spilledvars
        spill_vars = 0
        for line_number in spilled:
            line = line_number + line_offset
            instruction = intermediate[line].replace(',','').split(' ')
            if instruction[0] == 'addl':
                spill_vars += 2
                intermediate.insert(line+1, "movl spill_" + str(spilledvars+1) + ', ' + instruction[2])
                intermediate.insert(line+1, 'addl spill_' + str(spilledvars) + ', spill_' + str(spilledvars+1))
                intermediate.insert(line+1, 'movl ' + instruction[2] + ', spill_' + str(spilledvars+1))
                intermediate.insert(line+1, 'movl ' + instruction[1] + ', spill_' + str(spilledvars))
                spilledvars += 2
                del intermediate[line]
                line_offset += 3
            elif instruction[0] == 'neg':
                spill_vars += 1
                intermediate.insert(line+1, 'movl spill_' + str(spilledvars) + ', ' + instruction[1])
                intermediate.insert(line+1, 'neg spill_' + str(spilledvars))
                intermediate.insert(line+1, 'movl ' + instruction[1] + ', spill_' + str(spilledvars))
                spilledvars += 1
                del intermediate[line]
                line_offset += 2
            elif instruction[0] == 'movl':
                spill_vars += 1
                intermediate.insert(line+1, 'movl spill_' + str(spilledvars) + ', ' + instruction[2])
                intermediate.insert(line+1, 'movl ' + instruction[1] + ', spill_' + str(spilledvars))
                spilledvars += 1
                del intermediate[line]
                line_offset += 1
            elif instruction[0] == 'cmpl':
                #if instruction[2] in self.stack:
                #    spill_vars += 2
                #    intermediate.insert(line+1, 'cmpl ' + 'spill_' + str(spilledvars) + ', spill_' + str(spilledvars+1))
                #    intermediate.insert(line+1, 'movl ' + instruction[2] + ', spill_' + str(spilledvars+1))
                #    intermediate.insert(line+1, 'movl ' + instruction[1] + ', spill_' + str(spilledvars))
                #    spilledvars += 2
                #    del intermediate[line]
                #    line_offset += 2
                #else:
                spill_vars += 1
                intermediate.insert(line+1, 'cmpl ' + instruction[2] + ', spill_' + str(spilledvars))
                intermediate.insert(line+1, 'movl ' + instruction[1] + ', spill_' + str(spilledvars))
                spilledvars += 1
                del intermediate[line]
                line_offset += 1
            elif instruction[0] == 'movzbl':
                spill_vars += 1
                intermediate.insert(line+1, 'movl spill_' + str(spilledvars) +', ' + instruction[2])
                intermediate.insert(line+1, 'movzbl ' + instruction[1] + ', spill_' + str(spilledvars))
                spilledvars += 1
                del intermediate[line]
                line_offset += 1
            else:
                print("this line spilled?")
                print(instruction)
            
        new_vars = []
        for i in range(spill_vars):
            new_vars.append("spill_" + str(i + oj))
        #print(intermediate)
        
        as_str = ''
        for line in intermediate:
            as_str += line + '\n'
        
        print("----- removed spill -----")
        return as_str, new_vars