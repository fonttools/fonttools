import os
import sys
# next, the list of "normal" instructions
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

cvt_table_related = ['RCVT','WCVTF','WCVTP','SCVTCI']
storage_area_related = ['WS','RS']
graphics_state_related = ['SVTCA','SPVTCA','SFVTCA','SPVTL','SFVTL','SFVTPV','SDPVTL','SVPTL','SPVFS','SFVFS','SRP0']
function_table_related = ['FDEF','ENDF']
repeat_instruction = ['ALIGNRP','FLIPPT','IP','SHP','SHPIX']
skip_graphics_state_related  = True
def emit(stream, line, level=0):
        indent = "    "*level
        stream.write(indent + line + "\n")
def constructInstructionClasses(instructionList):
	HEAD = """#instructions classes are generated from instructionList
class root_instruct(object):
    def __init__(self):
	self.data = []
        self.successor = [] 
        self.top = None
    def add_data(self,new_data):
        self.data.append(new_data.value)
    def set_top(self,value):
        self.top = value
    def get_pop_num(self):
        return self.pop_num
    def get_push_num(self):
        return self.push_num
    def set_input(self,data):
        self.data = data
    def successor_size(self):
        return len(self.successor)
    def get_successor(self,index=0):
        return self.successor[index]
    def add_successor(self,successor):
        self.successor.append(successor)

    def get_result(self):
        return self.data
    def prettyPrinter(self):
        print(self.__class__.__name__,self.data,self.top)
class all():
"""

        here = os.path.dirname(__file__)
   	out_file = os.path.join(here, ".", "instructions.py")
	fp = open(out_file, "w")
        try:
            fp.write(HEAD)
            emit(fp,"class PUSH(root_instruct):",1)
            emit(fp,"def __init__(self):",2)
            emit(fp,"root_instruct.__init__(self)",3)
            emit(fp,"self.push_num = len(self.data)",3)
            emit(fp,"self.pop_num = 0",3)
            emit(fp,"def get_push_num(self):",2)
            emit(fp,"return len(self.data)",3)
            emit(fp,"def action(self):",2)
            emit(fp,"pass ",3)
            emit(fp,"")
            for op, mnemonic, argBits, name, pops, pushes in instructionList:
                emit(fp,"class %s(root_instruct):" % (mnemonic),1)
                emit(fp,"def __init__(self):", 2)
                emit(fp,"root_instruct.__init__(self) ", 3)
                if pops != 0 and pushes != 0:
                    emit(fp, "self.in_source = 'program_stack' ",3)
                    emit(fp, "self.out_source = 'program_stack'",3)
                elif pops == 0 and pushes != 0:
                    if op in cvt_table_related:
                        emit(fp,"self.in_source = 'cvt'",3)
                    elif op in storage_area_related:
                        emit(fp,"self.in_source = 'storage_area'",3)
                    else:
                        emit(fp,"self.in_source = 'None'",3)
                    emit(fp,"self.out_source = 'program_stack'",3)
                elif pushes == 0 and pops != 0:
                    emit(fp,"self.in_source = 'program_stack'",3)
                    if op in cvt_table_related:
                        emit(fp,"self.out_source = 'cvt'",3)
                    elif op in storage_area_related:
                        emit(fp,"self.out_source = 'storage_area'",3)
                    else:
                        emit(fp,"self.out_source = 'None'",3)
                else:
                    emit(fp,"self.in_source = 'self'",3)
                    emit(fp,"self.out_source = 'graphic_state'",3)
                emit(fp,"self.push_num =  %s "  %(pushes), 3)
                if pops>=0:
                    emit(fp,"self.pop_num =  %s "  %(pops), 3)
                else:
                    emit(fp,"self.pop_num =   'ALL' ", 3)
                if pops>=0:
                    emit(fp,"self.total_num = %s" %(pushes-pops),3)
                emit(fp,"def action(self, input):", 2)
                emit(fp,"pass ", 3)
                emit(fp,"")
        finally:
            fp.close()

if __name__ == "__main__":
    constructInstructionClasses(instructions)
