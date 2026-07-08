# Function Minimization — Loop State

**Spec:** MetricOptimizationKind | direction: higher_is_better  
**Baseline:** 1.42 | **Target:** 1.3 (already exceeded; true goal is approach 1.5 theoretical max)  
**Known global minimum:** (-1.704, 0.678) with value -1.519

---

## Loop Run Log

### Iteration 1 — 2026-07-07 17:18 PDT

**Executor:** cyclus-ralph L1 (cron)  
**Current score:** 1.405 (avg of 3 live eval runs: 1.411, 1.397, 1.404)  
**Score components (representative):**
- value_score: 0.961–0.970  
- distance_score: 0.837–0.852 (implied avg_distance ≈ 0.17–0.19)  
- reliability_score: 1.0 (all 10 trials succeed)  
- multiplier: 1.5× (avg_distance < 0.5, already in the top tier)

**Observations:**
- The naive random search (1000 uniform draws) already lands in the 1.5× multiplier bracket — it consistently gets within ~0.18 of the global min on average.
- The gap to the theoretical max (1.5) is entirely in value_score and distance_score. value_score ≈ 0.965 instead of 1.0 means avg_value ≈ -1.465 instead of -1.519; distance ≈ 0.17 instead of 0.0.
- Note: target_score: 1.3 in spec is already exceeded. The meaningful improvement target is pushing toward the theoretical ceiling of 1.5.

**Proposal summary:** Replace naive random search with `scipy.optimize.differential_evolution` — a global optimizer specifically designed for multimodal functions.

**Reasoning:**
- `differential_evolution` is a population-based evolutionary algorithm that explores the search space globally, not through random iid draws.
- Empirically verified: 5 seed runs all converged to (-1.7041, 0.6775) with value -1.518686, avg_distance ≈ 0.0005.
- Projected score: value_score ≈ 0.9997, distance_score ≈ 0.9995, reliability_score = 1.0, multiplier = 1.5× → combined_score ≈ **1.499** (vs current ~1.405).
- `scipy` is already in the requirements (used by evaluator.py via implicit dependency; it's a declared dep).
- The function signature and return type are preserved exactly — the eval harness sees no change.
- `iterations` param maps cleanly to `maxiter` in differential_evolution, preserving backward compatibility.

**Proposed diff:**
```diff
--- a/examples/function_minimization/code/initial_program.py
+++ b/examples/function_minimization/code/initial_program.py
@@ -1,33 +1,31 @@
 # EVOLVE-BLOCK-START
 """Function minimization example for OpenEvolve"""
 import numpy as np
+from scipy.optimize import differential_evolution
 
 
 def search_algorithm(iterations=1000, bounds=(-5, 5)):
     """
-    A simple random search algorithm that often gets stuck in local minima.
+    Global optimization using differential evolution — reliably escapes local minima.
 
     Args:
         iterations: Number of iterations to run
         bounds: Bounds for the search space (min, max)
 
     Returns:
         Tuple of (best_x, best_y, best_value)
     """
-    # Initialize with a random point
-    best_x = np.random.uniform(bounds[0], bounds[1])
-    best_y = np.random.uniform(bounds[0], bounds[1])
-    best_value = evaluate_function(best_x, best_y)
-
-    for _ in range(iterations):
-        # Simple random search
-        x = np.random.uniform(bounds[0], bounds[1])
-        y = np.random.uniform(bounds[0], bounds[1])
-        value = evaluate_function(x, y)
-
-        if value < best_value:
-            best_value = value
-            best_x, best_y = x, y
-
-    return best_x, best_y, best_value
+    search_bounds = [(bounds[0], bounds[1]), (bounds[0], bounds[1])]
+
+    result = differential_evolution(
+        lambda xy: evaluate_function(xy[0], xy[1]),
+        search_bounds,
+        maxiter=iterations,
+        tol=1e-10,
+        popsize=15,
+        mutation=(0.5, 1.5),
+        recombination=0.7,
+        seed=None,
+    )
+
+    return result.x[0], result.x[1], result.fun
 
 
 # EVOLVE-BLOCK-END
```

**Status:** L1 — proposed only, not applied.
