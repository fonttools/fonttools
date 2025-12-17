import argparse
import os
import sys
import shutil
import subprocess
from typing import Iterable, Iterator, List, Optional, Text, Tuple

from .color import color_unified_diff_line
from .diff import run_external_diff, u_diff
from .utils import file_exists, get_tables_argument_list


def pipe_output(output: str) -> None:
    """Pipes output to a pager if stdout is a TTY and a pager is available."""

    if not output:
        return

    if not sys.stdout.isatty():
        sys.stdout.write(output)
        return

    pager = os.getenv("PAGER") or shutil.which("less")

    if not pager:
        sys.stdout.write(output)
        return

    pager_cmd = [pager]
    if "less" in os.path.basename(pager):
        pager_cmd.append("-R")

    proc = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE, text=True)
    try:
        proc.stdin.write(output)
        proc.stdin.close()
        proc.wait()
    except (BrokenPipeError, KeyboardInterrupt):
        # Pager process was terminated before all output was written.
        # This is not an error. The main exception handler will deal with it.
        if proc.stdin:
            proc.stdin.close()
        # The process might still be running, but we have closed our side of the
        # pipe. The Popen destructor will send a SIGKILL to the child.
    except Exception:
        if proc.stdin:
            proc.stdin.close()
        raise


def main():
    """Compare two fonts for differences"""
    # try/except block rationale:
    # handles "premature" socket closure exception that is
    # raised by Python when stdout is piped to tools like
    # the `head` executable and socket is closed early
    # see: https://docs.python.org/3/library/signal.html#note-on-sigpipe
    ret = 0
    try:
        ret = run(sys.argv[1:])
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    return ret


def run(argv: List[Text]):
    # ------------------------------------------
    # argparse command line argument definitions
    # ------------------------------------------
    parser = argparse.ArgumentParser(
        description="An OpenType table diff tool for fonts."
    )
    parser.add_argument(
        "-l",
        "--lines",
        type=int,
        default=3,
        help="Number of context lines (default: 3)",
    )
    parser.add_argument(
        "-t",
        "--include",
        type=str,
        nargs="*",
        default=None,
        help="Font tables to include. Multiple options are allowed.",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        type=str,
        nargs="*",
        default=None,
        help="Font tables to exclude. Multiple options are allowed.",
    )
    parser.add_argument(
        "--diff", type=str, help="Run external diff tool command (default: diff)"
    )
    parser.add_argument(
        "--diff-arg",
        type=str,
        default=None,
        help="External diff tool arguments (default: -u)",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "never", "always"],
        default="auto",
        help="Whether to colorize output (default: auto)",
    )
    parser.add_argument("FILE1", help="Font file path/URL 1")
    parser.add_argument("FILE2", help="Font file path/URL 2")

    args: argparse.Namespace = parser.parse_args(argv)

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
        return 2

    # -------------------------------
    #  File path argument validations
    # -------------------------------

    if not args.FILE1.startswith("http") and not file_exists(args.FILE1):
        sys.stderr.write(
            f"[*] ERROR: The file path '{args.FILE1}' can not be found.{os.linesep}"
        )
        return 2
    if not args.FILE2.startswith("http") and not file_exists(args.FILE2):
        sys.stderr.write(
            f"[*] ERROR: The file path '{args.FILE2}' can not be found.{os.linesep}"
        )
        return 2

    # /////////////////////////////////////////////////////////
    #
    #  Command line logic
    #
    # /////////////////////////////////////////////////////////

    # parse explicitly included or excluded tables in
    # the command line arguments
    # set as a Python list if it was defined on the command line
    # or as None if it was not set on the command line
    include_list: Optional[List[Text]] = get_tables_argument_list(args.include)
    exclude_list: Optional[List[Text]] = get_tables_argument_list(args.exclude)

    diff_tool = args.diff
    color_output = args.color == "always" or (
        args.color == "auto" and sys.stdout.isatty
    )

    if diff_tool is None:
        diff_tool = shutil.which("diff")
    elif diff_tool:
        diff_tool = shutil.which(diff_tool)
        if diff_tool is None:
            sys.stderr.write(
                f"[*] ERROR: The external diff tool executable "
                f"'{args.diff}' was not found.{os.linesep}"
            )
            return 2

    if diff_tool:
        # ------------------------------
        #  External executable tool diff
        # ------------------------------

        diff_arg = args.diff_arg
        if diff_arg is None:
            if args.lines == 3:
                diff_arg = ["-u"]
            else:
                diff_arg = ["-u{}".format(args.lines)]
        else:
            diff_arg = diff_arg.split()

        try:
            ext_diff: Iterable[Tuple[Text, Optional[int]]] = run_external_diff(
                diff_tool,
                diff_arg,
                args.FILE1,
                args.FILE2,
                include_tables=include_list,
                exclude_tables=exclude_list,
                use_multiprocess=True,
            )

            # write stdout from external tool
            output_lines = []
            exit_code = 0
            for line, code in ext_diff:
                if color_output:
                    output_lines.append(color_unified_diff_line(line))
                else:
                    output_lines.append(line)
                if code is not None:
                    exit_code = code

            pipe_output("".join(output_lines))
            if output_lines:
                exit_code = 1
            if exit_code is not None:
                return exit_code
        except Exception as e:
            sys.stderr.write(f"[*] ERROR: {e}{os.linesep}")
            return 2
    else:
        # ---------------
        #  Unified diff
        # ---------------
        # perform the unified diff analysis
        try:
            uni_diff: Iterator[Text] = u_diff(
                args.FILE1,
                args.FILE2,
                context_lines=args.lines,
                include_tables=include_list,
                exclude_tables=exclude_list,
                use_multiprocess=True,
            )
        except Exception as e:
            sys.stderr.write(f"[*] ERROR: {e}{os.linesep}")
            return 2

        # print unified diff results to standard output stream
        output_lines = []
        has_diff = False
        if color_output:
            for line in uni_diff:
                has_diff = True
                output_lines.append(color_unified_diff_line(line))
        else:
            for line in uni_diff:
                has_diff = True
                output_lines.append(line)
        pipe_output("".join(output_lines))
        if has_diff:
            return 1
    return 0
