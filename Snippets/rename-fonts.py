#!/usr/bin/env python3
"""Script to add a suffix to all family names in the input font's `name` table,
and to optionally rename the output files with the given suffix.

The current family name substring is searched in the nameIDs 1, 3, 4, 6, 16,
and 21, and if found the suffix is inserted after it; or else the suffix is
appended at the end.
"""
import os
import argparse
import logging
from fontTools.ttLib import TTFont
from fontTools.misc.cliTools import makeOutputFileName


logger = logging.getLogger()

WINDOWS_ENGLISH_IDS = 3, 1, 0x409
MAC_ROMAN_IDS = 1, 0, 0

FAMILY_RELATED_IDS = dict(
    LEGACY_FAMILY=1,
    TRUETYPE_UNIQUE_ID=3,
    FULL_NAME=4,
    POSTSCRIPT_NAME=6,
    PREFERRED_FAMILY=16,
    WWS_FAMILY=21,
)


def get_current_family_name(table):
    family_name_rec = None
    for plat_id, enc_id, lang_id in (WINDOWS_ENGLISH_IDS, MAC_ROMAN_IDS):
        for name_id in (
            FAMILY_RELATED_IDS["PREFERRED_FAMILY"],
            FAMILY_RELATED_IDS["LEGACY_FAMILY"],
        ):
            family_name_rec = table.getName(
                nameID=name_id,
                platformID=plat_id,
                platEncID=enc_id,
                langID=lang_id,
            )
            if family_name_rec is not None:
                break
        if family_name_rec is not None:
            break
    if not family_name_rec:
        raise ValueError("family name not found; can't add suffix")
    return family_name_rec.toUnicode()


def insert_suffix(string, family_name, suffix):
    # check whether family_name is a substring
    start = string.find(family_name)
    if start != -1:
        # insert suffix after the family_name substring
        end = start + len(family_name)
        new_string = string[:end] + suffix + string[end:]
    else:
        # it's not, we just append the suffix at the end
        new_string = string + suffix
    return new_string


def rename_record(name_record, family_name, suffix):
    string = name_record.toUnicode()
    new_string = insert_suffix(string, family_name, suffix)
    name_record.string = new_string
    return string, new_string


def rename_file(filename, family_name, suffix):
    filename, ext = os.path.splitext(filename)
    ps_name = family_name.replace(" ", "")
    if ps_name in filename:
        ps_suffix = suffix.replace(" ", "")
        return insert_suffix(filename, ps_name, ps_suffix) + ext
    else:
        return insert_suffix(filename, family_name, suffix) + ext


def add_family_suffix(font, suffix):
    table = font["name"]

    family_name = get_current_family_name(table)
    logger.info("  Current family name: '%s'", family_name)

    # postcript name can't contain spaces
    ps_family_name = family_name.replace(" ", "")
    ps_suffix = suffix.replace(" ", "")
    for rec in table.names:
        name_id = rec.nameID
        if name_id not in FAMILY_RELATED_IDS.values():
            continue
        if name_id == FAMILY_RELATED_IDS["POSTSCRIPT_NAME"]:
            old, new = rename_record(rec, ps_family_name, ps_suffix)
        elif name_id == FAMILY_RELATED_IDS["TRUETYPE_UNIQUE_ID"]:
            # The Truetype Unique ID rec may contain either the PostScript
            # Name or the Full Name string, so we try both
            if ps_family_name in rec.toUnicode():
                old, new = rename_record(rec, ps_family_name, ps_suffix)
            else:
                old, new = rename_record(rec, family_name, suffix)
        else:
            old, new = rename_record(rec, family_name, suffix)
        logger.info("    %r: '%s' -> '%s'", rec, old, new)

    return family_name


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-s", "--suffix", required=True)
    parser.add_argument("input_fonts", metavar="FONTFILE", nargs="+")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-i", "--inplace", action="store_true")
    output_group.add_argument("-d", "--output-dir")
    output_group.add_argument("-o", "--output-file")
    parser.add_argument("-R", "--rename-files", action="store_true")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    options = parser.parse_args(args)

    if not options.verbose:
        level = "WARNING"
    elif options.verbose == 1:
        level = "INFO"
    else:
        level = "DEBUG"
    logging.basicConfig(level=level, format="%(message)s")

    if options.output_file and len(options.input_fonts) > 1:
        parser.error(
            "argument -o/--output-file can't be used with multiple inputs"
        )
    if options.rename_files and (options.inplace or options.output_file):
        parser.error("argument -R not allowed with arguments -i or -o")

    for input_name in options.input_fonts:
        logger.info("Renaming font: '%s'", input_name)

        font = TTFont(input_name)
        family_name = add_family_suffix(font, options.suffix)

        if options.inplace:
            output_name = input_name
        elif options.output_file:
            output_name = options.output_file
        else:
            if options.rename_files:
                input_name = rename_file(
                    input_name, family_name, options.suffix
                )
            output_name = makeOutputFileName(input_name, options.output_dir)

        font.save(output_name)
        logger.info("Saved font: '%s'", output_name)

        font.close()
        del font

    logger.info("Done!")


if __name__ == "__main__":
    main()
