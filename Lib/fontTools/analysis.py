from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from ttLib.instructions import *
import sys

class Global(object):
    def __init__(self):
        self.cvt = []
        self.function_table = {}
        self.state = 1
        self.program_stack = []
    def set_cvt_table(self,cvt):
        self.cvt = cvt
    def insert_function():
        pass

class AbstractExecutor(object):
    def __init__(self,prgm_global):
        self.global_env = prgm_global
        
    def execute(self,instruction):
        self.data = []
        #get data from global, feed it to instructions
        self.program_stack = self.global_env.program_stack
        self.instruction = instruction
        if len(self.program_stack)>0:
            self.instruction.set_top(self.program_stack[-1])

        if self.instruction.get_pop_num()> 0: 
            for i in range(self.instruction.get_pop_num()):
                self.data.append(self.program_stack[-1])
                self.program_stack.pop()
           
            
        
        if self.instruction.get_push_num()> 0:
            if len(self.data) > 0:
                self.instruction.set_input(self.data)
            self.instruction.action()
            self.result = self.instruction.get_result()
            for data in self.result:
                self.global_env.program_stack.append(data)

        
        if isinstance(self.instruction,instructions.all.FDEF):
            self.global_env.function_table[self.instruction.top] = self.instruction.data


class Tag(object):
    def __init__(self,tag,ttf,id=0):
        self.tag = tag

        self.instructions = ttf[self.tag].program.getAssembly()
       
        self.pe = pe.ProgramEnvironment()
        self.id = id 
    def set_instructions(instructions):
        self.instructions = instructions
    def set_pe(pe):
        self.pe = pe

global_env = Global()
def constructSuccessor(tag):
    tag_instructions = tag.instructions
    this_fdef = None

    for i in range(len(tag_instructions)):
        if this_fdef is not None and this_fdef.get_successor() is None:
            this_fdef.data.append(tag_instructions[i])
        #recording function instructions if this FDEF hasn't met ENDF yet
        if isinstance(tag_instructions[i],instructions.all.FDEF):
            this_fdef = tag_instructions[i]
        elif i < len(tag_instructions)-1:
            tag_instructions[i].set_successor(tag_instructions[i+1])

        if isinstance(tag_instructions[i],instructions.all.ENDF):
           
            this_fdef.set_successor(tag_instructions[i])
        
        if isinstance(tag_instructions[i],instructions.all.IF):
            this_if = tag_instructions[i]
        elif isinstance(tag_instructions[i],instructions.all.ELSE):
            this_if.set_successor(tag_instructions[i])
        
        
        

   
        
def ConstructCVTTable(values):
    key = 1
    cvt_table = {}
    for value in values:
        cvt_table[key] = value
        key = key + 1
    global_env.set_cvt_table(cvt_table)
def extractFunctions(fpgm_program):
    label = 1
    #for instruction in fpgm_program:
def constructInstructions(tag):
    thisinstruction = None
    instructions_list = []
    instructions = tag.instructions

    for instruction in instructions:
        
        instructionCons = instructionConstructor.instructionConstructor(instruction)
        instruction = instructionCons.getClass()
        
        if isinstance(instruction, instructionConstructor.data):
            
            combineInstrcutionData(thisinstruction,instruction)
        else:
           
            if thisinstruction is not None:
                instructions_list.append(thisinstruction)
               
            thisinstruction = instruction

    instructions_list.append(thisinstruction)
    tag.instructions = instructions_list
    
def combineInstrcutionData(instruction,data):
        instruction.add_data(data)
def testSuccessor(tag):
        instruction = tag.instructions[0]
        
        while instruction.get_successor() is not None:
            
            instruction.prettyPrinter()
            instruction = instruction.get_successor()
    
def main(args):
	#assume input is .ttx file
        #TODO:input is .ttf file
        input = args[0]
	ttf = TTFont()
	ttf.importXML(input,quiet=True)
	#build cvt table
	ConstructCVTTable(ttf['cvt '].values)
	fpgm_program = Tag('fpgm',ttf)


        constructInstructions(fpgm_program)
        constructSuccessor(fpgm_program)
        #testSuccessor(fpgm_program)
        font_global = Global()
        executor = AbstractExecutor(font_global)

        instruction = fpgm_program.instructions[0]
        
        while instruction.get_successor() is not None:
            executor.execute(instruction)
            instruction.prettyPrinter()
            instruction = instruction.get_successor()

        for key,value in font_global.function_table.items():
            print(key,value)
	'''
	prep_program = ttf['prep'].program.getAssembly()

	glyfs_ids = ttf['glyf'].glyphOrder
	for glyf in glyfs_ids:
		try:
			glyfinstructions = ttf['glyf'][glyf].program.getAssembly()
			#print(glyfinstructions)
		except:
			pass
	'''

	
if __name__ == "__main__":
	main(sys.argv[1:])
