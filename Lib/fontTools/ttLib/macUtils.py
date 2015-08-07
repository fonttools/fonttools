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
		self.file = BytesIO(res.data)
		Res.CloseResFile(resref)
		self.name = path

	def __getattr__(self, attr):
		# cheap inheritance
		return getattr(self.file, attr)
