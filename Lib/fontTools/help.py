import pkgutil
import sys
import fontTools
import importlib
import os
from pathlib import Path

cli_description = "Show this help"


def _discover_path_importables(pkg_pth, pkg_name):
    """Yield all importables under a given path and package."""
    for dir_path, _d, file_names in os.walk(pkg_pth):
        pkg_dir_path = Path(dir_path)

        if pkg_dir_path.parts[-1] == "__pycache__":
            continue

        if all(Path(_).suffix != ".py" for _ in file_names):
            continue

        rel_pt = pkg_dir_path.relative_to(pkg_pth)
        pkg_pref = ".".join((pkg_name,) + rel_pt.parts)
        yield from (
            pkg_path
            for _, pkg_path, _ in pkgutil.walk_packages(
                (str(pkg_dir_path),), prefix=f"{pkg_pref}.",
            )
        )


def show_help_list():
    path = fontTools.__path__
    for pkg in sorted(
        set(_discover_path_importables(fontTools.__path__[0], "fontTools"))
    ):
        try:
            description = __import__(
                pkg, globals(), locals(), ["cli_description"]
            ).cli_description
            pkg = pkg[10:].replace(".__main__", "")
            print("fonttools %-12s %s" % (pkg, description), file=sys.stderr)
        except Exception as e:
            pass


if __name__ == "__main__":
    print("fonttools v%s\n" % fontTools.__version__, file=sys.stderr)
    show_help_list()
