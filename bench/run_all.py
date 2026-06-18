"""Run the benchmark and regenerate every runtime plot.

Examples
--------
Full default benchmark:

    python bench/run_all.py

Quick verification run:

    python bench/run_all.py --sizes 100,300,1000 --seeds 1,2,3

Every argument is forwarded to ``bench/benchmark.py``. The plotting script runs
only after the benchmark finishes successfully.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def main() -> int:
    benchmark_cmd = [
        sys.executable,
        str(HERE / "benchmark.py"),
        *sys.argv[1:],
    ]
    plot_cmd = [sys.executable, str(HERE / "plot.py")]

    print("Running benchmark...")
    subprocess.run(benchmark_cmd, cwd=ROOT, check=True)

    print("\nGenerating plots...")
    subprocess.run(plot_cmd, cwd=ROOT, check=True)

    print("\nDone. Updated bench/results.csv and bench/runtime_*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
