from cgDocument.cgDocument import newDocument
from cgDocument.cgPen import CoreGraphicsPen
from robofab.world import CurrentGlyph, CurrentFont
from robofab.interface.all.dialogs import PutFile

import cgDocument.cgPen
reload(cgDocument.cgPen)

f = CurrentFont()
g = CurrentGlyph()

doc = newDocument((1000, 1000), "pdf")

pen = CoreGraphicsPen(f)
doc.setFillCMYK((1,1,0,1,1))

doc.scale((1, -1))
doc.rect((10, 10, 100, 100))

g.draw(pen)
pen.addToDocument(doc)

dst = PutFile("Save the pdf:")
if dst is not None:
	print dst
	doc.save(dst)