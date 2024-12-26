"""Copulative regret."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import ValueMetric


@define
class CumulativeRegret(ValueMetric):
    """Simple Regret metric."""

    best_value: float = field(validator=instance_of(float))
    """The maximum value in the lookup table or function."""

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
            cumulative_regret += abs(self.best_value - value)

        return cumulative_regret
