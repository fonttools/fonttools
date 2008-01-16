#FLM: 010 FontLab to RoboFab and Back

# In which an adventurous glyph of your choice
# makes a trip into RoboFab land,
# and returns safely home after various inspections
# and modifications.

from robofab.world import CurrentGlyph, CurrentFont

c = CurrentGlyph()
f = CurrentFont()

from robofab.objects.objectsRF import RGlyph
d = RGlyph()

# woa! d is now  a rf version of a fl glyph!
d.appendGlyph(c)
d.width = 100

c.printDump()
d.printDump()

e = f.newGlyph('copyTest')

# dump the rf glyph back to a fl glyph!
e.appendGlyph(d)

# see, it still takes its own kind as well
e.appendGlyph(f['a'])
e.printDump()


