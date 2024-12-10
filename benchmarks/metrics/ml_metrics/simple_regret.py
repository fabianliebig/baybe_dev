"""Simple regret metric."""

import numpy as np
from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import Metric


@define
class SimpleRegret(Metric):
    """Simple Regret metric."""

    lookup: DataFrame | tuple[float, float] = field(
        validator=instance_of((DataFrame, tuple))
    )
    """The lookup table or function to evaluate the goal orientation
    metric and compare the best included result."""

    _max_value_y: float = field(init=False, validator=instance_of(float))
    """The maximum value in the lookup table or function."""

    _min_value_y: float = field(init=False, validator=instance_of(float))
    """The minimum value in the lookup table or function."""

    @_max_value_y.default
    def _max_value_y_default(self) -> float:
        """Set the default value for the max value."""
        if isinstance(self.lookup, tuple):
            _, max = self.lookup
            return max
        return self.lookup[self.objective_name].max()

    @_min_value_y.default
    def _max_value_y_default(self) -> float:
        """Set the default value for the min value."""
        if isinstance(self.lookup, tuple):
            min, _ = self.lookup
            return min
        return self.lookup[self.objective_name].min()

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the simple regret for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        max_found = data[self.to_evaluate_row_header].max()
        simple_regret = abs(self._max_value_y - max_found)
        return simple_regret


@define
class NormalizedSimpleRegret(SimpleRegret):
    """Normalized simple regret."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the normalized simple regret for a data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed normalized AUC value.
        """
        regret = super().evaluate(data)
        normalized_regret = regret / (self._max_value_y - self._min_value_y)
        return normalized_regret
