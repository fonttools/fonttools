from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from ttLib.instructions import *
import sys

program_env = pe.ProgramEnvironment()
def ConstructCVTTable(values):
    key = 1
    for value in values:
        program_env.cvt_table[key] = value
        key = key + 1
def extractFunctions(fpgm_program):
    label = 1
    #for instruction in fpgm_program:
def constructInstructions(instructions):
    thisinstruction = None
    instructions_list = []
    for instruction in instructions:
        instructionCons = instructionConstructor.instructionConstructor(instruction)
        instruction = instructionCons.getClass()
        if isinstance(instruction, instructionConstructor.data):
            #print(instruction)
            combineInstrcutionData(thisinstruction,instruction)
        else:
            #print("not data",instruction)
            if instruction is not None:
                instructions_list.append(thisinstruction)
            thisinstruction = instruction 
    for instruct in instructions_list:
        try:
            instruct.prettyPrinter()
        except:
            pass
def combineInstrcutionData(instruction,data):
        instruction.add_data(data)
def main(args):
	#assume input is .ttx file
        #TODO:input is .ttf file
        input = args[0]
	ttf = TTFont()
	ttf.importXML(input,quiet=True)
	#build cvt table
	ConstructCVTTable(ttf['cvt '].values)
	#print(ttf['cvt '].__dict__)
	fpgm_program = ttf['fpgm'].program.getAssembly()
	#print(fpgm_program)
        constructInstructions(fpgm_program)
	#print(fpgm_program)
        extractFunctions(fpgm_program)
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
