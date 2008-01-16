#FLM: RoboFab Intro, Generating Fonts

#
#
#	demo generating fonts with robofab
#
#


# Generating fonts with RoboFab is super easy! Let's have a look.
# (you will need to have a font open in FontLab)

from robofab.world import CurrentFont
import os

# A little function for making folders. we'll need it later.
def makeFolder(path):
	#if the path doesn't exist, make it!
	if not os.path.exists(path):
		os.makedirs(path)

# We need to have a font open for this demo to work 
font = CurrentFont()
# This will tell us what folder the font is in
fontPath = os.path.dirname(font.path)

# We'll put the fonts into a folder called "FabFonts" next the .vfb file
macPath = os.path.join(fontPath, 'FabFonts', 'ForMac')
pcPath = os.path.join(fontPath, 'FabFonts', 'ForPC')
bothPath = os.path.join(fontPath, 'FabFonts', 'ForBoth')

# Now, we'll use that little function we made earlier to make the folders
makeFolder(macPath)
makeFolder(pcPath)
makeFolder(bothPath)

# A dict of all the font types we want to output
fontTypes = {	'mac'	:	['mactype1', 'macttf', 'macttdfont'],
		'pc'	:	['pctype1', 'pcmm'],
		'both'	:	['otfcff', 'otfttf']
		}

# Finally, let's generate the fonts!
for macType in fontTypes['mac']:
	print "generating %s..."%macType
	font.generate(macType, macPath)
for pcType in fontTypes['pc']:
	print "generating %s..."%pcType
	font.generate(pcType, pcPath)
for bothType in fontTypes['both']:
	print "generating %s..."%bothType
	font.generate(bothType, bothPath)
print 'Done!'

# Wow! Could it be any easier than that?
