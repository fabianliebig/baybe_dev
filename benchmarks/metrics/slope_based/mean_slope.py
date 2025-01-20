"""Metrics for using the gradient between two points of the optimization."""

from attrs import define
from interface_meta import override
from pandas import DataFrame

from benchmarks.metrics.base import ValueMetric


@define
class MeanSlope(ValueMetric):
    """Calculate the mean slope of the optimization."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the convergence rate for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed convergence rate value.
        """
        grouped_data = data.groupby(self.doe_iteration_header)
        mean_values = grouped_data[self.to_evaluate_row_header].mean()

        if len(mean_values) < 2:
            raise ValueError("The data must contain at least 2 iterations.")

        start_point = mean_values.iloc[0]
        end_point = mean_values.iloc[-1]

        return (end_point - start_point) / len(mean_values)
