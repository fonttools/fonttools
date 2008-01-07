#FLM: Copy all glyphs to mask layer

from robofab.world import CurrentFont

f = CurrentFont()
for c in f:
	
	# go to the desired glyph
	fl.EditGlyph(c.index)
	
	# copy the desired glyph
	fl.CallCommand(fl_cmd.MaskClear)
	fl.CallCommand(fl_cmd.MaskCopy)
