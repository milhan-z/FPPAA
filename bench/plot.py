"""Plot runtime-vs-size from results.csv (log-log) and fit empirical slopes.

Produces three PNGs in ``bench/``:

* ``runtime_A.png`` -- Algorithm A alone,
* ``runtime_B.png`` -- Algorithm B alone,
* ``runtime_overlay.png`` -- both on one axis,

each annotated with the least-squares slope of ``log(time)`` vs ``log(n)`` -- the
empirical growth exponent we compare against theory (A ~ 1, B ~ 2).

Run after the benchmark:

    python bench/plot.py
"""

from __future__ import annotations

import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")  # headless: write PNGs without a display
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CSV = HERE / "results.csv"

COLORS = {"A": "#2563eb", "B": "#dc2626"}
LABELS = {
    "A": "A: topo-sort + DAG longest path  O(V+E)",
    "B": "B: Bellman-Ford (negated)  O(V*E)",
}


def load() -> pd.DataFrame:
    if not CSV.exists():
        sys.exit(f"missing {CSV}; run `python bench/benchmark.py` first")
    return pd.read_csv(CSV)


def mean_by_size(df: pd.DataFrame, algo: str) -> pd.DataFrame:
    """Average time_ms over seeds and runs for one algorithm, per size."""
    sub = df[df["algorithm"] == algo]
    grouped = sub.groupby("n_tasks")["time_ms"].mean().reset_index()
    return grouped.sort_values("n_tasks")


def fit_slope(ns: list[float], ts: list[float]) -> float:
    """Least-squares slope of log(t) vs log(n) -- the empirical exponent."""
    xs = [math.log(n) for n in ns]
    ys = [math.log(t) for t in ts]
    k = len(xs)
    mx = sum(xs) / k
    my = sum(ys) / k
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else float("nan")


def _style_axes(ax) -> None:
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("number of tasks  n  (log scale)")
    ax.set_ylabel("solve time  (ms, log scale)")
    ax.grid(True, which="both", ls=":", alpha=0.5)


def single_plot(df: pd.DataFrame, algo: str) -> float:
    g = mean_by_size(df, algo)
    ns = g["n_tasks"].tolist()
    ts = g["time_ms"].tolist()
    slope = fit_slope(ns, ts)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(ns, ts, "o-", color=COLORS[algo], label=LABELS[algo])
    _style_axes(ax)
    ax.set_title(f"ReelPath runtime vs size -- Algorithm {algo}\n"
                 f"empirical slope ~ {slope:.2f}")
    ax.legend()
    fig.tight_layout()
    out = HERE / f"runtime_{algo}.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}  (empirical exponent ~ {slope:.2f})")
    return slope


def overlay_plot(df: pd.DataFrame, slopes: dict[str, float]) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    for algo in ("A", "B"):
        g = mean_by_size(df, algo)
        ax.plot(g["n_tasks"], g["time_ms"], "o-", color=COLORS[algo],
                label=f"{LABELS[algo]}  (slope ~ {slopes[algo]:.2f})")
    _style_axes(ax)
    ax.set_title("ReelPath runtime vs size -- A vs B (log-log)")
    ax.legend()
    fig.tight_layout()
    out = HERE / "runtime_overlay.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    df = load()
    slopes = {algo: single_plot(df, algo) for algo in ("A", "B")}
    overlay_plot(df, slopes)
    print("\nempirical growth exponents (log-log least-squares):")
    for algo in ("A", "B"):
        print(f"  Algorithm {algo}: {slopes[algo]:.3f}")


if __name__ == "__main__":
    main()
