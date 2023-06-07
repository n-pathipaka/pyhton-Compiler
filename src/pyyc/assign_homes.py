class AssignHomes():
    def __init__(self, print_vars, print_final_IR):
        self.print_vars = print_vars
        self.print_IR = print_final_IR
        self.esp = 0
        self.append_0_1 = ['neg', 'setne', 'sete', 'je', 'jmp']
        self.one_arg_in = ['print_any', 'error_pyobj']
        self.one_arg_out = ['eval_input_pyobj', 'create_dict']
        self.one_in_one_out = ['is_int', 'inject_int', 'project_int', 'inject_bool', 
                               'project_bool', 'is_bool', 'inject_big', 'project_big', 'create_list',
                               'is_big', 'is_true']
        self.three_arg_in = ['set_subscript']
        self.two_in_one_out = ['equal', 'get_subscript', 'add', 'not_equal']
        self.change_function = {
            'print':'print_any', 
            'eval_input': 'eval_input_pyobj',
            'box_int': 'inject_int',
            'unbox_int': 'project_int',
            'box_bool': 'inject_bool',
            'unbox_bool': 'project_bool',
            'int': 'inject_int',
            'box_big': 'inject_big',
            'unbox_big': 'project_big'
        }
    def push_into_stack(self, args, prog, var_pos):
        func_id = args[1]
        arg_list = []
        #print('---- args -----')
        #print(args)
        ## args will contain call func_id arg1 arg2 arg3 .... return_value
        for arg in args[2:]:
            if arg in var_pos.keys():
                arg_list.append(var_pos[arg])
            else:
                arg_list.append(arg)
        #print('func_id , arglist:', func_id, args, arg_list)
        if len(arg_list) > 1:
            ## need to push the arguments in reverse order, just removing the first value as we store the return value their.
            for arg in reversed(arg_list[:-1]):
                prog.append('pushl '+ arg)
                
        prog.append('call '+ func_id)

        ### free the stack variables or move to the stack positon up

        l = len(args[2:-1])
        if l > 0:
            prog.append('addl $'+ str(l*4)+' , %esp')
        ## return the value
        if arg_list[-1] != 'nr':  ## does have a return value
            if arg_list[-1] != '%eax':  ## we can remove unnecessary moves as the return value is already in eax
                prog.append('movl %eax, '+ arg_list[-1] )

    
    def assign_homes(self, x86IR, variables, interference_graph):
        if self.print_IR:
            print("----- final IR -----")
            print(x86IR)
        variable_dict = {}
        print("----- assigning homes -----")
        for variable in variables:
            register = interference_graph.get_node_register(variable)
            if self.print_vars:
                print(str(variable) + ':' + str(register))
            if isinstance(register, int):
                self.esp -= 4
                variable_dict[variable] = str(register) + "(%ebp)"
            else:
                variable_dict[variable] = "%" + register
        
        x86IR = x86IR.split('def')
        isaret = None
        for line in x86IR[-1].split('\n'):
            if line.replace('\t', '').split(' ')[0] == 'ret':
                #print('$$$$$ is ret $$$$$')
                #print(line)
                isaret = line
        if isaret:
            newlines = x86IR[-1].split(isaret)
            #if newlines[1][0] == '\t':
            #    print('is tabbed')
            #    print(newlines[1])
            x86IR[-1] = newlines[0] + isaret
            x86IR.append(newlines[1])
            #print('---- found ret -----')
            #print(x86IR[-1].split(isaret)[0])
            #print('the other')
            #print(x86IR[-1].split(isaret)[1])
        #for somethin in x86IR:
        #    print('---- somethin ----')
        #    print(somethin)
        #print(x86IR[-1])
        #for line in x86IR[-1].split('\n'):
            #print(line.split(' ')[0])
            #if line.split(' ')[0] == 'ret':
            #    x86IR[-1] = x86IR.split(line)[0]
            #    x86IR[-1].append(line)
            #    x86IR.append(x86IR.split(line)[1])
        progfuncs = []
        for function in x86IR[:-1]:
            if len(function.split('\n')) < 2:
                continue
            #print('----- is func -----')
            #print(function)
            funcname = function.split('\n')[0]
            #print(funcname)
            progfuncs.append('.globl ' + funcname)
            progfuncs.append(funcname + ':')
            prog = []
            prog.append('pushl %ebp')
            prog.append('movl %esp, %ebp')
            prog.append('subl $' + str(-self.esp) + ', %esp')
            prog.append('pushl %ebx')
            prog.append('pushl %esi')
            prog.append('pushl %edi')
            for line in function.split('\n')[1:]:
                #print(line)
                split = line.replace(',','').replace('\t','').split(' ')
                if split[0] == 'movl' or split[0] == 'movzbl':
                    if split[1] in variable_dict.keys():
                        split[1] = variable_dict[split[1]]
                    if split[2] in variable_dict.keys():
                        split[2] = variable_dict[split[2]]
                    if split[1] != split[2]:
                        prog.append('\t' + split[0] + ' ' + split[1] + ', ' + split[2])
                elif split[0] == 'call':
                    if split[1] in self.change_function.keys():
                            split[1] = self.change_function[split[1]] 
                    if split[1] in self.one_arg_in:
                        split.append('nr')
                        self.push_into_stack(split, prog, variable_dict)
                    elif split[1] in self.one_arg_out:
                        self.push_into_stack(split, prog, variable_dict)
                    elif split[1] in self.one_in_one_out:
                        self.push_into_stack(split, prog, variable_dict)
                    elif split[1] in self.two_in_one_out:
                        for i in range(len(split[2:])):
                            if split[i+2] in variable_dict.keys():
                                split[i+2] = variable_dict[split[i+2]]
                        prog.append('pushl ' + split[4])
                        prog.append('pushl ' + split[3])
                        prog.append('call ' + split[1])
                        prog.append('addl $8, %esp')
                        prog.append('movl %eax, ' + split[2])
                    elif split[1] in self.three_arg_in:
                        for i in range(len(split[2:])):
                            if split[i+2] in variable_dict.keys():
                                split[i+2] = variable_dict[split[i+2]]
                        prog.append('pushl ' + split[4])
                        prog.append('pushl ' + split[3])
                        prog.append('pushl ' + split[2])
                        prog.append('call ' + split[1])
                        prog.append('addl $12, %esp')
                    else:
                        self.push_into_stack(split, prog, variable_dict)
                        #prog.append('idk ' + str(split))
                elif split[0] == 'cmpl' or split[0] == 'addl':
                    if split[1] in variable_dict.keys():
                        split[1] = variable_dict[split[1]]
                    if split[2] in variable_dict.keys():
                        split[2] = variable_dict[split[2]]
                    prog.append(split[0] + ' ' + split[1] + ', ' + split[2])
                elif split[0] in self.append_0_1:
                    if split[1] in variable_dict.keys():
                        split[1] = variable_dict[split[1]]
                    prog.append(split[0] + ' ' + split[1])
                elif split[0] == 'ret':
                    if split[1] in variable_dict.keys():
                        split[1] = variable_dict[split[1]]
                    prog.append('movl ' + split[1] + ', %eax')
                    prog.append('popl %edi')
                    prog.append('popl %esi')
                    prog.append('popl %ebx')
                    prog.append('movl %ebp, %esp')
                    prog.append('popl %ebp')
                    prog.append('ret')
                else:
                    if len(split[0]) == 0:
                        break;
                    if split[0][-1] == ':':
                        prog.append(split[0])
                    else:
                        print("$$$$$ not in xIR funcs %s $$$$$" % (split[0]))
            for i in range(len(prog)):
                prog[i] = '\t' + prog[i]
            progfuncs += prog
        
        prog = []
        prog.append('pushl %ebp')
        prog.append('movl %esp, %ebp')
        prog.append('subl $' + str(-self.esp) + ', %esp')
        prog.append('pushl %ebx')
        prog.append('pushl %esi')
        prog.append('pushl %edi')
        for line in x86IR[-1].split('\n'):
            #print('line?????')
            #print(line)
            split = line.replace(",","").replace('\t','').split(" ")
            if split[0] == 'movl' or split[0] == 'movzbl':
                if split[1] in variable_dict.keys():
                    split[1] = variable_dict[split[1]]
                if split[2] in variable_dict.keys():
                    split[2] = variable_dict[split[2]]
                if split[1] != split[2]:
                    prog.append(split[0] + ' ' + split[1] + ', ' + split[2])
            elif split[0] == 'call':
                if split[1] in self.change_function.keys():
                        split[1] = self.change_function[split[1]]
                        
                if split[1] in self.one_arg_in:
                    split.append('nr')
                    self.push_into_stack(split, prog, variable_dict)
                    # if split[2] in variable_dict.keys():
                    #     split[2] = variable_dict[split[2]]
                    # prog.append('movl ' + split[2] + ', %eax')
                    # prog.append('pushl %eax')
                    # prog.append('call ' + split[1])
                    # #prog.append('call print_any')
                    # prog.append('addl $4, %esp')
                elif split[1] in self.one_arg_out:
                    self.push_into_stack(split, prog, variable_dict)
                    # if split[2] in variable_dict.keys():
                    #     split[2] = variable_dict[split[2]]
                    # prog.append('call ' + split[1])
                    # prog.append('movl %eax, ' + split[2])
                elif split[1] in self.one_in_one_out:
                    self.push_into_stack(split, prog, variable_dict)
                    # if split[2] in variable_dict.keys():
                    #     split[2] = variable_dict[split[2]]
                    # if split[3] in variable_dict.keys():
                    #     split[3] = variable_dict[split[3]]
                    # prog.append('movl ' + split[2] + ', %eax')
                    # prog.append('pushl %eax')
                    # prog.append('call ' + split[1])
                    # prog.append('addl $4, %esp')
                    # prog.append('movl %eax, ' + split[3])
                elif split[1] in self.two_in_one_out:
                    #self.push_into_stack(split, prog, variable_dict)
                    for i in range(len(split[2:])):
                        if split[i+2] in variable_dict.keys():
                            split[i+2] = variable_dict[split[i+2]]
                    prog.append('pushl ' + split[4])
                    prog.append('pushl ' + split[3])
                    prog.append('call ' + split[1])
                    prog.append('addl $8, %esp')
                    prog.append('movl %eax, ' + split[2])
                    
                elif split[1] in self.three_arg_in:
                    for i in range(len(split[2:])):
                        if split[i+2] in variable_dict.keys():
                            split[i+2] = variable_dict[split[i+2]]
                    #prog.append('movl ' + split[2] + ', %eax')
                    prog.append('pushl ' + split[4])
                    #prog.append('movl ' + split[3] + ', %eax')
                    prog.append('pushl ' + split[3])
                    #prog.append('movl ' + split[4] + ', %eax')
                    prog.append('pushl ' + split[2])
                    prog.append('call ' + split[1])
                    prog.append('addl $12, %esp')
                else:
                    self.push_into_stack(split, prog, variable_dict)
                    #prog.append('call ' + split[1])
                    #if split[-1] in variable_dict.keys():
                    #    split[-1] = variable_dict[split[-1]]
                    #prog.append('movl %eax, ' + split[-1])
                    #prog.append('idk ' + str(split[-1]))
            elif split[0] == 'cmpl' or split[0] == 'addl':
                if split[1] in variable_dict.keys():
                    split[1] = variable_dict[split[1]]
                if split[2] in variable_dict.keys():
                    split[2] = variable_dict[split[2]]
                prog.append(split[0] + ' ' + split[1] + ', ' + split[2])
            elif split[0] in self.append_0_1:
                if split[1] in variable_dict.keys():
                    split[1] = variable_dict[split[1]]
                prog.append(split[0] + ' ' + split[1])
            else:
                if len(split[0]) == 0:
                    continue
                if split[0][-1] == ':':
                    prog.append(split[0])
                else:
                    print("$$$$$ not in xIR %s $$$$$" % (split[0]))
            
        prog.append('popl %edi')
        prog.append('popl %esi')
        prog.append('popl %ebx')
        prog.append('movl $0, %eax')
        prog.append('movl %ebp, %esp')
        prog.append('popl %ebp')
        prog.append('ret')
        for i in range(len(prog)):
            prog[i] = '\t' + prog[i]
        prog.insert(0, '.globl main')
        prog.insert(1, 'main:')
        prog = progfuncs + prog
        return prog