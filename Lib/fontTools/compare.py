"""
usage: pyftcompare [options] fontA fontB inputFileOrURL 

    pyftcompare -- TrueType Glyph Compare Tool

    General options:
    -h Help: print this message
    -v Verbose: be more verbose
    -i Interrupt: interrupt execution if differing glyph found
    -e CODE Encoding: encoding used to read the input file
    -x HRES Hres: Horizontal resolution dpi
    -y VRES Vres: Vertical resolution dpi

    Default encoding for file is UTF-8.
    A list of supported encodings and their codes can be found at:
    https://docs.python.org/2/library/codecs.html
    If no horizonta/vertical dpi resolution is provided, glyphs
    will be rendered on the following resolutions: 72x72,
    300x300, 600x600, 1200x1200 and 2400x2400dpi.
"""

import sys
import getopt
import logging
import codecs
from freetype import *
from bs4 import BeautifulSoup
from fontTools.misc.inputParsing import getCharListFromInput
from fontTools.misc.compareFontFaces import compareFonts

def usage():
    print(__doc__)
    sys.exit(2)

class Options(object):
    encoding = 'utf-8'
    verbose = False
    interrupt = False 
    resolutionList = [(72,72), (300, 300), (600, 600),
                      (1200, 1200), (2400, 2400)]
 
    def __init__(self, rawOptions, files):
        
        hres = 0
        vres = 0

        for option, value in rawOptions:
            if option == "-h":
                usage()
            elif option == "-e":
                self.encoding = value
            elif option == "-v":
                self.verbose = True
            elif option == "-i":
                self.interrupt = True 
            elif option == "-x":
                hres = int(value)
            elif option == "-y":
                vres = int(value)

        if(self.verbose):
             logging.basicConfig(level = logging.INFO)
        else:
            logging.basicConfig(level = logging.ERROR)
        
        if(hres != 0 and vres == 0):
            vres = hres
        elif(vres != 0 and hres == 0):
            hres = vres
        if(hres != 0 and vres != 0):
            del self.resolutionList[:]
            self.resolutionList.append((hres, vres))

def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "hvie:x:y:")
    except getopt.GetoptError:
        usage()

    if not files or len(files) < 2:
        usage()
 
    options = Options(rawOptions, files)
    charList = []
    if len(files) > 2:
        charList = getCharListFromInput(files[2], options.encoding) 

    return options, files[0], files[1], charList    

def main(args):
    try:
        options, fontA, fontB, charList = parseOptions(args)
        compareFonts(fontA, fontB, charList, options.resolutionList, options.interrupt)
    
    except ValueError as err:
        print("ERROR: "+str(err))
    except KeyboardInterrupt:
        print("\nInterrupted")

if __name__ == "__main__":
    main(sys.argv[1:])
