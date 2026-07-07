---
kind: MetricOptimizationKind
name: function_minimization
version: "1.0"
direction: higher_is_better
metric: combined_score
baseline: 0.56
terminal:
  target_score: 1.3        # well above the 1.2x multiplier ceiling
  max_iterations: 100
  plateau_count: 10        # stall detection: 10 consecutive rejections
---

# Function Minimization

Improve `code/initial_program.py` to reliably find the global minimum of:

```
f(x, y) = sin(x) * cos(y) + sin(x*y) + (x^2 + y^2) / 20
```

Known global minimum: `(-1.704, 0.678)` ≈ `-1.519`.
Baseline (naive random search): `combined_score = 0.56`.

## Target files

Workers may ONLY modify:
- `examples/function_minimization/code/initial_program.py`
  — specifically the `search_algorithm` function between
  `# EVOLVE-BLOCK-START` and `# EVOLVE-BLOCK-END`

Workers must NOT modify:
- `code/evaluator.py`
- `code/config.yaml`
- `code/requirements.txt`

## Evaluate

```bash
cd examples/function_minimization && \
  pip install -q numpy scipy && \
  python3 code/evaluator.py
```

Output: JSON object. Read `combined_score` (higher is better).
Score components: `value_score` (50%) + `distance_score` (30%) + `reliability_score` (20%)
with a multiplier (1.5×) when avg distance < 0.5.

## Why this is a good first Cyclus test case

- Eval runs in ~1 second — tight feedback loop
- Self-contained: no external services, pure Python + numpy/scipy
- Known ground truth: `(-1.704, 0.678)` with value `-1.519`
- Works well for Saturate: concurrent workers explore different algorithm families
  simultaneously (simulated annealing, basin-hopping, gradient estimation, particle
  swarm) rather than one agent simulating diversity serially

## Distributed advantage (Cyclus + Saturate)

Sequential (Autoloop): one hypothesis per 6h trigger.

Distributed (Cyclus + Saturate):
```
Worker 1: claim() → simulated annealing variant  → combined_score: 0.89
Worker 2: claim() → basin-hopping                → combined_score: 1.12
Worker 3: claim() → gradient estimation          → combined_score: 0.74
          ↑ running concurrently on 3 nodes ↑
Orchestrator: commit best (1.12), requeue with baseline=1.12
```

3× search throughput per wall-clock window. Plateau detection is a scheduler signal,
not a role-prompt heuristic.

## Evolution strategy

Population size: 10 variants. Track per variant:
- `algorithm_type`: simulated_annealing | basin_hopping | gradient_based | particle_swarm | hybrid
- `code_complexity`: simple (<20 lines) | medium (20-50) | complex (>50)
- `combined_score`: current best for this variant
- `generation`: iteration that produced it

Per-iteration strategy mix (read from `code/config.yaml`):
- **Exploitation (70%)**: refine top-3 variant with small targeted diff
- **Exploration (20%)**: try algorithm family not yet in population
- **Weighted random (10%)**: moderate change to any population member

Plateau detection:
- 3 consecutive rejections → switch exploit↔explore
- 5 consecutive rejections → try radically different algorithm family

Source: adapted from [githubnext/autoloop](https://github.com/githubnext/autoloop/blob/main/.autoloop/programs/function_minimization/program.md)
and [OpenEvolve](https://github.com/codelion/openevolve).
