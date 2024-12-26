"""Metrics for convergence rate of optimization algorithms."""

from attrs import define
from interface_meta import override
from pandas import DataFrame
import math
from benchmarks.metrics.base import BestValueMetric


@define
class MeanConvergenceRateMetric(BestValueMetric):
    """Convergence rate metric."""

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
        start_point = mean_values.iloc[0]
        best_point = mean_values.iloc[-1]

        return 1 - (
            (abs((self.best_value - best_point) / (self.best_value - start_point)))
            ** (1 / len(mean_values))
        )


class DynamicConvergenceRateMetric(BestValueMetric):
    """Convergence rate metric."""

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

        conv_sum = 0
        if self.best_value is not None:
            for i in range(1, len(mean_values)):
                conv_sum += abs(self.best_value - mean_values.iloc[i]) / abs(
                    self.best_value - mean_values.iloc[i - 1]
                )
            return conv_sum

        for i in range(1, len(mean_values) - 1):
            conv_sum += abs(mean_values.iloc[i + 1] - mean_values.iloc[i]) / abs(
                mean_values.iloc[i] + mean_values.iloc[i - 1]
            )

        return conv_sum
