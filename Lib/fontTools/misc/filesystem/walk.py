from __future__ import annotations
import typing
from collections import deque
from collections.abc import Iterator, Collection

from .path import combine


if typing.TYPE_CHECKING:
    from .base import FS
    from .info import Info


class BoundWalker:
    def __init__(self, fs: FS):
        self._fs = fs

    def _iter_walk(
        self, path: str, namespaces: Collection[str] | None = None
    ) -> Iterator[tuple[str, Info | None]]:
        """Walk files using a *breadth first* search."""
        queue = deque([path])
        push = queue.appendleft
        pop = queue.pop

        while queue:
            dir_path = pop()
            for info in self._fs.scandir(dir_path, namespaces=namespaces):
                if info.is_dir:
                    yield dir_path, info  # opened a directory
                    push(combine(dir_path, info.name))
                else:
                    yield dir_path, info  # found a file
        yield path, None  # end of directory

    def files(self, path: str = "/") -> Iterator[str]:
        for path, info in self._iter_walk(path):
            if info is not None and info.is_file:
                yield combine(path, info.name)

    def dirs(self, path: str = "/") -> Iterator[str]:
        for path, info in self._iter_walk(path):
            if info is not None and info.is_dir:
                yield combine(path, info.name)
