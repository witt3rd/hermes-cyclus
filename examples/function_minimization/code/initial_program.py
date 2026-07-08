# EVOLVE-BLOCK-START
"""Function minimization example for OpenEvolve"""
import numpy as np
from scipy.optimize import differential_evolution, minimize


def search_algorithm(iterations=1000, bounds=(-5, 5)):
    """
    Uses multiple differential evolution runs + L-BFGS-B polish for reliable
    global optimization.

    Args:
        iterations: Number of iterations to run
        bounds: Bounds for the search space (min, max)

    Returns:
        Tuple of (best_x, best_y, best_value)
    """
    search_bounds = [(bounds[0], bounds[1]), (bounds[0], bounds[1])]

    def obj(xy):
        return evaluate_function(xy[0], xy[1])

    best_result = None
    best_val = np.inf

    # Run multiple times and keep the best to ensure global minimum is found
    for _ in range(3):
        result = differential_evolution(
            obj,
            bounds=search_bounds,
            maxiter=400,
            tol=1e-10,
            popsize=20,
            mutation=(0.5, 1.5),
            recombination=0.7,
            polish=True,
            strategy='best1bin',
        )
        if result.fun < best_val:
            best_val = result.fun
            best_result = result

    best_x, best_y = best_result.x
    best_value = best_result.fun

    return best_x, best_y, best_value


# EVOLVE-BLOCK-END


# This part remains fixed (not evolved)
def evaluate_function(x, y):
    """The complex function we're trying to minimize"""
    return np.sin(x) * np.cos(y) + np.sin(x * y) + (x**2 + y**2) / 20


def run_search():
    x, y, value = search_algorithm()
    return x, y, value


if __name__ == "__main__":
    x, y, value = run_search()
    print(f"Found minimum at ({x}, {y}) with value {value}")
