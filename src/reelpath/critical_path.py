"""Algorithm A: topological sort followed by a DAG longest-path pass.

The algorithm runs in ``O(V + E)`` by processing vertices in topological order
and relaxing each directed edge once. Every predecessor of a vertex is final
before that vertex is processed, so one maximum-relaxation pass is sufficient.

Kahn's topological sort and the longest-path relaxation are implemented directly
in this module. No library graph algorithm is used.
"""

from __future__ import annotations

from collections import deque

from .graph import CycleError, Graph

NAME = "topo-dag-longest-path"

NEG_INF = float("-inf")


def topological_sort(graph: Graph) -> list[int]:
    """Return a topological ordering of ``graph`` using Kahn's algorithm.

    Raises :class:`CycleError` if the graph is not acyclic. A cycle is detected
    when the produced order does not include every vertex.
    """
    indeg = graph.indegree()
    queue: deque[int] = deque(v for v in range(graph.num_vertices) if indeg[v] == 0)
    order: list[int] = []

    while queue:
        u = queue.popleft()
        order.append(u)
        for v, _w in graph.adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    if len(order) != graph.num_vertices:
        raise CycleError(
            "graph contains a cycle: only "
            f"{len(order)} of {graph.num_vertices} vertices could be ordered"
        )
    return order


def longest_path(graph: Graph, source: int) -> tuple[list[float], list[int]]:
    """Compute longest-path distances and predecessors from ``source`` on a DAG.

    ``dist[v]`` is the maximum total weight of a path from ``source`` to ``v``.
    It is negative infinity when ``v`` is unreachable. ``pred[v]`` stores the
    preceding vertex on one maximum-weight path, or ``-1`` when none exists.
    """
    order = topological_sort(graph)

    dist: list[float] = [NEG_INF] * graph.num_vertices
    pred: list[int] = [-1] * graph.num_vertices
    dist[source] = 0.0

    for u in order:
        du = dist[u]
        if du == NEG_INF:
            continue
        for v, w in graph.adj[u]:
            nd = du + w
            if nd > dist[v]:
                dist[v] = nd
                pred[v] = u
    return dist, pred
