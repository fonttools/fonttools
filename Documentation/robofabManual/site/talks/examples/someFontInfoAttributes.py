# robothon06
# getting data from the info object

from robofab.world import CurrentFont

font = CurrentFont()
# naming attributes
print font.info.familyName
print font.info.styleName
print font.info.fullName
# dimension attributes
print font.info.unitsPerEm
print font.info.ascender
print font.info.descender
