import DefaultTable

class table_D_S_I_G_(DefaultTable.DefaultTable):
	
	def toXML(self, xmlWriter, ttFont):
		xmlWriter.comment("note that the Digital Signature will be invalid after recompilation!")
		xmlWriter.newline()
		xmlWriter.begintag("hexdata")
		xmlWriter.newline()
		xmlWriter.dumphex(self.compile(ttFont))
		xmlWriter.endtag("hexdata")
		xmlWriter.newline()
