"""
usage: comparefonts [options] fontA fontB  

    compareFonts %s -- TrueType Glyph Compare Tool

    General options:
    -h Help: print this message
    -v Verbose: be more verbose
    -f INDEX First: first glyph index of the range to be compared
    -l INDEX Last: last glyph index of the range to be compared
    -x HRES Hres: Horizontal resolution dpi
    -y VRES Vres: Vertical resolution dpi

    If no glyph index range is provided, all glyphs from FontA
    will be tested.
    If no horizonta/vertical dpi resolution is provided, glyphs
    will be rendered on the following resolutions: 72x72,
    300x300, 600x600, 1200x1200 and 2400x2400.
"""

from __future__ import print_function
import numpy
import sys
import getopt
import logging
from freetype import *
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

logger = logging.getLogger(" ")

def compareFontGlyphs(fontA, fontB, resoList, firstGlyphIndex, lastGlyphIndex):
    '''
    Test if glyphs of two TrueType font glyphs are identical. 
    Any glyph in fontA differing from fontB or glyphs will be
    reported.
    Any glyph indexes that fail to be loaded will also be reported.

    :param fontA: name of the base font file

    :param fontB: name of the font file that will be compared
                  against glyphs of fontA

    :param resoList: list of tuples for horizontal and vertical
                     resolution in dpi.
    
    :param glyphList: a list of glyph indexes to be compared. If
                      None, all glyphs from fontA will be tested.
    '''

    try:
        print("Loading font A:"+fontA+"...")
        faceA = Face(fontA)
    except:
        raise ValueError('Failed to load font ', fontA)

    try:
        print("Loading font B: "+fontB+"...")
        faceB = Face(fontB)
    except:
        raise ValueError('Failed to load font ', fontB)

    if(lastGlyphIndex == -1 or firstGlyphIndex > lastGlyphIndex):
        lastGlyphIndex = faceA.num_glyphs

    print("Range to be tested: %d-%d" % (firstGlyphIndex, lastGlyphIndex))

    glyphCount = 0

    for hres, vres in resoList:
        print("\nTesting at "+str(hres)+"x"+str(vres)+"dpi...")
        faceA.set_char_size( 32*32, 32*32, int(hres), int(vres))
        faceB.set_char_size( 32*32, 32*32, int(hres), int(vres))
      
        differCount = 0
        failCount = 0

        for charmap in faceA.charmaps:
            faceA.set_charmap(charmap)
            char, agindex = faceA.get_first_char()

            while( agindex != firstGlyphIndex and agindex < faceA.num_glyphs ):
                    char, agindex = faceA.get_next_char(char, agindex)

            while ( agindex and agindex <= lastGlyphIndex):
                glyphCount += 1
                try:
                    faceA.load_glyph(agindex)
                    faceB.load_glyph(agindex)
                    equal = compareGlyph(faceA.glyph, faceB.glyph)
                    if(not equal):
                        logger.info("Differing on glyph index %d", agindex)
                        differCount += 1
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    logger.warn("Failed to load glyph index %d", agindex)
                    failCount += 1
                char, agindex = faceA.get_next_char(char, agindex)
           
        print("Number of glyphs differing: %d" % differCount)
        if(failCount > 0):
            print("Failed to load %d glyphs" % failCount)

    print("\nTotal of %d glyphs inspected over %d different dpi resolutions"
            % ((lastGlyphIndex-firstGlyphIndex+1), len(resoList)) )

def compareGlyph(glyphA, glyphB):
    bitmapA = glyphA.bitmap
    bitmapB = glyphB.bitmap
    if( bitmapA.buffer != bitmapB.buffer or
        bitmapA.num_grays != bitmapB.num_grays or
        bitmapA.palette != bitmapB.palette or
        bitmapA.palette_mode != bitmapB.palette_mode or
        bitmapA.pitch != bitmapB.pitch or
        bitmapA.pixel_mode != bitmapB.pixel_mode or
        bitmapA.rows != bitmapB.rows or
        bitmapA.width != bitmapB.width ):
        return False  

    return True 

def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)

def usage():
    print(__doc__)
    sys.exit(2)

class Options(object):
    verbose = False
    firstGlyph = 1 
    lastGlyph = -1 
    resolutionList = [(72,72), (300, 300), (600, 600),
                      (1200, 1200), (2400, 2400)]

 
    def __init__(self, rawOptions, files):
        
        hres = 0
        vres = 0

        for option, value in rawOptions:
            if option == "-h":
                usage()
            elif option == "-v":
                self.verbose = True
            elif option == "-r":
                self.resolutionList = [(value, value)]
            elif option == "-f":
                if(int(value) > 0):
                    self.firstGlyph = int(value)
                else:
                    self.firstGlyph = 1
            elif option == "-l":
                if(value > self.firstGlyph):
                    self.lastGlyph = int(value)
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
        rawOptions, files = getopt.getopt(args, "hvr:f:l:x:y:")
    except getopt.GetoptError:
        usage()

    if not files or len(files) != 2:
        usage()
 
    for input in files:
        fileformat = input.split('.')[-1]
        if fileformat != 'ttf':
            usage()

    options = Options(rawOptions, files)
    return options, files[0], files[1]    

def main(args):
    
    try:
        options, fontA, fontB = parseOptions(args)
        compareFontGlyphs(fontA, fontB, options.resolutionList,
                          int(options.firstGlyph), int(options.lastGlyph))
    
    except ValueError as err:
        print(err)
    except KeyboardInterrupt:
        print ("\nInterrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    
if __name__ == "__main__":
    main(sys.argv[1:])
