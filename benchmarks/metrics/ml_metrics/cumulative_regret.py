"""Copulative regret."""

from attrs import define, field
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class CumulativeRegret(ValueMetric):
    """Simple Regret metric."""

    value_range: tuple[float, float] = field()
    """The maximum value in the lookup table or function."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the comulative regret from the given data.

        Args:
            data: data data containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        best_value = (
            self.value_range[1]
            if self.target_mode is TargetMode.MAX
            else self.value_range[0]
        )

        grouped_data = data.groupby(self.doe_iteration_header)
        mean_values = grouped_data[self.to_evaluate_row_header].mean()
        cumulative_regret = 0
        for _, value in mean_values.items():
            cumulative_regret += abs(best_value - value)

        return cumulative_regret
