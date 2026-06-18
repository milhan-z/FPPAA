# ReelPath — Critical-Path Analyzer for Video Production Pipelines

> **EF234405 Design & Analysis of Algorithms — Final Exam (Capstone).**
> ITS, 2025/2026(2). ReelPath computes the **critical path** and **makespan** of a
> video/film production schedule, and **cross-checks its answer with two
> independent algorithms** on the same instances.

[![tests](https://img.shields.io/badge/tests-41%20passing-brightgreen)](tests)
[![python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Repository:** https://github.com/milhan-z/draftpaa

---

## 1. Problem & motivation

A video production (short film, YouTube video, ad) is a set of tasks with
durations and dependencies: you cannot edit a scene before it is shot, cannot
colour-grade before editing, cannot publish before rendering. Producers need to
know two things:

1. **What is the earliest the project can finish** — the *makespan*?
2. **Which chain of tasks is the bottleneck** — the *critical path* — i.e. which
   tasks have zero scheduling freedom, and which have *slack* (can slip without
   delaying release)?

ReelPath answers both, lets the producer run **what-if** analysis (drag a task's
duration and watch the critical path re-route), and **verifies its answer with a
second, independent algorithm**.

**Users:** indie filmmakers, content-team producers, video agencies, students
planning a production.

---

## 2. Formal model

We model a production instance as a **weighted, directed acyclic graph (DAG)**
using *node-splitting*, which turns task durations into edge weights so both
algorithms run on one purely edge-weighted graph.

### 2.1 Input
- A set of tasks `T = {1, …, k}`; each task `i` has a duration `d(i) > 0`.
- Precedence constraints `P ⊆ T × T`; `(i, j) ∈ P` means *"task `i` must finish
  before task `j` may start"*.
- **Constraint:** `P` must be acyclic. A cyclic instance is infeasible and is
  detected and rejected (`CycleError`) — no schedule exists.

### 2.2 Graph construction (node-splitting)
Split each task `i` into an entry node `i_in` and an exit node `i_out`:
- `V = {s, t} ∪ { i_in } ∪ { i_out }`, so `|V| = 2k + 2`.
- Edges `E`:
  - **Duration edge** `(i_in → i_out)` with weight `d(i)`.
  - **Precedence edge** `(i_out → j_in)` with weight `0` for each `(i, j) ∈ P`.
  - **Source edge** `(s → i_in)` with weight `0` for each task with no prerequisite.
  - **Sink edge** `(i_out → t)` with weight `0` for each terminal task.
- Weight function `w : E → ℝ≥0`; **source** `s`, **target** `t`.

### 2.3 Objective
Find the **maximum-weight** path from `s` to `t`:
`M = max over all s→t paths π of Σ_{e∈π} w(e)`.
- `M` = **makespan** (earliest possible completion time).
- **Critical path** = the tasks on a maximum-weight `s→t` path.
- Per-task: earliest start/finish `ES/EF`, latest start/finish `LS/LF`, and
  **slack `= LS − ES`**. A task is **critical ⇔ slack = 0**.

Because `G` is a DAG, every `s→t` path is finite, so `M` is finite and
well-defined. (Longest path in a graph with positive cycles is unbounded and
NP-hard — acyclicity is exactly what makes this tractable.)

### 2.4 Worked sanity instance
`Shoot (d=5) → Edit (d=4)`:
`s →0→ Shoot_in →5→ Shoot_out →0→ Edit_in →4→ Edit_out →0→ t`.
Makespan `= 9`; critical path `= Shoot → Edit`. This is a unit test
(`tests/test_small.py`).

---

## 3. The two algorithms

Both run on the **same** node-split graph and must report the **same makespan**
(exact cross-check). They sit behind one interface —
`longest_path(graph, source) -> (dist, pred)` — so the schedule layer drives
either with no duplicated logic.

### Algorithm A (core): Topological sort + DAG longest path — `src/reelpath/critical_path.py`
Kahn's algorithm produces a topological order (raising `CycleError` if the order
fails to cover every vertex), then a **single** max-relaxation pass over that
order computes the longest-path value at every vertex. Because every predecessor
of `u` is finalised before `u` is processed, one pass is exact.
**Time `O(V + E)`, space `O(V + E)`.**

### Algorithm B (baseline): Bellman–Ford on negated weights — `src/reelpath/bellman_ford.py`
Longest path in a DAG = shortest path with negated weights. The textbook
Bellman–Ford relaxes all edges `V − 1` times (no early-exit, deliberately, so it
exhibits its true worst-case cost), then a final pass certifies that no edge
relaxes further (no negative cycle). The negated distance is flipped back to the
makespan. **Time `O(V · E)`, space `O(V + E)`.**

### Schedule extraction — `src/reelpath/schedule.py`
Forward pass (longest path from `s`) gives `ES/EF`; a backward pass (reverse
topological order) gives `LS/LF`; `slack = LS − ES`; critical set = tasks with
`slack = 0`.

> **Own-the-core guarantee:** topological sort, the DAG longest-path relaxation,
> and Bellman–Ford are **hand-written**. No library path/toposort routine
> (`networkx.dag_longest_path`, `networkx.topological_sort`, `nx.bellman_ford_*`,
> `scipy.sparse.csgraph.*`, …) is used anywhere. Libraries are used only for the
> demo server, plotting, data I/O, and tests.

---

## 4. Architecture & modules

```
reelpath/
├── src/reelpath/
│   ├── __init__.py        # public API + solve() convenience
│   ├── graph.py           # Graph (adjacency list), CycleError, node-split build
│   ├── generator.py       # seeded layered-DAG generator (acyclic by construction)
│   ├── critical_path.py   # Algorithm A: Kahn topo-sort + DAG longest path  (CORE)
│   ├── bellman_ford.py    # Algorithm B: Bellman–Ford on negated weights
│   └── schedule.py        # ES/EF/LS/LF/slack + shared analyze() interface
├── app/
│   ├── server.py          # Flask backend: POST /solve -> real computation
│   └── ReelPath.dc.html   # single-page demo UI (DAG + Gantt + what-if sliders)
├── bench/
│   ├── benchmark.py       # size sweep -> results.csv  (fixed seeds)
│   ├── plot.py            # log–log runtime plots + empirical slope
│   ├── results.csv        # generated timing data (committed)
│   └── runtime_*.png      # generated plots (committed)
├── tests/
│   ├── test_small.py      # hand-verified tiny instances
│   └── test_crosscheck.py # A == B on many random instances
├── report/                # Report.md/pdf, Declaration.md/pdf, build_pdf.py
├── dist/make_zip.py       # packages Report.pdf + Declaration.pdf
├── README.md · requirements.txt · pyproject.toml · LICENSE · conftest.py
```

Data flow: `generator → graph → {critical_path, bellman_ford} → schedule →
{demo, benchmark → plot}`.

**Data-structure choices.** An integer-indexed **adjacency list** is used
throughout: it is `O(V + E)` in memory and gives cache-friendly, tight inner
loops — decisive for Algorithm B at the 10,000-task scale. A FIFO **queue**
drives Kahn's algorithm; flat parallel edge arrays drive Bellman–Ford's sweeps.

---

## 5. Build / run

Python **3.11.9** (any 3.11+ works). All commands below are run from the repo root.

```bash
# 1. Setup
python -m venv .venv
.venv\Scripts\activate           # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

# 2. Run the tests  (41 tests)
pytest -q

# 3. Reproduce the benchmark + plots  (one command each)
python bench/benchmark.py --sizes 100,300,1000,3000,10000 --seeds 1,2,3,4,5
python bench/plot.py

# 4. Launch the interactive demo, then open http://localhost:5000
python app/server.py
```

> The scripts add `src/` to `sys.path` themselves, so `pip install -r
> requirements.txt` is enough — no editable install required. (You *may*
> `pip install -e .` if you prefer an installed package.)
>
> ⏱️ **Benchmark runtime:** Algorithm A finishes in milliseconds at every size;
> Algorithm B is `O(V·E)` and a single `n = 10,000` solve takes ~2.5 minutes, so
> the full sweep above takes roughly **15–20 minutes** (B's run-count is scaled
> down at the largest sizes — see `bench/benchmark.py`). For a quick check,
> shrink it: `--sizes 100,300,1000 --seeds 1,2,3`.

---

## 6. Demo

`app/server.py` (Flask) serves `app/ReelPath.dc.html` and exposes
`POST /solve` with `{tasks, deps}`, returning **real** computed values:
`{makespan, critical_ids, critical_path, schedule[], timing:{A_ms,B_ms},
crosscheck_ok}` — there are **no mocked numbers**. The UI shows:

1. **Production DAG** with the critical path highlighted (amber = zero slack).
2. **Gantt chart** — bars at `ES`, length `d(i)`, slack drawn as a hatched extension.
3. **What-if sliders** — drag any task's duration and the critical path, Gantt,
   and makespan recompute live from the backend; the footer reports the real
   per-request `A_ms`, `B_ms`, and the A == B cross-check.

The demo is seeded with a sample short-film pipeline (makespan **27 days**;
critical path `Write script → Casting → Shoot → Edit → VFX → Colour grade →
Render → Publish`; `Storyboard`, `Location scout`, `Sound design` carry slack).

---

## 7. Benchmark & empirical results

- **Sizes:** `n_tasks ∈ {100, 300, 1000, 3000, 10000}` (≥ 1,000 satisfied;
  spans two orders of magnitude, 100 → 10,000).
- **Density:** `m ≈ 3n` precedence edges (split graph `|V| = 2n+2`, `|E| ≈ 4n`).
- **Seeds:** `{1, 2, 3, 4, 5}`, fixed and printed by the harness.
- **Timing:** `time.perf_counter` around the **solve only** (each algorithm's
  `longest_path`); construction and the shared schedule extraction are excluded.
- **CSV schema** (`bench/results.csv`):
  `algorithm,n_tasks,n_vertices,n_edges,seed,run,time_ms,makespan,crosscheck_ok`.

<!-- RESULTS:START -->
**Measured results** (this machine: Windows 11, CPython 3.11.9; 205 timing rows
over 25 instances). **All 25 instances passed the `makespan_A == makespan_B`
cross-check.** Mean solve time, averaged over seeds and runs:

| `n_tasks` | \|V\| | \|E\| | **A** mean (ms) | **B** mean (ms) | speedup B/A | makespan range |
|---:|---:|---:|---:|---:|---:|:--|
| 100 | 202 | 403 | 0.188 | 13.67 | 73× | 128–155 |
| 300 | 602 | 1 201 | 0.597 | 113.40 | 190× | 227–243 |
| 1 000 | 2 002 | 4 072 | 1.914 | 1 353.51 | 707× | 400–430 |
| 3 000 | 6 002 | 12 111 | 6.313 | 12 907.09 | 2 045× | 706–785 |
| 10 000 | 20 002 | 40 375 | 23.382 | 140 848.67 | 6 024× | 1 299–1 352 |

**Empirical growth exponents** (least-squares slope of `log(time)` vs `log(n)`):

| Algorithm | Empirical exponent | Theory |
|---|---|---|
| A — topo + DAG longest path | **1.04** | `O(n)` → 1.0 |
| B — Bellman–Ford (negated) | **2.02** | `O(n²)` → 2.0 |

Both match theory closely. At `n = 10 000`, Algorithm A finishes in ~23 ms while
the `O(V·E)` baseline takes ~141 s — a **~6 000× gap**, exactly the
linear-vs-quadratic prediction.

![Algorithm A vs B — log–log runtime](bench/runtime_overlay.png)

| Algorithm A (linear) | Algorithm B (quadratic) |
|---|---|
| ![A](bench/runtime_A.png) | ![B](bench/runtime_B.png) |
<!-- RESULTS:END -->

---

## 8. Testing

- `tests/test_small.py` — hand-verified instances: `Shoot→Edit` makespan = 9, a
  diamond DAG (makespan 11 with a known slack task), a cyclic instance that must
  raise `CycleError`, plus single-task and self-dependency edge cases.
- `tests/test_crosscheck.py` — across many seeds × sizes, asserts
  `makespan_A == makespan_B` exactly **and** that the critical-path durations sum
  to the makespan.

```bash
pytest -q          # 41 passed
```

---

## 9. Reproducibility & scale justification

- **One command** regenerates all timing data and plots (§5, step 3). Every
  random step takes an explicit `seed`; the benchmark fixes and prints its seeds.
- **Scale:** the core algorithm is exercised up to `n = 10,000` tasks
  (`|V| = 20,002`, `|E| ≈ 40,000`) — well past the mandated `n ≥ 1,000` — across
  five sizes spanning two orders of magnitude.

---

## 10. Attribution

- **Algorithms** (topological sort, DAG longest/shortest path, Bellman–Ford)
  follow **CLRS**, *Introduction to Algorithms* (Cormen, Leiserson, Rivest,
  Stein), as taught in EF234405. The implementations in `critical_path.py` and
  `bellman_ford.py` are the authors' own code.
- **Libraries** (support only — never for the core path computation):

  | Library | Version | Used for |
  |---|---|---|
  | Python | 3.11.9 | language runtime |
  | Flask | 3.1.3 | demo backend (serving/routing) |
  | matplotlib | 3.11.0 | benchmark plots |
  | pandas | 3.0.3 | reading/aggregating `results.csv` |
  | pytest | 9.1.0 | test runner |
  | markdown | 3.10.2 | report/declaration → HTML (PDF build only) |

  No `networkx`, `scipy`, or any graph library is used. The HTML/CSS/JS in
  `ReelPath.dc.html` is the authors' own.

---

## 11. License

MIT — see [LICENSE](LICENSE).
