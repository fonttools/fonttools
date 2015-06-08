"""
usage: comparefonts [options] fontA fontB  

    compareFonts %s -- TrueType Glyph Compare Tool

    General options:
    -h Help: print this message
    -G AllGlyphs: execute prep plus hints for all glyphs in font
    -v Verbose: be more verbose
"""

from __future__ import print_function
import numpy
import sys
import getopt
from freetype import *
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

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
                     resolution in dpi. If None, 72x72, 300x300,
                     600x600, 1200x1200 and 2400x2400 dpi  will 
                     be used by default
    
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

        if(lastGlyphIndex > faceA.num_glyphs):
            lastGlyphIndex = faceA.num_glyphs

    print("Range to be tested: %d-%d" % (firstGlyphIndex, lastGlyphIndex))

    glyphCount = 0

    for hres, vres in resoList:
        print("\nTesting at "+str(hres)+"x"+str(vres)+"dpi...")
        faceA.set_char_size( 32*64, 32*64, int(hres), int(vres))
        faceB.set_char_size( 32*64, 32*64, int(hres), int(vres))
      
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
                        differCount += 1
                except:
                    failCount += 1
                char, agindex = faceA.get_next_char(char, agindex)
           
        print("Number of glyphs differing: %d" % differCount)
        if(failCount > 0):
            print("Failed to load %d glyphs" % failCount)

    print("\nTotal number of glyphs inspected: %d" % glyphCount)

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
    lastGlyph = 255 
    resolutionList = [(72,72), (300, 300), (600, 600),
                      (1200, 1200), (2400, 2400)]

 
    def __init__(self, rawOptions, files):
        for option, value in rawOptions:
            if option == "-h":
                usage()
            elif option == "-v":
                self.verbose = True
            elif option == "-r":
                self.resolutionList = [(value, value)]
            elif option == "-b":
                self.firstGlyph = value
            elif option == "-e":
                if(value > self.firstGlyph):
                    self.lastGlyph = value

def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "hvr:b:e:")
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
    
    options, fontA, fontB = parseOptions(args)
    compareFontGlyphs(fontA, fontB, options.resolutionList,
                      options.firstGlyph, options.lastGlyph)

if __name__ == "__main__":
    main(sys.argv[1:])

