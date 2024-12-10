"""Copulative regret."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import Metric


@define
class CumulativeRegret(Metric):
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
        """Calculate the comulative regret from the given data.

        Args:
            data: data data containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        grouped_data = data.groupby(self.doe_iteration_header)
        mean_values = grouped_data[self.to_evaluate_row_header].mean()
        cumulative_regret = 0
        for _, value in mean_values.items():
            cumulative_regret += abs(self._max_value_y - value)

        return cumulative_regret
