"""Algorithm A (core): topological sort + DAG longest path.

This is the non-trivial, "own the core" algorithm. It runs in ``O(V + E)`` by
relaxing every vertex exactly once, in topological order. Because each
predecessor of a vertex ``u`` is finalised before ``u`` is processed, a single
max-relaxation pass yields the true longest-path value at every vertex
(see the inductive correctness argument in the report, README s10).

Nothing here calls a library graph routine -- Kahn's algorithm and the
relaxation loop are written by hand, as required by the exam guardrails.
"""

from __future__ import annotations

from collections import deque

from .graph import CycleError, Graph

NAME = "topo-dag-longest-path"

NEG_INF = float("-inf")


def topological_sort(graph: Graph) -> list[int]:
    """Return a topological ordering of ``graph`` using Kahn's algorithm.

    Raises :class:`CycleError` if the graph is not acyclic -- detected when the
    produced order fails to cover every vertex, which happens exactly when a
    cycle keeps some in-degrees from ever reaching zero.
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
    """Longest-path distances and predecessors from ``source`` on a DAG.

    Returns ``(dist, pred)`` where ``dist[v]`` is the maximum total weight of any
    ``source -> v`` path (``-inf`` if ``v`` is unreachable) and ``pred[v]`` is the
    vertex preceding ``v`` on such a path (``-1`` if none).

    This is the shared "input graph + source -> distances + predecessor map"
    interface; :mod:`reelpath.bellman_ford` exposes the identical signature so
    the schedule layer can drive either algorithm with no duplicated logic.
    """
    order = topological_sort(graph)

    dist: list[float] = [NEG_INF] * graph.num_vertices
    pred: list[int] = [-1] * graph.num_vertices
    dist[source] = 0.0

    for u in order:
        du = dist[u]
        if du == NEG_INF:
            continue  # u not reachable from source; nothing to relax
        for v, w in graph.adj[u]:
            nd = du + w
            if nd > dist[v]:  # relax for MAXIMUM
                dist[v] = nd
                pred[v] = u
    return dist, pred
