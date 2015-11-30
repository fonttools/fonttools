"""\
usage: pyftcount inputfile1 [... inputfileN]

    pyftcount %s -- Count bytecodes

    Reads inputfiles and says whether they contain bytecode or not.

    General options:
    -h Help: print this message
    -y <number> Select font number for TrueType Collection,
       starting from 0.

"""


from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, TTLibError
from fontTools.misc.macCreatorType import getMacCreatorAndType
import os
import sys
import getopt
import re

def usage():
    from fontTools import version
    print(__doc__ % version)
    sys.exit(2)

class Options(object):
    def __init__(self, rawOptions):
        self.fontNumber = -1
        for option, value in rawOptions:
            # general options
            if option == "-h":
                from fontTools import version
                print(__doc__ % version)
                sys.exit(0)
            elif option == "-y":
                self.fontNumber = int(value)


def yes_or_no(b):
    if b:
        return "yes"
    else:
        return "no"


def ttCount(input, options):
    ttf = TTFont(input, fontNumber=options.fontNumber, lazy=True)
    reader = ttf.reader
    hasPrep = 'prep' in reader.tables
    hasFpgm = 'fpgm' in reader.tables
    glyf_program_counts = 0
    glyf_names = ttf.getGlyphSet().keys()
    for glyf_name in glyf_names:
        glyf = ttf['glyf'].glyphs[glyf_name]
        glyf.expand(ttf['glyf'])
        if hasattr(ttf['glyf'].glyphs[glyf_name], "program"):
            prog = ttf['glyf'].glyphs[glyf_name].program
            if (hasattr(prog, "bytecode") and len(prog.bytecode) > 0) or (hasattr(prog, "assembly") and len(prog.assembly) > 0):
                glyf_program_counts += 1
        #print ("%s %s" % (glyf, hasattr(ttf['glyf'].glyphs[glyf_name], "program")))
    hasSomeGlyfCode = glyf_program_counts > 0
    globalAnswer = hasPrep or hasFpgm or hasSomeGlyfCode
    print ("%s: %s, prep = %s, fpgm = %s, glyf = %s [%d/%d]" %
           (input,
            yes_or_no(globalAnswer),
            yes_or_no(hasPrep),
            yes_or_no(hasFpgm),
            yes_or_no(hasSomeGlyfCode),
            glyf_program_counts,
            len(glyf_names)))
    ttf.close()


def ttDump(input, output, options):
    if not options.quiet:
        print('Dumping "%s" to "%s"...' % (input, output))
    ttf = TTFont(input, 0, verbose=options.verbose, allowVID=options.allowVID,
            quiet=options.quiet,
            ignoreDecompileErrors=options.ignoreDecompileErrors,
            fontNumber=options.fontNumber)
    ttf.saveXML(output,
            quiet=options.quiet,
            tables=options.onlyTables,
            skipTables=options.skipTables,
            splitTables=options.splitTables,
            disassembleInstructions=options.disassembleInstructions,
            bitmapGlyphDataFormat=options.bitmapGlyphDataFormat)
    ttf.close()


def guessFileType(fileName):
    base, ext = os.path.splitext(fileName)
    try:
        f = open(fileName, "rb")
    except IOError:
        return None
    cr, tp = getMacCreatorAndType(fileName)
    if tp in ("sfnt", "FFIL"):
        return "TTF"
    if ext == ".dfont":
        return "TTF"
    header = f.read(256)
    head = Tag(header[:4])
    if head == "OTTO":
        return "OTF"
    elif head == "ttcf":
        return "TTC"
    elif head in ("\0\1\0\0", "true"):
        return "TTF"
    elif head == "wOFF":
        return "WOFF"
    elif head.lower() == "<?xm":
        # Use 'latin1' because that can't fail.
        header = tostr(header, 'latin1')
        if opentypeheaderRE.search(header):
            return "OTX"
        else:
            return "TTX"
    return None


def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "vy:")
    except getopt.GetoptError:
        usage()

    if not files:
        usage()

    options = Options(rawOptions)
    jobs = []

    for input in files:
        tp = guessFileType(input)
        if tp in ("OTF", "TTF", "TTC", "WOFF"):
            extension = ".ttx"
        elif tp == "TTX":
            extension = ".ttf"
        elif tp == "OTX":
            extension = ".otf"
        else:
            print('Unknown file type: "%s"' % input)
            continue

        jobs.append(input)
    return jobs, options


def process(jobs, options):
    for input in jobs:
        ttCount(input, options)


def waitForKeyPress():
    """Force the DOS Prompt window to stay open so the user gets
    a chance to see what's wrong."""
    import msvcrt
    print('(Hit any key to exit)')
    while not msvcrt.kbhit():
        pass


def main(args):
    jobs, options = parseOptions(args)
    try:
        process(jobs, options)
    except KeyboardInterrupt:
        print("(Cancelled.)")
    except SystemExit:
        if sys.platform == "win32":
            waitForKeyPress()
        else:
            raise
    except TTLibError as e:
        print("Error:",e)
    except:
        if sys.platform == "win32":
            import traceback
            traceback.print_exc()
            waitForKeyPress()
        else:
            raise


if __name__ == "__main__":
    main(sys.argv[1:])
