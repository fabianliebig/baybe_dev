"""Metrics for using the variance per iteration."""

from attrs import define
from interface_meta import override
from pandas import DataFrame

from benchmarks.metrics.base import ValueMetric


@define
class MeanVariance(ValueMetric):
    """Calculate the mean variance over the iterations."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the convergence rate for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed convergence rate value.
        """
        grouped_data = data.groupby(self.doe_iteration_header)
        variance_values = grouped_data[self.to_evaluate_row_header].var()

        return variance_values.mean()
