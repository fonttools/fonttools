# robofab manual
# Buildingaccents howto
#	AccentBuilder examples


from robofab.accentBuilder import AccentTools, buildRelatedAccentList
font = CurrentFont

# a list of accented glyphs that you want to build
myList=['Aacute', 'aacute']

# search for glyphs related to glyphs in myList and add them to myList
myList=buildRelatedAccentList(font, myList)+myList

# start the class
at=AccentTools(font, myList)

# clear away any anchors that exist (this is optional)
at.clearAnchors()

# add necessary anchors if you want to
at.buildAnchors(ucXOffset=20, ucYOffset=40, lcXOffset=15, lcYOffset=30)

# print a report of any errors that occured
at.printAnchorErrors()

# build the accented glyphs if you want to
at.buildAccents()

# print a report of any errors that occured
at.printAccentErrors()
