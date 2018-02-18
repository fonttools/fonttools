#!/usr/bin/env python2.7

"""Update the 'name' table in the extra Roboto weights to be
more compatible with Windows' font chooser."""
__author__="codeman38"

import argparse
import glob
import os
from fontTools import ttLib

def main():
    parser = argparse.ArgumentParser(
        description="Update the 'name' table in the extra Roboto weights "
                    "to be more compatible with Windows' font chooser.")
    parser.add_argument('filename', nargs='+',
                        help='file name(s) of fonts to convert')
    args = parser.parse_args()
    for filespec in args.filename:
        for fname in glob.glob(filespec):
            process_font(fname)

def process_font(fname):
    outname = fname+'.tmp'
    bakname = fname+'.bak'

    ttf = ttLib.TTFont(fname)
    nametbl = ttf['name']
    prefFamRec = nametbl.getName(16, 3, 1, 1033)
    if prefFamRec is None:
        print("Ignoring {} because no preferred name field.".format(
            fname))
        return

    winFamRec = nametbl.getName(1, 3, 1, 1033)
    winSubRec = nametbl.getName(2, 3, 1, 1033)
    famName = winFamRec.string.decode('utf-16-be')
    subName = winSubRec.string.decode('utf-16-be')

    subSplit = subName.split()
    newFamName = famName + u' ' + subSplit[0]
    if subSplit[-1] == u'Italic':
        newSubName = u'Italic'
    else:
        newSubName = u'Regular'

    print(u'{}|{} -> {}|{}'.format(famName, subName,
                                   newFamName, newSubName))

    winFamRec.string = newFamName.encode('utf-16-be')
    winSubRec.string = newSubName.encode('utf-16-be')

    ttf.save(outname)
    ttf.close()
    os.rename(fname, bakname)
    os.rename(outname, fname)

if __name__=='__main__':
    main()