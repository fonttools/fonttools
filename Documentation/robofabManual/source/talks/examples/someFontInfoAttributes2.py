# robothon06
# setting data in the info object

from robofab.world import CurrentFont

font = CurrentFont()
# naming attributes
font.info.familyName = "MyFamily"
print font.info.familyName
font.info.styleName = "Roman"
print font.info.styleName
font.info.fullName = font.info.familyName + '-' + font.info.styleName
print font.info.fullName
# dimension attributes
font.info.ascender = 600
print font.info.ascender
font.info.descender = -400
print font.info.descender
font.update()

