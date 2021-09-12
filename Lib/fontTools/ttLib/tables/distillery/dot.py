"""Generates a Graphviz DOT file representing the (directed) graph of OTTableWriter objects."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import OTTableWriter
import logging
import sys
import math
from collections import deque

log = logging.getLogger(__name__)

def writerId(writer):
	s = '"' + writer.name

	if hasattr(writer, 'repeatIndex'):
		s += ' ' + str(writer.repeatIndex)

	s += '\n' + str(id(writer))
	return s + '"'

def writerLabel(writer):
	size = writer.getDataLength()
	return "%s\n%s bytes" % (writer.name, size)

def graph(font, tableTags, stream=sys.stdout):
	f = stream
	for tableTag in tableTags:
		log.debug("Processing %s", tableTag)
		table = font[tableTag].table

		writer = OTTableWriter(tableTag=tableTag)
		writer.name = tableTag
		table.compile(writer, font)

		f.write("digraph %s {\n" % tableTag)
		f.write(" rankdir=LR;\n")

		names = {}
		queue = deque()

		queue.append (writer)
		names[id(writer)] = tableTag
		f.write('graph [root=%s];\n' % tableTag)
		f.write('node [margin=0,width=0,height=0];\n')
		while queue:
			writer = queue.popleft()
			lhs = names[id(writer)]
			label = writerLabel(writer)
			size = writer.getDataLength()
			fontsize = 5+math.log(size) * 4
			color = "green" if len(writer.parents) > 1 else "black"
			f.write('%s [fontsize=%s,label="%s",color=%s]\n' % (lhs, fontsize, label, color))

			for item in writer.items:
				if not hasattr(item, "getData"):
					continue
				offsetSize = item.offsetSize
				rhs = writerId(item)
				f.write('  '+lhs+' -> '+rhs+';\n')

				if id(item) not in names:
					names[id(item)] = rhs
					queue.append(item)

		f.write("}\n")



def main(args=None):
	from fontTools import configLogger

	if args is None:
		args = sys.argv[1:]

	# configure the library logger (for >= WARNING)
	configLogger()
	# comment this out to enable debug messages from logger
	# log.setLevel(logging.DEBUG)

	if len(args) < 1:
		print("usage: fonttools ttLib.tables.distillery.dot font-file.ttf [table-tags...]", file=sys.stderr)
		sys.exit(1)

	font = TTFont(args[0])
	tags = args[1:]

	graph(font, tags)

if __name__ == '__main__':
	import sys
	sys.exit(main())
