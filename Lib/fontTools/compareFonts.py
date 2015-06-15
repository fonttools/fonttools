"""
usage: pyftcompare [options] fontA fontB inputFile 

    pyftcompare -- TrueType Glyph Compare Tool

    General options:
    -h Help: print this message
    -v Verbose: be more verbose
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

logger = logging.getLogger(" ")

def compareFontGlyphs(fontA, fontB, charList, resolutionList):
    '''
    Test if a set of glyphs present in the input file are
    identifical for the two given TrueType fonts.

    :param fontA: name of the first font file

    :param fontB: name of the second font file

    :param charList: list of chars to be compared

    :param resolutionList: list of tuples for horizontal and vertical
                     resolution in dpi.
    '''

    try:
        print("Loading font: "+fontA+"...")
        faceA = Face(fontA)
    except:
        raise ValueError('Failed to load font '+fontA)

    try:
        print("Loading font: "+fontB+"...")
        faceB = Face(fontB)
    except:
        raise ValueError('Failed to load font '+fontB)

    for hres, vres in resolutionList:

        differList = []
        identicalList = []
        aNotFoundList = []
        bNotFoundList = []
        notFoundCount = 0

        print("\nTesting at "+str(hres)+"x"+str(vres)+"dpi...")
        faceA.set_char_size( 32*32, 32*32, int(hres), int(vres))
        faceB.set_char_size( 32*32, 32*32, int(hres), int(vres))
     
        try:
            for charmap in faceA.charmaps:
                faceA.set_charmap(charmap)
               
                for char in charList:
     
                    aGlyphIndex = faceA.get_char_index(char)
                    bGlyphIndex = faceB.get_char_index(char)

                    if(aGlyphIndex == 0 or bGlyphIndex == 0):
                        notFoundCount += 1
                        if(aGlyphIndex == 0):
                            aNotFoundList.append(char)
                        if(bGlyphIndex == 0):             
                            bNotFoundList.append(char)
                    else:
                        faceA.load_glyph(aGlyphIndex)
                        faceB.load_glyph(bGlyphIndex)
                        equal = compareGlyph(faceA.glyph, faceB.glyph)
                        if(equal):
                            identicalList.append(char)
                        else:
                            differList.append(char)
                
        except KeyboardInterrupt:
            raise KeyboardInterrupt

        print("Number of identical glyphs: %d" % len(identicalList))
        logger.info("Identical glyphs: "+listToStr(identicalList))
        print("Number of glyphs differing: %d" % len(differList))
        logger.info("Differing glyphs: "+listToStr(differList))
        print("Number of not found glyphs: %d" % notFoundCount)
        logger.info("Glyphs not found in "+fontA+": "+listToStr(aNotFoundList))
        logger.info("Glyphs not found in "+fontB+": "+listToStr(bNotFoundList))
 
    print("\nTotal of %d glyphs inspected over %d different dpi resolutions"
            % (len(charList), len(resolutionList)) )

def compareGlyph(glyphA, glyphB):
    bitmapA = glyphA.bitmap
    bitmapB = glyphB.bitmap
    if(bitmapA.buffer != bitmapB.buffer or
        bitmapA.num_grays != bitmapB.num_grays or
        bitmapA.palette != bitmapB.palette or
        bitmapA.palette_mode != bitmapB.palette_mode or
        bitmapA.pitch != bitmapB.pitch or
        bitmapA.pixel_mode != bitmapB.pixel_mode or
        bitmapA.rows != bitmapB.rows or
        bitmapA.width != bitmapB.width ):
        return False  

    return True 

def listToStr(charList):
    string = ''
    for char in charList:
        string += char+' '
    return string

def readFile(input, encoding):
    try:
        with codecs.open(input) as file:
            data=file.read()
    except:
        raise ValueError("Couldn't open file "+input)

    try:
        data = data.decode(encoding)
    except:
        raise ValueError("Different encoding or wrong code provided: "+encoding)
    charList = list(set(data))
    return charList

def usage():
    print(__doc__)
    sys.exit(2)

class Options(object):
    encoding = 'utf-8'
    verbose = False
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
        rawOptions, files = getopt.getopt(args, "hve:x:y:")
    except getopt.GetoptError:
        usage()

    if not files or len(files) != 3:
        usage()
 
    options = Options(rawOptions, files)
    charList = readFile(files[2], options.encoding)
    
    return options, files[0], files[1], charList    

def main(args):
    
    try:
        options, fontA, fontB, charList = parseOptions(args)
        compareFontGlyphs(fontA, fontB, charList, options.resolutionList)
    
    except ValueError as err:
        print("ERROR: "+str(err))
    except KeyboardInterrupt:
        print("\nInterrupted")

if __name__ == "__main__":
    main(sys.argv[1:])
