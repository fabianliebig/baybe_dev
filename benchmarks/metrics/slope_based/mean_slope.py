"""Metrics for using the gradient between two points of the optimization."""

import numpy as np
from attrs import define
from interface_meta import override
from pandas import DataFrame
from baybe.targets.enum import TargetMode

from benchmarks.metrics.base import ValueMetric


@define
class MeanSlope(ValueMetric):
    """Cal."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the convergence rate for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed convergence rate value.
        """
        data = data.copy(True)
        grouped_data = data.groupby(self.doe_iteration_header)
        mean_values = grouped_data[self.to_evaluate_row_header].mean()

        if len(mean_values) < 2:
            raise ValueError("The data must contain at least 2 iterations.")

        slopes = []
        for i in range(1, len(mean_values)):
            delta_y = mean_values.iloc[i] - mean_values.iloc[i - 1]
            if self.target_mode == TargetMode.MIN:
                delta_y = -delta_y
            slopes.append(delta_y)

        return np.mean(slopes)
