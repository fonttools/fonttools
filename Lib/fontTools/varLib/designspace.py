"""Rudimentary support for loading MutatorMath .designspace files."""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

__all__ = ['load', 'loads']

def _xmlParseLocation(et):
	loc = {}
	for dim in et.find('location'):
		assert dim.tag == 'dimension'
		name = dim.attrib['name']
		value = float(dim.attrib['xvalue'])
		assert name not in loc
		loc[name] = value
	return loc

def _loadItem(et):
	item = dict(et.attrib)
	for elt in et:
		if elt.tag == 'location':
			value = _xmlParseLocation(et)
		else:
			value = {}
			if 'copy' in elt.attrib:
				value['copy'] = bool(int(elt.attrib['copy']))
			# TODO load more?!
		item[elt.tag] = value
	return item

def _load(et):
	masters = []
	ds = et.getroot()
	for et in ds.find('sources'):
		masters.append(_loadItem(et))

	instances = []
	for et in ds.find('instances'):
		instances.append(_loadItem(et))

	return masters, instances

def load(filename):
	"""Load designspace from a file name or object.  Returns two items:
	list of masters (aka sources) and list of instances."""
	return _load(ET.parse(filename))

def loads(string):
	"""Load designspace from a string."""
	return _load(ET.fromstring(string))
