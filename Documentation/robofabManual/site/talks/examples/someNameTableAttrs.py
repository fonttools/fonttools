# robothon06
# some attributes of the nametable
# this seems to work in FontLab 5
# it is broken in FontLab 4.6

from robofab.world import CurrentFont
from robofab.tools.nameTable import NameTable
f = CurrentFont()
nt = NameTable(f)

print 'copyright',  nt.copyright
print 'familyName', nt.familyName
print 'subfamilyName', nt.subfamilyName
print 'uniqueID', nt.uniqueID	# ok?
print 'fullName', nt.fullName
print 'versionString', nt.versionString
print 'postscriptName', nt.postscriptName
print 'trademark', nt.trademark
print 'manufacturer', nt.manufacturer
print 'designer', nt.designer
print 'description', nt.description
print 'vendorURL', nt.vendorURL
print 'designerURL', nt.designerURL
print 'license', nt.license
print 'licenseURL', nt.licenseURL
print 'preferredFamily', nt.preferredFamily
print 'preferredSubfamily', nt.preferredSubfamily
print 'compatibleFull', nt.compatibleFull
print 'sampleText', nt.sampleText
print 'postscriptCID', nt.postscriptCID