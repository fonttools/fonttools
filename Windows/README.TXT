FontTools 1.0 for Windows
-------------------------

Creating a Windows (9x/ME/NT/2000/XP) setup executable for FontTools
This file has been created by Adam Twardoch <adam@twardoch.com>
September 9, 2002

1. Install Python 2.2.1 on your computer: http://www.python.org/2.2.1/
   or install ActivePython 2.2.1:
   http://www.activestate.com/Products/Download/Download.plex?id=ActivePython
2. Install py2exe: http://starship.python.net/crew/theller/py2exe/
3. Download the current CVS snapshot of FontTools:
   http://fonttools.sourceforge.net/cvs-snapshots/zip/fonttools-current-snapshot.zip
4. Unzip the CVS snapshot of FontTools into a folder.
5. In the folder where you unzipped FontTools, type:
   python.exe setup.py py2exe -O2 -f --icon Win\fonttools.ico
7. Install InnoSetup 3:
   http://www.jrsoftware.org/is3.php
8. Run Inno Setup and open Win\fonttools-win-setup.iss (this file)
9. In Inno Setup, select File/Compile, then Run/Run.

The distributable FontTools Windows setup executable has been saved
in the Output subfolder of the FontTools\Win folder.

For information on running FontTools on Windows, see fonttools-win-setup.txt in this folder. 
