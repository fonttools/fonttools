import string
import DefaultTable


class asciiTable(DefaultTable.DefaultTable):
	
	def toXML(self, writer, ttFont):
		writer.begintag("source")
		writer.newline()
		writer.write_noindent(string.replace(self.data, "\r", "\n"))
		writer.newline()
		writer.endtag("source")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		lines = string.split(string.replace(string.join(content, ""), "\r", "\n"), "\n")
		self.data = string.join(lines[1:-1], "\r")

