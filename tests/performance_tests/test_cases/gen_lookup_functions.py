"""This contains functions to call itself or create Dataframes for the lookup data."""

import numpy as np
from botorch.test_functions.synthetic import Hartmann
from pandas import DataFrame, concat

from baybe.parameters.numerical import NumericalDiscreteParameter
from baybe.utils.botorch_wrapper import botorch_function_wrapper


def create_lookup_for_hartmann() -> DataFrame:
    DIMENSION = 3
    POINTS_PER_DIM = 7
    BOUNDS = Hartmann(dim=DIMENSION).bounds
    discrete_params = [
        NumericalDiscreteParameter(
            name=f"x{d}",
            values=np.linspace(lower, upper, POINTS_PER_DIM),
        )
        for d, (lower, upper) in enumerate(BOUNDS.T)
    ]

    def shifted_hartmann(*x: float) -> float:
        """Calculate a shifted, scaled and noisy variant of the Hartman function."""
        noised_hartmann = Hartmann(dim=DIMENSION, noise_std=0.15)
        return 2.5 * botorch_function_wrapper(noised_hartmann)(x) + 3.25

    test_functions = {
        "Hartmann": botorch_function_wrapper(Hartmann(dim=DIMENSION)),
        "Shifted": shifted_hartmann,
    }

    grid = np.meshgrid(*[p.values for p in discrete_params])
    lookups: dict[str, DataFrame] = {}
    for function_name, function in test_functions.items():
        lookup = DataFrame({f"x{d}": grid_d.ravel() for d, grid_d in enumerate(grid)})
        lookup["Target"] = tuple(lookup.apply(function, axis=1))
        lookup["Function"] = function_name
        lookups[function_name] = lookup
    return concat([lookups["Hartmann"], lookups["Shifted"]]).reset_index()
