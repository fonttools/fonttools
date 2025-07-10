import os
import platform


_WINDOWS_PLATFORM = platform.system() == "Windows"


def combine(path1: str, path2) -> str:
    # faster than os.path.join() but only works when second path is relative
    # and there are no backreferences in either
    if not path1:
        return path2.lstrip()
    return "{}/{}".format(path1.rstrip("/"), path2.lstrip("/"))


def split(path: str) -> tuple[str, str]:
    if "/" not in path:
        return ("", path)
    split = path.rsplit("/", 1)
    return (split[0] or "/", split[1])


def dirname(path: str) -> str:
    return split(path)[0]


def basename(path: str) -> str:
    return split(path)[1]


def forcedir(path: str) -> str:
    # Ensure the path ends with a trailing forward slash.
    if not path.endswith("/"):
        return path + "/"
    return path


def abspath(path: str) -> str:
    # Since FS objects have no concept of a *current directory*, this
    # simply adds a leading ``/`` character if the path doesn't already
    # have one.
    if not path.startswith("/"):
        return "/" + path
    return path


def isbase(path1: str, path2: str) -> bool:
    # Check if `path1` is a base of `path2`.
    _path1 = forcedir(abspath(path1))
    _path2 = forcedir(abspath(path2))
    return _path2.startswith(_path1)  # longer one is child


def frombase(path1: str, path2: str) -> str:
    # Get the final path of `path2` that isn't in `path1`.
    if not isbase(path1, path2):
        raise ValueError(f"path1 must be a prefix of path2: {path1!r} vs {path2!r}")
    return path2[len(path1) :]


def relpath(path: str) -> str:
    return path.lstrip("/")


def normpath(path: str) -> str:
    normalized = os.path.normpath(path)
    if _WINDOWS_PLATFORM:
        # os.path.normpath converts backslashes to forward slashes on Windows
        # but we want forward slashes, so we convert them back
        normalized = normalized.replace("\\", "/")
    return normalized
