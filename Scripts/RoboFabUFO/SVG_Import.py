#FLM: SVG font import

from robofab.world import CurrentFont, NewFont
from robofab.tools.toolsSVG import SVGFontReader
from robofab.interface.all.dialogs import GetFile
import os


path = GetFile("Select SVG font file.")
if path is not None:
	print path
	font = NewFont()
	reader = SVGFontReader(path, font)
	
print "done"