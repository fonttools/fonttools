from . import DefaultTable
import json

class table_D__e_b_g(DefaultTable.DefaultTable):

	def decompile(self, data, ttFont):
		self.data = json.loads(data)

	def compile(self, ttFont):
		return str.encode(json.dumps(self.data))

	def toXML(self, writer, ttFont):
		writer.writecdata(self.compile(ttFont).decode())

	def fromXML(self, name, attrs, content, ttFont):
		self.data = json.loads(content)
