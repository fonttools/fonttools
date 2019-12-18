#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from fontTools.ttLib import TTFont


def ProcessTable(table):
    found = set()

    for rec in table.ScriptList.ScriptRecord:
        if rec.ScriptTag == "DFLT" and rec.Script.LangSysCount != 0:
            tags = [r.LangSysTag for r in rec.Script.LangSysRecord]
            logging.info("Removing %d extraneous LangSys records: %s",
                         rec.Script.LangSysCount, " ".join(tags))
            rec.Script.LangSysRecord = []
            rec.Script.LangSysCount = 0
            found.update(tags)

    if not found:
        logging.info("All fine")
        return False
    else:
        for rec in table.ScriptList.ScriptRecord:
            tags = set([r.LangSysTag for r in rec.Script.LangSysRecord])
            found -= tags

        if found:
            logging.warning("Records are missing from non-DFLT scripts: %s",
                            " ".join(found))
        return True


def ProcessFont(font):
    found = False
    for tag in ("GSUB", "GPOS"):
        if tag in font:
            logging.info("Processing %s table", tag)
            if ProcessTable(font[tag].table):
                found = True
            else:
                # Unmark the table as loaded so that it is read from disk when
                # writing the font, to avoid any unnecessary changes caused by
                # decompiling then recompiling again.
                del font.tables[tag]

    return found


def ProcessFiles(filenames):
    for filename in filenames:
        logging.info("Processing %s", filename)
        font = TTFont(filename)
        name, ext = os.path.splitext(filename)
        fixedname = name + ".fixed" + ext
        if ProcessFont(font):
            logging.info("Saving fixed font to %s\n", fixedname)
            font.save(fixedname)
        else:
            logging.info("Font file is fine, nothing to fix\n")


def main():
    parser = argparse.ArgumentParser(
            description="Fix LangSys records for DFLT script")
    parser.add_argument("files", metavar="FILE", type=str, nargs="+",
                        help="input font to process")
    parser.add_argument("-s", "--silent", action='store_true',
                        help="suppress normal messages")

    args = parser.parse_args()

    logformat = "%(levelname)s: %(message)s"
    if args.silent:
        logging.basicConfig(format=logformat, level=logging.DEBUG)
    else:
        logging.basicConfig(format=logformat, level=logging.INFO)

    ProcessFiles(args.files)

if __name__ == "__main__":
    sys.exit(main())
