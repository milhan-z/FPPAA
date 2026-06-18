"""Benchmark harness: sweep instance sizes, time both algorithms, write CSV.

Reproducibility (README s7): every instance is built from an explicit seed, the
seeds and sizes are printed at the top of the run, and a single command
regenerates ``bench/results.csv``:

    python bench/benchmark.py --sizes 100,300,1000,3000,10000 --seeds 1,2,3,4,5

We time the *solve only* -- the call to each algorithm's ``longest_path`` -- with
``time.perf_counter``. Graph construction and the (identical, shared) schedule
extraction are excluded, so the numbers isolate the algorithmic difference
between A's single topological pass and B's V-1 Bellman-Ford sweeps.

Algorithm A is cheap at every size, so it gets a fixed number of timed runs.
Algorithm B is O(V*E); a single solve already costs ~135 s at n=10000, so its
run count is scaled down for the largest sizes to keep the one-command benchmark
to a sensible wall-clock while still averaging several runs at the smaller sizes.
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import sys
import time

# Make `reelpath` importable straight from a clean checkout (no install needed).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from reelpath import bellman_ford, critical_path  # noqa: E402
from reelpath.generator import generate_split_dag  # noqa: E402

CSV_HEADER = [
    "algorithm", "n_tasks", "n_vertices", "n_edges",
    "seed", "run", "time_ms", "makespan", "crosscheck_ok",
]

RUNS_A = 5  # Algorithm A is sub-second at every size -> always average 5 runs.


def runs_for_b(n: int, override: int | None) -> int:
    """Timed runs for Algorithm B, scaled by its O(V*E) cost."""
    if override is not None:
        return override
    if n <= 300:
        return 5
    if n <= 1000:
        return 3
    if n <= 3000:
        return 2
    return 1


def time_once(fn, graph, source) -> tuple[float, float]:
    """One timed solve -> (elapsed_ms, makespan = dist[target] read by caller)."""
    start = time.perf_counter()
    dist, _pred = fn(graph, source)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, dist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ReelPath benchmark harness")
    parser.add_argument("--sizes", default="100,300,1000,3000,10000",
                        help="comma-separated task counts")
    parser.add_argument("--seeds", default="1,2,3,4,5",
                        help="comma-separated random seeds")
    parser.add_argument("--runs", type=int, default=None,
                        help="force a uniform number of B runs per (size, seed)")
    parser.add_argument("--avg-degree", type=int, default=3,
                        help="approximate average out-degree (edge density)")
    parser.add_argument("--out",
                        default=str(pathlib.Path(__file__).with_name("results.csv")),
                        help="output CSV path")
    args = parser.parse_args(argv)

    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    out_path = pathlib.Path(args.out)

    print("=" * 66, flush=True)
    print("ReelPath benchmark", flush=True)
    print(f"  sizes      : {sizes}", flush=True)
    print(f"  seeds      : {seeds}   (fixed & reported for reproducibility)", flush=True)
    print(f"  avg degree : {args.avg_degree}  (m ~ {args.avg_degree}*n edges)", flush=True)
    print(f"  A runs     : {RUNS_A} per instance", flush=True)
    print(f"  output     : {out_path}", flush=True)
    print("=" * 66, flush=True)

    rows: list[dict] = []
    for n in sizes:
        rb = runs_for_b(n, args.runs)
        for seed in seeds:
            dag, _tg = generate_split_dag(n, avg_out_degree=args.avg_degree, seed=seed)
            g, src, tgt = dag.graph, dag.source, dag.target
            nv, ne = g.num_vertices, g.num_edges

            a_measurements: list[tuple[int, float]] = []
            mk_a = 0.0
            for run in range(1, RUNS_A + 1):
                ms, dist = time_once(critical_path.longest_path, g, src)
                mk_a = dist[tgt]
                a_measurements.append((run, ms))

            b_measurements: list[tuple[int, float]] = []
            mk_b = 0.0
            for run in range(1, rb + 1):
                ms, dist = time_once(bellman_ford.longest_path, g, src)
                mk_b = dist[tgt]
                b_measurements.append((run, ms))

            ok = int(mk_a == mk_b)
            for run, ms in a_measurements:
                rows.append({"algorithm": "A", "n_tasks": n, "n_vertices": nv,
                             "n_edges": ne, "seed": seed, "run": run,
                             "time_ms": round(ms, 4), "makespan": int(mk_a),
                             "crosscheck_ok": ok})
            for run, ms in b_measurements:
                rows.append({"algorithm": "B", "n_tasks": n, "n_vertices": nv,
                             "n_edges": ne, "seed": seed, "run": run,
                             "time_ms": round(ms, 4), "makespan": int(mk_b),
                             "crosscheck_ok": ok})

            a_avg = sum(m for _, m in a_measurements) / len(a_measurements)
            b_avg = sum(m for _, m in b_measurements) / len(b_measurements)
            status = "OK" if ok else "MISMATCH!"
            print(f"  n={n:>6} V={nv:>6} E={ne:>6} seed={seed} "
                  f"mk={int(mk_a):>5} | A~{a_avg:8.2f}ms  B~{b_avg:10.2f}ms "
                  f"(B runs={rb})  cross={status}", flush=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    all_ok = all(r["crosscheck_ok"] == 1 for r in rows)
    print("=" * 66, flush=True)
    print(f"wrote {len(rows)} rows to {out_path}", flush=True)
    print(f"cross-check A == B on every instance: {'PASS' if all_ok else 'FAIL'}", flush=True)
    print("=" * 66, flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
