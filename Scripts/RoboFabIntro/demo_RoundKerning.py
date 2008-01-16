"""round all kerning values to increments of a specified value"""

value  = 100

from robofab.world import CurrentFont

font = CurrentFont()
kerning = font.kerning
startCount = len(kerning)
kerning.round(value)
font.update()
print 'finished rounding kerning by %s.'%value
print 'you started with %s kerning pairs.'%startCount
print 'you now have %s kerning pairs.'%len(kerning)
