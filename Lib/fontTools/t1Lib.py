"""fontTools.t1Lib.py -- Tools for PostScript Type 1 fonts

Functions for reading and writing raw Type 1 data:

read(path)
	reads any Type 1 font file, returns the raw data and a type indicator: 
	'LWFN', 'PFB' or 'OTHER', depending on the format of the file pointed 
	to by 'path'. 
	Raises an error when the file does not contain valid Type 1 data.

write(path, data, kind = 'OTHER', dohex = 0)
	writes raw Type 1 data to the file pointed to by 'path'. 
	'kind' can be one of 'LWFN', 'PFB' or 'OTHER'; it defaults to 'OTHER'.
	'dohex' is a flag which determines whether the eexec encrypted
	part should be written as hexadecimal or binary, but only if kind
	is 'LWFN' or 'PFB'.
"""

__author__ = "jvr"
__version__ = "1.0b2"
DEBUG = 0

from fontTools.misc import eexec
import string
import re
import os

if os.name == 'mac':
	import Res
	import macfs

error = 't1Lib.error'

# work in progress


class T1Font:
	
	"""Type 1 font class. 
	XXX This is work in progress! For now just use the read()
	and write() functions as described above, they are stable.
	"""
	
	def __init__(self, path=None):
		if path is not None:
			self.data, type = read(path)
		else:
			pass # XXX
	
	def saveAs(self, path, type):
		self.write(path, self.getData(), type)
	
	def getData(self):
		return self.data
	
	def __getitem__(self, key):
		if not hasattr(self, "font"):
			self.parse()
			return self.font[key]
		else:
			return self.font[key]
	
	def parse(self):
		import psLib
		import psCharStrings
		self.font = psLib.suckfont(self.data)
		charStrings = self.font["CharStrings"]
		lenIV = self.font["Private"].get("lenIV", 4)
		assert lenIV >= 0
		for glyphName, charString in charStrings.items():
			charString, R = eexec.decrypt(charString, 4330)
			charStrings[glyphName] = psCharStrings.T1CharString(charString[lenIV:])
		subrs = self.font["Private"]["Subrs"]
		for i in range(len(subrs)):
			charString, R = eexec.decrypt(subrs[i], 4330)
			subrs[i] = psCharStrings.T1CharString(charString[lenIV:])
		del self.data
	


# public functions

def read(path):
	"""reads any Type 1 font file, returns raw data"""
	normpath = string.lower(path)
	if os.name == 'mac':
		fss = macfs.FSSpec(path)
		creator, type = fss.GetCreatorType()
		if type == 'LWFN':
			return readlwfn(path), 'LWFN'
	if normpath[-4:] == '.pfb':
		return readpfb(path), 'PFB'
	else:
		return readother(path), 'OTHER'

def write(path, data, kind='OTHER', dohex=0):
	asserttype1(data)
	kind = string.upper(kind)
	try:
		os.remove(path)
	except os.error:
		pass
	err = 1
	try:
		if kind == 'LWFN':
			writelwfn(path, data)
		elif kind == 'PFB':
			writepfb(path, data)
		else:
			writeother(path, data, dohex)
		err = 0
	finally:
		if err and not DEBUG:
			try:
				os.remove(path)
			except os.error:
				pass


# -- internal -- 

LWFNCHUNKSIZE = 2000
HEXLINELENGTH = 80


def readlwfn(path):
	"""reads an LWFN font file, returns raw data"""
	resref = Res.OpenResFile(path)
	try:
		Res.UseResFile(resref)
		n = Res.Count1Resources('POST')
		data = []
		for i in range(501, 501 + n):
			res = Res.Get1Resource('POST', i)
			code = ord(res.data[0])
			if ord(res.data[1]) <> 0:
				raise error, 'corrupt LWFN file'
			if code in [1, 2]:
				data.append(res.data[2:])
			elif code in [3, 5]:
				break
			elif code == 4:
				f = open(path, "rb")
				data.append(f.read())
				f.close()
			elif code == 0:
				pass # comment, ignore
			else:
				raise error, 'bad chunk code: ' + `code`
	finally:
		Res.CloseResFile(resref)
	data = string.join(data, '')
	asserttype1(data)
	return data

def readpfb(path):
	"""reads a PFB font file, returns raw data"""
	f = open(path, "rb")
	data = []
	while 1:
		if f.read(1) <> chr(128):
			raise error, 'corrupt PFB file'
		code = ord(f.read(1))
		if code in [1, 2]:
			chunklen = string2long(f.read(4))
			data.append(f.read(chunklen))
		elif code == 3:
			break
		else:
			raise error, 'bad chunk code: ' + `code`
	f.close()
	data = string.join(data, '')
	asserttype1(data)
	return data

def readother(path):
	"""reads any (font) file, returns raw data"""
	f = open(path, "rb")
	data = f.read()
	f.close()
	asserttype1(data)
	
	chunks = findencryptedchunks(data)
	data = []
	for isencrypted, chunk in chunks:
		if isencrypted and ishex(chunk[:4]):
			data.append(dehexstring(chunk))
		else:
			data.append(chunk)
	return string.join(data, '')

# file writing tools

def writelwfn(path, data):
	Res.CreateResFile(path)
	fss = macfs.FSSpec(path)
	fss.SetCreatorType('just', 'LWFN')
	resref = Res.OpenResFile(path)
	try:
		Res.UseResFile(resref)
		resID = 501
		chunks = findencryptedchunks(data)
		for isencrypted, chunk in chunks:
			if isencrypted:
				code = 2
			else:
				code = 1
			while chunk:
				res = Res.Resource(chr(code) + '\0' + chunk[:LWFNCHUNKSIZE - 2])
				res.AddResource('POST', resID, '')
				chunk = chunk[LWFNCHUNKSIZE - 2:]
				resID = resID + 1
		res = Res.Resource(chr(5) + '\0')
		res.AddResource('POST', resID, '')
	finally:
		Res.CloseResFile(resref)

def writepfb(path, data):
	chunks = findencryptedchunks(data)
	f = open(dstpath, "wb")
	try:
		for isencrypted, chunk in chunks:
			if isencrypted:
				code = 2
			else:
				code = 1
			f.write(chr(128) + chr(code))
			f.write(long2string(len(chunk)))
			f.write(chunk)
		f.write(chr(128) + chr(3))
	finally:
		f.close()
	if os.name == 'mac':
		fss = macfs.FSSpec(dstpath)
		fss.SetCreatorType('mdos', 'BINA')

def writeother(path, data, dohex = 0):
	chunks = findencryptedchunks(data)
	f = open(path, "wb")
	try:
		hexlinelen = HEXLINELENGTH / 2
		for isencrypted, chunk in chunks:
			if isencrypted:
				code = 2
			else:
				code = 1
			if code == 2 and dohex:
				while chunk:
					f.write(eexec.hexString(chunk[:hexlinelen]))
					f.write('\r')
					chunk = chunk[hexlinelen:]
			else:
				f.write(chunk)
	finally:
		f.close()
	if os.name == 'mac':
		fss = macfs.FSSpec(path)
		fss.SetCreatorType('R*ch', 'TEXT') # BBEdit text file


# decryption tools

EEXECBEGIN = "currentfile eexec"
EEXECEND = '0' * 64
EEXECINTERNALEND = "currentfile closefile"
EEXECBEGINMARKER = "%-- eexec start\r"
EEXECENDMARKER = "%-- eexec end\r"

_ishexRE = re.compile('[0-9A-Fa-f]*$')

def ishex(text):
	return _ishexRE.match(text) is not None


def decrypttype1(data):
	chunks = findencryptedchunks(data)
	data = []
	for isencrypted, chunk in chunks:
		if isencrypted:
			if ishex(chunk[:4]):
				chunk = dehexstring(chunk)
			decrypted, R = eexec.decrypt(chunk, 55665)
			decrypted = decrypted[4:]
			if decrypted[-len(EEXECINTERNALEND)-1:-1] <> EEXECINTERNALEND \
					and decrypted[-len(EEXECINTERNALEND)-2:-2] <> EEXECINTERNALEND:
				raise error, "invalid end of eexec part"
			decrypted = decrypted[:-len(EEXECINTERNALEND)-2] + '\r'
			data.append(EEXECBEGINMARKER + decrypted + EEXECENDMARKER)
		else:
			if chunk[-len(EEXECBEGIN)-1:-1] == EEXECBEGIN:
				data.append(chunk[:-len(EEXECBEGIN)-1])
			else:
				data.append(chunk)
	return string.join(data, '')

def findencryptedchunks(data):
	chunks = []
	while 1:
		ebegin = string.find(data, EEXECBEGIN)
		if ebegin < 0:
			break
		eend = string.find(data, EEXECEND, ebegin)
		if eend < 0:
			raise error, "can't find end of eexec part"
		chunks.append((0, data[:ebegin + len(EEXECBEGIN) + 1]))
		chunks.append((1, data[ebegin + len(EEXECBEGIN) + 1:eend]))
		data = data[eend:]
	chunks.append((0, data))
	return chunks

def dehexstring(hexstring):
	return eexec.deHexString(string.join(string.split(hexstring), ""))


# Type 1 assertion

_fontType1RE = re.compile(r"/FontType\s+1\s+def")

def asserttype1(data):
	for head in ['%!PS-AdobeFont', '%!FontType1-1.0']:
		if data[:len(head)] == head:
			break
	else:
		raise error, "not a PostScript font"
	if not _fontType1RE.search(data):
		raise error, "not a Type 1 font"
	if string.find(data, "currentfile eexec") < 0:
		raise error, "not an encrypted Type 1 font"
	# XXX what else?
	return data


# pfb helpers

def long2string(long):
	str = ""
	for i in range(4):
		str = str + chr((long & (0xff << (i * 8))) >> i * 8)
	return str

def string2long(str):
	if len(str) <> 4:
		raise ValueError, 'string must be 4 bytes long'
	long = 0
	for i in range(4):
		long = long + (ord(str[i]) << (i * 8))
	return long
