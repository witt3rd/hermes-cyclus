# EVOLVE-BLOCK-START
"""Function minimization example for OpenEvolve"""
import numpy as np
from scipy.optimize import differential_evolution


def search_algorithm(iterations=1000, bounds=(-5, 5)):
    """
    Uses differential evolution for reliable global optimization.

    Args:
        iterations: Number of iterations to run
        bounds: Bounds for the search space (min, max)

    Returns:
        Tuple of (best_x, best_y, best_value)
    """
    search_bounds = [(bounds[0], bounds[1]), (bounds[0], bounds[1])]

    result = differential_evolution(
        lambda xy: evaluate_function(xy[0], xy[1]),
        bounds=search_bounds,
        maxiter=300,
        tol=1e-9,

        popsize=15,
        mutation=(0.5, 1.5),
        recombination=0.7,
        polish=True,
    )

    best_x, best_y = result.x
    best_value = result.fun

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
