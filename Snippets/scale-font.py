"""
Script to change UnitsPerEm of a Font
USAGE:
scale-font.py path/to/inputFont.ttf targetUPM path/to/outputFont.ttf

Only works on .ttf (no CFF) for now

TO DO: add support for scaling GPOS lookups type 7 and 8
"""

from fontTools import ttLib
from sys import argv
from fontTools.misc.fixedTools import otRound

def scale_value_factor(value, scale_factor):
    return otRound(value * scale_factor)

def _scaleLookupType1(subTable, scale_factor):
    if subTable.Format == 1:
        for k, v in subTable.Value.__dict__.items():
            if k == 'XAdvance':
                subTable.Value.XAdvance = scale_value_factor(v, scale_factor)
            elif k == 'YAdvance':
                subTable.Value.YAdvance = scale_value_factor(v, scale_factor)
            elif k == 'XPlacement':
                subTable.Value.XPlacement = scale_value_factor(v, scale_factor)
            elif k == 'YPlacement':
                subTable.Value.YPlacement = scale_value_factor(v, scale_factor)
    if subTable.Format == 2:
        for value in subTable.Value:
            for k, v in value.__dict__.items():
                if k == 'XAdvance':
                    value.XAdvance = scale_value_factor(v, scale_factor)
                elif k == 'YAdvance':
                    value.YAdvance = scale_value_factor(v, scale_factor)
                elif k == 'XPlacement':
                    value.XPlacement = scale_value_factor(v, scale_factor)
                elif k == 'YPlacement':
                    value.YPlacement = scale_value_factor(v, scale_factor)


def _scaleLookupType2(subTable, scale_factor):
    # format 1: Single Pairs
    if subTable.Format == 1:
        for pairSet in subTable.PairSet:
            for pair in pairSet.PairValueRecord:
                if pair.Value1 is not None:
                    for k, v in pair.Value1.__dict__.items():
                        if k == 'XAdvance':
                            pair.Value1.XAdvance = scale_value_factor(v, scale_factor)
                        elif k == 'YAdvance':
                            pair.Value1.YAdvance = scale_value_factor(v, scale_factor)
                        elif k == 'XPlacement':
                            pair.Value1.XPlacement = scale_value_factor(v, scale_factor)
                        elif k == 'YPlacement':
                            pair.Value1.YPlacement = scale_value_factor(v, scale_factor)
                if pair.Value2 is not None:
                    for k, v in pair.Value2.__dict__.items():
                        if k == 'XAdvance':
                            pair.Value2.XAdvance = scale_value_factor(v, scale_factor)
                        elif k == 'YAdvance':
                            pair.Value2.YAdvance = scale_value_factor(v, scale_factor)
                        elif k == 'XPlacement':
                            pair.Value2.XPlacement = scale_value_factor(v, scale_factor)
                        elif k == 'YPlacement':
                            pair.Value2.YPlacement = scale_value_factor(v, scale_factor)

    # format 2: Class Pairs
    elif subTable.Format == 2:
        for class1Record in subTable.Class1Record:
            for class2Record in class1Record.Class2Record:
                if class2Record.Value2 is not None:
                    for k, v in class2Record.Value2.__dict__.items():
                        if k == 'XAdvance':
                            class2Record.Value2.XAdvance = scale_value_factor(v, scale_factor)
                        elif k == 'XPlacement':
                            class2Record.Value2.XPlacement = scale_value_factor(v, scale_factor)
                        else:
                            print("unknown: ", k)
                if class2Record.Value1 is not None:
                    for k, v in class2Record.Value1.__dict__.items():
                        if k == 'XAdvance':
                            class2Record.Value1.XAdvance = scale_value_factor(v, scale_factor)
                        elif k == 'XPlacement':
                            class2Record.Value1.XPlacement = scale_value_factor(v, scale_factor)


def _scaleLookupType3(subTable, scale_factor):
    for entryExitRecord in subTable.EntryExitRecord:
        entryExitRecord.EntryAnchor.XCoordinate = scale_value_factor(entryExitRecord.EntryAnchor.XCoordinate, scale_factor)
        entryExitRecord.EntryAnchor.YCoordinate = scale_value_factor(entryExitRecord.EntryAnchor.YCoordinate, scale_factor)
        entryExitRecord.ExitAnchor.XCoordinate = scale_value_factor(entryExitRecord.ExitAnchor.XCoordinate, scale_factor)
        entryExitRecord.ExitAnchor.YCoordinate = scale_value_factor(entryExitRecord.ExitAnchor.YCoordinate, scale_factor)

def _scaleLookupType4(subTable, scale_factor):
    for baseRecord in subTable.BaseArray.BaseRecord:
        for baseAnchor in baseRecord.BaseAnchor:
            if baseAnchor:
                baseAnchor.XCoordinate = scale_value_factor(baseAnchor.XCoordinate, scale_factor)
                baseAnchor.YCoordinate = scale_value_factor(baseAnchor.YCoordinate, scale_factor)
    for markRecord in subTable.MarkArray.MarkRecord:
        markRecord.MarkAnchor.XCoordinate = scale_value_factor(markRecord.MarkAnchor.XCoordinate, scale_factor)
        markRecord.MarkAnchor.YCoordinate = scale_value_factor(markRecord.MarkAnchor.YCoordinate, scale_factor)

def _scaleLookupType5(subTable, scale_factor):    
    for markRecord in subTable.MarkArray.MarkRecord:     
        markRecord.MarkAnchor.XCoordinate = scale_value_factor(markRecord.MarkAnchor.XCoordinate, scale_factor)
        markRecord.MarkAnchor.YCoordinate = scale_value_factor(markRecord.MarkAnchor.YCoordinate, scale_factor)
    for ligatureAttach in subTable.LigatureArray.LigatureAttach:
        for componentRecord in ligatureAttach.ComponentRecord:
            for ligatureAnchor in componentRecord.LigatureAnchor:
                ligatureAnchor.XCoordinate = scale_value_factor(ligatureAnchor.XCoordinate, scale_factor)
                ligatureAnchor.YCoordinate = scale_value_factor(ligatureAnchor.YCoordinate, scale_factor)
                
def _scaleLookupType6(subTable, scale_factor): 
    for mark1Record in subTable.Mark1Array.MarkRecord:
        mark1Record.MarkAnchor.XCoordinate = scale_value_factor(mark1Record.MarkAnchor.XCoordinate, scale_factor)
        mark1Record.MarkAnchor.YCoordinate = scale_value_factor(mark1Record.MarkAnchor.YCoordinate, scale_factor)
    for mark2Record in subTable.Mark2Array.Mark2Record:
        for mark2Anchor in mark2Record.Mark2Anchor:
            mark2Anchor.XCoordinate = scale_value_factor(mark2Anchor.XCoordinate, scale_factor)
            mark2Anchor.YCoordinate = scale_value_factor(mark2Anchor.YCoordinate, scale_factor)

def _scaleLookupType7(subTable, scale_factor):
    # TO DO
    pass 
    
def _scaleLookupType8(subTable, scale_factor):
    # TO DO
    pass        

def scale_font_toUPM(font, target_UPM):
    UPM = font['head'].unitsPerEm
    scale_factor =  target_UPM / UPM
    glyphOrder = font.getGlyphOrder()
    
    # HEAD
    font['head'].unitsPerEm = scale_value_factor(font['head'].unitsPerEm, scale_factor)
    font['head'].xMin = scale_value_factor(font['head'].xMin, scale_factor)
    font['head'].yMin = scale_value_factor(font['head'].yMin, scale_factor)
    font['head'].xMax = scale_value_factor(font['head'].xMax, scale_factor)
    font['head'].yMax = scale_value_factor(font['head'].yMax, scale_factor)
    
    # HHEA
    font['hhea'].ascent = scale_value_factor(font['hhea'].ascent, scale_factor)
    font['hhea'].descent = scale_value_factor(font['hhea'].descent, scale_factor)
    font['hhea'].lineGap = scale_value_factor(font['hhea'].lineGap, scale_factor)
    font['hhea'].advanceWidthMax = scale_value_factor(font['hhea'].advanceWidthMax, scale_factor)
    font['hhea'].minLeftSideBearing = scale_value_factor(font['hhea'].minLeftSideBearing, scale_factor)
    font['hhea'].minRightSideBearing = scale_value_factor(font['hhea'].minRightSideBearing, scale_factor)
    font['hhea'].xMaxExtent = scale_value_factor(font['hhea'].xMaxExtent, scale_factor)
    
    # HMTX
    for g in glyphOrder:
        scaledWidth = scale_value_factor(font['hmtx'].metrics[g][0], scale_factor)
        scaledLsb = scale_value_factor(font['hmtx'].metrics[g][1], scale_factor)
        font['hmtx'].metrics[g] = int(scaledWidth), int(scaledLsb)
    
    # OS/2
    font['OS/2'].xAvgCharWidth = scale_value_factor(font['OS/2'].xAvgCharWidth, scale_factor)
    font['OS/2'].ySubscriptXSize = scale_value_factor(font['OS/2'].ySubscriptXSize, scale_factor)
    font['OS/2'].ySubscriptYSize = scale_value_factor(font['OS/2'].ySubscriptYSize, scale_factor)
    font['OS/2'].ySubscriptXOffset = scale_value_factor(font['OS/2'].ySubscriptXOffset, scale_factor)
    font['OS/2'].ySubscriptYOffset = scale_value_factor(font['OS/2'].ySubscriptYOffset, scale_factor)
    font['OS/2'].ySuperscriptXSize = scale_value_factor(font['OS/2'].ySuperscriptXSize, scale_factor)
    font['OS/2'].ySuperscriptYSize = scale_value_factor(font['OS/2'].ySuperscriptYSize, scale_factor)
    font['OS/2'].ySuperscriptXOffset = scale_value_factor(font['OS/2'].ySuperscriptXOffset, scale_factor)
    font['OS/2'].ySuperscriptYOffset = scale_value_factor(font['OS/2'].ySuperscriptYOffset, scale_factor)
    font['OS/2'].yStrikeoutSize = scale_value_factor(font['OS/2'].yStrikeoutSize, scale_factor)
    font['OS/2'].yStrikeoutPosition = scale_value_factor(font['OS/2'].yStrikeoutPosition, scale_factor)
    font['OS/2'].sTypoAscender = scale_value_factor(font['OS/2'].sTypoAscender, scale_factor)
    font['OS/2'].sTypoDescender = scale_value_factor(font['OS/2'].sTypoDescender, scale_factor)
    font['OS/2'].sTypoLineGap = scale_value_factor(font['OS/2'].sTypoLineGap, scale_factor)
    font['OS/2'].usWinAscent = scale_value_factor(font['OS/2'].usWinAscent, scale_factor)
    font['OS/2'].usWinDescent = scale_value_factor(font['OS/2'].usWinDescent, scale_factor)
    font['OS/2'].sxHeight = scale_value_factor(font['OS/2'].sxHeight, scale_factor)
    font['OS/2'].sCapHeight = scale_value_factor(font['OS/2'].sCapHeight, scale_factor)

    # glyf
    for g in glyphOrder:
        if font['glyf'][g].isComposite():
            for component in font['glyf'][g].components:
                component.x = scale_value_factor(component.x, scale_factor)
                component.y = scale_value_factor(component.y, scale_factor)

        if hasattr(font['glyf'][g], 'xMin'):
            font['glyf'][g].xMin = scale_value_factor(font['glyf'][g].xMin, scale_factor)
        if hasattr(font['glyf'][g], 'yMin'):
            font['glyf'][g].yMin = scale_value_factor(font['glyf'][g].yMin, scale_factor)
        if hasattr(font['glyf'][g], 'xMax'):
            font['glyf'][g].xMax = scale_value_factor(font['glyf'][g].xMax, scale_factor)
        if hasattr(font['glyf'][g], 'yMax'):
            font['glyf'][g].yMax = scale_value_factor(font['glyf'][g].yMax, scale_factor)
        for i, c in enumerate(font['glyf'][g].getCoordinates(font['glyf'])[0]):
            scaled_x = scale_value_factor(c[0], scale_factor)
            scaled_y = scale_value_factor(c[1], scale_factor)
            font['glyf'][g].getCoordinates(font['glyf'])[0][i] = (scaled_x, scaled_y)
    
    # kern
    if 'kern' in font:
        for i, table in enumerate(font['kern'].kernTables):
            for k in table.kernTable.keys():
                table[k] = scale_value_factor(table[k], scale_factor)
  
    # GPOS
    if not 'GPOS' in font: return
    unknownAttributes = []
    for i, lookup in enumerate(font['GPOS'].table.LookupList.Lookup):
        for i, subTable in enumerate(lookup.SubTable):
            # Lookup Type 1, SinglePos
            if lookup.LookupType == 1:
                _scaleLookupType1(subTable, scale_factor)
            # lookup type 2: PairPos
            if lookup.LookupType == 2:
                _scaleLookupType2(subTable, scale_factor)
            # Lookup Type 3, CursivePos
            if lookup.LookupType == 3:
                _scaleLookupType3(subTable, scale_factor)
            # Lookup Type 4, MarkBasePos
            if lookup.LookupType == 4:
                _scaleLookupType4(subTable, scale_factor)
            # Lookup Type 5, markLigPos
            if lookup.LookupType == 5:
                _scaleLookupType5(subTable, scale_factor)
            # Lookup Type 6, MarkMarkPos
            if lookup.LookupType == 6:
                _scaleLookupType6(subTable, scale_factor)
            # Lookup Type 7, ContextPos
            if lookup.LookupType == 7:
                _scaleLookupType7(subTable, scale_factor)
            # Lookup Type 8, ChainContextPos
            if lookup.LookupType == 8:
                _scaleLookupType8(subTable, scale_factor)
            # Lookup Type 9, ExtensionPos
            if lookup.LookupType == 9:
                if subTable.ExtensionLookupType == 1:
                    _scaleLookupType1(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 2:
                    _scaleLookupType2(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 3:
                    _scaleLookupType3(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 4:
                    _scaleLookupType4(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 5:
                    _scaleLookupType5(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 6:
                    _scaleLookupType6(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 7:
                    _scaleLookupType7(subTable.ExtSubTable, scale_factor)
                if subTable.ExtensionLookupType == 8:
                    _scaleLookupType8(subTable.ExtSubTable, scale_factor)


def main():
    if not argv: return

    inputPath = argv[1]
    targetUPM = int(argv[2])
    outputPath = argv[3]

    inputFont = ttLib.TTFont(inputPath)
    scale_font_toUPM(inputFont, targetUPM)
    inputFont.save(outputPath)

if __name__ == '__main__':
    main()
