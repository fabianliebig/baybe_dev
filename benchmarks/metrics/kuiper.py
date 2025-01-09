"""Kuiper metric."""

import numpy as np
import pandas as pd
from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class KuiperMetric(ValueMetric):
    """Kuiper metric."""

    ground_truth: DataFrame = field(validator=instance_of(DataFrame))
    """The data frame which will be compared in the evaluation."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the ratio of points that are better than a random baseline.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        eval_data, ground_truth = self._compute_cumulative_mean(data)

        return np.max(eval_data - ground_truth) - np.min(eval_data - ground_truth)

    def _compute_cumulative_mean(self, data: DataFrame) -> tuple[pd.Series, pd.Series]:
        """Compute the cumulative mean with respect to the samples and iterations.

        This method calculates the cumulative mean for the given data and normalizes it
        based on the target mode (either MIN or MAX). It also computes the cumulative
        mean for the ground truth data and normalizes it similarly.

        Args:
            data (DataFrame): The input data for which the cumulative
            mean is to be computed.

        Returns:
            tuple[pd.Series, pd.Series]: A tuple containing two pandas Series:
                - The normalized cumulative mean of the evaluated data.
                - The normalized cumulative mean of the ground truth data.
        """
        data_copy = data.copy(True)
        evaluate_data = (
            data_copy.groupby(self.doe_iteration_header)[self.to_evaluate_row_header]
            .mean()
            .values
        )

        ground_truth_copy = self.ground_truth.copy(True)
        normalized_ground_truth = (
            ground_truth_copy.groupby(self.doe_iteration_header)[
                self.to_evaluate_row_header
            ]
            .mean()
            .values
        )

        normalize_value_to_one = None
        normalize_value_to_zero = None
        if self.target_mode == TargetMode.MIN:
            normalize_value_to_one = np.min(
                [evaluate_data[-1], normalized_ground_truth[-1]]
            )
            normalize_value_to_zero = np.max(
                [evaluate_data[0], normalized_ground_truth[0]]
            )
        elif self.target_mode == TargetMode.MAX:
            normalize_value_to_one = np.max(
                [evaluate_data[-1], normalized_ground_truth[-1]]
            )
            normalize_value_to_zero = np.min(
                [evaluate_data[0], normalized_ground_truth[0]]
            )

        evaluate_data = (evaluate_data - normalize_value_to_zero) / (
            normalize_value_to_one - normalize_value_to_zero
        )
        normalized_ground_truth = (
            normalized_ground_truth - normalize_value_to_zero
        ) / (normalize_value_to_one - normalize_value_to_zero)

        return evaluate_data, normalized_ground_truth


@define
class KolmogorovSmirnovMetric(KuiperMetric):
    """Kolmogorov-Smirnov metric."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the ratio of points that are better than a random baseline.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        eval_data, ground_truth = self._compute_cumulative_mean(data)

        return np.max(np.abs(eval_data - ground_truth))
