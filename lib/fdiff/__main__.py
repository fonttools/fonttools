#!/usr/bin/env python3

import os
import sys
import argparse

from fdiff import __version__
from fdiff.color import color_unified_diff_line
from fdiff.diff import external_diff, u_diff
from fdiff.textiter import head, tail
from fdiff.utils import file_exists, get_tables_argument_list


def main():  # pragma: no cover
    # try/except block rationale:
    # handles "premature" socket closure exception that is
    # raised by Python when stdout is piped to tools like
    # the `head` executable and socket is closed early
    # see: https://docs.python.org/3/library/signal.html#note-on-sigpipe
    try:
        run(sys.argv[1:])
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)


def run(argv):
    # ------------------------------------------
    # argparse command line argument definitions
    # ------------------------------------------
    parser = argparse.ArgumentParser(
        description="An OpenType table diff tool for fonts."
    )
    parser.add_argument("--version", action="version", version=f"fdiff v{__version__}")
    parser.add_argument(
        "-c",
        "--color",
        action="store_true",
        default=False,
        help="ANSI escape code colored diff",
    )
    parser.add_argument(
        "-l", "--lines", type=int, default=3, help="Number of context lines (default 3)"
    )
    parser.add_argument(
        "--include",
        type=str,
        default=None,
        help="Comma separated list of tables to include",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Comma separated list of tables to exclude",
    )
    parser.add_argument("--head", type=int, help="Display first n lines of output")
    parser.add_argument("--tail", type=int, help="Display last n lines of output")
    parser.add_argument(
        "--nomp", action="store_true", help="Do not use multi process optimizations"
    )
    parser.add_argument("--external", type=str, help="Run external diff tool command")
    parser.add_argument("PREFILE", help="Font file path/URL 1")
    parser.add_argument("POSTFILE", help="Font file path/URL 2")

    args = parser.parse_args(argv)

    # /////////////////////////////////////////////////////////
    #
    #  Validations
    #
    # /////////////////////////////////////////////////////////

    # ----------------------------------
    #  Incompatible argument validations
    # ----------------------------------
    #   --include and --exclude are mutually exclusive options
    if args.include and args.exclude:
        sys.stderr.write(
            f"[*] Error: --include and --exclude are mutually exclusive options. "
            f"Please use ONLY one of these options in your command.{os.linesep}"
        )
        sys.exit(1)

    # -------------------------------
    #  File path argument validations
    # -------------------------------

    if not args.PREFILE.startswith("http") and not file_exists(args.PREFILE):
        sys.stderr.write(
            f"[*] ERROR: The file path '{args.PREFILE}' can not be found.{os.linesep}"
        )
        sys.exit(1)
    if not args.PREFILE.startswith("http") and not file_exists(args.POSTFILE):
        sys.stderr.write(
            f"[*] ERROR: The file path '{args.POSTFILE}' can not be found.{os.linesep}"
        )
        sys.exit(1)

    # /////////////////////////////////////////////////////////
    #
    #  Command line logic
    #
    # /////////////////////////////////////////////////////////

    # parse explicitly included or excluded tables in
    # the command line arguments
    # set as a Python list if it was defined on the command line
    # or as None if it was not set on the command line
    include_list = get_tables_argument_list(args.include)
    exclude_list = get_tables_argument_list(args.exclude)

    # flip logic of the command line flag for multi process
    # optimization use
    use_mp = not args.nomp

    if args.external:
        # ------------------------------
        #  External executable tool diff
        # ------------------------------
        # head and tail are not supported when external diff tool is called
        if args.head or args.tail:
            sys.stderr.write(
                f"[ERROR] The head and tail options are not supported with external diff executable calls.{os.linesep}"
            )
            sys.exit(1)

        # lines of context filter is not supported when external diff tool is called
        if args.lines != 3:
            sys.stderr.write(
                f"[ERROR] The lines option is not supported with external diff executable calls.{os.linesep}"
            )
            sys.exit(1)

        try:
            diff = external_diff(
                args.external,
                args.PREFILE,
                args.POSTFILE,
                include_tables=include_list,
                exclude_tables=exclude_list,
                use_multiprocess=use_mp,
            )

            # write stdout from external tool
            for line, exit_code in diff:
                # format with color if color flag is entered on command line
                if args.color:
                    sys.stdout.write(color_unified_diff_line(line))
                else:
                    sys.stdout.write(line)
                if exit_code is not None:
                    sys.exit(exit_code)
        except Exception as e:
            sys.stderr.write(f"[*] ERROR: {e}{os.linesep}")
            sys.exit(1)
    else:
        # ---------------
        #  Unified diff
        # ---------------
        # perform the unified diff analysis
        try:
            diff = u_diff(
                args.PREFILE,
                args.POSTFILE,
                context_lines=args.lines,
                include_tables=include_list,
                exclude_tables=exclude_list,
                use_multiprocess=use_mp,
            )
        except Exception as e:
            sys.stderr.write(f"[*] ERROR: {e}{os.linesep}")
            sys.exit(1)

        # re-define the line contents of the diff iterable
        # if head or tail is requested
        if args.head:
            iterable = head(diff, args.head)
        elif args.tail:
            iterable = tail(diff, args.tail)
        else:
            iterable = diff

        # print unified diff results to standard output stream
        has_diff = False
        if args.color:
            for line in iterable:
                has_diff = True
                sys.stdout.write(color_unified_diff_line(line))
        else:
            for line in iterable:
                has_diff = True
                sys.stdout.write(line)

        # if no difference was found, tell the user instead of
        # simply closing with zero exit status code.
        if not has_diff:
            print("[*] There is no difference between the files.")
