"""Gives the ratio of points better than random based on the iteration."""

from enum import Enum

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class PointsDifferedRatio(ValueMetric):
    """Calculates the rato the positional relationship of points."""

    class CountMode(Enum):
        """Enumeration for the count mode."""

        COUNT_BETTER = "count_better"
        COUNT_WORSE = "count_worse"
        COUNT_EQUAL = "count_equal"

    data_baseline: DataFrame = field(validator=instance_of(DataFrame))
    """The data frame which will be compared in the evaluation."""

    count_mode: CountMode = field(
        validator=instance_of(CountMode), default=CountMode.COUNT_BETTER
    )
    """The count mode to be used for the evaluation."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the ratio of points between data frames based on the count mode.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        successful_points_count = 0
        mean_data = (
            data.groupby(self.doe_iteration_header)[self.to_evaluate_row_header]
            .mean()
            .reset_index()
        )
        mean_random = (
            self.data_baseline.groupby(self.doe_iteration_header)[
                self.to_evaluate_row_header
            ]
            .mean()
            .reset_index()
        )

        COUNT_POINTS_IF_ABOVE = (
            self.target_mode == TargetMode.MAX
            and self.count_mode == PointsDifferedRatio.CountMode.COUNT_BETTER
        ) or (
            self.target_mode == TargetMode.MIN
            and self.count_mode == PointsDifferedRatio.CountMode.COUNT_WORSE
        )
        COUNT_POINTS_IF_BELOW = (
            self.target_mode == TargetMode.MIN
            and self.count_mode == PointsDifferedRatio.CountMode.COUNT_BETTER
        ) or (
            self.target_mode == TargetMode.MAX
            and self.count_mode == PointsDifferedRatio.CountMode.COUNT_WORSE
        )

        for i in range(mean_data.shape[0]):
            if COUNT_POINTS_IF_BELOW:
                OPT_POINT_SMALLER = (
                    mean_data[self.to_evaluate_row_header].iloc[i]
                    < mean_random[self.to_evaluate_row_header].iloc[i]
                )
                if OPT_POINT_SMALLER:
                    successful_points_count += 1

            elif COUNT_POINTS_IF_ABOVE:
                OPT_POINT_LARGER = (
                    mean_data[self.to_evaluate_row_header].iloc[i]
                    > mean_random[self.to_evaluate_row_header].iloc[i]
                )
                if OPT_POINT_LARGER:
                    successful_points_count += 1
            else:
                OPT_POINT_EQUAL = (
                    mean_data[self.to_evaluate_row_header].iloc[i]
                    == mean_random[self.to_evaluate_row_header].iloc[i]
                )
                if OPT_POINT_EQUAL:
                    successful_points_count += 1

        return successful_points_count / data[self.doe_iteration_header].unique().size


class PointVarianceDifferRatio(PointsDifferedRatio):
    """Calculate the ratio of points depending on their variance."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the ratio of points that are better than a random baseline.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed uncertainty area value.
        """
        successful_points_count = 0

        COUNT_POINTS_IF_ABOVE = (
            self.count_mode == PointsDifferedRatio.CountMode.COUNT_WORSE
        )

        COUNT_POINTS_IF_BELOW = (
            self.count_mode == PointsDifferedRatio.CountMode.COUNT_BETTER
        )
        DF_GROUP = 1
        for data_group, baseline_group in zip(
            data.groupby(self.doe_iteration_header),
            self.data_baseline.groupby(self.doe_iteration_header),
        ):
            if COUNT_POINTS_IF_BELOW:
                OPT_POINT_SMALLER = (
                    data_group[DF_GROUP][self.to_evaluate_row_header].var()
                    < baseline_group[DF_GROUP][self.to_evaluate_row_header].var()
                )
                if OPT_POINT_SMALLER:
                    successful_points_count += 1

            elif COUNT_POINTS_IF_ABOVE:
                OPT_POINT_LARGER = (
                    data_group[DF_GROUP][self.to_evaluate_row_header].var()
                    > baseline_group[DF_GROUP][self.to_evaluate_row_header].var()
                )
                if OPT_POINT_LARGER:
                    successful_points_count += 1
            else:
                OPT_POINT_EQUAL = (
                    data_group[DF_GROUP][self.to_evaluate_row_header].var()
                    == baseline_group[DF_GROUP][self.to_evaluate_row_header].var()
                )
                if OPT_POINT_EQUAL:
                    successful_points_count += 1

        return successful_points_count / data[self.doe_iteration_header].unique().size
