import StringIO
import regex
import string
from fontTools.misc import eexec
import types
from psOperators import *


ps_special = '()<>[]{}%'	# / is one too, but we take care of that one differently

whitespace = string.whitespace
skipwhiteRE = regex.compile("[%s]*" % whitespace)

endofthingPat = "[^][(){}<>/%s%s]*" % ('%', whitespace)
endofthingRE = regex.compile(endofthingPat)

commentRE = regex.compile("%[^\n\r]*")

# XXX This not entirely correct:
stringPat = """
	(
		\(
			\(
				[^()]*   \\\\   [()]
			\)
			\|
			\(
				[^()]*  (   [^()]*  )
			\)
		\)*
		[^()]*
	)
"""
stringPat = string.join(string.split(stringPat), '')
stringRE = regex.compile(stringPat)

hexstringRE = regex.compile("<[%s0-9A-Fa-f]*>" % whitespace)

ps_tokenerror = 'ps_tokenerror'
ps_error = 'ps_error'

class PSTokenizer(StringIO.StringIO):
	
	def getnexttoken(self, 
			# localize some stuff, for performance
			len = len,
			ps_special = ps_special,
			stringmatch = stringRE.match,
			hexstringmatch = hexstringRE.match,
			commentmatch = commentRE.match,
			endmatch = endofthingRE.match, 
			whitematch = skipwhiteRE.match):
		
		self.pos = self.pos + whitematch(self.buf, self.pos)
		if self.pos >= self.len:
			return None, None
		pos = self.pos
		buf = self.buf
		char = buf[pos]
		if char in ps_special:
			if char in '{}[]':
				tokentype = 'do_special'
				token = char
			elif char == '%':
				tokentype = 'do_comment'
				commentlen = commentmatch(buf, pos)
				token = buf[pos:pos+commentlen]
			elif char == '(':
				tokentype = 'do_string'
				strlen = stringmatch(buf, pos)
				if strlen < 0:
					raise ps_tokenerror, 'bad string at character %d' % pos
				token = buf[pos:pos+strlen]
			elif char == '<':
				tokentype = 'do_hexstring'
				strlen = hexstringmatch(buf, pos)
				if strlen < 0:
					raise ps_tokenerror, 'bad hexstring at character %d' % pos
				token = buf[pos:pos+strlen]
			else:
				raise ps_tokenerror, 'bad token at character %d' % pos
		else:
			if char == '/':
				tokentype = 'do_literal'
				endofthing = endmatch(buf, pos + 1) + 1
			else:
				tokentype = ''
				endofthing = endmatch(buf, pos)
			if endofthing <= 0:
				raise ps_tokenerror, 'bad token at character %d' % pos
			token = buf[pos:pos + endofthing]
		self.pos = pos + len(token)
		return tokentype, token
	
	def skipwhite(self, whitematch = skipwhiteRE.match):
		self.pos = self.pos + whitematch(self.buf, self.pos)
	
	def starteexec(self):
		self.pos = self.pos + 1
		#self.skipwhite()
		self.dirtybuf = self.buf[self.pos:]
		self.buf, R = eexec.decrypt(self.dirtybuf, 55665)
		self.len = len(self.buf)
		self.pos = 4
	
	def stopeexec(self):
		if not hasattr(self, 'dirtybuf'):
			return
		self.buf = self.dirtybuf
		del self.dirtybuf
	
	def flush(self):
		if self.buflist:
			self.buf = self.buf + string.join(self.buflist, '')
			self.buflist = []


class PSInterpreter(PSOperators):
	
	def __init__(self):
		systemdict = {}
		userdict = {}
		self.dictstack = [systemdict, userdict]
		self.stack = []
		self.proclevel = 0
		self.procmark = ps_procmark()
		self.fillsystemdict()
	
	def fillsystemdict(self):
		systemdict = self.dictstack[0]
		systemdict['['] = systemdict['mark'] = self.mark = ps_mark()
		systemdict[']'] = ps_operator(']', self.do_makearray)
		systemdict['true'] = ps_boolean(1)
		systemdict['false'] = ps_boolean(0)
		systemdict['StandardEncoding'] = ps_array(ps_StandardEncoding)
		systemdict['FontDirectory'] = ps_dict({})
		self.suckoperators(systemdict, self.__class__)
	
	def suckoperators(self, systemdict, klass):
		for name in dir(klass):
			attr = getattr(self, name)
			if callable(attr) and name[:3] == 'ps_':
				name = name[3:]
				systemdict[name] = ps_operator(name, attr)
		for baseclass in klass.__bases__:
			self.suckoperators(systemdict, baseclass)
	
	def interpret(self, data, getattr = getattr):
		tokenizer = self.tokenizer = PSTokenizer(data)
		getnexttoken = tokenizer.getnexttoken
		do_token = self.do_token
		handle_object = self.handle_object
		try:
			while 1:
				tokentype, token = getnexttoken()
				#print token
				if not token:
					break
				if tokentype:
					handler = getattr(self, tokentype)
					object = handler(token)
				else:
					object = do_token(token)
				if object is not None:
					handle_object(object)
			tokenizer.close()
			self.tokenizer = None
		finally:
			if self.tokenizer is not None:
				print 'ps error:\n- - - - - - -'
				print self.tokenizer.buf[self.tokenizer.pos-50:self.tokenizer.pos]
				print '>>>'
				print self.tokenizer.buf[self.tokenizer.pos:self.tokenizer.pos+50]
				print '- - - - - - -'
	
	def handle_object(self, object):
		if not (self.proclevel or object.literal or object.type == 'proceduretype'):
			if object.type <> 'operatortype':
				object = self.resolve_name(object.value)
			if object.literal:
				self.push(object)
			else:
				if object.type == 'proceduretype':
					self.call_procedure(object)
				else:
					object.function()
		else:
			self.push(object)
	
	def call_procedure(self, proc):
		handle_object = self.handle_object
		for item in proc.value:
			handle_object(item)
	
	def resolve_name(self, name):
		dictstack = self.dictstack
		for i in range(len(dictstack)-1, -1, -1):
			if dictstack[i].has_key(name):
				return dictstack[i][name]
		raise ps_error, 'name error: ' + str(name)
	
	def do_token(self, token,
				atoi = string.atoi, 
				atof = string.atof,
				ps_name = ps_name,
				ps_integer = ps_integer,
				ps_real = ps_real):
		try:
			num = atoi(token)
		except (ValueError, OverflowError):
			try:
				num = atof(token)
			except (ValueError, OverflowError):
				if '#' in token:
					hashpos = string.find(token, '#')
					try:
						base = string.atoi(token[:hashpos])
						num = string.atoi(token[hashpos+1:], base)
					except (ValueError, OverflowError):
						return ps_name(token)
					else:
						return ps_integer(num)
				else:
					return ps_name(token)
			else:
				return ps_real(num)
		else:
			return ps_integer(num)
	
	def do_comment(self, token):
		pass
	
	def do_literal(self, token):
		return ps_literal(token[1:])
	
	def do_string(self, token):
		return ps_string(token[1:-1])
	
	def do_hexstring(self, token):
		hexStr = string.join(string.split(token[1:-1]), '')
		if len(hexStr) % 2:
			hexStr = hexStr + '0'
		cleanstr = []
		for i in range(0, len(hexStr), 2):
			cleanstr.append(chr(string.atoi(hexStr[i:i+2], 16)))
		cleanstr = string.join(cleanstr, '')
		return ps_string(cleanstr)
	
	def do_special(self, token):
		if token == '{':
			self.proclevel = self.proclevel + 1
			return self.procmark
		elif token == '}':
			proc = []
			while 1:
				topobject = self.pop()
				if topobject == self.procmark:
					break
				proc.append(topobject)
			self.proclevel = self.proclevel - 1
			proc.reverse()
			return ps_procedure(proc)
		elif token == '[':
			return self.mark
		elif token == ']':
			return ps_name(']')
		else:
			raise ps_tokenerror, 'huh?'
	
	def push(self, object):
		self.stack.append(object)
	
	def pop(self, *types):
		stack = self.stack
		if not stack:
			raise ps_error, 'stack underflow'
		object = stack[-1]
		if types:
			if object.type not in types:
				raise ps_error, 'typecheck, expected %s, found %s' % (`types`, object.type)
		del stack[-1]
		return object
	
	def do_makearray(self):
		array = []
		while 1:
			topobject = self.pop()
			if topobject == self.mark:
				break
			array.append(topobject)
		array.reverse()
		self.push(ps_array(array))
	
	def close(self):
		"""Remove circular references."""
		del self.stack
		del self.dictstack


def unpack_item(item):
	tp = type(item.value)
	if tp == types.DictionaryType:
		newitem = {}
		for key, value in item.value.items():
			newitem[key] = unpack_item(value)
	elif tp == types.ListType:
		newitem = [None] * len(item.value)
		for i in range(len(item.value)):
			newitem[i] = unpack_item(item.value[i])
		if item.type == 'proceduretype':
			newitem = tuple(newitem)
	else:
		newitem = item.value
	return newitem

def suckfont(data):
	import re
	m = re.search(r"/FontName\s+/([^ \t\n\r]+)\s+def", data)
	if m:
		fontName = m.group(1)
	else:
		fontName = None
	interpreter = PSInterpreter()
	interpreter.interpret("/Helvetica 4 dict dup /Encoding StandardEncoding put definefont pop")
	interpreter.interpret(data)
	fontdir = interpreter.dictstack[0]['FontDirectory'].value
	if fontdir.has_key(fontName):
		rawfont = fontdir[fontName]
	else:
		# fall back, in case fontName wasn't found
		fontNames = fontdir.keys()
		if len(fontNames) > 1:
			fontNames.remove("Helvetica")
		fontNames.sort()
		rawfont = fontdir[fontNames[0]]
	interpreter.close()
	return unpack_item(rawfont)


if __name__ == "__main__":
	import macfs
	fss, ok = macfs.StandardGetFile("LWFN")
	if ok:
		import t1Lib
		data, kind = t1Lib.read(fss.as_pathname())
		font = suckfont(data)
