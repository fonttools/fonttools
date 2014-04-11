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
    for instruction in instructions:
        instructionCons = instructionConstructor.instructionConstructor(instruction)
        instruction = instructionCons.getClass()
        try:
            print(instruction.__dict__ )
        except:
            pass
def main(args):
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
