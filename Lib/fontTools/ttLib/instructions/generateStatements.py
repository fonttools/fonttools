import os
'''
five categories of instructions:
   Pushing data onto the interpreter stack
   Managing the Storage Area
   Managing the Control Value Table
   Modifying Graphics State settings
   Managing outlines
   General purpose instructions
'''

from fontTools.ttLib.tables.ttProgram import instructions

def emit(stream, line, level=0):
    indent = "    "*level
    stream.write(indent + line + "\n")
 
def constructInstructionClasses(instructionList):
    HEAD = """ # WARNING: do not modify; generated code! See generateStatements.py and ../tables/ttProgram.py
class root_statement(object):
    def __init__(self):
	self.data = []
        #one instruction may have mutiple successors
        self.successors = [] 
        #one instruction has one predecessor
        self.predecessor = None
        self.top = None
        self.id = (0, 0)

    def add_successor(self,successor):
        self.successors.append(successor)
    def set_predecessor(self, predecessor):
        self.predecessor = predecessor
    def add_data(self,new_data):
        self.data.append(new_data)
    def get_pop_num(self):
        return self.pop_num
    def get_push_num(self):
        return self.push_num
    def get_result(self):
        return self.data
    def prettyPrint(self):
        print(self.__class__.__name__,self.data)
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__.split("_")[0],map(lambda x:x.value, self.data))
class all():
"""

    here = os.path.dirname(__file__)
    out_file = os.path.join(here, ".", "statements.py")
    fp = open(out_file, "w")
    try:
        fp.write(HEAD)
        emit(fp,"class PUSH_Statement(root_statement):",1)
        emit(fp,"def __init__(self):",2)
        emit(fp,"root_statement.__init__(self)",3)
        emit(fp,"self.push_num = len(self.data)",3)
        emit(fp,"self.mnemonic = 'PUSH'",3)
        emit(fp,"self.pop_num = 0",3)
        emit(fp,"def get_push_num(self):",2)
        emit(fp,"return len(self.data)",3)
        emit(fp,"class PUSHB_Statement(PUSH_Statement):",1)
        emit(fp,"def __init__(self):",2)
        emit(fp,"root_statement.__init__(self)",3)
        emit(fp,"self.push_num = len(self.data)",3)
        emit(fp,"self.pop_num = 0",3)
        emit(fp,"self.mnemonic = 'PUSHB'",3)
        emit(fp,"def get_push_num(self):",2)
        emit(fp,"return len(self.data)",3)
        emit(fp,"class NPUSHB_Statement(PUSH_Statement):",1)
        emit(fp,"def __init__(self):",2)
        emit(fp,"root_statement.__init__(self)",3)
        emit(fp,"self.push_num = len(self.data)",3)
        emit(fp,"self.pop_num = 0",3)
        emit(fp,"self.mnemonic = 'NPUSHB'",3)
        emit(fp,"def get_push_num(self):",2)
        emit(fp,"return len(self.data)",3)
        emit(fp,"class PUSHW_Statement(PUSH_Statement):",1)
        emit(fp,"def __init__(self):",2)
        emit(fp,"root_statement.__init__(self)",3)
        emit(fp,"self.push_num = len(self.data)",3)
        emit(fp,"self.pop_num = 0",3)
        emit(fp,"self.mnemonic = 'PUSHW'",3)
        emit(fp,"def get_push_num(self):",2)
        emit(fp,"return len(self.data)",3)
        emit(fp,"class NPUSHW_Statement(PUSH_Statement):",1)
        emit(fp,"def __init__(self):",2)
        emit(fp,"root_statement.__init__(self)",3)
        emit(fp,"self.push_num = len(self.data)",3)
        emit(fp,"self.pop_num = 0",3)
        emit(fp,"self.mnemonic = 'NPUSHW'",3)
        emit(fp,"def get_push_num(self):",2)
        emit(fp,"return len(self.data)",3)
        for op, mnemonic, argBits, name, pops, pushes in instructionList:
            emit(fp,"class %s_Statement(root_statement):" % (mnemonic),1)
            emit(fp,"def __init__(self):", 2)
            emit(fp,"root_statement.__init__(self) ", 3)
            emit(fp,"self.opcode = %s" %(op), 3)
            emit(fp,"self.mnemonic = '%s'" %(mnemonic), 3)
            emit(fp,"self.name = '%s'" %(name), 3)
            emit(fp,"self.push_num =  %s "  %(pushes), 3)
            if pops>=0:
                emit(fp,"self.pop_num =  %s "  %(pops), 3)
            else:
                emit(fp,"self.pop_num =   'ALL' ", 3)
            if pops>=0:
                emit(fp,"self.total_num = %s" %(pushes-pops),3)
    finally:
        fp.close()

if __name__ == "__main__":
    constructInstructionClasses(instructions)
