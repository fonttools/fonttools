"""Rudimentary support for loading MutatorMath .designspace files."""
from __future__ import print_function, division, absolute_import
import collections
from fontTools.misc.py23 import *
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

__all__ = ['load', 'loads']

namespaces = {'xml': '{http://www.w3.org/XML/1998/namespace}'}

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

def _xmlParseAxisOrMap(elt):
	dic = {}
	for name in elt.attrib:
		if name in ['name', 'tag']:
			dic[name] = elt.attrib[name]
		else:
			dic[name] = float(elt.attrib[name])
	return dic

def _loadAxis(et):
	item = dict(_xmlParseAxisOrMap(et))
	maps = []
	labelnames = {}
	for elt in et:
		assert elt.tag in ['labelname', 'map']
		if elt.tag == 'labelname':
			lang = elt.attrib["{0}lang".format(namespaces['xml'])]
			labelnames[lang] = elt.text
		elif elt.tag == 'map':
			maps.append(_xmlParseAxisOrMap(elt))
	if labelnames:
		item['labelname'] = labelnames
	if maps:
		item['map'] = maps
	return item

def _load(et):
	ds = et.getroot()

	axes = []
	ds_axes = ds.find('axes')
	if ds_axes:
		for et in ds_axes:
			axes.append(_loadAxis(et))

	masters = []
	for et in ds.find('sources'):
		masters.append(_loadItem(et))

	instances = []
	for et in ds.find('instances'):
		instances.append(_loadItem(et))

	return axes, masters, instances

def load(filename):
	"""Load designspace from a file name or object.
	   Returns three items:
	   - list of axes
	   - list of masters (aka sources)
	   - list of instances"""
	return _load(ET.parse(filename))

def loads(string):
	"""Load designspace from a string."""
	return _load(ET.fromstring(string))
