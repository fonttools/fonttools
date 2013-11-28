"""fontTools.misc.textTools.py -- miscelaneous routines."""


from __future__ import print_function, division
from fontTools.misc.py23 import *
import string


def safeEval(data, eval=eval):
	"""A (kindof) safe replacement for eval."""
	return eval(data, {"__builtins__":{}})


def readHex(content):
	"""Convert a list of hex strings to binary data."""
	return deHexStr(strjoin(chunk for chunk in content if isinstance(chunk, basestring)))

def deHexStr(hexdata):
	"""Convert a hex string to binary data."""
	hexdata = strjoin(hexdata.split())
	if len(hexdata) % 2:
		hexdata = hexdata + "0"
	data = []
	for i in range(0, len(hexdata), 2):
		data.append(bytechr(int(hexdata[i:i+2], 16)))
	return bytesjoin(data)


def hexStr(data):
	"""Convert binary data to a hex string."""
	h = string.hexdigits
	r = ''
	for c in data:
		i = byteord(c)
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
	return ' '.join(all)


def binary2num(bin):
	bin = strjoin(bin.split())
	l = 0
	for digit in bin:
		l = l << 1
		if digit != "0":
			l = l | 0x1
	return l


def caselessSort(alist):
	"""Return a sorted copy of a list. If there are only strings 
	in the list, it will not consider case.
	"""
	
	try:
		return sorted(alist, key=lambda a: (a.lower(), a))
	except TypeError:
		return sorted(alist)

