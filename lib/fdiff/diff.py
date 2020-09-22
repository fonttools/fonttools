#!/usr/bin/env python3

import asyncio
import os
import shlex
import subprocess
import tempfile
from difflib import unified_diff
from multiprocessing import Pool, cpu_count
from typing import Any, Iterable, Iterator, List, Optional, Text, Tuple

from fontTools.ttLib import TTFont  # type: ignore

from .exceptions import AIOError
from .remote import (_get_filepath_from_url,
                     create_async_get_request_session_and_run)
from .utils import get_file_modtime

#
#
#  Private functions
#
#


def _async_fetch_files(dirpath: Text, urls: List[Text]) -> None:
    loop = asyncio.get_event_loop()
    tasks = loop.run_until_complete(
        create_async_get_request_session_and_run(urls, dirpath)
    )
    for task in tasks:
        if task.exception():
            # raise exception here to notify calling code that something
            # did not work
            raise AIOError(f"{task.exception()}")
        elif task.result().http_status != 200:
            # handle non-200 HTTP response status codes + file write fails
            raise AIOError(
                f"failed to pull '{task.result().url}' with HTTP status "
                f"code {task.result().http_status}"
            )


def _get_fonts_and_save_xml(
    filepath_a: Text,
    filepath_b: Text,
    tmpdirpath: Text,
    include_tables: Optional[List[Text]],
    exclude_tables: Optional[List[Text]],
    use_multiprocess: bool,
) -> Tuple[Text, Text, Text, Text, Text, Text]:
    post_pathname, postpath, pre_pathname, prepath = _get_pre_post_paths(
        filepath_a, filepath_b, tmpdirpath
    )
    # instantiate left and right fontTools.ttLib.TTFont objects
    tt_left = TTFont(prepath)
    tt_right = TTFont(postpath)
    _validate_table_includes(include_tables, tt_left, tt_right)
    _validate_table_excludes(exclude_tables, tt_left, tt_right)
    left_ttxpath = os.path.join(tmpdirpath, "left.ttx")
    right_ttxpath = os.path.join(tmpdirpath, "right.ttx")
    _mp_save_ttx_xml(
        tt_left,
        tt_right,
        left_ttxpath,
        right_ttxpath,
        exclude_tables,
        include_tables,
        use_multiprocess,
    )
    return left_ttxpath, right_ttxpath, pre_pathname, prepath, post_pathname, postpath


def _get_pre_post_paths(
    filepath_a: Text,
    filepath_b: Text,
    dirpath: Text,
) -> Tuple[Text, Text, Text, Text]:
    urls: List[Text] = []
    if filepath_a.startswith("http"):
        urls.append(filepath_a)
        prepath = _get_filepath_from_url(filepath_a, dirpath)
        # keep URL as path name for remote file requests
        pre_pathname = filepath_a
    else:
        prepath = filepath_a
        pre_pathname = filepath_a
    if filepath_b.startswith("http"):
        urls.append(filepath_b)
        postpath = _get_filepath_from_url(filepath_b, dirpath)
        # keep URL as path name for remote file requests
        post_pathname = filepath_b
    else:
        postpath = filepath_b
        post_pathname = filepath_b
    # Async IO fetch and write of any remote file requests
    if len(urls) > 0:
        _async_fetch_files(dirpath, urls)
    return post_pathname, postpath, pre_pathname, prepath


def _mp_save_ttx_xml(
    tt_left: Any,
    tt_right: Any,
    left_ttxpath: Text,
    right_ttxpath: Text,
    exclude_tables: Optional[List[Text]],
    include_tables: Optional[List[Text]],
    use_multiprocess: bool,
) -> None:
    if use_multiprocess and cpu_count() > 1:
        # Use parallel fontTools.ttLib.TTFont.saveXML dump
        # by default on multi CPU systems.  This is a performance
        # optimization. Profiling demonstrates that this can reduce
        # execution time by up to 30% for some fonts
        mp_args_list = [
            (tt_left, left_ttxpath, include_tables, exclude_tables),
            (tt_right, right_ttxpath, include_tables, exclude_tables),
        ]
        with Pool(processes=2) as pool:
            pool.starmap(_ttfont_save_xml, mp_args_list)
    else:
        # use sequential fontTools.ttLib.TTFont.saveXML dumps
        # when use_multiprocess is False or single CPU system
        # detected
        _ttfont_save_xml(tt_left, left_ttxpath, include_tables, exclude_tables)
        _ttfont_save_xml(tt_right, right_ttxpath, include_tables, exclude_tables)


def _ttfont_save_xml(
    ttf: Any,
    filepath: Text,
    include_tables: Optional[List[Text]],
    exclude_tables: Optional[List[Text]],
) -> bool:
    """Writes TTX specification formatted XML to disk on filepath."""
    ttf.saveXML(filepath, tables=include_tables, skipTables=exclude_tables)
    return True


def _validate_table_excludes(
    exclude_tables: Optional[List[Text]], tt_left: Any, tt_right: Any
) -> None:
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


def _validate_table_includes(
    include_tables: Optional[List[Text]], tt_left: Any, tt_right: Any
) -> None:
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


#
#
#  Public functions
#
#


def u_diff(
    filepath_a: Text,
    filepath_b: Text,
    context_lines: int = 3,
    include_tables: Optional[List[Text]] = None,
    exclude_tables: Optional[List[Text]] = None,
    use_multiprocess: bool = True,
) -> Iterator[Text]:
    """Performs a unified diff on a TTX serialized data format dump of font binary data using
    a modified version of the Python standard libary difflib module.

    filepath_a: (string) pre-file local file path or URL path
    filepath_b: (string) post-file local file path or URL path
    context_lines: (int) number of context lines to include in the diff (default=3)
    include_tables: (list of str) Python list of OpenType tables to include in the diff
    exclude_tables: (list of str) Python list of OpentType tables to exclude from the diff
    use_multiprocess: (bool) use multi-processor optimizations (default=True)

    include_tables and exclude_tables are mutually exclusive arguments.  Only one should
    be defined

    :returns: Generator of ordered diff line strings that include newline line endings
    :raises: KeyError if include_tables or exclude_tables includes a mis-specified table
    that is not included in filepath_a OR filepath_b
    :raises: fdiff.exceptions.AIOError if exception raised during execution of async I/O
             GET request for URL or file write
    :raises: fdiff.exceptions.AIOError if GET request to URL returned non-200 response
    status code"""
    with tempfile.TemporaryDirectory() as tmpdirpath:
        # define the file paths with either local file requests
        # or HTTP GET requests of remote files based on the command line request
        (
            left_ttxpath,
            right_ttxpath,
            pre_pathname,
            prepath,
            post_pathname,
            postpath,
        ) = _get_fonts_and_save_xml(
            filepath_a,
            filepath_b,
            tmpdirpath,
            include_tables,
            exclude_tables,
            use_multiprocess,
        )

        with open(left_ttxpath) as ff:
            fromlines = ff.readlines()
        with open(right_ttxpath) as tf:
            tolines = tf.readlines()

        fromdate = get_file_modtime(prepath)
        todate = get_file_modtime(postpath)

        return unified_diff(
            fromlines,
            tolines,
            pre_pathname,
            post_pathname,
            fromdate,
            todate,
            n=context_lines,
        )


def external_diff(
    command: Text,
    filepath_a: Text,
    filepath_b: Text,
    include_tables: Optional[List[Text]] = None,
    exclude_tables: Optional[List[Text]] = None,
    use_multiprocess: bool = True,
) -> Iterable[Tuple[Text, Optional[int]]]:
    """Performs a unified diff on a TTX serialized data format dump of font binary data using
    an external diff executable that is requested by the caller via `command`

    command: (string) command line executable string and arguments to define execution
    filepath_a: (string) pre-file local file path or URL path
    filepath_b: (string) post-file local file path or URL path
    include_tables: (list of str) Python list of OpenType tables to include in the diff
    exclude_tables: (list of str) Python list of OpentType tables to exclude from the diff
    use_multiprocess: (bool) use multi-processor optimizations (default=True)

    include_tables and exclude_tables are mutually exclusive arguments.  Only one should
    be defined

    :returns: Generator of ordered diff line strings that include newline line endings
    :raises: KeyError if include_tables or exclude_tables includes a mis-specified table
    that is not included in filepath_a OR filepath_b
    :raises: IOError if exception raised during execution of `command` on TTX files
    :raises: fdiff.exceptions.AIOError if GET request to URL returned non-200 response
    status code"""
    with tempfile.TemporaryDirectory() as tmpdirpath:
        # define the file paths with either local file requests
        # or HTTP GET requests of remote files based on the command line request
        (
            left_ttxpath,
            right_ttxpath,
            pre_pathname,
            prepath,
            post_pathname,
            postpath,
        ) = _get_fonts_and_save_xml(
            filepath_a,
            filepath_b,
            tmpdirpath,
            include_tables,
            exclude_tables,
            use_multiprocess,
        )

        full_command = f"{command.strip()} {left_ttxpath} {right_ttxpath}"

        process = subprocess.Popen(
            shlex.split(full_command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf8",
        )

        while True:
            output = process.stdout.readline()  # type: ignore
            exit_status = process.poll()
            if len(output) == 0 and exit_status is not None:
                err = process.stderr.read()  # type: ignore
                if err:
                    raise IOError(err)
                yield output, exit_status
                break
            else:
                yield output, None
