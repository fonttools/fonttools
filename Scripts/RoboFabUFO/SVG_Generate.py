#FLM: SVG font generate

from robofab.world import CurrentFont
from robofab.tools.toolsSVG import makeSVGFont
import os

f = CurrentFont()
if f is not None:
	path = os.path.splitext(f.path)[0]+".svg"
	makeSVGFont(f, path, exportKerning=False)
	
print "done"