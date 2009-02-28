#FLM: RoboFab Intro, FoundrySettings.plist

#
#
#	demo FoundrySettings.plist
#
#

# Setting all the data strings in the FontLab font header can be a repetitive and
# tedious exercise. RoboFab to the rescue! RoboFab features some nifty tools
# that help automate this process. These tools read a .plist file that you are free
# to edit to include your own standard settings. Currently, the .plist file contains
# these bits of data. We reserve the right to add more in the future.
#	-copyright
#	-trademark
#	-license
#	-licenseurl
#	-notice
#	-ttvendor
#	-vendorurl
#	-designer
#	-designerurl
#
# The foundry settings tools parse this .plist file into a python dictionary that
# can be used to apply the data to fonts. It's really easy to use. Let's check it out!


from robofab.world import CurrentFont
from robofab.tools.toolsFL import makeDataFolder
# all the foundry settings tools live here:
from robofab.tools.toolsAll import readFoundrySettings, getFoundrySetting, setFoundrySetting
import time
import os

# You will need a font open in fontlab for this demo
font = CurrentFont()

# We need to know where the .plist file lives. In the FontLab environment
# it can live in the "RoboFab Data" folder with its friends. makeDataFolder()
# will make the data folder if it doesn't exist and it will return the path
settingsPath = os.path.join(makeDataFolder(), 'FoundrySettings.plist')

# Now, let's load those settings up
# readFoundrySettings(path) will return the data from the .plist as dictionary
mySettings = readFoundrySettings(settingsPath)

# Let's get the current year so that the year string is always up to date 
font.info.year = time.gmtime(time.time())[0]

# Apply those settings that we just loaded
font.info.copyright = mySettings['copyright']
font.info.trademark = mySettings['trademark']
font.info.openTypeNameLicense = mySettings['license']
font.info.openTypeNameLicenseURL = mySettings['licenseurl']
font.info.openTypeNameDescription = mySettings['notice']
font.info.openTypeOS2VendorID = mySettings['ttvendor']
font.info.openTypeNameManufacturerURL = mySettings['vendorurl']
font.info.openTypeNameDesigner = mySettings['designer']
font.info.openTypeNameDesignerURL = mySettings['designerurl']

# and call the update method
font.update()

# But, Prof. RoboFab, what if I want to change the settings in the .plist file?
# Good question. You can always edit the .plist data by hand, or you can
# do it via a script. It would go a little something like this:
setFoundrySetting('trademark', 'This font is a trademark of Me, Myself and I', settingsPath)
# If you are on OSX, and you have the Apple developers tools installed, you
# can also edit it with /Developer/Applications/Property List Editor.

# And to read only only one setting from the file you can use this handly little method.
font.info.trademark = getFoundrySetting('trademark', settingsPath)
font.update()

# It's that easy!
