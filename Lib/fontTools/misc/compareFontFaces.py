import logging
from freetype import *

logger = logging.getLogger(" ")

def compareFonts(fontA, fontB, charList, resolutionList, interrupt=False):
    '''
    Test if a set of glyphs present in the input file are
    identifical for the two given TrueType fonts.

    :param fontA: name of the first font file

    :param fontB: name of the second font file

    :param charList: list of chars to be compared

    :param resolutionList: list of tuples for horizontal and vertical
                     resolution in dpi.

    :param interrupt: interrupt if differing or not found glyph
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

        def loadAndCompareGlyph(aGlyphIndex, bGlyphIndex, char=None):

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

        try:
            for charmapA, charmapB in zip(faceA.charmaps, faceB.charmaps):
                faceA.set_charmap(charmapA)
                faceB.set_charmap(charmapB)

                if charList:

                    for char in charList:

                        aGlyphIndex = faceA.get_char_index(char)
                        bGlyphIndex = faceB.get_char_index(char)
                        loadAndCompareGlyph(aGlyphIndex, bGlyphIndex, char)

                else:

                    charcodeA, aGlyphIndex = faceA.get_first_char()
                    charcodeB, bGlyphIndex = faceB.get_first_char()
                    while aGlyphIndex != 0:
                        loadAndCompareGlyph(aGlyphIndex, bGlyphIndex)
                        charcodeA, aGlyphIndex  = faceA.get_next_char(charcodeA, aGlyphIndex)
                        charcodeB, bGlyphIndex  = faceA.get_next_char(charcodeB, bGlyphIndex)
                
                if interrupt:
                    assert len(differList)==0 
                    assert notFoundCount==0
                    
        except KeyboardInterrupt:
            raise KeyboardInterrupt

        print("Number of identical glyphs: %d" % len(identicalList))
        logger.info("Identical glyphs: ")
        logger.info(str(identicalList).encode('utf-8'))
        print("Number of glyphs differing: %d" % len(differList))
        logger.info("Differing glyphs: ")
        logger.info(str(differList).encode('utf-8'))
        print("Number of not found glyphs: %d-%d" % (len(aNotFoundList), len(bNotFoundList)))
        logger.info("Glyphs not found in "+fontA+": ")
        logger.info(str(aNotFoundList).encode('utf-8'))
        logger.info("Glyphs not found in "+fontB+": ")
        logger.info(str(bNotFoundList).encode('utf-8'))
 
    print("\nFinished glyphs inspection over %d different dpi resolutions"
            % (len(resolutionList)))


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
