"""Metrics for convergence rate of optimization algorithms."""

import numpy as np
from attrs import define
from interface_meta import override
from pandas import DataFrame

from baybe.targets.enum import TargetMode
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


@define
class MedianPointToPointConvergenceValue(BestValueMetric):
    """Estimated convergence rate metric."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the estimated convergence rate for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed estimated convergence rate value.
        """
        grouped_data = data.groupby(self.doe_iteration_header)
        mean_values = grouped_data[self.to_evaluate_row_header].mean()

        if len(mean_values) < 4:
            raise ValueError("The sequence must have at least 4 elements.")

        alpha_estimates = []
        for n in range(2, len(mean_values) - 1):
            diff1 = mean_values[n + 1] - mean_values[n]
            diff2 = mean_values[n] - mean_values[n - 1]
            diff3 = mean_values[n - 1] - mean_values[n - 2]

            if diff2 == 0 or diff3 == 0 or diff1 == 0:
                continue

            num = np.log(abs(diff1 / diff2))
            denom = np.log(abs(diff2 / diff3))

            if (num <= 0 or denom <= 0) and not (num < 0 and denom < 0):
                continue

            alpha = num / denom

            alpha_estimates.append(alpha)

        return np.median(alpha_estimates)


@define
class MedianGlobalBestConvergenceValue(BestValueMetric):
    """Estimated convergence rate metric."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the estimated convergence rate for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed estimated convergence rate value.
        """
        grouped_data = data.groupby(self.doe_iteration_header)
        mean_values = grouped_data[self.to_evaluate_row_header].mean()

        if len(mean_values) < 4:
            raise ValueError("The sequence must have at least 4 elements.")

        alpha_estimates = []
        for n in range(1, len(mean_values) - 1):
            diff1 = mean_values[n + 1] - self.best_value
            diff2 = mean_values[n] - self.best_value
            diff3 = mean_values[n - 1] - self.best_value

            if diff2 == 0 or diff3 == 0 or diff1 == 0:
                continue

            num = np.log(abs(diff1 / diff2))
            denom = np.log(abs(diff2 / diff3))

            if (num <= 0 or denom <= 0) and not (num < 0 and denom < 0):
                continue

            alpha = num / denom

            alpha_estimates.append(alpha)

        return np.median(alpha_estimates)
