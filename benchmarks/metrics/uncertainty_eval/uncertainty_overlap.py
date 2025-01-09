"""uncertanty overlap metric."""

import numpy as np
from attrs import define, field
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

        iterations = data[self.doe_iteration_header].unique().size

        total_overlap_area = 0.0

        for i in range(iterations - 1):
            y_data_i = data[(data[self.doe_iteration_header] == i)][
                self.to_evaluate_row_header
            ].values
            y_data_j = data[(data[self.doe_iteration_header] == i + 1)][
                self.to_evaluate_row_header
            ].values
            y_gt_i = ground_truth[(ground_truth[self.doe_iteration_header] == i)][
                self.to_evaluate_row_header
            ].values
            y_gt_j = ground_truth[(ground_truth[self.doe_iteration_header] == i + 1)][
                self.to_evaluate_row_header
            ].values

            lower_quantile_data = (
                np.percentile(y_data_i, 2.5, axis=0),
                np.percentile(y_data_j, 2.5, axis=0),
            )
            upper_quantile_data = (
                np.percentile(y_data_i, 97.5, axis=0),
                np.percentile(y_data_j, 97.5, axis=0),
            )

            lower_quantile_gt = (
                np.percentile(y_gt_i, 2.5, axis=0),
                np.percentile(y_gt_j, 2.5, axis=0),
            )
            upper_quantile_gt = (
                np.percentile(y_gt_i, 97.5, axis=0),
                np.percentile(y_gt_j, 97.5, axis=0),
            )

            lower_bound = np.maximum(lower_quantile_data, lower_quantile_gt)
            upper_bound = np.minimum(upper_quantile_data, upper_quantile_gt)

            if np.all(lower_bound < upper_bound):
                auc_lower = np.trapz(lower_bound)
                auc_upper = np.trapz(upper_bound)

                total_overlap_area += abs(auc_upper - auc_lower)

        return total_overlap_area
