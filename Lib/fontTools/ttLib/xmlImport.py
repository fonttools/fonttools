from fontTools import ttLib
from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables.DefaultTable import DefaultTable
import types
import string
import Numeric, array
from xml.parsers.xmlproc import xmlproc


xmlerror = "xmlerror"
xml_parse_error = "XML parse error"


class UnicodeString:
	
	def __init__(self, value):
		if isinstance(value, UnicodeString):
			self.value = value.value
		else:
			if type(value) == types.StringType:
				# Since Numeric interprets char codes as *signed*,
				# we feed it through the array module.
				value = array.array("B", value)
			self.value = Numeric.array(value, Numeric.Int16)
	
	def __len__(self):
		return len(self.value)
	
	#def __hash__(self):
	#	return hash(self.value.tostring())
	#
	#def __cmp__(self, other):
	#	if not isinstance(other, UnicodeString):
	#		return 1
	#	else:
	#		return not Numeric.alltrue(
	#				Numeric.equal(self.value, other.value))
	
	def __add__(self, other):
		if not isinstance(other, UnicodeString):
			other = self.__class__(other)
		return self.__class__(Numeric.concatenate((self.value, other.value)))
	
	def __radd__(self, other):
		if not isinstance(other, UnicodeString):
			other = self.__class__(other)
		return self.__class__(Numeric.concatenate((other.value, self.value)))
	
	def __getslice__(self, i, j):
		return self.__class__(self.value[i:j])
	
	def __getitem__(self, i):
		return self.__class__(self.value[i:i+1])
	
	def tostring(self):
		value = self.value
		if ttLib.endian <> "big":
			value = value.byteswapped()
		return value.tostring()
	
	def stripped(self):
		value = self.value
		i = 0
		for i in range(len(value)):
			if value[i] not in (0xa, 0xd, 0x9, 0x20):
				break
		value = value[i:]
		i = 0
		for i in range(len(value)-1, -1, -1):
			if value[i] not in (0xa, 0xd, 0x9, 0x20):
				break
		value = value[:i+1]
		return self.__class__(value)
	
	def __repr__(self):
		return "<%s %s at %x>" % (self.__class__.__name__, `self.value.tostring()`, id(self))


class UnicodeProcessor(xmlproc.XMLProcessor):
	
	def parse_charref(self):
		"Parses a character reference."
		
		if self.now_at("x"):
			digs=unhex(self.get_match(xmlproc.reg_hex_digits))
		else:
			try:
				digs=string.atoi(self.get_match(xmlproc.reg_digits))
			except ValueError,e:
				self.report_error(3027)
				digs=None
		if digs == 169:
			pass
		if not self.now_at(";"): self.report_error(3005,";")
		if digs==None: return
		
		if not (digs==9 or digs==10 or digs==13 or \
				(digs>=32 and digs<=255)):
			if digs>255:
				self.app.handle_data(UnicodeString([digs]),0,1)
			else:
				# hrm, I need to let some null bytes go through...
				self.app.handle_data(chr(digs),0,1)
				#self.report_error(3018,digs)
		else:
			if self.stack==[]:
				self.report_error(3028)
			self.app.handle_data(chr(digs),0,1)


class XMLErrorHandler(xmlproc.ErrorHandler):
	
	def fatal(self, msg):
		"Handles a fatal error message."
		# we don't want no stinkin' sys.exit(1)
		raise xml_parse_error, msg


class XMLApplication(xmlproc.Application):
	
	def __init__(self, ttFont, progress=None):
		self.ttFont = ttFont
		self.progress = progress
		self.root = None
		self.content_stack = []
		self.lastpos = 0
	
	def handle_start_tag(self, name, attrs):
		if self.progress:
			pos = self.locator.pos + self.locator.block_offset
			if (pos - self.lastpos) > 4000:
				self.progress.set(pos / 100)
				self.lastpos = pos
		stack = self.locator.stack
		stackSize = len(stack)
		if not stackSize:
			if name <> "ttFont":
				raise xml_parse_error, "illegal root tag: %s" % name
			sfntVersion = attrs.get("sfntVersion", "\000\001\000\000")
			if len(sfntVersion) <> 4:
				sfntVersion = safeEval('"' + sfntVersion + '"')
			self.ttFont.sfntVersion = sfntVersion
			self.content_stack.append([])
		elif stackSize == 1:
			msg = "Parsing '%s' table..." % ttLib.xmltag2tag(name)
			if self.progress:
				self.progress.setlabel(msg)
			elif self.ttFont.verbose:
				ttLib.debugmsg(msg)
			else:
				print msg
			tag = ttLib.xmltag2tag(name)
			if attrs.has_key("ERROR"):
				tableClass = DefaultTable
			else:
				tableClass = ttLib.getTableClass(tag)
				if tableClass is None:
					tableClass = DefaultTable
			if self.ttFont.has_key(tag):
				self.current_table = self.ttFont[tag]
			else:
				self.current_table = tableClass(tag)
				self.ttFont[tag] = self.current_table
			self.content_stack.append([])
		elif stackSize == 2:
			self.content_stack.append([])
			self.root = (name, attrs, self.content_stack[-1])
		else:
			list = []
			self.content_stack[-1].append(name, attrs, list)
			self.content_stack.append(list)
	
	def handle_data(self, data, start, end):
		if len(self.locator.stack) > 1:
			self.content_stack[-1].append(data[start:end])
	
	def handle_end_tag(self, name):
		del self.content_stack[-1]
		stack = self.locator.stack
		stackSize = len(stack)
		if stackSize == 1:
			self.root = None
		elif stackSize == 2:
			self.current_table.fromXML(self.root, self.ttFont)
			self.root = None


class ProgressPrinter:
	
	def __init__(self, title, maxval=100):
		print title
	
	def set(self, val, maxval=None):
		pass
	
	def increment(self, val=1):
		pass
	
	def setlabel(self, text):
		print text


