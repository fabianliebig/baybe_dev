"""Gives the ratio of points better than random based on the iteration."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class PointsBetterRandomRatio(ValueMetric):
    """Calculates the ratio of points that are better than a random baseline."""

    random_baseline: DataFrame = field(validator=instance_of(DataFrame))
    """The data frame which will be compared in the evaluation."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the ratio of points that are better than a random baseline.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        data = data.copy(True)
        self.random_baseline = self.random_baseline.copy(True)
        points_better_than_random = 0
        mean_data = (
            data.groupby(self.doe_iteration_header)[self.to_evaluate_row_header]
            .mean()
            .reset_index()
        )
        mean_random = (
            self.random_baseline.groupby(self.doe_iteration_header)[
                self.to_evaluate_row_header
            ]
            .mean()
            .reset_index()
        )

        for i in range(mean_data.shape[0]):
            if self.target_mode == TargetMode.MIN:
                OPT_POINT_SMALLER = (
                    mean_data[self.to_evaluate_row_header].iloc[i]
                    < mean_random[self.to_evaluate_row_header].iloc[i]
                )
                if OPT_POINT_SMALLER:
                    points_better_than_random += 1

            elif self.target_mode == TargetMode.MAX:
                OPT_POINT_LARGER = (
                    mean_data[self.to_evaluate_row_header].iloc[i]
                    > mean_random[self.to_evaluate_row_header].iloc[i]
                )
                if OPT_POINT_LARGER:
                    points_better_than_random += 1

        return points_better_than_random / data[self.doe_iteration_header].unique().size
