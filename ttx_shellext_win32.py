# ttx_shellext_win32
# v1.03 matches ttLib 1.0a6

#! /usr/bin/env python

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

import sys, os, string, tempfile

if not sys.platform == 'win32':
  print 'This program is for Win32 (Windows 9x/NT) systems only.'
  sys.exit(2)

# get the folder where Python resides
pythondir = sys.exec_prefix

# get the folder where the TTX scripts reside
pth_file = open(os.path.join(sys.exec_prefix, "ttlib.pth"))
ttxdir = os.path.dirname(pth_file.read())
pth_file.close()

# escape backslashes (regedit.exe requires that the reg files are formatted that way)
pythondir = string.replace(pythondir, '\\', '\\\\')
ttxdir = string.replace(ttxdir, '\\', '\\\\')

# Prepare the text to write to the temporary reg file
regtext = 'REGEDIT4\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\.ttf]\n@="ttffile"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttffile\\shell]\n@=""\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttffile\\shell\\[TTX] Convert current TrueType to XML]\n@="[TTX] Convert current TrueType to XML"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttffile\\shell\\[TTX] Convert current TrueType to XML\\command]\n@="\\"' + pythondir + '\\\\python.exe\\" \\"' + ttxdir + '\\\\ttDump.py\\" \\"%1\\""\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttffile\\shell\\[TTX] Convert all TrueType to XML]\n@="[TTX] Convert all TrueType to XML"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttffile\\shell\\[TTX] Convert all TrueType to XML\\command]\n@="command.com /c for %%I in (*.ttf) do \\"' + pythondir + '\\\\python.exe\\" \\"' + ttxdir + '\\\\ttDump.py\\" \\"%%I\\""\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\.ttx]\n@="ttxfile"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttxfile]\n@="TTX Document"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttxfile\\shell]\n@=""\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttxfile\\shell\\[TTX] Convert current XML to TrueType]\n@="[TTX] Convert current XML to TrueType"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttxfile\\shell\\[TTX] Convert current XML to TrueType\\command]\n@="\\"' + pythondir + '\\\\python.exe\\" \\"' + ttxdir + '\\\\ttCompile.py\\" \\"%1\\""\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttxfile\\shell\\[TTX] Convert all XML to TrueType]\n@="[TTX] Convert all XML to TrueType"\n\n'
regtext = regtext + '[HKEY_CLASSES_ROOT\\ttxfile\\shell\\[TTX] Convert all XML to TrueType\\command]\n@="command.com /c for %%I in (*.ttx) do \\"' + pythondir + '\\\\python.exe\\" \\"' + ttxdir + '\\\\ttCompile.py\\" \\"%%I\\""\n\n'

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

