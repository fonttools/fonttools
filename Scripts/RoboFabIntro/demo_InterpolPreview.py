#FLM: Interpol Preview

"""This script draws all incremental interpolations 
between 1% and 99% of a selected glyph into a new font.
It requires two open source fonts in FontLab."""

from robofab.interface.all.dialogs import SelectFont, OneList, ProgressBar
from robofab.world import NewFont

src1 = SelectFont('Select source font one:')
if src1:
	src2 = SelectFont('Select source font two:')
	if src2:
		# collect a list of all compatible glyphs
		common = []
		for glyphName in src1.keys():
			if src2.has_key(glyphName):
				if src1[glyphName].isCompatible(src2[glyphName]):
					common.append(glyphName)
		common.sort()
		selName = OneList(common, 'Select a glyph:')
		if selName:
			dest = NewFont()
			g1 = src1[selName]
			g2 = src2[selName]
			count = 1
			bar = ProgressBar('Interpolating...', 100)
			# add the sourec one glyph for reference
			dest.newGlyph(selName + '_000')
			dest[selName + '_000'].width = src1[selName].width
			dest[selName + '_000'].appendGlyph(src1[selName])
			dest[selName + '_000'].mark = 1
			dest[selName + '_000'].update()
			# add a new glyph and interpolate it
			while count != 100:
				factor = count * .01
				newName = selName + '_' + `count`.zfill(3)
				gD = dest.newGlyph(newName)
				gD.interpolate(factor, g1, g2)
				gD.update()
				bar.tick()
				count = count + 1
			# add the source two glyph for reference
			dest.newGlyph(selName + '_100')
			dest[selName + '_100'].width = src2[selName].width
			dest[selName + '_100'].appendGlyph(src2[selName])
			dest[selName + '_100'].mark = 1
			dest[selName + '_100'].update()		
			dest.update()
			bar.close()
