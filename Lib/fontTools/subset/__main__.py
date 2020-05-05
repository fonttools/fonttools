from fontTools.misc.py23 import *
import sys
from fontTools.subset import main


cli_description = "OpenType font subsetter and optimizer"

if __name__ == '__main__':
    sys.exit(main())
