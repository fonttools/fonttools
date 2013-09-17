"""sstruct.py -- SuperStruct

Higher level layer on top of the struct module, enabling to 
bind names to struct elements. The interface is similar to 
struct, except the objects passed and returned are not tuples 
(or argument lists), but dictionaries or instances. 

Just like struct, we use format strings to describe a data 
structure, except we use one line per element. Lines are 
separated by newlines or semi-colons. Each line contains 
either one of the special struct characters ('@', '=', '<', 
'>' or '!') or a 'name:formatchar' combo (eg. 'myFloat:f'). 
Repetitions, like the struct module offers them are not useful 
in this context, except for fixed length strings  (eg. 'myInt:5h' 
is not allowed but 'myString:5s' is). The 'x' format character 
(pad byte) is treated as 'special', since it is by definition 
anonymous. Extra whitespace is allowed everywhere.

The sstruct module offers one feature that the "normal" struct
module doesn't: support for fixed point numbers. These are spelled
as "n.mF", where n is the number of bits before the point, and m
the number of bits after the point. Fixed point numbers get 
converted to floats.

pack(format, object):
	'object' is either a dictionary or an instance (or actually
	anything that has a __dict__ attribute). If it is a dictionary, 
	its keys are used for names. If it is an instance, it's 
	attributes are used to grab struct elements from. Returns
	a string containing the data.

unpack(format, data, object=None)
	If 'object' is omitted (or None), a new dictionary will be 
	returned. If 'object' is a dictionary, it will be used to add 
	struct elements to. If it is an instance (or in fact anything
	that has a __dict__ attribute), an attribute will be added for 
	each struct element. In the latter two cases, 'object' itself 
	is returned.

unpack2(format, data, object=None)
	Convenience function. Same as unpack, except data may be longer 
	than needed. The returned value is a tuple: (object, leftoverdata).

calcsize(format)
	like struct.calcsize(), but uses our own format strings:
	it returns the size of the data in bytes.
"""

# XXX I would like to support pascal strings, too, but I'm not
# sure if that's wise. Would be nice if struct supported them
# "properly", but that would certainly break calcsize()...

__version__ = "1.2"
__copyright__ = "Copyright 1998, Just van Rossum <just@letterror.com>"

import struct
import re
import types


error = "sstruct.error"

def pack(format, object):
	formatstring, names, fixes = getformat(format)
	elements = []
	if type(object) is not types.DictType:
		object = object.__dict__
	for name in names:
		value = object[name]
		if fixes.has_key(name):
			# fixed point conversion
			value = int(round(value*fixes[name]))
		elements.append(value)
	data = apply(struct.pack, (formatstring,) + tuple(elements))
	return data

def unpack(format, data, object=None):
	if object is None:
		object = {}
	formatstring, names, fixes = getformat(format)
	if type(object) is types.DictType:
		dict = object
	else:
		dict = object.__dict__
	elements = struct.unpack(formatstring, data)
	for i in range(len(names)):
		name = names[i]
		value = elements[i]
		if fixes.has_key(name):
			# fixed point conversion
			value = value / fixes[name]
		dict[name] = value
	return object

def unpack2(format, data, object=None):
	length = calcsize(format)
	return unpack(format, data[:length], object), data[length:]

def calcsize(format):
	formatstring, names, fixes = getformat(format)
	return struct.calcsize(formatstring)


# matches "name:formatchar" (whitespace is allowed)
_elementRE = re.compile(
		"\s*"							# whitespace
		"([A-Za-z_][A-Za-z_0-9]*)"		# name (python identifier)
		"\s*:\s*"						# whitespace : whitespace
		"([cbBhHiIlLfd]|[0-9]+[ps]|"	# formatchar...
			"([0-9]+)\.([0-9]+)(F))"	# ...formatchar
		"\s*"							# whitespace
		"(#.*)?$"						# [comment] + end of string
	)

# matches the special struct format chars and 'x' (pad byte)
_extraRE = re.compile("\s*([x@=<>!])\s*(#.*)?$")

# matches an "empty" string, possibly containing whitespace and/or a comment
_emptyRE = re.compile("\s*(#.*)?$")

_fixedpointmappings = {
		8: "b",
		16: "h",
		32: "l"}

_formatcache = {}

def getformat(format):
	try:
		formatstring, names, fixes = _formatcache[format]
	except KeyError:
		lines = re.split("[\n;]", format)
		formatstring = ""
		names = []
		fixes = {}
		for line in lines:
			if _emptyRE.match(line):
				continue
			m = _extraRE.match(line)
			if m:
				formatchar = m.group(1)
				if formatchar <> 'x' and formatstring:
					raise error, "a special format char must be first"
			else:
				m = _elementRE.match(line)
				if not m:
					raise error, "syntax error in format: '%s'" % line
				name = m.group(1)
				names.append(name)
				formatchar = m.group(2)
				if m.group(3):
					# fixed point
					before = int(m.group(3))
					after = int(m.group(4))
					bits = before + after
					if bits not in [8, 16, 32]:
						raise error, "fixed point must be 8, 16 or 32 bits long"
					formatchar = _fixedpointmappings[bits]
					assert m.group(5) == "F"
					fixes[name] = float(1 << after)
			formatstring = formatstring + formatchar
		_formatcache[format] = formatstring, names, fixes
	return formatstring, names, fixes

def _test():
	format = """
		# comments are allowed
		>  # big endian (see documentation for struct)
		# empty lines are allowed:
		
		ashort: h
		along: l
		abyte: b	# a byte
		achar: c
		astr: 5s
		afloat: f; adouble: d	# multiple "statements" are allowed
		afixed: 16.16F
	"""
	
	print 'size:', calcsize(format)
	
	class foo:
		pass
	
	i = foo()
	
	i.ashort = 0x7fff
	i.along = 0x7fffffff
	i.abyte = 0x7f
	i.achar = "a"
	i.astr = "12345"
	i.afloat = 0.5
	i.adouble = 0.5
	i.afixed = 1.5
	
	data = pack(format, i)
	print 'data:', `data`
	print unpack(format, data)
	i2 = foo()
	unpack(format, data, i2)
	print vars(i2)

if __name__ == "__main__":
	_test()
