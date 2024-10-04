"""Helper functions for generating parameters for PARAMETER_COMBINATION."""

from collections.abc import Sequence

import numpy as np
from botorch.test_functions.synthetic import Hartmann

from baybe.parameters import NumericalDiscreteParameter, TaskParameter
from baybe.parameters.base import Parameter


def hartmann_parameters() -> Sequence[Parameter]:
    """Generate parameters for the Hartmann function from Backtesting.

    Returns:
        list: A list of parameter objects.
    """
    POINTS_PER_DIM = 7
    DIMENSION = 3
    BOUNDS = Hartmann(dim=DIMENSION).bounds

    discrete_params = [
        NumericalDiscreteParameter(
            name=f"x{d}",
            values=np.linspace(lower, upper, POINTS_PER_DIM),
        )
        for d, (lower, upper) in enumerate(BOUNDS.T)
    ]
    task_param = TaskParameter(
        name="Function",
        values=["Hartmann", "Shifted"],
    )  # type: ignore
    parameters = [*discrete_params, task_param]
    return parameters
