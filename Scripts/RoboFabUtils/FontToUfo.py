"""Use fonttools to open TrueType, Type 1 or OpenType, then write a UFO."""

from robofab.tools.toolsAll import fontToUFO, guessFileType

if len(sys.argv) not in (2, 3):
	print "usage: FontToUfo.py <FontFile> [<output UFO file to create>]"
	sys.exit(1)
src = sys.argv[1]
if len(sys.argv) == 3:
	dst = sys.argv[2]
else:
	base, ext = os.path.splitext(src)
	dst = base + ".ufo"

fileType = guessFileType(src)
if fileType is None:
	print "Can't determine input file type"
	sys.exit(1)
print "Converting %s %r to %r" % (fileType, src, dst)
fontToUFO(src, dst)
