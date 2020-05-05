import sys
from fontTools.varLib import main


cli_description = "Build a variable font from a designspace file and masters"

if __name__ == '__main__':
	sys.exit(main())
