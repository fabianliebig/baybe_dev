"""Kuiper metric."""

from enum import Enum
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

        normalized_ground_truth = (
            self.ground_truth.groupby(self.doe_iteration_header)[
                self.to_evaluate_row_header
            ]
            .mean()
            .values
        )

        evaluate_data = (evaluate_data - evaluate_data.min()) / (
            evaluate_data.max() - evaluate_data.min()
        )
        normalized_ground_truth = (
            normalized_ground_truth - normalized_ground_truth.min()
        ) / (normalized_ground_truth.max() - normalized_ground_truth.min())

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


class PositionalRelation(Enum):
    """Positional relation enum."""

    SHARE_NO_POINT = 1
    ONLY_SHARE_SOME_POINTS = 2
    CROSS_EACH_OTHER = 3

    def __eq__(self, value):
        if isinstance(value, PositionalRelation):
            return self.value == value.value
        return self.value == value

    def __ne__(self, value):
        return not self.__eq__(value)

    def __lt__(self, value):
        if isinstance(value, PositionalRelation):
            return self.value < value.value
        return self.value < value

    def __le__(self, value):
        return self.__lt__(value) or self.__eq__(value)

    def __gt__(self, value):
        return not self.__le__(value)

    def __ge__(self, value):
        return not self.__lt__(value)


@define
class ConvergenceLocationRelationship(ValueMetric):
    """Convergence location relationship metric."""

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
        kuiper = KuiperMetric(
            to_evaluate_row_header=self.to_evaluate_row_header,
            doe_iteration_header=self.doe_iteration_header,
            ground_truth=self.ground_truth,
            target_mode=self.target_mode,
        )
        kolmogorov = KolmogorovSmirnovMetric(
            to_evaluate_row_header=self.to_evaluate_row_header,
            doe_iteration_header=self.doe_iteration_header,
            ground_truth=self.ground_truth,
            target_mode=self.target_mode,
        )

        kuiper_value = kuiper.evaluate(data)
        kolmogorov_value = kolmogorov.evaluate(data)

        if kuiper_value == kolmogorov_value:
            return PositionalRelation.ONLY_SHARE_SOME_POINTS
        elif kuiper_value < kolmogorov_value:
            return PositionalRelation.SHARE_NO_POINT
        else:
            return PositionalRelation.CROSS_EACH_OTHER
