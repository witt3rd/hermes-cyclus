---
kind: MetricOptimizationKind
name: circle_packing
version: "1.0"
level: L1
direction: higher_is_better
metric: combined_score
baseline: 0.0            # naive concentric ring layout scores near 0
terminal:
  target_score: 1.0      # matching AlphaEvolve's result (sum_radii = 2.635)
  max_iterations: 200
  plateau_count: 15
---

# Circle Packing

Maximize the sum of radii of 26 non-overlapping circles packed inside a unit square
`[0,1]×[0,1]`. The AlphaEvolve paper achieved **2.635** — that is `combined_score = 1.0`.

Baseline (naive concentric rings): `combined_score ≈ 0.0` (fails validity or scores poorly).

## Target files

Workers may ONLY modify:
- `examples/circle_packing/code/initial_program.py`
  — `construct_packing()` and `compute_max_radii()` between
  `# EVOLVE-BLOCK-START` and `# EVOLVE-BLOCK-END`

Workers must NOT modify:
- `code/evaluator.py`
- `code/config.yaml`
- `code/requirements.txt`

## Evaluate

```bash
cd examples/circle_packing && \
  pip install -q numpy scipy matplotlib && \
  python3 code/evaluator.py
```

Output: JSON object. Read `combined_score` = `sum_radii / 2.635 * validity`.
Score of 1.0 = matching AlphaEvolve. Any constraint violation → score = 0.

Constraints:
- Exactly 26 circles
- All within unit square (with 1e-6 tolerance)
- No overlaps (with 1e-6 tolerance)
- Non-negative radii, no NaN

## Why this is the definitive Cyclus test case

- **Known ground truth**: AlphaEvolve's 2.635 is the published target
- **Hard constraint**: any overlap = score 0 — workers must reason about geometry
- **Full rewrites preferred**: unlike function_minimization, circle packing benefits
  from holistic redesigns, not incremental diffs (see `diff_based_evolution: false`
  in `code/config.yaml`)
- **Distributed advantage is maximal**: each worker explores a fundamentally different
  packing strategy; concurrent exploration across geometric families converges faster
  than serial hill-climbing

## Distributed advantage (Cyclus + Saturate)

```
Worker 1: claim() → hexagonal grid + SLSQP refinement    → sum_radii: 2.41
Worker 2: claim() → concentric shells + basin-hopping    → sum_radii: 2.51
Worker 3: claim() → force-directed simulation            → sum_radii: 2.38
Worker 4: claim() → greedy insertion + gradient polish   → sum_radii: 2.29
          ↑ all running concurrently ↑
Orchestrator: commit best (2.51), requeue, workers claim next
              generation with best=2.51 as new baseline
```

The island model is a natural fit for Saturate workers: assign each Saturate node an
island (constructive / optimization-based / hybrid / novel), let them evolve within
their island, and cross-pollinate via the shared queue state.

## Evolution strategy

Population: up to 10 variants across 4 islands.
- **Island 0**: Pure constructive (grid, hexagonal, layered shells)
- **Island 1**: Optimization-based (scipy SLSQP, COBYLA, gradient refinement)
- **Island 2**: Hybrid (construct layout → optimize positions/radii)
- **Island 3**: Novel/experimental (physics simulation, greedy insertion)

Per-iteration: read `database.exploitation_ratio` from `code/config.yaml`.
Every ~5 iterations: migration — take best technique from one island, apply to another.

Geometric domain knowledge (from `code/config.yaml` system message):
- Hexagonal patterns maximize density in the interior
- Edge effects make square container harder than infinite packing
- Mix of radii (large center + small gap-fillers) outperforms equal-size circles
- SLSQP with a good initial layout reliably polishes to local optima
- Shrink radii by 1e-6 to ensure validity under numerical precision

Source: adapted from [githubnext/autoloop](https://github.com/githubnext/autoloop/blob/main/.autoloop/programs/circle_packing/program.md)
and [OpenEvolve](https://github.com/codelion/openevolve).
AlphaEvolve reference: https://deepmind.google/research/publications/alphaevolve/
