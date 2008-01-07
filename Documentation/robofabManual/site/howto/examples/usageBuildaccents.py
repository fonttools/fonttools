# robofab manual
# 	Buildingaccents howto
#	usage examples


from robofab.world import CurrentFont

f = CurrentFont()
f.newGlyph("aacute")
f["aacute"].appendComponent("a")
f["aacute"].appendComponent("acute", (200, 0))
f["aacute"].width = f["a"].width
f.update()
