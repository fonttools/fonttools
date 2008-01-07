# robofab manual
# 	Glifnames howto
#	glyphNameToShortFileName examples


# examples of glyphname to glif name transformations
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName

# a short name
print glyphNameToShortFileName("accent", None)

# a short name, starting with capital letter
print glyphNameToShortFileName("Accent", None)

# a really long name - note the hexadecimal hash at the end
print glyphNameToShortFileName("this_is_a_very_long_glyph_name.altswash2", None)

# a name with a period in it, 1
print glyphNameToShortFileName("a.alt", None)

# a name with a period in it, 2
print glyphNameToShortFileName(".notdef", None)
