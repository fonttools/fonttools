from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from . import DefaultTable
from . import ttProgram

class table__f_p_g_m(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		program = ttProgram.Program()
		program.fromBytecode(data)
		self.program = program
	
	def compile(self, ttFont):
		return self.program.getBytecode()
	
	def toXML(self, writer, ttFont):
		self.program.toXML(writer, ttFont)
		writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		program = ttProgram.Program()
		program.fromXML(name, attrs, content, ttFont)
		self.program = program
	
	def __len__(self):
		return len(self.program)

