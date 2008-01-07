# robothon06
# get a pen and use it to print the coordinates
# to the output window. This is actually almost-python
# code which you can use it other scripts!

from robofab.world import CurrentFont
from robofab.pens.pointPen import PrintingSegmentPen

font = CurrentFont()
glyph = font['A']

# PrintingSegmentPen won't actually draw anything
# just print the coordinates to the output:
pen = PrintingSegmentPen()
glyph.draw(pen)
