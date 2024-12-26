"""Uncertainty Area metric implementation."""

import numpy as np
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class UncertaintyCurveArea(ValueMetric):
    """Area between the upper and lower quantiles of the uncertainty curve."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the uncertainty area for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        data = data.copy()
        header = self.to_evaluate_row_header
        if self.target_mode == TargetMode.MIN:
            data[header] -= data[header].max()
        elif self.target_mode == TargetMode.MAX:
            data[header] -= data[header].min()

        iter_group = data.groupby(self.doe_iteration_header)
        x = iter_group[self.doe_iteration_header].first().values
        y = iter_group[header].mean().values

        lower_quantile = np.percentile(y, 2.5)
        upper_quantile = np.percentile(y, 97.5)

        lower_y = np.clip(y, None, lower_quantile)
        upper_y = np.clip(y, upper_quantile, None)

        auc_lower = np.trapz(lower_y, x)
        auc_upper = np.trapz(upper_y, x)

        uncertainty_area = abs(auc_upper - auc_lower)
        return uncertainty_area
