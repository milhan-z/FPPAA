"""Algorithm B (baseline): Bellman-Ford on negated weights.

Longest path in a DAG equals shortest path once every weight is negated. The
graph has no cycles, so negation introduces no negative cycle and Bellman-Ford
terminates with correct shortest distances. We then negate the distance back to
recover the longest-path value.

This is the textbook ``O(V * E)`` version: it performs ``V - 1`` full sweeps over
the edge set with no early-exit, so its empirical cost grows with ``V * E`` and
provides the deliberately slower baseline against Algorithm A's single pass.
A final sweep asserts that nothing relaxes further -- the promised certificate
that no negative cycle exists.

Like :mod:`reelpath.critical_path`, every line of the relaxation is hand-written;
no library shortest-path routine is used.
"""

from __future__ import annotations

from .graph import Graph

NAME = "bellman-ford"

POS_INF = float("inf")
NEG_INF = float("-inf")


def longest_path(graph: Graph, source: int) -> tuple[list[float], list[int]]:
    """Longest-path distances and predecessors from ``source`` via Bellman-Ford.

    Returns ``(dist, pred)`` with the same meaning and conventions as
    :func:`reelpath.critical_path.longest_path` (``dist[v]`` is the longest
    ``source -> v`` weight, ``-inf`` if unreachable). Internally it works on
    negated weights as a shortest-path problem and negates the result back.
    """
    n = graph.num_vertices
    # Flatten the edges once into parallel arrays; the inner loop then touches
    # only locals, which keeps each of the V-1 sweeps as tight as Python allows.
    edges = graph.edge_list()
    us = [e[0] for e in edges]
    vs = [e[1] for e in edges]
    ws = [e[2] for e in edges]  # original (non-negative) weights
    m = len(edges)

    sdist: list[float] = [POS_INF] * n  # shortest distances on negated weights
    pred: list[int] = [-1] * n
    sdist[source] = 0.0

    # Relax all edges V - 1 times (negated weight => subtract).
    #
    # This is the *unconditional* textbook Bellman-Ford: we deliberately do NOT
    # early-exit when a sweep makes no change. Early termination would let this
    # baseline converge in a couple of sweeps on our near-topologically-ordered
    # edge list and hide its true worst-case cost. The exam asks B to be the
    # honest O(V * E) comparison point against Algorithm A's single pass, so we
    # let it pay the full V - 1 sweeps -- exactly the behaviour the runtime plot
    # is meant to reveal.
    for _ in range(n - 1):
        for k in range(m):
            u = us[k]
            du = sdist[u]
            if du == POS_INF:
                continue
            nd = du - ws[k]
            v = vs[k]
            if nd < sdist[v]:
                sdist[v] = nd
                pred[v] = u

    # Certificate pass: on a DAG (no negative cycle) nothing may relax further.
    for k in range(m):
        u = us[k]
        if sdist[u] != POS_INF and sdist[u] - ws[k] < sdist[vs[k]]:
            raise AssertionError("Bellman-Ford found a relaxable edge: negative cycle?")

    dist = [(-d if d != POS_INF else NEG_INF) for d in sdist]
    return dist, pred
