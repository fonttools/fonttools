# ttx_shellext_win32
# v1.04 matches ttLib 1.0a6

# This script installs a Windows 9x/NT shell extension for TTX
# After installing it, click with the right mouse button on a TrueType file
# and choose "[TTX] Convert current TrueType to XML" from the context menu
# to start the ttDump.py program with the selected TrueType file
# or "[TTX] Convert all TrueType to XML" to start the ttDump.py program 
# with all TrueType files in the current directory. 
# The other way around works analogically. 

# v1.0 written 26.08.1999 by Adam Twardoch <twardoch@font.org>
# v1.01 revised 26.01.2000 by Adam Twardoch <twardoch@font.org>
# v1.03 revised 16.02.2000 to match ttLib 1.0a6
# v1.04 revised 29.04.2000 to match FontTools.pth
# v1.05 revised 10.08.2001 cleaned up regtext for clarity (jvr)

import sys, os, string, tempfile

if not sys.platform == 'win32':
  print 'This program is for Win32 (Windows 9x/NT) systems only.'
  sys.exit(2)

# get the folder where Python resides
pythondir = sys.exec_prefix

# get the folder where the TTX scripts reside
pth_file = open(os.path.join(sys.exec_prefix, "FontTools.pth"))
ttxdir = os.path.dirname(pth_file.read())
pth_file.close()

# escape backslashes (regedit.exe requires that the reg files are formatted that way)
pythondir = string.replace(pythondir, '\\', '\\\\')
ttxdir = string.replace(ttxdir, '\\', '\\\\')

# Prepare the text to write to the temporary reg file
regtext = r"""REGEDIT4

[HKEY_CLASSES_ROOT\.ttf]
@="ttffile"

[HKEY_CLASSES_ROOT\ttffile\shell]
@=""

[HKEY_CLASSES_ROOT\ttffile\shell\[TTX] Convert current TrueType to XML]
@="[TTX] Convert current TrueType to XML"

[HKEY_CLASSES_ROOT\ttffile\shell\[TTX] Convert current TrueType to XML\command]
@="\"%(pythondir)s\\python.exe\" \"%(ttxdir)s\\ttDump.py\" \"%%1\""

[HKEY_CLASSES_ROOT\ttffile\shell\[TTX] Convert all TrueType to XML]
@="[TTX] Convert all TrueType to XML"

[HKEY_CLASSES_ROOT\ttffile\shell\[TTX] Convert all TrueType to XML\command]
@="command.com /c for %%%%I in (*.ttf) do \"%(pythondir)s\\python.exe\" \"%(ttxdir)s\\ttDump.py\" \"%%%%I\""

[HKEY_CLASSES_ROOT\.ttx]
@="ttxfile"

[HKEY_CLASSES_ROOT\ttxfile]
@="TTX Document"

[HKEY_CLASSES_ROOT\ttxfile\shell]
@=""

[HKEY_CLASSES_ROOT\ttxfile\shell\[TTX] Convert current XML to TrueType]
@="[TTX] Convert current XML to TrueType"

[HKEY_CLASSES_ROOT\ttxfile\shell\[TTX] Convert current XML to TrueType\command]
@="\"%(pythondir)s\\python.exe\" \"%(ttxdir)s\\ttCompile.py\" \"%%1\""

[HKEY_CLASSES_ROOT\ttxfile\shell\[TTX] Convert all XML to TrueType]
@="[TTX] Convert all XML to TrueType"

[HKEY_CLASSES_ROOT\ttxfile\shell\[TTX] Convert all XML to TrueType\command]
@="command.com /c for %%%%I in (*.ttx) do \"%(pythondir)s\\python.exe\" \"%(ttxdir)s\\ttCompile.py\" \"%%%%I\""

""" % globals()


# Create the temporary reg file which will be joined into the Windows registry
reg_file_name = os.path.join(os.path.dirname(tempfile.mktemp()), "~ttxtemp.reg")
reg_file = open(reg_file_name, "w")
reg_file.write(regtext)
reg_file.close()

# Join the temporary reg file into the Windows registry
execline = '%windir%\\regedit.exe ' + reg_file_name

file = os.popen(execline)
output = ""
while 1:
  chunk = file.read(1000)
  if not chunk:
    break
    output = output + chunk

print output

os.remove(reg_file_name)

