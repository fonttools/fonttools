# robothon06
# get a pen and draw something in the current glyph
# what will it draw? ha! run the script and find out!

from robofab.world import CurrentGlyph
g = CurrentGlyph()
myPen = g.getPen()

# myPen is a pen object of a type meant for
# constructing paths in a glyph.
# So rather than use this pen with the glyph's
# own draw() method, we're going to tell it 
# to do things ourselves. (Just like DrawBot!)
print myPen

myPen.moveTo((344, 645))
myPen.lineTo((647, 261))
myPen.lineTo((662, -32))
myPen.lineTo((648, -61))
myPen.lineTo((619, -61))
myPen.lineTo((352, 54))
myPen.lineTo((72, 446))
myPen.lineTo((117, 590))
myPen.lineTo((228, 665))
myPen.closePath()
myPen.moveTo((99, 451))
myPen.lineTo((365, 74))
myPen.curveTo((359, 122), (376, 178), (420, 206))
myPen.curveTo((422, 203), (142, 579), (142, 579))
myPen.closePath()
myPen.moveTo((631, -32))
myPen.lineTo((629, 103))
myPen.curveTo((556, 111), (524, 71), (508, 20))
myPen.closePath()

g.update()

