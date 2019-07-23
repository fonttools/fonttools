"""
Script to change UnitsPerEm of a Font
USAGE:
scale-font.py path/to/inputFont.ttf targetUPM path/to/outputFont.ttf

Only works on .ttf (no CFF) for now
"""

from fontTools import ttLib
from sys import argv

def scaleValue_toUPM(value, UPM, target_UPM):
    if value < 0.0 :
        return int ( ( value * target_UPM -0.5 ) / UPM )
    else:
        return int ( ( value * target_UPM +0.5 ) / UPM )

def scaleLookupType1(subTable, UPM, target_UPM):
    if subTable.Format == 1:
        for k, v in subTable.Value.__dict__.items():
            if k == 'XAdvance':
                subTable.Value.XAdvance = scaleValue_toUPM(v, UPM, target_UPM)
            elif k == 'YAdvance':
                subTable.Value.YAdvance = scaleValue_toUPM(v, UPM, target_UPM)
            elif k == 'XPlacement':
                subTable.Value.XPlacement = scaleValue_toUPM(v, UPM, target_UPM)
            elif k == 'YPlacement':
                subTable.Value.YPlacement = scaleValue_toUPM(v, UPM, target_UPM)                  
    if subTable.Format == 2:
        for value in subTable.Value:
            for k, v in value.__dict__.items():
                if k == 'XAdvance':
                    value.XAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                elif k == 'YAdvance':
                    value.YAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                elif k == 'XPlacement':
                    value.XPlacement = scaleValue_toUPM(v, UPM, target_UPM)
                elif k == 'YPlacement':
                    value.YPlacement = scaleValue_toUPM(v, UPM, target_UPM)


def scaleLookupType2(subTable, UPM, target_UPM):
    # format 1: Single Pairs
    if subTable.Format == 1:
        for pairSet in subTable.PairSet:
            for pair in pairSet.PairValueRecord:
                if pair.Value1 is not None:
                    for k, v in pair.Value1.__dict__.items():
                        if k == 'XAdvance':
                            pair.Value1.XAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'YAdvance':
                            pair.Value1.YAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'XPlacement':
                            pair.Value1.XPlacement = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'YPlacement':
                            pair.Value1.YPlacement = scaleValue_toUPM(v, UPM, target_UPM)
                if pair.Value2 is not None:
                    for k, v in pair.Value2.__dict__.items():
                        if k == 'XAdvance':
                            pair.Value2.XAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'YAdvance':
                            pair.Value2.YAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'XPlacement':
                            pair.Value2.XPlacement = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'YPlacement':
                            pair.Value2.YPlacement = scaleValue_toUPM(v, UPM, target_UPM)

    # format 2: Class Pairs
    elif subTable.Format == 2:
        for class1Record in subTable.Class1Record:
            for class2Record in class1Record.Class2Record:
                if class2Record.Value2 is not None:
                    for k, v in class2Record.Value2.__dict__.items():
                        if k == 'XAdvance':
                            class2Record.Value2.XAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'XPlacement':
                            class2Record.Value2.XPlacement = scaleValue_toUPM(v, UPM, target_UPM)
                        else:
                            print("unknown: ", k)
                if class2Record.Value1 is not None:
                    for k, v in class2Record.Value1.__dict__.items():
                        if k == 'XAdvance':
                            class2Record.Value1.XAdvance = scaleValue_toUPM(v, UPM, target_UPM)
                        elif k == 'XPlacement':
                            class2Record.Value1.XPlacement = scaleValue_toUPM(v, UPM, target_UPM)


def scaleLookupType3(subTable, UPM, target_UPM):
    for entryExitRecord in subTable.EntryExitRecord:
        entryExitRecord.EntryAnchor.XCoordinate = scaleValue_toUPM(entryExitRecord.EntryAnchor.XCoordinate, UPM, target_UPM)
        entryExitRecord.EntryAnchor.YCoordinate = scaleValue_toUPM(entryExitRecord.EntryAnchor.YCoordinate, UPM, target_UPM)
        entryExitRecord.ExitAnchor.XCoordinate = scaleValue_toUPM(entryExitRecord.ExitAnchor.XCoordinate, UPM, target_UPM)
        entryExitRecord.ExitAnchor.YCoordinate = scaleValue_toUPM(entryExitRecord.ExitAnchor.YCoordinate, UPM, target_UPM)

def scaleLookupType4(subTable, UPM, target_UPM):
    for baseRecord in subTable.BaseArray.BaseRecord:
        for baseAnchor in baseRecord.BaseAnchor:
            if baseAnchor:
                baseAnchor.XCoordinate = scaleValue_toUPM(baseAnchor.XCoordinate, UPM, target_UPM)
                baseAnchor.YCoordinate = scaleValue_toUPM(baseAnchor.YCoordinate, UPM, target_UPM)
    for markRecord in subTable.MarkArray.MarkRecord:
        markRecord.MarkAnchor.XCoordinate = scaleValue_toUPM(markRecord.MarkAnchor.XCoordinate, UPM, target_UPM)
        markRecord.MarkAnchor.YCoordinate = scaleValue_toUPM(markRecord.MarkAnchor.YCoordinate, UPM, target_UPM)

def scaleLookupType5(subTable, UPM, target_UPM):    
    for markRecord in subTable.MarkArray.MarkRecord:     
        markRecord.MarkAnchor.XCoordinate = scaleValue_toUPM(markRecord.MarkAnchor.XCoordinate, UPM, target_UPM)
        markRecord.MarkAnchor.YCoordinate = scaleValue_toUPM(markRecord.MarkAnchor.YCoordinate, UPM, target_UPM)
    for ligatureAttach in subTable.LigatureArray.LigatureAttach:
        for componentRecord in ligatureAttach.ComponentRecord:
            for ligatureAnchor in componentRecord.LigatureAnchor:
                ligatureAnchor.XCoordinate = scaleValue_toUPM(ligatureAnchor.XCoordinate, UPM, target_UPM)
                ligatureAnchor.YCoordinate = scaleValue_toUPM(ligatureAnchor.YCoordinate, UPM, target_UPM)
                
def scaleLookupType6(subTable, UPM, target_UPM): 
    for mark1Record in subTable.Mark1Array.MarkRecord:
        mark1Record.MarkAnchor.XCoordinate = scaleValue_toUPM(mark1Record.MarkAnchor.XCoordinate, UPM, target_UPM)
        mark1Record.MarkAnchor.YCoordinate = scaleValue_toUPM(mark1Record.MarkAnchor.YCoordinate, UPM, target_UPM)
    for mark2Record in subTable.Mark2Array.Mark2Record:
        for mark2Anchor in mark2Record.Mark2Anchor:
            mark2Anchor.XCoordinate = scaleValue_toUPM(mark2Anchor.XCoordinate, UPM, target_UPM)
            mark2Anchor.YCoordinate = scaleValue_toUPM(mark2Anchor.YCoordinate, UPM, target_UPM)

def scaleLookupType7(subTable, UPM, target_UPM):
    pass 
    
def scaleLookupType8(subTable, UPM, target_UPM):
    pass        

def scaleFont(tt, target_UPM):
    UPM = tt['head'].unitsPerEm
    glyphOrder = tt.getGlyphOrder()

    # Data related to UPM
    #################################
    # HEAD
    tt['head'].unitsPerEm = scaleValue_toUPM(tt['head'].unitsPerEm, UPM, target_UPM)
    tt['head'].xMin = scaleValue_toUPM(tt['head'].xMin, UPM, target_UPM)
    tt['head'].yMin = scaleValue_toUPM(tt['head'].yMin, UPM, target_UPM)
    tt['head'].xMax = scaleValue_toUPM(tt['head'].xMax, UPM, target_UPM)
    tt['head'].yMax = scaleValue_toUPM(tt['head'].yMax, UPM, target_UPM)
    #################################
    # HHEA
    tt['hhea'].ascent = scaleValue_toUPM(tt['hhea'].ascent, UPM, target_UPM)
    tt['hhea'].descent = scaleValue_toUPM(tt['hhea'].descent, UPM, target_UPM)
    tt['hhea'].lineGap = scaleValue_toUPM(tt['hhea'].lineGap, UPM, target_UPM)
    tt['hhea'].advanceWidthMax = scaleValue_toUPM(tt['hhea'].advanceWidthMax, UPM, target_UPM)
    tt['hhea'].minLeftSideBearing = scaleValue_toUPM(tt['hhea'].minLeftSideBearing, UPM, target_UPM)
    tt['hhea'].minRightSideBearing = scaleValue_toUPM(tt['hhea'].minRightSideBearing, UPM, target_UPM)
    tt['hhea'].xMaxExtent = scaleValue_toUPM(tt['hhea'].xMaxExtent, UPM, target_UPM)
    #################################
    # print tt['hhea'].numberOfHMetrics #Number of entries of the hmtx table
    # print len(glyphOrder)
    #################################
    # HMTX
    for g in glyphOrder:
        scaledWidth = scaleValue_toUPM(tt['hmtx'].metrics[g][0], UPM, target_UPM)
        scaledLsb = scaleValue_toUPM(tt['hmtx'].metrics[g][1], UPM, target_UPM)
        tt['hmtx'].metrics[g] = int(scaledWidth), int(scaledLsb)
    #################################
    # OS/2
    tt['OS/2'].xAvgCharWidth = scaleValue_toUPM(tt['OS/2'].xAvgCharWidth, UPM, target_UPM)
    tt['OS/2'].ySubscriptXSize = scaleValue_toUPM(tt['OS/2'].ySubscriptXSize, UPM, target_UPM)
    tt['OS/2'].ySubscriptYSize = scaleValue_toUPM(tt['OS/2'].ySubscriptYSize, UPM, target_UPM)
    tt['OS/2'].ySubscriptXOffset = scaleValue_toUPM(tt['OS/2'].ySubscriptXOffset, UPM, target_UPM)
    tt['OS/2'].ySubscriptYOffset = scaleValue_toUPM(tt['OS/2'].ySubscriptYOffset, UPM, target_UPM)
    tt['OS/2'].ySuperscriptXSize = scaleValue_toUPM(tt['OS/2'].ySuperscriptXSize, UPM, target_UPM)
    tt['OS/2'].ySuperscriptYSize = scaleValue_toUPM(tt['OS/2'].ySuperscriptYSize, UPM, target_UPM)
    tt['OS/2'].ySuperscriptXOffset = scaleValue_toUPM(tt['OS/2'].ySuperscriptXOffset, UPM, target_UPM)
    tt['OS/2'].ySuperscriptYOffset = scaleValue_toUPM(tt['OS/2'].ySuperscriptYOffset, UPM, target_UPM)
    tt['OS/2'].yStrikeoutSize = scaleValue_toUPM(tt['OS/2'].yStrikeoutSize, UPM, target_UPM)
    tt['OS/2'].yStrikeoutPosition = scaleValue_toUPM(tt['OS/2'].yStrikeoutPosition, UPM, target_UPM)
    tt['OS/2'].sTypoAscender = scaleValue_toUPM(tt['OS/2'].sTypoAscender, UPM, target_UPM)
    tt['OS/2'].sTypoDescender = scaleValue_toUPM(tt['OS/2'].sTypoDescender, UPM, target_UPM)
    tt['OS/2'].sTypoLineGap = scaleValue_toUPM(tt['OS/2'].sTypoLineGap, UPM, target_UPM)
    tt['OS/2'].usWinAscent = scaleValue_toUPM(tt['OS/2'].usWinAscent, UPM, target_UPM)
    tt['OS/2'].usWinDescent = scaleValue_toUPM(tt['OS/2'].usWinDescent, UPM, target_UPM)
    tt['OS/2'].sxHeight = scaleValue_toUPM(tt['OS/2'].sxHeight, UPM, target_UPM)
    tt['OS/2'].sCapHeight = scaleValue_toUPM(tt['OS/2'].sCapHeight, UPM, target_UPM)

    # glyf
    for g in glyphOrder:
        if tt['glyf'][g].isComposite():
            for component in tt['glyf'][g].components:
                component.x = scaleValue_toUPM(component.x, UPM, target_UPM)
                component.y = scaleValue_toUPM(component.y, UPM, target_UPM)

        if hasattr(tt['glyf'][g], 'xMin'):
            tt['glyf'][g].xMin = scaleValue_toUPM(tt['glyf'][g].xMin, UPM, target_UPM)
        if hasattr(tt['glyf'][g], 'yMin'):
            tt['glyf'][g].yMin = scaleValue_toUPM(tt['glyf'][g].yMin, UPM, target_UPM)
        if hasattr(tt['glyf'][g], 'xMax'):
            tt['glyf'][g].xMax = scaleValue_toUPM(tt['glyf'][g].xMax, UPM, target_UPM)
        if hasattr(tt['glyf'][g], 'yMax'):
            tt['glyf'][g].yMax = scaleValue_toUPM(tt['glyf'][g].yMax, UPM, target_UPM)
        for i, c in enumerate(tt['glyf'][g].getCoordinates(tt['glyf'])[0]):
            scaled_x = scaleValue_toUPM(c[0], UPM, target_UPM)
            scaled_y = scaleValue_toUPM(c[1], UPM, target_UPM)
            tt['glyf'][g].getCoordinates(tt['glyf'])[0][i] = (scaled_x, scaled_y)
    
    # kern
    if 'kern' in tt:
        for i, table in enumerate(tt['kern'].kernTables):
            for k in table.kernTable.keys():
                table[k] = scaleValue_toUPM(table[k], UPM, target_UPM)
  
    # GPOS
    if not 'GPOS' in tt: return
    unknownAttributes = []
    for i, lookup in enumerate(tt['GPOS'].table.LookupList.Lookup):
        for i, subTable in enumerate(lookup.SubTable):
            # Lookup Type 1, SinglePos
            if lookup.LookupType == 1:
                scaleLookupType1(subTable, UPM, target_UPM)
            # lookup type 2: PairPos
            if lookup.LookupType == 2:
                scaleLookupType2(subTable, UPM, target_UPM)
            # Lookup Type 3, CursivePos
            if lookup.LookupType == 3:
                scaleLookupType3(subTable, UPM, target_UPM)
            # Lookup Type 4, MarkBasePos
            if lookup.LookupType == 4:
                scaleLookupType4(subTable, UPM, target_UPM)
            # Lookup Type 5, markLigPos
            if lookup.LookupType == 5:
                scaleLookupType5(subTable, UPM, target_UPM)
            # Lookup Type 6, MarkMarkPos
            if lookup.LookupType == 6:
                scaleLookupType6(subTable, UPM, target_UPM)
            # Lookup Type 7, ContextPos
            if lookup.LookupType == 7:
                scaleLookupType7(subTable, UPM, target_UPM)
            # Lookup Type 8, ChainContextPos
            if lookup.LookupType == 8:
                scaleLookupType8(subTable, UPM, target_UPM)
            # Lookup Type 9, ExtensionPos
            if lookup.LookupType == 9:
                if subTable.ExtensionLookupType == 1:
                    scaleLookupType1(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 2:
                    scaleLookupType2(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 3:
                    scaleLookupType3(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 4:
                    scaleLookupType4(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 5:
                    scaleLookupType5(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 6:
                    scaleLookupType6(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 7:
                    scaleLookupType7(subTable.ExtSubTable, UPM, target_UPM)
                if subTable.ExtensionLookupType == 8:
                    scaleLookupType8(subTable.ExtSubTable, UPM, target_UPM)


def main():
    chk = argsCheck()
    if not chk: return

    inputPath = argv[1]
    targetUPM = int(argv[2])
    outputPath = argv[3]

    inputFont = ttLib.TTFont(inputPath)
    scaleFont(inputFont, targetUPM)
    inputFont.save(outputPath)

def argsCheck():
    return(argv)


if __name__ == '__main__':
    main()
