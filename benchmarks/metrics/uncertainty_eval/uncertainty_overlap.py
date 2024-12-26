"""uncertanty overlap metric."""

import numpy as np
from attrs import field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class OverlappingUncertaintyArea(ValueMetric):
    """Overlapping uncertainty area metric."""

    ground_truth: DataFrame = field(validator=instance_of(DataFrame))
    """The data frame which will be compared in the evaluation."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the uncertainty area for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        data = data.copy(True)
        ground_truth = self.ground_truth.copy(True)

        header = self.to_evaluate_row_header
        if self.target_mode == TargetMode.MIN:
            data[header] -= data[header].max()
            ground_truth[header] -= ground_truth[header].max()
        elif self.target_mode == TargetMode.MAX:
            data[header] -= data[header].min()
            ground_truth[header] -= ground_truth[header].min()

        iter_group_data = data.groupby(self.doe_iteration_header)
        iter_group_gt = ground_truth.groupby(self.doe_iteration_header)

        x_data = iter_group_data[self.doe_iteration_header].first().values
        y_data = iter_group_data[header].mean().values

        y_gt = iter_group_gt[header].mean().values

        lower_quantile_data = np.percentile(y_data, 2.5)
        upper_quantile_data = np.percentile(y_data, 97.5)

        lower_quantile_gt = np.percentile(y_gt, 2.5)
        upper_quantile_gt = np.percentile(y_gt, 97.5)

        lower_bound = np.maximum(lower_quantile_data, lower_quantile_gt)
        upper_bound = np.minimum(upper_quantile_data, upper_quantile_gt)

        lower_y = np.clip(y_data, None, lower_bound)
        upper_y = np.clip(y_data, upper_bound, None)

        auc_lower = np.trapz(lower_y, x_data)
        auc_upper = np.trapz(upper_y, x_data)

        uncertainty_area = abs(auc_upper - auc_lower)
        return uncertainty_area
