import sys
import ast
from ast import *
from flatten import Flatten


class ConvertToIR:

    def __init__(self):
        pass

    def convertTo86(self, n, intermediate, var):
        if isinstance(n, Module):
            for node in n.body:
                self.convertTo86(node, intermediate, var)
        elif isinstance(n, Assign):
            if  (isinstance(n.value, Name) or isinstance(n.value, Constant)) and isinstance(n.targets[0], Name) :
                intermediate.append('movl ' + self.convertTo86(n.value, intermediate, var) + ', ' + n.targets[0].id)
            else:
                self.convertTo86(n.value, intermediate, n.targets[0].id)
        elif isinstance(n, Expr):
            if isinstance(n.value, Call):
                self.convertTo86(n.value, intermediate, var)
        elif isinstance(n, Constant):
            return '$' + str(n.value)
        elif isinstance(n, Name):
            return n.id
        elif isinstance(n, Call):
            if n.func.id == 'print':
                intermediate.append('call ' + n.func.id + ', ' + self.convertTo86(n.args[0], intermediate, var))
            if n.func.id == 'eval':
                #intermediate.append('call eval_input_int, ' + self.convertTo86(n.args[0], intermediate, var))
                intermediate.append('call eval_input, ' + var)
                #intermediate.append('movl %, ' + var)
            for arg in n.args:
                self.convertTo86(arg, intermediate, var)
        elif isinstance(n, UnaryOp):
            intermediate.append('movl ' + self.convertTo86(n.operand, intermediate, var) + ', ' + var)
            intermediate.append(self.convertTo86(n.op, intermediate, var) + var )
        elif isinstance(n, BinOp):
            if not isinstance(n.left, Constant) and n.left.id == var:
                intermediate.append(
                    self.convertTo86(n.op, intermediate, var) 
                    + self.convertTo86(n.right, intermediate, var) 
                    + ', ' 
                    + self.convertTo86(n.left, intermediate, var) 
                )
            elif not isinstance(n.right, Constant) and n.right.id == var:
                intermediate.append(
                    self.convertTo86(n.op, intermediate, var) 
                    + self.convertTo86(n.left, intermediate, var) 
                    + ', ' 
                    + self.convertTo86(n.right, intermediate, var) )
            else:
                intermediate.append('movl ' + self.convertTo86(n.left, intermediate, var) + ', ' + var )
                intermediate.append(self.convertTo86(n.op, intermediate, var) + self.convertTo86(n.right, intermediate, var) + ', ' + var)
        elif isinstance(n, Add):
            return 'addl '
        elif isinstance(n, USub):
            return 'neg '
        elif isinstance(n, Load):
            return
        elif isinstance(n, Store):
            return
        else:
            raise Exception('Error: unrecognized AST node')
        
    def checkSpill(self, IR, stack):
        spilled = []
        for i in range(len(IR)):
            instruction = IR[i].replace(',','').split(' ')
            if instruction[0] == 'movl':
                if instruction[1] in stack and instruction[2] in stack:
                    spilled.append(i)
            elif instruction[0] == 'addl':
                if instruction[1] in stack or instruction[2] in stack:
                    spilled.append(i)
            elif instruction[0] == 'neg':
                if instruction[1] in stack:
                    spilled.append(i)
        return spilled

    def modify_IR(self, intermediate, spilled, spilledvars):
        ''' Need to work on this function.  Don't have clear idea on how to modify the IR
            Do we need to convert to ast and manipulate or can we do it directly on the IR.
        '''
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
            else:
                print("this line spilled?")
                print(instruction)
            
        new_vars = []
        for i in range(spill_vars):
            new_vars.append("spill_" + str(i + oj))
        #print(intermediate)

        print("----- removed spill -----")
        return intermediate, new_vars
        
    ## converts to intermediate representation ##

    def convert(self, new_tree):
        intermediate = []
        self.convertTo86(new_tree, intermediate, 'n')
        for i in range(len(intermediate)):
            print(intermediate[i])
        return intermediate



    



