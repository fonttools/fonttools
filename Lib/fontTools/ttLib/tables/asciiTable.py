from . import DefaultTable


class asciiTable(DefaultTable.DefaultTable):
	
	def toXML(self, writer, ttFont):
		data = self.data
		# removing null bytes. XXX needed??
		data = data.split('\0')
		data = ''.join(data)
		writer.begintag("source")
		writer.newline()
		writer.write_noindent(data.replace("\r", "\n"))
		writer.newline()
		writer.endtag("source")
		writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		lines = ''.join(content).replace("\r", "\n").split("\n")
		self.data = "\r".join(lines[1:-1])

