import sys
from .cli import main


cli_description = "Convert a UFO font from cubic to quadratic curves"
if __name__ == "__main__":
    sys.exit(main())
