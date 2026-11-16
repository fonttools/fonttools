"""Generic tools for working with trees."""

from math import ceil, log


def build_n_ary_tree(leaves, n):
    """Build N-ary tree from sequence of leaf nodes.

    Return a list of lists where each non-leaf node is a list containing
    max n nodes.
    """
    if not leaves:
        return []

    assert n > 1

    depth = ceil(log(len(leaves), n))

    if depth <= 1:
        return list(leaves)

    # Fully populate complete subtrees of root until we have enough leaves left
    root = []
    unassigned = None
    full_step = n ** (depth - 1)
    for i in range(0, len(leaves), full_step):
        subtree = leaves[i : i + full_step]
        if len(subtree) < full_step:
            unassigned = subtree
            break
        while len(subtree) > n:
            subtree = [subtree[k : k + n] for k in range(0, len(subtree), n)]
        root.append(subtree)

    if unassigned:
        # Recurse to fill the last subtree, which is the only partially populated one
        subtree = build_n_ary_tree(unassigned, n)
        if len(subtree) <= n - len(root):
            # replace last subtree with its children if they can still fit
            root.extend(subtree)
        else:
            root.append(subtree)
        assert len(root) <= n

    return root


def minimum_spanning_tree(edges):
    """Return a minimum spanning forest using Kruskal's algorithm.

    The undirected graph's edges are ``(weight, node1, node2)`` tuples. Nodes
    must be hashable, and weights must be comparable; tuple weights are
    supported. Equal-weight edges are considered in input order. The selected
    edges are returned in increasing weight order. Disconnected components
    get separate trees.
    """
    parents = {}
    sizes = {}

    def find(node):
        if node not in parents:
            parents[node] = node
            sizes[node] = 1
        while parents[node] != node:
            parents[node] = parents[parents[node]]
            node = parents[node]
        return node

    tree = []
    for edge in sorted(edges, key=lambda edge: edge[0]):
        _, node1, node2 = edge
        root1, root2 = find(node1), find(node2)
        if root1 == root2:
            continue
        # Union by size, with path compression in find().
        if sizes[root1] < sizes[root2]:
            root1, root2 = root2, root1
        parents[root2] = root1
        sizes[root1] += sizes[root2]
        tree.append(edge)
    return tree
