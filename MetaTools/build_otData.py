#! /usr/bin/env python


"""This script builds the Lib/fontTools/ttLib/tables/otData.py file
from the OpenType HTML documentation. However, it depends on a slightly
patched version the the HTML, as there are some inconsistencies in the
markup and the naming of certain fields. See doco.diff for differences,
but this is probably against a slightly older version of the documentation
than what is currently online. The documentation was taken from this URL:
	http://www.microsoft.com/typography/otspec/default.htm
"""


from sgmllib import SGMLParser


class HTMLParser(SGMLParser):
	
	def __init__(self):
		SGMLParser.__init__(self)
		self.data = None
		self.currenttable = None
		self.lastcaption = None
	
	def handle_data(self, data):
		if self.data is not None:
			self.data.append(data)
	
	def start_i(self, attrs):
		if self.currenttable is None:
			self.data = []
	def end_i(self):
		if self.currenttable is None:
			self.lastcaption = " ".join(self.data)
			self.data = None
	
	def start_b(self, attrs):
		if self.currenttable is None:
			self.data = []
	def end_b(self):
		if self.currenttable is None:
			self.lastcaption = " ".join(self.data)
			self.data = None
	
	def start_table(self, attrs):
		attrs = dict(attrs)
		if attrs.get('width') in ('455', '460'):
			#print "---", attrs
			self.currenttable = []
		else:
			self.currenttable = None
	def end_table(self):
		if self.currenttable is not None and self.lastcaption is not None:
			if self.currenttable[0] == ['Type', 'Name', 'Description'] or \
					self.currenttable[0] == ['Value', 'Type', 'Description']:
				caption = self.lastcaption.split()
				name = caption[0]
				if name == "LookupType" or name == "LookupFlag":
					self.currenttable = None
					return
				elif name == "Device":
					if "Tables" in caption:
						# XXX skip this one
						self.currenttable = None
						return
				buildTable(name, self.currenttable[1:], self.lastcaption)
		self.currenttable = None
	
	def start_tr(self, attrs):
		if self.currenttable is not None:
			self.currenttable.append([])
	def end_tr(self):
		pass
	
	def start_td(self, attrs):
		self.data = []
	def end_td(self):
		if self.currenttable is not None and self.data is not None:
			self.currenttable[-1].append(" ".join(self.data))
			self.data = None


globalDups = {}
localDups = {}
not3 = []

def buildTable(name, table, caption):
	if globalDups.has_key(name):
		globalDups[name].append(caption)
	else:
		globalDups[name] = [caption]
	print "\t(%s, [" % repr(name)
	allFields = {}
	for row in table:
		row = [" ".join(x.split()) for x in row]
		if len(row) <> 3:
			not3.append(row)
		row = makeRow(row)
		fieldName = row[1]
		if allFields.has_key(fieldName):
			key = (name, fieldName)
			localDups[key] = 1
		allFields[fieldName] = 1
		print "\t\t%s," % (tuple(row),)
	print "\t]),"
	print


def makeRow(rawRow):
	tp, name = rawRow[:2]
	name = name.strip()
	rest = tuple(rawRow[2:])
	if '[' in name:
		name, repeat = name.split("[")
		name = name.strip()
		assert repeat[-1] == "]"
		repeat = repeat[:-1].split()
		if repeat[1:]:
			repeatOffset = int("".join(repeat[1:]))
		else:
			repeatOffset = 0
		if not repeat:
			repeat = ""
		else:
			repeat = repeat[0]
	else:
		repeat = None
		repeatOffset = None
	row = (tp, name, repeat, repeatOffset) + rest
	return row


if __name__ == "__main__":
	import sys, os
	if "-" not in sys.argv:
		sys.stdout = open("otData.py", "w")
	print "otData = ["
	for file in ["chapter2.htm", "gpos.htm", "gsub.htm", "gdef.htm", "base.htm", "jstf.htm"]:
		name = os.path.splitext(file)[0]
		if name == "chapter2":
			name = "common"
		print
		print "\t#"
		print "\t# %s (generated from %s)" % (name, file)
		print "\t#"
		print 
		p = HTMLParser()
		p.feed(open(file).read())
		p.close()
	print "]"
	print
	for k, v in globalDups.items():
		if len(v) > 1:
			print "# XXX duplicate table name:", k, v
	for (name, fieldName), v in localDups.items():
		print "# XXX duplicate field name '%s' in table '%s'" % (fieldName, name)
	for n in not3:
		print "#XXX", not3

