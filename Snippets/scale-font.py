"""
Script to change UnitsPerEm of a Font
USAGE:
scale-font.py path/to/inputFont.ttf targetUPM path/to/outputFont.ttf

Only works on .ttf (no CFF) for now

TO DO: add support for scaling GPOS lookups type 7 and 8
"""

from fontTools import ttLib
import logging
from fontTools.misc.fixedTools import otRound

def scale_value_factor(value, scale_factor):
    return otRound(value * scale_factor)

def _scale_lookup_type1(subTable, scale_factor):
    attrs = ['XAdvance', 'YAdvance', 'XPlacement', 'YPlacement']

    for attr in attrs:
        if subTable.Format == 1 and hasattr(subTable, attr):
            setattr(subTable.Value, attr, scale_value_factor(getattr(subTable.Value, attr), scale_factor))
        elif subTable.Format == 2:
            for subSubTable in subTable.Value:
                if hasattr(subSubTable, attr):
                    setattr(subSubTable, attr, scale_value_factor(getattr(subSubTable, attr), scale_factor))

def _scale_lookup_type2(subTable, scale_factor):
    
    if subTable.Format == 1:
        attrs = ['XAdvance', 'YAdvance', 'XPlacement', 'YPlacement']
        pairs = [pair for pairSet in subTable.PairSet for pair in pairSet.PairValueRecord]

        for attr in attrs:
            for pair in pairs:
                if hasattr(pair.Value1, attr):
                    setattr(pair.Value1, attr, scale_value_factor(getattr(pair.Value1, attr), scale_factor))
                if hasattr(pair.Value2, attr):
                    setattr(pair.Value2, attr, scale_value_factor(getattr(pair.Value2, attr), scale_factor))

    elif subTable.Format == 2:
        attrs = ['XAdvance', 'XPlacement']
        class2Records = [class2Record for class1Record in subTable.Class1Record for class2Record in class1Record.Class2Record]

        for attr in attrs:
            for class2Record in class2Records:
                if hasattr(class2Record.Value1, attr):
                    setattr(class2Record.Value1, attr, scale_value_factor(getattr(class2Record.Value1, attr), scale_factor))
                if hasattr(class2Record.Value2, attr):
                    setattr(class2Record.Value2, attr, scale_value_factor(getattr(class2Record.Value2, attr), scale_factor))

def _scale_lookup_type3(subTable, scale_factor):
    attrs = ['XCoordinate', 'YCoordinate']

    for attr in attrs:
        for entryExitRecord in subTable.EntryExitRecord:
            if hasattr(entryExitRecord.EntryAnchor, attr):
                setattr(entryExitRecord.EntryAnchor, attr, scale_value_factor(getattr(entryExitRecord.EntryAnchor, attr), scale_factor))
            if hasattr(entryExitRecord.ExitAnchor, attr):
                setattr(entryExitRecord.ExitAnchor, attr, scale_value_factor(getattr(entryExitRecord.ExitAnchor, attr), scale_factor))

def _scale_lookup_type4(subTable, scale_factor):
    attrs = ['XCoordinate', 'YCoordinate']
    baseAnchors = [baseAnchor for attr in attrs for baseRecord in subTable.BaseArray.BaseRecord 
                    for baseAnchor in baseRecord.BaseAnchor if hasattr(baseAnchor, attr)]
    markRecords = [markRecord for attr in attrs for markRecord in subTable.MarkArray.MarkRecord 
                    if hasattr(markRecord, attr)]

    for attr in attrs:
        for baseAnchor in baseAnchors:
            setattr(baseAnchor, attr, scale_value_factor(getattr(baseAnchor, attr), scale_factor))
        for markRecord in markRecords:
            setattr(markRecord, attr, scale_value_factor(getattr(markRecord, attr), scale_factor))

def _scale_lookup_type5(subTable, scale_factor):
    attrs = ['XCoordinate', 'YCoordinate']
    markRecords = [markRecord for markRecord in subTable.MarkArray.MarkRecord]
    ligatureAnchors = [ligatureAnchor for ligatureAttach in subTable.LigatureArray.LigatureAttach 
                        for componentRecord in ligatureAttach.ComponentRecord 
                        for ligatureAnchor in componentRecord.LigatureAnchor if ligatureAnchor]

    for attr in attrs:
        for markRecord in markRecords:
            if hasattr(markRecord.MarkAnchor, attr):
                setattr(markRecord.MarkAnchor, attr, scale_value_factor(getattr(markRecord.MarkAnchor, attr), scale_factor))
        for ligatureAnchor in ligatureAnchors:
            if hasattr(ligatureAnchor, attr):
                setattr(ligatureAnchor, attr, scale_value_factor(getattr(ligatureAnchor, attr), scale_factor))
                
def _scale_lookup_type6(subTable, scale_factor):
    attrs = ['XCoordinate', 'YCoordinate']
    mark2Anchors = [mark2Anchor for mark2Record in subTable.Mark2Array.Mark2Record for mark2Anchor in mark2Record.Mark2Anchor]

    for attr in attrs:
        for mark1Record in subTable.Mark1Array.MarkRecord:
            if hasattr(mark1Record.MarkAnchor, attr):
                setattr(mark1Record.MarkAnchor, attr, scale_value_factor(getattr(mark1Record.MarkAnchor, attr), scale_factor))    
        for mark2Anchor in mark2Anchors:
            if hasattr(mark2Anchor, attr):
                setattr(mark2Anchor, attr, scale_value_factor(getattr(mark1Record.MarkAnchor, attr), scale_factor))

def _scale_lookup_type7(subTable, scale_factor):
    # TO DO
    pass 
    
def _scale_lookup_type8(subTable, scale_factor):
    # TO DO
    pass        


def scale_font(font, scale_factor):
    glyphOrder = font.getGlyphOrder()
    
    logging.info("scaling {} and {}".format('htmx', 'glyf'))
    for g in glyphOrder:      

        scaled_width = scale_value_factor(font['hmtx'].metrics[g][0], scale_factor)
        scaled_lsb = scale_value_factor(font['hmtx'].metrics[g][1], scale_factor)
        font['hmtx'].metrics[g] = (scaled_width, scaled_lsb)

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

    table2attrs = { 'head': ['unitsPerEm', 'xMin', 'yMin', 'xMax', 'yMax'],
                    'hhea': ['ascent', 'descent', 'lineGap', 'advanceWidthMax', 
                            'minLeftSideBearing', 'minRightSideBearing', 'xMaxExtent'],
                    'OS/2': ['xAvgCharWidth', 'ySubscriptXSize', 'ySubscriptYSize', 'ySubscriptXOffset',
                            'ySubscriptYOffset', 'ySuperscriptXSize', 'ySuperscriptYSize',
                            'ySuperscriptXOffset', 'ySuperscriptYOffset', 'yStrikeoutSize', 
                            'yStrikeoutSize', 'yStrikeoutPosition', 'sTypoAscender', 'sTypoDescender',
                            'sTypoLineGap', 'usWinAscent', 'usWinDescent', 'sxHeight', 'sCapHeight']
                  }

    for table, attrs in table2attrs.items():
        for attr in attrs:
            try:
                logging.info("scaling {}: {}".format(table, attr))
                setattr(font[table], attr, scale_value_factor(getattr(font[table], attr), scale_factor))
            except:
                logging.info("FAILED scaling {}: {}".format(table, attr))

    if 'kern' in font:
        logging.info("scaling {}".format('kern'))
        for i, table in enumerate(font['kern'].kernTables):
            for k in table.kernTable.keys():
                table[k] = scale_value_factor(table[k], scale_factor)
  
    if 'GPOS' in font:
        scale_func = [ _scale_lookup_type1, _scale_lookup_type2, _scale_lookup_type3, 
                       _scale_lookup_type4, _scale_lookup_type5, _scale_lookup_type6,
                       _scale_lookup_type7, _scale_lookup_type8 
                     ]

        for lookup in font['GPOS'].table.LookupList.Lookup:
            for subTable in lookup.SubTable:
                logging.info("scaling {}: lookup type {}".format('GPOS', lookup.LookupType ))
                if lookup.LookupType == 9:
                    logging.info("scaling {}:\t\t lookup type {}".format('GPOS', subTable.ExtensionLookupType))
                    scale_func[subTable.ExtensionLookupType - 1](subTable.ExtSubTable, scale_factor)
                else:
                    scale_func[lookup.LookupType - 1](subTable, scale_factor)


def main(args=None):
    import argparse
    parser = argparse.ArgumentParser("scale-font")

    parser.add_argument(
    "--output", metavar="OUTPUT_FONT", help="If omitted, save Font in place"
        )

    parser.add_argument(
    "input_font", metavar="INPUT_FONT", help="Path to input Font to be scaled"
        )

    parser.add_argument(
    "upem", metavar="UPEM", type=int, help="Units Per EM of the scaled Font"
        )

    options = parser.parse_args(args)

    logging.basicConfig(level="INFO")

    font = ttLib.TTFont(options.input_font, lazy=False)
    scale_factor = options.upem / font['head'].unitsPerEm

    logging.info("scale factor: %s", scale_factor)

    scale_font(font, scale_factor)

    if options.output:
        font.save(options.output)
    else:
        font.save(options.input_font)

if __name__ == '__main__':
    main()
