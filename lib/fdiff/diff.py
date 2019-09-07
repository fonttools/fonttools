import os
import tempfile

from fontTools.ttLib import TTFont

from fdiff.utils import get_file_modtime
from fdiff.thirdparty.fdifflib import unified_diff


def u_diff(
    filepath_a, filepath_b, context_lines=3, include_tables=None, exclude_tables=None
):
    """Performs a unified diff on a TTX serialized data format dump of font binary data using
    a modified version of the Python standard libary difflib module.

    filepath_a: (string) pre-file path
    filepath_b: (string) post-file path
    context_lines: (int) number of context lines to include in the diff (default=3)
    include_tables: (list of str) Python list of OpenType tables to include in the diff
    exclude_tables: (list of str) Python list of OpentType tables to exclude from the diff

    include_tables and exclude_tables are mutually exclusive arguments.  Only one should
    be defined

    :returns: Generator of ordered diff line strings that include newline line endings
    :raises: KeyError if include_tables or exclude_tables includes a mis-specified table
    that is not included in filepath_a OR filepath_b"""
    tt_left = TTFont(filepath_a)
    tt_right = TTFont(filepath_b)

    # Validation: include_tables request should be for tables that are in one of
    # the two fonts. This otherwise silently passes with exit status code 0 which
    # could lead to the interpretation of no diff between two files when the table
    # entry is incorrectly defined or is a typo.  Let's be conservative and consider
    # this an error, force user to use explicit definitions that include tables in
    # one of the two files, and understand that the diff request was for one or more
    # tables that are not present.
    if include_tables is not None:
        for table in include_tables:
            if table not in tt_left and table not in tt_right:
                raise KeyError(
                    f"'{table}' table was not identified for inclusion in either font"
                )

    # Validation: exclude_tables request should be for tables that are in one of
    # the two fonts.  Mis-specified OT table definitions could otherwise result
    # in the presence of a table in the diff when the request was to exclude it.
    # For example, when an "OS/2" table request is entered as "OS2".
    if exclude_tables is not None:
        for table in exclude_tables:
            if table not in tt_left and table not in tt_right:
                raise KeyError(
                    f"'{table}' table was not identified for exclusion in either font"
                )

    fromdate = get_file_modtime(filepath_a)
    todate = get_file_modtime(filepath_b)

    with tempfile.TemporaryDirectory() as tmpdirname:
        tt_left.saveXML(
            os.path.join(tmpdirname, "left.ttx"),
            tables=include_tables,
            skipTables=exclude_tables,
        )
        tt_right.saveXML(
            os.path.join(tmpdirname, "right.ttx"),
            tables=include_tables,
            skipTables=exclude_tables,
        )

        with open(os.path.join(tmpdirname, "left.ttx")) as ff:
            fromlines = ff.readlines()
        with open(os.path.join(tmpdirname, "right.ttx")) as tf:
            tolines = tf.readlines()

        return unified_diff(
            fromlines,
            tolines,
            filepath_a,
            filepath_b,
            fromdate,
            todate,
            n=context_lines,
        )
