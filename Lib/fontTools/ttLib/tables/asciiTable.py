import string
import DefaultTable


class asciiTable(DefaultTable.DefaultTable):
	
	def toXML(self, writer, ttFont):
		data = self.data
		# removing null bytes. XXX needed??
		data = string.split(data, '\0')
		data = string.join(data, '')
		writer.begintag("source")
		writer.newline()
		writer.write_noindent(string.replace(data, "\r", "\n"))
		writer.newline()
		writer.endtag("source")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		lines = string.split(string.replace(string.join(content, ""), "\r", "\n"), "\n")
		self.data = string.join(lines[1:-1], "\r")

