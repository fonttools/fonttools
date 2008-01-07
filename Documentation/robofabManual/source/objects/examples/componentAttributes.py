# robofab manual
# 	Component object
#	attribute examples

print f['adieresis'].components[0].baseGlyph
print f['adieresis'].components[1].baseGlyph

# move the component in the base glyph
f['adieresis'].components[1].offset = (100,100)

# scale the component in the base glyph
f['adieresis'].components[0].scale = (.5, .25)
