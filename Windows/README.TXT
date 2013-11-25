
TTX 2.0 for Windows
-------------------------

Creating a Windows (9x/ME/NT/2000/XP) setup executable for TTX
This file has been created by Adam Twardoch <list.adam@twardoch.com>
December 14, 2004

Pre-compiled versions are hosted at http://www.font.org/software/ttx/

APPROACH I: Using py2exe and InnoSetup

1. Install Python 2.3 for Windows: http://www.python.org/
2. Install py2exe: http://starship.python.net/crew/theller/py2exe/
3. Install InnoSetup 4: http://www.jrsoftware.org/
4. Download the latest released source code of TTX/FontTools at
   http://sourceforge.net/projects/fonttools/
   Or alternatively grab the sources from the VCS:
   http://fonttools.sourceforge.net/
5. Unzip the source code of TTX/FontTools into a folder.
6. In the folder where you unzipped TTX/FontTools, type:
   python setup.py py2exe --icon Windows\ttx.ico --packages encodings
7. Run Inno Setup and open Windows\fonttools-win-setup.iss
8. In Inno Setup, select File/Compile, then Run/Run.

APPROACH II: Using McMillan Installer and InnoSetup

1. Install Python 2.3 for Windows: http://www.python.org/
2. Download and unpack McMillan installer: 
   http://py.vaults.ca/apyllo2.py/22208368
   and put the Installer folder into your Python folder, 
   e.g. C:\Python23\Installer
3. Install InnoSetup 4: http://www.jrsoftware.org/
4. Install Microsoft Visual C++ Toolkit 2003: 
   http://msdn.microsoft.com/visualc/vctoolkit2003/
5. Put UPX somewhere within your PATH: http://upx.sourceforge.net/
6. Download the latest released source code of TTX/FontTools at
   http://sourceforge.net/projects/fonttools/
   Or alternatively grab the sources from the VCS:
   http://fonttools.sourceforge.net/
7. Unzip the source code of TTX/FontTools into a folder.
8. In the folder where you unzipped TTX/FontTools, type:
   python setup.py install -f 
9. Edit mcmillan.bat so the paths in the file correspond to the paths in your system, 
   and run it. 
10.Run Inno Setup and open Windows\fonttools-win-setup.iss
11.In Inno Setup, select File/Compile, then Run/Run.

The distributable TTX Windows setup executable has been saved
in the Output subfolder of the FontTools\Windows folder.

For information on running TTX on Windows, see fonttools-win-setup.txt in this folder. 

