"""Rudimentary support for loading MutatorMath .designspace files."""
from __future__ import print_function, division, absolute_import
import collections
from fontTools.misc.py23 import *
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

__all__ = ['load', 'loads']

standard_axis_map = collections.OrderedDict(
	[['weight', ('wght', 'Weight')],
	['width', ('wdth', 'Width')],
	['slant', ('slnt', 'Slant')],
	['optical', ('opsz', 'Optical Size')],
	['custom',('xxxx', 'Custom')]]
	)

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
	ds = et.getroot()
	
	axisMap = collections.OrderedDict()
	axesET = ds.find('axes')
	if axesET:
		axisList = axesET.findall('axis')
		for axisET in axisList:
			axisName = axisET.attrib["name"]
			labelET = axisET.find('labelname')
			if (None == labelET):
				# If the designpsace file axes is a std axes, the label name may be omitted.
				tag, label = standard_axis_map[axisName]
			else:
				label = labelET.text
				tag = axisET.attrib["tag"]
			axisMap[axisName] = (tag,  label)

	masters = []
	for et in ds.find('sources'):
		masters.append(_loadItem(et))

	instances = []
	for et in ds.find('instances'):
		instances.append(_loadItem(et))

	return masters, instances, axisMap

def load(filename):
	"""Load designspace from a file name or object.  Returns two items:
	list of masters (aka sources) and list of instances."""
	return _load(ET.parse(filename))

def loads(string):
	"""Load designspace from a string."""
	return _load(ET.fromstring(string))
