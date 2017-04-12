"""Rudimentary support for loading MutatorMath .designspace files."""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

__all__ = ['load', 'loads']

namespaces = {'xml': '{http://www.w3.org/XML/1998/namespace}'}


def _xml_parse_location(et):
	loc = {}
	for dim in et.find('location'):
		assert dim.tag == 'dimension'
		name = dim.attrib['name']
		value = float(dim.attrib['xvalue'])
		assert name not in loc
		loc[name] = value
	return loc


def _load_item(et):
	item = dict(et.attrib)
	for element in et:
		if element.tag == 'location':
			value = _xml_parse_location(et)
		else:
			value = {}
			if 'copy' in element.attrib:
				value['copy'] = bool(int(element.attrib['copy']))
			# TODO load more?!
		item[element.tag] = value
	return item


def _xml_parse_axis_or_map(element):
	dic = {}
	for name in element.attrib:
		if name in ['name', 'tag']:
			dic[name] = element.attrib[name]
		else:
			dic[name] = float(element.attrib[name])
	return dic


def _load_axis(et):
	item = _xml_parse_axis_or_map(et)
	maps = []
	labelnames = {}
	for element in et:
		assert element.tag in ['labelname', 'map']
		if element.tag == 'labelname':
			lang = element.attrib["{0}lang".format(namespaces['xml'])]
			labelnames[lang] = element.text
		elif element.tag == 'map':
			maps.append(_xml_parse_axis_or_map(element))
	if labelnames:
		item['labelname'] = labelnames
	if maps:
		item['map'] = maps
	return item


def _load(et):
	designspace = {}
	ds = et.getroot()

	axes_element = ds.find('axes')
	if axes_element is not None:
		axes = []
		for et in axes_element:
			axes.append(_load_axis(et))
		designspace['axes'] = axes

	sources_element = ds.find('sources')
	if sources_element is not None:
		sources = []
		for et in sources_element:
			sources.append(_load_item(et))
		designspace['sources'] = sources

	instances_element = ds.find('instances')
	if instances_element is not None:
		instances = []
		for et in instances_element:
			instances.append(_load_item(et))
		designspace['instances'] = instances

	return designspace


def load(filename):
	"""Load designspace from a file name or object.
	   Returns a dictionary containing three (optional) items:
	   - list of "axes"
	   - list of "sources" (aka masters)
	   - list of "instances"
	"""
	return _load(ET.parse(filename))


def loads(string):
	"""Load designspace from a string."""
	return _load(ET.fromstring(string))

if __name__ == '__main__':
	import sys
	from pprint import pprint
	for f in sys.argv[1:]:
		pprint(load(f))
