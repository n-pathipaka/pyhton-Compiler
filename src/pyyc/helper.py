## we all add the helper functions here to use acrosss files ###



def tempVar(body = 'tmp'):
        ## generate temporary variables
        if not hasattr(tempVar, "counter"):
            tempVar.counter = 0
        tempVar.counter += 1
        return body + "_" + str(tempVar.counter)


## pushing instruction class, in future if we want we can use objects of this classes and try
class InstObj():
    '''
       create objects for instructions so that it will be easy to handle function calls
    '''

    def __init__(self):
        self.instructions = []

    def movl(self, src, dst):
        if isinstance(src, int) :
            src = "${}".format(src)
        self.instructions.append("movl {}, {}".format(str(src), str(dst)))
        return self

    def addl(self, src, dst):
        if isinstance(src, int) :
            src = "${}".format(src)
        self.instructions.append("addl {}, {}".format(str(src), str(dst)))
        return self

    def negl(self, dst):
        self.instructions.append("negl {}".format(str(dst)))
        return self

    def subl(self, src, dst):
        if isinstance(src, int):
            src = "${}".format(src)
        self.instructions.append("subl  {}, {}".format(str(src), str(dst)))
        return self

    def pushl(self, dst):
        if isinstance(src, int):
            dst = "${}".format(dst)
        self.instructions.append("pushl {}".format(str(src)))
        return self

    def popl(self, dst):
        if isinstance(src, int):
            dst = "${}".format(dst)
        self.instructions.append("popl {}".format(str(src)))
        return self

    def cmpl(self, lhs, rhs):
        if isinstance(lhs, int):
            src = "${}".format(lhs)
        else:
            src = lhs
        self.instructions.append("cmpl {}, {}".format(str(src), str(rhs)))
        return self

    def jmp(self, label):
        self.instructions.append("jmp {}".format(str(label)))
        return self

    def jne(self, label):
        self.instructions.append("jne {}".format(str(label)))
        return self