from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from ttLib.instructions import *
import sys

class Global(object):
    def __init__(self):
        self.cvt = []
        self.function_table = []
        self.state = 1
        self.program_stack = []
    def set_cvt_table(self,cvt):
        self.cvt = cvt
    def insert_function():
        pass
class abstractExecution(object):
    def __init__(global):
        this_global = global
    def execute():

#individual tags 
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
    for i in range(len(tag_instructions)-1):
        if isinstance(tag_instructions[i],instructions.all.FDEF):
            this_fdef = tag_instructions[i]
        else:
            tag_instructions[i].set_successor(tag_instructions[i+1])
        if isinstance(tag_instructions[i],instructions.all.ENDF):
            this_fdef.set_successor(tag_instructions[i])
            #print(this_fdef.__dict__)
        if isinstance(tag_instructions[i],instructions.all.IF):
            this_if = tag_instructions[i]
        elif isinstance(tag_instructions[i],instructions.all.ELSE):
            this_if.set_successor(tag_instructions[i])
        #print(tag_instructions[i].__dict__) 
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
        #print(instruction)
        instructionCons = instructionConstructor.instructionConstructor(instruction)
        instruction = instructionCons.getClass()
        #instruction.set_pe(pe)
        if isinstance(instruction, instructionConstructor.data):
            #print(instruction)
            combineInstrcutionData(thisinstruction,instruction)
        else:
            #print("not data",instruction)
            if thisinstruction is not None:
                instructions_list.append(thisinstruction)
                #print(thisinstruction)
            thisinstruction = instruction

    #for instruct in instructions_list:
        #instruct.prettyPrinter()
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
	#print(ttf['cvt '].__dict__)
	fpgm_program = Tag('fpgm',ttf)

	#print(fpgm_program)
        constructInstructions(fpgm_program)
        constructSuccessor(fpgm_program)
        testSuccessor(fpgm_program)
	#print(fpgm_program)
        #extractFunctions(fpgm_program)
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
