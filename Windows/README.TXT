TTX 2.0 for Windows
-------------------------

Creating a Windows (9x/ME/NT/2000/XP) setup executable for TTX
This file has been created by Adam Twardoch <adam@twardoch.com>
September 9, 2002

1. Install Python 2.2.1 on your computer: http://www.python.org/2.2.1/
   or install ActivePython 2.2.1:
   http://www.activestate.com/Products/Download/Download.plex?id=ActivePython
2. Install py2exe: http://starship.python.net/crew/theller/py2exe/
3. Download the current CVS snapshot of TTX/FontTools:
   http://fonttools.sourceforge.net/cvs-snapshots/zip/fonttools-current-snapshot.zip
4. Unzip the CVS snapshot of TTX/FontTools into a folder.
5. In the folder where you unzipped TTX/FontTools, type:
   python.exe setup.py py2exe -f --icon Windows\ttx.ico --packages encodings
6. Install InnoSetup 3:
   http://www.jrsoftware.org/is3.php
7. Run Inno Setup and open Windows\fonttools-win-setup.iss (this file)
8. In Inno Setup, select File/Compile, then Run/Run.

The distributable TTX Windows setup executable has been saved
in the Output subfolder of the FontTools\Windows folder.

For information on running TTX on Windows, see fonttools-win-setup.txt in this folder. 
