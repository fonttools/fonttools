# robofab manual
# 	Info object
#	usage examples


from robofab.world import CurrentFont
f = CurrentFont()
print f.info.fullName
print f.info.designer

f.info.designer = "Jan van Krimpen"
print f.info.designer
print f.info.ttVendor
print f.info.unitsPerEm
print f.info.xHeight
print f.info.licenseURL

# but you can set the values as well
f.info.uniqueID = 4309359
f.info.designer = "Eric Gill"
    