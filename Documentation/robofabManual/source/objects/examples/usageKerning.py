# robofab manual
# 	Kerning object
#	usage examples

f = CurrentFont()
print f.kerning

# getting a value from the kerning dictionary
print f.kerning[('V', 'A')]
print f.kerning[('T', 'X')]
print f.kerning.keys()

