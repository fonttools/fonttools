"""Methods for traversing trees of otData-driven OpenType tables."""
from collections import deque
from typing import Callable, Deque, Iterable, List, Optional, Tuple
from .otBase import BaseTable


__all__ = [
    "bfs_base_table",
    "dfs_base_table",
]


SubTablePath = Tuple[BaseTable.SubTableEntry, ...]
# Given f(current frontier, new entries) add new entries to frontier
AddToFrontierFn = Callable[[Deque[SubTablePath], List[SubTablePath]], None]


def dfs_base_table(
    root: BaseTable, root_accessor: Optional[str] = None
) -> Iterable[SubTablePath]:
    """Depth-first search tree of BaseTables.

    Args:
        root (BaseTable): the root of the tree.
        root_accessor (Optional[str]): attribute name for the root table, if any (mostly
            useful for debugging).

    Yields:
        SubTablePath: tuples of BaseTable.SubTableEntry(name, table, index) namedtuples
        for each of the nodes in the tree. The last entry in a path is the current
        subtable, whereas preceding ones refer to its parent tables all the way up to
        the root.
    """
    yield from _traverse_ot_data(
        root, root_accessor, lambda frontier, new: frontier.extendleft(reversed(new))
    )


def bfs_base_table(
    root: BaseTable, root_accessor: Optional[str] = None
) -> Iterable[SubTablePath]:
    """Breadth-first search tree of BaseTables.

    Args:
        root (BaseTable): the root of the tree.
        root_accessor (Optional[str]): attribute name for the root table, if any (mostly
            useful for debugging).

    Yields:
        SubTablePath: tuples of BaseTable.SubTableEntry(name, table, index) namedtuples
        for each of the nodes in the tree. The last entry in a path is the current
        subtable, whereas preceding ones refer to its parent tables all the way up to
        the root.
    """
    yield from _traverse_ot_data(
        root, root_accessor, lambda frontier, new: frontier.extend(new)
    )


def _traverse_ot_data(
    root: BaseTable, root_accessor: Optional[str], add_to_frontier_fn: AddToFrontierFn
) -> Iterable[SubTablePath]:
    # no visited because general otData cannot cycle (forward-offset only)

    if root_accessor is None:
        root_accessor = type(root).__name__
    frontier: Deque[SubTablePath] = deque()
    frontier.append((BaseTable.SubTableEntry(root_accessor, root),))
    while frontier:
        # path is (value, attr_name) tuples. attr_name is attr of parent to get value
        path = frontier.popleft()
        current = path[-1].value

        yield path

        new_entries = []
        for subtable_entry in current.iterSubTables():
            new_entries.append(path + (subtable_entry,))

        add_to_frontier_fn(frontier, new_entries)
