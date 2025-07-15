from __future__ import annotations

import errno
import platform
import shutil
import stat
import typing
from os import PathLike
from pathlib import Path

from ._base import FS
from ._errors import (
    CreateFailed,
    DirectoryExpected,
    DirectoryNotEmpty,
    FileExpected,
    ResourceError,
    ResourceNotFound,
)
from ._info import Info

if typing.TYPE_CHECKING:
    from collections.abc import Collection
    from typing import IO, Any

    from ._subfs import SubFS


_WINDOWS_PLATFORM = platform.system() == "Windows"


class OSFS(FS):
    """Filesystem for a directory on the local disk.

    A thin layer on top of `pathlib.Path`.
    """

    def __init__(self, root: str | PathLike, create: bool = False):
        super().__init__()
        self._root = Path(root).resolve()
        if create:
            self._root.mkdir(parents=True, exist_ok=True)
        else:
            if not self._root.is_dir():
                raise CreateFailed(
                    f"unable to create OSFS: {root!r} does not exist or is not a directory"
                )

    def _abs(self, rel_path: str) -> Path:
        self.check()
        return (self._root / rel_path.strip("/")).resolve()

    def open(self, path: str, mode: str = "rb", **kwargs) -> IO[Any]:
        try:
            return self._abs(path).open(mode, **kwargs)
        except FileNotFoundError:
            raise ResourceNotFound(f"No such file or directory: {path!r}")

    def exists(self, path: str) -> bool:
        return self._abs(path).exists()

    def isdir(self, path: str) -> bool:
        return self._abs(path).is_dir()

    def isfile(self, path: str) -> bool:
        return self._abs(path).is_file()

    def listdir(self, path: str) -> list[str]:
        return [p.name for p in self._abs(path).iterdir()]

    def _mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> SubFS:
        self._abs(path).mkdir(parents=parents, exist_ok=exist_ok)
        return self.opendir(path)

    def makedir(self, path: str, recreate: bool = False) -> SubFS:
        return self._mkdir(path, parents=False, exist_ok=recreate)

    def makedirs(self, path: str, recreate: bool = False) -> SubFS:
        return self._mkdir(path, parents=True, exist_ok=recreate)

    def getinfo(self, path: str, namespaces: Collection[str] | None = None) -> Info:
        path = self._abs(path)
        if not path.exists():
            raise ResourceNotFound(f"No such file or directory: {str(path)!r}")
        info = {
            "basic": {
                "name": path.name,
                "is_dir": path.is_dir(),
            }
        }
        namespaces = namespaces or ()
        if "details" in namespaces:
            stat_result = path.stat()
            details = info["details"] = {
                "accessed": stat_result.st_atime,
                "modified": stat_result.st_mtime,
                "size": stat_result.st_size,
                "type": stat.S_IFMT(stat_result.st_mode),
                "created": getattr(stat_result, "st_birthtime", None),
            }
            ctime_key = "created" if _WINDOWS_PLATFORM else "metadata_changed"
            details[ctime_key] = stat_result.st_ctime
        return Info(info)

    def remove(self, path: str):
        path = self._abs(path)
        try:
            path.unlink()
        except FileNotFoundError:
            raise ResourceNotFound(f"No such file or directory: {str(path)!r}")
        except OSError as e:
            if path.is_dir():
                raise FileExpected(f"path {str(path)!r} should be a file")
            else:
                raise ResourceError(f"unable to remove {str(path)!r}: {e}")

    def removedir(self, path: str):
        try:
            self._abs(path).rmdir()
        except NotADirectoryError:
            raise DirectoryExpected(f"path {path!r} should be a directory")
        except OSError as e:
            if e.errno == errno.ENOTEMPTY:
                raise DirectoryNotEmpty(f"Directory not empty: {path!r}")
            else:
                raise ResourceError(f"unable to remove {path!r}: {e}")

    def removetree(self, path: str):
        shutil.rmtree(self._abs(path))

    def movedir(self, src: str, dst: str, create: bool = False):
        # TODO create
        self._abs(src).rename(self._abs(dst))

    def getsyspath(self, path: str) -> str:
        return str(self._abs(path))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self._root)!r})"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__.lower()} '{self._root}'>"
