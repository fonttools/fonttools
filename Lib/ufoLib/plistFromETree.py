from ufoLib.plistlib import PlistParser

__all__ = ["readPlistFromTree"]


def readPlistFromTree(tree):
	"""
	Given an ElementTree Element *tree*, parse Plist data and return the root
	object.
	"""
	parser = PlistTreeParser()
	return parser.parseTree(tree)


class PlistTreeParser(PlistParser):

	def parseTree(self, tree):
		self.parseElement(tree)
		return self.root

	def parseElement(self, element):
		self.handleBeginElement(element.tag, element.attrib)
		# if there are children, recurse
		for child in element:
			self.parseElement(child)
		# otherwise, parse the leaf's data
		if not len(element):
			# always pass str, not None
			self.handleData(element.text or "")
		self.handleEndElement(element.tag)
