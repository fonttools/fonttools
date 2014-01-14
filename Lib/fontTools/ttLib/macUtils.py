"""ttLib.macUtils.py -- Various Mac-specific stuff."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import sys
import os
if sys.platform not in ("mac", "darwin"):
	raise ImportError("This module is Mac-only!")
try:
	from Carbon import Res
except ImportError:
	import Res



def MyOpenResFile(path):
	mode = 1  # read only
	try:
		resref = Res.FSOpenResFile(path, mode)
	except Res.Error:
		# try data fork
		resref = Res.FSOpenResourceFile(path, unicode(), mode)
	return resref


def getSFNTResIndices(path):
	"""Determine whether a file has a resource fork or not."""
	try:
		resref = MyOpenResFile(path)
	except Res.Error:
		return []
	Res.UseResFile(resref)
	numSFNTs = Res.Count1Resources('sfnt')
	Res.CloseResFile(resref)
	return list(range(1, numSFNTs + 1))


def openTTFonts(path):
	"""Given a pathname, return a list of TTFont objects. In the case 
	of a flat TTF/OTF file, the list will contain just one font object;
	but in the case of a Mac font suitcase it will contain as many
	font objects as there are sfnt resources in the file.
	"""
	from fontTools import ttLib
	fonts = []
	sfnts = getSFNTResIndices(path)
	if not sfnts:
		fonts.append(ttLib.TTFont(path))
	else:
		for index in sfnts:
			fonts.append(ttLib.TTFont(path, index))
		if not fonts:
			raise ttLib.TTLibError("no fonts found in file '%s'" % path)
	return fonts


class SFNTResourceReader(object):
	
	"""Simple (Mac-only) read-only file wrapper for 'sfnt' resources."""
	
	def __init__(self, path, res_name_or_index):
		resref = MyOpenResFile(path)
		Res.UseResFile(resref)
		if isinstance(res_name_or_index, basestring):
			res = Res.Get1NamedResource('sfnt', res_name_or_index)
		else:
			res = Res.Get1IndResource('sfnt', res_name_or_index)
		self.file = StringIO(res.data)
		Res.CloseResFile(resref)
		self.name = path
	
	def __getattr__(self, attr):
		# cheap inheritance
		return getattr(self.file, attr)


class SFNTResourceWriter(object):
	
	"""Simple (Mac-only) file wrapper for 'sfnt' resources."""
	
	def __init__(self, path, ttFont, res_id=None):
		self.file = StringIO()
		self.name = path
		self.closed = 0
		fullname = ttFont['name'].getName(4, 1, 0) # Full name, mac, default encoding
		familyname = ttFont['name'].getName(1, 1, 0) # Fam. name, mac, default encoding
		psname = ttFont['name'].getName(6, 1, 0) # PostScript name, etc.
		if fullname is None or fullname is None or psname is None:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't make 'sfnt' resource, no Macintosh 'name' table found")
		self.fullname = fullname.string
		self.familyname = familyname.string
		self.psname = psname.string
		if self.familyname != self.psname[:len(self.familyname)]:
			# ugh. force fam name to be the same as first part of ps name,
			# fondLib otherwise barfs.
			for i in range(min(len(self.psname), len(self.familyname))):
				if self.familyname[i] != self.psname[i]:
					break
			self.familyname = self.psname[:i]
		
		self.ttFont = ttFont
		self.res_id = res_id
		if os.path.exists(self.name):
			os.remove(self.name)
		# XXX datafork support
		Res.FSpCreateResFile(self.name, 'DMOV', 'FFIL', 0)
		self.resref = Res.FSOpenResFile(self.name, 3)  # exclusive read/write permission
	
	def close(self):
		if self.closed:
			return
		Res.UseResFile(self.resref)
		try:
			res = Res.Get1NamedResource('sfnt', self.fullname)
		except Res.Error:
			pass
		else:
			res.RemoveResource()
		res = Res.Resource(self.file.getvalue())
		if self.res_id is None:
			self.res_id = Res.Unique1ID('sfnt')
		res.AddResource('sfnt', self.res_id, self.fullname)
		res.ChangedResource()
		
		self.createFond()
		del self.ttFont
		Res.CloseResFile(self.resref)
		self.file.close()
		self.closed = 1
	
	def createFond(self):
		fond_res = Res.Resource("")
		fond_res.AddResource('FOND', self.res_id, self.fullname)
		
		from fontTools import fondLib
		fond = fondLib.FontFamily(fond_res, "w")
		
		fond.ffFirstChar = 0
		fond.ffLastChar = 255
		fond.fondClass = 0
		fond.fontAssoc = [(0, 0, self.res_id)]
		fond.ffFlags = 20480	# XXX ???
		fond.ffIntl = (0, 0)
		fond.ffLeading = 0
		fond.ffProperty = (0, 0, 0, 0, 0, 0, 0, 0, 0)
		fond.ffVersion = 0
		fond.glyphEncoding = {}
		if self.familyname == self.psname:
			fond.styleIndices = (1,) * 48  # uh-oh, fondLib is too dumb.
		else:
			fond.styleIndices = (2,) * 48
		fond.styleStrings = []
		fond.boundingBoxes = None
		fond.ffFamID = self.res_id
		fond.changed = 1
		fond.glyphTableOffset = 0
		fond.styleMappingReserved = 0
		
		# calc:
		scale = 4096 / self.ttFont['head'].unitsPerEm
		fond.ffAscent = scale * self.ttFont['hhea'].ascent
		fond.ffDescent = scale * self.ttFont['hhea'].descent
		fond.ffWidMax = scale * self.ttFont['hhea'].advanceWidthMax
		
		fond.ffFamilyName = self.familyname
		fond.psNames = {0: self.psname}
		
		fond.widthTables = {}
		fond.kernTables = {}
		cmap = self.ttFont['cmap'].getcmap(1, 0)
		if cmap:
			names = {}
			for code, name in cmap.cmap.items():
				names[name] = code
			if 'kern' in self.ttFont:
				kern = self.ttFont['kern'].getkern(0)
				if kern:
					fondkerning = []
					for (left, right), value in kern.kernTable.items():
						if left in names and right in names:
							fondkerning.append((names[left], names[right], scale * value))
					fondkerning.sort()
					fond.kernTables = {0: fondkerning}
			if 'hmtx' in self.ttFont:
				hmtx = self.ttFont['hmtx']
				fondwidths = [2048] * 256 + [0, 0]  # default width, + plus two zeros.
				for name, (width, lsb) in hmtx.metrics.items():
					if name in names:
						fondwidths[names[name]] = scale * width
				fond.widthTables = {0: fondwidths}
		fond.save()
	
	def __del__(self):
		if not self.closed:
			self.close()
	
	def __getattr__(self, attr):
		# cheap inheritance
		return getattr(self.file, attr)
	

