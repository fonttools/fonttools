from __future__ import absolute_import
import sys
"""
Small helper module to parse Plist-formatted data from trees as created
by xmlTreeBuilder.
"""

__all__ = "readPlistFromTree"

try:
	from plistlib import _PlistParser

	if sys.version_info >= (3, 4):
		class PlistParser(_PlistParser):

			def __init__(self):
				super().__init__(use_builtin_types=True, dict_type=dict)

			def parseElement(self, *args, **kwargs):
				super().parse_element(*args, **kwargs)

			def handleBeginElement(self, *args, **kwargs):
				super().handle_begin_element(*args, **kwargs)

			def handleData(self, *args, **kwargs):
				super().handle_data(*args, **kwargs)

			def handleEndElement(self, *args, **kwargs):
				super().handle_end_element(*args, **kwargs)
	else:
		PlistParser = _PlistParser
except ImportError:
	from plistlib import PlistParser

def readPlistFromTree(tree):
	"""
	Given a (sub)tree created by xmlTreeBuilder, interpret it
	as Plist-formatted data, and return the root object.
	"""
	parser = PlistTreeParser()
	return parser.parseTree(tree)


class PlistTreeParser(PlistParser):

	def parseTree(self, tree):
		element, attributes, children = tree
		self.parseElement(element, attributes, children)
		return self.root

	def parseElement(self, element, attributes, children):
		self.handleBeginElement(element, attributes)
		for child in children:
			if isinstance(child, tuple):
				self.parseElement(child[0], child[1], child[2])
			else:
				self.handleData(child)
		self.handleEndElement(element)


if __name__ == "__main__":
	from ufoLib.xmlTreeBuilder import buildTree
	tree = buildTree("xxx.plist", stripData=0)
	print(readPlistFromTree(tree))
