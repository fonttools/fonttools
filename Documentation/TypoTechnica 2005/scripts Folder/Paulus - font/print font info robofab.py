#FLM: Print all font info Robofab

from robofab.world import CurrentFont

# f = SelectFont()
f = CurrentFont()

print "Number of glyphs:", str(len(f))
print "Number of kerning pairs:", str(len(f.kerning.keys()))


if f.info.familyName:
	print "f.info.familyName " + `f.info.familyName`
if f.info.fontStyle:
	print "f.info.fontStyle " + `f.info.fontStyle`
if f.info.styleName:
	print "f.info.styleName " + `f.info.styleName`
if f.info.fontName:
	print "f.info.fontName " + `f.info.fontName`
if f.info.fullName:
	print "f.info.fullName " + `f.info.fullName`
if f.info.menuName:
	print "f.info.menuName " + `f.info.menuName`
if f.info.fondName:
	print "f.info.fondName " + `f.info.fondName`
print ""
if f.info.otFamilyName:
	print "f.info.otFamilyName " + `f.info.otFamilyName`
if f.info.otStyleName:
	print "f.info.otStyleName " + `f.info.otStyleName`
if f.info.otMacName:
	print "f.info.otMacName " + `f.info.otMacName`
print ""
if f.info.year:
	print "f.info.year " + `f.info.year`
if f.info.copyright:
	print "f.info.copyright " + `f.info.copyright.encode('latin-1')`
if f.info.trademark:
	print "f.info.trademark " + `f.info.trademark.encode('latin-1')`
if f.info.notice:
	print "f.info.notice " + `f.info.notice.encode('latin-1')`
print ""
if f.info.designer:
	print "f.info.designer " + `f.info.designer.encode('latin-1')`
if f.info.designerURL:
	print "f.info.designerURL " + `f.info.designerURL`
if f.info.vendorURL:
	print "f.info.vendorURL " + `f.info.vendorURL`
print ""
if f.info.license:
	print "f.info.license " + `f.info.license.encode('latin-1')`
if f.info.licenseURL:
	print "f.info.licenseURL " + `f.info.licenseURL`
print ""
if f.info.versionMajor:
	print "f.info.versionMajor " + `f.info.versionMajor`
if f.info.versionMinor:
	print "f.info.versionMinor " + `f.info.versionMinor`
if f.info.ttVersion:
	print "f.info.ttVersion " + `f.info.ttVersion`
print ""
if f.info.ttUniqueID:
	print "f.info.ttUniqueID " + `f.info.ttUniqueID`
if f.info.uniqueID:
	print "f.info.uniqueID " + `f.info.uniqueID`
if f.info.ttVendor:
	print "f.info.ttVendor " + `f.info.ttVendor`
print ""
if f.info.unitsPerEm:
	print "f.info.unitsPerEm " + `f.info.unitsPerEm`
print ""
if f.info.ascender:
	print "f.info.ascender " + `f.info.ascender`
if f.info.capHeight:
	print "f.info.capHeight " + `f.info.capHeight`
if f.info.italicAngle:
	print "f.info.italicAngle " + `f.info.italicAngle`
if f.info.slantAngle:
	print "f.info.slantAngle " + `f.info.slantAngle`
print ""
if f.info.fondID:
	print "f.info.fondID " + `f.info.fondID`
print ""
if f.info.note:
	print "f.info.note " + `f.info.note.encode('latin-1')`
print ""

if f.info.msCharSet:
	print "f.info.msCharSet " + `f.info.msCharSet`
if f.info.selected:
	print "f.info.selected " + `f.info.selected`
if f.info.defaultWidth:
	print "f.info.defaultWidth " + `f.info.defaultWidth`
# print "f.info.parent " + `f.info.parent`
# print "f.info.weightName " + `f.info.weightName`
# print "f.info.weightValue " + `f.info.weightValue`
# print "f.info.widthName " + `f.info.widthName`
print "--- Done"
print ""
print ""
