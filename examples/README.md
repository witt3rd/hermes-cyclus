# hermes-cyclus Examples

These examples demonstrate `MetricOptimizationKind` loops — the loop kind that runs
until a numeric metric improves, then commits the change and continues. Based on the
same use cases as [GitHub Next's Autoloop](https://github.com/githubnext/autoloop)
and [Karpathy's autoresearch](https://github.com/karpathy/autoresearch).

## Why these are more interesting on Cyclus + Saturate

Autoloop runs one hypothesis per trigger (sequential). Cyclus + Saturate makes the
population *real*:

```
post(MetricOptimizationKind, "circle-packing", N candidates seeded)

Worker 1 (node A): claim() → propose hexagonal grid variant → eval → score 2.41
Worker 2 (node B): claim() → propose SLSQP warm-start      → eval → score 2.51
Worker 3 (node C): claim() → propose basin-hopping          → eval → score 2.38
                   ↑ all running concurrently ↑
Orchestrator:  collect → commit best (2.51) → requeue with updated baseline
```

N independent hypotheses per wall-clock window. Plateau detection becomes a scheduler
concern — if workers keep regressing, Saturate can signal a strategy shift. Diversity
isn't role-prompt advice; it's the natural state of concurrent workers exploring
different regions of the search space.

## Example index

| Example | Loop kind | Eval time | Known target | Status |
|---------|-----------|-----------|-------------|--------|
| [function_minimization](function_minimization/) | `MetricOptimizationKind` | ~1s | 0.56 → 1.0+ | ✅ ready |
| [circle_packing](circle_packing/) | `MetricOptimizationKind` | ~2s | AlphaEvolve 2.635 | ✅ ready |
| [test_coverage](test_coverage/) | `MetricOptimizationKind` | ~5s | meta: Cyclus improving itself | ✅ ready |
| [autoresearch](autoresearch/) | `MetricOptimizationKind` | ~5min | val_bpb minimization | 🔲 Arc 2 |

## Spec format

Each example has a `spec.md` — a `MetricOptimizationSpec` that Cyclus reads to drive
the loop. The spec declares:

- **goal** — what to optimize, in plain English
- **target_files** — what the worker may modify
- **evaluate** — command that outputs a JSON object with a numeric metric
- **metric** — which key to read from the JSON output
- **direction** — `higher_is_better` or `lower_is_better`
- **baseline** — starting score for comparison
- **terminal** — conditions to stop (max_iterations, target_score, plateau_count)
- **evolution_strategy** — optional: population tracking, exploration/exploitation mix

The spec format will map directly to a typed Python `MetricOptimizationSpec` dataclass
in Arc 1. For now it lives as structured markdown.

## Running an example (once Arc 1 ships)

```bash
# Post to queue
cyclus_queue post metric_opt circle_packing "Maximize circle packing sum of radii"

# Workers claim and run (one per Saturate node)
cyclus_queue claim metric_opt circle_packing

# Check progress
cyclus_queue status metric_opt circle_packing
```
