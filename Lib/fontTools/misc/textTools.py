"""fontTools.misc.textTools.py -- miscelaneous routines."""


import string


def safeEval(data, eval=eval):
	"""A safe replacement for eval."""
	return eval(data, {"__builtins__":{}}, {})


def readHex(content):
	"""Convert a list of hex strings to binary data."""
	return deHexStr(''.join([ chunk for chunk in content if isinstance(chunk,str) ]))

def deHexStr(hexdata):
	"""Convert a hex string to binary data."""
	parts = string.split(hexdata)
	hexdata = string.join(parts, "")
	if len(hexdata) % 2:
		hexdata = hexdata + "0"
	data = []
	for i in range(0, len(hexdata), 2):
		data.append(chr(string.atoi(hexdata[i:i+2], 16)))
	return "".join(data)


def hexStr(data):
	"""Convert binary data to a hex string."""
	h = string.hexdigits
	r = ''
	for c in data:
		i = ord(c)
		r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
	return r


def num2binary(l, bits=32):
	all = []
	bin = ""
	for i in range(bits):
		if l & 0x1:
			bin = "1" + bin
		else:
			bin = "0" + bin
		l = l >> 1
		if not ((i+1) % 8):
			all.append(bin)
			bin = ""
	if bin:
		all.append(bin)
	all.reverse()
	assert l in (0, -1), "number doesn't fit in number of bits"
	return string.join(all, " ")


def binary2num(bin):
	bin = string.join(string.split(bin), "")
	l = 0
	for digit in bin:
		l = l << 1
		if digit <> "0":
			l = l | 0x1
	return l


def caselessSort(alist):
	"""Return a sorted copy of a list. If there are only strings 
	in the list, it will not consider case.
	"""
	
	try:
		# turn ['FOO',  'aaBc', 'ABcD'] into 
		# [('foo', 'FOO'), ('aabc', 'aaBc'), ('abcd', 'ABcD')], 
		# but only if all elements are strings
		tupledlist = map(lambda item, lower = string.lower: 
			(lower(item), item), alist)
	except TypeError:
		# at least one element in alist is not a string, proceed the normal way...
		alist = alist[:]
		alist.sort()
		return alist
	else:
		tupledlist.sort()
		# turn [('aabc', 'aaBc'), ('abcd', 'ABcD'), ('foo', 'FOO')] into 
		# ['aaBc', 'ABcD', 'FOO']
		return map(lambda x: x[1], tupledlist)

