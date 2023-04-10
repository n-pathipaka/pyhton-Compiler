class x86_File():
    def __init__(self, print_assembly):
        self.print_ass = print_assembly
    
    def print_file(self, x86, filename):
        print("----- writing file -----")
        final_prog = ''
        final_prog += '.globl main\n'
        final_prog += 'main:\n\t'
        for line in x86:
            final_prog += line + '\n\t'
        with open(filename.replace('.py', '.s'), 'w') as f:
            f.write(final_prog)
        if self.print_ass:
            lined = final_prog.split('\n')
            for i in range(len(lined)):
                print(str(i) + ':' + lined[i])