# To rename glyphs in a TrueType flavour file, something like this works:

font = fontTools.ttLib.TTFont(inpath)
glyphnames = font.getGlyphOrder()
# Do the renaming in glyphnames...
font = fontTools.ttLib.TTFont(inpath) # load again
font.setGlyphOrder(glyphnames)
post = font['post']
font.save(outpath)

# For CFF flavour files, we need to set 
# font['CFF '].cff.topDictIndex[0].charset but also to remap 
# font['CFF '].cff.topDictIndex[0].CharStrings 

cff = font['CFF '].cff.topDictIndex[0]
cff.ROS = ('Adobe','Identity',0)
mapping = {name:("cid"+str(n) if n else ".notdef") for n,name in enumerate(cff.charset)}
charstrings = cff.CharStrings
charstrings.charStrings = {mapping[name]:v for name,v in charstrings.charStrings.items()}
cff.charset = ["cid"+str(n) if n else ".notdef" for n in range(len(cff.charset))]
