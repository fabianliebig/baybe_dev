"""Copulative regret."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class CumulativeRegret(ValueMetric):
    """Simple Regret metric."""

    lookup: DataFrame | tuple[float, float] = field(
        validator=instance_of((DataFrame, tuple))
    )
    """The lookup table or function to evaluate the goal orientation
    metric and compare the best included result."""

    objective_name: TargetMode = field(validator=instance_of(TargetMode))
    """The name of the objective to evaluate."""

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
        compare_value = (
            self._max_value_y
            if self.objective_name is TargetMode.MAX
            else self._min_value_y
        )
        for _, value in mean_values.items():
            cumulative_regret += abs(compare_value - value)

        return cumulative_regret
