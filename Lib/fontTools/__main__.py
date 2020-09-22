"""This main module for run main function.
"""
import sys
import runpy


def main():
    """ Main function
    in this function we do input-arg parsing
    and call related module.
    """
    if len(sys.argv) < 2:
        sys.argv.append("help")
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        sys.argv[1] = "help"
    mod = 'fontTools.'+sys.argv[1]
    sys.argv[1] = sys.argv[0] + ' ' + sys.argv[1]
    del sys.argv[0]
    runpy.run_module(mod, run_name='__main__')


if __name__ == '__main__':
    sys.exit(main())
